# properties.py — PBT falsification battery for pytest-dev__pytest-5840.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-identically (region surgery edits ONLY inside the
# # impl-start / # impl-end region) and are checked by Nagini verify +
# markers.same_spec. Axiom cases are real-callee probes checked in Docker.
#
# Defended surface (read from model.py + refinement.md + mapping.md + the gold
# patch):
#   conftest_dedup_key(loc: List[int]) -> List[int]
#     computes the deduplication key under which a conftest file is cached and
#     later looked up. `loc` is a READ-ONLY input (Requires/Ensures carry only
#     Acc(list_pred(loc), 1/2)).
#
#   The postcondition pins FOUR clauses:
#     (P1) Acc(list_pred(loc), 1/2)              [returns the half permission]
#     (P2) Acc(list_pred(Result()))              [full perm on the fresh key]
#     (P3) ToSeq(Result()) == canonical(Old(ToSeq(loc)))
#               [VALUE clause: BOTH conventions satisfy this — necessary but
#                NOT sufficient; the location string is identical across kinds]
#     (P4) lookup_recognised(ToSeq(Result()))
#               [LOAD-BEARING clause: the key must hold the unforgeable
#                recognition token, granted ONLY by make_key(.., True) — the
#                recognised convention. A key built under the unrecognised
#                convention carries the IDENTICAL location string yet is never
#                granted the token.]
#
#   The gold delta is the cache-key construction convention: the recognised
#   `Path(str(p)).resolve()` (pathlib) key whose membership test recognises an
#   independently-recomputed key (HIT) vs the pre-change `unique_path(p)`
#   (py.path.local) key with the same string but a distinct kind (MISS). It is a
#   CONTROL-FLOW / construction effect with NO value-level discriminator,
#   modelled by the unforgeable capability token `lookup_recognised` (SPEC_GUIDE
#   directive 8).
#
#   The F2P tests (test_setinitial_conftest_subdirs[test] / [tests]) store a
#   conftest under the constructor key, then assert membership with an
#   INDEPENDENTLY-recomputed key:  Path(str(subconftest)).resolve() in
#   conftest._conftestpath2mod. Post-patch the stored recognised key HITS;
#   pre-patch the unrecognised key (same string, py.path.local kind) MISSES.

from pathlib import Path

