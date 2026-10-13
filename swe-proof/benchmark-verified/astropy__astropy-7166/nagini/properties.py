"""properties.py — PBT falsification manifest for astropy__astropy-7166.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The single modeled changed decision is one iteration of the
`InheritDocstrings.__init__` docstring-inheritance loop, abstracted as

    apply_inheritance(m: Member) -> None

over a heap object `m` carrying the boolean results of three unchanged
introspection callees (`is_callable_member <- inspect.isfunction`,
`is_computed_attribute <- inspect.isdatadescriptor`, `is_public <-
is_public_member`), the own-doc flag (`has_own_doc <- val.__doc__ is not None`),
the docstring resolved from the bases (`inherited_doc`, an int identity; 0 =
None) and the member's current docstring (`doc`).

What the spec actually defends, and the attacks it must survive
---------------------------------------------------------------

  * READ-ONLY HEAP INPUTS. `apply_inheritance`'s precondition gives only HALF
    permission to five of the six fields:

        Requires(Acc(m.is_callable_member, 1/2) and Acc(m.is_computed_attribute, 1/2)
                 and Acc(m.is_public, 1/2) and Acc(m.has_own_doc, 1/2)
                 and Acc(m.inherited_doc, 1/2) and Acc(m.doc))

    `m.doc` is the ONLY writable field (full Acc); the kind predicates, the
    public flag, the own-doc flag and the resolved inherited docstring are
    read-only. This is the #1 weakness class: a rival that WRITES a read-only
    field to satisfy a postcondition vacuously MUST be rejected for INSUFFICIENT
    PERMISSION. The frame-mutation rivals below (frame-mut-*) target exactly
    that; the five `Ensures(m.X == Old(m.X))` preservation clauses plus the
    permission system are what reject them.

  * GROUNDED ORACLE, NO ECHO SHORTCUT. The load-bearing postcondition is a
    case split on the @Pure helper `fills_docstring(...)`, but that helper is
    FULLY GROUNDED in the four input booleans (`(a or b) and c and not d`,
    visible and unfolded), not an opaque answer-key. There is no wrong value an
    impl could "echo" to satisfy the contract without doing the work — the only
    way to satisfy `Implies(fills_docstring(Old...), m.doc == Old(m.inherited_doc))`
    AND `Implies(not fills_docstring(Old...), m.doc == Old(m.doc))` is to
    actually compute the same eligibility decision and assign the right value.
    So the ungrounded-oracle-echo class does NOT apply; instead we include an
    honest cheapest-correct positive control (pos-*) and the value-divergence
    rival (rival-fill-wrong-value).

  * NO @ContractOnly AXIOM. meta.axioms == []; the three introspection callees
    are A-reference deep models (bool fields validated == the real callees by
    axiom_check.py / G-AX, already pass). There is no consumed axiom whose
    Ensures the proof unfolds, so there is no Nagini-side axiom-soundness /
    containment obligation for the PBT runner to discharge in Docker. AXIOM_TESTS
    is therefore []; G-AX (axiom_check.py, run in-container) already discharges
    the abstraction-fidelity obligation that a property -> isfunction False /
    isdatadescriptor True, which is the discriminating real-callee fact. This is
    stated in the StructuredOutput assessment.

The discriminating change (F2P): the guard gains `or m.is_computed_attribute`
(`or inspect.isdatadescriptor(val)`). The discriminating member is a public
undocumented PROPERTY: is_callable_member=False, is_computed_attribute=True. The
F2P test `test_inherit_docstrings` asserts `Subclass.bar.__doc__ == "BAR"` — the
inherited docstring is filled in. The pre-patch isfunction-only guard does NOT
fill it (model_prepatch.py). The partial-domain rival rival-drop-descriptor
reproduces exactly that bug.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `apply_inheritance`'s `# impl-start`/`# impl-end` body, so
`markers.same_spec` is GUARANTEED and a rejection always comes from the
POSTCONDITION / permission system catching wrong behaviour, never from a tampered
spec. Each `expect:"reject"` rival carries the refinement argument that its
faithful real patch would NOT resolve the F2P.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7166"
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


# The gold impl body of apply_inheritance (text strictly between its
# # impl-start / # impl-end), unique in model.py — the single replaceable block.
_GOLD = """    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        m.doc = m.inherited_doc"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (pos) Structurally-DIFFERENT but CORRECT. The disjunction operands are
# REORDERED (descriptor first) and the whole eligibility decision is hoisted into
# a typed local boolean returned once, instead of an inline if-condition. This is
# a local-variable reshape + branch-condition reorder that keeps the gold proof
# valid (no induction / fold lemma needed — there is no loop). Semantically
# identical to gold. If it fails to verify, the postcondition is over-fit to the
# exact gold expression form => SPEC-TOO-STRONG.
_POS_BODY = """    eligible = ((m.is_computed_attribute or m.is_callable_member)
                and m.is_public and not m.has_own_doc)  # type: bool
    if eligible:
        m.doc = m.inherited_doc"""
