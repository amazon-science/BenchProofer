# properties.py — PBT falsification battery for django__django-16631.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py variant that shares the frozen spec
# byte-for-byte (markers.same_spec) and edits ONLY inside the impl region(s)
# (the nested invariants region is elided with impl, so loop invariants may be
# changed too). Each AXIOM_TESTS case is a self-contained probe run in the
# instance Docker image.
#
# Defended surface (read model.py):
#   session_outcome(session_token, current_token, previous_tokens) -> int{0,1,2}
#     read-only inputs: session_token, current_token  (Acc(list_pred(.),1/2))
#     pure value input: previous_tokens : PSeq[PSeq[int]]
#     post: Result in {0,1,2}; three GROUNDED biconditionals
#       (Result==1) iff present & ToSeq(session)==ToSeq(current)
#       (Result==2) iff present & differs from current & matches_any(session, previous)
#       (Result==0) iff absent | (differs from current & not matches_any)
#     + frame: Ensures Acc 1/2 on both lists (read-only preserved).
#   fallback_auth_hashes(password, default_secret, fallback_secrets) -> PSeq[PSeq[int]]
#     read-only inputs: password, default_secret  (Acc(list_pred(.),1/2))
#     post: Result == tokens_under(ToSeq(password), fallback_secrets)  (GROUNDED in
#       the @Pure fold over the @ContractOnly token_for_secret axiom). Note
#       default_secret is read-only AND UNUSED by the postcondition.
from pathlib import Path

INSTANCE = "django__django-16631"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (verbatim from model.py impl regions). Editing only between
# these guarantees same_spec.
# ---------------------------------------------------------------------------

# session_outcome impl (gold)
_SO_IMPL = """    if len(session_token) == 0:
        return 0
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    if matches_any(ToSeq(session_token), previous_tokens):
        return 2
    return 0"""

# fallback_auth_hashes impl (gold) — note the back-to-front loop that mirrors
# the front-recursive tokens_under fold.
_FA_IMPL = """    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        result = PSeq(token_for_secret(ToSeq(password), s)) + result
        i = i - 1
    return result"""


# ===========================================================================
# SITE A — session_outcome
# ===========================================================================

# --- pos-control-A : structurally-different CORRECT impl (soundness) --------
# Same priority semantics (current beats previous), but the branches are
# rewritten with explicit boolean guards and the order in which the two
# membership facts are computed is reshaped (compute the "present & differs
# from current" gate as a local, then branch). Every clause stays grounded;
# nothing is dropped. Must VERIFY (else SPEC-TOO-STRONG).
_POS_A = """    if len(session_token) == 0:
        return 0
    present_eq_current = ToSeq(session_token) == ToSeq(current_token)
    if present_eq_current:
        return 1
    in_previous = matches_any(ToSeq(session_token), previous_tokens)
    if in_previous:
        return 2
    return 0"""

# --- admiss-A : admissibility — the Requires admits an F2P-shaped input -----
# The impl READS both read-only lists (len + ToSeq), exercising exactly the
# 1/2 permission the precondition grants, then returns the gold decision. If a
# normal read-only input could not satisfy Requires this would fail to verify
# (PRECOND-TOO-STRONG). Behaviour identical to gold, so it must VERIFY.
_ADMISS_A = """    _present = len(session_token) > 0          # read session_token (1/2 ok)
    _cur_len = len(current_token)               # read current_token (1/2 ok)
    Assert(_cur_len >= 0)
    if not _present:
        return 0
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    if matches_any(ToSeq(session_token), previous_tokens):
        return 2
    return 0"""

# --- frame-mut-A : MANDATORY frame-mutation rival (uniqueness) --------------
# A rival that WRITES to the read-only session_token (append) to "use" it,
# while still returning the gold decision. With only Acc(list_pred,1/2) the
# append needs full permission -> must be REJECTED for insufficient permission.
# refinement: a faithful real get_user that MUTATES the inbound stored session
# hash string in place (it is read from request.session, an external store) is
# not what the gold does and is not what the F2P observes; the gold leaves the
# cookie value untouched on outcome 1 and only rewrites session[HASH_SESSION_KEY]
# via cycle_key on outcome 2 — it never edits the read session_hash itself. A
# variant that mutates its read input cannot be the gold behaviour.
_FRAME_A = """    if len(session_token) == 0:
        return 0
    session_token.append(0)
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    if matches_any(ToSeq(session_token), previous_tokens):
        return 2
    return 0"""

