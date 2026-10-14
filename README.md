# Battle Cats Save Editor (BCSFE GUI)

A visual interface, with menus and buttons, for
[BCSFE-Python](https://codeberg.org/fieryhenry/BCSFE-Python) 3.6 — fieryhenry's
save editor for The Battle Cats. Every BCSFE feature is available and runs
BCSFE's own code, so it behaves exactly like the console version, but each
question is shown as a dialog (buttons, checkboxes, number fields, the Windows
file picker…).

*Leer en español: [README.es.md](README.es.md)*

![Visual cat editor](docs/screenshot-cats.png)

| Home screen | BCSFE prompts as dialogs |
| --- | --- |
| ![Home screen](docs/screenshot-home.png) | ![BCSFE prompts as dialogs](docs/screenshot-dialog.png) |

## Features

- **Open your save**: download it with the transfer and confirmation codes,
  open a `SAVE_DATA` file, load the save from BCSFE's Documents folder, pull it
  from a phone with ADB or import it from JSON.
- **Overview**: Cat Food, XP, tickets, NP, leadership, Catseyes and battle items
  at a glance; click any of them to change it.
- **Visual cat editor**: every cat with its picture, search by name or ID
  (`25`, `100-120`), filters by rarity, form, target (red, floating, metal…),
  ability and immunity. Select several cats (click, Shift+click, Ctrl+A) and
  unlock them, change their level, give them their true or fourth form, max
  their talents, claim them in the Cat Guide… Double-click a cat to see its
  details.
- **All BCSFE features** grouped in the sidebar: save & sync, items, cats &
  skills, levels & maps, Gamatoto & Ototo, account, gacha, fixes, other and
  editor settings, plus a feature search box.
- **Save** (Ctrl+S), **Save as…** and **Save & upload**, which uploads the save
  to the game servers and shows the new codes to restore it on your phone
  (Data Transfer → Resume Data Transfer).
- **English or Spanish**: the interface and BCSFE's messages can be switched in
  *Editor settings → Language* (the Spanish translation of BCSFE's texts is
  bundled in `locales/es`).

## Requirements

- Windows 10/11 with Microsoft Edge (preinstalled). Without Edge or Chrome it
  opens in the default browser.
- Python 3.9 or newer.
- BCSFE 3.6.0 and its dependencies:

  ```
  py -m pip install -r requirements.txt
  ```

  The GUI relies on how BCSFE asks for input, so other BCSFE versions may not
  work. If a `BCSFE-Python-main` folder sits next to this one, that copy is
  used instead of the pip-installed package.

## Getting started

Double-click **`Start Editor.vbs`**. The editor opens in its own window (Edge
in app mode, without the browser bars) and stops when you close the window.

If something fails at start-up, run **`Start Editor (console).bat`**: it does
the same but keeps a console open with the error.

## Good to know

- Every save you open is copied as a backup to `Documents\bcsfe\saves\backups`.
- Editing Cat Food or Rare / Platinum / Legend tickets can get your account
  banned. Those options are tagged **Ban risk** and BCSFE warns you first.
  "Rare Ticket trade" and "Platinum Shards" are safer.
- "Cancel" in a dialog is the same as leaving that question in the console. If
  a BCSFE menu keeps coming back, the editor picks its exit option; you can
  also click **Stop task**.
- BCSFE's config (`Documents\bcsfe\config.yaml`), data and saves are shared
  with the console version. The GUI's own settings are stored in
  `%LOCALAPPDATA%\BCSFE_GUI\settings.json`.

## How it works

`bcsfe_gui` starts a small HTTP server bound to `127.0.0.1` (random port,
random token required on every API call) and opens the interface from `web/`
in an app window. BCSFE features run on a worker thread; the functions BCSFE
uses to read console input (`bcsfe.cli.dialog_creator`, `bcsfe.cli.color`,
the file dialogs) are replaced by versions that send the question to the
interface and wait for the answer.

| Path | Contents |
| --- | --- |
| `Start Editor.vbs` | Launcher without a console window |
| `BCSFE Editor.pyw` | Python entry point |
| `bcsfe_gui/` | Local server, BCSFE bridge and session logic |
| `web/` | The interface (HTML, CSS, JavaScript) and its images |
| `locales/es/` | Spanish translation of BCSFE's texts |

## Credits and license

- [BCSFE-Python](https://codeberg.org/fieryhenry/BCSFE-Python) by fieryhenry
  (GPL-3.0). This project is released under the same license, see
  [LICENSE](LICENSE).
- Cat, item and ability images, fonts and title art come from the
  *Battle Cats Save Editor GUI* project by Illusion137.
- The Battle Cats and its artwork belong to PONOS Corporation. This is an
  unofficial fan tool, not affiliated with or endorsed by PONOS. Use it at your
  own risk.
