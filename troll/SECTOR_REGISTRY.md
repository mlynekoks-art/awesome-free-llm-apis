# SECTOR_REGISTRY — rejestr sektorów świata Troll

_Plik generowany automatycznie: `python -m trollgis.report` (2026-11-16 18:24 UTC). Nie edytować ręcznie._

## Siatka

- Układ: EPSG:25833 (ETRS89 / UTM 33N), początek siatki E=-120000, N=6380000
- Sektor: 4000 m × 4000 m = 16000 studów; chunk importu: 250 m; region: 100 km
- ID sektora: `NO-<kolumna>-<wiersz>` (kolumny rosną na wschód, wiersze na północ); region: `NO-R<kk>-<ww>`
- Pełny indeks: `data/registry/mainland_sectors.csv`; stan sektora: `data/sectors/<ID>/sector.json`

## Stan kraju (Norwegia kontynentalna)

- Sektory zawierające ląd Norwegii: **24223** (LAND 17233, COAST 6232, BORDER 758)

| Status | Liczba sektorów |
|---|---|
| PENDING | 24211 |
| DEM_READY | 0 |
| EXPORTED | 12 |
| IMPORTED_IN_STUDIO | 0 |
| DRESSED | 0 |
| ACCEPTED | 0 |

Statusy: PENDING → DEM_READY (dane 1 m pobrane, zakodowane) → EXPORTED (walidacja GIS PASS, moduły Luau + plik .rbxl) → IMPORTED_IN_STUDIO (teren zapisany w Studio, sprawdzony `verifyChunk`) → DRESSED (przyroda, woda, zabudowa) → ACCEPTED (akceptacja użytkownika).

## Postęp wg fylke

| Fylke | Sektory | Wykonane (≥ DEM_READY) |
|---|---|---|
| Finnmark | 3670 | 0 |
| Nordland | 3464 | 1 |
| Innlandet | 3307 | 1 |
| Trøndelag | 3127 | 0 |
| Vestland | 2612 | 0 |
| Troms | 2149 | 0 |
| Møre og Romsdal | 1214 | 10 |
| Agder | 1119 | 0 |
| Telemark | 977 | 0 |
| Buskerud | 923 | 0 |
| Rogaland | 748 | 0 |
| Akershus | 393 | 0 |
| Østfold | 309 | 0 |
| Vestfold | 180 | 0 |
| Oslo | 31 | 0 |

## Wykonane sektory

| ID | Region | Fylke | Granice E (m) | Granice N (m) | Wys. min–max (m) | Morze | Status | LOD | Walidacja | Akceptacja |
|---|---|---|---|---|---|---|---|---|---|---|
| NO-066-117 | NO-R02-04 | Innlandet | 144000–148000 | 6848000–6852000 | 1355.0–2468.54 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-060-141 | NO-R02-05 | Møre og Romsdal | 120000–124000 | 6944000–6948000 | 184.45–1638.45 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-061-141 | NO-R02-05 | Møre og Romsdal | 124000–128000 | 6944000–6948000 | 53.22–1796.97 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-062-141 | NO-R02-05 | Møre og Romsdal | 128000–132000 | 6944000–6948000 | 52.53–1800.74 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-060-142 | NO-R02-05 | Møre og Romsdal | 120000–124000 | 6948000–6952000 | 15.09–1611.55 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-061-142 | NO-R02-05 | Møre og Romsdal | 124000–128000 | 6948000–6952000 | 3.38–1788.11 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-062-142 | NO-R02-05 | Møre og Romsdal | 128000–132000 | 6948000–6952000 | 8.09–1850.79 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-060-143 | NO-R02-05 | Møre og Romsdal | 120000–124000 | 6952000–6956000 | 7.99–1237.99 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-061-143 | NO-R02-05 | Møre og Romsdal | 124000–128000 | 6952000–6956000 | -0.2–1182.98 | 3.6% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-062-143 | NO-R02-05 | Møre og Romsdal | 128000–132000 | 6952000–6956000 | 3.45–1335.79 | 0.0% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-061-144 | NO-R02-05 | Møre og Romsdal | 124000–128000 | 6956000–6960000 | -0.22–1136.07 | 37.2% | EXPORTED | L2 | PASS | NOT_SUBMITTED |
| NO-134-289 | NO-R05-11 | Nordland | 416000–420000 | 7536000–7540000 | -0.3–796.25 | 39.6% | EXPORTED | L2 | PASS | NOT_SUBMITTED |

## Pozostałe obszary

- **Svalbard** (`SJ-…`) i **Jan Mayen** (`JM-…`): siatki zdefiniowane w `config/world.json`, źródło DEM jeszcze niepodłączone (Norsk Polarinstitutt) — 0 sektorów.
