"""properties.py — PBT falsification manifest for matplotlib__matplotlib-25287.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template.

--- the defended surface ----------------------------------------------------

Two structurally-IDENTICAL contracted functions (one per independently-observable
site, XAxis / YAxis):

    offset_color_primary(base_color: List[int], label_color: List[int]) -> List[int]
    offset_color_secondary(base_color: List[int], label_color: List[int]) -> List[int]

Both take TWO READ-ONLY inputs:

    Requires(Acc(list_pred(base_color), 1/2))
    Requires(Acc(list_pred(label_color), 1/2))

and return a fresh list. The load-bearing post-conditions (verbatim) are:

    Ensures(Acc(list_pred(base_color), 1/2))         # frame: inputs kept read-only
    Ensures(Acc(list_pred(label_color), 1/2))        # frame: inputs kept read-only
    Ensures(Acc(list_pred(Result())))                # owns a fresh result
    Ensures(ToSeq(Result()) == effective_color(ToSeq(base_color), ToSeq(label_color)))
    Ensures(Implies(ToSeq(label_color) == sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(base_color)))      # sentinel branch pin
    Ensures(Implies(ToSeq(label_color) != sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(label_color)))     # ordinary branch pin

where `effective_color` is a @Pure helper FULLY UNFOLDED over the inputs
(label_color except base_color when label_color == sentinel_inherit()) and
`sentinel_inherit()` is the @Pure constant PSeq(105,110,104,101,114,105,116) =
the code points of "inherit".

What the spec defends, and the attacks it must survive:

  * GROUNDED ORACLE, NOT an answer-key. `effective_color` is a deterministic
    @Pure function of the two inputs, fully unfolded (it is literally the
    if/else). There is no opaque marker an impl could echo without doing the
    work: ANY result equal to effective_color(base,label) IS the correct value
    by construction. So the classic "ungrounded-oracle echo" attack does NOT
    apply here — there is no WRONG echo. We instead include an honest
    cheapest-impl positive control that returns effective_color materialized
    (echo-honest), which MUST verify; if it could not, the oracle pin would be
    self-inconsistent (SPEC-TOO-STRONG). (Documented in 'assessment'.)

  * BOTH INPUTS ARE READ-ONLY (Acc(.,1/2)). This makes FRAME-MUTATION mandatory:
    a rival whose impl WRITES to base_color / label_color (e.g. item-assignment
    base_color[0]=...) to build its answer cannot return the half-permission it
    was lent and must be REJECTED for INSUFFICIENT PERMISSION. A byte-fuzzer
    never thinks to mutate the input; this is the project's #1 weakness class.
    The gold invariants are kept verbatim so the rejection is attributable to
    the write, not to a tampered spec.

  * BOTH BRANCHES ARE PINNED. The sentinel branch (label==inherit => base) and
    the ordinary branch (label!=inherit => label) are each pinned by an explicit
    Implies. A rival correct on ONE branch but wrong on the other (partial
    domain) must be rejected by the other branch's clause. The pre-patch bug —
    always taking base_color, ignoring the configured label colour — is exactly
    such a partial-domain rival (correct on the sentinel sub-domain, wrong on
    the ordinary sub-domain).

  * NO AXIOMS. The changed operation is a two-way conditional selection between
    two already-available colour values, expressed DIRECTLY (no @ContractOnly
    callee, no deep model, no axiom_check.py — G-AX vacuous). Hence
    AXIOM_TESTS = [].

  * TERMINATION IS DEMANDED. Both methods carry Requires(MustTerminate(n)) in
    their pre-conditions region (primary 2, secondary 6), so what the verifier
    proves is TOTAL correctness: an impl that never reaches the return no longer
    satisfies the Ensures vacuously. Neither method owns a loop, so there is no
    loop measure to state — the obligation is entirely method-level, and it is
    the CALL structure it constrains. The levels are ordinals and must strictly
    decrease across a call; primary < secondary, so a call may go
    secondary -> primary but never the reverse and never a self-call. That is
    load-bearing, not decorative: a spliced `while spin >= 0: spin = spin + 1`
    ahead of the return VERIFIES with the obligation removed and is REJECTED
    with it ("Obligation leak check failed. Loop might not take all unsatisfied
    obligations from the context."). It also decides where the admissibility
    probe may sit; see (P4).

Authoring mechanics: the two impl bodies are BYTE-IDENTICAL (one per site), so
every ATTACK is built by `_swap_both`, which replaces BOTH gold impl bodies
(count == 2) with the variant body — editing ONLY inside the two
`# impl-start`/`# impl-end` regions. `markers.same_spec` is therefore guaranteed
(the spec view elides the impl regions) and a rejection comes from the
POST-CONDITION / PERMISSION system catching wrong behaviour, never from a
tampered spec. Each rival attacks both sites symmetrically, matching the two
F2P tests (test_xaxis_offsetText_color / test_yaxis_offsetText_color), which
observe the identical rule at the two sites.

The one exception is the admissibility probe (P4), spliced at a SINGLE site by
`_swap_secondary_only`. Both-sites symmetry is right for an attack, which must
be wrong at both observable sites; a probe that CALLS one of the two methods is
not an attack, and duplicating it turns the call into a self-call that cannot
satisfy the termination obligation. See `_swap_secondary_only` and (P4).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25287"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap_both(src: str, old: str, new: str) -> str:
    """Replace BOTH occurrences of an impl-region body (one per identical site).

    The two functions offset_color_primary / offset_color_secondary have
    byte-identical gold impl bodies, so the gold body appears exactly twice and
    both lie strictly inside an impl region. Replacing both keeps `same_spec`
    (the spec view elides impl) while applying the attack/control symmetrically
    to both sites. Asserts the count so silent drift (model.py edited) fails
    loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 2:
        raise AssertionError(
            f"properties.py: expected the gold body twice (one per site), "
            f"found {src.count(old)}: {old!r}")
    return src.replace(old, new)


