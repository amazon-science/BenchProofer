# properties.py — PBT falsification battery for django__django-16255.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions + signatures untouched) and swaps
# ONLY text inside the # impl-start/# impl-end region (which here also contains
# the loop invariants — markers.spec_view elides the whole impl region including
# nested invariants, so editing invariants does NOT change the spec signature).
# The runner checks each with Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + instance.json):
#   latest_stamp(stamps: List[int]) -> Optional[int]
#   reports the latest per-entry modification stamp across a section's entries
#   (a DEEP model of `max([self.lastmod(item) for item in self.items()],
#   default=None)` at django/contrib/sitemaps/__init__.py:170). `stamps` is held
#   at HALF permission: Requires(Acc(list_pred(stamps), 1/2)) -> READ-ONLY input.
#   Four load-bearing postcondition clauses pin the output:
#     (1) Implies(len==0, Result() is None)              empty section -> absent marker
#     (2) Implies(len>0,  Result() is not None)          non-empty -> a real stamp
#     (3) Implies(len>0,  Exists k: Result()==stamps[k]) the result is a MEMBER
#     (4) Forall k: stamps[k] <= Result()  (with not-None) the result DOMINATES all
#   The oracle is GROUNDED directly in the input (stamps[k], len(stamps)); there
#   is NO @Pure answer-key / @ContractOnly axiom to echo (axioms region empty,
#   meta.axioms == [], deep_model_references is a single A-reference == max builtin
#   validated out-of-band by axiom_check.py / G-AX). See 'assessment' re ungrounded
#   -oracle echo (N/A) — replaced by an honest cheapest-impl positive control.
#
# F2P: test_callable_sitemod_no_items — a section with items()==[] must emit NO
#      Last-Modified header (get_latest_lastmod()==None) instead of raising
#      ValueError. This is exactly clause (1).
# Key P2P: "The Last-Modified header is set to the most recent sitemap lastmod"
#      (the MAXIMUM/dominance+membership clauses on a non-empty section).

from pathlib import Path

INSTANCE = "django__django-16255"
FLOAT_ENCODING = None  # meta.json float_encoding == null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen GOLD impl region (model.py lines 60-78, between # impl-start and
# # impl-end). Every rival edits ONLY inside this block. The loop invariants are
# part of the elided impl region, so reshaping them does not change the spec.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    result = None  # type: Optional[int]
    i = 0
    while i < len(stamps):
        # invariants-start
        Invariant(Acc(list_pred(stamps), 1 / 2))
        Invariant(0 <= i and i <= len(stamps))
        Invariant((i == 0) == (result is None))
        Invariant(Implies(
            result is not None,
            Exists(int, lambda k: 0 <= k and k < i and result == stamps[k])))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (result is not None) and stamps[k] <= result)))
        Invariant(MustTerminate(len(stamps) - i + 1))
        # invariants-end
        v = stamps[i]
        if result is None or v > result:
            result = v
        i = i + 1
    return result"""


# === POSITIVE CONTROL (soundness, expect=verify) ==========================
# Local-variable reshape: keep the forward sweep and EVERY gold invariant
# verbatim; only hoist the update test into a boolean local and write the
# comparison as `result < v` (equivalent to `v > result`). This is a
# directive-3-safe reshape (no loop-direction flip, no forward-append against a
# front-recursive fold), so the gold proof obligations still discharge. If a
# faithful correct impl of this shape cannot verify -> SPEC-TOO-STRONG.
_POS_IMPL = """    result = None  # type: Optional[int]
    i = 0
    while i < len(stamps):
        # invariants-start
        Invariant(Acc(list_pred(stamps), 1 / 2))
        Invariant(0 <= i and i <= len(stamps))
        Invariant((i == 0) == (result is None))
        Invariant(Implies(
            result is not None,
            Exists(int, lambda k: 0 <= k and k < i and result == stamps[k])))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (result is not None) and stamps[k] <= result)))
        Invariant(MustTerminate(len(stamps) - i + 1))
        # invariants-end
        v = stamps[i]
        bigger = result is None or result < v
        if bigger:
            result = v
        i = i + 1
    return result"""
POS_RESHAPE = _swap(_BASE, _GOLD_IMPL, _POS_IMPL)


# === ADMISSIBILITY (expect=verify) ========================================
# A separate top-level caller would break same_spec (spec_view only elides the
# impl region — module-level additions enter the spec signature), and a
# self-recursive call would need a Decreases measure the spec doesn't carry
# (proof gap, not spec defect). So the admissibility check lives INSIDE the impl
# region, at the very top: construct a concrete F2P-shaped non-empty stamp list
# and assert the Requires predicate (list_pred) is establishable on it. The gold
# obligations follow verbatim afterwards. If this block cannot verify, the
# precondition is unsatisfiable for a normal input -> PRECOND-TOO-STRONG.
_ADMISS_IMPL = """    # ADMISSIBILITY PROBE: a representative F2P/P2P-shaped section stamp list
    # (non-empty comparable stamps) establishes the Requires predicate.
    probe = [1, 2, 3]  # type: List[int]
    Assert(list_pred(probe))
    Assert(len(probe) == 3)
    result = None  # type: Optional[int]"""
