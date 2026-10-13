# refinement.md — sphinx-doc__sphinx-8551

Maps every operation in `implementation_makeXref` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `makeXref` (`PyXrefMixin.make_xref`, node-building step)

Post-patch repo code (`sphinx/domains/python.py:271-284`; the two `+` lines are
the gold patch):
```python
result = super().make_xref(rolename, domain, target, innernode, contnode, env)
result['refspecific'] = True
result['py:module'] = env.ref_context.get('py:module')   # + patch
result['py:class'] = env.ref_context.get('py:class')     # + patch
if target.startswith(('.', '~')):
    prefix, result['reftarget'] = target[0], target[1:]
    ...
return result
```

Lean impl (`implementation_makeXref`):
```lean
def implementation_makeXref (ctx : RefContext) (target : String) : XrefNode :=
  Id.run do
    let mut result : XrefNode :=
      { reftarget := target, refspecific := false, pyModule := none, pyClass := none }
    result := { result with refspecific := true }
    result := { result with pyModule := ctx.module }
    result := { result with pyClass := ctx.cls }
    if hasSigil target then
      result := { result with reftarget := target.drop 1 }
    return result
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `ctx : RefContext` | `env.ref_context.get('py:module')` / `get('py:class')` | **R** | the surrounding namespace context ↔ `RefContext` (mapping.md bijection: string ↔ `some`, missing/`None` ↔ `none`). An environmental input, not a callee. The `docfields.py:298` edit (`env=…`) is what makes this `env`/context available — the enabling half of the same fix, modeled as "the `ctx` argument exists". |
| 2 | `target : String` | the `target` argument of `make_xref` | **R** | identity string refinement (`str` ↔ Lean `String`). |
| 3 | `result : XrefNode` | the `result` `pending_xref` node, restricted to `{reftarget, refspecific, py:module, py:class}` | **R** | the four attributes the test observes; mapping.md bijection. The `~`-sigil display-TEXT rewrite (`result.traverse(nodes.Text)`) is UNCHANGED by the patch and unobserved by the F2P test, so it is outside the modeled state (frame: not an output component of this model). |
| 4 | `let mut result := { reftarget := target, refspecific := false, … }` | `result = super().make_xref(...)` establishes the node with `reftarget = target` | **I** | initial node state; `super().make_xref` sets `reftarget = target` and the node shell. Its `reftarget` is the only observed attribute and is modeled directly. |
| 5 | `result := { result with refspecific := true }` | `result['refspecific'] = True` | **I** | unchanged by the patch; identical concrete op. |
| 6 | `result := { result with pyModule := ctx.module }` | `result['py:module'] = env.ref_context.get('py:module')` | **I** (deep model of the changed op) | **the fixed operation** (gold `+` line 1). The node records the current module from the surrounding context. Modeled deeply as a direct field write of `ctx.module`; never axiomatized (SPEC_GUIDE §3). G-CONF differential-tests it. |
| 7 | `result := { result with pyClass := ctx.cls }` | `result['py:class'] = env.ref_context.get('py:class')` | **I** (deep model of the changed op) | **the fixed operation** (gold `+` line 2). The node records the enclosing class from the surrounding context. Modeled deeply; never axiomatized. G-CONF differential-tests it. |
| 8 | `if hasSigil target then result := { result with reftarget := target.drop 1 }` | `if target.startswith(('.', '~')): prefix, result['reftarget'] = target[0], target[1:]` | **I** | unchanged by the patch; the reftarget rewrite when a `.`/`~` sigil is present. `target.drop 1` ↔ `target[1:]`. (`prefix` and the text rewrite are unobserved by the model.) |
| 9 | `return result` | `return result` | **I** | the produced node flows out. |

The impl region contains **R/I ops only** and NO consumed axiom, so
`conf_skip = false`: `conformance_check.py` differential-tests the R/I node
construction against an in-process replica of the post-patch `make_xref`
attribute writes.

## Soundness check (verify ⟹ correct)

- `problem_spec_makeXref ctx target result` pins ALL FOUR observed node
  attributes: `refspecific = true`, `reftarget = strippedTarget target`,
  `pyModule = ctx.module`, `pyClass = ctx.cls`. Directive 5 (frame): every
  observed output component is pinned to the input — there is no unconstrained
  component a wrong impl could fill. Directive 8: the postcondition is grounded in
  the inputs (`ctx.module`, `ctx.cls`, `target` via `strippedTarget`), not an
  opaque oracle; the result must be *produced by* copying the surrounding context
  onto the node.
- The prepatch impl omits ops #6 and #7, leaving `pyModule = none`,
  `pyClass = none`. It violates the spec on the discriminating clause whenever a
  module/class is in force: e.g. `ctx.module = some "example"`,
  `ctx.cls = some "Class"`, where the spec requires `result.pyModule = some
  "example"` and `result.pyClass = some "Class"` but the prepatch yields `none`
  for both. Its carried gold proof cannot close (G-DIFF/G-PANEL).
- This discriminating case is exactly the FAIL_TO_PASS test
  `tests/test_domain_py.py::test_info_field_list`: under `.. py:module:: example`
  + `.. py:class:: Class`, a `:param str name:` and `:type age: int` produce
  `pending_xref` nodes that the test asserts carry
  `**{"py:module": "example", "py:class": "Class"}`. Base_commit produced nodes
  with no such context (the assertion fails); and in the issue's repro the missing
  context makes unqualified `A` fuzzy-match `mod.A` and `mod.submod.A` in every
  submodule → the "more than one target found" warnings. Post-patch the context is
  recorded and resolution is scope-aware.

## Why no axiom

The patch READS two values out of the surrounding namespace context and writes
them onto the produced node; it does not change any callee. The context values
are inputs (`ctx.module`, `ctx.cls`); the writes are modeled deeply as direct
field assignments. There is no unchanged pure callee whose property the proof
must consume, so the `axioms` region is empty and `axiom_check.py` is a skip stub
(G-AX = skip). G-CONF is the primary, exhaustive-over-the-fuzzed-domain
differential for the modeled node construction.
