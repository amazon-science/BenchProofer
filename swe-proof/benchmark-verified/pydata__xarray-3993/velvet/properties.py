"""properties.py — G-PBT falsification battery for pydata__xarray-3993 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct integrateDispatch`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  integrateDispatch (primary : Selector) (legacy : Selector)
      return (out : Except DispatchErr (Option Dispatch))
    ensures out = resolve primary legacy

The method is the argument-resolution head of a public entry point that takes
two coordinate SELECTORS (``Selector = Option Nat``: ``none`` ↔ the selector was
left absent, ``some k`` ↔ it was supplied with name tag ``k``) and resolves them
into one forwarded call. The pure region pins the whole outcome as a total
function of the method's own two inputs:

  resolve primary legacy = match primary, legacy with
    | some _, some _ => Except.error .bothSupplied
    | some c, none   => Except.ok (some { forwarded := c, advisory := false })
    | none,   some d => Except.ok (some { forwarded := d, advisory := true  })
    | none,   none   => Except.ok none

with ``Dispatch`` carrying ``forwarded : Nat`` (the coordinate handed to the
unchanged integrator) and ``advisory : Bool`` (whether the one-time advisory
about the legacy selector fires). The sole ensures therefore pins a four-way
decision with several independent top-level behaviours:

  * (R) REJECTION — supplying BOTH selectors yields ``Except.error
        .bothSupplied``, and ONLY that input does.
  * (F) FORWARDED value — every honoured single-selector call forwards the
        value carried by whichever selector was supplied (``c`` for primary,
        ``d`` for legacy), verbatim.
  * (A) ADVISORY signal — ``advisory = true`` fires EXACTLY on the legacy-only
        call (``none, some _``); it is ``false`` on the primary-only call and
        never reached otherwise. This is the newly-observable consequence the
        change introduces (what the F2P ``pytest.warns(FutureWarning)`` asserts).
  * (N) the NEITHER case — both absent yields ``Except.ok none`` (no coordinate
        to forward).

The two INPUT binders are free (no ``require`` clause) and the post-image must
hold for EVERY value of each:
  * ``primary`` — the primary coordinate selector;
  * ``legacy``  — the legacy coordinate selector.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling holds its selectors as
    plain value parameters and records this class as N/A already; here it is
    doubly so: Lean and Velvet are referentially transparent, every parameter is
    an immutable value, the method declares no ``mut`` binder, there is no heap
    and no aliasing. No read-only input to overwrite, no permission system to
    trip. Not fabricated.
  * DIVERGENCE / NON-TERMINATION — CLOSED BY THE CARRIER, and defended by a
    POSITIVE rather than attacked by a rival. CORRECTED BY AUDIT: this bundle
    runs under ``set_option loom.semantics.termination "total"``
    (Solution.lean line 4), NOT ``"partial"``. Under total semantics the
    verifier DISCHARGES a termination obligation, so a loop carrying no
    decreasing measure is refused outright. Audit-measured on this bundle: a
    spin-loop spliced into the impl region (both before and after gold's correct
    resolution tail) FAILS to build, exit 1, with ``error: Decreasing
    annotations are required in total correctness semantics``. So a diverging
    impl does NOT verify here and there is NO spec hole to record — the
    disposition this battery previously carried ("partial semantics, a
    non-terminating impl verifies vacuously, KNOWN SPEC HOLE") described a
    bundle this is not, and is corrected here and in the footer.

    It is also not shippable as a REJECT case, for a mechanical reason the audit
    measured rather than assumed. The termination error is raised by the
    ``method`` elaboration itself, so it fires in the WITNESS file too — where
    the obligations are stripped — and the extracted tester of a looping impl
    never reduces. Measured: the witness
    ``integrateDispatchTester (some 3) none = false`` against the diverging
    rival fails (exit 1) with ``Tactic `decide` failed … reduction got stuck at
    the `Decidable` instance``, and that is the half the gate requires to
    SUCCEED. Retried with ``decide +kernel``, ``simp
    [integrateDispatchTester]`` and ``rfl``: all three exit 1 on the rival side.
    A reject case therefore cannot be landed. The honest way to exercise the
    lane on this carrier is from the OTHER side: ``pos-terminating-loop`` below
    is a correct impl whose loop DOES carry a decreasing measure and must
    verify, which pins the termination obligation as
    discharged-and-satisfiable rather than merely unmentioned.
  * UNGROUNDED-ORACLE ECHO — N/A, as the sibling records. ``resolve`` is a
    concrete ``def`` over the method's own two arguments (the ``axioms`` region
    is empty; meta.json axioms == []); there is no opaque answer key to echo.
    The unique satisfier IS the grounded decision, so the honest controls are
    the cheapest faithful reshapes (the ``pos-*`` cases).
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    refusal (raise) is the ``Except.error`` carrier of the return value and the
    advisory is the ``Dispatch.advisory`` bool, so both observable effects are
    fully visible to the ensures; the no-raise / always-raise / always-advisory
    rivals are their discriminators.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. Each rival is right on a
    sub-domain and diverges on one match arm (never/always advise, forward the
    wrong value, refuse-vs-forward on both-supplied, forward on neither).

WITNESS MECHANICS ON THIS BUNDLE. The carrier is FULLY TRANSPARENT
(``Selector = Option Nat``, ``Dispatch`` over ``Nat``/``Bool``, ``DispatchErr``
a two-constructor inductive) and the frozen impl is STRAIGHT-LINE (a single
closed-form match, no loop): its extracted program reduces fully under
``decide``. Each reject rival carries a machine-checked refutation ``witness`` —
a Velvet tester statement ``integrateDispatchTester <primary> <legacy> = false``
at ONE concrete input, checked in a file whose ``prove_correct`` block is
stripped so no tactic script can mask the verdict. The
``Except DispatchErr (Option Dispatch)`` return carrier needs a decidable-
equality instance for the tester derivation; it is DERIVED
(``deriving instance DecidableEq for Except``), not assumed — no
``axiom``/``sorry``/``native_decide`` is involved, so the frozen solution
rejects the witnesses all the same. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the
extracted tester ``decide``s to ``false`` — the rival's output violates the
postcondition at the probed input) and FAILS against the frozen solution
(``decide`` proves the proposition false, since gold satisfies the spec at every
input). No witness binds a hypothesis (the carrier is fully transparent — every
input is a concrete literal), so there is no joint-satisfiability obligation.

AXIOM lane: EMPTY. meta.json declares no consumed ``axiom`` and no deep-model
reference; ``resolve`` is a concrete deep model (an I-op), refinement-checked by
conformance_check.py (G-CONF), not axiomatized. Nothing in the proof rests on an
axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3993"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl decision, verbatim — the closed-form match that resolves the
# two selectors, lying wholly inside the single `-- impl-start` / `-- impl-end`
# region and unique in Solution.lean. Every rival and reshape edits ONLY this
# block, so the spec view is untouched and same_spec holds by construction.
_MATCH = (
    "    let res : Except DispatchErr (Option Dispatch) :=\n"
    "      match primary, legacy with\n"
    "      | some _, some _ => Except.error .bothSupplied\n"
    "      | some c, none   => Except.ok (some { forwarded := c, advisory := false })\n"
    "      | none,   some d => Except.ok (some { forwarded := d, advisory := true })\n"
    "      | none,   none   => Except.ok none\n"
    "    return res"
)

assert _BASE.count(_MATCH) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); every case here happens to
# close under the frozen `loom_solve` unchanged, so the proof is never retuned.
_PROOF = "prove_correct integrateDispatch by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl decision replaced."""
    return _swap(_BASE, _MATCH, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `integrateDispatchTester <primary> <legacy> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped. The
# ---- `Except DispatchErr (Option Dispatch)` return carrier needs a decidable-
# ---- equality instance for the tester derivation; it is derived, not assumed.
_DEC = "deriving instance DecidableEq for Except\n\n"
_TESTER = (_DEC +
           "extract_program_for integrateDispatch\n"
           "prove_precondition_decidable_for integrateDispatch\n"
           "prove_postcondition_decidable_for integrateDispatch\n"
           "derive_tester_for integrateDispatch\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each computes the SAME resolution on every input and only
    # reshapes the executable surface, so the frozen `loom_solve` closes it
    # unchanged (verified out-of-band).
    # =====================================================================
    {
        "id": "pos-scrutinee-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: match on `legacy, primary` (scrutinees swapped) and permute the
        # arms accordingly. Same outcome on every input — the both-supplied arm
        # still errors, the single-selector arms still forward their value with
        # the same advisory, the neither arm still yields `ok none`.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match legacy, primary with\n"
            "      | some _, some _ => Except.error .bothSupplied\n"
            "      | none,   some c => Except.ok (some { forwarded := c, advisory := false })\n"
            "      | some d, none   => Except.ok (some { forwarded := d, advisory := true })\n"
            "      | none,   none   => Except.ok none\n"
            "    return res"),
        "rationale": "matching on the scrutinees in the opposite order and "
                     "permuting the arms to match computes the SAME resolution on "
                     "every input (both-supplied errors, each single-selector call "
                     "forwards its value with the same advisory, neither yields "
                     "`ok none`), so `out = resolve primary legacy` still holds; a "
                     "correct reshape must verify, else SPEC-TOO-STRONG on "
                     "scrutinee/arm order.",
    },
    {
        "id": "pos-nested-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: a nested match (scrutinise `primary` first, then `legacy` in
        # each branch) instead of the flat two-scrutinee match. Structurally
        # different control flow, identical value flow on every input.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary with\n"
            "      | some c =>\n"
            "        match legacy with\n"
            "        | some _ => Except.error .bothSupplied\n"
            "        | none   => Except.ok (some { forwarded := c, advisory := false })\n"
            "      | none =>\n"
            "        match legacy with\n"
            "        | some d => Except.ok (some { forwarded := d, advisory := true })\n"
            "        | none   => Except.ok none\n"
            "    return res"),
        "rationale": "a nested match (primary first, then legacy in each branch) "
                     "is structurally different control flow but identical value "
                     "flow: the four leaves are exactly the four arms of "
                     "`resolve`, so `out = resolve primary legacy` is unchanged; a "
                     "correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "flat-vs-nested dispatch FORM.",
    },

    {
        "id": "pos-terminating-loop",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack F′). The termination lane, defended from the only
        # side this carrier admits. This bundle is `termination "total"`, so the
        # risk runs in BOTH directions and both were measured: a measure-free
        # spin loop is REFUSED (exit 1, "Decreasing annotations are required in
        # total correctness semantics"), and a correct impl whose loop DOES carry
        # a measure must still verify. This is the second. The advisory flag is
        # computed by a bounded loop carrying `decreasing i`, then consumed by the
        # resolution: the primary-only arm takes `!adv`, the legacy-only arm takes
        # `adv`. The loop always runs exactly once and leaves `adv = true`, so the
        # outcome is identical to the frozen impl on every input; the only new
        # content is the loop and its measure. Verified to build, exit 0.
        "module": _impl(
            "    let mut adv : Bool := false\n"
            "    let mut i : Nat := 1\n"
            "    while i > 0\n"
            "    invariant i <= 1\n"
            "    invariant adv = (decide (i = 0))\n"
            "    decreasing i\n"
            "    do\n"
            "      adv := true\n"
            "      i := i - 1\n"
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary, legacy with\n"
            "      | some _, some _ => Except.error .bothSupplied\n"
            "      | some c, none   => Except.ok (some { forwarded := c, advisory := !adv })\n"
            "      | none,   some d => Except.ok (some { forwarded := d, advisory := adv })\n"
            "      | none,   none   => Except.ok none\n"
            "    return res"),
        "rationale": "the termination lane on a `total` bundle, defended from the "
                     "only side this carrier admits. The advisory flag is produced "
                     "by a bounded `while` carrying a `decreasing i` measure and "
                     "then consumed by the resolution (primary-only takes `!adv`, "
                     "legacy-only takes `adv`); the loop runs once and leaves "
                     "`adv = true`, so the outcome equals `resolve primary legacy` "
                     "on every input and the case must verify — else SPEC-TOO-STRONG "
                     "on the loop FORM, and the termination obligation would be "
                     "unsatisfiable rather than merely discharged. The dual "
                     "direction (a measure-free spin loop is REJECTED) was measured "
                     "by the audit and is why the divergence class is not a spec "
                     "hole here; see the header.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). Re-aimed
    # at the residual total-domain risk: that the post-image is DEGENERATE at the
    # interesting points — a `resolve` that collapsed distinct arms would read
    # like a live one. This case discharges an in-region assert pinning that
    # `resolve` genuinely separates all four cases (the both-supplied refusal, the
    # legacy-only advisory-raising forward — the F2P-shaped `da.integrate(dim=…)`
    # outcome — the primary-only silent forward, and the neither case), so the
    # decision is non-degenerate. The impl is kept verbatim so the method's own
    # obligation still discharges; the frozen `loom_solve` closes the assert VC
    # too (verified out-of-band).
    # =====================================================================
    {
        "id": "admiss-all-arms-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      (resolve none (some 7) = Except.ok (some { forwarded := 7, advisory := true }) ∧\n"
            "       resolve (some 4) none = Except.ok (some { forwarded := 4, advisory := false }) ∧\n"
            "       resolve (some 4) (some 7) = Except.error .bothSupplied ∧\n"
            "       resolve none none = Except.ok (none : Option Dispatch)))\n"
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary, legacy with\n"
            "      | some _, some _ => Except.error .bothSupplied\n"
            "      | some c, none   => Except.ok (some { forwarded := c, advisory := false })\n"
            "      | none,   some d => Except.ok (some { forwarded := d, advisory := true })\n"
            "      | none,   none   => Except.ok none\n"
            "    return res"),
        "rationale": "the post-image is satisfiable AND non-degenerate across all "
                     "four cases: the legacy-only call forwards its value WITH the "
                     "advisory (the F2P-shaped honoured outcome), the primary-only "
                     "call forwards WITHOUT it, both-supplied refuses, and neither "
                     "yields `ok none` — four distinct outcomes, so no arm is "
                     "collapsed. The in-region assert must discharge (else the "
                     "decision would be degenerate / the obligation vacuous); the "
                     "impl is kept verbatim so the ensures still discharges too. "
                     "AUDIT-CONFIRMED LOAD-BEARING: the assert genuinely generates "
                     "a VC rather than being trivially closed. Flipping the "
                     "neither-arm conjunct to `Except.error .bothSupplied` fails "
                     "(exit 1, `unsolved goals` with the false conjunct printed in "
                     "the goal), and flipping the F2P-shaped legacy-only conjunct's "
                     "advisory to `false` likewise fails (exit 1) — so a collapsed "
                     "or mis-stated arm would be caught here.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each edits exactly one match arm (straight-line, so
    # its witness reduces under `decide`), is refuted at a concrete input by a
    # witness that FAILS on the frozen solution, and carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================

    # ---- ADVISORY clause (A): never raise the advisory on the legacy-only call
    {
        "id": "weak-never-advise",
        "kind": "uniqueness",
        "expect": "reject",
        # PRE-PATCH behaviour: the legacy-only call forwards its value but the
        # advisory NEVER fires. Correct on forwarding (F) and refusal (R); wrong
        # only on the advisory (A) for the legacy-only sub-domain.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary, legacy with\n"
            "      | some _, some _ => Except.error .bothSupplied\n"
            "      | some c, none   => Except.ok (some { forwarded := c, advisory := false })\n"
            "      | none,   some d => Except.ok (some { forwarded := d, advisory := false })\n"
            "      | none,   none   => Except.ok none\n"
            "    return res"),
        "refinement": "this IS the pre-patch behaviour: the legacy selector's value "
                      "is forwarded verbatim but no advisory is emitted. The F2P "
                      "asserts a deprecation warning IS raised on the legacy-only "
                      "call; a no-advisory patch emits none, the warning assertion "
                      "fails, and it does NOT resolve. (This is the precise change "
                      "the spec senses — G-DIFF.)",
        "rationale": "REJECT from `out = resolve primary legacy` on the advisory "
                     "(A): on the legacy-only input the post-image demands "
                     "`advisory = true` but the rival sets it false. THE "
                     "discriminating clause; partial-domain (legacy-only "
                     "sub-domain). Refuted at `(none, some 3)` — the only arm where "
                     "the advisory should fire.",
        "witness": _witness("integrateDispatchTester none (some 3)"),
    },

    # ---- ADVISORY clause (A): raise the advisory on the primary-only call ----
    {
        "id": "weak-always-advise",
        "kind": "uniqueness",
        "expect": "reject",
        # Forwards and refuses correctly, but sets `advisory = true` even on the
        # primary-only call. Correct on the legacy-only and both/neither arms;
        # wrong on the primary-only sub-domain.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary, legacy with\n"
            "      | some _, some _ => Except.error .bothSupplied\n"
            "      | some c, none   => Except.ok (some { forwarded := c, advisory := true })\n"
            "      | none,   some d => Except.ok (some { forwarded := d, advisory := true })\n"
            "      | none,   none   => Except.ok none\n"
            "    return res"),
        "refinement": "a real patch that emits the advisory UNCONDITIONALLY "
                      "(hoisted above the legacy-selector guard) warns on the "
                      "ordinary primary-selector call too. The P2P suite / the "
                      "units test exercise the primary-selector call expecting NO "
                      "warning; an unconditional advisory makes the benign path "
                      "noisy (and under a warnings-as-errors filter, error) — it "
                      "does NOT resolve.",
        "rationale": "REJECT from `out = resolve primary legacy` on the advisory "
                     "(A, dual): on the primary-only input (`some c, none`) the "
                     "post-image demands `advisory = false` but the rival sets it "
                     "true. Partial-domain (primary-only sub-domain). Refuted at "
                     "`(some 3, none)` — the primary-only arm the never-advise "
                     "rival holds correct.",
        "witness": _witness("integrateDispatchTester (some 3) none"),
    },

    # ---- FORWARDED clause (F): forward the wrong value on the legacy-only call
    {
        "id": "weak-wrong-forward",
        "kind": "uniqueness",
        "expect": "reject",
        # Raises the advisory correctly (A holds) and refuses correctly, but on
        # the legacy-only call forwards a fixed WRONG coordinate (0) instead of the
        # supplied legacy value `d`. Correct exactly when the supplied legacy value
        # is 0; diverges otherwise.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary, legacy with\n"
            "      | some _, some _ => Except.error .bothSupplied\n"
            "      | some c, none   => Except.ok (some { forwarded := c, advisory := false })\n"
            "      | none,   some _ => Except.ok (some { forwarded := 0, advisory := true })\n"
            "      | none,   none   => Except.ok none\n"
            "    return res"),
        "refinement": "a real patch that emits the advisory but DROPS the "
                      "reassignment forwarding the legacy selector's value hands "
                      "the WRONG/absent coordinate to the unchanged integrator, so "
                      "the legacy-only call integrates along the wrong coordinate "
                      "(or errors) instead of the one requested. The F2P call must "
                      "SUCCEED returning the requested integral (only warning); an "
                      "integration along the wrong coordinate errors — it does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = resolve primary legacy` on the forwarded "
                     "value (F): on the legacy-only input the post-image demands "
                     "`forwarded = d` but the rival forwards the constant 0. "
                     "Partial-domain (legacy-only routing axis). Refuted at "
                     "`(none, some 8)` — a supplied legacy value ≠ 0, distinct from "
                     "the advisory witnesses' input point.",
        "witness": _witness("integrateDispatchTester none (some 8)"),
    },

    # ---- REJECTION clause (R): forward normally on the both-supplied call ----
    {
        "id": "weak-no-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        # Forwards/advises the honoured cases correctly, but on the contradictory
        # both-supplied input it forwards (the primary value) instead of refusing.
        # Correct on every single-selector / neither input; wrong only on the
        # both-supplied arm.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary, legacy with\n"
            "      | some c, some _ => Except.ok (some { forwarded := c, advisory := false })\n"
            "      | some c, none   => Except.ok (some { forwarded := c, advisory := false })\n"
            "      | none,   some d => Except.ok (some { forwarded := d, advisory := true })\n"
            "      | none,   none   => Except.ok none\n"
            "    return res"),
        "refinement": "a real patch that dropped the both-supplied guard SILENTLY "
                      "proceeds (forwarding a coordinate) when a caller supplies "
                      "BOTH selectors. The repo conflict semantics require a raise "
                      "(the test family asserts a ValueError on a contradictory "
                      "call); a silent-proceed patch never raises and does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = resolve primary legacy` on the rejection "
                     "(R): on the both-supplied input the post-image demands "
                     "`Except.error .bothSupplied` but the rival returns a normal "
                     "`Except.ok`. Control-flow-effect (refuse vs forward). Refuted "
                     "at `(some 4, some 7)` — the only both-supplied point, which "
                     "no other witness probes.",
        "witness": _witness("integrateDispatchTester (some 4) (some 7)"),
    },

    # ---- REJECTION clause (R): refuse UNCONDITIONALLY ----
    {
        "id": "weak-always-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-broad refusal: every call errors, honouring nothing. Trivially
        # correct only on the both-supplied sub-domain; wrong on every honoured
        # input.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      Except.error .bothSupplied\n"
            "    return res"),
        "refinement": "a real patch whose guard fires on `dim is not None or coord "
                      "is not None` (or refuses unconditionally) rejects the "
                      "ordinary single-selector calls outright. The F2P call must "
                      "SUCCEED (only warning); an unconditional refusal raises "
                      "instead of forwarding — it does NOT resolve.",
        "rationale": "REJECT from `out = resolve primary legacy` on the rejection "
                     "(R, over-broad): the refusal is sanctioned ONLY on the "
                     "both-supplied arm, so on any honoured input the post-image "
                     "demands `Except.ok …` but the rival errors. Supporting "
                     "control-flow-effect / over-broad-refusal case. Refuted at the "
                     "primary-only call `(some 5, none)`, which must forward.",
        "witness": _witness("integrateDispatchTester (some 5) none"),
    },

    # ---- NEITHER clause (N): forward a coordinate on the neither-supplied call
    {
        "id": "weak-forward-on-neither",
        "kind": "uniqueness",
        "expect": "reject",
        # Refuses/forwards/advises the other three arms correctly, but on the
        # neither-supplied input it fabricates a forwarded coordinate (`ok (some
        # …)`) instead of `ok none`. Isolates the `none, none` arm, which no other
        # rival touches. Correct on every input where at least one selector is
        # supplied; wrong only when both are absent.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary, legacy with\n"
            "      | some _, some _ => Except.error .bothSupplied\n"
            "      | some c, none   => Except.ok (some { forwarded := c, advisory := false })\n"
            "      | none,   some d => Except.ok (some { forwarded := d, advisory := true })\n"
            "      | none,   none   => Except.ok (some { forwarded := 0, advisory := false })\n"
            "    return res"),
        "refinement": "a real patch that fabricated a coordinate on the "
                      "neither-supplied call (rather than forwarding the absent "
                      "sentinel) would hand a bogus coordinate to the unchanged "
                      "integrator instead of letting the downstream "
                      "\"coordinate does not exist\" error surface. The "
                      "neither-supplied call must observe an error downstream, not "
                      "silently integrate along a fabricated coordinate — so it "
                      "does NOT resolve.",
        "rationale": "REJECT from `out = resolve primary legacy` on the neither "
                     "case (N): on `(none, none)` the post-image demands "
                     "`Except.ok none` but the rival returns `Except.ok (some …)`. "
                     "Isolates the neither-supplied arm — the sub-domain no other "
                     "rival exercises. Refuted at `(none, none)`.",
        "witness": _witness("integrateDispatchTester none none"),
    },

    # ---- ADVISORY clause (A): the advisory INVERTED on both honoured arms ----
    {
        "id": "weak-advisory-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). The existing advisory rivals each break ONE
        # honoured arm and leave the other correct, so each is refuted by a witness
        # at a point where the OTHER rival agrees with gold. This rival inverts the
        # advisory on BOTH honoured arms at once — silent on the legacy-only call,
        # advisory on the primary-only call — which is the "advisory attached to the
        # wrong selector" shape rather than "advisory missing" or "advisory always".
        # It is a strictly different impl from both existing advisory rivals and is
        # wrong at TWO points rather than one. Refuted at the legacy-only point.
        "module": _impl(
            "    let res : Except DispatchErr (Option Dispatch) :=\n"
            "      match primary, legacy with\n"
            "      | some _, some _ => Except.error .bothSupplied\n"
            "      | some c, none   => Except.ok (some { forwarded := c, advisory := true })\n"
            "      | none,   some d => Except.ok (some { forwarded := d, advisory := false })\n"
            "      | none,   none   => Except.ok none\n"
            "    return res"),
        "refinement": "a real patch that tests the WRONG selector when deciding "
                      "whether to emit the advisory (guarding on the primary "
                      "selector's presence instead of the legacy one's) forwards "
                      "every value correctly but attaches the advisory to exactly "
                      "the wrong call. The F2P asserts the advisory fires on the "
                      "legacy-only call — this patch stays silent there and instead "
                      "warns on the ordinary primary-selector call, so the warning "
                      "assertion fails AND the benign path turns noisy. It does NOT "
                      "resolve.",
        "rationale": "REJECT from `out = resolve primary legacy` on the advisory "
                     "(A, inverted): the post-image demands `advisory = true` on "
                     "`(none, some d)` and `advisory = false` on `(some c, none)`, "
                     "and this rival has both backwards. Wrong on TWO points, so it "
                     "is not subsumed by either single-arm advisory rival. Refuted "
                     "at `(none, some 2)` — an input point no other rival probes.",
        "witness": _witness("integrateDispatchTester none (some 2)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness) plus an empty AXIOM lane. The sibling
# models the SAME selector-routing prologue over two `Optional[int]` value
# parameters; this backend models it as `resolve` over `Selector = Option Nat`,
# with the outcome (refusal / forwarded value / advisory / neither) pinned
# EXACTLY by the sole ensures `out = resolve primary legacy`. The decision
# surface carries across intact. The sibling's five load-bearing clauses
# (C1..C6) collapse into a single exact-equality ensures here, so each nagini
# rival that attacked a clause becomes a rival that mis-handles one match arm.
#
#   sibling case            -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-reorder             -> pos-scrutinee-reorder             PORTED (reshaped)
#   (no sibling)            -> pos-nested-match                  ADDED (2nd pos.)
#   (no sibling)            -> pos-terminating-loop              ADDED BY AUDIT (F′)
#   admiss-legacy-only      -> admiss-all-arms-nondegenerate     RE-AIMED
#   w1-never-deprecate      -> weak-never-advise                 PORTED
#   w2-always-deprecate     -> weak-always-advise                PORTED
#   w3-wrong-coord          -> weak-wrong-forward                PORTED
#   w4-no-raise             -> weak-no-refuse                    PORTED
#   w5-always-raise         -> weak-always-refuse                PORTED
#   w6-diverge              -> pos-terminating-loop              LANE DEFENDED, not
#                                                                a hole (see below)
#   (no sibling)            -> weak-forward-on-neither           ADDED (arm cov.)
#   (no sibling)            -> weak-advisory-inverted            ADDED BY AUDIT (D)
#   AXIOM_TESTS (0)         -> (none)                            N/A (empty)
#
# 5 rivals ported + 1 positive ported + 1 admissibility re-aimed; 1 positive and
# 1 rival added for coverage at port time; 1 positive and 1 rival added by the
# audit; the divergence class is closed by the carrier and defended by a positive.
# Total: 3 soundness, 1 admissibility, 7 uniqueness = 11 SPEC cases.
#
# PORTED (pos-scrutinee-reorder). The sibling's positive is a branch/return
#   reshape (early-return cascade, no mutable `deprecated` local). This backend's
#   frozen impl is already a closed-form match, so the reshape SPIRIT —
#   "structurally different, behaviourally identical" — is carried by swapping the
#   two match scrutinees and permuting the arms. Same outcome on every input; the
#   frozen `loom_solve` closes it unchanged (verified to build).
# ADDED (pos-nested-match). A second reshape axis this backend affords: a nested
#   match (primary first, then legacy) instead of the flat two-scrutinee match.
#   Guards against SPEC-TOO-STRONG on the flat-vs-nested dispatch form. Verified
#   to build under the frozen proof.
# RE-AIMED (admissibility). The sibling constructs the F2P-shaped legacy-only
#   outcome inside the impl and asserts its fields. There is NO `require` clause
#   here, so the "precondition admits it" probe is degenerate; re-aimed at the
#   residual total-domain risk — that `resolve` is degenerate at the interesting
#   points — via an in-region assert that all four arms yield DISTINCT outcomes
#   (including the F2P-shaped legacy-only advisory-raising forward). Impl kept
#   verbatim; the frozen `loom_solve` closes the assert VC (verified to build).
# PORTED (5 rivals). weak-never-advise (C5, the pre-patch, THE discriminator),
#   weak-always-advise (C5 dual), weak-wrong-forward (C3 routing axis),
#   weak-no-refuse (C1/C6 refusal), weak-always-refuse (over-broad refusal) each
#   re-express their sibling onto the corresponding match arm of `resolve`. Each
#   refinement argument carries over verbatim in substance (a faithful counterpart
#   with that defect still mis-warns / mis-forwards / mis-refuses on the F2P or
#   P2P path, so it would NOT resolve). Each carries a machine-checked witness
#   that ELABORATES against the rival and FAILS against the frozen solution (two
#   real builds per case, plus a rival-verify build confirming each rival is
#   rejected by the verifier).
# ADDED (weak-forward-on-neither). The sibling's C1..C6 do not isolate the
#   neither-supplied outcome as a standalone rival, but the ensures pins the
#   `none, none` arm to `Except.ok none`. This rival fabricates a forwarded
#   coordinate on that arm, refuted at `(none, none)` — the one input no other
#   rival probes — so the battery demonstrates the spec's dependence on that arm.
# LANE DEFENDED, NOT A HOLE (w6-diverge). CORRECTED BY AUDIT. The sibling's W6
#   spins forever on the primary-selector path; under nagini's `MustTerminate(2)`
#   it is rejected, and pre-fix (no MustTerminate) it verified vacuously. The port
#   recorded the velvet analogue as a KNOWN SPEC HOLE on the stated ground that
#   this bundle runs under `termination "partial"`. IT DOES NOT: Solution.lean
#   line 4 reads `set_option loom.semantics.termination "total"`. The prose
#   described a different bundle, and under `total` the disposition INVERTS — the
#   verifier discharges a termination obligation, so a diverging impl does not
#   verify and there is no hole. Audit-measured, two builds:
#     * spin loop spliced BEFORE gold's resolution tail  -> exit 1
#     * spin loop spliced AFTER  gold's resolution tail  -> exit 1
#   both with `error: Decreasing annotations are required in total correctness
#   semantics`. So the frozen spec does NOT admit the diverging rival.
#   It is still not shippable as a REJECT case, for a mechanical reason the audit
#   measured rather than assumed: that termination error is raised by the `method`
#   elaboration, so it also fires in the witness file where the obligations are
#   stripped, and the extracted tester of a looping impl never reduces. The
#   witness `integrateDispatchTester (some 3) none = false` against the diverging
#   rival exits 1 with ``Tactic `decide` failed … reduction got stuck at the
#   `Decidable` instance`` — and that build is the half the gate requires to
#   SUCCEED. Retried with `decide +kernel`, `simp [integrateDispatchTester]` and
#   `rfl`: all three exit 1 on the rival side. So the lane is exercised from the
#   other direction instead, by `pos-terminating-loop`: a correct impl whose loop
#   DOES carry a `decreasing` measure, which must verify (audit-measured, exit 0).
#   That pins the termination obligation as discharged-and-SATISFIABLE rather than
#   merely unmentioned — the honest defense of this class on this carrier.
# ADDED BY AUDIT (weak-advisory-inverted). Attack D. The two ported advisory
#   rivals each break ONE honoured arm and leave the other agreeing with gold, so
#   neither probes the "advisory attached to the wrong selector" shape. This rival
#   inverts the advisory on BOTH honoured arms at once (silent on legacy-only,
#   advisory on primary-only) — wrong at two points, not subsumed by either. It is
#   REJECTED (exit 1) and its witness discriminates: rival exit 0, gold exit 1
#   with `Tactic decide proved that the proposition … is false`. The
#   claim-flipped forgery (`= true`) builds on gold at exit 0, confirming gold's
#   exit code tracks the CLAIM rather than being constant.
# ATTACK D / E RESIDUE (audit, no spec hole found). Six further wrong impls the
#   battery does not contain were built against the frozen spec and ALL SIX were
#   rejected (exit 1): advisory swapped on both arms, `forwarded := d + 1` on
#   legacy-only, refuse on the neither arm, a data-dependent advisory
#   (`advisory := decide (c = 0)`) on primary-only, a constant `forwarded := 0` on
#   primary-only, and `Except.ok none` on every arm. Three further CORRECT
#   reshapes were built: an advisory hoisted into a `let adv := primary.isNone`
#   binding (exit 0) and a legacy-first nested match (exit 0) both verify under the
#   frozen `loom_solve`; an `if primary.isSome && legacy.isSome then … else …`
#   guard ladder does NOT close under the frozen proof (`unsolved goals` on the
#   `if`-form) but DOES close once the elided proof body is retuned to
#   `loom_solve; cases primary <;> cases legacy <;> simp [resolve]` (exit 0,
#   measured) — a tactic-shape gap in the proof script, NOT a soundness hole in
#   the spec, and the proof region is elided from the spec view. No spec hole.
#
# BINDER / CLAUSE / ARM COVERAGE of the reject witnesses over the two input
#   binders of the sole ensures (pts = 6 distinct input points, one per rival):
#     (none, some 3)   — legacy-only: advisory should fire       (A)
#     (some 3, none)   — primary-only: advisory must NOT fire     (A dual)
#     (none, some 8)   — legacy-only: forwarded value            (F)
#     (some 4, some 7) — both-supplied: refusal                  (R)
#     (some 5, none)   — primary-only honoured: over-broad refuse (R)
#     (none, none)     — neither: the `ok none` arm              (N)
#     (none, some 2)   — legacy-only: advisory INVERTED          (A, both arms)
#   `primary` is varied across none / some 3 / some 4 / some 5, and `legacy`
#   across some 2 / some 3 / none / some 8 / some 7 — neither binder is held
#   constant, and the variation is MEANINGFUL rather than two spellings of one
#   point: each listed input changes the frozen spec's demanded outcome (a
#   different `resolve` arm, or a different field within an arm), which is why
#   each rival is refuted at its own point and no two rivals share an input tuple.
#   Every match arm of `resolve` is attacked by at least one rival: both-supplied
#   (weak-no-refuse), primary-only (weak-always-advise, weak-always-refuse),
#   legacy-only (weak-never-advise, weak-wrong-forward), neither
#   (weak-forward-on-neither); and each independent behaviour (refusal, forwarded
#   value, advisory, neither) has its own discriminator. No two rivals share an
#   input tuple.
# WITNESS DISCRIMINATION (verified during authoring, and INDEPENDENTLY RE-RUN BY
#   THE AUDIT with three real builds per reject case): each witness ELABORATES
#   against its rival (exit 0 — the extracted tester `decide`s to false, so the
#   rival's output violates the postcondition at the probed input) and FAILS
#   against the frozen solution (exit 1, `Tactic decide proved that the
#   proposition … is false`). Every gold-side signature is a PLAIN EVALUATION:
#   `decide` reduced the tester on this fully-transparent carrier and refuted the
#   claim on its merits — not a missing identifier, not a type error, not a stuck
#   unfolding, not a timeout. The audit additionally ran the FORGERY test on all
#   seven reject cases: the claim-flipped witness (`= true` in place of `= false`,
#   identical in every other byte) builds against the frozen solution at exit 0.
#   Gold's exit code therefore TRACKS THE CLAIM rather than being constant, which
#   is what makes the exit-1 half admissible evidence. No witness binds a
#   hypothesis (the carrier is fully transparent), so there is no
#   joint-satisfiability obligation.
#   No `sorry`/`admit`/`native_decide`/`axiom` appears in any witness (the
#   `deriving instance DecidableEq for Except` is an instance derivation, not an
#   assumption).
#
# AXIOM_TESTS: empty, matching the sibling (no consumed axioms, no A-reference
# deep models; `resolve` is an I-op checked by G-CONF). This gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
