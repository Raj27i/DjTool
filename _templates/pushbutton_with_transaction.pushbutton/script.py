# -*- coding: utf-8 -*-
"""Template for a button that modifies the Revit model (needs a Transaction)."""

__title__  = "Transaction\nExample"
__author__ = "Raj27i"
__doc__    = "Template button that wraps model changes in a Transaction."

from pyrevit import revit, forms, script
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Transaction,
    BuiltInCategory,
)

doc    = revit.doc
uidoc  = revit.uidoc
output = script.get_output()


def main():
    # Example: collect all walls in the active view
    walls = (
        FilteredElementCollector(doc, doc.ActiveView.Id)
        .OfCategory(BuiltInCategory.OST_Walls)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    if not walls:
        forms.alert("No walls found in the active view.")
        return

    # Wrap any model change in a Transaction
    t = Transaction(doc, __title__.replace("\n", " "))
    t.Start()
    try:
        for w in walls:
            # TODO: do something with each element
            pass
        t.Commit()
        forms.alert("Processed {} walls.".format(len(walls)))
    except Exception as ex:
        t.RollBack()
        output.print_md("**Error:** {}".format(ex))
        raise


if __name__ == "__main__":
    main()