ADMISS = _swap(_BASE, "    result = None  # type: Optional[int]", _ADMISS_IMPL)


# === FRAME-MUTATION (uniqueness, expect=reject for INSUFFICIENT PERMISSION)
# MANDATORY: `stamps` is read-only (Acc(list_pred(stamps), 1/2)). This rival
# computes the SAME correct running maximum but, plausibly "normalising" the
# section, writes the running max back into the list (stamps[i] = result). Every
# gold invariant is kept verbatim so the rejection is attributable to the WRITE,
# not to a broken value claim: with only half permission, `stamps[i] = result`
# cannot be framed -> the verifier rejects for INSUFFICIENT PERMISSION.
# refinement: the real get_latest_lastmod is a read-only reduction over the
# comprehension; a faithful patch that MUTATED self.items()/the per-entry stamp
# list (e.g. clamping each entry's lastmod to the running max) would corrupt the
# section's per-URL <lastmod> values that the sitemap then renders — the P2P
# tests that assert the exact rendered sitemap XML ("A simple sitemap section can
# be rendered", "Last-Modified header is set correctly") read those per-entry
# stamps back and would FAIL; it would NOT resolve.
# rejection source: the permission system (Acc(...,1/2) grants no write capability).
_FRAME_IMPL = _GOLD_IMPL.replace(
    """        v = stamps[i]
        if result is None or v > result:
            result = v
        i = i + 1""",
    """        v = stamps[i]
        if result is None or v > result:
            result = v
        # FRAME-MUTATION RIVAL: write the running max back into the read-only
        # input. stamps is held at half permission, so this assignment cannot be
        # framed and must be rejected for INSUFFICIENT PERMISSION.
        stamps[i] = result
        i = i + 1""",
)
FRAME_WRITE = _swap(_BASE, _GOLD_IMPL, _FRAME_IMPL)


# === UNIQUENESS / PARTIAL-DOMAIN reject rivals ============================

# --- W1 empty-section break (the PRE-PATCH bug, the very thing the patch fixes).
# Seed the accumulator with a concrete stamp (0) and never fall back to the
# absent marker, so an EMPTY section reports 0 instead of None. Correct on every
# non-empty section (still the true maximum); diverges ONLY on the empty
# sub-domain. This is exactly model_prepatch.py's shape.
# refinement: the faithful pre-patch code is `max([...])` with NO default, which
# RAISES ValueError on an empty section (real images, Python max([])). The F2P
# test_callable_sitemod_no_items asserts the empty section emits NO Last-Modified
# header (a clean None), not a 500/ValueError — the pre-patch FAILS it and does
# NOT resolve. (This also covers the control-flow-effect channel: in reality the
# empty path RAISES; the value abstraction captures it as "concrete vs None".)
# rejection source: postcondition clause (1) Implies(len(stamps)==0, Result() is None).
_W1_IMPL = """    result = 0  # type: Optional[int]
    seen = False
    i = 0
    while i < len(stamps):
        # invariants-start
        Invariant(Acc(list_pred(stamps), 1 / 2))
        Invariant(0 <= i and i <= len(stamps))
        Invariant(seen == (i > 0))
        Invariant(result is not None)
        Invariant(Implies(
            seen,
            Exists(int, lambda k: 0 <= k and k < i and result == stamps[k])))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (result is not None) and stamps[k] <= result)))
        Invariant(MustTerminate(len(stamps) - i + 1))
        # invariants-end
        v = stamps[i]
        if not seen or v > result:
            result = v
        seen = True
        i = i + 1
    return result"""
