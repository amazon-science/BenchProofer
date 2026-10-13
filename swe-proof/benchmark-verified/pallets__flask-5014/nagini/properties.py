"""properties.py — PBT falsification manifest for pallets__flask-5014.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The single modeled function is

    validate_name(name: List[int], import_name: List[int]) -> None

modeling the name-validation prologue of `flask.Blueprint.__init__` after the
gold patch added `if not name: raise ValueError("'name' may not be empty.")`
between the `super().__init__(...)` base init and the pre-existing
`if "." in name: raise ValueError(...)` dot check.

Load-bearing contract:

    Requires(Acc(list_pred(name), 1/2))            # READ-ONLY name
    Requires(Acc(list_pred(import_name), 1/2))     # READ-ONLY import_name
    Ensures (Acc(list_pred(name), 1/2))            # returned read-only
    Ensures (Acc(list_pred(import_name), 1/2))
    Ensures (len(name) > 0)                         # NORMAL return => non-empty  (the NEW clause)
    Ensures (not contains_dot(ToSeq(name)))         # NORMAL return => dot-free
    Ensures (base_init_can_complete(ToSeq(import_name)))         # NORMAL return => base init completed
    Exsures(NameValidationError,
            Acc(name,1/2) and Acc(import_name,1/2)
            and base_init_can_complete(ToSeq(import_name))       # reject runs AFTER init_base returned
            and (len(name) == 0 or contains_dot(ToSeq(name))))   # reject set EXACTLY
    Exsures(BaseInitError, Acc(name,1/2) and Acc(import_name,1/2)
            and base_init_can_fail(ToSeq(import_name)))          # base-init abort, its own witness

where base_init_can_complete / base_init_can_fail are two INDEPENDENT @Pure
@ContractOnly WITNESSES over the base callee's own argument: init_base hands out
the first only when it completes and the second only when it fails as a unit,
and neither is the negation of the other. For one import_name the real base init
can do either, because its outcome also turns on an ambient table it may itself
populate and on the construction's optional root-path argument, neither of which
this spec carries (mapping.md §3.2). The channels are still pinned: a name
rejection runs strictly AFTER init_base RETURNED, so it carries the SUCCESS
witness, while the BaseInitError channel demands the FAILURE witness — obtainable
only from a base call that actually failed — so a name rejection cannot be routed
through the BaseInitError channel.

What the spec defends, and the attacks it must survive:

  * The DISCRIMINATING clause is the NEW `Ensures(len(name) > 0)`: a normal
    return is reachable ONLY for a non-empty name. The pre-patch code lacked the
    empty guard, so an empty dot-free name fell through to a normal return —
    `model_prepatch.py` reproduces that and FAILS exactly this Ensures (G-DIFF).
    The sole F2P, tests/test_blueprints.py::test_empty_name_not_allowed
    (`flask.Blueprint("", __name__)` must raise `ValueError`), demands it.
    `rival-drop-empty-guard` reproduces the pre-patch bug.

  * `Ensures(not contains_dot(ToSeq(name)))` pins the pre-existing dot guard; a
    P2P (test_dotted_name_not_allowed: `Blueprint("app.ui", __name__)` raises)
    relies on it. `rival-drop-dot-guard` drops it.

  * The reject oracle `contains_dot` is a @Pure FOLD over `ToSeq(name)` — fully
    grounded in the input (a single-unfold front recursion), NOT an opaque
    answer-key. There is no value to echo without computing it: any impl that
    satisfies `Ensures(not contains_dot(ToSeq(name)))` on the normal path has to
    have ruled the dot out by control flow. So the UNGROUNDED-ORACLE-ECHO class
    is N/A here; the honest cheapest impl (merged single guard) is the positive
    control `pos-control-merged-guard` instead (directive 2).

  * BOTH inputs are read-only (1/2). The MANDATORY attack is FRAME MUTATION:
    an impl that WRITES to `name`/`import_name` to satisfy a postcondition
    vacuously must fail for INSUFFICIENT PERMISSION, not a value mismatch
    (`frame-mutate-name`, `frame-mutate-import-name`).

  * CONTROL-FLOW-EFFECT: the value abstraction distinguishes THREE exits —
    normal return, raise NameValidationError, raise BaseInitError — and the gold
    F2P/P2P assert the reject path raises specifically `ValueError`
    (NameValidationError), NOT the ImportError/RuntimeError modeled by
    BaseInitError. The two exception channels are pinned by PROVENANCE, not by a
    decision procedure: `init_base` hands out `base_init_can_complete(import_name)`
    only on the exit where it completed and `base_init_can_fail(import_name)` only
    on the exit where it failed as a unit (both witnessed against the real callee
    by G-AX). A name rejection runs strictly AFTER `init_base` returns, so
    `Exsures(NameValidationError,...)` carries the SUCCESS witness while
    `Exsures(BaseInitError,...)` demands the FAILURE witness. A rival that raises
    BaseInitError on a rejected name does so AFTER init_base returned, where only
    the success witness is in scope, so it CANNOT establish the
    `base_init_can_fail(import_name)` the BaseInitError post requires => it is
    rejected. The witnesses are deliberately INDEPENDENT (neither is the negation
    of the other), so this rejection never rests on the real base init's outcome
    being a function of its own argument — which it is not: the same import_name
    can complete on one call and fail on another.
    Its faithful real patch (raise ImportError on empty/dotted name)
    would FAIL the `pytest.raises(ValueError)` F2P/P2P.
    `rival-wrong-exc-on-reject` probes exactly this discriminator.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
editing ONLY text strictly inside the single `# impl-start`/`# impl-end` region,
so `markers.same_spec` is guaranteed and any rejection is attributable to the
POSTCONDITION catching wrong behaviour (or the permission system), never to a
tampered spec. Each impl landmark occurs EXACTLY once (one modeled function).
Each `expect:"reject"` rival carries the refinement argument that its faithful
real patch would NOT resolve the F2P/P2P. The axiom lane runs the REAL base
initialiser (`flask.Blueprint(...)` -> `super().__init__` -> `Scaffold.__init__`
-> `get_root_path` -> `pkgutil.get_loader`) in Docker, reusing axiom_check.py's
logic, for the one A-consumed @ContractOnly axiom `init_base`.
"""
from pathlib import Path

