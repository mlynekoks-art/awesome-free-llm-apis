# WORLD_MASTERPLAN — świat gry Troll (Norwegia 1:1)

## 1. Zakres
Cała Norwegia jako docelowy świat: kontynent (realm `MAINLAND`), Svalbard (`SVALBARD`) i Jan Mayen (`JANMAYEN`)
jako odrębne obszary. Geografia pochodzi wyłącznie z danych pomiarowych; wszystko, co jest rekonstrukcją
(np. dno morza, materiały terenu przed podłączeniem NIBIO), jest oznaczane w `sector.json`.

## 2. Skala i układ współrzędnych (decyzje)
| Decyzja | Wartość | Uzasadnienie |
|---|---|---|
| Układ GIS kontynentu | EPSG:25833 (ETRS89 / UTM 33N) | natywny układ krajowego modelu wysokości Kartverket — brak przepróbkowania |
| Skala | **4 study = 1 m** | 1 woksel terenu Roblox (4 study) = 1 m³, więc krajowy DTM 1 m trafia 1:1 do wokseli |
| Poziom morza | Y = 0 | wysokości NN2000 × 4 = study |
| Osie | +X wschód, +Y góra, −Z północ | widok z góry ma północ u góry |
| Początek lokalny | środek sektora, poziom morza | współrzędne w sektorze ≤ ±8000 studów → brak utraty precyzji float32 |
| Postać | awatar skalowany ok. 1,2× (≈1,75 m) | przy 4 studach/m domyślny awatar ma ≈1,4 m |

Konwersja: `X = (E − E_środka)·4`, `Y = h·4`, `Z = −(N − N_środka)·4` — `gis/trollgis/grid.py` i `roblox/src/shared/SectorGrid.luau`.
Galdhøpiggen (2469 m) = 9876 studów wysokości; Norwegia ma ok. 1750 km długości = 7 mln studów, dlatego świat
jest dzielony na sektory z własnym początkiem układu.

## 3. Hierarchia podziału
| Poziom | Rozmiar | Rola |
|---|---|---|
| Realm | cały obszar (kontynent / Svalbard / Jan Mayen) | osobny układ i źródła danych |
| Region `NO-Rkk-ww` | 100 km | jednostka planowania, klimatu i partii produkcyjnych |
| **Sektor `NO-kkk-www`** | **4 km × 4 km (16 000 studów)** | jednostka produkcji, walidacji, akceptacji i streamingu; kandydat na jedno Place lub jego część |
| Chunk `c_ii_jj` | 250 m (1000 studów) | jednostka importu do Studio (wznawialna), 256 na sektor |
| Blok | 25 m | pojedyncze wywołanie `Terrain:WriteVoxels` |

Dlaczego 4 km: 16 mln kolumn wokseli na sektor to rozmiar, który da się zaimportować i zweryfikować w jednej
sesji Studio, ±8000 studów mieści się daleko od granic precyzji, a 4 km to wielokrotność siatki DTM.
**Do potwierdzenia w Studio:** zużycie pamięci serwera dla pełnego sektora 1 m (patrz TEST_REPORT — testy w Studio
jeszcze niewykonane). Jeśli sektor okaże się za ciężki, chunk 250 m pozwala zejść do Place 2 km bez zmiany danych.

Kontynent: 24 223 sektory z lądem Norwegii (indeks w `data/registry/mainland_sectors.csv`). Pełna rozdzielczość
1 m dla całego kraju to ~388 mld komórek, więc sektory L2 powstają partiami na żądanie (≈1 min/sektor), a stan
każdego jest trwały — nic nie jest nadpisywane bez `force`.

## 4. Poziomy szczegółowości
| LOD | Rozdzielczość | Zawartość | Stan |
|---|---|---|---|
| L0 kraj | 250 m | model całej Norwegii: maska lądu, indeks, mapa, daleki horyzont | **zbudowany** |
| L1 region | 25 m | siatki dalekiego terenu wokół aktywnego sektora, tabele horyzontu dla cieni gór | zaprojektowany |
| L2 eksploracja | 1 m | teren wokselowy Roblox | **pipeline działa** |
| L3 fabuła | 1 m + siatki | L2 + ręczne ściany skalne/jaskinie (nawisy, których mapa wysokości nie odda) | planowany |

