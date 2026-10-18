# Non Player Plushie Animation Export Toolkit

[English: complete instructions](README.en.md) | [中文：完整说明](README.zh-CN.md)

Compass and controls / 指南针与操作：[English](COMPASS.en.md) | [中文](COMPASS.zh-CN.md)

Extract the entire toolkit, install Python 3.10+, and start with `templates/doll-authoring-template.bbmodel`. Run `python Export-DollAnimation.py` to choose a project. Results go to `output/`.

完整解压，安装 Python 3.10+，使用 `templates/doll-authoring-template.bbmodel` 制作动画，运行 `python Export-DollAnimation.py` 选择工程。结果位于 `output/`。

`models/doll-model-1.6.10/` contains doll-only model and texture references, not the combined animation scene. The folder's 1.6.10 label is the reference asset revision, not the required mod version.

Use the matching mod JAR supplied with this release. This toolkit ZIP is a separate authoring utility; do not install it as a Minecraft mod or animation pack.

## Download / 下载

Choose **Code → Download ZIP** on this repository, then extract the entire folder. Install Python 3.10+ and run `python Export-DollAnimation.py` to choose a project. Read the full English or Chinese guide above before editing.

点击仓库的 **Code → Download ZIP**，完整解压后安装 Python 3.10+，运行 `python Export-DollAnimation.py` 选择工程。制作前请阅读上面的中英文完整教程。

This repository contains animation authoring tools and reference assets, not the Minecraft mod. Match the toolkit version with your Non Player Plushie release. No pip dependencies are required. The file picker uses tkinter; you can pass the project path on the command line if tkinter is unavailable.

本仓库是动画制作工具与参考素材，不包含 mod。请与配套版本的 Non Player Plushie 一起使用。无需 pip 依赖；文件选择窗口使用 tkinter，不可用时可在命令行传入工程路径。

Created for Non Player Plushie by infinitycard (GitHub: informacard). Reference assets retain their original authorship. No additional redistribution license is granted here.
