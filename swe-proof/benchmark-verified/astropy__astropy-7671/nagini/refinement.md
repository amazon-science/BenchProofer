# refinement.md — astropy__astropy-7671

The operation-by-operation correspondence between `model.py`'s implementation
(the `version_meets_minimum` impl region and the deep `normalize` /
`loose_ge` / `loose_gt` models) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model is validated == the real callee by
axiom_check.py / G-AX, NOT consumed as an axiom), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `minversion()` (`astropy/utils/introspection.py:91`)

Gold hunk (body, lines 140-145 @ base_commit):
```
   have_version = resolve_name(module.__name__, version_path)

+  # LooseVersion raises a TypeError when strings like dev, rc1 are part
+  # of the version number. Match the dotted numbers only. Regex taken
+  # from PEP440, https://www.python.org/dev/peps/pep-0440/, Appendix B
+  expr = '^([1-9]\\d*!)?(0|[1-9]\\d*)(\\.(0|[1-9]\\d*))*'
+  m = re.match(expr, version)
+  if m:
+      version = m.group(0)
+
   if inclusive:
       return LooseVersion(have_version) >= LooseVersion(version)
   else:
       return LooseVersion(have_version) > LooseVersion(version)
```
(plus `import re` at module top.)

| # | model.py impl op (`version_meets_minimum`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `have: List[int]` | `have_version` (a version `str`, resolved at lines 137-140) | R | version `str` ↔ `List[int]` parsed release segments (mapping.md §2); the unchanged resolution prologue is abstracted to the resolved value. |
| A2 | parameter `want: List[int]` | `version` (the requested version `str` argument) | R | same `str` ↔ `List[int]` bijection (mapping.md §2). |
| A3 | parameter `inclusive: bool` | the `inclusive` keyword argument | I | identical boolean. |
| A4 | the loop building `norm` = `normalize(ToSeq(want))` (prefix of `want` up to the first qualifier marker `-1`) | the inserted `expr=...; m=re.match(expr, version); if m: version = m.group(0)` (lines 143-148 post-patch) | A-reference | the changed string operation (qualifier stripping) is modelled **deeply**: the front-recursive `@Pure normalize` and the matching backward loop ARE the leading-dotted-numeric-prefix extraction. There is no consumed `strip` axiom — the proof never depends on one. The deep model is validated **== the real `re.match(...).group(0)`** out-of-band by G-AX (axiom_check.py `check_normalize`, mapping.md §3.1). |
| A5 | `loose_ge(ToSeq(have), ToSeq(norm))` (inclusive branch) | `LooseVersion(have_version) >= LooseVersion(version)` AFTER the strip | A-reference + R | the inclusive comparison is modelled **deeply** by the front-recursive `@Pure loose_ge` over the parsed components; G-AX validates `loose_ge == LooseVersion.__ge__` on numeric versions (mapping.md §3.2). `ToSeq(norm) == normalize(ToSeq(want))` (proved in the loop) is the R-refinement of the post-strip `version`. |
| A6 | `loose_gt(ToSeq(have), ToSeq(norm))` (strict branch) | `LooseVersion(have_version) > LooseVersion(version)` AFTER the strip | A-reference + R | as A5 for the strict order; G-AX validates `loose_gt == LooseVersion.__gt__`. |
| A7 | `return` the boolean | the `return` of the comparison boolean | I | identical control flow / return value. |

The discriminating content of the change — the requested version is compared
only AFTER its non-numeric qualifier tail is stripped — lives in
`Result() == loose_ge(ToSeq(have), normalize(ToSeq(want)))` (the spec compares
against `normalize(want)`, never the raw `want`). The pre-patch code compared
the raw `version`; `model_prepatch.py` reproduces that (it calls
`loose_ge(ToSeq(have), ToSeq(want))` with no normalization) and **fails** the
postcondition `Result() == loose_ge(ToSeq(have), normalize(ToSeq(want)))`,
which is exactly the spec sensing the change (G-DIFF).

## B. The undefined-comparison subtlety (the real bug)

The bug is that `LooseVersion(have) >= LooseVersion('0.12dev')` RAISES a
`TypeError` (comparing `int` 2 with `str` `'dev'`), so the F2P test for
`minversion(test_module, '0.12dev')` fails pre-patch. The deep model captures
this faithfully: in `loose_ge`/`loose_gt`, a position pairing a numeric segment
with the qualifier marker (`(a[0] < 0) != (b[0] < 0)`) yields the
non-satisfied outcome `False` — a sound abstraction of distutils' "raises /
never returns True" on such input. Because the spec compares against
`normalize(want)` (always qualifier-free, proved numeric in the loop), the spec
path never reaches that case; it only fires on the pre-patch's raw comparison,
turning the pre-patch's `True`-expectation into a sensed `False`. G-AX confirms
the real machinery both ways: the stripped comparison returns `True`, the raw
comparison raises `TypeError`.

The contract's domain on `want` is restricted to the requested labels that
begin with a numeric release segment
(`Requires(len(want) > 0 and want[0] >= 0)`) — exactly the region on which the
real gold-patched `minversion` returns a defined boolean. Labels outside it
(pure / leading qualifier, empty, leading-dot, epoch) make the real callee raise
`TypeError`/`AttributeError` or lose any defined release order; the contract
makes no claim there, so the total deep model is a SOUND (no-raise)
over-approximation rather than over-claiming a defined answer where the real
machinery is partial (SPEC_GUIDE directive 7). The discriminator `0.12dev`
(carrier `[0,12,-1]`, first segment `0 ≥ 0`) is INSIDE this domain, so G-DIFF is
unaffected. axiom_check.py certifies the domain end-to-end against the real
callee (never raises in-domain; every excluded label is partial).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* — the qualifier-stripping regex and the version comparison it feeds —
are modelled **deeply** (the spelled-out `@Pure` `normalize`, `loose_ge`,
`loose_gt`, consumed by `version_meets_minimum`), not hidden behind an axiom
about the function under change. There are **no consumed `@ContractOnly`
axioms** (the axioms region is empty). The deep models are the **A-references**
G-AX validates against the real `re.match` and `LooseVersion`.

## D. verify(model) ⇒ resolved

`version_meets_minimum` verifies only if its result equals the component-wise
order against the qualifier-STRIPPED requested version (A4–A6) — i.e. only if
the requested version's non-numeric tail is removed before comparison. By R
(version `str` ↔ `List[int]` parsed segments; the unchanged resolution prologue;
`inclusive` identical) the verified routine equals
`LooseVersion(have_version) >= LooseVersion(re.match(EXPR, version).group(0))`
on the tested inputs; by G-AX the deep model `normalize` equals the real regex
prefix and `loose_ge`/`loose_gt` equal the real `LooseVersion` order
(A-references). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited callees — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: deep-model/axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
