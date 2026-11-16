import os

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(SCRIPTS))          # troll/assets
EXPORT = os.path.join(ROOT, "export")
TEXTURES = os.path.join(ROOT, "textures")
RENDERS = os.path.join(ROOT, "renders")
STATS = os.path.join(ROOT, "blender", "stats")
BLEND = os.path.join(ROOT, "blender", "blend")


def ensure(*parts):
    p = os.path.join(*parts)
    os.makedirs(p, exist_ok=True)
    return p


def tex_dir(species, mobile=False):
    return ensure(TEXTURES, species, "mobile") if mobile else ensure(TEXTURES, species)


def export_dir(asset):
    return ensure(EXPORT, asset)
