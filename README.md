# Framing-into-Smaller-section
Revit Check Beams

## Dynamo Python warning fix

If your Dynamo Python node reports:

`AttributeError: type object 'BuiltInParameter' has no attribute 'ALL_MODEL_INSTANCE_MARK'`

use `BuiltInParameter.ALL_MODEL_MARK` instead. In the Revit API, **Mark** is exposed as `ALL_MODEL_MARK`, not `ALL_MODEL_INSTANCE_MARK`.

### Example

```python
# old (throws AttributeError)
# mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_MARK)

# new
mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
mark_value = mark_param.AsString() if mark_param else None
```

### Optional safer fallback

```python
from Autodesk.Revit.DB import BuiltInParameter

mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)
if mark_param is None:
    # fallback by display name if needed for edge cases/localization-sensitive workflows
    mark_param = element.LookupParameter("Mark")
```
