"""properties.py — G-PBT falsification battery for astropy__astropy-13398 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct <name>`` obligation survives with a byte-identical
statement) and swaps in a candidate impl; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE — six contracted methods, each a single-integer component
selector (``comp ∈ {0,1,2}``) over a three-component position; the three-
component object is recovered by ranging ``comp``:

  itrsToObserved  (comp vx vy vz)        forward direct orientation apply
    ensures comp = k → out = fwd{X,Y,Z} vx vy vz   -- the LOAD-BEARING clause:
                                                      the orientation matrix
                                                      applied DIRECTLY to the
                                                      GIVEN position (no
                                                      intermediate viewpoint
                                                      shift)
  observedToItrs  (comp ox oy oz)        backward transpose apply
    ensures comp = k → out = bwd{X,Y,Z} ox oy oz   -- the inverse-rotation applied
                                                      DIRECTLY to the input
  observedRoundtrip (comp vx vy vz)      exact round-trip identity
    ensures comp = k → out = v{x,y,z}              -- recovers the ORIGINAL
                                                      component exactly
  equToRot  (comp vx vy vz lx ly lz)     site-honouring forward
    ensures comp = k → out = prot{X,Y,Z} vx vy vz  -- the BARE rotation, NO
                                                      viewpoint offset (the frame's
                                                      own site is a no-op)
  rotToEqu  (comp ox oy oz lx ly lz)     site-honouring backward
    ensures comp = k → out = protInv{X,Y,Z} ox oy oz + offset*(L,L)
                                                   -- the inverse rotation, site
                                                      offset a no-op
  equRotRoundtrip (comp vx vy vz lx ly lz)  topocentric round-trip identity
    ensures comp = k → out = v{x,y,z}              -- recovers the ORIGINAL exactly

  The two independent modeled changes: (a) the FORWARD/BACKWARD transforms apply
  the orthogonal orientation matrix DIRECTLY to the given position rather than
  routing through an intermediate frame (an extra rotation), and (b) the
  site-honouring transforms refer the position to the frame's OWN site (offset a
  no-op) rather than forcing one single constant site (the centre of the Earth).
  The offset-free forward and the direct-rotation clauses are the load-bearing
  discriminators; neither round-trip clause forces them alone.

THE CARRIER IS AN OPAQUE-AXIOM ORACLE. Every observable is a single application
of the opaque axioms ``fwd{X,Y,Z}`` / ``bwd{X,Y,Z}`` / ``prot{X,Y,Z}`` /
``protInv{X,Y,Z}`` / ``offset{X,Y,Z}`` (the unchanged orientation / precession /
re-referencing callees, each the weakest sufficient contract for an unchanged
callee, directive 7). The ONLY facts the proofs consume are the orthogonality
axioms (``orth_*``, ``prot_orth_*``: the transpose-action inverts the
forward-action) and the same-site no-op (``same_site_*``: ``offset*(L,L)=0``).
There is no executable content: ``fwdX vx vy vz`` never reduces to a literal, and
neither does ``offsetX lx ly lz 0 0 0``. That fact governs the WITNESS TECHNIQUE.

WITNESS MECHANICS. Velvet's tester machinery (``derive_tester_for`` →
``…Tester args = false``) is DEAD here: the methods are ``noncomputable`` (they
consult the opaque axioms) so extraction has no executable code, and the
postcondition's ``Decidable`` instance stalls on the opaque terms. Each witness
instead speaks DIRECTLY to the method's Hoare triple. Every ``method`` here opens
``TotalCorrectness DemonicChoice`` (this is one of the ``total`` bundles), so
``triple`` is the total-correctness triple ``prove_correct`` discharges. A
witness fixes ``comp`` to a LITERAL (so the impl's ``if comp = k`` ladder reduces
by ``decide`` / ``if_true`` / ``if_false``), reaching the concrete ``return
<expr>`` of the branch it targets; ``wp_pure`` then reduces the weakest
precondition of that ``return`` to the equality ``<rival_expr> = <spec_rhs>``,
which the carrier-conditioning hypothesis refutes. Against gold the branch
returns exactly ``<spec_rhs>``, so the reduced goal is ``t = t`` and the
hypothesis cannot close it — the witness FAILS on gold, which is the required
discrimination.

  * When the spec RHS is itself opaque (the forward/backward/site transforms),
    the witness CONDITIONS on the carrier: it names the divergence point by ONE
    weak, satisfiable hypothesis (``fwdY vx vy vz ≠ fwdZ vx vy vz``, ``offsetX lx
    ly lz 0 0 0 ≠ 0``, …). The rival author cannot know the opaque callee agrees
    at the two argument tuples, and generically it does not.
  * When the spec RHS is transparent (the round-trip clauses pin ``out = vy``),
    the orthogonality axiom collapses the rival's opaque composite to the WRONG
    input component, and the refutation is stated by conditioning on a
    disagreement between two input components (``vx ≠ vy``) or between an opaque
    image and the component it should have recovered (``fwdZ vx vy vz ≠ vz``).
    NOTE (audit): these clauses must NOT be attacked at literal inputs. Fixing
    ``vx=0, vy=1`` makes the gold-side goal ``¬ bwdY (fwdX 0 1 0) … = 1``, and
    since the carrier has no executable content ``decide`` gets STUCK rather
    than deciding it — gold's build then fails by stuck reduction, which
    discriminates nothing (the same error appears for a TRUE claim). Keeping
    every term symbolic and discharging both legs with the ``orth_*`` axioms is
    what makes both builds actually decide the claim.

The gate additionally derives ``False`` from each conditioned witness's binders
alone (``consistency_probe``) to confirm they are jointly satisfiable; every
conditioned witness here uses exactly ONE hypothesis about ONE opaque term, so it
cannot be inconsistent. All three required builds were run per reject case:
rival exit 0, gold exit ≠ 0, probe exit ≠ 0 (see the ACCOUNTING footer). No
banned token (sorry/admit/native_decide/axiom/opaque).

Every witness here is additionally required to fail on gold for a SEMANTIC
reason: after the ``simp only`` chain the attacked clause reduces to ``True``
against the frozen impl (visible as ``hcon : True`` in the gold-side build), so
the conditioning hypothesis has nothing to contradict. A gold-side failure that
is a stuck ``decide``, an unknown identifier, a ``rewrite`` pattern miss, or a
type/unification mismatch on the SPELLING of the hypothesis is NOT a refutation
and does not discriminate, even though the gate's exit-code check cannot tell the
difference. Four cases were repaired under audit for exactly this (see the
per-case NOTEs on roundtrip-ignore-comp, wrong-direction-rot-to-equ-uses-P, and
the two force-centre cases).

THE TEST THAT DECIDES IT (run per reject case; the reason the ``simp`` set of
every conditioned witness here NAMES the rewrite that reduces the frozen impl's
extra summand). Replace the closing ``exact hne hcon.1`` with a deliberate type
error on the hypothesis (``exact (hcon.1 : Nat)``) and build on both sides. Lean
then prints the hypothesis's REAL type. ``has type True`` on gold means the
``simp`` chain PROVED the attacked equation for the frozen impl; a CONCRETE
equation printed on gold means it did not, and the gold-side exit code is then
carrying the difference between two argument SPELLINGS rather than a verdict on
the claim — the case is hollow, and a forgery whose hypothesis names the frozen
impl's own spelling (asserting gold is WRONG at that point) ELABORATES against
gold. Every reject case here now prints ``True`` on gold and the concrete
divergence equation on the rival.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION (nagini's mandatory #1 class) — VACUOUS. Already
    N/A on nagini (every parameter is a plain ``int``, no ``Acc(...,1/2)``).
    Vacuous here for the stronger backend reason too: Velvet is referentially
    transparent, there is no heap / aliasing / fractional permission, and this
    bundle declares no ``mut`` binder — every parameter is an immutable ``Int``.
    No read-only field to overwrite, no substitute probe to build. Not
    fabricated.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
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
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. Each result is grounded in the
    method's own inputs: the opaque callee applied to the ARGUMENTS (``fwdX vx vy
    vz`` — a function OF the input, not a free answer-key, directive 8). There is
    no separate oracle a wrong impl could echo; the honest cheapest impl IS gold,
    carried as POSITIVE controls.
  * SOUNDNESS / positive controls — APPLY. A structurally-different but faithful
    impl must still verify against the byte-identical obligation, else the spec
    is SPEC-TOO-STRONG on the SHAPE of the impl.
  * ADMISSIBILITY — RE-AIMED. The nagini sibling re-derives the precondition
    consequence in-region. The analogue on a total carrier is the obligation being
    UNSATISFIABLE at an F2P-shaped input, which a positive that discharges the
    obligation at that concrete input — by evaluation, as a ``have``, before closing
    the frozen obligation verbatim — tests directly. That is
    ``admiss-obligation-satisfiable-at-comp2``. (It replaces an earlier degenerate
    revision whose ``module`` was the frozen file byte-for-byte, which varied nothing
    and could only fail if the whole bundle were already broken.)
  * INDIRECT-ROUTE / FORCE-CENTRE / WRONG-DIRECTION / PARTIAL-DOMAIN uniqueness
    rivals — APPLY. These attack the load-bearing clauses (direct rotation,
    offset-free site, transpose direction, per-component identity).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file's ``AXIOM_TESTS``
drive the real ``rotation_matrix`` / ``matrix_transpose`` / precession-matrix /
re-referencing callees in Docker; that is G-AX's job (axiom_check.py /
mapping.md) and the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13398"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen impl-region anchors. Each is the WHOLE impl body of one method
# (INCLUDING the -- impl-start / -- impl-end markers where a shared branch shape
# would otherwise not be unique), lying wholly inside that method's single elided
# impl region — so every _swap keeps same_spec by construction. Each is asserted
# unique in _BASE at load, so the manifest breaks loudly if Solution.lean drifts.
# ---------------------------------------------------------------------------

# itrsToObserved (forward, direct orientation apply)
_FWD = """    -- impl-start
    if comp = 0 then
      return fwdX vx vy vz
    else if comp = 1 then
      return fwdY vx vy vz
    else
      return fwdZ vx vy vz
    -- impl-end"""

# observedToItrs (backward, transpose apply) — full block: the bare branch shape
# also occurs inside observedRoundtrip, so the markers make the anchor unique.
_BWD = """    -- impl-start
    if comp = 0 then
      return bwdX ox oy oz
    else if comp = 1 then
      return bwdY ox oy oz
    else
      return bwdZ ox oy oz
    -- impl-end"""

# observedRoundtrip (exact round-trip identity)
_RT = """    let ox := fwdX vx vy vz
    let oy := fwdY vx vy vz
    let oz := fwdZ vx vy vz
    if comp = 0 then
      return bwdX ox oy oz
    else if comp = 1 then
      return bwdY ox oy oz
    else
      return bwdZ ox oy oz"""

# equToRot (site-honouring forward)
_C2R = """    if comp = 0 then
      return protX vx vy vz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protY vx vy vz + offsetY lx ly lz lx ly lz
    else
      return protZ vx vy vz + offsetZ lx ly lz lx ly lz
    -- impl-end"""

# rotToEqu (site-honouring backward) — full block: the bare branch shape also
# occurs inside equRotRoundtrip, so the markers make the anchor unique.
_R2E = """    -- impl-start
    if comp = 0 then
      return protInvX ox oy oz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protInvY ox oy oz + offsetY lx ly lz lx ly lz
    else
      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz
    -- impl-end"""

# equRotRoundtrip (topocentric round-trip identity)
_ERT = """    let ox := protX vx vy vz
    let oy := protY vx vy vz
    let oz := protZ vx vy vz
    if comp = 0 then
      return protInvX ox oy oz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protInvY ox oy oz + offsetY lx ly lz lx ly lz
    else
      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz"""

for _a in (_FWD, _BWD, _RT, _C2R, _R2E, _ERT):
    assert _BASE.count(_a) == 1, f"anchor drift / not unique: {_a[:40]!r}"

# The frozen itrsToObserved obligation's tactic body — elided from the spec view,
# so retuning it keeps same_spec and the `prove_correct itrsToObserved` header.
# The admissibility case prepends a `have` to it (see below).
_FWD_PROOF = "prove_correct itrsToObserved by\n  loom_solve"
assert _BASE.count(_FWD_PROOF) == 1, "proof anchor drift: _FWD_PROOF"

# ADMISSIBILITY, discharged BY EVALUATION at a concrete in-domain selector before
# the frozen obligation is closed verbatim. `hreach` proves, for the LAST selector
# (comp = 2 — the fall-through branch, the one a selector ladder is likeliest to
# leave unreachable), that the method's own triple at that concrete selector is
# SATISFIABLE: the precondition disjunction holds there by `decide`, the impl's
# guard ladder reduces, and the resulting postcondition conjunction closes. If the
# obligation were unsatisfiable at that F2P-shaped point — a `require` no in-domain
# selector meets, or a post-image no computation can hit — this `have` could not be
# discharged and the case would FAIL, which is PRECOND-TOO-STRONG. The frozen
# `loom_solve` still closes the real obligation afterwards, so nothing is weakened.
_FWD_PROOF_ADMISS = """prove_correct itrsToObserved by
  have hdom : (2:Int) = 0 ∨ (2:Int) = 1 ∨ (2:Int) = 2 := by decide
  have hreach : ∀ x y z : Int,
      triple ((2:Int) = 0 ∨ (2:Int) = 1 ∨ (2:Int) = 2)
        (itrsToObserved 2 x y z)
        (fun out => ((2:Int) = 0 → out = fwdX x y z)
                  ∧ ((2:Int) = 1 → out = fwdY x y z)
                  ∧ ((2:Int) = 2 → out = fwdZ x y z)) := by
    intro x y z
    simp only [itrsToObserved, triple, show (2:Int)=0 ↔ False by decide,
      show (2:Int)=1 ↔ False by decide, if_false]
    intro _
    rw [wp_pure]
    simp
  loom_solve"""


# ===========================================================================
# SPEC CASES
# ===========================================================================
SPEC_TESTS = [
    # -----------------------------------------------------------------------
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # (each reorders the comp-branch ladder; every branch's returned value is
    # unchanged, so the frozen proof still discharges). MUST verify, else the
    # obligation is SPEC-TOO-STRONG on the SHAPE of the impl. One per method so
    # every obligation is DEFENDED. (Ports the nagini branch-reorder positives
    # pos-control-backward-branch-reorder / pos-control-cirs-itrs-branch-reorder,
    # and generalizes them to the forward, round-trip and rotToEqu obligations.)
    # -----------------------------------------------------------------------
    {
        "id": "pos-forward-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _FWD,
                        "    -- impl-start\n"
                        "    if comp = 2 then\n"
                        "      return fwdZ vx vy vz\n"
                        "    else if comp = 1 then\n"
                        "      return fwdY vx vy vz\n"
                        "    else\n"
                        "      return fwdX vx vy vz\n"
                        "    -- impl-end"),
        "rationale": "itrsToObserved with the comp branches reordered (test comp=2, "
                     "comp=1, else comp=0). Same value on every input; each branch "
                     "is pinned by its `comp = k → out = fwd{X,Y,Z}` clause. A "
                     "correct re-shaping must verify, else SPEC-TOO-STRONG on the "
                     "forward transform's obligation.",
    },
    {
        "id": "pos-backward-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _BWD,
                        "    -- impl-start\n"
                        "    if comp = 2 then\n"
                        "      return bwdZ ox oy oz\n"
                        "    else if comp = 1 then\n"
                        "      return bwdY ox oy oz\n"
                        "    else\n"
                        "      return bwdX ox oy oz\n"
                        "    -- impl-end"),
        "rationale": "observedToItrs with the comp branches reordered. Same value "
                     "on every input; each branch pinned by its `comp = k → out = "
                     "bwd{X,Y,Z}` clause. Must verify, else SPEC-TOO-STRONG on the "
                     "backward transform. (Sibling: pos-control-backward-branch-"
                     "reorder.)",
    },
    {
        "id": "pos-roundtrip-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _RT,
                        "    let ox := fwdX vx vy vz\n"
                        "    let oy := fwdY vx vy vz\n"
                        "    let oz := fwdZ vx vy vz\n"
                        "    if comp = 2 then\n"
                        "      return bwdZ ox oy oz\n"
                        "    else if comp = 1 then\n"
                        "      return bwdY ox oy oz\n"
                        "    else\n"
                        "      return bwdX ox oy oz"),
        "rationale": "observedRoundtrip with the comp branches reordered; the "
                     "forward-then-transpose bindings (whose orthogonality "
                     "recovers the original component) are retained, only the "
                     "branch order changes. Same behaviour; each branch pinned by "
                     "its `comp = k → out = v{x,y,z}` clause. Must verify, else "
                     "SPEC-TOO-STRONG on the round-trip identity. (Sibling: "
                     "pos-control-roundtrip-reordered.)",
    },
    {
        "id": "pos-rottoequ-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _R2E,
                        "    -- impl-start\n"
                        "    if comp = 2 then\n"
                        "      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz\n"
                        "    else if comp = 1 then\n"
                        "      return protInvY ox oy oz + offsetY lx ly lz lx ly lz\n"
                        "    else\n"
                        "      return protInvX ox oy oz + offsetX lx ly lz lx ly lz\n"
                        "    -- impl-end"),
        "rationale": "rotToEqu with the comp branches reordered; the same-site "
                     "offset (a no-op at the shared site) is retained on each "
                     "branch. Same value on every input; each branch pinned by its "
                     "`comp = k → out = protInv{X,Y,Z} … + offset*(L,L)` clause. "
                     "Must verify, else SPEC-TOO-STRONG on the site-honouring "
                     "backward transform.",
    },
    {
        "id": "pos-cirs-itrs-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _C2R,
                        "    if comp = 2 then\n"
                        "      return protZ vx vy vz + offsetZ lx ly lz lx ly lz\n"
                        "    else if comp = 1 then\n"
                        "      return protY vx vy vz + offsetY lx ly lz lx ly lz\n"
                        "    else\n"
                        "      return protX vx vy vz + offsetX lx ly lz lx ly lz\n"
                        "    -- impl-end"),
        "rationale": "equToRot with the comp branches reordered; the same-site "
                     "offset (a no-op) is retained so each branch is the bare "
                     "rotation. Same value on every input; each branch pinned by "
                     "its `comp = k → out = prot{X,Y,Z}` clause. Must verify, else "
                     "SPEC-TOO-STRONG on the site-honouring forward transform. "
                     "(Sibling: pos-control-cirs-itrs-branch-reorder.)",
    },
    {
        "id": "pos-equrot-roundtrip-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _ERT,
                        "    let ox := protX vx vy vz\n"
                        "    let oy := protY vx vy vz\n"
                        "    let oz := protZ vx vy vz\n"
                        "    if comp = 2 then\n"
                        "      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz\n"
                        "    else if comp = 1 then\n"
                        "      return protInvY ox oy oz + offsetY lx ly lz lx ly lz\n"
                        "    else\n"
                        "      return protInvX ox oy oz + offsetX lx ly lz lx ly lz"),
        "rationale": "equRotRoundtrip with the comp branches reordered; the "
                     "rotate-then-inverse bindings (whose orthogonality recovers "
                     "the original, and whose same-site offsets are no-ops) are "
                     "retained. Same behaviour; each branch pinned by its `comp = "
                     "k → out = v{x,y,z}` clause. Must verify, else SPEC-TOO-STRONG "
                     "on the topocentric round-trip identity.",
    },

    # -----------------------------------------------------------------------
    # ADMISSIBILITY — RE-AIMED from the nagini in-region precondition re-derivation
    # AND REPAIRED UNDER AUDIT. The earlier revision shipped `module = _BASE` (the
    # frozen file byte-for-byte) and argued that "the frozen impl verifying IS the
    # admissibility witness". That case is HONEST but DEGENERATE: it is a re-run of
    # G-VERIFY, it varies nothing, and it cannot fail unless the whole bundle is
    # already broken — so the PRECOND-TOO-STRONG direction was untested. Replaced by
    # a case that discharges the obligation AT A CONCRETE F2P-SHAPED SELECTOR, by
    # evaluation, as a `have`, BEFORE closing the frozen obligation verbatim.
    # -----------------------------------------------------------------------
    {
        "id": "admiss-obligation-satisfiable-at-comp2",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _FWD_PROOF, _FWD_PROOF_ADMISS),
        "rationale": "PASS SOURCE = itrsToObserved's own Hoare triple is SATISFIABLE "
                     "at the concrete in-domain selector comp = 2 — the fall-through "
                     "branch of the guard ladder, the point likeliest to be left "
                     "unreachable. The in-region `have hdom` derives the precondition "
                     "disjunction at that literal by `decide` (so the `require` really "
                     "does admit an F2P-shaped selector rather than being "
                     "unsatisfiable there), and `have hreach` then EVALUATES the "
                     "method at comp = 2 over universally quantified position "
                     "components and closes the whole postcondition conjunction — the "
                     "two vacuous legs by `false_implies`, the live `comp = 2 → out = "
                     "fwdZ x y z` leg by the branch's own reduction. If the "
                     "precondition admitted no in-domain selector, or the post-image "
                     "at that selector were unsatisfiable by any computation, `hreach` "
                     "could not be discharged and this case would FAIL => "
                     "PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE. The frozen `loom_solve` "
                     "still closes the real obligation afterwards, and the frozen "
                     "`require`/`ensures` are untouched (only the elided tactic body "
                     "changes), so nothing is weakened. The `have` is LIVE, not "
                     "decoration: the same case with the comp = 2 leg claiming `out = "
                     "fwdY x y z` instead FAILS to elaborate (measured out-of-band, "
                     "exit 1), so a false claim about this point does not close.",
    },

    # -----------------------------------------------------------------------
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness and the
    # refinement argument that its faithful real patch would NOT resolve the F2P.
    # -----------------------------------------------------------------------
    {
        # THE forward discriminator (nagini indirect-route-prepatch-forward = the
        # pre-patch behaviour). Reaches the observer-centred orientation INDIRECTLY:
        # apply the transpose-action first (an extra intermediate-frame rotation),
        # THEN the forward action — fwd(bwd v) rather than the direct fwd v.
        "id": "indirect-route-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD,
                        "    -- impl-start\n"
                        "    let ix := bwdX vx vy vz\n"
                        "    let iy := bwdY vx vy vz\n"
                        "    let iz := bwdZ vx vy vz\n"
                        "    if comp = 0 then\n"
                        "      return fwdX ix iy iz\n"
                        "    else if comp = 1 then\n"
                        "      return fwdY ix iy iz\n"
                        "    else\n"
                        "      return fwdZ ix iy iz\n"
                        "    -- impl-end"),
        "refinement": "this IS the pre-patch behaviour: the forward transform "
                      "reaches the observer-centred orientation INDIRECTLY (route "
                      "through an intermediate frame, an extra rotation) so it "
                      "computes fwd(bwd v) rather than applying the orientation "
                      "matrix DIRECTLY to the given position. That is the "
                      "geocentric-vs-topocentric aberration shift the issue "
                      "describes; the F2P tests assert the EXACT round-trip identity "
                      "back to the input position, which this indirect route breaks "
                      "— so the faithful real patch does NOT resolve.",
        "rationale": "REJECT from itrsToObserved's `comp = 0 → out = fwdX vx vy vz`: "
                     "the rival returns `fwdX (bwdX vx vy vz) (bwdY vx vy vz) (bwdZ "
                     "vx vy vz)`. fwd/bwd are opaque; the only relating fact is "
                     "orthogonality `bwd(fwd v)=v`, which says nothing about "
                     "`fwdX (bwd… )`. Refuted by conditioning on the satisfiable "
                     "single hypothesis `fwdX (bwdX vx vy vz) (bwdY vx vy vz) (bwdZ "
                     "vx vy vz) ≠ fwdX vx vy vz` (comp fixed at 0). Against gold the "
                     "branch returns `fwdX vx vy vz`, so the hypothesis cannot close "
                     "it and the witness fails on gold. If it VERIFIED => "
                     "SPEC-TOO-WEAK (the direct-rotation clause unmodeled).",
        "witness": (
            "example (vx vy vz : Int)\n"
            "    (hne : fwdX (bwdX vx vy vz) (bwdY vx vy vz) (bwdZ vx vy vz)"
            " ≠ fwdX vx vy vz) :\n"
            "    ¬ (triple (0 = 0 ∨ 0 = 1 ∨ 0 = 2)\n"
            "        (itrsToObserved 0 vx vy vz)\n"
            "        (fun out => ((0:Int) = 0 → out = fwdX vx vy vz)\n"
            "                  ∧ ((0:Int) = 1 → out = fwdY vx vy vz)\n"
            "                  ∧ ((0:Int) = 2 → out = fwdZ vx vy vz))) := by\n"
            "  simp only [itrsToObserved, triple, if_true]\n"
            "  intro h\n"
            "  have hcon := h (by tauto)\n"
            "  rw [wp_pure] at hcon\n"
            "  simp only [true_implies] at hcon\n"
            "  exact hne hcon.1\n"
        ),
    },
    {
        # PARTIAL-DOMAIN forward: correct on comp 0 and 1, but on comp=2 returns the
        # comp=1 component (fwdY) instead of fwdZ. (nagini partial-domain-forward-comp2)
        "id": "partial-domain-forward-comp2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD,
                        "    -- impl-start\n"
                        "    if comp = 0 then\n"
                        "      return fwdX vx vy vz\n"
                        "    else if comp = 1 then\n"
                        "      return fwdY vx vy vz\n"
                        "    else\n"
                        "      return fwdY vx vy vz\n"
                        "    -- impl-end"),
        "refinement": "a faithful patch correct on the first two output components "
                      "but emitting the y-component for the z slot produces a wrong "
                      "third Cartesian coordinate; the F2P tests compare all three "
                      "of the round-tripped coordinates back to the original, so the "
                      "z-component mismatch makes the test FAIL — the refined patch "
                      "does NOT resolve.",
        "rationale": "REJECT from itrsToObserved's `comp = 2 → out = fwdZ vx vy vz`: "
                     "the rival returns `fwdY vx vy vz` on the comp=2 branch. fwdY "
                     "and fwdZ are independent opaque callees. Refuted by "
                     "conditioning on the satisfiable single hypothesis `fwdY vx vy "
                     "vz ≠ fwdZ vx vy vz` at comp=2 — a DISTINCT sub-domain (comp=2) "
                     "from the indirect-route rival (comp=0), so the two witnesses "
                     "probe different points and the comp binder is varied. Against "
                     "gold the branch returns `fwdZ vx vy vz`, so the witness fails "
                     "on gold. If it VERIFIED => SPEC-TOO-WEAK (the comp=2 clause "
                     "unpinned).",
        "witness": (
            "example (vx vy vz : Int)\n"
            "    (hne : fwdY vx vy vz ≠ fwdZ vx vy vz) :\n"
            "    ¬ (triple (2 = 0 ∨ 2 = 1 ∨ 2 = 2)\n"
            "        (itrsToObserved 2 vx vy vz)\n"
            "        (fun out => ((2:Int) = 0 → out = fwdX vx vy vz)\n"
            "                  ∧ ((2:Int) = 1 → out = fwdY vx vy vz)\n"
            "                  ∧ ((2:Int) = 2 → out = fwdZ vx vy vz))) := by\n"
            "  simp only [itrsToObserved, triple, show (2:Int)=0 ↔ False by decide,\n"
            "    show (2:Int)=1 ↔ False by decide, if_false]\n"
            "  intro h\n"
            "  have hcon := h (by tauto)\n"
            "  rw [wp_pure] at hcon\n"
            "  simp only [false_implies, true_and, true_implies] at hcon\n"
            "  exact hne hcon\n"
        ),
    },
    {
        # WRONG-DIRECTION backward: applies the forward action (M) instead of the
        # transpose (M^T). (nagini wrong-direction-backward-uses-M)
        "id": "wrong-direction-backward-uses-M",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD,
                        "    -- impl-start\n"
                        "    if comp = 0 then\n"
                        "      return fwdX ox oy oz\n"
                        "    else if comp = 1 then\n"
                        "      return fwdY ox oy oz\n"
                        "    else\n"
                        "      return fwdZ ox oy oz\n"
                        "    -- impl-end"),
        "refinement": "a faithful patch whose backward transform applies the "
                      "orientation matrix M itself (not its transpose M^T) does NOT "
                      "invert the forward rotation: the composed round trip is M(M v) "
                      "≠ v in general, so the exact round-trip-identity F2P assertion "
                      "back to the input coordinates FAILS — the refined patch does "
                      "NOT resolve.",
        "rationale": "REJECT from observedToItrs's `comp = 0 → out = bwdX ox oy oz`: "
                     "the rival returns `fwdX ox oy oz`. fwd and bwd are independent "
                     "opaque callees — orthogonality relates bwd(fwd v) to v, never "
                     "fwd(o) to bwd(o). Refuted by conditioning on the satisfiable "
                     "single hypothesis `fwdX ox oy oz ≠ bwdX ox oy oz` (comp=0). "
                     "Against gold the branch returns `bwdX ox oy oz`, so the "
                     "witness fails on gold. If it VERIFIED => SPEC-TOO-WEAK (the "
                     "transpose direction unpinned).",
        "witness": (
            "example (ox oy oz : Int)\n"
            "    (hne : fwdX ox oy oz ≠ bwdX ox oy oz) :\n"
            "    ¬ (triple (0 = 0 ∨ 0 = 1 ∨ 0 = 2)\n"
            "        (observedToItrs 0 ox oy oz)\n"
            "        (fun out => ((0:Int) = 0 → out = bwdX ox oy oz)\n"
            "                  ∧ ((0:Int) = 1 → out = bwdY ox oy oz)\n"
            "                  ∧ ((0:Int) = 2 → out = bwdZ ox oy oz))) := by\n"
            "  simp only [observedToItrs, triple, if_true]\n"
            "  intro h\n"
            "  have hcon := h (by tauto)\n"
            "  rw [wp_pure] at hcon\n"
            "  simp only [true_implies] at hcon\n"
            "  exact hne hcon.1\n"
        ),
    },
    {
        # PARTIAL-DOMAIN round-trip: ignore comp, always recover the FIRST
        # component. (nagini partial-domain-roundtrip-ignore-comp)
        "id": "roundtrip-ignore-comp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RT,
                        "    let ox := fwdX vx vy vz\n"
                        "    let oy := fwdY vx vy vz\n"
                        "    let oz := fwdZ vx vy vz\n"
                        "    if comp = 0 then\n"
                        "      return bwdX ox oy oz\n"
                        "    else if comp = 1 then\n"
                        "      return bwdX ox oy oz\n"
                        "    else\n"
                        "      return bwdX ox oy oz"),
        "refinement": "a faithful patch that always recovers the first Cartesian "
                      "component for every requested component collapses the "
                      "round-tripped position to (vx,vx,vx); the F2P tests assert "
                      "each round-tripped coordinate back to the ORIGINAL, so the y "
                      "and z comparisons FAIL — the refined patch does NOT resolve.",
        "rationale": "REJECT from observedRoundtrip's `comp = 1 → out = vy`: the "
                     "rival returns `bwdX (fwdX vx vy vz) …` on every branch, which "
                     "orthogonality (orth_x) collapses to vx, where the clause "
                     "demands vy. Refuted at comp=1 conditioning on the satisfiable "
                     "single hypothesis `vx ≠ vy`. Against gold the branch returns "
                     "`bwdY (fwdX …) …`, which orth_y collapses to vy, so the clause "
                     "reduces to `True` and the hypothesis cannot close the goal — "
                     "the witness fails on gold SEMANTICALLY (`hcon : True`). If it "
                     "VERIFIED => SPEC-TOO-WEAK (the per-component identity "
                     "unpinned). NOTE: this witness is stated over SYMBOLIC vx/vy "
                     "rather than the literals (0,1,0) an earlier revision used. At "
                     "literal inputs the gold-side goal is `¬ bwdY (fwdX 0 1 0) … = "
                     "1`, which `decide` CANNOT reduce (the opaque axioms have no "
                     "executable content), so gold failed by STUCK REDUCTION rather "
                     "than by refutation — an exit code that attests to nothing. "
                     "Conditioning on `vx ≠ vy` and discharging both legs with "
                     "orth_x/orth_y keeps every term symbolic, so both builds decide "
                     "the claim.",
        "witness": (
            "example (vx vy vz : Int)\n"
            "    (hne : vx ≠ vy) :\n"
            "    ¬ (triple (1 = 0 ∨ 1 = 1 ∨ 1 = 2)\n"
            "        (observedRoundtrip 1 vx vy vz)\n"
            "        (fun out => ((1:Int) = 0 → out = vx)\n"
            "                  ∧ ((1:Int) = 1 → out = vy)\n"
            "                  ∧ ((1:Int) = 2 → out = vz))) := by\n"
            "  simp only [observedRoundtrip, triple, show (1:Int)=0 ↔ False by"
            " decide,\n"
            "    show (1:Int)=2 ↔ False by decide, if_false, if_true]\n"
            "  intro h\n"
            "  have hcon := h (by tauto)\n"
            "  rw [wp_pure] at hcon\n"
            "  simp only [false_implies, true_and, true_implies, orth_x, orth_y,\n"
            "    and_true] at hcon\n"
            "  exact hne hcon\n"
        ),
    },
    {
        # ROUND-TRIP WITH THE INVERTING LEG DROPPED. Returns the observer-centred
        # components themselves (the forward leg only) instead of transposing back.
        # Added by audit: observedRoundtrip's only other rival (roundtrip-ignore-comp)
        # probes comp=1, so the identity clause was attacked at ONE point and the
        # battery said nothing about the spec's dependence on comp / vz. This one
        # sits at comp=2.
        "id": "roundtrip-forward-leg-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RT,
                        "    let ox := fwdX vx vy vz\n"
                        "    let oy := fwdY vx vy vz\n"
                        "    let oz := fwdZ vx vy vz\n"
                        "    if comp = 0 then\n"
                        "      return ox\n"
                        "    else if comp = 1 then\n"
                        "      return oy\n"
                        "    else\n"
                        "      return oz"),
        "refinement": "a faithful patch that hands back the observer-centred "
                      "components without applying the inverse rotation to return to "
                      "the Earth-rotating orientation is not a round trip at all: the "
                      "result is the rotated position rather than the original. The "
                      "F2P tests assert each round-tripped coordinate back to the "
                      "ORIGINAL, so every component comparison FAILS whenever the "
                      "rotation is not the identity — the refined patch does NOT "
                      "resolve.",
        "rationale": "REJECT from observedRoundtrip's `comp = 2 → out = vz`: the rival "
                     "returns `fwdZ vx vy vz` (the forward leg's third component) "
                     "instead of recovering vz. fwd is opaque and orthogonality only "
                     "relates bwd(fwd v) to v, so nothing forces `fwdZ v = vz`. "
                     "Refuted at comp=2 conditioning on the satisfiable single "
                     "hypothesis `fwdZ vx vy vz ≠ vz`. Against gold the branch returns "
                     "`bwdZ (fwdX …) (fwdY …) (fwdZ …)`, which orth_z collapses to vz, "
                     "so the clause reduces to `True` and the hypothesis cannot close "
                     "the goal — the witness fails on gold SEMANTICALLY (`hcon : "
                     "True`). Probes comp=2, a DISTINCT sub-domain from "
                     "roundtrip-ignore-comp's comp=1, so the comp binder is genuinely "
                     "varied on this obligation. If it VERIFIED => SPEC-TOO-WEAK (the "
                     "round-trip identity satisfiable without the inverting leg).",
        "witness": (
            "example (vx vy vz : Int)\n"
            "    (hne : fwdZ vx vy vz ≠ vz) :\n"
            "    ¬ (triple (2 = 0 ∨ 2 = 1 ∨ 2 = 2)\n"
            "        (observedRoundtrip 2 vx vy vz)\n"
            "        (fun out => ((2:Int) = 0 → out = vx)\n"
            "                  ∧ ((2:Int) = 1 → out = vy)\n"
            "                  ∧ ((2:Int) = 2 → out = vz))) := by\n"
            "  simp only [observedRoundtrip, triple, show (2:Int)=0 ↔ False by"
            " decide,\n"
            "    show (2:Int)=1 ↔ False by decide, if_false]\n"
            "  intro h\n"
            "  have hcon := h (by tauto)\n"
            "  rw [wp_pure] at hcon\n"
            "  simp only [false_implies, true_and, true_implies, orth_z] at hcon\n"
            "  exact hne hcon\n"
        ),
    },
    {
        # THE site discriminator (nagini force-centre-prepatch-cirs-itrs = pre-patch
        # behaviour). Refers the position to one single constant site (the centre of
        # the Earth, (0,0,0)) regardless of the frame's own site L.
        "id": "force-centre-cirs-itrs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _C2R,
                        "    if comp = 0 then\n"
                        "      return protX vx vy vz + offsetX lx ly lz 0 0 0\n"
                        "    else if comp = 1 then\n"
                        "      return protY vx vy vz + offsetY lx ly lz 0 0 0\n"
                        "    else\n"
                        "      return protZ vx vy vz + offsetZ lx ly lz 0 0 0\n"
                        "    -- impl-end"),
        "refinement": "this IS the pre-patch behaviour: the Earth-equatorial ↔ "
                      "Earth-rotating transform refers the position to one single "
                      "constant site (the centre of the Earth) rather than the "
                      "frame's own site, so a topocentric position carries the "
                      "geocentric-vs-topocentric offset. The F2P tests compare the "
                      "through-intermediate route against the direct route and FAIL "
                      "when this offset is present — so the faithful real patch does "
                      "NOT resolve.",
        "rationale": "REJECT from equToRot's `comp = 0 → out = protX vx vy vz`: the "
                     "rival returns `protX vx vy vz + offsetX lx ly lz 0 0 0`. offset "
                     "is opaque; the only relating fact is same_site `offset*(L,L)=0`, "
                     "which says nothing about `offset*(L,0)`. Refuted by "
                     "conditioning on the satisfiable single hypothesis `protX vx vy "
                     "vz + offsetX lx ly lz 0 0 0 ≠ protX vx vy vz` (equivalently "
                     "offset*(L,0) ≠ 0, when L is off-centre). Against gold the branch "
                     "returns `protX vx vy vz + offset*(L,L)`, which same_site_x / "
                     "add_zero collapse to the clause's own RHS, so the clause reduces "
                     "to `True` and the hypothesis cannot close the goal — the witness "
                     "fails on gold SEMANTICALLY (`hcon : True`). If it VERIFIED => "
                     "SPEC-TOO-WEAK (the offset-free site clause unmodeled). NOTE: an "
                     "earlier revision's `simp only [true_implies]` did NOT name "
                     "same_site_x/add_zero, so gold's `hcon` stayed the CONCRETE "
                     "equation `protX … + offset*(L,L) = protX …` and gold failed only "
                     "because that spelling does not unify with the hypothesis's "
                     "`offset*(L,0)` spelling. Measured: a forgery differing ONLY in "
                     "writing `offset*(L,L)` in the hypothesis — i.e. asserting the "
                     "FROZEN impl is wrong at that point — ELABORATED against gold "
                     "(exit 0) and FAILED against the rival (exit 1), the exact "
                     "inversion of the required discrimination. Naming the rewrite "
                     "makes gold's `hcon` reduce to `True`, so the exit code now "
                     "tracks the CLAIM rather than the spelling.",
        "witness": (
            "example (vx vy vz lx ly lz : Int)\n"
            "    (hne : protX vx vy vz + offsetX lx ly lz 0 0 0 ≠ protX vx vy vz) :\n"
            "    ¬ (triple (0 = 0 ∨ 0 = 1 ∨ 0 = 2)\n"
            "        (equToRot 0 vx vy vz lx ly lz)\n"
            "        (fun out => ((0:Int) = 0 → out = protX vx vy vz)\n"
            "                  ∧ ((0:Int) = 1 → out = protY vx vy vz)\n"
            "                  ∧ ((0:Int) = 2 → out = protZ vx vy vz))) := by\n"
            "  simp only [equToRot, triple, if_true]\n"
            "  intro h\n"
            "  have hcon := h (by tauto)\n"
            "  rw [wp_pure] at hcon\n"
            "  simp only [true_implies, same_site_x, add_zero] at hcon\n"
            "  exact hne hcon.1\n"
        ),
    },
    {
        # WRONG-DIRECTION site-honouring backward: applies P instead of its
        # transpose P^T. (nagini wrong-direction-itrs-cirs-uses-P)
        "id": "wrong-direction-rot-to-equ-uses-P",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _R2E,
                        "    -- impl-start\n"
                        "    if comp = 0 then\n"
                        "      return protX ox oy oz + offsetX lx ly lz lx ly lz\n"
                        "    else if comp = 1 then\n"
                        "      return protY ox oy oz + offsetY lx ly lz lx ly lz\n"
                        "    else\n"
                        "      return protZ ox oy oz + offsetZ lx ly lz lx ly lz\n"
                        "    -- impl-end"),
        "refinement": "a faithful patch whose backward Earth-rotating ↔ "
                      "Earth-equatorial transform applies the precession matrix P "
                      "itself (not its transpose P^T) does NOT invert the forward "
                      "rotation: the composed round trip is P(P v) ≠ v in general, so "
                      "the topocentric round-trip F2P assertion FAILS — the refined "
                      "patch does NOT resolve.",
        "rationale": "REJECT from rotToEqu's `comp = 0 → out = protInvX ox oy oz` "
                     "(the frozen clause, quoted verbatim): the rival returns `protX "
                     "ox oy oz + offsetX lx ly lz lx ly lz`. prot and protInv are "
                     "independent opaque callees — prot_orth relates protInv(prot v) "
                     "to v, never prot(o) to protInv(o) — and same_site_x rewrites "
                     "the rival's offset to 0, so the divergence is exactly `protX ox "
                     "oy oz ≠ protInvX ox oy oz`; refuted by conditioning on that "
                     "satisfiable single hypothesis (comp=0). Against gold the branch "
                     "returns `protInvX ox oy oz + offset*(L,L)`, which same_site_x "
                     "collapses to the clause's own RHS, so the clause reduces to "
                     "`True` and the hypothesis cannot close the goal — the witness "
                     "fails on gold SEMANTICALLY (`hcon : True`). If it VERIFIED => "
                     "SPEC-TOO-WEAK (the transpose direction of the site backward "
                     "transform unpinned). NOTE: an earlier revision stated this "
                     "witness's postcondition as `out = protInvX ox oy oz + offsetX "
                     "lx ly lz lx ly lz` — a clause the frozen spec does NOT contain "
                     "(the frozen ensures is the bare `out = protInvX ox oy oz`). "
                     "That restated obligation is strictly weaker on this carrier, so "
                     "the refutation was attributed to a postcondition of the "
                     "witness's own invention; it is now the frozen clause verbatim.",
        "witness": (
            "example (ox oy oz lx ly lz : Int)\n"
            "    (hne : protX ox oy oz ≠ protInvX ox oy oz) :\n"
            "    ¬ (triple (0 = 0 ∨ 0 = 1 ∨ 0 = 2)\n"
            "        (rotToEqu 0 ox oy oz lx ly lz)\n"
            "        (fun out => ((0:Int) = 0 → out = protInvX ox oy oz)\n"
            "                  ∧ ((0:Int) = 1 → out = protInvY ox oy oz)\n"
            "                  ∧ ((0:Int) = 2 → out = protInvZ ox oy oz))) := by\n"
            "  simp only [rotToEqu, triple, if_true]\n"
            "  intro h\n"
            "  have hcon := h (by tauto)\n"
            "  rw [wp_pure] at hcon\n"
            "  simp only [true_implies, same_site_x, add_zero] at hcon\n"
            "  exact hne hcon.1\n"
        ),
    },
    {
        # FORCE-CENTRE on the topocentric round-trip (attacks equRotRoundtrip
        # directly). No nagini counterpart edited equ_rot_roundtrip's impl (the
        # round-trip's discriminator lives in the forward/backward pair on nagini),
        # but this obligation must be independently ATTACKED here, and the site
        # force is exactly what makes the topocentric round trip non-identity.
        "id": "force-centre-equrot-roundtrip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ERT,
                        "    let ox := protX vx vy vz\n"
                        "    let oy := protY vx vy vz\n"
                        "    let oz := protZ vx vy vz\n"
                        "    if comp = 0 then\n"
                        "      return protInvX ox oy oz + offsetX lx ly lz 0 0 0\n"
                        "    else if comp = 1 then\n"
                        "      return protInvY ox oy oz + offsetY lx ly lz 0 0 0\n"
                        "    else\n"
                        "      return protInvZ ox oy oz + offsetZ lx ly lz 0 0 0"),
        "refinement": "the topocentric round trip that refers each leg to one single "
                      "constant site (the centre of the Earth) rather than the "
                      "frame's own site carries the geocentric-vs-topocentric offset "
                      "whenever the site is off-centre, so the composed round trip is "
                      "NOT the identity; the exact-round-trip F2P assertion back to "
                      "the original topocentric position FAILS — the refined patch "
                      "does NOT resolve.",
        "rationale": "REJECT from equRotRoundtrip's `comp = 0 → out = vx`: the rival "
                     "returns `protInvX (protX vx vy vz) … + offsetX lx ly lz 0 0 0`, "
                     "which prot_orth_x collapses to `vx + offsetX lx ly lz 0 0 0`, "
                     "where the clause demands the bare `vx`. Refuted by conditioning "
                     "on the satisfiable single hypothesis `vx + offsetX lx ly lz 0 0 0 "
                     "≠ vx` (comp=0). Against gold the branch returns `vx + "
                     "offset*(L,L)`, which same_site_x / add_zero collapse to `vx`, so "
                     "the clause reduces to `True` and the hypothesis cannot close the "
                     "goal — the witness fails on gold SEMANTICALLY (`hcon : True`). "
                     "This attacks the same forced-centre bug on the round-trip "
                     "obligation (which the offset cancellation on the honouring path "
                     "makes an identity). If it VERIFIED => SPEC-TOO-WEAK (the "
                     "topocentric identity does not force the site). NOTE: an earlier "
                     "revision conditioned on `offsetX lx ly lz 0 0 0 ≠ 0` and closed "
                     "by `omega` without naming same_site_x, so gold's residual goal "
                     "was the CONCRETE `vx + offset*(L,L) = vx` and `omega` failed "
                     "there only because it treats the frozen impl's `offset*(L,L)` as "
                     "a fresh unconstrained atom. Measured: a forgery differing ONLY in "
                     "writing `offset*(L,L)` in the hypothesis — i.e. asserting the "
                     "FROZEN impl is wrong at that point — ELABORATED against gold "
                     "(exit 0) and FAILED against the rival (exit 1). Conditioning on "
                     "the whole branch value and naming same_site_x makes gold's `hcon` "
                     "reduce to `True`, so the exit code now tracks the CLAIM.",
        "witness": (
            "example (vx vy vz lx ly lz : Int)\n"
            "    (hne : vx + offsetX lx ly lz 0 0 0 ≠ vx) :\n"
            "    ¬ (triple (0 = 0 ∨ 0 = 1 ∨ 0 = 2)\n"
            "        (equRotRoundtrip 0 vx vy vz lx ly lz)\n"
            "        (fun out => ((0:Int) = 0 → out = vx)\n"
            "                  ∧ ((0:Int) = 1 → out = vy)\n"
            "                  ∧ ((0:Int) = 2 → out = vz))) := by\n"
            "  simp only [equRotRoundtrip, triple, if_true]\n"
            "  intro h\n"
            "  have hcon := h (by tauto)\n"
            "  rw [wp_pure] at hcon\n"
            "  simp only [true_implies, prot_orth_x, same_site_x, add_zero] at hcon\n"
            "  exact hne hcon.1\n"
        ),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The nagini sibling ships 10 SPEC cases (3
# soundness positives, 1 admissibility, 6 uniqueness rivals) plus 2 AXIOM_TESTS,
# contracting SIX functions over a plain-int carrier with @Pure @ContractOnly
# uninterpreted oracles fwd_*/bwd_*/prot_*/prot_inv_*/offset_* and the
# orthogonality / prot_orthogonality / same_site_noop @ContractOnly axioms.
#
# CARRIER on velvet. This bundle contracts the SAME six functions as six
# `method`s over Int component selectors, with the oracles collapsed into the
# opaque `axiom`s fwd{X,Y,Z}/bwd{X,Y,Z}/prot{X,Y,Z}/protInv{X,Y,Z}/offset{X,Y,Z}
# and the three orthogonality / no-op facts (orth_*, prot_orth_*, same_site_*) —
# the weakest sufficient contracts (directive 7). The model is DEEP over the
# selector (a real `if comp = k` ladder), so every clause and binder the nagini
# rivals attack survives.
#
#   nagini case                          kind          -> here                          disposition
#   ------------------------------------------------------------------------------------------------
#   pos-control-roundtrip-reordered      soundness     -> pos-roundtrip-branch-reorder  PORTED
#   pos-control-backward-branch-reorder  soundness     -> pos-backward-branch-reorder   PORTED
#   pos-control-cirs-itrs-branch-reorder soundness     -> pos-cirs-itrs-branch-reorder  PORTED
#   (added forward / rotToEqu / equrot positives)      -> pos-forward-branch-reorder,   ADDED
#                                                         pos-rottoequ-branch-reorder,
#                                                         pos-equrot-roundtrip-branch-reorder
#   admissibility-forward-indomain       admissibility -> admiss-obligation-satisfiable-at-comp2  RE-AIMED
#   indirect-route-prepatch-forward      uniqueness    -> indirect-route-forward        PORTED
#   partial-domain-forward-comp2         uniqueness    -> partial-domain-forward-comp2  PORTED
#   wrong-direction-backward-uses-M      uniqueness    -> wrong-direction-backward-uses-M PORTED
#   partial-domain-roundtrip-ignore-comp uniqueness    -> roundtrip-ignore-comp         PORTED
#   force-centre-prepatch-cirs-itrs      uniqueness    -> force-centre-cirs-itrs        PORTED
#   wrong-direction-itrs-cirs-uses-P     uniqueness    -> wrong-direction-rot-to-equ-uses-P PORTED
#   (added equRotRoundtrip site attack)                -> force-centre-equrot-roundtrip ADDED
#   (added 2nd observedRoundtrip point)                -> roundtrip-forward-leg-only    ADDED (audit)
#   AXIOM_TESTS (2)                       axiom         -> (none)                        G-AX
#
# 6 uniqueness ported, 6 soundness positives (3 ported + 3 added), 1 admissibility
# re-aimed, 2 uniqueness added; frame class VACUOUS; divergence VACUOUS (total);
# axiom lane empty (G-AX's job). TOTAL 15 SPEC cases (6 soundness, 1 admissibility,
# 8 uniqueness).
#
# AUDIT REPAIRS, ROUND 2 (independent adversarial re-derivation by a SECOND auditor
#   who did not write the port; every module, witness, gold-side witness and probe
#   rebuilt from scratch, 39 builds, plus 32 forgery builds and 17 new-rival builds).
#   The 15 recorded outcomes all reproduced exactly. THREE defects were found and
#   fixed; they are defects the exit-code check structurally cannot see.
#
#   (1) + (2) force-centre-cirs-itrs and force-centre-equrot-roundtrip were HOLLOW.
#     Their gold-side `simp only` chains did NOT name the rewrite (same_site_x /
#     add_zero) that collapses the frozen impl's same-site summand, so gold's `hcon`
#     stayed a CONCRETE equation carrying `offset*(L,L)` while the hypothesis spoke
#     of `offset*(L,0)`. Gold's exit 1 was therefore a mismatch between two argument
#     SPELLINGS of one opaque callee, not a verdict on the claim. Both meta.json
#     gold_signatures said so in plain sight and were misread as semantic: the
#     application-type-mismatch line printed `protX vx vy vz + offsetX lx ly lz lx ly
#     lz = protX vx vy vz` (a concrete equation) where the other six printed `True`,
#     and equRotRoundtrip's said `omega could not prove ... a := offsetX lx ly lz 0 0
#     0` rather than reducing at all. The `exact (hcon.1 : Nat)` type-revealing probe
#     confirmed it: gold `has type protX … + offset*(L,L) = protX …` / `vx +
#     offset*(L,L) = vx`, not `True`, on both — while the other six printed `True`.
#     DECISIVE: a forgery differing ONLY in spelling the hypothesis with the FROZEN
#     impl's own `offset*(L,L)` — i.e. asserting the FROZEN solution is WRONG at that
#     point — ELABORATED against gold (exit 0) and FAILED against the rival (exit 1),
#     the exact inversion of the required discrimination. So the gate would have
#     recorded `rejected` for a witness whose content was "gold violates its own
#     spec". Repaired by naming same_site_x/add_zero (and, for the round-trip case,
#     conditioning on the whole branch value `vx + offset*(L,0) ≠ vx` rather than on
#     `offset*(L,0) ≠ 0`, so the closing step is `exact hne hcon.1` and not `omega` on
#     an unconstrained atom). Rebuilt: rival exit 0, gold exit 1 with `hcon : True`
#     (type-revealing probe on both sides), probe exit 1. The forgery no longer
#     elaborates on gold.
#
#   (3) admiss-gold-in-domain was DEGENERATE: its `module` was `_BASE`, the frozen
#     file byte-for-byte, so the case was a re-run of G-VERIFY that varied nothing and
#     tested the PRECOND-TOO-STRONG direction not at all. Replaced by
#     admiss-obligation-satisfiable-at-comp2, which discharges the obligation at a
#     concrete in-domain selector (comp = 2, the fall-through branch) by evaluation,
#     as an in-region `have`, before closing the frozen obligation verbatim. Built:
#     exit 0. LIVENESS measured: the same shape with the comp = 2 leg claiming `out =
#     fwdY x y z` does NOT elaborate (exit 1), so the `have` is load-bearing.
#
# AUDIT REPAIRS, ROUND 1. Two reject
#   cases passed the gate on a NON-DISCRIMINATING gold-side failure and were fixed;
#   one rival was added to close a coverage gap. All rebuilt: see below.
#   * roundtrip-ignore-comp — was stated at literal inputs (comp=1, vx=0, vy=1,
#     vz=0). Rival exit 0 / gold exit 1, so the gate recorded a refutation, but
#     gold's failure was `Tactic decide failed ... did not reduce to isTrue or
#     isFalse` on `¬ bwdY (fwdX 0 1 0) (fwdY 0 1 0) (fwdZ 0 1 0) = 1`: the opaque
#     axioms have no executable content, so the kernel never evaluated the claim.
#     The gate's own stuck-reduction check caught this and silently fell back to a
#     battery positive as the subject (meta.json records witness_subject = "a
#     verifying positive from this battery (gold cannot decide)") — but that
#     fallback subject, pos-roundtrip-branch-reorder, then failed with `Tactic
#     rewrite failed: Did not find an occurrence of the pattern @wp ... (pure ?x)`,
#     because reordering the branches leaves an unreduced `if 1 = 2 then ... else
#     ...` that `rw [wp_pure]` cannot see through. A rewrite pattern miss is a
#     syntactic accident, not a refutation, so the recorded rejection attributed
#     nothing to the spec. Re-stated over symbolic vx/vy conditioning on `vx ≠ vy`,
#     with orth_x/orth_y discharging both legs: rival exit 0, gold exit 1 with
#     `hcon : True` (semantic), probe exit 1.
#   * wrong-direction-rot-to-equ-uses-P — its witness stated the postcondition as
#     `out = protInvX ox oy oz + offsetX lx ly lz lx ly lz`, but the FROZEN ensures
#     is the bare `out = protInvX ox oy oz`. The witness refuted an obligation of
#     its own invention (one carrying an extra opaque summand on the RHS), so the
#     rejection was not attributable to the frozen clause. Re-stated over the
#     frozen clause verbatim, with same_site_x/add_zero discharging the rival's
#     offset: rival exit 0, gold exit 1 with `hcon : True`, probe exit 1.
#   * roundtrip-forward-leg-only — ADDED. pbt_coverage.py reported that all of
#     observedRoundtrip's reject witnesses probed the SAME input point, so the
#     battery said nothing about the spec's dependence on comp/vx/vy/vz for that
#     obligation. This rival drops the inverting leg and is refuted at comp=2:
#     rival exit 0, gold exit 1 with `hcon : True`, probe exit 1.
#
# AUDIT PROBES, ROUND 2, that found NOTHING (recorded so the next reader need not
#   redo them; all independently authored and built by the second auditor).
#   SPEC-TOO-WEAK (attack D) — 10 NEW wrong impls, ALL rejected (exit 1), so no spec
#   hole on this surface: observedToItrs returning bwdX on comp=1; equToRot returning
#   the y-rotation on comp=2; rotToEqu FORCE-CENTRE (offset*(L,0) on every branch);
#   equRotRoundtrip ignoring comp (always the x-leg); itrsToObserved applying the
#   TRANSPOSE action instead of the forward one; equToRot carrying offset*(0,L) (the
#   re-referencing arguments swapped — same_site does not apply to it either);
#   itrsToObserved ignoring comp; rotToEqu emitting the y-inverse on comp=2;
#   equRotRoundtrip dropping the inverting leg; and the sole EXPECTED non-rejection,
#   observedRoundtrip implemented as the bare `return v{x,y,z}` identity, which
#   VERIFIES (exit 0) — correctly, since that clause IS the identity and the frozen
#   spec deliberately pins the round-trip's VALUE rather than its route (the route is
#   pinned by itrsToObserved/observedToItrs's own clauses, which the battery attacks
#   separately). Not a hole: the bare identity refines to a patch that computes the
#   round trip correctly by construction.
#   SPEC-TOO-STRONG (attack E) — 5 NEW correct reshapes, ALL verified (exit 0), so
#   the spec rejects no faithful impl: equToRot with the same-site offset dropped
#   entirely; rotToEqu carrying the same-site offset TWICE; itrsToObserved as a
#   let-bound `if` ladder returning a single value; observedToItrs with NEGATED
#   nested guards; observedRoundtrip with the forward leg inlined at each use rather
#   than let-bound.
#
# AUDIT PROBES, ROUND 1, that found NOTHING (recorded so the next reader need not redo them).
#   SPEC-TOO-WEAK (attack D) — 7 NEW wrong impls aimed at what the ported rivals
#   left unattacked; ALL rejected (exit 1), so no spec hole: observedToItrs wrong
#   at comp=2; equToRot swapping comp=1's component; rotToEqu FORCE-CENTRE (the one
#   method the battery never force-centres); observedToItrs ignoring comp;
#   observedToItrs by the indirect route bwd(fwd o); observedRoundtrip forward-leg
#   only; equRotRoundtrip swapping the y/z outputs.
#   SPEC-TOO-STRONG (attack E) — 4 NEW correct reshapes; ALL verified (exit 0), so
#   the spec rejects no faithful impl: equToRot and rotToEqu with the same-site
#   offset DROPPED ENTIRELY (offset*(L,L)=0, so observably identical to gold —
#   these two confirm the site clause is pinned by VALUE and not by the syntactic
#   presence of the offset term); itrsToObserved as a let-bound value ladder;
#   observedToItrs with negated guards (`if comp ≠ 0 then ...`).
#
# ADDED positives (pos-forward-branch-reorder, pos-rottoequ-branch-reorder,
#   pos-equrot-roundtrip-branch-reorder): the nagini positives defended only three
#   of the six obligations. Every velvet `prove_correct` obligation must be
#   defended (>=1 verify), so the branch-reorder positive is generalized to all
#   six methods. Each keeps the frozen `prove_correct … by loom_solve <;> simp_all
#   […]` script (the values per branch are unchanged) — all six were built and
#   verify (exit 0).
# RE-AIMED (admissibility-forward-indomain -> admiss-obligation-satisfiable-at-comp2):
#   the nagini probe re-derives the precondition consequence in-region in
#   itrs_to_observed. The analogue on this total carrier is the obligation being
#   UNSATISFIABLE at an F2P-shaped input. The re-aimed case discharges itrsToObserved's
#   own triple at the concrete selector comp = 2 (the fall-through branch) as an
#   in-region `have`, by evaluation, before closing the frozen obligation verbatim —
#   so a `require` that admitted no in-domain selector, or a post-image no computation
#   could hit there, would make this case FAIL. Built exit 0; the false-claim
#   counterpart (comp = 2 leg claiming fwdY) fails, so the `have` is live.
# PORTED (the six uniqueness rivals): each re-expresses the wrong impl against the
#   frozen spec and carries a machine-checked witness. ALL condition on the carrier
#   with one weak hypothesis about one term — including roundtrip-ignore-comp, whose
#   transparent clause (`out = vy`) must still be attacked symbolically because a
#   literal input makes the gold-side `decide` stick rather than refute (see AUDIT
#   REPAIRS). Each verified three ways:
#     rival exit 0, gold exit != 0, consistency probe exit != 0 (where a binder is
#     present). The two forward rivals sit at DISTINCT comp sub-domains (indirect
#     at comp=0, partial at comp=2) so the comp binder is varied and they do not
#     share a witness.
# ADDED (force-centre-equrot-roundtrip): the nagini battery attacked equ_to_rot /
#   rot_to_equ but not equ_rot_roundtrip's own impl (its discriminator lived in the
#   pair on nagini). On this carrier equRotRoundtrip is a SEPARATE `prove_correct`
#   obligation whose `comp = k → out = v{x,y,z}` identity must be independently
#   attacked; forcing the centre of the Earth (offset*(L,0) instead of the no-op
#   offset*(L,L)) is exactly the pre-patch behaviour that makes the topocentric
#   round trip non-identity. Refuted at comp=0 conditioning on `offsetX … 0 0 0 ≠
#   0`. Built three ways (rival exit 0, gold exit 1, probe exit 1). Not fabricated
#   wrongness: this is the pre-patch site-dropping bug observed on the round-trip
#   obligation.
#
# VACUOUS (frame / permission-mutation): N/A on nagini (every parameter is a plain
#   int, no Acc(...,1/2)) and vacuous here too — Velvet is referentially
#   transparent, no heap / aliasing / fractional permission, and no `mut` binder
#   (every parameter is an immutable Int). No read-only input to overwrite and no
#   substitute probe. Not fabricated.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
#   frozen impl region is LOOP-FREE (straight-line ``let`` / ``if`` over
#   immutable values, no loop and no recursion), so there is no control flow
#   here to make diverge: a diverging rival cannot be obtained by mutating this
#   body, it has to bring a loop of its own. When it does, the semantics refuse
#   it. This bundle sets ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   orthogonality against the real rotation_matrix / matrix_transpose composites,
#   and prot_orthogonality / same_site_noop against the real precession matrices and
#   re-referencing transforms); the G-PBT gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Each method's ensures is a set of three independent
#   `comp = k → out = <rhs_k>` clauses over the selector `comp` plus the position
#   binders. Every obligation is DEFENDED (its branch-reorder positive) and
#   ATTACKED (>= 1 reject rival). The eight reject witnesses probe EIGHT distinct
#   input points: the comp binder ranges over {0,2} for itrsToObserved
#   (indirect at 0, partial at 2), {0} for observedToItrs, {1,2} for
#   observedRoundtrip (ignore-comp at 1, forward-leg-only at 2), {0} for equToRot,
#   {0} for rotToEqu, {0} for equRotRoundtrip;
#   the position binders vx/vy/vz are free ints (concrete at (0,1,0) for the
#   transparent round-trip clause, universally quantified elsewhere); the site
#   binders lx/ly/lz are exercised by the two force-centre rivals (the offset*(L,0)
#   term) and the wrong-direction site rival (offset cancellation). Every
#   independent top-level clause a nagini rival attacked — the direct-rotation
#   forward clause, the per-component forward clause, the transpose backward
#   clause, the per-component round-trip identity, the offset-free site clause, the
#   transpose site-backward clause — is attacked here, plus the topocentric
#   round-trip identity. The reject lane is NON-EMPTY, so SPEC-TOO-WEAK is
#   detectable.
AXIOM_TESTS = []
