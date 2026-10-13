# refinement.md — sphinx-doc__sphinx-8056

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `splitSharedNameFields` and `buildParameterFieldSeq` `do` blocks, the deep
`expandOne`/`expandFields`/`splitOnComma`/`stripWs` models) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-reference**
(deep model validated == the real callee by G-AX), **A-consumed** (proof uses an
axiom's `ensures` — none here), or **I** (identical concrete op). EVERY step is
R, A, or I; there is no kind-3 (inexpressible changed op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs are validated by **G-AX**; this narrative is audited
by **G-EQ**. `patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The collector — `_consume_fields` gains `multiple`

Gold hunk (`docstring.py:269-281` post-patch):
```
-    def _consume_fields(self, parse_type=True, prefer_type=False):
+    def _consume_fields(self, parse_type=True, prefer_type=False, multiple=False):
         self._consume_empty()
         fields = []
         while not self._is_section_break():
             _name, _type, _desc = self._consume_field(parse_type, prefer_type)
-            if _name or _type or _desc:
+            if multiple and _name:
+                for name in _name.split(","):
+                    fields.append((name.strip(), _type, _desc))
+            elif _name or _type or _desc:
                 fields.append((_name, _type, _desc,))
         return fields
```

| # | Solution.lean impl op (`splitSharedNameFields`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `multiple : Bool` | the new `multiple: bool = False` parameter | R | direct `bool ↔ Bool` (mapping.md §2). |
| A2 | param `raw : List Field` | the sequence of `_consume_field(...)` results gathered by `while not self._is_section_break()` | R | the unchanged scanner output is a FREE INPUT (mapping.md §1); `Tuple[str,str,List[str]] ↔ Field` (mapping.md §2). G-CONF feeds the same `raw` to both legs. |
| A3 | the backward `while` fold building `result = expandFields multiple raw` | the `while` loop appending into `fields` | I | both iterate the raw fields in order and concatenate each field's contribution; the backward fold computes the same left-to-right sequence (proven by `expandFields_drop_step`). |
| A4 | `expandOne multiple f` — branch `multiple ∧ f.name ≠ []` ⇒ `(splitOnComma f.name).map (name := stripWs ·)` | `if multiple and _name: for name in _name.split(","): fields.append((name.strip(), _type, _desc))` | I + A-reference | the per-piece field construction (shared `_type`/`_desc`, name replaced) is **I**; the split `splitOnComma` (== `str.split(",")`) and trim `stripWs` (== `str.strip()`) are **A-reference**, validated by G-AX (mapping.md §3.1-3.2). |
| A5 | `expandOne` else-branch: `if f.name ≠ [] ∨ f.typ ≠ [] ∨ f.desc ≠ [] then [f] else []` | `elif _name or _type or _desc: fields.append((_name, _type, _desc,))` | I | the verbatim-keep-when-nonempty branch, transliterated. Python truthiness of str/list ↔ `≠ []` (mapping.md §2). |

The discriminating content of the change — a field whose name lists several
comma-separated parameters becomes several fields when `multiple` — lives in
A4's `multiple ∧ f.name ≠ [] ⇒ (splitOnComma f.name).map …`. The pre-patch
collector had no `multiple` capability and always took A5 (verbatim keep);
`Solution_prepatch.lean` reproduces that and **fails** `out = expandFields
multiple raw` precisely on this clause (G-DIFF — the unsolved goal is exactly
`[f] = expandOne multiple f` under `multiple ∧ name ≠ []`).

## B. The caller — `_parse_parameters_section` wires `multiple=True`

Gold hunk (`docstring.py:683-691` post-patch):
```
     def _parse_parameters_section(self, section):
-        fields = self._consume_fields()
         if self._config.napoleon_use_param:
+            fields = self._consume_fields(multiple=True)
             return self._format_docutils_params(fields)
         else:
+            fields = self._consume_fields()
             return self._format_fields(_('Parameters'), fields)
```

| # | Solution.lean construct (`buildParameterFieldSeq`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `let fields ← splitSharedNameFields splitNames raw` | `self._consume_fields(multiple=True)` under `napoleon_use_param`, `self._consume_fields()` otherwise | I (callee-under-spec) | `splitNames` is passed straight through as `multiple`: when `splitNames` the collector expands (`multiple=True`); when not, `splitNames=False` makes `expandFields false raw` keep names verbatim — matching the `else` branch's `_consume_fields()` (default `multiple=False`). `splitSharedNameFields` is the callee-under-spec; `prove_correct` applies `splitSharedNameFields_correct`. |
| B2 | `return fields` | `return self._format_docutils_params(fields)` / `self._format_fields(…, fields)` | R | the two renderers are unchanged, deterministic functions of the field sequence (mapping.md §3.3); pinning the field sequence pins the rendered output the F2P test observes. Identity-on-fields boundary, out of R/I fuzz scope. |

`buildParameterFieldSeq`'s spec `out = expandFields splitNames raw` collapses both
branches: `splitNames` selects whether the collector expands. This is faithful
because the only behavioural difference between the two branches that the F2P
test observes is the field sequence — both render it deterministically.

### Why no separate prepatch for site B
Site B is pure wiring: it threads `splitNames` into the collector's `multiple`. Its
observable effect is entirely the field sequence `splitSharedNameFields` returns,
whose change is already exercised by site A's prepatch (the collector ignoring
`multiple`). A prepatch must keep the spec byte-identical (G-DIFF); the site-B
`do` block is a one-line callee call with nothing independently buggable that
would not duplicate site A's discriminator. `Solution_prepatch.lean` therefore
fixes the discriminator at site A (`splitSharedNameFields`), which is the single
independently-observable fixed behavior (the F2P test calls the section parser,
exercising both methods through the shared collector).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operations that genuinely *changed* —
the comma split and the per-piece field construction — are modeled **deeply**
(`splitOnComma`/`stripWs` in the `pure` region, A-reference; the `map` and
concatenation, I), not hidden behind an axiom about the function under change.
There are no consumed axioms: the only callees (`str.split(",")`, `str.strip()`)
are modeled deeply and validated == real by G-AX, and the unchanged scanner is a
free input.

## D. verify(Solution) ⇒ resolved

`splitSharedNameFields` verifies only if its output equals `expandFields multiple
raw` — i.e. each multi-name field is split-and-trimmed into one field per name
when `multiple` (A4), and kept verbatim-when-nonempty otherwise (A5).
`buildParameterFieldSeq` verifies only if it threads `splitNames` into that
expansion (B1). By G-AX the deep models `splitOnComma`/`stripWs` equal the real
`str.split(",")`/`str.strip()` (A-reference); by G-CONF the R/I transliteration
of the expansion agrees with `patch.diff`'s loop body on ≥10⁵ inputs; by R the
unchanged renderer maps the pinned field sequence to the rendered output the F2P
test checks. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and validated callees — and the gold
patch resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-
model fidelity (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
