"""Portable numeric Blockbench/Bedrock helpers; no game paths or third-party packages."""

def number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def convert(channel, vec):
    if channel == "rotation":
        return [-vec[0], -vec[1], vec[2]]
    if channel == "position":
        return [-vec[0], vec[1], vec[2]]
    return [vec[0], vec[1], vec[2]]


def trim(value):
    rounded = round(value, 4)
    if abs(rounded - round(rounded)) < 1e-9:
        return f"{rounded:.1f}"
    text = f"{rounded:.4f}".rstrip("0").rstrip(".")
    return text if "." in text else text + ".0"


def clean(value):
    """Round a component and drop negative zero so the file matches Blockbench output."""
    rounded = round(float(value), 5)
    return 0.0 if rounded == 0.0 else rounded


def bezier_axis(kf_a, kf_b, axis, channel):
    """Cubic bezier control points (time, value) for one axis of one segment."""
    p0 = (kf_a["time"], kf_a["value"][axis])
    p3 = (kf_b["time"], kf_b["value"][axis])
    right_time = kf_a.get("bezier_right_time") or [0.1, 0.1, 0.1]
    right_value = kf_a.get("bezier_right_value") or [0, 0, 0]
    left_time = kf_b.get("bezier_left_time") or [-0.1, -0.1, -0.1]
    left_value = kf_b.get("bezier_left_value") or [0, 0, 0]
    p1 = (p0[0] + float(right_time[axis]), p0[1] + float(right_value[axis]))
    p2 = (p3[0] + float(left_time[axis]), p3[1] + float(left_value[axis]))
    return p0, p1, p2, p3


def bezier_value(points, time):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = points

    def sample(s):
        inv = 1.0 - s
        x = inv ** 3 * x0 + 3 * inv ** 2 * s * x1 + 3 * inv * s ** 2 * x2 + s ** 3 * x3
        y = inv ** 3 * y0 + 3 * inv ** 2 * s * y1 + 3 * inv * s ** 2 * y2 + s ** 3 * y3
        return x, y

    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if sample(mid)[0] < time:
            lo = mid
        else:
            hi = mid
    return sample((lo + hi) / 2.0)[1]


def channel_keyframes(animation):
    """uuid -> channel -> list of keyframe dicts in animation order."""
    result = {}
    for uuid, animator in (animation.get("animators") or {}).items():
        channels = {}
        for kf in animator.get("keyframes") or []:
            data = (kf.get("data_points") or [{}])[0]
            values = [number(data.get("x")), number(data.get("y")), number(data.get("z"))]
            if any(value is None for value in values):
                # Molang expressions cannot be baked without a Molang evaluator.
                continue
            channels.setdefault(kf["channel"], []).append({
                "time": float(kf["time"]),
                "value": values,
                "interpolation": kf.get("interpolation", "linear"),
                "bezier_left_time": kf.get("bezier_left_time"),
                "bezier_right_time": kf.get("bezier_right_time"),
                "bezier_left_value": kf.get("bezier_left_value"),
                "bezier_right_value": kf.get("bezier_right_value"),
            })
        for frames in channels.values():
            frames.sort(key=lambda item: item["time"])
        result[uuid] = channels
    return result
