# -*- coding: utf-8 -*-
__title__   = "Pulldown Button 1"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:

This is the placeholder for a .pushbutton in a /pulldown
You can use it to start your pyRevit Add-In

________________________________________________________________
How-To:

1. [Hold ALT + CLICK] on the button to open its source folder.
You will be able to override this placeholder.

2. Automate Your Boring Work ;)

________________________________________________________________
TODO:
[FEATURE] - Describe Your ToDo Tasks Here
________________________________________________________________
Last Updates:
- [15.06.2024] v1.0 Change Description
- [10.06.2024] v0.5 Change Description
- [05.06.2024] v0.1 Change Description 
________________________________________________________________
Author: Erik Frits"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝
#==================================================
from Autodesk.Revit.DB import *

#.NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#==================================================
app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document #type:Document


from pyrevit import revit, DB, forms

# Initialize Revit document and UIDocument


# Ask user to select multiple views
views_collector = DB.FilteredElementCollector(doc).OfClass(DB.View).ToElements()
view_options = [view.Name for view in views_collector if view.ViewType == DB.ViewType.Section]

selected_views = forms.SelectFromList.show(
    view_options,
    title="Select Views",
    multiselect=True
)

# Exit if no views are selected
if not selected_views:
    forms.alert("No views selected. Script will now exit.", exitscript=True)

# String to store formatted results
results = "Category | Family | Type | View | Comments\n"
results += "-" * 70 + "\n"

# Process each selected view
with revit.Transaction("Update Comments with View Name"):
    for view_name in selected_views:
        # Find the view by name
        view = next(v for v in views_collector if v.Name == view_name)

        # Collect Windows and Doors in the view
        windows_collector = DB.FilteredElementCollector(doc, view.Id) \
            .OfCategory(DB.BuiltInCategory.OST_Windows) \
            .WhereElementIsNotElementType()

        doors_collector = DB.FilteredElementCollector(doc, view.Id) \
            .OfCategory(DB.BuiltInCategory.OST_Doors) \
            .WhereElementIsNotElementType()

        # Combine windows and doors
        elements = list(windows_collector) + list(doors_collector)

        # Process each element
        for element in elements:
            # Update Comments parameter with view name
            comments_param = element.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
            if comments_param and not comments_param.IsReadOnly:
                comments_param.Set(view_name)

            # Add to results for summary
            category = element.Category.Name
            family = element.Symbol.FamilyName
            type_name = element.Name
            results += "{} | {} | {} | {} | {}\n".format(category, family, type_name, view_name, view_name)

# Display results to the user
forms.alert(results, title="Updated Elements Summary", warn_icon=False)