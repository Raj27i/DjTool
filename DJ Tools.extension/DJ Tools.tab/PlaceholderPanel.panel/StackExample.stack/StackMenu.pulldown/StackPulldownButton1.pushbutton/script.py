# -*- coding: utf-8 -*- 
__title__   = "Section Openings Info with Area"
__doc__     = """Version = 1.2
Date    = 18.12.2024
________________________________________________________________
Description:
    Gets windows and doors from linked Revit files that are visible 
    in the active section view and shows category, type name, count, and area.
________________________________________________________________
Author: Claude"""

from Autodesk.Revit.DB import *
from pyrevit import forms
from System.Collections.Generic import List
from collections import defaultdict

# Document variables
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = doc.ActiveView

def get_linked_files():
    """Get all linked Revit files in the current document"""
    return FilteredElementCollector(doc)\
            .OfClass(RevitLinkInstance)\
            .ToElements()

def create_solid_from_bbox(bbox):
    """Create a solid from bounding box"""
    # Create base points
    pt0 = XYZ(bbox.Min.X, bbox.Min.Y, bbox.Min.Z)
    pt1 = XYZ(bbox.Max.X, bbox.Min.Y, bbox.Min.Z)
    pt2 = XYZ(bbox.Max.X, bbox.Max.Y, bbox.Min.Z)
    pt3 = XYZ(bbox.Min.X, bbox.Max.Y, bbox.Min.Z)
    
    # Create edges
    edges = List[Curve]()
    for pt1, pt2 in gen_pair_points(pt0, pt1, pt2, pt3):
        edges.Add(Line.CreateBound(pt1, pt2))
    
    # Create extrusion
    height = bbox.Max.Z - bbox.Min.Z
    base_loop = CurveLoop.Create(edges)
    loop_list = List[CurveLoop]()
    loop_list.Add(base_loop)
    
    # Create solid
    pre_transform_box = GeometryCreationUtilities.CreateExtrusionGeometry(
        loop_list, 
        XYZ.BasisZ, 
        height
    )
    transform_box = SolidUtils.CreateTransformed(pre_transform_box, bbox.Transform)
    
    return transform_box

def gen_pair_points(*args):
    """Generator for point pair loop"""
    for idx, pt in enumerate(args):
        try: 
            yield pt, args[idx + 1]
        except: 
            yield pt, args[0]

def get_visible_openings_from_link(link_instance):
    """Get windows and doors from link that are visible in section view"""
    # Get link document and transform
    link_doc = link_instance.GetLinkDocument()
    transform = link_instance.GetTotalTransform()
    
    # Get section view crop box
    view_box = active_view.CropBox
    
    # Create solid from view box
    section_solid = create_solid_from_bbox(view_box)
    
    # Create intersection filter with solid
    solid_filter = ElementIntersectsSolidFilter(section_solid)
    
    # Create category filter for windows and doors
    categories = List[BuiltInCategory]([
        BuiltInCategory.OST_Windows,
        BuiltInCategory.OST_Doors
    ])
    category_filter = ElementMulticategoryFilter(categories)
    
    # Get elements using combined filters
    elements = FilteredElementCollector(link_doc)\
              .WhereElementIsNotElementType()\
              .WherePasses(category_filter)\
              .WherePasses(solid_filter)\
              .ToElements()
            
    return elements, transform

def get_element_dimensions(element, link_doc=None):
    """Get width, height, and area of an element."""
    try:
        # Validate input document for linked elements
        if not link_doc:
            return None
        
        # Retrieve type ID and type element
        type_id = element.GetTypeId()
        if type_id == ElementId.InvalidElementId:
            return None
        
        element_type = link_doc.GetElement(type_id)
        if not element_type:
            return None

        # Retrieve 'Width' and 'Height' parameters
        width_param = element_type.LookupParameter("Width")
        height_param = element_type.LookupParameter("Height")

        # Ensure width and height exist
        if width_param and height_param:
            width = width_param.AsDouble() * 0.3048  # Convert from feet to meters
            height = height_param.AsDouble() * 0.3048  # Convert from feet to meters
            area = width * height
            return {
                'width': width,
                'height': height,
                'area': area
            }
        else:
            return None

    except Exception as e:
        print("Error retrieving dimensions: {}".format(e))
        return None

def main():
    # Check if we're in a section view
    if not isinstance(active_view, ViewSection):
        forms.alert("Please run this script in a section view.", title="Invalid View")
        return

    # Get linked models
    linked_models = get_linked_files()
    if not linked_models:
        forms.alert("No linked models found.", title="Error")
        return

    # Filter out unloaded or inaccessible links
    valid_links = [link for link in linked_models if link.GetLinkDocument()]
    if not valid_links:
        forms.alert("No loaded linked models found.", title="Error")
        return

    # Create selection options for models
    model_options = [Element.Name.GetValue(link) for link in valid_links]

    # Let user select model
    selected_model = forms.SelectFromList.show(
        model_options,
        title="Select Linked Model",
        multiselect=False
    )

    if not selected_model:
        forms.alert("No model selected. Exiting.", title="No Selection")
        return

    # Get the selected link instance and linked document
    selected_link = next(
        (link for link in valid_links 
         if Element.Name.GetValue(link) == selected_model),
        None
    )

    if not selected_link:
        forms.alert("Selected linked model not found.", title="Error")
        return

    link_doc = selected_link.GetLinkDocument()
    if not link_doc:
        forms.alert("Cannot access the linked document. Ensure the link is loaded.", title="Error")
        return

    # Get openings from the selected link
    elements, transform = get_visible_openings_from_link(selected_link)

    if not elements:
        forms.alert("No windows or doors found in the selected model.", title="No Elements")
        return

    # Count elements by category and type name, and calculate total area
    element_info = defaultdict(lambda: {'count': 0, 'total_area': 0.0})
    for element in elements:
        category_name = element.Category.Name if element.Category else "Unknown Category"
        type_name = element.Name
        dimensions = get_element_dimensions(element, link_doc)
        if dimensions:
            area = dimensions['area']
            element_info[(category_name, type_name)]['count'] += 1
            element_info[(category_name, type_name)]['total_area'] += area

    # Display results
    results = [
        "{} - {}: Count = {}, Total Area = {:.2f} m²".format(
            cat, typ, info['count'], info['total_area']
        )
        for (cat, typ), info in element_info.items()
    ]
    results_text = "\n".join(results)
    forms.alert("Visible Windows and Doors:\n\n" + results_text, title="Element Information")

if __name__ == '__main__':
    main()
