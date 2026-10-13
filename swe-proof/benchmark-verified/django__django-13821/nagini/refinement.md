# refinement.md — django__django-13821

The operation-by-operation correspondence between `model.py`'s implementation
(the `check_supported_version` impl region and the deep `lt_lex` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The version-guard site — `check_sqlite_version()` (`django/db/backends/sqlite3/base.py:66-68`)

Gold hunk:
```
 def check_sqlite_version():
-    if Database.sqlite_version_info < (3, 8, 3):
-        raise ImproperlyConfigured('SQLite 3.8.3 or later is required (found %s).' % Database.sqlite_version)
+    if Database.sqlite_version_info < (3, 9, 0):
+        raise ImproperlyConfigured(
+            'SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version
+        )
```

| # | model.py impl op (`check_supported_version`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | `Requires(MustTerminate(2))` + the loop's `Invariant(MustTerminate(m - i + 1))` | the guard is straight-line bounded code (one tuple comparison + optional raise): it always terminates | R | total-correctness obligation. The real `check_sqlite_version()` runs at import time and always either returns or raises; a diverging model impl would satisfy the value postconditions only vacuously (the partial-correctness gap a G-EQ audit demonstrated: a same-spec impl that hangs on the reject path verified, and its faithful patch `while True: pass` hung the F2P test — NOT resolved). `MustTerminate` pins termination; the comparison loop discharges it with the strictly decreasing measure `m - i`. |
| A1 | parameter `version: List[int]` | `Database.sqlite_version_info` (a tuple of ints) read inside the guard | R | `tuple` of ints ↔ `List[int]` of release components (mapping.md §2). Read-only ⇒ `Acc(list_pred(version), 1/2)`. |
| A2 | `mn = [3, 9, 0]` / `min_version() == PSeq(3, 9, 0)` | the literal `(3, 9, 0)` | I | identical concrete constant — the supported minimum. (This constant IS the behavioural delta; the pre-patch image used `(3, 8, 3)`.) |
| A3 | `below = lt_lex(ToSeq(version), min_version())` computed by the verified loop | `Database.sqlite_version_info < (3, 9, 0)` | A-reference | the comparison operation is modeled **deeply**: `lt_lex` (the spelled-out component-wise fold in the `pure` region) and the verified loop in `check_supported_version` ARE the lexicographic strict-less. There is no consumed comparison axiom — the proof never depends on one. Instead the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs Python's tuple `<` on boundary + 50k fuzz and asserts `lt_lex(a, b) == (tuple(a) < tuple(b))`. Python tuple `<` IS the lexicographic order `lt_lex` encodes (mapping.md §3.1). |
| A4 | `if below: raise UnsupportedConfiguration()` + the `Exsures` clause `lt_lex(ToSeq(version), min_version())`; else normal return under `not lt_lex(...)` | `if ... : raise ImproperlyConfigured('SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version)` | R | the *condition and fact* of the raise are identical (raise iff strictly below the minimum). `ImproperlyConfigured` ↔ `UnsupportedConfiguration` (a builtin/3rd-party exception in an `Exsures` crashes the translator; mapping.md §2). The message string is a presentation of the same minimum + the runtime's `sqlite_version`, carrying no behaviour beyond the reject condition the contract pins (mapping.md §4) — the F2P test's message change is entirely driven by the `(3,9,0)` threshold A2 captures. |

The discriminating content of the change — the minimum bumped from `(3, 8, 3)`
to `(3, 9, 0)` — lives in `min_version() == PSeq(3, 9, 0)` (model, frozen spec)
⇔ the `< (3, 9, 0)` literal of the gold patch (real). A runtime `(3, 8, 11, 1)`
is `>= (3, 8, 3)` (the old guard accepted it — the bug) but `< (3, 9, 0)` (the
new guard rejects it). `model_prepatch.py` reproduces the old threshold (its
impl compares against `[3, 8, 3]`) and **fails** the `Exsures` postcondition
`lt_lex(ToSeq(version), min_version())`, which is exactly the spec sensing the
change (G-DIFF): for `(3, 8, 11, 1)` the pre-patch impl returns normally while
the spec demands the raise.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — which minimum the runtime is compared against — is the literal
constant `min_version()` (step A2, **I** against the gold literal `(3, 9, 0)`),
and the comparison that consumes it is modeled **deeply** (the spelled-out
component-wise fold `lt_lex`, step A3, an **A-reference**), not hidden behind an
axiom about the operation under change. There is **no consumed `@ContractOnly`
axiom** in this bundle: the only callee, Python's tuple `<`, is unchanged and is
the **A-reference** that G-AX validates the deep model against.

## C. verify(model) ⇒ resolved

`check_supported_version` verifies only if it TERMINATES on every input (the
`MustTerminate(2)` precondition — no vacuous satisfaction via divergence, A0)
and raises on EXACTLY the runtimes strictly below `(3, 9, 0)` (the `Exsures`
condition) and returns normally on EXACTLY those at or above it (the
normal-return `Ensures`). By A3 (G-AX) the
deep model `lt_lex` equals Python's real tuple `<`; by R (tuple ↔ List[int],
`ImproperlyConfigured` ↔ `UnsupportedConfiguration`) and I (the `(3, 9, 0)`
constant, the raise-iff-below control flow) the verified guard equals
`if Database.sqlite_version_info < (3, 9, 0): raise ImproperlyConfigured(...)`
on the tested version tuples — in particular it rejects the F2P version
`(3, 8, 11, 1)` and accepts `(3, 9, 0)`. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
G-AX-audited comparison — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: the A-reference soundness (G-AX, the
`lt_lex == tuple <` check) and refinement fidelity (this document, G-EQ).
