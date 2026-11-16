--!strict
-- Decoder for the 'TRC2' terrain chunk format written by gis/trollgis/codec.py.
-- A chunk is an n x n grid (n = chunk cells + 2: one halo cell on every side).
-- Index = row * n + col + 1, row 0 = SOUTH edge, col 0 = WEST edge.
local Base64 = require(script.Parent.Base64)

export type Chunk = {
	n: number,
	heights: { number }, -- metres above sea level (negative = synthetic seabed)
	materials: { number }, -- codes from TerrainMaterials
	water: { number }, -- water surface level in metres, NO_WATER where dry; for wet cells `heights` is the bed
}

local ChunkCodec = {}

ChunkCodec.NO_WATER = -9999

function ChunkCodec.decode(payload: string, heightOffset: number, heightStep: number): Chunk
	local buf = Base64.decode(payload)
	assert(buffer.readstring(buf, 0, 4) == "TRC2", "not a TRC2 chunk")
	local n = buffer.readu16(buf, 4)
	local levelCount = buffer.readu16(buf, 6)
	local p = 8
	local total = n * n
	local heights = table.create(total, 0)
	local materials = table.create(total, 0)

	local function varint(): number
		local value, mult = 0, 1
		while true do
			local b = buffer.readu8(buf, p)
			p += 1
			value += (b % 128) * mult
			if b < 128 then
				return value
			end
			mult *= 128
		end
	end

	local idx = 1
	for _ = 1, n do
		local cur = buffer.readu16(buf, p)
		p += 2
		heights[idx] = cur * heightStep + heightOffset
		idx += 1
		for _ = 2, n do
			local z = varint()
			-- zig-zag decode
			if z % 2 == 0 then
				cur += z // 2
			else
				cur -= (z + 1) // 2
			end
			heights[idx] = cur * heightStep + heightOffset
			idx += 1
		end
	end

	idx = 1
	while idx <= total do
		local code = buffer.readu8(buf, p)
		p += 1
		local run = varint()
		for i = idx, idx + run - 1 do
			materials[i] = code
		end
		idx += run
	end
	local levels = table.create(levelCount, 0)
	for i = 1, levelCount do
		levels[i] = buffer.readu16(buf, p) * heightStep + heightOffset
		p += 2
	end
	local water = table.create(total, ChunkCodec.NO_WATER)
	idx = 1
	while idx <= total do
		local level = buffer.readu8(buf, p)
		p += 1
		local run = varint()
		if level > 0 then
			local value = levels[level]
			for i = idx, idx + run - 1 do
				water[i] = value
			end
		end
		idx += run
	end
	return { n = n, heights = heights, materials = materials, water = water }
end

return ChunkCodec
