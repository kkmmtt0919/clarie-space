# Claire 现代电子音乐空间 · Blender V3

2026-10-05，按已确认设计实施。原 V2 保持不变；V3 模型、贴图、生成脚本和运行时独立保存。Blender 5.2.2 LTS，默认第 135 帧，贴图已打包。

## 打开与回退

- V3：D:/projects/claire/models/modern-v03/claire-modern-v03.blend
- 原 V2：D:/projects/claire/models/modern-v02/claire-modern-v02.blend
- 校验过的存档：D:/projects/claire/models/archives/modern-v02-20261005-170425/modern-v02/claire-modern-v02.blend
- 未保存会话备份：D:/projects/claire/models/archives/live-v02-session-20261005T090824Z.blend

存档含 61 个文件、20,543,983 字节；逐文件 SHA-256 清单在存档父目录 manifest-sha256.json。已重新打开存档模型检查贴图；原 V2 与清单一致。回退时直接打开 V2。

## 动效与文字

入场为第 1–127 帧，30 fps，约 4.2 秒：闭盖俯视、轻启盖、展开露盘、连续拉远倾斜、稳定收尾。镜头没有回弹，第 135 帧为静止主画面。

三个夹页共用保留位置与速度的解析弹簧：质量 1、刚度 500、进入阻尼 30、离开阻尼 40。进入一次轻微过冲，进度峰值约 1.058；最终缩放 1.03，峰值约 1.0317。快速换目标不会重置速度，离开更快收稳。调试后采用绕右侧遮挡边旋转 4°、抬高 0.16 的翻页动作，避免穿过相邻夹页。备用盘随夹页运动，播放盘在悬停中固定；备用盘局部 y 间距调整为 -0.45。

换盘保留完整移出、运送、入仓与旋转；经过前方上层通道避开夹页，镜头轻微拉远容纳完整盘面，再回主机位。实时悬停与时间线使用同一弹簧算法。

印刷层采用短注：一些关于 Claire 的线索 / 做过的，也在继续试 / 音乐、手作，还有日常。盘面弧形文字简化为 ABOUT CLAIRE / MADE & MAKING / OFF DUTY，减少重复微文案。银色与镭射反光由三维材质产生。

网页窗口、触屏、导航和音频行为留待网页实现；这里只实现模型与动作。

## 操作与时间线

1. 打开 V3，数字小键盘 0 查看相机。
2. Text Editor 选择内置 claire_preview_runtime.py，Alt+P 注册面板。
3. 回到 3D Viewport，N 展开侧栏，选择 Claire。
4. Play Opening / 4.2s 播放开场，Skip to Hero 跳到主画面。
5. Start Hover Preview 后滑过三个露出的夹页或备用盘区域。移开归位；Esc 或 Stop Hover Preview 恢复启动前的帧、变换和视图。
6. 面板关键帧按钮切换时间线演示，切换前会退出实时悬停。

| 帧 | 状态 |
| --- | --- |
| 1 | 闭盖俯视 |
| 127 / 135 | 收稳 / 静止主画面 |
| 163 / 223 / 283 | 关于我 / 作品 / 世界悬停 |
| 374 | 归位 |
| 417 / 458 | 换盘途中 |
| 490 / 520 | 作品入仓 / 旋转收尾 |

场景标识 modern-v03，注册键 claire_modern_v03_preview_runtime，操作器前缀 claire_v3，避免 V2 混用。不要在模态预览运行时通过 Python Console 替换整个文件；先退出，再正常打开。调试中这种替换触发过 Blender 崩溃，已用新进程启动恢复验证；模型与存档未受影响。

## 预览与验证

- previews/opening-v3.mp4：完整入场，800×450，15 fps。
- previews/hover-v3.mp4：三入口悬停与归位。
- 同目录 GIF、PNG 序列与接触表可逐帧查看；keys 包含换盘关键帧。
- validation-report.json / runtime-validation-report.json：结构、三个入口、快速切换、速度保留、30/60/144 fps 一致性及状态恢复。
- motion-validation-report.json：入场逐帧构图、收稳、播放盘固定、备用盘跟随、换盘顺序与盘面镜头边界。
- clearance-report.json：悬停夹页包围盒分离。
- surface-validation-report.json：第 135–520 帧盘体与翻盖、其他盘体、其他夹页的三角网格相交检查；排除自身夹页的设计接触，范围不等同所有物件全表面检查。
- archive-verification-report.json / archived-model-open-report.json：原 V2 与存档哈希、存档打开验证。
- video-validation-report.json：预览编码帧数。
- visual-review-report.json：实际 Blender 操作与渲染视觉检查，独立于结构检查。

视觉核对覆盖入场接触表、三个悬停、归位及换盘关键帧，检查构图、标题可读性和回弹节奏。

## 重建

背景模式运行 build_modern_scene.py，读取原 V2，通过 tools/upgrade_motion.py 写出独立 V3。印刷源文件 assets/build_print_assets.py；预览工具 render_motion_preview.py、assemble_previews.py、encode_video.py。历史继承文件、修正前预览分别在 inherited-v02、pre-repair-previews，不作为最终交付。