# --- frame-mut-A2 : write to the OTHER read-only input (current_token) ------
# Supporting frame case: clear/append current_token. Also needs full perm.
_FRAME_A2 = """    if len(session_token) == 0:
        return 0
    current_token.append(0)
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    if matches_any(ToSeq(session_token), previous_tokens):
        return 2
    return 0"""

# --- swap-1-2-A : priority inversion (uniqueness, reasoned) -----------------
# Returns 2 on a current-token match (i.e. swaps the {1,2} verdicts whenever the
# stored token also coincides with a previous token, but in general returns 2
# where gold returns 1 by checking previous FIRST). Violates the biconditional
# (Result==1) iff present & equals current: here a present token equal to current
# that is ALSO a previous token returns 2, breaking the (Result==1) clause.
# refinement: the gold gives the CURRENT secret priority — a session still keyed
# by the active secret stays authenticated WITHOUT cycling the key (outcome 1,
# session untouched). A faithful patch that returned the upgrade/cycle path for a
# token that already equals the current hash would needlessly cycle_key on every
# request whose token happens to match a fallback too; the F2P's first phase keeps
# the user via the current-vs-fallback distinction and the order is load-bearing.
_SWAP_A = """    if len(session_token) == 0:
        return 0
    if matches_any(ToSeq(session_token), previous_tokens):
        return 2
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    return 0"""

# --- partial-A : partial-domain rival (uniqueness) --------------------------
# Correct EXCEPT it drops the previous-token (outcome-2) branch when the stored
# token has length 1 (a value sub-domain), returning 0 there instead of 2.
# Diverges only on a sub-domain; violates the (Result==2) biconditional for those
# inputs (matches_any holds yet it returns 0).
# refinement: a faithful get_user that refused to consult the fallback hashes for
# certain stored-hash shapes would, on the F2P, fail to keep the just-rotated user
# whenever the real digest hit that shape — the fallback acceptance must be total
# over all present mismatching tokens, not conditional on length.
_PARTIAL_A = """    if len(session_token) == 0:
        return 0
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    if len(session_token) != 1 and matches_any(ToSeq(session_token), previous_tokens):
        return 2
    return 0"""

# --- reject-all-A : collapse to reject (uniqueness, cheap supporting) -------
# The pre-patch behaviour: never produce outcome 2 (the missing fallback branch).
# This is model_prepatch.py's defect. Violates (Result==2) biconditional.
# refinement: this IS the unfixed get_user — it flushes any session not matching
# the current token, so after rotation the F2P user is logged out (outcome 0
# where gold gives 2). It would NOT resolve test_get_user_fallback_secret.
_REJECTALL_A = """    if len(session_token) == 0:
        return 0
    if ToSeq(session_token) == ToSeq(current_token):
        return 1
    return 0"""


# ===========================================================================
# SITE B — fallback_auth_hashes
# ===========================================================================

# --- pos-control-B : structurally-different CORRECT impl (soundness) --------
# Keep the back-to-front loop direction (a forward-append would need an
# f(a+b)==f(a)+f(b) lemma against the front-recursive tokens_under fold — AVOID).
# Reshape: hoist the per-step token into an explicit local and reorder the two
# framing Asserts. Loop invariants kept verbatim (they are the gold proof
# obligations; deleting them would fail for a PROOF reason, not a spec reason).
# Must VERIFY (else SPEC-TOO-STRONG).
_POS_B = """    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        tok = PSeq(token_for_secret(ToSeq(password), s))  # type: PSeq[PSeq[int]]
        result = tok + result
        i = i - 1
    return result"""

