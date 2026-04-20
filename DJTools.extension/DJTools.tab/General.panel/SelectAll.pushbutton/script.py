# -*- coding: utf-8 -*-
"""Select All Walls — selects every wall in the active view."""

__title__ = "Select\nAll Walls"
__author__ = "Raj27i"
__doc__ = "Selects all Wall instances in the current view."

from pyrevit import revit, DB, forms
from System.Collections.Generic import List

doc = revit.doc
uidoc = revit.uidoc
active_view = doc.ActiveView

# Collect all walls in the active view
walls = DB.FilteredElementCollector(doc, active_view) \
          .OfCategory(DB.BuiltInCategory.OST_Walls) \
          .WhereElementIsNotElementType() \
          .ToElements()

if not walls:
    forms.alert("No walls found in the active view.", title="DJTools")
else:
    ids = List[DB.ElementId]([w.Id for w in walls])
    uidoc.Selection.SetElementIds(ids)
    forms.alert(
        "Selected {} wall(s) in the active view.".format(len(walls)),
        title="DJTools"
    )
