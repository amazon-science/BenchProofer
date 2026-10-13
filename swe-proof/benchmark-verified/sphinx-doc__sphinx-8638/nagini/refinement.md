# refinement.md — sphinx-doc__sphinx-8638

The operation-by-operation correspondence between `model.py`'s implementation
(the `make_xref` and `rendered_role` deep models and the
`build_variable_field_entry` impl region) and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). **There is no consumed `@ContractOnly`
axiom in this bundle** — the changed rendering behaviour is modelled deeply.

## A. The change site — the `'variable'` field configuration (`sphinx/domains/python.py:352-357`)

Gold hunk (the one change):
```
-        PyTypedField('variable', label=_('Variables'), rolename='obj',
+        PyTypedField('variable', label=_('Variables'),
                      names=('var', 'ivar', 'cvar'),
                      typerolename='class', typenames=('vartype',),
                      can_collapse=True),
```

The patch removes the `rolename='obj'` keyword from the `'variable'`
`PyTypedField`. This configuration value flows into the unchanged renderer
`TypedField.make_field` → `handle_item` (`docfields.py:172-204`): the entry's
**name** token is built by `make_xrefs(self.rolename, …)` (line 176) and its
**type** token by `make_xrefs(self.typerolename, …)` (line 186); `make_xrefs`
delegates to `Field.make_xref`, whose `if not rolename` branch (`docfields.py:66`)
makes a token a plain inline node when its role is falsy and a `pending_xref`
(carrying `reftype=rolename`) when it is truthy. So removing the name `rolename`
makes the variable-name token render as plain text instead of an `obj`
cross-reference, while the unchanged `typerolename='class'` keeps the type token
a cross-reference.

One further piece of **unchanged** code sits on the type-token path and is
observable in the model's postcondition: `PyTypedField.make_xref`
(`sphinx/domains/python.py:326-333`) rewrites `rolename='class'` to `'obj'` when
the token's `target` is exactly `'None'` ("None is not a type, so use obj role
instead"). The type token of a `'variable'` entry therefore links under
`'class'` on an ordinary type target and under `'obj'` on `:vartype: None`. The
model states its type-token guarantee through `rendered_role`, the deep model of
that rewrite (step A3b), so the postcondition matches the real renderer on both
targets rather than only on the ordinary one. The gold patch does not touch this
override; it is preserved by the model so a wrong impl cannot satisfy the spec
by deleting it.

