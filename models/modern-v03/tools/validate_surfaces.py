"""Check solid mesh surface intersections during hover and disc travel."""
from pathlib import Path
import bpy, json
from mathutils.bvhtree import BVHTree

root=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
assert scene.get('claire_model_version')=='modern-v03'
keys=('about','projects','world')
disc_meshes=[scene.objects['CD '+key+' solid optical substrate'] for key in keys]
card_meshes=[scene.objects['Independent '+key+' insert'] for key in keys]
lid=scene.objects['Lid outer silver shell']

def tree(obj):
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        return BVHTree.FromPolygons([evaluated.matrix_world@vertex.co for vertex in mesh.vertices],[tuple(triangle.vertices) for triangle in mesh.loop_triangles],all_triangles=True,epsilon=0.)
    finally:evaluated.to_mesh_clear()

issues=[]
for frame in range(135,521):
    scene.frame_set(frame)
    dt=[tree(obj) for obj in disc_meshes]
    ct=[tree(obj) for obj in card_meshes]
    lt=tree(lid)
    for i in range(3):
        if dt[i].overlap(lt):issues.append((frame,keys[i],'lid'))
        for j in range(i+1,3):
            if dt[i].overlap(dt[j]):issues.append((frame,keys[i],keys[j]+' disc'))
        for j in range(3):
            # Own sleeves legitimately contain their discs at the end of travel.
            if j != i and dt[i].overlap(ct[j]):issues.append((frame,keys[i],keys[j]+' sleeve'))
report={'passed':not issues,'frames_checked':386,'issues':issues,'method':'evaluated triangle BVH surface overlap; own sleeve contacts excluded'}
(root/'surface-validation-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SURFACE_CHECK',json.dumps(report))
