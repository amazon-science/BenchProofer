# refinement.md — django__django-15503

The operation-by-operation correspondence between `model.py`'s implementation
(the `compile_final_key_segment` impl region and the deep `member_access_segment`
/ `json_string_literal` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The final-key compilation site — the new `compile_json_path_final_key`

Gold hunks (`django/db/models/fields/json.py`):
```
+    def compile_json_path_final_key(self, key_transform):
+        # Compile the final key without interpreting ints as array elements.
+        return ".%s" % json.dumps(key_transform)
...
-            rhs_params.append(
-                "%s%s"
-                % (
-                    lhs_json_path,
-                    compile_json_path(rhs_key_transforms, include_root=False),
-                )
-            )
+            *rhs_key_transforms, final_key = rhs_key_transforms
+            rhs_json_path = compile_json_path(rhs_key_transforms, include_root=False)
+            rhs_json_path += self.compile_json_path_final_key(final_key)
+            rhs_params.append(lhs_json_path + rhs_json_path)
```

| # | model.py impl op (`compile_final_key_segment`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `key: List[int]` | `key_transform` (a `str` key) of `compile_json_path_final_key` | R | `str` ↔ `List[int]` code points (mapping.md §2). The final key is the last element of `rhs_key_transforms` (`*rhs_key_transforms, final_key = ...`). |
| A2 | `result = [46, 34]` then append each `key[i]` then `[34]`, i.e. `Result() == member_access_segment(ToSeq(key)) == '.' + '"' + key + '"'` | `".%s" % json.dumps(key_transform)` | A-reference | the changed serialization step is modeled **deeply**: `member_access_segment` / `json_string_literal` (spelled out in the `pure` region) and the verified loop in `compile_final_key_segment` ARE the step `. + json.dumps(key)`. There is no consumed serialization axiom. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `compile_json_path_final_key` (real `json.dumps`) on boundary+fuzz and asserts equality on the modelled domain (`json.dumps(key) == '"'+key+'"'`, mapping.md §3.1). |
| A3 | the `'.'` separator `46` and the surrounding quotes `34` | the leading `"."` and the quotes `json.dumps` emits | I | identical literals under the code-point bijection. |
| A4 | (modelling restriction) `in_domain(ToSeq(key))` | (no node) | R | the key domain on which the deep model equals `json.dumps`; printable ASCII minus quote/backslash. Outside it `json.dumps` escapes; inside it the F2P keys and ordinary keys live. |

The remaining gold operations in `as_sql` are an **R/I** rearrangement that does
not change the modeled behaviour of the FINAL key:
`*rhs_key_transforms, final_key = rhs_key_transforms` (split off the last key) +
`compile_json_path(rhs_key_transforms, include_root=False)` (the UNCHANGED prefix
compiler) + `... += self.compile_json_path_final_key(final_key)` (the modeled
final step) + `rhs_params.append(lhs_json_path + rhs_json_path)`. The prefix
compiler is unchanged (a deeper array path into nested objects/arrays keeps the
same `[i]`/`."k"` semantics it always had); the single *behavioural* change is
that the FINAL key now uses the member-access form rather than the array-aware
`compile_json_path` — which is precisely `member_access_segment` (A2).

The discriminating content of the change — a numeric key `"1111"` / `"000"` →
the object-member step `."1111"` / `."000"` rather than the array-element step
`[1111]` / `[0]` — lives in `member_access_segment(key)` always beginning with
`.`(46)`"`(34) and reproducing `key` verbatim (model) ⇔ `".%s" % json.dumps(key)`
(real). `model_prepatch.py` reproduces the pre-patch array-element branch for an
all-digit key and **fails** the postcondition
`ToSeq(Result()) == member_access_segment(ToSeq(key))` (G-DIFF).

## B. The subclass-wiring / vendor-routing hunks (no separate model)

Gold also adds `class HasKeyOrArrayIndex(HasKey)` (overriding
`compile_json_path_final_key` back to the array-aware `compile_json_path([key],
include_root=False)`) and re-points three Oracle/SQLite `isnull`/`KeyTransform`
call sites from `HasKey` to `HasKeyOrArrayIndex`. These select, per call site,
**which of the two already-modeled segment forms** the final key takes
(member-access for an object key; array-element for a genuine array index). They
introduce no new computation: the member form is `compile_final_key_segment`
(A2), the array form is exactly what `model_prepatch.py` produces. They are pure
**R/I** class-wiring; no kind-3 step. Their correctness is exercised by the gold
patch under G-RESOLVE (which runs all sites) and audited here for G-EQ.

Why no separate failing `model_prepatch` for site B: site B only routes the
final key to one of the two forms already modeled in site A; the single shared
behaviour (member-access for an OBJECT key) is the F2P discriminator and is
already sensed by site A's prepatch. A second skeleton would re-test the same
clause.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — compiling the final key into a member-access path step instead of
an array-index step — is modeled **deeply** (the spelled-out
`member_access_segment` / `json_string_literal` consumed in
`compile_final_key_segment`, step A2, an **A-reference**), not hidden behind an
axiom about the function under change. There is **no consumed `@ContractOnly`
axiom**: the only stdlib callee involved (`json.dumps`) is the one the changed
step uses, and it is modeled as the A-reference deep model that G-AX validates,
not consumed. The `axioms` region is intentionally empty.

## D. verify(model) ⇒ resolved

`compile_final_key_segment` verifies only if its output equals the exact
member-access step `. " key "` for EVERY in-domain key, numeric or not (A2 +
the explicit structural clauses: begins with `.`(46)`"`(34), ends with `"`(34),
length `len(key)+3`, key verbatim between the quotes). By R (str ↔ List[int],
the code-point bijection) the verified step equals `".%s" % json.dumps(key)` on
the modelled domain (G-AX, A-reference) — which is exactly the body of the new
`compile_json_path_final_key`. The unchanged prefix compiler and the
subclass-wiring (site B) are R/I rearrangements that route the final key to one
of the two already-modeled forms. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: deep-model fidelity (G-AX, A-reference) and refinement
fidelity (this document, G-EQ).
