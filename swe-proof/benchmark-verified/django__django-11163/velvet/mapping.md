# mapping.md — django__django-11163

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = e6588aa4e793b7f56f4cadbfa155b581e0efc59a`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance and flag dependencies.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectModelFields (candidates) (selector) (excl)` | `model_to_dict(instance, fields=None, exclude=None)` — `django/forms/models.py:69` (the field-collection `for` loop, body lines 84–91) | the modeled changed function (builds a name→value dict, gated by the two filter knobs) |
| `candidates : List Int` | the candidate fields the loop iterates: `chain(opts.concrete_fields, opts.private_fields, opts.many_to_many)` restricted to those with `getattr(f, 'editable', False)` truthy — keyed by `f.name` (`models.py:84-86`) | the editable candidate field names |
| `selector : Option (List Int)` | the `fields` parameter (`models.py:69`, used at line 87) | optional list of names to keep; `None` ↔ `none`, a Python list ↔ `some [...]` |
| `excl : List Int` | the `exclude` parameter (`models.py:69`, used at line 89) | list of names to drop |
| `keep (sel) (excl) (n)` | the combined per-field guard `if fields is not None and f.name not in fields: continue` (line 87, post-patch) and `if exclude and f.name in exclude: continue` (line 89) | pure spec: whether one candidate name survives both filters |
| `selectNames (sel) (excl)` | the names surviving the whole loop (the keys placed into `data`, line 90) | pure spec: the kept-name list, in candidate order; modeled DEEPLY (no axiom) |

The only behaviour the patch changes is the `fields` guard on line 87: pre-patch
`if fields and f.name not in fields` (a truthiness test on `fields`) → post-patch
`if fields is not None and f.name not in fields` (an explicit `is not None` test).
The `exclude` guard on line 89 is **unchanged** and is modeled faithfully as the
`n ∉ excl` conjunct of `keep` (so the spec pins the unchanged frame too).

There is **no unchanged library callee** the proof must axiomatize: the whole
decision is a pure boolean function of the three inputs. `value_from_object`
(line 90) produces the dict *values*, not the *key set* the F2P test observes
(`sorted(model_to_dict(...))` compares keys), so it is outside the modeled
behaviour and is not referenced — see §3.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the ordered editable candidate field names (`f.name` for each kept `f`) | `List Int` | each distinct field name ↔ a distinct `Int` identifier; iteration order ↔ list order; `len` ↔ `.length`. Field *identity* (membership, equality) is all the loop's guards observe, so an injective name↔Int coding is faithful. |
| `fields` parameter: `None` or a list of names | `Option (List Int)` | `None` ↔ `none`; a Python list `[a,b,…]` ↔ `some [a',b',…]` under the name↔Int coding. The `Option` is essential: it makes "absent" (`None`) and "present but empty" (`[]`) genuinely different inputs — the discriminator of this bug. |
| `exclude` parameter: `None` or a list of names | `List Int` | `None` and `[]` are observationally identical for `exclude` (`if exclude and …`: both falsy ⇒ no exclusion, and `n ∈ []` is false anyway), so both map to `[]`; a list maps elementwise. mapping note: the `exclude` guard is unchanged by the patch. |
| `f.name in / not in <list>` | `n ∈ / ∉ <List Int>` | Python `in` on a list of names ↔ Lean `∈` on `List Int` under the coding. |
| the returned dict's KEY SET, `sorted(model_to_dict(...))` (what F2P observes) | `out : List Int` (the kept names) | the test compares the sorted key list; `value_from_object` values are not observed. `out` is the kept names in candidate order; sorting is applied on both sides in G-CONF. |

## 3. Callee provenance / no axioms

This bundle has **no axioms** and **no deep-model references to a library
callee** (cf. the no-axiom exemplars django__django-16527 / -13670). The changed
operation — the field-selection guard — is a pure boolean computation over the
function's own parameters, modeled deeply by `keep` / `selectNames`. The proof
consumes no `axiom`; `axiom_check.py` is therefore absent (G-AX: not applicable —
there is no unchanged callee whose contract the proof relies on).

`value_from_object(instance)` (line 90, unchanged) computes each kept field's
*value*. It is NOT modeled: the F2P / added tests assert on the dict's KEY set
(`sorted(model_to_dict(bw, fields=[])) == []`, etc.), which depends only on which
names survive the two guards — exactly what `selectNames` pins. Modeling the
values would axiomatize an unchanged callee with no bearing on the tested
behaviour (directive 7: no dead axioms), so it is deliberately omitted; the
refinement (refinement.md A/R rows) records this as an R-identity on the value
projection.

### Flag dependencies
None. The selection decision reads only `fields` (the `Option`) and `exclude`
(the list); there is no configuration flag (cf. `html.escape(quote=…)` in the
M1 case). The single relevant distinction is `None` vs `[]` for `fields`, carried
structurally by the `Option`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11163`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`keep` / `selectNames` (all R/I-tagged ops) to Python and compares against the
patched `model_to_dict` behaviour (the key set it returns) over a synthesized
model whose editable field names are controlled per fuzz case. No callee is left
as "the real callee" because there is no A-tagged op.
