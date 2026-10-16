import bpy, json
print('CLAIRE_PROBE', json.dumps({
    'version': bpy.app.version_string,
    'shader_inputs': [i.name for i in bpy.data.materials.new('probe').node_tree.nodes] if False else [],
    'cycles_devices': [],
}))
m = bpy.data.materials.new('Principled probe'); m.use_nodes = True
print('PRINCIPLED_INPUTS', [i.name for i in m.node_tree.nodes.get('Principled BSDF').inputs])
try:
    cp = bpy.context.preferences.addons['cycles'].preferences
    cp.get_devices()
    print('DEVICES', [(d.name, d.type) for d in cp.devices])
except Exception as e:
    print('DEVICE_PROBE_ERROR', str(e))
