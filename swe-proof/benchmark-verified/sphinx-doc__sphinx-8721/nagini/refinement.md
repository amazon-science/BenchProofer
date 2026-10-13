# refinement.md — sphinx-doc__sphinx-8721

The operation-by-operation correspondence between `model.py`'s implementation
(the `module_source_pages` impl region, plus the deep helper `begins_with` and
the pure models `prefix_eq` / `suppressed`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, the proof uses the axiom's `Ensures`, and **A-reference**,
a deep model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The page-collection gate — `collect_pages` (`sphinx/ext/viewcode.py:181`)

Gold hunk (inserted just after the `_viewcode_modules` guard):
```
+    if app.builder.name == "singlehtml":
+        return
+    if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub:
+        return
```
(`collect_pages` is a generator; a bare `return` makes it yield nothing, i.e.
produce no module pages. The unchanged code below the guard yields one page per
recorded module entry plus a trailing index page.)

The gold patch installs **two** early-return guards. The
electronic-book-default guard (the second one) is the behaviour the public
`problem_statement` describes ("module pages should not be created for epub by
default") and the only guard exercised by the FAIL_TO_PASS / PASS_TO_PASS tests
(`test_viewcode_epub_default`, `test_viewcode_epub_enabled`,
`test_linkcode`, `test_local_source_files`). The first guard (the single-file
co-change) is neither described in `problem_statement` nor exercised by any
F2P/P2P test, so it is NOT part of the modeled, consumer-visible behavioural
contract: the spec models exactly the tested discriminator. `patch.diff`
remains the gold verbatim (both guards), so G-RESOLVE is unaffected.

| # | model.py impl op (`module_source_pages`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `name: List[int]` | `app.builder.name: str` | R | `str` ↔ `List[int]` of code points (mapping.md §2). |
| A2 | parameter `enable_epub: bool` | `env.config.viewcode_enable_epub: bool` (default `False`, `viewcode.py:281`) | R/I | identity on the bool; the default-`False` reading is what makes epub suppress by default. |
| A3 | parameter `modules: List[int]`; the per-page result carrier | the `_viewcode_modules` entries iterated by the page loop; the yielded `(pagename, context, 'page.html')` tuples | R | each recorded module that would yield a page ↔ one list element; yielding a page ↔ appending it; yielding nothing ↔ empty list (mapping.md §2). Page content + the trailing index page are unchanged by the patch and abstracted away. |
| A4 | `begins_with(name, ep)` → `prefix_eq(ToSeq(name), lit_epub())`, AND `not enable_epub`, guarding `return empty` | `if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub: return` | A-reference | the begins-with test is modelled **deeply** (`prefix_eq`, verified `begins_with` loop); G-AX validates `prefix_eq == str.startswith`. The `and not enable_epub` is identical (I). `return` (yields nothing) ↔ `return empty`. |
| A5 | the per-module loop `result = result + [modules[i]]` over `0..len(modules)`, reached only when the epub guard did not fire | the unchanged page-emission loop below the inserted guards, reached only when neither `return` fired | R/I | the loop is the unchanged page production; under R it appends one carrier per recorded module entry. The patch does not touch it; it only gates whether it runs. |

The discriminating content of the change the tests observe — module pages are
NOT produced for an electronic-book target when the preference is off — lives in
`suppressed(name, enable_epub)` (model) ⇔ the inserted electronic-book early
`return` (real). The postcondition

  `Implies(suppressed(ToSeq(name), enable_epub), len(Result()) == 0)`

is exactly the spec sensing the change: with no gate the result is the full
module list (non-empty for any non-empty `modules`), so `model_prepatch.py`
(the gate-less pre-patch skeleton) **fails** on this clause (G-DIFF). The
companion clause

  `Implies(not suppressed(...), ToSeq(Result()) == ToSeq(modules))`

pins that *every other* target still gets all its pages — so a wrong impl
cannot pass by simply suppressing everything (that would fail the
`viewcode_enable_epub=True` P2P test, `test_viewcode_epub_enabled`, which
requires the page to exist).

## B. No consumed axioms; the begins-with builtin is an A-reference

The only library operation the modeled gate calls — `str.startswith` — is an
**unchanged** builtin, and it is modelled **deeply** (`prefix_eq`), not behind a
consumed `@ContractOnly` axiom. There is therefore no A-consumed row: the
`axioms` region is empty by design. The deep model is an **A-reference**,
validated == its real builtin by axiom_check.py / G-AX (mapping.md §3). No flag
dependency: `.startswith` is called with a single prefix argument (no
`start`/`end`), matching `prefix_eq`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The tested operation that
*changed* — the addition of the electronic-book suppression gate — is modelled
**deeply** (the spelled-out `prefix_eq` fold and the `suppressed` predicate,
consumed in `module_source_pages`'s contract and verified by the `begins_with`
loop), not hidden behind an axiom about the function under change. There is no
`@ContractOnly` for `module_source_pages` (repo `collect_pages`) or for the gate
itself. The single-file co-change guard is not modeled (it is untested and not
described in the public problem statement); the gold `patch.diff` still carries
it verbatim.

## D. verify(model) ⇒ resolved

`module_source_pages` verifies only if its output is empty exactly when the
target is suppressed (A4) and is the full per-module page list otherwise (A5).
By R (`str` ↔ `List[int]`, the page-set carrier, the bool identity) the verified
function equals the gold `collect_pages` on the tested builds: an epub build
with the default `viewcode_enable_epub=False` yields no module pages (so
`_modules/spam/mod1.xhtml` is absent — F2P `test_viewcode_epub_default`), an
epub build with `viewcode_enable_epub=True` yields them (so the file exists —
P2P `test_viewcode_epub_enabled`), and a plain html build is unaffected (P2P
`test_linkcode`, `test_local_source_files`). By G-AX the deep model `prefix_eq`
equals the real `str.startswith`. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
builtins on every tested input — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: deep-model/axiom soundness (G-AX)
and refinement fidelity (this document, G-EQ).
