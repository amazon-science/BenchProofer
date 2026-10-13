# properties.py — PBT falsification battery for django__django-11451. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start / # impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
# AXIOM_TESTS run the REAL Django callee in the instance Docker image.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + instance.json)
# ---------------------------------------------------------------------------
#   authenticate(self: Checker, identifier: Optional[int], secret: Optional[int],
#                fallback_identifier: Optional[int]) -> Optional[int]
#   Requires(Acc(self.lookups) and Acc(self.verifications))      # FULL perm
#   Requires(self.lookups >= 0 and self.verifications >= 0)      # the impl WRITES both counters
#
#   Postcondition (the load-bearing clauses, each an Implies guarded by the
#   present/absent pattern of the two credentials, after fallback recovery):
#     (1) (identifier absent after recovery) OR secret absent
#           => Result() is None
#              AND self.lookups       == Old(self.lookups)         # no DB query
#              AND self.verifications == Old(self.verifications)   # no hasher run
#     (2) (identifier present after recovery) AND secret present
#           => self.lookups       == Old(self.lookups) + 1         # EXACTLY one query
#              AND self.verifications == Old(self.verifications) + 1  # EXACTLY one hash, EVERY both-present path
#     (2a) ... AND directory_recognises(eff)
#           => (Result() is not None) == secret_verifies(eff, secret)   # return iff secret verifies
#              AND Implies(Result() is not None, Result() == eff)       # the EXACT matched account
#     (2b) ... AND not directory_recognises(eff)
#           => Result() is None
#   where eff = (identifier if identifier is not None else fallback_identifier).
#
#   directory_recognises(identifier:int)->bool and secret_verifies(identifier:int,
#   secret:int)->bool are @Pure @ContractOnly axioms with NO Ensures: opaque,
#   deterministic, pure decisions over the args (the unchanged callees
#   get_by_natural_key and check_password ∧ user_can_authenticate). They are
#   GROUNDED in the function's own arguments (eff, secret) — there is no separate
#   answer-key oracle to echo.
#
# ---------------------------------------------------------------------------
# Where each weakness class lands on THIS surface
# ---------------------------------------------------------------------------
#  * FRAME-MUTATION (the #1 class): N/A. The only Acc(...) is on self.lookups /
#    self.verifications, held at FULL permission because the impl must WRITE them
#    (the cost counters). identifier / secret / fallback_identifier are pass-by-
#    value Optional[int] (immutable; no permission, no frame). There is NO
#    read-only Acc(x,1/2) input, so the canonical frame-mutation probe (overwrite
#    a half-permission input) does not apply — see `assessment`.
#  * UNGROUNDED-ORACLE ECHO: N/A as a wrong echo. directory_recognises /
#    secret_verifies take the function's own arguments (eff, secret); an impl
#    that wants Result() is not None must MAKE secret_verifies(eff, secret) hold,
#    which it cannot fake (the axiom value is opaque and pure of the args). There
#    is no answer-key the impl could echo without doing the work. Covered instead
#    by the cheapest-honest positive controls below.
#  * THE CHANGE: the inserted early-return guard `if eff is None or secret is
#    None: return None`. Dropping it (uniq-no-guard-leak == model_prepatch.py)
#    violates clause (1). This is the F2P discriminator.
#  * PARTIAL-DOMAIN: guard only one credential's absence (identifier-only /
#    secret-only) — fails clause (1) on the OTHER credential's absent sub-domain.
#  * CONTROL-FLOW / COST: increment verifications only on the recognised path
#    (the pre-#20760 timing leak) — fails clause (2) on the unrecognised
#    both-present sub-domain; or over-count a counter.
#  * VALUE-LEVEL (wrong output): return a wrong recognised account (eff+1), or
#    authenticate a recognised account WITHOUT the secret check — both fail
#    clause (2a).
from pathlib import Path

