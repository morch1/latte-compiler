## Latte to LLVM compiler

Compiler Construction class assignment

---

### Original README in Polish:

Rzeczy potrzebne do zbudowania projektu:
- python3.7
- clang
- llvm-as

Polecenie make:
- tworzy środowisko pythonowe w katalogu "venv"
- instaluje wszystkie potrzebne pakiety (requirements.txt)
- kompiluje src/lib/runtime.c (do lib/runtime.bc)

Skrypty latc i latc_llvm uruchamiają skrypt src/compiler.py przy
użyciu interpretera venv/bin/python i przekazują mu na wejście standardowe kod do
skompilowania/sprawdzenia.
Skompilowany kod jest wypisywany przez compiler.py na wyjście standardowe,
a skrypt latc_llvm zapisuje go do odpowiedniego pliku.

Biblioteka użyta do parsowania:
  https://github.com/dabeaz/ply

Optymalizacje na drzewie składni abstrakcyjnej:
- obliczanie wyrażeń logicznych gdzie to możliwe (np. 'true || a && b' -> 'true')
- obliczanie wyrażeń matematycznych nie korzystających ze zmiennych
- usuwanie gałęzi if jeśli warunek ma stałą wartość
- usuwanie kodu po instrukcji return
- usuwanie nieużywanych funkcji

Optymalizacje na kodzie LLVM:
- zamiana instrukcji alloca/store/load na operacje na rejestrach (kod w postaci SSA, copy propagation)
- obliczanie stałych wyrażen (constant folding)
- ...

Optymalizacje na kodzie LLVM można wyłączyć uruchamiając skrypt latc_llvm z opcją -noopts
  latc_llvm -noopts input.lat

Rzeczy dodane w 2. wersji:
- tablice i pętla for
- usprawnienie optymalizacji (m.in. usuwanie trywialnych instrukcji phi)

Struktura projektu:
  - src:
    - backend/
      - llvm/
        - __init__.py - definicje elementów składni LLVM
        - types.py - definicje typów LLVM
        - translator.py - tłumaczenie języka wejściowego na LLVM
        - optimizer.py - optymalizacje na kodzie LLVM
    - frontend/
      - __init__.py - definicje elementów drzewa składni abstrakcyjnej
        każdy element posiada funkcję check() sprawdzającą jego poprawność (typy, czy
        są zwracane wartości tam gdzie powinny itd) oraz wykonującą optymalizacje
      - types.py - definicje typów języka wejściowego
      - lexer.py, parser.py - parsowanie tekstu z wejścia
      - parsetab.py - plik wygenerowany przez ply
    - lib/
      - runtime.c - kod źródłowy pliku lib/runtime.bc
    - errors.py - definicje błędów
    - compiler.py - program główny
  - latc, latc_llvm - skrypty wywołujące compiler.py
