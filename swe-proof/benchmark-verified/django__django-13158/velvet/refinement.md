# refinement.md — django__django-13158

Maps every operation in the `emptyCombined` `do` block to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `set_empty` (the observable fix)

Post-patch repo code (`patch.diff`, `django/db/models/sql/query.py`):
```python
def set_empty(self):
    self.where.add(NothingNode(), AND)
    for query in self.combined_queries:
        query.set_empty()
```

Lean impl (`emptyCombined`, the backward `while`-loop skeleton of the `for`):
```lean
let mut result : List Branch := []
let mut i := q.branches.length
while i > 0 …
  let b := q.branches[i - 1]!
  result := silence b :: result
  i := i - 1
return { topSilenced := true, branches := result }
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `q : Combined`, field `branches : List Branch` | `self` Query, attribute `self.combined_queries` (a tuple of operand `Query`s) | **R** | rich object → `structure` carrying only the touched observations: `combined_queries` ↔ `branches`. A `Query` operand ↔ `Branch` (its row source + whether it has been forced empty). mapping.md §2. |
| 2 | `{ topSilenced := true, … }` | `self.where.add(NothingNode(), AND)` — the combined query's OWN top-level row source is forced empty | **R** | adding a `NothingNode` to `self.where` ↔ setting `topSilenced := true`. This is the UNCHANGED pre-existing first line of `set_empty`; it does not by itself stop the operands (see `combinedRows`, which ignores `topSilenced` once there are branches). |
| 3 | `while i>0 … result := silence b :: result …` over every `b` | `for query in self.combined_queries: query.set_empty()` — **this is the added fix** | **I** | the per-operand recursive empty. Modeled as the M1 front-recursive fold `silenceAll` (each operand silenced, order preserved) realized by a backward accumulator `while`. `set_empty` on an operand forces its row source empty ↔ `silence b = {b with silenced := true}`. (One modeled level of operands: the F2P union is one level deep; deeper nesting silences identically by the same fold.) |
| 4 | `silence b = { b with silenced := true }` (preserves `b.rows`) | `query.set_empty()` adds a `NothingNode` to that operand's `where`, forcing it empty without dropping its other state | **I** | the operand keeps its identity/rows; only its emptiness flips. directive-5 frame: the `rows` field is pinned equal (via `out.branches = silenceAll q.branches`), nothing is left free. |

The `ensures combinedRows out.branches = []` is the **bug-discriminating** clause:
post-patch every operand is silenced so the combined row set is empty; the
prepatch leaves the operands untouched, so `combinedRows q.branches ≠ []` and its
carried proof cannot close (G-DIFF).

## Coupled aliasing fix: `clone` (tag I, non-modeled — the directive-5 frame)

Post-patch `clone` adds:
```python
obj.combined_queries = tuple(query.clone() for query in self.combined_queries)
```

| patch.diff op | tag | justification |
|---|---|---|
| `clone`: deep-clone `combined_queries` instead of sharing them | **I** (non-modeled, aliasing bridge) | Pure Python aliasing repair: `QuerySet.none()` does `clone = self._chain(); clone.query.set_empty()`. Pre-patch, `clone()` shallow-copies the dict, so the clone SHARES the original's `combined_queries` objects; `set_empty` then mutates them in place, corrupting the original (and, before fix #3, the clone still returned everything). Lean is referentially transparent — `emptyCombined : Combined → Combined` returns a FRESH value and provably cannot mutate its input `q` (which is not `mut`). So the value-semantics model already embodies the post-clone invariant "the original combined queryset is unchanged"; there is no aliasing to express. The clone edit is the Python-side bridge that makes the real code match value semantics. It is carried in `patch.diff` verbatim so G-RESOLVE passes, and its observable effect (the original queryset still yields all rows after `.none()`) is checked end-to-end by G-CONF's directive-5 frame assertion. |

## Soundness check (verify ⟹ correct)

- `emptyCombined`'s postconditions pin behavior EXACTLY: `out.topSilenced = true`
  (the unchanged first line), `out.branches = silenceAll q.branches` (every
  operand silenced, `rows` preserved — directive-5 frame, no free component), and
  `combinedRows out.branches = []` (the input-grounded discriminator — directive
  8: dischargeable only by actually silencing every operand, never by echoing an
  oracle). No wrong impl of the modeled behavior satisfies all three.
- The prepatch impl (only `topSilenced := true`, operands untouched) violates
  clauses 2 and 3 (`combinedRows q.branches = []` and
  `q.branches = silenceAll q.branches` are both unprovable), so its carried proof
  cannot close (G-DIFF/G-PANEL).
- All impl-region ops are **R/I** — NO A-tagged (axiom) content, so the impl is
  NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py` mechanically
  differential-tests the R/I shadow (`.none()` empty + original unchanged)
  against the real patched `union`/`none` over ≥10⁵ fuzzed inputs.
