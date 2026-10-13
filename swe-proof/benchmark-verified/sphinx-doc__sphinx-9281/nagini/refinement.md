# refinement.md — sphinx-doc__sphinx-9281

The operation-by-operation correspondence between `model.py`'s implementation
(the `describe` impl region and the deep `enum_rendering` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee/operation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The dispatch + the new enumerated-type branch — `object_description()` (`sphinx/util/inspect.py:433`)

Gold hunk (semantically): the bare `if isinstance(object, set)` /
`if isinstance(object, frozenset)` become `elif` (joining the dispatch chain),
and a new arm is inserted before the generic `repr` fallback:

```
+    elif isinstance(object, enum.Enum):
+        return "%s.%s" % (object.__class__.__name__, object.name)
```

| # | model.py impl op (`describe`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: Value`, field `value.kind` | the `object` argument and the `isinstance(object, …)` dispatch | R | the category (which `isinstance` arm fires) ↔ the integer tag `kind` (0 dict, 1 set, 2 frozenset, 3 `enum.Enum`, 4 other); the patched `if/elif` chain makes the arms mutually exclusive, mirrored by the `if … elif … elif … else` on `kind` (mapping.md §2). |
| A2 | `if value.kind == 0 or value.kind == 1 or value.kind == 2:` returns `value.category_text` (copied element-wise) | the dict / set / frozenset arms return their `"{…}"` / `"frozenset({…})"` renderings | R + I | these arms are UNCHANGED; their rendering is carried as the opaque `category_text` (mapping.md §2). The model reproduces it exactly; the `if`→`elif` edit does not change what these arms return. The element-wise copy loop is the identity on the sequence (`ToSeq(result) == ToSeq(value.category_text)`). |
| A3 | `elif value.kind == 3:` builds `value.class_name ++ [46] ++ value.member_name`, i.e. `enum_rendering(class_name, member_name)` | `elif isinstance(object, enum.Enum): return "%s.%s" % (object.__class__.__name__, object.name)` | A-reference | the changed rendering operation is modelled **deeply**: `enum_rendering` (the spelled-out `class_name + dot() + member_name` in the `pure` region) and the verified copy/append loop in `describe` ARE the `"%s.%s"` composition. There is no consumed `enum_repr` axiom — the proof never depends on one. Instead the deep model is validated **== the real operation** out-of-band: G-AX (axiom_check.py) builds real `enum.Enum` members and asserts `enum_rendering(ord*(cls.__name__), ord*(member.name))` equals the code points of `"%s.%s" % (cls.__name__, member.name)`. The dot `[46]` ↔ the literal `"."` in the format string (mapping.md §3.1). |
| A4 | `else:` returns `value.fallback_text` (copied element-wise) | the `try: s = repr(object)` generic fallback | R + I | the generic fallback is UNCHANGED; carried as the opaque `fallback_text` (mapping.md §2). Reached only when `kind ∉ {0,1,2,3}`, mirroring the patched chain where a value that is none of dict/set/frozenset/`enum.Enum` falls to `repr`. |

The discriminating content of the change — an enumerated-type member renders as
`ClassName.MemberName`, NOT as the generic `repr` fallback — lives in the A3
branch: `ToSeq(Result()) == enum_rendering(ToSeq(class_name), ToSeq(member_name))`
under `kind == 3` (model) ⇔ the new `elif isinstance(object, enum.Enum)` arm
(real). The pre-patch code had **no** such arm, so an enumerated-type member
fell through to `repr(object)` — the ugly value-revealing form
(`value.fallback_text`). `model_prepatch.py` reproduces exactly that
(the `kind == 3` value falls into the `else`/fallback branch and returns
`value.fallback_text`) and **fails** the postcondition
`Implies(value.kind == 3, ToSeq(Result()) == enum_rendering(…))`, which is
precisely the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the enumerated-type rendering — is modelled **deeply** (the
spelled-out `enum_rendering` composition consumed in `describe`, step A3, an
**A-reference**), not hidden behind an axiom about the function under change:
there is no consumed `enum_repr`/`object_description` axiom. The unchanged arms
(dict/set/frozenset renderings, the generic `repr` fallback) are carried as
opaque input sequences (`category_text`, `fallback_text`), so no axiom about
`sorted`/`repr`/`", ".join` is needed or claimed. **There are no A-consumed
axioms in this bundle.**

## B2. Termination obligation (total correctness)

Nagini is a partial-correctness verifier by default: an implementation with no
reachable normal exit (an endless loop before the `return`) satisfies every
`Ensures` — including the `kind == 3` enum pin — vacuously while sharing the
spec byte-for-byte. That is a wrong implementation the spec would otherwise
admit (the audit's P1 witness, atk_8). The real `object_description` always
answers: rendering a value is a bounded computation (`"%s.%s"` formatting over
two finite names, or reproducing an already-given finite rendering). The spec
therefore carries `Requires(MustTerminate(2))` on `describe` (consumed in each
copy loop by an `Invariant(MustTerminate(<remaining count>))` measure — the
remaining count is the strictly decreasing, bounded-below measure). With
termination required and the per-category value postconditions, any verifying
same-spec implementation must terminate and return exactly the pinned text on
every category (properties.py `w-diverge` pins the rejection).

## C. verify(model) ⇒ resolved

`describe` verifies only if it TERMINATES on every input (§B2,
`Requires(MustTerminate(2))`) and, for an enumerated-type member (`kind == 3`),
its output equals `enum_rendering(class_name, member_name) = ClassName "." MemberName`
(A3), and if the unchanged arms reproduce their renderings (A2/A4). By R
(`str` ↔ `List[int]`, category/fallback renderings carried verbatim) the
verified `describe` equals the patched `object_description` on every category;
by G-AX the deep model `enum_rendering` equals the real `"%s.%s" %
(cls.__name__, member.name)` (A-reference). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited deep-model reference — and the gold patch resolves (G-RESOLVE,
`tests/test_util_inspect.py::test_object_description_enum` plus the unchanged
collection/fallback P2P tests). The trust points are exactly the two of
PLAN §1.1: deep-model/axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
