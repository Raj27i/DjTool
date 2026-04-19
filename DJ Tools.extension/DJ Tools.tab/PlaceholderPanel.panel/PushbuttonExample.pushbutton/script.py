# -*- coding: utf-8 -*- 
__title__   = "Get Linked Rooms"
__doc__     = """Version = 1.0
Date    = 11.12.2024
________________________________________________________________
Description:
    Gets rooms from linked Revit files that are visible in active view
    and creates filled regions.
________________________________________________________________
Author: Claude"""

from Autodesk.Revit.DB import *
from pyrevit import forms
from System.Collections.Generic import List

# Document variables
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = doc.ActiveView

def get_linked_files():
    """Get all linked Revit files in the current document"""
    return FilteredElementCollector(doc)\
            .OfClass(RevitLinkInstance)\
            .ToElements()

def get_filled_region_types():
    """Get all filled region types in project"""
    return FilteredElementCollector(doc)\
            .OfClass(FilledRegionType)\
            .ToElements()

def get_visible_rooms_from_link(link_instance):
    """Get rooms from link that are visible in active view"""
    # Get link document and transform
    link_doc = link_instance.GetLinkDocument()
    transform = link_instance.GetTotalTransform()
    
    # Get view range data
    view_range = active_view.GetViewRange()
    
    # Get top clip plane info
    top_clip_id = view_range.GetLevelId(PlanViewPlane.TopClipPlane)
    top_clip = doc.GetElement(top_clip_id)
    top_offset = view_range.GetOffset(PlanViewPlane.TopClipPlane)
    
    # Get bottom clip plane info
    bottom_clip_id = view_range.GetLevelId(PlanViewPlane.BottomClipPlane)
    bottom_clip = doc.GetElement(bottom_clip_id)
    bottom_offset = view_range.GetOffset(PlanViewPlane.BottomClipPlane)
    
    # Get crop box and adjust for view range
    crop_box = active_view.CropBox
    min_point = XYZ(crop_box.Min.X, crop_box.Min.Y, bottom_clip.Elevation + bottom_offset)
    max_point = XYZ(crop_box.Max.X, crop_box.Max.Y, top_clip.Elevation + top_offset)
    
    outline = Outline(min_point, max_point)
    
    # Create filters
    inside_filter = BoundingBoxIsInsideFilter(outline)
    intersect_filter = BoundingBoxIntersectsFilter(outline)
    combined_filter = LogicalOrFilter(inside_filter, intersect_filter)
    
    # Get rooms using filter
    rooms = FilteredElementCollector(link_doc)\
            .OfCategory(BuiltInCategory.OST_Rooms)\
            .WherePasses(combined_filter)\
            .ToElements()
            
    return rooms, transform

def create_filled_region(room, transform, filled_region_type_id):
    """Create filled region from room boundary"""
    try:
        # Get room boundary
        room_boundary_options = SpatialElementBoundaryOptions()
        boundary_segs = room.GetBoundarySegments(room_boundary_options)
        
        if not boundary_segs:
            print("No boundary segments found for room")
            return None
            
        # Create CurveLoop from boundary
        curve_loops = []
        for boundary in boundary_segs:
            curve_loop = CurveLoop()
            for segment in boundary:
                curve = segment.GetCurve()
                # Transform curve to host model coordinates
                transformed_curve = curve.CreateTransformed(transform)
                curve_loop.Append(transformed_curve)
            curve_loops.append(curve_loop)
        
        # Create filled region
        filled_region = FilledRegion.Create(doc, filled_region_type_id, active_view.Id, List[CurveLoop](curve_loops))
        return filled_region
        
    except Exception as e:
        print("Error creating filled region: {}".format(str(e)))
        return None

def main():
    # Check if we're in a plan view
    if not isinstance(active_view, ViewPlan):
        forms.alert("Please run this script in a plan view.", title="Invalid View")
        return

    # Get linked models
    linked_models = get_linked_files()
    
    # Create selection options for models
    model_options = ["Current Model"] + [Element.Name.GetValue(link) for link in linked_models]
    
    # Let user select model
    selected_model = forms.SelectFromList.show(
        model_options,
        title="Select Model",
        multiselect=False
    )
    
    if not selected_model:
        forms.alert("No model selected. Exiting.", title="No Selection")
        return

    # Get filled region types
    filled_region_types = list(get_filled_region_types())
    if not filled_region_types:
        forms.alert("No filled region types found in the project.", title="No Filled Region Types")
        return

    # Let user select filled region type
    filled_region_type_names = [type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() 
                               for type in filled_region_types]
    
    selected_type_name = forms.SelectFromList.show(
        filled_region_type_names,
        title="Select Filled Region Type",
        multiselect=False
    )
    
    if not selected_type_name:
        return

    selected_type = next(
        (type for type in filled_region_types 
         if type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString() == selected_type_name),
        None
    )

    if not selected_type:
        forms.alert("Selected type not found.", title="Error")
        return

    # Process rooms based on selected model
    if selected_model == "Current Model":
        # Handle current model rooms (if needed)
        forms.alert("Current model selection not implemented yet.", title="Not Implemented")
        return
    else:
        # Get the selected link instance
        selected_link = next(
            (link for link in linked_models 
             if Element.Name.GetValue(link) == selected_model),
            None
        )
        
        if not selected_link:
            forms.alert("Selected linked model not found.", title="Error")
            return
            
        try:
            # Get rooms from selected link
            rooms, transform = get_visible_rooms_from_link(selected_link)
            
            if not rooms:
                forms.alert("No rooms found in selected model.", title="No Rooms")
                return
                
            # Create selection options for rooms
            room_options = [
                "{}: {}".format(
                    room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString(),
                    room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
                )
                for room in rooms
            ]
            
            # Let user select rooms
            selected_rooms = forms.SelectFromList.show(
                room_options,
                title="Select Rooms",
                multiselect=True
            )
            
            if not selected_rooms:
                return
                
            # Create filled regions for selected rooms
            success_count = 0
            with Transaction(doc, "Create Filled Regions") as t:
                t.Start()
                try:
                    for i, room_name in enumerate(selected_rooms):
                        room = rooms[room_options.index(room_name)]
                        if create_filled_region(room, transform, selected_type.Id):
                            success_count += 1
                except Exception as e:
                    forms.alert("Error creating filled regions: " + str(e), title="Error")
                t.Commit()
                
            forms.alert(
                "Successfully created {} filled regions!".format(success_count),
                title="Success"
            )
                
        except Exception as e:
            forms.alert("Error processing rooms: " + str(e), title="Error")

if __name__ == '__main__':
    main()