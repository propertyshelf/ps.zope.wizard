# -*- coding: utf-8 -*-
"""A z3c.form based wizard with adjustable storage backends."""

# zope imports
from z3c.form import (
    field,
    form,
)
from z3c.form.interfaces import IDataManager
from zope.component import getMultiAdapter
from zope.interface import implementer

# local imports
from ps.zope.wizard.interfaces import (
    IStep,
    IWizard,
)


WIZARD_SESSION_KEY = 'ps.zope.wizard'


def apply_changes(form, content, data):
    """Apply changes to the content.

    A slight modification of the normal applyChanges method from
    z3c.form.form, to make it not break if there's no value set yet.
    """
    changes = {}
    for name, _field in form.fields.items():
        # If the field is not in the data, then go on to the next one.
        if name not in data:
            continue
        # Get the datamanager and get the original value.
        dm = getMultiAdapter((content, _field.field), IDataManager)
        old_value = dm.query()
        # Only update the data, if it is different.
        if old_value != data[name]:
            dm.set(data[name])
            # Record the change using information required later.
            changes.setdefault(dm.field.interface, []).append(name)
    return changes


@implementer(IStep)
class Step(form.Form):
    """Base class for a wizard step implementing the IStep interface.

    Subclasses will typically want to override at least the fields attribute.
    """

    def apply_changes(self, data):
        """Save changes from this step to its content.

        The content is typically a PersistentDict in the wizard's session.
        """
        pass

    def load(self, context):
        """Load the data for this step based on a context."""
        pass

    def apply(self, context):
        """Update a context based on the session data for this step."""
        pass


@implementer(IWizard)
class Wizard(form.Form):
    """Abstract class for a wizard implementing the IWizard interface.

    Subclasses must provide at least the finish method.
    """

    steps = ()
    label = u''
    description = u''
    ignoreContext = True
    fields = field.Fields()

    current_step = None
    current_index = None
    finished = False
    validate_back = True

    @property
    def session_key(self):
        """Return the unique session key used by this wizard instance."""
        try:
            path = [getPath(self.context)]
        except TypeError:
            path = []
        path.append(self.__name__)
        return (WIZARD_SESSION_KEY, tuple(path))

    def initialize(self):
        """Called the first time a wizard is viewed in a new wizard session.

        This method may be used to populate the wizard session with data
        from some source. When assigning values into the wizard session,
        make sure you use the proper persistent classes (e.g. PersistentDict
        instead of dict), or else changes to subitems may be changed without
        those changes getting persisted.

        The default implementation calls the 'load_steps' method.
        """

    def load_steps(self, context):
        """Load the wizard session data from a context.

        The default implementation calls the 'load' method of each wizard step.
        """

    def finish(self):
        """Called when a wizard is successfully completed

        This method will be called after validation of the final step.

        Use this method to carry out some actions based on the values that have
        been filled out during completion of the wizard.

        The default implementation calls the 'apply_steps' method.
        """

    def apply_steps(self, context):
        """Update a context based on the wizard session data.

        The default implementation calls the 'apply' method of each wizard
        step.
        """

    def sync(self):
        """Mark the session as having changed.

        Do this to ensure that changes get persisted.
        """
