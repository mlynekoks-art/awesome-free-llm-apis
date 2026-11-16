--!strict
-- Studio-side terrain importer. Run from the Studio command bar (edit mode) so
-- the generated terrain is saved with the place:
--
--   require(game.ServerStorage.TrollTools.TerrainImporter).importSector("NO-061-142")
--
-- The import is resumable: finished chunks are recorded as attributes on the
-- sector data folder and skipped on the next run. Use clearProgress to redo.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("TrollShared")
local ChunkCodec = require(Shared.ChunkCodec)
local SectorGrid = require(Shared.SectorGrid)
local WorldConfig = require(Shared.WorldConfig)
local VoxelPlanner = require(script.Parent.VoxelPlanner)

local TerrainImporter = {}

local VOXEL = WorldConfig.scale.voxel_studs

local function materialGrid(names: { { { string } } }): { { { Enum.Material } } }
	local out = table.create(#names)
	for x, plane in names do
		local px = table.create(#plane)
		for y, row in plane do
			local py = table.create(#row)
			for z, name in row do
				py[z] = (Enum.Material :: any)[name]
			end
			px[y] = py
		end
		out[x] = px
	end
	return out
end

local function sectorFolder(sectorId: string): Instance
	local data = ServerStorage:FindFirstChild("TrollSectorData")
	local folder = data and data:FindFirstChild(sectorId)
	assert(folder, `No data for sector {sectorId} under ServerStorage.TrollSectorData`)
	return folder
end

export type Options = { chunkFilter: ((ci: number, cj: number) -> boolean)?, yieldEvery: number? }

function TerrainImporter.importSector(sectorId: string, options: Options?): { chunks: number, blocks: number, seconds: number }
	local folder = sectorFolder(sectorId)
	local manifest = require(folder:FindFirstChild("Manifest") :: ModuleScript) :: SectorGrid.Manifest
	local terrain = workspace.Terrain
	local started = os.clock()
	local chunkCount, blockCount = 0, 0
	local yieldEvery = if options and options.yieldEvery then options.yieldEvery else 20
	local voxelsPerMetre = manifest.studsPerMetre / VOXEL

	local modules = folder:GetChildren()
	table.sort(modules, function(a, b)
		return a.Name < b.Name
	end)
	for _, module in modules do
		local ci, cj = string.match(module.Name, "^c_(%d+)_(%d+)$")
		if not ci then
			continue
		end
		local ciN, cjN = tonumber(ci) :: number, tonumber(cj) :: number
		if options and options.chunkFilter and not options.chunkFilter(ciN, cjN) then
			continue
		end
		if folder:GetAttribute("done_" .. module.Name) then
			continue
		end
		local chunk = ChunkCodec.decode(require(module :: ModuleScript) :: string, manifest.heightOffset, manifest.heightStep)
		local xWest, nSouth = SectorGrid.chunkOriginMetres(manifest, ciN, cjN)
		for i, block in VoxelPlanner.plan(chunk, xWest, nSouth, voxelsPerMetre) do
			local min = Vector3.new(block.minX, block.minY, block.minZ) * VOXEL
			local size = Vector3.new(block.sizeX, block.sizeY, block.sizeZ) * VOXEL
			terrain:WriteVoxels(Region3.new(min, min + size), VOXEL, materialGrid(block.materials), block.occupancy)
			blockCount += 1
			if i % yieldEvery == 0 then
				task.wait()
			end
		end
		folder:SetAttribute("done_" .. module.Name, true)
		chunkCount += 1
		print(`[Troll] {sectorId} chunk {module.Name} imported ({chunkCount} this run)`)
		task.wait()
	end

	workspace:SetAttribute("TrollSectorId", sectorId)
	workspace:SetAttribute("TrollSectorCentreE", manifest.centre[1])
	workspace:SetAttribute("TrollSectorCentreN", manifest.centre[2])
	local seconds = os.clock() - started
	print(`[Troll] {sectorId}: {chunkCount} chunks, {blockCount} blocks in {string.format("%.1f", seconds)} s`)
	return { chunks = chunkCount, blocks = blockCount, seconds = seconds }
end

function TerrainImporter.clearProgress(sectorId: string)
	local folder = sectorFolder(sectorId)
	for name in folder:GetAttributes() do
		if string.sub(name, 1, 5) == "done_" then
			folder:SetAttribute(name, nil)
		end
	end
end

-- Samples the generated terrain and compares it with the source heights.
-- Returns the worst absolute error in metres over `samples` random columns of one chunk.
function TerrainImporter.verifyChunk(sectorId: string, ci: number, cj: number, samples: number?): number
	local folder = sectorFolder(sectorId)
	local manifest = require(folder:FindFirstChild("Manifest") :: ModuleScript) :: SectorGrid.Manifest
	local module = folder:FindFirstChild(string.format("c_%02d_%02d", ci, cj)) :: ModuleScript
	local chunk = ChunkCodec.decode(require(module) :: string, manifest.heightOffset, manifest.heightStep)
	local xWest, nSouth = SectorGrid.chunkOriginMetres(manifest, ci, cj)
	local rng = Random.new(1)
	local worst = 0
	local cells = chunk.n - 2
	for _ = 1, samples or 200 do
		local c, r = rng:NextInteger(1, cells), rng:NextInteger(1, cells)
		local h = chunk.heights[r * chunk.n + c + 1]
		if chunk.water[r * chunk.n + c + 1] == ChunkCodec.NO_WATER then
			local x = (xWest + c - 0.5) * manifest.studsPerMetre
			local z = -(nSouth + r - 0.5) * manifest.studsPerMetre
			local hit = workspace:Raycast(Vector3.new(x, (h + 60) * manifest.studsPerMetre, z), Vector3.new(0, -400 * manifest.studsPerMetre, 0))
			if hit then
				worst = math.max(worst, math.abs(hit.Position.Y / manifest.studsPerMetre - h))
			else
				worst = math.huge
			end
		end
	end
	return worst
end

return TerrainImporter
