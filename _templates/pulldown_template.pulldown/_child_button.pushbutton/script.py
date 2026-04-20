# -*- coding: utf-8 -*-
"""Child button inside a pulldown. Duplicate this folder next to it to add more items."""

__title__  = "Child\nButton"
__author__ = "Raj27i"
__doc__    = "Example child button within a pulldown menu."

from pyrevit import forms

forms.alert("Child button clicked.", title=__title__.replace("\n", " "))
