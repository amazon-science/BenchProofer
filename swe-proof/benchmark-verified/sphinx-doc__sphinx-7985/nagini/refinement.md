# refinement.md — sphinx-doc__sphinx-7985

The operation-by-operation correspondence between `model.py`'s implementation
(the `check` impl region, the deep helpers `starts_with` / `scheme_present`,
and the pure decision cascade `classify`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The classification site — nested `check()` (`sphinx/builders/linkcheck.py:211`)

Gold hunks:
```
+ uri_re = re.compile('[a-z]+://')          # new module-level pattern

  def check() -> Tuple[str, str, int]:
      # check for various conditions without bothering the network
-     if len(uri) == 0 or uri.startswith(('#', 'mailto:', 'ftp:')):
+     if len(uri) == 0 or uri.startswith(('#', 'mailto:')):
          return 'unchecked', '', 0
      elif not uri.startswith(('http:', 'https:')):
-         return 'local', '', 0
+         if uri_re.match(uri):
+             # non supported URI schemes (ex. ftp)
+             return 'unchecked', '', 0
+         else:
+             if path.exists(path.join(self.srcdir, uri)):
+                 return 'working', '', 0
+             else:
+                 for rex in self.to_ignore:
+                     if rex.match(uri):
+                         return 'ignored', '', 0
+                 else:
+                     return 'broken', '', 0
      elif uri in self.good:
          ...
```

| # | model.py impl op (`check`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `target: List[int]` | the closure variable `uri: str` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `len(target) == 0` | `len(uri) == 0` | R | `len` on the carrier ↔ `len` on the `str` (mapping.md §2). |
| A3 | `starts_with(target, [35]) or starts_with(target, mailto)` | `uri.startswith(('#', 'mailto:'))` | A-reference | the literal prefix test is modelled DEEPLY (`prefix_eq` fold + the verified `starts_with` loop); `str.startswith` with a tuple is the per-prefix disjunction. The deep model is validated == real `str.startswith` by G-AX (mapping.md §3.1). The `'ftp:'` member is *removed* by the patch — it is absent here and present in `model_prepatch` (the bug). |
| A4 | `return UNCHECKED()` (0) | `return 'unchecked', '', 0` | R | status string ↔ int code; the F2P tests observe the status, not the constant's representation (mapping.md §2). |
| A5 | `not (starts_with(target, http) or starts_with(target, https))` | `not uri.startswith(('http:', 'https:'))` | A-reference | as A3: deep `starts_with` == real `str.startswith` (G-AX). |
| A6 | `scheme_present(target)` | `uri_re.match(uri)` (`uri_re = re.compile('[a-z]+://')`) | A-reference | the introduced regex match is modelled DEEPLY (`has_uri_scheme` via `lower_run` + the verified `scheme_present` loop): a maximal leading `[a-z]+` run of length ≥ 1 immediately followed by `://`. `re.match` is anchored; G-AX asserts `has_uri_scheme == uri_re.match` over boundary + 80 000 fuzz (mapping.md §3.2). |
| A7 | `file_exists` (input) | `path.exists(path.join(self.srcdir, uri))` | R | the filesystem fact is an environment-dependent boolean the real branch consumes directly; modelled as the boolean input (mapping.md §2). Not an axiom — it has no value contract to over-approximate, only its boolean result, which the model takes as given exactly as the code does. |
| A8 | `return WORKING()` (1) | `return 'working', '', 0` | R | as A4. |
| A9 | `ignore_match` (input) | `for rex in self.to_ignore: if rex.match(uri): ...` (some pattern matches) | R | the inner ignore loop reduces to "some configured pattern matches the target"; modelled as the boolean input (mapping.md §2). The per-pattern regex is user configuration, not changed code. |
| A10 | `return IGNORED()` (3) | `return 'ignored', '', 0` | R | as A4. |
| A11 | `return MISSING()` (2) | `for…else: return 'broken', '', 0` | R + I | the `for…else` falls through to `'broken'` exactly when no pattern matched (`not ignore_match`); control flow identical, status string ↔ code (A4). The model symbol `MISSING` IS the `'broken'` status — a behaviour-faithful synonym describing the modelled meaning (the referenced local target is absent), `MISSING ↔ 'broken'` (mapping.md §1). |
| A12 | `return remote` | the unchanged web branch (`elif uri in self.good: … check_uri()`) | R | the web branch is unchanged by the patch; its outcome is modelled as the opaque `remote` value so the model neither strengthens nor weakens it (mapping.md §2). |

## B. The decision cascade is the spec, not an oracle

The postcondition is `Result() == classify(ToSeq(target), file_exists,
ignore_match, remote)` plus three explicit structural implications pinning the
MISSING / WORKING / IGNORED outcomes to *witnessed structural properties of the
input* (the target is non-empty, is not one of the literal prefixes, has no
`[a-z]+://` scheme, and the environment facts). `classify` is a `@Pure`
function spelled out over the input code points and the boolean facts — it is
NOT an opaque oracle: it is the modelled branch logic itself, so a verifying
impl must *produce* each outcome through the modelled decision, not merely echo
a constant. The discriminating clauses fail for any impl that, like the
pre-patch, collapses the non-web branch to a single unclassified outcome.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* — the literal-prefix tuple (dropping `ftp:`) and the new
`[a-z]+://` scheme test that gates the local-file lookup — are modelled
**deeply** (`starts_with`/`prefix_eq` and `scheme_present`/`has_uri_scheme`,
spelled out and verified), never hidden behind a consumed axiom. They are
**A-references** validated == the real `str.startswith` / `re.match('[a-z]+://')`
by G-AX. There is **no consumed `@ContractOnly` axiom**: the only opaque inputs
(`file_exists`, `ignore_match`, `remote`) are environment facts / the unchanged
branch outcome, passed as values exactly as the real code consumes them.

## D. G-DIFF — the prepatch fails on the right clause

`model_prepatch.py` keeps the spec byte-identical and reverts the `check` impl
to the pre-patch skeleton: the first guard tests the old tuple `('#',
'mailto:', 'ftp:')`, and the entire non-web branch returns the unclassified
outcome `4` (the old `'local'`). It **fails** verification on the postcondition
`Result() == classify(...)` (and the MISSING/WORKING/IGNORED implications),
because for a non-empty, non-web, non-scheme target it returns `4` where the
spec demands `MISSING()` (2) / `WORKING()` (1) / `IGNORED()` (3). This is exactly
the F2P-tested behaviour: `path/to/notfound` must be `broken` (the new F2P
assertion `[broken] path/to/notfound`), and an existing `conf.py` must be
`working` — neither is the pre-patch `local`.

## E. verify(model) ⇒ resolved

`check` verifies only if its output equals the exact decision cascade
`classify`, which by A1–A12 (R type refinement + A-reference deep models
validated by G-AX) is the gold-patched `check()` body up to type refinement.
The F2P tests (`test_defaults`, `test_anchors_ignored`) observe precisely these
outcomes: a missing local file rendered `[broken] path/to/notfound` with the
total line count rising to 6, and the same target rendered `ignored` (absent
from output) when added to `linkcheck_ignore`. Therefore an impl satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
G-AX-validated deep models — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: axiom/deep-model soundness (G-AX) and
refinement fidelity (this document, G-EQ).
