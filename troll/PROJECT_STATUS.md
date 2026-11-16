# PROJECT_STATUS — Troll (stan: 2026-11-16)

## Wykonane (faktycznie)
- Projekt `troll/`: konfiguracja świata, pipeline GIS w Pythonie (14 modułów), kod Luau, projekt Rojo, testy.
- Układ i skala: EPSG:25833, 4 study = 1 m (1 woksel = 1 m), sektory 4 km z lokalnym początkiem układu.
- Model L0 całej Norwegii kontynentalnej (250 m) z krajowego DTM Kartverket: `reports/L0_norway_overview.png`.
- Oficjalne granice 15 fylker (Kartverket WFS) → maska państwa.
- Globalny indeks: **24 223 sektory** z lądem Norwegii, każdy z ID, granicami, fylke, statystyką wysokości, statusem.
- Pipeline 1 m: pobranie → otoczka → maska morza → klasy terenu → chunki TRC1 → walidacja → moduły Luau → `.rbxl`.
- **12 sektorów (192 km²) w statusie EXPORTED**, wszystkie z walidacją PASS:
  Romsdalen 3×3 + Åndalsnes (NO-060…062-141…143, NO-061-144), Reine/Lofoty (NO-134-289), Galdhøpiggen (NO-066-117).
- Rejestr źródeł GIS z weryfikacją punktów dostępu: `GIS_SOURCES.md`.
- Architektura analizy słońce/cień (`SunExposure.luau`) i profile oświetlenia (`Environment.luau`).

## Niewykonane / zablokowane
- **Roblox Studio**: nie uruchomiono nowego okna, nie zaimportowano terenu, nie podłączono MCP. Powód: ta sesja
  działa w kontenerze chmurowym i nie widzi komputera (brak udostępnionego folderu Remote Control, brak
  Roblox/Blender MCP). Druga gra nie została dotknięta — nie było do niej żadnego dostępu.
  Zamiast tego powstał samodzielny plik miejsca `Troll_NO-061-142.rbxl` + importer do uruchomienia w Studio.
- Osobne repozytorium: niedostępne z tej sesji; projekt leży w `troll/` na gałęzi roboczej.
- Kryteria ukończenia Pakietu 0–1 niespełnione: „działa połączenie z instancją Studio” i „rzeczywisty import
  co najmniej jednego obszaru do Studio”. Pozostałe spełnione.
- Svalbard, Jan Mayen: tylko definicje siatek. Jeziora, rzeki, pokrycie terenu, drogi, zabudowa: niepodłączone.

## Narzędzia
| Narzędzie | Stan |
|---|---|
| Python 3.13 + rasterio, geopandas, pyproj, shapely, scipy | działa (instalowane per sesja) |
| Kartverket WCS DTM 1 m, WFS granice, API Stedsnavn | działa |
| Rojo 7.4.4 (budowa .rbxl), Lune 0.8.9 (testy Luau) | działa |
| Blender 4.2 headless (CPU) | używany przez agenta zasobów |
| Roblox Studio, Roblox Studio MCP, Blender MCP, lokalny Blender | niedostępne z chmury |
| GDAL CLI | brak (zastąpione przez rasterio) |
| Overpass API, nve.geodataonline.no | nieosiągalne z tego środowiska |

## Podział pracy na modele
Główny wykonawca: architektura, pipeline, walidacja. Agent lżejszego modelu: rejestr źródeł GIS. Agent mocnego
modelu: zasoby Blender. Limitu procentowego sesja nie udostępnia — stosowane częste commity.
