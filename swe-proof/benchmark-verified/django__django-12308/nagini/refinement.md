# refinement.md — django__django-12308

The operation-by-operation correspondence between `model.py`'s implementation
(the `display_structured_value` dispatch and the deep structural serialiser
`serialize` / `serialize_list`, validated against `interchange_form` /
`fallback_form`) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — split into **A-consumed**, where
the proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The added structured-data branch — `display_for_field` (`django/contrib/admin/utils.py:380`)

Gold hunk (inserted before the final `else`):
```python
+ elif isinstance(field, models.JSONField) and value:
+     try:
+         return field.get_prep_value(value)
+     except TypeError:
+         return display_for_value(value, empty_value_display)
```

| # | model.py impl op (`display_structured_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `value: JNode` (the structured value tree) | the structured `value` argument (a dict / list / str) | R | the rich JSON value ↔ a recursive `JNode` tree (STRING / ARRAY / OBJECT / MEMBER); field bijection in mapping.md §2. |
| A2 | param `empty: List[int]` | `empty_value_display` argument | R | `str` ↔ `List[int]` of code points (mapping.md §2). |
| A3 | param `content: List[int]` | the **output of** `display_for_value(value, empty_value_display)` on the fall-through arm (`utils.py:406`) | R | `str` ↔ `List[int]`; `content` carries that callee's own return value — **not** `str(value)`, since `display_for_value` dispatches on shape and takes a join arm for list/tuple roots (only consulted on the `present and not encodable` branch); mapping.md §2. |
| A4 | param `present: bool` | the `elif value is None` arm at `django/contrib/admin/utils.py:389` — the **only** arm that returns the placeholder | R | `present == (value is not None)`. The two repo guards do **NOT** collapse into this one boolean: the `and value` truthiness guard at `utils.py:401` sits *after* the `value is None` arm, so when it fails on a non-None falsy value control does not reach the placeholder — it falls THROUGH to the final `else` at `utils.py:406`. The guards therefore have **three** outcomes, matching the model's three arms (mapping.md §2). |
| A5 | param `encodable: bool` | the `and value` guard at `utils.py:401` **and** whether `field.get_prep_value(value)` returns vs. raises `TypeError` | R | `encodable == (bool(value) and json.dumps(value) returns)` — both conjuncts, since the encoder's output is displayed only when a truthy value is offered to it and it does not raise (mapping.md §2). |
| A6 | `if not present: return <copy of empty>` | the value renders as `empty_value_display` — reached **only** via the `elif value is None` arm (`utils.py:389`) | I + R | early placeholder return; the loop copies `empty` into a fresh owned list (R on the carrier). A falsy *stored* value does **not** reach here; it is `present` and takes A8. |
| A7 | `if encodable: return serialize(value)`, i.e. `ToSeq(Result()) == interchange_form(value)` | `return field.get_prep_value(value)` == `json.dumps(value)` | **A-reference** | the changed routing's encoder is modelled **deeply and STRUCTURALLY**: `interchange_form` (pure region, via `node_body`/`ser_list`) is the full recursive interchange serialisation of the value tree — a string token between the U+0022 (`"`) delimiters and, INSIDE them, laid down in the interchange alphabet by `esc_seq`/`esc_char` (U+0022 and U+005C each as U+005C + themselves; U+0008/U+0009/U+000A/U+000C/U+000D as U+005C + `b`/`t`/`n`/`f`/`r`; every other code point outside U+0020..U+007E as U+005C, `u` and four lowercase hexadecimal digits, one above U+FFFF as the two such forms of its surrogate halves), arrays bracketed and comma-and-space separated, objects braced with keys laid down the same way and `: ` member separators — and the verified `serialize`/`serialize_list` (through `append_escaped`/`append_esc_char`) build exactly that. There is **no consumed `json_dumps` axiom**; the proof depends on no `@ContractOnly`. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) reproduces the EXACT structural serialiser and asserts `interchange_form(value) == json.dumps(value)` on the three encodable F2P values plus 47 boundary values (every escape class as a token AND as an object key) + 20 000 fuzz nested structured values whose tokens are drawn from the full code point range + a sweep of ALL 1 114 112 code points as a single-token value: 1 135 253 checks, zero divergences. The real `json.dumps` IS this structural double-quote interchange encoding (mapping.md §3.1). |
| A8 | else (`present and not encodable`): `return <copy of content>`, i.e. `ToSeq(Result()) == fallback_form(ToSeq(content))` with `fallback_form` = **identity** | `return display_for_value(value, empty_value_display)` — **returned unchanged**, reached both from the `except TypeError:` arm (`utils.py:405`) and by fall-through from the failed `and value` guard (`utils.py:406`) | **A-reference** | the fallback is modelled as a **pass-through**: `fallback_form` (pure region) is the identity on `content` — the renderer adds NO delimiters of its own. `display_for_value` is **abstracted to the callee whose contract the real one honors**, not reproduced: it dispatches on the value's own shape (join arm `', '.join(str(v) for v in value)` at `utils.py:420` for a list/tuple, general arm `str(value)` at `utils.py:422` otherwise), so `content` carries **its output** rather than `str(value)` — the two differ on every sequence-rooted value (`[{('x','y'):'z'}]` → `{('x', 'y'): 'z'}`, not `[{('x', 'y'): 'z'}]`). This arm also covers the **falsy stored** values, which never reach the encoder and so render as this same text (`[]` → `''`, `{}` → `'{}'`, `0` → `'0'`, `False` → `'False'`). On the non-encodable F2P value, a tuple-keyed dict, the dispatch reaches the general arm and the text is `"{('a', 'b'): 'c'}"` (the F2P expected display, no outer quotes); the single-quote U+0027 delimiters come from `repr` on the tokens INSIDE that text. G-AX imports the **real** `display_for_value` and confirms the identity pass-through on it — on the tuple-key value, on join-arm sequence roots where its text differs from `str(value)`, and on the falsy stored values — plus the single-vs-double-quote contrast (mapping.md §3.2). |