INSTANCE = "django__django-11451"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    # The verification primitive runs exactly once on every both-present path:
    # on the recognised path it is the secret check; on the unrecognised path
    # it is the timing-defence invocation.
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff
        return None
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Every gold proof obligation that still
# applies is preserved; only the executable shape changes (pilot pitfalls #2/#3
# avoided: no loop / no fold, so no auto-undischargeable lemma is introduced).
# ===========================================================================

# pos-control-merge-branch: collapse the nested recognised/unrecognised branches
# into ONE combined boolean condition. The early-return guard and the two
# unconditional counter increments are UNCHANGED, so clauses (1) and (2) hold
# verbatim. For clause (2a): under the antecedent directory_recognises(eff) is
# true, so `directory_recognises(eff) and secret_verifies(eff, secret)` reduces
# to secret_verifies(eff, secret) — hence Result() is not None iff secret
# verifies, and the returned value is exactly eff. For clause (2b): when not
# recognised the combined condition is false, so it returns None. Behaviourally
# identical; must verify.
_POS_MERGE = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    if directory_recognises(eff) and secret_verifies(eff, secret):
        return eff
    return None
    # impl-end"""

# pos-control-single-return: a local-variable reshape — compute the answer into
# one typed local and return it once at the end (single-exit shape) instead of
# the gold's multiple early returns on the both-present path. Same guard, same
# unconditional increments. Must verify.
_POS_SINGLE_RETURN = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    answer = None  # type: Optional[int]
    if directory_recognises(eff):
        if secret_verifies(eff, secret):
            answer = eff
    return answer
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the precondition admits a normal F2P-shaped
# input (else PRECOND-TOO-STRONG). We cannot add a module-level caller (it would
# change the projected spec view and break same_spec); instead we inject the
# witness INSIDE the impl region (elided from the spec view). It constructs a
# fresh Checker (the F2P-shaped state: both counters 0 from the constructor
# Ensures) and Asserts the function's exact Requires holds for it (Acc on both
# counters, both >= 0). The real impl then runs unchanged. If the precondition
# could not be established for a legitimate freshly-constructed checker the
# Assert fails => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    adm = Checker()
    # the function's Requires is establishable for this concrete fresh checker:
    #   Acc(adm.lookups) and Acc(adm.verifications) (from the constructor Ensures)
    #   and adm.lookups >= 0 and adm.verifications >= 0 (both are 0).
    Assert(Acc(adm.lookups) and Acc(adm.verifications))
    Assert(adm.lookups >= 0 and adm.verifications >= 0)
    # --- end admissibility witness; the real impl follows unchanged ---
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff
        return None
    # impl-end"""


# ===========================================================================
# UNIQUENESS rivals — share the spec exactly, change ONLY the impl. Each MUST be
# rejected; a verifying rival is a true verify-but-not-resolve break
# (SPEC-TOO-WEAK). Each carries the refinement: why its faithful real patch
# would NOT resolve the F2P/P2P.
# ===========================================================================

# uniq-no-guard-leak: THE BUG (== model_prepatch.py). Drop the early-return
# guard entirely; consult the directory and run the verification primitive
# unconditionally (both counters +1 on every path), guarding the axiom calls
# against None so the variant still type-checks. On an absent-credential input
# this violates clause (1) — lookups and verifications are Old+1, not Old.
_UNIQ_NO_GUARD = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    if eff is None or not directory_recognises(eff):
        return None
    else:
        if secret is not None and secret_verifies(eff, secret):
            return eff
        return None
    # impl-end"""

# uniq-guard-identifier-only (partial-domain): the guard covers an absent
# identifier but NOT an absent secret. When the identifier is present and the
# secret is absent it falls through and spends both expensive operations,
# violating clause (1) on the secret-absent sub-domain.
_UNIQ_GUARD_ID_ONLY = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None:
        return None
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret is not None and secret_verifies(eff, secret):
            return eff
        return None
    # impl-end"""

# uniq-guard-secret-only (partial-domain, mirror): the guard covers an absent
# secret but NOT an absent identifier. When the secret is present and the
# identifier is absent (even after fallback) it falls through and spends both
# expensive operations, violating clause (1) on the identifier-absent sub-domain.
_UNIQ_GUARD_SECRET_ONLY = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if secret is None:
        return None
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    if eff is None or not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff
        return None
    # impl-end"""

