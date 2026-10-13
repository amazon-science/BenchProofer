# refinement.md — django__django-15098

Operation correspondence between `implementation_langCodeFromPath`
(Solution.lean) and the gold `patch.diff`. Tags: **R** (type refinement),
**A-consumed** (proof uses an axiom's property), **A-reference** (deep model
validated == real callee by G-AX), **I** (identical concrete op).

## Modeled function: `get_language_from_path`

Post-patch Python:
```python
regex_match = language_code_prefix_re.match(path)   # ^/(\w+([@-]\w+){0,2})(/|$)
if not regex_match:
    return None
lang_code = regex_match[1]
try:
    return get_supported_language_variant(lang_code, strict=strict)
except LookupError:
    return None
```
The patch changes only the matcher `language_code_prefix_re` (the `{0,2}` quantifier).

| # | `implementation_langCodeFromPath` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | input `path : List Char` | `path : str` | R | Python `str` (per code point) ↔ Lean `List Char` (mapping.md). |
| 2 | `if allAscii path then (langPrefix path …) else nonAsciiOutcome path` | `language_code_prefix_re.match(path)` + truthiness + `regex_match[1]` | R / A-reference | The CHANGED op (the regex with `{0,2}`) is modeled DEEPLY on the all-ASCII branch: `langPrefix` (= `langPrefixN 2`) reproduces group-1 of `^/(\w+([@-]\w+){0,2})(/|$)`, including the `$`-before-a-single-trailing-newline anchor semantics (`rrest = ['\n']` accepts). Not axiomatized. On paths with a non-ASCII code point (Python `\w` is Unicode-aware; Lean's char classes are ASCII — see mapping.md flag dep) the whole-routine outcome is the opaque `nonAsciiOutcome`, used identically on both sides of the spec equation, so no property of it is asserted or consumed. G-CONF mechanically confirms `langPrefix` == the real regex's group-1 (and `langPrefixN 1` == the pre-patch regex) over ≥10⁵ fuzzed paths drawn from the full ASCII plane. |
| 3 | `match … | none => return none` | `if not regex_match: return None` | I | no-match ⇒ `None`. Identical control flow. |
| 4 | `| some lc => return resolveVariant lc` | `try: return get_supported_language_variant(lang_code, strict) except LookupError: return None` | R / A-reference | `resolveVariant : List Char → Option (List Char)` is the UNCHANGED callee `get_supported_language_variant` with its `LookupError` outcome modeled as `none`. The impl invokes it identically to the real function (callee-by-signature); the spec relates the result to `resolveVariant` of the SAME candidate, so no `_prop` axiom is consumed. G-AX validates the signature/behavior correspondence (returns the candidate / a generic variant / nothing). |

The single changed op (#2, the matcher) is **modeled deeply** on the graded
(all-ASCII) branch, never axiomatized. There are **two opaque symbols**
(`resolveVariant`, `nonAsciiOutcome`), each used identically on both sides; the
proof consumes no `_prop` axiom about either (they appear on both sides of the
spec equation). Tags: **A-reference**.

## Prepatch (G-DIFF)

`Solution_prepatch.lean` is byte-identical outside the impl region; its impl uses
`langPrefixN 1` (the pre-patch single-trailing-subtag matcher
`^/(\w+([@-]\w+)?)(/|$)`) on the all-ASCII branch. On the new F2P inputs with
two trailing subtags (`/en-latn-us/`, `/en-Latn-US/`, `/de-ch-1901/`,
`/nan-hani-tw/`) — all ASCII — the pre-patch matcher returns `none` where the
spec (via `langPrefix = langPrefixN 2`) demands `resolveVariant` of the full
candidate — so `correct_langCodeFromPath` is unclosable against it. Confirmed
at construction (decidable discrimination examples elaborate).

## Out-of-scope gold-patch edits

None — the gold patch is a single one-line matcher change.
