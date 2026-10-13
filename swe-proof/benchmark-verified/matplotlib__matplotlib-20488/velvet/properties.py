"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-20488 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct logNormVmin`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it elaborates against the rival and FAILS against the
frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  logNormVmin (sVmin : Rat) (eps : Rat) return (out : Rat)
    require eps > 0
    ensures (sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)

A single lower scale bound is sanitised before a logarithmic intensity mapping
is applied — such a mapping is only defined for strictly positive magnitudes.
The postcondition is TWO clauses partitioning the domain on the sign/zero
boundary of ``sVmin`` and pinning the result exactly on each side:

  (P1) ``sVmin ≤ 0 → out = eps`` — a lower bound that is NOT strictly positive
       (zero OR negative) is replaced by the strictly-positive floor ``eps``.
  (P2) ``sVmin > 0 → out = sVmin`` — a bound that is already strictly positive
       is passed through untouched.

The load-bearing behaviour is the boundary at ``sVmin = 0``: the pre-change
guard replaced only STRICTLY-negative bounds, leaving zero to reach the
logarithmic mapping (whose value at zero is undefined — the reported failure).
P1 pins exactly that point: at ``sVmin = 0`` the result must be the positive
floor, not zero. The post-image is grounded entirely in the inputs (``eps`` and
``sVmin`` themselves); there is no opaque answer-key to echo, so a wrong impl
cannot verify by mirroring an oracle — it must reproduce the selection.

