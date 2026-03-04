import clr

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import BuiltInParameter

clr.AddReference("System")
from System.Collections import IList


def _is_sequence(value):
    """True for Python lists and .NET IList, excluding strings."""
    if value is None:
        return False
    if isinstance(value, (str, bytes)):
        return False
    return isinstance(value, list) or isinstance(value, IList)


def _as_iterable(value):
    if value is None:
        return []
    if _is_sequence(value):
        return value
    return [value]


def _read_mark(element):
    if element is None:
        return None

    # Correct Revit API enum name for Mark.
    mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
    if mark_param and mark_param.HasValue:
        mark_value = mark_param.AsString()
        if mark_value:
            return mark_value

    # Fallback only when needed.
    mark_by_name = element.LookupParameter("Mark")
    if mark_by_name and mark_by_name.HasValue:
        return mark_by_name.AsString()

    return None


input_data = IN[0] if len(IN) > 0 else None
is_input_sequence = _is_sequence(input_data)

marks = []
for item in _as_iterable(input_data):
    marks.append(_read_mark(UnwrapElement(item)))

OUT = marks if is_input_sequence else (marks[0] if marks else None)
