# Non Player Plushie Animation Export Toolkit

[English instructions](README.en.md) · [中文说明](README.zh-CN.md)

Use this toolkit with the Non Player Plushie mod JAR released alongside it. Earlier builds with the same version number may lack the current rig support. Minecraft, Blockbench, NoN, and the mod JAR are not included in this toolkit.

## Requirements


- Install Python 3.10 or newer. No pip packages are required. On Windows, enable **Add python.exe to PATH** during installation, then reopen your terminal or folder window.
- Use a Blockbench setup that can edit this type of multi-actor animation. Keep your existing editing plugins, such as Multi Actor Animator. Exporting uses the standalone Python script, rather than Blockbench's animation export button.
- In Minecraft, install the matching Non Player Plushie release, Needs of Nature, and their required dependencies. Check the accompanying mod release page for supported game versions.
- Extract the **entire ZIP** to a writable folder before running anything. Do not run scripts inside an archive preview or copy only one script out of the toolkit.

## Included files

```text
Export-DollAnimation.py                 Python launcher
README.en.md / README.zh-CN.md           Complete English and Chinese guides
templates/
  doll-authoring-template.bbmodel        Combined player + doll animation scene
  doll-authoring-template.doll-export.json
settings.example.json                   Example export settings
models/doll-model-1.6.10/
  sensory_link_doll_wide.bbmodel         Wide-arm model reference
  sensory_link_doll_slim.bbmodel         Slim-arm model reference
  steve.png / alex.png                   Matching texture references
tools/                                  Export scripts and standalone helper modules
data/                                   Model data used to validate joints; keep this folder
toolkit.json / MANIFEST.sha256           Matching release information and file checksums
output/                                 Created automatically on your first export
```

**Open `templates/doll-authoring-template.bbmodel` to create a combined animation.** The two projects in `models/doll-model-1.6.10/` contain only the doll. They are geometry and texture references, not combined player-and-doll animation scenes. Editing these reference models does not automatically replace the in-game doll mesh. This exporter handles animations, not model replacement.

## Quick start

1. Open `templates/doll-authoring-template.bbmodel` in Blockbench and save a copy as your own project, such as `my_scene.bbmodel`.
2. Copy the settings file next to the template, or `settings.example.json`, beside your new project. Rename it to `my_scene.doll-export.json`. The project and settings must have the same base name.
3. Edit `namespace`, `animation_id`, `display_name`, and `author`. Give each animation a unique ID to prevent one project from replacing another.
4. Create timeline clips named `p1`, `p2`, `p3`, and so on. Names such as `my_scene.p1` also work. Number stages consecutively from 1, use one clip per stage, and set each clip's duration.
5. Run `python Export-DollAnimation.py` in the toolkit root and select your `.bbmodel`. If Python file associations are configured, double-clicking the launcher also works.
6. Check the toolkit's `output/` folder. It contains a linked animation JSON, a complete NoN animation-pack ZIP, and an unpacked copy of the pack. An existing ZIP with the same name is backed up before replacement. The source project is never modified.
7. Put the **generated animation-pack ZIP** in your Minecraft instance's `needsofnature/` folder, then rejoin the world or restart to reload animation packs. **Do not put this toolkit ZIP in `mods/` or `needsofnature/`.** Only the mod JAR belongs in `mods/`.
8. Hold a bound doll and check its interaction menu for the new animation. Registration does not mean every actor satisfies NoN's playback requirements. Preview the final animation and camera behavior in game.

An offline doll owner or unmet gender requirements can prevent playback. A mob must also be listed in `entity_types` and have a compatible NoN humanoid rig.

## Rig and animation rules

Edit timeline keyframes while preserving the template's hierarchy, static pivots, rest rotations, rest scales, and geometry. The template's joints match the actual doll model in the accompanying mod. An arbitrary third-party skeleton is not automatically compatible.

| Template bone | Exported track | Purpose |
| --- | --- | --- |
| Bones prefixed with `actor1_` | Prefix removed, such as `head` or `body` | Player animation |
| Separate top-level `root` | `propfloor` | Doll placement, rotation, and scale |
| `plushie` | `doll_body` | Doll body |
| `head` | `doll_head` | Doll head |
| `left_arm/right_arm/left_leg/right_leg` | Corresponding `doll_*` names | Doll limbs |

The player and doll have separate top-level roots. Do not animate `actor1_propfloor` manually; move the doll's own `root` instead. The exporter compensates for inherited player transforms to preserve the relative placement from your source scene. Root translation, rotation, and uniform scaling are supported. Nonuniform parent scaling that creates shear is rejected with an error.

