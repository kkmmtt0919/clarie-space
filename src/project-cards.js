import { projects } from './projects.js';
import { springStep } from './spring.js';

const imageURL = name => window.CLAIRE_ASSETS?.images?.[name] || `./assets/${name}`;

// Original implementation based on the user's video; not React Bits source.
const cover = (p, i) => {
  const art = i === 0
    ? `<rect width="240" height="360" fill="#244bc3"/><path d="M-30 280L270 80M-30 310L270 110M-30 340L270 140" stroke="#6d8cf0" stroke-width="1"/><circle cx="192" cy="67" r="65" fill="#f0a55f"/><image href="${imageURL('growth-dashboard.png')}" x="22" y="106" width="285" height="187" preserveAspectRatio="xMinYMid slice"/><path d="M35 307h165m-9-9 9 9-9 9" fill="none" stroke="#fcf4dd" stroke-width="2"/><text x="23" y="48" fill="#fcf4dd" font-size="13">GROWTH LOOP</text><text x="23" y="330" fill="#fcf4dd" font-size="10">真实界面 · 受控 DEMO</text>`
    : i === 1
    ? `<rect width="240" height="360" fill="#edb28b"/><circle cx="240" cy="50" r="138" fill="#f5d3b8"/><text x="22" y="48" fill="#66321f" font-size="13">TEST / RETRIEVE / RUN</text><text x="16" y="139" fill="#66321f" font-size="67" font-weight="700">RAG</text><g fill="#faf2e4" stroke="#66321f" stroke-width="1.5"><rect x="36" y="174" width="159" height="49" rx="5"/><rect x="28" y="185" width="159" height="49" rx="5"/><rect x="20" y="196" width="159" height="49" rx="5"/></g><text x="35" y="224" fill="#66321f" font-size="12">需求 → 检索 → 生成</text><path d="M99 245v32h88m-9-9 9 9-9 9" fill="none" stroke="#66321f" stroke-width="2"/><text x="22" y="307" fill="#66321f" font-size="14">MCP → 执行 → 反馈</text><text x="22" y="330" fill="#66321f" font-size="10">项目流程示意</text>`
    : `<rect width="240" height="360" fill="#e9eadc"/><text x="22" y="48" fill="#555e32" font-size="13">A LITTLE TIME TO FOCUS</text><circle cx="120" cy="160" r="72" fill="#f7f5ec" stroke="#d9dbca" stroke-width="9"/><circle cx="120" cy="160" r="72" fill="none" stroke="#d3432e" stroke-width="9" stroke-dasharray="339 453" transform="rotate(-90 120 160)"/><text x="120" y="167" text-anchor="middle" fill="#d3432e" font-size="32">25:00</text><g fill="#737d47">${[17,32,24,44,28,53,37].map((h,n)=>`<rect x="${32+n*26}" y="${298-h}" width="14" height="${h}" rx="3"/>`).join('')}</g><text x="22" y="330" fill="#555e32" font-size="10">圆环与七天统计 · 功能示意</text>`;
  return `<svg viewBox="0 0 240 360" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" font-family="Arial, Microsoft YaHei, sans-serif">${art}</svg>`;
};
let cleanup;
export function disposeProjectNavigation() { cleanup?.(); cleanup = null; }
export function projectContent() {
  return `<div class="project-spread" aria-label="三个独立项目">${projects.map((p,i) => `
    <a class="project-cover" href="#${p.id}" data-project="${i}" aria-label="${p.title}，独立项目，查看详情">
      ${cover(p,i)}<span class="project-cover-caption"><span>0${i+1} / 独立项目</span><strong>${p.title}</strong></span>
    </a>`).join('')}</div>
    <div class="project-details" hidden>${projects.map(p => `
      <article class="project-detail" hidden id="${p.id}" tabindex="-1" style="--project-color:${p.color}">
        <div class="project-detail-top"><span class="project-code">${p.label} · 独立项目</span><button type="button" class="project-back">返回三张卡片 ↖</button></div>
        <h3>${p.title}</h3><p class="project-flow">${p.flow}</p>
        <dl>${[['为什么做',p.why],['怎么使用',p.how],['我做了什么',p.built],['下一步想改善什么',p.next]].map(([q,a]) => `<div><dt>${q}</dt><dd>${a}</dd></div>`).join('')}</dl>
        ${p.scope ? `<p class="project-scope">${p.scope}</p>` : ''}
        ${p.images.length ? `<div class="project-screens">${p.images.map(([name,alt]) => `<figure><img src="${imageURL(name)}" alt="成长回路${alt}真实界面" loading="lazy"><figcaption>${alt} · 受控 Demo 截图</figcaption></figure>`).join('')}</div>` : ''}
        ${p.download ? `<a class="project-download" href="${window.CLAIRE_ASSETS?.downloads?.[p.download] || `./assets/downloads/${p.download}`}" download="${p.download}">下载番茄专注 · Windows .exe ↓</a>` : ''}
        ${p.repo ? `<a class="project-repo" href="${p.repo}" target="_blank" rel="noopener noreferrer">查看项目仓库 ↗</a>` : ''}
      </article>`).join('')}</div>`;
}