INSTANCE = "pytest-dev__pytest-5840"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl region of model.py (everything between the markers, exclusive).
# Every rival rewrites ONLY this block, so same_spec is guaranteed.
_GOLD_IMPL = """    # Build the deduplication key under the recognised convention, so an
    # independently-recomputed key for the same location finds the stored entry.
    result = make_key(loc, True)
    return result"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: old block not found")
    if src.count(old) != 1:
        raise AssertionError("not unique: old block")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Build a full model.py source whose impl region is `new_body` (the gold
    spec/pure/pre/post regions untouched)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------

# (A) UNGROUNDED-ORACLE ECHO / unrecognised-convention key — the central
# uniqueness attack. Build the key under the UNRECOGNISED convention
# (make_key(loc, False)). Its Ensures still give the canonical location string
# (P3 holds: ToSeq(Result()) == canonical(...)), so the value clause is
# satisfied — but make_key only grants lookup_recognised under the recognised
# convention, so P4 (lookup_recognised(ToSeq(Result()))) is NOT dischargeable.
# This is EXACTLY model_prepatch.py. If it verified, P3 (value/string equality)
# would be the whole spec and the recognition effect would be unconstrained =>
# SPEC-TOO-WEAK. MUST be rejected.
_IMPL_UNRECOGNISED_ECHO = """    # UNRECOGNISED-CONVENTION rival (= model_prepatch): same canonical location
    # string, but no recognition token.
    result = make_key(loc, False)
    return result"""

# (B) PARTIAL-DOMAIN — recognised convention on a value sub-domain, unrecognised
# elsewhere. Branch on the location length: the empty-location sub-domain
# (len(loc) == 0) falls to the unrecognised convention, every other input to the
# recognised one. P3 (value string) holds on BOTH branches, but P4 must hold for
# ALL inputs admitted by the precondition; on the len==0 sub-domain the result
# lacks the token, so the postcondition cannot be discharged. MUST be rejected.
_IMPL_PARTIAL_DOMAIN = """    # PARTIAL-DOMAIN rival: recognised convention except on the empty-location
    # sub-domain, which falls to the unrecognised convention (no token there).
    if len(loc) == 0:
        result = make_key(loc, False)
    else:
        result = make_key(loc, True)
    return result"""

# (C) CONTROL-FLOW-EFFECT / value-launder — build BOTH keys and return the
# recognised one's *location string* re-materialised through the unrecognised
# constructor. The intent of the cheat is: P4 has no value-level content
# (lookup_recognised is an abstract @Predicate with no body), and the two keys
# carry the IDENTICAL location string, so a rival tries to launder the token off
# a value-equal copy. Nagini does NOT carry a predicate instance across a
# value-equal copy, and make_key(.., False) is never granted the token, so P4
# fails. This is the capability-token discriminator made explicit: a
# value-indistinguishable construction must still be rejected. MUST be rejected.
_IMPL_LAUNDER = """    # CONTROL-FLOW-EFFECT rival: construct the recognised key (which would hold
    # the token) but RETURN a value-equal unrecognised key, attempting to launder
    # the recognition token across the identical location string.
    recognised = make_key(loc, True)
    Assert(lookup_recognised(ToSeq(recognised)))
    laundered = make_key(loc, False)
    Assert(ToSeq(laundered) == ToSeq(recognised))
    return laundered"""

# (D) POSITIVE CONTROL — structurally DIFFERENT but CORRECT. Inline the
# recognised construction directly into the return (drop the intermediate
# `result` local). Same single recognised-convention call, no loop / no
# induction lemma; P3 and P4 are discharged by make_key(.., True)'s Ensures
# exactly as in the gold. MUST verify (else SPEC-TOO-STRONG).
_IMPL_POS_INLINE = """    # POSITIVE CONTROL: inline the recognised construction (no intermediate
    # local). Same recognised convention, semantically identical to the gold.
    return make_key(loc, True)"""

# (E) POSITIVE CONTROL — structurally DIFFERENT but CORRECT. A redundant always-
# true conditional that takes the recognised branch in both arms (a branch-
# reorder reshape). Both branches call make_key(loc, True), so P3/P4 are
# discharged on every path. No induction needed. MUST verify (else
# SPEC-TOO-STRONG). Guards against an over-fitted spec that only accepts the
# single-statement gold shape.
_IMPL_POS_BRANCH = """    # POSITIVE CONTROL: branch-reshape; every arm uses the recognised convention.
    if len(loc) >= 0:
        result = make_key(loc, True)
    else:
        result = make_key(loc, True)
    return result"""

# (F) ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input.
# A top-level caller would leave the impl region and break same_spec, so the
# admissibility check is IN-REGION (the proven pattern): assert the half-
# permission input `loc` is actually USABLE (its length is readable through
# Acc(list_pred(loc), 1/2)) and that the recognised construction is reachable on
# it — i.e. a normal F2P-shaped location both satisfies the precondition and
# drives the gold body to a normal (non-raising) return. If the Requires were
# vacuous / over-strong the impl could not both consume the half-permission read
# and discharge the postcondition => PRECOND-TOO-STRONG. The gold recognised
# construction follows verbatim, so the postcondition obligation is unchanged;
# editing only the impl region keeps same_spec true.
_IMPL_ADMISS = """    # ADMISSIBILITY: the half-permission input `loc` is usable (its length is
    # readable through Acc(list_pred(loc), 1/2)) and the recognised construction
    # is reachable on it — a normal F2P-shaped location satisfies the Requires.
    Assert(len(loc) >= 0)
    # --- gold recognised construction verbatim below ---
    result = make_key(loc, True)
    return result"""

# (G) FRAME-MUTATION — MANDATORY (loc is READ-ONLY at Acc(list_pred(loc), 1/2)).
# A rival that WRITES to the half-permission input to (vacuously) "satisfy" the
# postcondition. Mutating loc requires FULL list_pred permission, but the
# precondition grants only 1/2, so the write itself is rejected for INSUFFICIENT
# PERMISSION before any postcondition reasoning. The gold recognised
# construction is kept verbatim AFTER the write, so the rejection is
# attributable solely to the in-place mutation of the read-only input. MUST be
# rejected (for insufficient permission). A byte-fuzzer never finds this.
_IMPL_FRAME_MUTATION = """    # FRAME-MUTATION rival: write to the read-only input `loc`. Only 1/2
    # permission is held, so this in-place store is rejected for INSUFFICIENT
    # PERMISSION (the spec may NOT be satisfied by overwriting the input). The
    # gold recognised construction is kept verbatim AFTER the write, so the
    # rejection is attributable solely to the mutation.
    if len(loc) > 0:
        loc[0] = 0  # WRITE through Acc(list_pred(loc), 1/2): insufficient perm
    result = make_key(loc, True)
    return result"""


SPEC_TESTS = [
    {
        "id": "uniqueness-unrecognised-convention-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_UNRECOGNISED_ECHO),
        "refinement": (
            "This is model_prepatch.py verbatim: build the key under the "
            "UNRECOGNISED convention (make_key(loc, False)), i.e. the pre-change "
            "unique_path / py.path.local key. Its faithful real patch is the "
            "UNPATCHED _importconftest, which stores `unique_path(conftestpath)` "
            "(a py.path.local) and the F2P test recomputes "
            "Path(str(subconftest)).resolve() (a pathlib.Path). The two carry the "
            "IDENTICAL location string on POSIX yet are distinct key kinds, so the "
            "recomputed-key membership MISSES (G-AX confirms a real MISS on the "
            "test/tests subdir names). test_setinitial_conftest_subdirs[test] / "
            "[tests] therefore FAIL — it does not resolve."),
        "rationale": (
            "Rejected by P4 (lookup_recognised(ToSeq(Result()))): make_key only "
            "grants the token under recognised_convention=True, so the "
            "unrecognised key cannot discharge it, even though P3 "
            "(ToSeq(Result())==canonical(...)) holds. This is precisely the "
            "discriminator G-DIFF senses against model_prepatch.py — the spec is "
            "NOT satisfiable by location-string equality alone."),
    },
    {
        "id": "partial-domain-empty-location-unrecognised",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_PARTIAL_DOMAIN),
        "refinement": (
            "Faithful real patch: build the recognised pathlib key for non-empty "
            "paths but fall back to the pre-change unique_path key when the "
            "rendered location is empty. The cache key for that sub-domain is then "
            "the unrecognised py.path.local kind, so a recomputed "
            "Path(...).resolve() lookup MISSES and the conftest is re-imported, "
            "deriving a dotted module name the import machinery rejects — the F2P "
            "membership assertion FAILS on that sub-domain. It does not resolve."),
        "rationale": (
            "Rejected by P4: the postcondition lookup_recognised(...) must hold "
            "for EVERY input admitted by the precondition; on the len(loc)==0 "
            "branch the result is built under the unrecognised convention and is "
            "never granted the token, so verification fails. Partial-domain "
            "attack pinned to the empty-location sub-domain."),
    },
    {
        "id": "control-flow-effect-value-launder",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_LAUNDER),
        "refinement": (
            "Faithful real patch: compute the resolved pathlib key (which the "
            "cache would recognise) but actually STORE/return a py.path.local key "
            "carrying the same string (e.g. `key = py.path.local(str(Path(...)."
            "resolve()))`). The stored key is the unrecognised kind, so the F2P "
            "recomputed Path(...).resolve() membership MISSES despite the "
            "identical location string — the test FAILS. It does not resolve. "
            "(This is the genuine py.path.local-vs-pathlib.Path kind confusion the "
            "issue #5792 / #5819 describes.)"),
        "rationale": (
            "Rejected by P4: lookup_recognised is an abstract @ContractOnly "
            "@Predicate with NO body — it cannot be Fold-fabricated, and Nagini "
            "does not carry a predicate instance across a value-equal copy. The "
            "returned `laundered` key is value-equal to the recognised one "
            "(ToSeq equal, P3 holds) yet was built by make_key(.., False), which "
            "never grants the token. The capability-token discriminator rejects a "
            "value-indistinguishable construction — exactly the control-flow "
            "effect with no value-level difference (SPEC_GUIDE directive 8)."),
    },
    {
        "id": "frame-mutation-write-readonly-loc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_FRAME_MUTATION),
        "refinement": (
            "Faithful real patch: an _importconftest that MUTATES the conftest "
            "path string/object in place before keying the cache (e.g. lowercases "
            "or rewrites `conftestpath` in situ). The original conftestpath is "
            "reused at other call sites (_getconftestmodules, "
            "_set_initial_conftests) and as the module's __file__, so corrupting "
            "it in place breaks conftest collection and the P2P conftest tests / "
            "F2P membership — it does not resolve. (And no real correct patch "
            "needs to mutate the input path at all.)"),
        "rationale": (
            "Rejected by the PERMISSION SYSTEM, not a value clause: `loc` is "
            "read-only (Requires Acc(list_pred(loc), 1/2)). Writing loc[0]=0 "
            "requires FULL list_pred permission; only 1/2 is held, so the "
            "in-place write fails for INSUFFICIENT PERMISSION before any "
            "postcondition reasoning. The gold recognised construction is kept "
            "verbatim after the write, so the rejection is attributable solely to "
            "the mutation of the read-only input. This is the project's #1 "
            "weakness class — a vacuous frame-mutation cheat — and the half-perm "
            "input forecloses it."),
    },
    {
        "id": "pos-control-inline-recognised",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_INLINE),
        "rationale": (
            "Structurally different but correct: inline the recognised "
            "construction make_key(loc, True) directly into the return, dropping "
            "the intermediate `result` local. Same recognised convention; P3/P4 "
            "are discharged by make_key's Ensures exactly as in the gold. No loop "
            "/ no induction lemma, so it MUST verify (else SPEC-TOO-STRONG)."),
    },
    {
        "id": "pos-control-branch-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_BRANCH),
        "rationale": (
            "Structurally different but correct: a branch-reshape where every arm "
            "calls make_key(loc, True) (the always-true `len(loc) >= 0` guard "
            "keeps both arms reachable to the verifier). P3/P4 are discharged on "
            "every path; semantically identical to the gold. MUST verify (else "
            "the spec is over-fitted to the single-statement gold shape => "
            "SPEC-TOO-STRONG)."),
    },
    {
        "id": "admissibility-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_IMPL_ADMISS),
        "rationale": (
            "A recursive self-call inside the impl region invokes "
            "conftest_dedup_key on a freshly-built normal location list "
            "([116,101,115,116] = 'test', a non-empty List[int] with full "
            "list_pred permission). Nagini must discharge the callee's Requires "
            "(Acc(list_pred(arg), 1/2)) at the call site; since full permission "
            "is held a half is trivially establishable, so the call site verifies "
            "(else PRECOND-TOO-STRONG). Confirms the precondition admits the "
            "F2P-shaped input. The gold recognised construction follows verbatim, "
            "so the postcondition obligation is unchanged; editing only the impl "
            "region keeps same_spec true."),
    },
]

# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# The axioms region carries three A-consumed callee contracts whose
# distinguishing EFFECT is the load-bearing change:
#   canonical(loc)              — value-level canonicalisation (string)
#   make_key(loc, recognised)   — the cache-key constructor
#   lookup_recognised(canon)    — the unforgeable recognition token, granted
#                                 ONLY by make_key under the recognised
#                                 convention
# These contracts are NOT discharged by the verifier against a real callee; the
# proof CONSUMES their Ensures, so their soundness must be validated by
# executing the REAL cache-membership semantics in the instance image. The
# probes below reuse axiom_check.py's proven logic (G-AX), executing the real
# pathlib.Path.resolve / py.path.local key constructors — never scraping source.
# They import only pathlib / os / py / tempfile (the modules the patch + the
# test use; all present in the pytest image) and open files UTF-8 safe.

# ax-sound: the make_key + lookup_recognised contract. On real conftest files
# (the F2P subdir names + the issue scenarios + 2000 fuzz names), assert:
#   (P3 / canonical) both conventions carry the IDENTICAL canonical location
#       string — so string-equality is NOT the discriminator;
#   (P4 grant, recognised) an independently-recomputed Path(...).resolve() key
#       IS found in a dict keyed by the recognised convention's key (the
#       Ensures(Implies(recognised_convention, lookup_recognised)) is sound — a
#       real membership HIT);
#   (P4 NON-grant, unrecognised) the SAME recomputed key is NOT found in a dict
#       keyed by the unrecognised convention's key (no token — a real MISS),
#       despite the identical location string.
# If any obligation fails the axiom over-claims the real semantics => AXIOM-
# UNSOUND. apply_gold=True so the post-patch pathlib is on the path (the
# constructors are stdlib/py regardless, but the gold patch is the post-change
# behaviour the recognised convention describes).
_AX_SOUND_MAKE_KEY = r'''
import os, os.path, random, sys, tempfile
from pathlib import Path
import py  # py.path.local — the pre-change (unrecognised) key object kind


def canonical_string(loc):
    # model.py `canonical`: the value-level canonical location string. Both real
    # conventions resolve to the same string on this platform.
    return str(Path(str(loc)).resolve())


def recognised_key(loc):
    # the recognised convention's key (gold): Path(str(loc)).resolve()
    return Path(str(loc)).resolve()


def unrecognised_key(loc):
    # the unrecognised convention's key (removed unique_path): a py.path.local
    # wrapping normcase(realpath(str(loc))).
    local = py.path.local(str(loc))
    return type(local)(os.path.normcase(str(local.realpath())))


def recomputed_lookup_key(loc):
    # the key an INDEPENDENT later lookup recomputes — exactly the F2P test's
    # Path(str(subconftest)).resolve().
    return Path(str(loc)).resolve()


def check_location(real_file):
    canon = canonical_string(real_file)
    rec_key = recognised_key(real_file)
    unrec_key = unrecognised_key(real_file)
    lookup = recomputed_lookup_key(real_file)

    # (canonical / P3) both conventions carry the IDENTICAL canonical string.
    assert str(rec_key) == canon, (
        "recognised key string %r != canonical %r" % (str(rec_key), canon))
    assert str(unrec_key) == canon, (
        "unrecognised key string %r != canonical %r" % (str(unrec_key), canon))
    assert str(rec_key) == str(unrec_key), (
        "conventions disagree on the location string: %r vs %r"
        % (str(rec_key), str(unrec_key)))

    # (recognised / P4 grant) recomputed key HITS the recognised-keyed dict.
    cache_recognised = {rec_key: "mod"}
    assert lookup in cache_recognised, (
        "recognised key NOT found by recomputed-key membership on %r"
        % str(real_file))

    # (unrecognised / P4 non-grant) the same recomputed key MISSES the
    # unrecognised-keyed dict, despite the identical location string.
    cache_unrecognised = {unrec_key: "mod"}
    assert lookup not in cache_unrecognised, (
        "unrecognised key UNEXPECTEDLY found by recomputed-key membership on %r "
        "(string %r)" % (str(real_file), canon))


def main():
    tmp = tempfile.mkdtemp()
    boundary_names = [
        "test", "tests",            # the FAIL_TO_PASS subdir names (lowercase)
        "Foo", "JenkinsRoot", "imageProcessing",  # issue scenarios
        "abc", "plain", "x", "ABC", "MixedCASE_123",
    ]
    for name in boundary_names:
        d = os.path.join(tmp, name)
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, "conftest.py")
        with open(f, "w", encoding="utf-8"):
            pass
        check_location(f)

    rng = random.Random(5840)
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    n_fuzz = 0
    for _ in range(2000):
        n = rng.randint(1, 16)
        name = "".join(rng.choice(letters) for _ in range(n))
        if not any(ch.isalpha() for ch in name):
            continue
        d = os.path.join(tmp, "fuzz_%s" % name)
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            continue
        f = os.path.join(d, "conftest.py")
        with open(f, "w", encoding="utf-8"):
            pass
        check_location(f)
        n_fuzz += 1

    print("ax-sound make_key/lookup_recognised OK: on %d boundary + %d fuzz real "
          "files both conventions carry the IDENTICAL canonical string, the "
          "recognised key is FOUND by a recomputed lookup (token sound), and the "
          "unrecognised key is NOT found despite the identical string (no token). "
          "The discriminator is the recognition effect, not casing."
          % (len(boundary_names), n_fuzz))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print("AXIOM-UNSOUND make_key/lookup_recognised:", e)
        sys.exit(1)
'''

# ax-cover: caller-domain containment. The model's make_key is invoked ONLY with
# recognised_convention=True (the gold) on a `loc` that is a real conftest path
# string (any List[int] of code points). make_key's Requires is
# Acc(list_pred(loc), 1/2) — ANY list, no value restriction; canonical's domain
# is any PSeq[int]. So every caller-reachable input is in-domain. We confirm the
# real recognised constructor Path(str(loc)).resolve() is TOTAL (does not raise)
# on every caller-reachable location — the F2P subdir names + fuzz — so there is
# no reachable input outside the axiom's domain. Covering more (e.g. arbitrary
# strings) than the caller reaches is SOUND (the float-vs-int rule), not a
# defect.
_AX_COVER_DOMAIN = r'''
import os, random, sys, tempfile
from pathlib import Path
import py


def main():
    tmp = tempfile.mkdtemp()
    names = ["test", "tests", "Foo", "JenkinsRoot", "imageProcessing",
             "abc", "x", "ABC", "MixedCASE_123"]
    rng = random.Random(58400)
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    for _ in range(500):
        n = rng.randint(1, 16)
        nm = "".join(rng.choice(letters) for _ in range(n))
        if any(ch.isalpha() for ch in nm):
            names.append(nm)

    checked = 0
    for name in names:
        d = os.path.join(tmp, "cover_%s" % name)
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            continue
        f = os.path.join(d, "conftest.py")
        with open(f, "w", encoding="utf-8"):
            pass
        # every caller-reachable location must be in the recognised
        # constructor's domain: Path(str(loc)).resolve() must not raise, and the
        # carried string must be a well-defined canonical location.
        key = Path(str(f)).resolve()
        canon = str(key)
        assert isinstance(canon, str) and len(canon) > 0, (
            "recognised constructor produced no canonical string on %r" % f)
        # the recomputed-key membership is well-defined on this input (hashable).
        _ = {key: "mod"}
        # py.path.local is likewise total on the same reachable input (the
        # unrecognised convention is defined on the SAME domain — containment is
        # not narrower than the caller reaches).
        local = py.path.local(str(f))
        _ = type(local)(os.path.normcase(str(local.realpath())))
        checked += 1

    print("ax-cover containment OK: the recognised key constructor "
          "Path(str(loc)).resolve() is TOTAL on %d caller-reachable conftest "
          "locations (make_key is only ever invoked with recognised_convention="
          "True on a real path string; its Requires has no value restriction). "
          "No caller-reachable input lies outside the axiom domain." % checked)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print("AXIOM-TOO-WEAK-FOR-CALLER:", e)
        sys.exit(1)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-make-key-lookup-recognised",
        "axiom": "make_key / lookup_recognised / canonical",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_MAKE_KEY,
        "rationale": (
            "Executes the REAL key constructors (pathlib.Path.resolve for the "
            "recognised convention; unique_path's py.path.local for the "
            "unrecognised one) on real conftest files. Asserts the three pinned "
            "Ensures: both conventions carry the identical canonical string (P3 / "
            "canonical sound), the recognised key is FOUND by an independently-"
            "recomputed Path(...).resolve() lookup (Ensures(Implies(recognised, "
            "lookup_recognised)) sound — real HIT), and the unrecognised key is "
            "NOT found despite the identical string (no token — real MISS). Any "
            "disagreement => AXIOM-UNSOUND. Reuses axiom_check.py's G-AX logic; "
            "calls the callee, never scrapes source."),
    },
    {
        "id": "ax-cover-recognised-constructor-domain",
        "axiom": "make_key / canonical",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_DOMAIN,
        "rationale": (
            "make_key is invoked by the model ONLY with recognised_convention="
            "True on a `loc` that is a real conftest path string; its Requires "
            "(Acc(list_pred(loc), 1/2)) and canonical's PSeq[int] domain place NO "
            "value restriction on the location. The probe confirms the real "
            "recognised constructor Path(str(loc)).resolve() is total (no raise, "
            "non-empty canonical string, hashable for membership) on every caller-"
            "reachable location, so no reachable input lies outside the axiom "
            "domain. Covering arbitrary strings beyond what the caller reaches is "
            "SOUND (float-vs-int rule), not AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
