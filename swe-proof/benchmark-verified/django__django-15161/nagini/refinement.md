# refinement.md — django__django-15161

The operation-by-operation correspondence between `model.py`'s implementation
(`deconstruct_path`, the deep `serialized_module_rooted` / `qualified` models)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. What the patch changes

The gold patch adds, to six expression-node classes in
`django/db/models/expressions.py`, the class decorator
`@deconstructible(path='django.db.models.<ClassName>')`:

```
+@deconstructible(path='django.db.models.Func')             class Func(...)        (line 654)
+@deconstructible(path='django.db.models.Value')            class Value(...)       (line 734)
+@deconstructible(path='django.db.models.ExpressionWrapper')class ExpressionWrapper(...) (956)
+@deconstructible(path='django.db.models.When')             class When(...)        (line 988)
+@deconstructible(path='django.db.models.Case')             class Case(...)        (line 1055)
+@deconstructible(path='django.db.models.OrderBy')          class OrderBy(...)     (line 1228)
```

The decorator body (UNCHANGED, `django/utils/deconstruct.py:20-48`) computes
the deconstructed import path:

```python
if path and type(obj) is klass:           # a configured path, exact type
    ... module_name, _, name = path.rpartition('.')
else:
    module_name = obj.__module__; name = obj.__class__.__name__
return (path if path and type(obj) is klass
        else f'{obj.__class__.__module__}.{name}', args, kwargs)
```

Supplying `path=` is exactly what makes the first branch fire, so the reported
import path becomes the configured **public-package-rooted** string
(`django.db.models.Value`) instead of the `obj.__module__`-derived fallback
(`django.db.models.expressions.Value`). That rooting is what lets the migration
serializer emit the short `models.X` form.

## B. Operation correspondence

| # | model.py impl op (`deconstruct_path`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `configured/module/name: List[int]`, `exact: bool` | the `path` kwarg, `obj.__module__`, `obj.__class__.__name__`, and `type(obj) is klass`, all `str`/`bool` | R | `str` ↔ `List[int]` code points; `if path` truthiness ↔ `len(configured) > 0`; `type(obj) is klass` ↔ `exact` (mapping.md §2). The patch's per-class `path='django.db.models.<Name>'` literal is the `configured` value; `exact == True` for the F2P leaf-class instances. |
| B2 | `if len(configured) > 0 and exact:` choose `configured` | `path if path and type(obj) is klass` | I (under R) | the same branch selector; the result is the configured path verbatim. The patch ENABLES this branch by providing `path=`. |
| B3 | else build `qualified(module, name) == module + '.' + name` | `else f'{obj.__class__.__module__}.{name}'` | R | dotted-join refinement of the `str` f-string (mapping.md §2); the per-char loops materialize `module "." name`. |
| B4 | `serialized_module_rooted(Result())` postcondition | the downstream `DeconstructableSerializer._serialize_path` `module == "django.db.models"` short-form branch (`serializer.py:94-102`) | A-reference | the serializer rooting test is modeled DEEPLY by `serialized_module_rooted` (pure region); no consumed axiom. G-AX (`axiom_check.py`) asserts `serialized_module_rooted(p)` ⇔ the real serializer reduces `p` to the short `models.<leaf>` form, at the short-form level on both sides (no double-mask). |

## C. The discriminator (G-DIFF)

The tested change — these nodes reporting the public-rooted path
`django.db.models.Value` rather than the internal `django.db.models.expressions.Value`
— lives in the postcondition

  `Implies(len(configured) > 0 and exact, ToSeq(Result()) == ToSeq(configured))`.

`model_prepatch.py` reproduces the pre-patch behaviour (the classes carried NO
`path=`, so `deconstruct` always took the `else` fallback and reported the
internal-submodule name). It keeps the spec byte-identical and **fails** exactly
that postcondition (the verifier flags the configured-path clause), which is the
spec sensing the change. Because `django.db.models.expressions.Value` is NOT
public-package-rooted, the rooting postcondition (B4) likewise distinguishes the
two: the fixed value is short-form-eligible, the pre-patch value is not — which
is precisely what the F2P `test_serialize_complex_func_index` observes (the
emitted `models.Func(...)`/`models.Case(...)` short forms and the single
`from django.db import models` import).

## D. No consumed axioms; no kind-3 steps

There are **no `@ContractOnly` consumed axioms**: the path choice and the
rooting check are fully expressible over `List[int]`/`PSeq[int]`, so both are
modeled DEEPLY and verified. The two deep models are **A-reference**s, validated
== their real (UNCHANGED) callees by axiom_check.py / G-AX:
`deconstruct_path`'s choice == the real `deconstructible.deconstruct` path
selection (A-reference 1), and `serialized_module_rooted` == the real
`_serialize_path` short-form test (A-reference 2). Every step in §B is R, I, or
A-reference; the one operation the patch actually steers — which path the node
reports — is modeled deeply, not hidden behind an axiom.

## E. verify(model) ⇒ resolved

`deconstruct_path` verifies only if, when a canonical path is configured for the
exact type, the reported path is that configured public-rooted string (B2), and
otherwise the qualified fallback (B3), with the rooting flag tracking the chosen
branch (B4). By R (str ↔ List[int], f-string ↔ dotted-join, `if path` ↔
`len>0`), the verified function equals the real `deconstruct`'s path computation;
the gold patch supplies `path='django.db.models.<Name>'` for each of the six
classes, so each reports the public-rooted path, which (by A-reference 2, G-AX)
the serializer renders as the short `models.<Name>` form — exactly the F2P
expectations. The trust points are the two of PLAN §1.1: deep-model fidelity to
the real callees (G-AX, this document) and refinement fidelity (this document,
G-EQ). The gold patch resolves (G-RESOLVE).
