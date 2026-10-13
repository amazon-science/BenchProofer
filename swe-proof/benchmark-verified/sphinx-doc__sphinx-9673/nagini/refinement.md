# refinement.md — sphinx-doc__sphinx-9673

The operation-by-operation correspondence between `model.py`'s implementation
(the `augment_return_typefield` and `name_is_return_key` impl regions, plus the
deep `has_return_description` / `has_return_type` folds) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-consumed** (the
proof uses an axiom's `Ensures`), **A-reference** (a deep model is validated
== a real callee by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There are **no consumed axioms and no A-reference checks** — the changed
operation is pure structural logic, modeled deeply. Every row below is R or I.

## A. Hunk 1 — recognise the plural return-description spelling (the F2P behaviour)

Gold hunk (`sphinx/ext/autodoc/typehints.py:152`, first loop of
`augment_descriptions_with_types`):
```
-        elif parts[0] == 'return':
+        elif parts[0] in ('return', 'returns'):
             has_description.add('return')
```
and the unchanged emission block it feeds (`typehints.py:168-173`):
```python
if 'return' in annotations:
    if 'return' in has_description and 'return' not in has_type:
        node += <rtype field>
```

| # | model.py impl op (`augment_return_typefield`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `field_kinds: List[int]` | the `node` `field_list` iterated by `for field in fields` | R | each `nodes.field` ↦ its leading-token code; list `+`/`drop`/index ↔ field iteration (mapping.md §2). Read-only ⇒ `Acc(list_pred(field_kinds), 1/2)` required AND ensured. |
| A2 | backward loop classifying each `c = field_kinds[i-1]`; `c == 2 or c == 3 ⇒ described = True` | the first loop branch `elif parts[0] in ('return', 'returns'): has_description.add('return')` | R + I | the leading-token compare against the two spellings ↔ the int compare `c == 2 or c == 3` (the two return-description codes). `has_description.add('return')` is the set-membership the model carries as the boolean `described`; the loop computes `described == has_return_description(ToSeq(field_kinds))` (proven invariant). |
| A3 | `c == 4 ⇒ typed = True` | the first loop branch `elif parts[0] == 'rtype': has_type.add('return')` | R + I | the `'rtype'` token ↦ code 4; `has_type.add('return')` ↔ the boolean `typed == has_return_type(ToSeq(field_kinds))`. Unchanged by the patch, modeled for faithfulness of the decision. |
| A4 | `return_annotated` | `'return' in annotations` | R | the return annotation is stored under literal key `'return'`; membership ↔ the boolean (mapping.md §2). |
| A5 | `if return_annotated: if described and not typed: return True; return False` | `if 'return' in annotations: if 'return' in has_description and 'return' not in has_type: node += <rtype field>` | I | identical control flow / boolean structure; the appended rtype node ↔ the `True` Result (mapping.md §2). |

The discriminating content — the plural spelling `:returns:` must count as a
return description, identically to `:return:` — lives in
`has_return_description(kinds)` returning True on a code-3 field (model) ⇔
`parts[0] in ('return', 'returns')` (real). Pre-patch the real code recognized
only `parts[0] == 'return'`; `model_prepatch.py` reproduces that (the loop sets
`described` only on `c == 2`) and **fails** the loop invariant
`described == has_return_description(ToSeq(field_kinds).drop(i))` — exactly the
spec sensing the change (G-DIFF). This is the behaviour the F2P test
`test_autodoc_typehints_description_no_undoc` observes: a function documented
with `:returns:` must still emit a "Return type:" section.

## B. Hunk 2 — skip the return name (either spelling) in the param back-fill loop

Gold hunk (`sphinx/ext/autodoc/typehints.py:159`, the
`for name in annotations` back-fill loop):
```
-        if name == 'return':
+        if name in ('return', 'returns'):
             continue
```

| # | model.py construct (`name_is_return_key`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `name`, `return_key_a`, `return_key_b`: `int` ids | the annotated `name`, and the two return spellings `'return'`/`'returns'` | R | string-equality ↔ int-equality; the two return spellings ↦ `return_key_a`/`return_key_b` (mapping.md §2). |
| B2 | `Result() == (name == return_key_a or name == return_key_b)` and the `if name == return_key_a or name == return_key_b: return True` impl | `if name in ('return', 'returns'): continue` | I | the disjunction over the two spellings ↔ the membership test; the `True` Result ↔ taking the `continue` (skip) branch. |

Pre-patch the real code skipped only `name == 'return'`; `model_prepatch.py`
reproduces that (`name_is_return_key` checks only `return_key_a`) and **fails**
its byte-identical postcondition `Result() == (name == return_key_a or name ==
return_key_b)`. Hunk 2 is a defensive consistency change (the annotation key
is in practice always the literal `'return'`, never `'returns'`, so no test
exercises it independently); it is modeled for skeleton faithfulness, not as a
separate independently-observable F2P behaviour. The single
`model_prepatch.py` therefore reverts BOTH hunks (a faithful pre-image) and
fails on hunk 1's invariant (the tested behaviour) AND hunk 2's postcondition.

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The one operation that genuinely *changed* — the
recognition of the plural return-description spelling as a synonym of the short
one, and the resulting emission decision — is modeled **deeply** (the spelled-
out folds `has_return_description` / `has_return_type` and the two verified
contracted functions). There is **no consumed `@ContractOnly` axiom** and **no
A-reference deep-model check**: the change touches only pure integer/sequence
classification logic; no unchanged library callee is invoked inside any
`Ensures`. `axiom_check.py` is therefore a structural cross-check (the model's
decision == a direct re-implementation of the patched return-classification +
emission logic over boundary + fuzz field-lists), not an in-container callee
execution.

## D. verify(model) ⇒ resolved

`augment_return_typefield` verifies only if its Result equals
`return_annotated ∧ has_return_description(field_kinds) ∧ ¬has_return_type(...)`
with BOTH return-description spellings (codes 2 and 3) counted (A2/A5), and
`name_is_return_key` only if it skips the return name under either spelling
(B2). By R (field-list ↔ `List[int]` of codes, annotation membership ↔ bool,
appended node ↔ True) the verified decision equals the gold
`augment_descriptions_with_types` return path on every tested field-list. The
gold patch resolves (G-RESOLVE). The guarantee rests on no axiom trust point
here — only refinement fidelity (this document, G-EQ); there is no G-AX trust
point because there are no consumed axioms.
