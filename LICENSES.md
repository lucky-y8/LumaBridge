# 第三方许可证说明

发布前应将实际安装版本的完整许可证文本一并放入发行包。项目直接依赖如下：

| 组件 | 用途 | 许可证 |
| --- | --- | --- |
| Python | 运行时 | Python Software Foundation License 2.0 |
| PySide6 / Qt for Python | 桌面界面 | LGPL-3.0-only / GPL-2.0-only / GPL-3.0-only（本项目按 LGPL 动态链接使用） |
| Qt 6 | GUI 基础库 | LGPL-3.0-only / GPL 商业多重许可 |
| qrcode | 二维码编码 | BSD-3-Clause |
| Pillow | PNG/图像处理 | HPND |
| OpenCV / opencv-python | 视频读取 | Apache-2.0 |
| zxing-cpp | 二维码识别 | Apache-2.0 |
| PyInstaller | Windows/Linux 打包 | GPL-2.0-or-later，带发布非 GPL 应用的特殊例外 |
| pytest | 开发测试 | MIT |

LumaBridge 不静态修改或嵌入上述组件的源代码。Qt/PySide 发布需保留 LGPL 文本、版权声明，并允许用户替换相应动态库；具体发布义务应以构建时实际版本附带的许可证文件为准。