# --- admiss-B : admissibility — Requires admits an F2P-shaped input ---------
# Reads both read-only lists (ToSeq(password) used; default_secret len read),
# exercising the 1/2 permission, then runs the gold loop. Must VERIFY.
_ADMISS_B = """    _ds_len = len(default_secret)   # read default_secret (1/2 ok)
    Assert(_ds_len >= 0)
    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        result = PSeq(token_for_secret(ToSeq(password), s)) + result
        i = i - 1
    return result"""

# --- frame-mut-B : MANDATORY frame-mutation rival (uniqueness) --------------
# Writes to the read-only `password` (append) — needs full list_pred permission,
# only 1/2 granted -> must be REJECTED for insufficient permission. The gold
# proof obligations are kept verbatim so the rejection is attributable to the
# write, not a proof gap.
# refinement: _get_session_auth_hash reads self.password but never mutates it;
# a faithful patch does not edit the user's stored password while computing
# fallback hashes. A variant that does is not the gold behaviour.
_FRAME_B = """    password.append(0)
    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        result = PSeq(token_for_secret(ToSeq(password), s)) + result
        i = i - 1
    return result"""

# --- frame-mut-B2 : write to default_secret (the UNUSED read-only input) ----
# default_secret is read-only and not referenced by the postcondition. A rival
# that mutates it (append) must STILL be rejected for insufficient permission —
# even an unused read-only input cannot be written. Supporting frame case.
_FRAME_B2 = """    default_secret.append(0)
    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        result = PSeq(token_for_secret(ToSeq(password), s)) + result
        i = i - 1
    return result"""

# --- miskey-B : the discriminating site-B defect (uniqueness) ---------------
# Keys every token on `default_secret` (the active secret) instead of the
# iterated previous secret `s` — exactly model_prepatch_2.py's missing-`secret=`
# behaviour. Breaks the invariant result == tokens_under(password, drop(i))
# (tokens are mis-keyed), so it must be REJECTED.
# refinement: this is the unfixed _get_session_auth_hash — every fallback hash
# keyed by SECRET_KEY, so get_session_auth_fallback_hash yields tokens identical
# to the current token. On the F2P the stored token (keyed by the OLD secret)
# would match NONE of them, so the fallback `any(...)` never fires and the user
# is flushed (outcome 0). It would NOT resolve test_get_user_fallback_secret.
_MISKEY_B = """    result = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    i = len(fallback_secrets)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(password), 1 / 2))
        Invariant(Acc(list_pred(default_secret), 1 / 2))
        Invariant(0 <= i and i <= len(fallback_secrets))
        Invariant(result == tokens_under(ToSeq(password), fallback_secrets.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        s = fallback_secrets[i - 1]
        Assert(fallback_secrets.drop(i - 1)[0] == s)
        Assert(fallback_secrets.drop(i - 1).drop(1) == fallback_secrets.drop(i))
        result = PSeq(token_for_secret(ToSeq(password), ToSeq(default_secret))) + result
        i = i - 1
    return result"""

# --- drop-token-B : front-recursive omission (uniqueness, partial-domain) ---
# Emit an EMPTY token sequence (skip every secret). Breaks the invariant /
# postcondition (result != tokens_under for non-empty fallback_secrets).
# refinement: a fallback generator that yielded nothing is the pre-fix world
# (no get_session_auth_fallback_hash at all) — the F2P user is flushed.
_DROP_B = """    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    return empty"""


