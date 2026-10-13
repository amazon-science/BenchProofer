# mapping.md — django__django-12262

Cold spec (`spec_provenance: "cold"`): derived only from `problem_statement`, the
gold `patch`, and the repo source at `base_commit`
(`69331bb851c34f05bc77e9fc24020fe6908b9cd5`, django/django, version 3.1).

## 1. Symbol binding

| model symbol (`Solution.lean`) | repo symbol @ base_commit | file:line |
|---|---|---|
| `bindTagArguments` | `django.template.library.parse_bits` (the per-bit argument-binding loop + the final missing-argument check) | `django/template/library.py:237` (def); per-bit loop `:262-296`; final check `:297-306` |

The function `parse_bits` parses the argument "bits" of a custom template tag
(`simple_tag` / `inclusion_tag`), classifying each bit as positional or keyword
and raising `TemplateSyntaxError` on a malformed argument list. The single
modeled method `bindTagArguments` reproduces, abstractly, the OUTCOME of that
parse: either the first error raised (with its kind and the offending argument
name) or success.

## 2. The Lean ↔ Python type bijection (used by G-CONF)

| Python (parse_bits) | Lean model | note |
|---|---|---|
| an argument name (a `str`) | `Name := Nat` | names are opaque identifiers; only equality / membership is observed |
| a `bit` already classified by the *unchanged* callee `token_kwargs([bit], parser)` | `Bit` : `keyword (p : Name)` \| `positional` | `token_kwargs` returning a 1-entry dict ⇒ `keyword p`; returning empty ⇒ `positional`. `token_kwargs` and `parser.compile_filter` are UNCHANGED by the patch and produce values irrelevant to the error/validity outcome, so they are folded into the bit classification (a free input). The kwarg's *value* is never read by any decision, so it is dropped. |
| `params` (the positional parameter names, after the unchanged `takes_context` stripping) | `positionalParams : List Name` | the `takes_context` prefix handling at `:245-253` is UNCHANGED and orthogonal to this fix; its (possibly stripped) result is taken as the input `positionalParams`. mapping note §4. |
| `kwonly` (all keyword-only parameter names) | `keywordOnlyParams : List Name` | the constant full list of keyword-only names — the value the fix tests against |
| `kwonly_defaults` (keyword-only names that have a default) | `keywordOnlyDefaults : List Name` | used only to build the initial pending set |
| `unhandled_kwargs` (mutating: kwonly names *without* a default, minus those already supplied) | `PState.pendingKeywordOnly : List Name` | initialized `kwonly` filtered to names not in `kwonly_defaults`; entries removed as supplied — the value the *buggy* line tested against |
| `unhandled_params` (mutating list of `params`) | `PState.pendingPositional : List Name` | |
| `kwargs` dict keys (names already recorded) | `PState.recorded : List Name` | only membership is observed (`param in kwargs`) |
| `varkw is None` | `!acceptsExtraKeywords` | `varkw is not None` ⇔ tag accepts arbitrary extra keyword args ⇔ `acceptsExtraKeywords = true` |
| `varargs is None` | `!acceptsExtraPositional` | likewise for arbitrary extra positional args |
| `defaults is not None` | `hasDefaults : Bool` | |
| `len(defaults)` | `numDefaults : Nat` | when `hasDefaults`, `numDefaults ≥ 1` (a non-None `defaults` is a non-empty tuple) |
| `raise TemplateSyntaxError("…unexpected keyword argument '%s'", name, param)` | `Err.unexpectedKeyword p` | |
| `raise …("…multiple values for keyword argument '%s'")` | `Err.duplicateKeyword p` | |
| `raise …("…positional argument(s) after some keyword argument(s)")` | `Err.positionalAfterKeyword` | |
| `raise …("…too many positional arguments")` | `Err.tooManyPositional` | |
| `raise …("did not receive value(s) for the argument(s): …")` | `Err.missingArguments names` | `names` = `unhandled_params ++ unhandled_kwargs` after the `defaults` truncation |
| function returns `(args, kwargs)` normally | `none` (no error) | the modeled observable is the error outcome; `args`/`kwargs` contents are produced by unchanged callees and are not part of the validity decision |

`PState` = `{ recorded, pendingPositional, pendingKeywordOnly, error }`.
The whole parse outcome is `parseBits … = finalize (bits.foldl stepBit initState) …`.

## 3. Callee provenance & flag dependencies

No callee contract is *assumed*: there are **no axioms** and **no deep-model
references**. The two callees the loop invokes —
`token_kwargs([bit], parser)` and `parser.compile_filter(bit)` — are UNCHANGED by
the patch and produce only (a) the bit classification and (b) the compiled
positional value, neither of which the error decision under spec reads beyond the
kwarg/positional classification. They are therefore abstracted into the free
input `bits : List Bit` (each bit pre-classified). G-AX is `skip` (no axioms).

Flag dependencies recorded for G-CONF fuzzing: the outcome depends on
`acceptsExtraKeywords` (varkw), `acceptsExtraPositional` (varargs), `hasDefaults`
+ `numDefaults` (defaults), and the three name lists; G-CONF fuzzes all of them.

## 4. The `takes_context` prefix (excluded, with justification)

`parse_bits` begins (`:245-253`) by optionally stripping a leading `'context'`
positional parameter (or raising if `takes_context` is set without it). This
block is UNCHANGED by the patch and is independent of the keyword-only fix: it
only decides the *value* of `params` passed into the loop. We take the
post-stripping positional names as the input `positionalParams`, exactly as the
11820 bundle scoped to the inner walk of `_check_ordering`. The excluded block
raises a distinct, unrelated error kind that the fix never touches.

## 5. G-CONF fuzz seed

Pinned seed: **12262** (see `conformance_check.py`, `meta.json fuzz_seed`).