_POS = _swap(_BASE, _GOLD, _POS_BODY)

# (pos2) A second correct shape: an early no-op return when NOT eligible, then the
# unconditional assign. Different control flow (guard-clause / early return) but
# behaviourally identical. The `not (...)` guard is the De Morgan dual of the gold
# conjunction. If it fails to verify => SPEC-TOO-STRONG (over-fit to the
# positive-guard form).
_POS2_BODY = """    if not ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        return
    m.doc = m.inherited_doc"""
_POS2 = _swap(_BASE, _GOLD, _POS2_BODY)

# (admiss) ADMISSIBILITY. A self-call on an F2P-shaped in-domain input must be
# able to ESTABLISH apply_inheritance's precondition. Inside apply_inheritance's
# own impl we construct a FRESH member shaped exactly like the F2P discriminator
# — a public, undocumented computed-attribute member (a property):
# is_callable_member=False, is_computed_attribute=True, is_public=True,
# has_own_doc=False, inherited_doc=7 (the resolved base docstring), doc=0 (none).
# The fresh member holds full Acc on all six fields from __init__'s Ensures, so
# the call site can split off the 1/2 permissions the callee Requires. We then
# assert the postcondition outcome (the eligible property's docstring is filled to
# the inherited value) before running the gold body on the real `m`. If the call
# site cannot establish the Requires for this legitimate F2P input =>
# PRECOND-TOO-STRONG.
#
# The self-call is GUARDED by `not m.is_computed_attribute` solely to discharge
# the termination obligation, which the spec now demands: the level
# MustTerminate(3 if m.is_computed_attribute else 4) must STRICTLY decrease from
# caller to callee, and the probe is a computed-attribute member (level 3), so
# the caller must be at 4 — i.e. must itself not be a computed attribute. No
# constant level could satisfy this against itself (it would need n > n), so the
# guard is what makes the obligation dischargeable, NOT a weakening: the
# asserted claim (`probe.doc == 7`, the F2P outcome) is unchanged, and the
# guarded branch is genuinely reachable — replacing the assert with
# `Assert(False)` FAILS to verify, so the case is not vacuous.
_ADMISS_BODY = """    if not m.is_computed_attribute:
        probe = Member(False, True, True, False, 7, 0)
        apply_inheritance(probe)
        Assert(probe.doc == 7)
    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        m.doc = m.inherited_doc"""
_ADMISS = _swap(_BASE, _GOLD, _ADMISS_BODY)


# ===========================================================================
# FRAME-MUTATION RIVALS (read-only heap input) — expect "reject"
# ===========================================================================

# (frame-mut-inherited) The MANDATORY frame-mutation attack. The rival keeps the
# gold guard + assignment VERBATIM (so any rejection is attributable to the extra
# write, not to a changed decision), then additionally writes the READ-ONLY field
# m.inherited_doc — a vacuous-satisfaction move: overwrite the source field so
# that m.doc == Old(m.inherited_doc) could be "made true" by clobbering inputs.
# m.inherited_doc carries only Acc(m.inherited_doc, 1/2): a write requires FULL
# permission, so Nagini MUST reject for INSUFFICIENT PERMISSION (and, separately,
# it would violate Ensures(m.inherited_doc == Old(m.inherited_doc))). A byte
# fuzzer never thinks to mutate a read-only input — this is the project's #1
# weakness class.
_FRAME_INH_BODY = """    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        m.doc = m.inherited_doc
    m.inherited_doc = m.doc"""
