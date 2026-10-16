"""Build an independent, packed Blender cork-board scene and web renders."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'models'/'world-board-v01'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Warm studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.6,.64,.69,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5

def plain(name,color,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
def textured(name,colors,scale,bump,wood=False):
 m=plain(name,colors[0]);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.8
 coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(1,25,4) if wood else (1,1,1)
 l.new(coord.outputs['Generated'],mapping.inputs[0]);l.new(mapping.outputs[0],tex.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.25;ramp.color_ramp.elements[0].color=(*colors[0],1);ramp.color_ramp.elements[1].position=.75;ramp.color_ramp.elements[1].color=(*colors[1],1)
 l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
 b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.55;b.inputs['Distance'].default_value=bump;l.new(tex.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
 return m
cork=textured('Natural cork granules',[(.28,.115,.037),(.68,.39,.16)],130,.045)
wood=textured('Honey oak grain',[(.31,.12,.036),(.74,.44,.19)],4,.025,True)
paper=plain('Warm photo paper',(.94,.925,.87),.8)
red=plain('Cherry enamel pushpin',(.65,.025,.035),.24)
steel=plain('Pin steel',(.45,.48,.5),.23,.85)
decor=[];board=[];pins=[]
def box(name,loc,size,mat,bevel=.02):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:mod=o.modifiers.new('Rounded edges','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
board.append(box('Cork board', (0,0,0),(8,9.7,.16),cork))
for name,loc,size in [('Left',(-4.04,0,.12),(.32,9.46,.32)),('Right',(4.04,0,.12),(.32,9.46,.32)),('Top',(0,4.89,.12),(8.4,.32,.32)),('Bottom',(0,-4.89,.12),(8.4,.32,.32))]:board.append(box('Oak frame '+name,loc,size,wood,.025))
def pin(x,y,z):
 group=[]
 for name,radius,depth,zz,mat in [('Needle',.018,.18,z,steel),('Foot',.105,.065,z+.1,red),('Stem',.065,.14,z+.19,red),('Cap',.13,.075,z+.29,red)]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=radius,depth=depth,location=(x,y,zz));o=bpy.context.object;o.name='Pushpin '+name;o.data.materials.append(mat);mod=o.modifiers.new('Soft enamel edge','BEVEL');mod.width=.015;mod.segments=3;o.modifiers.new('Smooth normals','WEIGHTED_NORMAL');group.append(o)
 pins.extend(group);return group
font=bpy.data.fonts.load('C:/Windows/Fonts/msyh.ttc') if Path('C:/Windows/Fonts/msyh.ttc').exists() else None
ink=plain('Printed charcoal',(.04,.045,.035),.9)
def text(body,x,y,z,size=.18):
 c=bpy.data.curves.new(body,'FONT');c.body=body;c.size=size;c.align_x='CENTER';c.align_y='CENTER';c.space_character=1.1
 if font:c.font=font
 o=bpy.data.objects.new(body,c);scene.collection.objects.link(o);o.location=(x,y,z);o.data.materials.append(ink);decor.append(o);return o
decor.append(box('Title note',(0,3.65,.14),(4.8,1.1,.025),paper))
text('第三章 · 我的世界',0,3.78,.161,.38)
text('手作、新体验，还有日常。',0,3.35,.161,.19)
pin(0,4.23,.16)
items=[('world-beads.jpg','六小时的战利品',-.85,1.05,-4,1.95,3.25),('world-flowers.jpg','毕业那天的花',-2.9,-.5,3,1.95,3.35),('world-miniature.jpg','一起做的小世界',1,-2.1,2,2.65,2.4),('world-letter.jpg','朋友给我的信',2.75,.6,-3,1.95,3.25)]
for file,label,x,y,angle,pw,ph in items:
 bpy.ops.object.empty_add(location=(x,y,.17));parent=bpy.context.object;parent.name='Photo group '+label;decor.append(parent)
 backing=box('Photo paper '+label,(0,0,0),(pw,ph,.025),paper);backing.parent=parent;backing.location=(0,0,0);decor.append(backing)
 image=bpy.data.images.load(str(ROOT/'assets'/file));image.pack();ratio=image.size[0]/image.size[1];w=min(pw-.1,(ph-.35)*ratio);h=w/ratio
 bpy.ops.mesh.primitive_plane_add(size=1);photo=bpy.context.object;photo.name='Original photo '+label;photo.parent=parent;photo.location=(0,.1,.017);photo.scale=(w,h,1)
 m=plain('Photo ink '+label,(1,1,1));p=m.node_tree.nodes.get('Principled BSDF');tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.7;photo.data.materials.append(m);decor.append(photo)
 labelObj=text(label,0,-ph/2+.14,.019,.115);labelObj.parent=parent
 parent.rotation_euler.z=math.radians(angle)
 # Pin at the rotated top edge.
 a=parent.rotation_euler.z;pin(x-math.sin(a)*(ph/2-.06),y+math.cos(a)*(ph/2-.06),.2)

def aim(o,point):o.rotation_euler=(Vector(point)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(0,0,18));cam=bpy.context.object;cam.name='Board orthographic';cam.data.type='ORTHO';cam.data.ortho_scale=10.1;aim(cam,(0,0,0));scene.camera=cam
bpy.ops.object.light_add(type='AREA',location=(-3,4,8));light=bpy.context.object;light.data.energy=900;light.data.shape='DISK';light.data.size=7;aim(light,(0,0,0))
scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene['claire_component']='world-board-v01';scene['photo_files']=json.dumps([item[0] for item in items]);scene['source_preservation']='Independent scene; modern-v03 and all archives remain unchanged.'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'claire-world-board-v01.blend'))
scene.render.filepath=str(OUT/'board-with-photos.png');bpy.ops.render.render(write_still=True)
for o in decor+pins:o.hide_render=True
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.quality=90;scene.render.film_transparent=False
scene.render.filepath=str(ROOT/'assets'/'world-cork-board.jpg');bpy.ops.render.render(write_still=True)
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
for o in board:o.hide_render=True
sample=pin(0,0,.2)
cam.location=(0,-2,5);aim(cam,(0,0,.3));cam.data.ortho_scale=.65
scene.render.resolution_x=160;scene.render.resolution_y=160;scene.render.filepath=str(ROOT/'assets'/'world-pushpin.png');bpy.ops.render.render(write_still=True)
print('WORLD_BOARD_COMPLETE',str(OUT))
