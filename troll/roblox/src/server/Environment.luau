--!strict
-- Lighting / atmosphere baseline for a sector. Weather, seasons and the full
-- day-night driver will plug in here; for now this applies a neutral overcast-
-- capable Nordic daylight profile and the sector's real latitude.
local Lighting = game:GetService("Lighting")
local ServerStorage = game:GetService("ServerStorage")

local Environment = {}

export type Profile = { brightness: number, ambient: Color3, fogDensity: number, haze: number, colour: Color3 }

Environment.profiles = {
	clear = { brightness = 2.6, ambient = Color3.fromRGB(108, 116, 128), fogDensity = 0.22, haze = 1.2, colour = Color3.fromRGB(199, 210, 222) },
	overcast = { brightness = 1.4, ambient = Color3.fromRGB(122, 126, 132), fogDensity = 0.34, haze = 2.4, colour = Color3.fromRGB(186, 190, 196) },
	fog = { brightness = 1.0, ambient = Color3.fromRGB(128, 130, 134), fogDensity = 0.62, haze = 6, colour = Color3.fromRGB(196, 198, 200) },
} :: { [string]: Profile }

local function sectorLatitude(sectorId: string?): number?
	local data = ServerStorage:FindFirstChild("TrollSectorData")
	local folder = if sectorId and data then data:FindFirstChild(sectorId) else nil
	local manifest = folder and folder:FindFirstChild("Manifest")
	if manifest and manifest:IsA("ModuleScript") then
		return (require(manifest) :: any).latitude
	end
	return nil
end

function Environment.apply(sectorId: string?, profileName: string?)
	local profile = Environment.profiles[profileName or "clear"]
	Lighting.GeographicLatitude = sectorLatitude(sectorId) or 62.5
	Lighting.Brightness = profile.brightness
	Lighting.OutdoorAmbient = profile.ambient
	Lighting.EnvironmentDiffuseScale = 1
	Lighting.EnvironmentSpecularScale = 1
	local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere") or Instance.new("Atmosphere")
	atmosphere.Density = profile.fogDensity
	atmosphere.Haze = profile.haze
	atmosphere.Color = profile.colour
	atmosphere.Decay = Color3.fromRGB(92, 104, 120)
	atmosphere.Parent = Lighting
end

return Environment
