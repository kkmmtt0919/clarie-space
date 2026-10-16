# Claire / modern-v02 print assets

此目录只包含新设计的盘面、夹页与可重复生成的矢量绘制脚本，不修改主场景或旧版资产。

## 交付

| 主题 | 盘面 RGBA 纹理 | 夹页纹理 | 设计语言 |
| --- | --- | --- | --- |
| 关于我 | `disc-about.png` | `cover-about.png` | 黑白姓名撕字、朱红星号、个人档案排版 |
| 我的作品 | `disc-projects.png` | `cover-projects.png` | 钴蓝 02、原创流程板剪片、折线箭头 |
| 我的世界 | `disc-world.png` | `cover-world.png` | 单色植物剪片、酸绿音乐票根、黑白像素符号 |

对应的六张 `.svg` 保留可编辑矢量源；`asset-review.png` 是仅供预览的六图对照。

所有 PNG 为 **1600 × 1600 / RGBA / sRGB**。盘面的大面积透明区需要由 Blender 的银色镜面材质提供底色；镭射彩虹反光不烘焙在盘面图片中。预览板上的灰色圆盘是临时示意底色，不在交付盘面纹理中。

## Blender UV 与材质

- 图片中心对应 UV `(0.5, 0.5)`。外圆半径为图片宽度的 **0.46**，中心孔半径为图片宽度的 **0.065**；外圆以外和中心孔完全透明。
- 盘面网格若有半径 `R`，顶面 UV 应取 `u = 0.5 + 0.46*x/R`、`v = 0.5 + 0.46*y/R`。图片顶部即 UV 的高 v 端。首次应用请核对文字没有镜像。
- 图像节点设置 sRGB、Alpha Mode = Straight。推荐将 image alpha 作为银底与印刷材质的混合权重。RGB 输出仅给印刷材质的 Base Color；印刷建议 Metallic = 0、Roughness = 0.32–0.45，银底建议 Metallic = 1、Roughness = 0.07–0.12。
- 如果使用透明贴花网格，贴花略高于盘面，避免 z-fighting。中心孔和盘外透明区不可被当成黑底。
- 夹页为正方形全幅打印纹理，顶端中文标题在约 10%–20% 高度范围。叠放时至少露出夹页上方 24%，以保证三个主题和序号可辨认。
- 中文标题已烘焙进 PNG；Blender 不需要中文字体也能正确显示。项目流程图是原创的示意图案，不代表 Claire 的真实项目截图或内容。

## 字体与重新生成

运行 `python build_print_assets.py` 即可重建六张纹理、六张 SVG 与预览板。依赖 Pillow（当前环境已安装），无网络下载。

字体读取自 `C:/Windows/Fonts`：Arial Regular/Bold（arial.ttf、arialbd.ttf）、Consolas（consola.ttf）、Microsoft YaHei Bold（msyhbd.ttc）。PNG 已完整烘焙字形；SVG 使用 `Arial`、`Consolas`、`Microsoft YaHei` 字体族名，换机编辑 SVG 时需要相应字体或合适替代。SVG 源由与 PNG 相同的绘制指令同步构造，PNG 的旋转文字使用 Pillow 的真实字体字形栅格化。

## 设计边界

不使用人像、小动物、卡通角色、人物剪片、真实截图或外部照片。每张盘保留一个主要构成及少量辅助符号，环绕英文说明保持可读。银色和柔和镭射属于真实 3D 材质，因此可以跟随视角和光线变化。