SPEC_TESTS = [
    # ---- soundness / admissibility (must verify) ----
    {"id": "pos-control-A", "kind": "soundness", "expect": "verify",
     "module": _swap(_BASE, _SO_IMPL, _POS_A),
     "rationale": "structurally-different but correct session_outcome (explicit "
                  "boolean guards, reshaped order of the two membership facts, "
                  "current-priority preserved); must verify else SPEC-TOO-STRONG."},
    {"id": "admiss-A", "kind": "admissibility", "expect": "verify",
     "module": _swap(_BASE, _SO_IMPL, _ADMISS_A),
     "rationale": "reads both read-only lists under the 1/2 permission then "
                  "returns the gold decision; the Requires must admit a normal "
                  "F2P-shaped input else PRECOND-TOO-STRONG."},
    {"id": "pos-control-B", "kind": "soundness", "expect": "verify",
     "module": _swap(_BASE, _FA_IMPL, _POS_B),
     "rationale": "structurally-different correct fallback_auth_hashes (per-step "
                  "token hoisted to a local, framing Asserts reordered, gold loop "
                  "invariants kept verbatim, back-to-front direction preserved to "
                  "avoid an f(a+b) lemma); must verify else SPEC-TOO-STRONG."},
    {"id": "admiss-B", "kind": "admissibility", "expect": "verify",
     "module": _swap(_BASE, _FA_IMPL, _ADMISS_B),
     "rationale": "reads default_secret under the 1/2 permission then runs the "
                  "gold loop; Requires must admit a normal input else "
                  "PRECOND-TOO-STRONG."},

    # ---- frame-mutation (MANDATORY: read-only inputs; must reject) ----
    {"id": "frame-mut-A", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _SO_IMPL, _FRAME_A),
     "refinement": "the gold get_user reads session_hash from request.session and "
                   "never edits that value; outcome 1 leaves the cookie untouched "
                   "and outcome 2 rewrites session[HASH_SESSION_KEY] via cycle_key, "
                   "not the read session_hash. A patch that mutates its read input "
                   "is not the gold and is not what the F2P observes.",
     "rationale": "session_token is Acc(list_pred,1/2); append needs full "
                  "permission -> rejected for INSUFFICIENT PERMISSION (frame). "
                  "The #1 weakness class."},
    {"id": "frame-mut-A2", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _SO_IMPL, _FRAME_A2),
     "refinement": "current_token models user.get_session_auth_hash() (a freshly "
                   "computed digest the gold compares against); the gold never "
                   "mutates it. A variant that does is not the gold behaviour.",
     "rationale": "current_token is Acc(list_pred,1/2); append needs full "
                  "permission -> rejected for INSUFFICIENT PERMISSION (frame, "
                  "supporting)."},

    # ---- uniqueness / reasoned wrong impls (must reject) ----
    {"id": "swap-1-2-A", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _SO_IMPL, _SWAP_A),
     "refinement": "the gold gives the CURRENT secret priority: a session keyed "
                   "by the active secret stays authenticated WITHOUT cycling the "
                   "key (outcome 1, session untouched). Checking previous first "
                   "returns the upgrade/cycle path for a token equal to the current "
                   "hash, needlessly cycling the key; the order is load-bearing in "
                   "the F2P (the user is kept via the current branch in phase 2).",
     "rationale": "violates (Result()==1) == (present & ToSeq(session)==ToSeq("
                  "current)): a present token equal to current that is also a "
                  "previous token returns 2 here, breaking the outcome-1 clause."},
    {"id": "partial-A", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _SO_IMPL, _PARTIAL_A),
     "refinement": "fallback acceptance must be total over present mismatching "
                   "tokens; a get_user that refused the fallback path for some "
                   "stored-hash shapes would, on the F2P, fail to keep the rotated "
                   "user whenever the real digest hit that shape.",
     "rationale": "violates (Result()==2) == (... matches_any ...): for a present "
                  "token of length 1 that matches a previous token it returns 0, "
                  "breaking the outcome-2 biconditional on that sub-domain."},
    {"id": "reject-all-A", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _SO_IMPL, _REJECTALL_A),
     "refinement": "this is the unfixed get_user (no fallback branch) — it flushes "
                   "any session not matching the current token, so after rotation "
                   "the F2P user is logged out (outcome 0 where gold gives 2). It "
                   "would NOT resolve test_get_user_fallback_secret (model_prepatch).",
     "rationale": "never produces outcome 2; violates (Result()==2) biconditional "
                  "when matches_any holds (G-DIFF prepatch defect)."},

    {"id": "frame-mut-B", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _FA_IMPL, _FRAME_B),
     "refinement": "_get_session_auth_hash reads self.password but never mutates "
                   "it; a faithful patch does not edit the stored password while "
                   "computing fallback hashes. A mutating variant is not the gold.",
     "rationale": "password is Acc(list_pred,1/2); append needs full permission -> "
                  "rejected for INSUFFICIENT PERMISSION (frame)."},
    {"id": "frame-mut-B2", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _FA_IMPL, _FRAME_B2),
     "refinement": "default_secret is a read-only input unused by the result; even "
                   "an unused read-only input is never written by the gold. A "
                   "variant that writes it is not the gold behaviour.",
     "rationale": "default_secret is Acc(list_pred,1/2); append needs full "
                  "permission -> rejected for INSUFFICIENT PERMISSION (frame, "
                  "supporting — even an UNUSED read-only input is unwritable)."},
    {"id": "miskey-B", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _FA_IMPL, _MISKEY_B),
     "refinement": "this is the unfixed _get_session_auth_hash — every fallback "
                   "hash keyed by the active secret, so get_session_auth_fallback_"
                   "hash yields tokens equal to the current token. On the F2P the "
                   "stored token (keyed by the OLD secret) matches none of them, "
                   "the fallback any(...) never fires, and the user is flushed "
                   "(outcome 0). It would NOT resolve the F2P (model_prepatch_2).",
     "rationale": "keys token_for_secret on default_secret not on the iterated "
                  "secret s; breaks the invariant result == tokens_under(password, "
                  "fallback_secrets.drop(i)) (G-DIFF site-B defect)."},
    {"id": "drop-token-B", "kind": "uniqueness", "expect": "reject",
     "module": _swap(_BASE, _FA_IMPL, _DROP_B),
     "refinement": "an empty fallback sequence is the pre-fix world (no "
                   "get_session_auth_fallback_hash) — the F2P user is flushed.",
     "rationale": "returns the empty sequence; violates Result() == tokens_under("
                  "password, fallback_secrets) for any non-empty fallback_secrets "
                  "(supporting partial-domain)."},
]


