# Non Player Plushie 动画导出工具包

[English instructions](README.en.md) · [中文说明](README.zh-CN.md)

请将本工具包与作者同时发布的 Non Player Plushie mod jar 配套使用。早期同版本号的构建可能不包含当前骨架支持。本工具包不包含 Minecraft、Blockbench、NoN 或 mod jar。

## 准备


- 安装 Python 3.10 或更新版本，无需安装任何 pip 依赖。Windows 安装时勾选 **Add python.exe to PATH**，安装后重新打开文件夹/终端。
- 使用能编辑此类多演员动画的 Blockbench 环境，保留原有 Multi Actor Animator 等编辑插件。导出本身由独立 Python 脚本完成，无需使用 Blockbench 的动画导出按钮。
- 游戏中安装配套 Non Player Plushie、Needs of Nature 及它们所需的依赖。支持的游戏版本以配套 mod 发布页为准。
- 先将整个 zip 解压到可写文件夹。不要在压缩包预览中直接运行，也不要只复制一个脚本。

## 包内文件

```text
Export-DollAnimation.py                 Python 入口
README.en.md / README.zh-CN.md           中英文完整说明
templates/
  doll-authoring-template.bbmodel        玩家＋娃娃联动动画模板
  doll-authoring-template.doll-export.json
settings.example.json                   导出参数示例
models/doll-model-1.6.10/
  sensory_link_doll_wide.bbmodel         宽手臂模型参考
  sensory_link_doll_slim.bbmodel         细手臂模型参考
  steve.png / alex.png                   对应贴图参考
tools/                                  导出脚本及独立辅助模块
data/                                   校验关节所需的模型数据，请保留
toolkit.json / MANIFEST.sha256           配套版本与文件校验信息
output/                                 第一次导出时自动创建
```

**制作联动动画请打开 `templates/doll-authoring-template.bbmodel`。** `models/doll-model-1.6.10/` 中的两个文件只有娃娃模型，用于查看模型和贴图，不是含玩家的联动工程。修改参考模型不会自动更换游戏中的娃娃几何；该导出器负责动画，不负责替换模型。

## 第一次使用

1. 在 Blockbench 打开 `templates/doll-authoring-template.bbmodel`，另存为自己的工程，例如 `my_scene.bbmodel`。
2. 将模板旁的参数文件或 `settings.example.json` 复制到工程旁，改名为 `my_scene.doll-export.json`。两个文件必须同名，仅扩展名不同。
3. 编辑参数中的 `namespace`、`animation_id`、`display_name`、`author`。不同作品使用不同动画 ID，避免互相覆盖。
4. 在时间轴制作 `p1`、`p2`、`p3`……。也可以使用 `my_scene.p1` 这样的名称。必须从 1 连续编号，每个阶段一个片段，并设置正确时长。
5. 在工具包根目录运行 `python Export-DollAnimation.py`，选择 `.bbmodel`。若已配置 Python 文件关联，也可双击该入口。
6. 查看工具包根目录的 `output/`，其中包含联动动画 JSON、完整 NoN 动画包 zip 和展开目录。已有同名 zip 会先备份再覆盖。源工程不会被修改。
7. 将生成的**动画包 zip** 放入 Minecraft 实例的 `needsofnature/` 文件夹，然后重新进入世界或重启以重新加载动画包。**不要把这个工具包 zip 放到 `mods/` 或 `needsofnature/`。** mod jar 才放到 `mods/`。
8. 手持已绑定的娃娃，从娃娃互动菜单确认新动画。包已注册不代表每种角色都满足 NoN 的播放条件；最后请在游戏内预览动作与摄像头效果。

主人离线或性别条件不满足时，菜单可能不允许播放。怪物还需要在 `entity_types` 中声明，并能使用合适的 NoN 类人骨架。

## 骨架与动画规则

只改动画关键帧，保留模板的层级、静态轴心、静态旋转、静态缩放和几何。模板里的关节与配套 mod 的实际娃娃模型一致；直接换成任意第三方骨架不能保证兼容。

| 模板骨骼 | 导出轨道 | 用途 |
| --- | --- | --- |
| `actor1_` 前缀的骨骼 | 去掉前缀，例如 `head`、`body` | 玩家动画 |
| 独立顶层 `root` | `propfloor` | 娃娃整体位置、旋转、缩放 |
| `plushie` | `doll_body` | 娃娃身体 |
| `head` | `doll_head` | 娃娃头部 |
| `left_arm/right_arm/left_leg/right_leg` | 对应 `doll_*` | 娃娃四肢 |

