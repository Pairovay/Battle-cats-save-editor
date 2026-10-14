"""Bridge between BCSFE (a console program) and the graphical interface.

BCSFE asks the user for everything through a handful of functions in
``bcsfe.cli.dialog_creator`` and ``bcsfe.cli.color``. They are replaced here by
versions that, instead of reading from the console, publish a "prompt" that the
interface shows as a dialog (buttons, checkboxes, number fields...) and then
wait for the answer. The logic of every BCSFE feature is left untouched, so all
features behave exactly as they do in the console version.
"""

from __future__ import annotations

import builtins
import itertools
import sys
import threading
import time
from typing import Any, Callable

from . import native_dialogs, textfmt


class LogBuffer:
    """Output log (what BCSFE would print to the console)."""

    MAX_ENTRIES = 4000

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.entries: list[dict[str, Any]] = []
        self.next_index = 0
        self._line: list[list[str]] = []

    def _push_line(self, segs: list[list[str]]) -> None:
        self.entries.append({"i": self.next_index, "segs": segs, "t": time.time()})
        self.next_index += 1
        if len(self.entries) > self.MAX_ENTRIES:
            del self.entries[: len(self.entries) - self.MAX_ENTRIES]

    def write_segments(self, segs: list[list[str]], end: str = "\n") -> None:
        with self.lock:
            for text, style in segs + [[end, ""]]:
                parts = text.split("\n")
                for n, part in enumerate(parts):
                    if part:
                        self._line.append([part, style])
                    if n < len(parts) - 1:
                        self._push_line(self._line)
                        self._line = []

    def write_text(self, text: str, style: str = "") -> None:
        self.write_segments([[textfmt.ANSI_RE.sub("", text), style]], end="")

    def flush_partial(self) -> None:
        with self.lock:
            if self._line:
                self._push_line(self._line)
                self._line = []

    def since(self, index: int) -> tuple[list[dict[str, Any]], int]:
        with self.lock:
            entries = [e for e in self.entries if e["i"] >= index]
            return entries, self.next_index


class GuiStdout:
    """Replaces sys.stdout/sys.stderr so everything printed goes to the log."""

    def __init__(self, log: LogBuffer, original: Any, style: str = "") -> None:
        self.log = log
        self.original = original
        self.style = style
        self.encoding = "utf-8"

    def write(self, s: str) -> int:
        if not s:
            return 0
        self.log.write_text(s, self.style)
        if self.original is not None:
            try:
                self.original.write(s)
            except Exception:
                pass
        return len(s)

    def flush(self) -> None:
        if self.original is not None:
            try:
                self.original.flush()
            except Exception:
                pass

    def isatty(self) -> bool:
        return False


class JobCancelled(BaseException):
    """Stops the running BCSFE feature (like Ctrl+C in the console).

    It derives from BaseException so BCSFE's ``except Exception`` blocks do not
    swallow it."""


EXIT_KEYS = ("finish", "go_back", "exit", "cancel", "finish_edit_cats", "finish_selection")


class Bridge:
    def __init__(self) -> None:
        self.log = LogBuffer()
        self.lock = threading.Lock()
        self.prompt: dict[str, Any] | None = None
        self._answer: Any = None
        self._event = threading.Event()
        self._ids = itertools.count(1)
        self.job_thread: threading.Thread | None = None
        # Automatic answers: used by native screens (e.g. the visual cat
        # editor) to fill BCSFE prompts with what the user already chose.
        self.auto_answers: list[tuple[str, Any]] = []
        self.waiting_file_dialog = False
        self.abort_requested = False
        # Detects menus that come back after "Cancel" (BCSFE loops).
        self._last_cancelled: str | None = None
        self._repeat_cancels = 0

    # ------------------------------------------------------------------ prompts
    def in_job(self) -> bool:
        return self.job_thread is not None and threading.current_thread() is self.job_thread

    def ask(self, kind: str, text: Any = "", **data: Any) -> Any:
        if self.auto_answers:
            expected_kind, value = self.auto_answers[0]
            if expected_kind == kind:
                self.auto_answers.pop(0)
                return value
            # BCSFE asked something unexpected: ask the user instead.
            self.auto_answers = []
        if not self.in_job():
            raise RuntimeError("BCSFE asked for input outside of a GUI task")
        if self.abort_requested:
            raise JobCancelled()
        self.log.flush_partial()
        segs = textfmt.parse(text) if isinstance(text, str) else text
        signature = repr((kind, segs, data.get("options"), data.get("name")))
        if signature == self._last_cancelled:
            # The same menu came back right after being cancelled: it is a
            # BCSFE loop that only ends by picking its exit option.
            self._repeat_cancels += 1
            exit_index = self._exit_option(data.get("options")) if kind == "select" else None
            if exit_index is not None and self._repeat_cancels == 1:
                return exit_index
            raise JobCancelled()
        prompt = {"id": next(self._ids), "kind": kind, "text": segs, **data}
        with self.lock:
            self._answer = None
            self._event.clear()
            self.prompt = prompt
        self._event.wait()
        with self.lock:
            answer = self._answer
            self.prompt = None
        if self.abort_requested:
            raise JobCancelled()
        if answer is None:
            self._last_cancelled = signature
            self._repeat_cancels = 0
        else:
            self._last_cancelled = None
        return answer

    @staticmethod
    def _exit_option(options: Any) -> int | None:
        if not options:
            return None
        try:
            from bcsfe import core

            labels = {textfmt.plain(core.localize(key)).strip().lower() for key in EXIT_KEYS}
        except Exception:
            labels = {"finish", "go back", "exit", "cancel"}
        for index, option in enumerate(options):
            text = "".join(seg[0] for seg in option).strip().lower()
            if text in labels:
                return index
        return None

    def reset_for_job(self) -> None:
        self.abort_requested = False
        self._last_cancelled = None
        self._repeat_cancels = 0

    def request_abort(self) -> None:
        self.abort_requested = True
        with self.lock:
            if self.prompt is not None:
                self._answer = None
                self._event.set()

    def answer(self, prompt_id: int, value: Any) -> bool:
        with self.lock:
            if self.prompt is None or self.prompt["id"] != prompt_id:
                return False
            self._answer = value
            self._event.set()
            return True

    def cancel_prompt(self) -> None:
        with self.lock:
            if self.prompt is not None:
                self._answer = None
                self._event.set()

    def current_prompt(self) -> dict[str, Any] | None:
        with self.lock:
            return dict(self.prompt) if self.prompt else None


