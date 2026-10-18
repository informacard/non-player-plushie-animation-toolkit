"""Export one Blockbench scene to a linked player+doll animation and a NoN pack."""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import shutil
import sys
import time
import zipfile

import doll_animation_codec as codec
from doll_export_math import compose, decompose, inverse, multiply

PROJECT = Path(__file__).resolve().parents[1]
PORTABLE = (PROJECT / "data/wide.json").is_file()
DEFAULT_MAP = {"body": "plushie", "head": "head", "left_arm": "left_arm",
               "right_arm": "right_arm", "left_leg": "left_leg", "right_leg": "right_leg"}
CHANNELS = {"rotation": [0, 0, 0], "position": [0, 0, 0], "scale": [1, 1, 1]}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def rig_pivots():
    model = read(PROJECT / ("data/wide.json" if PORTABLE else "resources/assets/non_player_plushie/doll/wide.json"))
    pivots = {"root": [0, 0, 0], "body": [0, 0, 0]}
    for part in model["parts"]:
        name = part["name"]
        if name not in DEFAULT_MAP or name == "body":
            continue
        points = [v[:3] for f in part["faces"] for v in f]
        lo = [min(p[i] for p in points) for i in range(3)]
        hi = [max(p[i] for p in points) for i in range(3)]
        pivot = part.get("rig_pivot", [(lo[0]+hi[0])/2, hi[1] if name == "head" else lo[1], (lo[2]+hi[2])/2])
        pivots[name] = [-pivot[0], -pivot[1], pivot[2]]
    return pivots


def prepare(project, settings):
    groups = {g["uuid"]: g for g in project["groups"]}
    by_name = {}
    for g in groups.values():
        if g["name"] in by_name:
            raise ValueError(f"Duplicate bone name: {g['name']}")
        by_name[g["name"]] = g
    parents = {}

    def walk(nodes, parent=None):
        for node in nodes:
            if isinstance(node, dict):
                uid = node["uuid"]
                parents[uid] = parent
                walk(node.get("children", []), uid)
    walk(project["outliner"])
    prefix = settings.get("player_prefix", "actor1_")
    mapping = dict(DEFAULT_MAP)
    mapping.update(settings.get("doll_bones", {}))
    root = settings.get("doll_root", "root")
    for name in [root, prefix+"root", prefix+"player", *mapping.values()]:
        if name not in by_name:
            raise ValueError(f"Missing bone {name!r}; use the supplied authoring template or set the bone mapping")
    if len(set(mapping.values())) != len(mapping) or root in mapping.values():
        raise ValueError("Doll roles must map to distinct bones; placement root is separate")
    if parents.get(by_name[root]["uuid"]) is not None:
        raise ValueError("The doll placement root must be a separate top-level actor")
    for name in (root, prefix+"root", prefix+"player"):
        g = by_name[name]
        if any(g.get("origin", [0, 0, 0])) or any(g.get("rotation", [0, 0, 0])):
            raise ValueError(f"{name}: placement bones need origin [0,0,0] and zero rest rotation")
        if g.get("scale") not in (None, [1, 1, 1]):
            raise ValueError(f"{name}: rest scale must be one; put scaling on timeline keys")
    if parents.get(by_name[prefix+"root"]["uuid"]) is not None:
        raise ValueError("The player root must be a top-level actor")
    if parents.get(by_name[prefix+"player"]["uuid"]) != by_name[prefix+"root"]["uuid"]:
        raise ValueError("Player hierarchy must be actor_root -> actor_player -> propfloor")
    profile = settings.get("rig_profile", "runtime")
    if profile == "runtime":
        pivots = rig_pivots()
        for role, name in mapping.items():
            g = by_name[name]
            expected_parent = root if role == "body" else mapping["body"]
            if parents.get(g["uuid"]) != by_name[expected_parent]["uuid"]:
                raise ValueError(f"{name}: expected parent {expected_parent}; use the supplied authoring template")
            if any(g.get("rotation", [0, 0, 0])):
                raise ValueError(f"{name}: rest rotation must be zero; animate on the timeline instead")
            if g.get("scale") not in (None, [1, 1, 1]):
                raise ValueError(f"{name}: rest scale must be one")
            if max(abs(a-b) for a, b in zip(g.get("origin", [0, 0, 0]), pivots[role])) > 1e-4:
                raise ValueError(f"{name}: pivot must be {pivots[role]} for the installed doll mesh")
    elif profile != "legacy_example":
        raise ValueError("rig_profile must be runtime or legacy_example")
    return groups, by_name, prefix, mapping, root