玩家和娃娃分别放在两个顶层根节点下。不要手动动画化 `actor1_propfloor`；请移动娃娃自己的 `root`。导出器会抵消玩家父节点的变换，保留两者在源场景中的相对位置。支持根节点平移、旋转及均匀缩放；会产生剪切的非均匀父缩放组合会报错。

支持数值 XYZ 位移、欧拉旋转、缩放，以及线性和 Bezier 曲线。曲线默认以 60 FPS 烘焙为数值轨道；位移单位是 1/16 格，旋转单位是度，缩放是倍率。不要手动翻转 JSON 轴符号，也不要额外补半格或 8 单位的偏移。联动文件同时含玩家和娃娃轨道，NoN 使用一个实际 actor，配套 mod 驱动娃娃姿态。

Molang 表达式、pre/post 双值帧、step/Catmull-Rom、全局旋转、四元数插值、无限 hold 阶段及音效/粒子时间轴不受此导出器支持；必须先转换/烘焙或另行处理。这些内容会触发错误，不会被悄悄删掉。

## 参数说明

参数通过工程旁的 `工程名.doll-export.json` 自动读取；没有参数文件时使用默认值。JSON 不支持注释，逗号和双引号必须正确。

| 字段 | 说明 |
| --- | --- |
| `namespace` | 小写命名空间，默认 `custom_doll` |
| `animation_id` | 不含命名空间的动画名，默认由工程文件名生成 |
| `display_name` / `author` / `version` | 菜单显示名、署名、包版本 |
| `fps` | 烘焙帧率，1–120，默认 60 |
| `entity_types` | 允许的实体 ID，默认只有 `minecraft:player`；示例额外包含部分亡灵 |
| `player_genders` / `doll_genders` | 精确枚举列表：`none`、`male`、`female`、`both` |
| `priority` | 菜单排序优先级，越大越靠前 |
| `stage_seconds` | 循环阶段停留时长，例如 `{"1":6,"2":6,"3":4}`；省略的循环阶段默认 6 秒 |
| `tracking` | 本 mod 的效果及战败覆盖，见下例 |

片段的循环属性设置为 `loop` 或 `once`。非循环阶段按片段长度播放，最后阶段自动标为结算阶段，怪物会话会等待整段动画结束。

```json
"tracking": {
  "enabled": true,
  "liquid_ml": 15,
  "mess_amount": 1,
  "skip_defeat": false,
  "defeat_animation": "needsofnature:player_defeated-back"
}
```

这些字段可省略以使用全局配置。`enabled:false` 禁用本 mod 对该动画施加的感觉、减速和战败效果，仍保留视觉动画；`skip_defeat:true` 仅跳过战败。`defeat_animation` 必须是已安装的有效动画 ID。

摄像头始终使用娃娃实际头部变换；方向由游戏主配置 `projection_face_mode` 控制：`doll_normal` 沿脸部法向，`look_at_face` 朝向动作发起者的脸。动画包不能覆盖这个用户选择。

高级字段 `player_prefix`、`doll_root`、`doll_bones` 只改变名称映射，不会自动修复任意骨架的关节。新作品保持 `rig_profile:"runtime"`。`legacy_example` 仅兼容早期特定示例，不是通用模式；不能用于随意跳过骨架校验。

## 命令行

在解压后的工具包目录执行：

```text
python Export-DollAnimation.py "C:\My Animations\my_scene.bbmodel"
```

可选 `--settings "参数.json"`、`--output "输出目录"`。Python 命令行也可用：

```text
python tools/export_doll_pack.py "my_scene.bbmodel" --settings "my_scene.doll-export.json" --output "output"
```

使用 `python3` 命令的环境可将上面的 `python` 替换为 `python3`；文件选择窗口使用 Python tkinter；若不可用，请通过命令行传入工程路径。工具包应放在可写目录，Python 仅使用标准库。

## 常见问题

- **找不到 Python / 打开 Microsoft Store：** 安装 Python 3.10+ 并启用 PATH，确认终端中 `python --version` 或 `py -3 --version` 能运行，再重新打开导出入口。
- **缺少 `actor1_root` 或骨骼轴心不匹配：** 请使用联动模板，不要选择只有娃娃的参考模型，不要改静态轴心或层级。
- **不支持表达式/插值：** 先在制作工具中烘焙为数值线性或 Bezier 关键帧。
- **NoN 提示不认识 `non_player_plushie`：** 该扩展字段由配套 mod 读取；NoN 自身的这条警告是预期行为。
- **新作品覆盖旧作品：** 修改参数中的命名空间和动画 ID，而不只是改文件名。
- **想替换娃娃网格/比例：** 本工具包提供参考模型，但动画导出不包含模型替换管线。

模板和模型使用嵌入贴图；参考 PNG 也单独提供。请保留 `tools/` 和 `data/` 的相对位置，以免破坏独立运行能力。
