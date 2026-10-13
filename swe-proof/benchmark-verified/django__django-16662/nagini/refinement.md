# refinement.md — django__django-16662

The operation-by-operation correspondence between `model.py`'s implementation
(the `arrange_lines` impl region and the deep ordering key `compkey`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == the real callee by axiom_check.py / G-AX, NOT consumed), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The import-ordering site — `MigrationWriter.as_string`

Gold hunk (`django/db/migrations/writer.py:176-179`):
```
- sorted_imports = sorted(imports, key=lambda i: i.split()[1])
+ # First group the "import" statements, then "from ... import ...".
+ sorted_imports = sorted(
+     imports, key=lambda i: (i.split()[0] == "from", i.split()[1])
+ )
```

| # | model.py impl op (`arrange_lines`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `flags: List[int]`, `modules: List[int]` (the two key attributes of each line) | the elements of `imports` (import-statement `str`s) read by the key lambda via `i.split()[0]=="from"` and `i.split()[1]` | R | each `str` line ↔ the pair `(flag, module-code)` the key reads (mapping.md §2). The rest of the string never affects the order. |
| A2 | `compkey(flags[k], modules[k]) = flags[k]*1e9 + modules[k]` | the key `(i.split()[0]=="from", i.split()[1])` | R + A-reference | **R:** the tuple key `(bool, str)` ↔ the linearised int `compkey` (mapping.md §2: order-preserving because `0 ≤ module < 1e9`, group flag dominating). **A-reference:** that ascending `compkey` order == ascending real-tuple order is validated by G-AX against CPython tuple comparison + the real `sorted(key=...)`, NOT consumed as an axiom (mapping.md §3). |
| A3 | the arrangement: produce the permutation of the three keys that is ascending (`ToMS` preserved + `Result()[0] ≤ Result()[1] ≤ Result()[2]`), via the unrolled comparison sort | `sorted(imports, key=...)` | I | same operation — a comparison sort producing the ascending-by-key permutation. Keys of distinct lines are distinct (mapping.md §2), so the ascending permutation is unique; stability is unobservable and the unrolled three-element sort computes the same function as `sorted` on the modeled configuration. |
| A4 | (no node) | `"\n".join(sorted_imports)` and the surrounding `items["imports"]` / template fill (`writer.py:179` onward, unchanged) | I/omitted | the join and template are unchanged by the patch and are an order-preserving rendering of the arranged sequence; the F2P test observes the resulting substring, which is determined by the order A3 produces (mapping.md §1). |

The discriminating content of the change — the **group flag becomes the primary
ordering criterion** so plain `import` lines precede `from ... import` lines —
lives in `compkey`'s flag-dominating linearisation (`is_from*1e9`) consumed by
the ascending-order postcondition (A2+A3, model) ⇔ the added
`i.split()[0]=="from"` primary tuple component of the gold key (real). The
pre-patch key was `i.split()[1]` (module name only); `model_prepatch.py`
reproduces that (it arranges by the module code alone, ignoring the flag) and
**fails** the postcondition `Result()[0] <= Result()[1] <= Result()[2]`, which
is exactly the spec sensing the change (G-DIFF): on the F2P configuration a
from-line with a small module code (`django.db`) is placed before a plain-import
line with a larger module code (`time`), so the result is not ascending in
`compkey`.

## B. No consumed axioms

There is no `@ContractOnly` axiom. The only out-of-text trust point is the
**A-reference** of step A2 — that the deep linearised key `compkey` orders
identically to the real pair key, and that the real `sorted` with the gold key
produces the grouped order the model encodes. This is validated by
`axiom_check.py` / G-AX (mapping.md §3), not relied on as an axiom inside the
proof. There is therefore no dead axiom and no A-consumed row.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the ordering key gaining a primary group-flag component — is modeled
**deeply** (`compkey`'s flag-dominating linearisation, consumed by the ascending
postcondition), not hidden behind an axiom about the function under change. The
unchanged comparison engine `sorted` is the identical operation (I), and its
agreement with the deep key is the A-reference G-AX checks.

## D. verify(model) ⇒ resolved

`arrange_lines` verifies only if its output is the ascending-by-`compkey`
rearrangement of the three input keys (A3), and `compkey` places every plain
import before every from-import (A2). By R (string line ↔ (flag, module-code),
order-preserving module code, tuple ↔ linearised int) and I (`sorted` == the
ascending-permutation arrangement), the verified arrangement equals
`sorted(imports, key=(i.split()[0]=="from", i.split()[1]))` on the tested
configuration; by G-AX the linearisation matches the real tuple order and the
real `sorted` produces the same grouped sequence (A-reference). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited ordering reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: ordering-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
