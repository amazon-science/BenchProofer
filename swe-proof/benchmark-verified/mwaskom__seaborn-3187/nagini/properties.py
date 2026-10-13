"""properties.py -- PBT falsification manifest for mwaskom__seaborn-3187.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See docs/PBT_PLAN.md (esp. section 2 "four
falsification checks" and section 4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template.

What the spec defends
---------------------
Two structurally-identical modeled functions build a numeric legend from the
tick locations `locs`, rendering each entry's label text with the tick formatter
`fmt` they are handed:

    legend_values_continuous(fmt: TickFormatter, locs: List[int]) -> List[int]
    legend_values_locator(fmt:    TickFormatter, locs: List[int]) -> List[int]

`fmt` is SHARED MUTABLE STATE that arrives already built, in whatever
residual-rendering mode it happens to be in (enabled is the ordinary default),
with whatever rendering convention it was built with, and attached to an axis of
whatever numeric RANGE, and it outlives the call.  That range is a second input
the formatter reads when deciding how to write a tick, and it is INDEPENDENT of
the tick locations (a legend's ticks are chosen inside its variable's range, and
the range is normally wider than them).  A LABEL is an opaque `int` code standing for its exact TEXT: the model may
not see a label as the number it reads back to, because two different texts can
read back to the same number and it is the text the legend keeps.  The
LOAD-BEARING postcondition clauses are:

  (P1) len(Result()) == len(locs)
        one label per tick -- none dropped, none invented.
  (P2) ToSeq(Result()) == rendered_labels(fmt.convention, ToSeq(locs),
                                          fmt.residual, fmt.view_lo,
                                          fmt.view_hi)
        the labels are EXACTLY the ones THAT formatter renders for THIS WHOLE
        tick set, in this order, in the mode the call leaves it in, AGAINST THE
        RANGE OF THE AXIS IT IS ATTACHED TO.  Whole sequence, whole tick set: a
        formatter picks ONE way of writing all the ticks it is given, so a tick's
        label is not a function of that tick alone.  This clause is what rules
        out text written by a private route, text rendered for a different tick
        set or one tick at a time, text rendered against a different axis range
        (the span of the tick set included), and any reordering or dropping.
  (P3) not fmt.residual
        the formatter is LEFT with residual rendering disabled -- the object
        goes on rendering this same axis after the call.
  (P4) fmt.convention == Old(fmt.convention)
        the rendering convention is not the builder's to change.  Without it an
        implementation could rewrite the convention and make P5 vacuous instead
        of delivering it.
  (P4b) fmt.view_lo == Old(fmt.view_lo) and fmt.view_hi == Old(fmt.view_hi)
        nor is the range of the axis rendered against: it is settled before the
        legend is built.  Without it an implementation could widen or narrow the
        range and then render honestly against the range it chose, which would
        make P2 satisfiable while the legend's text no longer matched the axis
        the formatter goes on rendering.
  (P5) Implies(fmt.convention == 0,
               legend_reads_ticks(ToSeq(Result()), ToSeq(locs)))
        for the full-value convention every label reads back to the FULL value
        of its tick -- no residual lost -- stated over the whole label sequence,
        because the failure being ruled out factors a magnitude out of all of
        them at once.

P2 and P3 are inseparable and are what make the spec sense the required
behaviour rather than merely the returned values.  P3 alone is satisfiable by
configuring the formatter and then ignoring it; P2 alone is satisfiable by a
formatter still factoring a magnitude out.  P5 alone is satisfiable by writing
the numbers in directly -- which is exactly what P2 forbids, since no private
route produces the formatter's own text.

Read-only input, writable formatter
-----------------------------------
`Requires(Acc(list_pred(locs), 1/2))` -- HALF permission.  `locs` is a read-only
input, so the frame-mutation probe is MANDATORY: a rival that WRITES to `locs`
(append / element-store) must be rejected for INSUFFICIENT PERMISSION (it holds
only 1/2 of list_pred(locs), and list mutation needs full).  The gold invariants
are kept VERBATIM in those rivals so the rejection is attributable to the write.

`fmt.residual` is held at FULL permission on purpose: putting the formatter into
the non-residual mode IS part of the required behaviour (P3), so the spec must
permit that write.  What it must not permit is leaving it enabled -- nor writing
`fmt.convention`, which P4 pins, nor `fmt.view_lo` / `fmt.view_hi`, which P4b
pins.  All three are writable in the permission system and pinned in the
postcondition, so a rival CAN attempt them and must be rejected for what it did,
not for lacking permission to try.

Ungrounded-oracle echo
----------------------
The oracle in P2 is `rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
fmt.view_lo, fmt.view_hi)` -- uninterpreted apart from its length and, for the
full-value convention with residual rendering disabled, the readings of its
members.  So there is no value an implementation can write into the legend that
is PROVABLY the formatter's text unless it obtained it from `rendered_labels` at
the right convention, the right whole tick set, the right mode AND the right axis
range.  The echo family below probes every way of getting one of those four wrong
(a private route, another tick set, the other mode, the convention the guarantee
wants rather than the one the formatter has, another interval, and the interval
derived from the tick set itself), and each must be rejected.

Termination
-----------
`Requires(MustTerminate(3))` / `(4)`: the legend must actually be BUILT.  Without
it every clause above is claimed only of runs that reach the return, so a build
that never finishes would satisfy them all vacuously.  The `nonterminating-build`
rival is the probe that keeps that obligation honest.

Axiom lane
----------
`reading` and `rendered_labels` are `@Pure @ContractOnly` deep models, validated
against the REAL `matplotlib` formatters by axiom_check.py (G-AX).  The
AXIOM_TESTS below re-run the real callees in Docker:
  * axiom-soundness -- one label per tick for every convention, mode and axis
    range through both formatter APIs; the full-value convention with residual
    rendering disabled reads back to full ticks on every range, including ranges
    that do not contain the ticks; with it enabled the same formatter
    demonstrably does not (the `not residual` hypothesis is load-bearing); a
    label's TEXT carries strictly more than its reading and depends on the whole
    tick set (the opaque-text carrier and the set-valued signature justified);
    and the label sequence MOVES when only the axis range moves, so the range
    arguments of the deep model are load-bearing and a refinement may not render
    against the tick set's own span instead;
  * axiom-containment -- every callee input the MODEL can reach lies in the
    callee's domain, and the ONE measured exception is reported as a declared
    BOUND plus an exact measurement: only a convention that chooses its unit
    from the WIDTH of the axis range may lack a label sequence for a range of no
    width (measured set reported, possibly empty -- it is matplotlib-version
    dependent), which model.py's `rendered_labels` docstring discloses and
    conformance_check.py checks the refinement and the real site agree on.

Authoring mechanics: every spec variant is built by REGION-SURGERY
(`_swap_impl`) that replaces ONLY the text between one function's
`# impl-start` / `# impl-end`, so `markers.same_spec` is guaranteed and a
rejection comes from the POSTCONDITION / PERMISSION / TERMINATION obligation
catching wrong behaviour, never from a tampered spec.  The two functions share a
byte-identical impl block, so each swap is scoped to a single function by its
unique `def` line and the OTHER function is left gold (so a rival's reject is
attributable to the edited site, and a positive control still has a verifying
partner).  Each `expect:"reject"` rival carries the refinement argument that its
faithful real patch would NOT resolve the F2P.
"""
import re
from pathlib import Path

INSTANCE = "mwaskom__seaborn-3187"
FLOAT_ENCODING = None  # meta.json float_encoding is null (int carrier; not a precision bug)

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()

_FN_CONT = "def legend_values_continuous("
_FN_LOC = "def legend_values_locator("

_IMPL_RE = re.compile(r"( *# impl-start\n)(.*?)( *# impl-end)", re.S)


def _swap_impl(src: str, fn_anchor: str, new_body: str) -> str:
    """Replace the whole impl region of ONE modeled function (located by its
    unique `def` line) with `new_body`. The two functions have byte-identical
    impl blocks, so scoping the swap to one function keeps the edit unique and
    leaves the other function gold. Asserts the region is found so silent drift
    (model.py edited) fails loudly at load."""
    start = src.index(fn_anchor)
    nxt = src.find("\ndef ", start + 1)
    end = nxt if nxt != -1 else len(src)
    body = src[start:end]
    m = _IMPL_RE.search(body)
    if m is None:
        raise AssertionError(f"properties.py drift: no impl region in "
                             f"{fn_anchor!r}")
    new = body[:m.start(2)] + new_body + body[m.end(2):]
    return src[:start] + new + src[end:]


