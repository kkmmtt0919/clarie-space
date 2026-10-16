import { springStep } from './spring.js';

const memories = [
  ['world-beads.jpg', '六小时的战利品', '花了六个小时，一颗一颗拼出来的战利品。'],
  ['world-flowers.jpg', '毕业那天的花', '拍毕业照那天，朋友送给我的花。很美，想把这份心意留在这里。'],
  ['world-miniature.jpg', '一起做的小世界', '和朋友一起做的微观世界，把小小的细节装进同一个世界。'],
  ['world-letter.jpg', '朋友给我的信', '收到的心意，也想好好收藏。']
];
let cleanup = () => {};
let exit = null;
export function closeWorldEffects(done) { if(!exit)return false;exit(done);return true; }
export function disposeWorldEffects() { cleanup(); cleanup = () => {};exit=null; }
export function worldContent(asset) {
  return `<div class="world-intro"><h2 id="panel-title">第三章 · 我的世界</h2><p>除了编程，我也喜欢尝试新鲜事物，丰富自己的日常。<br>这里收藏一些花了时间、收到心意，也舍不得忘记的瞬间。</p></div><div class="world-collection">${memories.map(([file,title,copy],i)=>`<article class="world-memory" style="--tilt:${[-3,3,2,-2][i]}deg"><button class="world-photo" type="button" data-memory="${i}" aria-label="放大查看：${title}"><span class="world-pin" aria-hidden="true"></span><img src="${asset(file)}" alt="${title}" width="${i===2?1706:1279}" height="${i===2?1279:1706}"><span class="world-photo-title">${title} <small aria-hidden="true">↗</small></span></button><p>${copy}</p></article>`).join('')}</div><aside class="world-note">编程之外，也想多体验一点。<span>SMALL THINGS, GOOD MEMORIES.</span></aside><div class="world-viewer" hidden><button type="button" class="world-viewer-close">收起照片 ×</button><img alt=""><p></p></div>`;
}
export function mountWorldEffects(dialog, instant, source) {
  disposeWorldEffects();
  const cards = [...dialog.querySelectorAll('.world-memory')];
  const viewer = dialog.querySelector('.world-viewer');
  const image = viewer.querySelector('img');
  const close = viewer.querySelector('button');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let frame = 0, last = 0, origin = null;
  const states = cards.map((el,i)=>({el,i,value:instant?1:0,velocity:0,hover:0,hv:0,target:0}));
  function draw(time) {
    const dt = last ? Math.min((time-last)/1000,.04) : .016; last=time;
    let moving=false;
    for(const s of states) {
      [s.value,s.velocity]=springStep(s.value,s.velocity,1,dt,32);
      [s.hover,s.hv]=springStep(s.hover,s.hv,s.target,dt,32);
      const t=s.value;
      s.el.style.transform=`translate(${(1-t)*(s.i%2?-32:32)}px,${(1-t)*(20+s.i*7)-s.hover*5}px) rotate(${(1-t)*(s.i%2?5:-5)}deg)`;
      s.el.style.opacity=Math.min(1,t*1.5);
      moving ||= Math.abs(1-t)+Math.abs(s.velocity)+Math.abs(s.target-s.hover)+Math.abs(s.hv)>.002;
    }
    frame=moving?requestAnimationFrame(draw):0;
  }
  const wake=()=>{if(!frame){last=0;frame=requestAnimationFrame(draw);}};
  const reset=()=>{cancelAnimationFrame(frame);frame=0;for(const s of states){s.value=1;s.velocity=0;s.hover=0;s.hv=0;s.target=0;s.el.style.transform='none';s.el.style.opacity='1';}};
  const controller=new AbortController(), options={signal:controller.signal};
  cards.forEach((card,i)=>{
    card.addEventListener('pointerenter',e=>{if(!motion.matches&&e.pointerType!=='touch'){states[i].target=1;wake();}},options);
    card.addEventListener('pointerleave',()=>{states[i].target=0;if(!motion.matches)wake();},options);
  });
  function dismiss(){viewer.hidden=true;origin?.focus({preventScroll:true});}
  dialog.addEventListener('click',e=>{
    const button=e.target.closest('[data-memory]');
    if(button){origin=button;image.src=button.querySelector('img').src;image.alt=memories[+button.dataset.memory][1];viewer.querySelector('p').textContent=memories[+button.dataset.memory][2];viewer.hidden=false;close.focus({preventScroll:true});}
    else if(e.target===viewer||e.target===close)dismiss();
  },options);
  dialog.addEventListener('cancel',e=>{if(!viewer.hidden){e.preventDefault();e.stopImmediatePropagation();dismiss();}}, {...options,capture:true});
  dialog.addEventListener('keydown',e=>{if(!viewer.hidden&&e.key==='Tab'){e.preventDefault();close.focus();}},options);
  motion.addEventListener('change',reset,options);
  reset();
  const disposeEntrance = instant ? ()=>{} : collectionTransition(dialog, cards, source, motion);
  cleanup=()=>{controller.abort();cancelAnimationFrame(frame);disposeEntrance();};
}

