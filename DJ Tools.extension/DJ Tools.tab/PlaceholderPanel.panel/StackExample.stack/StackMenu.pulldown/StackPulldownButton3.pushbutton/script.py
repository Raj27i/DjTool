# -*- coding: utf-8 -*-
__title__ = "Stack Pulldown Button 3"
__doc__ = """Date    = 01.01.2023
_____________________________________________________________________
Description:
Examples of ISelectionFilter to limit Element Selection.
_____________________________________________________________________
Author: Erik Frits"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
#==================================================
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import Room, RoomTag
from Autodesk.Revit.UI.Selection import ObjectType, PickBoxStyle, Selection, ISelectionFilter

# .NET Imports
import clr
clr.AddReference("System")
from System.Collections.Generic import List

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
#==================================================
uidoc = __revit__.ActiveUIDocument
doc   = __revit__.ActiveUIDocument.Document

selection = uidoc.Selection # type: Selection

# ╔═╗╦  ╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝ CLASSES
#==================================================

# -*- coding: utf-8 -*-
"""Toggle Right Grid Bubbles"""
__title__ = "Right\nBubbles"

from pyrevit import revit, DB, forms

def get_grids_from_selection_or_view():
    """Get grids from selection or all grids in view"""
    selection = revit.get_selection()
    if selection.is_empty:
        doc = revit.doc
        active_view = revit.active_view
        collector = DB.FilteredElementCollector(doc, active_view.Id)
        return collector.OfClass(DB.Grid).ToElements()
    else:
        return [el for el in selection.elements if isinstance(el, DB.Grid)]

def determine_grid_direction(grid):
    """Determine grid direction based on coordinate sums"""
    curve = grid.Curve
    start_point = curve.GetEndPoint(0)
    end_point = curve.GetEndPoint(1)
    start_sum = start_point.X + start_point.Y
    end_sum = end_point.X + end_point.Y
    return start_sum > end_sum

def get_right_datum_end(grid):
    """Get the DatumEnd that represents the right side of the grid"""
    if determine_grid_direction(grid):
        return DB.DatumEnds.End1
    else:
        return DB.DatumEnds.End0

# Main execution
grids = get_grids_from_selection_or_view()

if not grids:
    forms.alert("No grids found in the active view.")
else:
    active_view = revit.active_view
    
    # Check current state of right bubbles
    bubble_states = []
    for grid in grids:
        right_end = get_right_datum_end(grid)
        is_visible = grid.IsBubbleVisibleInView(right_end, active_view)
        bubble_states.append(is_visible)
    
    # Determine action: if all are visible, hide them; otherwise show them
    all_visible = all(bubble_states)
    
    with revit.Transaction("Toggle Right Grid Bubbles"):
        for grid in grids:
            right_end = get_right_datum_end(grid)
            if all_visible:
                grid.HideBubbleInView(right_end, active_view)
            else:
                grid.ShowBubbleInView(right_end, active_view)
    
    action = "Hidden" if all_visible else "Shown"
    forms.alert("Right grid bubbles {} for {} grid(s).".format(action.lower(), len(grids)))




