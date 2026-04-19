# -*- coding: utf-8 -*-
__title__   = "Filled Regions"
__doc__     = """Version = 2.0
Date    = 30.09.2024
________________________________________________________________
Description:

Use this to quickly visualize room boundaries or create filled Regions for plans and diagrams.
This version shows only rooms visible in the current view, for both current and linked models.

________________________________________________________________
TODO:
1. Open the desired floor plan view in Revit.
2. Click this button to run the script.
3. Select a model (current or linked).
4. Select visible rooms from the list that appears.
5. Select a filled region type.
6. The script will create filled regions for selected rooms visible in the current view.
________________________________________________________________
Last Updates:
- [30.09.2024] v2.0 Updated room visibility check for both current and linked models
________________________________________________________________
Author: Durai"""

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import revit, DB, UI
from pyrevit import script
from pyrevit import forms

import clr
clr.AddReference('System')
from System.Collections.Generic import List

app = __revit__.Application
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
activeView  =doc.ActiveView

def create_filled_region_for_room(room, view, filled_region_type, transform=None):
    boundary_options = SpatialElementBoundaryOptions()
    boundary_segments = room.GetBoundarySegments(boundary_options)
    
    if not boundary_segments:
        return False
    
    curve_loop = CurveLoop()
    for segment in boundary_segments[0]:
        curve = segment.GetCurve()
        if transform:
            curve = curve.CreateTransformed(transform)
        curve_loop.Append(curve)
    
    try:
        FilledRegion.Create(doc, filled_region_type.Id, view.Id, List[CurveLoop]([curve_loop]))
        return True
    except:
        return False

def get_filled_region_types():
    return FilteredElementCollector(doc).OfClass(FilledRegionType).ToElements()

def get_linked_models():
    return FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements()





from pyrevit import forms
from System.Collections.Generic import List

def get_visible_rooms_in_current_model(view, doc):
    """
    Collects all rooms visible in the active view from the current model.
    """
    return FilteredElementCollector(doc, view.Id) \
        .OfCategory(BuiltInCategory.OST_Rooms) \
        .WhereElementIsNotElementType() \
        .ToElements()

def get_level_in_current_doc(doc, level_name):
    """
    Find a level in the current document that matches the given level name.
    """
    levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
    for level in levels:
        if level.Name == level_name:
            return level
    return None


def get_visible_rooms_in_linked_model(view, linked_model):
    """
    Collects all rooms from the linked model, maps levels to the current model,
    creates spaces for them, filters spaces visible in the active view, and deletes the spaces.
    """
    linked_doc = linked_model.GetLinkDocument()
    if not linked_doc:
        return []

    # Collect all rooms from the linked model
    linked_rooms = FilteredElementCollector(linked_doc) \
        .OfCategory(BuiltInCategory.OST_Rooms) \
        .WhereElementIsNotElementType() \
        .ToElements()

    if not linked_rooms:
        return []

    # Create spaces for the rooms
    created_spaces = []
    transform = linked_model.GetTotalTransform()
    transaction = Transaction(doc, "Create Spaces for Linked Rooms")
    transaction.Start()  # Start the transaction for creating spaces
    try:
        for room in linked_rooms:
            # Only process rooms with a valid level
            if room.Level is None:
                continue

            # Map the linked model level to the current document
            level_name = room.Level.Name
            current_model_level = get_level_in_current_doc(doc, level_name)
            if not current_model_level:
                continue  # Skip rooms with no corresponding level in the current model

            # Get room location and transform to host coordinates if needed
            if room.Location is None:
                continue
            location = room.Location.Point
            if transform:
                location = transform.OfPoint(location)

            # Convert XYZ to UV (using X and Y only)
            uv_location = UV(location.X, location.Y)

            # Create space in the current model
            space = doc.Create.NewSpace(current_model_level, uv_location)

            # Set room parameters on the new space
            space.LookupParameter("Name").Set(room.LookupParameter("Name").AsString())
            space.LookupParameter("Number").Set(room.LookupParameter("Number").AsString())
            phase = room.LookupParameter("Phase").AsValueString()
            if space.LookupParameter("Comments4_CW"):
                space.LookupParameter("Comments4_CW").Set(phase)

            created_spaces.append(space)
    except Exception as e:
        transaction.RollBack()
        forms.alert("Error while creating spaces: " + str(e), title="Error")
        return []
    transaction.Commit()  # Commit the transaction after creating spaces

    # Filter spaces visible in the active view
    visible_spaces = []
    view_bbox = view.get_BoundingBox(None)
    outline = Outline(view_bbox.Min, view_bbox.Max)
    bounding_box_filter = BoundingBoxIntersectsFilter(outline)

    for space in created_spaces:
        if bounding_box_filter.PassesFilter(space):
            visible_spaces.append(space)

    # Delete spaces after use
    transaction = Transaction(doc, "Delete Temporary Spaces")
    transaction.Start()
    try:
        for space in created_spaces:
            doc.Delete(space.Id)
    except Exception as e:
        transaction.RollBack()
        forms.alert("Error while deleting spaces: " + str(e), title="Error")
    transaction.Commit()

    return visible_spaces


