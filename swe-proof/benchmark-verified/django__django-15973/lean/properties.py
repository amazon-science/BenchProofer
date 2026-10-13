"""properties.py — G-PBT falsification battery for django__django-15973 (lean).

PORT of the nagini sibling's falsification battery to the lean carrier. NOT a
Lean file: a record of adversarial cases the G-PBT gate executes. Each SPEC case
is a full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte
(region surgery — only text inside ``-- impl-start`` / ``-- impl-end`` and, for a
case that re-proves or adds a ground instance, inside ``-- proof-start`` /
``-- proof-end`` — is changed, so ``markers.same_spec`` holds and the
``theorem correct_relationDependencies`` STATEMENT stays byte-identical).
``expect="verify"`` passes iff the file elaborates with the obligation closed;
``expect="reject"`` passes iff the variant does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution.

DEFENDED SURFACE (one total function producing the ordered dependency list a
relational field induces for its create migration):

  relationDependencies
      (targetRef : ModelRef) (throughRef : Option ModelRef)
      (swappableSetting : Option String) (scopeApp scopeName : String)
      : List (String × String)
    let firstDep := match swappableSetting with
                    | some setting => ("__setting__", setting)
                    | none         => modelRefToPair targetRef scopeApp scopeName
    result = [firstDep]                                     (no intermediary), or
    result = [firstDep, modelRefToPair thr scopeApp scopeName]  (intermediary thr)

  The spec pins the WHOLE list. Its top-level clauses (per the ``throughRef``
  match arms) fold several inseparable sub-decisions, each keyed to distinct
  binders:

    * WHICH REFERENCE feeds the resolver for the intermediary entry — it is the
      intermediary reference ``thr`` (the ``some`` binder of ``throughRef``), NOT
      the target reference. This is the load-bearing behavioural delta: the two
      coincide only when the two references resolve identically, and diverge
      otherwise. Keyed by ``targetRef`` vs ``throughRef``.
    * IN WHICH SCOPE each reference resolves — the owning model's
      ``(scopeApp, scopeName)`` supplies the scope for unscoped/recursive
      references. Keyed by ``scopeApp`` / ``scopeName``.
    * WHAT the target dependency is — the swappable ``("__setting__", setting)``
      head when a setting is present, else the resolved target. Keyed by
      ``swappableSetting``.
    * WHETHER the second entry is present at all — only when an intermediary is
      supplied. Keyed by the ``none``/``some`` shape of ``throughRef``.

  ``modelRefToPair`` (the reference→pair resolver) is deep-modeled from the
  inputs; its only abstract building block is ``lower`` (the object-name case
  fold, an ``opaque : String → String``). There is no ungrounded answer-key to
  echo. Most reject witnesses use ``ModelRef.concrete`` references — whose
  resolution touches neither ``lower`` nor ``splitFirstDot`` — so a plain
  ``decide`` closes them by evaluation. The two rivals that attack the TEXTUAL
  arms of the resolver (``weak-no-lowercase``, ``weak-split-on-last-dot``)
  necessarily use ``ModelRef.str`` and so must state the resolver's split by
  hypothesis; see their own notes for how each stays discriminating.

ADVERSARIAL READ of the nagini classes on this carrier (see 'assessment' below
for the full port ledger):

  * FRAME / PERMISSION MUTATION — VACUOUS, and demonstrated so rather than
    asserted. Nagini makes an input-write attack MANDATORY because the modeled
    references are held at fractional (read-only) permission and a rival that
    overwrites one is rejected for insufficient permission. Lean is referentially
    transparent: every input is a plain immutable value (``ModelRef`` /
    ``Option`` / ``String``), there is no half-permission to violate and no
    aliasing to exploit. The demonstration is the closest analogue this carrier
    admits: an impl that takes ``let mut`` copies of every input binder,
    clobbers all of them, and then answers from the ORIGINAL binders. It is an
    admissible variant (impl-region-only, empty scope problems) and it VERIFIES —
    the writes are unobservable to the spec, which is exactly the statement that
    the frame class has no falsifying instance here. A rival that instead answered
    FROM the clobbered copies would be rejected, but that is a value error already
    covered by the wrong-scope/wrong-reference rivals, not a frame violation. No
    substitute is fabricated for this class.

  * DIVERGENCE / NON-TERMINATION — inexpressible on this carrier, for a reason
    that is a property of the carrier and not of the bundle's semantics options.
    This solution sets no ``loom.semantics.termination`` option at all (no lean
    bundle in this corpus does): the obligation is an ordinary Lean theorem, and
    Lean's own elaborator refuses a non-terminating ``def`` outright — a
    recursive ``def spin (n : Nat) := spin (n + 1)`` fails to elaborate with
    ``fail to show termination``, so such a variant never reaches the spec at all.
    The two ways to smuggle divergence past the elaborator both fail to yield a
    shippable case: ``partial def`` is a token ``variant_scope`` bans outright,
    and a ``while true`` loop elaborates but leaves a ``forIn Lean.Loop.mk`` term
    the kernel cannot reduce, so a witness against it dies with ``decide ...
    did not reduce to isTrue or isFalse`` — the gate's own ``witness-undecided``
    screen, i.e. an inconclusive case rather than a refutation. Recorded here as a
    carrier limit, not as a spec hole: the total carrier means a diverging impl
    cannot even be WRITTEN, so there is nothing for the spec to fail to exclude.

  * PARTIAL-DOMAIN (the pre-patch bug) — APPLIES, and is the load-bearing rival.
    The pre-fix resolved the intermediary entry from the TARGET reference instead
    of the intermediary reference; it agrees with the fix only where the two
    references resolve identically and diverges elsewhere (the F2P sub-domain).

  * PARTIAL-DOMAIN, app-only mix — APPLIES. A subtler near-miss taking only the
    app-label half of the intermediary entry from the target reference; refuted
    where the two references' app labels differ.

  * NO-LOWERCASE / SPLIT-ON-LAST-DOT — EXPRESSIBLE and attacked (rivals R5, R6).
    Nagini spelled the resolver out over code points, so it could attack the
    case-fold and the dot-split rule directly. The frozen ``modelRefToPair`` (with
    ``splitFirstDot`` and ``lower``) lives in the spec's ``pure`` region and may
    NOT be edited — but a variant does not have to. The impl region is free to
    INLINE its own resolver for the intermediary entry (mirroring every arm of the
    frozen one except the case fold, resp. the split point), which edits only the
    impl and so keeps ``same_spec``. Two such rivals attack these rules:
      - ``weak-no-lowercase`` drops the object-name fold. Because ``lower`` is
        opaque, no literal input ``decide``s the divergence, so the witness names
        the fold by HYPOTHESIS (``lower n ≠ n``) and the consistency probe
        confirms that hypothesis is satisfiable — the technique that makes an
        opaque carrier attackable.
      - ``weak-split-on-last-dot`` splits on the last dot; its witness refutes on
        the APP-LABEL half, which carries no fold, so it is ``decide``-clean once
        the two concrete splits are supplied by hypothesis.
    (Earlier ports of this cell recorded these as VACUOUS/inexpressible; that was
    wrong — see the audit note. The G-AX A-reference validation of ``lower`` /
    ``resolve_relation`` remains the primary guard on fold/split correctness, but
    the PBT lane pins them here too.)

  * The lean spec additionally models behaviour nagini's did NOT: the swappable
    first-dependency, the presence/absence of the second entry, and the
    resolution scope. Those clauses get their own rivals: ignore-swappable for
    the swappable head, wrong-scope for the resolution scope, and — for the
    entry-COUNT decision, which no reshaped-value rival can reach — the pair
    ``weak-drop-through-entry`` / ``weak-always-two-entries``, which get the
    LENGTH of the list wrong in each direction (dropping the intermediary entry
    when one is supplied, and emitting a second entry when none is). An earlier
    revision of this docstring claimed the entry-count clause was covered by the
    rivals above; it was not — every one of those returns a two-element list on a
    ``some`` intermediary and a one-element list on ``none``, exactly as the spec
    requires, so they move the entry-count binder without ever discriminating on
    it. The two length rivals close that gap.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl — the frozen ``cases throughRef <;> rfl`` is tuned to the
frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a ``decide``-able concrete input; each was checked to HOLD
of its rival and to FAIL on the frozen solution (so it discriminates rather than
asserting a tautology). All witnesses use ``ModelRef.concrete`` (no ``lower``,
no ``splitFirstDot``), so ``decide`` closes without meeting the opaque fold.

BINDER COVERAGE. All five input binders are varied across the reject witnesses:
  * ``targetRef`` — moved between the prepatch/app-mix rivals and the others.
  * ``throughRef`` — ``some _`` for the intermediary rivals, ``none`` for the
    ignore-swappable rival (which needs the list to stop after the head).
  * ``swappableSetting`` — ``none`` for most, ``some _`` for the ignore-swappable
    rival (the discriminating value).
  * ``scopeApp`` / ``scopeName`` — moved by the wrong-scope rival's ``self``
    reference, whose resolution reads exactly those two binders.

AXIOM lane: EMPTY. meta.json axioms == []; the sole callee ``resolve_relation``
is a deep-model A-reference validated == the real callee by G-AX (its own gate).
The PBT axiom lane is therefore vacuous here. AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "django__django-15973"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- frozen anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_relationDependencies\n"
    "    (targetRef : ModelRef) (throughRef : Option ModelRef)\n"
    "    (swappableSetting : Option String) (scopeApp scopeName : String)\n"
    "    : List (String × String) := Id.run do\n"
    "  let firstDep : String × String :=\n"
    "    match swappableSetting with\n"
    "    | some setting => (\"__setting__\", setting)\n"
    "    | none         => modelRefToPair targetRef scopeApp scopeName\n"
    "  let mut deps : List (String × String) := [firstDep]\n"
    "  match throughRef with\n"
    "  | some thr =>\n"
    "      deps := deps ++ [modelRefToPair thr scopeApp scopeName]\n"
    "  | none => pure ()\n"
    "  return deps"
)

_PROOF_BODY = (
    "  intro targetRef throughRef swappableSetting scopeApp scopeName\n"
    "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
    "  cases throughRef <;> rfl"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival / positive impl bodies. Each is a full impl region; only the impl (and,
# for the reproven positive, the proof body) changes, so the spec and the
# theorem STATEMENT stay byte-identical.
# ---------------------------------------------------------------------------

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# direct functional expression (no `Id.run do` / `let mut`), spelling the
# presence decision as the spec's own `match throughRef`. Same value on every
# input; the frozen script still closes it (both sides reduce to the same
# match term), but the shape is genuinely different (no mutable accumulator).
_POS_IMPL = (
    "def implementation_relationDependencies\n"
    "    (targetRef : ModelRef) (throughRef : Option ModelRef)\n"
    "    (swappableSetting : Option String) (scopeApp scopeName : String)\n"
    "    : List (String × String) :=\n"
    "  let firstDep : String × String :=\n"
    "    match swappableSetting with\n"
    "    | some setting => (\"__setting__\", setting)\n"
    "    | none         => modelRefToPair targetRef scopeApp scopeName\n"
    "  match throughRef with\n"
    "  | none     => [firstDep]\n"
    "  | some thr => [firstDep, modelRefToPair thr scopeApp scopeName]"
)
_POS_PROOF = (
    "  intro targetRef throughRef swappableSetting scopeApp scopeName\n"
    "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
    "  cases throughRef <;> rfl"
)

# ADMISSIBILITY: discharge the frozen obligation AND a ground instance at the
# F2P-shaped input (a separate-apps through reference distinct from the target)
# inside the proof region, alongside the frozen tactic body verbatim.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_relationDependencies\n"
    "      (ModelRef.concrete \"testapp\" \"publisher\")\n"
    "      (some (ModelRef.concrete \"contract\" \"contract\")) none \"authors\" \"author\"\n"
    "      (implementation_relationDependencies\n"
    "        (ModelRef.concrete \"testapp\" \"publisher\")\n"
    "        (some (ModelRef.concrete \"contract\" \"contract\")) none \"authors\" \"author\") := by\n"
    "    unfold problem_spec_relationDependencies implementation_relationDependencies\n"
    "    decide\n"
    + _PROOF_BODY
)

# (R1) PARTIAL-DOMAIN — the pre-patch bug: resolve the intermediary entry from
# the TARGET reference instead of the intermediary reference.
_PREPATCH = _IMPL_GOLD.replace(
    "      deps := deps ++ [modelRefToPair thr scopeApp scopeName]",
    "      deps := deps ++ [modelRefToPair targetRef scopeApp scopeName]",
)

# (R2) PARTIAL-DOMAIN, app-only mix — take the app label of the intermediary
# entry from the target reference, the object name (correctly) from the
# intermediary. A subtler near-miss than the full prepatch bug.
_APP_MIX = _IMPL_GOLD.replace(
    "      deps := deps ++ [modelRefToPair thr scopeApp scopeName]",
    "      deps := deps ++ [((modelRefToPair targetRef scopeApp scopeName).1, "
    "(modelRefToPair thr scopeApp scopeName).2)]",
)

# (R3) IGNORE-SWAPPABLE — always resolve the target reference for the first
# dependency, never emitting the `("__setting__", setting)` head.
_IGNORE_SWAP = _IMPL_GOLD.replace(
    "  let firstDep : String × String :=\n"
    "    match swappableSetting with\n"
    "    | some setting => (\"__setting__\", setting)\n"
    "    | none         => modelRefToPair targetRef scopeApp scopeName\n",
    "  let firstDep : String × String :=\n"
    "    modelRefToPair targetRef scopeApp scopeName\n",
)

# (R4) WRONG-SCOPE — resolve the intermediary entry in a SWAPPED scope
# (scopeName as app, scopeApp as name). Diverges on any reference whose
# resolution depends on the scope (recursive `self`, bare `Object`).
_WRONG_SCOPE = _IMPL_GOLD.replace(
    "      deps := deps ++ [modelRefToPair thr scopeApp scopeName]",
    "      deps := deps ++ [modelRefToPair thr scopeName scopeApp]",
)

# (R5) NO-LOWERCASE — resolve the intermediary entry with an INLINE resolver
# that reproduces `modelRefToPair` in every arm EXCEPT it drops the object-name
# case fold (`(a, n)` instead of `(a, lower n)` on a dotted textual reference,
# `(scopeApp, s)` instead of `(scopeApp, lower s)` on a bare one). This edits
# only the impl region — it does NOT touch the frozen `modelRefToPair`/`lower`
# in the pure region — so `same_spec` holds and the case is an admissible
# variant. Its witness discriminates by CONDITIONING on `lower n ≠ n` (the
# opaque fold is stated by hypothesis, never computed), so `decide` never has to
# meet the opaque term. Agrees with gold exactly where the object name is a
# fold fixpoint; diverges otherwise.
_NO_LOWER = _IMPL_GOLD.replace(
    "      deps := deps ++ [modelRefToPair thr scopeApp scopeName]",
    "      let thrPair := match thr with\n"
    "        | .concrete a n => (a, n)\n"
    "        | .str s =>\n"
    "            if s = \"self\" then (scopeApp, scopeName)\n"
    "            else match splitFirstDot s with\n"
    "              | some (a, n) => (a, n)\n"
    "              | none        => (scopeApp, s)\n"
    "      deps := deps ++ [thrPair]",
)

# (R7) DROP-THROUGH-ENTRY — emit only the target dependency, never appending the
# intermediary entry even when an intermediary IS supplied. Attacks the entry
# COUNT (the LENGTH of the list) rather than the VALUE of any entry: every other
# rival returns a correctly-shaped two-element list on a `some` intermediary and
# gets an entry's contents wrong, so none of them discriminates on the presence
# decision itself. This one gets the length wrong in the "too short" direction.
_DROP_THROUGH = _IMPL_GOLD.replace(
    "  | some thr =>\n"
    "      deps := deps ++ [modelRefToPair thr scopeApp scopeName]\n",
    "  | some _thr => pure ()\n",
)

# (R8) ALWAYS-TWO-ENTRIES — append a second entry even when NO intermediary is
# supplied (duplicating the target dependency). The converse of R7: the length is
# wrong in the "too long" direction, on the `none` arm of `throughRef` — the arm
# whose spec clause is `result = [firstDep]`, i.e. the one that pins that the
# list STOPS after the head.
_ALWAYS_TWO = _IMPL_GOLD.replace(
    "  | none => pure ()",
    "  | none =>\n"
    "      deps := deps ++ [modelRefToPair targetRef scopeApp scopeName]",
)

# (R6) SPLIT-ON-LAST-DOT — resolve the intermediary entry with an INLINE
# resolver that splits the textual reference on its LAST dot instead of its
# first (`resolve_relation` uses `split(".", 1)` — the FIRST dot). Object name
# is (correctly) lower-cased; only the split POINT is wrong. Coincides with gold
# on single-dot references and diverges on multi-dot ones, where the app label
# and object name are cut at the wrong place. The witness discriminates on the
# APP-LABEL half, which carries NO fold (`app.split` keeps the app verbatim), so
# the refutation is fold-free and `decide`-clean once the two concrete splits
# are supplied by hypothesis.
_LAST_DOT = _IMPL_GOLD.replace(
    "      deps := deps ++ [modelRefToPair thr scopeApp scopeName]",
    "      let thrPair := match thr with\n"
    "        | .concrete a n => (a, n)\n"
    "        | .str s =>\n"
    "            if s = \"self\" then (scopeApp, scopeName)\n"
    "            else match (s.splitOn \".\").reverse with\n"
    "              | []      => (scopeApp, lower s)\n"
    "              | [_]     => (scopeApp, lower s)\n"
    "              | last :: pre => (\".\".intercalate pre.reverse, lower last)\n"
    "      deps := deps ++ [thrPair]",
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else SPEC-TOO-STRONG. Statement byte-identical; no new
    # lemma/axiom/sorry.
    # =====================================================================
    {
        "id": "pos-functional-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` and "
            "spells the whole list as one functional `match throughRef` (`none => "
            "[firstDep]`, `some thr => [firstDep, modelRefToPair thr scopeApp "
            "scopeName]`) must satisfy the frozen postcondition on every input; if "
            "it could not, the spec would be SPEC-TOO-STRONG. Both sides reduce to "
            "the same match term, so `cases throughRef <;> rfl` still closes it — "
            "no new declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the F2P-shaped input. The frozen theorem
    # carries NO precondition hypothesis (the behavior is total), so nagini's
    # precondition-admission probe has no binder to attack; the honest analogue
    # is to discharge the spec predicate at the F2P ground input inside the proof
    # region alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-separate-apps-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P ground input (target and "
            "intermediary references in DIFFERENT apps — target `testapp.publisher`, "
            "intermediary `contract.contract`, owning scope `authors`), where the "
            "spec requires a two-entry list whose SECOND entry resolves the "
            "INTERMEDIARY (`contract`) not the target, by `decide`; then the frozen "
            "obligation is closed verbatim. Verifies, else the spec is unsatisfiable "
            "at the normal input (the analogue of PRECOND-TOO-STRONG). Nothing is "
            "assumed: the theorem STATEMENT is byte-identical, the ground instance "
            "is a `have` inside the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a refutation witness
    # pinning the violation at one concrete (opaque-free) input.
    # =====================================================================
    {
        "id": "weak-through-resolves-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH),
        "refinement": (
            "this is the pre-fix behaviour verbatim: the intermediary dependency is "
            "resolved from the TARGET reference instead of the intermediary "
            "reference. Its faithful real patch is the pre-patch code. On the F2P "
            "separate-apps case the intermediary model lives in a DIFFERENT app "
            "from the target model, so the intermediary dependency would point at "
            "the wrong app and the create-migration dependency SET would not match "
            "the expected `{(authors,..),(contract,..),(testapp,..)}` — the F2P does "
            "NOT pass. This is exactly the delta the fix makes."
        ),
        "rationale": (
            "REJECT from the `some thr` clause `result = [firstDep, modelRefToPair "
            "thr scopeApp scopeName]`: the rival returns `modelRefToPair targetRef "
            "..` for the second entry, which matches only when the two references "
            "resolve identically (partial domain). Refuted with target "
            "`testapp.publisher` and intermediary `contract.contract` (distinct "
            "apps): the spec demands `(\"contract\",\"contract\")`, the rival yields "
            "`(\"testapp\",\"publisher\")`. Moves the `targetRef`/`throughRef` "
            "binders off equal values. Else SPEC-TOO-WEAK."
        ),
        "witness": (
            "-- Refuted where target and intermediary references resolve to\n"
            "-- DIFFERENT pairs: the second entry must resolve the INTERMEDIARY.\n"
            "example : ¬ problem_spec_relationDependencies\n"
            "    (ModelRef.concrete \"testapp\" \"publisher\")\n"
            "    (some (ModelRef.concrete \"contract\" \"contract\")) none \"authors\" \"author\"\n"
            "    (implementation_relationDependencies\n"
            "      (ModelRef.concrete \"testapp\" \"publisher\")\n"
            "      (some (ModelRef.concrete \"contract\" \"contract\")) none \"authors\" \"author\") := by\n"
            "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-app-from-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_APP_MIX),
        "refinement": (
            "app label of the intermediary entry taken from the target reference, "
            "object name correctly from the intermediary. On the separate-apps F2P "
            "the intermediary app label would be the target's app instead of the "
            "intermediary's, so the intermediary dependency would land in the wrong "
            "app and the dependency SET would not match — the F2P does NOT pass. "
            "Subtler than the full prepatch bug: only the app-label component of "
            "the intermediary entry is wrong."
        ),
        "rationale": (
            "REJECT from the `some thr` clause: the entry's app label must be "
            "`(modelRefToPair thr ..).1`, but the rival uses `(modelRefToPair "
            "targetRef ..).1`, violated whenever the two references' app labels "
            "differ. Refuted with target app `testapp` and intermediary app "
            "`contract` (object names deliberately EQUAL, `x`, so ONLY the app half "
            "discriminates). Else the app-label half of the spec is too weak."
        ),
        "witness": (
            "-- Refuted where the two references share an object name but differ in\n"
            "-- app: only the app-label component of the intermediary entry is wrong.\n"
            "example : ¬ problem_spec_relationDependencies\n"
            "    (ModelRef.concrete \"testapp\" \"x\")\n"
            "    (some (ModelRef.concrete \"contract\" \"x\")) none \"authors\" \"author\"\n"
            "    (implementation_relationDependencies\n"
            "      (ModelRef.concrete \"testapp\" \"x\")\n"
            "      (some (ModelRef.concrete \"contract\" \"x\")) none \"authors\" \"author\") := by\n"
            "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignore-swappable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IGNORE_SWAP),
        "refinement": (
            "the target dependency is always resolved from the target reference, "
            "never emitting the swappable `(\"__setting__\", setting)` head. A field "
            "tied to a swappable setting must depend on that SETTING, not on a "
            "concrete resolved model; the pre-existing swappable-dependency tests "
            "assert the `__setting__` head. Resolving the model instead breaks "
            "them — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the `firstDep` branch of BOTH clauses: with a swappable "
            "setting present the first entry must be `(\"__setting__\", setting)`, "
            "but the rival emits the resolved target pair. Refuted with "
            "`swappableSetting = some \"myapp.Model\"` (and `throughRef = none`, so "
            "the list stops after the head): the spec demands "
            "`[(\"__setting__\",\"myapp.Model\")]`, the rival yields the resolved "
            "target. Moves `swappableSetting` to `some _` and `throughRef` to "
            "`none`. Else the swappable clause is unpinned."
        ),
        "witness": (
            "-- Refuted where the field is tied to a swappable setting: the target\n"
            "-- head must be the setting sentinel, not a resolved model pair.\n"
            "example : ¬ problem_spec_relationDependencies\n"
            "    (ModelRef.concrete \"a\" \"b\") none (some \"myapp.Model\") \"s1\" \"s2\"\n"
            "    (implementation_relationDependencies\n"
            "      (ModelRef.concrete \"a\" \"b\") none (some \"myapp.Model\") \"s1\" \"s2\") := by\n"
            "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-wrong-scope",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WRONG_SCOPE),
        "refinement": (
            "the intermediary reference is resolved in a SWAPPED scope (the owning "
            "model's name used as the app label and vice versa). References are "
            "resolved within the owning model's scope; a recursive (`self`) or "
            "unscoped (bare) intermediary reference resolved under a swapped scope "
            "would point at a model in the wrong app, so its create-migration "
            "dependency would be wrong — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the `some thr` clause: the intermediary must resolve as "
            "`modelRefToPair thr scopeApp scopeName`, but the rival passes "
            "`scopeName scopeApp`, violated for any reference whose resolution reads "
            "the scope. Refuted with a recursive intermediary `self` and DISTINCT "
            "scope strings `scopeApp = \"app4\"`, `scopeName = \"name4\"`: the spec "
            "demands `(\"app4\",\"name4\")`, the rival yields `(\"name4\",\"app4\")`. "
            "Moves `scopeApp`/`scopeName` off equal values. Else the resolution "
            "scope is unpinned."
        ),
        "witness": (
            "-- Refuted with a recursive `self` intermediary and asymmetric scope:\n"
            "-- the pair must be (scopeApp, scopeName), not the swap.\n"
            "example : ¬ problem_spec_relationDependencies\n"
            "    (ModelRef.concrete \"t\" \"n\") (some (ModelRef.str \"self\")) none \"app4\" \"name4\"\n"
            "    (implementation_relationDependencies\n"
            "      (ModelRef.concrete \"t\" \"n\") (some (ModelRef.str \"self\")) none \"app4\" \"name4\") := by\n"
            "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-through-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_DROP_THROUGH),
        "refinement": (
            "the intermediary dependency is never emitted: the list carries only "
            "the target dependency even when an intermediary model IS specified. A "
            "relation routed through an explicit intermediary must make the "
            "migration that creates the field depend on that intermediary model "
            "too, else the create-migration can be ordered before the intermediary "
            "model exists. The pre-existing through-model tests assert the "
            "intermediary dependency is present, so dropping it breaks them — it "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the `some thr` clause `result = [firstDep, modelRefToPair "
            "thr scopeApp scopeName]`, which pins the list LENGTH at two on that "
            "arm: the rival returns `[firstDep]`. This is the one clause no "
            "value-reshaping rival reaches — every other rival here returns a "
            "two-element list on a `some` intermediary and merely gets an entry's "
            "CONTENTS wrong, so the presence decision itself would otherwise go "
            "unattacked. Refuted at the F2P-shaped separate-apps input, where the "
            "spec demands two entries and the rival yields one. Else the "
            "entry-count half of the through clause is unpinned."
        ),
        "witness": (
            "-- Refuted where an intermediary IS supplied: the list must carry a\n"
            "-- SECOND entry (the resolved intermediary), not stop after the target\n"
            "-- dependency. Concrete references, so `decide` closes by evaluation.\n"
            "example : ¬ problem_spec_relationDependencies\n"
            "    (ModelRef.concrete \"testapp\" \"publisher\")\n"
            "    (some (ModelRef.concrete \"contract\" \"contract\")) none \"authors\" \"author\"\n"
            "    (implementation_relationDependencies\n"
            "      (ModelRef.concrete \"testapp\" \"publisher\")\n"
            "      (some (ModelRef.concrete \"contract\" \"contract\")) none \"authors\" \"author\") := by\n"
            "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-always-two-entries",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_TWO),
        "refinement": (
            "a second dependency is emitted even when NO intermediary model is "
            "specified (the target dependency duplicated). A plain relational field "
            "with no intermediary induces exactly ONE dependency; inventing a "
            "second one adds a spurious entry to the create migration's dependency "
            "list, which the pre-existing tests for ordinary (non-through) "
            "relational fields assert the exact contents of — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the `none` clause `result = [firstDep]`, which pins that "
            "the list STOPS after the target dependency: the rival returns a "
            "two-element list. The converse direction of `weak-drop-through-entry` "
            "— that one is too short on the `some` arm, this one too long on the "
            "`none` arm — so between them the entry-count decision is pinned in "
            "both directions and on both arms of `throughRef`. Refuted with "
            "`throughRef = none` (the discriminating shape). Else the spec would "
            "admit a spurious trailing dependency."
        ),
        "witness": (
            "-- Refuted where NO intermediary is supplied: the list must stop after\n"
            "-- the target dependency, with no second entry at all.\n"
            "example : ¬ problem_spec_relationDependencies\n"
            "    (ModelRef.concrete \"testapp\" \"publisher\") none none \"authors\" \"author\"\n"
            "    (implementation_relationDependencies\n"
            "      (ModelRef.concrete \"testapp\" \"publisher\") none none \"authors\" \"author\") := by\n"
            "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-no-lowercase",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NO_LOWER),
        "refinement": (
            "the intermediary reference is resolved WITHOUT the object-name case "
            "fold: an inline resolver that mirrors the frozen one in every arm but "
            "returns the object name verbatim instead of lower-cased. The resolver "
            "applies a case fold to the object-name segment of a textual reference; "
            "an intermediary given as a CamelCase textual reference (the ordinary "
            "shape of a through model named in another app) would then keep its "
            "upper-case letters where the resolved dependency must be all "
            "lower-case, so the create-migration dependency's object name would "
            "mismatch — it does NOT resolve. Coincides with the fix only where the "
            "object name is a fold fixpoint (already all lower-case)."
        ),
        "rationale": (
            "REJECT from the `some thr` clause `result = [firstDep, modelRefToPair "
            "thr scopeApp scopeName]`: `modelRefToPair` lower-cases the object name "
            "of a textual reference, but the rival emits it verbatim. Because the "
            "fold `lower` is opaque, no literal input `decide`s the divergence; the "
            "witness instead states the refutation at a textual intermediary "
            "`\"app.Contract\"` under the hypothesis `lower \"Contract\" ≠ "
            "\"Contract\"` (a fold that actually changes the name), which the "
            "consistency probe confirms is satisfiable. Else the case-fold half of "
            "the through clause is unpinned. GOLD-SIDE SIGNATURE, and why it is a "
            "refutation rather than a tactic mismatch: on the frozen impl `simp` "
            "PROVES the spec equation outright, so `hspec` collapses to `True` and "
            "the projection `hspec.2.1.2` then fails as `Invalid projection`. That "
            "is a semantic verdict, not a syntactic gap, and two further builds "
            "establish it rather than assert it — flipping the claim (asserting the "
            "spec HOLDS at this point) makes gold SUCCEED and the rival FAIL, so "
            "gold's exit code tracks what is claimed; and replacing the closing step "
            "with a deliberate type error reveals `hspec : True` on gold against the "
            "live equation `True ∧ (True ∧ n = lower n) ∧ True` on the rival."
        ),
        "witness": (
            "-- Refuted at a textual intermediary whose object name the fold would\n"
            "-- change: the through entry must carry `lower n`, not `n`. The fold is\n"
            "-- opaque, so it is named by HYPOTHESIS rather than computed; the split\n"
            "-- of the concrete reference is supplied likewise.\n"
            "example (n : String) (h : lower n ≠ n)\n"
            "    (hs : splitFirstDot \"app.Contract\" = some (\"app\", n)) :\n"
            "    ¬ problem_spec_relationDependencies\n"
            "      (ModelRef.concrete \"t\" \"n0\") (some (ModelRef.str \"app.Contract\")) none \"authors\" \"author\"\n"
            "      (implementation_relationDependencies\n"
            "        (ModelRef.concrete \"t\" \"n0\") (some (ModelRef.str \"app.Contract\")) none \"authors\" \"author\") := by\n"
            "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
            "  simp only [Id.run, Id.pure_eq, Id.bind_eq, modelRefToPair]\n"
            "  rw [hs]\n"
            "  intro hspec\n"
            "  simp only [if_neg (by decide : ¬ (\"app.Contract\" = \"self\")),\n"
            "    List.cons_append, List.nil_append, List.cons.injEq, Prod.mk.injEq] at hspec\n"
            "  exact h hspec.2.1.2.symm\n"
        ),
    },
    {
        "id": "weak-split-on-last-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_LAST_DOT),
        "refinement": (
            "the intermediary textual reference is split on its LAST dot instead of "
            "its FIRST when separating the app label from the object name; the "
            "resolver's real split keeps only the first dot as the separator "
            "(`split(\".\", 1)`). For a multi-segment reference (an app label that "
            "itself contains a dot) the app label and object name would be cut at "
            "the wrong point, so the dependency would name the wrong app — it does "
            "NOT resolve. Coincides with the fix on every single-dot reference."
        ),
        "rationale": (
            "REJECT from the `some thr` clause: the app label of the intermediary "
            "entry must be the prefix before the FIRST dot, but the rival takes the "
            "prefix before the LAST dot. Refuted at `\"a.b.Contract\"`, where the "
            "first-dot split gives app `\"a\"` and the last-dot split gives app "
            "`\"a.b\"`. The app label carries NO fold (kept verbatim), so the "
            "refutation is stated on the fold-free app half and closes without "
            "meeting `lower`; the two concrete splits are supplied by hypothesis. "
            "Else the first-dot split semantics is under-pinned. Both hypotheses are "
            "TRUE facts about the carrier, not merely unrefutable ones: "
            "`splitFirstDot \"a.b.Contract\"` evaluates to `some (\"a\", "
            "\"b.Contract\")` and `\"a.b.Contract\".splitOn \".\"` to `[\"a\", "
            "\"b\", \"Contract\"]` (both confirmed by evaluation), and the "
            "refutation turns on `\".\".intercalate [\"a\", \"b\"] = \"a\"` being "
            "FALSE — that intercalation is `\"a.b\"`. GOLD-SIDE SIGNATURE: as with "
            "the fold rival, `simp` proves the equation on the frozen impl so "
            "`hspec` collapses to `True` and the projection fails; the flipped claim "
            "SUCCEEDS on gold and FAILS on the rival, and the type-revealing build "
            "prints `True` on gold against `\".\".intercalate [\"a\", \"b\"] = \"a\" "
            "∧ lower \"Contract\" = lower m` on the rival. So gold's exit code "
            "carries information about the claim."
        ),
        "witness": (
            "-- Refuted at a multi-dot reference: the app label must be the prefix\n"
            "-- before the FIRST dot (`a`), not the LAST (`a.b`). The app half carries\n"
            "-- no fold, so the refutation is decidable once the two concrete splits\n"
            "-- are named by hypothesis.\n"
            "example (m : String)\n"
            "    (hsf : splitFirstDot \"a.b.Contract\" = some (\"a\", m))\n"
            "    (hso : \"a.b.Contract\".splitOn \".\" = [\"a\", \"b\", \"Contract\"]) :\n"
            "    ¬ problem_spec_relationDependencies\n"
            "      (ModelRef.concrete \"t\" \"n0\") (some (ModelRef.str \"a.b.Contract\")) none \"authors\" \"author\"\n"
            "      (implementation_relationDependencies\n"
            "        (ModelRef.concrete \"t\" \"n0\") (some (ModelRef.str \"a.b.Contract\")) none \"authors\" \"author\") := by\n"
            "  unfold problem_spec_relationDependencies implementation_relationDependencies\n"
            "  intro hspec\n"
            "  simp only [Id.run, Id.pure_eq, Id.bind_eq, modelRefToPair, hsf, hso,\n"
            "    if_neg (by decide : ¬ (\"a.b.Contract\" = \"self\")),\n"
            "    List.reverse_cons, List.reverse_nil, List.nil_append, List.cons_append,\n"
            "    List.cons.injEq, Prod.mk.injEq] at hspec\n"
            "  exact absurd hspec.2.1.1 (by decide)\n"
        ),
    },
]


# No consumed axioms: the sole callee `resolve_relation` is a deep-model
# A-reference validated == the real callee by G-AX (its own gate), and `lower`
# is an opaque building block the proof never inspects. There is no in-model
# axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
