# refinement.md — django__django-16899

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`readonlyItemCheck` `do` block + the deep `itemDiagnostic` / `readonlyItemReport`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I; no kind-3 (changed inexpressible op).

There are **NO axioms** in this bundle: the four observations and four quoted
strings are free inputs (mapping.md §2/§3), so no row is A-consumed or
A-reference, and G-AX is `skip`. The whole impl region is R/I, mechanically
refuted by **G-CONF** (`conformance_check.py`); the narrative below is audited
by G-EQ.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The message site — `_check_readonly_fields_item` (`django/contrib/admin/checks.py:761`)

Gold hunk (the changed lines):
```
-                        "The value of '%s' is not a callable, an attribute of "
-                        "'%s', or an attribute of '%s'."
+                        "The value of '%s' refers to '%s', which is not a callable, "
+                        "an attribute of '%s', or an attribute of '%s'."
                         % (
                             label,
+                            field_name,
                             obj.__class__.__name__,
                             obj.model._meta.label,
                         ),
```

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `if isCallable then none` | `if callable(field_name): return []` | R | `none ↔ []` (acceptable, no `Error`); `isCallable ↔ callable(field_name)`. Unchanged branch. mapping.md §2. |
| 2 | `else if hasAttrAdmin then none` | `elif hasattr(obj, field_name): return []` | R | `hasAttrAdmin ↔ hasattr(obj, field_name)`. Unchanged branch. |
| 3 | `else if hasAttrModel then none` | `elif hasattr(obj.model, field_name): return []` | R | `hasAttrModel ↔ hasattr(obj.model, field_name)`. Unchanged branch. |
| 4 | `else if fieldUnknown then some (…) else none` | `else: try: obj.model._meta.get_field(field_name) except FieldDoesNotExist: return [Error(…)] else: return []` | R | `fieldUnknown ↔ get_field raises FieldDoesNotExist`; the `except` arm produces the single `Error` (`some msg`), the `else` arm `[]` (`none`). The control structure (try/except inverted to a boolean test on whether the lookup raises) is unchanged by the patch; only the message in the `except` arm changes. mapping.md §2. |
| 5 | `some ("The value of '" ++ label ++ "' refers to '" ++ name ++ "', which is not a callable, an attribute of '" ++ adminName ++ "', or an attribute of '" ++ modelLabel ++ "'.")` (= `itemDiagnostic label name adminName modelLabel`) | the **patched** format string `"The value of '%s' refers to '%s', which is not a callable, an attribute of '%s', or an attribute of '%s'." % (label, field_name, obj.__class__.__name__, obj.model._meta.label)` | R + I | the single changed op: the message is built by literal-and-argument concatenation. `%s`-interpolation ↔ `List Char` concatenation of the literal segments with the four free string inputs in order `label, name (field_name), adminName, modelLabel`. The literal segments are **I** (byte-identical to the patched format string); the four `++` insertions of the free strings are **R** (`str` ↔ `List Char`). The `obj=` and `id="admin.E035"` args of the `Error` are unchanged and not modeled (they are not what the F2P tests' message comparison turns on — `checks.Error.__eq__` compares all of msg/obj/id, but only the msg differs pre/post-patch). mapping.md §1. |

### Why the spec sees the bug (G-DIFF)

`Solution_prepatch.lean` builds the **pre-patch** message on the `fieldUnknown`
branch: `"The value of '" ++ label ++ "' is not a callable, an attribute of '"
++ adminName ++ "', or an attribute of '" ++ modelLabel ++ "'."` — with NO
`"refers to '" ++ name ++ "', which "` segment. The frozen spec requires
`out = readonlyItemReport … = some (itemDiagnostic label name adminName
modelLabel)`, whose `fieldUnknown` value DOES contain the `name` segment, so the
`ensures` equality is unprovable on that branch → `prove_correct` fails. This is
exactly the F2P discriminator: both `test_nonexistent_field`
(`readonly_fields[1]` / `nonexistent`) and `test_nonexistent_field_on_inline`
(`readonly_fields[0]` / `i_dont_exist`) assert the message now contains
`refers to '<field_name>', which`. A single prepatch suffices: the patch makes
ONE behavioural change (the message text on the unresolvable path), exercised
identically by both F2P tests.

## C. No axioms; no kind-3

Every changed op is expressible: the patch is a pure rearrangement of literal
text and free string arguments into a message, modeled deeply by explicit
`List Char` concatenation (`itemDiagnostic`). The four runtime observations are
unchanged callees abstracted to free booleans (no axiom — they are not consumed,
and no claim is made about them; mapping.md §3). Nothing is inexpressible; no
BLOCKED.

## D. verify(Solution) ⇒ resolved

`readonlyItemCheck` verifies only if its output equals `readonlyItemReport`,
which on the `fieldUnknown` branch is exactly `itemDiagnostic` — the patched
message with `field_name` quoted (row 5). By R (`str ↔ List Char`, `[] ↔ none`,
single `Error` ↔ `some msg`) and the unchanged branches (rows 1-4), the verified
report equals the gold-patched `_check_readonly_fields_item` result on every
input; by G-CONF the R/I transliteration of the message logic agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs (including the two F2P scenarios).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axioms, so the only residual trust point is refinement fidelity (this doc,
G-EQ + G-CONF); G-AX is vacuous (skip).
