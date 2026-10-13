# mapping.md — django__django-15930

Binds every `model.py` symbol to its repo counterpart at `base_commit`
(`63884829acd207404f2a5c3cc1d6b4cd0a822b70`), records the type abstraction, and
cites the provenance of the one deep-model reference (`true_predicate()` /
`true_params()` ↔ `compiler.compile(Value(True))`).

## 1. Modeled function

| model.py | repo symbol | repo location (base_commit) |
|---|---|---|
| `render_branch(pred, pred_params, cons, cons_params)` | `django.db.models.expressions.When.as_sql` | `django/db/models/expressions.py:1297-1308` |

`When.as_sql` renders one conditional branch into SQL by filling the class
template `WHEN %(condition)s THEN %(result)s` (`expressions.py:1246`) and
concatenating the branch's bound parameters (condition params then result
params). `render_branch` models exactly the body of `as_sql`:

* `pred`         ↔ `condition_sql` = `compiler.compile(self.condition)[0]`
* `pred_params`  ↔ `condition_params` = `compiler.compile(self.condition)[1]`
* `cons`         ↔ `result_sql` = `compiler.compile(self.result)[0]`
* `cons_params`  ↔ `result_params` = `compiler.compile(self.result)[1]`
* `Result()[0]`  ↔ the rendered SQL string `template % template_params`
* `Result()[1]`  ↔ `sql_params`

The `compiler.compile(self.condition)` / `compiler.compile(self.result)` calls
are the UPSTREAM PRODUCERS of the four inputs; they are unchanged by the patch
and are not part of the modeled operation (they produce `render_branch`'s
arguments). The fixed template framing is modeled by the constants `lead()`
(`"WHEN "`, the literal text before `%(condition)s`) and `sep()` (`" THEN "`,
the literal text between `%(condition)s` and `%(result)s`); the trailing
template text is empty.

## 2. Type abstraction

| repo reality | model |
|---|---|
| SQL fragment `str` (`condition_sql`, `result_sql`, rendered SQL) | `List[int]` of code points; specification carried by `PSeq[int]` (Nagini bans `str` indexing). Only fragment identity and emptiness matter to the behaviour, so code points are faithful carriers. |
| bound-parameter `list` (`condition_params`, `result_params`, `sql_params`) | `List[int]` of opaque parameter-identity tokens; only order and concatenation order matter. |
| `template % template_params` string interpolation of `WHEN %(condition)s THEN %(result)s` | `lead() + <predicate slot> + sep() + cons` sequence concatenation. |
| `sql_params = condition_params(or Value(True) params) + result_params` | `clause_params(...)` = predicate-slot params ++ consequent params. |

The emptiness test `condition_sql == ""` ↔ `len(pred) == 0` is identical (an
empty string is the empty code-point list).

## 3. The one deep-model reference (A-reference): `compile(Value(True))`

The patch, when `condition_sql == ""`, replaces the condition with
`compiler.compile(Value(True))` (`expressions.py`, gold hunk at line 1299+).
`Value(True).as_sql` (`expressions.py:992-1008`) returns `("%s", [val])` for a
non-`None` value (here `val == True`), i.e. a NON-empty placeholder fragment
carrying one bound parameter. The model spells this substituted constant out
deeply:

* `true_predicate()` — the fixed NON-empty always-true predicate fragment
  (`"TRUE"` in the model; the relied-on property is only NON-EMPTINESS).
* `true_params()` — the always-true predicate's bound parameters: one opaque
  token (mirrors the single `[True]` parameter).

This is an **A-reference**, NOT a consumed `@ContractOnly` axiom: there is no
axiom in `model.py`. The deep-model constants stand in for the real
`compile(Value(True))` output, and the only property the proof rides on
(non-emptiness of the predicate slot) is validated against the REAL callee by
`axiom_check.py` (G-AX).

**Provenance / evidence (observed against the base_commit + gold tree):**
```
compiler.compile(Value(True))            -> ('%s', [True])          # NON-empty
compiler.compile(~Q(pk__in=[]))          -> ('', [])                # empty fragment (all-matching sentinel)
When(~Q(pk__in=[]), then=...).as_sql     -> ('WHEN %s THEN %s', [True, 'selected'])
```
The all-matching condition compiles to the EMPTY fragment via
`django/db/models/sql/where.py:128,135` (`return "", []`); the gold fix detects
that empty fragment and substitutes the non-empty `Value(True)` fragment. The
rendered clause's params are `Value(True)`'s `[True]` followed by the result's
`['selected']` — exactly `clause_params` = `true_params() ++ cons_params`.

**Flag/version dependency:** the empty-string protocol (`condition_sql == ""`)
is the base_commit behaviour. Later Django releases replaced it with a
`FullResultSet` exception raised before `When.as_sql` runs; that is a different
code path absent at this base_commit. `axiom_check.py` exercises the
empty-fragment substitution against the in-container base_commit tree and
detects/annotates the newer-tree path so it never crashes.

## 4. Axioms

None. The changed operation (the empty-predicate substitution + clause
assembly) is modeled deeply; the only external product (`compile(Value(True))`)
is an A-reference checked by G-AX, not a consumed axiom.
