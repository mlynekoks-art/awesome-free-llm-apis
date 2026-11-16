# NEXT_STEPS — kolejność dalszych prac

Zasada: wykonuj od góry; po każdym punkcie aktualizuj `SESSION_CHECKPOINT.md` i commituj.

## A. Wymaga komputera użytkownika (Roblox Studio / Blender lokalny)
1. Otworzyć `Troll_NO-061-142.rbxl` w NOWYM oknie Studio, zapisać jako projekt Troll, uruchomić import
   (`RESUME.md` → sekcja Roblox Studio). Zmierzyć: czas importu sektora, pamięć Studio, błąd `verifyChunk`.
2. Zgłosić wyniki → wpisać do `TEST_REPORT.md` (sekcja „Testy w Studio”), ustawić status `IMPORTED_IN_STUDIO`.
3. Obejrzeć kandydatów zasobów (`assets/renders/`, `ASSET_APPROVALS.md`) i zaakceptować / odrzucić.
4. Uruchomić sesję Claude na komputerze (Claude Desktop lub `claude remote-control`), żeby kolejne importy
   i widoki w Studio wykonywał agent, a nie człowiek.

## B. Możliwe w sesji chmurowej (bez Studio)
1. **Rzeki**: NVE Elvenett (osie) + N50 (poligony szerokich rzek) → woda płynąca ze spadkiem; wyjaśnić jeziora
   `REJECTED_NOT_FLAT`. (Jeziora i lodowce: zrobione.)
2. **Pokrycie terenu**: NIBIO AR5/AR50 + SR16 (gatunek, wysokość drzewostanu) → materiały terenu i mapy gęstości
   roślinności per sektor; zastąpić klasy tymczasowe (`material_source`).
3. **Śnieg sezonowy**: seNorge (MET/NVE) → pokrywa śnieżna wg pory roku. (Lodowce: zrobione.)
4. **Drogi, tunele, mosty, kolej**: NVDB + N50 → wektory per sektor (`roads.json`), wyrównanie terenu pod drogą.
5. **Zabudowa i miejscowości**: N50 / OSM budynki, Stedsnavn → `settlements.json`, obrysy, klasy architektury.
6. **L1 25 m**: siatki dalekiego terenu per region + tabele horyzontu dla `SunExposure`.
7. **Svalbard i Jan Mayen**: podłączyć DEM Norsk Polarinstitutt, zbudować indeksy `SJ-`/`JM-`.
8. **Batymetria**: zastąpić syntetyczne dno (EMODnet / Kartverket dybdedata w dozwolonej rozdzielczości).
9. **Partie sektorów**: `python -m trollgis.cli batch N --near E,N` — kolejność regionów: Romsdalen →
   Jotunheimen → Lofoty → Geiranger/Sunnmøre → Lysefjord → Oslo → Tromsø/Lyngen → Finnmark.
10. **Optymalizacja importu**: bloki o zmiennej wysokości pionowej tylko przy powierzchni (mniej zapisów wokseli
    na stromych ścianach), ewentualnie bezpośredni zapis `SmoothGrid` do .rbxl.
11. **Zasoby przyrody**: poprawki kandydatów po uwagach, kolejne gatunki (jarzębina, olsza, jałowiec, karłowata
    brzoza, wierzby), runo (borówka, wrzos, mchy, porosty), martwe drewno; system rozmieszczania wg SR16.

## C. Decyzje czekające na użytkownika
- Akceptacja skali 4 study = 1 m i rozmiaru sektora 4 km (po teście w Studio).
- Akceptacja kandydatów modeli (patrz `ASSET_APPROVALS.md`).
- Czy projekt ma dostać własne repozytorium (obecnie katalog `troll/` w istniejącym repo).
