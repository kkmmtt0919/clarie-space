# Claire · 我的世界软木拼贴板

独立 Blender 模型：`claire-world-board-v01.blend`。

木框、程序化软木与木纹材质、四张用户原照片、白色相纸、中文标签、五枚红色图钉均可编辑。照片与字体已打包。相机、灯光和渲染配置保存在模型中。

`board-with-photos.png` 是完整模型渲染。网页使用 Blender 渲染的空板面 `assets/world-cork-board.jpg` 与透明图钉 `assets/world-pushpin.png`，叠加可访问的原照片按钮；这保留既有照片展开、收回、悬停和放大交互。网页采用渲染图层，并非新增实时三维场景。

重建：在项目根目录使用 Blender 后台运行 `tools/build_world_board.py`，随后 `npm run build`。主播放器模型、历史模型和原验证证据不受影响。