Supported channels are numeric XYZ translation, Euler rotation, and scale, with linear or Bezier interpolation. Curves are baked to numeric tracks at 60 FPS by default. Translation uses model units (16 units per block), rotation uses degrees, and scale uses multipliers. Do not manually flip JSON axes or add an extra half-block/eight-unit offset. The linked file contains both player and doll tracks: NoN runs one actual actor, and the matching mod drives the doll's pose.

This exporter does not support Molang expressions, pre/post dual-value keys, step/Catmull-Rom interpolation, global rotation, quaternion interpolation, indefinite hold stages, or sound/particle timelines. Convert or bake these features first, or handle them separately. Unsupported content produces an error instead of being silently discarded.

## Export settings

Settings are read automatically from `project_name.doll-export.json` beside the project. Defaults are used if that file is absent. Settings must be valid JSON: comments are not supported, and quotes and commas must be correct.

| Field | Meaning |
| --- | --- |
| `namespace` | Lowercase namespace; defaults to `custom_doll` |
| `animation_id` | Animation name without the namespace; defaults to a name derived from the project filename |
| `display_name` / `author` / `version` | Menu label, author credit, and pack version |
| `fps` | Baking rate, 1–120; defaults to 60 |
| `entity_types` | Allowed entity IDs; defaults to `minecraft:player` only. The example also lists several undead mobs |
| `player_genders` / `doll_genders` | Exact-value lists containing `none`, `male`, `female`, and/or `both` |
| `priority` | Menu sorting priority; larger values appear first |
| `stage_seconds` | Duration of looping stages, such as `{"1":6,"2":6,"3":4}`. Unspecified looping stages default to six seconds |
| `tracking` | Overrides for this mod's effects and defeat behavior; see below |

Set each clip's loop mode to `loop` or `once`. Non-looping stages play for their clip duration. The last stage is marked as the settlement stage, and mob sessions wait for the entire animation to finish.

```json
"tracking": {
  "enabled": true,
  "liquid_ml": 15,
  "mess_amount": 1,
  "skip_defeat": false,
  "defeat_animation": "needsofnature:player_defeated-back"
}
```

Omit these fields to use global configuration. `enabled:false` disables this mod's sensation, slowness, and defeat effects for the animation while keeping the visual animation available. `skip_defeat:true` skips only the defeat animation. `defeat_animation` must refer to a valid installed animation ID.

The secondary camera follows the doll's actual head transform. Its direction uses the game's main `projection_face_mode` setting: `doll_normal` looks along the doll's face normal, and `look_at_face` looks toward the initiating actor's face. Animation packs do not override this user choice.

Advanced fields `player_prefix`, `doll_root`, and `doll_bones` change name mappings only; they do not retarget arbitrary joint layouts. Keep `rig_profile:"runtime"` for new work. `legacy_example` supports only a specific early example project; it is not a general-purpose mode or a way to bypass rig validation.

## Command line

From the extracted toolkit folder:

```text
python Export-DollAnimation.py "C:\My Animations\my_scene.bbmodel"
```

Optional arguments are `--settings "settings.json"` and `--output "output_folder"`. You can also use Python directly:

```text
python tools/export_doll_pack.py "my_scene.bbmodel" --settings "my_scene.doll-export.json" --output "output"
```

Replace `python` with `python3` where that is your Python command. The file picker uses Python tkinter; if unavailable, pass the project path on the command line. Keep the toolkit in a writable location; the Python exporter uses only the standard library.

## Troubleshooting

- **Python is missing or Microsoft Store opens:** install Python 3.10+, enable PATH, and verify that `python --version` or `py -3 --version` runs in a terminal. Then reopen the launcher.
- **Missing `actor1_root` or a pivot mismatch:** use the combined authoring template, not a doll-only reference model. Preserve the static pivots and hierarchy.
- **Unsupported expression or interpolation:** bake it to numeric linear or Bezier keys in your authoring tool first.
- **NoN reports an unknown `non_player_plushie` field:** the matching mod reads this extension; NoN's warning about the field is expected.
- **A new project replaces an older animation:** change the namespace or animation ID in the settings, rather than only renaming the project file.
- **You want to replace the doll mesh or proportions:** reference models are included, but model replacement is outside this animation export pipeline.

The templates and models have embedded textures; reference PNG files are also included separately. Preserve the relative locations of `tools/` and `data/` so the toolkit can run independently.
