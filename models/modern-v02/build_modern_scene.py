"""Rebuild Claire's modern studio as editable geometry; Blender 5.2.

No existing .blend is opened or overwritten. All output belongs to modern-v02.
"""
import bpy, math, json, os
from pathlib import Path
from mathutils import Vector, Euler

OUT = Path(__file__).resolve().parent
ASSETS = OUT / 'assets'
OUT.mkdir(exist_ok=True)
RENDER = os.environ.get('CLAIRE_RENDER', '1') == '1'
SAMPLES = int(os.environ.get('CLAIRE_SAMPLES', '48'))
RES = int(os.environ.get('CLAIRE_RES', '1400'))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
default_collection = bpy.data.collections.get('Collection')
COLLS = {}
for name in ['01 Player', '02 Three Discs', '03 Compact Cards', '04 Studio', '05 Lights and Camera']:
    c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); COLLS[name] = c

def place_collection(obj, name):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    COLLS[name].objects.link(obj)
    return obj

def material(name, rgb, metallic=0, roughness=.45):
    m = bpy.data.materials.new(name); m.use_nodes = True
    s = m.node_tree.nodes.get('Principled BSDF')
    s.inputs['Base Color'].default_value = (*rgb,1)
    s.inputs['Metallic'].default_value = metallic
    s.inputs['Roughness'].default_value = roughness
    m.diffuse_color = (*rgb,1)
    return m

silver = material('PLAYER / fine frosted aluminum', (.61,.64,.69), .85, .34)
graphite = material('PLAYER / soft graphite trim', (.022,.028,.038), .1, .36)
black = material('PLAYER / recessed black polymer', (.009,.011,.017), 0, .4)
button_metal = material('PLAYER / matte control caps', (.53,.57,.63), .8, .24)
cobalt = material('ACCENT / cobalt blue', (.012,.055,.62), .25, .3)
red = material('ACCENT / vermilion', (.8,.038,.014), 0, .36)
paper_edge = material('CARDS / uncoated ivory paper edges', (.82,.83,.82), 0, .7)
floor_mat = material('STUDIO / soft silver white', (.86,.87,.90), 0, .72)
metal_edge = material('CD / polished aluminum edge', (.8,.83,.87), 1, .12)
clear = material('CD / transparent polycarbonate hub', (.92,.95,.99), 0, .06)
clear.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value = 1
clear.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value = 1.49

# Microscopic roughness variation only: silver stays smooth rather than looking scratched.
n = silver.node_tree.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value=700
mp = silver.node_tree.nodes.new('ShaderNodeMapRange')
mp.inputs['To Min'].default_value=.29; mp.inputs['To Max'].default_value=.37
silver.node_tree.links.new(n.outputs['Fac'],mp.inputs['Value'])
silver.node_tree.links.new(mp.outputs['Result'],silver.node_tree.nodes.get('Principled BSDF').inputs['Roughness'])

def empty(name, coll, loc=(0,0,0), rot=(0,0,0)):
    o=bpy.data.objects.new(name,None); COLLS[coll].objects.link(o)
    o.location=loc; o.rotation_euler=rot; o.empty_display_type='PLAIN_AXES'; o.empty_display_size=.22
    return o

