---
name: troll-checkpoint
description: Zapisuje zwięzły checkpoint projektu Troll, tak aby następna sesja mogła wystartować bez historii czatu. Użyj po każdym ukończonym zadaniu, przed końcem limitu, przed długą operacją i gdy rozmowa robi się długa.
---
# Checkpoint Troll

1. `cd troll/gis && python -m trollgis.report` (odświeża `SECTOR_REGISTRY.md` z rejestru).
2. Nadpisz `troll/SESSION_CHECKPOINT.md` — maks. 25 linii, tylko fakty:
   - data, gdzie działała sesja (komputer / chmura);
   - co ukończono od poprzedniego checkpointu (z nazwami plików / ID sektorów);
   - co jest w toku i w jakim stanie (albo "nic");
   - błędy i pułapki odkryte w tej sesji (1 linia każda);
   - **dokładnie jedno** następne zadanie z poleceniem do uruchomienia.
3. Odhacz lub dopisz punkty w `troll/NEXT_STEPS.md`; wyniki testów dopisz do `troll/TEST_REPORT.md`
   (osobno testy automatyczne i testy w Studio); nowe zasoby do `troll/ASSET_APPROVALS.md`.
4. Jeśli zmienił się stan ogólny — popraw odpowiednią linię w `troll/PROJECT_STATUS.md` (nie przepisuj całości).
5. Na komputerze użytkownika: zapisz plik Troll w Studio (tylko instancja Troll) i pliki .blend.
6. `git add troll .claude && git commit && git push` na gałąź roboczą.