def _swap_secondary_only(src: str, old: str, new: str) -> str:
    """Replace ONLY the second (secondary-site) occurrence of the gold body.

    Used by the admissibility probe alone. Every ATTACK is applied to both
    sites by `_swap_both`, because a rival must be wrong at both
    independently-observable sites. A self-call probe is not an attack, and
    applying it to both sites is not symmetry but a bug: the probe calls
    `offset_color_primary`, so splicing it into BOTH bodies makes
    `offset_color_primary` call ITSELF unconditionally — unbounded recursion.
    Under `Requires(MustTerminate(n))` Nagini correctly refuses that
    (`Obligation leak check failed. Callee offset_color_primary might not take
    all unsatisfied obligations from the caller.`), since a level must strictly
    decrease across a call and no level strictly exceeds itself.

    So the probe goes at the SECONDARY site (level 6) and calls the PRIMARY one
    (level 2): 6 > 2 gives the callee the room its own obligation needs, and the
    call is to a *different* method, so the call graph is acyclic and the probe
    demonstrably terminates. This still drives the real precondition with a real
    materialized input, which is the whole point of the admissibility lane.
    Asserts the count so drift in model.py fails loudly at load."""
    if src.count(old) != 2:
        raise AssertionError(
            f"properties.py: expected the gold body twice (one per site), "
            f"found {src.count(old)}: {old!r}")
    cut = src.rindex(old)
    return src[:cut] + new + src[cut + len(old):]


