# refinement.md — django__django-14580

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderTypeRef` `do` block, routed through the deep model `typeRef`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** / **A-reference** (axiomatized callee —
none here), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (absent) A legs and this narrative are audited by **G-EQ**. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The render site — `TypeSerializer.serialize()` (`serializer.py:274`)

Gold hunk:
```
 special_cases = [
-    (models.Model, "models.Model", []),
+    (models.Model, "models.Model", ['from django.db import models']),
     (type(None), 'type(None)', []),
 ]
```
The change augments the base-model special case so its emitted reference
`models.Model` is accompanied by the import `from django.db import models`
needed to make that reference valid standalone Python. (Pre-patch the imports
list is empty, so a generated migration referencing `models.Model` fails with a
name error — the issue.)

| # | Solution.lean impl op (`renderTypeRef` / `typeRef`) | patch.diff / source op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `t : TypeInfo` | the runtime `type` in `self.value` | R | Python `type` ↔ its observable-field record (mapping.md §2). |
| A2 | `if t.isBaseModelType then ("models.Model", ["from django.db import models"])` | `special_cases` row 0 (post-patch): `(models.Model, "models.Model", ['from django.db import models'])` returned via `return string, set(imports)` | I | identical concrete op. The string is the literal `"models.Model"`; the import list is the patched literal. **This is the discriminating step**: the import is exactly what the gold patch adds (and what `Solution_prepatch.lean` drops → G-DIFF). G-CONF compares the import set. |
| A3 | `else if t.isNoneType then ("type(None)", [])` | `special_cases` row 1: `(type(None), 'type(None)', [])` | I | identical; unchanged by the patch. |
| A4 | `else if t.moduleName = "builtins" then (t.simpleName, [])` | `if module == builtins.__name__: return self.value.__name__, set()` (`serializer.py:285-287`) | R + I | `builtins.__name__ == "builtins"` (R: string literal); `set()` ↔ `[]`. Concrete otherwise. |
| A5 | `else (t.moduleName ++ "." ++ t.qualName, ["import " ++ t.moduleName])` | `else: return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}` (`serializer.py:288-289`) | R + I | `%s.%s` ↔ `++ "." ++` ; `"import %s" % m` ↔ `"import " ++ m` ; `{...}` ↔ `[...]` singleton (mapping.md §2). |
| A6 | the two-row `special_cases` loop | the `for case, string, imports in special_cases:` loop | R | the fixed two-element literal with mutually-exclusive `is` guards unrolls to the ordered `if/elif` ladder A2/A3 (mapping.md §2a). Exact, not approximate. |
| A7 | returned `String × List String` | `return string, set(imports)` (a `(str, set)` tuple) | R | the second component is a set in source; modeled as a duplicate-free `List String` and compared as a set by G-CONF (mapping.md §2). |

## B. No consumed axioms / no deep-model references

`TypeSerializer.serialize` consumes no callee contract: every operation is an
attribute read, an identity test, string formatting, or set construction — all
modeled directly as R/I (mapping.md §3). There is therefore no A-consumed axiom
and no A-reference deep model. `meta.json` `axioms` / `deep_model_references`
are empty; **G-AX is `skip`**.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the import
list attached to the base-model special case — is modeled **directly and
concretely** as the literal `["from django.db import models"]` in step A2, an
**I** op. Nothing about the change is hidden behind an axiom about the function
under change.

## D. verify(Solution) ⇒ resolved

`renderTypeRef` verifies only if its output equals `typeRef t` for every
`TypeInfo` — in particular the base-model branch must emit BOTH the reference
`"models.Model"` AND the import `"from django.db import models"` (A2). By R
(`TypeInfo ↔ Python type`, set↔list, `%`-format↔`++`) the verified renderer
equals the patched `TypeSerializer.serialize` on the modeled inputs; by G-CONF
the R/I transliteration agrees with `patch.diff`'s behaviour (the real patched
`MigrationWriter.serialize`) on ≥10⁵ fuzzed inputs. The pre-patch dropped the
import (`Solution_prepatch.lean`), failing `out = typeRef t` on the base-model
clause — exactly the F2P `test_serialize_type_model` assertion
(`serialize(models.Model) == ("('models.Model', {'from django.db import
models'})", set())`). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There are no axiom trust points (G-AX skip); the only trust point
is refinement fidelity (this doc, G-EQ + G-CONF).
