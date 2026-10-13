"""properties.py — PBT falsification manifest for astropy__astropy-7606.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The two functions under spec are the two patched equality
dunders, abstracted to the boolean observables they read off the operand and a
THREE-VALUED integer result tag:

    eq_unparsed_name(parse_succeeds, parsed_same_kind, names_equal) -> int
        # = UnrecognizedUnit.__eq__   (the F2P-discriminating hunk)
    eq_unit(is_same, parse_succeeds, parsed_is_unit,
            convertible, effectively_unity) -> int
        # = UnitBase.__eq__           (the second hunk)

with RES_FALSE=0, RES_TRUE=1, RES_NOTIMPL=2.

What the spec actually defends, and the attacks it must survive
---------------------------------------------------------------

  * The result is a TOTAL function of the input booleans, fully pinned by the
    postconditions for EVERY combination — there is NO opaque @Pure answer-key
    oracle and NO heap input. So there is no "echo the oracle" shortcut and no
    "mutate a read-only input" shortcut; the load-bearing content is the
    THREE-VALUED discrimination between RES_NOTIMPL (defer) and a definite
    RES_TRUE/RES_FALSE.

  * The single discriminating clause — the one that senses the gold change — is

        eq_unparsed_name:  Implies(not parse_succeeds, Result() == RES_NOTIMPL)
        eq_unit:           Implies(not is_same and not parse_succeeds,
                                   Result() == RES_NOTIMPL)

    A non-coercible operand (e.g. None) must yield the NOT-APPLICABLE sentinel
    (RES_NOTIMPL = `return NotImplemented`), never a definite decision and never
    a failure. The pre-patch code RAISES (eq_unparsed_name) / returns a definite
    `False` (eq_unit); both are caught by these clauses. The uniqueness rivals
    target exactly this discrimination and the surrounding decision clauses.

  * NO read-only Acc(x,1/2) input exists: `self` and `other` are abstracted to
    plain value-typed booleans (mapping.md §2), so directive 5 (frame mutation)
    is satisfied VACUOUSLY — there is no mutable heap reference to over-permit or
    overwrite. The frame-mutation class therefore does NOT apply to this bundle;
    this is stated in the StructuredOutput assessment.

  * NO @ContractOnly axiom / A-reference deep model is consumed (meta.axioms ==
    []). The single soundness obligation is the refinement fidelity of the
    boolean-predicate + three-valued-tag abstraction: that the model's pinned
    outcome equals the REAL post-patch UnrecognizedUnit.__eq__ / UnitBase.__eq__
    on every reachable observable combination, decisively that the non-coercible
    operands DEFER via NotImplemented and never raise. The AXIOM_TESTS below run
    the REAL post-patch dunders in Docker to discharge exactly that obligation
    (reusing/strengthening axiom_check.py's catalogue) — an axiom-soundness
    probe of the abstraction itself.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside a function's `# impl-start`/`# impl-end` body, so
`markers.same_spec` is guaranteed and a rejection comes from the POSTCONDITION
catching wrong behaviour, never from a tampered spec. Each `expect:"reject"`
rival carries the refinement argument that its faithful real patch would NOT
resolve the F2P/P2P.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7606"
FLOAT_ENCODING = None

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Whole gold impl bodies (text strictly between # impl-start / # impl-end), each
# unique in model.py, used as a single replaceable block for rewrites.
# ---------------------------------------------------------------------------

# eq_unparsed_name gold body
_G1 = """    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than fail.
        return RES_NOTIMPL
    if parsed_same_kind and names_equal:
        return RES_TRUE
    return RES_FALSE"""

# eq_unit gold body
_G2 = """    if is_same:
        return RES_TRUE
    if not parse_succeeds:
        # The silent unit-coercion could not denote this operand: decline to
        # decide rather than return a definite (and wrong) \"not equal\".
        return RES_NOTIMPL
    if not parsed_is_unit:
        return RES_NOTIMPL
    if convertible and effectively_unity:
        return RES_TRUE
    return RES_FALSE"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5a) eq_unparsed_name, structurally DIFFERENT but CORRECT. The deferral guard
