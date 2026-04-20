# DJTools

A custom pyRevit extension with tools for Revit.

## Install

From a Windows command prompt / PowerShell:

```
pyrevit extend ui DJTools https://github.com/Raj27i/DjTool.git
```

Then restart Revit. A **DJTools** tab will appear in the ribbon.

## Structure

```
DJTools.extension/
└── DJTools.tab/
    └── General.panel/
        ├── HelloWorld.pushbutton/   # Shows a hello message
        └── SelectAll.pushbutton/    # Selects all walls in active view
```

## Add more buttons

Create a new folder ending in `.pushbutton` inside `General.panel/`, then
put a `script.py` and optionally an `icon.png` inside it. Restart Revit.
