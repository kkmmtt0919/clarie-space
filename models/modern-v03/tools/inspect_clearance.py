"""Exact oriented-box separation test for the three rigid paper inserts."""
import bpy, json
from mathutils import Vector
from pathlib import Path
scene=bpy.context.scene
cards=[scene.objects['Independent '+key+' insert'] for key in ('about','projects','world')]

def intersects(a,b):
    pa=[a.matrix_world@Vector(v) for v in a.bound_box]
    pb=[b.matrix_world@Vector(v) for v in b.bound_box]
    aa=[(a.matrix_world.to_3x3()@Vector(axis)).normalized() for axis in ((1,0,0),(0,1,0),(0,0,1))]
    ab=[(b.matrix_world.to_3x3()@Vector(axis)).normalized() for axis in ((1,0,0),(0,1,0),(0,0,1))]
    for axis in aa+ab+[u.cross(v) for u in aa for v in ab]:
        if axis.length<1e-8:continue
        ap=[v.dot(axis) for v in pa]; bp=[v.dot(axis) for v in pb]
        if max(ap)<min(bp)-1e-5 or max(bp)<min(ap)-1e-5:return False
    return True

hits=[]
for frame in range(135,391):
    scene.frame_set(frame)
    for i in range(3):
        for j in range(i+1,3):
            if intersects(cards[i],cards[j]):hits.append((frame,i,j))
print('CARD_INTERSECTIONS',hits)
print('CARD_HOMES',scene['claire_card_home_poses'])
print('HOVER_DIRECTION',list(scene['claire_hover_direction']))
(Path(__file__).resolve().parents[1]/'clearance-report.json').write_text(json.dumps({'passed':not hits,'intersections':hits},indent=2),encoding='utf-8')