# ===========================================================================
# AXIOM lane — token_for_secret (@ContractOnly, A-consumed) +
#              constant_time_compare (A-reference deep model).
# Probes run in the instance Docker image (real django.utils.crypto present;
# stdlib reconstruction otherwise). Self-contained stdlib-only python strings.
# ===========================================================================

# Embed the bundle's axiom_check.py source so the probe reuses the audited
# real-callee oracle (the runner mounts ONLY the probe at /work).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


_AX_SOUND_PROBE = r'''
# axiom-soundness: token_for_secret == salted_hmac(...).hexdigest(), keyed
# exactly as _get_session_auth_hash. The axiom states NO Ensures: the proof
# consumes ONLY functional determinism (equal (password,secret) -> equal token),
# supplied by @Pure. We verify determinism on the boundary + sentinels + fuzz,
# AND secret-sensitivity (the rotation premise the F2P exercises). We never
# assert any exact digest value. Runs the REAL callee (Django when present),
# never scrapes source. Exit 0 iff the obligation holds.
import hashlib, hmac, random, secrets, sys

KEY_SALT = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"

def _force_bytes(s):
    return s.encode("utf-8") if isinstance(s, str) else bytes(s)

def _stdlib_token(value, secret):
    key = hashlib.sha256(_force_bytes(KEY_SALT) + _force_bytes(secret)).digest()
    return hmac.new(key, msg=_force_bytes(value), digestmod=hashlib.sha256).hexdigest()

try:
    from django.conf import settings as _s
    if not _s.configured:
        _s.configure(SECRET_KEY="axiomcheck-secret")
    from django.utils.crypto import salted_hmac as _dj
    def token_for_secret(pw, sec):
        return _dj(KEY_SALT, pw, secret=sec, algorithm="sha256").hexdigest()
    BACKEND = "django.utils.crypto (real callee)"
except Exception:
    def token_for_secret(pw, sec):
        return _stdlib_token(pw, sec)
    BACKEND = "stdlib reconstruction (no Django on path)"

# token_for_secret's Requires domain (model.py): password, secret are PSeq[int]
# of code points (any str). No further restriction. So every str is in-domain.
passwords = ["", "testpw", "p@ss w0rd!", "Ω-π-é", "x"*128, "Joe's", "0"*64]
secrets_pool = ["newsecret", "oldsecret", "", "k", "Ω-secret", "x"*64, "django-insecure-aaa"]

# (a) determinism — the ONLY property the proof consumes (purity).
for pw in passwords:
    for sec in secrets_pool:
        t1 = token_for_secret(pw, sec)
        t2 = token_for_secret(pw, sec)
        if t1 != t2:
            print("FAIL determinism pw=%r sec=%r: %r vs %r" % (pw, sec, t1, t2))
            sys.exit(1)

# (b) secret-sensitivity (rotation premise, an input fact not an axiom claim).
for pw in passwords:
    for i in range(len(secrets_pool)):
        for j in range(i+1, len(secrets_pool)):
            sa, sb = secrets_pool[i], secrets_pool[j]
            if sa == sb:
                continue
            if token_for_secret(pw, sa) == token_for_secret(pw, sb):
                print("FAIL secret-collision pw=%r %r/%r" % (pw, sa, sb))
                sys.exit(1)

# fuzz
rng = random.Random(16631)
alpha = "abcdefghijklmnopqrstuvwxyzABCDEF0123456789@!$ ΩπéΣ"
for _ in range(20000):
    pw = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 20)))
    sa = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 16)))
    sb = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 16)))
    if token_for_secret(pw, sa) != token_for_secret(pw, sa):
        print("FAIL determinism fuzz"); sys.exit(1)
    if sa != sb and token_for_secret(pw, sa) == token_for_secret(pw, sb):
        print("FAIL secret-collision fuzz pw=%r %r/%r" % (pw, sa, sb)); sys.exit(1)

print("AX-SOUND OK [%s]: token_for_secret deterministic + secret-sensitive over "
      "%d boundary + 20000 fuzz; no exact-value claim" % (BACKEND, len(passwords)*len(secrets_pool)))
sys.exit(0)
'''


