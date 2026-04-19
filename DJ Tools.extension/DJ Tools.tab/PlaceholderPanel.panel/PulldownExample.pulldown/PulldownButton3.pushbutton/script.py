# -*- coding: utf-8 -*-
__title__   = "Pulldown Button 3"
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



__title__ = "Copy Detail\nItem Comments"
__doc__ = "Copies Comments parameter to Comments_CW1 for Detail Items"

from pyrevit import revit, DB, forms
from pyrevit import script

# Get the current document
doc = revit.doc
output = script.get_output()
# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝
#==================================================
app    = __revit__.Application
uidoc  = __revit__.ActiveUIDocument
doc    = __revit__.ActiveUIDocument.Document #type:Document


def copy_detail_item_comments():
    """Copy Comments parameter to Comments_CW1 for all detail items"""
    
    # Collect all detail items in the project
    collector = DB.FilteredElementCollector(doc) \
        .OfCategory(DB.BuiltInCategory.OST_DetailComponents) \
        .WhereElementIsNotElementType()
    
    detail_items = list(collector)
    
    if not detail_items:
        forms.alert("No detail items found in the project.", exitscript=True)
    
    output.print_md("## Processing Detail Items")
    output.print_md("Found **{}** detail items".format(len(detail_items)))
    
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    # Start transaction
    with revit.Transaction("Copy Comments to Comments_CW1"):
        for item in detail_items:
            try:
                # Get the Comments parameter
                comments_param = item.LookupParameter("Comments")
                
                if comments_param and comments_param.HasValue:
                    comment_value = comments_param.AsString()
                    
                    # Only process if there's a value
                    if comment_value:
                        # Get the Comments_CW1 parameter
                        comments_cw1_param = item.LookupParameter("Comments1_CW")
                        
                        if comments_cw1_param:
                            # Check if parameter is not read-only
                            if not comments_cw1_param.IsReadOnly:
                                # Add "Skakt:" prefix
                                new_value = "Skakt: " + comment_value
                                comments_cw1_param.Set(new_value)
                                processed_count += 1
                                output.print_md("✓ **Element ID {}**: Copied '{}' to Comments1_CW".format(
                                    item.Id, new_value))
                            else:
                                skipped_count += 1
                                output.print_md("⊗ **Element ID {}**: Comments1_CW is read-only".format(item.Id))
                        else:
                            skipped_count += 1
                            output.print_md("⊗ **Element ID {}**: Comments1_CW parameter not found".format(item.Id))
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                error_count += 1
                output.print_md("✗ **Element ID {}**: Error - {}".format(item.Id, str(e)))
    
    # Print summary
    output.print_md("---")
    output.print_md("## Summary")
    output.print_md("**Processed:** {} items".format(processed_count))
    output.print_md("**Skipped:** {} items (no Comments value or missing Comments_CW1 parameter)".format(skipped_count))
    output.print_md("**Errors:** {} items".format(error_count))
    
    if processed_count > 0:
        forms.alert("Successfully copied comments for {} detail items!".format(processed_count))
    else:
        forms.alert("No detail items were updated. Check the output for details.")

# Run the script
if __name__ == '__main__':
    copy_detail_item_comments()



#==================================================
#🚫 DELETE BELOW
from Snippets._customprint import kit_button_clicked    # Import Reusable Function from 'lib/Snippets/_customprint.py'
kit_button_clicked(btn_name=__title__)                  # Display Default Print Message
