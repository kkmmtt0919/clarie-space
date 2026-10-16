import * as THREE from 'three';
import layout from './loading-label.json';

export function createLabelLoader(stage, reduced) {
  const host = document.getElementById('loading');
  const label = host.querySelector('.loading-label');
  const ring = host.querySelector('.loading-ring-progress');
  const image = host.querySelector('img');
  image.src = window.CLAIRE_ASSETS?.images['loading-label.svg'] || './assets/loading-label.svg';
  let progress = 0, displayed = 0, scale = 1, closed = false, complete;
  let progressFrame = 0, progressTime = performance.now(), progressComplete;
  let paceTime = 0, progressVelocity = 0;
  const pauses = new Map();
  const animations = [];
  function position() {
    if (closed) return;
    const {width:w,height:h} = stage.getBoundingClientRect();
    const aspect = w/h;
    let vw = layout.scale * (w>600 ? 1.22 : 1.04);
    if (aspect<1.35) vw=Math.max(vw,11.8);
    const vh=vw/aspect, offset=vh*(w>600?.09:.05);
    const camera = new THREE.OrthographicCamera(-vw/2,vw/2,vh/2+offset,-vh/2+offset,.01,200);
    camera.position.fromArray(layout.camera.position);camera.quaternion.fromArray(layout.camera.quaternion);camera.updateMatrixWorld();
    const points = layout.points.map(({uv,point})=>{const p=new THREE.Vector3(...point).project(camera);return {uv,x:(p.x*.5+.5)*w,y:(-p.y*.5+.5)*h};});
    const origin=points.find(p=>p.uv[0]===0&&p.uv[1]===0), right=points.find(p=>p.uv[0]===1&&p.uv[1]===0), bottom=points.find(p=>p.uv[0]===0&&p.uv[1]===1);
    const a=(right.x-origin.x)/1000,b=(right.y-origin.y)/1000,c=(bottom.x-origin.x)/1000,d=(bottom.y-origin.y)/1000;
    label.style.transform=`matrix(${a},${b},${c},${d},${origin.x},${origin.y})`;
    // Magnify around the printed label's center, keeping its screen anchor fixed.
    scale=Math.min(2.2,Math.max(1.45,240/(Math.hypot(a,b)*700)));
    host.querySelector('.loading-label-art').style.transform=`scale(${scale})`;
    host.dataset.positioned='true';
  }
  const observer=new ResizeObserver(position);observer.observe(stage);position();
  function drawProgress(now) {
    progressFrame=0;
    if(closed)return;
    const dt=Math.min(64,Math.max(0,now-progressTime));progressTime=now;
    if(reduced()){
      displayed=progress;progressVelocity=0;
    }else{
      paceTime+=dt/1000;
      const phase=Math.min(1,paceTime/1.2);
      // A smooth lead: quicker at the start, gently held through the middle.
      const paced=phase+.075*Math.sin(2*Math.PI*phase);
      const target=Math.min(progress,paced);
      // Exact critically damped spring, retaining velocity across resource updates.
      const seconds=dt/1000,frequency=16,offset=displayed-target;
      const coefficient=progressVelocity+frequency*offset,decay=Math.exp(-frequency*seconds);
      const next=target+(offset+coefficient*seconds)*decay;
      progressVelocity=(progressVelocity-frequency*coefficient*seconds)*decay;
      displayed=Math.max(displayed,Math.min(target,next));
      if(target===progress&&progress-displayed<.0005&&Math.abs(progressVelocity)<.01){displayed=progress;progressVelocity=0;}
    }
    ring.style.strokeDashoffset=String(1-displayed);
    host.setAttribute('aria-label',`唱片场景加载中，${Math.round(displayed*100)}%`);
    if(displayed<progress)progressFrame=requestAnimationFrame(drawProgress);
    else if(displayed===1)progressComplete?.();
  }
  function setProgress(value) {
    progress=Math.max(progress,Math.min(value,1));
    if(!closed&&!progressFrame){progressTime=performance.now();progressFrame=requestAnimationFrame(drawProgress);}
  }
  function pause(ms) {
    return new Promise(resolve=>{const timer=setTimeout(()=>{pauses.delete(timer);resolve();},ms);pauses.set(timer,resolve);});
  }
  function dismiss() {
    if(closed)return;
    closed=true;observer.disconnect();cancelAnimationFrame(progressFrame);
    for(const [timer,resolve] of pauses){clearTimeout(timer);resolve();}pauses.clear();
    animations.forEach(a=>a.cancel());host.hidden=true;progressComplete?.();complete?.();
  }
  async function handoff(reveal, revealPrint) {
    if(closed){reveal();return;}
    setProgress(1);
    await image.decode().catch(()=>{});
    if(closed){reveal();return;}
    // Finish the full outline before holding it briefly and shrinking the name.
    if(displayed<1)await new Promise(resolve=>progressComplete=resolve);
    if(!closed&&!reduced())await pause(150);
    if(closed){reveal();return;}
    const duration=reduced()?160:480;
    const art=host.querySelector('.loading-label-art');
    const shrink=art.animate(reduced()?[{opacity:1},{opacity:0}]:[{transform:`scale(${scale})`},{transform:'scale(1)'}],{duration,easing:'cubic-bezier(.23,1,.32,1)',fill:'forwards'});
    animations.push(shrink,host.querySelector('.loading-ring').animate([{opacity:1},{opacity:0}],{duration:140,fill:'forwards'}));
    const timer=setTimeout(reveal,reduced()?0:200);
    const printTimer=setTimeout(()=>{
      revealPrint?.();
      animations.push(art.animate([{opacity:1},{opacity:0}],{duration:100,fill:'forwards'}));
    },duration-100);
    await Promise.race([shrink.finished.catch(()=>{}),new Promise(resolve=>complete=resolve)]);
    clearTimeout(timer);clearTimeout(printTimer);reveal();revealPrint?.();dismiss();
  }
  return {setProgress,handoff,dismiss};
}

