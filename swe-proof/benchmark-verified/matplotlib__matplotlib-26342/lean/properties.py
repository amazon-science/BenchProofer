"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-26342 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_setPaths`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with every obligation closed); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

DEFENDED SURFACE (one total operation over a container carrier)
---------------------------------------------------------------
A single modeled function installs a replacement list into a container that
holds an ordered list, a staleness marker, and an opaque carrier for every other
field:

  setPaths (coll) (newPaths) : Except Unit Container
    ∃ c, result = Except.ok c ∧ c.paths = newPaths ∧ c.stale = true
                             ∧ c.rest = coll.rest

The load-bearing clauses of the postcondition, each an independent top-level
conjunct:
  (K1) result = Except.ok c   — the operation SUCCEEDS for every input; it never
       rejects the request. This is exactly what the F2P observes: the operation
       used to reject the call and now must accept it.
  (K2) c.paths = newPaths     — the stored list is the supplied list, wholesale.
  (K3) c.stale = true         — the staleness marker is raised.
  (K4) c.rest = coll.rest     — the frame: every other field is left as it was.

WHAT THIS CARRIER COLLAPSES vs the nagini sibling
-------------------------------------------------
The nagini bundle models one heap procedure over a mutable object under
fractional permissions, and its adversarial classes lean on nagini-only
machinery. This lean carrier is referentially transparent and abstracts the
operation to ONE pure total function returning ``Except Unit Container``. Two
nagini classes therefore have NO expressible instance here and are omitted
deliberately (see the ``assessment`` in the port report):

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini #1 attack writes back into
    the read-only half-permission input to trip INSUFFICIENT PERMISSION. Lean has
    no aliasing and no fractional permission: an input list cannot be
    "overwritten", and there is no permission to be insufficient. The mandatory
    nagini frame rival has no counterpart and no substitute is fabricated. What
    the frame obligation BECOMES on this carrier is the explicit ``c.rest =
    coll.rest`` conjunct (K4) — and that IS attacked directly, by a rival that
    clobbers the untouched carrier (see ``reject-clobber-rest``).
  * REFERENCE-IDENTITY / COPY-NOT-IDENTITY — VACUOUS. The nagini identity clause
    ``self.items is new_items`` pins CPython object identity, so a store of a
    value-equal COPY is a distinct rival there. This carrier pins VALUE equality
    (``c.paths = newPaths``, the ``List Path ↔ python list`` identity bijection);
    a value-equal copy is value-equal, so ``list(newPaths)`` and ``newPaths`` are
    indistinguishable and the copy rival's abstraction collapses. It cannot be
    given a discriminating witness on this carrier and is honestly dropped.

Both omissions were re-derived from scratch during audit and CONFIRMED
inexpressible by real builds, not accepted on the port's word:
  * the input-frame clauses (``len``/contents of the supplied list unchanged) are
    provable here of an ARBITRARY candidate operation — the input is a value, so
    those conjuncts hold for every impl including wrong ones, and no witness can
    discriminate on them;
  * every candidate "store a copy" operation is EQUAL as a function to storing the
    supplied list (``newPaths.map id = newPaths`` etc.), so the copy rival is not
    a distinct impl and no input separates it from the frozen one.

The nagini positive control (reorder the two straight-line assignments) and the
admissibility probe (a normal in-domain input is reachable) port directly. The
nagini ``skip-the-flag`` and ``install-empty/wrong-object`` rivals port to K3 and
K2 respectively; the nagini "install nothing / raise" pre-patch failure mode
ports to K1 (the operation must succeed rather than reject).

