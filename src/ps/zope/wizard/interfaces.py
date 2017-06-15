# -*- coding: utf-8 -*-
"""Interface definitions for the Wizards."""

# zope imports
from z3c.form.interfaces import IForm
from zope.interface import Attribute


class IWizard(IForm):
    """A multi-step z3c.form based wizard."""

    steps = Attribute("""
        A sequence of step classes that will be instantiated when the wizard's
        update method is called.
        """)

    active_steps = Attribute("""
        A sequence of active wizard step instances.

        Available after the wizard's update method has been called.
        """)

    current_step = Attribute("""
        The wizard step instance currently being displayed.
        """)

    current_index = Attribute("""
        The (0-based) index of the current step within the active_steps
        sequence.
        """)

    session_key = Attribute("""
        Returns the unique session key used by this wizard instance.

        By default, this is a tuple of 'ps.zope.wizard' and the URL
        path to the wizard.
        """)

    session = Attribute("""
        The session where data for this wizard is persisted.

        Available after the wizard's update method has been called.
        This can be a session or annotation.
        """)

    on_first_step = Attribute("""
        True if the first step of the wizard is being displayed.
        """)

    on_last_step = Attribute("""
        True if the last step of the wizard is being displayed.
        """)

    all_steps_finished = Attribute("""
        True if the 'available' attribute of each wizard step is True.
        """)

    finished = Attribute("""
        True if the wizard has been completed and the final actions have run.
        """)

    absolute_url = Attribute("""The URL of the wizard.""")

    validate_back = Attribute("""
        Set to True if you want the Wizard to validate the input if a user
        uses the Back button on a Step. Set to False if you don't and abandon
        all user input (data).
        """)

    def initialize():
        """Called the first time a wizard is viewed in a new wizard session.

        This method may be used to populate the wizard session with data
        from some source. When assigning values into the wizard session,
        make sure you use the proper persistent classes (e.g. PersistentDict
        instead of dict), or else changes to subitems may be changed without
        those changes getting persisted.

        The default implementation calls the 'load_steps' method.
        """

    def load_steps(context):
        """Load the wizard session data from a context.

        The default implementation calls the 'load' method of each wizard step.
        """

    def finish():
        """Called when a wizard is successfully completed

        This method will be called after validation of the final step.

        Use this method to carry out some actions based on the values that have
        been filled out during completion of the wizard.

        The default implementation calls the 'apply_steps' method.
        """

    def apply_steps(context):
        """Update a context based on the wizard session data.

        The default implementation calls the 'apply' method of each wizard
        step.
        """

    def sync():
        """Mark the session as having changed.

        Do this to ensure that changes get persisted.
        """


class IStep(IForm):
    """A single step of a z3c.form based wizard.

    By default, the content accessed by this form will be a PersistentDict
    within the wizard session, with a key equal to the step's prefix.
    """

    label = Attribute("""Title displayed at the wizard step.""")

    description = Attribute("""Description displayed at the wizard step.""")

    wizard = Attribute("""The wizard this step is being used in.""")

    available = Attribute("""
        It indicates whether the current step can be accessed via the
        wizard navigation links or not. By default, only steps for which
        there is already data stored in the session can be accessed.

        The next and previous steps can always be accessed via the
        respective buttons regardless of the value of this property.
        """)

    completed = Attribute("""
        Indicates whether the user should be allowed to move on to the
        next step or not. Defaults to True. If false, the Continue button
        will be disabled.
        """)

    def apply_changes(data):
        """Save changes from this step to its content.

        The content is typically a PersistentDict in the wizard's session.
        """

    def load(context):
        """Load the data for this step based on a context."""

    def apply(context):
        """Update a context based on the session data for this step."""
