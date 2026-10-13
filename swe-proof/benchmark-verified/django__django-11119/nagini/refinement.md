# refinement.md — django__django-11119

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_value` impl region, plus the deep `escaped_seq` model in the `pure`
region) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized / deep-modeled callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — `Engine.render_to_string` (`django/template/engine.py:163`)

Gold hunk:
```
-            return t.render(Context(context))
+            return t.render(Context(context, autoescape=self.autoescape))
```

The patch changes ONE thing: the `Context` built for rendering now inherits the
engine's `autoescape` policy instead of taking `Context.__init__`'s `autoescape`
default of `True`. The renderer (`render_value_in_context`,
`django/template/base.py:970-975`) reads `context.autoescape` to decide between
escaping the interpolated value (`conditional_escape(value)`, true branch) and
emitting it verbatim (`str(value)`, false branch). So the *observable* effect of
the change is: the policy that governs per-value escaping is the engine's
`self.autoescape`, not a forced `True`.

`model.py` models this end-to-end observable effect on a single interpolated
value (the F2P template `obj:{{ obj }}` interpolates exactly one value, with a
constant literal prefix/suffix common to both branches and to pre/post-patch).

| # | model.py impl op (`render_value`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: List[int]` | the context value `context['obj']` (a `str`) flowing to `render_value_in_context` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | parameter `engine_autoescape: bool` | `self.autoescape` (`engine.py:44`, the `Engine.__init__` attribute) | I | a Python `bool`; identity. |
| A3 | `ctx_autoescape = engine_autoescape` | `Context(context, autoescape=self.autoescape)` builds a context whose `autoescape` attribute is `self.autoescape` (`context.py:137-138`) | R | `Context.__init__` only stores the flag; the renderer only reads it (`base.py:970`). The boolean assignment is the model's faithful image of "the context inherits the engine's policy". Identity on the boolean. |
| A4 | `if ctx_autoescape:` escaping branch — `result == escaped_seq(value)` computed by the backward per-code-point fold | `render_value_in_context` true branch (`base.py:970-973`): `conditional_escape(value)`, which for a plain `str` value reduces to `django.utils.html.escape(value)` | A-reference | the escape operation is UNCHANGED by this patch; it is modeled **deeply** (`escaped_seq` / `entity` in the `pure` region + the verified loop) and validated **== the real callee** out-of-band by G-AX (axiom_check.py runs `django.utils.html.escape` and asserts `escaped_seq == escape`). There is NO consumed escape axiom; the escaper appears only as the A-reference. mapping.md §3.1. |
| A5 | `else:` verbatim branch — `result == value` copied element-by-element | `render_value_in_context` false branch (`base.py:974-975`): `str(value)` | R + I | for the `str` inputs the F2P passes, `str(value)` is the identity on the character content; the model copies the code-point list verbatim. axiom_check.py confirms `str(value) == value` on the witnesses. |
| A6 | `result` returned (a `List[int]`) | the rendered fragment substituted into the template (`mark_safe`/`SafeString` wrapper on the escape branch) | R | `mark_safe` only sets the safe flag; it does not change the character content the F2P test observes (mapping.md §2). |

The discriminating content of the change — escaping must follow the engine
policy, NOT be forced on — lives in the postcondition pair
`Implies(engine_autoescape, Result == escaped_seq(value))` /
`Implies(not engine_autoescape, Result == value)`. The pre-patch code forces the
context flag to the escaping default (`Context(context)` ⇒ `autoescape=True`);
`model_prepatch.py` reproduces that (`ctx_autoescape = True`, ignoring
`engine_autoescape`) and **fails** the verbatim clause
`Implies(engine_autoescape == False, ToSeq(Result()) == ToSeq(value))` — exactly
the spec sensing the bug (G-DIFF). This is the F2P witness: engine
`autoescape=False`, value `<script>`, required output `<script>` (verbatim), but
the pre-patch escapes it to `&lt;script&gt;`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— which auto-escaping policy the rendering context carries — is modeled directly
as the boolean assignment `ctx_autoescape = engine_autoescape` (A3, an I on the
flag), branched on to choose escaped vs verbatim output. The escaping itself is
UNCHANGED, so it is the **A-reference** (deep model `escaped_seq` validated ==
`django.utils.html.escape` by G-AX), never a consumed axiom and never the thing
the patch alters. There is no `@ContractOnly` axiom in this bundle: the proof
consumes none, so the `axioms` region is empty (no dead axioms).

## C. verify(model) ⇒ resolved

`render_value` verifies only if it escapes exactly when `engine_autoescape` is
true (A4, the per-code-point substitution) and emits the value verbatim when it
is false (A5). By R (str ↔ List[int]; `Context` stores/`render_value_in_context`
reads the flag; `mark_safe`/`str()` identities) the verified function equals the
renderer's behaviour under `Context(context, autoescape=self.autoescape)` on the
tested inputs; by G-AX the deep model `escaped_seq` equals the real
`django.utils.html.escape` (A-reference) and the verbatim branch is the
identity. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the audited escape reference — and the
gold patch resolves (G-RESOLVE). The single trust point is refinement fidelity
(this document, G-EQ) plus the A-reference escape soundness (G-AX); there are no
consumed axioms.
