# Claire 现代电子音乐空间 · Blender v02

这一版采用银灰色无边摄影棚空间：磨砂银色翻盖播放器、光滑镜面镭射光盘，以及紧密错位叠放的三个夹页。图案改为成熟、顽皮的印刷拼贴，分别以朱红姓名、钴蓝过程图、酸绿票根与单色植物表达关于我、我的作品、我的世界。

这是可继续编辑的 Blender 模型与动作预览；最终网页内容窗口、点击导航和音频播放尚未实现。

## 文件与预览

- [主模型 claire-modern-v02.blend](D:/projects/claire-vinyl-preview/modern-v02/claire-modern-v02.blend)：独立物件、材质、时间线与打包贴图。
- [最终机位／默认状态](D:/projects/claire-vinyl-preview/modern-v02/hero-idle.png)：第 135 帧，关于我光盘位于播放器中。
- [鼠标选中作品盘的状态](D:/projects/claire-vinyl-preview/modern-v02/hero-hover-projects.png)：第 163 帧，作品夹页及对应光盘向前突出。
- [闭盖俯视首帧](D:/projects/claire-vinyl-preview/modern-v02/opening-closed-top.png)：第 1 帧，播放器闭合。
- [盘面、夹页与标签资产说明](D:/projects/claire-vinyl-preview/modern-v02/assets/README.md)：包含 PNG、SVG、字体和 UV 用法。

模型生成于 Blender **5.2.2 LTS**，保存时停在第 135 帧。镜面与镭射反光由 3D 材质提供；透明印刷图案覆盖在银色盘底上，因此反光可以随视角变化。

最新模型已载入当前 Blender 桌面窗口，`Claire` 预览面板已注册。载入前的未保存场景已另存到 `session-backups`，未覆盖旧场景。

## 在 Blender 中查看与操作

1. 打开主模型。按数字小键盘 `0` 查看相机机位；可直接在时间线跳转到下方列出的关键帧。
2. 把一个区域切换为 **Text Editor／文本编辑器**，从文本数据下拉框选择模型内置的 `claire_preview_runtime.py`。
3. 点击 **Run Script／运行脚本**，或在文本编辑器按 `Alt+P`。直接运行内置文本会调用 `register()`；如果通过模块方式载入，则需显式调用该模块的 `register()`。
4. 回到 **3D Viewport／3D 视图**，按 `N` 展开侧栏，选择 **Claire** 页签。面板提供七个关键帧快捷按钮。
5. 点击 **Start Hover Preview**，鼠标滑过三个夹页的露出部分，即可预览对应卡片向前移、轻微抬高、转动与放大。备用盘跟随自己的夹页；正在播放的关于我光盘保持在盘仓中。
6. 移开鼠标，夹页平滑归位。按 `Esc` 或面板的 **Stop Hover Preview**，恢复启动预览前的帧、变换、机位和悬停状态。

悬停过渡约 **0.30 秒**，放大至 **1.03 倍**。此工具只提供 Blender 内的实时悬停体验；点击不会打开网页窗口、执行内容导航或播放声音。实时悬停与时间线演示是两种预览方式，面板切换关键帧时会先退出悬停工具。

## 时间线动作

模型使用 **30 fps**；第 1–135 帧为约 **4.5 秒**的开场。完整第 1–350 帧还包括悬停和换盘演示。

| 帧 | 画面与动作 |
| --- | --- |
| 1 | 闭合播放器，近距离俯视首帧 |
| 15–75 | 盖子围绕独立铰链缓慢打开，最终角度为 78° |
| 55–135 | 默认盘轻微旋转；镜头拉远并倾斜至最终机位 |
| 135 | 默认紧密叠放状态，关于我盘在播放器内 |
| 163–190 | 作品夹页向前突出，配套备用盘同步移动 |
| 204 | 夹页回到紧密叠放状态 |
| 220–270 | 关于我盘抬起，沿弧线路径返回自己的夹页；247 为中段标记 |
| 270–320 | 作品盘抬起并移入播放器；288 为中段标记 |
| 350 | 作品盘在盘仓中旋转，正在播放标记移至作品夹页 |

目前换盘时间线演示的是**关于我 → 我的作品**。三张盘均保留独立根节点，后续可复用同一动作机制扩展世界盘的切换。

## 模型结构与编辑

- `PLAYER_ROOT`：播放器整体位置与朝向；机身、深色底边、按钮、盘仓和轴心为可编辑部件。
- `LID_HINGE`：独立盖子铰链。盖子外壳、内壳与姓名标签跟随铰链开合，不与唱片展示组混在一起。
- `DISC_01_ABOUT`、`DISC_02_PROJECTS`、`DISC_03_WORLD`：始终只有三张导航光盘，每张拥有独立镜面环、中心孔、印刷图案及变换。
- `CARD_01_ABOUT`、`CARD_02_PROJECTS`、`CARD_03_WORLD`：三个独立夹页。紧密倾斜叠放，中文名称直接印在夹页连续延伸的顶部区域；默认盘的夹页为空，保留正在播放标记。已移除原先架空的标题牌和细支撑柱。
- `04 Studio` 与 `05 Lights and Camera`：无边背景、地面、柔光与开场至最终机位的相机。取消音乐小屋与厚墙结构。

贴图和使用的字体已打包到 `.blend`。盘面、夹页、顶部标签与盖子姓名贴纸的可编辑 SVG 源均保留在 `assets`。若修改物体位置或动画，先关闭悬停预览，避免临时预览变换影响编辑。

## 检查与后续范围

[validation-report.json](D:/projects/claire-vinyl-preview/modern-v02/validation-report.json) 的结构检查结果为 `passed: true`，包括三张盘与三个夹页、闭盖相机不裁切、盖子正确打开、悬停不移动播放盘、突出深度、夹页互不穿插、作品盘换入与贴图／运行时打包。

两个检查脚本可用独立 Blender 后台进程运行，不保存或覆盖模型：

```powershell
& 'D:\Steam\steamapps\common\Blender\blender.exe' --background 'D:\projects\claire-vinyl-preview\modern-v02\claire-modern-v02.blend' --python 'D:\projects\claire-vinyl-preview\modern-v02\tools\validate_model.py'

& 'D:\Steam\steamapps\common\Blender\blender.exe' --background 'D:\projects\claire-vinyl-preview\modern-v02\claire-modern-v02.blend' --python 'D:\projects\claire-vinyl-preview\modern-v02\tools\validate_preview_runtime.py'
```

运行时检查脚本覆盖重复注册、重开文件后的注册、场景版本保护、七个关键帧跳转、三个夹页的可选区域、移动后的稳定命中、播放盘保持原位、备用盘跟随、退出恢复与不复制对象。

后续网页需要绑定三个入口、点击确认后的换盘动作、音符展开内容窗口、关闭与切换状态，以及访客主动开启的歌单和音频。Blender 内的按钮与悬停预览是动作验证工具，不等同于网页交互已交付。
