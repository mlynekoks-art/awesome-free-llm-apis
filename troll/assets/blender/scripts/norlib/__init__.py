"""norlib - shared helpers for the Norwegian nature asset generators.

Modules
-------
paths   : canonical output folders (everything lives under troll/assets/)
tex     : numpy texture synthesis (tileable noise, worley, needle/leaf card
          painter, height->normal, PNG IO).  Run inside Blender's Python.
bark    : bark texture builders (spruce / pine / birch)
foliage : needle / leaf card atlas builders (spruce / pine / birch)
geo     : mesh builder (tubes with bark UVs, alpha cards), Blender object creation
mats    : PBR material builders that only use image textures (Roblox friendly)
export  : LOD export (FBX + GLB) and mesh statistics
studio  : render studio (neutral turntable still, 1.8 m reference figure,
          overcast Nordic sky line-up)

1 Blender unit = 1 metre everywhere.
"""
