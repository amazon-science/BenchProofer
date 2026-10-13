# refinement.md — sphinx-doc__sphinx-8621

Maps every op in `implementation_tokenizeKeystrokes` (Solution.lean) to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

The patch's single semantic op is: `parts = re.split(r'(?<=.)(-|\+|\^|\s+)(?=.)',
text)`. The impl's loop + `finalize` is a single-pass transliteration of that
regex's split semantics (the "deferred separator" tokenizer). Every op below is
therefore **R** (the regex is modeled by the explicit fold, related by the
`str ↔ List Char` / `list[str] ↔ List (List Char)` bijection of mapping.md) — no
op is A-tagged, so `conf_skip = false` and G-CONF differential-tests the whole
thing.

| # | impl op (Solution.lean) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut st := initState` | start of `re.split` over `text` | R | empty token list + empty buffer; the regex begins scanning at position 0 |
| 2 | `for c in text do step st c` | the regex engine scanning `text` left-to-right | R | one transition per character (`str ↔ List Char`, per-code-point) |
| 3 | `step` / `stepNoPend`: `!started → cur ++ [c]` | `(?<=.)` lookbehind: a match needs a char BEFORE the separator | R | the first character can never be an interior separator → kept as text |
| 4 | `step`: `pendSep`/`pendWs` committed when the NEXT char arrives | `(?=.)` lookahead: a match needs a char AFTER the separator | R | a separator candidate becomes a real boundary only once a following char exists |
| 5 | `pendWs (run ++ [c])` while `isWsChar c` | `\s+` greedy whitespace run | R | maximal whitespace munch; the run is one separator token |
| 6 | `isSepChar` = `c ∈ {-,+,^}`, `isWsChar` = `\s` minus `\n` | alternation `(-|\+|\^|\s+)` | R | separator alphabet (newline-free domain, mapping.md) |
| 7 | `finalize` `pendSep`/`pendWs len<2` → fold candidate back into `cur` | `(?=.)` fails at end-of-string: a trailing separator is not a boundary | R | trailing/standalone `-`,`+`,`^` or single trailing space stays in the keystroke token |
| 8 | `finalize` `pendWs len≥2` → `run.dropLast` is the sep, `[run.getLast!]` starts trailing token | `(?=.)` + greedy `\s+` backtracking at EOS: the run yields its last char to satisfy the lookahead | R | a multi-char trailing whitespace run splits off all but its last char |

**No changed-inexpressible op.** The whole regex behavior is modeled deeply (the
`step`/`finalize` fold). Validated exhaustively (≤6 chars) + 800k random
newline-free inputs == Python `re.split` in `conformance_check.py`.

**Prepatch (`Solution_prepatch.lean`).** Its impl transliterates the PRE-patch
regex `(-|\+|\^|\s+)` (no lookaround): every separator char and whitespace run
splits unconditionally. On `:kbd:`-`` it yields `["","-",""]` (the bug — a
separator framed by two empty keystrokes) and on `:kbd:`Alt+^`` it yields
`["Alt","+","","^",""]`, both disagreeing with `specSplit`, so its carried proof
cannot close (G-DIFF). This is the exact behavior the FAIL_TO_PASS tests
(`:kbd:`Alt+^``, `:kbd:`-``) catch.
