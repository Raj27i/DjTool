# -*- coding: utf-8 -*-
"""Placeholder button for the Structure panel."""

__title__ = "Structure\nPlaceholder"
__author__ = "Raj27i"
__doc__ = "Placeholder button. Duplicate this folder to add a real Structure tool."

from pyrevit import forms

forms.alert(
    msg="Structure panel placeholder",
    sub_msg="Duplicate this .pushbutton folder to create a real Structure tool.",
    title="DJTools - Structure",
    ok=True,
)
