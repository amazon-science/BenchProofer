# mapping.md — django__django-16662

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0eb3e9bd754e4c9fac8b616b705178727fc8031e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each deep-model reference.

Repo file under change: `django/db/migrations/writer.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `orderImportLines (imports : List (List Char))` | the import-line ordering step inside `MigrationWriter.as_string` — `django/db/migrations/writer.py:176-178` (the `sorted_imports = sorted(imports, key=…)` statement) | the modeled changed operation: produce the ordered list of import-statement lines |
| `firstTok` / `afterFirst` / `moduleTok` *(deep model — A-reference)* | `str.split()` selection of token 0 / token 1 (`i.split()[0]`, `i.split()[1]`) — `writer.py:178` | pure spec: the leading whitespace-delimited token, and the module token; deep model of the unchanged builtin `str.split`, validated `== str.split()` by axiom_check.py (G-AX), NOT a consumed axiom |
| `isQualified (l)` | the predicate `i.split()[0] == "from"` — `writer.py:178` (post-patch key, first component) | pure spec: line names objects from a module (vs. a whole module) |
| `lcharLe` | Python `str` comparison of the module token (`<=`, code-point lexicographic) | pure spec: total order on module tokens |
| `keyLe (x y)` | the composite key `lambda i: (i.split()[0] == "from", i.split()[1])` ordering — `writer.py:178` post-patch | pure spec: the CHANGED comparison (group whole-module lines first, then by module token); concrete, differential-tested by G-CONF |
| `sortImports (l)` *(deep model — A-reference for the sort primitive)* | `sorted(imports, key=…)` — `writer.py:178` | pure spec: the stable key-sort; the stable-sort *primitive* `sorted` is the unchanged builtin (A-reference, G-AX checks `mergeSort keyLe == sorted` under the composite key); the *key logic* `keyLe` is the changed behavior (concrete, G-CONF) |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): `sorted(imports, key=lambda i: i.split()[1])`
(`writer.py:178` pre-patch) — module-token only, with no grouping.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an import-statement line, a `str` (e.g. `"import datetime"`, `"from django.db import migrations, models"`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; single space `' '` is the token delimiter; `str` `<=` ↔ `lcharLe` (code-point lexicographic) |
| the collection of import lines (`imports`, a Python `set[str]`) | `List (List Char)` | order-insensitive on input (a set); G-CONF feeds list inputs (incl. duplicates) so the stable-sort primitive is exercised on arbitrary multiplicities. The frozen postcondition `out ~ imports` (`List.Perm`) pins that no line is dropped, added, or fabricated — the `mut`-frame analogue (directive 5). |
| `i.split()[0]`, `i.split()[1]` | `firstTok l`, `moduleTok l` | the writer emits single-space-separated lines, so whitespace `str.split()` of tokens 0/1 equals taking chars up to / between single spaces. G-AX validates this equality on 20 007 real-shaped lines. |
| a single character | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the keys are per-code-point token comparisons.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There are **no consumed axioms** in this bundle. The operation under
specification is modeled deeply; two stdlib *primitives* it leans on are
A-references (the deep model is validated == the real callee by G-AX):

### 3.1 `firstTok` / `moduleTok` deep model ↔ `str.split()` (A-reference)
**Callee:** Python `str.split()` (whitespace split), tokens 0 and 1. The writer
constructs each import line with a single space between tokens
(`"import %s"`, `"from %s import %s"`, `"from django.db import migrations, models"`),
so the first whitespace token is the leading keyword (`import`/`from`) and the
second is the module. `firstTok`/`moduleTok` compute exactly those by scanning
to single-space delimiters. **G-AX** asserts
`firstTok line == line.split()[0]` and `moduleTok line == line.split()[1]` on
the F2P boundary lines plus 20 000 fuzzed import lines.

### 3.2 `sortImports` deep model ↔ `sorted` stable key-sort (A-reference)
**Callee:** Python `sorted(seq, key=…)`, a STABLE sort. `sortImports` is
`List.mergeSort keyLe`, also a stable sort, under the boolean comparator
`keyLe` that realizes the composite key `(isQualified, moduleTok)`. **G-AX**
asserts `mergeSort keyLe` (modeled in Python as `sorted(lines, key=lambda i:
(is_qualified(i), module_tok(i)))`, a stable sort under the same total preorder)
equals the real `sorted(lines, key=lambda i: (i.split()[0]=="from",
i.split()[1]))` on the F2P scenario plus 20 000 fuzzed lists, INCLUDING lists
with duplicate / tied keys (where stability is observable). The *key logic*
itself (the changed behavior) is not an axiom — it is concrete and is the leg
G-CONF differential-tests.

**Soundness check (G-AX):** `axiom_check.py` imports only the Python standard
library (`str.split`, `sorted` — the very primitives the gold patch calls).
Exit 0 iff every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16662`** so the
consumer-side verdict (§11.3) is reproducible. The shadow is an INDEPENDENT
from-scratch transliteration of `orderImportLines` (a hand-written stable merge
sort under `keyLe`, with from-scratch `firstTok`/`moduleTok`/`lcharLe`) — it
does NOT call Python `sorted`/`str.split` (those stay with G-AX as A-references).
The oracle is `patch.diff`'s exact sort expression. They must agree on every
input over ≥10⁵ fuzzed lists.