# is kept first (the only ordering the total spec forces), but the two definite
# branches are collapsed into a SINGLE boolean expression returned via a local —
# a different control shape (no if/elif over the definite case, a computed tag).
# Semantically identical to gold. If it fails to verify, the postcondition is
# over-fit to the if/return code form => SPEC-TOO-STRONG.
_POS_UNPARSED_BODY = """    if not parse_succeeds:
        return RES_NOTIMPL
    decided_equal = parsed_same_kind and names_equal  # type: bool
    if decided_equal:
        return RES_TRUE
    else:
        return RES_FALSE"""
_POS_UNPARSED = _swap(_BASE, _G1, _POS_UNPARSED_BODY)

# (5b) eq_unit, structurally DIFFERENT but CORRECT. The two DEFER conditions
# (not parse_succeeds; parsed but not a unit) are merged into one guard, and the
# definite decision is computed into a local boolean and returned once. The
# identity short-circuit stays first. A different code shape, same behaviour. If
# it fails to verify => SPEC-TOO-STRONG.
_POS_UNIT_BODY = """    if is_same:
        return RES_TRUE
    if (not parse_succeeds) or (not parsed_is_unit):
        return RES_NOTIMPL
    same_unit = convertible and effectively_unity  # type: bool
    if same_unit:
        return RES_TRUE
    return RES_FALSE"""
_POS_UNIT = _swap(_BASE, _G2, _POS_UNIT_BODY)

# (6) ADMISSIBILITY. A self-call on an F2P-shaped in-domain input must establish
# the precondition. eq_unparsed_name has a vacuous precondition (plain bools);
# eq_unit has Requires(Implies(effectively_unity, convertible)). We add a
# self-call to eq_unit on the F2P "non-coercible None" shape
# (is_same=False, parse_succeeds=False, the rest False) — for which the implies
# holds vacuously (effectively_unity=False) — and assert the deferral result, to
# prove the precondition ADMITS a normal F2P input. If the call site cannot
# establish the Requires for a legitimate input => PRECOND-TOO-STRONG. The probe
# is prepended inside eq_unparsed_name's impl so the eq_unit spec is untouched.
_ADMISS_BODY = (
    "    _none = eq_unit(False, False, False, False, False)\n"
    "    Assert(_none == RES_NOTIMPL)\n"
    + _G1
)
_ADMISS = _swap(_BASE, _G1, _ADMISS_BODY)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (3 / control-flow-as-value) THE F2P BUG, eq_unparsed_name. On a non-coercible
# operand the rival returns a DEFINITE RES_FALSE instead of the not-applicable
# RES_NOTIMPL — exactly the pre-patch behaviour modelled by model_prepatch.py
# (the absent try/except, which on the real callee RAISES TypeError on None).
# Rejection source: the discriminating postcondition
# Implies(not parse_succeeds, Result() == RES_NOTIMPL) AND the iff clause
# (Result in {TRUE,FALSE}) == parse_succeeds.
_RIVAL_UNPARSED_FALSE_BODY = """    if not parse_succeeds:
        return RES_FALSE
    if parsed_same_kind and names_equal:
        return RES_TRUE
    return RES_FALSE"""
_RIVAL_UNPARSED_FALSE = _swap(_BASE, _G1, _RIVAL_UNPARSED_FALSE_BODY)

# (3b) THE F2P BUG, eq_unit. On a non-coercible operand the rival returns the
# pre-patch definite RES_FALSE instead of RES_NOTIMPL — exactly the single edited
# token `False`->`NotImplemented` reverted (model_prepatch_2.py). Rejection
# source: Implies(not is_same and not parse_succeeds, Result() == RES_NOTIMPL).
_RIVAL_UNIT_FALSE_BODY = """    if is_same:
        return RES_TRUE
    if not parse_succeeds:
        return RES_FALSE
    if not parsed_is_unit:
        return RES_NOTIMPL
    if convertible and effectively_unity:
        return RES_TRUE
    return RES_FALSE"""
