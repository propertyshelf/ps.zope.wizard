# -*- coding: utf-8 -*-
"""Allow traversal to widgets via the ++widget++ namespace."""

# zope imports
from z3c.form import util
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.traversing.interfaces import (
    ITraversable,
    TraversalError,
)

# local imports
from ps.zope.wizard.wizard import Wizard


@implementer(ITraversable)
@adapter(Wizard, IBrowserRequest)
class WizardWidgetTraversal(object):
    """Allow traversal to widgets via the ++widget++ namespace."""

    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def _prepareForm(self):
        self.context.update()
        for step in self.context.active_steps:
            step.update()
        return self.context

    def traverse(self, name, ignored):  # noqa
        form = self._prepareForm()

        # Since we cannot check security during traversal,
        # we delegate the check to the widget view.
        # alsoProvides(self.request, IDeferSecurityCheck)
        form.update()
        # noLongerProvides(self.request, IDeferSecurityCheck)

        # If name begins with form.widgets., remove it
        form_widgets_prefix = util.expandPrefix(
            form.prefix) + util.expandPrefix(form.widgets.prefix)
        if name.startswith(form_widgets_prefix):
            name = name[len(form_widgets_prefix):]

        # Split string up into dotted segments and work through
        target = form
        parts = name.split('.')
        while len(parts) > 0:
            part = parts.pop(0)
            # i.e. a z3c.form.widget.MultiWidget
            if isinstance(getattr(target, 'widgets', None), list):
                try:
                    # part should be integer index in list, look it up
                    target = target.widgets[int(part)]
                except IndexError:
                    raise TraversalError("'" + part + "' not in range")
                except ValueError:
                    # HACK: part isn't integer. Iterate through widgets to
                    # find matching name. This is required for
                    # DataGridField, which appends 'AA' and 'TT' rows to
                    # it's widget list.
                    full_name = util.expandPrefix(target.prefix) + part
                    filtered = [w for w in target.widgets
                                if w.name == full_name]
                    if len(filtered) == 1:
                        target = filtered[0]
                    else:
                        raise TraversalError("'" + part + "' not valid index")
            elif hasattr(target, 'widgets'):  # Either base form, or subform
                # Check to see if we can find a "Behaviour.widget"
                new_target = None
                if len(parts) > 0:
                    new_target = self._form_traverse(
                        target,
                        part +
                        '.' +
                        parts[0])

                if new_target is not None:
                    # Remove widget name from stack too
                    parts.pop(0)
                else:
                    # Find widget in form without behaviour prefix
                    new_target = self._form_traverse(target, part)

                target = new_target
            # subform-containing widget, only option is to go into subform
            elif hasattr(target, 'subform'):
                if part == 'widgets':
                    target = target.subform
                else:
                    target = None
            else:
                raise TraversalError(
                    'Cannot traverse through ' +
                    target.__repr__())

            # Could not traverse from target to part
            if target is None:
                raise TraversalError(part)

        # Make the parent of the widget the traversal parent.
        # This is required for security to work in Zope 2.12
        if target is not None:
            target.__parent__ = self.context
            return target
        raise TraversalError(name)

    def _form_traverse(self, form, name):
        """Look for name within a form."""
        # If we have a current step, look for the widget here first.
        if getattr(form, 'current_step', None) is not None:
            if name in form.current_step.widgets:
                return form.current_step.widgets.get(name)

        # Now check the parent (wizard) form.
        if name in form.widgets:
            return form.widgets.get(name)

        # If there are no groups, give up now.
        if getattr(form, 'groups', None) is None:
            return None

        for group in form.groups:
            if group.widgets and name in group.widgets:
                return group.widgets.get(name)
