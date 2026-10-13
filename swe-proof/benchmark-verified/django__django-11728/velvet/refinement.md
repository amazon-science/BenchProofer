# refinement.md — django__django-11728

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`scanGroupEnd` `do` block plus the deep `scanLen`/`nextBal` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep model
validated == the real callee by G-AX), or **I** (identical concrete op). EVERY
step is R, A, or I; there is no kind-3 (changed-but-inexpressible) op.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs and this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change — the inner bracket-balancing scan (shared by both functions)

The gold patch makes the SAME edit twice: in `replace_named_groups`
(`utils.py:169-182`) and in `replace_unnamed_groups` (`utils.py:203-216`). In
both, the loop that walks the characters after a group's opening token is fixed
by (1) moving the `unmatched_open_brackets == 0` test from the TOP of the loop to
the BOTTOM (after the current character has been folded into the depth and
`prev_char` updated), and (2) advancing the recorded end index by one
(`end + idx` → `end + idx + 1`; `start + 1 + idx` → `start + 2 + idx`) to include
the balancing bracket.

Gold hunk (named; unnamed is identical mutatis mutandis):
```
-        for idx, val in enumerate(pattern[end:]):
-            if unmatched_open_brackets == 0:
-                group_pattern_and_name.append((pattern[start:end + idx], group_name))
-                break
-            if val == '(' and prev_char != '\\': ...
-            elif val == ')' and prev_char != '\\': ...
-            prev_char = val
+        for idx, val in enumerate(pattern[end:]):
+            if val == '(' and prev_char != '\\': ...
+            elif val == ')' and prev_char != '\\': ...
+            prev_char = val
+            if unmatched_open_brackets == 0:
+                group_pattern_and_name.append((pattern[start:end + idx + 1], group_name))
+                break
```

| # | Solution.lean impl op (`scanGroupEnd`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `rest : List Char` | `pattern[end:]` (named) / `pattern[start+1:]` (unnamed), the iterated suffix | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `bal := 1`, `prev := none` initial state | `unmatched_open_brackets, prev_char = 1, None` | I | identical initialization. |
| A3 | `bal' := nextBal prev bal c` each step | the `if val=='(' … elif val==')' …` depth update + `prev_char = val` | A-reference (`nextBal`) + I | the per-char depth transition is modeled deeply by `nextBal`; G-AX validates `nextBal == the real update` over the alphabet (mapping.md §3.2). The `prev` threading (`prev := some c`) is the **I** transliteration of `prev_char = val`. |
| A4 | balance test `if bal' = 0 then res := some (i+1); stopped := true` evaluated AFTER folding `c` | the patched `if unmatched_open_brackets == 0:` placed AFTER the depth update + `prev_char = val`, recording `end + idx + 1` | I | the control-flow fix itself: test-at-bottom, record one-past the balancing bracket. `some (i+1)` ↔ slice end `base + (idx+1)` (mapping.md §3.1). |
| A5 | result `scanLen none 1 rest` (the `ensures`) | the consumed length the patched loop's `break` index encodes | A-reference (`scanLen`) | the whole scan's input→length relation is modeled deeply by `scanLen`; G-AX validates `scanLen == the real patched loop's reported offset` end-to-end (mapping.md §3.1). No consumed axiom about the function under change. |
| A6 | `none` when the loop exhausts `rest` without `bal'=0` | the loop finishing with no `break` ⇒ no `append` for this group ⇒ the group is left untouched | R | `none` ↔ "no slice recorded"; G-CONF's host transliteration leaves the group text unmodified in that case, exactly as the real function does. |

## B. Discriminating content of the change

The defect: with the test at the TOP of the loop and the end index `end + idx`,
a group whose balancing `)` is the **final** character of the pattern is never
recorded — the depth reaches zero only on an iteration that never runs (the
string ends), so `replace_named_groups`/`replace_unnamed_groups` leaves that
trailing group unsubstituted (the issue's `r'…/relationships/(?P<related_field>\w+)'`
example).

This lives in `scanGroupEnd`'s contract as: when `rest`'s balancing bracket is
its last character, `scanLen none 1 rest = some rest.length` (a real `some`), not
`none`. `Solution_prepatch.lean` reproduces the buggy top-of-loop / `some i`
skeleton and **fails** the `out = scanLen none 1 rest` postcondition precisely on
that clause (G-DIFF): for a final balancing bracket it returns `none`/short while
the frozen spec demands `some rest.length`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely changed — the
inner bracket-balancing scan — is modeled **deeply** (`scanLen`/`nextBal` + the
verified loop, steps A3/A5), not hidden behind an axiom about the function under
change. There is **no consumed axiom**: `nextBal` and `scanLen` are A-references
(G-AX-validated against the real patched code), and the unchanged host pieces
(match producer + textual substitution) are transliterated/bridged by G-CONF, not
axiomatized.

## D. verify(Solution) ⇒ resolved

`scanGroupEnd` verifies only if its output equals `scanLen none 1 rest` for every
suffix — i.e. it folds the depth with `nextBal`, tests at the bottom, and records
one-past the balancing bracket (A3/A4/A5), returning `none` exactly when the
brackets never balance (A6). By R (`str ↔ List Char`, the slice-index
reconciliation of mapping.md §3.1) this is exactly the patched inner scan. By
G-AX the deep model equals the real patched loop (A-reference) and `nextBal`
equals the real depth update. By G-CONF, embedding that R/I scan shadow inside
the two otherwise-unchanged host functions reproduces `patch.diff`'s
`replace_named_groups`/`replace_unnamed_groups` output on ≥10⁵ inputs. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and validated callees — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: the A-reference soundness (G-AX)
and refinement fidelity (this doc, G-EQ + G-CONF).
