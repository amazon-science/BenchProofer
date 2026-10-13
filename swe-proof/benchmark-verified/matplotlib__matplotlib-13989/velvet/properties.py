"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-13989 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct buildHistOptionsM`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method over three value inputs):

  buildHistOptionsM
      (boundsOpt : Option (Float × Float)) (density : Bool) (accumulate : Bool)
      return (out : HistOptions)
    ensures out = buildHistOptions boundsOpt density accumulate            (C1)
    ensures out.boundsOpt = boundsOpt                                      (C2)
    ensures (density = true ∧ accumulate = false) →
              out.densityOpt = some density                               (C3)
    ensures ¬(density = true ∧ accumulate = false) →
              out.densityOpt = none                                       (C4)

The operation assembles the two-entry option mapping handed to a single
histogram computation: a bounds entry (``boundsOpt`` — present when explicit
lower/upper data bounds were determined, absent otherwise) and a density entry
(``densityOpt`` — recorded when the density choice applies to this computation).
The desired behaviour the issue demands: recording the density choice must NOT
discard the already-determined bounds entry.

  * C1 pins the whole result to the transparent ``def buildHistOptions`` — a
    concrete deep model, NOT an opaque oracle (the ``axioms`` region is empty),
    so there is no answer key a wrong impl could echo. C1 alone implies C2/C3/C4,
    but the three explicit clauses name the facets a rival attacks;
  * C2 (bounds survival) is the load-bearing clause the fix turns on: the bounds
    entry of the result is ALWAYS exactly the bounds entry that was determined,
    regardless of the density branch;
  * C3 pins the density entry's PRESENCE and VALUE on the density sub-domain
    (a density computation that is not accumulated);
  * C4 pins the density entry ABSENT off that sub-domain.

The method has NO ``require`` clause, so the admitted domain is total.

CARRIER NOTE — WHY THE SIBLING TESTER ROUTE IS UNAVAILABLE HERE. The result
carrier ``HistOptions`` embeds ``Option (Float × Float)`` and ``Float`` has NO
``DecidableEq`` in this workspace (``failed to synthesize DecidableEq Float`` —
confirmed empirically). So ``prove_postcondition_decidable_for`` cannot discharge
the C1/C2 clauses and ``derive_tester_for`` does not yield a usable
``buildHistOptionsMTester``. The witnesses therefore state the refutation
DIRECTLY against the extracted executable ``buildHistOptionsMExec`` (produced by
``extract_program_for``): each asserts

    buildHistOptionsMExec <bounds> <density> <accumulate>
      ≠ DivM.res (buildHistOptions <bounds> <density> <accumulate>)

i.e. the rival's extracted result differs from the spec's deep model at that
concrete input — exactly what C1 forbids. The proof reduces the monadic run
(``simp only [NonDetT.run]``), then peels the two ``DivM.res``/``HistOptions.mk``
constructors by ``injection`` and closes the surviving field inequality by
``simp_all``. Confirmed empirically per rival: the witness ELABORATES against its
rival and FAILS against the frozen solution.

