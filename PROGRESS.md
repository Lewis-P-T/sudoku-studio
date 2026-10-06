# Sudoku Studio — Build Progress

Generate, solve and play Sudoku in the terminal. Python standard library only.
Run `python sudoku.py` (menu) or `python sudoku.py --self-check`.

- [x] 1. Skeleton: grid parse/print, validity checks, backtracking solver, menu to solve a built-in or pasted puzzle, `--self-check`.
- [x] 2. Faster solver: candidate sets with constraint propagation (naked singles) + MRV cell choice; solution counter (stop at 2).
- [x] 3. Generator: random full grid, remove clues while keeping a unique solution; easy / medium / hard by clue count.
- [ ] 4. Interactive play mode: place/erase digits (`r c v`), conflict detection, pencil marks, win detection.
- [ ] 5. Hints & checking: logical hint (naked/hidden single, with explanation), mark mistakes against the solution.
- [ ] 6. Save / load games to a JSON file; resume; per-game timer and move count; undo.
- [ ] 7. Stats & leaderboard: best times and games won per difficulty, persisted.
- [ ] 8. Technique-based difficulty rater, import/export 81-char puzzle strings & files, README polish.
