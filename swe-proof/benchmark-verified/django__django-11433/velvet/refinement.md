# refinement.md — django__django-11433

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `assignCleanedValues` `do` block and the `applies`/`applyPlan` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The per-field decision — `construct_instance()` (`django/forms/models.py:40-59`)

Gold hunk:
```
-        if (f.has_default() and
-                form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name))):
+        if (
+            f.has_default() and
+            form[f.name].field.widget.value_omitted_from_data(form.data, form.files, form.add_prefix(f.name)) and
+            cleaned_data.get(f.name) in form[f.name].field.empty_values
+        ):
             continue
```

The hunk lives inside the `for f in opts.fields` loop. Before this guard the
loop already `continue`s past fields that are not editable / are auto keys / are
absent from cleaned data / are excluded by the `fields`/`exclude` selection
(`models.py:42-47`) — the **eligibility** gate, unchanged. After the guard the
field's cleaned value is written via `save_form_data` (`models.py:55-62`),
unchanged. The patch adds the third conjunct (`cleaned_data.get(f.name) in
form[f.name].field.empty_values`) to the "leave the model fallback" guard.

| # | Solution.lean impl op (`assignCleanedValues`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `fields : List Field` | the `opts.fields` sequence the `for` loop iterates | R | model-field sequence ↔ `List Field` (mapping.md §2); each visited field ↔ one `Field`. |
| A2 | `f.eligible` | the four prior `continue` gates `models.py:42-47` (`editable`, not `AutoField`, `f.name in cleaned_data`, `fields`/`exclude` selection) | R + I | an ineligible field is skipped before the changed guard is reached; bundled into one boolean (mapping.md §2). Unchanged by the patch. G-CONF drives the real gates with real form/model objects. |
| A3 | `f.modelHasDefault` | `f.has_default()` (`models.py:51`) | R + I | `has_default()` ↔ `modelHasDefault` (mapping.md §2). Unchanged callee, fixed semantics, exercised by G-CONF. |
| A4 | `f.noIncomingValue` | `form[f.name].field.widget.value_omitted_from_data(...)` (`models.py:52`) | R + I | the widget's payload-omission check ↔ `noIncomingValue` (mapping.md §2). Unchanged callee. |
| A5 | `f.cleanedValueEmpty` | `cleaned_data.get(f.name) in form[f.name].field.empty_values` (`models.py:53`, the **added** conjunct) | R + I | membership in `[None,'',[],(),{}]` ↔ `cleanedValueEmpty` (mapping.md §2). The single behavioural change, modeled identically. |
| A6 | `applies f = eligible && !(modelHasDefault && noIncomingValue && cleanedValueEmpty)` | the loop hands `f`'s cleaned value to its write step (reaches `save_form_data`) iff eligible AND the post-patch `if (… and … and …): continue` does **not** fire | I | the negation/conjunction of A2-A5 is the exact post-patch decision; the changed string of conjuncts is spelled out identically. mapping.md §1. |
| A7 | `out = applyPlan fields` (the per-field decision list, built by the backward `while` fold) | the per-field outcomes of the whole `for` loop (each field either skipped or handed to `save_form_data`) | R + I | the fold computes exactly the left-to-right per-field decision sequence; the file-field deferral reorders hand-offs but not which fields are handed off (mapping.md §1), so the observable list is identical. |

The modeled observable is the **hand-off decision** (mapping.md §1 boundary
note): whether the loop reaches `f.save_form_data(instance,
cleaned_data[f.name])` for the field, vs `continue`-ing past it so the model
fallback stands. `save_form_data` itself is an unchanged callee downstream of
the boundary; some field classes' write steps interpret particular handed
tokens as "no change" and leave the attribute untouched, but that token
handling predates and is untouched by the patch — the patch changes only which
fields are handed off. G-CONF instruments the hand-off directly on the real
patched `construct_instance`, and additionally pins hand-off ⇔
attribute-changed for plain text-valued fields, where the write step is an
unconditional attribute write (this is the slice the F2P test grades).

Discriminating content of the change — a field that **has a model default**,
**was omitted from the submitted payload**, but whose **cleaned value is
non-empty** — is handed to its write step (`applies = true`) by the post-patch
decision because the third conjunct `cleanedValueEmpty` is false, so the
"leave the fallback" guard does not fire. This lives in the third conjunct of
`applies`. The
pre-patch guard lacked that conjunct (it deferred to the model fallback whenever
the field had a default and the payload omitted it, regardless of the cleaned
value); `Solution_prepatch.lean` reproduces that 2-conjunct guard and **fails**
`out = applyPlan fields` (G-DIFF) precisely when `modelHasDefault &&
noIncomingValue && !cleanedValueEmpty` holds — the F2P scenario.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the per-field
skip guard gaining a third conjunct — is modeled **identically** (`applies`,
step A6), not hidden behind an axiom. There are no unchanged opaque callees whose
contract the proof must assume: `has_default`, `value_omitted_from_data`, and the
`in empty_values` membership are Django/Python builtins with fixed semantics,
refined to the `Field` fields per mapping.md §2 and exercised on real objects by
G-CONF. Hence no consumed axioms and no A-references; G-AX confirms the
no-axiom claim and the builtin semantics.

## C. verify(Solution) ⇒ resolved

The spec is stated under **total-correctness semantics**
(`loom.semantics.termination "total"`, with a `decreasing` measure required on
every loop), so a verifying impl must *terminate* and return; divergent impls
(e.g. a correct fold followed by an infinite spin loop) are rejected at
verification, closing the partial-correctness vacuity lever. Given termination,
`assignCleanedValues` verifies only if its output equals, field by field, the
exact post-patch decision `applies` (A6) — in particular handing off a field
whose cleaned value is non-empty even when it has a default and the payload
omitted it (A5 false ⇒ guard does not fire ⇒ `applies = true`). By R
(`opts.fields` ↔ `List Field`, the four builtins ↔ the `Field` booleans,
hand-off-or-skip ↔ the `Bool` entry) the verified decision list equals the
per-field hand-off outcome of the patched `construct_instance` on the tested
inputs; by G-CONF the R/I transliteration of `applies`/`applyPlan` agrees with
the real patched `construct_instance`'s hand-off observable on ≥10⁵ fuzzed
real forms/models. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). Trust points reduce
to refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness
leg (no axioms).
