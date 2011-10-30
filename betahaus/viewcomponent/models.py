from zope.interface import implements
from zope.interface.interfaces import ComponentLookupError
from pyramid.security import has_permission
from pyramid.traversal import find_interface

from betahaus.viewcomponent.interfaces import IViewGroup


class ViewGroup(dict):
    """ Named utility for views. Behaves like a dict with some extra funkyness.
        See interfaces.py for documentation.
    """
    implements(IViewGroup)
    
    def __init__(self, perm_checker = None):
        if perm_checker is None:
            perm_checker = has_permission
        self.perm_checker = perm_checker
        self._order = []
    
    def __call__(self, context, request, **kw):
        results = []
        for va in self.get_context_vas(context, request):
            out = va(context, request, **kw)
            assert isinstance(out, basestring)
            results.append(out)
        return results

    def get_context_vas(self, context, request):
        for va in self.values():
            if va.interface and not va.interface.providedBy(context):
                continue
            if va.permission and not self.perm_checker(va.permission, context, request):
                continue
            if va.containment and not find_interface(context, va.containment):
                continue
            yield va

    def add(self, view_action):
        self[view_action.name] = view_action

    def __setitem__(self, key, value):
        assert isinstance(value, ViewAction)
        super(ViewGroup, self).__setitem__(key, value)
        if key not in self._order:
            self._order.append(key)

    def __delitem__(self, key):
        super(ViewGroup, self).__detitem__(key)
        if key in self._order:
            self._order.remove(key)

    def _get_order(self):
        return self._order
    def _set_order(self, value):
        handle_keys = set(self.order)
        value = [unicode(x) for x in value]
        for val in value:
            if val not in self:
                raise ValueError("You can't set order with key '%s' since it doesn't exist in this util." % val)
            handle_keys.remove(val)
        for unhandled_key in handle_keys:
            value.append(unhandled_key)
        self._order = value
    order = property(_get_order, _set_order)

    def keys(self):
        return self.order

    def __iter__(self):
        return iter(self.order)

    def values(self):
        return [self[key] for key in self.order]

    def items(self):
        return [(name, self[name]) for name in self.order]


class ViewAction(object):

    def __init__(self, _callable, name, title = u"",
                 permission = None, interface = None, containment = None, **kw):
        assert callable(_callable)
        assert isinstance(name, basestring)
        self.callable = _callable
        self.name = name
        self.title = title
        self.permission = permission
        self.interface = interface
        self.containment = containment
        self.kwargs = kw

    def __call__(self, context, request, **kw):
        return self.callable(context, request, self, **kw)

    def __repr__(self): # pragma : no cover
        klass = self.__class__
        classname = '%s.%s' % (klass.__module__, klass.__name__)
        return "<%s '%s'>" % (classname, self.name)