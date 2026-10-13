# mapping.md — django__django-11163

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e6588aa4e793b7f56f4cadbfa155b581e0efc59a`, states the type
abstraction, and records callee provenance. This bundle consumes **no
`@ContractOnly` axiom** — the changed operation is pure membership/structure
logic over a record's attributes and two optional lists, modelled deeply; the
behavioural facts the deep model rests on are validated against the real Django
filtering loop by `axiom_check.py` (G-AX).

Repo file under change: `django/forms/models.py` (single one-line hunk at line
86, inside the record-projection helper at `django/forms/models.py:69`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `project_record(names, edit, allowed, blocked)` | the record-projection helper `django/forms/models.py:69` (the function whose loop body the gold hunk edits, line 86) | the changed function: builds the projected key set; model symbol named off the repo name to keep the spec view leakage-clean (G-LEAK) |
| `names: List[int]` + `edit: List[int]` | the iterated attribute stream `chain(opts.concrete_fields, opts.private_fields, opts.many_to_many)` — `models.py:83`; per attribute `f` the loop reads `f.name` (`models.py:86,88,90`) and `getattr(f, 'editable', False)` (`models.py:84`) | the record's attributes abstracted to two equal-length parallel streams: a name code per attribute and a 0/non-0 editability flag per attribute, in iteration order |
| `allowed: Optional[List[int]]` | the `fields` parameter — `models.py:69` default `None`, tested at `models.py:86` | the optional restriction list; `None` ⟺ absent, a (possibly empty) list ⟺ present |
| `blocked: Optional[List[int]]` | the `exclude` parameter — `models.py:69` default `None`, tested at `models.py:88` | the optional removal list; `None` ⟺ absent, a (possibly empty) list ⟺ present |
| `contains(s, x)` | the membership tests `f.name not in fields` (`models.py:86`) and `f.name in exclude` (`models.py:88`) | unchanged `in`/`not in` membership over the optional lists |
| `passes_restriction(allowed, n)` | the restriction filter `if fields is not None and f.name not in fields: continue` (`models.py:86`, the gold-fixed line) | the changed keep decision: presence (`is not None`) gating, not truthiness |
| `is_removed(blocked, n)` | the removal filter `if exclude and f.name in exclude: continue` (`models.py:88`, unchanged) | the removal keep decision: truthiness gating (present AND non-empty) |
| `projection(names, edit, allowed, blocked)` | the whole loop body's keep-and-collect decision (`models.py:83-90`) → the key set of `data` | the deep model of the projected key set (the F2P-observed behaviour) |
| `Requires(MustTerminate(2))` / `Invariant(MustTerminate(i))` | the finite `for f in chain(...)` traversal (`models.py:83`) terminating at `return data` (`models.py:91`) | the totality obligation: the helper's loop is over a finite field chain doing bounded per-field work with no recursion and no unbounded construct, so it returns on EVERY input (`fields=[]` included, where every attribute is skipped and an empty dict is returned). Carried in the model as a method-level obligation consumed by the impl loop's strictly-decreasing measure `i`. |

Pre-patch repo state the change fixes (for the refinement audit, not referenced
from the consumer spec view): `models.py:86` read
`if fields and f.name not in fields:`, so a present-but-empty `fields=[]` was
falsy and imposed no restriction, leaking every editable, non-removed attribute.
The gold hunk changes it to `if fields is not None and f.name not in fields:`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| each iterated field object `f` | one position `k` in the parallel streams `names[k]` (a name code), `edit[k]` (1 iff `getattr(f,'editable',False)` is truthy else 0) | `str` field names are banned in Nagini, so each name is an `int` code (an injective code per distinct `f.name`); the only field attributes the three filters read are `f.name`, `f.editable` — both carried. Iteration order preserved (`names`/`edit` are in `chain(...)` order). `len(names) == len(edit)` (one editability flag per attribute). |
| `fields` / `exclude` (Python `list` or `None`) | `Optional[List[int]]` of name codes | `None` ⟺ `None`; a present list ⟺ a non-`None` `List[int]` carrying the same name codes; the empty list ⟺ a present `List[int]` of length 0. The `is None` vs present-empty distinction — the crux of the change — is preserved exactly by `Optional`. |
| `f.name not in fields` / `f.name in exclude` | `contains(ToSeq(list), n)` | `in`/`not in` over a `list` ⟺ `contains` over the `PSeq[int]` view; membership is order- and multiplicity-insensitive, matching Python `in`. |
| `if fields is not None and f.name not in fields: continue` | `passes_restriction`: `allowed is None` ⇒ keep; else keep iff member | presence gating: absent list keeps all, present (even empty) list keeps only members. |
| `if exclude and f.name in exclude: continue` | `is_removed`: `blocked is None or len==0` ⇒ not removed; else removed iff member | Python truthiness of a list: `None`/empty ⇒ falsy ⇒ the whole `and` short-circuits ⇒ never removed; non-empty ⇒ removed iff member. |
| `data[f.name] = f.value_from_object(instance)` and the observation `sorted(model_to_dict(...))` | appending the surviving name code to `Result()` | the FAIL_TO_PASS test observes the KEY SET (`sorted(...)` of the returned dict), so the projected key sequence — built in source order — is the complete tested behaviour. `f.value_from_object(instance)` is an UNCHANGED per-field value callee whose RESULT the keyset observation never inspects; it is not modelled (it cannot affect which keys appear). |

`str`/rich field objects are banned/intractable in Nagini, so the attribute
stream is carried as parallel `List[int]` and the specification is phrased over
`PSeq[int]` via `ToSeq`.

## 3. Callee provenance — NO consumed axioms

There is **no `@ContractOnly` axiom** in `model.py` (the `axioms` region is
empty). The changed operation is Django's own membership/filtering logic,
modelled deeply:

- `passes_restriction` / `is_removed` / `projection` spell out the three filters
  and the per-attribute keep decision as a verified fold + loop (model.py pure +
  impl regions). Their faithfulness to the real loop is audited by refinement.md
  (G-EQ) and validated executably by axiom_check.py / G-AX, which transcribes the
  real post-patch filtering loop (`if not editable / if fields is not None and
  name not in fields / if exclude and name in exclude`) VERBATIM over lightweight
  field objects and asserts the deep model agrees with it.

- The only repo callees the changed code invokes are the unchanged builtins
  `getattr`, `in`/`not in`, and `f.value_from_object` (per-field value
  extraction, `django/db/models/fields/__init__.py`); none is on the keyset
  observable's critical path for membership, and none is changed by the patch, so
  none is axiomatized. No flag dependencies.

**Soundness check (G-AX):** `axiom_check.py` imports only the standard library
(`itertools.chain`, `random`); it requires no database connection or settings
configuration. It reconstructs the real post-patch filtering loop verbatim over
`FakeField` objects (each exposing only `name`, `editable`, `value_from_object`
— the sole attributes the filters read), and asserts (over a boundary battery +
20000 fuzz configurations spanning restriction absent/empty/subset × removal
absent/empty/subset × non-editable attributes) that the deep model `projection`
yields the same projected names; and that the pre-patch loop
(`if fields and ...`) diverges on EXACTLY the present-empty restriction list —
the clause `model_prepatch.py` fails on. Exit 0 iff sound.