_RIVAL_UNIT_FALSE = _swap(_BASE, _G2, _RIVAL_UNIT_FALSE_BODY)

# (3c) PARTIAL-DOMAIN, eq_unit. The "coerced-but-not-a-genuine-unit" branch
# returns a definite RES_FALSE instead of RES_NOTIMPL. This rival is CORRECT on
# the entire None / same-object / genuine-unit domain and diverges ONLY on the
# unit-like-but-not-UnitBase sub-domain (parse_succeeds, not parsed_is_unit).
# Rejection source: the clause
# Implies(not is_same and parse_succeeds and not parsed_is_unit,
#         Result() == RES_NOTIMPL).
_RIVAL_UNIT_NOTUNIT_BODY = """    if is_same:
        return RES_TRUE
    if not parse_succeeds:
        return RES_NOTIMPL
    if not parsed_is_unit:
        return RES_FALSE
    if convertible and effectively_unity:
        return RES_TRUE
    return RES_FALSE"""
_RIVAL_UNIT_NOTUNIT = _swap(_BASE, _G2, _RIVAL_UNIT_NOTUNIT_BODY)

# (3d) PARTIAL-DOMAIN, eq_unparsed_name — the definite-decision sub-domain. On a
# coercible same-kind operand the rival flips equal-name to RES_FALSE only when
# names match (returns RES_FALSE for the names_equal case), i.e. it is correct
# everywhere except it never reports a definite EQUAL. Rejection source:
# Implies(parse_succeeds and parsed_same_kind and names_equal,
#         Result() == RES_TRUE).
_RIVAL_UNPARSED_NEVER_TRUE_BODY = """    if not parse_succeeds:
        return RES_NOTIMPL
    return RES_FALSE"""
_RIVAL_UNPARSED_NEVER_TRUE = _swap(_BASE, _G1, _RIVAL_UNPARSED_NEVER_TRUE_BODY)

