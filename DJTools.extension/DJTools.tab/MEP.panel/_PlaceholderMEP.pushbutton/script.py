# -*- coding: utf-8 -*-
"""Placeholder button for the MEP panel."""

__title__ = "MEP\nPlaceholder"
__author__ = "Raj27i"
__doc__ = "Placeholder button. Duplicate this folder to add a real MEP tool."

from pyrevit import forms

forms.alert(
    msg="MEP panel placeholder",
    sub_msg="Duplicate this .pushbutton folder to create a real MEP tool.",
    title="DJTools - MEP",
    ok=True,
)
