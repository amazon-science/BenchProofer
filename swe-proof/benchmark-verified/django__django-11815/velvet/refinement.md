# refinement.md — django__django-11815

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `referenceEnumMember` `do` block plus the deep `memberReference` /
`quotedName` / `referenceImports` models) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (deep model validated == the
real callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has no
A legs. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The serialize site — `EnumSerializer.serialize()` (`serializer.py:120`)

Gold hunk:
```
-        v_string, v_imports = serializer_factory(self.value.value).serialize()
-        imports = {'import %s' % module, *v_imports}
-        return "%s.%s(%s)" % (module, enum_class.__name__, v_string), imports
+        return (
+            '%s.%s[%r]' % (module, enum_class.__name__, self.value.name),
+            {'import %s' % module},
+        )
```

| # | Solution.lean impl op (`referenceEnumMember`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `module`, `className` : `List Char` | `module = enum_class.__module__`, `enum_class.__name__` (read at lines 121–122) | R | `str` ↔ `List Char` (mapping.md §2). Pure attribute reads on the unchanged enum type; G-CONF supplies them via the stand-in. |
| A2 | param `memberName : List Char` | `self.value.name` | R | `str` ↔ `List Char`. The post-patch key: the member's symbolic name. |
| A3 | params `payloadText`, `payloadImports` (read-only, unused) | `serializer_factory(self.value.value).serialize()` result, pre-patch lines deleted | R + directive 5 | the member's serialized payload and its imports — supplied to the operation but the post-patch code never uses them for the reference. Pinned unused by the spec: the postconditions reference neither, so any impl letting them reach the output fails to verify (the directive-5 ignored-input frame; cf. 12741 `suppliedKey`). |
| A4 | `refString = module ++ ['.'] ++ className ++ ['['] ++ (['\''] ++ memberName ++ ['\'']) ++ [']']` == `memberReference module className memberName` | `'%s.%s[%r]' % (module, enum_class.__name__, self.value.name)` | I | identical concrete string interpolation. The two `%s` are plain concat (R, mapping.md §2); the `%r` of the member name equals `'` + name + `'` on the identifier domain, which the spec pins EXPLICITLY via `require ∀ c ∈ memberName, isIdentChar c` (mapping.md §3.2) — an R-refinement of the `require`-pinned input domain, transliterated by G-CONF. |
| A5 | `imports = ["import " ++ module]` == `referenceImports module` | `{'import %s' % module}` | I + R | identical singleton construction; Python `set` with one element ↔ one-element `List` (mapping.md §2). |
| A6 | `return (refString, imports)` (`List Char × List (List Char)`) | `return (<string>, <set>)` | R | the `(str, set)` 2-tuple ↔ `(List Char) × (List (List Char))` per mapping.md §2. |

Discriminating content of the change — the reference is keyed on the member's
**symbolic name in subscript form** (`Class['NAME']`), not on its **serialized
value in call form** (`Class(value)`), and only the module import is emitted —
lives in `memberReference` / `referenceImports` (model) ⇔ the post-patch format
and import set (real). `Solution_prepatch.lean` reproduces the pre-patch bug
(`Class(payloadText)` + payload imports merged) and **fails** the postconditions
`out.1 = memberReference …` and `out.2 = referenceImports module` (G-DIFF).

## B. No other change sites

The patch touches only `EnumSerializer.serialize`. There is no second
independently-fixed behavior; one prepatch covers the whole change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — switching the
reference key from the serialized value (call form) to the symbolic name
(subscript form) and dropping the payload imports — is modeled **deeply**
(`memberReference`, `quotedName`, `referenceImports` in the `pure` region, steps
A4/A5), not hidden behind an axiom about the function under change. There are no
consumed axioms and no A-reference deep models: the post-patch reference
construction calls no outside callee (mapping.md §3.1), so `axiom_check.py`
(G-AX) is a skip stub.

## D. verify(Solution) ⇒ resolved

`referenceEnumMember` verifies only if its result is exactly
`(memberReference module className memberName, referenceImports module)` —
i.e. the symbolic-name subscript reference with only the module import (A4/A5),
and the payload provably unused (A3, directive 5). The claim is made on the
spec's declared domain `require ∀ c ∈ memberName, isIdentChar c` — exactly the
names class-body enum members can have. By R (`str ↔ List Char`, the
`(str,set)` ↔ pair bijection, and the identifier-domain `%r` exactness of
mapping.md §3.2, exact on the `require`-pinned domain) the verified operation
equals the gold patch's
`('%s.%s[%r]' % (module, name, value.name), {'import %s' % module})` on the
tested inputs; by G-CONF the R/I transliteration agrees with the REAL patched
`EnumSerializer.serialize` on ≥10⁵ inputs. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc + G-CONF); there are no axioms to trust (G-AX is a skip).
