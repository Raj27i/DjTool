# -*- coding: utf-8 -*-
__title__   = "Bulk Schedule Export"
__doc__     = """Version = 1.0
Date    = 15.06.2024
________________________________________________________________
Description:

This is the placeholder for a .pushbutton
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
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import *

#.NET Imports
import clr
clr.AddReference('System')
from System.Collections.Generic import List

import os
from pyrevit import forms
from pyrevit import script


# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#==================================================
app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document #type:Document


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#==================================================

from pyrevit import script
from pyrevit import forms
from pyrevit import DB
from pyrevit.framework import List
import os

# Get active Revit document
doc = __revit__.ActiveUIDocument.Document

# Ask user to select a schedule view
from pyrevit import script
from pyrevit import forms
from pyrevit import DB
from pyrevit.framework import List
import os

# Get active Revit document
doc = __revit__.ActiveUIDocument.Document

# Ask user to select multiple schedule views
schedules = [v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewSchedule) if not v.IsTemplate]

selected_schedules = forms.SelectFromList.show(
    sorted(schedules, key=lambda x: x.Name),
    title="Select Schedules to Export",
    button_name="Select",
    multiselect=True,
    name_attr='Name'
)

# If no schedules selected, stop script
if not selected_schedules:
    script.exit()

# Ask user to select the folder to save the exported files
selected_folder = forms.pick_folder(
    title="Select Folder to Save Schedules"
)

# If no folder is selected, stop script
if not selected_folder:
    script.exit()

# Set options for schedule export
options = DB.ViewScheduleExportOptions()

options.TextQualifier = DB.ExportTextQualifier.DoubleQuote 

# Iterate over selected schedules and export each as an Excel file
for schedule in selected_schedules:
    schedule_name = schedule.Name
    file_path = os.path.join(selected_folder, "{}.xls".format(schedule_name))  # Set file extension to .xls

    try:
        # Export the schedule to Excel format
        schedule.Export(selected_folder, "{}.xls".format(schedule_name), options)
        script.get_output().print_md("**Schedule '{}' exported successfully to: {}**".format(schedule_name, file_path))
    except Exception as e:
        script.get_output().print_md("**Failed to export schedule '{}': {}**".format(schedule_name, e))



#🤖 Automate Your Boring Work Here





#==================================================
#🚫 DELETE BELOW
from Snippets._customprint import kit_button_clicked    # Import Reusable Function from 'lib/Snippets/_customprint.py'
kit_button_clicked(btn_name=__title__)                  # Display Default Print Message
