# refinement.md — django__django-11163

The operation-by-operation correspondence between `model.py`'s implementation
(the `project_record` impl region, plus the deep `projection` /
`passes_restriction` / `is_removed` / `contains` models) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, the proof uses the axiom's `Ensures`, and
**A-reference**, a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — the record-projection helper (`django/forms/models.py:86`)

Gold hunk (single line, inside the loop body at `models.py:83-90`):
```
- if fields and f.name not in fields:
+ if fields is not None and f.name not in fields:
      continue
```

The loop body iterates `chain(opts.concrete_fields, opts.private_fields,
opts.many_to_many)` and, for each attribute `f`, applies three skip filters
(`not editable` → `models.py:84`; the restriction filter → `models.py:86`, the
changed line; the removal filter → `models.py:88`), collecting
`data[f.name] = f.value_from_object(instance)` for survivors.

| # | model.py impl op (`project_record` / deep models) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `names: List[int]`, `edit: List[int]` (parallel, equal-length) | the iterated attribute stream `for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many)`, reading `f.name` and `getattr(f,'editable',False)` | R | each field `f` ↔ position `k`: `names[k]` ↔ `f.name` (str → int code, mapping.md §2), `edit[k]` ↔ `1 if getattr(f,'editable',False) else 0`; iteration order preserved. |
| A2 | parameters `allowed`, `blocked: Optional[List[int]]` | the `fields` / `exclude` parameters | R | `None` ↔ absent, present list (incl. empty) ↔ non-`None` `List[int]` (mapping.md §2). The `is None` vs present-empty distinction is carried exactly by `Optional`. |
| A3 | `e != 0` guard in the loop/`projection` | `if not getattr(f, 'editable', False): continue` (`models.py:84`, UNCHANGED) | R + I | the editability skip, unchanged: a non-editable attribute never survives. `edit[k] != 0` ⟺ `getattr(f,'editable',False)` truthy (mapping.md §2). |
| A4 | `passes_restriction(allowed, n)`: `allowed is None ⇒ True`, else `contains(ToSeq(allowed), n)` | `if fields is not None and f.name not in fields: continue` (`models.py:86`, the GOLD-FIXED line) | A-reference | the changed keep decision is modelled **deeply**: `passes_restriction` IS the predicate "kept by the restriction filter", computed by presence (`is None`) gating plus `contains` membership. There is no consumed axiom — the proof never depends on one. The deep model is validated **== the real post-patch loop** out-of-band: G-AX (axiom_check.py) reconstructs `if fields is not None and f.name not in fields: continue` verbatim and asserts the model agrees on boundary + 20000 fuzz configs. The De-Morgan equivalence: "kept" = `not (fields is not None and name not in fields)` = `fields is None or name in fields` = `passes_restriction`. |
| A5 | `is_removed(blocked, n)`: `blocked is None or len==0 ⇒ False`, else `contains(ToSeq(blocked), n)` | `if exclude and f.name in exclude: continue` (`models.py:88`, UNCHANGED) | A-reference + I | the removal filter, unchanged: Python truthiness of `exclude` (`None`/empty ⇒ falsy ⇒ the `and` short-circuits ⇒ never removed; non-empty ⇒ removed iff member) ⟺ `is_removed`. Validated == the real loop by G-AX. |
| A6 | `contains(ToSeq(list), n)` | `f.name not in fields` / `f.name in exclude` membership | R + I | `in`/`not in` over a `list` ⟺ `contains` over its `PSeq[int]` view (mapping.md §2). |
| A7 | survivor appended: `result = [n] + result` (backward loop ⇒ source order) | `data[f.name] = f.value_from_object(instance)` (`models.py:90`) | R | the observed behaviour is the KEY SET (`sorted(model_to_dict(...))`), so collecting the surviving name code ⟺ inserting the key. `f.value_from_object(instance)` is an unchanged value callee whose result the keyset observation never reads (mapping.md §2), so it is not modelled. |
| A8 | `Ensures(ToSeq(Result()) == projection(ToSeq(names), ToSeq(edit), allowed, blocked))` | the loop's net effect: `data` keyed by exactly the surviving names | A-reference | `projection` is the front-recursive composition of A3–A7 over all attributes; the spec pins the result to it. G-AX validates `projection == real post-patch loop keyset`. |
| A9 | `Requires(MustTerminate(2))` on `project_record`, discharged by the impl loop's `Invariant(MustTerminate(i))` | the loop `for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many)` at `models.py:83` and the `return data` at `models.py:91` | R + I | **totality.** The real helper iterates a FINITE `chain(...)` of field objects, performs only bounded per-field work (two membership tests over finite lists, a `getattr`, one dict store), contains no unbounded construct and no recursion, and reaches `return data` on EVERY input — including `fields=[]`, where the loop body simply `continue`s on each attribute and an empty dict is returned. So "a result is delivered for every admissible input" is TRUE of the real post-patch function on its whole domain, not merely on the gold path. It is load-bearing rather than incidental: the F2P observation `sorted(model_to_dict(bw, fields=[])) == []` is an assertion ABOUT A RETURNED VALUE on exactly the input the change concerns, so a helper that never returns there does not satisfy the reported behaviour however its filters are written. Modelled as the standard obligation pair (a method-level `MustTerminate` consumed by the loop's strictly-decreasing, bounded-below measure `i`). |

The discriminating content of the change — a **present-but-empty** restriction
list (`fields=[]`) must let NO attribute through (presence gating), whereas the
pre-patch truthiness gating let every editable, non-removed attribute through —
lives in `passes_restriction(allowed, n)` returning `contains(ToSeq(allowed), n)`
(here `False` for every `n`, since `[]` contains nothing) the instant `allowed`
is present, regardless of its length. The pre-patch skeleton (`model_prepatch.py`)
reproduces the truthiness gating
(`allowed is None or len(allowed) == 0 or contains(...)`) in its impl loop and
**fails** the postcondition / loop invariant
`ToSeq(Result()) == projection(...)`, which is exactly the spec sensing the
change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the restriction filter's presence-vs-truthiness gating — is modelled
**deeply** (`passes_restriction`, the spelled-out presence + membership predicate
consumed in `projection` and the impl loop, an **A-reference**), not hidden
behind an axiom about the function under change: there is **no consumed axiom**
(`axioms` region empty). The unchanged callees the loop invokes (`getattr`,
membership, `f.value_from_object`) are either trivial builtins (modelled as `in`
/ flags, R/I) or off the keyset observable (`value_from_object`, not modelled);
none is axiomatized. The deep model is validated == the real loop by G-AX.

## C. verify(model) ⇒ resolved

`project_record` verifies only if it DELIVERS a result on every admissible input
(A9) whose value equals the exact per-attribute projection (A8) under presence
gating for the restriction filter (A4) and truthiness gating for the removal
filter (A5). A8 alone is a partial-correctness claim — it constrains the result
only where one is produced — so without A9 an implementation could compute the
gold projection everywhere it answers and never answer the present-but-empty
restriction list, discharging A8 vacuously on precisely the observation the
instance turns on; A9 closes that. By R (str ↔ List[int] field
names, list ↔ `Optional[List[int]]`, `in` ↔ `contains`, keyset ↔ result
sequence) the verified projection equals the real post-patch loop's key set on
the tested inputs; by G-AX the deep model `projection` equals that real loop
(A-reference) over the boundary battery + fuzz. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The single trust point is refinement fidelity
(this document, G-EQ) backed by the executable equivalence check (G-AX); there is
no axiom-soundness trust point because no axiom is consumed.
