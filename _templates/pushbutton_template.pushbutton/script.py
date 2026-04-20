# -*- coding: utf-8 -*-
"""One-line description shown as tooltip sub-text."""

# =========================================================================
# Metadata — shown by pyRevit in the ribbon/tooltip
# =========================================================================
__title__   = "Button\nTitle"          # use \n to wrap onto two lines
__author__  = "Raj27i"
__doc__     = "Longer description shown in the tooltip when hovering."
# __min_revit_ver__ = 2022              # uncomment to gate by Revit version
# __context__ = ['selection']           # uncomment to require a selection

# =========================================================================
# Imports
# =========================================================================
from pyrevit import revit, forms, script
from Autodesk.Revit.DB import FilteredElementCollector, Transaction

doc    = revit.doc
uidoc  = revit.uidoc
output = script.get_output()

# =========================================================================
# Main
# =========================================================================
def main():
    # TODO: write your logic here
    forms.alert("Replace me with real logic.", title=__title__.replace("\n", " "))


if __name__ == "__main__":
    main()
