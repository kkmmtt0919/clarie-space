export const entries = [
  {
    title: '第一章 · 关于我', short: '一些关于 Claire 的线索。', code: '01 / ABOUT CLAIRE', color: '#d3432e', art: 'cover-about.png',
    body: '<div class="about-introduction"><h3>你好，我是 Claire，黄雯。</h3><div class="about-copy"><p>遇到感兴趣的想法，我总想亲手做出来，看看它能解决什么问题，又能带来什么乐趣。我享受从一团模糊的念头，到一点点理清、做成、改好的过程。</p><p>写代码之外，我也喜欢游泳、学点新东西，给日常留一些探索的空间。这里放着我的作品，也记录着我慢慢摸索的生活。</p></div><p class="about-status" aria-label="目前状态">大四在读 <span>/</span> 寻找实习 <span>/</span> 探索 AI 产品</p><div class="about-contacts"><button type="button" id="copy-email" data-email="kkmtthw@163.com"><span aria-hidden="true">✉</span> <span class="email-label">给我写邮件</span><small>复制邮箱</small></button><a href="https://github.com/kkmmtt0919" target="_blank" rel="noopener noreferrer"><span aria-hidden="true">↗</span> 逛逛我的 GitHub</a></div><p class="email-feedback" role="status" aria-live="polite"></p></div>'
  },
  {
    title: '第二章 · 我的作品', short: '把想法做成可以用的东西。', code: '02 / MADE & MAKING', color: '#2858ca', art: 'cover-projects.png',
    body: '<div id="project-cards" tabindex="-1"></div>'
  },
  {
    title: '第三章 · 我的世界', short: '手作、新体验，还有日常。', code: '03 / OFF DUTY', color: '#617024', art: 'cover-world.png',
    body: '' // The photo collection is rendered by worldContent in world-effects.js.
  }
];