W1_EMPTY_CONCRETE = _swap(_BASE, _GOLD_IMPL, _W1_IMPL)


# --- W2 partial-domain: SKIP THE FIRST element (start the sweep at i=1, seeding
# result with None so an empty section still reports None — keeps clause (1)).
# Correct whenever stamps[0] is not the unique maximum; WRONG when the latest
# stamp is the first entry (then the reported value omits / under-reports it).
# refinement: a real `max(values[1:], default=None)` (an off-by-one slice of the
# comprehension) would, for a section whose only or whose latest entry is the
# first one, report an older stamp (or None for a singleton section) — the P2P
# "Last-Modified header is set to the most recent sitemap lastmod" asserts the
# EXACT latest value and would FAIL; it would NOT resolve.
# rejection source: clause (4) dominance Forall k: stamps[k] <= Result() (k==0 is
# unbounded) and, for a singleton, clause (2) non-empty -> not None.
_W2_IMPL = """    result = None  # type: Optional[int]
    i = 1
    while i < len(stamps):
        # invariants-start
        Invariant(Acc(list_pred(stamps), 1 / 2))
        Invariant(1 <= i and i <= len(stamps))
        Invariant((i <= 1) == (result is None))
        Invariant(Implies(
            result is not None,
            Exists(int, lambda k: 1 <= k and k < i and result == stamps[k])))
        Invariant(Forall(int, lambda k: Implies(
            1 <= k and k < i,
            (result is not None) and stamps[k] <= result)))
        Invariant(MustTerminate(len(stamps) - i + 1))
        # invariants-end
        v = stamps[i]
        if result is None or v > result:
            result = v
        i = i + 1
    return result"""
W2_SKIP_FIRST = _swap(_BASE, _GOLD_IMPL, _W2_IMPL)


# --- W3 ungrounded-dominator: return a value that DOMINATES every stamp but is
# NOT a member (result + 1 on the non-empty path). Correct on the empty section
# (None) and satisfies dominance; violates MEMBERSHIP.
# refinement: a real reduction returning `max(values) + timedelta(days=1)` (or
# any synthesised stamp strictly newer than every entry) would emit a
# Last-Modified header LATER than any real entry's lastmod — the P2P
# "Last-Modified header is set to the most recent sitemap lastmod" / "set
# correctly" assert the exact (real, member) stamp and would FAIL; NOT resolve.
# rejection source: clause (3) Exists k: Result()==stamps[k] (membership).
_W3_IMPL = _GOLD_IMPL.replace(
    """        i = i + 1
    return result""",
    """        i = i + 1
    # UNGROUNDED-DOMINATOR RIVAL: report a value strictly newer than every
    # collected stamp. It dominates all entries but is not one of them.
    if result is not None:
        result = result + 1
    return result""",
)
W3_NONMEMBER_DOMINATOR = _swap(_BASE, _GOLD_IMPL, _W3_IMPL)


# --- W4 member-but-not-max: report the FIRST collected stamp (a genuine member)
# instead of the greatest. Correct on the empty section (None) and on singletons,
# and is always a member; violates DOMINANCE whenever a later entry is newer.
# refinement: a real reduction using `values[0]` / `min(values, default=None)`
# would report an OLDER stamp than the section's latest entry — the P2P
# "Last-Modified is set to the most recent sitemap lastmod" asserts the MAXIMUM
# and would FAIL; it would NOT resolve.
# rejection source: clause (4) dominance Forall k: stamps[k] <= Result().
_W4_IMPL = """    result = None  # type: Optional[int]
    if len(stamps) > 0:
        result = stamps[0]
    return result"""
W4_FIRST_MEMBER = _swap(_BASE, _GOLD_IMPL, _W4_IMPL)


