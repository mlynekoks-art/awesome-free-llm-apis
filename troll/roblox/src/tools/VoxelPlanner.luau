--!strict
-- Pure planning step: turns a decoded chunk into small voxel blocks ready for
-- Terrain:WriteVoxels. No Roblox API is used here so it can be unit-tested in Lune.
--
-- Every block is BLOCK x BLOCK columns. Its vertical range runs from 3 voxels
-- below the lowest column (including the 1-cell ring around the block, so that
-- neighbouring blocks always overlap vertically and cliffs have no holes) up to
-- the highest column or water surface. Water cells carry their own surface level
-- (sea = 0 m, each lake its own height); their stored height is the bed.
local TerrainMaterials = require(script.Parent.Parent.TrollShared.TerrainMaterials)

local VoxelPlanner = {}

VoxelPlanner.BLOCK = 25
VoxelPlanner.SHELL = 3

export type Block = {
	-- voxel-index bounds; multiply by voxel size (studs) for world coordinates
	minX: number,
	minY: number,
	minZ: number,
	sizeX: number,
	sizeY: number,
	sizeZ: number,
	materials: { { { string } } }, -- [x][y][z] Enum.Material names
	occupancy: { { { number } } },
}

-- chunk: decoded TRC1 chunk; xWestM / nSouthM: sector-local metres of the chunk's SW corner;
-- voxelsPerMetre: studsPerMetre / voxelStuds (1 for the Troll world).
function VoxelPlanner.plan(chunk: any, xWestM: number, nSouthM: number, voxelsPerMetre: number): { Block }
	local n = chunk.n
	local cells = n - 2
	local B = VoxelPlanner.BLOCK
	assert(voxelsPerMetre == 1, "planner currently assumes 1 voxel per metre cell")
	assert(cells % B == 0, "chunk size must be a multiple of the block size")
	local heights, mats, waters = chunk.heights, chunk.materials, chunk.water
	local NO_WATER = -9999
	local byCode = TerrainMaterials.byCode
	local blocks: { Block } = {}

	for br = 0, cells / B - 1 do
		for bc = 0, cells / B - 1 do
			local lo, hi = math.huge, -math.huge
			for r = br * B, br * B + B + 1 do -- includes halo ring (stored index = cell index + 1)
				local base = r * n
				for c = bc * B, bc * B + B + 1 do
					local h = heights[base + c + 1]
					if h < lo then
						lo = h
					end
					local inside = r > br * B and r <= br * B + B and c > bc * B and c <= bc * B + B
					if inside then
						if h > hi then
							hi = h
						end
						local wl = waters[base + c + 1]
						if wl ~= NO_WATER and wl > hi then
							hi = wl
						end
					end
				end
			end
			local minY = math.floor(lo * voxelsPerMetre) - VoxelPlanner.SHELL
			local maxY = math.ceil(hi * voxelsPerMetre) -- exclusive
			if maxY <= minY then
				maxY = minY + 1
			end
			local sizeY = maxY - minY

			local materials = table.create(B)
			local occupancy = table.create(B)
			for xi = 1, B do
				local c = bc * B + xi -- stored column index (halo offset already included)
				local mx = table.create(sizeY)
				local ox = table.create(sizeY)
				for yi = 1, sizeY do
					mx[yi] = table.create(B, "Air")
					ox[yi] = table.create(B, 0)
				end
				for zi = 1, B do
					local r = br * B + (B - zi) + 1 -- +Z is south, so zi = 1 is the northern row
					local i = r * n + c + 1
					local hv = heights[i] * voxelsPerMetre
					local code = mats[i]
					local surface = byCode[code] or "Ground"
					local wl = waters[i]
					local water = wl ~= NO_WATER
					local wv = wl * voxelsPerMetre
					for yi = 1, sizeY do
						local k = minY + yi - 1
						local occ = hv - k
						if occ >= 1 then
							mx[yi][zi] = if hv - k > 3 then TerrainMaterials.SUBSURFACE else surface
							ox[yi][zi] = 1
						elseif occ > 0 and (not water or occ >= 0.5) then
							mx[yi][zi] = surface
							ox[yi][zi] = occ
						elseif water and wv - k > 0 then
							mx[yi][zi] = TerrainMaterials.WATER
							ox[yi][zi] = math.min(1, wv - k)
						end
					end
				end
				materials[xi] = mx
				occupancy[xi] = ox
			end

			table.insert(blocks, {
				minX = (xWestM + bc * B) * voxelsPerMetre,
				minY = minY,
				minZ = -(nSouthM + (br + 1) * B) * voxelsPerMetre,
				sizeX = B,
				sizeY = sizeY,
				sizeZ = B,
				materials = materials,
				occupancy = occupancy,
			})
		end
	end
	return blocks
end

return VoxelPlanner