BINDER COVERAGE. The spec predicate's input binders are ``coll`` (with fields
``paths``, ``stale``, ``rest``) and ``newPaths``. The seven reject witnesses probe
SEVEN distinct input points, varying every binder rather than sitting at one
point (which would say nothing about the spec's dependence on any binder):

  * ``coll.paths`` — ``[]``, ``[9]``, ``[7]``, ``[4]``, ``[5]``, ``[3]``, ``[1]``.
  * ``coll.stale`` — ``true``, ``true``, ``false``, ``true``, ``false``,
    ``true``, ``false``.
  * ``coll.rest``  — ``0``, ``7``, ``3``, ``9``, ``6``, ``2``, ``4``.
  * ``newPaths``   — ``[8]``, ``[2]``, ``[7]``, ``[4]``, ``[1, 2]``, ``[4]``,
    ``[]`` (varying LENGTH as well as contents: K2 is probed at a multi-element
    list, and both K2 and K3 are probed at the EMPTY replacement list, the
    boundary sub-domain).

The variation is MEANINGFUL, not two spellings of one point: the last two
witnesses sit where their rival is the ONLY one that misbehaves, and the empty
replacement list is a point at which five of the seven rivals coincide exactly
with the frozen impl. A witness set that stayed on non-empty single-element
lists would have left both sub-domain rivals below undetected.

SPEC STRENGTH IS COMPLETE, MECHANICALLY. Audit-checked: the postcondition
determines the result UNIQUELY on this carrier — from ``problem_spec_setPaths
coll newPaths r`` one proves ``r = Except.ok { paths := newPaths, stale := true,
rest := coll.rest }`` (obtain the witness container, substitute, destructure,
``simp_all``). So there is no room for a SPEC-TOO-WEAK hole in the modeled
operation at all: any impl satisfying the spec agrees with the frozen one on
every input. The reject rivals below are therefore probing the four conjuncts for
PRESENCE, and the positives are probing the spec for over-strength; the
uniqueness direction is settled outright by that completeness argument.

Each rival isolates the clause it attacks: it holds the other three clauses at a
satisfying value so the ONLY failing conjunct is the one named, and its witness
sits at an input where that conjunct is observably violated.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen closing proof is tuned to the frozen
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec predicate at one concrete input. Each is stated directly
against ``problem_spec_setPaths`` at a ground container / list, discharged by
``simp`` after unfolding, and each was checked to hold of its rival AND to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).

WITNESS DISCRIMINATION IS FORGERY-TESTED, not merely "read as semantic". Every
reject case's gold-side failure is ``error: unsolved goals ⊢ False`` — but an
error text is admissible evidence only if it CHANGES when the claim changes, so
each of the five witnesses was rebuilt in all four quadrants (audit a6):

  * witness (``¬ spec``) on the RIVAL  -> exit 0 (the rival really is refuted);
  * witness (``¬ spec``) on GOLD       -> exit 1, ``⊢ False``;
  * FLIPPED claim (``spec``, negation dropped) on GOLD  -> exit 0;
  * FLIPPED claim (``spec``) on the RIVAL               -> exit 1, ``⊢ False``.

The exit codes INVERT with the claim on both impls, which is what rules out the
hollow case where gold's exit code carries no information about what was
asserted. The ``⊢ False`` on the gold side is therefore a genuine semantic
refutation: ``simp`` reduced ``¬ spec`` to ``False`` because the spec HOLDS of
gold at that point. No witness binds a hypothesis (all inputs are ground
literals), so ``consistency_probe`` returns None and no forged-hypothesis
vacuity is possible — the failure mode where a witness "proves" its point from
an unsatisfiable assumption cannot arise here.

