# refinement.md — django__django-13512

Maps every operation in `implementation_jsonEncodeString` to its `patch.diff`
counterpart. Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** op left as the real repo callee in G-CONF (not
axiomatized), **I** identical concrete op.

## Patch (the behavioral delta)
Two call sites are changed identically:
```python
# django/forms/fields.py  JSONField.prepare_value
-        return json.dumps(value, cls=self.encoder)
+        return json.dumps(value, ensure_ascii=False, cls=self.encoder)
# django/contrib/admin/utils.py  display_for_field (JSONField branch)
-            return field.get_prep_value(value)        # == json.dumps(value, cls=field.encoder)
+            return json.dumps(value, ensure_ascii=False, cls=field.encoder)
```
In both sites the JSON serialization of `value` flips from the default
`ensure_ascii=True` to `ensure_ascii=False`. The two sites encode the SAME
behavioral change (the second also inlines `get_prep_value`, which is itself
`json.dumps(value, cls=self.encoder)` — so post-patch both are
`json.dumps(value, ensure_ascii=False, cls=encoder)`).

## Modeling decision
`ensure_ascii` affects exactly ONE thing in `json.dumps`: how each character of a
serialized **string leaf** is rendered. With `ensure_ascii=True` every code point
≥ U+0080 is expanded to a `\uXXXX` escape (surrogate pair for astral characters);
with `ensure_ascii=False` those code points are emitted literally. The structure
of the JSON (object/array/number/bool/null layout, key quoting, separators `", "`
and `": "`) and the escaping of `"`, `\`, and the control characters < U+0020 are
**identical** under either flag — only the non-ASCII-character rendering differs.

The modeled object is therefore the JSON serializer's **string-leaf renderer**:
`jsonEncodeString : (s : List Char) → List Char`, the function that turns a text
value into its quoted JSON string literal. This is the smallest carrier on which
the fix is observable, and the whole `json.dumps` output is built from it by an
unchanged, flag-independent structural walk (the composers and key/number/bool
serializers are unchanged callees, not modeled). `problem_spec_jsonEncodeString`
pins the full post-patch rendering: `'"' :: escapeBody s ++ ['"']`, where
`escapeChar` emits `"`→`\"`, `\`→`\\`, the five short control escapes, `\u00XX`
for the remaining sub-U+0020 controls, and **every other character (printable
ASCII AND every non-ASCII character) literally**. The non-ASCII-literal clause is
the fixed behavior.

`escapeChar` is spelled out as a concrete `def` (deep model), so there is no
axiom: the per-character escape table is public (it is the JSON string grammar),
and the only flag-sensitive case — "char ≥ U+0080 emitted literally" — is exactly
the `else [c]` branch the spec fixes.

## Operation correspondence
| # | Lean op (`implementation_jsonEncodeString`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `return ('"' :: acc) ++ ['"']` (delimiters) | the surrounding `"`…`"` of a JSON string literal emitted by `json.dumps` (flag-independent) | I | identical under both flags. |
| 2 | `for c in s do acc := acc ++ escapeChar c` (per-char escape walk) | `json.dumps`' per-character string-encoding loop | R + A-reference | the loop scans EVERY input character and renders it via the escape table; `escapeChar` is the unchanged-grammar escape function bound to the REAL `json.dumps(c-string)` rendering in G-CONF. |
| 3 | `escapeChar`'s `else [c]` branch covering code points ≥ U+0080 | `ensure_ascii=False` ⇒ non-ASCII characters emitted literally (was `\uXXXX`) | R | THE behavioral fix: post-patch a non-ASCII char renders as itself; the prepatch impl renders it as `\uXXXX`. |

The behavior-changing op is #3 (folded into the `escapeChar` table consumed by
the loop #2). The prepatch impl uses an `escapeBuggy` table whose `≥ U+0080`
branch produces `\uXXXX` (the pre-patch `ensure_ascii=True` behavior), so on input
`中` it yields `"中"` while the spec forces `"中"` — the exact discrimination
the F2P tests (`{'a':'你好 世界'}`, `'你好，世界'`, `{'a':'😀🐱'}`, `["你好，世界","jaźń"]`) demand.

## R/I legs ⇒ G-CONF
Op 1 (delimiters, I) and op 2/3 (the escape walk + the non-ASCII-literal branch,
R) are the R content. G-CONF builds the shadow (`'"' + escapeBody(s) + '"'` with
`escapeChar` bound to the REAL `json.dumps(s_singleton_string, ensure_ascii=False)`
string-leaf rendering) and differential-tests it against the real post-patch
serializer over ≥10⁵ fuzzed strings (ASCII, control chars, Latin-1, CJK, emoji /
astral, quotes, backslashes). `conf_skip = false`: the impl region has genuine
R/I content (the full string-literal rendering is the fixed behavior).

## No A-consumed row
The proof consumes no axiom: `escapeChar`/`escapeBody` are concrete `def`s, fully
spelled out, so the proof reasons about them directly (`implementation` ↔ `spec`
is a `forIn`/`foldl` ↔ front-recursive-fold equality, PROOF_PLAYBOOK Route B).
`meta.json axioms = []`. There is no `opaque`/`axiom` declaration in
`Solution.lean`; `axiom_check.py` is a skip stub. The `json.dumps` string-leaf
rendering is recorded as an A-reference solely to document the G-CONF binding to
the real serializer.

## F2P / issue alignment
- `field.prepare_value('你好，世界') == '"你好，世界"'`, `prepare_value({'a':'😀🐱'}) ==
  '{"a": "😀🐱"}'`, `prepare_value(["你好，世界","jaźń"])`, and admin
  `display_for_field({'a':'你好 世界'}, JSONField) == '{"a": "你好 世界"}'` are the new
  F2P cases. Each contains a non-ASCII string leaf; post-patch (and the spec) it
  renders literally, while the prepatch impl renders `\uXXXX` — the discriminator.
- The pre-existing ASCII cases (`{'a':'b'}`, `'foo'`, `null`, `[…]`) are unchanged
  under either flag, so the spec and both impls agree on them (no regression).
- `patch.diff` is the gold patch verbatim; it makes the harness `resolved`.
