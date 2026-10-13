# properties.py — PBT falsification battery for django__django-10973. NOT a Nagini
# module; a record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read from model.py + refinement.md + the gold patch):
#   password_env_value(passwd: List[int]) -> List[int]
#   The value the gold-patched runshell_db exposes to the child process for the
#   connection password. The patch replaces the legacy `.pgpass`-file path (which
#   ran the password through _escape_pgpass: '\\'(92)->'\\\\', ':'(58)->'\\:') with
#   a VERBATIM exposure: subprocess_env['PGPASSWORD'] = str(passwd), set iff passwd
#   is truthy. The model carries `str` as List[int] of code points; the spec is
#   over PSeq[int] via ToSeq.
#
#   Precondition (ONE input, READ-ONLY):
#     (P1) Requires(Acc(list_pred(passwd), 1 / 2))   # HALF permission => no write
#   Postcondition (four clauses; the first two are framing/permission):
#     (Q1) Ensures(Acc(list_pred(passwd), 1 / 2))    # returns the read perm
#     (Q2) Ensures(Acc(list_pred(Result())))         # FULL perm on a fresh result
#     (Q3) Ensures(ToSeq(Result()) == ToSeq(passwd)) # LOAD-BEARING: verbatim copy
#     (Q4) Ensures((len(Result()) > 0) == (len(passwd) > 0))  # populated iff non-empty
#
# FRAME-MUTATION lane is MANDATORY: passwd is Acc(...,1/2) (read-only). A rival
#   that WRITES to passwd must be rejected for INSUFFICIENT PERMISSION (frame-mut).
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q3 pins Result to ToSeq(passwd),
#   which is GROUNDED entirely in the input argument (no opaque @Pure answer-key,
#   no exact-marker oracle — the pure region is empty in model.py; the only @Pure
#   fold pgpass_quote_seq lives in model_prepatch.py's ELIDED impl region and is
#   never referenced by model.py's proof). There is no value an echo could carry
#   that satisfies Q3 yet is wrong: the unique satisfier IS the password. So the
#   honest grounded-oracle positive control is "produce the password" (the copy /
#   the pos controls below), not a wrong echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. password_env_value is a pure value-returning copy
#   with no raise/return-vs-fallthrough difference invisible to the value
#   abstraction. The one genuine control-flow point of the gold change — "set the
#   env var iff passwd is truthy" — is already captured by Q4 (len>0 iff len>0),
#   which any rival must satisfy. The SIGINT save/ignore/restore and args
#   construction are kind-I unchanged plumbing (refinement.md §B), not modeled.
#
# AXIOM lane: meta.axioms == []. There is ONE deep_model_reference (pgpass_quote_seq,
#   an A-reference for the REMOVED _escape_pgpass helper) but it is consumed by NO
#   axiom and is not in model.py at all (it lives only in model_prepatch.py's
#   elided impl region; the proof never references it). axiom_check.py validates it
#   under G-AX already. Nothing in this bundle's model.py proof rests on a
#   @ContractOnly axiom or an A-reference, so AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "django__django-10973"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`, INCLUDING the nested invariants region).
# Every spec variant _swap()s ONLY this block, so the edit never touches the spec
# (axioms/pure/pre-/post-conditions regions + the function signature). same_spec is
# computed over the spec_view, which elides every impl region (and nested
# invariants), so swapping inside here is guaranteed same_spec.
_IMPL = """\
    result = []  # type: List[int]
    i = 0
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        Invariant(MustTerminate(len(passwd) - i + 1))
        # invariants-end
        c = passwd[i]
        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
    return result"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-cached-bound: structurally different (the loop bound is cached in a local
# `n` rather than re-evaluating len(passwd) each iteration) but behaviourally
# identical forward verbatim copy. KEEPS every gold proof obligation — the same
# forward take(i) invariant, the same per-element take-prefix Assert, the same
# final take(len) == whole Assert — and adds the trivially-preserved framing
# Invariant(n == len(passwd)) (passwd is read-only so len is constant). No loop
# direction flip (which would need an f(a+b) lemma against the front loop) and no
# dropped framing assert; the gold proof stays valid. If it fails => SPEC-TOO-STRONG.
_POS_CACHED = """\
    result = []  # type: List[int]
    n = len(passwd)
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(n == len(passwd))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        Invariant(MustTerminate(len(passwd) - i + 1))
        # invariants-end
        c = passwd[i]
        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
    return result"""

# admiss-reads: an admissibility positive control. The precondition is the
# non-trivial heap permission Acc(list_pred(passwd), 1/2); this control confirms
# it ADMITS the reads a normal F2P-shaped input needs — it reads len(passwd) and
# (when non-empty) the first code point under the half-permission, asserting those
# reads succeed, before running the gold verbatim-copy body. If the half-permission
# did not admit a legitimate read of a normal password, this would fail =>
# PRECOND-TOO-STRONG. All asserts are over values readable under Acc(...,1/2); no
# write, so no proof gap and no permission demand beyond the spec.
_ADMISS = """\
    # Admissibility: a normal (possibly empty) password is in-domain; the
    # half-permission admits reading its length and its elements.
    Assert(len(passwd) >= 0)
    result = []  # type: List[int]
    i = 0
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        Invariant(MustTerminate(len(passwd) - i + 1))
        # invariants-end
        c = passwd[i]
        Assert(c == passwd[i])  # the read is admitted under the half-permission
        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
    return result"""


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — passwd is Acc(...,1/2) read-only).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: the rival keeps the gold verbatim-copy body VERBATIM (so the
# rejection is attributable solely to the added write, not to a value mismatch),
# then WRITES BACK into the read-only input: passwd[0] = passwd[0]. A no-op store,
# but a STORE — it demands write permission (full) on `passwd`, which the caller
# only granted at 1/2. The verifier must reject for insufficient permission. A
# byte-fuzzer never thinks to mutate the input; this is the project's #1 weakness
# class.
_FRAME_MUT = """\
    result = []  # type: List[int]
    i = 0
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        Invariant(MustTerminate(len(passwd) - i + 1))
        # invariants-end
        c = passwd[i]
        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
    if len(passwd) > 0:
        # Frame violation: write back into the read-only (Acc(...,1/2)) input.
        passwd[0] = passwd[0]
    return result"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly and changes only the function impl region.
