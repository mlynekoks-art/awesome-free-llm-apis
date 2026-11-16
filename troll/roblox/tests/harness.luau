-- Minimal fake Roblox instance tree so game modules can be required under Lune.
-- Only pure modules (no Roblox services) can be loaded this way.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local serde = require("@lune/serde")

local Harness = {}
local cache = {}

local function node(name, parent)
	local children = {}
	local self = { Name = name, Parent = parent, __children = children }
	setmetatable(self, { __index = function(_, key)
		return children[key]
	end })
	if parent then
		parent.__children[name] = self
	end
	return self
end

local function mount(dir, name, parent)
	local folder = node(name, parent)
	for _, entry in fs.readDir(dir) do
		local path = dir .. "/" .. entry
		if fs.isDir(path) then
			mount(path, entry, folder)
		else
			local base = string.match(entry, "^(.-)%.luau$")
			if base and not string.find(base, "%.") then
				node(base, folder).__source = path
			end
		end
	end
	return folder
end

function Harness.require(target)
	if cache[target] ~= nil then
		return cache[target]
	end
	if target.__value ~= nil then
		return target.__value
	end
	local chunk = luau.load(fs.readFile(target.__source), {
		debugName = target.Name,
		environment = { script = target, require = Harness.require },
	})
	local result = chunk()
	cache[target] = result
	return result
end

function Harness.build(root)
	local game = node("game", nil)
	local shared = mount(root .. "/roblox/src/shared", "TrollShared", game)
	node("WorldConfig", shared).__value = serde.decode("json", fs.readFile(root .. "/config/world.json"))
	local tools = mount(root .. "/roblox/src/tools", "TrollTools", game)
	return { shared = shared, tools = tools }
end

return Harness
