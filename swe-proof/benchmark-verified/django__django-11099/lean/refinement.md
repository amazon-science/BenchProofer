# refinement.md — django__django-11099

Maps every operation in the two `implementation_*` skeletons to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

The patch changes one token in each of two validator classes:
```python
-    regex = r'^[\w.@+-]+$'
+    regex = r'^[\w.@+-]+\Z'
```
applied to `ASCIIUsernameValidator` and `UnicodeUsernameValidator`. Validation is
`RegexValidator.__call__`: it raises `ValidationError` iff
`self.regex.search(str(value)) is None`. So "accept" ⇔ the compiled regex matches.

The two modeled functions are structurally identical, differing only in the
per-character allowed-set callee (`isAllowedAscii` vs `isAllowedUnicode`, the
`re.ASCII` vs flags-`0` flavor of `[\w.@+-]`). The table below is written for the
ASCII function; every row applies verbatim to the Unicode function with
`isAllowedUnicode` substituted.

## Modeled function: `validateAscii` (apply `ASCIIUsernameValidator`)

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `username : List Char` (input carrier) | `str(value)` passed to `self.regex.search` | **R** | per-code-point view of the string; `str s` ↔ `s.toList`. See mapping.md. |
| 2 | `if username.isEmpty then return false` | the regex requires `+` (≥1 char): the empty string never matches `^[\w.@+-]+\Z` ⇒ `search` is `None` ⇒ reject | **R** | the post-patch regex's `+` quantifier ⇒ non-empty is necessary; the early `return false` models the empty-string rejection. (Holds pre- and post-patch alike; unchanged behavior.) |
| 3 | `for c in username do if !isAllowedAscii c then ok := false` | the post-patch regex `^[\w.@+-]+\Z` matches iff EVERY character of the whole string is in `[\w.@+-]` | **I** (deep model of the changed op) | **the fixed operation.** `\Z` anchors at the true end of string, so the match requires the class `[\w.@+-]` to cover characters `0 .. len-1` inclusive — the FINAL character is no longer exempt. The loop conjoins `isAllowedAscii` over the FULL list (no last-char special case), i.e. `username.all isAllowedAscii`. This is the heart of the fix. |
| 4 | `isAllowedAscii c` | "the character `c` is matched by the class `[\w.@+-]` under `re.ASCII`" | **A-reference** | the per-character class membership is UNCHANGED by the patch; modeled as an opaque callee and validated `== ` the real class test by G-AX. The Lean proof does NOT consume any property of it (the loop computes `all isAllowedAscii` for whatever the predicate is), so it is an A-reference, not a consumed axiom. |
| 5 | `return ok` | `search(...) is not None` ⇒ accept (no `ValidationError`) | **R** | the accumulated conjunction is the accept/reject boolean; `true` ↔ accept ↔ no raise. |

The Unicode function: rows 1–5 identical with `isAllowedUnicode` (the flags-`0`
flavor of `[\w.@+-]`).

## A-tagging summary

- `isAllowedAscii`, `isAllowedUnicode` — **A-reference** (deep-model references):
  unchanged callees, opaque signatures, validated against the real class test by
  G-AX. Neither `correct_*` proof consumes a `_prop` axiom about them: the loop
  equals `username.all isAllowed*` purely structurally (the proof agent's Route-B
  loop≡fold induction), independent of the predicate's truth table. So there is
  **no A-consumed axiom**, and no dead `axiom` is shipped.
- The impl region is NOT all-A-tagged (rows 1–3,5 are R/I): `conf_skip = false`,
  and `conformance_check.py` differential-tests the R/I shadow against the real
  patched regex over ≥1e5 fuzzed inputs (per validator/flag).

## Soundness check (verify ⟹ correct)

- `problem_spec_validate*` pins the result EXACTLY as
  `!username.isEmpty && username.all isAllowed*` — the result Bool is fully
  determined by the input (directive 5 frame: nothing about the result is left
  free). It is grounded in the input carrier via `List.all` over the whole list
  (directive 8: no ungrounded oracle — the boolean must be PRODUCED by scanning
  every character, including the last).
- A wrong impl that exempts the final character (the pre-fix `$` behavior) cannot
  satisfy this spec: on `username = allowedchars ++ ['\n']`, the spec demands
  `false` (since `isAllowed* '\n' = false`, so `all = false`), but the pre-fix
  impl yields `true`. This is the discriminating clause.
- `Solution_prepatch.lean` reproduces the pre-fix ASCII behavior (drop a single
  trailing `'\n'` before the whole-sequence check); `Solution_prepatch_2.lean`
  does the same for the Unicode behavior. Each is byte-identical in spec to
  `Solution.lean` and must FAIL G-VERIFY on the discriminating input — its carried
  gold proof cannot close (G-DIFF / G-PANEL). Two prepatch variants because the
  two validators are INDEPENDENTLY-observable fixed behaviors (separate F2P tests
  `test_ascii_validator`, `test_unicode_validator`).
- These discriminating cases are exactly the FAIL_TO_PASS assertions added by the
  test patch: `'trailingnewline\n'` is added to ASCII `invalid_usernames` and
  `'trailingnewline
'` to Unicode `invalid_usernames`.
- patch.diff == gold verbatim.