def _gold_impl(src: str) -> str:
    """The gold impl body, read out of model.py rather than duplicated here, so
    the battery cannot drift away from the spec it is testing."""
    bodies = [m.group(2) for m in _IMPL_RE.finditer(src)]
    if len(bodies) != 2 or bodies[0] != bodies[1]:
        raise AssertionError("properties.py drift: expected two byte-identical "
                             "impl regions in model.py")
    return bodies[0]


_GOLD_IMPL = _gold_impl(_BASE)

# The gold prologue: snapshot the rendering convention and the axis range (so P4
# and P4b survive the loop's havoc) and put the formatter into the non-residual
# mode (P3).
_SNAP = """    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
"""
_GOLD_HEAD = _SNAP + """    fmt.residual = False
"""
assert _GOLD_IMPL.startswith(_GOLD_HEAD), "properties.py drift: gold prologue"

# The invariant block every rival splices on, minus the clauses each rival has
# to change. Kept as text so a rival's own invariants are visible in the record.
_INV_HEAD = """        # invariants-start
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(locs))
        Invariant(len(result) == i)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
"""
_INV_TAIL = """        Invariant(MustTerminate(len(locs) - i + 1))
        # invariants-end
"""
_APPEND = """        old_seq = ToSeq(result)
        result.append(lab)
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
"""
_RES_OFF = "        Invariant(not fmt.residual)\n"
_CONV_PIN = "        Invariant(fmt.convention == conv0)\n"
_SEQ_INV = ("        Invariant(ToSeq(result) == rendered_labels(fmt.convention,\n"
            "            ToSeq(locs), fmt.residual, fmt.view_lo,\n"
            "            fmt.view_hi).take(i))\n")
_GOLD_LAB = ("        lab = rendered_labels(fmt.convention, ToSeq(locs),\n"
             "                              fmt.residual, fmt.view_lo,\n"
             "                              fmt.view_hi)[i]\n")


def _body(head, extra_inv, get_lab, tail="    return result\n",
          guard="    while i < len(locs):\n", append=_APPEND):
    """Assemble an impl body: prologue, loop with invariants, label choice,
    append, epilogue. Every rival differs from gold in exactly the pieces its
    entry names."""
    return (head + "    result = []  # type: List[int]\n    i = 0\n"
            + guard + _INV_HEAD + extra_inv + _INV_TAIL + get_lab + append
            + tail)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) -- expect "verify"
# ===========================================================================

# (1) STRUCTURALLY-DIFFERENT but CORRECT, applied to legend_values_locator.
# Renders the whole tick set ONCE into a local label sequence before the loop and
# copies out of it, instead of asking for the sequence each pass; configures the
# formatter BEFORE snapshotting the convention (the opposite order to gold); and
# drops gold's `old_seq` / `Assert` framing scaffolding and the `lab` temporary
# entirely. Behaviourally identical to gold (the sequence is the same sequence).
# If this fails to verify, the postcondition is over-fit to the gold local-
# variable shape, to the gold order of the two prologue statements, or to
# re-deriving the label sequence per iteration => SPEC-TOO-STRONG.
_POS_PRECOMPUTED_BODY = """    fmt.residual = False
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    labs = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                           fmt.view_lo, fmt.view_hi)
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        # invariants-start
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(locs))
        Invariant(len(result) == i)
        Invariant(not fmt.residual)
        Invariant(fmt.convention == conv0)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
        Invariant(labs == rendered_labels(fmt.convention, ToSeq(locs),
                                          fmt.residual, fmt.view_lo,
                                          fmt.view_hi))
        Invariant(ToSeq(result) == labs.take(i))
        Invariant(MustTerminate(len(locs) - i + 1))
        # invariants-end
        old_seq = ToSeq(result)
        result.append(labs[i])
        Assert(ToSeq(result) == old_seq + PSeq(labs[i]))
        i = i + 1
    return result
"""
_POS_PRECOMPUTED = _swap_impl(_BASE, _FN_LOC, _POS_PRECOMPUTED_BODY)

# (2) A DIFFERENT LOOP SHAPE, applied to legend_values_continuous: the walk ends
# on `i != len(locs)` rather than `i < len(locs)`, so the loop guard no longer
# has gold's form while the walk is the same walk (the invariant
# `0 <= i and i <= len(locs)` makes the two guards equivalent). Must verify; if
# not, the spec or its measure is over-fit to the gold guard => SPEC-TOO-STRONG.
_POS_GUARD_BODY = _body(_GOLD_HEAD, _RES_OFF + _CONV_PIN + _SEQ_INV, _GOLD_LAB,
                        guard="    while i != len(locs):\n")
_POS_GUARD = _swap_impl(_BASE, _FN_CONT, _POS_GUARD_BODY)

# (3) ADMISSIBILITY. A self-call caller on an in-domain input must establish the
# precondition. Inside legend_values_locator's impl we build a FRESH formatter in
# the state a real one arrives in -- residual rendering ENABLED -- and with a
# NON-DEFAULT rendering convention (so the probe also witnesses that the domain
# was not narrowed to the convention the reading guarantee is stated for), plus a
# fresh F2P-shaped tick list, and call legend_values_continuous on them. If the
# call site cannot establish Requires for such a legitimate input =>
# PRECOND-TOO-STRONG.
_ADMISS_BODY = ("    probe = []  # type: List[int]\n"
                "    probe.append(100000000)\n"
                "    probe_fmt = TickFormatter(7, True, 0, 1000000000)\n"
                "    _vals = legend_values_continuous(probe_fmt, probe)\n"
                "    Assert(len(_vals) == len(probe))\n"
                "    Assert(not probe_fmt.residual)\n"
                "    Assert(probe_fmt.convention == 7)\n"
                "    Assert(probe_fmt.view_lo == 0)\n"
                "    Assert(probe_fmt.view_hi == 1000000000)\n"
                + _GOLD_IMPL)
_ADMISS = _swap_impl(_BASE, _FN_LOC, _ADMISS_BODY)

# (4) VACUITY CONTROL for (3). The same self-call probe with `Assert(False)`
# appended. If the probe's guarantees were unreachable -- an infeasible call site
# proves anything -- this would verify too, and (3) would be certifying nothing.
# It must be REJECTED. Rejection here is what makes (3) evidence.
_ADMISS_VACUITY_BODY = ("    probe = []  # type: List[int]\n"
                        "    probe.append(100000000)\n"
                        "    probe_fmt = TickFormatter(7, True, 0, 1000000000)\n"
                        "    _vals = legend_values_continuous(probe_fmt, probe)\n"
                        "    Assert(len(_vals) == len(probe))\n"
                        "    Assert(not probe_fmt.residual)\n"
                        "    Assert(probe_fmt.convention == 7)\n"
                        "    Assert(probe_fmt.view_lo == 0)\n"
                        "    Assert(probe_fmt.view_hi == 1000000000)\n"
                        "    Assert(False)\n"
                        + _GOLD_IMPL)
_ADMISS_VACUITY = _swap_impl(_BASE, _FN_LOC, _ADMISS_VACUITY_BODY)


# ===========================================================================
# UNIQUENESS / FRAME / TERMINATION RIVALS -- expect "reject"
# ===========================================================================

# (R1, the recorded defect itself) The formatter is LEFT in the rendering mode it
# arrived in -- residual rendering enabled -- and the labels are the ones it
# renders in that mode. Every label really is the formatter's own text, so P1, P2
# and P4 all hold; what fails is P3 (and with it P5, since a formatter still
# factoring a magnitude out renders residuals). This is the arrived-in behaviour
# the twins model.
_LEFT_ENABLED = _swap_impl(_BASE, _FN_CONT, _body(
    _SNAP, _CONV_PIN + _SEQ_INV, _GOLD_LAB))

# (R2, over-approximation / private route) The label is written privately, as the
# tick's own number, with no formatter involved at all. The formatter is left
# correctly configured, so P3, P4 and even P5 are deliverable; P2 is not, because
# nothing makes a privately written number the formatter's text.
_PRIVATE_ROUTE = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN
    + "        Invariant(ToSeq(result) == ToSeq(locs).take(i))\n",
    "        lab = locs[i]\n"))