CARRIER NOTE (decisive for this port). The carrier is Mathlib ``Rat`` (mapping.md
§2 — Float defeats the solver, Real is noncomputable, Rat is exact/computable and
the discriminating property is order-only). Because ``Rat`` order is decidable
and the whole post-image is a decidable proposition at concrete inputs, a rival's
disagreement with the spec is DECIDABLE at a literal point: each refutation
witness reaches the method contract through Velvet's tester machinery
(``logNormVminTester sVmin eps = false``) and closes by ``decide`` — no
conditioning on an opaque term, hence no witness binds anything and the gate's
consistency probe is a no-op. The uniqueness class is therefore LIVE on this
carrier. ONE trap was measured and worked around: ``decide`` reduces the
``Decidable`` instance but does not compute ``Rat`` ARITHMETIC, so a rival
returning ``eps + 1`` leaves the tester stuck (`decide` fails on both files); the
wrong-constant rival is expressed with a LITERAL positive constant (``1``)
instead, which the selection-only post-image decides cleanly. Every reject
witness below was SEEN to discriminate with two real builds: it ELABORATES
against the rival and FAILS against the frozen (straight-line, tester-reducible)
solution, whose tester returns ``true`` because gold satisfies the spec there.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally-different but CORRECT
    reshapes (positive-guard-first; a flat if-expression staged through the
    result) must still verify under the frozen ``loom_solve`` proof, else the spec
    is SPEC-TOO-STRONG on the branch shape.
  * ADMISSIBILITY — RE-AIMED. The sole precondition ``eps > 0`` is trivially
    satisfiable for every F2P-shaped input (``np.finfo(dtype).eps`` is always
    strictly positive), so the "a normal input meets the precondition" probe is
    vacuous. Re-aimed at the residual total-domain risk — that the post-image is
    degenerate / unsatisfiable — with a live in-region assert pinning the headline
    guarantee (the sanitised bound is strictly positive on the whole domain).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a transparent function of the
    inputs (``eps`` / ``sVmin``); the ``axioms`` region is empty (no opaque answer
    key). The cheapest correct impl simply selects, which the positive controls
    cover honestly.
  * FRAME-MUTATION (nagini's MANDATORY class) — VACUOUS here. The nagini sibling
    holds its inputs at a fractional heap permission an impl can illegally
    overwrite. Lean/Velvet are referentially transparent: ``sVmin`` and ``eps``
    are immutable values (neither is a ``mut`` binder), there is no heap, no
    aliasing and no permission system. No read-only input to overwrite and no
    substitute probe to build. Reported vacuous, not fabricated.

See the footer for the full nagini→velvet accounting.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20488"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen selection body, verbatim (the executable
# ---- lines strictly inside logNormVmin's -- impl-start / -- impl-end). Lies
# ---- wholly inside the single impl region and is unique in the file (the
# ---- prepatch skeleton lives in a different file); both facts asserted at load
# ---- by _swap. Every variant _swap()s only this block (and, where the reshape
# ---- needs it, the proof body below), so the edit never touches the spec
# ---- regions (axioms/pure/pre/post + the method signature and the `ensures`).
_IMPL = (
    "    if sVmin ≤ 0 then\n"
    "      return eps\n"
    "    else\n"
    "      return sVmin"
)
assert _BASE.count(_IMPL) == 1, "logNormVmin impl region drifted from expected text"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a case that introduces an in-region `assert` may
# ---- retune its script without touching the spec or dropping the obligation.
_PROOF = "prove_correct logNormVmin by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY logNormVmin's impl body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof_body):
    """Reshape the impl region AND retune the tactic body."""
    src = _swap(_BASE, _IMPL, new_impl)
    return _swap(src, _PROOF, "prove_correct logNormVmin by\n" + new_proof_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `logNormVminTester sVmin eps = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- masks the verdict. Closes by `decide` on the decidable Rat order carrier.
def _witness(call):
    return ("extract_program_for logNormVmin\n"
            "prove_precondition_decidable_for logNormVmin\n"
            "prove_postcondition_decidable_for logNormVmin\n"
            "derive_tester_for logNormVmin\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG. Each keeps the byte-identical obligation and the frozen
    # `prove_correct` body (`loom_solve`, which is generic over the selection
    # shape) and only reshapes the executable surface. Both verified out-of-band
    # with real builds.
    # =====================================================================
    {
        "id": "pos-control-positive-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: branch on the STRICTLY-POSITIVE case first (pass through),
        # falling to the floor otherwise. Same selection on the whole domain;
        # `≤ 0` and `> 0` partition the Rat line, so `else` is exactly the floor
        # branch. No new lemma — the frozen `loom_solve` closes unchanged.
        "module": _impl(
            "    if sVmin > 0 then\n"
            "      return sVmin\n"
            "    else\n"
            "      return eps"),
        "rationale": "structurally different CORRECT reshape: the sanitisation guard "
                     "is rewritten in positive form (branch on the already-positive "
                     "case first, floor otherwise). `> 0` and `≤ 0` partition the "
                     "Rat order, so the selection is identical on P1 and P2; the "
                     "frozen `loom_solve` proof closes unchanged. Must verify, else "
                     "SPEC-TOO-STRONG on the branch shape.",
    },
    {
        "id": "pos-control-flat-conditional",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: stage the whole result through a single if-expression returned
        # unconditionally — a flat (guard-less control-flow) shape with the gold
        # value. Proves the spec is not over-fitted to the gold's exact branch
        # statement.
        "module": _impl(
            "    return (if sVmin ≤ 0 then eps else sVmin)"),
        "rationale": "second correct shape: return a single if-expression "
                     "unconditionally rather than branching with two `return`s — a "
                     "flat control flow computing the gold selection. Proves the "
                     "spec admits a guard-less but correct shape; the frozen proof "
                     "closes unchanged. Must verify, else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sole precondition (`eps > 0`) is trivially satisfiable
    # for every F2P-shaped input (`np.finfo(dtype).eps` is always strictly
    # positive), so the "a normal input meets the precondition" probe is vacuous.
    # Re-aimed at the residual total-domain risk: that the post-image is
    # degenerate / UNSATISFIABLE (a spec no impl can meet reads exactly like one
    # every impl meets). The in-region assert pins the HEADLINE guarantee — the
    # sanitised bound is strictly positive on the WHOLE domain (this is the
    # property the logarithmic mapping needs, and the exact thing the boundary bug
    # violated at zero). The surrounding impl is kept verbatim so the method's own
    # obligation still discharges under `loom_solve`. The assert is live: replacing
    # `out > 0` with `out < 0` leaves an unsolved goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-floor-positive-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    let out := if sVmin ≤ 0 then eps else sVmin\n"
            "    assert (with_name_prefix `assert (out > 0))\n"
            "    return out",
            "  loom_solve"),
        "rationale": "the post-image is satisfiable AND non-degenerate: the sanitised "
                     "bound is STRICTLY POSITIVE on the whole domain (the headline "
                     "guarantee the logarithmic mapping requires) — `eps > 0` by "
                     "precondition on the floor branch, and `sVmin > 0` by the guard "
                     "on the passthrough branch. The live in-region assert `out > 0` "
                     "must discharge (else the obligation is unsatisfiable / "
                     "PRECOND-TOO-STRONG); the impl selection is kept verbatim so the "
                     "method's own `ensures` still discharges. (A false assert "
                     "`out < 0` leaves an unsolved goal — verified during authoring.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary BOTH input
    # binders: sVmin over {0, -1, 5} and eps over {3, 2, 1} across three distinct
    # points (pts=3).
    # =====================================================================
    {
        "id": "reject-strict-lt-misses-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour: sanitise only STRICTLY-negative bounds
        # (`< 0`), so a bound of exactly zero passes through to the logarithmic
        # mapping. Correct on the entire domain EXCEPT the single boundary point
        # sVmin = 0. (On this carrier the nagini `>= 0`-passthrough survivor is the
        # IDENTICAL total function — see footer — so it merges into this case.)
        "module": _impl(
            "    if sVmin < 0 then\n"
            "      return eps\n"
            "    else\n"
            "      return sVmin"),
        "refinement": "this IS the pre-change guard: sanitising only strictly "
                      "negative bounds leaves a lower bound of exactly zero to reach "
                      "the logarithmic intensity mapping, whose value there is "
                      "undefined — the exact reported failure (invalid lower bound "
                      "on a zero-floored log scale). The faithful counterpart still "
                      "feeds zero to that mapping, so it does NOT resolve.",
        "rationale": "REJECT from P1 (`sVmin ≤ 0 → out = eps`): at the boundary "
                     "sVmin = 0 the rival passes zero through (`0 < 0` is false) "
                     "while the spec forces the positive floor. Verifying would be "
                     "SPEC-TOO-WEAK at exactly the boundary the fix turns on. Refuted "
                     "at (sVmin = 0, eps = 3) — the single point on which `< 0` and "
                     "`≤ 0` diverge.",
        "witness": _witness("logNormVminTester 0 3"),
    },
    {
        "id": "reject-wrong-positive-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Sanitise the right domain but to a DIFFERENT positive value (the literal
        # constant 1) rather than the floor `eps`. Satisfies "strictly positive"
        # but violates the EXACT value P1 pins. A literal constant (not `eps + 1`)
        # is used deliberately: `decide` reduces the Decidable instance but not Rat
        # arithmetic, so `eps + 1` leaves the tester stuck on BOTH files (measured);
        # the literal keeps the post-image a pure selection the tester decides.
        # Agrees with gold only when eps = 1, so it is refuted at eps ≠ 1 — the
        # sub-domain that makes the post-image's dependence on `eps` observable.
        "module": _impl(
            "    if sVmin ≤ 0 then\n"
            "      return 1\n"
            "    else\n"
            "      return sVmin"),
        "refinement": "the faithful counterpart sets the sanitised bound to a fixed "
                      "constant of its own choosing rather than the precision floor "
                      "the input supplies. Handing the logarithmic mapping a lower "
                      "bound above the intended floor shifts the normalisation, so "
                      "the rendered figure no longer matches the reference image — "
                      "the image-level comparison FAILS and it does NOT resolve.",
        "rationale": "REJECT from P1 (`sVmin ≤ 0 → out = eps`): the rival returns the "
                     "constant 1, not `eps`, so it diverges whenever eps ≠ 1. This "
                     "proves P1 pins the floor VALUE (not merely positivity) and "
                     "demonstrates the post-image's dependence on the `eps` binder. "
                     "Verifying would be SPEC-TOO-WEAK on the floor value. Refuted at "
                     "(sVmin = -1, eps = 2): out = 1 ≠ 2.",
        "witness": _witness("logNormVminTester (-1) 2"),
    },
    {
        "id": "reject-overreach-clamps-positive",
        "kind": "uniqueness",
        "expect": "reject",
        # OVERREACH: clamp EVERY bound down to the floor, including an
        # already-strictly-positive one. Satisfies P1 (floor branch) but violates
        # P2 (passthrough) on the sVmin > 0 sub-domain. Isolates the passthrough
        # clause, which the boundary/constant rivals (both about the floor branch)
        # do not pin.
        "module": _impl(
            "    if sVmin ≤ 0 then\n"
            "      return eps\n"
            "    else\n"
            "      return eps"),
        "refinement": "the faithful counterpart floors a lower bound that is ALREADY "
                      "strictly positive, discarding the caller's intended bound. "
                      "For a normal positive-bounded log scale this replaces the "
                      "requested lower limit with the precision floor, changing the "
                      "normalisation so the rendered figure diverges from the "
                      "reference — the image comparison FAILS and it does NOT "
                      "resolve (and regresses the sibling passing case).",
        "rationale": "REJECT from P2 (`sVmin > 0 → out = sVmin`): on the "
                     "strictly-positive sub-domain the spec forces passthrough, "
                     "while the rival returns `eps`. This abuses the `sVmin` binder "
                     "on a sub-domain the floor-branch rivals never reach. Verifying "
                     "would be SPEC-TOO-WEAK on passthrough. Refuted at "
                     "(sVmin = 5, eps = 1): out = 1 ≠ 5.",
        "witness": _witness("logNormVminTester 5 1"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 5 uniqueness rivals) plus a 1-entry
# AXIOM lane. The sibling contracts one function `sanitized_lower_bound(is_log,
# lower_bound, eps)` over THREE scalar inputs partitioning the domain into three
# clauses (P1/P2/P3) gated by BOTH `is_log` and the sign of `lower_bound`. This
# bundle models the same fix over the `Rat` carrier as `logNormVmin(sVmin, eps)`
# — but the `is_log` gate is NOT a modeled input: mapping.md §2 records that the
# `isinstance(norm, LogNorm)` guard IS the modeled-operation framing (the
# precondition context), not a computed argument. So the modeled surface is the
# BODY of the log branch: two clauses (P1 floor / P2 passthrough) on the sign of
# `sVmin` alone. Every sibling case is accounted for.
#
#   sibling case (nagini)                    -> here
#   -------------------------------------------------------------------------
#   pos-control-nested-reorder                -> pos-control-positive-guard   PORTED
#   pos-control-cheapest-grounded             -> pos-control-flat-conditional PORTED
#   admiss-f2p-shaped                         -> admiss-floor-positive-grounded RE-AIMED
#   reject-partial-strict-lt-misses-zero      -> reject-strict-lt-misses-zero PORTED (central)
#   reject-partial-ge-zero-passthrough        -> reject-strict-lt-misses-zero MERGED (same fn)
#   reject-wrong-positive-constant            -> reject-wrong-positive-constant PORTED
#   reject-overreach-clamp-positive           -> reject-overreach-clamps-positive PORTED
#   reject-overreach-nonlog-sanitizes         -> (none)                       NOT MODELED
#   AXIOM_TESTS (1 entry)                     -> (none)                        DROPPED (G-AX)
#
# PORTED (2 positives): the nagini nested-reorder positive maps to
#   pos-control-positive-guard (branch on the positive case first — `> 0` / `≤ 0`
#   partition the Rat line); the cheapest-grounded conditional maps to
#   pos-control-flat-conditional (return one if-expression). Both keep the
#   byte-identical obligation and the frozen `loom_solve`, and both were verified
#   to build.
# PORTED / MERGED (3 rivals from 4 nagini rivals): the pre-patch `< 0` guard
#   (reject-partial-strict-lt-misses-zero) is the central rival, refuted at the
#   boundary sVmin = 0. The nagini G-MUT-survivor `>= 0`-passthrough
#   (reject-partial-ge-zero-passthrough) is, on the Rat carrier with `is_log`
#   folded into the framing, the IDENTICAL total function of (sVmin, eps) as the
#   `< 0` guard — both leak exactly sVmin = 0 and agree with gold everywhere else
#   — so it is not a distinct rival here (a separate reject case would be two
#   surfaces of one function, adding no coverage and sharing the same witness at
#   the same point for the same reason); it MERGES into reject-strict-lt-misses-
#   zero. The wrong-constant rival (P1 value pin) and the overreach-clamp rival
#   (P2 passthrough pin) port directly.
# RE-AIMED (1): admiss-f2p-shaped relied on the sibling's `is_log=True,
#   lower_bound=0.0` input lying inside the precondition. Here the sole
#   precondition `eps > 0` is trivially satisfiable for every F2P-shaped input, so
#   that probe is vacuous. Re-aimed at the total-domain admissibility risk (a
#   degenerate / unsatisfiable post-image) with a live in-region assert pinning
#   the headline guarantee: the sanitised bound is strictly positive on the whole
#   domain.
# NOT MODELED — carrier narrowing (1): reject-overreach-nonlog-sanitizes attacks
#   the `is_log` GATE (sanitise in the non-log branch). This bundle does not model
#   `is_log` as an input at all — the LogNorm guard is the modeled-operation
#   framing (mapping.md §2), so there is no non-log branch and no `is_log` binder
#   to mishandle. Attacking it would require fabricating an input this bundle does
#   not carry. Legitimately omitted, not a hidden gap.
# VACUOUS — frame/permission-mutation: the nagini DEFENDED-SURFACE docstring notes
#   all inputs are scalar-by-value with NO Acc(x,1/2) reference and NO frame to
#   mutate, so the sibling itself declares the frame class N/A. On this
#   referentially-transparent backend it is likewise vacuous: `sVmin` and `eps`
#   are immutable values (neither is `mut`), no heap, no aliasing, no permission
#   system. No probe fabricated (per the porting map).
# DROPPED (AXIOM_TESTS, 1 entry): the nagini axiom-soundness probe grounds
#   `Requires(eps>0.0)` in the real callee `np.finfo(dtype).eps > 0`. That belongs
#   to the G-AX lane; this bundle declares NO axiom (mapping.md §4 — `eps` is a
#   plain positive input, its positivity captured by `require eps > 0`, with no
#   axiom_check.py). This gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Two input binders, both varied and both abused:
#     sVmin -> 0 (boundary), -1 (negative), 5 (positive)
#     eps   -> 3, 2, 1
#   Both top-level clauses are attacked: P1 (`sVmin ≤ 0 → out = eps`) by
#   reject-strict-lt-misses-zero (the boundary point, out = sVmin not eps) and
#   reject-wrong-positive-constant (the floor VALUE, out = 1 not eps — refuted at
#   eps = 2 ≠ 1, which is what makes the dependence on the `eps` binder
#   observable); P2 (`sVmin > 0 → out = sVmin`) by reject-overreach-clamps-positive
#   (passthrough, refuted at sVmin = 5 — which makes the dependence on the `sVmin`
#   binder observable). Both clauses are defended by the two positive controls and
#   the admissibility assert. The three reject witnesses probe three DISTINCT input
#   points (pts=3); no point is pinned across the battery.
#
# CARRIER NOTE. The `Rat` carrier is order-decidable and the post-image is a
#   decidable proposition, so every witness refutes at concrete literals via the
#   tester machinery and closes by `decide` — no conditioning on an opaque term,
#   hence no witness binds anything and the consistency probe is a no-op. Each
#   witness was SEEN to discriminate with two real builds (ELABORATES against the
#   rival, FAILS against the frozen solution). The one measured trap: `decide`
#   does not compute Rat ARITHMETIC (an `eps + 1` rival leaves the tester stuck on
#   both files), so the wrong-constant rival uses a LITERAL positive constant,
#   keeping its post-image a pure selection the tester decides.
AXIOM_TESTS = []
