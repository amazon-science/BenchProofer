"""properties.py — G-PBT falsification battery for django__django-11333 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The two batteries look
very different because the two carriers do. The nagini bundle contracts a single
``get_resolver(cache, selector, cached, existing, fresh)`` in which the memoized
factory is modeled DEEPLY as a mutable ``Dict`` lookup-or-insert, with explicit
pre-state scalars (``existing`` = the already-cached object, ``fresh`` = the
freshly-built one) and a full-permission cache the impl mutates. Its defended
surface has SIX postcondition clauses (resolved slot present; return the slot's
object; HIT reuses; MISS builds fresh; distinctness of other slots; cache only
grows) plus four preconditions anchoring the memo on the genuine entry state.

This Lean bundle models only the purely-functional core. The memoization is not
a mutable dictionary here; it is captured by the factory being an ordinary
(referentially transparent) function ``buildArtifact : Option String →
Artifact`` — asking it about equal keys yields the identical artifact by
construction, so no cache state, no HIT/MISS scalars, and no ``existing``/
``fresh`` distinction exist to model. The entire observable behavior collapses to
ONE clause over TWO binders: normalise the effective configuration key (the
explicit one when given, the default one when omitted) and present it to the
factory —

    result = buildArtifact (some (config.getD defaultConfig))

so ``config : Option String`` and ``defaultConfig : String`` are the only inputs,
and there is a single ``theorem correct_cachedLookup``. Every nagini clause that
lived on the mutable cache therefore has NO counterpart here; the mapping of each
nagini case to its Lean port (or its principled omission) is the NAGINI CASE
MAPPING table at the bottom of this docstring.

(AUDIT REPAIR: this sentence previously pointed at a module ``assessment`` that
does not exist anywhere in this bundle — a dangling promise of exactly the
per-case omission accounting the reader needs. The table now discharges it in
place, with the mechanical reason each dropped case is inexpressible here.)

DEFENDED SURFACE (one modeled behavior, one clause). The result is fully pinned
to the factory applied to the NORMALISED key ``some (config.getD defaultConfig)``.
There are no independent top-level conjuncts to attack separately, but the clause
still has two separable parts — WHICH key is presented, and that the result IS
the factory's artifact at that key — and the reject rivals attack both. The key
selection ``config.getD defaultConfig`` has two arms:

  * the OMITTED arm (``config = none`` ⇒ the default is meant): the actual bug.
    A rival that keys the factory on the raw argument leaves the omitted lookup
    pinned to a DIFFERENT factory application than the explicit-default lookup;
  * the EXPLICIT arm (``config = some s`` ⇒ ``s`` is meant): a rival that ignores
    the supplied configuration and always uses the default collapses distinct
    configurations onto one artifact. Attacked twice, at a whole-arm miss and at
    a NEAR-MISS (``config = some ""``, where a rival that tests emptiness rather
    than absence over-normalises — ``getD`` inspects presence only);

and the PIN itself is attacked by a rival that normalises the key exactly like
gold and then returns a self-built handle instead of the factory's artifact
(``weak-unpinned-artifact``), which is the conjunct an arm-selection rival
cannot reach. Both of the latter two rivals were added by the AUDIT; the ported
battery attacked only the arm selection.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini "over-construct into an
    occupied slot" analogue (its rival-overwrite-on-hit) is expressible only
    where the cache is a mutable object; here the cache is the transparent
    factory and there is no slot to overwrite. No substitute is fabricated.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs (``buildArtifact``
    applied to the normalised key). ``buildArtifact`` is an ``opaque`` carrier
    for an UNCHANGED platform factory — NOT an answer key for the modeled
    decision. The impl still has to compute the normalised key and present it.
    In its place the battery carries honest cheapest-implementation POSITIVE
    CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. The two rivals are each correct on part of
    the domain and wrong exactly on one arm of the normalisation.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet refuting the spec predicate at one concrete
input, checked to HOLD of its rival and to FAIL on the frozen solution.

CONDITIONING ON THE CARRIER. ``buildArtifact`` is ``opaque``, so no literal input
makes the spec ``decide``-able: ``buildArtifact none`` and ``buildArtifact (some
"root")`` are distinct terms with no computable value. The refutation is stated
at a point described by hypothesis — one weak, satisfiable disequality about the
factory at the two keys the rival conflates — and reads: whenever the factory
distinguishes those two keys, the rival's answer differs from the spec's. That is
exactly the sub-domain where the rival is wrong. Each witness carries a SINGLE
hypothesis (two distinct opaque applications assumed unequal), so the assumptions
are jointly satisfiable and the consistency probe cannot derive ``False`` from
them.

WITNESS SUBJECT — why every reject case names a ``witness_reference``
(AUDIT REPAIR; the original port refuted each witness against the FROZEN impl,
and that half of the discrimination check carried no information).

The frozen impl is spelled ``Id.run do`` with a mutable local and an ``if``.
That elaborates to a join-point term —

    have key := none;
    have __do_jp := fun key y => pure (buildArtifact key);
    if key = none then have key := some "root"; ... else ...

— which ``simp only [Id.run, pure]`` does NOT normalise. So a witness refuted
against the frozen impl fails with a TYPE MISMATCH against that unreduced
``do`` block, not because the frozen impl satisfies the spec at that input. The
failure is syntactic, and it does not track what the witness CLAIMS. Measured,
with the real verifier, on the shape the original port shipped:

  * A FORGERY asserting the exact OPPOSITE of a refutation — that the rival is
    CORRECT at an agreement point, e.g. ``problem_spec_cachedLookup (some "A")
    "B" (implementation_cachedLookup (some "A") "B")`` with no ``¬`` and no
    binders at all — elaborates against the raw-key rival (exit 0) and FAILS
    against the frozen impl (exit 1, ``unsolved goals ⊢ (if some "A" = none
    then do PUnit.unit ...) = buildArtifact (some "A")``). Both halves of the
    gate's discrimination check pass, and because the forgery binds nothing the
    consistency probe is never even run. It would have been recorded as
    ``rejected (witness refutes the rival)``. The same forgery works against
    the always-default rival at ITS agreement point (rival 0, frozen 1).
  * Conversely a wrong impl written in the frozen impl's own ``mut``/``if``
    shape — ``if key = none then key := none`` — ACCEPTS the shipped raw-key
    witness (exit 0), confirming what the witness build actually keys on is the
    impl's syntactic form.

So against the frozen impl the exit code was an artefact of the spelling. The
repair points the second build at ``_REF_REDUCING``: the same behavior with no
``mut`` and no ``if``, which reduces completely. There the exit code tracks the
claim, which is the property that makes it evidence:

    refutation (¬ …) against the reference   -> FAILS (exit 1), and the residual
        goal is ``¬True`` — i.e. ``simp`` PROVED the spec equation for that impl
    the same claim with the ``¬`` dropped     -> SUCCEEDS (exit 0)

and the flipped claim's success is exactly what kills the forgery above: an
anti-refutation now also holds of the reference, so the gate records
``witness-vacuous`` instead of a pass. The reference is not trusted on this
file's word — the gate re-checks that it shares the frozen spec and that it
VERIFIES, and an impl the verifier accepts cannot violate its own spec, so a
genuine witness must still fail against it.

BINDER / POINT SPREAD. The reject witnesses move BOTH spec binders rather than
fixing either at one convenient point: ``config`` takes ``none`` (omitted arm),
``some "A"`` (explicit arm) and ``some ""`` (the near-miss); ``defaultConfig``
takes ``"root"`` and ``"B"``. Each rival is refuted at the input it actually
mishandles, and the four reject cases visit three distinct points.

A caution the audit measured, recorded because a clean-looking spread can still
be weak here: on this carrier the binder VALUES are nearly inert. ``buildArtifact``
is opaque and ``getD`` inspects only presence, so what makes an input
discriminating is never the particular string — ``"root"`` versus ``"B"`` versus
``""`` changes no verdict by itself — but only whether ``config`` is ``none`` or
``some``, and whether the string presented differs from the one the spec
requires. So the meaningful spread is: omitted-vs-explicit (both covered), and
key-selection-vs-pin (both covered, the latter only after the audit's addition).
Two spellings of the same arm would look like spread and add nothing.

AXIOM lane: EMPTY here. The bundle declares one ``opaque`` leaf (the unchanged
platform factory) validated executably by G-AX (an A-reference), and consumes no
``axiom``. The axiom lane belongs to G-AX; this gate ignores it, and the nagini
``AXIOM_TESTS`` (also empty there) are dropped.

NAGINI CASE MAPPING (every nagini SPEC_TESTS case, ported or dropped). The
nagini obligation binds five inputs (``cache, selector, cached, existing,
fresh``); this one binds two (``config, defaultConfig``). A rival that attacks a
clause living on the mutable cache or on the ``existing``/``fresh`` pre-state
scalars has no impl-region spelling here, because those binders do not exist —
and INTRODUCING one means rewriting the ``theorem correct_cachedLookup``
statement, which ``variant_scope`` refuses. That refusal is the mechanical
demonstration, not an appeal to difficulty; each entry below names the binder it
would need.

  * ``pos-control-merge-tail``  -> PORTED as ``pos-branch-on-config``. Nagini's
    single-return control reshape becomes the per-arm ``match`` reshape (the
    control-shape axis that survives the collapse to a pure function).
  * ``pos-control-tmp-local``   -> PORTED as ``pos-key-staged-in-local``. Same
    local-staging axis. Doubles as this battery's reducing witness reference.
  * ``admiss-omitted-empty-cache`` -> PORTED as ``admiss-omitted-config``. The
    nagini probe establishes ``Requires`` on a fresh ``{}``; the frozen
    obligation here has no precondition binder to admit, so the total-carrier
    analogue is taken instead: discharge the obligation BY EVALUATION at the
    F2P-shaped omitted-configuration input as a ``have``, then close the frozen
    obligation verbatim. Non-vacuity is real, not decorative — the audit
    measured that ground instance passing by ``rfl`` against gold and FAILING
    against two of this battery's own rivals, so it is discriminating rather
    than trivially true.
  * ``rival-raw-key``           -> PORTED as ``weak-raw-key``. The one nagini
    rival whose clause survives the collapse: it attacks WHICH key reaches the
    factory, which is the whole modeled behavior here.
  * ``rival-overwrite-on-hit``  -> DROPPED, inexpressible. Needs the memo to be
    a MUTABLE object so "re-store into an occupied slot" is a distinct act from
    "read it"; needs the ``cached``/``existing`` pre-state scalars its rejection
    clause (nagini P3) is gated on. Here the memo is a referentially transparent
    function, so re-presenting the same key IS the cached artifact by
    construction and the over-construct is not a writable behavior. Adding a
    cache binder rewrites the obligation statement (``variant_scope``:
    "obligation statement was rewritten"). The PIN axis this rival morally
    guards — "the result is the factory's artifact at all" — is instead covered
    by ``weak-unpinned-artifact``, which needs no new binder.
  * ``rival-miss-returns-existing`` -> DROPPED, inexpressible. Its rejection
    clause is nagini P4, quantified over the ``existing``/``fresh`` pre-state
    scalars that model "the already-cached object" versus "the freshly-built
    one". That HIT/MISS distinction does not exist on a transparent factory (no
    call is a miss), and both scalars would have to be added to the statement.
  * ``rival-corrupt-other-key`` -> DROPPED, inexpressible. Its rejection clause
    is nagini P5, a frame condition ``∀ k ≠ resolved, cache[k] = Old(cache[k])``
    over a mutable map's OTHER slots. There is no map, no ``Old``, and no other
    slot: the result is a single ``Artifact``. A ``cache`` binder would be
    required and is refused for the same reason.

None of the three drops is a proof-difficulty concession: each names a specific
missing binder, and the frozen statement is the artifact that may not be edited
in this lane.
"""
from pathlib import Path

