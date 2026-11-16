"""Chunk codec 'TRC1' - compact binary shared with roblox/src/shared/ChunkCodec.luau.

Layout (little endian):
  magic 'TRC1' | u16 n (cells per side incl. halo) | u16 reserved
  heights: per row (south->north), u16 absolute first cell then zig-zag varint deltas west->east
  materials: RLE (u8 code, varint run length), row-major, same order
Heights are quantised: q = round((h_m - offset_m) / step_m).
"""
from __future__ import annotations
import base64
import numpy as np
from .config import world


def quantise(h: np.ndarray) -> np.ndarray:
    e = world()["height_encoding"]
    q = np.rint((h.astype(np.float64) - e["offset_m"]) / e["step_m"])
    if q.min() < 0 or q.max() >= e["nodata"]:
        raise ValueError(f"height out of encodable range: {h.min()}..{h.max()}")
    return q.astype(np.int64)


def dequantise(q: np.ndarray) -> np.ndarray:
    e = world()["height_encoding"]
    return q * e["step_m"] + e["offset_m"]


def _varint(out: bytearray, v: int) -> None:
    while v >= 0x80:
        out.append((v & 0x7F) | 0x80)
        v >>= 7
    out.append(v)


def encode(q: np.ndarray, mat: np.ndarray) -> bytes:
    """q, mat: (n, n) arrays, row 0 = SOUTH edge, col 0 = WEST edge."""
    n = q.shape[0]
    out = bytearray(b"TRC1")
    out += int(n).to_bytes(2, "little") + b"\0\0"
    d = np.diff(q, axis=1)
    zz = ((d << 1) ^ (d >> 63)).tolist()
    first = q[:, 0].tolist()
    for r in range(n):
        out += first[r].to_bytes(2, "little")
        for v in zz[r]:
            _varint(out, v)
    flat = mat.ravel()
    cuts = np.flatnonzero(np.diff(flat)) + 1
    starts = np.concatenate(([0], cuts))
    lens = np.diff(np.concatenate((starts, [flat.size])))
    for s, ln in zip(starts.tolist(), lens.tolist()):
        out.append(int(flat[s]))
        _varint(out, ln)
    return bytes(out)


def decode(blob: bytes) -> tuple[np.ndarray, np.ndarray]:
    assert blob[:4] == b"TRC1"
    n = int.from_bytes(blob[4:6], "little")
    p = 8
    q = np.empty((n, n), np.int64)

    def varint():
        nonlocal p
        v = shift = 0
        while True:
            b = blob[p]; p += 1
            v |= (b & 0x7F) << shift
            if b < 0x80:
                return v
            shift += 7

    for r in range(n):
        cur = int.from_bytes(blob[p:p + 2], "little"); p += 2
        q[r, 0] = cur
        for c in range(1, n):
            z = varint()
            cur += (z >> 1) ^ -(z & 1)
            q[r, c] = cur
    mat = np.empty(n * n, np.uint8)
    i = 0
    while i < n * n:
        code = blob[p]; p += 1
        ln = varint()
        mat[i:i + ln] = code
        i += ln
    return q, mat.reshape(n, n)


def to_b64(blob: bytes) -> str:
    return base64.b64encode(blob).decode()
