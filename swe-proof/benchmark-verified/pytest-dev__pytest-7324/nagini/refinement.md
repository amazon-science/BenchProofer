# refinement.md — pytest-dev__pytest-7324

The operation-by-operation correspondence between `model.py`'s implementation
(the `encode_ident` and `lookup_key` impl regions, the deep `strip_sentinel`
model, and the live `match` axiom) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The gold patch has three hunks: (h0) introduce the one-code-point prefix
constant `IDENT_PREFIX = "$"`; (h1) site 1 — `not_expr` builds
`ast.Name(IDENT_PREFIX + ident.value, ast.Load())`; (h2) site 2 —
`MatcherAdapter.__getitem__` returns `self.matcher(key[len(IDENT_PREFIX):])`.

## A. Site 1 — the name placed into the program (`encode_ident` ↔ `not_expr`)

Gold hunks h0 + h1:
```
+ IDENT_PREFIX = "$"
  ...
- return ast.Name(ident.value, ast.Load())
+ return ast.Name(IDENT_PREFIX + ident.value, ast.Load())
```

| # | model.py impl op (`encode_ident`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `ident: List[int]` | `ident.value: str` (the scanned identifier) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `result = [sentinel()]` (start with the single code point `36`) | the `IDENT_PREFIX` literal `"$"` (`ord("$") == 36`, length 1) prepended via `IDENT_PREFIX + …` | R + I | the prefix is the one code point U+0024; `[36]` ↔ `"$"`. `sentinel() == 36` is pinned to the real `IDENT_PREFIX` by axiom_check.py (asserts `IDENT_PREFIX == "$"`). |
| A3 | the loop appends every `ident[i]`, yielding `ToSeq(Result()) == PSeq(sentinel()) + ToSeq(ident)` | `IDENT_PREFIX + ident.value` (string concatenation) | R | list `+` ↔ `str` `+` under the carrier; the model spells the concatenation out as a verified loop so a single fold/unfold is available. |
| A4 | the result `List[int]` is the `Name.id` content | `ast.Name(<that string>, ast.Load())` | R | only the `id` field changes; `ast.Load()` and the node wrapper are constant and observation-irrelevant (mapping.md §2 — the AST node is modeled by its `id`). |

The discriminating content of the change lives in the postconditions
`ToSeq(Result()) == PSeq(sentinel()) + ToSeq(ident)` together with
`ToSeq(Result())[0] != 84/70/78` (the first code points of `True`/`False`/
`None`): the emitted name begins with the sentinel, hence is a **legal program
name** and is never one of the three reserved constant spellings. The pre-patch
`not_expr` emitted the bare identifier; `model_prepatch.py` reproduces that
(`result = []`, no sentinel) and **fails** the postcondition
`ToSeq(Result()) == PSeq(sentinel()) + ToSeq(ident)` (and, for a reserved-word
identifier, the `!= 84/70/78` safety clauses) — exactly the spec sensing the
change (G-DIFF). This is the bug the F2P tests `test_valid_idents[True/False/
None]` exercise: pre-patch `compile()` rejects the bare `ast.Name("True")`
(CPython 3.8+: `ValueError`, debug-build abort), so those tests fail.

## B. Site 2 — the membership lookup (`lookup_key` ↔ `MatcherAdapter.__getitem__`)

Gold hunk h2:
```
- return self.matcher(key)
+ return self.matcher(key[len(IDENT_PREFIX) :])
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `key: List[int]`, `Requires(key[0] == sentinel())` | `key: str` (the program name being looked up — always a prefixed name) | R | `str` ↔ `List[int]`; the precondition records that every name the program contains carries the sentinel (it was emitted by site 1). |
| B2 | `recovered` built from `key[1:]` (the loop drops index 0), `strip_sentinel(ToSeq(key)) == ToSeq(key).drop(1)` | `key[len(IDENT_PREFIX):]` — slice off the prefix | R + I | `len(IDENT_PREFIX) == 1`, so the slice removes exactly one leading code point; `drop(1)` ↔ `[1:]`. The model spells the slice out as a verified loop. |
| B3 | `match(ToSeq(recovered))` | `self.matcher(<de-prefixed key>)` | A-consumed | `match` is the weakest contract on the unchanged user predicate the spec needs: a deterministic `str -> bool` function (mapping.md §3.1). The proof consumes its result as `lookup_key`'s return value. G-AX confirms the real predicate is consulted on the recovered identifier. |

The pre-patch `__getitem__` returned `self.matcher(key)` — the raw, prefixed
name. `model_prepatch_2.py` reproduces that (`return match(ToSeq(key))`) and
**fails** the postcondition `Result() == match(strip_sentinel(ToSeq(key)))`:
the predicate would be asked about `"$True"` rather than `"True"`, so the F2P
matcher `{"True": True}.__getitem__` would `KeyError`. The strip exists precisely
to invert the prepend so the predicate sees the original identifier (G-DIFF).

## C. The two sites are inverse (the round-trip property)

`encode_ident`'s postcondition `strip_sentinel(ToSeq(Result())) == ToSeq(ident)`
is the lemma tying the two changed sites: prepend-then-strip is the identity on
every identifier. This is what guarantees the membership predicate is always
consulted on the identifier the user wrote — including the three reserved
spellings, which now (a) compile (site 1 safety) and (b) match correctly
(site 2 strip). Both sites are needed and each has its own failing
`model_prepatch` (sites are independently observable).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The two operations that genuinely
*changed* — the prefix prepend (site 1) and the prefix strip (site 2) — are
modeled **deeply** (the spelled-out loops in `encode_ident`/`lookup_key` and the
`strip_sentinel` pure function), not hidden behind an axiom about the functions
under change. They are tagged **A-reference**: G-AX (axiom_check.py) validates
the deep models == the real `not_expr` / `MatcherAdapter.__getitem__`. The only
**consumed** axiom, `match` (B3), covers the **unchanged** user predicate the
new code invokes.

## E. Termination obligation (liveness)

Both contracted functions additionally carry `Requires(MustTerminate(2))` and
their loops carry `Invariant(MustTerminate(<bound> - i))` (a strictly
decreasing, bounded-below measure). The value pins alone are partial-
correctness facts: without a termination obligation, an implementation that
never returns (an unbounded loop or unbounded self-recursion) would discharge
every postcondition vacuously and yet its faithful real counterpart would hang
or exhaust the recursion limit under the tests. The obligation makes the spec
demand that the emitted name and the lookup answer are actually **delivered**,
matching the real code: both changed callees are straight-line/`O(len)`
operations that always return. This is a liveness fact of the gold behaviour,
not an over-tightening.

## F. verify(model) ⇒ resolved

`encode_ident` verifies only if its output equals `sentinel ++ ident` with the
first code point `36` (≠ the reserved-word initials), and `lookup_key` verifies
only if it forwards the de-prefixed key to the predicate; the round-trip clause
ties them. Both must moreover terminate (§E), so a verifying implementation
actually produces its answer in finite time. By R (`str` ↔ `List[int]`, the one-code-point `"$"` prefix, the
`ast.Name`-by-`id` abstraction) the verified pair equals
`ast.Name("$"+ident, Load())` / `self.matcher(key[1:])` on the tested inputs;
by G-AX the deep models equal the real `not_expr` / `__getitem__`
(A-reference) and the real predicate meets the `match` axiom it stands in for
(A-consumed). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