INSTANCE = "django__django-11333"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The whole gold impl body, strictly INSIDE the impl region.
_GOLD_BODY = (
    "  let mut key := config\n"
    "  if key = none then\n"
    "    key := some defaultConfig\n"
    "  return buildArtifact key\n"
)

# The first tactic line of the frozen proof body (inside the proof region).
_P_INTRO = "  intro config defaultConfig\n"

# ---- the reducing reference subject for every reject case's witness ---------
# AUDIT REPAIR (see the WITNESS SUBJECT note in the module docstring). The
# frozen impl is written in `Id.run do` with a mutable local and an `if`, which
# elaborates to a `have key := ...; have __do_jp := fun key y => ...` join-point
# term. `simp only [Id.run, pure]` does NOT normalise that term, so a witness
# refuted against the frozen impl fails by SYNTACTIC mismatch on an unreduced
# `do` block rather than because the frozen impl satisfies the spec there. That
# failure does not track the claim, so it is not admissible evidence.
#
# This impl computes the same normalised key with no `mut` and no `if`, so it
# reduces completely: `simp only [Id.run, pure]` closes the spec equation and
# the witness's remaining goal becomes `¬True` — the signature of a real
# refutation. It shares the frozen spec byte-for-byte and it VERIFIES (it is
# `pos-key-staged-in-local`'s module), which is what the gate independently
# re-checks before accepting it as a witness subject: an impl the verifier
# accepts cannot violate its own spec, so a genuine witness must still fail
# against it.
_REF_REDUCING = _swap(
    _BASE, _GOLD_BODY,
    "  let key := some (config.getD defaultConfig)\n"
    "  let art := buildArtifact key\n"
    "  return art\n",
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem STATEMENT byte-identical; the reshapes preserve the
    # definitional form so the frozen tactic body (`cases config`; `rfl` each
    # arm) still closes — no helper lemma, no axiom, no assumption token.
    #
    # Ports nagini's two soundness positives (pos-control-merge-tail,
    # pos-control-tmp-local): a single-return control reshape and a
    # local-staging reshape of the same behavior.
    # =====================================================================
    {
        "id": "pos-branch-on-config",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: branch on `config` directly and
        # present the effective key per arm, rather than mutating a local key
        # through an `if`. Same value flows into the factory on every input, so
        # `result = buildArtifact (some (config.getD defaultConfig))` still holds
        # and the frozen `cases config`/`rfl` proof closes definitionally.
        "module": _swap(
            _BASE, _GOLD_BODY,
            "  match config with\n"
            "  | some s => return buildArtifact (some s)\n"
            "  | none => return buildArtifact (some defaultConfig)\n",
        ),
        "rationale": "the single modeled clause is reshaped by branching on "
                     "`config` and presenting the effective key per arm (explicit "
                     "arm uses the supplied value, omitted arm uses the default), "
                     "instead of mutating a local through an `if`. The factory "
                     "argument is identical on every input, so `result = "
                     "buildArtifact (some (config.getD defaultConfig))` still "
                     "holds. Must verify, else the clause is SPEC-TOO-STRONG "
                     "(over-fit to the mutate-local control shape). Proof: frozen "
                     "tactic body retained (`cases config`; each arm `rfl`). Ports "
                     "nagini's single-return control reshape.",
    },
    {
        "id": "pos-key-staged-in-local",
        "kind": "soundness",
        "expect": "verify",
        # Structurally-different but CORRECT: stage the normalised key and the
        # produced artifact through immutable locals, then return the artifact.
        # Same behaviour; the locals zeta-reduce so the frozen `rfl` still closes.
        "module": _swap(
            _BASE, _GOLD_BODY,
            "  let key := some (config.getD defaultConfig)\n"
            "  let art := buildArtifact key\n"
            "  return art\n",
        ),
        "rationale": "a correct impl that stages the normalised key and the "
                     "produced artifact through immutable locals (local-variable "
                     "reshape) must verify; if not, the spec is over-fit to the "
                     "mutate-local spelling => SPEC-TOO-STRONG. Doubles as the "
                     "cheapest-honest control: the spec is GROUNDED (no answer key "
                     "to echo), so this honest impl IS the cheapest verifier. "
                     "Proof: frozen tactic body retained (the locals zeta-reduce, "
                     "each `cases` arm `rfl`). Ports nagini's local-staging "
                     "positive.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input rather than only in the
    # abstract. The frozen theorem carries NO precondition hypothesis (the
    # modeled behavior is total, so `∀` is unguarded), so nagini's
    # precondition-admission probe (admiss-omitted-empty-cache) has no binder to
    # attack here; the honest analogue discharges the spec predicate at the
    # ground omitted-configuration input (the F2P's no-argument call) by `rfl`
    # alongside the frozen obligation. Ports nagini's admissibility case.
    # =====================================================================
    {
        "id": "admiss-omitted-config",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped omitted-configuration input
        # (`config = none`, an arbitrary default) by `rfl` in a `have`, then close
        # the frozen obligation verbatim. Nothing is assumed: no new declaration,
        # statement byte-identical, ground instance is a `have` in the tactic body.
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_cachedLookup none \"root\"\n"
            "      (implementation_cachedLookup none \"root\") := rfl\n"
            "  intro config defaultConfig\n",
        ),
        "rationale": "the obligation is discharged at a ground omitted-"
                     "configuration input (the F2P scenario: the no-argument "
                     "lookup, whose effective key is the default) by `rfl`, then "
                     "the frozen obligation is closed verbatim. Verifies (else the "
                     "modeled behavior is unsatisfiable at exactly the input the "
                     "F2P exercises — the analogue of PRECOND-TOO-STRONG). Nothing "
                     "is assumed: no new declaration, the theorem statement is "
                     "byte-identical, and the ground instance is a `have` inside "
                     "the existing tactic body. Ports nagini's admissibility "
                     "probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement argument
    # that its faithful real patch would NOT resolve the F2P, so a verifying
    # rival would be a true verify-does-not-imply-resolve break, and (b) a
    # refutation witness conditioning on the opaque factory at one concrete input.
    # =====================================================================

    # ---- the bug itself: key the factory on the RAW argument (omitted arm) ----
    {
        "id": "weak-raw-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: present the factory the RAW argument without
        # normalising the omitted configuration to the default. For the omitted
        # lookup the key is `none`, a DIFFERENT factory application than the
        # explicit-default lookup, so the two do not coincide.
        "module": _swap(
            _BASE, _GOLD_BODY,
            "  return buildArtifact config\n",
        ),
        "refinement": "this IS the pre-fix behavior: memoise on the raw argument "
                      "rather than the normalised effective key. The omitted "
                      "lookup lands in the `none`-keyed slot while the "
                      "explicit-default lookup lands in the default-keyed slot, so "
                      "the two build and store DISTINCT artifacts even though both "
                      "denote the identical effective configuration. The F2P "
                      "asserts the omitted and explicit-default lookups return the "
                      "IDENTICAL object, so the faithful real patch (the pre-patch "
                      "raw-keyed memoization) would NOT resolve.",
        "rationale": "REJECT from the single modeled clause on its OMITTED arm: "
                     "with `config = none` the spec pins the result to "
                     "`buildArtifact (some defaultConfig)` while the rival returns "
                     "`buildArtifact none`, distinct opaque applications. Binder "
                     "spread: config=none (omitted arm), defaultConfig=\"root\". "
                     "If it verified => SPEC-TOO-WEAK (the omitted lookup is not "
                     "pinned to the default — the exact bug).",
        "witness": (
            "-- Refuted at the omitted lookup. `buildArtifact` is opaque, so no\n"
            "-- literal input decides the goal; condition on the factory instead.\n"
            "-- The single hypothesis is satisfiable (two distinct keys may map to\n"
            "-- distinct artifacts) and states exactly the sub-domain where the\n"
            "-- rival is wrong: whenever the factory distinguishes the `none` slot\n"
            "-- from the default slot, the rival's answer differs from the spec's.\n"
            "example (h : buildArtifact none ≠ buildArtifact (some \"root\")) :\n"
            "    ¬ problem_spec_cachedLookup none \"root\"\n"
            "        (implementation_cachedLookup none \"root\") := by\n"
            "  unfold problem_spec_cachedLookup implementation_cachedLookup\n"
            "  simp only [Id.run, pure]\n"
            "  exact h\n"
        ),
        # AUDIT REPAIR: refute against the REDUCING reference, not the frozen
        # impl. Against the frozen `mut`/`if` spelling this witness failed by
        # type mismatch on an unreduced `do` block — a failure that does NOT
        # track the claim (a forgery asserting the rival is CORRECT at an
        # agreement point failed there identically, so it would have passed the
        # gate). Against the reference the refutation fails with residual goal
        # `¬True` (simp PROVED the spec equation) while the same claim without
        # the `¬` succeeds. See the WITNESS SUBJECT note in the docstring.
        "witness_reference": _REF_REDUCING,
    },

    # ---- ignore the supplied configuration (explicit arm) ----
    {
        "id": "weak-always-default",
        "kind": "uniqueness",
        "expect": "reject",
        # A partial-domain miss on the OTHER arm: normalise EVERY lookup to the
        # default, ignoring an explicitly supplied configuration. Correct on the
        # omitted arm, wrong whenever a configuration is actually given.
        "module": _swap(
            _BASE, _GOLD_BODY,
            "  let mut key := config\n"
            "  key := some defaultConfig\n"
            "  return buildArtifact key\n",
        ),
        "refinement": "a faithful real patch that always presented the factory the "
                      "default configuration — ignoring an explicitly supplied one "
                      "— would collapse every lookup onto the single "
                      "default-keyed artifact. A lookup naming a DIFFERENT "
                      "configuration would then return the same object as the "
                      "no-argument lookup, so the F2P's assertion that distinct "
                      "configurations yield DISTINCT objects breaks. It would NOT "
                      "resolve.",
        "rationale": "REJECT from the single modeled clause on its EXPLICIT arm: "
                     "with `config = some \"A\"` the spec pins the result to "
                     "`buildArtifact (some \"A\")` while the rival returns "
                     "`buildArtifact (some defaultConfig)` = `buildArtifact (some "
                     "\"B\")`, distinct opaque applications. Binder spread: "
                     "config=some \"A\" (explicit arm), defaultConfig=\"B\" — an "
                     "input DISTINCT from the raw-key rival so the two probe their "
                     "own points. If it verified => SPEC-TOO-WEAK (the explicit "
                     "configuration is not pinned).",
        "witness": (
            "-- Refuted at an explicit lookup, a point distinct from the raw-key\n"
            "-- rival. Single satisfiable hypothesis over the opaque factory: the\n"
            "-- explicit key and the default key may map to distinct artifacts.\n"
            "example (h : buildArtifact (some \"B\") ≠ buildArtifact (some \"A\")) :\n"
            "    ¬ problem_spec_cachedLookup (some \"A\") \"B\"\n"
            "        (implementation_cachedLookup (some \"A\") \"B\") := by\n"
            "  unfold problem_spec_cachedLookup implementation_cachedLookup\n"
            "  simp only [Id.run, pure, Option.getD_some]\n"
            "  exact h\n"
        ),
        # AUDIT REPAIR — same reason as `weak-raw-key`. The forgery measured
        # against the frozen impl for THIS rival was the anti-refutation at its
        # own agreement point (the omitted arm): rival exit 0, frozen exit 1.
        "witness_reference": _REF_REDUCING,
    },

    # ---- ignore the DEFAULT and pin every lookup to one fixed key ----
    # AUDIT ADDITION (attack D). The two ported rivals both attack the CHOICE
    # between the two arms of `config.getD defaultConfig`; neither attacks the
    # `buildArtifact` application itself, so nothing in the ported battery
    # falsified "the result is the factory's artifact at all". This rival
    # normalises the key exactly like gold, then discards it and returns a
    # freshly-constructed handle — the artifact is not the memoized factory's
    # at all. Confirmed to be REJECTED, with a witness that discriminates
    # against the reducing reference.
    {
        "id": "weak-unpinned-artifact",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "  let _key := some (config.getD defaultConfig)\n"
            "  return { handle := 0 }\n",
        ),
        "refinement": "a faithful real patch of this shape would compute the "
                      "effective configuration correctly and then hand back a "
                      "NEWLY constructed artifact instead of the memoized "
                      "factory's, on every call. Two lookups naming the same "
                      "configuration would then return two DISTINCT objects, so "
                      "the F2P's assertion that the omitted and explicit-default "
                      "lookups return the IDENTICAL object breaks — and so does "
                      "the identity of a repeated lookup. It would NOT resolve; "
                      "it defeats the memoization entirely rather than mis-keying "
                      "it.",
        "rationale": "REJECT from the single modeled clause's PIN, not from its "
                     "arm selection: the spec requires the result to BE "
                     "`buildArtifact (some (config.getD defaultConfig))`, and a "
                     "self-built handle is not that opaque application at any "
                     "input. Attacks the conjunct the other two rivals leave "
                     "unprobed (they both invoke the factory and differ only in "
                     "the key). Binder spread: config=none, defaultConfig="
                     "\"root\". If it verified => SPEC-TOO-WEAK (the result is "
                     "not actually pinned to the factory).",
        "witness": (
            "-- Refuted at the omitted lookup. The rival's answer is a literal\n"
            "-- handle; the spec's is the opaque factory at the default key. The\n"
            "-- single hypothesis (they may differ) is satisfiable — nothing\n"
            "-- constrains an opaque application to equal a given handle — so the\n"
            "-- consistency probe cannot derive `False` from it.\n"
            "example (h : ({ handle := 0 } : Artifact) ≠ buildArtifact (some \"root\")) :\n"
            "    ¬ problem_spec_cachedLookup none \"root\"\n"
            "        (implementation_cachedLookup none \"root\") := by\n"
            "  unfold problem_spec_cachedLookup implementation_cachedLookup\n"
            "  simp only [Id.run, pure]\n"
            "  exact h\n"
        ),
        "witness_reference": _REF_REDUCING,
    },

    # ---- near-miss: treat an EMPTY explicit configuration as omitted ----
    # AUDIT ADDITION (attack D, near-miss). The ported rivals are wrong on a
    # whole arm; this one agrees with gold everywhere except the single input
    # `config = some ""`, where it over-normalises a supplied-but-empty
    # configuration to the default. It is the tightest wrong impl the spec must
    # still reject, and it probes a THIRD point (`config = some ""`) that
    # neither ported witness visits.
    {
        "id": "weak-empty-config-as-omitted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _GOLD_BODY,
            "  let mut key := config\n"
            "  if key = none || key = some \"\" then\n"
            "    key := some defaultConfig\n"
            "  return buildArtifact key\n",
        ),
        "refinement": "a faithful real patch of this shape would test the "
                      "supplied configuration for emptiness rather than for "
                      "absence, so a lookup that explicitly names the empty "
                      "configuration would be redirected to the default and "
                      "return the DEFAULT's artifact. That lookup would then "
                      "share an object with the no-argument lookup instead of "
                      "having its own, collapsing two configurations the F2P "
                      "requires to stay distinct. It would NOT resolve.",
        "rationale": "REJECT on the EXPLICIT arm at its tightest point: the "
                     "spec's effective key for `config = some \"\"` is `some "
                     "\"\"` (`getD` inspects only presence, never contents), "
                     "while the rival presents `some defaultConfig`. Agrees "
                     "with gold at EVERY other input, so it is a genuine "
                     "near-miss rather than a whole-arm miss. Binder spread: "
                     "config=some \"\", defaultConfig=\"root\" — a third point, "
                     "distinct from both ported witnesses. If it verified => "
                     "SPEC-TOO-WEAK (presence and non-emptiness conflated).",
        "witness": (
            "-- Refuted at the explicitly-empty configuration, the single input\n"
            "-- where this rival and the spec disagree. Single satisfiable\n"
            "-- hypothesis over the opaque factory at the two keys it conflates.\n"
            "example (h : buildArtifact (some \"root\") ≠ buildArtifact (some \"\")) :\n"
            "    ¬ problem_spec_cachedLookup (some \"\") \"root\"\n"
            "        (implementation_cachedLookup (some \"\") \"root\") := by\n"
            "  unfold problem_spec_cachedLookup implementation_cachedLookup\n"
            "  simp only [Id.run, pure, Option.getD_some]\n"
            "  exact h\n"
        ),
        "witness_reference": _REF_REDUCING,
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` (one `opaque` leaf, the
# unchanged platform factory, is an A-reference validated by G-AX, not a consumed
# contract). The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
