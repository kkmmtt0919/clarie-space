const fs = require('node:fs');
const THREE = require('three');
const bytes = fs.readFileSync('assets/claire-v3.glb');
const jsonLength = bytes.readUInt32LE(12);
const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength));
const binary = bytes.subarray(28 + jsonLength);
const motion = JSON.parse(fs.readFileSync('assets/motion.json'));
const index = gltf.nodes.findIndex(n => n.name === 'Closed lid outer name label');
const primitive = gltf.meshes[gltf.nodes[index].mesh].primitives[0];
const image = gltf.images[gltf.textures[gltf.materials[primitive.material].pbrMetallicRoughness.baseColorTexture.index].source];
const view = gltf.bufferViews[image.bufferView];
fs.writeFileSync('assets/loading-label.png', binary.subarray(view.byteOffset, view.byteOffset + view.byteLength));
// Use the existing vector lettering, with the paper polygon removed, for loading.
const lettering = fs.readFileSync('models/modern-v03/assets/lid-label.svg', 'utf8').replace(/<polygon\b[^>]*\/>/g, '');
fs.writeFileSync('assets/loading-label.svg', lettering);
function matrix(i) {
  const node = gltf.nodes[i];
  const parent = gltf.nodes.findIndex(n => n.children?.includes(i));
  const pose = node.name === motion.names.hinge ? motion.opening[0].hinge : node;
  const local = new THREE.Matrix4().compose(new THREE.Vector3(...(pose.position || pose.translation || [0,0,0])), new THREE.Quaternion(...(pose.quaternion || pose.rotation || [0,0,0,1])), new THREE.Vector3(...(pose.scale || [1,1,1])));
  return parent < 0 ? local : matrix(parent).multiply(local);
}
function values(accessor) {
  const a = gltf.accessors[accessor], v = gltf.bufferViews[a.bufferView];
  return Array.from(new Float32Array(binary.buffer, binary.byteOffset + v.byteOffset + (a.byteOffset || 0), a.count * (a.type === 'VEC3' ? 3 : 2)));
}
const positions = values(primitive.attributes.POSITION), uv = values(primitive.attributes.TEXCOORD_0), world = matrix(index);
const points = Array.from({length:4}, (_,i) => ({uv:uv.slice(i*2,i*2+2), point:new THREE.Vector3(...positions.slice(i*3,i*3+3)).applyMatrix4(world).toArray()}));
fs.writeFileSync('src/loading-label.json', JSON.stringify({points, camera:motion.opening[0].camera, scale:motion.opening[0].scale}, null, 2));