def box(name, loc, dims, mat, bevel=.05, parent=None, coll='01 Player'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.name=name
    o.dimensions=dims; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod=o.modifiers.new('Editable rounded edges','BEVEL'); mod.width=bevel; mod.segments=6
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    o.data.materials.append(mat); place_collection(o,coll)
    if parent: o.parent=parent
    return o

def cylinder(name, loc, r, depth, mat, parent=None, rot=(0,0,0), coll='01 Player'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r, depth=depth, location=loc)
    o=bpy.context.object; o.name=name; o.rotation_euler=rot; o.data.materials.append(mat)
    b=o.modifiers.new('Machined rim','BEVEL'); b.width=min(.012,depth/4); b.segments=3
    o.modifiers.new('Weighted normals','WEIGHTED_NORMAL'); place_collection(o,coll)
    if parent: o.parent=parent
    return o

def rounded_shell(name,loc,dims,radius,mat,parent=None):
    w,h,d=dims; outline=[]
    for cx,cy,a0 in [(w/2-radius,h/2-radius,0),(-w/2+radius,h/2-radius,90),(-w/2+radius,-h/2+radius,180),(w/2-radius,-h/2+radius,270)]:
        for j in range(13):
            a=math.radians(a0+j*90/12)
            outline.append((cx+radius*math.cos(a),cy+radius*math.sin(a)))
    n=len(outline);vs=[(x,y,z) for z in [-d/2,d/2] for x,y in outline]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces.extend([(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);COLLS['01 Player'].objects.link(obj);obj.location=loc;mesh.materials.append(mat)
    edge=obj.modifiers.new('Soft shell edge','BEVEL');edge.width=min(.024,d/3);edge.segments=4
    obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    if parent:obj.parent=parent
    return obj

def line(name, pts, mat, radius=.008, parent=None, coll='01 Player'):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=radius; c.bevel_resolution=3
    s=c.splines.new('POLY'); s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts): p.co=(*co,1)
    o=bpy.data.objects.new(name,c); COLLS[coll].objects.link(o); c.materials.append(mat)
    if parent:o.parent=parent
    return o

FONT = bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
def label(text,loc,size,mat,parent=None,rot=(0,0,0),coll='01 Player',align='LEFT'):
    c=bpy.data.curves.new(text,'FONT'); c.body=text; c.size=size; c.font=FONT
    c.align_x=align; c.extrude=.0003
    o=bpy.data.objects.new('Label / '+text,c); COLLS[coll].objects.link(o); o.location=loc; o.rotation_euler=rot
    c.materials.append(mat)
    if parent:o.parent=parent
    return o

def image_material(name,file,alpha=False):
    m=material(name,(1,1,1),0,.42)
    ns=m.node_tree.nodes; ls=m.node_tree.links; p=ns.get('Principled BSDF')
    img=ns.new('ShaderNodeTexImage'); img.image=bpy.data.images.load(str(ASSETS/file),check_existing=True)
    ls.new(img.outputs['Color'],p.inputs['Base Color'])
    if alpha:
        transparent=ns.new('ShaderNodeBsdfTransparent'); mix=ns.new('ShaderNodeMixShader')
        ls.new(img.outputs['Alpha'],mix.inputs[0]); ls.new(transparent.outputs[0],mix.inputs[1]); ls.new(p.outputs[0],mix.inputs[2]); ls.new(mix.outputs[0],ns.get('Material Output').inputs['Surface'])
        if hasattr(m,'surface_render_method'):m.surface_render_method='DITHERED'
    return m

def quad(name, coords, mat, parent=None, coll='01 Player',uvs=None):
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(coords,[],[(0,1,2,3)]); mesh.update()
    uv=mesh.uv_layers.new(name='UVMap'); uvs=uvs or [(0,0),(1,0),(1,1),(0,1)]
    for i,v in enumerate(uvs): uv.data[i].uv=v
    o=bpy.data.objects.new(name,mesh); COLLS[coll].objects.link(o); mesh.materials.append(mat)
    if parent:o.parent=parent
    return o

def ring_mesh(name, outer, inner, thickness, mat, parent=None, coll='02 Three Discs',segments=192):
    # A true hole and independent sidewall; UVs deliberately match 0.46-radius prints.
    verts=[]
    for z in [-thickness/2,thickness/2]:
        for r in [inner,outer]:
            verts.extend([(r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),z) for i in range(segments)])
    faces=[]
    for i in range(segments):
        j=(i+1)%segments
        faces.extend([(2*segments+i,3*segments+i,3*segments+j,2*segments+j),(i,j,segments+j,segments+i),(segments+i,segments+j,3*segments+j,3*segments+i),(i,2*segments+i,2*segments+j,j)])
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(.5+.46*co.x/outer,.5+.46*co.y/outer)
    o=bpy.data.objects.new(name,mesh); COLLS[coll].objects.link(o); mesh.materials.append(mat)
    if parent:o.parent=parent
    return o

def optical_material(name,file):
    m=bpy.data.materials.new(name); m.use_nodes=True; ns=m.node_tree.nodes; ns.clear(); ls=m.node_tree.links
    out=ns.new('ShaderNodeOutputMaterial'); base=ns.new('ShaderNodeBsdfPrincipled'); base.label='Mirror silver with real thin-film interference'
    base.inputs['Metallic'].default_value=1; base.inputs['Roughness'].default_value=.10
    base.inputs['Coat Weight'].default_value=.25; base.inputs['Coat Roughness'].default_value=.08
    base.inputs['Thin Film IOR'].default_value=1.38
    texcoord=ns.new('ShaderNodeTexCoord'); sep=ns.new('ShaderNodeSeparateXYZ'); ls.new(texcoord.outputs['UV'],sep.inputs[0])
    x=ns.new('ShaderNodeMath'); x.operation='SUBTRACT'; x.inputs[1].default_value=.5; ls.new(sep.outputs['X'],x.inputs[0])
    y=ns.new('ShaderNodeMath'); y.operation='SUBTRACT'; y.inputs[1].default_value=.5; ls.new(sep.outputs['Y'],y.inputs[0])
    angle=ns.new('ShaderNodeMath'); angle.operation='ARCTAN2'; ls.new(y.outputs[0],angle.inputs[0]); ls.new(x.outputs[0],angle.inputs[1])
    mul=ns.new('ShaderNodeMath'); mul.operation='MULTIPLY'; mul.inputs[1].default_value=1/math.tau; ls.new(angle.outputs[0],mul.inputs[0])
    add=ns.new('ShaderNodeMath'); add.operation='ADD'; add.inputs[1].default_value=.5; ls.new(mul.outputs[0],add.inputs[0])
    ramp=ns.new('ShaderNodeValToRGB'); ramp.label='Subtle radial diffraction, not painted full rainbow'
    stops=[(0,(.35,.70,1,1)),(.18,(1,.42,.80,1)),(.36,(1,.86,.35,1)),(.54,(.35,1,.78,1)),(.72,(.35,.70,1,1)),(.9,(1,.42,.80,1)),(1,(.35,.70,1,1))]
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1]); ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=stops[0][1]
    for t,color in stops[1:]:ramp.color_ramp.elements.new(t).color=color
    ls.new(add.outputs[0],ramp.inputs[0]); mixcolor=ns.new('ShaderNodeMixRGB'); mixcolor.inputs[0].default_value=.55;mixcolor.inputs[1].default_value=(.82,.85,.9,1)
    ls.new(ramp.outputs[0],mixcolor.inputs[2]); ls.new(mixcolor.outputs[0],base.inputs['Base Color'])
    film=ns.new('ShaderNodeMapRange'); film.inputs['To Min'].default_value=280; film.inputs['To Max'].default_value=690; ls.new(add.outputs[0],film.inputs['Value']); ls.new(film.outputs[0],base.inputs['Thin Film Thickness'])
    image=ns.new('ShaderNodeTexImage'); image.image=bpy.data.images.load(str(ASSETS/file),check_existing=True); image.label='Independent transparent printed artwork'
    ink=ns.new('ShaderNodeBsdfPrincipled'); ink.inputs['Roughness'].default_value=.36;ink.inputs['Specular IOR Level'].default_value=.24;ink.inputs['Coat Weight'].default_value=.14;ink.inputs['Coat Roughness'].default_value=.13
    ls.new(image.outputs['Color'],ink.inputs['Base Color'])
    blend=ns.new('ShaderNodeMixShader'); ls.new(image.outputs['Alpha'],blend.inputs[0]);ls.new(base.outputs[0],blend.inputs[1]);ls.new(ink.outputs[0],blend.inputs[2]);ls.new(blend.outputs[0],out.inputs[0])
    # First surface needs print. Separate inverse side remains reflective silver.
    return m

