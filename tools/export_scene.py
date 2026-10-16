"""Read V3 in Blender background mode; export web assets without saving the source."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion

root = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
assert scene['claire_model_version'] == 'modern-v03'
names = json.loads(scene['claire_root_names'])
C = Matrix.Rotation(-math.pi / 2, 4, 'X')
def pose(obj, world=False):
    matrix = obj.matrix_world if world else obj.matrix_local
    converted = C @ matrix if obj.type == 'CAMERA' else C @ matrix @ C.inverted()
    p,q,s = converted.decompose()
    return {'position':list(p), 'quaternion':[q.x,q.y,q.z,q.w], 'scale':list(s)}
def sample():
    return {'camera':pose(scene.camera,True), 'scale':scene.camera.data.ortho_scale,
            'hinge':pose(scene.objects[names['hinge']]), 'disc':pose(scene.objects[names['discs'][0]])}
opening=[]
for frame in range(1,128):
    scene.frame_set(frame)
    opening.append(sample())
scene.frame_set(135)
cards=[scene.objects[n] for n in names['cards']]
discs=[scene.objects[n] for n in names['discs']]
homes=[pose(o) for o in cards]
disc_homes=[pose(o) for o in discs]
# Playing badges are animated separately; excluding them keeps the baseline hit
# geometry tied to the sleeve itself, including its extended title tab.
corners=[[[x,y,z] for x,y,z in [(-1.1455,-1.1445,.0575),(1.1455,-1.1445,.0575),(1.1455,1.435,.0575),(-1.1455,1.435,.0575)]] for card in cards]
metadata={'version':'modern-v03-web','fps':30,'opening':opening,'hero':sample(),
          'names':names,'cards':homes,'discs':disc_homes,
          'playerDisc':pose(discs[0]),'source':'claire-modern-v03.blend',
          'corners':corners,'basis':'glTF Y-up','objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in scene.objects]}
(root/'assets'/'motion.json').write_text(json.dumps(metadata,separators=(',',':')),encoding='utf-8')
# Resolve packed images; browser textures need no native procedural nodes.
for image in bpy.data.images:
    if image.source == 'FILE' and image.size[0] > 1024:
        image.scale(1024,max(1,round(image.size[1]*1024/image.size[0])))
        image.pack()
# Translate mixed Blender print shaders into exportable glTF alpha materials.
# This only modifies the background export session, never the .blend on disk.
for material in bpy.data.materials:
    if not material.use_nodes:continue
    images=[n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    if not images:continue
    image=images[0]
    material.node_tree.nodes.clear()
    nodes=material.node_tree.nodes;links=material.node_tree.links
    tex=nodes.new('ShaderNodeTexImage');tex.image=image
    shader=nodes.new('ShaderNodeBsdfPrincipled');shader.inputs['Roughness'].default_value=.42
    output=nodes.new('ShaderNodeOutputMaterial')
    links.new(tex.outputs['Color'],shader.inputs['Base Color'])
    links.new(tex.outputs['Alpha'],shader.inputs['Alpha'])
    links.new(shader.outputs['BSDF'],output.inputs['Surface'])
    material.surface_render_method='DITHERED'
# Record all solid floor objects for runtime adjustment, including shadows.
for obj in scene.objects:
    if obj.type=='MESH' and 'solid optical substrate' in obj.name:
        uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='Optical radial UV')
        radius=max(max(abs(vertex.co.x),abs(vertex.co.y)) for vertex in obj.data.vertices)
        for loop in obj.data.loops:
            vertex=obj.data.vertices[loop.vertex_index]
            uv.data[loop.index].uv=(.5+vertex.co.x/(2*radius),.5+vertex.co.y/(2*radius))
bpy.ops.object.select_all(action='DESELECT')
for obj in scene.objects:
    if obj.type in {'MESH','EMPTY','CURVE','FONT'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(root/'assets'/'claire-v3.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_animations=False,
    export_cameras=False,export_lights=False,export_extras=False,export_current_frame=True)
print('WEB_EXPORTED',root/'assets'/'claire-v3.glb')