def main():
    active_view = doc.ActiveView
    if not isinstance(active_view, ViewPlan):
        forms.alert("Please run this script in a plan view.", title="Invalid View")
        return

    # User selects current model or linked model
    linked_models = get_linked_models()
    model_options = ["Current Model"] + [link.Name for link in linked_models]
    selected_model_name = forms.SelectFromList.show(
        model_options,
        title="Select Model",
        multiselect=False
    )
    if not selected_model_name:
        forms.alert("No model selected. Exiting.", title="No Selection")
        return

    # Handle current model rooms
    if selected_model_name == "Current Model":
        rooms = get_visible_rooms_in_current_model(active_view, doc)

    # Handle linked model rooms
    else:
        linked_model = next((link for link in linked_models if link.Name == selected_model_name), None)
        if not linked_model:
            forms.alert("Selected linked model not found.", title="Error")
            return
        rooms = get_visible_rooms_in_linked_model(active_view, linked_model)

    # Validate room selection
    if not rooms:
        forms.alert("No visible rooms found in the selected model.", title="No Visible Rooms")
        return

    # Let the user select from visible rooms
    room_options = ["{0}: {1}".format(room.Number, room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()) for room in rooms]
    selected_rooms = forms.SelectFromList.show(
        room_options,
        title="Select Visible Rooms",
        multiselect=True
    )
    if not selected_rooms:
        return

    # Get selected room objects
    selected_room_objects = [room for room in rooms if "{0}: {1}".format(room.Number, room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()) in selected_rooms]

    # Get filled region types
    filled_region_types = list(get_filled_region_types())
    if not filled_region_types:
        forms.alert("No filled region types found in the project.", title="No Filled Region Types")
        return

    # Let user select filled region type
    filled_region_type_names = [type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() for type in filled_region_types]
    selected_type_name = forms.SelectFromList.show(
        filled_region_type_names,
        title="Select Filled Region Type",
        multiselect=False
    )
    if not selected_type_name:
        return

    selected_type = next((type for type in filled_region_types if type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == selected_type_name), None)
    if not selected_type:
        forms.alert("Selected type not found.", title="Error")
        return

    # Create filled regions for selected rooms
    success_count = 0
    with Transaction(doc, "Create Filled Regions"):
        try:
            for room in selected_room_objects:
                boundary_options = SpatialElementBoundaryOptions()
                boundary_segments = room.GetBoundarySegments(boundary_options)
                if not boundary_segments:
                    continue

                curve_loop = CurveLoop()
                for segment in boundary_segments[0]:
                    curve_loop.Append(segment.GetCurve())

                FilledRegion.Create(doc, selected_type.Id, active_view.Id, List[CurveLoop]([curve_loop]))
                success_count += 1
        except Exception as e:
            forms.alert("Error while creating filled regions: " + str(e), title="Error")
            return

    forms.alert("Successfully created filled regions for {0} rooms!".format(success_count), title="Success")

if __name__ == "__main__":
    main()