def numeric_tracks(animation):
    for animator in animation.get("animators", {}).values():
        if animator.get("rotation_global") or animator.get("quaternion_interpolation"):
            raise ValueError(f"{animator.get('name')}: global/quaternion authoring is unsupported; bake to local Euler keys first")
        for key in animator.get("keyframes", []):
            if key.get("channel") not in CHANNELS:
                raise ValueError(f"Unsupported channel {key.get('channel')}: export bone transforms only")
            if key.get("interpolation", "linear") not in ("linear", "bezier"):
                raise ValueError("Only linear and Bezier authoring is supported; bake step/Catmull-Rom keys first")
            points = key.get("data_points", [])
            if len(points) != 1 or any(codec.number(points[0].get(axis)) is None for axis in "xyz"):
                raise ValueError(f"{animator.get('name')}: expressions or pre/post keyframes must be baked to numeric XYZ")
            if any(not math.isfinite(float(points[0][axis])) for axis in "xyz"):
                raise ValueError("Non-finite keyframe component")
    tracks = codec.channel_keyframes(animation)
    for channels in tracks.values():
        for frames in channels.values():
            times = [codec.trim(f["time"]) for f in frames]
            if len(set(times)) != len(times):
                raise ValueError("Duplicate or sub-0.0001-second keys on one channel must be merged first")
    return tracks


def sample(frames, t, neutral):
    if not frames:
        return list(neutral)
    if t <= frames[0]["time"]:
        return frames[0]["value"]
    for a, b in zip(frames, frames[1:]):
        if t <= b["time"]:
            if a["interpolation"] == "bezier" or b["interpolation"] == "bezier":
                return [codec.bezier_value(codec.bezier_axis(a, b, axis, ""), t) for axis in range(3)]
            alpha = (t-a["time"])/(b["time"]-a["time"])
            return [x+(y-x)*alpha for x, y in zip(a["value"], b["value"])]
    return frames[-1]["value"]


def transform(channels, t):
    return compose(*(sample(channels.get(c, []), t, CHANNELS[c]) for c in ("position", "rotation", "scale")))


def bake_channel(channel, frames, times):
    values = {codec.trim(t): [codec.clean(v) for v in sample(frames, t, CHANNELS[channel])] for t in times}
    return next(iter(values.values())) if len({tuple(v) for v in values.values()}) == 1 else values