INSTANCE = "pallets__flask-5014"
FLOAT_ENCODING = None  # meta.json float_encoding is null


# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace the single occurrence of an impl-region substring. Assert it
    appears exactly once so silent drift (model.py edited) fails loudly at
    load."""
    n = src.count(old)
    if n == 0:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if n != 1:
        raise AssertionError(
            f"properties.py: expected exactly 1 occurrence, found {n}: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmark: the WHOLE impl body, strictly between # impl-start / # impl-end.
# Occurs exactly once (single modeled function).
# ---------------------------------------------------------------------------
_IMPL_BODY = """    init_base(import_name)
    if len(name) == 0:
        raise NameValidationError()
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) Structurally-different but CORRECT: MERGE the two reject guards into a
# single disjunctive guard. init_base is still called first (so the BaseInitError
# pass-through is preserved), the raise fires on EXACTLY the reject set
# (len==0 or contains_dot), and the normal return is reachable only for an
# accepted name. Semantically identical to gold, different control-flow shape.
# This is also the cheapest HONEST impl: the dot test is the grounded @Pure fold,
# not an echoable oracle, so there is nothing cheaper than computing it. No
# induction lemma is needed (contains_dot unfolds the same way as in gold). If
# this fails to verify, the postcondition is over-fit to the two-guard form =>
# SPEC-TOO-STRONG.
_IMPL_MERGED_GUARD = """    init_base(import_name)
    if len(name) == 0 or contains_dot(ToSeq(name)):
        raise NameValidationError()
    return"""
_POS_MERGED_GUARD = _swap(_BASE, _IMPL_BODY, _IMPL_MERGED_GUARD)

# (5b) Structurally-different but CORRECT: REORDER the two guards (dot check
# first, then empty check). Both raise the same NameValidationError and the
# Exsures reject predicate is the disjunction (len==0 or contains_dot), so the
# firing order is immaterial to the spec; the accept set is unchanged. init_base
# stays first. A different code shape over identical logic; if it fails to verify
# the spec is over-fit to the gold guard order => SPEC-TOO-STRONG.
_IMPL_REORDER_GUARD = """    init_base(import_name)
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    if len(name) == 0:
        raise NameValidationError()
    return"""
_POS_REORDER_GUARD = _swap(_BASE, _IMPL_BODY, _IMPL_REORDER_GUARD)

# (6) ADMISSIBILITY. Build an F2P/P2P-shaped accepted name `[111, 107]` = "ok"
# as a FULL-permission fresh local, then self-call validate_name on it BEFORE
# running the gold body unchanged. Passing 1/2 from a full-permission local must
# succeed; if the precondition Acc(list_pred(.),1/2) cannot be established for a
# normal input => PRECOND-TOO-STRONG. The self-call reuses the method's OWN
# `import_name` as its second argument: the base-init channel carries the FAILURE
# witness for its argument, so the self-call's Exsures(BaseInitError,
# base_init_can_fail(import_name)) matches the method's own Exsures(BaseInitError,
# base_init_can_fail(import_name)) on the SAME import_name and propagates soundly.
# (A fresh resolvable `pimp` would instead require producing
# `base_init_can_fail(ToSeq(pimp))` for an OPAQUE witness the self-call's failure
# exit hands out only for its own argument — not a precondition fact, so it is
# unprovable in-proof and would be a spurious proof gap, NOT a
# precondition-strength signal.) The self-call is placed first; the gold body
# then runs against the method's own `name`/`import_name` exactly as before.
_IMPL_ADMISS = """    pname = [111, 107]  # type: List[int]
    # Proof: discharge that the self-call's Exsures(NameValidationError,
    # base_init_can_complete and (len==0 or contains_dot)) is unreachable for this
    # accepted local by UNFOLDING the front-recursive @Pure contains_dot bottom-up
    # over the concrete 2-element ToSeq(pname). Nagini does not auto-evaluate the
    # recursive fold on a literal, so these in-region asserts trigger the unfold
    # (no spec change). The self-call passes the method's OWN import_name, so its
    # Exsures(BaseInitError, base_init_can_fail(import_name)) matches the method's
    # own BaseInitError post on the same import_name and propagates soundly.
    Assert(len(ToSeq(pname)) == 2)
    Assert(not contains_dot(ToSeq(pname).drop(2)))
    Assert(ToSeq(pname).drop(1)[0] == 107)
    Assert(not contains_dot(ToSeq(pname).drop(1)))
    Assert(ToSeq(pname)[0] == 111)
    Assert(not contains_dot(ToSeq(pname)))
    Assert(Acc(list_pred(pname), 1 / 2))
    Assert(Acc(list_pred(import_name), 1 / 2))
    init_base(import_name)
    if len(name) == 0:
        raise NameValidationError()
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return"""
_POS_ADMISS = _swap(_BASE, _IMPL_BODY, _IMPL_ADMISS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) FRAME MUTATION on `name` — MANDATORY, the #1 weakness class. `name` is
# read-only (1/2). This rival STORES name[0] = name[0] before any guard, touching
# the read-only input. Under Acc(list_pred(name),1/2) a store requires FULL
# permission, so it MUST fail for INSUFFICIENT PERMISSION (not a value mismatch).
# The gold body is kept verbatim after the write so the rejection is attributable
# solely to the store. (Guarded by len so the index is in range when reached, but
# the permission obligation fires regardless of the value.) Rejection source: the
# PERMISSION SYSTEM.
_IMPL_FRAME_NAME = """    init_base(import_name)
    if len(name) > 0:
        name[0] = name[0]
    if len(name) == 0:
        raise NameValidationError()
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return"""
_RIVAL_FRAME_NAME = _swap(_BASE, _IMPL_BODY, _IMPL_FRAME_NAME)

