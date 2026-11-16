"""Low-level mesh building: bark tubes and foliage alpha cards with explicit UVs and
custom (split) normals, then conversion to Blender objects."""
import math
import numpy as np

try:
    import bpy
except ImportError:  # allows importing the maths in plain Python
    bpy = None

UP = np.array([0.0, 0.0, 1.0])


def unit(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def perp(v):
    a = np.array([1.0, 0, 0]) if abs(v[0]) < 0.9 else np.array([0, 1.0, 0])
    return unit(np.cross(v, a))


def rotate(v, axis, ang):
    """Rodrigues rotation of v around unit axis."""
    axis = unit(axis)
    c, s = math.cos(ang), math.sin(ang)
    return v * c + np.cross(axis, v) * s + axis * np.dot(axis, v) * (1 - c)


class MeshBuilder:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.uvs = []      # per face: list of (u, v)
        self.lnorm = []    # per face: list of normals
        self.nv = 0

    @property
    def tris(self):
        return sum(len(f) - 2 for f in self.faces)

    def _add_verts(self, pts):
        base = self.nv
        self.verts.extend([tuple(p) for p in pts])
        self.nv += len(pts)
        return base

    # ------------------------------------------------------------------ tubes
    def add_tube(self, pts, radii, sides, u_range=(0.0, 0.5), v0=0.0, cap_end=True,
                 tex_aspect=2.0, twist=0.0, flare=None):
        """Generalised cylinder along polyline pts (N,3) with radii (N,).
        UV: u wraps once around within u_range, v advances ds / (tex_aspect * circumference)
        so texels stay square.  Returns final v."""
        pts = np.asarray(pts, dtype=np.float64)
        radii = np.asarray(radii, dtype=np.float64)
        n = len(pts)
        if n < 2:
            return v0
        tang = np.zeros_like(pts)
        tang[0] = pts[1] - pts[0]
        tang[-1] = pts[-1] - pts[-2]
        tang[1:-1] = pts[2:] - pts[:-2]
        tang = np.array([unit(t) for t in tang])
        normal = perp(tang[0])
        frames = []
        for i in range(n):
            if i > 0:
                b = np.cross(tang[i - 1], tang[i])
                if np.linalg.norm(b) > 1e-9:
                    ang = math.acos(max(-1.0, min(1.0, float(np.dot(tang[i - 1], tang[i])))))
                    normal = rotate(normal, b, ang)
            frames.append((normal.copy(), np.cross(tang[i], normal)))
        u0, u1 = u_range
        eps = (u1 - u0) * 0.004
        ring_pts, ring_nrm, ring_uv = [], [], []
        v = v0
        for i in range(n):
            if i > 0:
                ds = np.linalg.norm(pts[i] - pts[i - 1])
                circ = 2 * math.pi * max(0.5 * (radii[i] + radii[i - 1]), 1e-3)
                v += ds / (tex_aspect * circ)
            nrm, bin_ = frames[i]
            row_p, row_n, row_uv = [], [], []
            for j in range(sides + 1):
                a = 2 * math.pi * j / sides + twist * i
                d = math.cos(a) * nrm + math.sin(a) * bin_
                r = radii[i]
                if flare is not None:
                    r *= flare(i, a)
                row_p.append(pts[i] + d * r)
                row_n.append(d)
                row_uv.append((u0 + eps + (u1 - u0 - 2 * eps) * j / sides, v))
            ring_pts.append(row_p)
            ring_nrm.append(row_n)
            ring_uv.append(row_uv)
        base = self._add_verts([p for row in ring_pts for p in row])
        w = sides + 1
        for i in range(n - 1):
            for j in range(sides):
                a, b = base + i * w + j, base + i * w + j + 1
                c, d = base + (i + 1) * w + j + 1, base + (i + 1) * w + j
                self.faces.append((a, b, c, d))
                self.uvs.append([ring_uv[i][j], ring_uv[i][j + 1], ring_uv[i + 1][j + 1], ring_uv[i + 1][j]])
                self.lnorm.append([ring_nrm[i][j], ring_nrm[i][j + 1], ring_nrm[i + 1][j + 1], ring_nrm[i + 1][j]])
        if cap_end and radii[-1] > 0.004:
            tip = self._add_verts([pts[-1] + tang[-1] * radii[-1] * 0.8])
            for j in range(sides):
                a, b = base + (n - 1) * w + j, base + (n - 1) * w + j + 1
                self.faces.append((a, b, tip))
                self.uvs.append([ring_uv[-1][j], ring_uv[-1][j + 1], (0.5 * (u0 + u1), v + 0.01)])
                self.lnorm.append([ring_nrm[-1][j], ring_nrm[-1][j + 1], tang[-1]])
        return v

    # ------------------------------------------------------------------ cards
    def add_card(self, base, direction, normal, length, width, u_range, bend=0.0, segs=1,
                 fold=0.0, outward=None, outward_mix=0.5, v_range=(0.0, 1.0)):
        """Alpha card whose v=0 edge sits at `base` and grows along `direction`.
        bend: total downward (towards -normal of a horizontal card, i.e. gravity) bend in rad.
        fold: V-fold angle (rad) along the centre line -> 3 verts across, 4 tris per segment.
        outward: optional unit vector blended into the vertex normals (soft crown shading)."""
        d = unit(direction)
        nrm = unit(normal - d * np.dot(normal, d))
        if outward is not None and np.dot(nrm, outward) < 0:
            nrm = -nrm                      # face the crown exterior (cards are double sided)
        side = unit(np.cross(d, nrm))       # winding so that the geometric normal == nrm
        cols = 3 if fold else 2
        rows = segs + 1
        pts, nrms, uvs = [], [], []
        pos = np.asarray(base, dtype=np.float64)
        cur_d, cur_n = d.copy(), nrm.copy()
        step = length / segs
        u0, u1 = u_range
        for r in range(rows):
            t = r / segs
            if r > 0:
                rot_axis = side
                cur_d = rotate(cur_d, rot_axis, -bend / segs)
                cur_n = rotate(cur_n, rot_axis, -bend / segs)
                pos = pos + cur_d * step if r == 1 else pos + cur_d * step
            vv = v_range[0] + (v_range[1] - v_range[0]) * t
            for c in range(cols):
                if cols == 2:
                    off = (c - 0.5) * width
                    p = pos + side * off
                    uu = u0 if c == 0 else u1
                    nn = cur_n
                else:
                    off = (c - 1) * width * 0.5
                    lift = -abs(off) * math.tan(fold)
                    p = pos + side * off + cur_n * lift
                    uu = (u0, 0.5 * (u0 + u1), u1)[c]
                    nn = unit(cur_n + side * (np.sign(off) * math.sin(fold)))
                if outward is not None:
                    nn = unit(nn * (1 - outward_mix) + np.asarray(outward) * outward_mix)
                pts.append(p)
                nrms.append(nn)
                uvs.append((uu, vv))
        base_i = self._add_verts(pts)
        for r in range(segs):
            for c in range(cols - 1):
                a = base_i + r * cols + c
                b, cc, dd = a + 1, a + cols + 1, a + cols
                self.faces.append((a, b, cc, dd))
                self.uvs.append([uvs[a - base_i], uvs[b - base_i], uvs[cc - base_i], uvs[dd - base_i]])
                self.lnorm.append([nrms[a - base_i], nrms[b - base_i], nrms[cc - base_i], nrms[dd - base_i]])

    # ------------------------------------------------------------------ blender
    def to_object(self, name, material=None, collection=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        me.validate(clean_customdata=False)
        uvl = me.uv_layers.new(name="UVMap")
        flat_uv = [uv for f in self.uvs for uv in f]
        flat_n = [tuple(n) for f in self.lnorm for n in f]
        if len(flat_uv) == len(me.loops):
            uvl.data.foreach_set("uv", np.array(flat_uv, dtype=np.float32).ravel())
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        if len(flat_n) == len(me.loops):
            me.normals_split_custom_set(flat_n)
        if material is not None:
            me.materials.append(material)
        ob = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        return ob