# Player shell, true separate hinged lid, recessed top and plausible controls.
player=empty('PLAYER_ROOT','01 Player',(-1.85,-.55,0),(0,0,math.radians(13)))
player['purpose']='Portable hinged CD navigation player, no tonearm'
rounded_shell('Lower graphite shell',(0,0,.19),(3.50,2.92,.27),.38,graphite,player)
rounded_shell('Main matte silver shell',(0,0,.36),(3.53,2.94,.38),.39,silver,player)
top=rounded_shell('Upper shell with disc recess',(0,0,.545),(3.44,2.85,.13),.37,silver,player)
# Make the round compartment a true boolean recess in the editable shell.
cut=cylinder('Temporary cavity cutter',(-.15,.12,.61),1.225,.30,black,parent=player)
bpy.context.view_layer.update()
boolean=top.modifiers.new('Actual circular disc compartment','BOOLEAN'); boolean.operation='DIFFERENCE';boolean.object=cut
bpy.context.view_layer.objects.active=top
try:bpy.ops.object.modifier_apply(modifier=boolean.name)
except Exception:pass
bpy.data.objects.remove(cut,do_unlink=True)
cylinder('Recessed disc compartment',(-.15,.12,.535),1.227,.037,black,parent=player)
ring_mesh('Compartment raised circular rim',1.252,1.218,.024,button_metal,parent=player,coll='01 Player').location=(-.15,.12,.555)
cylinder('Central spindle',(-.15,.12,.612),.113,.07,black,parent=player)
cylinder('Spindle cap',(-.15,.12,.652),.074,.015,button_metal,parent=player)
for i in range(8):box('Side ventilation slot %02d'%i,(1.756,-.66+i*.15,.34),(.008,.07,.045),graphite,.003,player)
for x in [-1.35,1.35]:
    for y0 in [-1.1,1.1]:cylinder('Low rubber foot',(x,y0,.072),.09,.036,graphite,parent=player)