# The gold impl body, identical in both functions (verbatim from model.py).
_GOLD_BODY = """    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (P1) Structurally-DIFFERENT but CORRECT: reorder the branches so the ORDINARY
# (non-sentinel) case is tested first. Same selection, mirror-image control
# flow. No induction/lemma needed (no loop, no fold; just an if/else over a
# fixed @Pure equality), so the gold proof stays valid. If this fails to verify,
# the postcondition is over-fit to one branch ordering => SPEC-TOO-STRONG.
_POS_REORDERED_BODY = """    if ToSeq(label_color) != sentinel_inherit():
        tick_color = list(label_color)  # type: List[int]
    else:
        tick_color = list(base_color)
    return tick_color"""
_POS_REORDERED = _swap_both(_BASE, _GOLD_BODY, _POS_REORDERED_BODY)

# (P2) Structurally-DIFFERENT but CORRECT: single-assignment shape. Initialise
# tick_color to the ordinary (label) colour, then OVERRIDE it to the base colour
# only on the sentinel. A different executable shape (one local, one conditional
# reassign) for the same value. If it fails to verify the spec is over-fit to
# the explicit if/else literal form => SPEC-TOO-STRONG.
_POS_SINGLE_BODY = """    tick_color = list(label_color)  # type: List[int]
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)
    return tick_color"""
_POS_SINGLE = _swap_both(_BASE, _GOLD_BODY, _POS_SINGLE_BODY)

# (P3) ECHO-HONEST. The only "oracle" is the @Pure effective_color, which is
# GROUNDED in the inputs (fully unfolded if/else). There is no WRONG echo: the
# only value satisfying ToSeq(Result()) == effective_color(...) is the correct
# colour. This control is the gold impl with an extra Assert immediately before
# the return that the colour it built equals the oracle. It is CORRECT (redundant
# with the gold proof) and MUST verify; its purpose is to demonstrate the spec is
# NOT echo-vulnerable. If it failed, the oracle pin would be self-inconsistent
# (=> SPEC-TOO-STRONG).
_POS_ECHO_BODY = """    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    Assert(ToSeq(tick_color) == effective_color(ToSeq(base_color), ToSeq(label_color)))
    return tick_color"""
_POS_ECHO = _swap_both(_BASE, _GOLD_BODY, _POS_ECHO_BODY)

# (P4) ADMISSIBILITY. Drive the precondition with a freshly-constructed,
# F2P-shaped input: a call on two literal colour lists (base = "yellow" code
# points, label = "blue" code points), both of which the impl fully owns (full
# permission), so the call site can give the half-permission the Requires asks
# for. If the call cannot establish Requires(Acc(list_pred(.),1/2)) for a normal
# materialized colour-name input => PRECOND-TOO-STRONG. Edits only the impl
# region (the probe is placed at the head of the body; its result is discarded;
# the gold work then runs unchanged).
#
# TERMINATION. The spec now carries Requires(MustTerminate(n)), so the probe's
# call must also prove it terminates, and that constrains WHERE the probe may go.
# A MustTerminate level must strictly decrease across a call, so this case is
# spliced at ONE site only (`_swap_secondary_only`): the probe sits in
# offset_color_secondary (level 6) and calls offset_color_primary (level 2).
# 6 > 2 leaves the callee the room its own obligation needs, and the callee is a
# DIFFERENT method, so the call graph stays acyclic.
#
# Splicing it into both bodies (the old `_swap_both`) made
# offset_color_primary call ITSELF unconditionally, i.e. unbounded recursion, and
# Nagini rightly rejected it ("Obligation leak check failed. Callee
# offset_color_primary might not take all unsatisfied obligations from the
# caller."): no level strictly exceeds itself. That rejection was a true report
# about the PROBE's own non-termination, never evidence that the precondition
# rejects an F2P-shaped input — so the fix is to make the probe terminate, not to
# weaken the precondition or drop the case.
_ADMISS_BODY = """    probe_base = [121, 101, 108, 108, 111, 119]  # type: List[int]
    probe_label = [98, 108, 117, 101]  # type: List[int]
    _probe = offset_color_primary(probe_base, probe_label)
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color"""
_ADMISS = _swap_secondary_only(_BASE, _GOLD_BODY, _ADMISS_BODY)


# ===========================================================================
# FRAME-MUTATION RIVAL (mandatory; both inputs read-only) — expect "reject"
# ===========================================================================

# (F1) FRAME-MUTATION. Before returning the correct colour, item-assign into the
# read-only base_color input (base_color[0] = 0). base_color is lent at
# Acc(list_pred(base_color), 1/2); item-assignment needs FULL write permission,
# which the impl does not hold, so it CANNOT verify and CANNOT re-establish
# Ensures(Acc(list_pred(base_color), 1/2)). The returned value is still the gold
# colour, so this fails ONLY for INSUFFICIENT PERMISSION on a read-only input —
# the rejection is attributable to the write, not to wrong output. A byte-fuzzer
# never constructs this.
_FRAME_BODY = """    if len(base_color) > 0:
        base_color[0] = 0  # WRITE to read-only Acc(list_pred(base_color),1/2) input
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color"""
_FRAME = _swap_both(_BASE, _GOLD_BODY, _FRAME_BODY)


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) PREPATCH BEHAVIOUR / partial-domain. The exact pre-gold bug
# (model_prepatch.py / model_prepatch_2.py): ALWAYS take the base colour,
# ignoring the configured label colour. Correct on the sentinel sub-domain
# (label==inherit => base, which is what gold also returns) but WRONG on the
# ordinary sub-domain (label!=inherit must return label). Rejected by
# Implies(label != inherit, Result == label). This is the G-DIFF differential
# witness and precisely what the F2P tests observe (a non-'inherit' label colour
# must reach the offset text).
_U_BASE_ALWAYS_BODY = """    tick_color = list(base_color)  # type: List[int]
    return tick_color"""
_U_BASE_ALWAYS = _swap_both(_BASE, _GOLD_BODY, _U_BASE_ALWAYS_BODY)

# (U2) LABEL-ALWAYS / partial-domain (the OPPOSITE half-bug). Drop the sentinel
# fallback entirely: ALWAYS take the label colour. Correct on the ordinary
# sub-domain (label!=inherit => label) but WRONG on the sentinel sub-domain,
# where the offset text must fall back to the base colour (gold returns base when
# label=='inherit'). Rejected by Implies(label == inherit, Result == base):
# when label_color == sentinel_inherit() this returns the literal code points of
# "inherit" instead of the base colour. The F2P second assertions
# (xtick.color='yellow', labelcolor='inherit' => offsetText 'yellow') fail.
_U_LABEL_ALWAYS_BODY = """    tick_color = list(label_color)  # type: List[int]
    return tick_color"""
_U_LABEL_ALWAYS = _swap_both(_BASE, _GOLD_BODY, _U_LABEL_ALWAYS_BODY)

# (U3) INVERTED SENTINEL TEST / control-flow flip. Use `!=` where the gold uses
# `==`: take the BASE colour when label != inherit and the LABEL colour when
# label == inherit — the branches selected on the wrong condition. Wrong on BOTH
# sub-domains: violates Implies(label==inherit, Result==base) (returns the
# "inherit" code points) AND Implies(label!=inherit, Result==label) (returns
# base). A real patch with the comparison inverted would mis-colour every offset
# text and FAIL both F2P assertions. Rejection source: both Implies clauses.
_U_INVERTED_BODY = """    if ToSeq(label_color) != sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color"""
_U_INVERTED = _swap_both(_BASE, _GOLD_BODY, _U_INVERTED_BODY)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reordered", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDERED,
     "rationale": "structurally-different (ordinary branch first, sentinel branch second) but "
                  "CORRECT impl with the same selection must verify; no induction lemma is needed "
                  "(a single if/else over a @Pure equality, no loop/fold). If it fails to verify "
                  "the postcondition is over-fit to one branch ordering => SPEC-TOO-STRONG."},
    {"id": "pos-control-single-assign", "kind": "soundness", "expect": "verify",
     "module": _POS_SINGLE,
     "rationale": "a correct impl with a different executable shape — initialise tick_color to "
                  "the label colour, then override to base only on the sentinel — must verify. "
                  "Both branch-paths still produce effective_color(base,label). If it fails the "
                  "spec is over-fit to the explicit if/else literal form => SPEC-TOO-STRONG."},
    {"id": "echo-honest", "kind": "soundness", "expect": "verify",
     "module": _POS_ECHO,
     "rationale": "the only oracle (the @Pure effective_color pin) is GROUNDED in the inputs "
                  "(fully unfolded if/else); there is no WRONG echo. Asserting that the built "
                  "colour equals effective_color(base,label) immediately before the return is "
                  "redundant with the gold proof and must verify. Demonstrates the spec is NOT "
                  "echo-vulnerable (no wrong oracle echo could verify)."},
    {"id": "admiss-f2p-shaped", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "a call on a freshly-built F2P-shaped input (base='yellow' code points, "
                  "label='blue' code points), which the impl fully owns, must establish the "
                  "precondition Requires(Acc(list_pred(.),1/2)) AND Requires(MustTerminate(n)) "
                  "for a normal materialized colour-name input. If it cannot => "
                  "PRECOND-TOO-STRONG (the precondition rejects a representative F2P input). "
                  "Spliced at the secondary site ONLY, so the probe calls the OTHER method "
                  "(secondary level 6 -> primary level 2, strictly decreasing, acyclic): a "
                  "both-sites splice would make the probe call itself and fail the obligation "
                  "leak check for its OWN unbounded recursion, which would say nothing about "
                  "whether the precondition admits the input."},

    # ---- frame-mutation rival (must be REJECTED for insufficient permission) ----
    {"id": "frame-mutation-base", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME,
     "refinement": "item-assigning base_color[0] is NOT a faithful patch of the gold hunk: the "
                   "real code reads mpl.rcParams['xtick.color'] / ['ytick.color'] (a borrowed "
                   "colour-name value) and never mutates it. A real patch that overwrote that "
                   "rcParam in place would corrupt the shared configuration for every other "
                   "consumer (tick labels, axis labels) and break unrelated P2P tests; it would "
                   "NOT be the gold fix and would NOT resolve the F2P cleanly.",
     "rationale": "Rejection source: the PERMISSION system. base_color is lent at "
                  "Acc(list_pred(base_color),1/2); item-assignment needs full write permission, "
                  "which the impl does not hold, so it cannot verify and cannot re-establish "
                  "Ensures(Acc(list_pred(base_color),1/2)). The returned value is still the gold "
                  "colour, so the failure is attributable to the write, not to wrong output. If "
                  "it VERIFIED, the read-only frame condition would be vacuous (SPEC-TOO-WEAK)."},

    # ---- uniqueness / partial-domain rivals (must be REJECTED) ----
    {"id": "rival-base-always-prepatch", "kind": "uniqueness", "expect": "reject",
     "module": _U_BASE_ALWAYS,
     "refinement": "this is the exact pre-gold behaviour (model_prepatch.py / model_prepatch_2.py): "
                   "color=mpl.rcParams['<axis>tick.color'] unconditionally, ignoring "
                   "['<axis>tick.labelcolor']. F2P test_xaxis_offsetText_color asserts that with "
                   "xtick.labelcolor='blue' the offsetText is 'blue'; this code keeps it the base "
                   "color, so the unpatched behaviour does NOT resolve (the G-DIFF witness).",
     "rationale": "partial-domain: correct on the sentinel sub-domain (label==inherit => base) "
                  "but WRONG on the ordinary sub-domain. Rejected by Implies(label != inherit, "
                  "Result == label) — when label!=inherit it returns base, not label. If it "
                  "verified => SPEC-TOO-WEAK (admits the original bug)."},
    {"id": "rival-label-always", "kind": "uniqueness", "expect": "reject",
     "module": _U_LABEL_ALWAYS,
     "refinement": "drops the sentinel fallback: color=mpl.rcParams['<axis>tick.labelcolor'] "
                   "unconditionally. When labelcolor=='inherit' the real Text.set_color('inherit') "
                   "stores the literal string 'inherit' (NOT the base color); F2P "
                   "test_xaxis_offsetText_color's second assertion (xtick.color='yellow', "
                   "labelcolor='inherit' => offsetText 'yellow') would see 'inherit' and FAIL, so "
                   "this patch would NOT resolve.",
     "rationale": "partial-domain (the opposite half): correct on the ordinary sub-domain "
                  "(label!=inherit => label) but WRONG on the sentinel sub-domain. Rejected by "
                  "Implies(label == inherit, Result == base) — when label==sentinel_inherit() it "
                  "returns the 'inherit' code points, not base_color. If it verified => "
                  "SPEC-TOO-WEAK (the sentinel fallback clause would be unenforced)."},
    {"id": "rival-inverted-sentinel", "kind": "uniqueness", "expect": "reject",
     "module": _U_INVERTED,
     "refinement": "inverts the sentinel comparison (!= where gold uses ==): a faithful patch of "
                   "this shape writes `mpl.rcParams['xtick.color'] if labelcolor!='inherit' else "
                   "mpl.rcParams['xtick.labelcolor']` — the branches selected on the wrong "
                   "condition. With labelcolor='blue' it picks xtick.color and with "
                   "labelcolor='inherit' it picks the 'inherit' string; both F2P assertions fail, "
                   "so it would NOT resolve.",
     "rationale": "wrong on BOTH sub-domains: violates Implies(label==inherit, Result==base) "
                  "(returns the 'inherit' code points) and Implies(label!=inherit, Result==label) "
                  "(returns base). Rejection source: both Implies clauses. If it verified => "
                  "SPEC-TOO-WEAK (the conditional direction would be unconstrained)."},
]

# ===========================================================================
# AXIOM LANE — none. The changed operation is a direct two-way conditional
# selection between two already-available colour values; no @ContractOnly axiom,
# no deep model, no library callee abstracted (refinement.md §C; mapping.md §3;
# G-AX vacuous). Nothing to probe in Docker.
# ===========================================================================
AXIOM_TESTS = []
