import playlist from './music-playlist.json';
import { createLabelLoader } from './label-loader.js';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { entries } from './content.js';
import { springStep } from './spring.js';
import { worldContent, mountWorldEffects, disposeWorldEffects, closeWorldEffects } from './world-effects.js';
import { mountAboutEffects, disposeAboutEffects } from './about-effects.jsx';
import { projectContent, mountProjectNavigation, disposeProjectNavigation } from './project-cards.js';

const $ = id => document.getElementById(id);
const stage = $('stage'), hero = document.querySelector('.hero'), dialog = $('content-dialog');
const targets = [...document.querySelectorAll('.scene-entry')];
const reducedQuery = matchMedia('(prefers-reduced-motion: reduce)');
let reduced = reducedQuery.matches;
const labelLoader = createLabelLoader(stage,()=>reduced);
let skipRequested=false, loadingHandoff=false;
let ready = false, intro = false, active = 0, hovered = -1, busy = false, queued = null;
let model, metadata, scene, renderer, camera, hinge, cards, discs, markers;
let introStart = 0, lastTime = 0, scheduledFrame = 0, swap = null, lastTrigger = null;
const openingViewDuration = .7;
const openingViewFrame = 48;
const lidOpeningDuration = 1.2;
const openingDuration = openingViewDuration + lidOpeningDuration + (126-openingViewFrame)/30;
let focused = -1, keyboardAction = false, width = 1, height = 1;
const springValues = [0,0,0], springVelocities = [0,0,0], pointer = new THREE.Vector2();
const raycaster = new THREE.Raycaster();
let hitPolygons = [], discPolygons = [], cameraScale = 11.35, closingTimer = 0;
const v = data => new THREE.Vector3(...data), q = data => new THREE.Quaternion(...data);
const clamp = THREE.MathUtils.clamp;
const ease = x => { x=clamp(x,0,1); return 1-(1-x)**3; };
// Strong ease-in-out (0.77, 0, 0.175, 1): concentrate the camera turn
// in the middle, then settle without overshooting the lid-opening view.
function cameraWhipEase(progress) {
  const x=clamp(progress,0,1);
  if(x===0||x===1)return x;
  let low=0,high=1,t=x;
  for(let i=0;i<18;i++){
    t=(low+high)/2;
    const projected=3*(1-t)*(1-t)*t*.77+3*(1-t)*t*t*.175+t*t*t;
    if(projected<x)low=t;else high=t;
  }
  return t*t*(3-2*t);
}
const assetURL = name => window.CLAIRE_ASSETS?.images[name] || './assets/'+name;
function opticalMaps() {
  const size=512,film=new Uint8Array(size*size*4),grooves=new Uint8Array(size*size*4);
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const u=(x+.5)/size-.5,w=(y+.5)/size-.5,r=Math.hypot(u,w)*2,angle=Math.atan2(w,u),at=(y*size+x)*4;
    // Optical film thickness and radial micro-grooves, not painted rainbow RGB.
    const thickness=clamp(.18+.62*r+.12*Math.sin(angle*2),0,1);
    film[at]=0;film[at+1]=Math.round(thickness*255);film[at+2]=0;film[at+3]=255;
    grooves[at]=Math.round((.5+.5*Math.cos(angle))*255);
    grooves[at+1]=Math.round((.5+.5*Math.sin(angle))*255);grooves[at+2]=210;grooves[at+3]=255;
  }
  const map=data=>{const texture=new THREE.DataTexture(data,size,size);texture.magFilter=THREE.LinearFilter;texture.minFilter=THREE.LinearMipmapLinearFilter;texture.generateMipmaps=true;texture.needsUpdate=true;return texture;};
  return {film:map(film),grooves:map(grooves)};
}
function pose(obj, data) { obj.position.fromArray(data.position); obj.quaternion.fromArray(data.quaternion); obj.scale.fromArray(data.scale); }
function snapshot(obj) { return {position:obj.position.toArray(),quaternion:obj.quaternion.toArray(),scale:obj.scale.toArray()}; }
function blendPose(obj,a,b,t) { obj.position.copy(v(a.position).lerp(v(b.position),t));obj.quaternion.copy(q(a.quaternion).slerp(q(b.quaternion),t));obj.scale.copy(v(a.scale).lerp(v(b.scale),t)); }
function needFrame() { if (ready && !scheduledFrame && renderer) scheduledFrame = requestAnimationFrame(tick); }
function updateCurrent() {
  $('current-record').textContent='当前内容：'+entries[active].title;
  document.querySelector('.status-dot').style.background=entries[active].color;
  document.querySelectorAll('.nav-entry').forEach((b,i)=>b.setAttribute('aria-current',i===active?'true':'false'));
  markers?.forEach((marker,i)=>{if(marker)marker.visible=i===active;});
}
function setHovered(index) {
  if (!ready || intro || busy || dialog.open || reduced) index=-1;
  hovered=index;
  stage.style.cursor=index>=0?'pointer':'default';
  needFrame();
}
function applyCard(index, progress) {
  const base=metadata.cards[index], card=cards[index];
  const rotation=q(base.quaternion).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),THREE.MathUtils.degToRad(4)*progress));
  const factor=1+.03*progress, pivot=new THREE.Vector3(1,0,0);
  card.position.copy(v(base.position)).add(pivot.clone().applyQuaternion(q(base.quaternion))).sub(pivot.multiplyScalar(factor).applyQuaternion(rotation));
  card.position.y+=.16*progress;card.quaternion.copy(rotation);card.scale.copy(v(base.scale)).multiplyScalar(factor);
  if(index!==active) {
    // Blender (0,-.45,-.25) transformed into glTF Y-up.
    discs[index].position.copy(card.position).add(new THREE.Vector3(0,-.25,.45).applyQuaternion(rotation));
    const relative=q(base.quaternion).invert().multiply(q(metadata.discs[index].quaternion));
    // About's exported disc is in the player: share the spare-disc local rotation.
    const spareRelative=q(metadata.cards[1].quaternion).invert().multiply(q(metadata.discs[1].quaternion));
    discs[index].quaternion.copy(rotation).multiply(index===0?spareRelative:relative);
    discs[index].scale.copy(card.scale);
  }
}
function resetCards() {springValues.fill(0);springVelocities.fill(0);cards.forEach((card,i)=>applyCard(i,0));hovered=-1;}
function projection(point) {const p=point.clone().project(camera);return [(p.x*.5+.5)*width,(-p.y*.5+.5)*height];}
function cardPolygon(index,current=false) {
  const matrix=current?cards[index].matrixWorld:new THREE.Matrix4().compose(v(metadata.cards[index].position),q(metadata.cards[index].quaternion),v(metadata.cards[index].scale));
  return metadata.corners[index].map(p=>projection(v(p).applyMatrix4(matrix)));
}
function inPolygon(point, polygon) {
  let inside=false;
  for(let i=0,j=polygon.length-1;i<polygon.length;j=i++) {
    const a=polygon[i],b=polygon[j];
    if(((a[1]>point[1])!==(b[1]>point[1])) && point[0]<(b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
  }
  return inside;
}
function fitCamera(scale) {
  // Keep a full 16:9 scene beneath the copy on smaller screens.
  let viewWidth=scale*(width>600?1.22:1.04), aspect=width/height;
  if(aspect<1.35) viewWidth=Math.max(viewWidth,11.8);
  const viewHeight=viewWidth/aspect;
  const verticalOffset=viewHeight*(width>600?.09:.05);
  camera.left=-viewWidth/2;camera.right=viewWidth/2;camera.top=viewHeight/2+verticalOffset;camera.bottom=-viewHeight/2+verticalOffset;
  camera.updateProjectionMatrix();camera.updateMatrixWorld();
}
function layoutTargets() {
  if(!ready || intro || busy)return;
  scene.updateMatrixWorld(true);
  hitPolygons=cards.map((_,i)=>cardPolygon(i));
  // Fixed baseline hit surfaces include the spare disc silhouette. Hovering never
  // redefines these regions, so crossing the three entries cannot oscillate.
  discPolygons=cards.map((_,i)=>{
    const base=metadata.cards[i], rotation=q(base.quaternion);
    const center=v(base.position).add(new THREE.Vector3(0,-.25,.45).applyQuaternion(rotation));
    const discRot=rotation.clone().multiply(q(metadata.cards[1].quaternion).invert().multiply(q(metadata.discs[1].quaternion)));
    return Array.from({length:24},(_,n)=>projection(new THREE.Vector3(Math.cos(n/24*Math.PI*2)*1.03,0,Math.sin(n/24*Math.PI*2)*1.03).applyQuaternion(discRot).add(center)));
  });
  targets.forEach((b,i)=>{
    const polygon=hitPolygons[i],xs=polygon.map(p=>p[0]),ys=polygon.map(p=>p[1]);
    const left=Math.min(...xs),top=Math.min(...ys),w=Math.max(...xs)-left,h=Math.max(...ys)-top;
    b.style.cssText=`left:${left}px;top:${top}px;width:${w}px;height:${h}px;z-index:${i+1};clip-path:polygon(${polygon.map(p=>`${(p[0]-left)/w*100}% ${(p[1]-top)/h*100}%`).join(',')})`;
    b.disabled=false;
  });
}
function pick(event) {
  const rect=stage.getBoundingClientRect(), point=[event.clientX-rect.left,event.clientY-rect.top];
  for(let i=2;i>=0;i--)if(inPolygon(point,hitPolygons[i]||[]) || (i!==active&&inPolygon(point,discPolygons[i]||[])))return i;
  if(hovered>=0&&inPolygon(point,cardPolygon(hovered,true)))return hovered;
  // A ray cast covers exposed moving parts beyond the fixed hit surface.
  pointer.set(point[0]/width*2-1,-point[1]/height*2+1);raycaster.setFromCamera(pointer,camera);
  for(const hit of raycaster.intersectObjects([...cards,...discs.filter((_,i)=>i!==active)],true)) {
    let obj=hit.object;while(obj){const index=cards.indexOf(obj),discIndex=discs.indexOf(obj);if(index>=0)return index;if(discIndex>=0&&discIndex!==active)return discIndex;obj=obj.parent;}
  }
  return -1;
}
stage.addEventListener('pointermove',event=>{if(event.pointerType!=='touch'&&ready&&!busy&&!dialog.open)setHovered(pick(event));});
stage.addEventListener('pointerleave',()=>setHovered(-1));
stage.addEventListener('click',event=>{
  if(event.target.closest('.scene-entry'))return;
  if(ready&&!intro&&!dialog.open){const index=pick(event);if(index>=0)selectEntry(index,event.target,false);}
});
document.querySelectorAll('[data-entry]').forEach(button=>{
  const index=Number(button.dataset.entry);
  button.addEventListener('pointerenter',event=>{if(event.pointerType!=='touch')setHovered(index);});
  button.addEventListener('pointerleave',()=>setHovered(-1));
  button.addEventListener('focus',()=>{focused=index;if(keyboardAction){setHovered(-1);needFrame();}});
  button.addEventListener('blur',()=>{focused=-1;needFrame();});
  button.addEventListener('click',event=>selectEntry(index,button,event.detail===0));
});
document.addEventListener('keydown',event=>{if(['Tab','Enter',' ','Escape'].includes(event.key)){keyboardAction=true;setHovered(-1);}if(event.key==='Escape'&&intro)finishIntro();});
document.addEventListener('pointerdown',()=>{keyboardAction=false;});

function finishIntro() {
  skipRequested=true;labelLoader.dismiss();
  if(!ready)return;
  stage.classList.add('loaded');
  intro=false;resetCards();pose(camera,metadata.hero.camera);pose(hinge,metadata.hero.hinge);pose(discs[active],metadata.playerDisc);
  cameraScale=metadata.hero.scale;fitCamera(cameraScale);hero.classList.add('ready');
  targets.forEach(b=>b.disabled=false);layoutTargets();
  try{sessionStorage.setItem('claire-v3-seen','1');}catch{}
  needFrame();
}
function playIntro() {
  if(!ready||busy||dialog.open)return;
  if(reduced||width<=600){finishIntro();return;}
  active=0;updateCurrent();resetCards();pose(discs[0],metadata.playerDisc);
  intro=true;introStart=performance.now();hero.classList.remove('ready');targets.forEach(b=>b.disabled=true);
  applyOpening(0);
  needFrame();
}
function applyOpening(elapsed) {
  const first=metadata.opening[0],openingView=metadata.opening[openingViewFrame];
  if(elapsed<openingViewDuration){
    const smooth=cameraWhipEase(elapsed/openingViewDuration);
    // Reach the existing lid-opening view before allowing the hinge to move.
    blendPose(camera,first.camera,openingView.camera,smooth);
    pose(hinge,first.hinge);pose(discs[0],first.disc);
    cameraScale=THREE.MathUtils.lerp(first.scale,openingView.scale,smooth);
  }else{
    const openingElapsed=elapsed-openingViewDuration;
    const lidProgress=ease(openingElapsed/lidOpeningDuration);
    // The exported hinge track includes an initial hold and an intermediate
    // hesitation. Use one continuous ease-out arc from closed to fully open.
    blendPose(hinge,first.hinge,metadata.hero.hinge,lidProgress);
    const frame=clamp(openingViewFrame+Math.max(0,openingElapsed-lidOpeningDuration)*30,openingViewFrame,126);
    const i=Math.floor(frame),t=frame-i;
    const a=metadata.opening[i],b=metadata.opening[Math.min(i+1,126)];
    blendPose(discs[0],a.disc,b.disc,t);
    blendPose(camera,a.camera,b.camera,t);
    cameraScale=THREE.MathUtils.lerp(a.scale,b.scale,t);
  }
  fitCamera(cameraScale);
}
$('skip-opening').addEventListener('click',finishIntro);
$('replay-opening').addEventListener('click',playIntro);

function openPanel(index,trigger,instant=false) {
  const worldPolygon=hitPolygons[2];
  const stageRect=stage.getBoundingClientRect();
  const worldOrigin=worldPolygon?.length ? {x:stageRect.left+worldPolygon.reduce((s,p)=>s+p[0],0)/worldPolygon.length,y:stageRect.top+worldPolygon.reduce((s,p)=>s+p[1],0)/worldPolygon.length} : null;
  disposeWorldEffects();
  disposeProjectNavigation();
  disposeAboutEffects();
  dialog.classList.toggle('about-panel', index === 0);
  dialog.classList.toggle('world-panel', index === 2);
  dialog.classList.toggle('projects-panel', index === 1);
  if(index === 2){
    dialog.style.setProperty('--world-board',`url("${assetURL('world-cork-board.jpg')}")`);
    dialog.style.setProperty('--world-pin',`url("${assetURL('world-pushpin.png')}")`);
    dialog.style.setProperty('--world-label-paper',`url("${assetURL('world-label-paper.svg')}")`);
  }
  if (index === 0) dialog.style.setProperty('--paper-texture', `url("${assetURL('paper-crumpled.png')}")`);
  if (index === 0) dialog.style.setProperty('--kraft-texture', `url("${assetURL('paper-kraft.png')}")`);
  if (index === 0) dialog.style.setProperty('--floral-border', `url("${assetURL('about-floral-border.svg')}")`);
  const entry=entries[index];lastTrigger=trigger || document.querySelector(`.nav-entry[data-entry="${index}"]`);
  dialog.style.setProperty('--accent',entry.color);
  $('panel-kicker').textContent=entry.code;$('panel-number').textContent=`0${index+1} — 03`;
  $('panel-content').innerHTML=index === 0
    ? `<div class="panel-content about-paper"><div class="about-chapter"><h2 id="panel-title">${entry.title}</h2><p>${entry.short}</p></div>${entry.body}<span class="about-tape" aria-hidden="true"></span><button type="button" class="about-sticker sticker-cat" aria-label="切换小猫表情" aria-pressed="false"><img class="cat-rest" src="${assetURL('sticker-cat.png')}" alt="" width="168" height="145"><img class="cat-hover" src="${assetURL('sticker-cat-hover.png')}" alt="" width="168" height="145"></button><img class="about-sticker sticker-acai" src="${assetURL('sticker-acai.png')}" alt="" width="90" height="115"></div>`
    : `<div class="panel-content"><div class="panel-lead"><div><h2 id="panel-title">${entry.title}</h2><p>${entry.short}</p></div><img class="panel-art" src="${assetURL(entry.art)}" alt="" width="210" height="210"></div>${entry.body}</div>`;
  if(index === 2) $('panel-content').innerHTML = `<div class="panel-content">${worldContent(assetURL)}</div>`;
  if (index === 0) {
    const heading = $('panel-content').querySelector('.about-introduction h3');
    heading.classList.add('handwritten-heading');
    heading.innerHTML = `<span class="sr-only">你好，我是 Claire，黄雯。</span><img src="${assetURL('about-title-handwritten.png')}" alt="" width="2172" height="724">`;
  }
  clearTimeout(closingTimer);dialog.classList.remove('closing');dialog.style.animationDuration=instant?'0s':'';
  if(!dialog.open)dialog.showModal();dialog.scrollTop=0;$('close-panel').focus({preventScroll:true});
  if(index === 0) mountAboutEffects(dialog, instant || reduced);
  if(index === 2) mountWorldEffects(dialog, instant || reduced, worldOrigin);
  if(index === 1) {
    const projectsHost = $('project-cards');
    projectsHost.innerHTML = projectContent();
    mountProjectNavigation(projectsHost);
  }
  hovered=-1;if(ready)resetCards();needFrame();
  $('announcement').textContent='已打开'+entry.title;
}
function closePanel() {
  if(!dialog.open)return;
  const finish=()=>{disposeWorldEffects();disposeProjectNavigation();disposeAboutEffects();dialog.close();dialog.classList.remove('closing');lastTrigger?.focus({preventScroll:true});layoutTargets();needFrame();};
  if(reduced||keyboardAction){finish();return;}
  if(dialog.classList.contains('world-panel')&&closeWorldEffects(finish))return;
  dialog.classList.add('closing');closingTimer=setTimeout(finish,170);
}
$('close-panel').addEventListener('click',closePanel);
let emailFeedbackTimer;
$('panel-content').addEventListener('click', async event => {
  const cat = event.target.closest('.sticker-cat');
  if (cat) {
    if (event.detail === 0 || matchMedia('(hover: none)').matches) {
      const active = cat.classList.toggle('cat-switched');
      cat.setAttribute('aria-pressed', String(active));
    }
    return;
  }
  const button = event.target.closest('#copy-email');
  if (!button) return;
  const email = button.dataset.email;
  const feedback = $('panel-content').querySelector('.email-feedback');
  let copied = false;
  try { await navigator.clipboard.writeText(email); copied = true; } catch {
    const input = document.createElement('textarea');
    input.value = email; input.style.cssText = 'position:fixed;left:-9999px';
    dialog.append(input); input.select();
    try { copied = document.execCommand('copy'); } catch {}
    input.remove(); button.focus({preventScroll:true});
  }
  if (!button.isConnected) return;
  button.querySelector('.email-label').textContent = copied ? '邮箱已复制' : '复制邮箱';
  feedback.textContent = copied ? `${email} 已复制到剪贴板` : `请手动复制：${email}`;
  clearTimeout(emailFeedbackTimer);
  emailFeedbackTimer = setTimeout(() => {
    if (button.isConnected) { button.querySelector('.email-label').textContent = '给我写邮件'; feedback.textContent = ''; }
  }, 4000);
});
dialog.addEventListener('cancel',event=>{event.preventDefault();closePanel();});
dialog.addEventListener('click',event=>{if(performance.now() < (window.claireBadgeClickUntil || 0)) return;if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closePanel();}});
function selectedImmediately(index,trigger) {
  if(ready){resetCards();active=index;cards.forEach((_,i)=>applyCard(i,0));pose(discs[index],metadata.playerDisc);updateCurrent();layoutTargets();}
  else {active=index;updateCurrent();}
  openPanel(index,trigger,true);
}
function selectEntry(index,trigger,fromKeyboard=false) {
  if(dialog.open)return;
  if(!ready){active=index;updateCurrent();openPanel(index,trigger,fromKeyboard);return;}
  if(intro)finishIntro();
  if(busy){queued={index,trigger,fromKeyboard};return;}
  if(reduced||fromKeyboard){selectedImmediately(index,trigger);return;}
  if(index===active){openPanel(index,trigger);return;}
  hovered=-1;busy=true;stage.classList.add('swapping');
  targets.forEach(b=>b.disabled=true);
  // Hand off from the actual current spring pose. Freeze sleeves while discs
  // travel; never instantiate or duplicate a disc during a change.
  swap={start:performance.now(),from:active,to:index,trigger,fromPose:snapshot(discs[active]),toPose:snapshot(discs[index])};
  needFrame();
}
function discSlot(index) {
  const base=metadata.cards[index],card={position:v(base.position),quaternion:q(base.quaternion),scale:v(base.scale)};
  const position=card.position.clone().add(new THREE.Vector3(0,-.25,.45).applyQuaternion(card.quaternion));
  const rotation=card.quaternion.clone().multiply(q(metadata.cards[1].quaternion).invert().multiply(q(metadata.discs[1].quaternion)));
  return {position:position.toArray(),quaternion:rotation.toArray(),scale:card.scale.toArray()};
}
// A single cubic keeps the travel tangent continuous: lift vertically at
// departure and approach vertically at arrival, with clearance above the lid.
function discRoute(start,end) {
  const clearance=Math.max(5.5,start.y+2,end.y+2);
  return new THREE.CubicBezierCurve3(start,start.clone().setY(clearance),end.clone().setY(clearance),end);
}
function routePose(obj,curve,from,to,progress,arriving=false) {
  const p=clamp(progress,0,1),t=p*p*(3-2*p);
  obj.position.copy(curve.getPoint(t));
  // Keep the outgoing disc flat while clearing the spindle; flatten the
  // incoming disc before its final descent. No rotation snap at handoff.
  const rotation=arriving?ease(clamp(p/.7,0,1)):ease(clamp((p-.2)/.8,0,1));
  obj.quaternion.copy(q(from.quaternion)).slerp(q(to.quaternion),rotation);
  obj.scale.copy(v(from.scale)).lerp(v(to.scale),t);
}
function updateSwap(now) {
  const elapsed=(now-swap.start)/1000,half=1.08;
  const outgoing=discs[swap.from],incoming=discs[swap.to];
  // Cache endpoints so sleeve hover cannot move a destination during travel.
  if(!swap.outRoute){
    swap.outSlot=discSlot(swap.from);swap.inSlot=discSlot(swap.to);
    swap.outRoute=discRoute(v(swap.fromPose.position),v(swap.outSlot.position));
    swap.inRoute=discRoute(v(swap.toPose.position),v(metadata.playerDisc.position));
  }
  if(elapsed<half){
    routePose(outgoing,swap.outRoute,swap.fromPose,swap.outSlot,elapsed/half);
  }else{
    pose(outgoing,swap.outSlot);
    routePose(incoming,swap.inRoute,swap.toPose,metadata.playerDisc,(elapsed-half)/half,true);
  }
  cameraScale=metadata.hero.scale+3.3*Math.sin(Math.PI*clamp(elapsed/(half*2),0,1));fitCamera(cameraScale);
  if(elapsed>=half*2){
    active=swap.to;const trigger=swap.trigger;swap=null;busy=false;stage.classList.remove('swapping');
    resetCards();pose(discs[active],metadata.playerDisc);updateCurrent();cameraScale=metadata.hero.scale;fitCamera(cameraScale);layoutTargets();
    if(queued){const next=queued;queued=null;selectEntry(next.index,next.trigger,next.fromKeyboard);}else openPanel(active,trigger);
  }
}

function resize() {
  if(!renderer)return;
  const rect=stage.getBoundingClientRect();width=Math.max(1,rect.width);height=Math.max(1,rect.height);
  renderer.setSize(width,height,false);fitCamera(cameraScale);layoutTargets();
  if(width<=600&&intro&&!loadingHandoff)finishIntro();
  $('scene-hint').textContent=matchMedia('(hover: none)').matches?'选一张，打开看看。':'移过去看看，点一下打开。';
  needFrame();
}
function tick(now) {
  scheduledFrame=0;
  if(loadingHandoff){scene.updateMatrixWorld(true);renderer.render(scene,camera);return;}
  if(document.hidden){lastTime=0;return;}
  const dt=lastTime?Math.max(0,(now-lastTime)/1000):0;lastTime=now;
  let moving=false;
  if(intro){
    const elapsed=(now-introStart)/1000;
    applyOpening(elapsed);
    if(elapsed>=openingDuration)finishIntro();else moving=true;
  }else if(busy){
    const travelling=discs.map(snapshot);
    for(let i=0;i<3;i++){
      [springValues[i],springVelocities[i]]=springStep(springValues[i],springVelocities[i],0,dt,40);
      applyCard(i,springValues[i]);
    }
    pose(discs[swap.from],travelling[swap.from]);pose(discs[swap.to],travelling[swap.to]);
    updateSwap(now);moving=true;
  }
  else{
    for(let i=0;i<3;i++) {
      const target=hovered===i?1:0;
      [springValues[i],springVelocities[i]]=reduced?[0,0]:springStep(springValues[i],springVelocities[i],target,dt,target?30:40);
      if(Math.abs(springValues[i]-target)<.0001&&Math.abs(springVelocities[i])<.001){springValues[i]=target;springVelocities[i]=0;}else moving=true;
      applyCard(i,springValues[i]);
    }
    // Decorative rotation never means sound is enabled. Suspend it in dialogs,
    // reduced-motion mode and hidden tabs.
    if(!reduced&&!dialog.open){discs[active].rotateY(dt*.12);moving=true;}
  }
  if(focused>=0&&keyboardAction) {
    targets[focused].style.background='#2858ca12';
  }else targets.forEach(button=>button.style.background='');
  scene.updateMatrixWorld(true);renderer.render(scene,camera);
  if(moving)needFrame();else lastTime=0;
}
document.addEventListener('visibilitychange',()=>{lastTime=0;if(!document.hidden){if(intro)finishIntro();needFrame();}});
reducedQuery.addEventListener('change',event=>{
  reduced=event.matches;hovered=-1;
  if(ready){if(intro)finishIntro();if(busy){const index=swap.to,trigger=swap.trigger;busy=false;swap=null;queued=null;stage.classList.remove('swapping');selectedImmediately(index,trigger);}resetCards();}
  needFrame();
});

// Playback starts only after a press; the four supplied tracks loop in order.
const audio=$('audio');
let trackIndex=0,playRequest=0;
function updateAudio() {
  const loaded=Boolean(audio.getAttribute('src')),playing=loaded&&!audio.paused;
  $('sound-label').textContent=playing?'暂停音乐':loaded?'继续播放':'播放音乐';
  $('audio-status').textContent=loaded?`${playing?'正在播放':'已暂停'} · ${playlist[trackIndex].title}`:'声音未开启';
  $('sound-toggle').setAttribute('aria-label',playing?'暂停音乐':loaded?'继续播放音乐':'播放内置歌单');
  $('sound-toggle').setAttribute('aria-pressed',String(playing));
  $('change-track').hidden=!loaded;
}
async function startAudio() {
  const request=++playRequest;
  try{await audio.play();if(request===playRequest)updateAudio();}
  catch{if(request===playRequest){updateAudio();$('audio-status').textContent='暂时无法播放，点击重试或下一首。';}}
}
function loadTrack(index) {
  ++playRequest;trackIndex=(index+playlist.length)%playlist.length;
  audio.src=window.CLAIRE_ASSETS?.music?.[playlist[trackIndex].file] || './music/'+encodeURIComponent(playlist[trackIndex].file);
  updateAudio();startAudio();
}
$('sound-toggle').addEventListener('click',()=>{
  if(!audio.getAttribute('src'))loadTrack(0);
  else if(audio.paused)startAudio();
  else{++playRequest;audio.pause();}
});
$('change-track').addEventListener('click',()=>loadTrack(trackIndex+1));
audio.addEventListener('ended',()=>loadTrack(trackIndex+1));
for(const event of ['play','pause'])audio.addEventListener(event,updateAudio);
audio.addEventListener('error',()=>{$('audio-status').textContent='这首暂时播放不了，点击下一首。';});
window.addEventListener('pagehide',()=>{++playRequest;audio.pause();});

async function initialize() {
  try{
    renderer=new THREE.WebGLRenderer({canvas:$('scene'),antialias:true,alpha:true,powerPreference:'high-performance'});
    renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;
    renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.08;
    renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.VSMShadowMap;
    scene=new THREE.Scene();camera=new THREE.OrthographicCamera(-5,5,3,-3,.01,200);
    const env=new RoomEnvironment(),pmrem=new THREE.PMREMGenerator(renderer);
    scene.environment=pmrem.fromScene(env,.045).texture;env.dispose();pmrem.dispose();
    scene.add(new THREE.HemisphereLight(0xffffff,0xb1b4b0,2.0));
    const light=new THREE.DirectionalLight(0xffffff,3.0);light.position.set(-3,10,7);light.castShadow=true;
    light.shadow.mapSize.set(1024,1024);light.shadow.camera.left=-9;light.shadow.camera.right=9;light.shadow.camera.top=9;light.shadow.camera.bottom=-9;
    light.shadow.normalBias=.025;light.shadow.bias=-.0002;light.shadow.radius=4;light.shadow.blurSamples=8;scene.add(light);
    const fill=new THREE.DirectionalLight(0xe8edff,1);fill.position.set(7,6,-4);scene.add(fill);
    const manager=new THREE.LoadingManager();manager.onProgress=(_,loaded,total)=>labelLoader.setProgress(loaded/total*.85);
    const loader=new GLTFLoader(manager),embedded=window.CLAIRE_ASSETS;
    labelLoader.setProgress(.03);
    const modelPromise=embedded?loader.parseAsync(Uint8Array.from(atob(embedded.model),c=>c.charCodeAt(0)).buffer,''):loader.loadAsync('./assets/claire-v3.glb',event=>{if(event.total)labelLoader.setProgress(.03+.67*event.loaded/event.total);});
    const motionPromise=embedded?Promise.resolve(embedded.motion):fetch('./assets/motion.json').then(r=>{if(!r.ok)throw Error('motion');return r.json();});
    const [motion,gltf]=await Promise.all([motionPromise,modelPromise]);
    metadata=motion;model=gltf.scene;scene.add(model);
    // Remove the extra title strips above the three original cover designs.
    const extraTitles = [];
    model.traverse(object => {
      // GLTFLoader replaces spaces in node names with underscores.
      if (/^Readable[ _]top[ _]title[ _](about|projects|world)$/.test(object.name)) extraTitles.push(object);
      if (/^Independent[ _](about|projects|world)[ _]insert$/.test(object.name) && object.geometry) {
        object.geometry = object.geometry.clone();
        const positions = object.geometry.attributes.position;
        for (let i = 0; i < positions.count; i++) {
          if (positions.getY(i) > 1.135) positions.setY(i, 1.135);
        }
        positions.needsUpdate = true;
        object.geometry.computeBoundingBox();
        object.geometry.computeBoundingSphere();
      }
    });
    extraTitles.forEach(title => title.removeFromParent());
    cards=metadata.names.cards.map(name=>model.getObjectByName(name));discs=metadata.names.discs.map(name=>model.getObjectByName(name));hinge=model.getObjectByName(metadata.names.hinge);
    if([...cards,...discs,hinge].some(o=>!o))throw Error('Model hierarchy missing');
    markers=cards.map(card=>card.children.find(n=>n.name.startsWith('Playing_marker')));
    // The old demonstration badge had baked world-space travel. Reuse the
    // stationary about badge's local transform for every content slot.
    if(markers[0])for(let i=1;i<3;i++){
      if(markers[i])cards[i].remove(markers[i]);
      markers[i]=markers[0].clone();markers[i].name='Playing_marker_'+i;cards[i].add(markers[i]);
    }
    const optical=opticalMaps();
    model.traverse(obj=>{
      if(!obj.isMesh)return;
      obj.castShadow=true;obj.receiveShadow=true;
      const material=obj.material;
      if(obj.name.includes('solid_optical_substrate')){
        obj.material=new THREE.MeshPhysicalMaterial({color:0xe1e4e6,metalness:1,roughness:.24,iridescence:1,iridescenceIOR:1.4,iridescenceThicknessRange:[140,680],iridescenceThicknessMap:optical.film,anisotropy:.8,anisotropyMap:optical.grooves,clearcoat:1,clearcoatRoughness:.16});
      }else if(obj.name.includes('printed_optical_face')){
        obj.material=new THREE.MeshStandardMaterial({map:material.map,metalness:.22,roughness:.36,alphaTest:.07,side:THREE.DoubleSide});
      }else if(obj.name.includes('name_label')){
        material.alphaTest=.1;material.side=THREE.DoubleSide;
      }else if(obj.name.includes('studio_cove')){
        obj.visible=false; // Seamless DOM background, with a soft shadow receiver below.
      }else if(material.name.includes('fine frosted')){
        material.roughness=.48;material.metalness=.65;
      }
      if(obj.material.map){obj.material.alphaTest=.08;obj.material.transparent=false;obj.material.depthWrite=true;obj.material.needsUpdate=true;obj.castShadow=false;}
    });
    const ground=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.ShadowMaterial({opacity:.09}));ground.rotation.x=-Math.PI/2;ground.position.y=-.03;ground.receiveShadow=true;scene.add(ground);
    // Compile before starting the clock; first-time shader preparation must not
    // consume the visitor's entrance.
    pose(camera,metadata.hero.camera);pose(hinge,metadata.hero.hinge);
    const initial=stage.getBoundingClientRect();width=initial.width;height=initial.height;
    renderer.setSize(width,height,false);cameraScale=metadata.hero.scale;fitCamera(cameraScale);
    await renderer.compileAsync(scene,camera);
    labelLoader.setProgress(.95);
    ready=true;updateCurrent();
    new ResizeObserver(resize).observe(stage);resize();
    if(skipRequested||dialog.open){finishIntro();}
    else {
      loadingHandoff=true;intro=true;targets.forEach(b=>b.disabled=true);
      applyOpening(0);scene.updateMatrixWorld(true);renderer.render(scene,camera);
      const outerLabel=model.getObjectByName('Closed_lid_outer_name_label');
      if(outerLabel)outerLabel.visible=false;
      await labelLoader.handoff(()=>stage.classList.add('loaded'),()=>{if(outerLabel)outerLabel.visible=true;scene.updateMatrixWorld(true);renderer.render(scene,camera);});
      if(outerLabel)outerLabel.visible=true;
      loadingHandoff=false;
      if(skipRequested||reduced||width<=600||dialog.open)finishIntro();else playIntro();
    }
    scene.updateMatrixWorld(true);renderer.render(scene,camera);
    window.dispatchEvent(new Event('claire-ready'));
  }catch(error){
    console.error('Claire scene could not load:',error);
    labelLoader.dismiss();
    stage.classList.add('failed');hero.classList.add('ready');$('scene-hint').textContent='选一张，打开看看。';
    targets.forEach(b=>b.disabled=true);
    $('announcement').textContent='三维场景暂时不可用，仍可用顶部入口浏览内容。';
  }
}
// Read-only diagnostics used by browser verification, with no production controls.
Object.defineProperty(window,'claireState',{get:()=>({ready,intro,active,hovered,busy,queued:queued?.index??null,reduced,dialogOpen:dialog.open,
  discCount:discs?.length??0,cardProgress:[...springValues],cardVelocity:[...springVelocities],
  discPositions:discs?.map(d=>d.position.toArray())??[],cameraScale,cameraQuaternion:camera?.quaternion.toArray(),hingeQuaternion:hinge?.quaternion.toArray(),introElapsed:intro?(performance.now()-introStart)/1000:null,hitPolygons,discPolygons})});
initialize();
