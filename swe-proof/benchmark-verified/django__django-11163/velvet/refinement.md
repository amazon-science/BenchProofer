# refinement.md — django__django-11163

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`selectModelFields` `do` block, plus the deep `keep` / `selectNames` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — A-consumed / A-reference), or **I** (identical
concrete op). EVERY step is R, A, or I.

This bundle has **no A rows**: there is no unchanged library callee the proof
relies on (mapping.md §3). The R/I legs are mechanically refuted by **G-CONF**
(`conformance_check.py`, §4.1); the narrative is audited by G-EQ.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change site — `model_to_dict()` (`django/forms/models.py:87`)

Gold hunk:
```
- if fields and f.name not in fields:
+ if fields is not None and f.name not in fields:
      continue
```
The guard `if exclude and f.name in exclude:` on the next line is **unchanged**.

| # | Solution.lean impl op (`selectModelFields`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | param `candidates : List Int` | the editable candidate fields the loop iterates (`f.name` for each `f` in `chain(...)` with `getattr(f,'editable',False)`) | R | ordered field names ↔ `List Int` under the name↔Int coding (mapping.md §2). G-CONF bridges via a synthesized model whose editable names are the fuzz case. |
| 2 | param `selector : Option (List Int)` | the `fields` argument (`None` or a list) | R | `None ↔ none`, list `↔ some [...]` (mapping.md §2). The `Option` carrier is what makes `None` and `[]` distinct — the discriminator. |
| 3 | param `excl : List Int` | the `exclude` argument | R | `None`/`[]` both ↔ `[]`; list maps elementwise (mapping.md §2). Models the **unchanged** exclude guard, pinning that frame. |
| 4 | `keep sel excl n`: `(match sel with none => true \| some present => n ∈ present) && n ∉ excl` | the two `continue` guards combined: keep `f` iff `(fields is None or f.name in fields)` **and** `f.name not in exclude` | I (+R on the carrier) | this is the post-patch guard transliterated. `match none => true / some => n ∈ present` is exactly `fields is None or f.name in fields` (the **fixed** `is not None` test: presence, not truthiness); `n ∉ excl` is the unchanged `f.name not in exclude` (`if exclude and …`: when `exclude` is empty/None, `n ∉ []` is vacuously true — same result). |
| 5 | `selectNames sel excl candidates` (the `while` fold building `result`) | the loop's net effect: the ordered list of `f.name` placed into `data` (its key set) | I (+R) | the backward `while` computes the front-recursive concatenation `selectNames`, i.e. the kept names in candidate order. The dict KEY set is what the F2P test observes (`sorted(model_to_dict(...))`). |
| 6 | (not modeled) `data[f.name] = f.value_from_object(instance)` | the value stored per kept key | R-identity | `value_from_object` is an unchanged callee producing the *values*; the tested behaviour is the *key set* (mapping.md §3). R-identity on the value projection: omitting it cannot change which keys appear. No dead axiom (directive 7). |

Discriminating content of the change — a PRESENT-but-empty `fields` (`fields=[]`)
must yield NO keys, not all keys — lives in `keep (some []) excl n = false`
(model, `keep_empty_selector` / `selectNames_empty_selector`) ⇔ the post-patch
`fields is not None and f.name not in fields` evaluating its first conjunct
`True` for `fields=[]` so every field hits `continue`. The pre-patch
`if fields and …` treats `fields=[]` as falsy, skipping the guard and keeping
every field. `Solution_prepatch.lean` reproduces exactly that
(`if present.isEmpty then true else …`) and **fails** the
`selector = some [] → out = []` clause and the main `out = selectNames …`
invariant (G-DIFF).

## No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the `fields`
guard — is modeled **deeply** (the spelled-out `keep` / `selectNames`, rows 4–5),
not hidden behind an axiom about the function under change. There is no consumed
axiom and no A-reference: the decision is a pure boolean function of the
function's own parameters.

## verify(Solution) ⇒ resolved

`selectModelFields` verifies only if `out = selectNames selector excl candidates`
AND `selector = some [] → out = []` AND every returned name is an admissible
candidate. By R (`List Int`/`Option` ↔ Python names/optional list) the verified
kept-name list equals the post-patch `model_to_dict` key set on every input; in
particular `fields=[]` ⇒ `[]` (the added F2P assertion `model_to_dict(bw,
fields=[]) == {}`), `fields=['id','name'] ⇒ those keys`, `exclude=[] ⇒ all keys`,
`exclude=['id','name'] ⇒ the rest`. By G-CONF the R/I transliteration of
`keep`/`selectNames` agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The single
trust point (plan §1.1) is refinement fidelity (this doc, G-EQ + G-CONF); there is
no axiom-soundness trust point because there is no axiom.