# (R3, order of operations) Renders with the mode the formatter arrived in, then
# switches residual rendering off afterwards. The state the call LEAVES is gold's,
# so P3 and P4 hold; the labels are residuals, so P2 fails.
_RENDER_THEN_DISABLE = _swap_impl(_BASE, _FN_CONT, _body(
    _SNAP + "    res0 = fmt.residual\n",
    "        Invariant(fmt.residual == res0)\n" + _CONV_PIN + _SEQ_INV,
    _GOLD_LAB, tail="    fmt.residual = False\n    return result\n"))

# (R4, a different tick set) Renders these ticks TOGETHER WITH ONE MORE and uses
# the labels that come back for the ones asked about. Every label is the
# formatter's own text, in the right mode, in order -- but for the wrong set, and
# a formatter picks its way of writing from the set.
_OTHER_TICK_SET = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN
    + "        Invariant(ToSeq(result) == rendered_labels(fmt.convention,\n"
      "            ToSeq(locs) + PSeq(0), fmt.residual, fmt.view_lo,\n"
      "            fmt.view_hi).take(i))\n",
    "        lab = rendered_labels(fmt.convention, ToSeq(locs) + PSeq(0),\n"
    "                              fmt.residual, fmt.view_lo, fmt.view_hi)[i]\n"))

# (R5, boundary token swap) The formatter's own label texts for exactly this tick
# set, ROTATED ONE PLACE: every entry carries a real label, just not its own.
_ROTATED = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN
    + "        Invariant(ToSeq(result) == (rendered_labels(fmt.convention,\n"
      "            ToSeq(locs), fmt.residual, fmt.view_lo,\n"
      "            fmt.view_hi).drop(1)\n"
      "            + rendered_labels(fmt.convention, ToSeq(locs),\n"
      "                              fmt.residual, fmt.view_lo,\n"
      "                              fmt.view_hi).take(1)).take(i))\n",
    "        rot = rendered_labels(fmt.convention, ToSeq(locs),\n"
    "                              fmt.residual, fmt.view_lo,\n"
    "                              fmt.view_hi).drop(1) + rendered_labels(\n"
    "            fmt.convention, ToSeq(locs), fmt.residual, fmt.view_lo,\n"
    "            fmt.view_hi).take(1)\n"
    "        lab = rot[i]\n"))

# (R6, mode token swap) Renders under residual rendering ON while reporting the
# mode off: the state half looks settled and the labels are residuals.
_MODE_SWAP = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN
    + "        Invariant(ToSeq(result) == rendered_labels(fmt.convention,\n"
      "            ToSeq(locs), True, fmt.view_lo, fmt.view_hi).take(i))\n",
    "        lab = rendered_labels(fmt.convention, ToSeq(locs), True,\n"
    "                              fmt.view_lo, fmt.view_hi)[i]\n"))

# (R7, oracle echo) Renders under the convention the reading guarantee is stated
# for rather than the one the formatter actually has -- an echo of P5's guard
# instead of a fact about this formatter.
_CONVENTION_ECHO = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN
    + "        Invariant(ToSeq(result) == rendered_labels(0,\n"
      "            ToSeq(locs), fmt.residual, fmt.view_lo,\n"
      "            fmt.view_hi).take(i))\n",
    "        lab = rendered_labels(0, ToSeq(locs), fmt.residual, fmt.view_lo,\n"
    "                              fmt.view_hi)[i]\n"))

# (R8, the freedom the repair leaves) REWRITES the formatter's rendering
# convention to a non-default one and renders honestly under it. Then P5's guard
# is false and its guarantee is claimed of nothing -- the exact way a repair that
# guarded the reading property could be made vacuous.
_CONVENTION_REWRITE = _swap_impl(_BASE, _FN_CONT, _body(
    "    fmt.convention = 1\n" + _SNAP + "    fmt.residual = False\n",
    _RES_OFF + _CONV_PIN + _SEQ_INV, _GOLD_LAB))

# (R9, partial-domain guard) Delivers the state guarantee only where there is at
# least one tick to render: an empty legend leaves the formatter as it arrived.
_PARTIAL_EMPTY = _swap_impl(_BASE, _FN_CONT, _body(
    _SNAP + "    if len(locs) > 0:\n        fmt.residual = False\n"
    "    res1 = fmt.residual\n",
    "        Invariant(fmt.residual == res1)\n" + _CONV_PIN + _SEQ_INV,
    _GOLD_LAB))

# (R10, partial-domain on length) Drops the LAST tick's label.
_DROP_LAST = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN + _SEQ_INV, _GOLD_LAB,
    guard="    while i < len(locs) - 1:\n"))

# (R11, frame mutation by append) Writes to the read-only input `locs`.
_FRAME_APPEND = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN + _SEQ_INV, _GOLD_LAB,
    append="""        old_seq = ToSeq(result)
        result.append(lab)
        locs.append(lab)
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
"""))

# (R12, frame mutation by element store) Overwrites an element of the read-only
# input in place.
_FRAME_STORE = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN + _SEQ_INV, _GOLD_LAB,
    append="""        old_seq = ToSeq(result)
        result.append(lab)
        locs[i] = lab
        Assert(ToSeq(result) == old_seq + PSeq(lab))
        i = i + 1
"""))

# (R13, non-termination) Builds the legend correctly and then never returns it:
# a second loop spins forever. Every value clause holds of the state it reaches,
# so this is the rival that shows `Requires(MustTerminate(3))` is doing
# independent work -- without it the whole postcondition would be satisfied
# vacuously by a build that produces no legend at all.
_NONTERMINATING = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN + _SEQ_INV, _GOLD_LAB,
    tail="""    spin = 0
    while spin < 1:
        Invariant(Acc(fmt.convention) and Acc(fmt.residual))
        Invariant(Acc(fmt.view_lo) and Acc(fmt.view_hi))
        Invariant(Acc(list_pred(locs), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(spin == 0)
        Invariant(not fmt.residual)
        Invariant(fmt.convention == conv0)
        Invariant(fmt.view_lo == lo0 and fmt.view_hi == hi0)
        Invariant(ToSeq(result) == rendered_labels(fmt.convention,
            ToSeq(locs), fmt.residual, fmt.view_lo, fmt.view_hi))
        spin = 0
    return result
"""))

# (R14, the freedom the repair leaves, second form) REWRITES the range of the
# axis the formatter is attached to and then renders honestly against the range
# it chose. Every label really is that formatter's text for those ticks -- but
# for an axis that is no longer the one the legend accompanies.
_INTERVAL_REWRITE = _swap_impl(_BASE, _FN_CONT, _body(
    "    fmt.view_lo = fmt.view_lo - 1\n"
    "    fmt.view_hi = fmt.view_hi + 1\n" + _SNAP + "    fmt.residual = False\n",
    _RES_OFF + _CONV_PIN + _SEQ_INV, _GOLD_LAB))

# (R15, oracle echo against another interval) Renders against an interval that is
# not the one the formatter is attached to (one unit wider at the top).
_OTHER_INTERVAL = _swap_impl(_BASE, _FN_CONT, _body(
    _GOLD_HEAD, _RES_OFF + _CONV_PIN
    + "        Invariant(ToSeq(result) == rendered_labels(fmt.convention,\n"
      "            ToSeq(locs), fmt.residual, fmt.view_lo,\n"
      "            fmt.view_hi + 1).take(i))\n",
    "        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,\n"
    "                              fmt.view_lo, fmt.view_hi + 1)[i]\n"))

# (R16, oracle echo against the tick set's own span) Derives the interval to
# render against FROM the tick sequence's ends instead of reading the axis's --
# the most tempting confusion, because the ticks are inside the range and a
# legend's tick set looks like a description of it.
_INTERVAL_FROM_TICKS = _swap_impl(_BASE, _FN_CONT, _body(
    _SNAP + "    lo1 = 0\n    hi1 = 0\n"
    "    if len(locs) > 0:\n"
    "        lo1 = locs[0]\n"
    "        hi1 = locs[len(locs) - 1]\n"
    "    fmt.residual = False\n",
    _RES_OFF + _CONV_PIN
    + "        Invariant(ToSeq(result) == rendered_labels(fmt.convention,\n"
      "            ToSeq(locs), fmt.residual, lo1, hi1).take(i))\n",
    "        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,\n"
    "                              lo1, hi1)[i]\n"))


