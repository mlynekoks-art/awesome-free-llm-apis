"""Chunk codec 'TRC2' - compact binary shared with roblox/src/shared/ChunkCodec.luau.

Layout (little endian):
  magic 'TRC2' | u16 n (cells per side incl. halo) | u16 number of water levels L
  heights: per row (south->north), u16 absolute first cell then zig-zag varint deltas west->east
  materials: RLE (u8 code, varint run length), row-major, same order
  water: L x u16 quantised water-surface levels, then RLE (u8 level index, varint run); index 0 = no water,
         index i = levels[i-1]. For water cells the HEIGHT is the bed (sea bed / lake bed), not the surface.
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


def _rle(out: bytearray, flat: np.ndarray) -> None:
    cuts = np.flatnonzero(np.diff(flat)) + 1
    starts = np.concatenate(([0], cuts))
    lens = np.diff(np.concatenate((starts, [flat.size])))
    for s, ln in zip(starts.tolist(), lens.tolist()):
        out.append(int(flat[s]))
        _varint(out, ln)


def encode(q: np.ndarray, mat: np.ndarray, wq: np.ndarray) -> bytes:
    """q, mat, wq: (n, n) arrays, row 0 = SOUTH edge, col 0 = WEST edge.
    wq = quantised water surface level per cell, -1 where there is no water."""
    n = q.shape[0]
    levels = np.unique(wq[wq >= 0])
    if len(levels) > 255:
        raise ValueError("more than 255 distinct water levels in one chunk")
    out = bytearray(b"TRC2")
    out += int(n).to_bytes(2, "little") + len(levels).to_bytes(2, "little")
    d = np.diff(q, axis=1)
    zz = ((d << 1) ^ (d >> 63)).tolist()
    first = q[:, 0].tolist()
    for r in range(n):
        out += first[r].to_bytes(2, "little")
        for v in zz[r]:
            _varint(out, v)
    _rle(out, mat.ravel())
    for lv in levels.tolist():
        out += int(lv).to_bytes(2, "little")
    idx = np.zeros(wq.shape, np.int64)
    idx[wq >= 0] = np.searchsorted(levels, wq[wq >= 0]) + 1
    _rle(out, idx.ravel())
    return bytes(out)


def decode(blob: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    assert blob[:4] == b"TRC2"
    n = int.from_bytes(blob[4:6], "little")
    nlev = int.from_bytes(blob[6:8], "little")
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
    levels = [-1]
    for _ in range(nlev):
        levels.append(int.from_bytes(blob[p:p + 2], "little")); p += 2
    wq = np.empty(n * n, np.int64)
    i = 0
    while i < n * n:
        code = blob[p]; p += 1
        ln = varint()
        wq[i:i + ln] = levels[code]
        i += ln
    return q, mat.reshape(n, n), wq.reshape(n, n)


def to_b64(blob: bytes) -> str:
    return base64.b64encode(blob).decode()