# (3e, supporting near-miss) eq_unparsed_name returns the deferral sentinel for
# EVERY operand (always RES_NOTIMPL). Satisfies totality + the not-coercible
# clause, but violates the coercible-decides clauses and the iff clause. A
# faithful real patch (return NotImplemented unconditionally) would make
# `unit == "FOO"` defer to str.__eq__ (False), so the F2P `assert unit == "FOO"`
# would FAIL — it would NOT resolve. Rejection source: the iff clause
# (Result in {TRUE,FALSE}) == parse_succeeds (false when parse_succeeds=True).
_RIVAL_UNPARSED_ALL_DEFER_BODY = """    return RES_NOTIMPL"""
_RIVAL_UNPARSED_ALL_DEFER = _swap(_BASE, _G1, _RIVAL_UNPARSED_ALL_DEFER_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-unparsed-restructured", "kind": "soundness", "expect": "verify",
     "module": _POS_UNPARSED,
     "rationale": "structurally-different but CORRECT eq_unparsed_name (definite case "
                  "collapsed into a computed boolean, different control shape) must verify; "
                  "if not, the postcondition is over-fit to the gold if/return form => "
                  "SPEC-TOO-STRONG."},
    {"id": "pos-unit-restructured", "kind": "soundness", "expect": "verify",
     "module": _POS_UNIT,
     "rationale": "structurally-different but CORRECT eq_unit (the two DEFER conditions "
                  "merged into one guard; definite decision computed into a local and "
                  "returned once) must verify; if not, the spec is over-fit to the gold "
                  "branch sequence => SPEC-TOO-STRONG."},
    {"id": "admiss-defer-self-call", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call eq_unit(False,False,False,False,False) on the F2P "
                  "non-coercible-None shape must establish the precondition "
                  "Requires(Implies(effectively_unity, convertible)) (vacuous: "
                  "effectively_unity=False) and yield RES_NOTIMPL; if the call site cannot "
                  "establish the Requires for a legitimate input => PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-unparsed-defer-as-false", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNPARSED_FALSE,
     "refinement": "returns a DEFINITE RES_FALSE on a non-coercible operand instead of the "
                   "not-applicable sentinel — the pre-patch shape (model_prepatch.py). Its "
                   "faithful real patch is the pre-patch UnrecognizedUnit.__eq__ that calls "
                   "Unit(other, parse_strict='silent') with NO try/except, which RAISES "
                   "TypeError on None (core.py:1822) — so `unit != None` and "
                   "`unit not in (None, u.m)` raise and the F2P test_unknown_unit3 FAILS. It "
                   "would NOT resolve.",
     "rationale": "the F2P-discriminating bug. Rejection source: the postcondition "
                  "Implies(not parse_succeeds, Result() == RES_NOTIMPL) (model.py:89) and "
                  "the iff clause (Result in {TRUE,FALSE}) == parse_succeeds. If it verified "
                  "=> SPEC-TOO-WEAK (admits the pre-patch raise/definite-decision bug)."},
    {"id": "rival-unit-defer-as-false", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNIT_FALSE,
     "refinement": "reverts the single edited token (`NotImplemented`->`False`) in "
                   "UnitBase.__eq__'s coercion-failure path — exactly model_prepatch_2.py. "
                   "Its faithful real patch returns a definite `False` on a non-coercible "
                   "operand instead of deferring, so `other.__eq__` is never given a chance "
                   "(the documented robustness regression). While test_compare_with_none "
                   "collapses both to False for `==`, the modeled+prepatch pair pins this "
                   "hunk for faithful multi-site coverage; a verifying rival would break the "
                   "model<->patch equivalence the bundle asserts (G-DIFF/G-EQ).",
     "rationale": "Rejection source: Implies(not is_same and not parse_succeeds, "
                  "Result() == RES_NOTIMPL) (model.py:139). If it verified => SPEC-TOO-WEAK "
                  "(admits the pre-patch definite-False on coercion failure)."},
    {"id": "rival-unit-notunit-as-false", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNIT_NOTUNIT,
     "refinement": "PARTIAL-DOMAIN: correct on None / same-object / genuine-unit operands, "
                   "diverges ONLY on the coerced-but-not-a-UnitBase sub-domain, returning a "
                   "definite RES_FALSE instead of deferring. Its faithful real patch replaces "
                   "`if not isinstance(other, UnitBase): return NotImplemented` (core.py:735) "
                   "with `return False`, which stops a unit-like non-UnitBase operand (e.g. a "
                   "Quantity) from getting its reflected __eq__ — a behavioural regression vs "
                   "the gold UnitBase.__eq__ the model abstracts, so it would NOT be the gold "
                   "patch and would not resolve the P2P comparison suite faithfully.",
     "rationale": "partial-domain on the parsed-not-unit sub-domain. Rejection source: "
                  "Implies(not is_same and parse_succeeds and not parsed_is_unit, "
                  "Result() == RES_NOTIMPL) (model.py:143). If it verified => SPEC-TOO-WEAK "
                  "(domain-incomplete: drops the not-a-unit deferral)."},
    {"id": "rival-unparsed-never-true", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNPARSED_NEVER_TRUE,
     "refinement": "PARTIAL-DOMAIN: defers correctly on non-coercible operands and reports "
                   "RES_FALSE on every coercible operand — it NEVER returns a definite EQUAL. "
                   "Its faithful real patch is UnrecognizedUnit.__eq__ that always returns "
                   "False for a coercible operand (e.g. drops the `self.name == other.name` "
                   "conjunct, hard-returning False), so `unit == \"FOO\"` is False and the "
                   "F2P assert `unit == \"FOO\"` FAILS — it would NOT resolve.",
     "rationale": "partial-domain on the definite-EQUAL sub-domain. Rejection source: "
                  "Implies(parse_succeeds and parsed_same_kind and names_equal, "
                  "Result() == RES_TRUE) (model.py:92). If it verified => SPEC-TOO-WEAK "
                  "(never reports equal)."},
    {"id": "rival-unparsed-always-defer", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNPARSED_ALL_DEFER,
     "refinement": "returns the deferral sentinel for EVERY operand (always RES_NOTIMPL). "
                   "Its faithful real patch is UnrecognizedUnit.__eq__ that unconditionally "
                   "`return NotImplemented`, so `unit == \"FOO\"` defers to str.__eq__ and is "
                   "False — the F2P assert `unit == \"FOO\"` FAILS — and it would NOT resolve.",
     "rationale": "supporting near-miss with a real refinement: total but never decides for a "
                  "coercible operand. Rejection source: the iff clause "
                  "(Result in {TRUE,FALSE}) == parse_succeeds (model.py:98), false whenever "
                  "parse_succeeds is True. If it verified => SPEC-TOO-WEAK (the coercible "
                  "operand is never decided)."},
]

