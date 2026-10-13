# refinement.md — pytest-dev__pytest-8399

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`privatizeName` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no axioms** in this
bundle, so no A-tagged rows and no `axiom_check.py` (G-AX auto-skips).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The fixture-name construction — `_make_xunit_fixture` (`src/_pytest/unittest.py:147`)

Gold hunk (the F2P-graded site):
```
- name=f"unittest_{setup_name}_fixture_{obj.__qualname__}",
+ name=f"_unittest_{setup_name}_fixture_{obj.__qualname__}",
```

| # | Solution.lean impl op (`privatizeName`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `base : List Char` | the f-string body `unittest_{setup_name}_fixture_{obj.__qualname__}` (the pre-patch generated name) | R | `str` ↔ `List Char` (mapping.md §2). `base` is the entire descriptive label that already existed; the patch does not touch its body. G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `return '_' :: base` | prepend the literal `"_"` to the f-string (the `_` added at the front of `unittest_...`) | I | concrete one-character front-cons; `'_' :: base` over `List Char` is exactly `"_" + base` over `str`. The patch adds a single leading `_` and changes nothing else. Transliterated and differential-tested by G-CONF against the patched `_make_xunit_fixture`'s registered name. |
| A3 | post `out.head? = some '_'` | the property the unchanged downstream consumer keys on | I | the listing routine (`python.py:1429,1511`, unchanged) hides any fixture whose name `startswith("_")`; the postcondition pins exactly that observable. Not a separate op — it is the *purpose* of A2, stated as a structural predicate on the produced identifier. |

Discriminating content of the change — the produced identifier must **begin with
an underscore** — lives in `ensures out = '_' :: base` / `ensures out.head? =
some '_'` (model) ⇔ the added leading `_` in the f-string (real). The pre-patch
returned `base` unchanged (no leading `_`); `Solution_prepatch.lean` reproduces
that and **fails** both `out = '_' :: base` and `out.head? = some '_'` (G-DIFF).

## B. The four xunit-style sites (`src/_pytest/python.py`) — same operation

The gold patch makes the byte-identical edit at four further generated-name
constructions in `python.py` (module/function/class/method xunit fixtures):
each `name=f"xunit_..._{...}"` gains a leading `_`. These are the **same**
operation `privatizeName` models (`name = "_" + base`) applied to a different
`base`; they are **I** under the same A1/A2 refinement. They are not modeled as
separate `method`s because:

- the operation is identical (no new behavior to pin), and
- the F2P test grades the `unittest.py` `setUpClass` site (mapping.md §3); the
  `python.py` sites are covered by the PASS_TO_PASS suite (no behavior of theirs
  regresses) and are mentioned only in `hints_text`, never the public
  `problem_statement`.

No separate failing prepatch is required for site B: a prepatch must keep the
spec byte-identical (G-DIFF), and site A's prepatch already exercises the shared
"missing leading underscore" defect that is the single behavioral change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — prepending a
leading underscore to the generated identifier — is modeled **directly** as the
concrete front-cons `'_' :: base` (step A2, an **I** op), not hidden behind an
axiom. There are no consumed axioms and no deep-model references: the identifier
is built purely from its given label, consulting no external callee, so there is
nothing to axiomatize. (Directive 7: never axiomatize the operation the patch
changes; here it is modeled concretely instead.)

## D. verify(Solution) ⇒ resolved

`privatizeName` verifies only if its output equals `base` with a single leading
`'_'` prepended (A2) and therefore begins with `'_'` (A3). By R
(`str ↔ List Char`, single-char prefix ↔ front-cons) the verified construction
equals the patched f-string `f"_unittest_{setup_name}_fixture_{qualname}"` on
every label. The unchanged downstream listing (mapping.md §1) hides exactly the
names beginning with `_`, so the F2P assertion (the `setUpClass` fixture is
hidden by default, shown under `-v`) holds. By G-CONF the R/I transliteration of
`privatizeName` agrees with `patch.diff`'s behaviour (the patched
`_make_xunit_fixture`'s registered name) on ≥10⁵ inputs across both call-site
configurations. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms to trust.
