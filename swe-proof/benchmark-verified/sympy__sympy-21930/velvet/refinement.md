# refinement.md — sympy__sympy-21930

Operation-by-operation correspondence between `Solution.lean`'s `impl` regions
(the three `do` blocks + the pure `wrapGroup` / `concatNames` models) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs and this narrative are audited by **G-EQ**. There are **no A legs**
in this bundle (no axiomatized or deeply-referenced callees — §C below), so
soundness rests entirely on the R/I refinement (G-CONF) plus the frozen-spec
strength (G-DIFF/G-PANEL).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. `AntiSymmetricTensor._latex` — `secondquant.py:220`

Gold hunk:
```
- return "%s^{%s}_{%s}" % (
+ return "{%s^{%s}_{%s}}" % (
      self.symbol,
      "".join([ i.name for i in self.args[1]]),
      "".join([ i.name for i in self.args[2]])
  )
```

| # | Solution.lean op (`tensorIndexLatex`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `symbol`, `upper`, `lower : List Char / List (List Char)` | `self.symbol`, `self.args[1]`, `self.args[2]` read | R | `str ↔ List Char`; each `args[k]` `Tuple` ↔ list of the elements' `.name` sequences. The `.name` read per index is an unchanged upstream attribute access (R). mapping.md §2. |
| A2 | `up = concatNames upper` via the backward `while` fold | `"".join([ i.name for i in self.args[1]])` | I | `str.join` with empty separator = left-to-right concatenation; the verified loop computes exactly `concatNames`. Unchanged by the patch. |
| A3 | `lo = concatNames lower` (second fold) | `"".join([ i.name for i in self.args[2]])` | I | as A2. |
| A4 | `body = symbol ++ "^{" ++ up ++ "}_{" ++ lo ++ "}"` | the `%s^{%s}_{%s}` template fill | I | literal-string interleaving by `++`; identical pre- and post-patch. |
| A5 | `out = wrapGroup body` (prepend `{`, append `}`) | the **added** outer `{`…`}` of `"{%s^{%s}_{%s}}"` | I | the one changed op: enclose the rendering in a group. Concrete, transliterated by G-CONF. |

Discriminating content: A5. Pre-patch returns `body`; post-patch returns
`{body}`. `Solution_prepatch.lean` reproduces the bare `body` return and **fails**
the postcondition `out = wrapGroup (…)` (G-DIFF).

## B. `CreateBoson._latex` — `secondquant.py:480`

Gold hunk:
```
- return "b^\\dagger_{%s}" % self.state.name
+ return "{b^\\dagger_{%s}}" % self.state.name
```

| # | Solution.lean op (`bDaggerLatex`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `name : List Char` | `self.state.name` (`str`) read | R | `str ↔ List Char`; unchanged attribute access. |
| B2 | `body = "b^\dagger_{" ++ name ++ "}"` | the `"b^\dagger_{%s}"` template fill | I | literal interleaving by `++`; unchanged. |
| B3 | `out = wrapGroup body` | the **added** outer `{`…`}` | I | the changed op: group-wrap. G-CONF transliterates. |

Discriminating content: B3. `Solution_prepatch_2.lean` returns the bare `body`
and **fails** the postcondition (G-DIFF).

## C. `CreateFermion._latex` — `secondquant.py:941`

Gold hunk:
```
- return "a^\\dagger_{%s}" % self.state.name
+ return "{a^\\dagger_{%s}}" % self.state.name
```

| # | Solution.lean op (`aDaggerLatex`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | param `name : List Char` | `self.state.name` read | R | as B1. |
| C2 | `body = "a^\dagger_{" ++ name ++ "}"` | the `"a^\dagger_{%s}"` template fill | I | as B2. |
| C3 | `out = wrapGroup body` | the **added** outer `{`…`}` | I | the changed op. |

Discriminating content: C3. `Solution_prepatch_3.lean` returns the bare `body`
and **fails** (G-DIFF).

## D. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The only operation that *changed* in any of the three
methods — enclosing the rendered atom in a `{ … }` group — is modeled **deeply
and concretely** (`wrapGroup`, an I op), not hidden behind an axiom. There is no
callee the changed functions call-but-don't-change that needs axiomatizing: the
join is modeled deeply (`concatNames`, I) and the `.name`/`str` reads are R
identities. Hence **zero** consumed axioms and **zero** A-reference deep models;
`axiom_check.py` is a no-op pass and `meta.json` lists empty `axioms` /
`deep_model_references`.

## E. verify(Solution) ⇒ resolved

Each method verifies only if its output equals `wrapGroup(<body>)` — i.e. the
exact pre-patch rendering enclosed in an added `{ … }` group (A5/B3/C3). By R
(`str ↔ List Char`, `.name`/`str()` identities) the verified renderings equal
the patched `_latex` outputs on the tested inputs; by G-CONF the R/I
transliteration of all three `do` blocks agrees with `patch.diff`'s behaviour on
≥10⁵ fuzzed inputs. The three F2P-observable behaviors (tensor, boson-creation,
fermion-creation rendering) each have a failing prepatch. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The only trust point is
refinement fidelity (this doc + G-CONF); there are no axiom-soundness trust
points (no axioms).