# (1b) FRAME MUTATION on `import_name` — the second read-only input. Same attack,
# stores import_name[0]. Must fail for insufficient permission. import_name is
# held at 1/2 across the call to init_base too, so the store is also an aliasing
# hazard; the permission check fires regardless.
_IMPL_FRAME_IMP = """    init_base(import_name)
    if len(import_name) > 0:
        import_name[0] = import_name[0]
    if len(name) == 0:
        raise NameValidationError()
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return"""
_RIVAL_FRAME_IMP = _swap(_BASE, _IMPL_BODY, _IMPL_FRAME_IMP)

# (2) THE BUG ITSELF — DROP THE EMPTY GUARD (the pre-patch behaviour;
# model_prepatch.py reverts to exactly this). With no `if len(name) == 0` check,
# an empty, dot-free name (len==0, contains_dot False) falls through to the normal
# return. Its faithful real patch is the UNCHANGED pre-patch Blueprint.__init__,
# which is precisely what FAILS the sole F2P
# tests/test_blueprints.py::test_empty_name_not_allowed (`Blueprint("", __name__)`
# must raise ValueError but the pre-patch code constructs it) — it would NOT
# resolve. Rejection source: the NEW postcondition `Ensures(len(name) > 0)` —
# unprovable on the normal path because an empty name reaches `return`.
_IMPL_DROP_EMPTY = """    init_base(import_name)
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return"""
_RIVAL_DROP_EMPTY = _swap(_BASE, _IMPL_BODY, _IMPL_DROP_EMPTY)

# (3) DROP THE DOT GUARD — the pre-existing check the patch leaves in place. With
# no `if contains_dot(...)` check, a dotted name (e.g. "app.ui") falls through to
# the normal return. Its faithful real patch removes the `if "." in name: raise`
# line, which FAILS the P2P test_dotted_name_not_allowed
# (`Blueprint("app.ui", __name__)` must raise ValueError) — it would NOT resolve.
# Rejection source: `Ensures(not contains_dot(ToSeq(name)))` — unprovable on the
# normal path because a dotted name reaches `return`.
_IMPL_DROP_DOT = """    init_base(import_name)
    if len(name) == 0:
        raise NameValidationError()
    return"""
_RIVAL_DROP_DOT = _swap(_BASE, _IMPL_BODY, _IMPL_DROP_DOT)

# (4) PARTIAL-DOMAIN — guard only the EMPTY case and the *first* code point being
# a dot, missing dots elsewhere. Replace the full-fold dot guard with a check of
# only the leading element (name[0] == 46). A name whose dot is NOT first (e.g.
# "a.b", code points [97,46,98]) passes the weakened guard and reaches the normal
# return. Its faithful real patch (`if name[:1] == ".": raise` — only a leading
# dot) would accept "a.b"/"app.ui", FAILING the P2P test_dotted_name_not_allowed
# (`Blueprint("app.ui", __name__)`) — it would NOT resolve. Rejection source:
# `Ensures(not contains_dot(ToSeq(name)))` — for "a.b" contains_dot is True yet
# the impl returns normally, so the dot-free Ensures is unprovable.
_IMPL_PARTIAL = """    init_base(import_name)
    if len(name) == 0:
        raise NameValidationError()
    if name[0] == 46:
        raise NameValidationError()
    return"""
_RIVAL_PARTIAL = _swap(_BASE, _IMPL_BODY, _IMPL_PARTIAL)

# (5) CONTROL-FLOW-EFFECT — raise the WRONG exception on the reject path. The
# reject guards raise BaseInitError instead of NameValidationError, AFTER
# init_base has already returned normally. The spec pins that channel to the
# base callee's FAILURE witness: the BaseInitError post carries
# `base_init_can_fail(import_name)`, a fact `init_base` hands out ONLY on its
# failure exit. At this program point `init_base` has RETURNED, so only
# `base_init_can_complete(import_name)` is in scope — and the success witness does
# NOT imply the failure witness (the two are independent by design). The
# synthesized BaseInitError therefore cannot discharge `Exsures(BaseInitError, ...
# base_init_can_fail(import_name))` and the rival is REJECTED ("Assertion
# base_init_can_fail(ToSeq(import_name)) might not hold"). Its faithful
# real patch raises ImportError/RuntimeError (BaseInitError's referent) on a
# rejected name instead of ValueError, which FAILS the `pytest.raises(ValueError)`
# F2P/P2P (test_empty_name_not_allowed / test_dotted_name_not_allowed) — it would
# NOT resolve. Rejection source: the BaseInitError post demands a witness only a
# base call that actually FAILED produces, so routing a name rejection through
# that channel is INADMISSIBLE. If it verified => SPEC-TOO-WEAK (the
# error-channel for the reject set unconstrained — a control-flow effect
# invisible to the value side).
_IMPL_WRONG_EXC = """    init_base(import_name)
    if len(name) == 0:
        raise BaseInitError()
    if contains_dot(ToSeq(name)):
        raise BaseInitError()
    return"""