_AX_COVER_PROBE = r'''
# axiom-containment: enumerate EXACTLY the token_for_secret inputs the MODEL can
# reach and assert each lies in the axiom's Requires domain.
#   - model.py declares token_for_secret(password: PSeq[int], secret: PSeq[int]).
#     Its Requires domain is "any pair of int-code-point sequences" (no further
#     constraint). The model reaches it from tokens_under(ToSeq(password),
#     fallback_secrets) where each call passes (ToSeq(password), fallback_secrets[k])
#     — both PSeq[int]. There is NO caller-reachable input outside that domain:
#     the axiom domain is the full PSeq[int] x PSeq[int] product the caller draws
#     from, so containment is total. (Covering the whole product is SOUND.)
# We make this concrete by executing the real callee on every shape the model can
# produce (incl. empty password / empty secret / empty fallback list semantics)
# and confirming it returns a value (a hex digest) for each — i.e. no reachable
# input is rejected by / outside the callee's domain.
import sys

KEY_SALT = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"

def _force_bytes(s):
    return s.encode("utf-8") if isinstance(s, str) else bytes(s)

try:
    from django.conf import settings as _s
    if not _s.configured:
        _s.configure(SECRET_KEY="axiomcheck-secret")
    from django.utils.crypto import salted_hmac as _dj
    def token_for_secret(pw, sec):
        return _dj(KEY_SALT, pw, secret=sec, algorithm="sha256").hexdigest()
    BACKEND = "django.utils.crypto (real callee)"
except Exception:
    import hashlib, hmac
    def token_for_secret(pw, sec):
        key = hashlib.sha256(_force_bytes(KEY_SALT) + _force_bytes(sec)).digest()
        return hmac.new(key, msg=_force_bytes(pw), digestmod=hashlib.sha256).hexdigest()
    BACKEND = "stdlib reconstruction (no Django on path)"

# Every caller-reachable shape: passwords and secrets drawn from arbitrary code
# points; the previous-secret list may be empty (no token_for_secret call) or any
# length (one call per element). Confirm the callee accepts each in-domain input
# and yields a hex digest (so the model never reaches an out-of-domain input).
passwords = ["", "testpw", "Ω-π-é", "x"*200, "0"*1]
secret_lists = [[], ["oldsecret"], ["a", "b", "c"], ["", "Ω", "x"*64]]
HEX = set("0123456789abcdef")
total = 0
for pw in passwords:
    for secs in secret_lists:
        for sec in secs:           # exactly the calls tokens_under makes
            tok = token_for_secret(pw, sec)
            if not (isinstance(tok, str) and len(tok) == 64 and set(tok) <= HEX):
                print("FAIL out-of-domain / bad digest pw=%r sec=%r -> %r" % (pw, sec, tok))
                sys.exit(1)
            total += 1
        # empty list -> tokens_under returns the empty seq; zero callee calls (in domain trivially)

print("AX-COVER OK [%s]: all %d caller-reachable token_for_secret inputs are in "
      "the axiom Requires domain (PSeq[int] x PSeq[int]); no reachable input "
      "lies outside it" % (BACKEND, total))
sys.exit(0)
'''