for x in [-1.44,1.44]:
    for y0 in [-1.17,1.17]:
        cylinder('Flush shell screw',(x,y0,.621),.025,.003,button_metal,parent=player)
        line('Screw notch',[(x-.012,y0,.624),(x+.012,y0,.624)],graphite,.002,parent=player)

for i,x in enumerate([-.97,-.49,-.01,.47]):
    box('Button recess %d'%i,(x,-1.476,.405),(.39,.037,.18),black,.065,player)
    b=box(['Play pause button','Stop button','Previous button','Next button'][i],(x,-1.505,.415),(.33,.055,.135),button_metal,.045,player)
    # Symbols lie on the front XZ plane with normal -Y.
    if i==0:
        quad('Play triangle',[(x-.09,-1.538,.38),(x-.09,-1.538,.45),(x-.028,-1.538,.414),(x-.09,-1.538,.38)],graphite,player)
        for xx in [x+.035,x+.075]:box('Pause bar',(xx,-1.539,.415),(.016,.003,.059),graphite,.002,player)
    elif i==1:box('Stop symbol',(x,-1.539,.415),(.06,.003,.06),graphite,.004,player)
    else:
        sign=-1 if i==2 else 1
        for dx in [-.036,.025]:
            quad('Skip triangle',[(x+dx-sign*.021,-1.539,.38),(x+dx-sign*.021,-1.539,.45),(x+dx+sign*.022,-1.539,.415),(x+dx-sign*.021,-1.539,.38)],graphite,player)
cylinder('Cobalt tactile select button',(1.07,-1.494,.405),.091,.07,cobalt,parent=player,rot=(math.pi/2,0,0))
cylinder('Headphone jack',(1.48,-1.500,.365),.055,.055,black,parent=player,rot=(math.pi/2,0,0))
label('CLAIRE  /  PORTABLE ARCHIVE',(-1.25,-1.490,.545),.045,graphite,player,rot=(math.pi/2,0,0))