bridge = Bridge()


def _segs(text: Any) -> list[list[str]]:
    return textfmt.parse(text if isinstance(text, str) else str(text))


def install() -> None:
    """Installs the replacements into BCSFE's modules (call it once)."""
    from bcsfe import core
    from bcsfe.cli import color, dialog_creator as dc, file_dialog

    b = bridge
    sys.stdout = GuiStdout(b.log, sys.__stdout__)
    sys.stderr = GuiStdout(b.log, sys.__stderr__, "e")

    def quit_key() -> str:
        return core.localize("quit_key")

    # ---------------------------------------------------------------- output
    def color_print(text: str, end: str = "\n") -> None:
        b.log.write_segments(textfmt.parse(text), end)

    color.color_print = color_print

    # ----------------------------------------------------------------- input
    def color_input(text: str) -> str:
        value = b.ask("text", text)
        if value is None:
            return quit_key()
        return str(value)

    color.color_input = color_input

    original_input = builtins.input

    def gui_input(prompt: Any = "") -> str:
        if not b.in_job():
            return original_input(prompt)
        value = b.ask("text", str(prompt))
        return "" if value is None else str(value)

    builtins.input = gui_input

    def single_select_raw(actions: Any, dialog: str) -> Any:
        if actions.max() == 0:
            return None
        if actions.len() == 1 and actions.actions[0].len() == 1:
            return actions.actions[0].run(0)
        options = [_segs(opt) for action in actions.actions for opt in action.options]
        index = b.ask("select", dialog, options=options)
        if index is None:
            return None
        found = actions.get_rebase(int(index))
        if found is None:
            return None
        action, rebased = found
        return action.run(rebased)

    dc.single_select_raw = single_select_raw

    def multi_select_entries_raw(options: list[str], dialog: str) -> list[tuple[int, str]] | None:
        if not options:
            return None
        if len(options) == 1:
            return [(0, options[0])]
        indexes = b.ask("multi", dialog, options=[_segs(o) for o in options])
        if indexes is None:
            return None
        result: list[tuple[int, str]] = []
        for index in indexes:
            index = int(index)
            if 0 <= index < len(options):
                result.append((index, options[index]))
        return result

    dc.multi_select_entries_raw = multi_select_entries_raw

    def int_input_raw(dialog: str, _max: Any, _min: int = 0, default: int | None = None, auto_clamp: bool = False) -> int | None:
        value = b.ask("int", dialog, min=_min, max=_max.max, default=default, show_max=bool(_max.show))
        if value is None or value == "":
            return None if value is None else default
        try:
            value = int(value)
        except (TypeError, ValueError):
            return default
        return min(max(_min, value), _max.max)

    dc.int_input_raw = int_input_raw

    def str_input_raw(dialog: str) -> str | None:
        value = b.ask("text", dialog)
        if value is None:
            return None
        return str(value)

    dc.str_input_raw = str_input_raw

    def yes_no_raw(dialog: str) -> bool | None:
        value = b.ask("yesno", dialog)
        if value is None:
            return None
        return bool(value)

    dc.yes_no_raw = yes_no_raw

    def range_multi_input_raw(dialog: str, max: Any, min: int = 0) -> list[int] | None:
        value = b.ask("range", dialog, min=min, max=max.max)
        if value is None:
            return None
        value = str(value).strip()
        if value == "__all__" or value.lower() == core.localize("all").lower():
            return list(range(min, max.max))
        nums: list[int] = []
        for part in value.replace(",", " ").split():
            if part.isdigit():
                n = int(part)
                if min <= n <= max.max:
                    nums.append(n)
                else:
                    color.color_print_key("invalid_input_int", min=min, max=max.max)
            elif "-" in part:
                lo, hi = part.split("-", 1)
                if not lo.isdigit() or not hi.isdigit() or int(hi) < int(lo):
                    color.color_print_key("invalid_range", val=part)
                    continue
                lo_i, hi_i = int(lo), int(hi)
                if hi_i > max.max or lo_i < min:
                    color.color_print_key("invalid_input_int", min=min, max=max.max)
                    continue
                nums.extend(range(lo_i, hi_i + 1))
            else:
                color.color_print_key("invalid_range", val=part)
        return nums

    dc.range_multi_input_raw = range_multi_input_raw

    def max_clamp(value: int) -> int:
        return value if value >= 0 else 0

    def edit_int_raw(item_name: str, current_value: int, max: Any) -> int:
        value = b.ask("edit_int", "", name=_segs(item_name), current=current_value, max=max.max, show_max=bool(max.show))
        if value is None or value == "":
            value = current_value
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = current_value
        value = min(max_clamp(value), max.max)
        color.color_print_key("value_changed", name=item_name, value=value, escape=False)
        return value

    dc.edit_int_raw = edit_int_raw

    def edit_str_raw(item_name: str, current_value: str) -> str:
        value = b.ask("edit_str", "", name=_segs(item_name), current=current_value)
        value = str(value) if value else current_value
        color.color_print_key("value_changed", name=item_name, value=value)
        return value

    dc.edit_str_raw = edit_str_raw

    def edit_ints_raw(group_name: str, item_names: list[str], current_values: list[int], max: Any) -> list[int]:
        items = []
        total_max = None
        for index, (name, value) in enumerate(zip(item_names, current_values)):
            if isinstance(max, dc.MultiMax):
                item_max = max.get(index)
                item_max_v = item_max.max if item_max is not None else 0
            elif isinstance(max, dc.CumulativeMax):
                item_max_v = max.max.max
                total_max = max.max.max
            else:
                item_max_v = max.max
            items.append({"name": _segs(name), "value": value, "max": item_max_v})
        values = b.ask("edit_ints", group_name, items=items, total_max=total_max)
        if values is None:
            return current_values
        remaining = total_max
        for index, new_value in enumerate(values[: len(current_values)]):
            try:
                new_value = int(new_value)
            except (TypeError, ValueError):
                continue
            new_value = min(max_clamp(new_value), items[index]["max"])
            if remaining is not None:
                # CumulativeMax: the sum of all values cannot exceed the cap.
                new_value = min(new_value, remaining)
                remaining -= new_value
            if new_value != current_values[index]:
                current_values[index] = new_value
                color.color_print_key("value_changed", name=item_names[index], value=new_value, escape=False)
        return current_values

    dc.edit_ints_raw = edit_ints_raw

    # ---------------------------------------------------------- file dialogs
    def fd_init(self: Any) -> None:
        self.tk = True
        self.filedialog = True
        self.root = None

    def fd_get_file(self: Any, title: str, initialdir: str, initialfile: str, filetypes: Any = None, ignore_json: bool = False) -> str | None:
        title_text = textfmt.plain(core.core_data.local_manager.get_key(title))
        color.color_print_key(title)
        b.waiting_file_dialog = True
        try:
            return native_dialogs.open_file(title_text, initialdir, initialfile, filetypes)
        finally:
            b.waiting_file_dialog = False

    def fd_save_file(self: Any, title: str, initialdir: str, initialfile: str, filetypes: Any = None) -> str | None:
        title_text = textfmt.plain(core.core_data.local_manager.get_key(title))
        color.color_print_key(title)
        b.waiting_file_dialog = True
        try:
            return native_dialogs.save_file(title_text, initialdir, initialfile, filetypes)
        finally:
            b.waiting_file_dialog = False

    file_dialog.FileDialog.__init__ = fd_init  # type: ignore[method-assign]
    file_dialog.FileDialog.get_file = fd_get_file  # type: ignore[method-assign]
    file_dialog.FileDialog.save_file = fd_save_file  # type: ignore[method-assign]
    file_dialog.FileDialog.use_tk = lambda self: True  # type: ignore[method-assign]


def run_with_answers(answers: list[tuple[str, Any]], func: Callable[[], Any]) -> Any:
    """Runs ``func`` answering its first prompts automatically.

    ``answers`` is a list of (prompt kind, answer), e.g. ``[("text", "50+70")]``."""
    bridge.auto_answers = list(answers)
    try:
        return func()
    finally:
        bridge.auto_answers = []
