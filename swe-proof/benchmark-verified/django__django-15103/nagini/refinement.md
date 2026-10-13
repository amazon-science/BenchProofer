# refinement.md — django__django-15103

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_json_script` impl region + the constant `@Pure` markup helpers) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The wrapper site — `django.utils.html.json_script` (`html.py:64`)

Gold hunk (the behavioural change):
```
- return format_html(
-     '<script id="{}" type="application/json">{}</script>',
-     element_id, mark_safe(json_str)
- )
+ if element_id:
+     template = '<script id="{}" type="application/json">{}</script>'
+     args = (element_id, mark_safe(json_str))
+ else:
+     template = '<script type="application/json">{}</script>'
+     args = (mark_safe(json_str),)
+ return format_html(template, *args)
```
(plus the signature change `def json_script(value, element_id):` →
`def json_script(value, element_id=None):` and a docstring tweak.)

| # | model.py impl op (`build_json_script`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `payload: List[int]` | the local `json_str` = `json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)` | R | `str` ↔ `List[int]` code points (mapping.md §2). The serialization+escape step is UNCHANGED by the patch; the model takes its output as the `payload` input. |
| A2 | param `element_id: Optional[List[int]]` | `element_id` argument (now `=None` default) | R | `None` ↔ absent; non-empty list ↔ present token; empty list ↔ empty (falsy) token. The model's presence test `element_id is not None and len(element_id) > 0` is the refinement of Python truthiness `if element_id:` (mapping.md §2). |
| A3 | the present-branch result `prefix_with_id(element_id) + payload + tag_close()`, i.e. `'<script id="' + element_id + '" type="application/json">' + payload + '</script>'`, assembled by the two verified loops | `format_html('<script id="{}" type="application/json">{}</script>', element_id, mark_safe(json_str))` | I + R | the present branch is the SAME concrete template as before the patch. The constant literals are identical character sequences (I); `element_id`/`payload` carry through `format_html` positional interpolation as their characters (R: `mark_safe(json_str)` is already safe = identity; the tested `element_id` has no HTML-special chars = identity; mapping.md §2). Validated == the real callee by G-AX. |
| A4 | the absent-branch result `tag_open_no_id() + payload + tag_close()`, i.e. `'<script type="application/json">' + payload + '</script>'`, assembled by the verified loop | `format_html('<script type="application/json">{}</script>', mark_safe(json_str))` | I + R | the NEW id-free template; constant literals identical (I); `payload` interpolated as its characters (R). This is the branch the patch adds; the id attribute is absent entirely. |
| A5 | the branch selection `if element_id is not None and len(element_id) > 0` | the gold's `if element_id:` | R | refinement of Python truthiness on a `str|None` to the `Optional[List[int]]` carrier (mapping.md §2): both pick the id-bearing template iff the identifier is truthy. |

The discriminating content of the change — *the id attribute is OMITTED when no
identifier is supplied* — lives in the `else`/absent branch (A4): the output is
`tag_open_no_id() + payload + tag_close()` (no `id="..."` segment). The pre-patch
code had no such branch and ALWAYS emitted the id-bearing template;
`model_prepatch.py` reproduces that (a single always-id-bearing path) and **fails**
the postcondition
`Implies(element_id is None or len(element_id) == 0, ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close())`,
which is exactly the spec sensing the change (G-DIFF).

## B. The template-filter site — `defaultfilters.json_script` (`defaultfilters.py:86`)

Gold hunk:
```
- def json_script(value, element_id):
+ def json_script(value, element_id=None):
      """... tag (with an optional id)."""
      return _json_script(value, element_id)
```

This site is a pure pass-through: it forwards `(value, element_id)` to
`django.utils.html.json_script` (`_json_script`) unchanged; the only edit is the
`element_id=None` default + a docstring word. It introduces NO observable
behaviour beyond making the argument optional at the filter boundary, which is
the same R-refinement of optionality already captured by A2/A5. There is thus no
independent behaviour to model and no separate failing `model_prepatch_<k>`: the
F2P template test `test_without_id` exercises exactly the absent-id wrapping that
site A's prepatch already fails on. (Per SPEC_GUIDE §3, one failing prepatch per
independently-observable fixed behaviour; both sites fix the single behaviour
"id attribute is optional", observed in `build_json_script`.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or (for the executable wrapper assumption) an
A-reference checked by G-AX. The one operation that genuinely *changed* — the
conditional selection of the id-free template and the omission of the id
attribute — is modeled **deeply** and concretely (constant code-point literals +
two verified append loops, branching on the presence of the identifier), not
hidden behind an axiom about the function under change. There is **no consumed
`@ContractOnly` axiom**: the only callees invoked (`format_html`, `mark_safe`,
`json.dumps`, `str.translate`) are UNCHANGED and structure-preserving (R), and
their structure-preservation is validated == the real post-patch callee by
axiom_check.py (the A-reference of mapping.md §3, G-AX).

## D. verify(model) ⇒ resolved

**Total correctness.** `build_json_script` carries `Requires(MustTerminate(2))`:
wrapping is a bounded, straight-line assembly, so the operation must terminate
and return the wrapped element. Without this obligation the value
postconditions could be satisfied vacuously by an implementation that never
returns (an infinite loop verified against the value-only spec — the exact
rival the G-PANEL-1 audit exhibited, whose faithful real patch hangs every
F2P/P2P test). Under the obligation, every loop must consume it with a
strictly decreasing measure; the gold-faithful copy loops discharge it with
`Invariant(MustTerminate(len(...) - i + 1))` inside the impl region, while a
diverging rival is rejected by Nagini's obligation system ("Obligation leak
check failed"). The real `json_script` trivially terminates (a constant-size
`format_html` call), so the obligation is faithful, not spec-too-strong.

`build_json_script` verifies only if (A4) the absent-identifier output is the
id-free wrapping `tag_open_no_id() + payload + tag_close()` (no `id="..."`) and
(A3) the present-identifier output is the id-bearing wrapping. By R (str ↔
List[int]; `mark_safe`/`format_html` structure preservation, validated by G-AX)
the verified assembler equals `format_html(template, *args)` with the patch's
branch selection on the tested inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
G-AX-validated wrapper assumption — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: the wrapper-structure soundness
(G-AX, here an A-reference, no consumed axiom) and refinement fidelity (this
document, G-EQ).
