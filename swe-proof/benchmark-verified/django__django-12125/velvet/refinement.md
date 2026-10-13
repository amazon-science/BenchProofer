# refinement.md — django__django-12125

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `typeReference` `do` block + the deep `renderRef` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — none in this bundle), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The type-reference site — `TypeSerializer.serialize()` (`serializer.py:259`)

Gold hunk (`serializer.py:272`):
```
- return "%s.%s" % (module, self.value.__name__), {"import %s" % module}
+ return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}
```

The method, in full, dispatches in priority order:
```python
special_cases = [(models.Model, "models.Model", []), (type(None), 'type(None)', [])]
for case, string, imports in special_cases:
    if case is self.value:
        return string, set(imports)
if hasattr(self.value, "__module__"):
    module = self.value.__module__
    if module == builtins.__name__:
        return self.value.__name__, set()
    else:
        return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}  # patched
```

| # | Solution.lean impl op (`typeReference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `t : TypeValue` (six read facts) | `self.value` (a `type`); the method reads `is models.Model`, `is type(None)`, `__module__`, `__qualname__`, `__name__` | R | rich object → structure of only the touched attributes (mapping.md §2). G-CONF reads the same facts off genuine `type` objects. |
| A2 | `if t.isSentinelBase then ⟨"models.Model", none⟩` | `special_cases[0]`: `case is self.value` → `("models.Model", set())` | I | identical literal + empty import. |
| A3 | `else if t.isNoneType then ⟨"type(None)", none⟩` | `special_cases[1]`: → `("type(None)", set())` | I | identical literal + empty import. |
| A4 | `else if t.isBuiltin then ⟨t.bare, none⟩` | `module == builtins.__name__` → `(self.value.__name__, set())` | I | builtins branch: bare name, no import. `isBuiltin` ↔ `__module__ == builtins.__name__` (mapping.md §2). The method's `hasattr(__module__)` guard is always true of a `type`. |
| A5 | `else ⟨t.module ++ ['.'] ++ t.qualified, some ("import " ++ t.module)⟩` | `("%s.%s" % (module, self.value.__qualname__), {"import %s" % module})` | I (post-patch) | **the patched line**: general branch names the value by `module . qualified`, where `qualified` = `__qualname__` = the FULL within-module location **including enclosing classes**, and imports `module`. `++ ['.'] ++` ↔ the `"%s.%s"` join (R: `str` ↔ `List Char`, mapping.md §2). |

Discriminating content of the change — for a value nested inside another class,
`__qualname__` (`Outer.Inner`) differs from `__name__` (`Inner`); the patch
selects `__qualname__`. This lives in step A5 (`t.qualified`, not `t.bare`). The
pre-patch used `__name__` (the bare component), producing `module.Inner` — the
wrong, unresolvable top-level path. `Solution_prepatch.lean` reproduces that
(`t.module ++ ['.'] ++ t.bare`) and **fails** the spec's general-branch clause
(`out = … t.qualified …`) exactly when `t.bare ≠ t.qualified`, i.e. the nested
case (G-DIFF; the unsolved goal is literally `t.bare = t.qualified`).

## B. No axioms, no second site

The method calls nothing it does not change: it only reads attributes of the
input value and concatenates strings. There is **no consumed axiom** and **no
A-reference** — the only operation that changed (which attribute names the value)
is modeled **deeply** in `renderRef` (step A5). G-AX therefore has no obligation
and skips (mapping.md §3; as in django__django-12713 / astropy__astropy-13236).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — selecting the
enclosing-class-qualified location instead of the bare name when building the
general-branch reference — is modeled **deeply** (step A5, `t.qualified`), not
hidden behind an axiom about the function under change. There are no consumed
axioms at all.

## D. verify(Solution) ⇒ resolved

`typeReference` verifies only if its general-branch output equals
`module . qualified` with an `import module` (A5, the post-patch line) and the
sentinel/builtin branches match (A2–A4). By R (`str ↔ List Char`, the structure
bijection of mapping.md §2) the verified function equals the patched
`TypeSerializer.serialize` on every type value; by G-CONF the R/I transliteration
agrees with `patch.diff`'s behaviour on ≥10⁵ genuine `type` objects (including
real nested classes, where the change is observable). The only F2P test driven by
the modeled function, `test_serialize_nested_class`, asserts exactly the
general-branch nested case A5 fixes. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there is no axiom-soundness trust point (no axioms).