# --- the refutation each reject case shares ---------------------------------
_P2P = ("tests/test_relational.py::TestLinePlotter::test_legend_data")
_MEASURED = (
    "MEASURED on this host with the docker oracle for the recorded attack of "
    "this shape: FAIL_TO_PASS 2/2 pass but PASS_TO_PASS fails 1/248 (%s), whose "
    "assertion is on the exact label TEXT ['0.20','0.22','0.24','0.26','0.28'] "
    "(tests/test_relational.py:866,877) -- so it does NOT resolve." % _P2P)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-precomputed-sequence", "kind": "soundness", "expect": "verify",
     "module": _POS_PRECOMPUTED,
     "rationale": "structurally-different but CORRECT legend_values_locator: renders the whole "
                  "tick set ONCE into a local label sequence and copies out of it instead of "
                  "re-deriving it each pass, configures the formatter before snapshotting the "
                  "convention (the opposite prologue order to gold), and drops the `lab` "
                  "temporary. Behaviourally identical to gold. Must verify; if not, the "
                  "postcondition is over-fit to the gold local-variable shape, to the gold "
                  "order of the two prologue statements, or to re-deriving the sequence per "
                  "iteration => SPEC-TOO-STRONG."},
    {"id": "pos-different-loop-guard", "kind": "soundness", "expect": "verify",
     "module": _POS_GUARD,
     "rationale": "the same walk with the loop ending on `i != len(locs)` instead of "
                  "`i < len(locs)`; the invariant `0 <= i and i <= len(locs)` makes the two "
                  "guards equivalent, and the decreasing measure `len(locs) - i + 1` is "
                  "unchanged. Must verify; if not, the spec or its termination measure is "
                  "over-fit to the gold guard form => SPEC-TOO-STRONG."},
    {"id": "admiss-self-call-arrived-state-nondefault-convention",
     "kind": "admissibility", "expect": "verify", "module": _ADMISS,
     "rationale": "a self-call legend_values_continuous(TickFormatter(7, True), [100000000]) "
                  "must establish the precondition: full permission on the fresh formatter's "
                  "fields and Acc(list_pred(locs), 1/2) on the fresh list. The probe formatter "
                  "is in the state a real one ARRIVES in (residual rendering enabled) and "
                  "carries a NON-DEFAULT rendering convention, and the tick list is "
                  "F2P-shaped. So this is also the check that the repair narrowed the domain "
                  "neither to already-configured formatters nor to the convention the reading "
                  "guarantee is stated for: if either ordinary input is inadmissible => "
                  "PRECOND-TOO-STRONG. It further reads back, at the call site, that the "
                  "callee left the formatter non-residual with its convention intact."},
    {"id": "admiss-self-call-vacuity-control", "kind": "uniqueness",
     "expect": "reject", "module": _ADMISS_VACUITY,
     "refinement": "not a behaviour rival: the VACUITY CONTROL for the admissibility probe "
                   "above. It is that probe with `Assert(False)` appended. There is no real "
                   "patch to weigh; what is being weighed is whether the probe's call site is "
                   "REACHABLE. If an infeasible guard made it unreachable, anything would be "
                   "provable there and the positive control would certify nothing.",
     "rationale": "must be REJECTED. If it verified, the call site is infeasible, the "
                  "admissibility positive is vacuous, and the spec is inconsistent -- under "
                  "which every rival in this battery would 'verify' => SPEC-TOO-WEAK in its "
                  "strongest form. Rejection at `Assert(False)` is what makes "
                  "admiss-self-call-arrived-state-nondefault-convention evidence."},

    # ---- the recorded defect (must be REJECTED) ----
    {"id": "left-residual-enabled", "kind": "uniqueness", "expect": "reject",
     "module": _LEFT_ENABLED,
     "refinement": "leaves the formatter in the rendering mode it arrived in and reports the "
                   "labels it renders in THAT mode -- the arrived-in behaviour. Its faithful "
                   "real patch is no patch at all at this site, so it does NOT resolve: on the "
                   "F2P data the legend's labels are small residuals and the magnitude is "
                   "parked in a separate string the legend never records.",
     "rationale": "the behaviour the repair is about. Rejection source: P3 "
                  "(Ensures(not fmt.residual)) -- and P5 with it, since a formatter still "
                  "factoring a magnitude out cannot render labels that read back to full "
                  "ticks. P1, P2 and P4 all HOLD here (the labels really are that formatter's "
                  "own text for this tick set, in the mode it is in), which is what makes this "
                  "the case that shows P3 carries independent weight."},

    # ---- the hole the repair closes: value-only clauses are not enough ----
    {"id": "private-route-raw-tick", "kind": "uniqueness", "expect": "reject",
     "module": _PRIVATE_ROUTE,
     "refinement": "writes each tick's own number into the legend by a private route, with no "
                   "formatter involved, while leaving the formatter correctly configured. Its "
                   "faithful real patch formats the tick itself instead of asking the "
                   "formatter -- and that is exactly the recorded attack. " + _MEASURED
                   + " The recovered NUMBERS are gold's on every input; only the TEXT differs "
                   "('0.2' where the formatter renders '0.20'), which is why a spec whose "
                   "observable was the parsed number admitted it and why this repair makes "
                   "the observable the text.",
     "rationale": "the spec-too-weak witness this repair closes, and the reason P2 is stated "
                  "as a whole-sequence equality against `rendered_labels` rather than as a "
                  "property of the numbers. Rejection source: P2 -- no privately written value "
                  "is provably the formatter's text, since `rendered_labels` is uninterpreted "
                  "apart from its length and (for the full-value convention) its readings. If "
                  "it verified => SPEC-TOO-WEAK: the spec would admit an implementation that "
                  "never consults the formatter and would break the repo's own exact-text "
                  "legend assertions."},
    {"id": "render-then-disable", "kind": "uniqueness", "expect": "reject",
     "module": _RENDER_THEN_DISABLE,
     "refinement": "renders every label with the formatter in the mode it ARRIVED in, then "
                   "switches residual rendering off before returning, so the state the call "
                   "leaves behind is gold's. Its faithful real patch moves the two setter "
                   "calls after the `format_ticks` call (seaborn/_core/scales.py:385-389): the "
                   "labels are residuals, so it does NOT resolve the F2P.",
     "rationale": "ORDER-OF-OPERATIONS rival: the state half is delivered, the label half is "
                  "not. Rejection source: P2, whose oracle is evaluated at the mode the call "
                  "LEAVES the formatter in -- so labels rendered in the other mode do not "
                  "satisfy it. If it verified => SPEC-TOO-WEAK (the spec would constrain the "
                  "final state but not what the legend was actually built from)."},
    {"id": "other-tick-set", "kind": "uniqueness", "expect": "reject",
     "module": _OTHER_TICK_SET,
     "refinement": "asks the formatter to render this tick set together with one extra tick "
                   "and takes the labels for the ones asked about. Its faithful real patch "
                   "passes a different array to format_ticks / set_locs than the one the "
                   "legend records (seaborn/_core/scales.py:389, seaborn/utils.py:711-712). "
                   "MEASURED at the formatter level: adding a tick changes the rendering the "
                   "formatter chooses for the whole set (axiom_check.py's set-dependence "
                   "check: tick 1e8 renders '0' in {1e8,1e8+1} and '1' in {0,1e8,1e8+1}), so "
                   "the legend text no longer matches the axis and it does NOT resolve.",
     "rationale": "WRONG-DOMAIN rival, and the reason `rendered_labels` takes the whole tick "
                  "SEQUENCE rather than one tick. Rejection source: P2 -- the sequence "
                  "rendered for `locs + [0]` is not provably the sequence rendered for `locs`. "
                  "If it verified => SPEC-TOO-WEAK (a per-tick-isolated or wrong-set rendering "
                  "would be admitted, and a formatter's choice is made for the set)."},
    {"id": "rotated-labels", "kind": "uniqueness", "expect": "reject",
     "module": _ROTATED,
     "refinement": "reports the formatter's own labels for exactly this tick set, rotated one "
                   "place, so every entry carries a genuine label and the multiset of labels "
                   "is exactly gold's. Its faithful real patch pairs `list(locs)` with a "
                   "rotated `labels` list at seaborn/_core/scales.py:390; the F2P assertions "
                   "read entry k's text against tick k, so it does NOT resolve.",
     "rationale": "BOUNDARY TOKEN SWAP -- the ordering probe. Rejection source: P2 as an "
                  "ORDERED sequence equality (a set- or multiset-level clause would admit "
                  "this). If it verified => SPEC-TOO-WEAK (labels could be paired with the "
                  "wrong ticks)."},
    {"id": "mode-token-swap", "kind": "uniqueness", "expect": "reject",
     "module": _MODE_SWAP,
     "refinement": "renders with residual rendering ON while leaving the flag reported off: "
                   "the state half looks settled and the labels are residuals. Its faithful "
                   "real patch calls the setters on a DIFFERENT formatter instance than the "
                   "one that renders (seaborn/_core/scales.py:385-389 operate on "
                   "`axis.major.formatter`; a patch that configured a fresh throwaway "
                   "formatter instead would leave the rendering unchanged), so it does NOT "
                   "resolve.",
     "rationale": "MODE TOKEN SWAP: the mode argument of the oracle is hard-wired to the one "
                  "gold does NOT render in. Rejection source: P2 -- the oracle is evaluated at "
                  "`fmt.residual`, which P3 pins false, so a sequence rendered at `True` is a "
                  "different sequence. If it verified => SPEC-TOO-WEAK (the flag and the "
                  "rendering could disagree)."},
    {"id": "convention-echo", "kind": "uniqueness", "expect": "reject",
     "module": _CONVENTION_ECHO,
     "refinement": "renders under the convention the reading guarantee is STATED for (0) "
                   "rather than the one the formatter actually has. Its faithful real patch "
                   "replaces the axis's formatter with a default one and renders through that "
                   "(the branch at seaborn/_core/scales.py:623-660 chooses the formatter from "
                   "what the caller asked for); a legend built that way ignores `label(unit=)` "
                   "/ `label(like=)` entirely, so the P2P legend expectations for those paths "
                   "break and it does NOT resolve.",
     "rationale": "ORACLE ECHO on the GUARD: it echoes the hypothesis of P5 instead of a fact "
                  "about this formatter, which would make P5 trivially true and P2 false. "
                  "Rejection source: P2 -- `rendered_labels(0, ...)` is not provably "
                  "`rendered_labels(fmt.convention, ...)` for an arbitrary convention. If it "
                  "verified => SPEC-TOO-WEAK (the guarantee could be delivered by substituting "
                  "the formatter the guarantee is easiest for)."},
    {"id": "convention-rewrite", "kind": "uniqueness", "expect": "reject",
     "module": _CONVENTION_REWRITE,
     "refinement": "REWRITES the formatter's rendering convention to a non-default one and "
                   "then renders honestly under it, so P5's guard is false and its guarantee "
                   "is claimed of nothing. Its faithful real patch mutates the axis "
                   "formatter's own rendering convention (e.g. calling a set-format method on "
                   "`axis.major.formatter` beside the two setters at "
                   "seaborn/_core/scales.py:385-388). MEASURED: the reading property is then "
                   "unavailable, not merely unclaimed -- the SI-prefixed-unit and precision "
                   "conventions render the F2P 1e8-scale ticks as '100 Mg' / '1e+08' "
                   "(axiom_check.py's guard check), whose text is not the tick's full value, "
                   "so it does NOT resolve.",
     "rationale": "the FREEDOM THE REPAIR LEAVES, probed directly: P5 is a guarded clause, so "
                  "the cheapest way to satisfy it is to falsify its guard. Rejection source: "
                  "P4 (Ensures(fmt.convention == Old(fmt.convention))). This is the case that "
                  "shows P4 is load-bearing rather than decorative -- without it the guarded "
                  "reading guarantee could be made vacuous by the implementation it is meant "
                  "to constrain."},
    {"id": "interval-rewrite", "kind": "uniqueness", "expect": "reject",
     "module": _INTERVAL_REWRITE,
     "refinement": "REWRITES the range of the axis the formatter is attached to (widens it by "
                   "one unit at each end) and then renders honestly against the range it chose, "
                   "so P2 is satisfied of a range nobody asked for. Its faithful real patch "
                   "calls `axis.set_view_interval(...)` with its own bounds beside the two "
                   "setters at seaborn/_core/scales.py:385-388 instead of leaving the range the "
                   "data set at :378, or builds site 2's stub axis "
                   "(seaborn/utils.py:694-696) to return bounds of its own. MEASURED: the label "
                   "sequence MOVES with the range for the SI-prefixed-unit, the two logarithmic "
                   "and the plain full-value conventions (axiom_check.py "
                   "`check_range_dependence` reports ['eng','log','logsci','scalar']), and at "
                   "site 1 that axis is the one the plot itself goes on rendering, so its own "
                   "tick labels change too -- it does NOT resolve.",
     "rationale": "the FREEDOM THE REPAIR LEAVES, second form: P2 is now stated against "
                  "`fmt.view_lo`/`fmt.view_hi`, so the cheapest way to satisfy it is to move "
                  "them. Rejection source: P4b "
                  "(Ensures(fmt.view_lo == Old(fmt.view_lo)) and the same for view_hi). This is "
                  "the case that shows P4b is load-bearing rather than decorative -- without it "
                  "an implementation could render truthfully against a range of its own "
                  "choosing."},
    {"id": "other-interval", "kind": "uniqueness", "expect": "reject",
     "module": _OTHER_INTERVAL,
     "refinement": "renders against an interval that is NOT the one the formatter is attached to "
                   "(one unit wider at the top) while leaving the formatter's own range "
                   "untouched, so the state half looks settled and the text is a different "
                   "axis's. Its faithful real patch renders through a formatter attached to a "
                   "throwaway axis carrying bounds close to but not equal to the data's -- e.g. "
                   "site 2's stub axis (seaborn/utils.py:694-696) returning the UNCLIPPED "
                   "`raw_levels` span rather than `limits`. MEASURED: four of the seven "
                   "conventions render differently when only the range moves "
                   "(axiom_check.py `check_range_dependence`), so the legend text disagrees "
                   "with the axis it labels and it does NOT resolve.",
     "rationale": "ORACLE ECHO on the RANGE ARGUMENT: it evaluates the oracle at an interval of "
                  "its own instead of the formatter's. Rejection source: P2 -- the oracle is "
                  "evaluated at `fmt.view_hi`, and `rendered_labels(..., fmt.view_hi + 1)` is "
                  "not provably `rendered_labels(..., fmt.view_hi)` for an uninterpreted "
                  "callee. If it verified => SPEC-TOO-WEAK (the range rendered against would be "
                  "unconstrained, which is exactly the hole this repair closes)."},
    {"id": "interval-from-ticks", "kind": "uniqueness", "expect": "reject",
     "module": _INTERVAL_FROM_TICKS,
     "refinement": "derives the interval to render against from the TICK SEQUENCE's own ends "
                   "instead of reading the axis's range. Its faithful real patch sets the view "
                   "interval from the tick array -- `axis.set_view_interval(locs.min(), "
                   "locs.max())` in place of the data bounds at seaborn/_core/scales.py:378, or "
                   "site 2's stub axis (seaborn/utils.py:694-696) returning "
                   "`(min(raw_levels), max(raw_levels))` instead of `limits`. This is the most "
                   "tempting confusion, because both sites CLIP the ticks into the range "
                   "(seaborn/_core/scales.py:380, seaborn/utils.py:692) so the ticks always "
                   "look like a description of it -- but the range is normally strictly wider. "
                   "MEASURED: with ticks at 2,3,4 inside a 1..1000 range the logarithmic "
                   "convention renders ['2\u00d710\u2070','3\u00d710\u2070','4\u00d710\u2070'] "
                   "against the tick span and ['','',''] against the real range, so the legend "
                   "text differs and it does NOT resolve.",
     "rationale": "ORACLE ECHO via a DERIVED argument -- the range recomputed from data already "
                  "in hand rather than read where the callee reads it. Rejection source: P2 -- "
                  "the oracle is evaluated at `fmt.view_lo`/`fmt.view_hi`, and the ticks' ends "
                  "are not provably those bounds. If it verified => SPEC-TOO-WEAK, and in the "
                  "most damaging way: the axis range would be a redundant argument and the spec "
                  "would no longer pin WHERE the rendering context comes from."},

    # ---- partial-domain rivals (must be REJECTED) ----
    {"id": "partial-domain-empty-tick-set", "kind": "uniqueness",
     "expect": "reject", "module": _PARTIAL_EMPTY,
     "refinement": "delivers the state guarantee only when there is at least one tick, leaving "
                   "the formatter as it arrived for an empty legend. Its faithful real patch "
                   "guards the two setter calls on `len(locs) > 0` "
                   "(seaborn/_core/scales.py:385-388). It happens to pass the F2P tests, whose "
                   "data is non-empty -- which is exactly why the SPEC must reject it: the "
                   "formatter left factoring a magnitude out of an empty legend's axis is "
                   "still the object that renders that axis's own tick labels afterwards.",
     "rationale": "PARTIAL-DOMAIN GUARD on the state half. Rejection source: P3, which is "
                  "unconditional. If it verified => SPEC-TOO-WEAK (the guarantee would hold "
                  "only where the tests happen to look)."},
    {"id": "partial-drop-last", "kind": "uniqueness", "expect": "reject",
     "module": _DROP_LAST,
     "refinement": "drops the LAST tick's label (builds len(locs)-1 entries). Its faithful real "
                   "patch pairs `list(locs)` with a short `labels` list at "
                   "seaborn/_core/scales.py:390; the F2P legend assertions count and read every "
                   "entry, so it does NOT resolve. NOTE: on an empty `locs` the bound "
                   "len(locs)-1 == -1 still gives an empty result, so P1 holds there "
                   "vacuously; the rejection bites on every non-empty input.",
     "rationale": "PARTIAL-DOMAIN on length. Rejection source: P1 len(Result()) == len(locs), "
                  "and P2 as a whole-sequence equality (a prefix is not the sequence). If it "
                  "verified => SPEC-TOO-WEAK (a short legend is admitted)."},

    # ---- frame-mutation rivals (must be REJECTED for insufficient permission) ----
    {"id": "frame-append-to-locs", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_APPEND,
     "refinement": "appends to the read-only input `locs` -- a write the real legend code never "
                   "performs (the patch only calls two setters on the formatter, "
                   "seaborn/_core/scales.py:385-388; seaborn/utils.py:704-705). A faithful real "
                   "patch that mutated `locs` would corrupt the "
                   "`new._legend = list(locs), list(labels)` tuple (site 1, "
                   "seaborn/_core/scales.py:390) and `raw_levels` (site 2, "
                   "seaborn/utils.py:711), so it does NOT resolve.",
     "rationale": "FRAME MUTATION (#1 weakness class). Rejection source: the PERMISSION system "
                  "-- `locs` is held at Acc(list_pred(locs), 1/2) and a list .append needs "
                  "FULL permission. The gold invariants are kept verbatim so the rejection is "
                  "attributable to the write. If it verified => the frame condition is "
                  "unsound."},
    {"id": "frame-store-into-locs", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_STORE,
     "refinement": "overwrites an element of the read-only input in place (locs[i] = lab). The "
                   "real legend code never writes the tick array; a patch that did would change "
                   "the locations half of the legend tuple, so the rendered legend ticks would "
                   "no longer match the data -- it does NOT resolve.",
     "rationale": "FRAME MUTATION via element store. Rejection source: the PERMISSION system "
                  "-- element assignment on a list held at Acc(list_pred(locs), 1/2) needs FULL "
                  "permission."},

    # ---- termination rival (must be REJECTED) ----
    {"id": "nonterminating-build", "kind": "uniqueness", "expect": "reject",
     "module": _NONTERMINATING,
     "refinement": "builds the legend exactly as gold does and then never returns it: a second "
                   "loop spins forever. Its faithful real patch is a legend build that does not "
                   "finish, so the caller never receives a legend and every test that renders "
                   "one hangs -- it does NOT resolve.",
     "rationale": "PARTIAL-CORRECTNESS PROBE. Every value clause holds of the state this rival "
                  "reaches; what it never does is return. Rejection source: the TERMINATION "
                  "obligation `Requires(MustTerminate(3))`, which the spinning loop carries no "
                  "measure for. This is the case that shows the obligation is load-bearing: "
                  "without it P1-P5 would all be satisfied vacuously by a build that produces "
                  "no legend at all. If it verified => SPEC-TOO-WEAK."},
]

