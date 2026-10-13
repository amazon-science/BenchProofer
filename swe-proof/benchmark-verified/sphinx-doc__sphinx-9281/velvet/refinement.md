# refinement.md — sphinx-doc__sphinx-9281

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `objectDescription` `do` block and the deep `describe` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none in this bundle), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The render site — `object_description()` (`sphinx/util/inspect.py:433`)

Gold hunk (essential content):
```
- if isinstance(object, set):
+ elif isinstance(object, set):
        ...
- if isinstance(object, frozenset):
+ elif isinstance(object, frozenset):
        ...
+ elif isinstance(object, enum.Enum):
+     return "%s.%s" % (object.__class__.__name__, object.name)
+
    try:
        s = repr(object)
        ...
```

| # | Solution.lean impl op (`objectDescription`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `obj : Obj` | `object` arg of `object_description` | R | the value's display-relevant *kind* ↔ `Obj` (mapping.md §2). G-CONF bridges concrete Python values to the two `Obj` cases. |
| A2 | `match obj with \| .enumValue className memberName _ => …` (the value is a member of an enumerated type) | `elif isinstance(object, enum.Enum):` guard | R | "is a member of an enumerated type" ↔ the `.enumValue` constructor. The `if`→`elif` rewrite of the preceding container checks is behaviour-neutral (disjoint types) — mapping.md §3.1 — so it adds no observable op; the only new branch is this one. |
| A3 | `className ++ "." ++ memberName` | `return "%s.%s" % (object.__class__.__name__, object.name)` | I + R | the structured label: identical string-composition op (`++ "." ++` ↔ `"%s.%s"`), under the R bijection `className ↔ __class__.__name__`, `memberName ↔ name` (mapping.md §2). No `repr`/escaping on either operand. |
| A4 | `\| .plain genericText => genericText` | every non-enumerated path: the unchanged container legs (`dict`/`set`/`frozenset`) and the `repr()`/memory-address-strip/newline-replace fallback (`inspect.py:435-467`) | I | the unchanged rendering, carried opaquely as `genericText`. `if`→`elif` cannot change which (mutually exclusive) leg fires, so the pre-patch result is preserved exactly; G-CONF reproduces the real generic renderer and confirms agreement. |
| A5 | `out` returned (`String`) | the returned `str` | R | identity on character content (mapping.md §2); `test_object_description_enum` compares the returned string exactly. |

Discriminating content of the change — a member of an enumerated type renders
as `ClassName.MemberName` (e.g. `MyEnum.FOO`) rather than the verbose generic
fallback `<MyEnum.FOO: value>` — lives in
`describe (.enumValue cn mn _) = cn ++ "." ++ mn` (model) ⇔ the new
`elif isinstance(object, enum.Enum)` branch (real). The pre-patch code had no
such branch, so an enum member reached the generic `repr()` fallback;
`Solution_prepatch.lean` reproduces that (every value routes to `genericText`)
and **fails** `out = describe obj` on the `.enumValue` case (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — adding the
structured rendering for members of an enumerated type — is modeled **deeply**
(the spelled-out `describe` dispatch, steps A2–A4), not hidden behind an axiom
about the function under change. There are **no consumed axioms**: the unchanged
generic renderer (containers + `repr`/strip/newline) is carried as the opaque
`genericText` field and reproduced concretely by G-CONF, never axiomatized.
Hence there is no `axiom_check.py` and G-AX is `skip` (meta.json).

## C. verify(Solution) ⇒ resolved

`objectDescription` verifies only if its output equals `describe obj`: for a
member of an enumerated type, `ClassName.MemberName` (A3); for everything else,
the unchanged generic text (A4). By R (`Obj` ↔ Python value kind, `String`
identity on content) the verified renderer equals the patched
`object_description` on the tested inputs; by G-CONF the deep model `describe`
agrees with the real patched `object_description` on the boundary matrix +
100 000 fuzz inputs (seed 9281), 0 disagreements. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). The single trust point is refinement
fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness trust point
(no axioms).
