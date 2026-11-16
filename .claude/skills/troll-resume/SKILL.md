---
name: troll-resume
description: Wznawia pracę nad grą Roblox "Troll" (Norwegia 1:1) z zapisanego stanu, bez czytania historii czatu. Użyj na początku każdej sesji dotyczącej Troll albo gdy użytkownik pisze "wznów Troll", "kontynuuj Troll", "dalej z mapą".
---
# Wznowienie Troll — minimalne zużycie limitu

Stan projektu jest w plikach, nie w czacie. NIE odtwarzaj kontekstu z rozmowy i nie czytaj całych dokumentów.

1. Przeczytaj TYLKO: `troll/SESSION_CHECKPOINT.md` (cały, jest krótki) i sekcję z pierwszym niezakończonym
   punktem w `troll/NEXT_STEPS.md`. Inne pliki otwieraj dopiero, gdy zadanie tego wymaga (Grep zamiast Read).
2. `git status --short && git log --oneline | head -5` na gałęzi roboczej.
3. Ustal, gdzie działasz:
   - **komputer użytkownika** (jest Roblox Studio / Studio MCP): wykonuj listę A z `NEXT_STEPS.md`.
     Najpierw wylistuj instancje Studio; pracuj wyłącznie na tej z projektem Troll. Drugiej gry nie dotykaj:
     nie zapisuj, nie zamykaj, nie publikuj. Przed każdą modyfikacją potwierdź, że cel to Troll.
   - **kontener chmurowy** (brak Studio): wykonuj listę B. Środowisko: polecenia z `troll/RESUME.md` §3–4.
4. Pracuj od pierwszego niezakończonego punktu. Nie planuj od nowa, nie zmieniaj decyzji z `WORLD_MASTERPLAN.md`.

## Oszczędzanie limitu
- Wyniki poleceń ograniczaj (`| tail -5`, `grep`), długie zadania puszczaj w tle.
- Delegowanie: wyszukiwanie, rejestry źródeł, dokumenty → lżejszy model (sonnet/haiku); modele Blender,
  architektura, trudne błędy → mocny model. Agentowi dawaj ścieżki plików i kryteria, nie historię.
- Po każdym ukończonym punkcie uruchom skill `troll-checkpoint`.
- Nie raportuj jako wykonanych testów w Studio, jeśli ich nie uruchomiono.
