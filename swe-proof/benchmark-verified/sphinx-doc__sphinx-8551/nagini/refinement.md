# refinement.md — sphinx-doc__sphinx-8551

The operation-by-operation correspondence between `model.py`'s implementation
(the `make_field_ref` impl region, the `RefNode` constructor, and the deep
`resolve_*` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The node-construction site — `PyXrefMixin.make_xref` (`sphinx/domains/python.py:272-275`)

Gold hunk:
```
 result = super().make_xref(...)
 result['refspecific'] = True
+result['py:module'] = env.ref_context.get('py:module')
+result['py:class'] = env.ref_context.get('py:class')
```

| # | model.py impl op (`make_field_ref` / `RefNode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `target: PSeq[int]` parameter; `RefNode.target` | the `reftarget`/`target` string of the pending_xref | R | dotted name `str` ↔ `PSeq[int]` of segment tokens (mapping.md §2). |
| A2 | `RefNode(target, True, ...)` sets `specific = True` | `result['refspecific'] = True` (unchanged line 274) | I | the prefer-specific flag, set identically pre- and post-patch. |
| A3 | `cur_module`/`cur_class: Optional[PSeq[int]]` params; `RefNode.ctx_mod = cur_module`, `ctx_cls = cur_class` | `result['py:module'] = env.ref_context.get('py:module')`, `result['py:class'] = env.ref_context.get('py:class')` | R | the surrounding namespace context, `str`/`None` ↔ `PSeq[int]`/`None` (mapping.md §2). The model passes the current context positionally; the patch reads it from `env.ref_context`. The added lines ARE this attachment; the prepatch omits them (attaches `None, None`). |

## B. The call-site plumbing — `DocFieldTransformer.transform` (`sphinx/util/docfields.py:293-298`)

Gold hunk:
```
 xrefs = typed_field.make_xrefs(
     typed_field.typerolename, self.directive.domain, target,
     contnode=content[0],
+    env=self.directive.state.document.settings.env
 )
```

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `make_field_ref` is *called with a real `cur_module`/`cur_class`* (its precondition `cur_module is not None`), i.e. the env/context is threaded in | adding `env=self.directive.state.document.settings.env` to the `make_xrefs` call | R | site B is the *means* by which site A receives a non-`None` `env`: without `env`, `make_xref` (hunk A) would read context from `env=None` and attach nothing. The model collapses "thread the env so context is available" into "`make_field_ref` is given the live context" — a type/dataflow refinement of the same edit. The prepatch models the joint defect (no context reaches the node). |

Hunks A and B are two halves of ONE observable change: the implicit
type/`:type:`/`:rtype:` xref node must carry the current `(py:module, py:class)`
context. Hunk A copies it onto the node; hunk B supplies the `env` that hunk A
needs in the info-field code path. The single modeled function `make_field_ref`
+ its `cur_module is not None` precondition capture the composition; one
prepatch (context dropped) is the joint differential witness.

## C. The resolution the change fixes — deep model ↔ `find_obj(searchmode=1)`

The behavioural payoff lives in the postcondition

```
resolve_count(node.ctx_mod, node.ctx_cls, node.target, objs) == 1
resolve_name (node.ctx_mod, node.ctx_cls, node.target, objs) == cur_module + target
```

| # | model.py construct | patch.diff correspondence | tag | justification |
|---|---|---|---|---|
| C1 | `resolve_count` / `resolve_name` / `has_ctx_candidate` / `first_suffix` / `member` / `count_suffix` / `suffix_eq` (pure region) | `PythonDomain.find_obj(env, modname, classname, name, type, searchmode=1)` (`python.py:1236-1290`), unchanged by the patch but fed the node's `py:module`/`py:class` (`resolve_xref`, lines 1295-1299) | A-reference | the resolver is an **unchanged callee**, modeled DEEPLY (the suffix/membership cascade), NOT behind a consumed axiom. There is no `find_obj` `@ContractOnly`. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `find_obj` in searchmode 1 and asserts `len(find_obj(...)) == resolve_count` and the single match `== resolve_name`, over the issue scenario + 20000 fuzz + an exhaustive subset (mapping.md §3). |

The discriminating content of the change: with the context attached
(`ctx_mod = cur_module`), the cascade hits the `module + name` branch and
returns the **single** contextual object `cur_module + target`; with the context
dropped (`None`, the pre-patch), the cascade skips every qualified branch and
falls to the suffix fallback, which returns `count_suffix(objs, target) ≥ 2`
candidates — the *"more than one target found for cross-reference"* WARNING in
the issue. `model_prepatch.py` reproduces the dropped context
(`RefNode(target, True, None, None)`) and **fails** the postconditions
`Result().ctx_mod is cur_module` and `resolve_count(...) == 1`, which is exactly
the spec sensing the change (G-DIFF).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. There is **no consumed axiom**
(`# axioms-start` is empty): the only callee involved, `find_obj`, is unchanged
and modeled **deeply** (the `resolve_*` cascade), validated against the real
callee by G-AX as an **A-reference** — not consumed via `Ensures`. The operation
that genuinely *changed* — attaching the surrounding `(module, class)` context
to the implicit field xref node (hunks A + B) — is modeled directly as the
node's `ctx_mod`/`ctx_cls` fields (step A3/B1), not hidden behind an axiom.

## E. verify(model) ⇒ resolved

`make_field_ref` verifies only if the node it returns records the surrounding
context (`ctx_mod is cur_module`, `ctx_cls is cur_class`, step A3) AND that
context makes the prefer-specific resolution unique on the contextual object
(`resolve_count == 1`, `resolve_name == cur_module + target`, step C1). By R
(dotted `str` ↔ `PSeq[int]` segments; `Optional` context; `objects` key set) the
verified node equals the `pending_xref` the gold `make_xref` builds with
`py:module`/`py:class` attached and fed by the gold `env=` plumbing (hunks A+B);
by G-AX the deep model `resolve_*` equals the real `find_obj` in searchmode 1
(A-reference). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited resolver — and the gold
patch resolves (G-RESOLVE: F2P `test_info_field_list` passes, asserting the
pending_xref carries `py:module="example"`, `py:class="Class"`). The trust
points are exactly the two of PLAN §1.1: deep-model/refinement fidelity (this
document, G-EQ) and callee soundness (G-AX) — here both concern the single
unchanged callee `find_obj`.