export function mountProjectNavigation(container) {
  disposeProjectNavigation();
  const abort = new AbortController(), options = { signal: abort.signal };
  const fan = container.querySelector('.project-spread'), cards = [...fan.querySelectorAll('.project-cover')];
  const details=container.querySelector('.project-details'), articles=[...details.querySelectorAll('.project-detail')];
  const dialog=container.closest('dialog');
  let entrance=null,transition=0,restoreFan=null,returningFocus=false;
  const animations=[];
  const surface=document.createElement('div');surface.className='project-window-surface';surface.hidden=true;surface.setAttribute('aria-hidden','true');dialog.prepend(surface);
  const stop=()=>{transition++;animations.splice(0).forEach(a=>a.cancel());restoreFan?.();restoreFan=null;};
  const animate=(el,frames,settings)=>{const a=el.animate(frames,settings);animations.push(a);return a;};
  const enter=()=>{if(motion.matches)return;entrance=fan.animate([{transform:'translateY(85px) scale(.82)',opacity:0},{transform:'translateY(-28px) scale(1.06)',opacity:1,offset:.3},{transform:'translateY(14px) scale(.97)',offset:.48},{transform:'translateY(-10px) scale(1.02)',offset:.65},{transform:'translateY(5px) scale(.99)',offset:.8},{transform:'translateY(0) scale(1)',opacity:1}],{duration:950,easing:'ease-out'});};
  const motion = matchMedia('(prefers-reduced-motion: reduce)'), pointer = matchMedia('(hover: hover) and (pointer: fine)');
  let selected = 0, active = -1, raf = 0, last = 0;
  const values = [0,0,0], velocities = [0,0,0];
  const render = () => cards.forEach((card,i) => {
    const shift = values.reduce((sum,v,j) => sum + (i===j ? 0 : Math.sign(i-j)*v*3.6/(Math.abs(i-j))),0);
    const degrees = (i-1)*22+shift, radians = degrees*Math.PI/180;
    const radius = 390 + values[i]*26;
    card.style.transform = `translate(-50%, 0) translate(${Math.sin(radians)*radius}px, ${390-Math.cos(radians)*radius}px) rotate(${degrees}deg)`;
    card.style.zIndex = active === i ? '10' : String(3-Math.abs(i-1));
  });
  const tick = time => {
    raf = 0;
    const dt = Math.min((time-last)/1000, .04); last=time;
    let moving = false;
    cards.forEach((_,i) => {
      const target = active===i ? 1 : 0;
      [values[i],velocities[i]] = springStep(values[i],velocities[i],target,dt);
      if(Math.abs(values[i]-target)>.0005 || Math.abs(velocities[i])>.005) moving=true;
      else { values[i]=target; velocities[i]=0; }
    });
    render(); if(moving) raf=requestAnimationFrame(tick);
  };
  const retarget = (index, instant=false) => {
    active=index;
    if(instant || motion.matches) {
      cancelAnimationFrame(raf); raf=0;
      cards.forEach((_,i)=>{values[i]= !motion.matches && i===index ? 1 : 0; velocities[i]=0;}); render();
    } else if(!raf) {last=performance.now(); raf=requestAnimationFrame(tick);}
  };
  const select = (index,keyboard=false) => {
    const opening=!container.classList.contains('project-reading');
    const origin=cards[index].getBoundingClientRect(),oldFan=fan.getBoundingClientRect();
    stop();selected=index;entrance?.cancel();dialog.append(fan);container.classList.add('project-reading');dialog.classList.add('projects-reading');surface.hidden=false;
    details.hidden=false;articles.forEach((article,i)=>article.hidden=i!==index);
    cards.forEach((card,i)=>card.setAttribute('aria-current',String(i===index)));
    resizeFan();dialog.scrollTop=0;
    if(opening&&!motion.matches&&!keyboard){
      const destination=dialog.getBoundingClientRect(),newFan=fan.getBoundingClientRect();
      const start=`translate(${origin.left-destination.left}px,${origin.top-destination.top}px) scale(${origin.width/destination.width},${origin.height/destination.height})`;
      animate(surface,[{transform:start,opacity:.4},{transform:'translate(0,0) scale(1)',opacity:1}],{duration:520,easing:'cubic-bezier(.22,1,.36,1)'});
      animate(fan,[{transform:`translate(${oldFan.left-newFan.left}px,${oldFan.top-newFan.top}px) scale(${oldFan.width/newFan.width})`},{transform:'translate(0,0) scale(1) rotate(-8deg)'}],{duration:520,easing:'cubic-bezier(.22,1,.36,1)'});
      animate(details,[{opacity:0,offset:0},{opacity:0,offset:.35},{opacity:1}],{duration:520});
    }
    articles[index].focus({preventScroll:true});
  };
  const back=(keyboard=false)=>{
    stop();const id=transition;
    const finish=()=>{if(id!==transition)return;container.classList.remove('project-reading');dialog.classList.remove('projects-reading');details.hidden=true;surface.hidden=true;container.prepend(fan);resizeFan();returningFocus=true;cards[selected].focus({preventScroll:true});returningFocus=false;dialog.scrollTop=0;};
    if(motion.matches||keyboard){finish();return;}
    const card=cards[selected].getBoundingClientRect(),r=dialog.getBoundingClientRect();
    // Measure the chooser destination synchronously, without painting the new layout.
    const fanStyle=fan.getAttribute('style'), startTransform=getComputedStyle(fan).transform;
    restoreFan=()=>{if(fanStyle===null)fan.removeAttribute('style');else fan.setAttribute('style',fanStyle);};
    const startScale=parseFloat(getComputedStyle(fan).getPropertyValue('--spread-scale'));
    container.classList.remove('project-reading');dialog.classList.remove('projects-reading');
    details.hidden=true;container.prepend(fan);resizeFan();
    const destination=cards[selected].getBoundingClientRect();
    const destinationScale=parseFloat(getComputedStyle(fan).getPropertyValue('--spread-scale'));
    container.classList.add('project-reading');dialog.classList.add('projects-reading');
    details.hidden=false;dialog.append(fan);
    if(fanStyle===null)fan.removeAttribute('style');else fan.setAttribute('style',fanStyle);
    // Keep the fan in its reading layout while it travels; commit only at the end.
    fan.style.animation='none';fan.style.transformOrigin='0 0';fan.style.transform='none';
    const base=fan.getBoundingClientRect(),source=cards[selected].getBoundingClientRect();
    const ratio=destinationScale/startScale;
    const x=destination.left+destination.width/2-base.left-ratio*(source.left+source.width/2-base.left);
    const y=destination.top+destination.height/2-base.top-ratio*(source.top+source.height/2-base.top);
    // The old CSS transform rotated around the center; preserve that exact pose.
    const matrix=new DOMMatrix(startTransform),cx=fan.clientWidth/2,cy=fan.clientHeight/2;
    const initial=new DOMMatrix().translate(cx,cy).multiply(matrix).translate(-cx,-cy);
    const travel=animate(fan,[{transform:initial.toString()},{transform:`translate(${x}px,${y}px) scale(${ratio})`}],{duration:280,easing:'cubic-bezier(.22,1,.36,1)',fill:'forwards'});
    const a=animate(surface,[{transform:'translate(0,0) scale(1)',opacity:1},{transform:`translate(${card.left-r.left}px,${card.top-r.top}px) scale(${card.width/r.width},${card.height/r.height})`,opacity:0}],{duration:280,easing:'cubic-bezier(.22,1,.36,1)',fill:'forwards'});
    animate(details,[{opacity:1},{opacity:0}],{duration:160,fill:'forwards'});
    a.finished.then(()=>{if(id!==transition)return;travel.cancel();restoreFan?.();restoreFan=null;finish();}).catch(()=>{});
  };
  cards.forEach((card,i) => {
    card.addEventListener('pointerenter',()=>{if(pointer.matches){retarget(i);}},options);
    card.addEventListener('focus',()=>{if(!returningFocus)retarget(i,true);},options);
  });
  fan.addEventListener('pointerleave',()=>{if(pointer.matches){retarget(-1);}},options);
  fan.addEventListener('focusout',event=>{if(!fan.contains(event.relatedTarget))retarget(-1,true);},options);
  motion.addEventListener('change',()=>{entrance?.cancel();stop();retarget(-1,true);},options);
  function resizeFan(){
    const scale=Math.min(1,Math.max(.1,(fan.clientWidth-16)/650));
    fan.style.setProperty('--spread-scale',scale);fan.style.height=`${430*scale}px`;
  }
  const resize=new ResizeObserver(resizeFan);
  resize.observe(fan);render();enter();
  dialog.addEventListener('click', event => {
    const card=event.target.closest('[data-project]');
    if(card){event.preventDefault();select(Number(card.dataset.project),event.detail===0);retarget(-1,true);return;}
    if(event.target.closest('.project-back'))back(event.detail===0);
  },options);
  cleanup=()=>{stop();surface.remove();fan.remove();entrance?.cancel();cancelAnimationFrame(raf);resize.disconnect();abort.abort();dialog.classList.remove('projects-reading');};
}