# ---------------------------------------------------------------------------

# weak-prepatch-quote: the FULL pre-patch behaviour reborn — expose the legacy
# file-fragment quoting of the password (backslash 92 doubles, colon 58 ->
# backslash+colon, else identity), spelled out inline so it needs no @Pure
# reference. This is exactly model_prepatch.py's value. Correct on colon/
# backslash-free passwords (test_basic 'somepassword', test_accent 'sésame',
# test_nopass) but wrong on any ':' or '\\'. Must be rejected by Q3 (the forward
# take(i) invariant breaks at the first special code point, since
# ToSeq(result) gains TWO elements there while take(i) gains one).
_WEAK_QUOTE = """\
    result = []  # type: List[int]
    i = 0
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        Invariant(MustTerminate(len(passwd) - i + 1))
        # invariants-end
        c = passwd[i]
        if c == 92:
            result = result + [92, 92]
        elif c == 58:
            result = result + [92, 58]
        else:
            result = result + [c]
        i = i + 1
    return result"""

# weak-colon-only: PARTIAL-DOMAIN. A copy that is verbatim EXCEPT it still escapes
# the colon (58 -> backslash+colon), the single character the F2P test_column
# pins. Correct on every colon-free password (test_basic, test_accent, test_nopass)
# but diverges on 'some:password' -> 'some\\:password'. Rejected by Q3 at the colon
# position. A byte-fuzzer would not isolate exactly the one code point whose
# escaping the bug-fix removes.
_WEAK_COLON = """\
    result = []  # type: List[int]
    i = 0
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        Invariant(MustTerminate(len(passwd) - i + 1))
        # invariants-end
        c = passwd[i]
        if c == 58:
            result = result + [92, 58]
        else:
            result = result + [c]
        i = i + 1
    return result"""

# weak-drop-first: PARTIAL-DOMAIN / off-by-one. Copy starting at index 1, dropping
# the FIRST code point. Correct length/content ONLY for empty passwords; wrong for
# every non-empty password (the result is missing element 0 and is one shorter).
# Rejected by Q3 (content) and Q4 (a 1-char password yields an empty result, so
# len(Result())>0 is False while len(passwd)>0 is True). Targets the input that
# fails first (the leading character).
_WEAK_DROP = """\
    result = []  # type: List[int]
    i = 1
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(passwd) + 1)
        Invariant(0 <= i)
        # invariants-end
        c = passwd[i - 1]
        result = result + [c]
        i = i + 1
    return result"""

# weak-always-empty: the trivial too-weak baseline — always expose nothing. This
# is what a rival that "forgot to populate PGPASSWORD" would do; it satisfies Q3
# only for the empty password. Rejected by Q3 (non-empty mismatch) AND Q4 (for a
# non-empty password, len(Result())>0 is False but len(passwd)>0 is True). Cheap
# supporting near-miss; still carries a real refinement.
_WEAK_EMPTY = """\
    empty = []  # type: List[int]
    return empty"""


