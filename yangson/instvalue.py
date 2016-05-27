"""This module contains classes andtype aliases representing instance values."""

from datetime import datetime
from typing import List, Union
from .datatype import *

# Local type aliases

Value = Union[ScalarValue, "ArrayValue", "ObjectValue"]

class StructuredValue:
    """Abstract class for array and object values."""

    def __init__(self, ts: datetime) -> None:
        """Initialize class instance.

        :param ts: creation timestamp
        """
        self.timestamp = ts if ts else datetime.now()

    def stamp(self) -> None:
        """Update the receiver's timestamp to current time."""
        self.timestamp = datetime.now()

    def __eq__(self, val: "StructuredValue") -> bool:
        """Return ``True`` if the receiver equal to `val`.

        :param val: value to compare
        """
        return self.__class__ == val.__class__ and hash(self) == hash(val)

class ArrayValue(StructuredValue, list):
    """Array values corresponding to YANG lists and leaf-lists."""

    def __init__(self, val: List[Value], ts: datetime=None):
        StructuredValue.__init__(self, ts)
        list.__init__(self, val)

    def __hash__(self) -> int:
        """Return integer hash value for the receiver."""
        return tuple([ x.__hash__() for x in self]).__hash__()

class ObjectValue(StructuredValue, dict):
    """Array values corresponding to YANG container."""

    def __init__(self, val: Dict[InstanceName, Value], ts: datetime = None):
        StructuredValue.__init__(self, ts)
        dict.__init__(self, val)

    def __hash__(self) -> int:
        """Return integer hash value for the receiver."""
        sks = sorted(self.keys())
        return tuple([ (k, self[k].__hash__()) for k in sks ]).__hash__()