The discriminating content of the change — an encodable value renders as the
full **structural** interchange serialisation with the **double-quote**
delimiter `"` (U+0022) on every string token and key, rather than the
general-purpose display text (whose internal string tokens are single quote `'`,
U+0027) — lives in the contrast `interchange_form` (structural,
`"`/brackets/braces) vs `fallback_form` (that display text unchanged, its
internal tokens `'`-delimited). The pre-patch `display_for_field` had **no**
structured-data branch, so a present value fell through to `display_for_value`
(`str(value)` / `', '.join`, single-quote internal tokens).
`model_prepatch.py` reproduces exactly that (the present value is
routed through the pass-through `fallback_form` path) and **fails** the
postcondition `Implies(present and encodable, ToSeq(Result()) ==
interchange_form(value))` — precisely the spec sensing the change (G-DIFF). The
F2P `test_json_display_for_field` observes this structurally: `'a' → "a"`,
`['a', 'b'] → ["a", "b"]`, `{'a': {'b': 'c'}} → {"a": {"b": "c"}}`, and the
tuple-keyed dict falling back to `str`.

A single-token wrap of the printed value (`'"' + str(value) + '"'`) does **not**
satisfy the spec: for `['a', 'b']` it gives `"a, b"` (or `"['a', 'b']"`),
whereas `interchange_form(value)` is the structural `["a", "b"]`. This is the
G-EQ kill-criterion of SPEC_GUIDE §0.4 — confirmed: that impl fails to verify
against the strengthened spec.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations the new branch
*calls* — the interchange encoder (`json.dumps`) and the general-purpose display renderer
(`str`/`repr`) — are **unchanged callees**; the *changed* thing is the dispatch
that newly routes a structured value through the encoder. That dispatch is
modelled directly (the `present`/`encodable` branch structure, I/R), and the two
callees are modelled **deeply** — the interchange encoder as the spelled-out
recursive STRUCTURAL serialiser `interchange_form` (`node_body`/`ser_list`), the
display fallback as the identity pass-through `fallback_form` — each an **A-reference**
validated == its real callee by G-AX. There is **no consumed `@ContractOnly`
axiom**, so there is no dead axiom and nothing to mislabel.

## C. verify(model) ⇒ resolved

`display_structured_value` verifies only if a present, encodable value renders
as the full structural `interchange_form` (A7) and a non-encodable one as the
unchanged display text `fallback_form(content)` (A8), with an absent value
rendering as the placeholder (A6). By R (str ↔ List[int], the JSON value ↔
`JNode` tree; the `value is None` arm ↔ `not present`; the `and value` guard
conjoined with the `try/except` outcome ↔ `encodable`; and everything else ↔ the
`present and not encodable` fallback, so the repo's **three** outcomes map onto
the model's three arms) the verified function equals the gold branch's behaviour
on the tested inputs; by G-AX the deep model `interchange_form` equals the real
`json.dumps` on the F2P structured values + nested fuzz + every code point as
a token (so the token form, not merely the structural skeleton, is what the
clause pins), and `fallback_form`
passes the real `display_for_value(value, empty)` text through unchanged on the
fallback arm — checked against that repo callee itself, including the join-arm
sequence roots and the falsy stored values (the two A-references). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited deep-model callees — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-model-vs-
callee soundness (G-AX) and refinement fidelity (this document, G-EQ).
