# -*- coding: utf-8 -*-
__title__   = "View Aligner"
__doc__     = """Version = 1.0



View Aligner

Description:
This PyRevit script helps you align views across multiple sheets in your Revit project. 
It's designed to save time and ensure consistency when you need to position views in the 
same location across different sheets. 

The tool works by taking the position of a view on a source sheet and applying that same 
position to views on one or more target sheets. This is particularly useful when you have 
a standard layout that needs to be replicated across multiple sheets.

Key features:
- Aligns views based on their center points
- Allows selection of multiple target sheets for batch processing
- Works with the first view found on each sheet
- Provides a summary of successful alignments

Important notes:
- This script assumes each sheet contains at least one view
- If a sheet has multiple views, only the first view will be affected
- Ensure your source sheet has the view positioned exactly where you want it
- Back up your project before running this script on a large number of sheets

How to use:
1. Run the script from the PyRevit tab.
2. Select a single source sheet containing the view you want to align to.
3. Select one or more target sheets to align.
4. The script will align the views on target sheets to match the source.
5. Review the results message for successful alignments.

Author: Durai



"""

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


# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝
#==================================================




# -*- coding: utf-8 -*-
from pyrevit import revit, DB, UI
from pyrevit import forms

doc = revit.doc

def get_sheets():
    return DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet).ToElements()

def get_view_on_sheet(sheet):
    viewport_ids = sheet.GetAllViewports()
    if viewport_ids:
        viewport = doc.GetElement(viewport_ids[0])
        return doc.GetElement(viewport.ViewId)
    return None

def get_view_center_on_sheet(sheet):
    viewport_ids = sheet.GetAllViewports()
    if viewport_ids:
        viewport = doc.GetElement(viewport_ids[0])
        return viewport.GetBoxCenter()
    return None

def align_view(source_sheet, target_sheet):
    source_center = get_view_center_on_sheet(source_sheet)
    if not source_center:
        print('No view found on the source sheet: {0}'.format(source_sheet.Name))
        return False
    
    target_view = get_view_on_sheet(target_sheet)
    if not target_view:
        print('No view found on the target sheet: {0}'.format(target_sheet.Name))
        return False
    
    target_viewport_ids = target_sheet.GetAllViewports()
    if target_viewport_ids:
        target_viewport = doc.GetElement(target_viewport_ids[0])
        current_center = target_viewport.GetBoxCenter()
        offset = source_center - current_center
        DB.ElementTransformUtils.MoveElement(doc, target_viewport.Id, offset)
        return True
    return False

def main():
    # Select source sheet
    source_sheet = forms.select_sheets(title='Select Source Sheet', multiple=False)
    if not source_sheet:
        return

    # Select multiple target sheets
    target_sheets = forms.select_sheets(title='Select Target Sheets', multiple=True)
    if not target_sheets:
        return

    # Align views
    with revit.Transaction('Align Views'):
        successful_alignments = 0
        for target_sheet in target_sheets:
            if align_view(source_sheet, target_sheet):
                successful_alignments += 1

    forms.alert('Views aligned successfully on {0} out of {1} sheets!'.format(successful_alignments, len(target_sheets)), ok=True)

if __name__ == '__main__':
    main()