_RIVAL_WRONG_EXC = _swap(_BASE, _IMPL_BODY, _IMPL_WRONG_EXC)

# (6) OVER-REJECTION (supporting near-miss with a real refinement) — raise on a
# name that should be ACCEPTED. The impl unconditionally raises
# NameValidationError after init_base (rejects EVERY name). Its faithful real
# patch raises ValueError on every name, which FAILS every constructing P2P
# (e.g. `Blueprint("test", __name__)` is used throughout the suite) — it would
# NOT resolve. Rejection source: `Exsures(NameValidationError, ... len==0 or
# contains_dot(...))` — an accepted name (non-empty, dot-free) raises, but the
# Exsures predicate is False there, so the raise is not admissible.
_IMPL_OVER_REJECT = """    init_base(import_name)
    raise NameValidationError()"""
_RIVAL_OVER_REJECT = _swap(_BASE, _IMPL_BODY, _IMPL_OVER_REJECT)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-merged-guard", "kind": "soundness", "expect": "verify",
     "module": _POS_MERGED_GUARD,
     "rationale": "structurally-different (the two reject guards merged into one "
                  "disjunctive `if len(name)==0 or contains_dot(ToSeq(name))`) but "
                  "semantically identical impl; init_base stays first so the "
                  "BaseInitError pass-through is preserved. Must verify; if not, the "
                  "postcondition is over-fit to the two-guard form => SPEC-TOO-STRONG. "
                  "Also the cheapest HONEST impl: contains_dot is a grounded @Pure fold, "
                  "not an echoable oracle, so nothing is cheaper than computing it."},
    {"id": "pos-control-reorder-guard", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER_GUARD,
     "rationale": "a correct impl with the two guards REORDERED (dot check first). Both "
                  "raise the same NameValidationError and the Exsures reject predicate is "
                  "the disjunction, so the firing order is immaterial; the accept set is "
                  "unchanged. Must verify; if not, the spec is over-fit to the gold guard "
                  "order => SPEC-TOO-STRONG."},
    {"id": "admiss-self-call", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "a self-call on an F2P/P2P-shaped accepted name \"ok\"=[111,107] built as a "
                  "fresh FULL-permission local (passing the method's own import_name as the "
                  "second arg) must establish the precondition Acc(list_pred(.),1/2) (passing "
                  "1/2 from full permission); if it cannot => PRECOND-TOO-STRONG. The accepted "
                  "name's NameValidationError post is discharged unreachable by unfolding the "
                  "front-recursive @Pure contains_dot over the literal; reusing the method's "
                  "own import_name keeps the self-call's Exsures(BaseInitError, "
                  "base_init_can_fail(import_name)) aligned with the method's own (so the "
                  "opaque failure witness need not be produced for a fresh literal "
                  "— that would be a spurious proof gap, not a precondition signal). The gold "
                  "body then runs unchanged."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_NAME,
     "refinement": "no faithful real patch corresponds to this: Blueprint.__init__ never "
                   "mutates the `name` string (strings are immutable in Python, and the "
                   "validation prologue only reads it). The rival exists solely to test "
                   "whether the read-only (1/2) precondition on `name` can be subverted by "
                   "writing to it. No resolving patch overwrites its input, so a verifying "
                   "rival here would be a pure verify-not-resolve artifact (vacuous "
                   "satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `name[0] = name[0]` stores through a 1/2 "
                  "(read-only) reference and MUST fail for insufficient permission. "
                  "Rejection source: the PERMISSION SYSTEM (a store needs full perm), not a "
                  "value mismatch; the gold body is kept verbatim after the write. If it "
                  "verified => SPEC-TOO-WEAK (frame protection on `name` hollow)."},
    {"id": "frame-mutate-import-name", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME_IMP,
     "refinement": "import_name is an immutable string passed straight to the base "
                   "initialiser; no resolving patch writes to it. A verifying rival here "
                   "would be a verify-not-resolve artifact.",
     "rationale": "MANDATORY frame-mutation probe on the second read-only input. "
                  "`import_name[0] = import_name[0]` stores through a 1/2 reference and MUST "
                  "fail for insufficient permission. Rejection source: the PERMISSION SYSTEM. "
                  "If it verified => SPEC-TOO-WEAK (frame protection on `import_name` hollow)."},
    {"id": "rival-drop-empty-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_EMPTY,
     "refinement": "drops the NEW empty guard — exactly the PRE-PATCH "
                   "Blueprint.__init__ (model_prepatch.py reverts to this). Its faithful "
                   "real patch is the unchanged pre-patch constructor, which is precisely "
                   "what FAILS the sole F2P tests/test_blueprints.py::test_empty_name_not_"
                   "allowed (`Blueprint(\"\", __name__)` must raise ValueError but the "
                   "pre-patch code constructs it) — it would NOT resolve.",
     "rationale": "the DISCRIMINATING bug this patch fixes (mirrors G-DIFF / "
                  "model_prepatch.py). Rejection source: the NEW postcondition "
                  "`Ensures(len(name) > 0)` — unprovable on the normal path because an "
                  "empty, dot-free name reaches `return`. If it verified => SPEC-TOO-WEAK "
                  "(admits the very bug)."},
    {"id": "rival-drop-dot-guard", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_DOT,
     "refinement": "drops the pre-existing dot guard. Its faithful real patch removes the "
                   "`if \".\" in name: raise ValueError(...)` line, which FAILS the P2P "
                   "test_dotted_name_not_allowed (`Blueprint(\"app.ui\", __name__)` must "
                   "raise ValueError) — it would NOT resolve.",
     "rationale": "Rejection source: `Ensures(not contains_dot(ToSeq(name)))` — unprovable "
                  "on the normal path because a dotted name reaches `return`. If it "
                  "verified => SPEC-TOO-WEAK (the dot guarantee is hollow)."},
    {"id": "rival-partial-domain-leading-dot", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL,
     "refinement": "weakens the dot guard to only the FIRST code point (name[0]==46), so a "
                   "name whose dot is not leading (e.g. \"a.b\", \"app.ui\") passes. Its "
                   "faithful real patch (`if name[:1] == \".\": raise` — leading dot only) "
                   "would accept \"app.ui\", FAILING the P2P test_dotted_name_not_allowed — "
                   "it would NOT resolve.",
     "rationale": "partial-domain: correct on empty and on leading-dot names, wrong on the "
                  "interior-dot sub-domain. Rejection source: `Ensures(not "
                  "contains_dot(ToSeq(name)))` — for \"a.b\" contains_dot is True yet the "
                  "impl returns normally, so the dot-free Ensures is unprovable. If it "
                  "verified => SPEC-TOO-WEAK (domain-incomplete dot check)."},
    {"id": "rival-wrong-exc-on-reject", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_EXC,
     "refinement": "raises BaseInitError (the ImportError/RuntimeError referent) instead of "
                   "NameValidationError (the ValueError referent) on a rejected name. Its "
                   "faithful real patch would raise ImportError/RuntimeError on an "
                   "empty/dotted name, which FAILS the `pytest.raises(ValueError)` F2P/P2P "
                   "(test_empty_name_not_allowed / test_dotted_name_not_allowed expect a "
                   "ValueError, not an ImportError) — it would NOT resolve.",
     "rationale": "control-flow-effect: the error CHANNEL on the reject set is the "
                  "discriminator. The channels are pinned by PROVENANCE of two INDEPENDENT "
                  "witnesses: `Exsures(BaseInitError,... base_init_can_fail(import_name))` vs "
                  "`Exsures(NameValidationError,... base_init_can_complete(import_name) and "
                  "(len==0 or contains_dot))`. The rival raises BaseInitError on a reject AFTER "
                  "init_base returned, where only the success witness is in scope; the success "
                  "witness does not imply the failure witness, so it cannot discharge the "
                  "`base_init_can_fail(import_name)` the BaseInitError post demands => "
                  "REJECTED. If it verified => SPEC-TOO-WEAK (the reject error-channel "
                  "unconstrained)."},
    {"id": "rival-over-reject", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_OVER_REJECT,
     "refinement": "unconditionally raises NameValidationError after init_base (rejects "
                   "EVERY name). Its faithful real patch raises ValueError on every name, "
                   "which FAILS every constructing P2P (`Blueprint(\"test\", __name__)` and "
                   "friends are used across the suite) — it would NOT resolve.",
     "rationale": "supporting near-miss with a real refinement. Rejection source: "
                  "`Exsures(NameValidationError, ... len==0 or contains_dot(...))` — an "
                  "accepted name (non-empty, dot-free) raises, but the Exsures reject "
                  "predicate is False there, so the raise is INADMISSIBLE. If it verified => "
                  "SPEC-TOO-WEAK (admits rejecting valid names)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real flask base initialiser callee)
# ===========================================================================
# Three @ContractOnly axioms for the unchanged base initialiser
# flask.scaffold.Scaffold.__init__ (invoked via super().__init__ at
# blueprints.py:185, BEFORE name validation):
#   base_init_can_complete(import_name) / base_init_can_fail(import_name) — two
#     @Pure ATTAINABILITY witnesses over the base callee's own argument. Neither is
#     the negation of the other: the real base init's outcome for one import_name
#     also turns on the ambient module table it may itself populate (helpers.py:572,
#     :590) and on the construction's optional root_path argument (scaffold.py:96),
#     so it is NOT a function of import_name alone.
#   init_base(import_name) — the sound contract, whose two exits each hand out
#     their OWN witness: Ensures(base_init_can_complete + Acc(list_pred,1/2)) on
#     normal completion, Exsures(BaseInitError, base_init_can_fail + Acc) on
#     failure-as-a-unit. It says NOTHING about `name`. The real base init reaches
#     get_root_path(import_name) -> pkgutil.get_loader(import_name), which RAISES on
#     an unresolvable dotted import_name (the path the OLD Ensures-only axiom
#     over-claimed away). Because each witness is obtainable ONLY from the exit that
#     produces it, a name rejection (which runs only after init_base RETURNED, so it
#     holds the success witness) cannot be routed through the BaseInitError channel
#     — the discrimination is by provenance, not by disjointness of the two facts.
#
# The probes EXECUTE the real callee (construct a real flask.Blueprint, holding
# the blueprint name at an ACCEPTED value so no name guard fires, fuzzing the
# import_name), mirroring axiom_check.py. They import ONLY `flask` + stdlib. The
# runner mounts only the probe script, so the oracle logic is embedded inline
# (not read from the bundle). Files opened in probes use encoding="utf-8" (none
# needed here — no file reads).

# (1) axiom-soundness — BOTH posts of init_base are REALISED by the real base
# initialiser: it RETURNS on a resolvable import_name (the Ensures post) and it
# RAISES on an unresolvable dotted import_name (the Exsures(BaseInitError) post).
# The weakened axiom permits BOTH outcomes for any Requires-satisfying
# import_name, so soundness is by construction; what we MUST establish is that the
# RAISE path is REACHABLE (otherwise the old no-raise over-claim would have been
# harmless and the Exsures would be dead). We assert >=1 in-domain import_name
# raises AND >=1 returns. A real base init that NEVER raised on any unresolvable
# dotted name would mean the OLD Ensures-only axiom was after all sound — but the
# panel CEs ('.', '..', 'no.such.package') show it is not. If NEITHER post is
# witnessed the axiom would be mis-specified.
_AX_INIT_BASE_SOUND = r'''
import sys
import flask

ACCEPTED_NAME = "ok"   # non-empty, dot-free -> never trips a name guard

def base_init_outcome(import_name):
    """Run the real base init over import_name (with an accepted blueprint name).
    Constructing flask.Blueprint runs super().__init__ -> Scaffold.__init__ ->
    (root_path is None at the call site) get_root_path(import_name) ->
    pkgutil.get_loader(import_name)."""
    try:
        flask.Blueprint(ACCEPTED_NAME, import_name)
        return ("return", None)
    except BaseException as exc:   # any failure of the base init as a unit
        return ("raise", repr(exc))

raising = [".", "..", "no.such.package",
           "definitely.not.a.real.module.xyzzy", "a.b.c.d.e",
           ".leading", "trailing.", "no_such_top_level_module_qwertyz"]
returning = [__name__, "flask", "os", "sys", "__main__"]

saw_raise = False
saw_return = False
raise_examples = []
for imp in raising:
    kind, info = base_init_outcome(imp)
    if kind == "raise":
        saw_raise = True
        if len(raise_examples) < 3:
            raise_examples.append((imp, info))
    else:
        saw_return = True
for imp in returning:
    kind, info = base_init_outcome(imp)
    if kind == "raise":
        saw_raise = True
    else:
        saw_return = True

# fuzz dotted / relative / nonsense import_names
import random
rng = random.Random(50140)
for _ in range(2000):
    nseg = rng.randint(0, 4)
    seg = ["".join(rng.choice(list("abcdefghxyz_")) for _ in range(rng.randint(0, 5)))
           for _ in range(nseg)]
    imp = ".".join(seg)
    kind, info = base_init_outcome(imp)
    if kind == "raise":
        saw_raise = True
    else:
        saw_return = True

if not saw_raise:
    print("AXIOM-UNDER-WITNESSED: the real base init never RAISED on any "
          "unresolvable dotted import_name; Exsures(BaseInitError) would be dead "
          "(but the panel CEs '.', '..', 'no.such.package' should raise)")
    sys.exit(1)
if not saw_return:
    print("AXIOM-UNDER-WITNESSED: the real base init never RETURNED on any "
          "resolvable import_name (e.g. __name__); Ensures path missing")
    sys.exit(1)

# NAME-INDEPENDENCE of the base-init outcome: the two witnesses are stated over
# the base callee's OWN argument and say nothing about `name`, which is sound only
# if the base init's outcome does not read the blueprint name (it is not even
# handed it). Same import_name must decide the same way for two different accepted
# names.
def base_init_outcome_named(name, import_name):
    try:
        flask.Blueprint(name, import_name)
        return "return"
    except ValueError:
        # a ValueError is a NAME-guard rejection (NameValidationError channel),
        # NOT a base-init failure; the base init itself completed. Sound because
        # the base step never raises ValueError: over ~4050 import_name shapes
        # (empty/dotted/relative/non-ASCII/absent/builtin + 4000 fuzz) its only
        # failure types are ImportError, RuntimeError and AttributeError.
        return "return"
    except BaseException:
        return "raise"

probe_imports = [".", "no.such.package", __name__, "os", "a.b.c.d.e",
                 "definitely.not.a.real.module.xyzzy"]
for imp in probe_imports:
    a = base_init_outcome_named("ok", imp)
    b = base_init_outcome_named("alsofine", imp)
    if a != b:
        print("AXIOM-UNSOUND: base init outcome DEPENDS on blueprint name for "
              "import_name %r (%r vs %r) — the witnesses are name-silent" % (imp, a, b))
        sys.exit(1)

# INDEPENDENCE of the two witnesses. The axiom deliberately does NOT claim the
# base-init outcome is a function of import_name: each exit hands out its own
# witness and neither is the negation of the other. That weaker claim is the
# faithful one ONLY IF the real base init can genuinely do EITHER for one and the
# same import_name — otherwise a single predicate of import_name would model it and
# the independence would be unmotivated. Two routes, both exercised:
#   (A) the construction's optional root_path argument — scaffold.py:96 consults
#       get_root_path ONLY when root_path is None, so an import_name that fails via
#       get_root_path completes when root_path is supplied. No fixture needed.
#   (B) the ambient module table — get_root_path consults sys.modules
#       (helpers.py:572) and itself populates it via __import__ (helpers.py:590):
#       for a namespace package whose __file__ is None the base init COMPLETES
#       while the package is absent from sys.modules (loader lookup falls back to
#       the cwd) and FAILS with RuntimeError once it is present.
def outcome_with_root_path(import_name, root_path):
    try:
        flask.Blueprint(ACCEPTED_NAME, import_name, root_path=root_path)
        return "return"
    except BaseException:
        return "raise"

both_channels = []
for imp in [".", "no.such.package", "definitely.not.a.real.module.xyzzy"]:
    if (base_init_outcome(imp)[0] == "raise"
            and outcome_with_root_path(imp, "/tmp") == "return"):
        both_channels.append(("root_path", imp))

# route (B): build a namespace package (a directory with no __init__.py) on
# sys.path and observe the flip across its import. A filesystem the runner will
# not let us write is not an axiom failure, so the fixture is best-effort; route
# (A) alone already carries the obligation.
try:
    import os
    import tempfile
    import importlib
    _tmp = tempfile.mkdtemp(prefix="axns5014_")
    os.makedirs(os.path.join(_tmp, "axns5014pkg"))
    with open(os.path.join(_tmp, "axns5014pkg", "leaf.py"), "w",
              encoding="utf-8") as _fh:
        _fh.write("X = 1\n")
    sys.path.insert(0, _tmp)
    _before = base_init_outcome("axns5014pkg")[0]
    importlib.import_module("axns5014pkg")
    _after = base_init_outcome("axns5014pkg")[0]
    if _before != _after:
        both_channels.append(("sys.modules", "axns5014pkg", _before, _after))
except OSError as _exc:
    print("note: namespace-package fixture unavailable (%r); relying on the "
          "root_path route" % (_exc,))

if not both_channels:
    print("AXIOM-MIS-SPECIFIED: no import_name was found on which the real base "
          "init both FAILS and COMPLETES, so the two independent witnesses are "
          "unmotivated — a single predicate of import_name would model the callee")
    sys.exit(1)

print("OK init_base soundness: both posts realised by the real base initialiser "
      "— RETURNS on resolvable import_name (Ensures) and RAISES on unresolvable "
      "dotted import_name (Exsures(BaseInitError)); the outcome is NAME-SILENT "
      "(same import_name decides the same way for two accepted names) and the two "
      "witnesses are INDEPENDENT, witnessed by import_names on which the real base "
      "init does BOTH: %r; raise examples: %r"
      % (both_channels, raise_examples))
sys.exit(0)
'''

# (2) axiom-soundness — NAME-INDEPENDENCE: init_base says NOTHING about `name`,
# so it must NOT itself validate or raise on the blueprint name. Hold import_name
# RESOLVABLE (__name__, so the base init returns) and vary the blueprint `name`
# over accepted (non-empty, dot-free) AND rejected (empty, dotted) values. Whether
# the overall Blueprint construction raises must be decided by the NAME guards in
# Blueprint.__init__, NOT by the base initialiser: with a resolvable import_name
# the base init completes for every name (its outcome is name-independent), and
# the accept/reject is then purely the name decision. If the base init's outcome
# DEPENDED on `name` (e.g. raised for a dotted name with a resolvable import_name
# in a way attributable to the base init), the axiom's name-silence would be
# unsound. We confirm name-independence: on a resolvable import_name the
# accept/reject of every name matches the model's name predicate (len==0 or dot).
_AX_INIT_BASE_NAME_INDEP = r'''
import sys
import flask

RESOLVABLE = __name__   # base init returns for this import_name

def model_rejects(name):
    return len(name) == 0 or ("." in name)

def constructs(name):
    try:
        flask.Blueprint(name, RESOLVABLE)
        return True
    except ValueError:
        return False
    except BaseException as exc:
        # On a RESOLVABLE import_name the base init returns; any non-ValueError
        # failure attributable to `name` would contradict name-independence.
        print("AXIOM-UNSOUND: base init / construction raised a non-ValueError on "
              "name=%r with a resolvable import_name (%r) — name-silence violated" %
              (name, exc))
        sys.exit(1)

# Detect the mounted tree (post-patch rejects '', base_commit accepts '').
empty_rejected = not constructs("")

names_nonempty_accept = ["a", "ok", "test", "my_blueprint", "admin-panel",
                         "0", " ", "a b c", "ünïcоde"]
names_dot_reject = [".", "a.b", "app.ui", ".leading", "trailing.", "x.y.z"]

for nm in names_nonempty_accept:
    if not constructs(nm):
        print("AXIOM/DECISION mismatch: accepted name %r did not construct on a "
              "resolvable import_name" % (nm,)); sys.exit(1)
for nm in names_dot_reject:
    if constructs(nm):
        print("AXIOM/DECISION mismatch: dotted name %r constructed on a resolvable "
              "import_name (dot guard / name-independence broken)" % (nm,)); sys.exit(1)

# the empty name: tree-dependent (post-patch rejects, base_commit accepts).
if empty_rejected:
    print("tree=post-patch: empty name rejected (F2P test_empty_name_not_allowed)")
else:
    print("tree=base_commit: empty name accepted (empty guard absent)")

# name-independence holds for the non-empty (tree-independent) decisions: the
# base init returned for a resolvable import_name regardless of `name`, and the
# accept/reject was the NAME decision alone.
print("OK init_base name-independence: with a resolvable import_name the base "
      "init returns for every name; accept/reject is the name guard alone (no "
      "base-init dependence on `name`), matching the model predicate len==0 or dot")
sys.exit(0)
'''

# (3) axiom-containment — every callee-input the MODEL can reach lies in the
# init_base axiom's Requires domain. init_base's Requires is only
# Acc(list_pred(import_name),1/2): ANY import_name list with that permission. The
# model passes its own `import_name` argument straight through (no value
# restriction beyond list_pred), so EVERY import_name the model can hold is in the
# axiom domain. The real callee `super().__init__`/`Scaffold.__init__` accepts ANY
# import_name string as its argument (it never rejects an import_name as a TYPE
# error; it may RAISE later in get_root_path, which the axiom's Exsures covers).
# We assert the real base init ACCEPTS (as an argument — does not TypeError/refuse
# the call) every shape of import_name the model can reach: empty, single-char,
# dotted, relative, non-ASCII; the only outcomes are return or BaseInitError (both
# in-axiom). A model-reachable import_name the callee refused to even accept would
# be AXIOM-TOO-WEAK-FOR-CALLER.
_AX_CONTAINMENT = r'''
import sys
import flask

ACCEPTED_NAME = "ok"

def call_outcome(import_name):
    """Return ('ok', kind) where kind in {return, BaseInitError-ish} if the call
    was ACCEPTED as an argument; only an argument-level refusal (the callee
    rejecting the import_name shape outright, e.g. TypeError on the wrong type)
    is a containment failure. A later in-body raise (ImportError/RuntimeError) is
    the axiom's Exsures(BaseInitError) and is IN-domain."""
    try:
        flask.Blueprint(ACCEPTED_NAME, import_name)
        return ("return", None)
    except (ImportError, RuntimeError, ModuleNotFoundError, ValueError) as exc:
        # in-axiom: base-init failure-as-a-unit (BaseInitError) — still a
        # callee-accepted import_name that merely failed downstream.
        return ("raise-in-domain", repr(exc))
    except TypeError as exc:
        # the callee REFUSED the import_name shape as an argument -> out-of-domain.
        return ("refused", repr(exc))
    except BaseException as exc:
        # treat any other failure as a downstream in-domain failure-as-a-unit.
        return ("raise-in-domain", repr(exc))

# every shape of import_name the model can reach (List[int] of code points).
reachable = [
    "",                  # empty import_name
    "a",                 # single char
    "os",                # resolvable
    __name__,            # resolvable
    ".",                 # relative / unresolvable dotted
    "a.b",               # dotted
    "no.such.package",   # unresolvable dotted
    "ünïcоde",           # non-ASCII
    "with space",        # space
    "0",                 # digit
]
refused = []
for imp in reachable:
    kind, info = call_outcome(imp)
    if kind == "refused":
        refused.append((imp, info))

if refused:
    print("AXIOM-TOO-WEAK-FOR-CALLER: the base init REFUSED a model-reachable "
          "import_name shape outright (argument-level): %r" % (refused,))
    sys.exit(1)
print("containment OK: the base init ACCEPTS every model-reachable import_name "
      "shape (empty/single/dotted/relative/non-ASCII/space/digit) as an argument; "
      "outcomes are only return (Ensures) or a downstream failure-as-a-unit "
      "(Exsures(BaseInitError)) — both in the axiom's Requires domain "
      "(Acc(list_pred(import_name),1/2)). No caller-reachable input lies outside.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-init-base-sound", "axiom": "init_base", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_INIT_BASE_SOUND,
     "rationale": "init_base gives TWO posts, each handing out its OWN witness: "
                  "Ensures(base_init_can_complete) on normal return, "
                  "Exsures(BaseInitError, base_init_can_fail) on failure-as-a-unit. The "
                  "obligations: (i) the RAISE path is REACHABLE on a real unresolvable dotted "
                  "import_name and the RETURN path on a resolvable one (>=1 each over the "
                  "panel CEs '.', 'no.such.package' + __name__ + 2000 fuzz import_names); "
                  "(ii) the outcome is NAME-SILENT (same import_name decides the same way for "
                  "two accepted names), which is what lets both witnesses be stated over "
                  "import_name alone; and (iii) the two witnesses are INDEPENDENT — the real "
                  "base init both FAILS and COMPLETES on one and the same import_name, via the "
                  "optional root_path argument (scaffold.py:96) and via the ambient module "
                  "table it itself populates (helpers.py:572/:590). (iii) is what forbids "
                  "modelling the callee with a single predicate of its argument. Mirrors "
                  "axiom_check.py obligation (A)."},
    {"id": "ax-init-base-name-indep", "axiom": "init_base", "kind": "axiom-soundness",
     "expect": "holds", "apply_gold": True, "probe": _AX_INIT_BASE_NAME_INDEP,
     "rationale": "init_base's contract says NOTHING about `name`; it must not validate or "
                  "raise on the blueprint name itself. With a RESOLVABLE import_name (base "
                  "init returns) the accept/reject of every name must be the NAME guard "
                  "alone (matching len==0 or dot), with no base-init dependence on `name`. "
                  "Any non-ValueError failure attributable to `name` on a resolvable "
                  "import_name => AXIOM-UNSOUND (name-silence violated). Tree-aware on the "
                  "empty name (post-patch rejects, base_commit accepts). Mirrors "
                  "axiom_check.py obligation (B)."},
    {"id": "ax-init-base-containment", "axiom": "init_base", "kind": "axiom-containment",
     "expect": "covered", "apply_gold": True, "probe": _AX_CONTAINMENT,
     "rationale": "every callee-input the model can reach (its own import_name, any "
                  "List[int] with Acc(list_pred,1/2)) lies in the axiom's Requires domain: "
                  "the real base init accepts ANY import_name string as its argument "
                  "(empty/single/dotted/relative/non-ASCII/space/digit) — the only outcomes "
                  "are return (Ensures) or a downstream failure-as-a-unit "
                  "(Exsures(BaseInitError)), both in-domain. A model-reachable import_name "
                  "the callee refused at the argument level would be "
                  "AXIOM-TOO-WEAK-FOR-CALLER; here the domain is total."},
]
