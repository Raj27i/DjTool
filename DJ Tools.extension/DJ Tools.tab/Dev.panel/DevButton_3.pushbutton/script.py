# -*- coding: utf-8 -*-
__title__   = "Doors and Windows in Linked Models"
__doc__     = """Version = 3.8
Date    = 05.12.2024
________________________________________________________________
Description:

Use this script to list the visible door and window elements in the current view, for both current and linked models.
This version adds functionality to take elements from the active view in linked models, and supports working in section, elevation, and plan views.

________________________________________________________________
TODO:
1. Open the desired view in Revit (plan, section, or elevation).
2. Click this button to run the script.
3. Select a model (current or linked).
4. View the list of visible elements by category in the active view, along with their count.
________________________________________________________________
Last Updates:
- [05.12.2024] v3.8 Removed incorrect usage of IsElementVisibleInTemporaryVisibilityMode, improved visibility check logic.
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

# Import view types explicitly to avoid NameError
from Autodesk.Revit.DB import ViewPlan, ViewSection, View3D
# Import Architecture and Structure namespaces
from Autodesk.Revit.DB.Architecture import *
from Autodesk.Revit.DB.Structure import *


app = __revit__.Application
uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document


active_view = doc.ActiveView


element_counts = {}

# Start transaction (required in pyRevit even for read-only operations)
with revit.Transaction("Count Windows and Doors"):
    # Collect Windows and Doors visible in the active view
    windows_collector = DB.FilteredElementCollector(doc, active_view.Id) \
        .OfCategory(DB.BuiltInCategory.OST_Windows) \
        .WhereElementIsNotElementType()

    doors_collector = DB.FilteredElementCollector(doc, active_view.Id) \
        .OfCategory(DB.BuiltInCategory.OST_Doors) \
        .WhereElementIsNotElementType()

    # Combine windows and doors
    elements = list(windows_collector) + list(doors_collector)

    # Count elements by category, family name, and type name
    for element in elements:
        category = element.Category.Name  # Get category (e.g., "Windows" or "Doors")
        family_name = element.Symbol.FamilyName  # Get family name
        type_name = element.Name  # Get type name

        # Create a unique key based on category, family, and type
        key = "{} | {} | {}".format(category, family_name, type_name)

        if key in element_counts:
            element_counts[key] += 1
        else:
            element_counts[key] = 1

# Print results in a structured format
print("Category | Family Name | Type Name | Count")
print("-" * 50)
for key, count in element_counts.items():
    print("{} | Count: {}".format(key, count))