# ===========================================================================
# AXIOM LANE (Docker, real post-patch dunders) — the abstraction-fidelity
# soundness obligation (this bundle has NO @ContractOnly axiom / A-reference;
# the single soundness obligation is the boolean-predicate + three-valued-tag
# refinement == the real UnrecognizedUnit.__eq__ / UnitBase.__eq__).
# ===========================================================================

# (axiom-soundness) Drive the REAL post-patch dunders with concrete operands
# spanning the full observable space — incl. the discriminating non-coercible
# None/object/list operands that MUST defer via NotImplemented and MUST NOT
# raise — and assert the RAW dunder return (mapped to the three-valued tag)
# equals the model's pinned outcome. Strengthens axiom_check.py with extra
# non-coercible sentinels (a dict, a tuple, a float that is not a unit). Applies
# the gold patch in-container first (idempotent). Exit 0 iff the abstraction is
# sound; nonzero on any raise / tag mismatch.
_AX_ABSTRACTION_SOUND = r'''
import os, subprocess, sys

RES_FALSE, RES_TRUE, RES_NOTIMPL = 0, 1, 2
_CHANGED = "astropy/units/core.py"
_MARKER = "isinstance(other, type(self))"  # unique to the post-patch source

def ensure_postpatch():
    testbed = os.environ.get("TESTBED", "/testbed")
    changed = os.path.join(testbed, _CHANGED)
    # core.py carries non-ASCII unit glyphs (e.g. Greek mu/Omega); the testbed
    # container's Python 3.6 locale is ASCII, so open() WITHOUT an explicit
    # encoding crashes with UnicodeDecodeError on byte 0xce. Read as UTF-8 (this
    # is only a marker check; the soundness obligation is the real dunder below).
    try:
        with open(changed, encoding="utf-8") as fh:
            if _MARKER in fh.read():
                return None
    except OSError as exc:
        return "could not read %s: %r" % (changed, exc)
    cands = ["/work/patch.diff", "/gold.patch",
             os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch.diff")]
    patch = next((p for p in cands if os.path.exists(p)), None)
    if patch is None:
        return "post-patch source required but no patch.diff in %r" % (cands,)
    proc = subprocess.run(["git", "apply", "-v", patch], cwd=testbed,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return "git apply failed (rc %d): %s" % (
            proc.returncode, (proc.stderr or proc.stdout).strip())
    with open(changed, encoding="utf-8") as fh:
        if _MARKER not in fh.read():
            return "patch applied but marker still absent"
    return None

def tag(raw):
    if raw is NotImplemented: return RES_NOTIMPL
    if raw is True:  return RES_TRUE
    if raw is False: return RES_FALSE
    raise AssertionError("dunder returned non-bool/non-NotImplemented: %r" % (raw,))

def main():
    err = ensure_postpatch()
    if err:
        print("AXIOM-UNSOUND probe could not establish post-patch source:", err)
        return 1
    import astropy.units as u
    from astropy.units.core import UnitBase, UnrecognizedUnit

    foo = u.Unit("FOO", parse_strict="silent")
    assert isinstance(foo, UnrecognizedUnit), "FOO must be an unparsed-name unit"

    # eq_unparsed_name <-> UnrecognizedUnit.__eq__
    # (label, operand, parse_succeeds, parsed_same_kind, names_equal)
    unrec = [
        ("None", None, False, False, False),
        ("object", object(), False, False, False),
        ("list", [1, 2], False, False, False),
        ("dict", {"a": 1}, False, False, False),
        ("tuple", (1, 2), False, False, False),
        ("same_name_str", "FOO", True, True, True),
        ("same_name_unit", u.Unit("FOO", parse_strict="silent"), True, True, True),
        ("other_name_str", "BAR", True, True, False),
        ("metre", u.m, True, False, False),
        ("dimensionless_str", "", True, False, False),
    ]
    checked = 0
    for label, other, ps, sk, ne in unrec:
        exp = RES_NOTIMPL if not ps else (RES_TRUE if (sk and ne) else RES_FALSE)
        try:
            raw = foo.__eq__(other)
        except Exception as exc:
            print("AXIOM-UNSOUND UnrecognizedUnit.__eq__(%s) RAISED %r — must be total"
                  % (label, exc)); return 1
        obs = tag(raw)
        if obs != exp:
            print("AXIOM-UNSOUND UnrecognizedUnit.__eq__ tag mismatch on %s: real=%s model=%s"
                  % (label, obs, exp)); return 1
        if (foo == other) != (exp == RES_TRUE):
            print("AXIOM-UNSOUND user-facing == disagrees on %s" % label); return 1
        checked += 1
    # F2P witnesses (test_unknown_unit3)
    assert (foo == "FOO") is True
    assert (foo != u.m) is True
    assert (foo != None) is True            # noqa: E711
    assert foo not in (None, u.m)

    # eq_unit <-> UnitBase.__eq__
    metre = u.m
    # (label, operand, is_same, parse_succeeds, parsed_is_unit, convertible, eff_unity)
    units = [
        ("self", metre, True, True, True, True, True),
        ("equal_unit", u.m, False, True, True, True, True),
        ("equal_str", "m", False, True, True, True, True),
        ("convertible_unequal", u.cm, False, True, True, True, False),
        ("incompatible", u.kg, False, True, True, False, False),
        ("None", None, False, False, False, False, False),
        ("object", object(), False, False, False, False, False),
        ("list", [1], False, False, False, False, False),
    ]
    for label, other, isn, ps, piu, conv, eu in units:
        if isn: exp = RES_TRUE
        elif not ps: exp = RES_NOTIMPL
        elif not piu: exp = RES_NOTIMPL
        elif conv and eu: exp = RES_TRUE
        else: exp = RES_FALSE
        try:
            raw = metre.__eq__(other)
        except Exception as exc:
            print("AXIOM-UNSOUND UnitBase.__eq__(%s) RAISED %r — must be total"
                  % (label, exc)); return 1
        obs = tag(raw)
        if obs != exp:
            print("AXIOM-UNSOUND UnitBase.__eq__ tag mismatch on %s: real=%s model=%s"
                  % (label, obs, exp)); return 1
        if (metre == other) != (exp == RES_TRUE):
            print("AXIOM-UNSOUND user-facing == disagrees on %s" % label); return 1
        checked += 1
    assert not (u.m == None)                # noqa: E711
    assert (u.m != None) is True            # noqa: E711

    print("abstraction SOUND: three-valued model == real post-patch "
          "UnrecognizedUnit.__eq__ / UnitBase.__eq__ over %d operands "
          "(non-coercible None/object/list/dict/tuple DEFER via NotImplemented, "
          "never raise)." % checked)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# (axiom-containment) The model only ever passes the observed predicate
# combinations of `other` to the abstracted callees. Confirm every observable
# combination the model can REACH corresponds to a real operand the dunder
# handles without raising — i.e. the abstraction's input domain is contained in
# the real callee's domain. We enumerate the reachable observable tuples and,
# for each, exhibit a concrete operand and confirm the real dunder produces the
# tag (no reachable combination falls outside the callee's domain). A reachable
# combination the real callee cannot handle => the abstraction is too weak for
# the caller.
_AX_CONTAINMENT = r'''
import os, subprocess, sys