hinge=empty('LID_HINGE','01 Player',(0,1.355,.605));hinge.parent=player
hinge['axis']='Local X; 0 closed / -78 degrees open'
rounded_shell('Lid outer silver shell',(0,-1.355,.086),(3.53,2.91,.15),.39,silver,hinge)
rounded_shell('Lid graphite seal',(0,-1.355,.001),(3.42,2.8,.044),.36,graphite,hinge)
rounded_shell('Inner matte silver lid panel',(0,-1.355,-.025),(3.32,2.70,.040),.35,button_metal,hinge)
for x in [-1.18,1.18]:
    cylinder('Hinge fixed bearing',(x,1.355,.616),.11,.37,button_metal,player,rot=(0,math.pi/2,0))
    cylinder('Hinge barrel',(x,0,0),.083,.39,graphite,hinge,rot=(0,math.pi/2,0))
lidlabel=image_material('LID / removable Claire torn label','lid-label.png',True)
# Interior is the local downward-facing side, so mapping reverses appropriately.
quad('Inner lid printed name label',[(-1.35,-2.56,-.048),(1.35,-2.56,-.048),(1.35,-.15,-.048),(-1.35,-.15,-.048)],lidlabel,hinge,uvs=[(0,1),(1,1),(1,0),(0,0)])
quad('Closed lid outer name label',[(-1.35,-2.56,.165),(1.35,-2.56,.165),(1.35,-.15,.165),(-1.35,-.15,.165)],lidlabel,hinge)

# Three separately modeled card groups; meaningful tight overlap.
CARD_KEYS=['about','projects','world'];CARD_POS=[(1.34,1.58,2.72),(2.72,2.05,2.43),(4.11,2.52,2.14)]
cards=[];CARD_W=2.27
for i,key in enumerate(CARD_KEYS):
    root=empty('CARD_%02d_%s'%(i+1,key.upper()),'03 Compact Cards',CARD_POS[i],(0,0,math.radians(24)))
    root['entry_id']=key;root['hoverable']=True;root['baseline_location']=list(CARD_POS[i]); cards.append(root)
    # One continuous sheet: the upper .30 is the printed index header.
    box('Independent %s insert'%key,(0,0,.15),(CARD_W,.042,CARD_W+.30),paper_edge,.026,root,'03 Compact Cards')
    cm=image_material('CARD / '+key+' printed cover','cover-'+key+'.png')
    quad('Printed %s insert front'%key,[(-CARD_W/2,-.024,-CARD_W/2),(CARD_W/2,-.024,-CARD_W/2),(CARD_W/2,-.024,CARD_W/2),(-CARD_W/2,-.024,CARD_W/2)],cm,root,'03 Compact Cards')
    if (ASSETS/('title-'+key+'.png')).exists():
        title_z = CARD_W/2+.15
        tm=image_material('CARD / '+key+' readable title tab','title-'+key+'.png',True)
        quad('Readable top title '+key,[(-1.06,-.024,title_z-.105),(1.06,-.024,title_z-.105),(1.06,-.024,title_z+.105),(-1.06,-.024,title_z+.105)],tm,root,'03 Compact Cards')
    # Fine clear sleeve edge, open at top for taking the disc out.
    for xx in [-CARD_W/2,CARD_W/2]:box('Thin sleeve edge '+key,(xx,-.041,-.1),(.021,.033,2.05),button_metal,.008,root,'03 Compact Cards')
    box('Sleeve lower edge '+key,(0,-.041,-CARD_W/2),(CARD_W,.033,.019),button_metal,.007,root,'03 Compact Cards')