def compile_project(project, settings):
    groups, names, prefix, mapping, root = prepare(project, settings)
    fps = int(settings.get("fps", 60))
    if not 1 <= fps <= 120:
        raise ValueError("fps must be between 1 and 120")
    stages = {}
    for animation in project.get("animations", []):
        match = re.search(r"(?:^|[.])p([1-9][0-9]*)$", animation["name"])
        if not match:
            raise ValueError(f"Animation {animation['name']!r} must end in p1, p2, ...")
        number = int(match[1])
        if number in stages:
            raise ValueError(f"Duplicate stage p{number}")
        stages[number] = animation
    if not stages or sorted(stages) != list(range(1, len(stages)+1)):
        raise ValueError("Stages must be contiguous starting at p1")
    result = {}
    definitions = []
    source_roles = {names[n]["uuid"]: role for role, n in mapping.items()}
    source_root = names[root]["uuid"]
    for number, animation in sorted(stages.items()):
        length = float(animation["length"])
        if animation.get("loop", "once") not in ("loop", "once"):
            raise ValueError("Use loop or once stages; indefinite hold stages are not exported")
        if not math.isfinite(length) or not .001 <= length <= 3600:
            raise ValueError("Stage length must be between .001 and 3600 seconds")
        tracks = numeric_tracks(animation)
        times = sorted({0.0, length} | {round(i/fps, 6) for i in range(int(length*fps)+1) if i/fps < length}
                       | {f["time"] for channels in tracks.values() for frames in channels.values() for f in frames})
        if any(t < 0 or t > length for t in times):
            raise ValueError(f"p{number}: keyframe lies outside the stage duration")
        if len(times)*max(1, len(tracks)) > 2_000_000:
            raise ValueError("This stage is too large to bake; reduce FPS or split it into shorter stages")
        bones = {}
        for uid, channels in tracks.items():
            name = groups.get(uid, {}).get("name", "")
            if not channels:
                continue
            if name.startswith(prefix):
                target = name[len(prefix):]
                if target == "propfloor":
                    raise ValueError("Animate the separate doll root, not actor_propfloor")
                payload = {}
                for channel, frames in channels.items():
                    raw = bake_channel(channel, frames, times)
                    payload[channel] = ({t: codec.convert(channel, v) for t, v in raw.items()}
                                        if isinstance(raw, dict) else codec.convert(channel, raw))
                bones[target] = payload
            elif uid in source_roles:
                bones["doll_"+source_roles[uid]] = {c: bake_channel(c, fs, times) for c, fs in channels.items()}
            elif uid != source_root:
                raise ValueError(f"Animated bone {name!r} is not mapped; no channels were silently discarded")
        if settings.get("rig_profile") == "legacy_example":
            head = tracks.get(names[mapping["head"]]["uuid"], {})
            if head:
                raise ValueError("Legacy example profile cannot animate its head wrapper; use the runtime template")
        # Keep the rig path active even for a static doll, avoiding the item mount's -.5 Y shift.
        bones.setdefault("doll_body", {"rotation": [0, 0, 0]})
        mount = {c: {} for c in CHANNELS}
        previous_rotation = None
        for t in times:
            parent = multiply(transform(tracks.get(names[prefix+"root"]["uuid"], {}), t),
                              transform(tracks.get(names[prefix+"player"]["uuid"], {}), t))
            pos, rot, scale = decompose(multiply(inverse(parent), transform(tracks.get(source_root, {}), t)))
            if previous_rotation is not None:
                rot = [a+((b-a+180) % 360-180) for a, b in zip(previous_rotation, rot)]
            previous_rotation = rot
            for channel, vector in (("position", pos), ("rotation", rot), ("scale", scale)):
                mount[channel][codec.trim(t)] = [codec.clean(v) for v in codec.convert(channel, vector)]
        bones["propfloor"] = {c: next(iter(v.values())) if len({tuple(a) for a in v.values()}) == 1 else v for c, v in mount.items()}
        loop = animation.get("loop") == "loop"
        clip = {"animation_length": length, "bones": bones}
        if loop:
            clip["loop"] = True
        result[f"p{number}_player"] = clip
        stage = {"stage": number, "loop": loop, "cycle_seconds": length,
                 "allow_join": False, "escapable": number != len(stages)}
        if loop:
            stage["stage_seconds"] = float(settings.get("stage_seconds", {}).get(str(number), 6))
            if stage["stage_seconds"] <= 0:
                raise ValueError("Loop stage_seconds must be positive for automatic completion")
        if number == len(stages):
            stage["non_peak"] = True
        definitions.append(stage)
    return {"format_version": "1.8.0", "animations": result}, definitions


