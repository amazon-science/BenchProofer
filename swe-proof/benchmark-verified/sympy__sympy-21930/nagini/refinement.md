# refinement.md — sympy__sympy-21930

The operation-by-operation correspondence between `model.py`'s implementation
(the three `render_token_{a,b,c}` impl regions and the deep models
`grouped_token` / `appended_super_is_outer`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## Common shape of the three hunks

The gold patch is three identical-in-kind hunks, each wrapping an operator's
`_latex` body in an outer LaTeX group `{ ... }`:

```
# AntiSymmetricTensor._latex (secondquant.py:219)
- return "%s^{%s}_{%s}" % (self.symbol, ...upper..., ...lower...)
+ return "{%s^{%s}_{%s}}" % (self.symbol, ...upper..., ...lower...)

# CreateBoson._latex (secondquant.py:480)
- return "b^\\dagger_{%s}" % self.state.name
+ return "{b^\\dagger_{%s}}" % self.state.name

# CreateFermion._latex (secondquant.py:941)
- return "a^\\dagger_{%s}" % self.state.name
+ return "{a^\\dagger_{%s}}" % self.state.name
```

Each is modeled by its own contracted function (`render_token_a`,
`render_token_b`, `render_token_c`) — per the multi-site rule the
pre/post/invariants/impl regions repeat, one set per site. (The model names are
deliberately non-echoing: they do not token-overlap the patched repo class
names — the true binding is in mapping.md / meta.json, never the spec view.)

## A. Per-site operation correspondence (each of the three `render_token_{a,b,c}`)

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `body: List[int]` | the intrinsic `%`-format body (`"b^\\dagger_{%s}" % ...`, `"%s^{%s}_{%s}" % ...`) the method builds before wrapping | R | `str` ↔ `List[int]` code points (mapping.md §2). The body is the UNCHANGED part of the format; the change is only the outer braces, so the body is carried as an uninterpreted input. |
| A2 | `result = [LBRACE()]` (start with `{` = 123) | the gold's prepended outer `{` in `"{%s...}"` | I | identical concrete prefix character. |
| A3 | the loop copies `body[i]` into `result` for `i in [0,len)` | the unchanged interior of the `%`-format string (the operator symbol, `^`, `\dagger`, the `_{...}` subscript, the interpolated index/state name) | R + I | identity copy of the carried body; `str` ↔ `List[int]` (R). The body content is unchanged by the patch (I). |
| A4 | `result.append(RBRACE())` (append `}` = 125) | the gold's appended outer `}` in `"{%s...}"` | I | identical concrete suffix character. |
| A5 | postcondition `ToSeq(Result()) == grouped_token(ToSeq(body))` is established | the whole hunk: `"{" + body + "}"` | A-reference | the changed string operation is modeled **deeply**: `grouped_token(body) = "{" + body + "}"` (pure region) IS the wrap the gold installs. No consumed `wrap_latex` axiom exists — the proof never depends on one. G-AX (axiom_check.py) validates `sympy.latex(op) == grouped_token(intrinsic_body)` on the REAL patched printer (mapping.md §3.1). |
| A6 | postcondition `Forall e: appended_super_is_outer(Result(), e)` (`Result()` ends in `}`) | the *purpose* of the wrap: a power's appended `^{exp}` binds to the whole group | A-reference | the interaction with the power printer (`latex.py:663`, `r"%s^{%s}"`) is modeled **deeply** by `appended_super_is_outer` (pure region), validated == the real printer by G-AX (mapping.md §3.2): for each operator the composite `latex(op**2)` is `token + "^{2}"` and is NOT the malformed `body + "^{2}"`. (The earlier illustrative helper `with_exponent` was removed — it was `@Pure` but cited by no `Ensures`/impl, hence non-load-bearing; the composite shape it documented is asserted directly in `axiom_check.py`.) |

The discriminating content of the change — wrapping the intrinsic body so an
appended superscript cannot collide with the body's interior `^` — lives in
`ToSeq(Result()) == grouped_token(ToSeq(body))` (the exact `{body}` shape) and
in `appended_super_is_outer` (the token ends in `}`). The pre-patch returns the
bare body (no braces); `model_prepatch.py` reproduces that and **fails** the
postcondition `ToSeq(Result()) == grouped_token(ToSeq(body))` on all three
sites — exactly the spec sensing the change (G-DIFF).

**Total correctness.** Each renderer carries `Requires(MustTerminate(2))`: the
real `_latex` methods are bounded, straight-line string formatting that always
returns. Without this obligation the value postconditions admit a vacuous
implementation that diverges before returning (an infinite loop verifies
against any `Ensures`); with it, Nagini's obligation system rejects any loop
without a decreasing termination measure. The gold-faithful copy loop
discharges the obligation with the measure `len(body) - i` (the
`Invariant(MustTerminate(len(body) - i + 1))` inside the impl region). The
real repo counterpart is trivially total (`"%s..." % ...` terminates), so the
obligation does not exclude any faithful implementation.

## B. No consumed axioms; no kind-3 steps

There is **no `@ContractOnly`** axiom in this bundle: the only changed operation
(the brace-wrap) is expressible directly as a `List[int]` construction, so it is
modeled **deeply** (`grouped_token`, A-reference A5) rather than hidden behind an
axiom about the function under change. The power-printer interaction it exists to
fix is likewise modeled deeply (`appended_super_is_outer`, A-reference A6) and
validated against the real `LatexPrinter` by G-AX.

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the wrap and its grouping effect — is modeled deeply, not
axiomatized. No step is a *changed* operation Nagini cannot express (no kind-3).

## C. Multi-site differential coverage (G-DIFF)

The three sites are the same fix applied to three renderers; a single
`model_prepatch.py` reverts all three impls to the bare-body (unwrapped) form
and **fails the `grouped_token` postcondition at each of the three sites**
(three independent verification errors, one per renderer). Because the three
hunks are behaviourally identical (wrap in `{...}`) and each fails on its own
postcondition, one prepatch file with three failing sites is the natural
differential witness; the F2P tests exercise each renderer
(`test_create`/`test_create_b` → CreateBoson, `test_create_f`/`test_commutation`/
`test_NO` → CreateFermion, `test_Tensors` → AntiSymmetricTensor,
`test_issue_19661` → the CreateBoson power composite).

## D. verify(model) ⇒ resolved

Each `render_*` verifies only if its output equals `{body}` (A5) and ends in `}`
so an appended exponent binds outside it (A6). By R (`str` ↔ `List[int]`, the
carried-body identity) the verified renderer equals the gold method
`"{...}" % ...` on every operator (G-AX confirms the deep model `grouped_token`
== the real patched `_latex`, A-reference). The power-safety the wrap provides
matches the real `LatexPrinter` (G-AX, A-reference). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited deep-model references — and the gold patch resolves
(G-RESOLVE). The trust point is exactly one of PLAN §1.1: refinement fidelity
(this document, G-EQ); there is no consumed axiom, so the axiom-soundness trust
point reduces to the A-reference validation (G-AX).
