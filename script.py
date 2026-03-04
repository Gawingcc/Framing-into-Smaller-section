# Load the Python Standard and DesignScript Libraries
import sys
import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

# The inputs to this node will be stored as a list in the IN variables.
dataEnteringNode = IN

# Place your code below this line

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
import System.Collections.Generic as Generic

clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

import os
import datetime

doc = DocumentManager.Instance.CurrentDBDocument

def get_beam_depth(beam):
    """Gets the depth of a beam from its type parameters."""
    b_type = doc.GetElement(beam.GetTypeId())
    for p_name in ["h", "d", "Height", "Depth", "Structural Section Height"]:
        p = b_type.LookupParameter(p_name)
        if p and p.HasValue:
            return p.AsDouble()
    bbox = beam.get_BoundingBox(None)
    if bbox:
        return bbox.Max.Z - bbox.Min.Z
    return 0

# REMOVED COLON (:) as it is a prohibited character in Revit filter names
FILTER_NAME = "REVIEW-Large Framing into Small"
MARK_VALUE = "Mismatched Support"

# 1. Collect all Structural Framing (Beams)
all_beams = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFraming).WhereElementIsNotElementType().ToElements()

problematic_beams = []
report_data = []

endpoint_map = {}

for b in all_beams:
    if not hasattr(b, 'Location') or not b.Location.Curve: continue
    curve = b.Location.Curve
    p0 = curve.GetEndPoint(0)
    p1 = curve.GetEndPoint(1)
    for p in [p0, p1]:
        key = (round(p.X, 3), round(p.Y, 3), round(p.Z, 3))
        if key not in endpoint_map:
            endpoint_map[key] = []
        endpoint_map[key].append(b)

# 2. Analyze Connections
for beam in all_beams:
    if not hasattr(beam, 'Location') or not beam.Location.Curve: continue
    curve = beam.Location.Curve
    depth = get_beam_depth(beam)
    is_problematic = False
    supporting_info = ""
    
    for i in [0, 1]:
        pt = curve.GetEndPoint(i)
        key = (round(pt.X, 3), round(pt.Y, 3), round(pt.Z, 3))
        neighbors = endpoint_map.get(key, [])
        for nb in neighbors:
            if nb.Id == beam.Id: continue
            nb_depth = get_beam_depth(nb)
            if nb_depth > 0 and nb_depth < (depth - 0.01):
                is_problematic = True
                supporting_info = "{:.3f}".format(nb_depth)
                break
        if is_problematic: break
    
    if is_problematic:
        problematic_beams.append(beam)
        mark_param = beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        mark = mark_param.AsString() if mark_param and mark_param.HasValue else ""
        type_name = doc.GetElement(beam.GetTypeId()).get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        report_data.append("{},{},{},{:.3f},{}".format(beam.Id.IntegerValue, mark, type_name, depth, supporting_info))

# 3. Automated Tagging and Filter Creation
TransactionManager.Instance.EnsureInTransaction(doc)

for beam in problematic_beams:
    comment_param = beam.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if comment_param and comment_param.IsReadOnly == False:
        comment_param.Set(MARK_VALUE)

cat_list = Generic.List[ElementId]()
cat_list.Add(ElementId(BuiltInCategory.OST_StructuralFraming))

existing_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement).ToElements()
my_filter = next((f for f in existing_filters if f.Name == FILTER_NAME), None)

if not my_filter:
    rule = ParameterFilterRuleFactory.CreateEqualsRule(ElementId(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS), MARK_VALUE, True)
    filter_rule = ElementParameterFilter(rule)
    my_filter = ParameterFilterElement.Create(doc, FILTER_NAME, cat_list, filter_rule)

TransactionManager.Instance.TransactionTaskDone()

# 4. Generate CSV Report on Desktop
report_status = ""
try:
    desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    
    # Create Desktop directory if it doesn't exist
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path)
    
    report_path = os.path.join(desktop_path, "Beam_Support_Review.csv")
    
    with open(report_path, 'w') as f:
        f.write("Beam ID,Mark,Type Name,Beam Depth (ft),Supporting Depth (ft)\n")
        f.write("\n".join(report_data))
    
    report_status = "Report saved to: " + report_path
except Exception as e:
    report_status = "Error: " + str(e)

OUT = "Found {} issues. Filter '{}' ready. {}".format(len(problematic_beams), FILTER_NAME, report_status)
