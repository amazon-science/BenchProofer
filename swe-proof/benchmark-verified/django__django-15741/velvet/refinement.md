# refinement.md — django__django-15741

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `lookupValue` `do` block, with `force` and the `resolveName` A-consumed
callee) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses the
axiom's contract, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1) — here all R/I content collapses into the patch's own coercion, so G-CONF
is **skipped** (conf_skip=true, see §C); the A legs + narrative are audited by
**G-EQ** and **G-AX**. Claim: any impl verifying against this frozen spec,
refined per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The coercion site — `get_format()` (`django/utils/formats.py:100`)

Gold hunk (added line):
```
     if use_l10n and lang is None:
         lang = get_language()
+    format_type = str(format_type)  # format_type may be lazy.
     cache_key = (format_type, lang)
```

| # | Solution.lean impl op (`lookupValue`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `nm : Name` (`eager`/`deferred` carrier) | the `format_type` argument: a concrete `str` OR a lazy proxy | R | `str s ↔ Name.eager s.toList`; lazy proxy denoting `s` ↔ `Name.deferred s.toList` (mapping.md §2). The carrier records whether the name arrived deferred — the one bit the issue turns on. |
| A2 | `let key := force nm` | `format_type = str(format_type)  # format_type may be lazy.` | **R** | `force : Name → List Char` ↔ `str(format_type)`. Total on both carriers (`force (eager s) = s`, `force (deferred s) = s`), exactly as `str(...)` is the identity on a concrete string and forces a lazy proxy to its concrete text — and never raises. This is THE added line; it makes the downstream name a forced, concrete sequence. |
| A3 | `resolveName key` | the downstream resolution of `format_type` to its format value: `cache_key = (format_type, lang)`, the cache hit/miss, `getattr(module, format_type, None)`, `getattr(settings, format_type)` (`formats.py:117-145`) | **A-consumed** | `resolveName` is the unchanged callee. The consumed property: resolution is a function of the **resolved name content alone** — equal forced content ⇒ equal value. That is precisely why the lazy form must equal the eager form once forced. We pin no specific value (directive 7, weakest contract). G-AX validates against the real `get_format`. |
| A4 | `return Except.ok (...)` | the function returns the resolved value (no exception) | R | success ↔ `Except.ok`. The patched function never raises on a lazy name because `force` (`str(...)`) always succeeds; the pre-patch `TypeError` is `Except.error .unresolvedName` (the prepatch's deferred branch). |

Discriminating content of the change — a **deferred** name must be **forced**
before use, and forcing always succeeds — lives in `let key := force nm`
(handles `eager` and `deferred` uniformly to `content`) ⇔ the added
`format_type = str(format_type)`. The pre-patch skeleton uses the name *unforced*
and so cannot use a deferred name as a lookup name; `Solution_prepatch.lean`
reproduces that (its `deferred` branch returns `Except.error .unresolvedName`)
and **fails** `out = Except.ok (resolveName (force nm))` on exactly that clause
(G-DIFF).

## B. No second change site

The patch is a single added line; there is one modeled function and one
A-consumed callee. No additional sites.

## C. conf_skip — why G-CONF is skipped (not a weakening)

After the R-refinement `force ↔ str(format_type)`, the impl region's computed
output is `resolveName (force nm)` — a single A-consumed callee applied to the
forced name. The only non-A op is `force`, and `force` IS the patch's added line
(`str(format_type)`). A differential G-CONF would transliterate `force` to
`str(...)` and leave `resolveName` as the real downstream resolution; but the
real downstream resolution is only reachable through `get_format` itself, and the
in-container oracle is the **patched** `get_format`, which already applies the
same `str(...)` coercion idempotently. So the R/I shadow and the oracle are
identical by construction — there is no independent R/I content to refute. The
behavioral content the patch adds (forcing a deferred name succeeds and yields
the eager content) is the **A-consumed** property, whose soundness is covered by
**G-AX** (`axiom_check.py`): it runs the real `get_format` on each name supplied
both as a concrete `str` and as the corresponding lazy proxy, asserting they
return equal values and the lazy form never raises. `meta.json conf_skip=true`;
`conformance_check.py` exits with `status=skip`.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation the patch *adds* — coercing a
possibly-deferred name to its concrete content — is modeled directly as the total
function `force` (an **R** op, A2), not hidden behind an axiom about the function
under change. The only axiomatized symbol, `resolveName` (A3), covers the
**unchanged** downstream resolution. There is no axiom about `get_format` itself.

## E. verify(Solution) ⇒ resolved

`lookupValue` verifies only if it forces the name (`force nm`, handling `eager`
and `deferred` uniformly, A2) and returns `resolveName` of the forced content
(A3). By R (`Name ↔ str`-or-lazy, `force ↔ str(format_type)`, `Except.ok ↔`
normal return) the verified routine equals `get_format` with the
`str(format_type)` coercion applied — the gold patch. By G-AX the real downstream
resolution depends only on the resolved content (so the lazy form equals the
eager form and never raises), validating the `resolveName` A-consumed contract.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points: axiom soundness (G-AX) and refinement fidelity
(this doc, G-EQ).
