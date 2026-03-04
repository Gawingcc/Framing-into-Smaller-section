"""Dynamo Python node helper for reading Revit element Mark values efficiently.

Fixes warning:
AttributeError: type object 'BuiltInParameter' has no attribute 'ALL_MODEL_INSTANCE_MARK'

Use BuiltInParameter.ALL_MODEL_MARK instead.
"""

import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import BuiltInParameter


# Dynamo provides UnwrapElement in the Python node runtime.
def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _read_mark(element):
    """Return Mark for one element, or None if missing/unreadable."""
    if element is None:
        return None

    # Correct built-in parameter for Mark.
    param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
    if param is not None and param.HasValue:
        value = param.AsString()
        if value:
            return value

    # Fallback when the built-in is unavailable for a given element/category.
    by_name = element.LookupParameter("Mark")
    if by_name is not None and by_name.HasValue:
        return by_name.AsString()

    return None


is_list_input = isinstance(IN[0], list)
wrapped_input = _as_list(IN[0])
elements = [UnwrapElement(item) for item in wrapped_input]

# Efficient single-pass read.
marks = [_read_mark(element) for element in elements]
OUT = marks if is_list_input else (marks[0] if marks else None)
