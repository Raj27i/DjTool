# -*- coding: utf-8 -*-
"""Grid Bubble Controller"""
__title__ = "Grid\nBubbles"

from pyrevit import revit, DB, forms

def get_all_views():
    """Get all available views in the document"""
    doc = revit.doc
    collector = DB.FilteredElementCollector(doc)
    views = collector.OfClass(DB.View).ToElements()
    
    valid_views = []
    for view in views:
        if (isinstance(view, DB.ViewPlan) and
            not view.IsTemplate and view.CanBePrinted):
            valid_views.append(view)
        elif (hasattr(view, 'ViewType') and 
              view.ViewType == DB.ViewType.Elevation and
              not view.IsTemplate and view.CanBePrinted):
            valid_views.append(view)
    
    return valid_views

def get_all_grids_from_view(view):
    """Collect all grid elements from the specified view"""
    doc = revit.doc
    collector = DB.FilteredElementCollector(doc, view.Id)
    return collector.OfClass(DB.Grid).ToElements()

def determine_grid_orientation(grid):
    """Determine if grid is horizontal or vertical based on direction vector"""
    try:
        curve = grid.Curve
        if curve:
            start = curve.GetEndPoint(0)
            end = curve.GetEndPoint(1)
            direction = end - start
            
            if abs(direction.X) > abs(direction.Y):
                return "horizontal"
            else:
                return "vertical"
    except:
        pass
    return None

def get_horizontal_ends(grid):
    """Get left/right datum ends for horizontal grid"""
    try:
        curve = grid.Curve
        if curve:
            start_point = curve.GetEndPoint(0)
            end_point = curve.GetEndPoint(1)
            
            if start_point.X < end_point.X:
                return {"left": DB.DatumEnds.End0, "right": DB.DatumEnds.End1}
            else:
                return {"left": DB.DatumEnds.End1, "right": DB.DatumEnds.End0}
    except:
        pass
    return None

def get_vertical_ends(grid):
    """Get top/bottom datum ends for vertical grid"""
    try:
        curve = grid.Curve
        if curve:
            start_point = curve.GetEndPoint(0)
            end_point = curve.GetEndPoint(1)
            
            if start_point.Y > end_point.Y:
                return {"top": DB.DatumEnds.End0, "bottom": DB.DatumEnds.End1}
            else:
                return {"top": DB.DatumEnds.End1, "bottom": DB.DatumEnds.End0}
    except:
        pass
    return None

def apply_horizontal_bubble(grid, selected_sides, view):
    """Apply bubble settings to horizontal grid only"""
    ends = get_horizontal_ends(grid)
    if not ends:
        return False
    
    # Turn OFF both sides first
    grid.HideBubbleInView(ends["left"], view)
    grid.HideBubbleInView(ends["right"], view)
    
    # Turn ON selected sides only
    if "left" in selected_sides:
        grid.ShowBubbleInView(ends["left"], view)
    if "right" in selected_sides:
        grid.ShowBubbleInView(ends["right"], view)
    
    return True

def apply_vertical_bubble(grid, selected_sides, view):
    """Apply bubble settings to vertical grid only"""
    ends = get_vertical_ends(grid)
    if not ends:
        return False
    
    # Turn OFF both sides first
    grid.HideBubbleInView(ends["top"], view)
    grid.HideBubbleInView(ends["bottom"], view)
    
    # Turn ON selected sides only
    if "top" in selected_sides:
        grid.ShowBubbleInView(ends["top"], view)
    if "bottom" in selected_sides:
        grid.ShowBubbleInView(ends["bottom"], view)
    
    return True

def create_view_display_name(view):
    """Create a display name for view selection"""
    if isinstance(view, DB.ViewPlan):
        view_type = "Plan"
    elif hasattr(view, 'ViewType') and view.ViewType == DB.ViewType.Elevation:
        view_type = "Elevation"
    else:
        view_type = "View"
    
    return "{} - {}".format(view_type, view.Name)

def main():
    # Step 1: Get all available views
    all_views = get_all_views()
    
    if not all_views:
        forms.alert("No valid views found in the document.")
        return
    
    # Step 2: Let user select view(s)
    view_dict = {}
    view_options = []
    
    # Add current view first
    current_view = revit.active_view
    current_name = "{} (Current)".format(create_view_display_name(current_view))
    view_options.append(current_name)
    view_dict[current_name] = current_view
    
    for view in all_views:
        display_name = create_view_display_name(view)
        if view.Id != current_view.Id:
            view_options.append(display_name)
            view_dict[display_name] = view
    
    selected_view_names = forms.SelectFromList.show(
        view_options,
        title="Select View(s)",
        multiselect=True,
        button_name="Next"
    )
    
    if not selected_view_names:
        return
    
    selected_views = [view_dict[name] for name in selected_view_names]
    
    # Step 3: Check for grids
    views_with_grids = []
    for view in selected_views:
        grids = get_all_grids_from_view(view)
        if grids:
            views_with_grids.append(view)
    
    if not views_with_grids:
        forms.alert("No grids found in the selected view(s).")
        return
    
    # Step 4: User selects which sides to show bubbles
    side_options = [
        "Left (Horizontal Grids)",
        "Right (Horizontal Grids)",
        "Top (Vertical Grids)",
        "Bottom (Vertical Grids)"
    ]
    
    selected_options = forms.SelectFromList.show(
        side_options,
        title="Select Bubble Side(s) to Show",
        multiselect=True,
        button_name="Apply"
    )
    
    if not selected_options:
        return
    
    # Parse selected sides and determine which orientations to process
    horizontal_sides = []  # sides for horizontal grids
    vertical_sides = []    # sides for vertical grids
    
    for option in selected_options:
        if "Left" in option:
            horizontal_sides.append("left")
        elif "Right" in option:
            horizontal_sides.append("right")
        elif "Top" in option:
            vertical_sides.append("top")
        elif "Bottom" in option:
            vertical_sides.append("bottom")
    
    # Determine which grid types to process
    process_horizontal = len(horizontal_sides) > 0 or any("Horizontal" in opt for opt in selected_options)
    process_vertical = len(vertical_sides) > 0 or any("Vertical" in opt for opt in selected_options)
    
    # Step 5: Apply settings
    h_count = 0
    v_count = 0
    
    with revit.Transaction("Apply Grid Bubble Settings"):
        for view in views_with_grids:
            grids = get_all_grids_from_view(view)
            
            for grid in grids:
                orientation = determine_grid_orientation(grid)
                
                # Only process horizontal grids if user selected horizontal options
                if orientation == "horizontal" and process_horizontal:
                    if apply_horizontal_bubble(grid, horizontal_sides, view):
                        h_count += 1
                
                # Only process vertical grids if user selected vertical options
                elif orientation == "vertical" and process_vertical:
                    if apply_vertical_bubble(grid, vertical_sides, view):
                        v_count += 1
    
    # Show result
    msg = "Bubbles applied!\n\n"
    
    if process_horizontal:
        sides_text = ", ".join(horizontal_sides) if horizontal_sides else "none"
        msg += "Horizontal grids: {} processed (showing: {})\n".format(h_count, sides_text)
    
    if process_vertical:
        sides_text = ", ".join(vertical_sides) if vertical_sides else "none"
        msg += "Vertical grids: {} processed (showing: {})\n".format(v_count, sides_text)
    
    msg += "\nViews: {}".format(len(views_with_grids))
    
    forms.alert(msg)

if __name__ == "__main__":
    main()