// A separate visual layer carries the same photos between the sleeve and their
// measured reading positions. Layout and focus remain stable underneath it.
function collectionTransition(dialog, cards, source, motion) {
  const narrow=innerWidth<=600;
  const anchor=source||{x:innerWidth*.75,y:innerHeight*.45};
  if(narrow){anchor.x=innerWidth*.65;anchor.y=Math.min(anchor.y,innerHeight*.45);}
  const layer=document.createElement('div');layer.className='world-flight';layer.setAttribute('aria-hidden','true');
  dialog.append(layer);
  let flights=[],progress=0,velocity=0,frame=0,start=performance.now(),last=start,closing=false,finished=false,done=null;
  let closingStart=0;
  const clamp=x=>Math.max(0,Math.min(1,x));
  function measure(){
    layer.replaceChildren();
    const measured=cards.map((card,i)=>{
      const original=card.querySelector('.world-photo'),r=original.getBoundingClientRect();
      return {original,r,i,width:original.offsetWidth,height:original.offsetHeight};
    });
    flights=measured.map(({original,r,i,width,height})=>{
      const clone=original.cloneNode(true);clone.removeAttribute('data-memory');clone.removeAttribute('aria-label');clone.tabIndex=-1;clone.classList.add('world-flying-photo');
      clone.style.width=width+'px';clone.style.height=height+'px';layer.append(clone);
      return {el:clone,x:r.left+r.width/2,y:r.top+r.height/2,width,height,tilt:[-3,3,2,-2][i],i};
    });
  }
  function paint(){
    const travel=clamp(progress/.28),spread=Math.max(0,(progress-.25)/.75);
    const spreadClamped=clamp(spread),ink=clamp((progress-.72)/.28);
    dialog.style.setProperty('--world-spread',spreadClamped);
    dialog.style.setProperty('--world-ink',ink);
    dialog.style.setProperty('--world-dim',clamp(progress*2));
    for(const f of flights){
      const cx=innerWidth/2,cy=Math.min(innerHeight*.47,400);
      const stackedX=anchor.x+(cx-anchor.x)*travel;
      const stackedY=anchor.y+(cy-anchor.y)*travel;
      const x=stackedX+(f.x-stackedX)*spread,y=stackedY+(f.y-stackedY)*spread;
      const small=Math.min(narrow?130:170,f.width)/f.width;
      const scale=small+(1-small)*spread;
      f.el.style.transform=`translate(${x-f.width/2}px,${y-f.height/2}px) rotate(${(1-spread)*(f.i-1.5)*7+f.tilt*spread}deg) scale(${scale})`;
      f.el.style.opacity=closing?clamp(progress/.18):clamp(progress/.07);
    }
  }
  function restore(){
    finished=true;layer.hidden=true;layer.replaceChildren();dialog.classList.remove('world-unfolding');
    dialog.style.setProperty('--world-spread',1);dialog.style.setProperty('--world-ink',1);dialog.style.setProperty('--world-dim',1);
  }
  function tick(time){
    const dt=Math.min((time-last)/1000,.04);last=time;
    const target=closing?0:(time-start<200?.28:1);
    [progress,velocity]=springStep(progress,velocity,target,dt*(closing||target===.28?1:.65),closing?38:32);
    paint();
    if(closing&&time-closingStart>=300){const callback=done;done=null;callback?.();return;}
    if(!closing&&time-start>=800&&Math.abs(1-progress)<.003){restore();frame=0;return;}
    frame=requestAnimationFrame(tick);
  }
  measure();dialog.classList.add('world-unfolding');paint();frame=requestAnimationFrame(tick);
  exit=callback=>{
    if(closing)return;
    done=callback;closing=true;closingStart=performance.now();
    viewerDismiss();
    if(finished){measure();progress=1;velocity=0;finished=false;layer.hidden=false;dialog.classList.add('world-unfolding');}
    if(!frame){last=performance.now();frame=requestAnimationFrame(tick);}
  };
  function viewerDismiss(){dialog.querySelector('.world-viewer').hidden=true;}
  const reduce=()=>{cancelAnimationFrame(frame);frame=0;if(closing){const callback=done;done=null;callback?.();}else restore();};
  const resize=()=>{if(closing)reduce();else{cancelAnimationFrame(frame);frame=0;restore();}};
  motion.addEventListener('change',reduce);window.addEventListener('resize',resize);
  return ()=>{cancelAnimationFrame(frame);layer.remove();dialog.classList.remove('world-unfolding');for(const name of ['--world-spread','--world-ink','--world-dim'])dialog.style.removeProperty(name);motion.removeEventListener('change',reduce);window.removeEventListener('resize',resize);};
}

