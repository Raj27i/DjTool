# -*- coding: utf-8 -*-
"""Hello World button — verifies the DJTools extension loads correctly."""

__title__ = "Hello\nWorld"
__author__ = "Raj27i"
__doc__ = "A simple test button that shows a Hello World message."

from pyrevit import forms, revit

doc = revit.doc
uidoc = revit.uidoc

forms.alert(
    msg="Hello from DJTools!",
    sub_msg="If you see this, your extension is loading correctly.",
    title="DJTools - Hello World",
    ok=True
)
