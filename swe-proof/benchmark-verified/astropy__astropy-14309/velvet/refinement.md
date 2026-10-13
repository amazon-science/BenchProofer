# refinement.md — astropy__astropy-14309

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `classifyFitsOrigin` `do` block and the deep `hasKnownExt` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The classifier — `is_fits()` (`astropy/io/fits/connect.py:48`)

Gold hunk (the only behavioural change):
```
-        if filepath.lower().endswith(
+        return filepath.lower().endswith(
             (".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz")
-        ):
-            return True
+        )
     return isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))
```
Pre-patch: the path branch returns `True` only when the extension matches and
otherwise falls THROUGH to `return isinstance(args[0], …)`, which raises
`IndexError` when `*args` is empty. Post-patch: the path branch returns the
extension test's boolean OUTRIGHT, so a present path never reaches `args[0]`.

| # | Solution.lean impl op (`classifyFitsOrigin`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `match stream with \| some s => Except.ok s` | `if fileobj is not None: … return sig == FITS_SIGNATURE` | R + I | `fileobj` present ↔ `some`; the branch's only observation is the boolean `sig == FITS_SIGNATURE`, carried as `s` (mapping.md §2). UNCHANGED by the patch; transliterated by G-CONF. |
| A2 | `\| none => match path with \| some p => Except.ok (hasKnownExt p)` | `elif filepath is not None: return filepath.lower().endswith((...))` (POST-patch) | R + A-reference | this is the changed control flow: a present path yields the extension verdict outright. `str` ↔ `List Char` (R, mapping.md §2); the extension test is the deep model `hasKnownExt` (A-reference, validated `== str.lower().endswith((...))` by G-AX, mapping.md §3.1). |
| A3 | `\| none => match extra with \| [] => Except.error Crash.indexOOB \| a :: _ => Except.ok a` | `return isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))` | R + I | reached only when neither stream nor path is present; `args[0]` ↔ head of `extra` (each entry already collapsed to its `isinstance` boolean, mapping.md §2); empty `*args` raising `IndexError` ↔ `Except.error Crash.indexOOB` (R). UNCHANGED op; the only behaviour the change affects here is that this branch is now UNREACHABLE from a present path. |

Discriminating content of the change — a present, NON-matching path must yield a
plain `false`, NOT fall through to `args[0]` — lives in clause A2 returning
`Except.ok (hasKnownExt p)` unconditionally. The pre-patch fell through on a
non-match; `Solution_prepatch.lean` reproduces that fall-through (the path
branch reads `extra` on a non-match) and **fails** `out = originSpec stream path
extra` (G-DIFF) at exactly the `some p`/non-matching case — which, with
`extra = []`, is the `IndexError` the F2P test `test_is_fits_gh_14305`
(`is_fits("", "foo.bar", None)` → `extra = ()`) exposes.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the path
branch's control flow (return-outright vs short-circuit-and-fall-through) — is
modeled **directly** as the branch structure of `originSpec` (concrete `match`
ops, tag I/R), not hidden behind an axiom about the function under change. The
unchanged extension test is the deep model `hasKnownExt` (A-reference, G-AX),
not a consumed axiom. There is **no A-consumed axiom** in this bundle.

## C. verify(Solution) ⇒ resolved

`classifyFitsOrigin` verifies only if its output equals `originSpec`, whose
`some p` branch returns `Except.ok (hasKnownExt p)` for EVERY path — matching or
not — and never reads `extra`. By R (`fileobj`/`filepath`/`*args` ↔
`Option Bool`/`Option (List Char)`/`List Bool`, IndexError ↔ `Crash.indexOOB`)
and by G-AX (`hasKnownExt == real str.lower().endswith((...))`; the real
`is_fits` never reads `args` when a path is present and raises `IndexError` on
an empty `*args` path-absent call) the verified classifier equals the
gold-patched `is_fits` on the tested inputs; by G-CONF the R/I transliteration
of the branch structure agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited extension test — and the gold
patch resolves (G-RESOLVE). The single trust point is the A-reference fidelity
(G-AX) and refinement faithfulness (this doc, G-EQ + G-CONF).
