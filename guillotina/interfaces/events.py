from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import interfaces


class IObjectModifiedEvent(interfaces.IObjectEvent):
    """An object has been modified"""


class IObjectMovedEvent(interfaces.IObjectEvent):
    """An object has been moved."""

    old_parent = Attribute("The old location parent for the object.")
    old_name = Attribute("The old location name for the object.")
    new_parent = Attribute("The new location parent for the object.")
    new_name = Attribute("The new location name for the object.")


class IObjectAddedEvent(IObjectMovedEvent):
    """An object has been added to a container."""


class IObjectRemovedEvent(IObjectMovedEvent):
    """An object has been removed from a container."""


class IBeforeObjectAddedEvent(IObjectMovedEvent):
    """An object has been removed from a container."""


class IBeforeObjectRemovedEvent(IObjectMovedEvent):
    """An object has been removed from a container."""


class IObjectVisitedEvent(interfaces.IObjectEvent):
    """An object has been visited."""


class IObjectPermissionsViewEvent(interfaces.IObjectEvent):
    """An object permissions has been visited."""


class IObjectPermissionsModifiedEvent(interfaces.IObjectEvent):
    """An object permissions has been modified."""


class IFileFinishUploaded(interfaces.IObjectEvent):
    """A file has been finish uploaded."""


class INewUserAdded(Interface):
    """A new user logged in.

    The user is the id from the user logged in"""

    user = Attribute("User id created.")