_FRAME_INH = _swap(_BASE, _GOLD, _FRAME_INH_BODY)

# (frame-mut-public, supporting) Same attack on a different read-only field: the
# rival writes m.is_public (Acc(m.is_public, 1/2)) — insufficient permission, and
# it would also break Ensures(m.is_public == Old(m.is_public)). Cheap supporting
# frame case proving the half-permission discipline holds on every read-only
# field, not just inherited_doc.
_FRAME_PUB_BODY = """    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        m.doc = m.inherited_doc
    m.is_public = True"""
_FRAME_PUB = _swap(_BASE, _GOLD, _FRAME_PUB_BODY)


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (rival-drop-descriptor) THE F2P-DISCRIMINATING BUG. The rival DROPS the
# `or m.is_computed_attribute` disjunct — exactly the pre-patch isfunction-only
# guard reproduced by model_prepatch.py. On a public undocumented PROPERTY
# (is_callable_member=False, is_computed_attribute=True) the guard is
# (False) and True and True = False, so the docstring is NOT filled. Rejection
# source: Ensures(Implies(fills_docstring(Old...), m.doc == Old(m.inherited_doc)))
# — for the property fills_docstring is True but m.doc stays Old(m.doc) != the
# inherited doc.
_RIVAL_DROP_DESC_BODY = """    if (m.is_callable_member
            and m.is_public and not m.has_own_doc):
        m.doc = m.inherited_doc"""
_RIVAL_DROP_DESC = _swap(_BASE, _GOLD, _RIVAL_DROP_DESC_BODY)

# (rival-fill-always) Drops the WHOLE guard: unconditionally fills the docstring.
# Fills even an ineligible member (private, OR one that already has its own
# docstring). Rejection source:
# Ensures(Implies(not fills_docstring(Old...), m.doc == Old(m.inherited_doc) ... ))
# — when NOT eligible the postcondition requires m.doc == Old(m.doc), but this
# rival sets it to Old(m.inherited_doc), which differ in general.
_RIVAL_FILL_ALL_BODY = """    m.doc = m.inherited_doc"""
_RIVAL_FILL_ALL = _swap(_BASE, _GOLD, _RIVAL_FILL_ALL_BODY)

# (rival-drop-public) PARTIAL-DOMAIN: drops the `and m.is_public` guard. CORRECT
# on every public member; diverges ONLY on the private (is_public=False)
# sub-domain, where it fills a non-public member that the spec says must be left
# unchanged. Rejection source: Implies(not fills_docstring(Old...),
# m.doc == Old(m.doc)) on the is_public=False, otherwise-eligible sub-domain.
_RIVAL_DROP_PUB_BODY = """    if ((m.is_callable_member or m.is_computed_attribute)
            and not m.has_own_doc):
        m.doc = m.inherited_doc"""
_RIVAL_DROP_PUB = _swap(_BASE, _GOLD, _RIVAL_DROP_PUB_BODY)

# (rival-drop-owndoc) PARTIAL-DOMAIN: drops the `and not m.has_own_doc` guard.
# CORRECT on every member lacking its own docstring; diverges ONLY on the
# has_own_doc=True sub-domain, OVERWRITING a docstring the member already has.
# Rejection source: Implies(not fills_docstring(Old...), m.doc == Old(m.doc)) on
# the has_own_doc=True, otherwise-eligible sub-domain.
_RIVAL_DROP_OWNDOC_BODY = """    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public):
        m.doc = m.inherited_doc"""
_RIVAL_DROP_OWNDOC = _swap(_BASE, _GOLD, _RIVAL_DROP_OWNDOC_BODY)

# (rival-fill-wrong-value) VALUE divergence: the eligibility decision is GOLD, but
# when eligible the rival assigns 0 ("no docstring") instead of the resolved
# inherited docstring. Rejection source: Implies(fills_docstring(Old...),
# m.doc == Old(m.inherited_doc)) — m.doc==0 != Old(m.inherited_doc) whenever the
# resolved base docstring is non-empty (e.g. inherited_doc=7).
_RIVAL_WRONG_VAL_BODY = """    if ((m.is_callable_member or m.is_computed_attribute)
            and m.is_public and not m.has_own_doc):
        m.doc = 0"""
