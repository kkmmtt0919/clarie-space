import bpy,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
root=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
names=json.loads(scene['claire_root_names']);discs=[bpy.data.objects[n] for n in names['discs']];cards=[bpy.data.objects[n] for n in names['cards']]
assert len(discs)==3 and len(cards)==3
assert len([o for o in scene.objects if o.get('is_navigation_disc')])==3
assert not any('tonearm' in o.name.lower() for o in scene.objects)
assert all(bpy.data.images.get('disc-'+k+'.png').packed_file for k in ['about','projects','world'])
assert bpy.data.texts.get('claire_preview_runtime.py')
assert all(d.children_recursive for d in discs)
scene.frame_set(1); assert abs(bpy.data.objects[names['hinge']].rotation_euler.x)<1e-5
shell=bpy.data.objects['Lid outer silver shell'];points=[world_to_camera_view(scene,scene.camera,shell.matrix_world@Vector(p)) for p in shell.bound_box]
assert all(.005<p.x<.995 and .005<p.y<.995 for p in points),'Opening camera crops closed player'
scene.frame_set(135);a=discs[0].location.copy();baseline=cards[1].location.copy()
assert math.isclose(bpy.data.objects[names['hinge']].rotation_euler.x,math.radians(-78),abs_tol=1e-5)
scene.frame_set(163)
assert (discs[0].location-a).length<1e-5,'Hover moved playing disc'
assert (cards[1].location-baseline).length>.2
assert cards[1].scale.x>1.02
camera_dir=(scene.camera.location-Vector((.8,.7,1.6))).normalized()
assert cards[1].location.dot(camera_dir)>cards[2].location.dot(camera_dir),'Hovered project does not come to front'
scene.frame_set(135)
for i in [1,2]:
    normal=cards[i].rotation_euler.to_quaternion()@Vector((0,-1,0))
    assert abs((cards[i].location-cards[i-1].location).dot(normal))>.06,'Parallel cards intersect'
scene.frame_set(350)
target=json.loads(scene['claire_player_disc_pose'])
assert (discs[1].location-Vector(target['loc'])).length<1e-5
assert scene.objects['Playing marker / about'].hide_render
assert not scene.objects['Playing marker / projects'].hide_render
scene.frame_set(135)
report={'passed':True,'disc_count':3,'cards':3,'opening_camera_fits':True,'lid_opens':True,'hover_keeps_active_disc':True,'hover_front_depth':True,'card_planes_separated':True,'swap_projects_in_player':True,'images_packed':True,'runtime_packed':True}
(root/'validation-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CLAIRE_MODEL_VALIDATED',json.dumps(report))