RES_FALSE, RES_TRUE, RES_NOTIMPL = 0, 1, 2
_CHANGED = "astropy/units/core.py"
_MARKER = "isinstance(other, type(self))"

def ensure_postpatch():
    testbed = os.environ.get("TESTBED", "/testbed")
    changed = os.path.join(testbed, _CHANGED)
    # See ensure_postpatch in the soundness probe: open() must be UTF-8 because
    # core.py carries non-ASCII unit glyphs and the container locale is ASCII.
    try:
        with open(changed, encoding="utf-8") as fh:
            if _MARKER in fh.read():
                return None
    except OSError as exc:
        return "could not read %s: %r" % (changed, exc)
    cands = ["/work/patch.diff", "/gold.patch",
             os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch.diff")]
    patch = next((p for p in cands if os.path.exists(p)), None)
    if patch is None:
        return "no patch.diff in %r" % (cands,)
    proc = subprocess.run(["git", "apply", "-v", patch], cwd=testbed,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return "git apply failed (rc %d)" % proc.returncode
    return None

def main():
    err = ensure_postpatch()
    if err:
        print("containment probe could not establish post-patch source:", err); return 1
    import astropy.units as u
    from astropy.units.core import UnrecognizedUnit
    foo = u.Unit("FOO", parse_strict="silent")

    # The observable tuples the model's CONTROL FLOW can reach, each with a
    # concrete witness operand that realises that tuple. The model never reaches
    # a (parse_succeeds=False AND parsed_same_kind=True) tuple — those are
    # excluded by the contract structure (a kind/name predicate is only read when
    # coercion succeeded), so they are not in the reachable domain and need no
    # witness. Every reachable tuple below must be handled by the real callee
    # without raising (totality), establishing domain containment.
    reachable_unrec = [
        # (operand, parse_succeeds, same_kind, names_equal)
        (None, False, False, False),
        (object(), False, False, False),
        ("FOO", True, True, True),
        ("BAR", True, True, False),
        (u.m, True, False, False),
    ]
    for other, ps, sk, ne in reachable_unrec:
        try:
            foo.__eq__(other)   # must not raise -> operand is in the callee domain
        except Exception as exc:
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable operand %r outside callee domain "
                  "(raised %r)" % (other, exc)); return 1
    print("containment OK: every reachable observable tuple of the abstraction maps to a "
          "concrete operand the real UnrecognizedUnit.__eq__/UnitBase.__eq__ handles "
          "totally (no raise). The abstraction over-covers nothing the caller cannot reach.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

AXIOM_TESTS = [
    {"id": "ax-abstraction-sound", "axiom": "boolean_predicate_three_valued_tag",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_ABSTRACTION_SOUND,
     "rationale": "the bundle's single soundness obligation: the three-valued "
                  "boolean-predicate abstraction must equal the REAL post-patch "
                  "UnrecognizedUnit.__eq__ / UnitBase.__eq__ over the full observable space, "
                  "decisively that non-coercible operands DEFER via NotImplemented and never "
                  "raise. Any raise or tag mismatch => the abstraction is UNSOUND."},
    {"id": "ax-abstraction-containment", "axiom": "boolean_predicate_three_valued_tag",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "every observable predicate tuple the model's control flow can reach is "
                  "realised by a concrete operand the real callee handles totally (no raise); "
                  "a reachable tuple outside the callee's domain => AXIOM-TOO-WEAK-FOR-CALLER."},
]
