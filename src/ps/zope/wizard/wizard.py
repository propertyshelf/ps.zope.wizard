# -*- coding: utf-8 -*-
"""A z3c.form based wizard with adjustable storage backends."""

# zope imports
from persistent.dict import PersistentDict
from z3c.form import (
    button,
    field,
    form,
)
from z3c.form.interfaces import IDataManager
from zope.browserpage import ViewPageTemplateFile
from zope.component import getMultiAdapter
from zope.interface import implementer
from zope.session.interfaces import ISession
from zope.traversing.api import getPath
from zope.traversing.browser import absoluteURL

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

    label = u''
    description = u''
    wizard = None
    enabled = True

    def __init__(self, context, request, wizard):
        super(Step, self).__init__(context, request)
        self.wizard = wizard

    def getContent(self):
        """See z3c.form.interfaces.IForm."""
        return self.wizard.session.setdefault(self.prefix, PersistentDict())

    def update(self):
        """See z3c.form.interfaces.IForm."""
        session = self.wizard.session
        data = session.get(self.prefix, None)
        if not data:
            self.load(self.wizard.context)
            self.wizard.sync()
        super(Step, self).update()

    @property
    def finished(self):
        content = self.getContent()
        return content.get('_finished', False)

    def apply_changes(self, data):
        """Save changes from this step to its content.

        The content is typically a PersistentDict in the wizard's session.
        """
        content = self.getContent()
        apply_changes(self, content, data)
        self.wizard.sync()

    def load(self, context, **kw):
        """Load the data for this step based on a context."""
        pass

    def apply(self, context, **kw):
        """Update a context based on the session data for this step."""
        pass

    def mark_finished(self, finished):
        if not isinstance(finished, bool):
            try:
                finished = bool(finished)
            except TypeError:
                finished = False
        content = self.getContent()
        content['_finished'] = finished

    @property
    def next_url(self):
        """Next step url known by wizard."""
        return self.wizard.next_url

    @button.buttonAndHandler(
        u'Continue',
        name='continue',
        condition=lambda form: form.wizard.show_continue()
    )
    def handle_continue(self, action):
        """"Continue button."""
        data, errors = self.extractData()
        if errors:
            self.status = self.wizard.form_errors_message
            self.mark_finished(False)
        else:
            self.apply_changes(data)
            self.mark_finished(True)
            self.wizard.update_current_step(self.wizard.current_index + 1)

            # Proceeding can change the conditions for the finish button,
            # so we need to reconstruct the button actions, since we
            # do not redirect.
            self.wizard.updateActions()

    @button.buttonAndHandler(
        u'Finish',
        name='finish',
        condition=lambda form: form.wizard.show_finish())
    def handle_finish(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.wizard.form_errors_message
            return
        else:
            self.status = self.wizard.success_message
            self.wizard.finished = True
        self.wizard.current_step.apply_changes(data)
        self.wizard.finish()
        # Clear out the session
        del self.wizard.request_session[self.wizard.session_key]
        self.wizard.sync()

    @button.buttonAndHandler(
        u'Back',
        name='back',
        condition=lambda form: form.wizard.show_back(),
    )
    def handle_back(self, action):
        """Back button."""
        if self.wizard.validate_back:
            # If enabled, allow navigating back only if the current
            # step validates and can be saved.
            data, errors = self.extractData()
            if errors:
                self.status = self.wizard.form_errors_message
                self.mark_finished(False)
                return
            self.apply_changes(data)
            self.mark_finished(True)

        self.wizard.update_current_step(self.wizard.current_index - 1)

        # Going back can change the conditions for the finish button,
        # so we need to reconstruct the button actions, since we
        # do not redirect.
        self.wizard.updateActions()

    @button.buttonAndHandler(
        u'Cancel',
        name='cancel',
    )
    def handle_cancel(self, action):
        """Clear button."""
        # Clear out the session
        try:
            del self.wizard.request_session[self.wizard.session_key]
        except KeyError:
            pass
        else:
            self.wizard.sync()
        self.request.response.redirect(absoluteURL(self.context, self.request))


@implementer(IWizard)
class Wizard(form.Form):
    """Abstract class for a wizard implementing the IWizard interface.

    Subclasses must provide at least the finish method.
    """

    template = ViewPageTemplateFile('wizard.pt')
    steps = ()
    label = u''
    description = u''
    ignoreContext = True
    fields = field.Fields()

    current_step = None
    current_index = None
    finished = False
    validate_back = True

    success_message = u'Information submitted successfully.'
    form_errors_message = u'There were errors.'
    next_url = None
    confirmation_page_name = None

    def update(self):
        """See z3c.form.interfaces.IForm."""
        # Initialize session.
        session_key = self.session_key
        if session_key not in self.request_session:
            self.request_session[session_key] = {}
        self.session = self.request_session[session_key]

        self.update_active_steps()

        # If this wizard hasn't been loaded yet in this session, load the data.
        if not len(self.session):
            self.initialize()
            self.sync()

        self.jump_to_current_step()
        super(Wizard, self).update()

    def updateActions(self):
        """See z3c.form.interfaces.IForm."""
        # Allow the current step to determine whether the wizard navigation
        # is enabled.
        form.Form.updateActions(self)
        if not self.current_step.enabled:
            if self.on_last_step:
                self.actions['finish'].disabled = 'disabled'
            else:
                self.actions['continue'].disabled = 'disabled'

    @property
    def session_key(self):
        """Return the unique session key used by this wizard instance."""
        try:
            path = [getPath(self.context)]
        except TypeError:
            path = []
        path.append(self.__name__)
        return (WIZARD_SESSION_KEY, tuple(path))

    @property
    def request_session(self):
        return ISession(self.request)['ps.zope.wizard']

    def update_active_steps(self):
        self.active_steps = []
        for step in self.steps:
            step = step(self.context, self.request, self)
            self.active_steps.append(step)

    def jump_to_current_step(self):
        self.update_current_step(self.session.setdefault('step', 0))
        if 'step' in self.request.form:
            self.jump(self.request.form['step'])

    def update_current_step(self, index):
        self.current_index = index
        self.session['step'] = self.current_index
        self.sync()
        self.current_step = self.active_steps[self.current_index]
        self.current_step.update()

    def jump(self, step_idx):
        """Jump to specific step.

        A jump is only possible, if the step has been completed already.
        """
        try:
            target_step = self.active_steps[step_idx]
        except (KeyError, TypeError):
            return
        if not target_step.finished:
            return

        self.update_current_step(step_idx)
        self.updateActions()

    def initialize(self):
        """Called the first time a wizard is viewed in a new wizard session.

        This method may be used to populate the wizard session with data
        from some source. When assigning values into the wizard session,
        make sure you use the proper persistent classes (e.g. PersistentDict
        instead of dict), or else changes to subitems may be changed without
        those changes getting persisted.

        The default implementation calls the 'load_steps' method.
        """
        self.load_steps(self.context)

    def load_steps(self, context):
        """Load the wizard session data from a context.

        The default implementation calls the 'load' method of each wizard step.
        """
        for step in self.active_steps:
            if hasattr(step, 'load'):
                step.load(context)

    def finish(self):
        """Called when a wizard is successfully completed

        This method will be called after validation of the final step.

        Use this method to carry out some actions based on the values that have
        been filled out during completion of the wizard.

        The default implementation calls the 'apply_steps' method.
        """
        self.apply_steps(self.context)
        self.next_url = self.confirmation_page_url()

    def confirmation_page_url(self):
        return '{0}/{1}'.format(
            absoluteURL(self.context, self.request),
            self.confirmation_page_name or '',
        )

    def apply_steps(self, context):
        """Update a context based on the wizard session data.

        The default implementation calls the 'apply' method of each wizard
        step.
        """
        for step in self.active_steps:
            if hasattr(step, 'apply'):
                step.apply(context)

    def sync(self):
        """Mark the session as having changed.

        Do this to ensure that changes get persisted.
        """
        self.request_session._p_changed = True

    @property
    def absolute_url(self):
        return '/'.join([
            absoluteURL(self.context, self.request),
            self.__name__ or '',
        ])

    @property
    def on_last_step(self):
        return self.current_index == len(self.steps) - 1

    def show_continue(self):
        return not self.on_last_step

    @property
    def all_steps_finished(self):
        for step in self.active_steps:
            if not step.finished:
                return False
        return True

    def show_finish(self):
        return self.all_steps_finished or self.on_last_step

    @property
    def on_first_step(self):
        return self.current_index == 0

    def show_back(self):
        return not self.on_first_step
