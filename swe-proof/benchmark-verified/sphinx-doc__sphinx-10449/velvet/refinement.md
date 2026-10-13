# refinement.md — sphinx-doc__sphinx-10449

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `emitReturnTypeEntry` and `emitReturnTypeForKind` `do` blocks and the pure
region they reference) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the narrative is audited by **G-EQ**. `patch.diff` is the gold patch **verbatim**
(G-RESOLVE).

## A. The entry-builder site — `modify_field_list` (`typehints.py:86`)

Gold hunk (the trailing return-type block, post-patch):
```
     if 'return' in annotations and 'return' not in arguments:
+        annotation = annotations['return']
+        if annotation == 'None' and suppress_rtype:
+            return
+
         field = nodes.field()
         field += nodes.field_name('', 'rtype')
         field += nodes.field_body('', nodes.paragraph('', annotation))
         node += field
```
and the signature gains `suppress_rtype: bool = False`.

| # | Solution.lean impl op (`emitReturnTypeEntry`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `hasReturnAnno : Bool` | `'return' in annotations` | R | membership read ↔ Bool (mapping.md §2). |
| A2 | `returnInArgs : Bool` | `'return' not in arguments` (negated in the guard) | R | membership read ↔ Bool; the guard is `... and 'return' not in arguments`, so the append-regime predicate is `hasReturnAnno && !returnInArgs`. |
| A3 | `if hasReturnAnno && !returnInArgs then …` | the `if 'return' in annotations and 'return' not in arguments:` guard | I | identical Boolean control flow. |
| A4 | `returnAnnotation : List Char` | `annotation = annotations['return']` | R | `str` ↔ `List Char` (mapping.md §2). |
| A5 | `if (returnAnnotation == "None".toList) && omitNoneReturnType then return none` | `if annotation == 'None' and suppress_rtype: return` (no field appended) | I + R | the added early-return guard; `'None'` literal ↔ `"None".toList`, `suppress_rtype` ↔ `omitNoneReturnType` (R); the control flow (skip the append) is I, modeled as `none`. |
| A6 | `else return (some returnAnnotation)` | build `field` with `field_body('', paragraph('', annotation))` and `node += field` | I + R | the entry is appended carrying the annotation text; the constant `rtype`/field structure is unchanged (I), abstracted to the carried text `some returnAnnotation` (R, mapping.md §2 last row). |

Discriminating content: the suppression branch (A5). The pre-patch
`modify_field_list` had no `suppress_rtype` and always reached A6 — so it
appended `some "None"` where the spec now requires `none`.
`Solution_prepatch_1.lean` reproduces that (drops A5) and **fails** the
`emitReturnTypeEntry` postcondition (G-DIFF).

## B. The dispatch site — `merge_typehints` "all" arm (`typehints.py:61`)

Gold hunk (post-patch):
```
             if app.config.autodoc_typehints_description_target == "all":
-                modify_field_list(field_list, annotations[fullname])
+                if objtype == 'class':
+                    modify_field_list(field_list, annotations[fullname], suppress_rtype=True)
+                else:
+                    modify_field_list(field_list, annotations[fullname])
```

| # | Solution.lean impl op (`emitReturnTypeForKind`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `kind : List Char` | `objtype` argument | R | descriptor kind str ↔ `List Char` (mapping.md §2). |
| B2 | `if isClassKind kind then …` | `if objtype == 'class':` | I + R | `objtype == 'class'` ↔ `kind == "class".toList` (R, `isClassKind`); the branch is I. |
| B3 | (then) `emitReturnTypeEntry … true` | `modify_field_list(..., suppress_rtype=True)` | I + R | delegates to site A with the suppress flag set; callee-under-spec (`emitReturnTypeEntry_correct`), not an axiom. |
| B4 | (else) `emitReturnTypeEntry … false` | `modify_field_list(annotations[fullname])` (default `suppress_rtype=False`) | I + R | delegates with the flag unset; the default keeps prior behavior for non-class kinds. |

Discriminating content: the class branch (B2/B3) — only a class kind sets the
suppress flag. The pre-patch `merge_typehints` had no `if objtype == 'class'`
and called the modifier with the default (no suppression) for every kind.
`Solution_prepatch_2.lean` reproduces that (always delegates with `false`) and
**fails** the class-kind postcondition `out = none` (G-DIFF).

Inter-method: `emitReturnTypeForKind` calls `emitReturnTypeEntry` via
`let r ← emitReturnTypeEntry …`; `prove_correct` discharges the caller using the
generated `emitReturnTypeEntry_correct` — callee-under-spec, strictly better than
an axiom (SPEC_GUIDE §3).

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. There is **no consumed axiom** and **no A-reference**: the
patch adds only control flow (a kind test and a `None`-suppression guard) and
threads a Boolean flag; the `nodes.field()` entry-construction is byte-identical
pre/post-patch (an I op carried as the `Option (List Char)` entry text). No
unchanged library callee's contract is needed by the proof, and no changed
string/numeric op is hidden behind an axiom. `axiom_check.py` is therefore a
no-axiom stub and G-AX is `skip` (mirroring sphinx-9229).

## D. verify(Solution) ⇒ resolved

`emitReturnTypeEntry` verifies only if its output omits the entry exactly when
the annotation is `None` and suppression is requested (A5), and otherwise carries
the annotation (A6); `emitReturnTypeForKind` verifies only if a class kind sets
suppression and other kinds do not (B2-B4), with the class-`None` case pinned to
`none` and the non-class case pinned to `some returnAnnotation`. By R
(`str ↔ List Char`, membership ↔ Bool, the constant `rtype` field structure) the
verified decisions equal the gold-patched `modify_field_list`/`merge_typehints`
behavior on the documented objects the F2P test exercises; by G-CONF the R/I
transliteration agrees with `patch.diff`'s real behavior on ≥10⁵ fuzzed inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axiom trust points (G-AX skip); the sole trust point is refinement fidelity
(this doc, G-EQ + G-CONF).
