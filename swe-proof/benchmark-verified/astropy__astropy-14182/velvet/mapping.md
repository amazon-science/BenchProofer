# mapping.md — astropy__astropy-14182

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a5917978be39d13cd90b517e1de4e7a539ffaa48`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo file under change: `astropy/io/ascii/rst.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `surroundWithRuler (lines : List (List Char)) (headerRowCount : Nat)` | `RST.write(self, lines)` — `astropy/io/ascii/rst.py:63` | modeled changed function: frames the rendered table lines with the ruler line. Models the body `idx = len(self.header.header_rows); lines = [lines[idx]] + lines + [lines[idx]]` (post-patch). |
| `dataStartOffset (headerRowCount : Nat)` | `RST.read(self, table)` — `astropy/io/ascii/rst.py:71` (added by the patch) | modeled changed function: the data start-line index. Models `self.data.start_line = 2 + len(self.header.header_rows)` (post-patch). |
| `lines` parameter of `surroundWithRuler` | the `lines` argument of `RST.write` — the output of `super().write(lines)` (`FixedWidth`→`Basic`→`BaseReader.write`, `core.py:1535`) | the rendered table: header rows, then the column-extent ruler line, then data lines |
| `headerRowCount` | `len(self.header.header_rows)` — the number of header rows requested for this writer/reader (`FixedWidth.__init__`, `fixedwidth.py:347-354`; default `["name"]` ⇒ 1) | the count both modeled behaviours key off of |

### Why these two functions

The patch makes three edits to `rst.py`:

1. `RST.__init__` gains a `header_rows=None` parameter forwarded to
   `super().__init__(..., header_rows=header_rows)` (`fixedwidth.py:339`). This is
   **pure plumbing** — it threads the new keyword into the already-existing
   `FixedWidth.__init__` parameter, which stores it on `self.header.header_rows`
   / `self.data.header_rows`. It introduces no new observable computation of its
   own; it merely makes `len(self.header.header_rows)` configurable. It is an
   **R/plumbing** step (refinement.md), not separately modeled. The previously
   crashing call `RST(header_rows=[...])` (the `TypeError` in the issue) is fixed
   by this thread-through; the *behaviour* the F2P test then observes is entirely
   in `write` and `read` below.
2. `RST.write`: `[lines[1]] + lines + [lines[1]]` → `idx = len(self.header.header_rows); [lines[idx]] + lines + [lines[idx]]`.
   Modeled by `surroundWithRuler`.
3. `RST.read` (new) + the removal of the class attribute `SimpleRSTData.start_line = 3`:
   the data start line becomes `2 + len(self.header.header_rows)` instead of the
   hard-wired class default `3`. Modeled by `dataStartOffset`.

The removal of `SimpleRSTData.start_line = 3` and the addition of `RST.read`
are two faces of the *same* change: where the data start index used to be the
fixed constant `3` (correct only for a single `"name"` header row: 2 ruler lines
+ 1 header line), it is now computed as `2 + len(header_rows)`. `dataStartOffset`
models that index.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `lines : list[str]` (the rendered table lines) | `List (List Char)` | `[s0, s1, …]` (Python list of str) ↔ `[s0.toList, s1.toList, …]`; `len(lines)` ↔ `lines.length`; `lines[k]` ↔ `lines[k]!` (in range by `require`); list concat `a + b` ↔ `a ++ b`; one line `str` ↔ `List Char` |
| `idx = len(self.header.header_rows)` (a non-negative count) | `headerRowCount : Nat` | `len(...)` ↔ the `Nat`; the post-patch index `lines[idx]` ↔ `lines[headerRowCount]!`; `2 + len(...)` ↔ `2 + headerRowCount` |
| `self.data.start_line` (an `int` line index) | `Nat` | the computed start-line index; non-negative for all reachable configurations (`len(header_rows) ≥ 0`) |
| `self.header.header_rows` (a `list`, default `["name"]`) | abstracted to its **length** `headerRowCount` | only the *count* of header rows is observed by these two index computations; the row identities are irrelevant to the framing position and the start offset, so the list is abstracted to its length (the single integer the real code reads via `len(...)`). |

`require headerRowCount < lines.length` mirrors the real precondition that the
ruler line exists at position `len(header_rows)` in `super().write`'s output: a
fixed-width simple-table rendering emits the header rows first, then the ruler
line, so `len(lines) ≥ len(header_rows) + 1 > len(header_rows)`. G-CONF only
feeds inputs that satisfy this (it constructs real renderings).

Lean `List` indexing with `[_]!` is total; the `require` guarantees the index is
in range so `[_]!` agrees with Python's `lines[idx]` (no out-of-range default).

## 3. Callee provenance (kind-A) — none

There are **no axiomatized callees and no deep-model references** in this bundle.
Both modeled functions are changed functions whose new behaviour is a single
closed-form expression of the inputs:

- `surroundWithRuler` = a positional pick (`lines[headerRowCount]!`) and two list
  concatenations (`++`) — concrete R/I ops (refinement.md), transliterated by
  G-CONF.
- `dataStartOffset` = an integer expression `2 + headerRowCount` — a concrete I
  op, transliterated by G-CONF.

The callees the changed functions invoke — `super().write` (which produces
`lines`) and `super().read` / `FixedWidth.__init__` (which consume the start
index / store `header_rows`) — are **unchanged** and supply or consume the values
modeled as inputs. They are R-refinements (an input already holds the rendered
lines / the header-row count), not callees whose contract the proof assumes.
Hence `axioms` is empty, `axiom_check.py` is a no-op stub (`status=skip`), and
G-AX is `skip` (consistent with the django-13794 axiom-free exemplar).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14182`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`surroundWithRuler` and `dataStartOffset` (all R/I ops) to Python and compares
against `patch.diff`'s behaviour: the patched `RST.write` (driven through a real
`QTable.write(format="ascii.rst", header_rows=...)`) and the patched data
start-line index (read back via `QTable.read`). There are no A-tagged callees to
leave as the real callee.