## 5. Styki
Każdy sektor pobiera 40 m otoczki z tej samej krajowej siatki, a każdy chunk niesie 1 komórkę otoczki. Sąsiedzi
czytają te same komórki źródłowe, więc krawędzie zgadzają się co do kwantu (0,05 m) bez wygładzania — sprawdza to
`validate_neighbours`. Bloki wokseli sięgają 3 m poniżej najniższej kolumny wraz z sąsiadami, więc klify nie mają dziur.

## 6. Roblox: Places, streaming, pamięć
- `Workspace.StreamingEnabled = true`; klient dostaje tylko okolicę gracza.
- Serwer trzyma cały teren Place → jedno Place = jeden sektor lub mały blok sektorów; przejścia teleportem
  z zachowaniem pozycji GIS (`SectorGrid.fromStuds` → sąsiedni sektor → `toStuds`).
- Daleki krajobraz (góry poza Place) = siatki L1, nie teren wokselowy.
- Ograniczenie platformy: 24 tys. sektorów nie będzie istniało jednocześnie jako Places. Plan: sektory fabularne
  i zamieszkane budowane w pełni, reszta generowana pipeline'em w miarę rozszerzania gry. Zakres geograficzny
  (indeks, dane, współrzędne) pozostaje kompletny.

## 7. Warstwy świata i ich źródła (szczegóły: GIS_SOURCES.md)
| Warstwa | Źródło docelowe | Stan |
|---|---|---|
| Wysokości | Kartverket NHM DTM 1 m (WCS) | działa |
| Granica państwa, fylker | Kartverket Administrative enheter (WFS) | działa |
| Morze | maska z DTM (h = 0, spójny obszar ≥ 400 m²) | działa; dno syntetyczne |
| Jeziora, rzeki | NVE Innsjødatabase / Elvenett, N50 | do podłączenia |
| Pokrycie terenu, lasy | NIBIO AR5 / SR16, N50 | do podłączenia; teraz klasy tymczasowe z wysokości i nachylenia |
| Drogi, tunele, mosty | Statens vegvesen NVDB | do podłączenia |
| Zabudowa, miejscowości | N50 / OSM / Stedsnavn | do podłączenia |
| Klimat, pogoda | MET Norway (seNorge, Frost) | do podłączenia |

## 8. Oświetlenie i analiza słońce/cień
`Environment.luau` ustawia szerokość geograficzną sektora i profile atmosfery (clear/overcast/fog).
`SunExposure.luau` odpowiada na pytanie „czy punkt jest w bezpośrednim słońcu”: (1) słońce nad horyzontem,
(2) raycast w stronę słońca po streamowanym terenie, (3) zaczep na tabelę dalekiego horyzontu z L1 (góry poza
obszarem streamingu). To fundament późniejszej mechaniki trolli; walka nie jest implementowana.

## 9. Architektura repozytorium
```
troll/
  config/world.json        jedyne źródło prawdy o skali, siatce, LOD (czytane przez Pythona i Luau)
  gis/trollgis/            pipeline: grid, wcs, overview, boundaries, registry, tiles, materials, codec,
                           export_roblox, validate, preview, report, luau_test, cli
  data/registry/           globalny indeks sektorów (CSV)      data/sectors/<ID>/sector.json  stan sektora
  data/boundaries/         fylker (Kartverket)                 data/cache/  pobrane dane (poza gitem)
  roblox/default.project.json   projekt Rojo
  roblox/src/shared/       WorldConfig, SectorGrid, ChunkCodec, Base64, TerrainMaterials, SunExposure
  roblox/src/tools/        VoxelPlanner (czysta logika), TerrainImporter (Studio)
  roblox/src/server|client Bootstrap, Environment
  roblox/tests/            testy Lune (poza Studio)
  assets/                  skrypty Blender, rendery, eksporty kandydatów
  reports/                 wyniki testów, podglądy
```
Miejsca na przyszłe systemy (multiplayer, AI trolli, zwierzęta, ekonomia, pojazdy, fabuła): osobne foldery pod
`roblox/src/server/<System>` i `shared/<System>`; świat udostępnia im `SectorGrid`, `SunExposure`, manifest sektora.
