# Claire · HTML V3

项目已统一整理到 **`D:/projects/claire`**。双击根目录的 `claire.html` 查看网页；开发也从本目录进行。

网页源码在根目录，当前模型在 `models/modern-v03`，设计文档在 `docs/handoff`，早期图在 `references`，审阅与检查在 `reviews` / `checks`，本地动画 skill 在 `skills/emil-design-eng`。完整索引见 [项目目录说明](D:/projects/claire/docs/项目目录说明.md)。

基于已经确认的 Blender V3 和交互设计稿制作，模型与印刷资产直接从 V3 导出。原 V2、V3 Blender 文件与存档保持不变。

## 直接打开

**双击 `D:/projects/claire/claire.html`，用 Edge 或 Chrome 打开。**

这是约 7 MB 的单文件 HTML：样式、JavaScript、三维模型、贴图、动画参数和面板图片全部内嵌。不需要安装 Node、启动服务器或联网。已在 Edge 中实际验证 `file://` 打开、三维加载、内容面板与零外部请求。

可维护的分文件版本入口为 `index.html`，需通过 HTTP 打开。默认本地地址：`http://127.0.0.1:4193`。之后双击 `start-preview.cmd`，或在本目录运行 `npm start` 即可启动；使用此方式需本机已安装 Node。本次迁移检查使用 `http://127.0.0.1:4194`，避免与旧预览混淆。

## 已实现

- 资源与材质就绪后播放约 4.2 秒开场：闭盖俯视、轻启盖、展开、连续拉远倾斜、平稳收尾。开场可跳过，同一会话再次访问直接显示主画面；移动端默认主画面。
- 三入口即时悬停：保留位置和速度的解析弹簧，刚度 500、进入阻尼 30、退出阻尼 40；一次小幅过冲。固定原始命中区域并补充移动盘面的射线命中，快速切换连贯。
- 备用盘随自己的夹页运动，正在播放的盘在盘仓中。三个内容盘始终是三个实体，换盘不复制模型。
- 点击切换内容盘：旧盘从前方上层通道归位，新盘经过同一安全区域入仓，随后打开内容面板。动画期间连续选择保留最后一个目标。
- 关于我、作品、世界三个独立内容面板；关闭保持当前盘与机位，不重播开场。
- 键盘 Tab、Enter、Space、Escape；焦点提示、原生模态焦点约束与关闭后返回入口。键盘选择直接切换，省略空间飞行动画。
- 手机单次点击选择；减少动态效果模式取消入场、回弹、旋转和换盘飞行。隐藏标签页暂停渲染。
- 选择本地音频、播放、暂停与换一首。音乐不自动开启，文件只在浏览器本地使用，不上传。
- 三维资源不可用时显示静态画面，顶部三个内容入口仍能使用。

## 内容边界

已沿用批准的短文案和三个主题，没有补造个人经历、项目成绩、真实项目截图或歌单。作品面板当前显示“作品正在整理”；正式内容集中在 `src/content.js`，可替换为 Claire 确认过的介绍与作品。

音乐没有预置曲目，当前通过页面左下角选择本地音频。以后提供可用的音乐文件时，可替换这一入口。

## 文件与修改

| 文件 | 用途 |
| --- | --- |
| `claire.html` | 可离线直接打开的交付文件 |
| `index.html` / `style.css` | 可维护的页面结构与样式 |
| `src/app.js` | 三维、开场、悬停、换盘、面板和音频状态 |
| `src/spring.js` | 保留速度的解析弹簧 |
| `src/content.js` | 三个面板的文案 |
| `assets/claire-v3.glb` | 导出的独立三维模型与打包贴图 |
| `assets/motion.json` | V3 原始入场逐帧机位、盖子、盘面及基准位置 |
| `tools/export_scene.py` | Blender 背景导出，不保存源模型 |
| `tools/pack-standalone.cjs` | 将所有依赖打包为单个 HTML |
| `checks/` | 实际浏览器截图与检查记录 |

修改后在本目录运行：

```powershell
npm run build
```

这会重新生成 `app.js` 和 `claire.html`。从零安装开发依赖可运行 `npm ci`。原始模型路径：`D:/projects/claire/models/modern-v03/claire-modern-v03.blend`；原模型的说明和回退路径仍见同目录 README。

## 验证

`checks/browser-report.json` 记录自动化实际浏览器检查，截图包括桌面、手机、三种悬停、换盘途中、三个面板及单文件离线打开。验证覆盖三实体盘、播放盘固定、连续悬停归位、换盘与最后目标优先、键盘和焦点恢复、减少动态效果、音频本地选择与暂停、触屏单次选择、资源失败降级，以及加载过程中提前选择入口。

在本地服务器运行时执行 `npm test`。当前验证使用 Windows Edge；未宣称所有浏览器或真实手机均已测试。软件渲染驱动有着色器浮点精度警告，记录在报告中，未产生页面 JavaScript 错误。

视觉检查与功能检查分别记录在 `checks/visual-review.json` 与 `checks/browser-report.json`。浏览器材质使用即时光照与光学薄膜效果，取景为网页文字留白调整；不等同 Blender Cycles 的离线光照。

实现沿用本地 [Emil Design Engineering](D:/projects/claire/skills/emil-design-eng/SKILL.md) 的即时反馈、可打断弹簧、克制过冲和输入方式差异。三维 API 依据官方 [GLTFLoader 文档](https://threejs.org/docs/pages/GLTFLoader.html) 和 [MeshPhysicalMaterial 文档](https://threejs.org/docs/pages/MeshPhysicalMaterial.html)。Three.js 许可证随附于 `THREE-LICENSE.txt`。
