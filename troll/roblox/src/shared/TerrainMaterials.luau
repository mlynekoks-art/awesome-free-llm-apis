--!strict
-- Terrain class codes. MUST match gis/trollgis/materials.py (checked by gis/tests).
-- Values are Enum.Material item names so this module stays loadable outside Roblox.
local TerrainMaterials = {}

TerrainMaterials.SEA = 13
TerrainMaterials.LAKE = 14

TerrainMaterials.byCode = {
	[1] = "Grass",
	[2] = "LeafyGrass",
	[3] = "Ground",
	[4] = "Rock",
	[5] = "Slate",
	[6] = "Snow",
	[7] = "Glacier",
	[8] = "Sand",
	[9] = "Mud",
	[13] = "Sand", -- seabed under sea water
	[14] = "Mud", -- lake bed under fresh water
} :: { [number]: string }

TerrainMaterials.SUBSURFACE = "Rock"
TerrainMaterials.WATER = "Water"

function TerrainMaterials.isWater(code: number): boolean
	return code == TerrainMaterials.SEA or code == TerrainMaterials.LAKE
end

return TerrainMaterials
