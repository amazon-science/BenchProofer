# mapping.md — sphinx-doc__sphinx-8638

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 4b452338f914d4f6b54704222d70ae8a746e3db5`, states the type
abstraction, and gives the provenance of each deep-model reference (the real
callee the deep model is validated against by axiom_check.py / G-AX).

Repo file under change: `sphinx/domains/python.py` (one configuration line).
The behaviour the change controls lives in the unchanged renderer
`sphinx/util/docfields.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_variable_field_entry(type_role, type_target_is_null)` | the rendering of one typed `variable` field entry: `TypedField.make_field` / its inner `handle_item` (`sphinx/util/docfields.py:172-204`) **driven by** the `'variable'` `PyTypedField` configuration in `PyObject.doc_field_types` (`sphinx/domains/python.py:352-357`) | the modeled changed behaviour: how an attribute/instance-variable field entry is rendered under its configured roles. The single configuration value the gold patch edits (the name-token `rolename`) is the `name_role` literal in this function's impl. |
| `make_xref(role)` *(deep model — A-reference)* | `Field.make_xref(rolename, domain, target, …)` (`sphinx/util/docfields.py:63-73`) | pure node-kind decision for one token: a present (truthy) role yields a cross-reference carrying that role; an absent (falsy) role yields a plain inline node. Validated `== Field.make_xref` by axiom_check.py (G-AX), NOT consumed as a `@ContractOnly` axiom. |
| `rendered_role(role, target_is_null)` *(`@Pure` deep model — A-reference)* | the role rewrite in `PyTypedField.make_xref` (`sphinx/domains/python.py:326-333`): `if rolename == 'class' and target == 'None': rolename = 'obj'` before delegating to `super().make_xref` | the role a token is actually RENDERED under, as opposed to the role its slot is configured with: the type-reference role gives way to the fallback object role when the token's target names the null value; identity in every other case, absent roles included. UNCHANGED code the gold patch does not touch, on the type-token path, and therefore part of what the type-token postcondition must state. Validated `== PyTypedField.make_xref`'s rendered role by axiom_check.py (G-AX §3.3), NOT consumed as a `@ContractOnly` axiom. |
| `FieldNode` (fields `is_xref`, `reftype`) | a rendered token node: either `addnodes.pending_xref` (a cross-reference, `is_xref=True`, `reftype=<role>`) or a plain inline node such as `addnodes.literal_strong` / `nodes.Text` (`is_xref=False`) | minimal node carrying only the two touched observations (whether the token links, and which reference kind it carries). |

The pre-patch repo value the change removes (for the refinement audit, not
referenced from the consumer spec view): the keyword argument `rolename='obj'`
on the `'variable'` `PyTypedField` (`sphinx/domains/python.py:352-357`). The
`'parameter'` `PyTypedField` (`python.py:352-356`) has likewise never set a name
`rolename`, which is why its parameter names already render as plain
`literal_strong` (the existing `test_info_field_list` baseline).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a field's configured role (`rolename` / `typerolename`): a `str` or `None` | `int` role code | only two properties of a role are observed by the rendering decision: its **presence** (a truthy `str` vs `None`/`''`) and, when present, its **identity** (used as the cross-reference `reftype`). `int 0` ↔ an absent role (`None`/`''`); a non-zero code ↔ a present role identified by that code; the code value ↔ the role identity carried into `reftype`. (`str` indexing is banned in Nagini; the rendering decision is purely truthiness + identity, both faithfully captured by the code — see refinement.md A1/A2 and the executable check.) |
| a token's `target` (a `str`) | the `bool` `..._is_null` parameter | the rendering observes exactly one property of a target: whether it is the spelling of the null value (`target == 'None'`), which is the guard of the role rewrite in `PyTypedField.make_xref`. `True` ↔ the target text is exactly `'None'`; `False` ↔ any other target, the near misses `'NoneType'`/`'none'`/`'None_'` included (all three are probed on the `False` side by axiom_check.py and conformance_check.py, so the exact-match test cannot be loosened). Nothing else about a target — its text, its module/class context, the `.`/`~` trimming — reaches either observable. |
| a rendered token node (`pending_xref` vs plain inline) | `FieldNode` with `is_xref: bool`, `reftype: int` | `is_xref` ↔ `isinstance(node, addnodes.pending_xref)`; `reftype` (when `is_xref`) ↔ `node['reftype']`. The token's text is not behaviour the change observes and is abstracted away. |
| the field entry paragraph (`name` token then parenthesised `type` token) | `List[FieldNode]` of length 2 (`[name_node, type_node]`) | `Result()[0]` ↔ the name token built by `make_xrefs(self.rolename, …)` (`docfields.py:176`); `Result()[1]` ↔ the type token built by `make_xrefs(self.typerolename, …)` (`docfields.py:186`). |

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `make_xref` deep model ↔ `Field.make_xref` (A-reference)
**Callee:** `sphinx.util.docfields.Field.make_xref` (`docfields.py:63-73`),
reached by `PyTypedField` through `super()` (the `PyXrefMixin` override only adds
`refspecific`/module/class context and `.`/`~` target trimming on top of the same
node — it does not change the node KIND; the `PyTypedField` override rewrites the
ROLE before delegating, which is §3.3's `rendered_role`, not the node kind).
Source at base_commit:

```python
def make_xref(self, rolename, domain, target, innernode=..., contnode=None, env=None):
    if not rolename:
        return contnode or innernode(target, target)        # plain inline node
    refnode = addnodes.pending_xref('', refdomain=domain, refexplicit=False,
                                    reftype=rolename, reftarget=target)
    refnode += contnode or innernode(target, target)
    if env:
        env.get_domain(domain).process_field_xref(refnode)
    return refnode