Two witness FORMS are needed, because C2 has two independently attackable halves
and only one of them is decidable at a literal:

  * PRESENCE (``boundsOpt`` as ``none`` vs ``some _``, ``densityOpt`` as
    ``none`` vs ``some b`` and as ``some b`` vs ``some b'`` over ``Bool``) — a
    constructor clash on a decidable projection. Stated at literal inputs, so the
    witness head binds NOTHING and the consistency probe is not reached. Six of
    the seven rivals below.
  * PAYLOAD IDENTITY (``boundsOpt = some (lo, hi)`` with the SAME pair the caller
    determined) — NOT decidable at a literal here: ``Float`` has no
    ``DecidableEq``, and the kernel cannot even reduce ``(0.0 : Float) == 1.0``
    to ``false`` (``#eval`` says ``false``, ``rfl`` fails — measured). So the
    payload half is attacked the way an opaque carrier always is: the refutation
    is stated at a point described by HYPOTHESIS (``(lo hi : Float) (hne : lo ≠ hi)``)
    rather than computed, and ``simp_all`` closes it from ``hne``. Nothing has to
    PROVE the guard; the gate's consistency probe then confirms the hypotheses are
    satisfiable, which an opaque ``Float`` makes easy (no tactic derives ``False``
    from ``lo ≠ hi`` — measured: the probe fails, as it must). This is
    ``rival-bounds-transpose``, and it is the only witness that puts a ``Float``
    payload in the goal at all.

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend, exactly as the nagini
    sibling records it N/A: every parameter is an immutable value carrier
    (``Option (Float × Float)``, ``Bool``, ``Bool``) passed by value; Lean and
    Velvet are referentially transparent, there is no heap, no aliasing, no
    fractional permission, and this bundle declares NO ``mut`` parameter. There
    is no read-only input to overwrite and no substitute probe to fabricate (per
    the porting map, legitimately dropped, not faked). The frame ARGUMENT is not
    lost — it is re-expressed as C2 (the determined bounds entry is carried
    through unchanged) and attacked by the bounds-drop / bounds-fabricate rivals.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. C1 pins the result to the transparent ``def
    buildHistOptions`` (a two-entry structure literal over an ``if``), not to an
    axiomatized oracle; there is no opaque answer key a wrong impl could echo.
    The cheapest correct impl returns ``buildHistOptions boundsOpt density
    accumulate`` directly, which the positive controls cover honestly.
  * PARTIAL-DOMAIN / VALUE / KEY-SET — APPLIES, and is the whole reject surface
    (see the seven rivals below).

WITNESS PLACEMENT. The seven reject witnesses sit at SIX DISTINCT input points,
moving every input binder across the battery: ``boundsOpt`` over
{some(0,1), none, some(lo,hi) with lo ≠ hi} — absent, present-literal, and
present-symbolic; ``density`` over {true, false} — both; ``accumulate`` over
{false, true} — both. So no facet is demonstrated at a single pinned point, and
each binder C1 depends on is varied by some witness. Both HALVES of C2 are
witnessed: presence (rival-rebind-drop, rival-bounds-fabricate, rival-empty) and
payload identity (rival-bounds-transpose). Both halves of C3 likewise: VALUE by
rival-wrong-density-value and PRESENCE by rival-density-never. Two rivals
(rival-rebind-drop, rival-density-never) share the input point
(some(0,1), true, false) — the F2P-shaped point — but refute on DIFFERENT
projections of the result there (the bounds field vs the density field), which is
why the shared point is not a duplicated probe.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-13989"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl body (the single
# ---- `-- impl-start`/`-- impl-end` region, inclusive) and unique in Solution.lean.
_GOLD_IMPL = """    -- impl-start
    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
    let result : HistOptions :=
      if density && !accumulate then
        { base with densityOpt := some density }
      else
        base
    return result
    -- impl-end"""
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# ---- proof-block anchor. The frozen `prove_correct` tactic body. A soundness
# ---- positive whose impl shape needs a different-but-honest closer swaps this
# ---- for a stronger tactic; NO new lemma/axiom/sorry is introduced (only the
# ---- goal-management combinator changes). The `prove_correct buildHistOptionsM`
# ---- HEADER is preserved verbatim, so the obligation survives.
_GOLD_PROOF = """prove_correct buildHistOptionsM by
  loom_solve
  cases density <;> cases accumulate <;> simp_all [buildHistOptions]"""
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof block drifted from expected text"

# A closer that dispatches every residual goal (the frozen closer plus the extra
# goal a reshaped impl / an in-region assert introduces). Same tactics, wrapped
# in `all_goals`; no assumption added.
_ALLGOALS_PROOF = """prove_correct buildHistOptionsM by
  loom_solve
  all_goals (cases density <;> cases accumulate <;> simp_all [buildHistOptions])"""


def _variant(impl_body, proof=None):
    """Full Solution.lean variant with the impl region body replaced (and,
    optionally, the frozen proof tactic body swapped for `_ALLGOALS_PROOF`). The
    `prove_correct buildHistOptionsM` header is kept, so the obligation survives;
    a reject rival keeps the frozen proof and is expected NOT to verify, its
    witness carrying the evidence."""
    out = _swap(_BASE, _GOLD_IMPL,
                "    -- impl-start\n" + impl_body + "\n    -- impl-end")
    if proof is not None:
        out = _swap(out, _GOLD_PROOF, proof)
    return out


# ---- witness machinery. `Float` has no DecidableEq, so the postcondition tester
# ---- route is unavailable (see CARRIER NOTE). Instead each witness extracts the
# ---- executable and states the refutation directly against it: the rival's
# ---- extracted result differs from the deep model `buildHistOptions` at one
# ---- concrete input, which C1 forbids. Checked in a file whose `prove_correct`
# ---- block is stripped (so no tactic script can mask the verdict); the proof
# ---- reduces the run, peels the DivM.res / HistOptions.mk constructors, and
# ---- closes the surviving decidable-field inequality. No sorry/admit/
# ---- native_decide.
def _witness(bounds, density, accumulate):
    return (
        "extract_program_for buildHistOptionsM\n\n"
        "example :\n"
        f"    buildHistOptionsMExec ({bounds}) {density} {accumulate}\n"
        f"      ≠ DivM.res (buildHistOptions ({bounds}) {density} {accumulate}) := by\n"
        "  unfold buildHistOptionsMExec buildHistOptions\n"
        "  simp only [NonDetT.run]\n"
        "  intro h\n"
        "  injection h with h1\n"
        "  injection h1 with hb hd\n"
        "  simp_all\n")


# ---- CONDITIONED witness, for the PAYLOAD-IDENTITY half of C2. `Float` has no
# ---- DecidableEq and the kernel cannot reduce a Float comparison at all, so a
# ---- literal bounds pair decides nothing about the payload. The refutation is
# ---- therefore stated at a point described by HYPOTHESIS — an arbitrary
# ---- non-degenerate pair `(lo, hi)`, `lo ≠ hi` — which is the standard way an
# ---- opaque carrier is attacked. `simp_all` closes the peeled field inequality
# ---- from `hne`; nothing proves the guard, and the gate's consistency probe
# ---- confirms `lo ≠ hi` is satisfiable (no tactic derives `False` from it).
_WITNESS_BOUNDS_PAYLOAD = (
    "extract_program_for buildHistOptionsM\n\n"
    "example (lo hi : Float) (hne : lo ≠ hi) :\n"
    "    buildHistOptionsMExec (some (lo, hi)) true false\n"
    "      ≠ DivM.res (buildHistOptions (some (lo, hi)) true false) := by\n"
    "  unfold buildHistOptionsMExec buildHistOptions\n"
    "  simp only [NonDetT.run]\n"
    "  intro h\n"
    "  injection h with h1\n"
    "  injection h1 with hb hd\n"
    "  simp_all\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-spec",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the modeled assembly directly. Honest cheapest-correct
        # impl; C1 holds by definition. The frozen closer leaves one residual
        # goal (the density facet under the direct return), so the tactic body is
        # wrapped in `all_goals` — same tactics, no new lemma/assumption.
        "module": _variant(
            "    return buildHistOptions boundsOpt density accumulate",
            proof=_ALLGOALS_PROOF),
        "rationale": "the straight-line `return buildHistOptions boundsOpt "
                     "density accumulate` is the simplest correct impl; it meets "
                     "C1 by definition, hence C2/C3/C4. If it failed to verify the "
                     "postcondition would be over-fit to the let-binding form => "
                     "SPEC-TOO-STRONG. Only the goal-management combinator changes "
                     "in the proof; no assumption is added.",
    },
    {
        "id": "pos-single-record-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the density entry into a local `Option Bool` first,
        # then build the result in ONE structure literal (no `{ base with ... }`
        # update). Same behaviour, different executable shape; the frozen proof
        # closes unchanged.
        "module": _variant(
            "    let d : Option Bool := if density && !accumulate then some density else none\n"
            "    return { boundsOpt := boundsOpt, densityOpt := d }"),
        "rationale": "the density entry is computed into a local and the result "
                     "built in one structure literal (no record-update). Same "
                     "writes, different shape; must verify under the frozen proof. "
                     "If it cannot, the spec is over-fit to the record-update form "
                     "=> SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method has NO `require` clause, so the
    # nagini "a self-call on an F2P-shaped input satisfies the precondition"
    # probe is vacuous on the total domain — nothing could exclude any input.
    # Re-aimed at the residual admissibility risk: that the post-image is
    # DEGENERATE so no rival could be distinguished. This case discharges an
    # in-region `assert`, at the concrete F2P-shaped input, that the modeled
    # behaviour genuinely records BOTH the determined bounds AND the density
    # choice at once — the exact conjunction the issue demands. The frozen impl
    # is kept verbatim so C1..C4 still discharge; the assert is LIVE (a false
    # claim leaves an unsolved goal — confirmed empirically). The extra goal the
    # assert introduces is dispatched by `all_goals` (same tactics, no
    # assumption added).
    # =====================================================================
    {
        "id": "admiss-f2p-bounds-and-density",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(
            "    assert (with_name_prefix `adm\n"
            "      ((buildHistOptions (some (0.0, 1.0)) true false).boundsOpt "
            "= some (0.0, 1.0) ∧\n"
            "       (buildHistOptions (some (0.0, 1.0)) true false).densityOpt "
            "= some true))\n"
            "    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }\n"
            "    let result : HistOptions :=\n"
            "      if density && !accumulate then\n"
            "        { base with densityOpt := some density }\n"
            "      else\n"
            "        base\n"
            "    return result",
            proof=_ALLGOALS_PROOF),
        "rationale": "on the F2P-shaped input (bounds determined, density "
                     "requested, not accumulated) the modeled assembly records "
                     "BOTH the determined bounds AND the density choice at once — "
                     "the post-image is non-degenerate and actually pins the "
                     "conjunction the issue demands, not a constant. The in-region "
                     "assert must discharge (else the modeled behaviour would be "
                     "degenerate); the frozen impl is kept verbatim so C1..C4 "
                     "still discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each carrying a machine-checked refutation witness at
    # a DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "rival-rebind-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # THE base-commit bug: the density branch REBUILDS the mapping with only
        # the density entry, discarding the determined bounds entry (facet C2).
        "module": _variant(
            "    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }\n"
            "    let result : HistOptions :=\n"
            "      if density && !accumulate then\n"
            "        { boundsOpt := none, densityOpt := some density }\n"
            "      else\n"
            "        base\n"
            "    return result"),
        "refinement": "this is the pre-change behaviour: on the density sub-domain "
                      "the mapping is rebuilt carrying only the density entry, so "
                      "the explicitly-determined bounds entry is dropped. A "
                      "histogram computation then receives no bounds, so its bins "
                      "no longer span the requested interval and the failing test "
                      "(which pins the bins to that interval exactly) fails. It "
                      "would NOT resolve.",
        "rationale": "REJECT from C2 (bounds survival): with bounds determined and "
                     "the density branch taken, out.boundsOpt = none ≠ boundsOpt. "
                     "Refuted at (some(0,1), density=true, accumulate=false), where "
                     "the rival drops the bounds but the deep model keeps them. A "
                     "verify here is SPEC-TOO-WEAK (the survival clause "
                     "unenforced) — the discriminating clause the fix turns on.",
        "witness": _witness("some (0.0, 1.0)", "true", "false"),
    },
    {
        "id": "rival-bounds-fabricate",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain (bounds ABSENT sub-domain): the rival FABRICATES a bounds
        # entry even when none was determined. Mirrors the nagini range-always
        # rival (records the bounds entry unconditionally, including the branch
        # where no explicit bounds apply). Attacks C2 on the `boundsOpt = none`
        # sub-domain.
        "module": _variant(
            "    let base : HistOptions := { boundsOpt := some (0.0, 0.0), densityOpt := none }\n"
            "    let result : HistOptions :=\n"
            "      if density && !accumulate then\n"
            "        { base with densityOpt := some density }\n"
            "      else\n"
            "        base\n"
            "    return result"),
        "refinement": "records a bounds entry unconditionally, including the "
                      "computation where no explicit bounds were determined "
                      "(boundsOpt = none). A faithful counterpart forwards a bounds "
                      "keyword the histogram routine would otherwise not receive, "
                      "so a computation whose bins were already fixed by an "
                      "explicit edge array gets a conflicting bounds argument and "
                      "is mis-binned; those histogram tests break. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C2 on the bounds-absent sub-domain: when "
                     "boundsOpt = none the rival returns out.boundsOpt = "
                     "some (0,0) ≠ none. Refuted at (none, density=false, "
                     "accumulate=false). A verify here would mean C2 does not pin "
                     "the bounds entry to the input on the absent sub-domain "
                     "(SPEC-TOO-WEAK).",
        "witness": _witness("none", "false", "false"),
    },
    {
        "id": "rival-bounds-transpose",
        "kind": "uniqueness",
        "expect": "reject",
        # C2's PAYLOAD-IDENTITY half: the rival KEEPS the bounds entry present on
        # every branch (so every presence-only witness in this battery passes it)
        # but hands on a TRANSPOSED pair — lower and upper exchanged. Presence
        # preserved, identity destroyed. This is the facet the four literal
        # witnesses above cannot reach, since a Float pair is opaque to the
        # kernel; its witness conditions on `lo ≠ hi` instead.
        "module": _variant(
            "    let b2 : Option (Float × Float) := boundsOpt.map (fun p => (p.2, p.1))\n"
            "    let base : HistOptions := { boundsOpt := b2, densityOpt := none }\n"
            "    let result : HistOptions :=\n"
            "      if density && !accumulate then\n"
            "        { base with densityOpt := some density }\n"
            "      else\n"
            "        base\n"
            "    return result"),
        "refinement": "carries the determined bounds through with its two ends "
                      "exchanged. A faithful counterpart forwards a reversed "
                      "lower/upper bounds pair to the histogram routine: the bins "
                      "no longer span the requested interval in the requested "
                      "orientation, so the failing test (which pins the first and "
                      "last bin edge to the two ends of that interval, in order) "
                      "still fails — a computation asked for the interval it named "
                      "gets its mirror image. It would NOT resolve.",
        "rationale": "REJECT from C2 read as an IDENTITY, not merely a presence: "
                     "out.boundsOpt = boundsOpt demands the very pair that was "
                     "determined, so a transposed pair violates it while keeping "
                     "the entry present on every branch. Refuted at "
                     "(some (lo, hi), density=true, accumulate=false) for an "
                     "arbitrary lo ≠ hi — the witness must condition rather than "
                     "compute, because Float is opaque to the kernel here. A verify "
                     "here would mean C2 pins only that SOME bounds entry survives, "
                     "not WHICH (SPEC-TOO-WEAK on the payload).",
        "witness": _WITNESS_BOUNDS_PAYLOAD,
    },
    {
        "id": "rival-wrong-density-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Records the density entry but with the WRONG value (`some (!density)`
        # instead of `some density`). Right presence, wrong payload (facet C3).
        "module": _variant(
            "    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }\n"
            "    let result : HistOptions :=\n"
            "      if density && !accumulate then\n"
            "        { base with densityOpt := some (!density) }\n"
            "      else\n"
            "        base\n"
            "    return result"),
        "refinement": "records the density entry with the negated value. A "
                      "faithful counterpart forwards the opposite normalize choice "
                      "to the histogram routine, so the requested density "
                      "normalization is silently inverted and the density tests "
                      "fail. It would NOT resolve.",
        "rationale": "REJECT from C3 (density value): on the density sub-domain "
                     "out.densityOpt = some (!density) ≠ some density. Refuted at "
                     "(none, density=true, accumulate=false), where the rival "
                     "records some false but the spec demands some true. A verify "
                     "here is SPEC-TOO-WEAK (the density value unpinned).",
        "witness": _witness("none", "true", "false"),
    },
    {
        "id": "rival-density-never",
        "kind": "uniqueness",
        "expect": "reject",
        # C3's PRESENCE half: the density entry is NEVER recorded, on any branch,
        # while the bounds entry is carried through exactly. The mirror image of
        # rival-wrong-density-value (right presence, wrong payload): here the
        # payload question never arises because the entry is absent where C3
        # demands it be present. No other rival isolates this — every other
        # density attack either corrupts the VALUE of a present entry or bundles
        # the density failure with a bounds drop (rival-empty), so a spec that
        # pinned only the density entry's value and not its presence would still
        # reject all of them.
        "module": _variant(
            "    return { boundsOpt := boundsOpt, densityOpt := none }"),
        "refinement": "never records the density choice at all, while carrying "
                      "the determined bounds through untouched. A faithful "
                      "counterpart forwards no normalize choice to the histogram "
                      "routine, so a computation asked to normalize returns raw "
                      "counts instead of a density and every density test fails. "
                      "It leaves the bounds behaviour correct, so it would pass a "
                      "bounds-only check while still not resolving.",
        "rationale": "REJECT from C3 (density PRESENCE, not merely value): on the "
                     "density sub-domain C3 demands out.densityOpt = some density, "
                     "but the rival returns none — a none-vs-some constructor "
                     "clash, decidable here. Refuted at (some(0,1), density=true, "
                     "accumulate=false), the F2P-shaped point; it shares that "
                     "point with rival-rebind-drop but refutes on the OTHER "
                     "projection (density field, not bounds field). A verify here "
                     "would mean C3 pins only WHICH value a present density entry "
                     "carries and not THAT one is recorded (SPEC-TOO-WEAK on the "
                     "presence half).",
        "witness": _witness("some (0.0, 1.0)", "true", "false"),
    },
    {
        "id": "rival-ignore-accumulate",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain (accumulate sub-domain): records the density entry
        # whenever density is requested, DROPPING the `!accumulate` guard. Mirrors
        # the nagini ignore-stacked rival. Attacks C4 (density present when it
        # must be absent).
        "module": _variant(
            "    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }\n"
            "    let result : HistOptions :=\n"
            "      if density then\n"
            "        { base with densityOpt := some density }\n"
            "      else\n"
            "        base\n"
            "    return result"),
        "refinement": "records the density entry whenever density is requested, "
                      "dropping the not-accumulated guard. A faithful counterpart "
                      "forwards the density choice to accumulated computations too, "
                      "so an accumulated-density histogram is normalized per "
                      "component instead of as an accumulation and the "
                      "accumulated-density tests fail. It would NOT resolve.",
        "rationale": "REJECT from C4 (density absent off the sub-domain): with "
                     "density=true and accumulate=true, ¬(density ∧ ¬accumulate) "
                     "holds so the spec demands densityOpt = none, but the rival "
                     "returns some true. Refuted at (none, density=true, "
                     "accumulate=true) — the accumulate sub-domain no other rival "
                     "isolates. A verify here is SPEC-TOO-WEAK (the accumulate "
                     "guard unenforced).",
        "witness": _witness("none", "true", "true"),
    },
    {
        "id": "rival-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheap supporting near-miss: returns the empty mapping always. Neither
        # bounds nor density ever reaches the histogram routine. Fails C2 (and
        # C3). Witnessed on the bounds-drop it shares with the base-commit bug but
        # at a DISTINCT input (bounds determined, density NOT requested), so it
        # isolates the no-density corner rather than duplicating rebind's point.
        "module": _variant(
            "    return { boundsOpt := none, densityOpt := none }"),
        "refinement": "forwards no options at all; neither the determined bounds "
                      "nor the density choice reaches the histogram routine, so "
                      "both the failing bounds test and the density tests fail. "
                      "Cheap supporting near-miss with a real refinement (it never "
                      "substitutes for the reasoned attacks above).",
        "rationale": "REJECT from C2 (bounds survival): with bounds determined the "
                     "rival returns out.boundsOpt = none ≠ boundsOpt. Refuted at "
                     "(some(0,1), density=false, accumulate=false) — bounds "
                     "determined but density NOT requested, a distinct corner from "
                     "rival-rebind-drop, so the two probe different points.",
        "witness": _witness("some (0.0, 1.0)", "false", "false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus 2 AXIOM_TESTS. The
# sibling contracts `assemble_binning_options(multi_precomputed, density,
# stacked, range_value) -> Dict[int,int]` over a `Dict[int,int]` carrier of key
# tokens (KEY_RANGE=0 / KEY_DENSITY=1), with six postcondition clauses (C1
# wellformed .. C6 key-set upper bound). This bundle models the SAME assembly
# more directly: a two-field `HistOptions` structure chosen by the density guard
# (`out = buildHistOptions boundsOpt density accumulate`). The bijection
# (mapping.md): the dict's KEY_RANGE presence <-> `boundsOpt = some _`,
# KEY_DENSITY presence/value <-> `densityOpt = some b`; `multi_precomputed` (which
# in the sibling controls whether KEY_RANGE is recorded) collapses into the INPUT
# `boundsOpt` (a computation with no determined bounds is modeled by
# `boundsOpt = none`), `density`/`stacked` map to `density`/`accumulate`. Every
# sibling case is accounted for below.
#
#   sibling case (nagini)          -> here                              disposition
#   ----------------------------------------------------------------------------
#   pos-reorder-correct            -> pos-single-record-reshape         RE-SHAPED
#   pos-locals-correct             -> pos-direct-spec                   RE-SHAPED
#   admiss-f2p-shaped              -> admiss-f2p-bounds-and-density     RE-AIMED
#   rival-rebind-drop              -> rival-rebind-drop                 PORTED
#   rival-range-always             -> rival-bounds-fabricate            PORTED
#   rival-wrong-density-value      -> rival-wrong-density-value         PORTED
#   rival-ignore-stacked           -> rival-ignore-accumulate           PORTED
#   rival-empty                    -> rival-empty                       PORTED
#   rival-stray-key                -> (none)                            VACUOUS (carrier)
#   (no sibling counterpart)       -> rival-bounds-transpose             ADDED (audit)
#   (no sibling counterpart)       -> rival-density-never                ADDED (audit)
#
# 8 ported/re-shaped/re-aimed, 1 vacuous, 2 added by audit.
#
# ADDED (rival-density-never). Not a port: a second audit found the C3 analogue of
#   the C2 gap below. C3 (`out.densityOpt = some density` on the density
#   sub-domain) also has two halves — the entry is RECORDED, and it records the
#   right value — and every density attack in the battery hit the VALUE half only
#   (rival-wrong-density-value negates the payload of a PRESENT entry;
#   rival-ignore-accumulate attacks C4, the absence clause; rival-empty drops the
#   density entry but also drops the bounds, so its witness refutes on the bounds
#   field and would fire even against a spec with no density clause at all). So an
#   impl that simply never records the density entry — bounds handling perfect —
#   was attacked by no witness, and a hypothetical spec pinning only the value of a
#   present entry would have passed the whole battery. The spec correctly rejects
#   it (residual `ensures_2: ... -> out.densityOpt = some density`), so this was a
#   BATTERY gap, not a spec hole.
#
# ADDED (rival-bounds-transpose). Not a port: an audit found that every C2 attack
#   in the battery discriminated on bounds PRESENCE only (`none` vs `some _`, a
#   constructor clash), so the payload-IDENTITY half of C2 — the entry is the pair
#   that was determined, not merely SOME pair — was defended by no witness. The
#   sibling had no such gap to port, because its bounds payload was a comparable
#   `int` and `R[KEY_RANGE]==range_value` was checked by SMT automatically; here
#   the payload is an opaque `Float` pair. Landed with a conditioned witness (see
#   WITNESS FORM below).
#
# RE-SHAPED (positives): the sibling's branch-reorder positive maps onto returning
#   the deep model directly (pos-direct-spec); the sibling's hoist-locals positive
#   maps onto computing the density entry into a local `Option Bool` and building
#   the result in one structure literal (pos-single-record-reshape). Both are
#   behaviourally identical, structurally different correct impls that verify.
# RE-AIMED (admissibility): the sibling shows the F2P-shaped input satisfies the
#   Requires (KEY_RANGE()!=KEY_DENSITY()) and pins the F2P observable via a
#   self-call. This method has NO `require` clause, so nothing could exclude any
#   input on the total domain — that probe is vacuous. Re-aimed at proving the
#   post-image is NON-DEGENERATE: on the F2P-shaped input the assembly records
#   BOTH the determined bounds AND the density choice at once (the conjunction the
#   issue demands), via an in-region assert discharged by the frozen proof.
# PORTED (rivals): five sibling rivals port cheaply because both carriers pin the
#   same facets; only the mechanics change (dict key/value conjuncts -> the
#   `HistOptions` field equalities C1..C4) and each gains a machine-checked witness
#   (new work — the sibling relied on Viper's automatic postcondition discharge):
#     * rival-rebind-drop: the base-commit bug — the density branch rebuilds the
#       mapping dropping the determined bounds (C2). This is the frame ARGUMENT the
#       vacuous permission-mutation class cannot express on a referentially
#       transparent backend — attacked as a value-drop, not a heap mutation.
#     * rival-bounds-fabricate: records a bounds entry unconditionally, including
#       the bounds-absent sub-domain (sibling range-always) — C2 on `none`.
#     * rival-wrong-density-value: right presence, negated payload (C3 value).
#     * rival-ignore-accumulate: drops the not-accumulated guard (sibling
#       ignore-stacked) — C4 on the accumulate sub-domain.
#     * rival-empty: forwards nothing (C2/C3), a cheap supporting near-miss.
# VACUOUS (rival-stray-key): the sibling splats a stray THIRD dict key, violating
#   C6 (the key-set upper bound: Forall k, k==KEY_RANGE or k==KEY_DENSITY). Here
#   the carrier is a FIXED two-field `structure HistOptions`; there is no
#   variable key set and no way to add a third entry, so the key-set upper bound
#   is a type-level invariant, not a spec clause a rival could violate — the
#   stray-key rival cannot be written at all. This is carrier narrowing (the
#   two-field structure makes the option-set a type invariant), not a
#   dropped-because-hard omission. The nagini C6 has no counterpart clause here
#   and needs no rival. Verified mechanically rather than argued: adding a third
#   field to `HistOptions` is the only way to express a stray entry, and
#   `HistOptions` lives in the `pure` region, which the spec view SHOWS — so that
#   variant is rejected by `variant_problems` as `spec view differs (same_spec
#   failed)` before any build. A stray entry is inexpressible inside the admissible
#   variant scope, not merely hard to prove.
#
# BINDER / CLAUSE COVERAGE. The input binders are `boundsOpt`, `density`,
#   `accumulate`; the clauses are C1 (whole result), C2 (bounds survival), C3
#   (density presence+value), C4 (density absence). C1..C4 are DEFENDED by both
#   positive controls and the admissibility case, and ATTACKED: C2's PRESENCE half
#   by rival-rebind-drop, rival-bounds-fabricate, and rival-empty, and C2's
#   PAYLOAD-IDENTITY half by rival-bounds-transpose (the one rival that keeps the
#   entry present on every branch and still violates C2); C3's VALUE half by
#   rival-wrong-density-value and its PRESENCE half by rival-density-never; C4 by
#   rival-ignore-accumulate. Every input binder is varied by some witness:
#   `boundsOpt` over {some(0,1), none, some(lo,hi) with lo ≠ hi} (absent,
#   present-literal, present-symbolic), `density` over {true, false}, `accumulate`
#   over {false, true}. Seven witnesses over six DISTINCT input points; the one
#   shared point (some(0,1), true, false) carries two rivals that refute on
#   DIFFERENT projections of the result (bounds field vs density field), so it is
#   two probes rather than one repeated twice.
#
# CLOSER NOTE (measured, for the next porter). The `_ALLGOALS_PROOF` swap the three
#   positives use is NOT a loosening: all seven rivals were rebuilt under it and
#   every one still FAILS (exit 1) on a real `ensures` residual, and each swap is
#   REQUIRED — the same two impls under the frozen closer fail on `ensures_2` /
#   `ensures_4` respectively. Separately, a correct reshape that rebuilds the
#   bounds pair through a `match` on `boundsOpt` needs the option binder split
#   (`cases boundsOpt <;> ...`) as well; it verifies with that closer, so the
#   residual is goal management and not a spec restriction.
#
# WITNESS FORM. `Float` has no DecidableEq in this workspace, so the sibling
#   tester route (`derive_tester_for`) cannot discharge the C1/C2 clauses. Each
#   witness instead extracts the executable (`extract_program_for`) and states
#   `buildHistOptionsMExec <b> <d> <a> ≠ DivM.res (buildHistOptions <b> <d> <a>)`
#   — the rival's result differs from the deep model at that input, which C1
#   forbids. The proof reduces the run, peels the DivM.res/HistOptions.mk
#   constructors by `injection`, and closes the surviving field inequality by
#   `simp_all`. Confirmed empirically: each witness ELABORATES against its rival
#   and FAILS against the frozen solution (the gold-side failure is `unsolved
#   goals ⊢ False` — a real semantic residual, not an unknown name, a type error,
#   or a stuck reduction), and each rival module does NOT verify under the frozen
#   proof.
#
#   Two forms, because C2's two halves differ in decidability:
#     * LITERAL inputs (six rivals) for the facets that are constructor clashes
#       on a decidable projection — `boundsOpt` as none-vs-some, `densityOpt` as
#       some-vs-some over Bool. These heads bind NOTHING, so the consistency probe
#       is not reached.
#     * CONDITIONED input (rival-bounds-transpose) for the payload-identity half of
#       C2. A Float pair is opaque to the kernel — `#eval ((0.0:Float) == 1.0)`
#       says `false` but `rfl` cannot reduce it, and `DecidableEq Float` fails to
#       synthesize (both measured) — so no literal decides the payload. The
#       refutation is stated over `(lo hi : Float) (hne : lo ≠ hi)` and closed from
#       `hne`. That head binds, so the gate runs its consistency probe; the probe
#       FAILS (no tactic derives `False` from `lo ≠ hi` on an opaque carrier),
#       which is what confirms the refuting input actually exists.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this gate ignores it. This
#   bundle consumes no `axiom` (the `axioms` region is empty — the assembly is
#   modeled directly by the pure `def buildHistOptions`), so there is nothing here
#   for this gate to probe.
AXIOM_TESTS = []