# uniq-verify-only-on-recognised (control-flow / timing leak): run the
# verification primitive (increment verifications) ONLY on the recognised path,
# not on the unrecognised path. This is the pre-#20760 timing leak. It violates
# clause (2) on the unrecognised both-present sub-domain: verifications stays at
# Old (the clause requires Old+1).
_UNIQ_VERIFY_ON_RECOGNISED = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    if not directory_recognises(eff):
        return None
    else:
        self.verifications = self.verifications + 1
        if secret_verifies(eff, secret):
            return eff
        return None
    # impl-end"""

# uniq-wrong-identity (value-level): on the recognised + verifying path return a
# DIFFERENT account (eff + 1) instead of the matched one. Clause (2a) pins
# Result() == eff; eff + 1 != eff, so it is rejected (machine-confirmed in
# meta.json G-EQ: returning eff+1 fails verification).
_UNIQ_WRONG_IDENTITY = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff + 1
        return None
    # impl-end"""

# uniq-skip-secret-check (value-level): on the recognised path return the account
# WITHOUT consulting secret_verifies (authenticate anyone whose identifier is
# recognised). Clause (2a) requires (Result() is not None) == secret_verifies(
# eff, secret); when the secret does NOT verify this returns the account anyway,
# so Result() is not None while secret_verifies is false => rejected.
_UNIQ_SKIP_SECRET = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        return eff
    # impl-end"""

