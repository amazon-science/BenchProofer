# refinement.md — django__django-11099

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`validateName` `do` block and the deep `allowedAll`/`validName` models,
parametric in the free per-code-point class `isAllowed`) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — none here), or **I** (identical concrete op). The R/I legs are
mechanically refuted by **G-CONF**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE): it changes the validator
regex `r'^[\w.@+-]+$'` → `r'^[\w.@+-]+\Z'` in both `ASCIIUsernameValidator` and
`UnicodeUsernameValidator`.

## A. The acceptance decision — `[Unicode|ASCII]UsernameValidator`

Gold hunk (twice, ASCII and Unicode):
```
-    regex = r'^[\w.@+-]+$'
+    regex = r'^[\w.@+-]+\Z'
```

The whole regex is the acceptance predicate of `RegexValidator.__call__`: the
candidate is accepted (no `ValidationError`) iff `re.search(regex, value)` matches.

| # | Solution.lean impl op (`validateName`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `s : List Char` | the `value: str` argument of `RegexValidator.__call__` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | parameter `isAllowed : Char → Bool` (free input) | the character class `[\w.@+-]` under the validator's regex flags | R | the class membership is an UNCHANGED building block: the gold edit never touches which single code points are in the class. It is a spec/impl **parameter** — the `ensures` holds for every `isAllowed` — instantiated per validator by mapping.md §2 (ASCII word chars vs Unicode word chars, plus `. @ + -`). Being universally quantified, nothing about it is asserted (in particular nothing about the Unicode `\w` boundary), so it is not an axiom; the instantiation leg is R, differential-tested by G-CONF. |
| A3 | `allowedAll isAllowed s` via the backward `while` fold | the `+` quantifier: every code point matches the class | I | the verified loop computes the conjunction of `isAllowed` over all code points; `allowedAll` (front-recursive) and the loop ARE the quantification. |
| A4 | `!s.isEmpty` (non-empty conjunct) | the `+` (one-or-more) quantifier requires at least one code point | I | empty input is rejected by `+`; modeled by `!s.isEmpty`. |
| A5 | `validName isAllowed s = !s.isEmpty && allowedAll isAllowed s` (NO end-of-input tolerance) | the `^...\Z` anchoring: `\Z` matches only the true end of string, so a trailing line terminator is NOT consumed and the name is rejected | I | the post-patch anchor admits no stray end-of-input code point: the quantification runs through the very LAST code point, none is dropped or exempted. Since no faithful class instantiation contains U+000A, a name ending in `'\n'` makes `allowedAll` false → rejected. This is the `$`→`\Z` fix. |

No A (axiom) steps; no kind-3 (changed-inexpressible) steps. The operation that
genuinely changed — the end anchor — is modeled **deeply**: the absence of
trailing-code-point tolerance is the universal `allowedAll` running through the
final code point. The operation that did NOT change — the per-code-point class —
is a free parameter, so the spec cannot be satisfied by any impl that hardcodes
a narrower or wider class (it must be correct for EVERY `isAllowed`), and it
cannot misstate the real class either (it says nothing about it). There is no
axiom about the regex engine.

## B. How the prepatch captures the `$`-vs-`\Z` bug (G-DIFF)

`Solution_prepatch.lean` keeps the spec **byte-identical** (`ensures out =
validName isAllowed s`) but its skeleton reproduces the pre-patch `$` semantics:
Python's `$` matches just before a single trailing newline, so the engine
effectively checks the candidate AFTER dropping one optional trailing line
terminator. The skeleton computes `core := if s.getLast? = some '\n' then
s.dropLast else s` and returns `!core.isEmpty && allowedAll isAllowed core`.

Take any `isAllowed` admitting `'a'` but not `'\n'` (every faithful
instantiation qualifies) and `s = "a\n"`: the prepatch returns `true` (after
stripping the `\n`, the core is all-allowed and non-empty), but
`validName isAllowed s = false` (the raw `s` contains the out-of-class `'\n'`).
So the exit-leg goal cannot close — the prepatch FAILS exactly on the
discriminating clause. (The loop-body leg still closes via the shared drop-step
lemma; the failure is the genuine spec divergence, not a proof typo.)

## C. verify(Solution) ⇒ resolved

`validateName` verifies only if `out = validName isAllowed s =
(!s.isEmpty && allowedAll isAllowed s)` for EVERY `isAllowed` (A2–A5): the impl
must consult the given class on every code point through the last, so it can
neither tolerate a trailing terminator (the fixed bug) nor substitute its own
class (which would break some instantiation). By R (`str ↔ List Char`,
`isAllowed ↦` the real per-validator class) the verified decision equals the
patched validator's accept/reject: the F2P cases `'trailingnewline\n'` (ASCII)
and `'trailingnewline
'` (Unicode) are rejected because no faithful class
contains `'\n'`, so `allowedAll` is false; the previously-passing valid names
(`'glenn'`, `'GLEnN'`, `'jean-marc'`, and the Unicode ones like `'René'`,
`'أحمد'`) remain accepted under the per-mode instantiation. G-CONF
differential-tests the R/I shadow — `validName` instantiated at each
validator's real class — against the patched validator on ≥10⁵ fuzzed inputs
including trailing-newline cases. The prepatch fails on the trailing-newline
clause (G-DIFF). The single trust point is the type bijection plus the class
instantiation (mapping.md §2); there are no axioms (G-AX is skipped).