SPEC_TESTS = [
    {
        "id": "pos-cached-bound",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_CACHED),
        "rationale": (
            "structurally-different forward copy (loop bound cached in a local n, "
            "extra trivially-preserved Invariant(n == len(passwd))) that keeps "
            "every gold proof obligation (take(i) invariant, per-element prefix "
            "Assert, final take(len)==whole Assert). The verbatim copy still holds "
            "Q3/Q4. If it fails => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the non-trivial precondition Acc(list_pred(passwd), 1/2) must admit "
            "the reads a normal password needs (its length and each element). The "
            "control reads len(passwd) and each passwd[i] under the half-permission "
            "and asserts the reads succeed before the gold copy. If it fails => "
            "PRECOND-TOO-STRONG (the half-permission would reject a legitimate input)."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold patch reads the caller's password and exposes it VERBATIM "
            "(env['PGPASSWORD'] = str(passwd)); it NEVER writes back into the "
            "caller's password object. A faithful real patch that mutated the "
            "shared password (e.g. in-place rewrite of conn_params['password']) "
            "would corrupt the caller's connection params and diverge from the "
            "gold's read-only verbatim exposure — it would not be the gold patch "
            "and would not faithfully resolve. The store here is a no-op only by "
            "coincidence; the point is that the spec must forbid ANY write."
        ),
        "rationale": (
            "REJECTED by the permission system: passwd is granted at Acc(...,1/2) "
            "(P1); the store passwd[0]=passwd[0] demands FULL write permission, "
            "which is not available, so the verifier rejects for INSUFFICIENT "
            "PERMISSION. The gold verbatim-copy body is kept verbatim so the "
            "rejection is attributable solely to the write. If it verifies => the "
            "read-only frame is not enforced (frame-mutation, the #1 weakness class)."
        ),
    },
    {
        "id": "weak-prepatch-quote",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_QUOTE),
        "refinement": (
            "this is exactly the PRE-PATCH behaviour (model_prepatch.py): the "
            "password run through _escape_pgpass legacy quoting ('\\\\'->'\\\\\\\\', "
            "':'->'\\\\:'). Its faithful real patch is the unpatched repo, which "
            "exposes 'some\\\\:password' for test_column's 'some:password' and the "
            "old colon-escaped pgpass line for test_basic/test_accent — failing "
            "the F2P tests that now assert the RAW password. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (ToSeq(Result()) == ToSeq(passwd)): at the first "
            "colon/backslash the result gains TWO code points while ToSeq(passwd)."
            "take(i) gains one, so the take(i) invariant (hence Q3) fails. This is "
            "the precise change the spec senses (G-DIFF). If it verifies => "
            "SPEC-TOO-WEAK (the verbatim requirement would not be enforced)."
        ),
    },
    {
        "id": "weak-colon-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_COLON),
        "refinement": (
            "a real patch that switched to PGPASSWORD but still ran the password "
            "through a colon-escape (a plausible half-fix: 'I removed the pgpass "
            "file but kept escaping the separator') would expose 'some\\\\:password' "
            "for test_column's 'some:password', failing that F2P which now asserts "
            "the raw 'some:password'. Correct on every colon-free F2P password "
            "(test_basic, test_accent, test_nopass), so it is a true PARTIAL-DOMAIN "
            "break, not a blanket wrong impl. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 at the colon code point (58): the result gains two "
            "elements there, breaking the take(i) invariant. The divergence is "
            "confined to the colon sub-domain — exactly the boundary a byte-fuzzer "
            "would not isolate. If it verifies => SPEC-TOO-WEAK on the colon "
            "sub-domain."
        ),
    },
    {
        "id": "weak-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP),
        "refinement": (
            "an off-by-one real patch that built the exposed value from passwd[1:] "
            "would expose 'omepassword' for 'somepassword' and '' for a 1-char "
            "password, failing every non-empty-password F2P (test_basic, "
            "test_column, test_accent). Correct only on the empty password. "
            "PARTIAL-DOMAIN attack on the input that fails first (the leading "
            "code point). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (content differs by the dropped first element) and by "
            "Q4 for a 1-char password (len(Result())>0 is False while "
            "len(passwd)>0 is True). If it verifies => SPEC-TOO-WEAK (the first "
            "element and the populated-iff-non-empty clause would be unpinned)."
        ),
    },
    {
        "id": "weak-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY),
        "refinement": (
            "always exposing nothing is what a real patch that 'forgot to set "
            "PGPASSWORD' would do (subprocess_env never gets the key). It exposes "
            "'' for every non-empty password, failing test_basic/test_column/"
            "test_accent (which assert the actual password). Does NOT resolve. "
            "Cheap supporting near-miss with a genuine refinement."
        ),
        "rationale": (
            "REJECTED by Q3 (empty != non-empty password) AND Q4 (for a non-empty "
            "password len(Result())>0 is False but len(passwd)>0 is True). The "
            "`empty = []  # type: List[int]` local is bound BEFORE return to keep "
            "the Nagini type comment valid (no bare `return []`). If it verifies => "
            "SPEC-TOO-WEAK."
        ),
    },
]

# No @ContractOnly axioms (meta.axioms == []) and no A-reference deep model in
# model.py's proof: the changed behaviour is modeled DIRECTLY as a verbatim
# code-point copy pinned by Q3. The single deep_model_reference (pgpass_quote_seq,
# the removed _escape_pgpass helper) is consumed by no axiom and lives only in
# model_prepatch.py's elided impl region — validated separately by axiom_check.py
# under G-AX. Nothing in this bundle's proof rests on an axiom or A-reference, so
# there is nothing for the axiom lane to execute.
AXIOM_TESTS = []