_AX_CTC_PROBE = r'''
# A-reference: constant_time_compare(a, b) == (a == b) on hex digests — the deep
# model behind site A's compare / matches_any. Validates the model's PSeq
# equality against the REAL callee on equal, unequal-equal-length, and
# unequal-length digest pairs + fuzz. Exit 0 iff it matches everywhere.
import random, secrets, sys

def _force_bytes(s):
    return s.encode("utf-8") if isinstance(s, str) else bytes(s)

try:
    from django.conf import settings as _s
    if not _s.configured:
        _s.configure(SECRET_KEY="axiomcheck-secret")
    from django.utils.crypto import constant_time_compare as ctc
    BACKEND = "django.utils.crypto.constant_time_compare (real callee)"
except Exception:
    def ctc(a, b):
        return secrets.compare_digest(_force_bytes(a), _force_bytes(b))
    BACKEND = "stdlib secrets.compare_digest reconstruction"

def check(a, b):
    obs = bool(ctc(a, b))
    exp = (a == b)
    if obs != exp:
        print("FAIL ctc(%r,%r)=%r but (a==b)=%r" % (a, b, obs, exp))
        sys.exit(1)

# boundary
check("a"*64, "a"*64)       # equal
check("a"*64, "b"*64)       # equal-length differ
check("a"*64, "a"*63)       # unequal length
check("", "")               # both empty
check("", "a")              # one empty
rng = random.Random(166312)
alpha = "0123456789abcdef"
for _ in range(20000):
    a = "".join(rng.choice(alpha) for _ in range(rng.randint(0, 64)))
    b = a if rng.random() < 0.5 else "".join(rng.choice(alpha) for _ in range(rng.randint(0, 64)))
    check(a, b)
print("A-REF OK [%s]: constant_time_compare == byte equality over boundary + "
      "20000 fuzz" % BACKEND)
sys.exit(0)
'''


AXIOM_TESTS = [
    {"id": "ax-sound-token_for_secret", "axiom": "token_for_secret",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_SOUND_PROBE,
     "rationale": "token_for_secret's only consumed property is functional "
                  "determinism (@Pure); the real salted_hmac(...).hexdigest() is "
                  "deterministic and secret-sensitive. A non-deterministic or "
                  "secret-insensitive callee would be AXIOM-UNSOUND."},
    {"id": "ax-cover-token_for_secret", "axiom": "token_for_secret",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_COVER_PROBE,
     "rationale": "every token_for_secret input the model can reach "
                  "(ToSeq(password), fallback_secrets[k]) is a PSeq[int] pair, "
                  "inside the axiom's full PSeq[int] x PSeq[int] domain; no "
                  "reachable input lies outside it (else AXIOM-TOO-WEAK-FOR-CALLER)."},
    {"id": "ax-ref-constant_time_compare", "axiom": "constant_time_compare",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_CTC_PROBE,
     "rationale": "constant_time_compare is modeled as PSeq equality (A-reference); "
                  "the real callee returns plain byte equality on hex digests. A "
                  "divergence would make the site-A membership model unsound."},
]
