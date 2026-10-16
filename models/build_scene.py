import bpy, math, os, json
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def mat(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 return m
cream=mat('Warm enamel',(0.78,.73,.60)); red=mat('Tomato lacquer',(.62,.045,.028)); blue=mat('Cobalt',(.025,.12,.48)); pink=mat('Paper pink',(.85,.39,.48)); green=mat('Leaf',(.13,.35,.19)); gold=mat('Brushed metal',(.6,.46,.22),.8,.25); black=mat('Vinyl',(.012,.015,.02),.15,.24); paper=mat('Ivory card',(.91,.87,.74)); ink=mat('Ink',(.025,.025,.034)); yellow=mat('Butter yellow',(.95,.66,.08))
def cube(name,loc,scale,material,bevel=.05):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material)
 if bevel: mod=o.modifiers.new('Rounded edges','BEVEL'); mod.width=bevel; mod.segments=3; o.modifiers.new('Normals','WEIGHTED_NORMAL')
 return o
def cyl(name,loc,r,depth,material):
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r,depth=depth,location=loc); o=bpy.context.object; o.name=name; o.data.materials.append(material); o.modifiers.new('Edge','BEVEL').width=.015; o.modifiers.new('Normals','WEIGHTED_NORMAL'); return o
def line(name,pts,material,r=.025):
 c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=r; c.bevel_resolution=3; s=c.splines.new('POLY'); s.points.add(len(pts)-1)
 for p,co in zip(s.points,pts): p.co=(*co,1)
 o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(material); return o
def text(body,loc,size,material,rot=(math.pi/2,0,0)):
 c=bpy.data.curves.new(body,'FONT'); c.body=body; c.size=size; c.extrude=.001; o=bpy.data.objects.new(body,c); bpy.context.collection.objects.link(o); o.location=loc; o.rotation_euler=rot; o.data.materials.append(material); return o
def sphere(name,loc,r,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=r,location=loc); o=bpy.context.object; o.name=name; o.data.materials.append(material); return o
def torus(name,loc,r,minor,material):
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=minor,major_segments=96,minor_segments=6,location=loc); o=bpy.context.object; o.name=name; o.data.materials.append(material); return o
cube('Player body',(0,0,.12),(3.5,2.6,.36),red,.13); cube('Top panel',(0,0,.32),(3.38,2.48,.08),cream,.09)
cyl('Platter',(-.42,0,.43),1.05,.12,gold)
def disc(name,center,color,vertical=False):
 root=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(root); root.location=center
 obs=[cyl(name+' vinyl',(0,0,0),.99,.035,black),cyl(name+' printed label',(0,0,.023),.68,.005,color),cyl(name+' centre',(0,0,.03),.22,.008,paper)]
 for r in [.73,.77,.82,.86,.90,.94]: obs.append(torus('Groove',(0,0,.02),r,.0025,gold))
 count=8 if '01' in name else 12 if '02' in name else 6
 for i in range(count):
  a=i*math.tau/count; x,y=.48*math.cos(a),.48*math.sin(a)
  if '03' in name:
   obj=cyl('Flower sticker centre',(x,y,.033),.035,.007,yellow); obs.append(obj)
   for j in range(5):
    b=j*math.tau/5;obs.append(cyl('Flower sticker petal',(x+.058*math.cos(b),y+.058*math.sin(b),.031),.04,.006,pink))
  else:
   obj=cube('Individual collage patch',(x,y,.03),(.20,.14,.006),[pink,yellow,blue,green][i%4],.008); obj.rotation_euler.z=a
   obs.append(obj)
   if '01' in name:
    obj=text('CLAIRE'[i%6],(x-.06,y-.05,.037),.11,ink,(0,0,a));obs.append(obj)
 obs.append(cyl('Spindle hole',(0,0,.04),.035,.01,ink))
 for o in obs:o.parent=root
 if vertical:root.rotation_euler=(math.pi/2,0,0)
 return root
active=disc('01 About Claire',(-.42,0,.515),pink); cyl('Spindle',(-.42,0,.58),.028,.11,gold)
cyl('Tonearm pivot',(1.12,.72,.47),.18,.18,gold); line('Tonearm',[(1.12,.72,.59),(1.2,.38,.59),(.48,-.53,.59)],gold,.045); cube('Cartridge',(.43,-.61,.57),(.2,.29,.12),blue,.02)
for x in [1.12,1.48]:cyl('Control',(x,-.93,.44),.105,.13,gold)
# Lid is a real hinged separate object; keyed for the entrance.
glass=mat('Transparent acrylic',(.75,.88,.9),0,.12); p=glass.node_tree.nodes.get('Principled BSDF'); p.inputs['Transmission Weight'].default_value=.92; p.inputs['IOR'].default_value=1.46
hinge=bpy.data.objects.new('Lid hinge animation',None); bpy.context.collection.objects.link(hinge); hinge.location=(0,1.25,.38)
lid=cube('Acrylic lid',(0,-1.25,.05),(3.5,2.6,.10),glass,.06); lid.parent=hinge
for x in [-1.72,1.72]:
 o=line('Lid side rim',[(x,0,.07),(x,-2.5,.07)],gold,.017); o.parent=hinge