```

The node KIND is decided solely by `if not rolename`: a falsy role → a plain
inline node (no `pending_xref`); a truthy role → a `pending_xref` carrying
`reftype=rolename`. This is exactly `make_xref(role)`'s contract
(`is_xref == (role != 0)`, and `reftype == role` when linking). The model omits
the `env`-dependent `process_field_xref` step: it leaves the node kind and
`reftype` untouched, which are the only observations the F2P test and the model
make.

### 3.2 `build_variable_field_entry` ↔ the `'variable'` `TypedField.make_field` (A-reference)
**Callee:** `sphinx.util.docfields.TypedField.make_field` / its `handle_item`
(`docfields.py:172-204`), driven by the `'variable'` `PyTypedField`
configuration (`python.py:352-357`). `handle_item` builds the name token with
`make_xrefs(self.rolename, …)` (line 176) and the type token with
`make_xrefs(self.typerolename, …)` (line 186); `make_xrefs` delegates each token
to `make_xref` — for a `PyTypedField` that is the override of §3.3 followed by
`Field.make_xref` (§3.1). Post-patch the `'variable'` field has **no** `rolename`
(so `self.rolename is None` → name token plain) while `typerolename='class'`
(so the type token is a `pending_xref` whose `reftype` is `'class'` on an
ordinary type target and `'obj'` on the type target `'None'`, per §3.3). That is
exactly `build_variable_field_entry`'s postcondition
(`Result()[0].is_xref is False`, `Result()[1].is_xref is True`,
`Result()[1].reftype == rendered_role(type_role, type_target_is_null)`).

### 3.3 `rendered_role` ↔ `PyTypedField.make_xref`'s role rewrite (A-reference)
**Callee:** `sphinx.domains.python.PyTypedField.make_xref`
(`python.py:326-333`). Source at base_commit:

```python
class PyTypedField(PyXrefMixin, TypedField):
    def make_xref(self, rolename, domain, target, innernode=nodes.emphasis,
                  contnode=None, env=None) -> Node:
        if rolename == 'class' and target == 'None':
            # None is not a type, so use obj role instead.
            rolename = 'obj'
        return super().make_xref(rolename, domain, target, innernode, contnode, env)
