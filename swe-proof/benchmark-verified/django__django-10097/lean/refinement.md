# refinement.md — django__django-10097

Maps every operation in `implementation_urlUserinfoValid` (Solution.lean impl
region) to its `patch.diff` counterpart (the post-patch inner regex group
`[^\s:@/]+(?::[^\s:@/]*)?`). Tags: **R** type refinement, **A-consumed** proof
uses this axiom, **A-reference** deep-model validated == real callee (G-AX), **I**
identical concrete op.

The whole fix is a regex-character-class change; there is no repo callee to
axiomatize. Every op is R or I over the `List Char` refinement of the Python
`str` segment. No A rows ⇒ no consumed axiom, no A-reference.

| # | Lean op (impl region) | patch.diff counterpart | tag |
|---|---|---|---|
| 1 | `s : List Char` | the credentials segment `str` matched before `@` | **R** — Python `str` ↔ `List Char`, per-code-point (mapping.md) |
| 2 | `if s.isEmpty then return false` | the `+` quantifier on the user part `[^\s:@/]+` requires ≥1 char ⇒ empty segment does not match | **R** — `str` non-empty ↔ `¬ s.isEmpty` |
| 3 | `if s.head? == some ':' then return false` | the user part `[^\s:@/]+` must consume ≥1 admissible (non-`:`) char before the optional `:` separator ⇒ a leading `:` cannot match | **R** — regex anchoring ↔ head test |
| 4 | `if !Nat.ble (s.count ':') 1 then return false` | only ONE `:` is permitted (the single optional `user:pass` separator; both `[^\s:@/]` classes exclude `:`) ⇒ ≥2 colons reject | **R** — regex "at most one colon" ↔ `count ':' ≤ 1` |
| 5 | `if !(s.all (fun c => isUserinfoChar c \|\| c == ':')) then return false` | every char is in `[^\s:@/]` except the single allowed separator `:` ⇒ any whitespace / `@` / `/` rejects | **R** — char-class membership ↔ `isUserinfoChar`; `isUserinfoChar` = `!isUserinfoWhitespace && ≠':' && ≠'@' && ≠'/'` = `[^\s:@/]`, with `isUserinfoWhitespace` the full 29-code-point Unicode `\s` class (mapping.md) |
| 6 | `return true` | the segment fully matches the inner group | **I** — accept |

Prepatch (Solution_prepatch.lean) models the OLD group `\S+(?::\S*)?` as
"non-empty and all-non-whitespace" (`\S` = the complement of the same
29-code-point `\s` class, delimiters included). Its `correct_` (gold `rfl` proof carried over) fails to typecheck
against the spec, which is exactly the G-DIFF signal that the spec sees the bug:
the pre-patch impl accepts `foo/bar@`, `foo@bar@`, `foo:bar:baz@` — the F2P
invalid URLs — whereas the spec (post-patch predicate) rejects them.

conf_skip = **false** (all rows are R/I; G-CONF differential-tests them).
