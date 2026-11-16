# TEST_REPORT — wyniki testów (stan: 2026-11-16)

Rozróżnienie: **testy automatyczne na danych / w Lune** (wykonane) kontra **testy w uruchomionym Roblox Studio**
(NIEWYKONANE — sesja chmurowa nie ma dostępu do Studio).

## 1. Testy automatyczne GIS — wykonane
| Test | Zakres | Wynik |
|---|---|---|
| Kodek TRC2 (zapis→odczyt) | 12 sektorów, wszystkie komórki lądowe | PASS, błąd ≤ 0,025 m (pół kwantu 0,05 m) |
| Styki chunków w sektorze | 12 sektorów × 256 chunków | PASS, 0 rozbieżności |
| Krawędź sektora vs niezależne ponowne pobranie z WCS | 12 sektorów | PASS (różnica 0 m) |
| Styki między sektorami (dane zakodowane) | 26 krawędzi, 104 000 komórek | PASS, 0 rozbieżności (`reports/neighbour_seams.json`) |
| Dziury / NaN / zakres wysokości | 12 sektorów | PASS |
| Woda: lustro nie niżej niż dno; poziom jeziora = płaska powierzchnia DTM | 12 sektorów, 56 jezior | PASS (różnica ≤ 0,025 m) |
| Szczyty: DEM vs wysokość oficjalna | 8 szczytów (`reports/landmarks.json`) | różnice −1,23…+1,10 m |

Szczyty: Galdhøpiggen 2468,54 (ofic. 2469), Glittertind 2451,68 (2452), Store Skagastølstind 2403,77 (2405),
Snøhetta 2287,10 (2286), Store Trolltind 1788,11 (1788), Romsdalshornet 1549,73 (1550), Gaustatoppen 1882,12 (1883),
Stetinden 1391,09 (1392). Pozycje z API Stedsnavn Kartverket lub przeliczone z lon/lat; szukane maksimum DEM w oknie.

Położenie: podglądy z zakodowanych danych (`reports/previews/`) pokazują rozpoznawalne Romsdalen (Trollveggen,
ujście Raumy, Isfjorden) i Reine/Reinefjorden — kontrola wzrokowa, nie pomiar.

## 2. Testy kodu Luau poza Studio (Lune) — wykonane
`python -m trollgis.luau_test` — dekoder `ChunkCodec` i `VoxelPlanner` na prawdziwych chunkach:
- NO-061-142 (Trollveggen): 4 chunki — PASS
- NO-134-289 (Reine, 40% morza, jeziora na 3–406 m): 5 chunków — PASS
- NO-066-117 (Galdhøpiggen, 55% lodowca): 2 chunki — PASS
- NO-062-142: 2 chunki — PASS

Sprawdzane: zgodność dekodera Luau z Pythonem (różnica < 1e-12 m), wysokość kolumny odtworzona z wypełnienia wokseli
= wysokość źródłowa, woda (morze i jeziora) sięga zapisanego poziomu lustra z dokładnością pół woksela, brak pustek w kolumnach, brak otwartych ścian między sąsiednimi
kolumnami. Najbardziej stromy chunk: 7,9 mln wokseli, bloki do 444 wokseli wysokości.

## 3. Budowanie plików Roblox — wykonane
`rojo build` tworzy `Troll.rbxl` (baza) i `Troll_<ID>.rbxl` (baza + dane sektora, ok. 21 MB). Pliki NIE były otwierane w Studio.

## 4. Testy w Roblox Studio — NIEWYKONANE
Import terenu (`TerrainImporter.importSector`), `verifyChunk`, kolizje, przejezdność, czas importu, pamięć,
stabilność Studio, wygląd materiałów, streaming, oświetlenie. Kod importera nie został uruchomiony w Studio ani razu.

## 5. Znane ograniczenia i błędy
- Indeks L0 zawyża ląd o ok. 4,6% (338,9 tys. km² vs ok. 323,8 tys.) — próbkowanie biliniowe 250 m wzdłuż wybrzeża;
  indeks jest przez to zachowawczy (nie gubi lądu), ale część sektorów COAST może być samym morzem.
- Jeziora: zarys z NVE Innsjødatabase doprecyzowany na DTM; 2 z 58 odrzucone (`REJECTED_NOT_FLAT`, m.in.
  Reinevatnet) — DTM nie jest tam płaski, zostają lądem do wyjaśnienia. Rzeki nie mają jeszcze wody; dolne odcinki
  na poziomie 0 m są klasyfikowane jako morze.
- Błąd znaleziony i naprawiony w tej sesji: jeziora przecięte granicą sektora miały różne dno po obu stronach
  (do 2,15 m). Wykrył to test styków; poziom jeziora jest teraz liczony z punktu wewnątrz całego poligonu.
- Dno morza (rampa do −12 m) i jezior (do −6 m) jest syntetyczne. Lodowce: poligony NVE Bre → materiał Glacier. Materiały terenu są tymczasowe (wysokość + nachylenie).
- Mapa wysokości nie odda nawisów (np. górne partie Trollveggen) — potrzebne siatki L3.
- DTM to model terenu bez roślinności i budynków; na lodowcach i śniegu wysokość zależy od daty skanowania.
- Granica państwa w indeksie pochodzi z poligonów fylker rasteryzowanych na 250 m (dokładność indeksu, nie terenu).
- Wydajność importu stromych sektorów jest nieznana (do ~1 mld zapisów wokseli na sektor).