for y in [0,-2.5]:
 o=line('Lid cross rim',[(-1.72,y,.07),(1.72,y,.07)],gold,.017); o.parent=hinge
hinge.rotation_euler.x=0; hinge.keyframe_insert('rotation_euler',frame=1); hinge.rotation_euler.x=math.radians(-68); hinge.keyframe_insert('rotation_euler',frame=65)
for x in [-1.25,1.25]:cyl('Hinge hardware',(x,1.15,.39),.07,.14,gold)
# S ribbon, two occupied positions and one permanently identified now-playing sleeve.
for offset in [-.10,0,.10]:
 pts=[(-2.7+.33*math.sin(i/70*math.tau)+offset,.65, .3+i/70*3.5) for i in range(71)]; line('S ribbon rail',pts,blue,.025)
def sleeve(name,x,z,color,subtitle):
 cube(name+' sleeve',(x,.46,z),(1.6,.045,1.6),paper,.008)
 cube(name+' patch',(x,.425,z+.39),(1.36,.014,.41),color,.004)
 text(name,(x-.62,.409,z+.29),.21,ink)
 text(subtitle,(x-.61,.406,z+.05),.09,ink)
 for i in range(4):
  patch=cube('Cutout letter tile',(x-.49+i*.32,.403,z-.38),(.27,.015,.29),[yellow,pink,green,blue][i],.006)
  text(['C','L','A','I'][i],(x-.57+i*.32,.39,z-.46),.23,paper)
sleeve('02 MAKE',-2.85,2.82,yellow,'GROWTH / RAG / FOCUS')
sleeve('03 LIFE',-2.7,1.02,green,'MUSIC / FLOWERS / LITTLE THINGS')
disc('02 Projects',(-2.23,.30,2.77),yellow,True); disc('03 My world',(-2.08,.30,.99),green,True)
for x,z in [(-2.85,2.82),(-2.7,1.02)]:
 line('Individual open cradle',[(x-.85,.2,z-.85),(x+.9,.2,z-.85)],blue,.04)
sleeve('01 CLAIRE',2.9,1.4,pink,'HELLO / DATA SCIENCE / AI')
text('NOW PLAYING',(2.15,.39,.37),.105,red)
# A small playlist card is a layout placeholder, independent of the three records.
cube('Playlist paper',(4.0,.75,2.88),(1.65,.055,1.45),paper,.035)
text('ON REPEAT',(3.29,.707,3.42),.18,red)
for i,s in enumerate(['Star Crossing Night','thank u, next','Setsunahanabi','The Other Side of Paradise',"We Don't Talk Anymore","Creepin Up on You"]):text(s,(3.29,.705,3.14-i*.16),.083,ink)
text('PLAY  /  PAUSE',(3.29,.705,2.16),.10,blue)
# Two subordinate ornaments: bead-inspired flower and tomato collectible.
cyl('Flower core',(-4,-.3,.83),.14,.10,yellow).rotation_euler.x=math.pi/2
for i in range(6):
 a=i*math.tau/6;sphere('Flower petal',(-4+.23*math.cos(a),-.3,.83+.23*math.sin(a)),.13,pink)
line('Flower stem',[(-4,-.3,.15),(-4,-.3,.7)],green,.03)
sphere('Tomato mascot',(2.8,-.8,.32),.23,red)
for i in range(5):a=i*math.tau/5;line('Leaf',[(2.8,-.8,.54),(2.8+.17*math.cos(a),-.8+.17*math.sin(a),.59)],green,.025)
# Background plane lies behind everything, no horizontal table or display base.
bg=mat('Soft textured backdrop',(.72,.69,.59)); nodes=bg.node_tree.nodes; links=bg.node_tree.links
n=nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value=3; n.inputs['Detail'].default_value=4
r=nodes.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.50,.58,.60,1);r.color_ramp.elements[1].color=(.87,.80,.65,1);links.new(n.outputs['Fac'],r.inputs[0]);links.new(r.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
cube('Backdrop',(0,4,2),(200,.1,200),bg,0)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.world.color=(.25,.25,.25)
def area(name,loc,power,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
area('Key',(-4,-5,8),1100,7);area('Fill',(5,-2,5),750,5);area('Rim',(0,2,7),900,4)
bpy.ops.object.camera_add(location=(8,-13,10));cam=bpy.context.object;cam.name='Hero camera';cam.rotation_euler=(Vector((.1,.15,1.7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=12;scene.camera=cam
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.frame_end=100;scene.frame_set(80)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'claire-vinyl-v01.blend'))
scene.render.filepath=os.path.join(OUT,'hero-v01.png');bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
 if o.type in {'MESH','CURVE','FONT'}:
  pos=o.matrix_world.translation
  if abs(pos.x)>1.8 or o.name.startswith(('S ribbon','Individual open cradle')):o.hide_render=True
cam.location=(0,-.01,10);cam.rotation_euler=(0,0,0);cam.data.ortho_scale=4.9;scene.frame_set(1)
scene.render.filepath=os.path.join(OUT,'opening-top-v01.png');bpy.ops.render.render(write_still=True)
print('DONE: hero and opening renders saved')
