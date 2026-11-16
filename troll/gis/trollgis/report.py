"""Generates SECTOR_REGISTRY.md from the registry (never edit that file by hand)."""
from __future__ import annotations
import collections
from datetime import datetime, timezone
from . import registry
from .config import ROOT, world


def write_sector_registry() -> None:
    w = world()
    rows = registry.read_index()
    counts = collections.Counter(r["status"] for r in rows)
    cls = collections.Counter(r["class"] for r in rows)
    fy = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        fy[r["fylke"]][r["status"]] += 1
    done = [r for r in rows if r["status"] != "PENDING"]
    L = ["# SECTOR_REGISTRY — rejestr sektorów świata Troll", "",
         f"_Plik generowany automatycznie: `python -m trollgis.report` ({datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC). Nie edytować ręcznie._", "",
         "## Siatka", "",
         f"- Układ: EPSG:25833 (ETRS89 / UTM 33N), początek siatki E={w['realms']['MAINLAND']['origin_e']}, N={w['realms']['MAINLAND']['origin_n']}",
         f"- Sektor: {w['grid']['sector_m']} m × {w['grid']['sector_m']} m = {int(w['grid']['sector_m'] * w['scale']['studs_per_metre'])} studów; chunk importu: {w['grid']['chunk_m']} m; region: {w['grid']['region_m'] // 1000} km",
         "- ID sektora: `NO-<kolumna>-<wiersz>` (kolumny rosną na wschód, wiersze na północ); region: `NO-R<kk>-<ww>`",
         "- Pełny indeks: `data/registry/mainland_sectors.csv`; stan sektora: `data/sectors/<ID>/sector.json`", "",
         "## Stan kraju (Norwegia kontynentalna)", "",
         f"- Sektory zawierające ląd Norwegii: **{len(rows)}** (LAND {cls['LAND']}, COAST {cls['COAST']}, BORDER {cls['BORDER']})", ""]
    L += ["| Status | Liczba sektorów |", "|---|---|"]
    L += [f"| {s} | {counts.get(s, 0)} |" for s in registry.STATUSES]
    L += ["", "Statusy: PENDING → DEM_READY (dane 1 m pobrane, zakodowane) → EXPORTED (walidacja GIS PASS, moduły Luau + plik .rbxl) → "
          "IMPORTED_IN_STUDIO (teren zapisany w Studio, sprawdzony `verifyChunk`) → DRESSED (przyroda, woda, zabudowa) → ACCEPTED (akceptacja użytkownika).", "",
          "## Postęp wg fylke", "", "| Fylke | Sektory | Wykonane (≥ DEM_READY) |", "|---|---|---|"]
    for name, c in sorted(fy.items(), key=lambda kv: -sum(kv[1].values())):
        tot = sum(c.values())
        L.append(f"| {name} | {tot} | {tot - c.get('PENDING', 0)} |")
    L += ["", "## Wykonane sektory", "",
          "| ID | Region | Fylke | Granice E (m) | Granice N (m) | Wys. min–max (m) | Morze | Status | LOD | Walidacja | Akceptacja |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in done:
        m = registry.load_meta(r["id"])
        L.append(f"| {r['id']} | {r['region']} | {r['fylke']} | {r['min_e']}–{r['max_e']} | {r['min_n']}–{r['max_n']} | "
                 f"{m['elevation']['min_m']}–{m['elevation']['max_m']} | {m['sea_frac']:.1%} | {r['status']} | {r['lod']} | {r['validation']} | {r['approval']} |")
    L += ["", "## Pozostałe obszary", "",
          "- **Svalbard** (`SJ-…`) i **Jan Mayen** (`JM-…`): siatki zdefiniowane w `config/world.json`, źródło DEM jeszcze niepodłączone (Norsk Polarinstitutt) — 0 sektorów.", ""]
    (ROOT / "SECTOR_REGISTRY.md").write_text("\n".join(L))


if __name__ == "__main__":
    registry.sync()
    write_sector_registry()
    print("SECTOR_REGISTRY.md written")
