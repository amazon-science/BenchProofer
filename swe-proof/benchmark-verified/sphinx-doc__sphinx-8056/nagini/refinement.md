# refinement.md — sphinx-doc__sphinx-8056

The operation-by-operation correspondence between `model.py`'s implementation
(the `emitted_names` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures` for an unchanged callee), **A-reference** (a deep model validated ==
the real callee by G-AX, not consumed), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed `_consume_fields` per-field body (`docstring.py:269-277`)

Gold hunk:
```
-            if _name or _type or _desc:
+            if multiple and _name:
+                for name in _name.split(","):
+                    fields.append((name.strip(), _type, _desc))
+            elif _name or _type or _desc:
                 fields.append((_name, _type, _desc,))
```
plus the signature gains `multiple: bool = False`.

| # | model.py impl op (`emitted_names`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `name: List[int]` | the local `_name: str` of one consumed field | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | parameter `multiple: bool` | the new `multiple: bool` parameter | I | identical boolean. |
| A3 | `type_nonempty`, `desc_nonempty: bool` | truthiness of `_type` / `_desc` | R | only the keep-guard `_name or _type or _desc` reads them; their content is shared verbatim across emitted entries (mapping.md §2), so non-emptiness is the only observable. |
| A4 | branch `if multiple and len(name) > 0:` | branch `if multiple and _name:` | R+I | `_name` truthy ↔ `len(name) > 0` (empty `str` ↔ `[]`); the `and` is identical. |
| A5 | `parts = split_on_comma(ToSeq(name))`, loop `i in 0..n` building `result + PSeq(trim(parts[i]))` | `for name in _name.split(","): fields.append((name.strip(), _type, _desc))` | A-consumed | `split_on_comma` ↔ `str.split(',')` and `trim` ↔ `str.strip()` are the unchanged stdlib callees the new loop invokes (mapping.md §3.1-3.3). The proof consumes the `split_on_comma` count `Ensures` (`len == num_commas+1`); the content `Result()[k] == trim(split_on_comma(name)[k])` is discharged by construction (the impl returns exactly that). The emitted entries are the NAME runs; `_type`/`_desc` ride along unchanged (A3). |
| A6 | else: append `ToSeq(name)` once when `len(name) > 0 or type_nonempty or desc_nonempty`, else nothing | `elif _name or _type or _desc: fields.append((_name, _type, _desc,))` | R+I | the legacy keep-guard, unchanged; the single emitted name is the verbatim (unsplit, untrimmed) `_name` ↔ `ToSeq(name)`. |

## B. The call-site change (`_parse_parameters_section`, `docstring.py:683-688`)

Gold hunk:
```
-        fields = self._consume_fields()
         if self._config.napoleon_use_param:
+            fields = self._consume_fields(multiple=True)
             return self._format_docutils_params(fields)
         else:
+            fields = self._consume_fields()
             return self._format_fields(_('Parameters'), fields)
```

This change supplies `multiple=True` exactly in the `napoleon_use_param` branch.
It is captured by the `multiple` parameter of `emitted_names` (A2/A4): the
F2P test exercises BOTH configurations —

* `napoleon_use_param=True`  ⇒ `multiple=True`  ⇒ the multi-name field
  `"x1, x2"` is expanded to two entries `x1`, `x2` (model branch A5, spec clause
  `len(Result()) == num_commas+1` and `Result()[k] == trim(split[k])`);
* `napoleon_use_param=False` ⇒ `multiple=False` ⇒ the same field stays a single
  verbatim entry `"x1, x2"` (model branch A6, spec clause `len <= 1`,
  `Result()[0] == ToSeq(name)`).

Both are pinned by the single frozen spec; no second spec is needed. The downstream
formatters (`_format_docutils_params`, `_format_fields`) are unchanged and emit
one rendered line per `fields` entry, so the field-count change is exactly the
rendered-output change the F2P test asserts.

## C. The discriminating clause (G-DIFF)

The pre-patch `_consume_fields` had no `multiple` parameter and
`_parse_parameters_section` always called `_consume_fields()` — so a multi-name
field was kept as ONE entry regardless of configuration. `model_prepatch.py`
reproduces that (the impl ignores `multiple` and always takes branch A6) and
**fails** the postcondition

  `Implies(multiple and len(name) > 0, len(Result()) == num_commas(ToSeq(name)) + 1)`

— exactly the clause sensing the change: when expansion is requested and the
name carries a comma, the patched code emits `commas+1` entries, the pre-patch
emits 1. This is precisely what F2P `test_multiple_parameters` observes
(`"x1, x2"` → two `:param` entries under `napoleon_use_param=True`).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
is the control-flow choice to expand the name run per comma; it is modeled
DIRECTLY (the `if multiple and len(name) > 0` branch and its loop), NOT hidden
behind an axiom about the function under change. The three consumed axioms
(`num_commas`, `split_on_comma`, `trim`) cover only the UNCHANGED stdlib callees
the new loop invokes (`str.count`/`str.split`/`str.strip`); their soundness is
audited by G-AX (axiom_check.py runs the real built-ins). There are no
A-reference deep models in this bundle.

## E. verify(model) ⇒ resolved

`emitted_names` verifies only if, under the per-comma expansion, it emits
`num_commas+1` entries each equal to `trim(split_on_comma(name)[k])` (A5), and
otherwise emits the single verbatim name under the legacy keep-guard (A6). By R
(`str` ↔ `List[int]`, the `_type`/`_desc` ride-along) the verified behaviour
equals the gold `_consume_fields`/`_parse_parameters_section` per-field
behaviour; by G-AX the axiomatized callees are sound stand-ins for the real
`str.split`/`str.strip`/`str.count`, and the composed observable equals the gold
patch on boundary + fuzz. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and audited callees — and the
gold patch resolves (G-RESOLVE). The trust points are the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
