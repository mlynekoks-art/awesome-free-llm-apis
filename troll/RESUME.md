# RESUME — jak wznowić pracę nad Troll

## Gdzie co jest
- Repozytorium: `mlynekoks-art/awesome-free-llm-apis`, gałąź `ccr-f82a2ec5-gq49mt`, katalog `troll/`.
  (Osobne repozytorium nie zostało utworzone: sesja chmurowa ma dostęp tylko do tego repo.)
- Sesje chmurowe są ulotne: `data/cache/`, pliki `dem_1m.tif`, `chunks.npy` i `roblox/build/` NIE są w gicie.
  Odtwarza je pipeline z danych Kartverket (≈1 min na sektor).

## Procedura na początku każdej sesji
1. Przeczytaj `RESUME.md`, potem `SESSION_CHECKPOINT.md` i `NEXT_STEPS.md`.
2. `git status`, `git log --oneline | head` na gałęzi roboczej.
3. Środowisko (kontener chmurowy nie ma nic zainstalowanego na stałe):
   ```bash
   pip install rasterio geopandas pyproj shapely scipy pyogrio
   curl -sSL -o /tmp/rojo.zip https://github.com/rojo-rbx/rojo/releases/download/v7.4.4/rojo-7.4.4-linux-x86_64.zip && unzip -o /tmp/rojo.zip -d /usr/local/bin
   curl -sSL -o /tmp/lune.zip https://github.com/lune-org/lune/releases/download/v0.8.9/lune-0.8.9-linux-x86_64.zip && unzip -o /tmp/lune.zip -d /usr/local/bin
   ```
4. Odtwórz dane podstawowe (≈1 min): `cd troll/gis && python -m trollgis.cli overview`
   (indeksu NIE przebudowuj — `data/registry/mainland_sectors.csv` jest w gicie i niesie statusy).
5. `python -m trollgis.cli status` — liczba sektorów wg statusu.
6. Odtworzenie danych gotowego sektora (gdy potrzebny .rbxl): `python -m trollgis.cli rebuild <ID>`
   (pobiera, koduje, waliduje, eksportuje od nowa, zachowuje status).
7. Kontynuuj od pierwszego niezakończonego punktu w `NEXT_STEPS.md`.

## Najważniejsze polecenia
```bash
cd troll/gis
python -m trollgis.cli sector NO-061-142          # zbuduj + zwaliduj + wyeksportuj sektor (ID albo "E,N")
python -m trollgis.cli batch 20 --near 126000,6950000   # kolejne 20 sektorów PENDING najbliżej punktu
python -m trollgis.cli landmarks                  # wysokości szczytów vs DEM
python -m trollgis.luau_test NO-061-142 08_02 00_00     # test dekodera/planera Luau w Lune
python -m trollgis.report                         # odśwież SECTOR_REGISTRY.md
cd ../roblox && rojo build build/NO-061-142.project.json -o build/Troll_NO-061-142.rbxl
```

## Roblox Studio (na komputerze użytkownika — z chmury niedostępne)
1. NIE dotykaj otwartej instancji Studio z inną grą. Otwórz plik `Troll_<ID>.rbxl` w NOWYM oknie Studio
   (dwuklik na pliku albo File → Open from File w nowym oknie), zapisz jako `Troll.rbxl` we własnym katalogu.
2. W pasku poleceń (View → Command Bar):
   `require(game.ServerStorage.TrollTools.TerrainImporter).importSector("NO-061-142")`
   Import jest wznawialny (ukończone chunki są pomijane).
3. Kontrola: `print(require(game.ServerStorage.TrollTools.TerrainImporter).verifyChunk("NO-061-142", 8, 2))`
   — największy błąd wysokości w metrach (oczekiwane < 1 m).
4. Zapisz plik (Ctrl+S). Zgłoś czas importu i zużycie pamięci — to brakujące pomiary w `TEST_REPORT.md`.

Aby kolejna sesja Claude mogła sama sterować Studio i Blenderem, uruchom ją na swoim komputerze
(aplikacja Claude Desktop albo `claude remote-control` w katalogu projektu) — sesja chmurowa nie widzi komputera.

## Automatyczne wznowienie
Nie skonfigurowano żadnego harmonogramu (wymaga zgody). Wznowienie = nowa wiadomość w tej sesji lub nowa sesja
z poleceniem „wznów Troll wg troll/RESUME.md”.
