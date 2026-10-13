# refinement.md — sphinx-doc__sphinx-10466

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `publishPositions` `do` block, the deep `orderedPositions`/`toPos`/`posLe`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses
the axiom's `ensures`, **A-reference** where a deep model is validated == the
real callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs and this narrative are audited by **G-AX** / G-EQ.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The position-publishing site — `Catalog.__iter__` (`gettext.py:59-60`)

Gold hunk:
```
- positions = [(source, line) for source, line, uuid in self.metadata[message]]
+ positions = sorted(set((source, line) for source, line, uuid
+                        in self.metadata[message]))
```

| # | Solution.lean impl op (`publishPositions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `entries : List Entry` (`List (List Char × Int × List Char)`) | `self.metadata[message]`, a `List[Tuple[str, int, str]]` | R | each `(source, line, uuid)` ↔ `(source.toList, line, uuid.toList)` (mapping.md §2). The input list IS the recorded entries for one message. |
| A2 | `entries.map toPos` — keep `(e.1, e.2.1)`, drop the tag | the generator projection `(source, line) for source, line, uuid in …` | I | identical concrete projection: drop the `uuid`, keep `(source, line)`. The duplication the issue reports arises because distinct uuids made coincident positions distinct entries. G-CONF transliterates this op. |
| A3 | `(…).dedup` — keep one representative per distinct position | the `set(...)` wrapper | A-reference + I | the deduplication is modeled **deeply** (`List.dedup`); the equality `set(map(to_pos, entries)) == set(dedup(...))` (distinct positions exactly preserved) is the **A-reference** G-AX validates. The *order* dedup keeps is immaterial — the sort (A4) canonicalises it. mapping.md §3.1. |
| A4 | `(…).mergeSort posLe` — ascending under `posLe` | `sorted(...)` | A-reference + I | the stable-sort *primitive* `sorted` is unchanged; `mergeSort` is its analogue. Input is deduplicated (no ties), so the result is the unique ascending arrangement. The equality `mergeSort posLe == sorted` under the default tuple order is the **A-reference** G-AX validates (mapping.md §3.2). `posLe` (source lexicographic, then line) **is** Python's default tuple comparison — concrete, G-CONF-tested. |
| A5 | `out` returned (`List Pos`); `out.Nodup` | `positions`, later `Message(message, positions, uuids)` (`gettext.py:62`, unchanged) | R | `Message.__init__` stores `locations = positions` verbatim — identity on the position list. The F2P `test_Catalog_duplicated_message` asserts `msg.locations == [(...), ...]` exactly; the `out.Nodup` postcondition (R: distinctness) pins that no position repeats — the duplicate-removal the issue demands. |

Discriminating content of the change — coincident positions are collapsed to a
single entry AND the survivors are emitted in ascending order — lives in steps
A3 (`.dedup`) and A4 (`.mergeSort posLe`). The pre-patch emitted the raw
projection in insertion order (`[(source, line) for …]`), so it neither dropped
duplicates nor sorted; `Solution_prepatch.lean` reproduces that
(`entries.map toPos`) and **fails** `out = orderedPositions entries` (G-DIFF).
On the F2P scenario the bug is directly observable: pre-patch yields
`[('/path/to/filename',1), ('/path/to/filename',1), ('/path/to/filename',2),
('/path/to/yetanother',1)]` (a duplicate present), gold yields
`[('/path/to/filename',1), ('/path/to/filename',2), ('/path/to/yetanother',1)]`
(distinct, ascending) — exactly the asserted `msg1.locations`.

## B. The unchanged sibling — `uuids` and `Message(...)`

The statement `uuids = [uuid for source, line, uuid in self.metadata[message]]`
(`gettext.py:61`) and the `yield Message(message, positions, uuids)`
(`gettext.py:62`) are **UNCHANGED** by the gold patch. They are not modeled: the
fixed behavior the issue + F2P test observe is `Message.locations` (= `positions`)
only. `uuids` is observationally inert for the resolution (the F2P test asserts
`msg.text` and `msg.locations`, never `msg.uuids`). Modeling it would add no
discriminating power and is correctly omitted (directive 6: spec the touched
behavior, nothing more). mapping.md §1 records the binding for audit.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
publishing positions deduplicated and sorted instead of raw — is modeled
**concretely** in the `do` block (`map toPos`, `.dedup`, `.mergeSort posLe`, all
I ops differential-tested by G-CONF), not hidden behind an axiom. The only
A-reference legs (A3 dedup primitive, A4 sort primitive) cover **unchanged**
standard-library builtins (`set`, `sorted`), each validated against the real
callee by G-AX. There are **no consumed axioms**.

## D. verify(Solution) ⇒ resolved

`publishPositions` verifies only if its output equals `orderedPositions entries`
(A3/A4: the deduplicated positions in ascending order) and is duplicate-free
(A5 frame, `out.Nodup`). By R (`List[Tuple[str,int,str]]` ↔ `List Entry`,
`Message` identity on `locations`) the verified result equals the gold
`sorted(set((source, line) for source, line, uuid in self.metadata[message]))`
on the entries the catalog records; by G-AX the deep model's `.dedup` equals the
real `set` (A-reference) and `mergeSort posLe` equals the real `sorted`
(A-reference); by G-CONF the R/I transliteration of the project-dedup-sort logic
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited primitives — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: A-reference soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