_RIVAL_WRONG_VAL = _swap(_BASE, _GOLD, _RIVAL_WRONG_VAL_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-reorder-local", "kind": "soundness", "expect": "verify",
     "module": _POS,
     "rationale": "structurally-different but CORRECT: disjunction operands reordered "
                  "(descriptor first) and the whole eligibility decision hoisted into a typed "
                  "local boolean. No loop/fold => no induction lemma needed, gold proof stays "
                  "valid. If it fails to verify the postcondition is over-fit to the gold "
                  "expression form => SPEC-TOO-STRONG."},
    {"id": "pos-guard-clause", "kind": "soundness", "expect": "verify",
     "module": _POS2,
     "rationale": "second correct shape: De Morgan-negated early-return guard then an "
                  "unconditional assign — different control flow, identical behaviour. If it "
                  "fails to verify => SPEC-TOO-STRONG (over-fit to the positive-guard form)."},
    {"id": "admiss-property-self-call", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a self-call apply_inheritance on a freshly-constructed F2P-shaped member "
                  "(public undocumented property: is_computed_attribute=True, the rest as the "
                  "F2P `bar`) must ESTABLISH the precondition (the fresh member holds full Acc, "
                  "so the 1/2 perms split off) and yield the filled docstring (Assert "
                  "probe.doc == 7). If the call site cannot establish the Requires for this "
                  "legitimate input => PRECOND-TOO-STRONG."},

    # ---- frame-mutation rivals (read-only heap input) — must be REJECTED ----
    {"id": "frame-mut-inherited", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_INH,
     "refinement": "keeps the gold decision verbatim but additionally WRITES the read-only "
                   "field m.inherited_doc. There is no faithful real patch: m.inherited_doc "
                   "abstracts the result of the UNCHANGED MRO `getattr` resolution "
                   "(misc.py:533-538) — a real impl that wrote back to that resolution is not "
                   "the gold patch, mutates shared/base state, and would not be the verbatim "
                   "gold hunk that resolves. The rival exists only to satisfy a postcondition "
                   "vacuously by clobbering an input.",
     "rationale": "MANDATORY frame-mutation. m.inherited_doc carries only Acc(...,1/2); a "
                  "write needs FULL permission, so Nagini rejects for INSUFFICIENT PERMISSION "
                  "(and separately it would violate Ensures(m.inherited_doc == Old(...))). If "
                  "it verified the read-only contract would be hollow => the #1 weakness class."},
    {"id": "frame-mut-public", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_PUB,
     "refinement": "supporting frame case: writes the read-only field m.is_public, which "
                   "abstracts is_public_member(key) — a pure function of the dict KEY, never "
                   "reassigned by any faithful patch. A real impl mutating the public flag is "
                   "not the gold hunk and would not resolve.",
     "rationale": "frame-mutation on a second read-only field. Acc(m.is_public, 1/2) => a "
                  "write is INSUFFICIENT PERMISSION (also violates Ensures(m.is_public == "
                  "Old(...))). Confirms the half-permission discipline holds on every read-only "
                  "field."},

    # ---- uniqueness / partial-domain rivals (must be REJECTED) ----
    {"id": "rival-drop-descriptor", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_DESC,
     "refinement": "drops the `or m.is_computed_attribute` disjunct — the EXACT pre-patch "
                   "isfunction-only guard (model_prepatch.py). Its faithful real patch is the "
                   "pre-patch `if (inspect.isfunction(val) and is_public_member(key) and "
                   "val.__doc__ is None)`, which on a property gives isfunction(prop)=False "
                   "(G-AX) => the docstring is NOT filled, so the F2P assert "
                   "`Subclass.bar.__doc__ == \"BAR\"` FAILS. It would NOT resolve.",
     "rationale": "THE F2P-discriminating bug. Rejection source: Ensures(Implies("
                  "fills_docstring(Old...), m.doc == Old(m.inherited_doc))) (model.py:116-119) "
                  "— for a public undocumented property fills_docstring is True yet m.doc is "
                  "left unchanged. If it verified => SPEC-TOO-WEAK (admits the original bug)."},
    {"id": "rival-fill-always", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FILL_ALL,
     "refinement": "drops the whole eligibility guard and fills unconditionally. Its faithful "
                   "real patch sets `val.__doc__ = super_method.__doc__` for EVERY member — "
                   "including private members and members that already define their own "
                   "docstring — clobbering documented members. That would break the "
                   "`Subclass.__call__.__doc__ == \"FOO\"`/own-docstring expectations and is "
                   "plainly not the gold hunk; it would not resolve faithfully.",
     "rationale": "Rejection source: Ensures(Implies(not fills_docstring(Old...), m.doc == "
                  "Old(m.doc))) (model.py:121-124) — for an ineligible member the rival sets "
                  "m.doc to Old(m.inherited_doc) != Old(m.doc). If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-drop-public", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_PUB,
     "refinement": "PARTIAL-DOMAIN: drops `and m.is_public`. Correct on every public member; "
                   "diverges only on the PRIVATE sub-domain, filling a non-public member's "
                   "docstring. Its faithful real patch removes `is_public_member(key)` from the "
                   "guard, so leading-underscore (private) members get base docstrings copied "
                   "in — a behavioural regression vs the gold guard; not the gold hunk, would "
                   "not resolve faithfully.",
     "rationale": "partial-domain on the is_public=False sub-domain. Rejection source: "
                  "Ensures(Implies(not fills_docstring(Old...), m.doc == Old(m.doc))) "
                  "(model.py:121-124). If it verified => SPEC-TOO-WEAK (domain-incomplete)."},
    {"id": "rival-drop-owndoc", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DROP_OWNDOC,
     "refinement": "PARTIAL-DOMAIN: drops `and not m.has_own_doc`. Correct on every member "
                   "lacking its own docstring; diverges only on the has_own_doc=True "
                   "sub-domain, OVERWRITING a docstring the member already defines. Its "
                   "faithful real patch removes `val.__doc__ is None` from the guard, "
                   "clobbering members' own docstrings with the base's — the exact behaviour "
                   "the `val.__doc__ is None` guard exists to prevent; not the gold hunk, would "
                   "not resolve faithfully.",
     "rationale": "partial-domain on the has_own_doc=True sub-domain. Rejection source: "
                  "Ensures(Implies(not fills_docstring(Old...), m.doc == Old(m.doc))) "
                  "(model.py:121-124). If it verified => SPEC-TOO-WEAK (domain-incomplete)."},
    {"id": "rival-fill-wrong-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_VAL,
     "refinement": "the eligibility decision is GOLD, but when eligible the rival assigns 0 "
                   "(no docstring) instead of the resolved inherited docstring. Its faithful "
                   "real patch sets `val.__doc__ = None` instead of `super_method.__doc__`, so "
                   "the inherited docstring is never copied and the F2P assert "
                   "`Subclass.bar.__doc__ == \"BAR\"` FAILS (it would be None). It would NOT "
                   "resolve.",
     "rationale": "value divergence on the assigned docstring. Rejection source: "
                  "Ensures(Implies(fills_docstring(Old...), m.doc == Old(m.inherited_doc))) "
                  "(model.py:116-119) — m.doc==0 != Old(m.inherited_doc) for any non-empty "
                  "resolved base docstring. If it verified => SPEC-TOO-WEAK (assigns wrong "
                  "value)."},
]

# ===========================================================================
# AXIOM LANE — none. meta.axioms == [] (no @ContractOnly axiom is consumed). The
# three introspection callees are A-reference deep models (bool fields validated
# == the real inspect.isfunction / inspect.isdatadescriptor / is_public_member by
# axiom_check.py / G-AX, run in-container, already pass). There is no Nagini-side
# axiom Ensures the proof unfolds, hence no axiom-soundness / containment
# obligation for the PBT runner to discharge. See the StructuredOutput assessment.
# ===========================================================================
AXIOM_TESTS = []
