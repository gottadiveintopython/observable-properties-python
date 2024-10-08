# ****************************************************************************
# @file observable_properties.py
#
# @author Ángel Fernández Pineda. Madrid. Spain.
# @date 2024-01-26
# @brief Observable managed attributes
# @copyright 2024. Ángel Fernández Pineda. Madrid. Spain.
# @license Licensed under the EUPL
# *****************************************************************************

"""Observable object properties

Declare observable properties using the `@observable` decorator instead of `@property`.
Subscribe/unsubscribe any number of callback functions to observable properties.
If the value of an observable property changes, all subscribed observers are executed.

Functions:
    subscribe(): subscribe a callback to changes in observable properties.
    unsubscribe(): unsubscribe a callback to changes in observable properties.

Classes:
    Observable: helper class for easy subscription to observable properties.

Types:
    Observer: callback prototype for observable properties.

Exceptions:
    ObservablePropertyError: for invalid operations on observable object properties.
"""

# *****************************************************************************
# "Exports"
# *****************************************************************************

__all__ = [
    "subscribe",
    "unsubscribe",
    "Observable",
    "ObservablePropertyError",
    "observable",
    "Observer",
]

# *****************************************************************************
# Imports
# *****************************************************************************

from typing import Callable, Any
from contextlib import contextmanager

# *****************************************************************************
# Types
# *****************************************************************************

Observer = Callable[[object, str, Any], None]
"""Callback prototype for observable properties.

Args:
    instance (object): object being observed
    property_name (str): name of the property that changes
    value (Any): new value of the property

Raises:
    ObservablePropertyError: attempt to modify the property being observed.
"""

# *****************************************************************************
# Exceptions
# *****************************************************************************


class ObservablePropertyError(Exception):
    """Exception for invalid operations on observable object properties."""

    pass


# *****************************************************************************
# Classes
# *****************************************************************************


class observable(property):
    def __execute_callbacks(
        self, __instance: Any, __value: Any, subscribers: list, recursions: list
    ):
        for observer in subscribers:
            if observer not in recursions:
                recursions.append(observer)
                observer(__instance, self.observable_property, __value)
            else:
                raise ObservablePropertyError(
                    f"'{observer.__name__}' is not allowed to modify observable property "
                    + f"'{__instance.__class__.__name__}.{self.observable_property}'"
                )

    def _run_observers(self, __instance: Any, __value: Any):
        subscribers = getattr(__instance, self.subscribers)
        recursions = getattr(__instance, self.recursions)
        try:
            self.__execute_callbacks(__instance, __value, subscribers, recursions)
        finally:
            recursions.clear()

    def __set__(self, __instance: Any, __value: Any) -> None:
        subscribers = getattr(__instance, self.subscribers)
        recursions = getattr(__instance, self.recursions)
        try:
            super().__set__(__instance, __value)
            self.__execute_callbacks(__instance, __value, subscribers, recursions)
        finally:
            recursions.clear()

    def __delete__(self, __instance: Any) -> None:
        super().__delete__(__instance)
        delattr(__instance, self.subscribers)
        delattr(__instance, self.recursions)

    def __set_name__(self, owner, owner_name):
        self.observable_property = owner_name
        self.subscribers = f"__{owner_name}_subscribers"
        self.recursions = f"__{owner_name}_recursions"
        if not hasattr(owner, self.subscribers):
            setattr(owner, self.subscribers, [])
        if not hasattr(owner, self.recursions):
            setattr(owner, self.recursions, [])


class Observable:
    """Helper class for easy subscription to observable properties."""

    def subscribe(self, property_name: str, callback: Observer) -> None:
        """Subscribe a callback to changes in observable properties of this object.

        Args:
            property_name (str): name of the property to observe in this object.
            callback (Callable[[object, str, Any], None]): function to subscribe.

        Raises:
            ObservablePropertyError: if the requested property is not observable or does not exist.
        """
        return subscribe(callback, self, property_name)

    def unsubscribe(self, property_name: str, callback: Observer) -> bool:
        """Unsubscribe a callback to changes in an observable property of this object.

        Args:
            callback (Callable[[object, str, Any], None]): function to be called.
            property_name (str): name of the observed property.

        Returns:
            bool: True on success. If false, the property is not observable or does not exist.
        """
        return unsubscribe(callback, self, property_name)

    def _observable_notify(self, property_name: str) -> None:
        """Run subscribers (if any) of an observable property.

        Args:
            property_name (str): name of the property that changes.

        Raises:
            ObservablePropertyError: if the given property is not observable or does not exist.
        """
        vrs = vars(self.__class__)
        if (property_name in vrs) and isinstance(vrs[property_name], observable):
            vrs[property_name]._run_observers(self, getattr(self, property_name))
        else:
            raise ObservablePropertyError(
                f"'{property_name}' is not an observable property of '{self.__class__.__name__}'"
            )

    @contextmanager
    def _observable(self, property_name: str):
        """Run subscribers (if any) of an observable property on context exit.

        Args:
            property_name (str): name of the property that changes.

        Raises:
            ObservablePropertyError: if the given property is not observable or does not exist.
        """
        yield
        self._observable_notify(property_name)


# *****************************************************************************
# "public" functions
# *****************************************************************************


def subscribe(
    callback: Observer, instance: object, property_name: str
) -> None:
    """Subscribe a callback to changes in observable properties.

    Args:
        callback (Callable[[object, str, Any], None]): function to subscribe.
        instance (object): instance to observe.
        property_name (str): name of the property to observe at the given instance.

    Raises:
        ObservablePropertyError: if the requested property is not observable or does not exist.
    """
    unsubscribe(callback, instance, property_name)
    subscribers_attr_name = f"__{property_name}_subscribers"
    subscribers = getattr(instance, subscribers_attr_name)
    subscribers.append(callback)


def unsubscribe(callback: Observer, instance: object, property_name: str) -> bool:
    """Unsubscribe a callback from changes in observable properties.

    Args:
        callback (Callable[[object, str, Any], None]): function to unsubscribe.
        instance (object): observed instance.
        property_name (str): name of the observed property at the given instance.

    Returns:
         bool: True on success. False if the callback was not subscribed.

    Raises:
        ObservablePropertyError: if the requested property is not observable or does not exist.
    """
    subscribers_attr_name = f"__{property_name}_subscribers"
    if hasattr(instance, subscribers_attr_name):
        subscribers = getattr(instance, subscribers_attr_name)
        if callback in subscribers:
            subscribers.remove(callback)
            return True
        else:
            return False
    else:
        raise ObservablePropertyError(
            f"'{property_name}' is not an observable property of '{instance.__class__.__name__}'"
        )
