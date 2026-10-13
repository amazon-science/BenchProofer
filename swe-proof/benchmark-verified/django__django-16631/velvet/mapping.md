# mapping.md — django__django-16631

Binds every `Solution.lean` symbol to the repository at
`base_commit = 9b224579875e30203d079cc2fee83b116d98eb78`, states the type
abstraction (the Lean↔Python bijection), and records callee provenance.

Repo file under change: `django/contrib/auth/__init__.py` (the session-credential
verification block inside `get_user`). A second hunk in
`django/contrib/auth/base_user.py` adds the plumbing that supplies the
per-prior-secret credentials the decision consumes (see §3).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveSessionPrincipal (storedCred : Option Cred) (currentCred : Cred) (priorCreds : List Cred)` | the session-verification block of `get_user(request)` — `django/contrib/auth/__init__.py:199-207` | the modeled changed decision (given a located principal, decide whether to keep it and what to do with the session) |
| `storedCred` | `session_hash = request.session.get(HASH_SESSION_KEY)` (`__init__.py:201`) | the credential token stored on the session; `none` ↔ absent/empty (Python falsy), `some h` ↔ a present token |
| `currentCred` | `user.get_session_auth_hash()` (`__init__.py:203`) — the principal's credential under the **current** secret | a present token (always computable for a located principal) |
| `priorCreds` | the tokens yielded by `user.get_session_auth_fallback_hash()` (post-patch) — the principal's credential under each **prior** secret | free input: the list of tokens under the configured prior secrets (possibly empty) |
| `Cred (= Nat)` | a credential token (an HMAC hex digest `str`) | opaque carrier; only **equality** of two tokens is ever observed (via `constant_time_compare`), never the digest content |
| `SessionVerify` (`principalKept : Bool`, `action : SessionAction`) | the block's two observables: whether `user` survives the block, and what is done to `request.session` | structured outcome (see §2) |
| `SessionAction.valid` | the verified-by-current case: the block leaves `request.session` untouched | session accepted as-is |
| `SessionAction.acceptedPrior` | the fallback-acceptance path of the post-patch block (`__init__.py` post-patch): user kept, and the gold patch's fallback-acceptance body runs verbatim — `request.session.cycle_key(); request.session[HASH_SESSION_KEY] = session_auth_hash` | prior-secret match: the effect glue is FIXED by the refinement (see §2a), not described in the spec view |
| `SessionAction.reject` | `request.session.flush(); user = None` (`__init__.py:206-207`) | session cleared and the principal dropped |

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): the single
`session_hash_verified = session_hash and constant_time_compare(session_hash,
user.get_session_auth_hash())` followed by an unconditional `flush()` + `user =
None` on failure (`__init__.py:202-207` @ base_commit).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `session_hash = request.session.get(HASH_SESSION_KEY)` : a `str` token or `None`/`""` | `Option Cred` (`Cred := Nat`) | `some h` ↔ a present, non-empty token; `none` ↔ Python falsy (`None` or `""`). `if not session_hash` ↔ `storedCred.isNone`. |
| `user.get_session_auth_hash()` : a `str` token | `Cred` | a present token; always computable for the located principal. |
| `user.get_session_auth_fallback_hash()` : an iterable of `str` tokens | `List Cred` | one token per configured prior secret, in order; empty ↔ no prior secrets configured. |
| `constant_time_compare(a, b)` : bool | Lean `a = b` on `Cred` | the call is a pure constant-time **equality** test on two `str` tokens; its timing property is unobservable to the F2P/P2P tests, so it refines to `DecidableEq` on `Cred`. |
| `any(constant_time_compare(session_hash, fb) for fb in priors)` : bool | `priorCreds.contains storedTok` | "some prior secret's token equals the stored token". |
| "the principal `user` survives the block" | `principalKept : Bool` | `true` ↔ `user` is still the located principal at block exit; `false` ↔ `user = None` (the caller then returns `AnonymousUser()`). |
| which glue path of the block runs | `SessionAction` | `valid` ↔ the no-op path; `acceptedPrior` ↔ the fallback-acceptance path; `reject` ↔ the flush-and-drop path. What each path *does* is effect glue held fixed by the refinement (§2a). |

### 2a. Effect glue (OUTSIDE the modeled slice; fixed by the refinement)

What `get_user` *does* on each classification is unmodeled glue, held fixed by
the refinement (refinement.md): `reject` ⇒ `request.session.flush()` +
`user = None`; `valid` ⇒ no state change; `acceptedPrior` ⇒ user kept and the
gold patch's fallback-acceptance body runs verbatim
(`request.session.cycle_key()`;
`request.session[HASH_SESSION_KEY] = session_auth_hash`). A refined patch is
*faithful* only if it attaches each classification to exactly this glue — the
same convention as the lean/nagini twins of this instance. The spec region
intentionally does not describe the glue: it is derivable only from
hints_text/gold and disclosing it would leak (see the G-PANEL-3 history of this
bundle).

`Cred` is modeled as `Nat` because the decision observes only **equality** of
tokens (the `constant_time_compare` results), never the digest content; the
content flows untouched through the unchanged crypto plumbing (§3).

## 3. Callee provenance

No axioms and no A-reference deep models.

- The token-producing machinery is **crypto plumbing that the decision observes
  only by equality**: `constant_time_compare` (unchanged), `salted_hmac`
  (unchanged — it already accepted the `secret=` keyword), and the principal's
  credential under the current and prior secrets. The patch's `base_user.py`
  hunk is a refactor + new generator: `get_session_auth_hash()` delegates to
  `_get_session_auth_hash()` with `secret=None` (which defaults to the current
  secret — **behaviourally identical** to the pre-patch body), and the new
  `get_session_auth_fallback_hash()` yields `_get_session_auth_hash(secret=s)`
  for each prior secret `s`. None of this changes what a token *is*; it only
  makes the list of prior-secret tokens available to the decision. These tokens
  are therefore taken as the **free inputs** `currentCred` / `priorCreds`. The
  spec makes no behavioural claim about how a token is computed and holds for
  EVERY value they could take, so there is nothing to check against a real
  callee — hence **no G-AX** (mirrors django__django-11451's `backendOutcome`
  and django__django-11149's `userHasPerm`/`superResult` free inputs).
- The CHANGED op is the decision itself — "if the current secret does not verify
  the session, accept it under a prior secret instead of dropping the
  principal" (with the per-classification effect glue fixed by the refinement,
  §2a). It is modeled **deeply** as `verifyDecision` / the `if … then …
  else` impl. No outside contract is consumed (I-tagged, refinement.md).

## 4. G-CONF — conf_skip=true (documented reason)

`conformance_check.py` is a `status=skip` stub. The fix's discriminating
observables — that the principal is **kept** (not replaced by `AnonymousUser`),
that the session key is **cycled** (`cycle_key()`), and that the stored token is
**refreshed to the current-secret token** — materialize only against a **live
Django request/session + `AUTH_USER_MODEL` + database**: to observe them one
must drive `get_user(request)` end to end with a configured user, a real session
store, and `override_settings(SECRET_KEY=…, SECRET_KEY_FALLBACKS=…)` — i.e. the
F2P integration test itself (`test_get_user_fallback_secret`), not a pure
transliteration this gate can fuzz over ≥10⁵ inputs. The decision's pure inputs
(`storedCred`, `currentCred`, `priorCreds`) are themselves outputs of the
crypto plumbing folded into free inputs (§3); there is no DB-free,
input-dependent R/I shadow whose oracle is anything other than the patched
`get_user` running against that live stack.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the modeled op's only discriminating
observable is a side effect on a live request/session/ORM with no DB-free R/I
shadow, set `meta.json conf_skip=true` and ship a `status=skip` stub (precedent:
django__django-11451, django__django-11179). Soundness of the modeled behaviour
is carried instead by **G-VERIFY** (the spec provably forces `principalKept =
true` ∧ `action = acceptedPrior` exactly when the stored token matches a
prior — not the current — secret, and `reject` when no secret matches) and
**G-DIFF** (the prepatch, lacking the prior-secret path, drops the principal in
that case and fails exactly that clause — refinement.md §B).

## 5. Notes — `mut`-frame discipline (directive 5)

`storedCred`, `currentCred`, `priorCreds` are all read-only inputs — none is
declared `mut`: the decision reads them and produces a fresh `SessionVerify`,
mutating nothing it is handed.

The single FAIL_TO_PASS entry (`test_get_user_fallback_secret`) exercises one
fixed behavior — sessions surviving a secret rotation — through two successive
`get_user` calls (the first takes the `acceptedPrior` branch under a configured
prior secret; the second takes the `valid` branch because of the effect glue,
§2a, that path ran). One modeled function + one prepatch covers
that behavior; the gold-verbatim `patch.diff` resolves it (G-RESOLVE).
