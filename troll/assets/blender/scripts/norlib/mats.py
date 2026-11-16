"""Image-texture-only PBR materials (what Roblox SurfaceAppearance can reproduce):
ColorMap (+alpha), NormalMap (OpenGL), RoughnessMap, MetalnessMap (0)."""
import os
import bpy

ALPHA_CUTOFF = 0.35


def _img(path, non_color):
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def pbr(name, folder, files, alpha=False):
    """files: dict with keys albedo, normal, rough (file names inside folder)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.45

    t_alb = nt.nodes.new("ShaderNodeTexImage")
    t_alb.image = _img(os.path.join(folder, files["albedo"]), False)
    t_alb.location = (-400, 300)
    nt.links.new(t_alb.outputs["Color"], bsdf.inputs["Base Color"])

    t_r = nt.nodes.new("ShaderNodeTexImage")
    t_r.image = _img(os.path.join(folder, files["rough"]), True)
    t_r.location = (-400, 0)
    nt.links.new(t_r.outputs["Color"], bsdf.inputs["Roughness"])

    t_n = nt.nodes.new("ShaderNodeTexImage")
    t_n.image = _img(os.path.join(folder, files["normal"]), True)
    t_n.location = (-400, -300)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.location = (-100, -300)
    nt.links.new(t_n.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    if alpha:
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = ALPHA_CUTOFF
        gt.location = (0, 200)
        nt.links.new(t_alb.outputs["Alpha"], gt.inputs[0])
        nt.links.new(gt.outputs[0], bsdf.inputs["Alpha"])
        try:
            mat.blend_method = "CLIP"
        except Exception:
            pass
        t_alb.image.alpha_mode = "STRAIGHT"
    else:
        t_alb.image.alpha_mode = "NONE"
    mat["roblox_maps"] = {k: v for k, v in files.items()}
    return mat


def flat(name, rgb, rough=0.6):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    return mat
