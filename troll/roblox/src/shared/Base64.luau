--!strict
-- Base64 decoder writing straight into a buffer (used for the terrain chunk payloads).
local Base64 = {}

local LUT = table.create(256, 0)
do
	local alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
	for i = 1, #alphabet do
		LUT[string.byte(alphabet, i) + 1] = i - 1
	end
end

function Base64.decode(text: string): buffer
	local len = #text
	local pad = 0
	if len > 0 and string.byte(text, len) == 61 then
		pad += 1
	end
	if len > 1 and string.byte(text, len - 1) == 61 then
		pad += 1
	end
	local outLen = (len // 4) * 3 - pad
	local out = buffer.create(outLen)
	local o = 0
	for i = 1, len, 4 do
		local a, b, c, d = string.byte(text, i, i + 3)
		local n = LUT[a + 1] * 262144 + LUT[b + 1] * 4096 + LUT[c + 1] * 64 + LUT[d + 1]
		if o < outLen then
			buffer.writeu8(out, o, n // 65536)
		end
		if o + 1 < outLen then
			buffer.writeu8(out, o + 1, (n // 256) % 256)
		end
		if o + 2 < outLen then
			buffer.writeu8(out, o + 2, n % 256)
		end
		o += 3
	end
	return out
end

return Base64