SPEC_TESTS = [
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_RESHAPE,
        "rationale": "structurally-different CORRECT impl (running max via a "
        "hoisted boolean local, comparison written `result < v`) keeping every "
        "gold invariant verbatim — a directive-3-safe local-variable reshape that "
        "must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-nonempty",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control probe builds an F2P/P2P-shaped non-empty "
        "stamp list [1,2,3] and asserts the Requires predicate list_pred holds on "
        "it before the gold obligations run — Requires(Acc(list_pred(stamps),1/2)) "
        "must admit a normal section, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_WRITE,
        "refinement": "the real get_latest_lastmod is a read-only reduction over "
        "the lastmod comprehension; a faithful patch that mutated the per-entry "
        "stamp list (e.g. clamping each entry to the running max) would corrupt "
        "the per-URL <lastmod> values the sitemap renders — P2P tests asserting "
        "the exact rendered sitemap XML / 'Last-Modified header is set correctly' "
        "read those stamps back and would FAIL; it would NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: stamps is held at "
        "Acc(list_pred(stamps),1/2) (read-only), so the write `stamps[i]=result` "
        "cannot be framed -> INSUFFICIENT PERMISSION. Gold invariants kept "
        "verbatim so the rejection is attributable to the write (frame-mutation, "
        "the #1 weakness class).",
    },
    {
        "id": "w1-empty-concrete",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W1_EMPTY_CONCRETE,
        "refinement": "this is the PRE-PATCH shape (running max with no absent "
        "marker == `max([...])` with no default), which RAISES ValueError on an "
        "empty section. The F2P test_callable_sitemod_no_items asserts an empty "
        "section emits NO Last-Modified header (a clean None), not a ValueError — "
        "the pre-patch FAILS it and does NOT resolve (it is the very bug fixed).",
        "rationale": "rejected by postcondition clause (1) Implies(len(stamps)==0, "
        "Result() is None). Partial-domain (diverges only on the empty section) "
        "and also the control-flow-effect channel (real empty path RAISES; the "
        "value abstraction captures it as concrete-vs-None).",
    },
    {
        "id": "w2-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W2_SKIP_FIRST,
        "refinement": "a real `max(values[1:], default=None)` (an off-by-one slice "
        "of the comprehension) reports an older stamp — or None for a singleton "
        "section — whenever the latest/only entry is the first one. The P2P "
        "'Last-Modified header is set to the most recent sitemap lastmod' asserts "
        "the EXACT latest value and would FAIL; it would NOT resolve.",
        "rationale": "rejected by clause (4) dominance Forall k: stamps[k] <= "
        "Result() (k==0 is unbounded by the i=1 start) and, for a singleton, "
        "clause (2) non-empty -> Result() is not None. Partial-domain (first "
        "element / singleton sub-domain).",
    },
    {
        "id": "w3-nonmember-dominator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W3_NONMEMBER_DOMINATOR,
        "refinement": "a real reduction returning `max(values)+timedelta(days=1)` "
        "(or any synthesised stamp strictly newer than every entry) emits a "
        "Last-Modified LATER than any real entry — the P2P 'Last-Modified header "
        "is set to the most recent sitemap lastmod' / 'set correctly' assert the "
        "exact real (member) stamp and would FAIL; it would NOT resolve.",
        "rationale": "rejected by clause (3) Exists k: Result()==stamps[k] "
        "(membership): a strictly-greater synthetic value is not one of the "
        "collected stamps.",
    },
    {
        "id": "w4-first-member",
        "kind": "uniqueness",
        "expect": "reject",
        "module": W4_FIRST_MEMBER,
        "refinement": "a real reduction using `values[0]` / `min(values, "
        "default=None)` reports an OLDER stamp than the section's latest entry. "
        "The P2P 'Last-Modified is set to the most recent sitemap lastmod' asserts "
        "the MAXIMUM and would FAIL; it would NOT resolve.",
        "rationale": "rejected by clause (4) dominance Forall k: stamps[k] <= "
        "Result(): the first collected stamp is a genuine member but need not "
        "dominate a later, newer entry. Partial-domain (correct on empty + "
        "singletons + already-sorted-descending sections).",
    },
]


# No @ContractOnly axioms and no A-reference deep models that the AXIOM lane
# checks at runtime: model.py's axioms region is empty (meta.axioms == []) and
# the single A-reference (latest_stamp == max(values, default=None)) is validated
# out-of-band by axiom_check.py / G-AX, not via a @ContractOnly the proof
# consumes. Nothing for the Docker axiom lane to run here.
AXIOM_TESTS = []