| # | model.py impl op | patch.diff op (gold) / real callee | tag | justification |
|---|---|---|---|---|
| A1 | `make_xref(role)` returns a `FieldNode` with `is_xref == (role != 0)` and, when linking, `reftype == role` | `Field.make_xref(rolename, …)`: `if not rolename: return <plain inline>` else `return pending_xref(reftype=rolename, …)` (`docfields.py:63-73`) | **A-reference** | the node-kind decision is modelled **deeply** (spelled out in `make_xref`), not behind a `@ContractOnly` axiom the proof consumes. The role `str`/`None` ↔ `int` code is an R-refinement on the only observed properties (presence + identity; mapping.md §2). G-AX validates `make_xref == Field.make_xref` over falsy + truthy roles (mapping.md §3.1). |
| A2 | `name_role = 0` (the absent name role); `name_node = make_xref(name_role)` ⇒ `name_node.is_xref is False` | the FIX: the `'variable'` field now has **no** `rolename` (was `'obj'`), so `self.rolename is None` and `make_xrefs(self.rolename, fieldarg, …)` (`docfields.py:176`) produces a plain inline name token | **I** (under R on the role carrier) | the single behavioural delta of the gold patch: the configured name role is removed. `name_role = 0` (model) ⇔ `rolename` absent/`None` (real); both make `make_xref` take the falsy/`role==0` branch → a plain inline node. This is the discriminating step (see §B). |
| A3 | `type_node = make_xref(rendered_role(type_role, type_target_is_null))` with `type_role != 0` ⇒ `type_node.is_xref is True` and `type_node.reftype == rendered_role(type_role, type_target_is_null)` | the UNCHANGED type path: `make_xrefs(self.typerolename, typename, …)` (`docfields.py:186`) with `typerolename='class'` (unchanged by the patch) → a `pending_xref` whose `reftype` is the role `PyTypedField.make_xref` renders the token under | **I** (under R on the role carrier) | the type token still cross-references; `type_role != 0` (model precondition) ⇔ `typerolename='class'` is present (real). The patch does not touch this; the model preserves it so a wrong impl cannot satisfy the spec by also dropping the type link. |
| A3b | `rendered_role(role, target_is_null)` returns the fallback role when `role == TYPE_ROLE and target_is_null`, else `role` | `PyTypedField.make_xref` (`sphinx/domains/python.py:326-333`): `if rolename == 'class' and target == 'None': rolename = 'obj'`, then `super().make_xref(...)` | **A-reference** | UNCHANGED code on the type-token path, modelled **deeply** (the branch is spelled out in the `pure` region), not behind a consumed axiom. The target `str` ↔ `bool` `..._is_null` is an R-refinement on the only property the branch observes (`target == 'None'`; mapping.md §2). G-AX layer 2 validates `rendered_role == PyTypedField.make_xref`'s rendered role over 140 (role, target) observations including the near misses `'NoneType'`/`'none'`/`'None_'` and an absent role on the null target; G-CONF fuzzes it inside the entry-level diff (9638 of 97118 fuzz entries on the null target). Without this step the model's type-token `reftype` clause would assert `'class'` where the real renderer emits `'obj'`. |
| A4 | `par = [name_node, type_node]`; `return par` (length-2 list, name then type) | `handle_item` assembles the paragraph `par` as the name token(s) followed by the parenthesised type token (`docfields.py:174-193`) | **R** | the rendered entry paragraph ↔ a `List[FieldNode]` of the two observed tokens in order (mapping.md §2). The intervening literal `' ('` / `')'` / `' -- '` text and the description content carry no role and are not behaviour the change observes; they are abstracted away. |

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton: its `build_variable_field_entry`
impl sets `name_role = NULL_ROLE` (a present, non-zero role — the
object-reference role `'obj'`) instead of `0`, exactly as the pre-patch
`'variable'` field carried `rolename='obj'`. With the byte-identical frozen spec
it **fails** verification on the postcondition
`Ensures(Result()[0].is_xref is False)`
(`model_prepatch.py:116` — `Assertion (Result()[0].is_xref is False) might not
hold`): a non-zero name role makes the name token a cross-reference, violating
the "name token must be plain" guarantee. That is precisely the behaviour the
F2P test observes: `test_info_field_list_var` asserts the `:var int attr:`
field body begins with `[addnodes.literal_strong, "attr"]` (a PLAIN node) — not
a `pending_xref` — while the type `int` is `[pending_xref, …]`. The spec is
therefore strong enough that no implementation re-introducing a name role can
verify (spec sees the bug).

The companion clauses `Result()[1].is_xref is True` and
`Result()[1].reftype == rendered_role(type_role, type_target_is_null)` pin the
unchanged type cross-reference, so a wrong impl cannot satisfy the spec by
dropping the type link too, nor by collapsing both tokens to plain text, nor by
deleting the role normalisation the real renderer applies on the null type
target (properties.py rivals `rival-skip-normalisation` and
`rival-overeager-normalisation` are rejected by that clause from either side).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the node-KIND decision for the variable-name token (cross-reference
vs plain inline, driven by the presence of the configured role) — is modelled
**deeply** by `make_xref` (the spelled-out `if role != 0` decision), an
**A-reference** validated `== Field.make_xref` by G-AX (mapping.md §3.1). The
unchanged role normalisation on the type-token path is likewise modelled deeply
by `rendered_role` (step A3b), an **A-reference** validated against the real
`PyTypedField.make_xref`. There is **no consumed `@ContractOnly` axiom**: we
never axiomatize the renderer the change affects; the deep models ARE the
decisions. The fix itself (removing the name role) is the **I** step A2 under the
role-carrier R-refinement.

## D. verify(model) ⇒ resolved

`build_variable_field_entry` verifies only if (A2) the name token is NOT a
cross-reference and (A3/A3b) the type token IS a cross-reference carrying the
type-role as normalised against the type target. By R (role `str`/`None` ↔ `int`
code on presence+identity; target ↔ the `..._is_null` bool; the entry paragraph
↔ the two-token list) and the **I** fix step A2, the verified rendering equals
the gold post-patch rendering of the `'variable'` field on the tested input. By
G-AX the deep model `make_xref` equals the real `Field.make_xref` (A-reference
§3.1), `rendered_role` equals the real `PyTypedField.make_xref`'s rendered role
(A-reference §3.3), and the real `TypedField.make_field` over the actual
post-patch `'variable'` config produces exactly the plain-name / normalised-xref-
type pair the model ensures, on the ordinary and the null type target alike
(A-reference §3.2).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited deep models — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-
model/axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
