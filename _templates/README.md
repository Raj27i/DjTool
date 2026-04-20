# DJTools — Templates

Copy-ready scaffolding for adding new buttons/panels. This folder lives **outside** `DJTools.extension/`, so pyRevit ignores it at load time.

## How to add a new button

1. Pick a template folder (`pushbutton_template.pushbutton`, `pushbutton_with_transaction.pushbutton`, `urlbutton_template.urlbutton`, or `pulldown_template.pulldown`).
2. Copy it into the target panel, e.g.:
   `DJTools.extension/DJTools.tab/MEP.panel/MyNewTool.pushbutton/`
3. Rename the folder — the suffix (`.pushbutton`, `.pulldown`, `.urlbutton`, `.panel`) **must** stay.
4. Edit `script.py`:
   - `__title__` — ribbon label (use `\n` to wrap 2 lines).
   - `__doc__` — tooltip text.
5. Replace `icon.png` with a 32×32 PNG (or copy one from an existing button).
6. Reload pyRevit in Revit: **pyRevit tab → Reload**.

## How to add a new panel

1. Create a folder inside the `.tab/` directory:
   `DJTools.extension/DJTools.tab/NewPanel.panel/`
2. Add at least one `.pushbutton` folder inside it (panels cannot be empty).

## Folder suffixes (pyRevit rules)

| Suffix | Purpose |
|---|---|
| `.extension` | The extension root |
| `.tab` | A Revit ribbon tab |
| `.panel` | A panel within a tab |
| `.pushbutton` | A clickable button |
| `.pulldown` | Dropdown menu of buttons |
| `.stack` | Vertical stack of 2–3 items |
| `.urlbutton` | Button that opens a URL |

## Required files in a `.pushbutton`

- `script.py` — Python 3 (IronPython) code.
- `icon.png` — 32×32 icon.
- `bundle.yaml` — *optional*, can set title/tooltip instead of `__title__`.
