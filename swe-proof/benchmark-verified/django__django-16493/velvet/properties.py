"""properties.py — G-PBT falsification battery for django__django-16493 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method over an optional-reference domain:

  serializedStorageArg (storage : Backend) (storageCallable : Option Backend)
      ensures out =
        (if (storageCallable.getD storage) ≠ defaultBackend
         then some (storageCallable.getD storage) else none)

``Backend`` is an opaque reference carrying only identity (``id : Nat``);
``defaultBackend`` is the one distinguished reference whose presence is
redundant. Both inputs are FREE, read-only values and there is no ``require``
clause, so the admitted domain is total: the post-image must hold for EVERY
pairing of the held reference and the (present-or-absent) configuring reference.

The single top-level ensures clause bundles TWO decisions over one derived
quantity ``value := storageCallable.getD storage`` (the configuring reference
when supplied, else the held reference):
  (a) the RECORDED VALUE — when a reference is emitted it must be exactly
      ``value`` (so the configuring reference, when present, takes precedence
      over the held one); and
  (b) the PRESENCE DECISION — a reference is emitted iff ``value`` is not the
      default. The load-bearing subtlety the change corrects is that this
      decision is keyed on ``value`` (the recorded reference), NOT on the held
      reference: the two diverge exactly when a configuring reference distinct
      from the default is present while the held reference IS the default.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini
    because an input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent: every parameter
    is an immutable value (neither input is a ``mut`` binder), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Reported as vacuous, not fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the method's own two arguments (``defaultBackend`` is a concrete
    ``def`` and the ``axioms`` region declares nothing) — there is no opaque
    answer key to echo. Instead we carry an honest cheapest-reshape POSITIVE
    CONTROL (``pos-*``).
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals right on part of the domain but
    diverging on a sub-domain (the presence decision keyed on the wrong
    quantity; always-emit; never-emit; recording the held reference in place of
    the configuring one). Each is refuted at a concrete point that varies the
    two input binders across the default / non-default and present / absent
    boundaries, so neither binder is pinned across the battery.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; the sub-computation
producing the held reference from a callable is an unchanged free input owed no
contract). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16493"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region (everything the variants replace). It is a single
# ---- contiguous block wholly inside the one `-- impl-start` / `-- impl-end`
# ---- region and unique in Solution.lean (the `let mut out` line occurs
# ---- nowhere else); both facts are asserted at load by _swap. -------------
_GOLD_IMPL = (
    "    let value := storageCallable.getD storage\n"
    "    let mut out : Option Backend := none\n"
    "    if value ≠ defaultBackend then\n"
    "      out := some value\n"
    "    return out"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


# The frozen proof body (the `prove_correct` tactic script). It is elided from
# the consumer spec view, so a variant that adds an in-region `assert` (which
# raises an extra side goal `loom_solve` leaves open) may retune it to discharge
# that goal — the obligation STATEMENT and the `prove_correct` header are
# untouched, so same_spec still holds. Anchored on the exact frozen script.
_GOLD_PROOF = "prove_correct serializedStorageArg by\n  loom_solve"


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. The spec here is a `method` CONTRACT, not a bare
# ---- predicate, so a witness reaches it through Velvet's own tester
# ---- machinery: `serializedStorageArgTester storage callable = false` says the
# ---- extracted program's result violates the method's postcondition at that
# ---- concrete input. Checked in a file whose `prove_correct` block has been
# ---- stripped, so no tactic script can mask the verdict. `Backend` derives
# ---- DecidableEq (and hence `Option Backend` does), so the postcondition is
# ---- decidable with no extra instance and every witness closes by `decide`.
def _tester(pre=""):
    m = "serializedStorageArg"
    return (f"{pre}extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the post-image is SPEC-TOO-STRONG. The
    # obligation is preserved and only the executable surface is reshaped;
    # the contract is a single point-wise equality over immutable values, so
    # no induction is needed and the frozen `loom_solve` still discharges it.
    # =====================================================================
    {
        "id": "pos-direct-if",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: derive the recorded reference once, then bind the result
        # with a single pure conditional expression, replacing the
        # mutable-accumulator form. Observationally identical on every input:
        # exactly the post-image, computed directly.
        "module": _impl(
            "    let value := storageCallable.getD storage\n"
            "    let out : Option Backend :=\n"
            "      if value ≠ defaultBackend then some value else none\n"
            "    return out"),
        "rationale": "a correct reshape (pure conditional binding of the result "
                     "instead of a mutable accumulator) computes the identical "
                     "`out` on every input and adds no new proof obligation, so "
                     "the single equality clause still discharges under the "
                     "frozen `loom_solve`; else SPEC-TOO-STRONG on impl shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal
    # input satisfies the precondition" probe is vacuous (nothing could
    # exclude the F2P-shaped input). Re-aimed at the residual admissibility
    # risk on a total domain: that the post-image is UNSATISFIABLE / degenerate
    # at the interesting point. This case discharges an in-region `assert`
    # pinning the post-image at the decisive corner — a configuring reference
    # distinct from the default present, while the held reference IS the
    # default — where it must demand that reference be RECORDED (not omitted).
    # The impl is kept verbatim so the method's own obligation still discharges;
    # the assert is live, not decoration: a false claim about the same point
    # leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-f2p-records-callable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      ((if ((some ({ id := 1 } : Backend)).getD defaultBackend)"
            " ≠ defaultBackend\n"
            "        then some ((some ({ id := 1 } : Backend)).getD defaultBackend)"
            " else none)\n"
            "       = some ({ id := 1 } : Backend)))\n" + _GOLD_IMPL,
            "prove_correct serializedStorageArg by\n  loom_solve <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P corner: a configuring reference distinct from the "
                     "default present while the held reference is the default "
                     "(`getD`'s fallback = defaultBackend) must RECORD that "
                     "reference (`some { id := 1 }`), not omit it. The in-region "
                     "assert must discharge (else the obligation is "
                     "unsatisfiable/PRECOND-TOO-STRONG); the impl is verbatim so "
                     "the equality clause still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Witnesses vary BOTH
    # binders: `storage` over the default `{ id := 0 }` and non-default
    # `{ id := 1 }` / `{ id := 2 }`, and `storageCallable` over `some _` and
    # `none`.
    # =====================================================================
    {
        "id": "weak-decision-keyed-on-held",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug. The recorded VALUE is right (the configuring
        # reference when present), but the presence decision is keyed on the
        # HELD reference rather than on that recorded value. Diverges exactly
        # when a configuring reference distinct from the default is present
        # while the held reference IS the default — the F2P corner.
        "module": _impl(
            "    let value := storageCallable.getD storage\n"
            "    let mut out : Option Backend := none\n"
            "    if storage ≠ defaultBackend then\n"
            "      out := some value\n"
            "    return out"),
        "refinement": "the faithful real counterpart keys the omit decision on "
                      "the already-evaluated held reference, so a field "
                      "configured by a callable that evaluates to the default "
                      "has its configuring reference dropped — exactly the "
                      "regression. The failing test that pins the recorded "
                      "reference for such a field to the configuring callable "
                      "still observes it absent and still fails. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the presence half of "
                     "`out = if value ≠ defaultBackend then some value else "
                     "none`: with a configuring reference `{ id := 1 } ≠ "
                     "default` present and the held reference the default, the "
                     "post-image demands `some { id := 1 }` but the impl keys on "
                     "the held reference (= default) and emits `none`. Refuted at "
                     "`storage = default`, `callable = some _`.",
        "witness": _tester() +
                   "example : serializedStorageArgTester { id := 0 } "
                   "(some { id := 1 }) = false := by\n  decide\n",
    },
    {
        "id": "weak-always-record",
        "kind": "uniqueness",
        "expect": "reject",
        # Records the recorded reference UNCONDITIONALLY — never omits, even
        # when it is the default. Right whenever the recorded value is
        # non-default; wrong exactly when it is the default (a field left on the
        # default backend, which must be omitted). Partial-domain dual of
        # weak-never-record.
        "module": _impl(
            "    let value := storageCallable.getD storage\n"
            "    let out : Option Backend := some value\n"
            "    return out"),
        "refinement": "a counterpart that always emits the reference records an "
                      "explicit entry for a field left on the default backend, "
                      "where the canonical default is re-supplied automatically "
                      "on rebuild. The existing deconstruction tests that assert "
                      "the reference is ABSENT for such a field still fail. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the presence half: at `value = defaultBackend` "
                     "(held reference default, no configuring reference) the "
                     "post-image demands `none` but the impl emits "
                     "`some defaultBackend`. Refuted at `storage = default`, "
                     "`callable = none`.",
        "witness": _tester() +
                   "example : serializedStorageArgTester { id := 0 } none "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-never-record",
        "kind": "uniqueness",
        "expect": "reject",
        # Emits nothing, ever. Right whenever the recorded value IS the default;
        # wrong exactly when it is non-default. The other-direction dual of
        # weak-always-record, refuted on the complementary sub-domain.
        "module": _impl(
            "    let out : Option Backend := none\n"
            "    return out"),
        "refinement": "a counterpart that never emits the reference cannot "
                      "round-trip any field carrying a non-default backend, so "
                      "the existing deconstruction tests that assert the "
                      "reference is PRESENT for such a field still fail. It would "
                      "NOT resolve.",
        "rationale": "REJECT from the presence half: at `value ≠ defaultBackend` "
                     "the post-image demands `some value` but the impl always "
                     "emits `none`. Refuted at `storage = { id := 1 }` "
                     "(non-default held reference), `callable = none` — the "
                     "sub-domain complementary to weak-always-record's.",
        "witness": _tester() +
                   "example : serializedStorageArgTester { id := 1 } none "
                   "= false := by\n  decide\n",
    },
    {
        "id": "weak-drops-callable-preference",
        "kind": "uniqueness",
        "expect": "reject",
        # Records the HELD reference, dropping the configuring reference's
        # precedence. The presence decision is even self-consistent (keyed on
        # the value it records), so this is a near-miss of the pre-fix bug: it
        # diverges on the RECORDED-VALUE half rather than the presence half, at
        # a NON-DEFAULT held reference where the pre-fix rival is correct.
        "module": _impl(
            "    let value := storage\n"
            "    let mut out : Option Backend := none\n"
            "    if value ≠ defaultBackend then\n"
            "      out := some value\n"
            "    return out"),
        "refinement": "recording the evaluated held reference instead of the "
                      "configuring one loses the deferred callable, so the "
                      "rebuilt field carries the evaluated backend rather than "
                      "the callable it was configured with. The existing test "
                      "that asserts the recorded reference IS the configuring "
                      "callable still fails. It would NOT resolve.",
        "rationale": "REJECT from the recorded-value half of the clause: with a "
                     "configuring reference `{ id := 1 }` present and a distinct "
                     "held reference `{ id := 2 }`, the post-image records "
                     "`some { id := 1 }` (the configuring reference takes "
                     "precedence) but the impl records `some { id := 2 }`. "
                     "Refuted at `storage = { id := 2 }`, `callable = "
                     "some { id := 1 }` — a NON-DEFAULT held reference, where "
                     "weak-decision-keyed-on-held agrees with the frozen "
                     "solution, so this near-miss carries its own separating "
                     "witness rather than that rival's.",
        "witness": _tester() +
                   "example : serializedStorageArgTester { id := 2 } "
                   "(some { id := 1 }) = false := by\n  decide\n",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 cases (1 soundness
# positive, 1 admissibility, 3 uniqueness rivals, 1 frame-mutation); the sibling
# contracts one function (`deconstruct_storage`) over a three-attribute field
# configuration (has_producer, producer_id, store_id), which this bundle models
# as a single method over (storage : Backend, storageCallable : Option Backend).
# The sibling's `reported_value(has_producer, producer_id, store_id) =
# producer_id if has_producer else store_id` IS `storageCallable.getD storage`
# here (`some c` <-> has a producer; `none` <-> no producer), so every sibling
# case lands on the same clause, re-expressed against this carrier.
#
#   sibling case                          -> here
#   ---------------------------------------------------------------------
#   pos-control-ternary-explicit-inclusion -> pos-direct-if            PORTED
#   admissibility-producer-f2p-shape       -> admiss-f2p-records-callable RE-AIMED
#   partial-domain-prepatch-guard          -> weak-decision-keyed-on-held PORTED
#   partial-domain-always-include          -> weak-always-record        PORTED
#   drop-producer-preference               -> weak-drops-callable-preference PORTED
#   frame-mutation-store-write             -> (none)                    VACUOUS
#
# 4 ported/re-expressed, 1 re-aimed, 1 vacuous = 6.
#
# RE-AIMED (admissibility): the sibling's case Asserts the F2P consequence under
#   a producer distinct from the default. That argument is preserved verbatim in
#   spirit, but since no method here has a `require` clause the "admits a normal
#   input" reading is vacuous; the case is re-aimed at proving the post-image is
#   satisfiable and NON-degenerate at the F2P corner (configuring reference
#   present and distinct from default, held reference default => the reference is
#   RECORDED). The in-region assert is discharged symbolically against concrete
#   literals so `loom_solve` closes it.
# FRAME-MUTATION: VACUOUS here, and for a stronger reason than the sibling's own
#   note. The sibling's rival WRITES a read-only input held at Acc(...,1/2). This
#   backend is referentially transparent, has no heap and no aliasing, and this
#   bundle declares NO `mut` binder — there is no read-only input to overwrite
#   and no substitute probe to build. No case fabricated.
#
# ADDED (1, no sibling counterpart): weak-never-record — the presence-decision
#   DUAL of weak-always-record, refuted on the complementary sub-domain
#   (non-default recorded value, where the reference must be emitted). The
#   sibling covers the "always-include" direction only; adding the "never-emit"
#   direction attacks the presence half from both sides and moves `storage` to a
#   third distinct value. It is a real divergence from the post-image with a
#   machine-checked witness, not a fabricated wrongness.
#
# BINDER / POINT COVERAGE. The four reject witnesses probe four distinct inputs:
#   (storage={0}, callable=some{1})   weak-decision-keyed-on-held
#   (storage={0}, callable=none)      weak-always-record
#   (storage={1}, callable=none)      weak-never-record
#   (storage={2}, callable=some{1})   weak-drops-callable-preference
#   so `storage` is varied over {0} (default), {1}, {2}, and `storageCallable`
#   over `some _` and `none`. Neither binder is pinned across the battery, and
#   the single top-level clause is attacked on BOTH of its halves (presence
#   decision and recorded value) and defended by the positive control and the
#   admissibility case.
#
# WITNESS DISTINCTNESS. weak-decision-keyed-on-held and
#   weak-drops-callable-preference agree with each other (and both diverge from
#   gold) at (storage={0}, callable=some{1}), but for DIFFERENT reasons — one
#   mishandles the presence decision, the other the recorded value. So
#   weak-drops-callable-preference is refuted at a NON-default held reference
#   (storage={2}), where weak-decision-keyed-on-held agrees with the frozen
#   solution (its presence decision keyed on a non-default held reference is
#   correct there) — making the near-miss's recorded-value claim machine-checked
#   rather than shared.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom, so there is nothing there to probe.
AXIOM_TESTS = []