badge=image_material('CARD / current playing marker','playing-badge.png')
badge_obj=quad('Playing marker / about',[(-.4,-.040,.38),(.43,-.040,.38),(.43,-.040,.61),(-.4,-.040,.61)],badge,cards[0],'03 Compact Cards')
badge_project=quad('Playing marker / projects',[(-.4,-.085,.88),(.43,-.085,.88),(.43,-.085,1.11),(-.4,-.085,1.11)],badge,cards[1],'03 Compact Cards')
for marker,initial in [(badge_obj,False),(badge_project,True)]:
    marker.hide_render=initial;marker.hide_viewport=initial
    for f in [1,310]:marker.keyframe_insert('hide_render',frame=f);marker.keyframe_insert('hide_viewport',frame=f)
    marker.hide_render=not initial;marker.hide_viewport=not initial
    for f in [320,350]:marker.keyframe_insert('hide_render',frame=f);marker.keyframe_insert('hide_viewport',frame=f)

# Disc roots have no parenting dependency: ready to travel between card and player.
discs=[]
for i,key in enumerate(CARD_KEYS):
    root=empty('DISC_%02d_%s'%(i+1,key.upper()),'02 Three Discs')
    root['disc_id']=key;root['is_navigation_disc']=True;root['original_card']=cards[i].name
    pm=optical_material('CD / '+key+' silver + independent artwork','disc-'+key+'.png')
    ring_mesh('CD %s solid optical substrate'%key,1.105,.245,.030,metal_edge,root)
    face=ring_mesh('CD %s printed optical face'%key,1.105,.245,.0012,pm,root);face.location.z=.0162
    ring_mesh('CD %s clear central ring'%key,.245,.145,.030,clear,root)
    discs.append(root)

def card_disc_pose(i):
    c=cards[i]; q=c.rotation_euler.to_quaternion(); local=Vector((.0,-.078,-.25))
    return c.location + q @ local, (q @ Euler((math.pi/2,0,0)).to_quaternion()).to_euler()

def player_disc_pose():
    q=player.rotation_euler.to_quaternion()
    return player.location + q @ Vector((-.15,.12,.587)),player.rotation_euler.copy()

def apply_disc_pose(root,pose,scale=1):root.location=pose[0];root.rotation_euler=pose[1];root.scale=(scale,)*3

def key_obj(o,frame):
    for path in ['location','rotation_euler','scale']:o.keyframe_insert(data_path=path,frame=frame)

base_cards=[(o.location.copy(),o.rotation_euler.copy(),o.scale.copy()) for o in cards]
base_discs=[player_disc_pose(),card_disc_pose(1),card_disc_pose(2)]
for d,p in zip(discs,base_discs):apply_disc_pose(d,p)

# Studio cyclorama, horizontal plane bends into an unbounded rear wall.
profile=[(-35,0),(6,0)]
for j in range(1,33):
    a=j/32*math.pi/2;profile.append((6+4*math.sin(a),4-4*math.cos(a)))
profile.append((10,25))
vs=[]
for x in [-40,40]:vs.extend([(x,y,z) for y,z in profile])
ns=len(profile);fs=[(i,i+1,ns+i+1,ns+i) for i in range(ns-1)]
me=bpy.data.meshes.new('Infinite cove geometry');me.from_pydata(vs,[],fs);me.update()
cove=bpy.data.objects.new('Seamless infinite studio cove',me);COLLS['04 Studio'].objects.link(cove);me.materials.append(floor_mat)
for p in me.polygons:p.use_smooth=True

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=SAMPLES;scene.cycles.use_denoising=True
try:
    cp=bpy.context.preferences.addons['cycles'].preferences;cp.compute_device_type='OPTIX';cp.get_devices()
    for d in cp.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:scene.cycles.device='CPU'
scene.world.use_nodes=True;world=scene.world.node_tree.nodes.get('Background');world.inputs['Color'].default_value=(.64,.68,.75,1);world.inputs['Strength'].default_value=.23

