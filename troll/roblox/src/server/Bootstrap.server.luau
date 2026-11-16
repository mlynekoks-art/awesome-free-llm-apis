--!strict
-- Server entry point. Only wires services together; systems live in their own modules.
local Environment = require(script.Parent.Environment)

Environment.apply(workspace:GetAttribute("TrollSectorId") :: string?)
