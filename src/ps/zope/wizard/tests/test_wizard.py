# -*- coding: utf-8 -*-
"""Test wizards."""

# python imports
try:
    import unittest2 as unittest
except ImportError:
    import unittest

# zope imports
from zope.interface.verify import (
    verifyClass,
    verifyObject,
)

# local imports
from ps.zope.wizard.interfaces import (
    IStep,
    IWizard,
)
from ps.zope.wizard.wizard import (
    Step,
    Wizard,
)


class TestWizard(unittest.TestCase):
    """Validate wizard implementation."""

    def test_step_implementation(self):
        verifyClass(IStep, Step)

    def test_wizard_implementation(self):
        verifyClass(IWizard, Wizard)
