"""properties.py — G-PBT falsification battery for django__django-14315 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC_TESTS entry is a
full ``Solution.lean`` variant produced by region surgery: only text inside an
``-- impl-start``/``-- impl-end`` region — and, for a case that legitimately
re-proves, inside a ``-- proof-start``/``-- proof-end`` region — is changed, so
``markers.same_spec`` holds by construction and both ``theorem correct_*``
STATEMENTS stay byte-identical. ``expect="verify"`` passes iff the variant is in
scope AND the file elaborates with both obligations closed (no ``sorry`` /
``admit`` / ``native_decide``, no new ``axiom`` / ``theorem`` / ``lemma``);
``expect="reject"`` passes iff the variant is in scope AND does NOT verify AND
the case's refutation ``witness`` holds of the rival while FAILING on the frozen
solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier — the nagini manifest
is the design document, not a text to translate. The nagini sibling models two
functions over a ``Dict[int,int]`` carrier with fractional-permission
preconditions; this bundle models the SAME two purely-functional behaviours over
``List (String × String)`` / ``Option (List (String × String))``, so every nagini
case that attacks a VALUE clause carries over, while every case that attacks a
PERMISSION is vacuous here (see ``assessment`` and the accounting block at the
bottom, which records the disposition of all ten sibling cases).

DEFENDED SURFACE (two obligations, four independent top-level clauses).

``problem_spec_runshell_env osEnviron env result`` — resolving the environment
handed to a spawned child, from the ambient environment and an optionally
supplied override environment:

  * (A1) ``envIsSet env = false → result = none`` — when the override is not
    present (absent, or supplied but empty) the resolved environment is absent,
    so the child inherits the ambient one. Two sub-domains live under this one
    clause (``env = none`` and ``env = some []``) and the battery attacks BOTH,
    since a rival can be wrong on exactly one of them.
  * (A2) ``∀ kvs, env = some kvs → kvs ≠ [] →
    result = some (combineEnv osEnviron kvs)`` — when the override is present,
    the result is the ambient environment overlaid with those overrides, in that
    argument order, with nothing else added.

``problem_spec_client_env env result`` — reporting the override environment a
command builder assembles (always a concrete, possibly empty set):

  * (B1) ``env = [] → result = none`` — an empty set of overrides is reported as
    absent.
  * (B2) ``env ≠ [] → result = some env`` — a non-empty set is reported
    unchanged, entry for entry.

The load-bearing behaviour, exactly as in the nagini sibling, is (a) the
not-present → absent normalization at BOTH sites and (b) the overlay's argument
order / no-extra-entries value clause. There is no answer-key oracle to echo:
``result`` is pinned either to ``none`` or to a term built from the two inputs.

BINDER STRUCTURE. ``problem_spec_runshell_env`` has two input binders
(``osEnviron``, ``env``) and ``problem_spec_client_env`` has one (``env``). All
three are varied by the reject witnesses: the five runshell witnesses probe five
DISTINCT ``(osEnviron, env)`` points with three distinct ``osEnviron`` values and
``env`` ranging over ``none``, ``some []`` and two distinct non-empty overrides;
the two client witnesses probe ``[]`` and a one-entry set. The point spread is
tabulated at the bottom of this file.

ATTACKING AN OPAQUE CARRIER. The overlay operation ``combineEnv`` is declared
without a defining equation and the proof consumes no property of it, so no
literal input lets a tactic compute it. That does NOT put clause A2 out of reach;
this battery attacks it four ways, none of which needs the overlay's value:

  * ``weak-absent-overlaid-anyway`` — the result's ``some``/``none`` SHAPE is
    fully transparent, so a rival that returns an overlay where the spec demands
    absence is refuted without evaluating anything;
  * ``weak-spurious-entry`` — the rival prepends an entry to the overlay's
    result, and ``x :: l ≠ l`` holds for ANY ``l``, so the COMBINATION is
    refutable while the combined value stays unknown;
  * ``weak-overlay-args-swapped`` — the rival passes the two environments in the
    wrong order. This one CONDITIONS on the carrier instead of computing it: the
    witness assumes only that the operation is not symmetric at one concrete
    pair of arguments, which is precisely the sub-domain where the rival is
    wrong, and is a single satisfiable hypothesis about the operation (not two
    hypotheses about one term, which would be the shape of a forged
    contradiction);
  * ``weak-ambient-dropped`` — the rival overlays onto NOTHING, discarding the
    ambient environment while keeping the shape, the argument order and the
    entry set. Conditions on the carrier the same way: the single hypothesis is
    that the ambient argument is observable at all.

No witness in this battery may open by restating its rival's body (a
``have himpl : implementation_… = … := rfl``). Such a step makes the gold-side
build fail with a definitional ``Type mismatch`` about gold's impl — a SYNTACTIC
failure that discriminates the two implementations rather than attesting that the
spec holds on gold — and the gate cannot distinguish that from a real refutation.
Every witness here instead reduces the branch generically with ``simp only`` on
the presence predicate at its literal input, so that against the frozen solution
the instantiated clause reduces to ``True`` and the script fails for want of
anything to contradict. That gold-side error text is the audited evidence.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen scripts end in ``rfl``, which is tuned
to the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet that instantiates the
offending clause at one concrete input and derives a contradiction. Each was
checked with real builds to HOLD of its rival and to FAIL on the frozen
solution, so it discriminates rather than asserting a tautology; each witness
that binds a hypothesis was additionally checked not to prove ``False`` from
those hypotheses alone.

Independently re-derived by a second audit, which rebuilt all eight and did NOT
stop at reading the error text, since "it looks semantic" is not evidence in
either direction. Four things were measured per case.

  * The two halves: witness against the rival exit 0, against the frozen
    solution exit 1, for all eight.
  * That gold's exit code TRACKS THE CLAIM rather than the script. For each case
    a file differing only in what it CLAIMS — the exact opposite assertion, that
    the frozen solution IS correct at that same input — was built on both sides.
    All eight inverted cleanly: exit 0 against the frozen solution, exit 1
    against the rival. So the gold-side failure is not a fixed artifact of the
    script; flip the claim and the exit code flips with it, which is precisely
    what a forged witness cannot do.
  * What gold's hypothesis actually REDUCES TO, via a deliberate type error on it
    (``exact (h : Nat)``). Against the frozen solution every case prints
    ``h has type True`` — ``simp`` PROVED the instantiated equation there — while
    against the rival the same probe prints the concrete unproven equation
    (e.g. ``combineEnv [] [("C","3")] = combineEnv [("A","1")] [("C","3")]``, or
    ``[("Z","0"), ("A","1")] = [("A","1")]``). That pair is a genuine refutation
    rather than a tactic mismatch.
  * That each claim is false of gold for a reason independent of any tactic: the
    frozen ``correct_*`` theorems were instantiated at ALL the witness points in
    one file (exit 0), so the frozen solution provably SATISFIES the spec at
    every point a witness asserts it is violated.

REFINEMENT. Each reject case's ``refinement`` states what its faithful real
counterpart would do. For the four rivals attacking the empty/absent
normalization (A1 both sub-domains, B1, B2) that counterpart demonstrably fails
the F2P set, so a rival that VERIFIED would be a true
verify-does-not-imply-resolve break. For the three rivals attacking clause A2
(``weak-overlay-args-swapped``, ``weak-spurious-entry``, ``weak-ambient-dropped``)
it does NOT: audit re-derived the F2P set and found the only case exercising the
child-spawn site drives it exclusively where the override is not present, so the
overlay branch is never reached and a faithful counterpart of those three would
most likely still pass. The port asserted otherwise for all three; that claim is
withdrawn in each ``refinement`` rather than restated. Those cases are kept
anyway, on the narrower and true ground that A2 is a load-bearing clause of the
frozen spec whose uniqueness must be probed — a rival verifying there would be a
SPEC-TOO-WEAK break whatever the test set does — but they are not evidence about
resolution and are no longer described as if they were.

SPEC STRENGTH (measured, independent audit). Both obligations pin ``result``
totally: each is a pair of implications whose antecedents partition the input
domain, so the spec is a FUNCTION, not a loose constraint. That was checked
mechanically rather than argued — a derivation of
``problem_spec_… o e r1 → problem_spec_… o e r2 → r1 = r2`` for both obligations
elaborates (exit 0), and with it
``(∀ o e, problem_spec_runshell_env o e (f o e)) → ∀ o e, f o e = implementation_runshell_env o e``
for an arbitrary ``f`` (likewise for the second obligation). So ANY impl the
frozen spec accepts is pointwise equal to the frozen impl: there is no room for a
wrong-but-verifying rival, and a SPEC-TOO-WEAK hole in these two obligations is
impossible by construction rather than merely unobserved. Re-derived
independently by the second audit: a file deriving both determinism lemmas AND
both ``pins_*`` corollaries from the frozen obligations elaborates (exit 0). Seven
NEW wrong implementations written by that audit and not present above were then
tried against the frozen spec; six were rejected, and the one that VERIFIED
(``env.getD [("Z","9")]``, a changed ``Option.getD`` default) is not a
counterexample but a defeq artifact — the default is unreachable on the branch
where it appears, since that branch is guarded by the override being present, so
the impl is pointwise IDENTICAL to the frozen one and its acceptance is correct.
The residual risk is therefore SPEC-TOO-STRONG (a faithful reshape the proof
cannot close), which is what the positive controls probe; the second audit
confirmed three further correct reshapes provable beyond those controls
(``Option.bind``, a ``match`` on the list, and a ``==``-decided emptiness guard),
finding no faithful reshape the spec rejects.

AXIOM lane: dropped. The nagini sibling carries two AXIOM_TESTS probes for its
merge callee; the axiom lane belongs to G-AX (here: the overlay operation is an
unchanged-callee reference exercised by G-AX / G-CONF), and this gate ignores
AXIOM_TESTS regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14315"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file (both asserted by _swap at import), so a drifting solution
# breaks this manifest loudly instead of silently editing the wrong text.
# ---------------------------------------------------------------------------

# --- impl regions ---
# The whole branch structure of the first modeled behaviour.
_I_RESOLVE = (
    "  if envIsSet env then\n"
    "    env := some (combineEnv osEnviron (env.getD []))\n"
    "  else\n"
    "    env := none\n"
)
# Just the overlay assignment (the present-override branch).
_I_OVERLAY = "    env := some (combineEnv osEnviron (env.getD []))\n"
# The whole body of the second modeled behaviour.
_I_REPORT = (
    "  if env.isEmpty then\n"
    "    return none\n"
    "  return some env\n"
)

# --- proof regions (tactic bodies only; the theorem STATEMENTS are untouched) ---
_P_RESOLVE = (
    "  intro osEnviron env\n"
    "  unfold problem_spec_runshell_env implementation_runshell_env\n"
    "  simp only [Id.run]\n"
    "  refine ⟨?_, ?_⟩\n"
    "  · intro h\n"
    "    simp only [h]\n"
    "    rfl\n"
    "  · intro kvs henv hne\n"
    "    subst henv\n"
    "    have h1 : envIsSet (some kvs) = true := by\n"
    "      simp [envIsSet, hne]\n"
    "    simp only [h1, if_true, Option.getD_some]\n"
    "    rfl\n"
)
_P_REPORT = (
    "  intro env\n"
    "  unfold problem_spec_client_env implementation_client_env\n"
    "  simp only [Id.run]\n"
    "  refine ⟨?_, ?_⟩\n"
    "  · intro h\n"
    "    simp only [h, List.isEmpty_nil, if_true]\n"
    "    rfl\n"
    "  · intro hne\n"
    "    have he : env.isEmpty = false := by simp [hne]\n"
    "    simp only [he]\n"
    "    rfl\n"
)
# The first line of each obligation's tactic body — the anchors the
# admissibility case prepends its ground instances to.
_P_REPORT_INTRO = "  intro env\n  unfold problem_spec_client_env"
_P_RESOLVE_INTRO = "  intro osEnviron env\n  unfold problem_spec_runshell_env"


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS positives — structurally different but CORRECT implementations
    # that MUST verify, else SPEC-TOO-STRONG. Each re-proves inside the proof
    # region for its new shape, keeping the theorem STATEMENT byte-identical and
    # introducing no helper lemma and no assumption token.
    # =====================================================================
    {
        "id": "pos-resolve-match-on-option",
        "kind": "soundness",
        "expect": "verify",
        # Replace the mutable-`do` branch with a `match` on the Option and an
        # inner emptiness test on the BOUND list. The presence predicate
        # `envIsSet` disappears from the impl entirely and the `Id.run do` /
        # `let mut` scaffolding goes with it, so the two obligations must be
        # discharged by case analysis on `env` rather than by reducing a guard.
        # AUDIT NOTE. This case previously used `if !envIsSet env then` with the
        # arms swapped. That reshape is DEFINITIONALLY EQUAL to the frozen impl
        # on this carrier: measured, the frozen proof script closes it verbatim
        # (exit 0) with no re-proof at all, so it exercised neither the spec nor
        # the proof and passed for free. A positive control has to be a reshape
        # the frozen `rfl` script does NOT see through; this one is (the frozen
        # script fails on it: `simp made no progress`), and it needs the genuine
        # re-proof below.
        "module": _swaps(
            _BASE,
            ("  Id.run do\n"
             "  let mut env := env\n"
             + _I_RESOLVE +
             "  return env\n",
             "  match env with\n"
             "  | none => none\n"
             "  | some kvs =>\n"
             "    if kvs.isEmpty then none else some (combineEnv osEnviron kvs)\n"),
            (_P_RESOLVE,
             "  intro osEnviron env\n"
             "  unfold problem_spec_runshell_env implementation_runshell_env\n"
             "  refine ⟨?_, ?_⟩\n"
             "  · intro h\n"
             "    cases env with\n"
             "    | none => rfl\n"
             "    | some kvs =>\n"
             "      have hk : kvs.isEmpty = true := by\n"
             "        simpa [envIsSet] using h\n"
             "      simp [hk]\n"
             "  · intro kvs henv hne\n"
             "    subst henv\n"
             "    have he : kvs.isEmpty = false := by simp [hne]\n"
             "    simp [he]\n"),
        ),
        "rationale": (
            "positive control on the first obligation: the presence predicate "
            "and the mutable-`do` scaffolding are replaced by a `match` on the "
            "optional override with the emptiness test on the bound list — "
            "identical values on every (osEnviron, env), a genuinely different "
            "term. Both clauses A1 (absent → none) and A2 (present → the "
            "overlay of the ambient environment with the overrides) still hold, "
            "so it MUST verify; if it did not, the spec/proof would be too "
            "strong for a faithful reshape. The reshape is NOT definitionally "
            "equal to the frozen impl — the frozen tactic script fails on it — "
            "so the re-proof (case analysis on `env`, inside the proof region "
            "only) is doing real work: statement byte-identical, no new "
            "axiom/lemma, no assumption token. Ports the sibling's "
            "pos-control-effective-disjunctive-guard (there the two early "
            "returns fuse into one disjunctive guard; here the two sub-domains "
            "are re-split along the Option, which is the structural variation "
            "this carrier makes observable)."),
    },
    {
        "id": "pos-report-length-guard",
        "kind": "soundness",
        "expect": "verify",
        # Decide emptiness by LENGTH instead of by `List.isEmpty`. Same value on
        # every input; a different decidable proposition drives the branch, so
        # the guard has to be related back to `env ≠ []` in the re-proof.
        # AUDIT NOTE. This case previously used `if !env.isEmpty then` with the
        # arms swapped, which is definitionally equal to the frozen impl here:
        # measured, the frozen proof script closes that reshape verbatim (exit
        # 0), so it tested nothing. The length guard is not defeq — the frozen
        # script fails on it — and the re-proof below has to bridge
        # `env.length = 0` and `env = []` (`List.length_eq_zero_iff`), which is
        # the real content a positive control is supposed to supply.
        "module": _swaps(
            _BASE,
            (_I_REPORT,
             "  if env.length = 0 then\n"
             "    return none\n"
             "  return some env\n"),
            (_P_REPORT,
             "  intro env\n"
             "  unfold problem_spec_client_env implementation_client_env\n"
             "  simp only [Id.run]\n"
             "  refine ⟨?_, ?_⟩\n"
             "  · intro h\n"
             "    subst h\n"
             "    rfl\n"
             "  · intro hne\n"
             "    have he : ¬ (env.length = 0) := by\n"
             "      simpa [List.length_eq_zero_iff] using hne\n"
             "    simp only [he, if_false]\n"
             "    rfl\n"),
        ),
        "rationale": (
            "positive control on the second obligation: emptiness is decided by "
            "length rather than by the list's own emptiness test — same value on "
            "every input, a different decidable proposition in the guard. "
            "Clauses B1 (empty → none) and B2 (non-empty → reported unchanged) "
            "both still hold, so it MUST verify, else SPEC-TOO-STRONG. The "
            "reshape is NOT definitionally equal to the frozen impl (the frozen "
            "tactic script fails on it), so the re-proof — which must connect "
            "the length guard to `env ≠ []` — is doing real work, inside the "
            "proof region only; statement byte-identical, no new declaration. "
            "Ports the sibling's pos-control-normalized-reordered."),
    },

    # =====================================================================
    # ADMISSIBILITY — the modeled behaviour is SATISFIABLE at a normal,
    # F2P-shaped input, so the obligation is not vacuous and no hypothesis
    # excludes an ordinary case. The sibling's admissibility case asserts that
    # the (permission-only) precondition admits a normal non-empty mapping all
    # the way through the merge; these obligations carry NO precondition
    # hypothesis at all, so the honest analogue is to discharge the spec
    # predicate itself at concrete F2P-shaped inputs as `have`s, then close each
    # frozen obligation verbatim. Nothing is assumed: the `have`s sit in the
    # existing tactic bodies, add no declaration, and leave both theorem
    # statements byte-identical. Widened by audit to cover BOTH obligations —
    # as ported it discharged ground instances of the second one only, so the
    # lane that detects PRECOND-TOO-STRONG never touched the first.
    # =====================================================================
    {
        "id": "admiss-report-one-entry",
        "kind": "admissibility",
        "expect": "verify",
        # AUDIT NOTE (widened). As ported, this case discharged ground instances
        # of the SECOND obligation only, so the admissibility lane said nothing
        # about the first — including at the two inputs whose normalization is
        # the load-bearing behaviour (override absent, override supplied-empty)
        # and at a present override, where the obligation's conclusion is a term
        # over the OPAQUE overlay. That last point is the one worth having: if a
        # ground instance over an opaque callee were unsatisfiable, no rival
        # would reveal it and every reject case would still pass. Three `have`s
        # for the first obligation are prepended here as well, so both
        # obligations are shown satisfiable at their own F2P-shaped inputs.
        # Measured: exit 0.
        "module": _swaps(
            _BASE,
            (_P_RESOLVE_INTRO,
             "  have _abs : problem_spec_runshell_env [(\"A\", \"1\")] none\n"
             "      (implementation_runshell_env [(\"A\", \"1\")] none) := by\n"
             "    unfold problem_spec_runshell_env implementation_runshell_env\n"
             "    refine ⟨?_, ?_⟩\n"
             "    · intro _\n"
             "      simp only [Id.run, envIsSet, if_false]\n"
             "      rfl\n"
             "    · intro kvs h _\n"
             "      exact absurd h (by simp)\n"
             "  have _empty : problem_spec_runshell_env [(\"A\", \"1\")] (some [])\n"
             "      (implementation_runshell_env [(\"A\", \"1\")] (some [])) := by\n"
             "    unfold problem_spec_runshell_env implementation_runshell_env\n"
             "    refine ⟨?_, ?_⟩\n"
             "    · intro _\n"
             "      simp only [Id.run, envIsSet, List.isEmpty_nil, "
             "Bool.not_true,\n"
             "        Option.getD_some, if_false]\n"
             "      rfl\n"
             "    · intro kvs h hne\n"
             "      simp only [Option.some.injEq] at h\n"
             "      exact absurd h.symm hne\n"
             "  have _over : problem_spec_runshell_env [(\"A\", \"1\")] "
             "(some [(\"B\", \"2\")])\n"
             "      (implementation_runshell_env [(\"A\", \"1\")] "
             "(some [(\"B\", \"2\")])) := by\n"
             "    unfold problem_spec_runshell_env implementation_runshell_env\n"
             "    refine ⟨?_, ?_⟩\n"
             "    · intro h\n"
             "      simp [envIsSet] at h\n"
             "    · intro kvs hk _\n"
             "      simp only [Option.some.injEq] at hk\n"
             "      subst hk\n"
             "      simp only [Id.run, envIsSet, List.isEmpty_cons, "
             "Bool.not_false,\n"
             "        if_true, Option.getD_some]\n"
             "      rfl\n"
             + _P_RESOLVE_INTRO),
            (_P_REPORT_INTRO,
            "  have _ground : problem_spec_client_env [(\"A\", \"1\")]\n"
            "      (implementation_client_env [(\"A\", \"1\")]) := by\n"
            "    unfold problem_spec_client_env implementation_client_env\n"
            "    refine ⟨?_, ?_⟩\n"
            "    · intro h\n"
            "      simp at h\n"
            "    · intro _\n"
            "      rfl\n"
            "  have _absent : problem_spec_client_env []\n"
            "      (implementation_client_env []) := by\n"
            "    unfold problem_spec_client_env implementation_client_env\n"
            "    refine ⟨?_, ?_⟩\n"
            "    · intro _\n"
            "      rfl\n"
            "    · intro h\n"
            "      simp at h\n"
            + _P_REPORT_INTRO),
        ),
        "rationale": (
            "admissibility: BOTH modeled behaviours are discharged by evaluation "
            "at their F2P-shaped boundary inputs, as `have`s prepended to the "
            "existing tactic bodies, after which each frozen obligation closes "
            "verbatim. For the first obligation: the override absent and the "
            "override supplied-but-empty (clause A1, both sub-domains — the "
            "normalization that is the load-bearing behaviour) and a present "
            "one-entry override (clause A2, whose conclusion is a term over the "
            "OPAQUE overlay, so this is the point where an unsatisfiable ground "
            "instance would be invisible to every rival). For the second: a "
            "one-entry override set (clause B2) and the empty set (clause B1). "
            "It must verify: if the spec were unsatisfiable at exactly the "
            "ordinary inputs the tests exercise, that is the analogue of "
            "PRECOND-TOO-STRONG. Nothing is assumed — no new declaration, "
            "statement byte-identical, no assumption token. Ports the sibling's "
            "admiss-effective-normal-input, widened by audit to cover the first "
            "obligation, which the port left untouched by this lane."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each shares the frozen spec, must be
    # REJECTED, and carries a witness pinning the violation at one concrete
    # input plus the refinement argument that its faithful real counterpart
    # would not make the F2P tests pass.
    # =====================================================================

    # ---- A1, sub-domain "supplied but empty": the pre-fix behaviour ----------
    {
        "id": "weak-supplied-empty-not-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the not-present arm entirely: a supplied-but-empty override is
        # passed through as a present-but-empty override instead of becoming
        # absent. Correct on the absent and non-empty sub-domains.
        "module": _swap(
            _BASE, _I_RESOLVE,
            "  if envIsSet env then\n"
            "    env := some (combineEnv osEnviron (env.getD []))\n"),
        "refinement": (
            "this is the pre-fix behaviour of the first modeled site: only the "
            "present case was normalized, so a supplied-but-empty override "
            "reached the child as an empty environment instead of letting it "
            "inherit the ambient one. The F2P case that exercises the child "
            "spawn asserts that an absent environment is handed over for BOTH an "
            "absent and an empty override; a present-but-empty value is not that "
            "value, so the faithful patch does NOT resolve."),
        "rationale": (
            "REJECT from clause A1 at env = some []: the presence predicate is "
            "false there, so the spec pins result = none, but the rival leaves "
            "the supplied empty override untouched and returns a present one. "
            "Refuted at the point (osEnviron = [], env = some []), which is the "
            "empty-override sub-domain of A1 — the sub-domain the companion "
            "rival weak-absent-overlaid-anyway does NOT reach."),
        "witness": (
            "example : ¬ problem_spec_runshell_env [] (some [])\n"
            "    (implementation_runshell_env [] (some [])) := by\n"
            "  unfold problem_spec_runshell_env implementation_runshell_env\n"
            "  rintro ⟨habsent, -⟩\n"
            "  simp [envIsSet, Id.run] at habsent\n"),
    },

    # ---- A1, sub-domain "absent": overlay even when nothing was supplied ----
    {
        "id": "weak-absent-overlaid-anyway",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong ONLY where the override is absent: treat it as an empty override
        # and overlay anyway, so the ambient environment is materialised instead
        # of being inherited. Correct on `some []` and on every non-empty input.
        "module": _swap(
            _BASE, _I_RESOLVE,
            "  if env.isNone then\n"
            "    env := some (combineEnv osEnviron [])\n"
            "  else if envIsSet env then\n"
            "    env := some (combineEnv osEnviron (env.getD []))\n"
            "  else\n"
            "    env := none\n"),
        "refinement": (
            "a faithful counterpart substitutes an empty override set for a "
            "missing one and always overlays, so the resolved environment is a "
            "materialised copy of the ambient environment rather than the "
            "'absent' value that makes the child inherit it. The F2P case for "
            "the child spawn asserts the absent value is handed over when no "
            "override is supplied; a concrete mapping is not that value, so the "
            "faithful patch does NOT resolve. (It also loses the inherit-by-"
            "reference behaviour for anything the ambient environment gains "
            "between resolution and spawn.)"),
        "rationale": (
            "REJECT from clause A1 at env = none: the presence predicate is "
            "false, so the spec pins result = none, but the rival returns an "
            "overlay. The refutation needs nothing about the overlay's VALUE — "
            "the some/none shape of the result is transparent — so it is decided "
            "at the literal point (osEnviron = [(\"A\", \"1\")], env = none). "
            "This is the OTHER sub-domain of A1: the rival agrees with the "
            "frozen behaviour at env = some [] and on every non-empty override, "
            "so it is a strict near-miss of weak-supplied-empty-not-absent and "
            "is refuted at its own distinguishing input."),
        "witness": (
            "example : ¬ problem_spec_runshell_env [(\"A\", \"1\")] none\n"
            "    (implementation_runshell_env [(\"A\", \"1\")] none) := by\n"
            "  unfold problem_spec_runshell_env implementation_runshell_env\n"
            "  rintro ⟨habsent, -⟩\n"
            "  simp [envIsSet, Id.run] at habsent\n"),
    },

    # ---- A2: the two environments overlaid in the wrong order ---------------
    {
        "id": "weak-overlay-args-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Overlay the ambient environment ONTO the overrides instead of the
        # other way round, so on a shared name the ambient value wins.
        "module": _swap(
            _BASE, _I_OVERLAY,
            "    env := some (combineEnv (env.getD []) osEnviron)\n"),
        "refinement": (
            "the overlay is applied in the wrong direction, so on a name present "
            "in both the ambient environment and the per-command overrides the "
            "ambient value wins and the override is silently discarded. A "
            "faithful counterpart hands the child an inherited value where the "
            "command's own setting was required — a real behavioural regression "
            "at the child-spawn site. HONEST LIMIT, corrected by audit: this "
            "clause describes UNCHANGED behaviour (the overlay is pre-existing "
            "on the present-override path), and the F2P case that exercises the "
            "child spawn drives it only where the override is not present, so it "
            "never reaches the overlay at all. A faithful counterpart of THIS "
            "rival would therefore most likely still make the F2P set pass. The "
            "case is retained deliberately: clause A2 is a load-bearing part of "
            "the frozen spec and must be attacked, and a rival that VERIFIED "
            "here would be a genuine SPEC-TOO-WEAK break regardless of the test "
            "set. What it is NOT is a verify-does-not-resolve probe, and the "
            "port's claim that it was is withdrawn."),
        "rationale": (
            "REJECT from clause A2: the spec pins "
            "result = some (combineEnv osEnviron kvs) — ambient first, overrides "
            "second — while the rival produces combineEnv kvs osEnviron. The "
            "overlay has no defining equation, so the witness CONDITIONS on the "
            "carrier rather than computing it: it assumes only that the overlay "
            "is not symmetric at one concrete pair (a name bound in both "
            "environments to different values — precisely the sub-domain where "
            "the direction is observable, and the sub-domain in which the rival "
            "is wrong). One hypothesis, about two distinct applications, so it "
            "is satisfiable. Probed at (osEnviron = [(\"A\", \"1\")], "
            "env = some [(\"A\", \"2\")]) — a shared name, unlike every other "
            "witness here. Ports the sibling's "
            "uniqueness-effective-swapped-merge."),
        # AUDIT NOTE (witness rewritten). The previous witness opened with
        #   have himpl : implementation_runshell_env … = some (combineEnv … ) := rfl
        # i.e. it RESTATED the rival's own body as its first step. That makes the
        # witness fail on the frozen solution for a purely SYNTACTIC reason —
        # measured, the gold-side error was `Type mismatch: rfl … but is expected
        # to have type implementation_runshell_env … = some (combineEnv kvs
        # osEnviron)`, an unprovable definitional claim about gold's impl, NOT a
        # report that the spec's clause holds there. A witness that fails on gold
        # because it hard-codes the rival's body discriminates the two IMPLS, not
        # the spec, and the gate cannot tell the difference. Rewritten to reduce
        # the branch generically (`simp only` on the presence predicate at this
        # literal input, no `rfl` naming any impl body). Now, against the frozen
        # solution, the same script reduces the instantiated clause to `True` and
        # the script fails for lack of anything to contradict — a semantic
        # refutation. Verified: rival exit 0, gold exit 1 (`h : True`),
        # consistency probe exit 1 (hypothesis satisfiable).
        "witness": (
            "-- The overlay has no defining equation, so nothing here computes\n"
            "-- it: the only assumption is that it is not symmetric at this one\n"
            "-- pair of arguments (a name bound in both environments to\n"
            "-- different values). That single hypothesis is satisfiable, and it\n"
            "-- is exactly the sub-domain where the rival's direction is wrong.\n"
            "-- No step mentions any implementation's body: against the frozen\n"
            "-- solution the same script reduces the clause to `True`, so the\n"
            "-- refutation is semantic rather than syntactic.\n"
            "example (hasym : combineEnv [(\"A\", \"1\")] [(\"A\", \"2\")]\n"
            "    ≠ combineEnv [(\"A\", \"2\")] [(\"A\", \"1\")]) :\n"
            "    ¬ problem_spec_runshell_env [(\"A\", \"1\")] "
            "(some [(\"A\", \"2\")])\n"
            "      (implementation_runshell_env [(\"A\", \"1\")] "
            "(some [(\"A\", \"2\")])) := by\n"
            "  unfold problem_spec_runshell_env implementation_runshell_env\n"
            "  rintro ⟨-, hpresent⟩\n"
            "  have h := hpresent [(\"A\", \"2\")] rfl (by decide)\n"
            "  simp only [Id.run, bind, pure, envIsSet, List.isEmpty_cons,\n"
            "    Bool.not_false, if_true, Option.getD_some,\n"
            "    Option.some.injEq] at h\n"
            "  exact hasym h.symm\n"),
    },

    # ---- A2: an entry the inputs never contained ----------------------------
    {
        "id": "weak-spurious-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Prepend an entry to the overlay's result: the resolved environment
        # carries a name neither input ever mentioned.
        "module": _swap(
            _BASE, _I_OVERLAY,
            "    env := some ((\"X\", \"\") :: "
            "combineEnv osEnviron (env.getD []))\n"),
        "refinement": (
            "a faithful counterpart injects a name into the resolved "
            "environment that neither the ambient environment nor the overrides "
            "contained, so the child is spawned with a variable nobody asked "
            "for — a real behavioural regression at the child-spawn site. "
            "HONEST LIMIT, corrected by audit: same as for "
            "weak-overlay-args-swapped. The F2P case that exercises the child "
            "spawn drives that site only where the override is not present, so "
            "it never reaches this branch, and a faithful counterpart of this "
            "rival would most likely still make the F2P set pass. Retained "
            "because clause A2 must be attacked and a rival that VERIFIED would "
            "be a real SPEC-TOO-WEAK break; the port's claim that the F2P "
            "equalities catch it is withdrawn."),
        "rationale": (
            "REJECT from clause A2: the spec pins result to exactly "
            "some (combineEnv osEnviron kvs), while the rival returns that "
            "overlay with one extra entry in front. Refutable WITHOUT knowing "
            "the overlay's value, because the way the overlay's result is "
            "COMBINED is transparent: x :: l ≠ l for every l, so the two sides "
            "differ by a length argument alone. Probed at the third distinct "
            "point (osEnviron = [(\"A\", \"1\"), (\"B\", \"2\")], "
            "env = some [(\"C\", \"3\")]) — the only witness with a two-entry "
            "ambient environment and with disjoint ambient/override names. "
            "Ports the sibling's uniqueness-effective-spurious-key."),
        # AUDIT NOTE (witness rewritten), same defect as
        # weak-overlay-args-swapped: the previous witness began with a `himpl …
        # := rfl` restating the RIVAL's body, so on the frozen solution it failed
        # with `Type mismatch: rfl … but is expected to have type
        # implementation_runshell_env … = some (("X", "") :: combineEnv …)` — a
        # syntactic failure about gold's impl, not evidence that the spec's clause
        # holds there. Rewritten to reduce the branch generically and close by the
        # length argument. Verified: rival exit 0, gold exit 1 with the clause
        # reduced to `h : True` (it fails BECAUSE the clause holds), no
        # consistency probe needed since the head binds nothing.
        "witness": (
            "-- Nothing here computes the overlay. `simp only` reduces the\n"
            "-- branch at this literal input (the presence predicate is\n"
            "-- decidable on it) and the contradiction is closed by the length\n"
            "-- argument x :: l ≠ l, which holds for EVERY l. No step mentions\n"
            "-- any implementation's body: against the frozen solution the same\n"
            "-- script reduces the instantiated clause to `True`, i.e. it fails\n"
            "-- there because the clause HOLDS.\n"
            "example : ¬ problem_spec_runshell_env "
            "[(\"A\", \"1\"), (\"B\", \"2\")] (some [(\"C\", \"3\")])\n"
            "    (implementation_runshell_env [(\"A\", \"1\"), (\"B\", \"2\")] "
            "(some [(\"C\", \"3\")])) := by\n"
            "  unfold problem_spec_runshell_env implementation_runshell_env\n"
            "  rintro ⟨-, hpresent⟩\n"
            "  have h := hpresent [(\"C\", \"3\")] rfl (by decide)\n"
            "  simp only [Id.run, bind, pure, envIsSet, List.isEmpty_cons,\n"
            "    Bool.not_false, if_true, Option.getD_some,\n"
            "    Option.some.injEq] at h\n"
            "  exact (List.cons_ne_self _ _) h\n"),
    },

    # ---- A2: the ambient environment dropped from the overlay ---------------
    # ADDED BY AUDIT. The three pre-existing A2 rivals attack the result's
    # some/none SHAPE, the overlay's ARGUMENT ORDER, and an EXTRA entry. None of
    # them attacks whether the ambient environment is passed at all: a rival that
    # overlays the overrides onto NOTHING keeps the argument order, adds no
    # entry, and returns the right shape, so it slips past all three. That is the
    # least-probed part of clause A2 and it is the direction in which the modeled
    # behaviour is most obviously load-bearing.
    {
        "id": "weak-ambient-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Overlay the overrides onto the EMPTY environment instead of the ambient
        # one: correct shape, correct argument order, no extra entry, but the
        # ambient environment is discarded.
        "module": _swap(
            _BASE, _I_OVERLAY,
            "    env := some (combineEnv [] (env.getD []))\n"),
        "refinement": (
            "a faithful counterpart overlays the per-command overrides onto an "
            "empty environment rather than onto the ambient one, so the child is "
            "spawned with ONLY the overrides and loses every inherited variable "
            "— PATH, HOME, the lot. HONEST LIMIT, corrected by audit: the port "
            "claimed the F2P case that exercises the child spawn asserts the "
            "ambient environment is present whenever an override is applied. It "
            "does not — that case drives the site only where the override is NOT "
            "present, so this branch is never reached, and a faithful "
            "counterpart would most likely still make the F2P set pass. "
            "Retained because clause A2 must be attacked and a rival that "
            "VERIFIED would be a real SPEC-TOO-WEAK break; the resolve claim is "
            "withdrawn."),
        "rationale": (
            "REJECT from clause A2: the spec pins "
            "result = some (combineEnv osEnviron kvs) — the AMBIENT environment "
            "as the first argument — while the rival produces "
            "combineEnv [] kvs, dropping it. This is the sub-domain of A2 that "
            "the other three A2 rivals leave unattacked: it preserves the "
            "some/none shape (unlike weak-absent-overlaid-anyway), the argument "
            "ORDER (unlike weak-overlay-args-swapped) and the entry set (unlike "
            "weak-spurious-entry), so it is a strict near-miss of all three. "
            "Like the swapped-order rival it CONDITIONS on the carrier instead "
            "of computing it: the witness assumes only that overlaying onto the "
            "empty environment differs from overlaying onto this ambient one — "
            "i.e. that the ambient argument is observable at all, which is "
            "precisely the sub-domain where discarding it is wrong. One "
            "hypothesis about two distinct applications, so it is satisfiable. "
            "Probed at (osEnviron = [(\"A\", \"1\")], env = some [(\"C\", "
            "\"3\")]) — a fifth distinct point for this obligation, and the only "
            "one pairing a one-entry ambient environment with a disjoint "
            "override."),
        "witness": (
            "-- Same technique as the swapped-order witness, for the same\n"
            "-- reason: the overlay has no defining equation, so this CONDITIONS\n"
            "-- on it rather than computing it. The single hypothesis is that\n"
            "-- overlaying onto the EMPTY ambient environment differs from\n"
            "-- overlaying onto this one — that the ambient argument is\n"
            "-- observable at all, which is exactly the sub-domain in which a\n"
            "-- rival that discards it is wrong. Satisfiable, and no step\n"
            "-- mentions any implementation's body: against the frozen solution\n"
            "-- the same script reduces the clause to `True`.\n"
            "example (hamb : combineEnv [] [(\"C\", \"3\")]\n"
            "    ≠ combineEnv [(\"A\", \"1\")] [(\"C\", \"3\")]) :\n"
            "    ¬ problem_spec_runshell_env [(\"A\", \"1\")] "
            "(some [(\"C\", \"3\")])\n"
            "      (implementation_runshell_env [(\"A\", \"1\")] "
            "(some [(\"C\", \"3\")])) := by\n"
            "  unfold problem_spec_runshell_env implementation_runshell_env\n"
            "  rintro ⟨-, hpresent⟩\n"
            "  have h := hpresent [(\"C\", \"3\")] rfl (by decide)\n"
            "  simp only [Id.run, bind, pure, envIsSet, List.isEmpty_cons,\n"
            "    Bool.not_false, if_true, Option.getD_some,\n"
            "    Option.some.injEq] at h\n"
            "  exact hamb h\n"),
    },

    # ---- B1: the assembled empty set reported as present -------------------
    {
        "id": "weak-assembled-empty-not-absent",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the assembled override set verbatim, with no empty → absent
        # normalization. Correct on every non-empty input.
        "module": _swap(_BASE, _I_REPORT, "  return some env\n"),
        "refinement": (
            "this is the pre-fix behaviour of the second modeled site: the "
            "assembled override set was reported as-is, so an empty set was "
            "reported as a present-but-empty override. The F2P cases that "
            "assemble no overrides assert the reported environment component is "
            "the absent value, not an empty mapping, so the faithful patch does "
            "NOT resolve — and, since the reported value flows into the first "
            "modeled behaviour, it is also what made the child receive an empty "
            "environment."),
        "rationale": (
            "REJECT from clause B1 at env = []: the spec pins result = none for "
            "the empty set, but the rival returns a present, empty one. Refuted "
            "at the literal input [] — fully transparent, no overlay involved. "
            "Ports the sibling's partial-domain-normalized-empty-not-none."),
        "witness": (
            "example : ¬ problem_spec_client_env [] "
            "(implementation_client_env []) := by\n"
            "  unfold problem_spec_client_env implementation_client_env\n"
            "  rintro ⟨habsent, -⟩\n"
            "  simp [Id.run] at habsent\n"),
    },

    # ---- B2: over-eager normalization swallows a real override -------------
    {
        "id": "weak-single-override-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-normalize: treat a ONE-entry override set as absent too. Correct
        # on the empty set and on every set with two or more entries.
        "module": _swap(
            _BASE, _I_REPORT,
            "  if env.length ≤ 1 then\n"
            "    return none\n"
            "  return some env\n"),
        "refinement": (
            "a faithful counterpart that normalizes any override set with fewer "
            "than two entries to the absent value silently discards a lone "
            "override, so the child never receives it. Most of the F2P cases "
            "assemble exactly ONE override from the connection settings and "
            "assert that single-entry mapping is reported; reporting the absent "
            "value instead breaks those equalities, so the faithful patch does "
            "NOT resolve."),
        "rationale": (
            "REJECT from clause B2 at env = [(\"A\", \"1\")]: the spec pins "
            "result = some env for every non-empty set, but the rival reports "
            "the absent value for a one-entry set. This is the ONLY rival "
            "attacking B2 (the sibling's rivals all leave the report-unchanged "
            "clause alone), and it is a near-miss of "
            "weak-assembled-empty-not-absent from the other side — it agrees "
            "with the frozen behaviour on the empty set and on every set of two "
            "or more entries — so it is refuted at its own distinguishing "
            "input, a second distinct probe point for this obligation."),
        "witness": (
            "example : ¬ problem_spec_client_env [(\"A\", \"1\")]\n"
            "    (implementation_client_env [(\"A\", \"1\")]) := by\n"
            "  unfold problem_spec_client_env implementation_client_env\n"
            "  rintro ⟨-, hpresent⟩\n"
            "  have h := hpresent (by decide)\n"
            "  simp [Id.run] at h\n"),
    },

    # ---- B2: an entry the assembled set never contained ---------------------
    # ADDED BY AUDIT. weak-single-override-dropped attacks clause B2 by
    # SUBTRACTION (a non-empty set reported as absent) and is the only rival on
    # that clause, so B2's other failure direction — reporting a set that is
    # non-empty and present but NOT the one assembled — was unattacked. The
    # `= some env` half of B2 is an equality on the LIST, not merely on the
    # some/none shape, and nothing in the battery exercised that half: a rival
    # that reports the right shape with an extra entry satisfies everything
    # weak-single-override-dropped tests. This is also the value-level analogue
    # of the sibling's uniqueness-effective-spurious-key at the SECOND site
    # (the port carried that attack over to the first obligation only) and of
    # the three frame-mutation cases' observable consequence — the port recorded
    # those as vacuous for the right reason (no permissions here), but their
    # value-level shadow, an entry injected into the reported set, is expressible
    # and is landed here.
    {
        "id": "weak-report-spurious-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Report the assembled set with one extra entry in front: correct
        # some/none shape on BOTH sub-domains, correct normalization of the
        # empty set, but the non-empty set is not reported unchanged.
        "module": _swap(
            _BASE, _I_REPORT,
            "  if env.isEmpty then\n"
            "    return none\n"
            "  return some ((\"Z\", \"0\") :: env)\n"),
        "refinement": (
            "a faithful counterpart injects a name into the reported override "
            "set that the builder never assembled from the connection settings, "
            "so the command is described as carrying a variable nobody asked for "
            "— and, since the reported value flows into the first modeled "
            "behaviour, the child is spawned with it too. The F2P cases assert "
            "the reported environment component equals the expected mapping "
            "exactly, entry for entry, so an extra entry breaks those "
            "equalities and the faithful patch does NOT resolve."),
        "rationale": (
            "REJECT from clause B2 at env = [(\"A\", \"1\")]: the spec pins "
            "result = some env — the SAME set, not merely a present one — while "
            "the rival returns that set with one extra entry prepended. This is "
            "B2's other failure direction: weak-single-override-dropped attacks "
            "the clause by SUBTRACTION (reporting absence for a non-empty set) "
            "and so leaves the list EQUALITY in `= some env` untested; a rival "
            "that keeps the shape and changes the value slips past it. Fully "
            "transparent (no overlay involved), so it is refuted by the length "
            "argument x :: l ≠ l at the literal input, and it agrees with the "
            "frozen behaviour on the empty set, making it a strict near-miss of "
            "weak-assembled-empty-not-absent as well."),
        # Verified by the audit that added it, with real builds: witness against
        # the rival exit 0; against the frozen solution exit 1 with
        # `Application type mismatch: the argument h has type True` — the
        # instantiated clause reduced to `True`, i.e. it fails there BECAUSE the
        # clause holds. Type-revealing forgery (`exact (h : Nat)`) confirms the
        # asymmetry is about the CLAIM and not about the script: gold prints
        # `h has type True`, the rival prints
        # `h has type [("Z", "0"), ("A", "1")] = [("A", "1")]`. Head binds
        # nothing, so no consistency probe is needed.
        "witness": (
            "-- Fully transparent: `simp only` reduces the branch at this\n"
            "-- literal input and the contradiction is closed by x :: l ≠ l,\n"
            "-- which holds for EVERY l. No step mentions any implementation's\n"
            "-- body, so against the frozen solution the same script reduces the\n"
            "-- instantiated clause to `True` and fails for lack of anything to\n"
            "-- contradict — a semantic refutation, not a tactic mismatch.\n"
            "example : ¬ problem_spec_client_env [(\"A\", \"1\")]\n"
            "    (implementation_client_env [(\"A\", \"1\")]) := by\n"
            "  unfold problem_spec_client_env implementation_client_env\n"
            "  rintro ⟨-, hpresent⟩\n"
            "  have h := hpresent (by decide)\n"
            "  simp only [Id.run, bind, pure, List.isEmpty_cons, "
            "Bool.false_eq_true,\n"
            "    if_false, Option.some.injEq] at h\n"
            "  exact (List.cons_ne_self _ _) h\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 10 SPEC cases (3
# frame/permission mutations, 2 partial-domain rivals, 2 value-uniqueness
# rivals, 2 soundness positives, 1 admissibility) plus 2 AXIOM_TESTS. This
# bundle models the SAME two behaviours, so every sibling case that attacks a
# VALUE has a counterpart; the disposition of all ten is recorded here.
#
#   sibling case                                  -> here
#   ---------------------------------------------------------------------------
#   frame-mut-normalized-write-env                -> (none) VACUOUS
#   frame-mut-effective-write-base                -> (none) VACUOUS
#   frame-mut-effective-write-env                 -> (none) VACUOUS
#   partial-domain-effective-empty-not-normalised -> weak-supplied-empty-not-absent
#   partial-domain-normalized-empty-not-none      -> weak-assembled-empty-not-absent
#   uniqueness-effective-swapped-merge            -> weak-overlay-args-swapped
#   uniqueness-effective-spurious-key             -> weak-spurious-entry
#   pos-control-normalized-reordered              -> pos-report-length-guard
#   pos-control-effective-disjunctive-guard       -> pos-resolve-match-on-option
#   admiss-effective-normal-input                 -> admiss-report-one-entry
#   (none)                                        -> weak-absent-overlaid-anyway  ADDED
#   (none)                                        -> weak-single-override-dropped ADDED
#   (none)                                        -> weak-ambient-dropped   ADDED (audit)
#   (none)                                        -> weak-report-spurious-entry
#                                                        ADDED (audit)
#   AXIOM_TESTS (2, the merge callee)             -> (none) DROPPED (G-AX's lane)
#
# VACUOUS (the three frame/permission-mutation rivals). The sibling's inputs are
#   held at a fractional permission, so a rival that WRITES to a read-only input
#   is rejected by the permission system. This carrier is referentially
#   transparent: the inputs are immutable values, there is no aliasing and no
#   read-only cell to overwrite, so the PERMISSION violation cannot be expressed
#   and no substitute for it is fabricated. Re-derived by audit, with one
#   correction: the permission violation is inexpressible, but its observable
#   CONSEQUENCE is not. Each sibling frame-mutation rival injects a key into a
#   mapping that is then reported or merged, and that value-level shadow is
#   perfectly expressible here — weak-spurious-entry already lands it for the
#   first obligation, and weak-report-spurious-entry (added by audit) lands it
#   for the second, which the port had left unattacked. So the disposition of
#   the three stays "no permission analogue", not "nothing to port".
#   (The corresponding frame DISCIPLINE is separately discharged by the spec
#   itself: both postconditions pin the result entirely, in every case, so
#   nothing is left unconstrained — machine-checked, see SPEC STRENGTH.)
# ADDED (weak-report-spurious-entry, by AUDIT). Clause B2 pins
#   result = some env — an equality on the LIST, not just on the some/none
#   shape. weak-single-override-dropped attacks it by SUBTRACTION only
#   (reporting absence for a non-empty set), so the equality half went untested
#   and a rival that keeps the shape while changing the value passed
#   unattacked. This is also the second obligation's counterpart of the
#   sibling's uniqueness-effective-spurious-key, which the port had carried over
#   to the first obligation only.
# ADDED (weak-absent-overlaid-anyway). Clause A1 covers two sub-domains — the
#   override absent and the override supplied-but-empty — and the sibling's
#   partial-domain rival is wrong on only the second. A rival wrong on only the
#   FIRST would otherwise never be attacked, which is exactly the shape of an
#   unprobed binder value.
# ADDED (weak-ambient-dropped, by AUDIT). The other three A2 rivals attack the
#   result's SHAPE, the overlay's argument ORDER and an EXTRA entry; a rival that
#   overlays onto the empty environment instead of the ambient one keeps all
#   three of those correct and so passed unattacked. It is the least-probed
#   direction of A2 and the one whose faithful counterpart is most plainly
#   test-breaking (the child loses every inherited variable).
# ADDED (weak-single-override-dropped). None of the sibling's rivals attacks the
#   report-unchanged clause B2: all of them keep the non-empty case correct. This
#   backend's coverage requirement is that every top-level clause is attacked, so
#   this rival over-normalizes a one-entry set. It is not fabricated for an
#   unmodeled behaviour — it attacks a load-bearing clause of the same spec, and
#   its faithful counterpart plainly fails the tests that assemble one override.
# DIVERGENCE lane: the sibling carries NO diverge-* / nonterm-* / weak-diverge
#   case, so there is nothing to port. Had it carried one, the class would be
#   vacuous on this backend anyway: both implementation_* are total Lean `def`s,
#   so a non-terminating implementation cannot be written at all (contrast the
#   velvet `partial` semantics recorded in the corpus-wide termination-semantics finding, where the
#   same rival is a genuine SPEC HOLE rather than an inexpressible one).
#
# POINT SPREAD. Eight reject witnesses over two obligations.
#   correct_runshell_env  (osEnviron, env), 5 distinct points:
#     ([], some [])                                weak-supplied-empty-not-absent  A1
#     ([("A","1")], none)                          weak-absent-overlaid-anyway     A1
#     ([("A","1")], some [("A","2")])              weak-overlay-args-swapped       A2
#     ([("A","1")], some [("C","3")])              weak-ambient-dropped            A2
#     ([("A","1"),("B","2")], some [("C","3")])    weak-spurious-entry             A2
#   osEnviron takes 3 distinct values (empty, one entry, two entries) and env
#   takes 4 (absent, supplied-empty, a name shared with the ambient environment,
#   a name disjoint from it), so neither binder is pinned and both sub-domains of
#   A1 are probed. The variation is MEANINGFUL, not two spellings of one point:
#   each of the five runshell points is the input at which exactly one rival
#   diverges from the frozen behaviour while the other four agree with it, and
#   the frozen solution is machine-checked to SATISFY the spec at all five
#   (`correct_runshell_env` instantiated at each — exit 0).
#   correct_client_env  (env), 2 distinct points, 3 rivals:
#     []                                           weak-assembled-empty-not-absent B1
#     [("A","1")]                                  weak-single-override-dropped    B2
#     [("A","1")]                                  weak-report-spurious-entry      B2
#   The two B2 rivals share a probe point deliberately, and that is the point:
#   they attack OPPOSITE failure directions of the same clause at the same input
#   — one reports absence where a value is required, the other reports a value
#   that is not the required one — so the shared input is not two spellings of
#   one probe. B2's binder has only two meaningful values here (empty and
#   non-empty), so distinctness of the clause's two directions, not of the
#   input, is what makes the second rival non-redundant.
#
# AXIOM_TESTS: dropped, per the porting map — the axiom lane is G-AX's job and
# this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
