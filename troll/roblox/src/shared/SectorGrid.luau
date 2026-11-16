--!strict
-- Coordinate conversion between the realm CRS (metres, e.g. EPSG:25833) and the
-- local stud space of one sector. Mirrors gis/trollgis/grid.py.
--   +X = east, +Y = up, -Z = north. Local origin = sector centre at sea level.
local SectorGrid = {}

export type Manifest = {
	id: string,
	centre: { number },
	bounds: { number },
	sectorMetres: number,
	chunkMetres: number,
	studsPerMetre: number,
	heightOffset: number,
	heightStep: number,
	latitude: number?,
	longitude: number?,
}

function SectorGrid.toStuds(m: Manifest, easting: number, northing: number, heightM: number?): (number, number, number)
	local s = m.studsPerMetre
	return (easting - m.centre[1]) * s, (heightM or 0) * s, -(northing - m.centre[2]) * s
end

function SectorGrid.fromStuds(m: Manifest, x: number, y: number, z: number): (number, number, number)
	local s = m.studsPerMetre
	return m.centre[1] + x / s, m.centre[2] - z / s, y / s
end

-- West edge X and south edge northing-offset (both in metres, sector-local) of chunk (ci, cj).
function SectorGrid.chunkOriginMetres(m: Manifest, ci: number, cj: number): (number, number)
	local half = m.sectorMetres / 2
	return -half + ci * m.chunkMetres, -half + cj * m.chunkMetres
end

return SectorGrid
