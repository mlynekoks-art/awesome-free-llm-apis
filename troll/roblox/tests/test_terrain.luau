-- Lune test: Luau decoder + voxel planner against values exported by the Python pipeline.
--   lune run roblox/tests/test_terrain.luau <root> <fixture.json>
local fs = require("@lune/fs")
local process = require("@lune/process")
local serde = require("@lune/serde")
local Harness = require("./harness")

local root, fixturePath = process.args[1], process.args[2]
local tree = Harness.build(root)
local ChunkCodec = Harness.require(tree.shared.ChunkCodec)
local SectorGrid = Harness.require(tree.shared.SectorGrid)
local VoxelPlanner = Harness.require(tree.tools.VoxelPlanner)
local fixture = serde.decode("json", fs.readFile(fixturePath))
local manifest = fixture.manifest
local failures = 0
local report = { sector = manifest.id, chunks = {} }

for _, case in fixture.chunks do
	local t0 = os.clock()
	local chunk = ChunkCodec.decode(case.payload, manifest.heightOffset, manifest.heightStep)
	local decodeS = os.clock() - t0
	local n = chunk.n
	-- 1. decoder agrees with Python on every cell
	local maxDiff, matDiff, waterDiff = 0, 0, 0
	for i = 1, n * n do
		maxDiff = math.max(maxDiff, math.abs(chunk.heights[i] - case.heights[i]))
		waterDiff = math.max(waterDiff, math.abs(chunk.water[i] - case.water[i]))
		if chunk.materials[i] ~= case.materials[i] then
			matDiff += 1
		end
	end
	-- 2. planner: rebuild each column's surface height from the voxel occupancies
	t0 = os.clock()
	local xWest, nSouth = SectorGrid.chunkOriginMetres(manifest, case.ci, case.cj)
	local blocks = VoxelPlanner.plan(chunk, xWest, nSouth, 1)
	local planS = os.clock() - t0
	local voxels, maxColErr, waterBad, holes, maxSizeY, wetColumns = 0, 0, 0, 0, 0, 0
	local cells = n - 2
	local columnTop = {} -- key r*cells+c -> {minY, top}
	for _, b in blocks do
		voxels += b.sizeX * b.sizeY * b.sizeZ
		maxSizeY = math.max(maxSizeY, b.sizeY)
		for xi = 1, b.sizeX do
			for zi = 1, b.sizeZ do
				local c = (b.minX - xWest) + xi -- 1-based cell column
				local r = (-b.minZ - nSouth) - zi + 1 -- 1-based cell row from south
				local i = r * n + c + 1
				local h, code = chunk.heights[i], chunk.materials[i]
				local wl = chunk.water[i]
				local solid, gap, seenAir, waterSum, waterBelowSolid = 0, false, false, 0, false
				for yi = 1, b.sizeY do
					local m, o = b.materials[xi][yi][zi], b.occupancy[xi][yi][zi]
					if m == "Water" then
						waterSum += o
					elseif m ~= "Air" then
						if seenAir or waterSum > 0 then
							gap = true
						end
						solid += o
					else
						seenAir = true
					end
				end
				if gap then
					holes += 1
				end
				local surface = b.minY + solid
				if wl ~= -9999 then
					-- bed within half a voxel of the stored bed, water column reaches the surface level
					local top = math.floor(surface + 0.5) + waterSum
					if math.abs(surface - h) > 0.5 + 1e-9 or math.abs(top - wl) > 0.5 + 1e-9 or (code ~= 13 and code ~= 14) then
						waterBad += 1
					end
					wetColumns += 1
				else
					if waterSum > 0 then
						waterBad += 1
					end
					maxColErr = math.max(maxColErr, math.abs(surface - h))
				end
				columnTop[r * 1000 + c] = { b.minY, h }
			end
		end
	end
	-- 3. no vertical hole between horizontally adjacent columns (cliff faces stay closed)
	local open = 0
	for r = 1, cells do
		for c = 1, cells do
			local me = columnTop[r * 1000 + c]
			for _, d in { { 0, 1 }, { 1, 0 }, { 0, -1 }, { -1, 0 } } do
				local other = columnTop[(r + d[1]) * 1000 + c + d[2]]
				if other and me[1] > other[2] then
					open += 1
				end
			end
		end
	end
	local ok = maxDiff < 1e-6 and waterDiff < 1e-6 and matDiff == 0 and maxColErr < 1e-6 and waterBad == 0 and holes == 0 and open == 0 and #blocks == (cells / 25) ^ 2
	if not ok then
		failures += 1
	end
	table.insert(report.chunks, {
		chunk = case.name, pass = ok, decodeMaxDiffM = maxDiff, materialMismatches = matDiff, blocks = #blocks,
		voxelsWritten = voxels, maxBlockHeightVoxels = maxSizeY, columnHeightMaxErrM = maxColErr, waterColumnsWrong = waterBad, wetColumns = wetColumns, waterLevelDecodeDiffM = waterDiff,
		interiorGaps = holes, openCliffFaces = open, decodeSeconds = decodeS, planSeconds = planS,
	})
	print(string.format("%s %s  decodeDiff=%.2g colErr=%.2g blocks=%d voxels=%d maxH=%d wet=%d water_bad=%d gaps=%d open=%d  (decode %.3fs plan %.3fs)",
		case.name, ok and "PASS" or "FAIL", maxDiff, maxColErr, #blocks, voxels, maxSizeY, wetColumns, waterBad, holes, open, decodeS, planS))
end
report.result = failures == 0 and "PASS" or "FAIL"
fs.writeFile(process.args[3], serde.encode("json", report, true))
print("RESULT", report.result)
process.exit(failures == 0 and 0 or 1)
