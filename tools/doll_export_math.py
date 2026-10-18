"""Small affine math helpers; authoring and Gecko both compose Euler as Rz*Ry*Rx."""
import math


def multiply(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def compose(position, rotation, scale):
    x, y, z = map(math.radians, rotation)
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    r = [[cz*cy, cz*sy*sx-sz*cx, cz*sy*cx+sz*sx],
         [sz*cy, sz*sy*sx+cz*cx, sz*sy*cx-cz*sx], [-sy, cy*sx, cy*cx]]
    return [[r[i][j]*scale[j] for j in range(3)]+[position[i]] for i in range(3)]+[[0, 0, 0, 1]]


def inverse(a):
    r = [row[:3] for row in a[:3]]
    det = sum(r[0][i]*(r[1][(i+1)%3]*r[2][(i+2)%3]-r[1][(i+2)%3]*r[2][(i+1)%3]) for i in range(3))
    if abs(det) < 1e-10:
        raise ValueError("A player ancestor has zero scale; the doll mount has no inverse")
    inv = [[(r[(j+1)%3][(i+1)%3]*r[(j+2)%3][(i+2)%3]-r[(j+1)%3][(i+2)%3]*r[(j+2)%3][(i+1)%3])/det for j in range(3)] for i in range(3)]
    return [row+[-sum(row[k]*a[k][3] for k in range(3))] for row in inv]+[[0, 0, 0, 1]]


def decompose(a):
    scale = [math.sqrt(sum(a[i][j]**2 for i in range(3))) for j in range(3)]
    if min(scale) < 1e-10:
        raise ValueError("The doll mount has zero scale")
    r = [[a[i][j]/scale[j] for j in range(3)] for i in range(3)]
    if max(abs(sum(r[k][i]*r[k][j] for k in range(3))) for i in range(3) for j in range(i+1, 3)) > 1e-5:
        raise ValueError("Parent nonuniform scale plus rotation produces shear; use uniform scale on player root/player")
    det = sum(r[0][i]*(r[1][(i+1)%3]*r[2][(i+2)%3]-r[1][(i+2)%3]*r[2][(i+1)%3]) for i in range(3))
    if det < 0:
        scale[0] *= -1
        for row in r:
            row[0] *= -1
    y = math.asin(max(-1, min(1, -r[2][0])))
    if abs(math.cos(y)) > 1e-7:
        x, z = math.atan2(r[2][1], r[2][2]), math.atan2(r[1][0], r[0][0])
    else:
        x, z = math.atan2(-r[1][2], r[1][1]), 0
    return [a[i][3] for i in range(3)], list(map(math.degrees, (x, y, z))), scale
