"""State of the open save and the operations on it.

Everything that changes the save runs as a task (see jobs.py) and calls the
same functions the BCSFE console uses."""

from __future__ import annotations

import threading
from typing import Any, Callable

from bcsfe import core
from bcsfe.cli import color, edits, feature_handler, main as cli_main, server_cli
from bcsfe.cli.save_management import SaveManagement

from . import labels, settings, textfmt
from .bridge import run_with_answers
from .i18n import t


class SessionError(Exception):
    pass


def _feature_func_name(func: Any) -> str:
    return getattr(func, "__qualname__", "") or ""


class Session:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.save_file: core.SaveFile | None = None
        self.backup_path: core.Path | None = None
        self.fh: feature_handler.FeatureHandler | None = None
        self.baseline: bytes | None = None
        self.dirty = False
        self.cat_meta: dict[int, dict[str, Any]] | None = None
        self.version = 0  # bumped every time the save changes

    # -------------------------------------------------------------- helpers
    def require_save(self) -> core.SaveFile:
        if self.save_file is None:
            raise SessionError(t("no_save_open"))
        return self.save_file

    def _bump(self) -> None:
        self.version += 1

    def _set_save(self, save_file: core.SaveFile, backup_path: core.Path | None) -> None:
        with self.lock:
            core.core_data.init_data()
            self.save_file = save_file
            self.backup_path = backup_path
            self.fh = feature_handler.FeatureHandler(save_file)
            # Same steps the console runs when a save is opened. The temp copy
            # is written here and not on another thread: serialising the save
            # from two threads at once is not safe.
            self._write_temp(save_file.to_data())
            edits.clear_tutorial.clear_tutorial(save_file, False)
            save_file.show_ban_message = False
            self.baseline = save_file.to_data().to_bytes()
            self.dirty = False
            self.cat_meta = None
            self._bump()
        color.color_print_key(
            "current_save",
            inquiry_code=self.masked_inquiry(),
            gv=save_file.game_version,
            cc=save_file.cc,
        )

    def masked_inquiry(self) -> str:
        sf = self.save_file
        if sf is None or not getattr(sf, "inquiry_code", ""):
            return ""
        code = sf.inquiry_code
        return code[:4] + "***" + code[-2:]

    def language_changed(self) -> None:
        with self.lock:
            if self.save_file is not None:
                self.cat_meta = None
            self._bump()

    def close(self) -> None:
        with self.lock:
            self.save_file = None
            self.backup_path = None
            self.fh = None
            self.baseline = None
            self.dirty = False
            self.cat_meta = None
            self._bump()

    @staticmethod
    def _write_temp(data: core.Data) -> None:
        try:
            data.to_file(core.SaveFile.get_temp_path())
        except Exception as exc:  # noqa: BLE001 - the temp copy is not critical
            print(exc)

    def update_dirty(self, current: bytes | None = None) -> None:
        sf = self.save_file
        if sf is None:
            return
        if current is None:
            try:
                current = sf.to_data().to_bytes()
            except Exception:
                self.dirty = True
                self._bump()
                return
        on_disk = None
        try:
            if sf.save_path is not None and sf.save_path.exists():
                on_disk = sf.save_path.read().to_bytes()
        except Exception:
            on_disk = None
        self.dirty = current != self.baseline and current != on_disk
        self._bump()

    def after_edit(self) -> None:
        """Steps the console runs after every feature."""
        sf = self.save_file
        if sf is None:
            return
        core.core_data.game_data_getter = None
        try:
            data = sf.to_data()
        except Exception:
            self.dirty = True
            self._bump()
            raise
        self._write_temp(data)
        self.update_dirty(data.to_bytes())

    # --------------------------------------------------------- loading a save
    def _load_result(self, result: tuple[core.SaveFile, core.Path] | None) -> bool:
        if result is None:
            color.color_print(f"<@w>{t('no_save_loaded')}</>")
            return False
        save_file, backup_path = result
        self._set_save(save_file, backup_path)
        return True

    def load_from_file_dialog(self) -> bool:
        path = cli_main.Main.load_save_file()
        if path is None:
            color.color_print(f"<@w>{t('no_file_selected')}</>")
            return False
        return self._load_result(SaveManagement.load_save_file_path(path))

    def load_from_path(self, path: str) -> bool:
        p = core.Path(path)
        if not p.exists():
            raise SessionError(t("file_not_found", path=path))
        return self._load_result(SaveManagement.load_save_file_path(p))

    def load_from_documents(self) -> bool:
        path = core.SaveFile.get_save_path()
        if not path.exists():
            raise SessionError(t("no_documents_save"))
        return self._load_result(SaveManagement.load_save_file_path(path))

    def load_from_json(self) -> bool:
        res = cli_main.Main.load_save_data_json()
        if res is None:
            color.color_print(f"<@w>{t('no_json_loaded')}</>")
            return False
        path, cc = res
        return self._load_result(SaveManagement.load_save_file_path(path, cc))

    def load_from_adb(self) -> bool:
        return self._load_result(SaveManagement.pull_adb())

    def load_from_codes(self, transfer_code: str, confirmation_code: str, cc: str) -> bool:
        codes = core.CountryCode.get_all_str()
        if cc not in codes:
            raise SessionError(t("invalid_region", cc=cc))
        answers = [("text", transfer_code.strip()), ("text", confirmation_code.strip()), ("select", codes.index(cc))]
        res = run_with_answers(answers, lambda: server_cli.ServerCLI().download_save())
        if res is None:
            color.color_print(f"<@e>{t('download_failed')}</>")
            return False
        path, country = res
        return self._load_result(SaveManagement.load_save_file_path(path, country))

    # -------------------------------------------------------------- features
    def menu(self) -> list[dict[str, Any]]:
        fh = self.fh
        if fh is None:
            raise SessionError(t("no_save_open"))
        result: list[dict[str, Any]] = []
        for cat_key, content in fh.get_features().items():
            if cat_key in labels.HIDDEN_FEATURES or not isinstance(content, dict):
                continue
            info = labels.category(cat_key)
            items = [self._feature_info(cat_key, feat_key, func) for feat_key, func in content.items()]
            result.append(
                {
                    "key": cat_key,
                    "label": info[1] if info else textfmt.plain(core.core_data.local_manager.get_key(cat_key)),
                    "desc": info[2] if info else "",
                    "icon": info[0] if info else "dots",
                    "features": items,
                }
            )
        return result

    def _feature_info(self, cat_key: str, feat_key: str, func: Any) -> dict[str, Any]:
        lookup = labels.FEATURES_BY_FUNCTION.get(_feature_func_name(func), feat_key)
        info = labels.feature(lookup)
        # BCSFE's own name, shown as a hint (it matches the Spanish translation,
        # so it is only useful when the interface is in English).
        original = ""
        if feat_key and settings.current["language"] != "es":
            original = textfmt.plain(core.core_data.local_manager.get_all_aliases(core.localize(feat_key))[0])
        if info is None:
            return {"path": [cat_key, feat_key], "label": original or feat_key, "desc": "", "icon": "dots", "flag": "", "original": original}
        icon, flag, name, desc = info
        return {"path": [cat_key, feat_key], "label": name, "desc": desc, "icon": icon, "flag": flag, "original": original}

    def feature_title(self, path: list[str]) -> str:
        fh = self.fh
        if fh is None:
            return t("feature")
        try:
            func = fh.get_feature(path)
        except (KeyError, TypeError):
            return t("feature")
        return self._feature_info(path[0], path[-1], func)["label"]

    def run_feature(self, path: list[str]) -> None:
        sf = self.require_save()
        fh = self.fh
        assert fh is not None
        try:
            func = fh.get_feature(path)
        except (KeyError, TypeError) as exc:
            raise SessionError(t("unknown_feature", path=" / ".join(path))) from exc
        if not callable(func):
            raise SessionError(t("not_a_feature"))
        fh.do_save_actions()
        try:
            func(sf)
            if path[-1] in ("load_save", "convert_region", "convert_version"):
                # These replace the whole save, so it becomes the new baseline.
                self.fh = feature_handler.FeatureHandler(sf)
                self.cat_meta = None
                self.baseline = sf.to_data().to_bytes()
        finally:
            # Even if the feature fails or is stopped it may have changed something.
            self.after_edit()

    def run_editor_option(self, option: str) -> None:
        if option == "config":
            core.core_data.config.edit_config()
        elif option == "update_external":
            core.update_external_content()
        elif option == "manage_game_data":
            core.manage_game_data()
        else:
            raise SessionError(t("unknown_option"))

    # -------------------------------------------------------------- overview
    def overview(self) -> dict[str, Any]:
        sf = self.require_save()

        def val(attr: str) -> Any:
            v = getattr(sf, attr, None)
            return v if isinstance(v, int) else None

        resources = [
            ("catfood", "item:CatFood", ["items", "catfood"], "ban"),
            ("xp", "xp", ["items", "xp"], ""),
            ("normal_tickets", "ticket", ["items", "normal_tickets"], ""),
            ("rare_tickets", "ticket-rare", ["items", "rare_tickets"], "ban"),
            ("platinum_tickets", "ticket-plat", ["items", "platinum_tickets"], "ban"),
            ("legend_tickets", "ticket-legend", ["items", "legend_tickets"], "ban"),
            ("platinum_shards", "gem", ["items", "platinum_shards"], ""),
            ("np", "np", ["items", "np"], ""),
            ("leadership", "flag", ["items", "leadership"], ""),
        ]
        battle_items: list[int] = []
        try:
            battle_items = [int(item.amount) for item in sf.battle_items.items]
        except Exception:
            pass
        catseyes = [int(v) for v in (getattr(sf, "catseyes", None) or [])]
        cats = sf.cats.cats
        return {
            "resources": [
                {"key": key, "label": t("res_" + key), "icon": icon, "value": val(key), "feature": feat, "flag": flag}
                for key, icon, feat, flag in resources
                if val(key) is not None
            ],
            "battle_items": battle_items,
            "catseyes": catseyes,
            "cats_total": len(cats),
            "cats_unlocked": sum(1 for c in cats if c.unlocked),
            "cats_true_form": sum(1 for c in cats if c.unlocked and c.unlocked_forms >= 3),
        }

    def info(self) -> dict[str, Any] | None:
        sf = self.save_file
        if sf is None:
            return None
        return {
            "cc": sf.cc.get_code(),
            "gv": sf.game_version.to_string(),
            "inquiry": self.masked_inquiry(),
            "path": sf.save_path.to_str() if sf.save_path is not None else None,
            "backup": self.backup_path.to_str() if self.backup_path is not None else None,
            "dirty": self.dirty,
            "version": self.version,
        }

    # ------------------------------------------------------------------ cats
    def cats_state(self) -> dict[str, Any]:
        sf = self.require_save()
        cats = []
        for cat in sf.cats.cats:
            talents = cat.talents or []
            cats.append(
                [
                    cat.id,
                    1 if cat.unlocked else 0,
                    cat.upgrade.base + 1,
                    cat.upgrade.plus,
                    cat.current_form,
                    cat.unlocked_forms,
                    cat.fourth_form,
                    1 if cat.catguide_collected else 0,
                    len(talents),
                    sum(talent.level for talent in talents),
                ]
            )
        return {"cats": cats, "meta": self.cat_meta, "version": self.version}

    def load_cat_meta(self) -> None:
        """Reads names, rarity and number of forms from the game data (which
        may be downloaded the first time)."""
        sf = self.require_save()
        color.color_print(f"<@t>{t('loading_cats')}</>")
        meta: dict[int, dict[str, Any]] = {}
        try:
            unit_buy = sf.cats.read_unitbuy(sf)
        except Exception:
            unit_buy = None
        try:
            pic_book = sf.cats.read_nyanko_picture_book(sf)
        except Exception:
            pic_book = None
        total = len(sf.cats.cats)
        for cat in sf.cats.cats:
            entry: dict[str, Any] = {}
            try:
                names = cat.get_names_cls(sf)
                if names:
                    entry["n"] = [textfmt.plain(x) for x in names if x]
            except Exception:
                pass
            if unit_buy is not None:
                try:
                    entry["r"] = unit_buy.get_cat_rarity(cat.id)
                except Exception:
                    pass
            if pic_book is not None:
                try:
                    pb = pic_book.get_cat(cat.id)
                    if pb is not None:
                        entry["f"] = pb.total_forms
                        entry["o"] = 1 if pb.is_displayed_in_catguide else 0
                except Exception:
                    pass
            meta[cat.id] = entry
        try:
            rarity_names = type(sf.cats).get_rarity_names(sf)
        except Exception:
            rarity_names = []
        meta[-1] = {"rarity_names": [textfmt.plain(x) for x in rarity_names]}
        self.cat_meta = meta
        self._bump()
        color.color_print(f"<@su>{t('cats_loaded', total=total)}</>")

    def cat_action(self, action: str, ids: list[int], params: dict[str, Any]) -> None:
        sf = self.require_save()
        editor = edits.cat_editor.CatEditor(sf)
        wanted = set(int(i) for i in ids)
        cats = [cat for cat in sf.cats.cats if cat.id in wanted]
        if not cats:
            raise SessionError(t("no_cats_selected"))
        force = bool(params.get("force"))
        actions: dict[str, Callable[[], Any]] = {
            "unlock": lambda: editor.unlock_cats(cats),
            "remove": lambda: editor.remove_cats(cats),
            "true_form": lambda: editor.true_form_cats(cats, force=force),
            "remove_true_form": lambda: editor.remove_true_form_cats(cats),
            "fourth_form": lambda: editor.fourth_form_cats(cats, force=force),
            "remove_fourth_form": lambda: editor.remove_fourth_form_cats(cats),
            "upgrade": lambda: self._upgrade(editor, cats, params),
            "talents_max": lambda: self._talents_max(editor, cats),
            "talents_edit": lambda: editor.edit_talent_individual(cats),
            "talents_remove": lambda: editor.remove_talents_cats(cats),
            "guide_unlock": lambda: editor.unlock_cat_guide(cats),
            "guide_remove": lambda: editor.remove_cat_guide(cats),
        }
        if action not in actions:
            raise SessionError(t("unknown_action", action=action))
        color.color_print(t("cats_selected", count=len(cats)))
        try:
            actions[action]()
            edits.cat_editor.CatEditor.set_rank_up_sale(sf)
        finally:
            self.after_edit()

    @staticmethod
    def _level_part(value: Any) -> str:
        if value in (None, "", "keep"):
            return ""
        if value == "max":
            return core.core_data.local_manager.get_key("max")
        return str(max(0, int(value)))

    def _upgrade(self, editor: Any, cats: list[core.Cat], params: dict[str, Any]) -> None:
        base = self._level_part(params.get("base"))
        plus = self._level_part(params.get("plus"))
        if not base and not plus:
            color.color_print(f"<@w>{t('no_level_change')}</>")
            return
        # Same text a console user would type, e.g. "50+70" or "max+".
        text = f"{base}+{plus}"
        if len(cats) == 1:
            ok = run_with_answers([("text", text)], lambda: editor.upgrade_individual(cats))
        else:
            ok = run_with_answers([("text", text)], lambda: editor.upgrade_many(cats))
        if ok:
            color.color_print_key("upgrade_success")

    def _talents_max(self, editor: Any, cats: list[core.Cat]) -> None:
        sf = self.require_save()
        gdg = core.core_data.get_game_data_getter(sf)
        if not gdg.does_save_version_match(sf):
            data_version = gdg.version
            if data_version is None:
                color.color_print_key("no_data_version")
                return
            color.color_print_key(
                "talents_version_warning",
                save_version=sf.game_version.to_string(),
                data_version=data_version,
            )
            from bcsfe.cli import dialog_creator

            if not dialog_creator.yes_no_key("continue_q"):
                return
        editor.edit_talent_many(cats)
        color.color_print_key("talents_success")


session = Session()