def area(name,loc,energy,size,target,color=(1,1,1),size_y=None):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;place_collection(o,'05 Lights and Camera')
    o.data.energy=energy;o.data.shape='RECTANGLE';o.data.size=size;o.data.size_y=size_y or size;o.data.color=color
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Large diffuse key',(-4,-5,8),1050,7,(0,0,1),(.95,.97,1),6)
area('Broad right fill',(6,-2,6),800,6,(1,1,1),(1,1,1),6)
area('Tall CD reflection softbox',(-1,5,7),850,5,(1,0,1),(1,1,1),7)
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.25
scene.render.resolution_x=RES;scene.render.resolution_y=int(RES*9/16);scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.fps=30
scene.render.film_transparent=False

bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='CAMERA / opening to hero';place_collection(camera,'05 Lights and Camera');scene.camera=camera
camera.data.type='ORTHO';camera.data.lens=50;camera.data.clip_end=150
hero_target=Vector((.8,.7,1.60));hero_loc=Vector((7.7,-13,8.8));hero_rot=(hero_target-hero_loc).to_track_quat('-Z','Y').to_euler()
camera.location=player.location+Vector((0,0,10));camera.rotation_euler=(0,0,0);camera.data.ortho_scale=6.8
for frame in [1,15,55]:key_obj(camera,frame);camera.data.keyframe_insert('ortho_scale',frame=frame)
camera.location=hero_loc;camera.rotation_euler=hero_rot;camera.data.ortho_scale=11.35
for frame in [135,350]:key_obj(camera,frame);camera.data.keyframe_insert('ortho_scale',frame=frame)
hinge.rotation_euler.x=0
for f in [1,15]:hinge.keyframe_insert('rotation_euler',frame=f)
hinge.rotation_euler.x=math.radians(-78)
for f in [75,350]:hinge.keyframe_insert('rotation_euler',frame=f)

# Timeline: opening, compact idle, hover demonstration, and a real two-disc swap.
for i,c in enumerate(cards):
    for frame in [1,135,150]:key_obj(c,frame)
for i,d in enumerate(discs):
    for frame in [1,55,135,150]:key_obj(d,frame)
    if i==0:
        d.rotation_euler.z+=math.radians(32);key_obj(d,135);key_obj(d,150)
hover_dir=(hero_loc-Vector(CARD_POS[1])).normalized()
hover_cards=[(p.copy(),r.copy(),s.copy()) for p,r,s in base_cards]
cards[1].location+=Vector((hover_dir.x*.34,hover_dir.y*.34,.16));cards[1].scale=(1.03,)*3
cards[1].rotation_euler.z=math.radians(18)
for i,c in enumerate(cards):
    for f in [163,190]:key_obj(c,f)
for i in [1,2]:
    apply_disc_pose(discs[i],card_disc_pose(i),1.03 if i==1 else 1)
    for f in [163,190]:key_obj(discs[i],f)
for i,c in enumerate(cards):
    c.location,c.rotation_euler,c.scale=base_cards[i]
    for f in [204,220,350]:key_obj(c,f)
for i,d in enumerate(discs):
    apply_disc_pose(d,base_discs[i])
    for f in [204,220]:key_obj(d,f)

active_pose=player_disc_pose();return_pose=card_disc_pose(0);new_start=card_disc_pose(1)
for frame,t,up in [(232,.0,.40),(247,.45,1.7),(261,1,.35),(270,1,0)]:
    discs[0].location=active_pose[0].lerp(return_pose[0],t)+Vector((0,-.15,up))
    discs[0].rotation_euler=active_pose[1].to_quaternion().slerp(return_pose[1].to_quaternion(),t).to_euler();key_obj(discs[0],frame)
for frame,t,up in [(270,0,.30),(288,.5,1.65),(308,1,.4),(320,1,0)]:
    discs[1].location=new_start[0].lerp(active_pose[0],t)+Vector((0,-.18,up))
    discs[1].rotation_euler=new_start[1].to_quaternion().slerp(active_pose[1].to_quaternion(),t).to_euler();key_obj(discs[1],frame)