```

The role the token is RENDERED under is therefore not the configured role in
general: on the type target `'None'` the type-reference role `'class'` becomes
the fallback `'obj'`, and every other (role, target) pair passes through. That is
exactly `rendered_role(role, target_is_null)`
(`role == TYPE_ROLE and target_is_null` → `NULL_ROLE`, else `role`) under the
role-code and target-`bool` refinements of §2, with `TYPE_ROLE ↔ 'class'` and
`NULL_ROLE ↔ 'obj'`. This code is UNCHANGED by the gold patch and sits on the
type-token path, so the model's type-token `reftype` clause has to be stated
through it: a clause pinning the configured type-role unconditionally would
assert `'class'` on the `:vartype: None` input where the real renderer emits
`'obj'`.

**Soundness check (G-AX):** `axiom_check.py` (a) runs the real
`Field.make_xref` over falsy (`None`, `''`) and 12 truthy role strings,
asserting the node is a `pending_xref` **iff** the role is truthy and that its
`reftype` equals the role; (b) runs the real `PyTypedField.make_xref` over 14
roles × 10 targets (= 140 observations), asserting the role read back off the
node equals `rendered_role`'s — the null target `'None'`, the near misses
`'NoneType'`/`'none'`/`'None_'`, six ordinary targets, and an absent role on all
of them — and that exactly ONE of those pairs normalises, so a model that
normalised too eagerly or not at all would fail; (c) runs the real
`TypedField.make_field` over the **actual** post-patch `'variable'`
configuration built by the real `PyTypedField` class (no `rolename`,
`typerolename='class'`) and asserts the name token is a plain
`addnodes.literal_strong` (not a `pending_xref`) while the type token is a
`pending_xref` under the NORMALISED role — `'class'` for `:vartype: int`,
`'obj'` for `:vartype: None` — and, for the pre-patch `rolename='obj'`
configuration, that the name token instead becomes a `pending_xref` (confirming
the model discriminates). It imports only the standard library plus the repo's
own `sphinx.util.docfields` / `sphinx.domains.python` / `sphinx.addnodes` (no
full app). Exit 0 iff sound. There is **no consumed `@ContractOnly` axiom** in
this bundle.

## G-CONF (differential conformance)

`conformance_check.py` refutes the refinement leg: it diffs the SHADOW (the
`# impl-start` / `# impl-end` regions of `model.py` — `build_variable_field_entry`,
`make_xref`, and `FieldNode.__init__` — plus the `# pure-start` / `# pure-end`
region carrying `rendered_role` and the two role identities, copied verbatim with
only the contract calls and the `@Pure` decorator stripped) against the ORACLE
(the REAL patched repo function of §1:
`sphinx.util.docfields.TypedField.make_field` / its inner `handle_item`,
**called**, not transliterated, on the live `'variable'` `PyTypedField` read out
of `PyObject.doc_field_types` at `sphinx/domains/python.py:352-357` after the
gate applies the gold patch). The `pure` region is diffed even though it is spec
rather than impl: it is the leg on which the type token's reference kind is
claimed, so it is the leg that must be refutable against real code. Because the
field objects are the real `PyTypedField` (the live one, or one built by
`type(live_field)`), the real `PyTypedField.make_xref` override of §3.3 is in the
call path on every probe, so the normalisation is exercised by repo code rather
than assumed. No `@ContractOnly` axiom is consumed (§3), and the model uses no
`PSeq`/`ToSeq` carrier, so no axiom or sequence shim is needed.
The only stand-in is the `env` object (`ref_context` + a `get_domain` whose
`process_field_xref` is a no-op, matching `Domain.process_field_xref`'s `pass`
body at `sphinx/domains/__init__.py:311-315`); it touches neither the node kind
nor `reftype`, the two observables of the §2 bridge.

The `name_role = 0` literal of the impl is the model's CLAIM about the patched
configuration; the oracle reads that configuration live from the repo instead of
restating it, so the check is capable of failing — run against the unpatched tree
it reports `shadow=[(False,0),(True,1)] oracle=[(True,2),(True,1)]` on the first
boundary case (the real name token is then an `obj` `pending_xref`). The
normalisation leg is capable of failing independently: with the shadow's
`rendered_role(...)` call replaced by the bare `type_role` (i.e. the
normalisation dropped) the check reports
`type_target='None' (is_null=True) shadow=[(False,0),(True,1)]
oracle=[(False,0),(True,2)]` and exits 1.

Bridge, inverting §2: model role code `0` ↔ an absent role (`None`/`''`), a
non-zero code ↔ the pool role string interned to that code (a bijection, so role
identity round-trips — and the interning of `'class'` → `TYPE_ROLE` and `'obj'` →
`NULL_ROLE` is asserted at module level, so the normalisation leg cannot silently
stop testing what the model claims); the target ↔ the `..._is_null` bool via
`target == 'None'`; a rendered token ↔ `(isinstance(node,
addnodes.pending_xref), interned node['reftype'])`, with code `0` for a plain
inline node; the entry paragraph ↔ the length-2 `List[FieldNode]`, extracted
from `handle_item`'s asserted `[name, ' (', type, ')', ' -- ', content]` layout.
Inputs stay inside `Requires(type_role != 0)` (the type role is always a
non-empty role string) and inside the modeled two-token entry (identifier-ish
targets, since `make_xrefs` splits on `[](),`/`or`). The literal target `'None'`
is **in** the domain on both the name and the type axis and is probed at every
role identity: it is the target on which the role rewrite of §3.3 is observable,
so excluding it would leave the normalisation leg unrefuted.

- **Inputs:** 100000 checks — 2732 boundary entries (the exact F2P `:var int
  attr:` shape on the unmodified live field object first, then the same live
  object on the null type target `:vartype: None`, then every pool role identity
  × boundary target pairs × descriptions, the target lists including `'None'` and
  the near misses `'NoneType'`/`'none'`/`'None_'`) + 97118 seeded fuzz entries,
  of which 9638 draw the null type target deliberately (a random identifier is
  essentially never exactly `'None'`, so the draw is forced rather than left to
  chance) + 150 token-level probes of the shadow's `rendered_role`-then-
  `make_xref` composition over falsy (`None`, `''`) and truthy roles × null /
  near-miss / ordinary targets, which pin both the `role == 0` branch and both
  sides of the normalisation directly against the real `PyTypedField.make_xref`.
  Both shadow branches are taken on every entry input (name token `role == 0`,
  type token `role != 0`).
- **Pinned seed:** `SEED = 86380` (module constant `SEED` in
  `conformance_check.py`).
- **Verdict:** exit 0 iff zero disagreements; on a disagreement the input and
  both outputs are printed and the exit status is 1.
