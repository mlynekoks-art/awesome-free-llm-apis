"""LOD export (FBX + GLB) and mesh statistics.

Export conventions (documented in ASSET_REPORT.md):
* Units: metres (FBX unit scale 1 m).  In Roblox Studio's 3D Importer pick
  "File Dimensions: Meter" (1 stud = 0.28 m) so the assets arrive at true size.
* FBX: Y-up, -Z forward, triangulated, tangent space included, textures referenced by
  relative path (not embedded), one MeshPart per Blender object.
* GLB: Y-up (glTF standard), textures embedded at the LOD's texture resolution.
"""
import json
import os
import bpy
import numpy as np


def mesh_stats(ob):
    me = ob.data
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3) @ np.array(ob.matrix_world)[:3, :3].T + np.array(ob.matrix_world)[:3, 3]
    # 'render vertices' = unique (vertex, uv, normal) combinations, which is what an engine uploads
    uv = np.empty(len(me.loops) * 2, np.float32)
    if me.uv_layers:
        me.uv_layers.active.data.foreach_get("uv", uv)
    vi = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", vi)
    nrm = np.zeros(len(me.loops) * 3, np.float32)
    if hasattr(me, "corner_normals"):
        me.corner_normals.foreach_get("vector", nrm)
    key = np.concatenate([vi[:, None].astype(np.float64), np.round(uv.reshape(-1, 2), 5),
                          np.round(nrm.reshape(-1, 3), 3)], axis=1)
    render_verts = len(np.unique(key, axis=0)) if len(key) else 0
    return {
        "object": ob.name,
        "tris": tris,
        "verts": len(me.vertices),
        "render_verts": int(render_verts),
        "min": co.min(0).round(3).tolist() if len(co) else [0, 0, 0],
        "max": co.max(0).round(3).tolist() if len(co) else [0, 0, 0],
        "material": me.materials[0].name if me.materials else None,
    }


def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def export_lod(objs, folder, base):
    os.makedirs(folder, exist_ok=True)
    select_only(objs)
    fbx = os.path.join(folder, base + ".fbx")
    glb = os.path.join(folder, base + ".glb")
    bpy.ops.export_scene.fbx(
        filepath=fbx, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z", axis_up="Y", use_triangles=True, use_tspace=True, mesh_smooth_type="OFF",
        use_mesh_modifiers=True, path_mode="RELATIVE", embed_textures=False, add_leaf_bones=False,
        bake_anim=False, object_types={"MESH"})
    bpy.ops.export_scene.gltf(
        filepath=glb, export_format="GLB", use_selection=True, export_yup=True,
        export_apply=True, export_tangents=True, export_image_format="AUTO",
        export_materials="EXPORT", export_cameras=False, export_lights=False)
    stats = [mesh_stats(o) for o in objs]
    return {
        "fbx": os.path.relpath(fbx, folder), "glb": os.path.relpath(glb, folder),
        "fbx_bytes": os.path.getsize(fbx), "glb_bytes": os.path.getsize(glb),
        "meshes": stats, "tris": sum(s["tris"] for s in stats),
        "verts": sum(s["verts"] for s in stats),
        "render_verts": sum(s["render_verts"] for s in stats),
    }


def bounds(objs):
    mins, maxs = [], []
    for o in objs:
        s = mesh_stats(o)
        mins.append(s["min"])
        maxs.append(s["max"])
    return np.min(mins, 0), np.max(maxs, 0)


def write_stats(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