DIVERGENCE / NON-TERMINATION lane: NO SHIPPABLE CASE, demonstrated (not assumed).
This is plain Lean 4 + Mathlib; there is no ``loom.semantics.termination`` option
in this bundle (that setting is velvet's), so Lean's own total-by-default
semantics govern and both diverging shapes were built to see which disposition
applies:

  * a genuinely recursive rival (``implementation_setPaths coll newPaths`` as its
    own body, no ``partial``) is REJECTED by the elaborator for TERMINATION:
    ``fail to show termination ... no parameters suitable for structural
    recursion``. But that rejection is a definition-level well-formedness error,
    not the spec refuting a value: the module never gets far enough to state the
    obligation, and a witness against it dies with the SAME termination error
    rather than a claim-tracking one. It attributes nothing to the spec.
  * a ``partial def`` rival is accepted as a definition, and then the frozen
    obligation cannot be closed (``simp made no progress``) because a ``partial``
    constant is OPAQUE — it has no equation lemma to reduce. That same opacity is
    what defeats a witness: the direct witness fails with ``Tactic `unfold`
    failed to unfold `implementation_setPaths```, a SYNTACTIC failure, and the
    hypothesis-style form (assume ``impl … = Except.error ()``, then refute) was
    built against BOTH impls and elaborated on BOTH (exit 0 / exit 0) — the
    assumed equation is unsatisfiable-but-undetectable for gold too, so it is a
    forged hypothesis and not a discriminator.

So the class is a KNOWN HOLE at the witness level rather than a vacuous class:
nothing here can separate a diverging impl from the frozen one by a
claim-tracking build, because the only rival the carrier admits is opaque. It is
recorded as such deliberately, and no case is fabricated to cover it.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total computation over the inputs with no consumed callee
axiom, so there is no axiom-soundness obligation to probe here (that lane belongs
to G-AX in any case).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26342"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full impl def and its individual straight-line steps, plus the full proof
# tactic body, so every replacement lands entirely inside the region it edits.
_IMPL_DEF = (
    "def implementation_setPaths {Path : Type}\n"
    "    (coll : PathContainer Path) (newPaths : List Path) :\n"
    "    Except Unit (PathContainer Path) := Id.run do\n"
    "  let mut c := coll\n"
    "  c := { c with paths := newPaths }\n"
    "  c := { c with stale := true }\n"
    "  return Except.ok c"
)
_STEP_PATHS = "  c := { c with paths := newPaths }\n"
_STEP_STALE = "  c := { c with stale := true }\n"
_RET_OK = "  return Except.ok c"
_ORDER = (
    "  c := { c with paths := newPaths }\n"
    "  c := { c with stale := true }"
)
_PROOF = (
    "  intro Path coll newPaths\n"
    "  refine ⟨{ coll with paths := newPaths, stale := true }, ?_, rfl, rfl, rfl⟩\n"
    "  rfl"
)

assert _IMPL_DEF in _BASE, "impl anchor drift: setPaths body not verbatim"
assert _PROOF in _BASE, "proof anchor drift: correct_setPaths body not verbatim"


def _witness(coll, newpaths):
    return (
        "example : ¬ problem_spec_setPaths\n"
        "    (" + coll + ")\n"
        "    (" + newpaths + ")\n"
        "    (implementation_setPaths\n"
        "      (" + coll + ")\n"
        "      (" + newpaths + ")) := by\n"
        "  unfold problem_spec_setPaths implementation_setPaths\n"
        "  simp\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_setPaths` statement byte-identical; the frozen
    # closing proof still discharges the reshaped impl (it reduces to the same
    # normal form), so no helper lemma, no axiom, no assumption token is added.
    # =====================================================================
    {
        "id": "pos-reorder-assignments",
        "kind": "soundness",
        "expect": "verify",
        # Swap the two independent straight-line field updates: raise the
        # staleness marker FIRST, then install the list. Same post-state on every
        # clause (paths = newPaths, stale = true, rest = coll.rest, result = ok).
        "module": _swap(
            _BASE, _ORDER,
            "  c := { c with stale := true }\n"
            "  c := { c with paths := newPaths }",
        ),
        "rationale": "a correct reshape of the two independent field updates "
                     "(raise the staleness marker first, then install the list) "
                     "yields the identical container, so it must satisfy every "
                     "conjunct of `∃ c, result = ok c ∧ c.paths = newPaths ∧ "
                     "c.stale = true ∧ c.rest = coll.rest`; if it could not, the "
                     "postcondition would be SPEC-TOO-STRONG. Proof: the frozen "
                     "tactic body is retained — both orderings reduce to the same "
                     "record `{ coll with paths := newPaths, stale := true }`, "
                     "which the `refine ⟨…, rfl, rfl, rfl⟩; rfl` closes.",
    },
    {
        "id": "pos-single-record",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulator `do`-block into a single record-update literal
        # returned directly, with no mutable local and no `Id.run do`. Same value
        # on every input; the frozen proof still closes.
        "module": _swap(
            _BASE, _IMPL_DEF,
            "def implementation_setPaths {Path : Type}\n"
            "    (coll : PathContainer Path) (newPaths : List Path) :\n"
            "    Except Unit (PathContainer Path) :=\n"
            "  Except.ok { coll with paths := newPaths, stale := true }",
        ),
        "rationale": "collapsing the accumulator loop into a single "
                     "record-update literal (`Except.ok { coll with paths := "
                     "newPaths, stale := true }`) computes the identical result, "
                     "so a correct reshape must verify (else SPEC-TOO-STRONG). "
                     "Proof: frozen tactic body retained — the impl already IS the "
                     "witness record the `refine` supplies, closed by `rfl`.",
    },

    {
        "id": "pos-branch-on-marker",
        "kind": "soundness",
        "expect": "verify",
        # A correct reshape that is NOT definitionally equal to the frozen impl.
        # AUDIT NOTE — the two positives above are both closed by the FROZEN
        # tactic body, which means each reduces to the same normal form as the
        # frozen impl: they are defeq reshapes, and a defeq reshape is the
        # weakest kind of soundness probe (it cannot distinguish "the spec admits
        # a different shape" from "the shape was never different"). This case
        # branches on the INCOMING staleness marker, so the two arms have
        # genuinely distinct normal forms and the frozen `refine … rfl` no longer
        # closes it (verified: it fails with the frozen proof body retained). It
        # therefore has to be REPROVEN inside the proof region — which is exactly
        # what a real SPEC-TOO-STRONG probe must do. The reproof adds no
        # declaration, no axiom and no assumption token, and the theorem
        # statement stays byte-identical.
        "module": _swap(
            _swap(
                _BASE, _IMPL_DEF,
                "def implementation_setPaths {Path : Type}\n"
                "    (coll : PathContainer Path) (newPaths : List Path) :\n"
                "    Except Unit (PathContainer Path) := Id.run do\n"
                "  let mut c := coll\n"
                "  if c.stale then\n"
                "    c := { c with paths := newPaths }\n"
                "  else\n"
                "    c := { c with paths := newPaths, stale := true }\n"
                "  c := { c with stale := true }\n"
                "  return Except.ok c",
            ),
            _PROOF,
            "  intro Path coll newPaths\n"
            "  unfold problem_spec_setPaths implementation_setPaths\n"
            "  by_cases h : coll.stale <;> simp [Id.run, h] <;> "
            "exact ⟨_, rfl, rfl, rfl, rfl⟩",
        ),
        "rationale": "a correct reshape that takes a DIFFERENT computational route "
                     "per incoming marker value (install the list, then raise the "
                     "marker; where the marker was already down, raise it in the "
                     "same update) reaches the identical post-state on all four "
                     "conjuncts, so it must verify or the postcondition is "
                     "SPEC-TOO-STRONG. Unlike the two positives above it is NOT "
                     "definitionally equal to the frozen impl — the frozen tactic "
                     "body does not close it — so it is reproven by case-splitting "
                     "on the incoming marker and exhibiting the resulting container "
                     "in each arm. This is the case that actually shows the spec "
                     "admits a shape other than the frozen one.",
    },
    {
        "id": "reject-ignore-input",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks K2 from the other side: rather than KEEPING the old list
        # (reject-keep-old-paths), install a constant empty list — the operation
        # ignores its replacement argument entirely. Distinct from
        # reject-keep-old-paths: that rival's stored list is a function of `coll`,
        # this one's is a function of NEITHER binder, so it also refutes any
        # reading of K2 that merely required the stored list to "change".
        "module": _swap(_BASE, _STEP_PATHS, "  c := { c with paths := [] }\n"),
        "refinement": "an operation that discards the supplied list and installs an "
                      "empty one installs no geometry at all: the F2P replaces one "
                      "subject's paths with another's and compares the two rendered "
                      "figures, so a subject holding an empty path list draws nothing "
                      "while the reference draws its geometry, and the comparison "
                      "FAILS — the patch does not resolve the F2P. This is the "
                      "value-level 'install nothing' miss on the dominant non-empty "
                      "input.",
        "rationale": "REJECT from the K2 conjunct `c.paths = newPaths`: the rival "
                     "returns `Except.ok c` with `c.paths = []`, unequal to "
                     "`newPaths` for every non-empty replacement list. The marker "
                     "and frame are kept correct so the ONLY failing conjunct is K2. "
                     "Witnessed at newPaths = [1, 2] ≠ [], on a container whose "
                     "marker starts DOWN and whose carrier is non-zero, so the "
                     "witness point differs from every other rival's.",
        "witness": _witness(
            "{ paths := ([5] : List Nat), stale := false, rest := 6 }",
            "([1, 2] : List Nat)",
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at a normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled operation is total, so `∀` is unguarded), which
    # means the nagini precondition-admission probe has no binder to attack here;
    # the honest analogue discharges the spec predicate at a ground non-empty
    # replacement input, inside the proof region, alongside the frozen
    # obligation. If that ground instance could not be discharged, the modeled
    # operation would be unsatisfiable at exactly the shape the F2P exercises (a
    # non-empty replacement list installed onto a stale-false container).
    # =====================================================================
    {
        "id": "admiss-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_setPaths\n"
            "      ({ paths := ([1] : List Nat), stale := false, rest := 5 })\n"
            "      ([2, 3] : List Nat)\n"
            "      (implementation_setPaths\n"
            "        ({ paths := ([1] : List Nat), stale := false, rest := 5 })\n"
            "        ([2, 3] : List Nat)) := by\n"
            "    unfold problem_spec_setPaths implementation_setPaths\n"
            "    exact ⟨{ paths := [2, 3], stale := true, rest := 5 }, rfl, rfl, rfl, rfl⟩\n"
            + _PROOF,
        ),
        "rationale": "the obligation is discharged at a ground F2P-shaped input (a "
                     "non-empty replacement list installed onto a container whose "
                     "staleness marker starts down) by exhibiting the resulting "
                     "container explicitly, then the frozen obligation is closed "
                     "verbatim. Verifies (else the operation is unsatisfiable at "
                     "the normal input, the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, the theorem "
                     "statement is byte-identical, and the ground instance is a "
                     "`have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying rival
    # would be a true verify-does-not-imply-resolve break rather than an artifact,
    # and (b) a refutation witness pinning the violation at one concrete input.
    # The four rivals attack the four independent postcondition conjuncts K1..K4.
    # =====================================================================
    {
        "id": "reject-not-ok",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks K1 (success): the operation REJECTS the request instead of
        # accepting it — returns the error result rather than the updated
        # container. This is the pre-existing failure mode at the value level.
        "module": _swap(_BASE, _RET_OK, "  return Except.error ()"),
        "refinement": "an operation that rejects the call instead of accepting it "
                      "reproduces the pre-existing behavior the F2P was added to "
                      "exclude: the F2P calls the operation on a subject that does "
                      "NOT override it (so the base behavior applies) and expects "
                      "it to succeed and install the supplied paths; if it rejects "
                      "the request the call errors out and the render comparison "
                      "never happens — the patch does not resolve the F2P.",
        "rationale": "REJECT from the K1 conjunct `∃ c, result = Except.ok c`: the "
                     "rival returns `Except.error ()`, which is never `Except.ok "
                     "c` for any c, so no witness container exists and the whole "
                     "existential fails. Isolates K1 — this is the only clause the "
                     "rival can violate since there is no returned container to "
                     "test the other conjuncts against.",
        "witness": _witness(
            "{ paths := ([] : List Nat), stale := true, rest := 0 }",
            "([8] : List Nat)",
        ),
    },
    {
        "id": "reject-keep-old-paths",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks K2 (paths): raises the staleness marker and succeeds, but never
        # installs the supplied list — the container keeps its previous path list.
        "module": _swap(_BASE, _STEP_PATHS, ""),
        "refinement": "an operation that raises the staleness marker but leaves "
                      "the previous path list in place installs nothing: the "
                      "F2P replaces one subject's paths with another's and expects "
                      "the first to render the replacement geometry; keeping the "
                      "old list renders the wrong geometry and the render "
                      "comparison FAILS — the patch does not resolve the F2P.",
        "rationale": "REJECT from the K2 conjunct `c.paths = newPaths`: the rival "
                     "returns `Except.ok coll'` whose `.paths` is the input "
                     "`coll.paths`, unequal to `newPaths` whenever they differ. "
                     "The staleness marker and frame are kept correct so the ONLY "
                     "failing conjunct is K2. Witnessed at coll.paths = [9] ≠ "
                     "newPaths = [2].",
        "witness": _witness(
            "{ paths := ([9] : List Nat), stale := true, rest := 7 }",
            "([2] : List Nat)",
        ),
    },
    {
        "id": "reject-skip-stale",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks K3 (stale): installs the supplied list and succeeds, but never
        # raises the staleness marker — it stays at whatever the container held.
        "module": _swap(_BASE, _STEP_STALE, ""),
        "refinement": "AUDIT NOTE — this rival's refinement argument is a "
                      "GOLD-BEHAVIOR argument, not an F2P-render argument, and is "
                      "stated as such deliberately. The save-to-image path used by "
                      "the F2P oracle draws UNCONDITIONALLY (the figure's save "
                      "routine calls draw on every invocation; nothing on that path "
                      "is guarded on the staleness marker, which only schedules "
                      "redraws for interactive/animated consumers via its "
                      "propagation callback). So a faithful patch that installed the "
                      "list but omitted raising the marker would still RESOLVE this "
                      "instance's F2P, and any claim that the render comparison "
                      "fails without the marker is false. The rival is nonetheless a "
                      "correct expect=\"reject\" case on a narrower ground: raising "
                      "the marker is part of the declared post-state of the modeled "
                      "operation (K3) and of the behavior the real change installs, "
                      "so an operation that skips it is a DIFFERENT algorithm that "
                      "violates the frozen postcondition. Its rejection therefore "
                      "attests to K3's presence in the spec — it does not attest to "
                      "verify-implies-resolve, and must not be read as doing so.",
        "rationale": "REJECT from the K3 conjunct `c.stale = true`: the rival "
                     "returns `Except.ok coll'` whose `.stale` is the input "
                     "`coll.stale`; at coll.stale = false this is `false ≠ true`. "
                     "The stored list and frame are kept correct (newPaths equals "
                     "coll.paths at the witness so K2 also holds) so the ONLY "
                     "failing conjunct is K3.",
        "witness": _witness(
            "{ paths := ([7] : List Nat), stale := false, rest := 3 }",
            "([7] : List Nat)",
        ),
    },
    {
        "id": "reject-clobber-rest",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks K4 (frame): installs the list and raises the marker correctly,
        # but ALSO overwrites the opaque carrier for every other field — the frame
        # obligation this carrier expresses in place of nagini's permission check.
        "module": _swap(_BASE, _RET_OK, "  c := { c with rest := 0 }\n  return Except.ok c"),
        "refinement": "an operation that also rewrites an unrelated field of the "
                      "container while installing the list corrupts state the "
                      "operation is supposed to leave alone; a faithful patch that "
                      "reset some other attribute of the subject as a side effect "
                      "would leave the object in an inconsistent state and other "
                      "assertions/renders that depend on that state would break — "
                      "the frame is exactly what the operation must NOT touch, so "
                      "such a patch would not faithfully resolve.",
        "rationale": "REJECT from the K4 conjunct `c.rest = coll.rest`: the rival "
                     "returns `Except.ok c` with `c.rest = 0`, unequal to the "
                     "input `coll.rest` whenever it is non-zero. This is the "
                     "lean expression of nagini's read-only-frame obligation. "
                     "Stored list and marker are kept correct so the ONLY failing "
                     "conjunct is K4. Witnessed at coll.rest = 9 ≠ 0.",
        "witness": _witness(
            "{ paths := ([4] : List Nat), stale := true, rest := 9 }",
            "([4] : List Nat)",
        ),
    },

    # =====================================================================
    # SUB-DOMAIN rivals (added by audit a6). The five rivals above are each
    # wrong on a LARGE part of the domain, so a spec that pinned its clauses
    # only "somewhere" would still reject them. These two are correct on most
    # inputs and wrong only on a thin slice, which is what actually tests that
    # K2/K3 are quantified over the WHOLE domain rather than merely typical
    # inputs. Both were confirmed discriminating by build before landing.
    # =====================================================================
    {
        "id": "reject-append-not-replace",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks K2 on a THIN slice: appends the replacement list to what the
        # container already holds instead of replacing wholesale. Correct exactly
        # when the container started empty, wrong otherwise — so it survives any
        # reading of K2 that only required the supplied elements to be PRESENT in
        # the stored list. This is the "replace vs. accumulate" confusion.
        "module": _swap(
            _BASE, _STEP_PATHS,
            "  c := { c with paths := coll.paths ++ newPaths }\n"),
        "refinement": "an operation that appends the replacement list to the "
                      "existing one instead of replacing it leaves the previous "
                      "geometry in place alongside the new: the F2P installs one "
                      "subject's paths onto another and compares the two rendered "
                      "figures, so the subject would draw BOTH its original "
                      "geometry and the replacement while the reference draws only "
                      "the replacement, and the comparison FAILS — the patch does "
                      "not resolve the F2P. It resolves only in the degenerate case "
                      "where the subject held nothing to begin with.",
        "rationale": "REJECT from the K2 conjunct `c.paths = newPaths`: the rival "
                     "stores `coll.paths ++ newPaths`, which equals `newPaths` iff "
                     "`coll.paths = []`. K1/K3/K4 are all held correct, so K2 is "
                     "isolated. Witnessed at coll.paths = [3] with newPaths = [4], "
                     "where the stored list is [3, 4] ≠ [4] — a point the other K2 "
                     "rivals do not reach, since both of them are wrong even on an "
                     "initially-empty container while this one is CORRECT there.",
        "witness": _witness(
            "{ paths := ([3] : List Nat), stale := true, rest := 2 }",
            "([4] : List Nat)",
        ),
    },
    {
        "id": "reject-marker-tracks-emptiness",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks K3 at the EMPTY boundary only: raises the marker iff the
        # replacement list is non-empty. Correct on every non-empty input — i.e. on
        # every input the other rivals' witnesses use — and wrong only at
        # newPaths = []. Probes that K3 is unconditional rather than merely
        # holding on the dominant (non-empty) sub-domain.
        "module": _swap(
            _BASE, _STEP_STALE,
            "  c := { c with stale := !newPaths.isEmpty }\n"),
        "refinement": "an operation that raises the staleness marker only when the "
                      "replacement list is non-empty makes the marker's post-state "
                      "depend on the payload, so installing an empty list leaves "
                      "the container claiming its cached rendering is current when "
                      "its contents just changed. A faithful patch of that shape "
                      "would leave a consumer that clears the geometry with a stale "
                      "cache it believes fresh — the declared post-state (K3) is "
                      "unconditional, so this is a different algorithm on the empty "
                      "boundary even though it agrees with gold everywhere else.",
        "rationale": "REJECT from the K3 conjunct `c.stale = true`: the rival stores "
                     "`!newPaths.isEmpty`, which is `true` for every non-empty "
                     "replacement list but `false` at newPaths = []. K1/K2/K4 hold "
                     "at the witness, isolating K3. Witnessed at the EMPTY "
                     "replacement list on a marker-down container — the one "
                     "sub-domain no other rival's witness visits, since the other "
                     "four K2/K3 witnesses all use non-empty lists where this rival "
                     "is indistinguishable from the frozen impl.",
        "witness": _witness(
            "{ paths := ([1] : List Nat), stale := false, rest := 4 }",
            "([] : List Nat)",
        ),
    },
]

# No Docker AXIOM_TESTS: meta.json axioms == [] and deep_model_references == []
# (no consumed callee axiom, no A-reference; the impl is all R/I, validated by
# G-CONF over 1e5 fuzzed inputs). The axiom lane is G-AX's job and is a skip stub
# for this instance; this gate ignores it.
AXIOM_TESTS = []
