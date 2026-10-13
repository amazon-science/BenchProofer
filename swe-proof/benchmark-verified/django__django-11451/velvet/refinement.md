# refinement.md — django__django-11451

Operation-by-operation correspondence between `Solution.lean`'s `authGuard` impl
region and `patch.diff` (the gold patch adds an admissibility short-circuit to
`ModelBackend.authenticate`: `if username is None or password is None: return`).
Each step is tagged **R** (type refinement), **A** (axiomatized callee), or
**I** (identical concrete op). EVERY step is R, A, or I.

`patch.diff` is the gold patch **verbatim** (applies at base_commit, resolves —
G-RESOLVE).

## A. The admissibility short-circuit — `ModelBackend.authenticate`

Gold hunk (context + added lines):
```
     def authenticate(self, request, username=None, password=None, **kwargs):
         if username is None:
             username = kwargs.get(UserModel.USERNAME_FIELD)
+        if username is None or password is None:
+            return
         try:
             user = UserModel._default_manager.get_by_natural_key(username)
         except UserModel.DoesNotExist:
```

| # | Solution.lean impl op (`authGuard`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `let effective := effectiveName suppliedName recoveredName` | `if username is None: username = kwargs.get(UserModel.USERNAME_FIELD)` (`backends.py:40-41`, UNCHANGED context) | **I** | identical concrete op: the local identifier resolution — keep the directly-supplied identifier, else fall back to the one recovered from the extra kwargs. `username`/`kwargs.get(...)` ↔ `suppliedName`/`recoveredName : Option Name` (mapping.md §2); `is None` ↔ `Option.isNone`. |
| A2 | `if effective.isNone \|\| password.isNone then ...` | `if username is None or password is None:` (the added guard) | **I** | identical concrete op: the CHANGED op, modeled deeply as the conditional. Python `or` ↔ Lean `\|\|`; `username is None` (the post-fallback local) ↔ `effective.isNone`; `password is None` ↔ `password.isNone`. |
| A3 | `return { queried := false, principal := none }` (guard taken) | `return` (the added early return — yields `None`, runs NO query and NO hasher) | **I** | the early return performs neither the store lookup nor the credential-strength computation, and hands back nothing. `queried := false` ↔ "no `get_by_natural_key` query, no `set_password` hasher call" (the `assertNumQueries(0)` + `CountingMD5PasswordHasher.calls == 0` observable, mapping.md §2); `principal := none` ↔ implicit `return None`. |
| A4 | `return { queried := true, principal := backendOutcome }` (guard not taken) | falls through to `try: user = get_by_natural_key(...)` … `return user` / implicit `None` (`backends.py:42-49`, UNCHANGED) | **R** + free input | the proceed path runs the UNCHANGED downstream chain; `queried := true` ↔ "the lookup/hasher path was entered"; the principal it yields ↔ the free input `backendOutcome : Option Principal` (mapping.md §3). The chain is unchanged by the fix, so its result is taken as a given input, not re-derived or axiomatized. |

No A (axiom) steps; no A-reference deep models; no kind-3 (changed inexpressible)
steps. The single changed op (A2/A3) is the early-return guard, modeled deeply
and tagged **I**. The unchanged fallthrough (A4) carries the unchanged callee
chain's result as a free input (**R**).

## B. verify(Solution) ⇒ resolved; prepatch fails on the right clause

`authGuard` verifies only if `out = authDecision …`, i.e. both:
- when an effective identifier OR the secret is absent: `queried = false` AND
  `principal = none` (forced by A2/A3); and
- otherwise: `queried = true` AND `principal = backendOutcome` (A4).

By R (mapping.md §2) this is exactly: the patched `authenticate` issues NO
database query and runs NO password hasher when `username`-after-fallback or
`password` is `None`, returning `None`; otherwise it behaves as the unchanged
downstream chain dictates. The F2P test `test_authentication_without_credentials`
asserts precisely `assertNumQueries(0)` and `CountingMD5PasswordHasher.calls == 0`
for the three incomplete-credential cases (`{}`, username-only, password-only) —
the `queried = false` clause. The PASS_TO_PASS suite (e.g.
`test_authenticate`, the timing test "Hasher is run once …") requires the
proceed path to be unperturbed when both credentials are present — the A4 leg
(`queried = true`, `principal = backendOutcome`).

The prepatch (`Solution_prepatch.lean`) omits the guard: it always proceeds
(`queried := true`) and returns `backendOutcome`. With incomplete credentials
the frozen spec demands `queried = false`, so `prove_correct` fails on exactly
the discriminating clause:
```
case «ensures_1: out = authDecision suppliedName recoveredName password backendOutcome»
⊢ ¬(match suppliedName with | some u => some u | none => recoveredName) = none
  ∧ ¬password = none          -- unprovable: credentials may be absent
```
This is the precise bug the issue describes ("shouldn't make a database query
when username is None"). G-DIFF passes.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
admissibility short-circuit — is modeled **deeply** (the `authDecision`
conditional / the `if … then … else` impl, A2/A3, **I**), not hidden behind an
axiom. There are no consumed axioms: the only callee the proceed path touches
(the unchanged `get_by_natural_key` / `check_password` / `user_can_authenticate`
chain) is folded into the free input `backendOutcome`, about which the spec
claims nothing (mapping.md §3), so there is nothing for G-AX to check.

## D. G-CONF — conf_skip=true

The fix's only DISCRIMINATING observable is a side effect (no DB query, no hasher
run) on a live `AUTH_USER_MODEL` + database — there is no DB-free, input-dependent
R/I shadow to differential-test, and the proceed-path principal is the free input
`backendOutcome`. `conformance_check.py` is a documented `status=skip` stub
(`meta.json conf_skip=true`; precedent: django__django-11179). Soundness is
carried by G-VERIFY (spec forces `queried = false` ∧ `principal = none` on
incomplete credentials) and G-DIFF (the prepatch fails exactly that clause). See
mapping.md §4.
