# refinement.md — django__django-14539

Operation correspondence between `implementation_peelTrailingPunct`
(`Solution.lean`, impl region) and `patch.diff` (the patched trailing-punctuation
block of `trim_punctuation` inside `django/utils/html.py`). Every step tagged
**R** (type refinement), **A-consumed** (proof uses the axiom's property),
**A-reference** (deep model, validated == real callee by G-CONF), or **I**
(identical concrete op).

## Type bijection (R)

| Python | Lean | tag |
|---|---|---|
| `middle : str` (per-code-point) | `token : List Char` | R |
| `trail : str` | `tailPunct : List Char` | R |
| `trimmed_something : bool` | `Bool` (3rd result component) | R |
| `(middle, trail)` mutated state | `Id.run do` with `let mut token / tailPunct / trimmed` | R |
| return `lead, middle, trail` (only middle/trail touched here) | `(token, tailPunct, trimmed)` tuple | R |

`lead` is not touched by the edited block, so it is not modeled (frame: the patch
hunk only rewrites the `trail`/`middle` assignments; `lead` flows through
unchanged and is outside the modeled operation).

## Operation table

| # | patch.diff op (post-patch) | impl op | tag |
|---|---|---|---|
| 1 | `middle_unescaped = html.unescape(middle)` | `let decoded := decode token` | A-reference |
| 2 | `stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)` | `let stripped := rstripPunct decoded` | I (R on str↔List Char) |
| 3 | `if middle_unescaped != stripped:` | `if decoded ≠ stripped then` | I |
| 4 | `punctuation_count = len(middle_unescaped) - len(stripped)` | `let punctCount := decoded.length - stripped.length` | I |
| 5 | `trail = middle[-punctuation_count:] + trail` | `tailPunct := takeRightN token punctCount ++ tailPunct` | I |
| 6 | `middle = middle[:-punctuation_count]` | `token := dropRightN token punctCount` | I |
| 7 | `trimmed_something = True` | `trimmed := true` | I |

`takeRightN cs n = cs.drop (cs.length - n)` ≡ Python `cs[-n:]` for `1 ≤ n ≤ len`;
`dropRightN cs n = cs.take (cs.length - n)` ≡ Python `cs[:-n]` for `1 ≤ n ≤ len`.
Inside the `if`, `punctCount ≥ 1` (decoded ≠ stripped ⟹ a punctuation suffix was
dropped) and `punctCount ≤ decoded.length ≤ token.length`, so the slice analogy
is exact. (The bijection is checked over both branches anyway by G-CONF.)

## A-reference: `decode` ↔ `html.unescape`

Op #1 calls the unchanged stdlib HTML entity decoder. It is modeled as
`opaque decode : List Char → List Char` and consumed by NO `_prop` axiom — the
proof of the conservation clause `result.1 ++ result.2.1 = token ++ tailPunct`
holds for an arbitrary `decode` (it is `List.take_append_drop` on `token`). Hence
`decode` is an A-reference, not an A-consumed axiom. Its concrete behaviour is
validated against the real `html.unescape` by `conformance_check.py` (G-CONF):
both the shadow and the verbatim patched reference call `html.unescape` directly.

## No changed-inexpressible op

Every op of the changed block is expressed concretely (slicing arithmetic over
`List Char`). The single unchanged callee is an A-reference. Nothing is
axiomatized that the patch changes; there is no dead axiom.

## The fix (what discriminates Solution from Solution_prepatch)

Pre-patch op #5 was `trail = middle[len(stripped):] + trail` — slicing the
ORIGINAL token at an index measured on the DECODED view. When the token carries
HTML-escaped sequences (`len(token) > len(decoded)`), that index starts too far
left and captures extra characters into `trail`, duplicating them. The post-patch
slices a count (`punctuation_count`) off the END of the original token, so exactly
the peeled characters move. The discriminating spec clause is the conservation
clause #4 of `problem_spec_peelTrailingPunct`
(`result.1 ++ result.2.1 = token ++ tailPunct`), which the prepatch impl violates
on any entity-bearing token (e.g. the issue's `google.com/?q=1&lt!`).