def export(source, output, settings):
    if not isinstance(settings, dict):
        raise ValueError("Export settings must be a JSON object")
    if not isinstance(settings.get("stage_seconds", {}), dict):
        raise ValueError("stage_seconds must be an object keyed by stage number")
    tracking = settings.get("tracking", {"enabled": True})
    if not isinstance(tracking, dict):
        raise ValueError("tracking must be an object")
    for key in ("enabled", "skip_defeat"):
        if key in tracking and not isinstance(tracking[key], bool):
            raise ValueError(f"tracking.{key} must be true or false")
    for key in ("liquid_ml", "mess_amount"):
        if key in tracking and (type(tracking[key]) is not int or not 0 <= tracking[key] <= 1000):
            raise ValueError(f"tracking.{key} must be an integer from 0 to 1000")
    if tracking.get("defeat_animation") and not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", tracking["defeat_animation"]):
        raise ValueError("tracking.defeat_animation must be a namespaced animation ID")
    namespace = settings.get("namespace", "custom_doll")
    default_id = re.sub(r"[^a-z0-9_.-]+", "_", Path(source).stem.lower()).strip("_") or "my_doll_animation"
    name = settings.get("animation_id", default_id)
    if not re.fullmatch(r"[a-z0-9_.-]+", namespace) or namespace in (".", "..") or not re.fullmatch(r"[a-z0-9_./-]+", name) or ".." in name or name.startswith("/"):
        raise ValueError("Use a lowercase namespace and animation_id (no traversal or absolute paths)")
    document, stages = compile_project(read(source), settings)
    title = settings.get("display_name", Path(source).stem)
    author = settings.get("author", "Custom animator")
    if not isinstance(title, str) or not title.strip() or not isinstance(author, str) or not author.strip():
        raise ValueError("display_name and author must be nonempty strings")
    genders = settings.get("player_genders", ["none", "male", "female", "both"])
    doll_genders = settings.get("doll_genders", ["none", "male", "female", "both"])
    for values in (genders, doll_genders):
        if not values or not set(values) <= {"none", "male", "female", "both"}:
            raise ValueError("Gender lists may contain none, male, female and both")
    actor_types = settings.get("entity_types", ["minecraft:player"])
    if not actor_types or any(not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", v) for v in actor_types):
        raise ValueError("entity_types must contain valid namespaced entity IDs")
    definition = {"display_name": title, "animators": [author], "attack_eligible": False,
                  "actors": [{"label": "player", "entity_types": actor_types, "held_item": {
                      "items": ["non_player_plushie:sensory_link_doll"], "hand": "either", "prop_slot": "floor"}}],
                  "speed": 1.0, "escapable": True, "stages": stages,
                  "non_player_plushie": {"doll_interaction": {"name": title, "author": author,
                      "player_genders": genders, "doll_genders": doll_genders, "priority": settings.get("priority", 0)},
                      "tracking": settings.get("tracking", {"enabled": True})}}
    slug = namespace+"_"+name.replace("/", "_")
    folder = Path(output).resolve() / slug
    meta = {"pack": {"pack_format": 64, "supported_formats": [64, 100], "min_format": 64,
                     "max_format": 100, "description": title}, "animationframework": {
                         "id": namespace+":"+name+"_pack", "default_model_revision": 1,
                         "name": title, "author": author, "version": settings.get("version", "1.0.0")}}
    files = {"pack.mcmeta": meta, f"data/{namespace}/afw_animdefs/{name}.json": definition,
             f"assets/{namespace}/geckolib/animations/afw/{name}.animation.json": document}
    for relative, data in files.items():
        write(folder / relative, data)
    flat = Path(output).resolve() / (slug+".animation.json")
    write(flat, document)
    archive = Path(output).resolve() / (slug+".zip")
    if archive.exists():
        shutil.copy2(archive, archive.with_suffix(f".backup-{time.time_ns()}.zip"))
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for relative in files:
            z.write(folder / relative, relative)
    print(f"Animation ID: {namespace}:{name}\nStages: {len(stages)}\nLinked animation: {flat}\nNoN pack: {archive}")
    return archive, document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--output", type=Path, default=PROJECT / ("output" if PORTABLE else "exports/custom-packs"))
    args = parser.parse_args()
    sidecar = args.model.with_suffix(".doll-export.json")
    try:
        settings = read(args.settings or sidecar) if args.settings or sidecar.exists() else {}
        export(args.model, args.output, settings)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Export failed: {error}\n")


if __name__ == "__main__":
    main()
