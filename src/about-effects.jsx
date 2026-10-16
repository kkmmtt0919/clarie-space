import React, { Suspense, Component, useState } from 'react';
import { createRoot } from 'react-dom/client';
import Lanyard from './Lanyard.jsx';

let root, host, paperAnimation;
const fallback = <div className="badge-static"><img src={window.CLAIRE_ASSETS?.images?.['badge-front.svg'] || './assets/badge-front.svg'} alt="Claire 的照片工牌" /></div>;
class BadgeBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? fallback : this.props.children; }
}
export function mountAboutEffects(dialog, instant) {
  disposeAboutEffects();
  host = document.createElement('div');
  host.className = 'about-badge-layer';
  host.setAttribute('aria-label', 'Claire 的悬挂工牌，可用鼠标或触摸拖动');
  dialog.append(host);
  root = createRoot(host);
  dialog.classList.add('badge-only');
  root.render(<AboutStage dialog={dialog} instant={instant} />);
}
function AboutStage({dialog, instant}) {
  const [revealed, setRevealed] = useState(false);
  function reveal() {
    if (revealed) return;
    setRevealed(true); dialog.classList.remove('badge-only');
    if (!instant) paperAnimation = dialog.querySelector('#panel-content').animate([
      {transform:'translateY(24px) rotate(-8deg) scale(.16)',opacity:0,offset:0},
      {transform:'translateY(-3px) rotate(.7deg) scale(1.025)',opacity:1,offset:.78},
      {transform:'translateY(0) rotate(0) scale(1)',opacity:1,offset:1}
    ],{duration:480,easing:'cubic-bezier(.23,1,.32,1)'});
    dialog.querySelector('#close-panel').focus({preventScroll:true});
    document.getElementById('announcement').textContent = '已展开关于我介绍';
  }
  return <>
    {instant ? fallback : <BadgeBoundary><Suspense fallback={null}><Lanyard revealed={revealed} onReveal={reveal}/></Suspense></BadgeBoundary>}
    {!revealed && <button className="reveal-about" onClick={reveal}>点一下工牌，展开介绍 <span aria-hidden="true">↗</span></button>}
  </>;
}
export function disposeAboutEffects() {
  paperAnimation?.cancel(); paperAnimation = null;
  document.getElementById('content-dialog')?.classList.remove('badge-only');
  root?.unmount(); host?.remove(); root = host = null;
}
