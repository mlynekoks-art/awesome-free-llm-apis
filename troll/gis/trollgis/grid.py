"""Sector grid maths: global GIS metres <-> sector ids <-> local Roblox studs.

Hierarchy (all axis-aligned in the realm CRS, sizes in metres):
  realm  -> region (100 km) -> sector (4 km, one streamed Roblox area) -> chunk (250 m import unit)

Roblox axes: +X = east, +Y = up, -Z = north (so a top-down view has north up).
Each sector has its own local origin at the sector CENTRE at sea level, which keeps
coordinates within +-8000 studs and avoids float32 precision loss.
"""
from __future__ import annotations
from dataclasses import dataclass
from .config import world


@dataclass(frozen=True)
class Sector:
    realm: str
    col: int
    row: int

    @property
    def id(self) -> str:
        g = world()["grid"]
        return g["sector_id_format"].format(realm_code=g["realm_codes"][self.realm], col=self.col, row=self.row)

    @property
    def size(self) -> int:
        return world()["grid"]["sector_m"]

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """(min_e, min_n, max_e, max_n) in realm CRS metres."""
        r = world()["realms"][self.realm]
        e0 = r["origin_e"] + self.col * self.size
        n0 = r["origin_n"] + self.row * self.size
        return (e0, n0, e0 + self.size, n0 + self.size)

    @property
    def centre(self) -> tuple[float, float]:
        e0, n0, e1, n1 = self.bounds
        return ((e0 + e1) / 2, (n0 + n1) / 2)

    @property
    def region_id(self) -> str:
        g = world()["grid"]
        k = g["region_m"] // g["sector_m"]
        return f"{g['realm_codes'][self.realm]}-R{self.col // k:02d}-{self.row // k:02d}"

    def neighbours(self) -> dict[str, "Sector"]:
        return {"E": Sector(self.realm, self.col + 1, self.row), "W": Sector(self.realm, self.col - 1, self.row),
                "N": Sector(self.realm, self.col, self.row + 1), "S": Sector(self.realm, self.col, self.row - 1)}

    def to_studs(self, e: float, n: float, h: float = 0.0) -> tuple[float, float, float]:
        """Realm CRS metres -> this sector's local Roblox studs (X, Y, Z)."""
        s = world()["scale"]["studs_per_metre"]
        ce, cn = self.centre
        return ((e - ce) * s, h * s, -(n - cn) * s)

    def from_studs(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        s = world()["scale"]["studs_per_metre"]
        ce, cn = self.centre
        return (ce + x / s, cn - z / s, y / s)


def sector_at(realm: str, e: float, n: float) -> Sector:
    r = world()["realms"][realm]
    m = world()["grid"]["sector_m"]
    return Sector(realm, int((e - r["origin_e"]) // m), int((n - r["origin_n"]) // m))


def parse_id(sid: str) -> Sector:
    code, col, row = sid.split("-")
    realm = {v: k for k, v in world()["grid"]["realm_codes"].items()}[code]
    return Sector(realm, int(col), int(row))


def realm_bounds(realm: str) -> tuple[int, int, int, int]:
    r = world()["realms"][realm]
    m = world()["grid"]["sector_m"]
    return (r["origin_e"], r["origin_n"], r["origin_e"] + r["cols"] * m, r["origin_n"] + r["rows"] * m)