# uniq-double-lookup (cost over-count; supporting near-miss): increment lookups
# twice on the both-present path. Violates clause (2): lookups becomes Old+2,
# the clause requires exactly Old+1.
_UNIQ_DOUBLE_LOOKUP = """    # impl-start
    eff = identifier  # type: Optional[int]
    if eff is None:
        eff = fallback_identifier
    if eff is None or secret is None:
        return None
    self.lookups = self.lookups + 1
    self.lookups = self.lookups + 1
    self.verifications = self.verifications + 1
    if not directory_recognises(eff):
        return None
    else:
        if secret_verifies(eff, secret):
            return eff
        return None
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-merge-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_MERGE),
        "rationale": "structurally-different CORRECT impl: collapse the nested "
                     "recognised/unrecognised branches into one combined condition "
                     "`if directory_recognises(eff) and secret_verifies(eff, secret): "
                     "return eff; return None`. Same early-return guard, same two "
                     "unconditional increments. Under clause (2a)'s antecedent "
                     "directory_recognises(eff) is true so the conjunction reduces to "
                     "secret_verifies, giving Result() is not None iff the secret "
                     "verifies and Result()==eff; under clause (2b) (not recognised) it "
                     "returns None. Behaviourally identical, no loop/fold, no new lemma. "
                     "If a faithful correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-single-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_SINGLE_RETURN),
        "rationale": "local-variable reshape to a single-exit shape: accumulate the "
                     "answer into one typed local `answer` and return it once, instead "
                     "of the gold's multiple early returns on the both-present path. "
                     "Same guard and same unconditional increments, so clauses (1)/(2) "
                     "hold; the recognised/verifying assignment gives the exact clause "
                     "(2a)/(2b) outcomes. Must verify; else SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-fresh-checker",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) constructs a fresh Checker "
                     "(the F2P-shaped state: both counters 0 via the constructor "
                     "Ensures) and Asserts the function's exact Requires for it "
                     "(Acc(adm.lookups) and Acc(adm.verifications); both >= 0). The real "
                     "impl then runs unchanged. If the precondition could not be "
                     "established for this legitimate fresh checker the Assert fails => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- uniqueness (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-no-guard-leak",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_NO_GUARD),
        "refinement": "this is EXACTLY model_prepatch.py / the pre-patch behaviour: no "
                      "early-return guard, so on an absent-credential input the "
                      "directory lookup runs (one DB query) and the verification "
                      "primitive runs (one hasher run) on the unrecognised path. Its "
                      "faithful real patch is the un-guarded ModelBackend.authenticate "
                      "the gold hunk fixes; the F2P test_authentication_without_"
                      "credentials asserts assertNumQueries(0) and "
                      "CountingMD5PasswordHasher.calls == 0 for each of {}, "
                      "{'username':X}, {'password':'test'} — the unguarded code makes a "
                      "query (and a hasher run) and FAILS those assertions, so it does "
                      "NOT resolve.",
        "rationale": "rejected by clause (1): with the guard dropped, on an absent-"
                     "credential input self.lookups == Old+1 and self.verifications == "
                     "Old+1, violating Ensures(... => lookups == Old(lookups) and "
                     "verifications == Old(verifications)).",
    },
    {
        "id": "uniq-guard-identifier-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_GUARD_ID_ONLY),
        "refinement": "guards only an absent identifier (`if username is None: return`), "
                      "omitting the `or password is None` half of the gold hunk. The "
                      "faithful real patch with that half-guard still runs the lookup "
                      "(and hasher) when the username is present but the password is "
                      "absent — the F2P test_authentication_without_credentials subTest "
                      "credentials={'username': X} (password absent) then makes a query "
                      "and FAILS assertNumQueries(0), so it does NOT resolve.",
        "rationale": "rejected by clause (1) on the secret-absent sub-domain: when "
                     "identifier present and secret is None the impl reaches the "
                     "increments, so self.lookups == Old+1 / self.verifications == Old+1 "
                     "violate the both-counters-unchanged guarantee.",
    },
    {
        "id": "uniq-guard-secret-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_GUARD_SECRET_ONLY),
        "refinement": "the mirror partial guard: guards only an absent secret (`if "
                      "password is None: return`), omitting the `username is None` half. "
                      "The faithful real patch still runs the lookup (and the "
                      "timing-defence hasher) when the password is present but the "
                      "username is absent (recovered as None) — the F2P subTest "
                      "credentials={'password':'test'} (username absent) then makes a "
                      "query and FAILS assertNumQueries(0), so it does NOT resolve.",
        "rationale": "rejected by clause (1) on the identifier-absent sub-domain: when "
                     "secret present and the identifier is absent (after fallback) the "
                     "impl reaches the increments, so lookups/verifications == Old+1 "
                     "violate the both-counters-unchanged guarantee.",
    },
    {
        "id": "uniq-verify-only-on-recognised",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_VERIFY_ON_RECOGNISED),
        "refinement": "runs the verification primitive only on the recognised branch — "
                      "the pre-#20760 timing leak. Its faithful real patch omits the "
                      "unrecognised-path UserModel().set_password(password) timing-"
                      "defence hasher run, so an unrecognised user is verified with 0 "
                      "hasher runs while a recognised user takes 1, leaking existence by "
                      "timing. The P2P test_authentication_timing asserts "
                      "CountingMD5PasswordHasher.calls == 1 for BOTH a recognised "
                      "account AND no_such_user; with 0 hasher runs on the unrecognised "
                      "path that assertion FAILS, so it does NOT resolve.",
        "rationale": "rejected by clause (2) on the unrecognised both-present sub-"
                     "domain: when both credentials are present but not recognised, "
                     "self.verifications stays at Old, violating "
                     "Ensures(... => verifications == Old(verifications) + 1).",
    },
    {
        "id": "uniq-wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_WRONG_IDENTITY),
        "refinement": "returns a DIFFERENT account (eff + 1) on the recognised+verifying "
                      "path. The faithful real patch would return a user object other "
                      "than the one matched by get_by_natural_key — the authenticate "
                      "identity tests (test_authenticates / login flow) observe the "
                      "returned account and would see the wrong user, so it does NOT "
                      "resolve.",
        "rationale": "rejected by clause (2a)'s Implies(Result() is not None, Result() "
                     "== eff): eff + 1 != eff, so the returned-identity pin fails "
                     "(machine-confirmed in meta.json G-EQ — returning eff+1 fails "
                     "verification).",
    },
    {
        "id": "uniq-skip-secret-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_SKIP_SECRET),
        "refinement": "authenticates anyone whose identifier is recognised WITHOUT "
                      "checking the secret (drops secret_verifies). Its faithful real "
                      "patch returns the user without `user.check_password(password) and "
                      "user_can_authenticate(user)`, so a recognised account with a "
                      "WRONG password (or an inactive account) would authenticate — the "
                      "wrong-password / inactive-user authenticate tests would then pass "
                      "authentication where they must fail, so it does NOT resolve.",
        "rationale": "rejected by clause (2a)'s (Result() is not None) == "
                     "secret_verifies(eff, secret): on the recognised path with a "
                     "non-verifying secret this returns eff (non-None) while "
                     "secret_verifies is false, breaking the equivalence.",
    },

    # ---- supporting mechanical near-miss (cheap; still carries a refinement) ----
    {
        "id": "uniq-double-lookup",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DOUBLE_LOOKUP),
        "refinement": "performs the directory lookup twice on the both-present path. A "
                      "faithful real patch issuing two get_by_natural_key DB queries per "
                      "authenticate would double the query count the auth tests pin via "
                      "assertNumQueries, so it does NOT resolve. Supporting near-miss for "
                      "the exact-cost clause (2).",
        "rationale": "rejected by clause (2): self.lookups becomes Old+2, violating "
                     "Ensures(... => lookups == Old(lookups) + 1).",
    },
]


# ===========================================================================
# AXIOM LANE — two A-consumed @Pure @ContractOnly axioms (NO Ensures):
#   directory_recognises(identifier:int)->bool  ↔ get_by_natural_key raising/not
#       raising UserModel.DoesNotExist (the recognition decision)
#   secret_verifies(identifier:int, secret:int)->bool ↔ user.check_password(
#       password) and user_can_authenticate(user) (the verify+permission decision)
# Because the axioms carry NO value Ensures, "axiom-soundness" here means: the
# real ModelBackend.authenticate's recognition + verification decisions are pure,
# deterministic functions of (identifier, secret), and the DEEP cost/return model
# the proof rides on holds against the real callee — exactly the obligations
# axiom_check.py validates: both-present => exactly 1 query + exactly 1 hasher run
# on EVERY path; recognised => the matched account iff the secret verifies;
# unrecognised => None; absent => None. We embed axiom_check.py's logic (it
# imports only Django + stdlib, both present in the eval image; the runner mounts
# ONLY the probe at /work, so the bundle file itself is NOT available
# in-container — its source is inlined below). flag_dependency: PASSWORD_HASHERS
# is pinned to MD5PasswordHasher and user_can_authenticate uses is_active (the
# default ModelBackend config), matching the F2P/P2P runtime config.
# ===========================================================================

# Embed the bundle's own G-AX soundness logic (read on the HOST at load time, so
# the probe is self-contained in-container).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AX_SOUNDNESS_PROBE = _AXIOM_CHECK_SRC

# axiom-containment: the model can pass to directory_recognises / secret_verifies
# ONLY `eff` (a present, non-None Optional[int], i.e. an opaque present
# identifier code) and, for secret_verifies, `secret` (a present non-None
# Optional[int]) — both reached strictly AFTER the early-return guard, so both
# arguments are PRESENT (never None) on every call. The axiom Requires domain is
# `identifier: int` (and `secret: int`) — present codes. So every caller-
# reachable callee-input lies inside the axiom domain (the real callee accepts a
# present username string / password string; the model abstracts present-vs-
# absent, and only the present case is ever passed). We confirm operationally
# that the real callee, driven over the PRESENT-credential matrix (the only
# inputs the model reaches for the axiom calls), is a total, deterministic
# decision — i.e. the caller never reaches an axiom input the real callee cannot
# decide. (Covering the absent case too would be SOUND, not required — the model
# never reaches it for these axioms because the guard returns first.)
_AX_CONTAINMENT_PROBE = r'''
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            AUTH_USER_MODEL="auth.User",
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
            USE_TZ=True,
        )
    django.setup()


def main():
    try:
        _configure_django()
    except Exception as exc:
        print("AXIOM-CONTAINMENT FAIL: Django not configurable: %r" % (exc,))
        return 1

    from django.db import connection
    from django.core.management import call_command
    from django.contrib.auth.backends import ModelBackend
    from django.contrib.auth.models import User

    call_command("migrate", run_syncdb=True, verbosity=0)
    User.objects.create_user(username="alice", password="s3cret")
    backend = ModelBackend()

    # The model reaches directory_recognises(eff) / secret_verifies(eff, secret)
    # ONLY with PRESENT (non-None) credentials (the early-return guard returns
    # before any axiom call when either is absent). Enumerate exactly that
    # caller-reachable set: present identifier x present secret, across
    # recognised(correct/wrong) and unrecognised. Each is an input INSIDE the
    # axiom's present-code Requires domain, and the real callee renders a
    # well-defined, deterministic decision for each (no exception escapes;
    # recognition is decided by DoesNotExist, verification by check_password).
    reachable = [
        ("alice", "s3cret"),   # recognised + correct
        ("alice", "wrong"),    # recognised + wrong
        ("nobody", "s3cret"),  # unrecognised
        ("ALICE", "s3cret"),   # unrecognised (case-sensitive natural key)
        ("alice2", "s3cret"),  # unrecognised
    ]
    seen = 0
    for username, password in reachable:
        # both present => inside the axiom domain (present identifier code +
        # present secret code). The real callee must decide it without error.
        assert username is not None and password is not None, (
            "AXIOM-CONTAINMENT FAIL: a reachable axiom input was not present-only")
        try:
            r1 = backend.authenticate(None, username=username, password=password)
            r2 = backend.authenticate(None, username=username, password=password)
        except Exception as exc:
            print("AXIOM-TOO-WEAK-FOR-CALLER: real callee could not decide a "
                  "model-reachable present-credential input (%r,%r): %r"
                  % (username, password, exc))
            return 1
        # deterministic decision (purity of the axiom): same authenticated-vs-not
        assert (r1 is not None) == (r2 is not None), (
            "AXIOM-CONTAINMENT FAIL: recognition/verification decision for "
            "(%r,%r) is not deterministic" % (username, password))
        seen += 1

    print("AXIOM-CONTAINMENT OK: every model-reachable callee-input for "
          "directory_recognises / secret_verifies is a PRESENT (non-None) "
          "credential code (the early-return guard precedes every axiom call), "
          "which lies inside the axioms' present-code Requires domain; the real "
          "ModelBackend.authenticate decides each of %d reachable inputs "
          "deterministically without error. The caller reaches only the "
          "present-credential subset of the axiom domain; no reachable input is "
          "outside it." % (seen,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-recognition-verification",
        "axiom": "directory_recognises,secret_verifies",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # axiom_check.py detects the tree and asserts the matching path
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "drives the REAL ModelBackend.authenticate over the full credential "
                     "matrix and asserts the obligations the two @ContractOnly axioms + "
                     "deep counter model ride on: both-present => exactly 1 query AND "
                     "exactly 1 hasher run on EVERY path (recognised-correct, "
                     "recognised-wrong, unrecognised); recognised => the matched account "
                     "iff the secret verifies; unrecognised => None; absent => None (post-"
                     "patch: 0 query/0 hash). The recognition/verification decisions are "
                     "deterministic (purity). Any disagreement => AXIOM-UNSOUND. Runs "
                     "under the F2P/P2P config (MD5 hasher, is_active permission).",
    },
    {
        "id": "ax-cover-recognition-verification",
        "axiom": "directory_recognises,secret_verifies",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "every callee-input the model can pass to directory_recognises / "
                     "secret_verifies is a PRESENT (non-None) credential code — the "
                     "early-return guard returns before any axiom call when either "
                     "credential is absent — so each reachable input lies inside the "
                     "axioms' present-code Requires domain and the real callee decides "
                     "it without error. A reachable input the callee could not decide "
                     "would be AXIOM-TOO-WEAK-FOR-CALLER; none exists.",
    },
]
