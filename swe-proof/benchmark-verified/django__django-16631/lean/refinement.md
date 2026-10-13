# refinement.md — operation correspondence (django__django-16631)

Maps every op in `implementation_validateToken` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python is the session-verification block of `get_user` plus the new
fallback-hash producer. We model the three-way DECISION over three opaque token
values (stored token, current-secret token, fallback-secret tokens); the per-
decision session/user EFFECTS are refinement glue held fixed by this document
(mapping.md "Effect glue"), not part of the modeled function:

- `.rejected` ⇒ `request.session.flush(); user = None`
- `.acceptedCurrent` ⇒ no state change (block falls through)
- `.acceptedAlternate` ⇒ user kept; the gold fallback-acceptance body runs
  verbatim (`request.session.cycle_key()`;
  `request.session[HASH_SESSION_KEY] = session_auth_hash`)

A refined patch is FAITHFUL only if each decision value is wired to exactly this
glue. An impl that computes the same decision function therefore refines to the
gold patch behavior; an impl that misclassifies any input refines to a patch
that takes the wrong glue path there.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `storedToken : List Char`, `[]` = absent | `session_hash = request.session.get(HASH_SESSION_KEY)` (hex str or falsy) | R | str/None ↔ `List Char` with `[]` modeling falsy/absent (mapping.md) |
| 2 | `currentToken : List Char` | `session_auth_hash = user.get_session_auth_hash()` | R | hex digest str ↔ `List Char` |
| 3 | `alternateTokens : List (List Char)` | `[h for h in user.get_session_auth_fallback_hash()]` | R | list of digests ↔ `List (List Char)`, order preserved |
| 4 | `if storedToken = [] then tokenVerified := false else tokenVerified := (storedToken == currentToken)` | `if not session_hash: session_hash_verified = False / else: ... = constant_time_compare(session_hash, session_auth_hash)` | I | identical branch; `constant_time_compare` ⟺ value equality (list `==`). This is the patched restructuring of the old short-circuit `session_hash and constant_time_compare(...)`. |
| 5 | `for t in alternateTokens do if t == storedToken then alternateMatched := true` | `any(constant_time_compare(session_hash, fallback_auth_hash) for fallback_auth_hash in user.get_session_auth_fallback_hash())` | I | `any(... ct_compare ...)` ⟺ `∃ alternate. alternate == storedToken`; the `for`+`mut` loop is the skeleton of the generator-fed `any` |
| 6 | `if storedToken != [] && alternateMatched then return .acceptedAlternate` | `if session_hash and any(...):` — the fallback-acceptance branch is selected (its body is glue, see header) | I | the **changed op**: on a fallback match the decision is `.acceptedAlternate`; the `session_hash` guard re-checks the stored token is present |
| 7 | `else return .rejected` (mismatch, no alternate) | `else: request.session.flush(); user = None` — the reject branch is selected | I | reject decision ⟺ the flush-and-drop glue path |
| 8 | `return .acceptedCurrent` (verified path) | falls through `if not session_hash_verified:` — `user` and session untouched | I | verified against the current token ⟺ the no-op glue path |

No A-consumed rows: the proof discharges the decision directly; no UNCHANGED
callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: the only callee in the modeled decision
(`constant_time_compare`) is reproduced concretely as list equality (I), not
abstracted behind a model needing G-AX validation. The token-producing callees
(`get_session_auth_hash` / `get_session_auth_fallback_hash`) supply the model's
*inputs* and are not operations inside the modeled function. No
changed-inexpressible op.

## Discriminating clause (G-DIFF)
Rows 5–6: when `storedToken ≠ []`, `storedToken ≠ currentToken`, and some
`t ∈ alternateTokens` equals `storedToken`, the post-patch decision is
`.acceptedAlternate`. The prepatch impl never consults the alternates: on any
mismatch it returns `.rejected`. Hence on such an input the frozen
`problem_spec_validateToken` clause 3 (`… → result = .acceptedAlternate`)
is violated by the prepatch impl, so prepatch `correct_validateToken` cannot
close — exactly the G-DIFF signal. This is the input class the F2P test
`test_get_user_fallback_secret` exercises (login under the old secret, rotate to
a new `SECRET_KEY` with the old one in `SECRET_KEY_FALLBACKS`, assert the user is
still returned).

## Why decision-level modeling is sound here (verify ⇒ correct)
The four spec clauses partition the input space and pin the decision to a single
value on each cell, so the spec is a total function: every same-spec impl whose
`correct_` closes computes the SAME decision function as the gold. Faithful
refinement (glue table above) then attaches each decision to the gold patch's
per-branch effects — in particular `.acceptedAlternate` carries the gold
fallback-acceptance body (key cycling + stored-hash refresh), so the refined
patch of ANY verifying impl is behaviorally the gold patch and resolves. An impl
cannot verify yet route a decision to different glue: the glue is fixed by this
refinement document, not chosen by the impl.