# ===========================================================================
# AXIOM LANE (Docker, real matplotlib formatters) -- the A-consumed
# `rendered_labels` / `reading` deep models. Re-runs and strengthens
# axiom_check.py's catalogue in-container.
# ===========================================================================

# (axiom-soundness) Every obligation model.py's axioms region states, against the
# REAL formatters, through BOTH APIs the modeled sites render with
# (`format_ticks` for site 1, `set_locs` + `formatter(x)` for site 2), and over
# axis ranges DRAWN INDEPENDENTLY of the tick set (the diagonal a careless driver
# would use, ranges wider by 2x and 1000x, ranges anchored at zero, ranges
# widened upward only, and ranges that do not contain the ticks at all):
#   * one label per tick, for every convention, every mode and every range;
#   * the full-value convention with residual rendering disabled reads back to
#     the tick's FULL value, at every magnitude and on every range;
#   * with residual rendering enabled the same formatter demonstrably does NOT
#     (so the `not residual` hypothesis is load-bearing, not idle);
#   * a label's TEXT carries strictly more than its reading, and depends on the
#     whole tick SET -- which is why the model's label carrier is an opaque code
#     for the exact text and `rendered_labels` takes the sequence;
#   * the label sequence MOVES when only the axis RANGE moves -- which is why
#     `rendered_labels` takes the range, and why a refinement may neither render
#     against a range of its own nor recompute one from the tick set;
#   * some non-default convention is unreadable even with every residual control
#     disabled -- so P5's convention guard withholds nothing that is available --
#     while the default convention IS the one those controls move, so convention
#     0 is pinned to the formatter the guarantee is about rather than chosen to
#     make it easy.
# Imports only matplotlib/numpy/stdlib. Exit 0 iff every obligation holds. The
# gold patch is applied by the runner but is irrelevant here: the callee under
# test is the unchanged matplotlib formatter.
_AX_SOUND = r"""
import random, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker as mticker

DEFAULT_KIND = ("scalar",)
OTHER_KINDS = ("eng", "strmethod_3g", "strmethod_0f", "func_3g", "logsci", "log")
ALL_KINDS = DEFAULT_KIND + OTHER_KINDS
APIS = ("format_ticks", "set_locs")

# holding (convention, tick set, mode) fixed and moving ONLY the axis range
RANGE_PROBES = [
    ([2, 3, 4], (2.0, 4.0), (1.0, 1000.0)),
    ([100, 200, 300], (100.0, 300.0), (0.0, 10.0 ** 6)),
    ([7], (7.0, 7.0), (0.0, 10.0 ** 9)),
    ([100000000, 100000001], (1e8, 1e8 + 1.0), (0.0, 10.0 ** 9)),
    ([1, 10, 100], (1.0, 100.0), (1.0, 10.0 ** 9)),
]


def _make(kind, view):
    # The axis range is an INPUT of the rendering, supplied through the ONLY
    # channel a matplotlib formatter has to its environment on this path.
    class _Axis:
        def get_view_interval(self):
            return (float(view[0]), float(view[1]))

    if kind == "scalar":
        fmt = mticker.ScalarFormatter()
    elif kind == "eng":
        fmt = mticker.EngFormatter("g")
    elif kind == "strmethod_3g":
        fmt = mticker.StrMethodFormatter("{x:.3g}")
    elif kind == "strmethod_0f":
        fmt = mticker.StrMethodFormatter("{x:.0f}")
    elif kind == "func_3g":
        fmt = mticker.FuncFormatter(lambda x, pos: "%.3g" % x)
    elif kind == "logsci":
        fmt = mticker.LogFormatterSciNotation(10)
    elif kind == "log":
        fmt = mticker.LogFormatter()
    else:
        raise AssertionError("unknown kind %r" % kind)
    fmt.axis = _Axis()
    return fmt


def rendered_labels(kind, ticks, residual, view, via="format_ticks"):
    fmt = _make(kind, view)
    if not residual:
        for setter in ("set_useOffset", "set_scientific"):
            if hasattr(fmt, setter):
                getattr(fmt, setter)(False)
    tick_list = [float(t) for t in ticks]
    if via == "format_ticks":
        return list(fmt.format_ticks(tick_list))
    fmt.set_locs(tick_list)
    return [fmt(t) for t in tick_list]


def reading(label):
    try:
        return float(label.replace("−", "-").strip())
    except ValueError:
        return None


def views_for(ticks):
    lo, hi = float(min(ticks)), float(max(ticks))
    width = max(hi - lo, 1.0)
    return [(lo, hi),                          # the diagonal
            (lo - width, hi + width),           # twice as wide
            (lo - 1000.0 * width, hi + 1000.0 * width),
            (0.0, hi + width),                  # anchored at zero
            (lo, hi + 1000.0 * width),          # widened upward only
            (0.0, 1.0),                         # unrelated, may exclude ticks
            (-(10.0 ** 9), 10.0 ** 9),
            (lo, lo)]                           # no width


def main():
    rng = random.Random(3187)
    boundary = [
        [0, 1, 2, 3], [1, 2, 3, 4, 5], [-3, -1, 1, 3], [100, 200, 300],
        [100000000, 100000001, 100000002, 100000003],   # the F2P 1e8 shape
        [100000000, 500000000, 900000000], [1000000, 2000000, 3000000],
        [12340000, 12350000, 12360000],
        [999999999, 1000000000, 1000000001],
        [10000000, 20000000, 30000000],
    ]
    residual_loses_magnitude = False
    other_unreadable = False
    guard_moves = 0
    renders = 0
    for ticks in boundary:
        for view in views_for(ticks):
            if view[0] == view[1]:
                # the one disclosed domain restriction lives here; the
                # containment probe pins it exactly, so totality skips it
                continue
            for kind in ALL_KINDS:
                for residual in (False, True):
                    for via in APIS:
                        labels = rendered_labels(kind, ticks, residual, view, via)
                        renders += 1
                        if len(labels) != len(ticks):
                            print("AXIOM-UNSOUND [%s/%s/residual=%s/view=%r] %d "
                                  "labels for %d ticks"
                                  % (kind, via, residual, view, len(labels),
                                     len(ticks)))
                            return 1
            for via in APIS:
                for tick, lbl in zip(ticks,
                                     rendered_labels("scalar", ticks, False,
                                                     view, via)):
                    if reading(lbl) != float(tick):
                        print("AXIOM-UNSOUND [scalar/%s/view=%r] tick %r "
                              "rendered %r, reads back as %r"
                              % (via, view, tick, lbl, reading(lbl)))
                        return 1
            for kind in OTHER_KINDS:
                for via in APIS:
                    try:
                        off = rendered_labels(kind, ticks, False, view, via)
                    except Exception as exc:
                        off = "raise:%s" % type(exc).__name__
                    try:
                        on = rendered_labels(kind, ticks, True, view, via)
                    except Exception as exc:
                        on = "raise:%s" % type(exc).__name__
                    if off != on:
                        guard_moves += 1
                    if isinstance(off, list) and any(
                            reading(l) != float(t) for t, l in zip(ticks, off)):
                        other_unreadable = True
            # The converse-guard check is asserted on the ranges the modeled
            # sites can actually present -- ones that CONTAIN the tick set,
            # since both sites clip their ticks to the range. On a range that
            # excludes the ticks the default formatter has no common magnitude
            # to factor out and the controls are measurably inert, which is a
            # fact about the callee, not about the modeled behaviour.
            contains = view[0] <= min(ticks) and max(ticks) <= view[1]
            if min(ticks) >= 10000000 and contains:
                for via in APIS:
                    off = rendered_labels("scalar", ticks, False, view, via)
                    on = rendered_labels("scalar", ticks, True, view, via)
                    if off == on:
                        print("AXIOM-UNSOUND: the default convention is NOT "
                              "moved by the residual controls on %r [%s/view=%r]"
                              % (ticks, via, view))
                        return 1
                    if any(reading(l) != float(t) for t, l in zip(ticks, on)):
                        residual_loses_magnitude = True
    if not residual_loses_magnitude:
        print("AXIOM-IDLE: no large tick set lost its magnitude with residual "
              "rendering enabled, so the `not residual` hypothesis would be idle")
        return 1
    if not other_unreadable:
        print("AXIOM-GUARD-WITHHOLDS: every non-default convention read back to "
              "its ticks, so guarding the reading property would withhold an "
              "available guarantee")
        return 1
    # the label sequence is NOT a function of (convention, tick set, mode) alone
    range_dependent = set()
    for kind in ALL_KINDS:
        for ticks, view_a, view_b in RANGE_PROBES:
            for residual in (False, True):
                for via in APIS:
                    try:
                        a = rendered_labels(kind, ticks, residual, view_a, via)
                    except Exception as exc:
                        a = "raise:%s" % type(exc).__name__
                    try:
                        b = rendered_labels(kind, ticks, residual, view_b, via)
                    except Exception as exc:
                        b = "raise:%s" % type(exc).__name__
                    if a != b:
                        range_dependent.add(kind)
    if not range_dependent:
        print("AXIOM-ARGUMENT-IDLE: no convention's rendering moved when only "
              "the axis range moved, so the deep model's range arguments would "
              "be idle and a refinement could render against any range at all")
        return 1
    # a label's TEXT carries strictly more than its reading, and depends on the
    # whole tick SET
    together = rendered_labels("scalar", [0.2, 0.22, 0.24, 0.26, 0.28], False,
                               (0.0, 1.0))
    alone = rendered_labels("scalar", [0.2], False, (0.0, 1.0))
    if together[0] == alone[0] or reading(together[0]) != reading(alone[0]):
        print("AXIOM-CARRIER: expected the same tick to render to DIFFERENT text "
              "reading back to the SAME number, got %r and %r"
              % (together[0], alone[0]))
        return 1
    small = rendered_labels("scalar", [100000000, 100000001], True,
                            (0.0, 10.0 ** 9))
    wide = rendered_labels("scalar", [0, 100000000, 100000001], True,
                           (0.0, 10.0 ** 9))
    if small[0] == wide[1]:
        print("AXIOM-SIGNATURE: expected tick 1e8 to render differently in "
              "{1e8,1e8+1} than in {0,1e8,1e8+1}, got %r both ways" % (small[0],))
        return 1
    for _ in range(4000):
        base = rng.choice([1, 10, 100, 1000, 10 ** 5, 10 ** 6, 10 ** 7,
                           10 ** 8, 10 ** 9])
        step = rng.choice([1, 2, 5, 10, 100, 1000])
        n = rng.randint(2, 8)
        start = rng.randint(0, base)
        ticks = [start + i * step for i in range(n)]
        # the range is drawn INDEPENDENTLY of the ticks, never from them
        factor = rng.choice([0, 1, 1, 2, 10, 1000])
        lo, hi = float(min(ticks)), float(max(ticks))
        if factor:
            span = max(hi - lo, 1.0) * factor
            lo, hi = lo - span, hi + span
        view = (lo, hi)
        if view[0] == view[1]:
            view = (lo, hi + 1.0)
        for kind in ALL_KINDS:
            for residual in (False, True):
                for via in APIS:
                    if len(rendered_labels(kind, ticks, residual, view,
                                           via)) != len(ticks):
                        print("AXIOM-UNSOUND [%s/%s] label count on %r over %r"
                              % (kind, via, ticks, view))
                        return 1
                    renders += 1
        for via in APIS:
            for tick, lbl in zip(ticks, rendered_labels("scalar", ticks, False,
                                                        view, via)):
                if reading(lbl) != float(tick):
                    print("AXIOM-UNSOUND [scalar/%s] tick %r rendered %r over %r"
                          % (via, tick, lbl, view))
                    return 1
    print("AXIOM SOUND: rendered_labels/reading match the real formatters over "
          "%d renders -- %d boundary tick sets x 7 independently drawn axis "
          "ranges + 4000 fuzz sets each with its own range, through both legend "
          "APIs. One label per tick for every convention, mode and range; the "
          "full-value convention with residual rendering disabled reads back to "
          "full ticks (including on ranges that do not contain them) and with it "
          "enabled demonstrably does not; label text carries strictly more than "
          "its reading and depends on the whole tick set; the label sequence "
          "moves when only the axis range moves (%s), so the range arguments are "
          "load-bearing; %d non-default (convention,API,range) renderings moved "
          "with the residual controls while some stayed unreadable even with "
          "them disabled, so the convention guard withholds nothing available; "
          "and the default convention is exactly the one those controls move."
          % (renders, len(boundary), ",".join(sorted(range_dependent)),
             guard_moves))
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

# (axiom-containment) What the model can pass to the deep models, and whether the
# real callee is defined there.
#
# The model reaches `rendered_labels` only inside the loop, where the invariants
# pin `not fmt.residual`, `fmt.convention == conv0` and the axis range at the
# bounds it arrived with; the tick sequence is `ToSeq(locs)`, an arbitrary
# List[int], and the two bounds are arbitrary ints. So the reachable callee
# domain is {(any convention code, any int tick sequence, residual=False, any
# lo, any hi)}. Neither deep model declares a Requires, so the declared domain is
# UNIVERSAL and containment is immediate. What this probe therefore MEASURES is
# the real callee's own domain, on the only inputs where it could be restricted:
# an axis range of NO WIDTH, where a convention that chooses its unit from that
# width may have no label sequence at all. The claim is a declared BOUND plus an
# exact measurement, because whether that convention raises or renders is a
# property of the matplotlib version in use: whatever raises must lie inside the
# width-reading set, every convention that does render must render one label per
# tick even then, an empty tick set must always render, and on a range of
# non-zero width nothing may raise at all. The measured set is reported and may
# be empty. That restriction is what model.py's `rendered_labels` docstring
# discloses, and conformance_check.py checks that the refinement and the real
# legend site produce no legend TOGETHER on those inputs (its `raise_agreements`
# counter).
_AX_CONTAINMENT = r"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker as mticker

# the only conventions whose rendering is chosen from the WIDTH of the axis range
WIDTH_DEPENDENT = ("eng",)
ALL_KINDS = ("scalar", "eng", "strmethod_3g", "strmethod_0f", "func_3g",
             "logsci", "log")
APIS = ("format_ticks", "set_locs")


def _make(kind, view):
    class _Axis:
        def get_view_interval(self):
            return (float(view[0]), float(view[1]))

    if kind == "scalar":
        fmt = mticker.ScalarFormatter()
    elif kind == "eng":
        fmt = mticker.EngFormatter("g")
    elif kind == "strmethod_3g":
        fmt = mticker.StrMethodFormatter("{x:.3g}")
    elif kind == "strmethod_0f":
        fmt = mticker.StrMethodFormatter("{x:.0f}")
    elif kind == "func_3g":
        fmt = mticker.FuncFormatter(lambda x, pos: "%.3g" % x)
    elif kind == "logsci":
        fmt = mticker.LogFormatterSciNotation(10)
    else:
        fmt = mticker.LogFormatter()
    fmt.axis = _Axis()
    return fmt


def render(kind, ticks, residual, view, via):
    fmt = _make(kind, view)
    if not residual:
        for setter in ("set_useOffset", "set_scientific"):
            if hasattr(fmt, setter):
                getattr(fmt, setter)(False)
    tick_list = [float(t) for t in ticks]
    if via == "format_ticks":
        return list(fmt.format_ticks(tick_list))
    fmt.set_locs(tick_list)
    return [fmt(t) for t in tick_list]


def main():
    # model-reachable: any convention code, any List[int], residual False (True
    # is checked too, which is strictly more than the model can reach), any two
    # int bounds.
    tick_sets = [[7], [100000000], [0], [10 ** 8, 10 ** 8], [5, 5, 5],
                 [0, 1], [-3, -1, 1, 3]]
    zero_width = [(7.0, 7.0), (0.0, 0.0), (1e8, 1e8), (-3.0, -3.0)]
    positive_width = [(0.0, 1.0), (0.0, 10.0 ** 9), (-10.0 ** 9, 10.0 ** 9),
                      (1.0, 1000.0)]
    raised = set()
    for ticks in tick_sets:
        for view in zero_width:
            for kind in ALL_KINDS:
                for residual in (False, True):
                    for via in APIS:
                        try:
                            labels = render(kind, ticks, residual, view, via)
                        except Exception:
                            raised.add(kind)
                            continue
                        if len(labels) != len(ticks):
                            print("AXIOM-UNSOUND [%s/%s/residual=%s/view=%r] %d "
                                  "labels for %d ticks on a range of no width"
                                  % (kind, via, residual, view, len(labels),
                                     len(ticks)))
                            return 1
    if not raised <= set(WIDTH_DEPENDENT):
        print("DOMAIN-MISDECLARED: a convention with no rendering for an axis "
              "range of no width that is NOT one whose unit is chosen from that "
              "width: measured %r, declared bound %r"
              % (sorted(raised), sorted(WIDTH_DEPENDENT)))
        return 1
    # an empty tick set has no label to render, so nothing is undefined for it
    for view in zero_width:
        for kind in ALL_KINDS:
            for residual in (False, True):
                for via in APIS:
                    labels = render(kind, [], residual, view, via)
                    if len(labels) != 0:
                        print("AXIOM-UNSOUND [%s/%s/residual=%s/view=%r] %d "
                              "labels for an empty tick set"
                              % (kind, via, residual, view, len(labels)))
                        return 1
    for ticks in tick_sets:
        for view in positive_width:
            for kind in ALL_KINDS:
                for residual in (False, True):
                    for via in APIS:
                        try:
                            labels = render(kind, ticks, residual, view, via)
                        except Exception as exc:
                            print("AXIOM-TOO-WEAK-FOR-CALLER: model-reachable "
                                  "input %r over %r [%s/%s] outside the callee "
                                  "domain (raised %r)"
                                  % (ticks, view, kind, via, exc))
                            return 1
                        if len(labels) != len(ticks):
                            print("AXIOM-UNSOUND [%s/%s/view=%r] %d labels for "
                                  "%d ticks" % (kind, via, view, len(labels),
                                                len(ticks)))
                            return 1
    print("CONTAINMENT OK: the model reaches the deep models only at (any "
          "convention, any List[int] tick sequence, residual=False, any two int "
          "range bounds) -- the loop invariants pin the mode, the convention and "
          "both bounds -- and neither deep model declares a Requires, so the "
          "declared domain is universal and contains it. Measured callee domain: "
          "on an axis range of NO WIDTH the conventions with no label sequence "
          "are exactly %r, inside the declared bound %r (the bound is what "
          "model.py discloses; the measured set is version-dependent and may be "
          "empty); every convention that does render there renders one label per "
          "tick, an empty tick set renders everywhere, and on a range of "
          "non-zero width nothing raises at all. conformance_check.py checks the "
          "refinement and the real site produce no legend together on the "
          "restricted inputs."
          % (sorted(raised), sorted(WIDTH_DEPENDENT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""

AXIOM_TESTS = [
    {"id": "ax-rendered-labels-sound", "axiom": "rendered_labels",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_SOUND,
     "rationale": "every obligation the axioms region states, checked against the REAL "
                  "matplotlib formatters through both APIs the modeled sites render with, over "
                  "axis ranges drawn INDEPENDENTLY of the tick set (the diagonal, 2x, 1000x, "
                  "zero-anchored, upward-only, and ranges that exclude the ticks): one label "
                  "per tick for every convention, mode and range; the full-value convention "
                  "with residual rendering disabled reads back to FULL ticks at every "
                  "magnitude and on every range, and with it enabled demonstrably does not "
                  "(the hypothesis is load-bearing); a label's TEXT carries strictly more than "
                  "its reading and depends on the whole tick SET (so the opaque-text carrier "
                  "and the set-valued signature are justified, not conveniences); the label "
                  "sequence MOVES when only the axis range moves (so the range arguments are "
                  "load-bearing, and rendering against the tick set's own span is a different "
                  "application of the callee); some non-default convention stays unreadable "
                  "even with every residual control disabled (the convention guard withholds "
                  "nothing available); and the default convention is exactly the one those "
                  "controls move (convention 0 is pinned to the formatter the guarantee is "
                  "about). Any residual under the disabled default config => AXIOM-UNSOUND."},
    {"id": "ax-rendered-labels-containment", "axiom": "rendered_labels",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAINMENT,
     "rationale": "the model reaches the deep models only at (any convention code, any "
                  "List[int] tick sequence, residual=False, any two int range bounds) -- the "
                  "loop invariants pin the mode, the convention and both bounds -- and neither "
                  "declares a Requires, so the declared domain is universal and containment is "
                  "immediate. The probe therefore measures the REAL callee's domain on the only "
                  "inputs where it could be restricted: an axis range of NO WIDTH, where a "
                  "convention that picks its unit from that width may have no label sequence. "
                  "The claim is a declared BOUND plus an exact measurement, because whether "
                  "that convention raises or renders is a property of the matplotlib version in "
                  "use: whatever raises must lie inside the width-reading set, every convention "
                  "that does render must render one label per tick even then, an empty tick set "
                  "must always render, and on a range of non-zero width nothing may raise at "
                  "all. The measured set is reported and may be empty. That restriction is "
                  "disclosed in model.py's rendered_labels docstring and cross-checked by "
                  "conformance_check.py, which requires the refinement and the real legend site "
                  "to produce no legend TOGETHER on those inputs."},
]