apply_disc_pose(discs[0],return_pose);key_obj(discs[0],350)
apply_disc_pose(discs[1],active_pose);discs[1].rotation_euler.z+=math.radians(60);key_obj(discs[1],350)
key_obj(discs[2],350)
scene.frame_start=1;scene.frame_end=350
for name,frame in [('01 CLOSED TOP',1),('02 OPEN HERO / IDLE',135),('03 PROJECTS HOVER',163),('04 COMPACT RESET',204),('05 RETURN ABOUT',247),('06 INSERT PROJECTS',288),('07 PROJECTS PLAYING',350)]:scene.timeline_markers.new(name,frame=frame)

def curves_for(o):
    ad=o.animation_data
    if not ad or not ad.action:return []
    a=ad.action
    if hasattr(a,'fcurves'):return list(a.fcurves)
    result=[]
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:result.extend(bag.fcurves)
    return result
for o in [camera,camera.data,hinge,*cards,*discs]:
    for fc in curves_for(o):
        for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type='AUTO_CLAMPED';kp.handle_right_type='AUTO_CLAMPED'

scene['claire_model_version']='modern-v02'
scene['claire_active_disc']='about';scene['claire_hover_disc']='none'
scene['claire_disc_count']=3
scene['claire_web_note']='Blender models and motion rigs only; webpage interaction requires frontend binding.'
scene['claire_root_names']=json.dumps({'player':player.name,'hinge':hinge.name,'discs':[d.name for d in discs],'cards':[c.name for c in cards]})
scene['claire_card_home_poses']=json.dumps([{'loc':list(p),'rot':list(r),'scale':list(s)} for p,r,s in base_cards])
scene['claire_hover_direction']=list(hover_dir)
scene['claire_player_disc_pose']=json.dumps({'loc':list(active_pose[0]),'rot':list(active_pose[1])})

# Store instructions and optional live Blender hover panel script inside the file.
readme=bpy.data.texts.new('START HERE — Claire modern-v02')
readme.write('Claire modern-v02\n\nEditable modern silver portable player, three unique printed optical discs, three compact cards, seamless studio.\nTimeline markers: frame 1 closed/top; 135 hero idle; 163 hover projects; 204 compact; 247/288 swapping; 350 projects playing.\n\nThe three DISC_* empties are the only three navigation discs. Every component and texture is independent. Images are packed.\n\nSelect Text Editor > claire_preview_runtime.py > Run Script to register the Claire panel. Optional viewport hover requires Start Hover Preview, then mouse over entry cards. No sound or webpage is implemented in Blender.\n')
runtime_path=OUT/'claire_preview_runtime.py'
if runtime_path.exists():bpy.data.texts.load(str(runtime_path))

# Save in a useful camera/material view, not the old layout.
scene.frame_set(135)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.shading.type='MATERIAL'
            a.spaces.active.shading.use_scene_world=True;a.spaces.active.shading.use_scene_lights=True
            a.spaces.active.overlay.show_overlays=False
bpy.ops.object.select_all(action='DESELECT');player.select_set(True);bpy.context.view_layer.objects.active=player
for image in bpy.data.images:
    if image.source=='FILE':
        try:image.pack()
        except Exception:pass
FONT.pack()
blend=OUT/'claire-modern-v02.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend),check_existing=False)
manifest={'version':bpy.app.version_string,'blend':str(blend),'objects':len(bpy.data.objects),'disc_roots':[d.name for d in discs], 'card_roots':[c.name for c in cards],'packed_images':len([im for im in bpy.data.images if im.packed_file]),'timeline':{m.name:m.frame for m in scene.timeline_markers},'renderer':scene.cycles.device,'player_shell_dimensions':list(bpy.data.objects['Main matte silver shell'].dimensions),'web_hover_implemented':False}
(OUT/'model-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('CLAIRE_MODEL_SAVED',str(blend),flush=True)
if RENDER:
    for name,frame in [('hero-idle',135),('hero-hover-projects',163),('opening-closed-top',1)]:
        scene.frame_set(frame);scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    scene.frame_set(135)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),check_existing=False)
print('CLAIRE_BUILD_DONE',flush=True)
