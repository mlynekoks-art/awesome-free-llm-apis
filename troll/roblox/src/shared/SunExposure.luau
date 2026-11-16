--!strict
-- Sun / shadow query used by world systems (later: troll behaviour and light combat).
-- Answers "is this point in direct sunlight right now?" in two stages:
--   1. astronomical: is the sun above the horizon at all;
--   2. local occlusion: raycast towards the sun against streamed terrain and parts;
--   3. (hook) far occlusion: mountains outside the streamed area, supplied by a
--      per-sector horizon table that the GIS pipeline will precompute from L1 data.
local SunExposure = {}

export type HorizonProvider = (position: Vector3, azimuthRad: number) -> number -- horizon elevation angle (rad)

local horizonProvider: HorizonProvider? = nil

function SunExposure.setHorizonProvider(provider: HorizonProvider?)
	horizonProvider = provider
end

export type Result = { lit: boolean, reason: "night" | "far_horizon" | "occluded" | "lit", hit: RaycastResult? }

function SunExposure.query(position: Vector3, sunDirection: Vector3, params: RaycastParams?, maxDistance: number?): Result
	if sunDirection.Y <= 0 then
		return { lit = false, reason = "night" }
	end
	if horizonProvider then
		local azimuth = math.atan2(sunDirection.X, -sunDirection.Z)
		if math.asin(sunDirection.Y) < horizonProvider(position, azimuth) then
			return { lit = false, reason = "far_horizon" }
		end
	end
	local hit = workspace:Raycast(position, sunDirection * (maxDistance or 4000), params)
	if hit then
		return { lit = false, reason = "occluded", hit = hit }
	end
	return { lit = true, reason = "lit" }
end

return SunExposure
