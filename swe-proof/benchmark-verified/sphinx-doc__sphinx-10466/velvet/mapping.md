# mapping.md — sphinx-doc__sphinx-10466

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = cab2d93076d0cca7c53fac885f927dde3e2a5fec`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each deep-model reference.

Repo file under change: `sphinx/builders/gettext.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `publishPositions (entries : List Entry)` | the per-message `positions = …` computation inside `Catalog.__iter__` — `sphinx/builders/gettext.py:59-60` | the modeled changed operation: produce the published list of positions for one message |
| `Entry` (`List Char × Int × List Char`) | one element of `self.metadata[message]`, a `Tuple[str, int, str]` `(source, line, uuid)` — `gettext.py:54` (`self.metadata[msg].append((origin.source, origin.line, origin.uid))`) | the recorded entry: source, line, identity tag |
| `Pos` (`List Char × Int`) | a `(source, line)` pair, the element type of `Message.locations` — `gettext.py:31` (`Message.__init__(text, locations, uuids)`) | a published position |
| `toPos (e)` | the generator projection `(source, line) for source, line, uuid in …` — `gettext.py:59` | pure spec: drop the identity tag, keep `(source, line)` |
| `lcharLt` | Python `str` `<` on the `source` component (code-point lexicographic) | pure spec: strict total order on source names |
| `posLe (x y)` | tuple comparison of `(source, line)` pairs (`<=`, lexicographic: source then line) — the order `sorted(...)` uses | pure spec: total order on positions |
| `orderedPositions (entries)` *(deep model — A-references for dedup + sort)* | `sorted(set((source, line) for source, line, uuid in self.metadata[message]))` — `gettext.py:59-60` post-patch | pure spec: the DISTINCT positions in ascending order; the `set(...)` dedup and `sorted(...)` sort are the unchanged builtins (A-references, G-AX); the projection `toPos` is concrete (G-CONF) |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): `[(source, line) for source, line, uuid in
self.metadata[message]]` (`gettext.py:59` pre-patch) — the raw projection in
insertion order, with no deduplication and no ordering.

Note: the sibling statement `uuids = [uuid for source, line, uuid in
self.metadata[message]]` (`gettext.py:61`) is UNCHANGED by the gold patch and is
not modeled — it is observationally inert for the fixed behavior (the F2P test
asserts only `msg.locations`, i.e. `positions`). See §2.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.metadata[message]`, a `List[Tuple[str, int, str]]` | `List Entry` = `List (List Char × Int × List Char)` | per element `(s, n, u)` ↔ `(s.toList, (n : Int), u.toList)`; list order ↔ `List` order |
| a Python `str` (a `source` / `uuid`) | `List Char` | `s` ↔ `s.toList`-shaped `List Char`; `str` `<` ↔ `lcharLt` (code-point lexicographic); empty `str` ↔ `[]` |
| a Python `int` line index | Lean `Int` | identity; `int` `<=` ↔ `Int` `≤` |
| a single character | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `(source, line)` 2-tuple | `Pos` = `List Char × Int` | componentwise; tuple `<=` ↔ `posLe` (source lexicographic, then line) |
| `Message(text, positions, uuids)` constructor (`gettext.py:62`) | omitted (only `positions` modeled) | the F2P test (`test_Catalog_duplicated_message`) asserts only `msg.locations` (= `positions`) and `msg.text`; `uuids` is the unchanged sibling statement, not part of the fixed behavior. `Message.__init__` stores `locations` verbatim — identity on the position list. |

`line` is modeled as `Int` (not `Nat`) because `origin.line` is a plain Python
`int` and the issue example shows line `0`; negative values never arise from the
real source but the carrier must not silently exclude any `int`. Lean `List Char`
indexing is total and sound; the carrier for source/uuid is `List Char` because
the order is a per-code-point string comparison.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There are **no consumed axioms** in this bundle. The operation under
specification is modeled deeply; two stdlib *primitives* it leans on are
A-references (the deep model is validated == the real callee by G-AX):

### 3.1 `(entries.map toPos).dedup` ↔ `set(...)` deduplication (A-reference)
**Callee:** Python `set(...)` over the projected `(source, line)` 2-tuples. The
gold patch wraps the generator in `set(...)` to collapse coincident positions
(the duplicate-locations the issue reports). `List.dedup` keeps one
representative of each distinct value; because the subsequent `sorted` imposes a
canonical order, the *order* in which `dedup` keeps representatives is immaterial
to the final result — only the resulting SET of positions matters. **G-AX**
asserts `set(map(to_pos, entries)) == set(model_dedup(map(to_pos, entries)))`
(equal as sets) on the F2P boundary plus 20 000 fuzzed entry lists, i.e. the
deduplication preserves exactly the distinct positions.

### 3.2 `… .mergeSort posLe` ↔ `sorted(...)` total-order sort (A-reference)
**Callee:** Python `sorted(...)` of `(source, line)` tuples under the default
tuple order (source lexicographic, then line). `List.mergeSort posLe` sorts under
the boolean comparator `posLe` realizing that same total order. Because the input
to the sort is already deduplicated (distinct positions), there are no tied keys
and the result is the unique ascending arrangement. **G-AX** asserts
`mergeSort posLe (model_dedup(map(to_pos, entries)))` (modeled in Python as
`sorted(set(...))`) equals the real `sorted(set((source, line) for source, line,
uuid in entries))` on the F2P scenario plus 20 000 fuzzed lists, INCLUDING lists
with duplicate entries (where the dedup is observable) and ties on the `source`
component (where the secondary `line` key decides).

**Soundness check (G-AX):** `axiom_check.py` imports only the Python standard
library (`set`, `sorted` — the very primitives the gold patch calls). Exit 0 iff
every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10466`** so the
consumer-side verdict (§11.3) is reproducible. The shadow is an INDEPENDENT
from-scratch transliteration of `publishPositions` (a hand-written `toPos`
projection, a from-scratch set-based dedup keeping first occurrence, and a
hand-written merge sort under `posLe`) — it does NOT call Python `sorted`/`set`
(those stay with G-AX as A-references). The oracle is `patch.diff`'s exact
expression `sorted(set((source, line) for source, line, uuid in entries))`. They
must agree on every input over ≥10⁵ fuzzed entry lists.
