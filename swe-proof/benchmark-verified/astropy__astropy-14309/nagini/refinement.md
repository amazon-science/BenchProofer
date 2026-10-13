# refinement.md — astropy__astropy-14309

The operation-by-operation correspondence between `model.py`'s implementation
(the `is_recognised_input` impl region, plus the deep `decided` reference in the
`pure` region) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — split into **A-consumed**, where
the proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The modeled site — `is_fits` (`astropy/io/fits/connect.py:48`)

The patch is a single hunk that rewrites the present-path branch from a
one-armed `if ... : return True` into a `return ...`:

```
     elif filepath is not None:
-        if filepath.lower().endswith(
+        return filepath.lower().endswith(
             (".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz")
-        ):
-            return True
+        )
     return isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))
```

After the change the present-path branch returns the suffix-test boolean
directly (TRUE *and* FALSE), so control no longer falls through to the
`isinstance(args[0], ...)` line when the suffix is unrecognised.

### A.1 The classification inputs

| # | model.py construct | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | param `stream_present: bool` | `fileobj is not None` (`connect.py:62`) | R | one None test ↔ one boolean bit (mapping.md §2). |
| A2 | param `sig_matches: bool` | `sig == FITS_SIGNATURE` (`connect.py:66`) | R | the stream branch's verdict, a leading-bytes comparison ↔ one boolean bit; unchanged by the patch. |
| A3 | param `path_present: bool` | `filepath is not None` (`connect.py:67`) | R | one None test ↔ one boolean bit. |
| A4 | param `path_recognised: bool` | `filepath.lower().endswith((".fits", ...))` (`connect.py:68-70`) | R | the suffix test ↔ one boolean bit; the exact suffix set and `str.lower()` are unchanged by the patch (mapping.md §2). |
| A5 | param `n_trailing: int >= 0` | `len(args)` — the trailing positional `*args` tuple | R | the count of trailing positional arguments; `args[0]` is in range iff `n_trailing >= 1`. |
| A6 | param `first_trailing_accepted: bool` | `isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))` (`connect.py:72`) | R | one isinstance test ↔ one boolean bit, meaningful only for `n_trailing >= 1` (the `Requires` domain fact). |

### A.2 The decision (the rewritten branch and the surviving cascade)

| # | model.py impl op (`is_recognised_input`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A7 | `if stream_present: if sig_matches: return R_TRUE() ; return R_FALSE()` | `if fileobj is not None: ... return sig == FITS_SIGNATURE` (`connect.py:62-66`) | I + R | identical control-flow guard; the branch returns the boolean `sig == FITS_SIGNATURE`, abstracted to `R_TRUE`/`R_FALSE` (R, mapping.md §2). Unchanged by the patch. |
| A8 | `if path_present: if path_recognised: return R_TRUE() ; return R_FALSE()` | `elif filepath is not None: return filepath.lower().endswith((...))` (post-patch `connect.py:67-70`) | I + R | the load-bearing step: the present-path branch returns its suffix boolean directly in **both** cases (`R_TRUE` when recognised, `R_FALSE` otherwise), exactly the patch's `return ...endswith(...)`. The pre-patch one-armed `if ...: return True` (no else) is reproduced verbatim only in `model_prepatch.py` (which therefore fails the spec — G-DIFF). |
| A9 | `if n_trailing == 0: return R_FAULT()` | the implicit out-of-range fault of `args[0]` when `args` is empty (`connect.py:72`) | I + R | indexing the first trailing argument when there is none is the `IndexError`; modeled as the `R_FAULT` sentinel. Reached (in both pre- and post-patch) only when neither stream nor path is present. The patch makes the present-path branch unable to reach this line; the model's post-patch impl returns inside the path branch so it likewise cannot reach it with `path_present` true. |
| A10 | `if first_trailing_accepted: return R_TRUE() ; return R_FALSE()` | `return isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))` (`connect.py:72`) | I + R | the trailing-argument verdict, an isinstance boolean ↔ `R_TRUE`/`R_FALSE`; unchanged by the patch and reached only for `n_trailing >= 1`. |

The branch guards (A7–A10) are evaluated in the same first-match order as the
real `if/elif/return` cascade; the model's `decided` pure function encodes that
exact order and the post-patch impl returns it (the `Result() == decided(...)`
postcondition). Because the present-path branch in `decided` returns a definite
boolean (`R_TRUE`/`R_FALSE`) and never `R_FAULT`, the spec pins the load-bearing
property of the patch: a present path name yields a total boolean verdict
without consulting the trailing arguments (postconditions B below).

## B. The discriminating content (what G-DIFF senses)

The change's whole effect is: when a path name is present, the predicate must
return a definite boolean computed solely from the suffix test — and in
particular, an unrecognised present path with no trailing argument must return
`FALSE` rather than falling through to index the (empty) trailing-argument tuple
and faulting.

- model.py postconditions:
  `Implies(not stream_present and path_present and not path_recognised, Result() == R_FALSE())`
  and `Implies(not stream_present and path_present, Result() != R_FAULT())`.
- `model_prepatch.py` reproduces the pre-patch one-armed branch (`if
  path_recognised: return R_TRUE()` with no `else`) and therefore, for a present
  but unrecognised path with `n_trailing == 0`, falls through and returns
  `R_FAULT()`, FAILING `Result() == decided(...)` (which requires `R_FALSE`).
  The verifier reports exactly this postcondition.
- The F2P test `test_is_fits_gh_14305` is precisely this case:
  `connect.is_fits("", "foo.bar", None)` — no stream (`fileobj=None`), a present
  path with an unrecognised suffix (`"foo.bar"`), and no trailing argument
  (`args == ()`) — must return `False` (post-patch) instead of raising
  `IndexError` (pre-patch).

## C. No kind-3 (unexpressible-changed-op) steps; no consumed axiom

Every step above is R or I. The changed operation — a control-flow decision
over boolean classification bits and an argument count — is modeled **deeply**:
the cascade is spelled out in the impl and in the `decided` reference, with no
opaque callee consumed inside an `Ensures`. There is therefore **no
`@ContractOnly` axiom** (A-consumed) and **no A-reference deep model of a stdlib
callee**: the `axioms` region is empty. The booleans the cascade branches on are
R-refinements of unchanged predicate evaluations (`is not None`, `==`,
`str.endswith`, `len`, `isinstance` — A1–A6), not axiomatized callees.
`axiom_check.py` (G-AX) instead validates that the real `is_fits` produces the
model's decided verdict on the F2P input and on a fuzz of the classification
configurations (decision-equivalence).

## D. verify(model) ⇒ resolved

`is_recognised_input` verifies only if it TERMINATES (the
`Requires(MustTerminate(2))` obligation — the real predicate is a straight-line
cascade that always answers, and a diverging body meeting the value
postconditions vacuously is rejected) and its result equals the first-match
cascade `decided`, whose present-path branch is a total boolean
(`R_TRUE`/`R_FALSE`, never `R_FAULT`) — so a verifying impl, when a path name
is present, returns the suffix verdict directly and never indexes an absent
trailing argument, exactly the gold patch's behaviour (A7–A10). By R (each boolean ↔ its runtime predicate;
`R_TRUE`/`R_FALSE` ↔ the `bool` returns; `R_FAULT` ↔ the `IndexError` the patch
eliminates, mapping.md §1–§2) the verified decision equals the gold patch's
post-rewrite cascade on the tested inputs, and the gold patch resolves
(G-RESOLVE). The only trust point is refinement fidelity (this document, G-EQ);
there is no axiom-soundness trust point because no axiom is consumed (G-AX
reduces to the executable decision-equivalence check).
