"""properties.py — G-PBT falsification battery for django__django-12419 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_<name>`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file elaborates
with the obligation closed); ``expect:"reject"`` passes iff (in scope AND it does
NOT verify AND the case's refutation ``witness`` holds of the rival while FAILING
on the frozen solution).

DEFENDED SURFACE (one total function over a two-layer configuration domain):

  referrerPolicy (projectSetting : Option (Option String)) : Option String
      result = (match projectSetting with
                | some v => v                  -- project declared the value v
                | none   => some "same-origin")-- project left it unconfigured

  The value domain ``Option String`` carries the "policy string or no-policy"
  choice: ``none`` = no policy advertised, ``some s`` = the policy string ``s``.
  The OUTER option records whether the project declared the setting at all:
  ``none`` = left at the built-in default, ``some v`` = declared as ``v``.

  Two INDEPENDENT top-level clauses:

    * CLAUSE A — the unconfigured branch. When the project declares nothing, the
      result is pinned to the concrete built-in default policy string. This is
      the behavior the change introduces and the behavior the F2P observable
      depends on: with no project override the resolved value must be exactly
      that one concrete policy string (previously it resolved to "no policy", so
      no header was advertised at all).

    * CLAUSE B — the declared branch, pre-existing most-specific-wins behavior:
      a declared value is used outright and passes through UNCHANGED, whether it
      is a concrete policy string or the explicit no-policy choice. Frame
      discipline (§0.5): this pre-existing cascade is pinned so a wrong impl
      cannot put anything else there, even though the change itself does not
      touch it.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent:
    the input is a plain immutable ``Option (Option String)``, there is no
    read-only half-permission on a list to overwrite and no aliasing to exploit.
    The nagini in-place-append rival has no expressible instance here and no
    substitute is fabricated for it.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against a term built only from the input (a match on ``projectSetting`` plus
    one concrete literal). The bundle declares no ``opaque``/``axiom``, so there
    is no answer key an implementation could echo without doing the work.

  * VALUE (nagini _WRONG_VALUE + _PARTIAL) — the two nagini value rivals both
    attack CLAUSE A. On the nagini ``List[int]`` carrier they were distinct: a
    wholly different constant vs. an off-by-one truncation reasoning about the
    LAST code point of a per-element copy loop. Here the policy value is modeled
    as an ATOMIC ``Option String`` (mapping.md: identity bijection, not
    ``List Char``), so "truncate the last code point" has no counterpart — it
    collapses to "a different string". The two nagini rivals therefore MERGE
    into one Clause-A rival that returns a different policy string; the spec
    pins the EXACT string, so any other value is rejected. (Documented in
    ``assessment``.)

  * CONTROL-FLOW-EFFECT / SETDEFAULT-IDENTITY (nagini _OVERWRITE, P2) — on the
    nagini carrier this attacked "never clobber an already-present header". Its
    faithful counterpart on this carrier is the most-specific-wins cascade of
    CLAUSE B: a rival that ignores the project's declared value and always
    yields the built-in default breaks the pass-through the same way clobbering
    a present header did. Two rivals cover the two inner shapes of a declared
    value (a concrete string, and the explicit no-policy choice).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete input; each was checked to HOLD of its rival and to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).

BINDER COVERAGE. The single input binder ``projectSetting`` is varied across the
reject witnesses over all three of its constructor shapes so the battery
exercises the spec's dependence on it rather than probing one point three times:
Clause A is refuted at ``none`` (unconfigured); Clause B is refuted at
``some (some "origin")`` (a declared concrete policy) AND at ``some none`` (the
declared no-policy choice). ``pts`` = 3 distinct inputs.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
modeled behavior is a total selection over the input's own data, so there is no
axiom-soundness / axiom-containment obligation to probe here (that lane is
G-AX's in any case). AXIOM_TESTS is therefore empty.
"""
from pathlib import Path

INSTANCE = "django__django-12419"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The full impl-region body, and sub-strings that lie ENTIRELY inside it.
_IMPL_GOLD = (
    "def implementation_referrerPolicy\n"
    "    (projectSetting : Option (Option String)) : Option String := Id.run do\n"
    "  let mut setting : Option String := defaultReferrerPolicy\n"
    "  match projectSetting with\n"
    "  | some v => setting := v\n"
    "  | none   => pure ()\n"
    "  return setting\n"
)
# init line (unique — the pure def and the proof `unfold` mention the name in
# different syntactic contexts)
_I_INIT = "  let mut setting : Option String := defaultReferrerPolicy\n"
# the whole override selection + return (unique inside the impl region)
_I_MATCH = (
    "  match projectSetting with\n"
    "  | some v => setting := v\n"
    "  | none   => pure ()\n"
    "  return setting\n"
)
# just the two match arms (unique inside the impl region)
_I_ARMS = (
    "  | some v => setting := v\n"
    "  | none   => pure ()\n"
)
# the frozen tactic body (everything after `:= by`; unique)
_PROOF_BODY = (
    "  intro projectSetting\n"
    "  unfold problem_spec_referrerPolicy implementation_referrerPolicy defaultReferrerPolicy\n"
    "  cases projectSetting with\n"
    "  | none => rfl\n"
    "  | some v => rfl\n"
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the `theorem correct_referrerPolicy` STATEMENT byte-identical; the
    # frozen tactic body still closes for these reshapes (the match/`getD` forms
    # reduce under the same `cases ... <;> rfl`), so no new lemma, axiom, or
    # assumption token is introduced.
    # =====================================================================
    {
        "id": "pos-explicit-match",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: drop the mutable-accumulator `Id.run do` and spell
        # the cascade as a direct pattern match — declared value in one arm, the
        # built-in default in the other. Same value on every input.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_referrerPolicy\n"
            "    (projectSetting : Option (Option String)) : Option String :=\n"
            "  match projectSetting with\n"
            "  | some v => v\n"
            "  | none   => defaultReferrerPolicy\n",
        ),
        "rationale": "a correct reshape of the two-layer selection (a direct "
                     "match returning the declared value, else the built-in "
                     "default) must satisfy `result = (match projectSetting with "
                     "| some v => v | none => some \"same-origin\")`; if it "
                     "cannot, the spec is SPEC-TOO-STRONG. Proof: the frozen "
                     "tactic body is retained — after `unfold` the match splits "
                     "under `cases projectSetting` and each arm is `rfl`.",
    },
    {
        "id": "pos-getd",
        "kind": "soundness",
        "expect": "verify",
        # Structural reshape: express the whole cascade as the library
        # most-specific-wins combinator `Option.getD`, defaulting to the
        # built-in value. `projectSetting.getD d` = `match projectSetting with
        # | some v => v | none => d`, so it is the spec pointwise.
        "module": _swap(
            _BASE, _IMPL_GOLD,
            "def implementation_referrerPolicy\n"
            "    (projectSetting : Option (Option String)) : Option String :=\n"
            "  projectSetting.getD defaultReferrerPolicy\n",
        ),
        "rationale": "expressing the cascade via `Option.getD` (declared value, "
                     "else built-in default) equals the spec's match pointwise, "
                     "so `result = (match projectSetting with | some v => v | "
                     "none => some \"same-origin\")` still holds; must verify. "
                     "Proof: the frozen tactic body is retained — `Option.getD` "
                     "reduces definitionally on each `cases projectSetting` arm, "
                     "so `rfl` closes both. No helper lemma or new declaration.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped input rather than only
    # provable in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the behavior is total, so `∀` is unguarded), so nagini's
    # precondition-admission probe has no binder to attack here; the honest
    # analogue is to discharge the spec predicate at the F2P ground input (the
    # project leaves the setting unconfigured, so the resolved value is the
    # built-in default) inside the proof region, alongside the frozen
    # obligation. If that ground instance could not be discharged, the modeled
    # behavior would be unsatisfiable at exactly the input the F2P exercises.
    # =====================================================================
    {
        "id": "admiss-unconfigured-ground-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_referrerPolicy none\n"
            "      (implementation_referrerPolicy none) := by\n"
            "    unfold problem_spec_referrerPolicy implementation_referrerPolicy defaultReferrerPolicy\n"
            "    rfl\n"
            + _PROOF_BODY,
        ),
        "rationale": "the obligation is discharged at the F2P ground input (the "
                     "project leaves the setting unconfigured, `projectSetting = "
                     "none`, so the resolved value is the built-in default) by "
                     "`rfl`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the spec is unsatisfiable at the normal "
                     "input, the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: the theorem STATEMENT is byte-identical, the "
                     "ground instance is a `have` inside the existing tactic "
                     "body, and no new declaration/axiom/`sorry` is introduced.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one
    # concrete input.
    # =====================================================================

    # ---- CLAUSE A (unconfigured branch = the change) ----
    {
        "id": "weak-wrong-default-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Initialise the unconfigured result to a DIFFERENT policy string. The
        # declared-value pass-through is untouched, so this diverges only on the
        # unconfigured branch — exactly the branch the change pins.
        "module": _swap(
            _BASE, _I_INIT,
            "  let mut setting : Option String := some \"no-referrer\"\n",
        ),
        "refinement": "resolving the unconfigured setting to a DIFFERENT policy "
                      "string means the out-of-the-box response advertises that "
                      "other policy; the F2P observable pins the rendered value "
                      "to exactly the one concrete built-in default policy "
                      "string, so a different default would surface the wrong "
                      "value and NOT resolve. This is the nagini _WRONG_VALUE and "
                      "_PARTIAL rivals merged: the value is atomic here, so "
                      "'a different constant' and 'a truncated constant' are the "
                      "same attack — any string other than the exact default.",
        "rationale": "REJECT from CLAUSE A (`projectSetting = none => result = "
                     "some \"same-origin\"`): at `none` the spec pins the exact "
                     "built-in default string and the rival yields a different "
                     "string. The spec pins the VALUE, not merely 'some "
                     "non-empty policy', so any other string is refuted.",
        "witness": (
            "-- Refuted on the unconfigured branch (the branch the change pins):\n"
            "-- with no project override the resolved value must be EXACTLY the\n"
            "-- built-in default string, so a different string violates the spec.\n"
            "example : ¬ problem_spec_referrerPolicy none\n"
            "    (implementation_referrerPolicy none) := by\n"
            "  unfold problem_spec_referrerPolicy implementation_referrerPolicy\n"
            "  decide\n"
        ),
    },

    # ---- CLAUSE B (declared branch = pre-existing most-specific-wins) ----
    {
        "id": "weak-override-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the selection entirely: always return the built-in default,
        # ignoring a project-declared value. Diverges wherever the project
        # declares a concrete policy that differs from the default.
        "module": _swap(_BASE, _I_MATCH, "  return setting\n"),
        "refinement": "always yielding the built-in default and ignoring a "
                      "project-declared value discards the most-specific-wins "
                      "cascade: a project that configures a concrete policy would "
                      "silently get the default instead. That is not the change "
                      "(which only alters the default) — it regresses the "
                      "pre-existing settings-resolution contract the surrounding "
                      "suite relies on, so a faithful such patch would NOT "
                      "resolve. Analogue of nagini _OVERWRITE (the setdefault "
                      "identity: never clobber a value that was already set).",
        "rationale": "REJECT from CLAUSE B (`projectSetting = some v => result = "
                     "v`): at `some (some \"origin\")` the spec requires "
                     "`some \"origin\"` (the declared value passes through) and "
                     "the rival returns the built-in default `some "
                     "\"same-origin\"`. Refuted at a DECLARED concrete policy so "
                     "the `some v` binder is exercised, not just `none`.",
        "witness": (
            "-- Refuted where the project declares a concrete policy differing\n"
            "-- from the built-in default: the declared value must pass through.\n"
            "example : ¬ problem_spec_referrerPolicy (some (some \"origin\"))\n"
            "    (implementation_referrerPolicy (some (some \"origin\"))) := by\n"
            "  unfold problem_spec_referrerPolicy implementation_referrerPolicy defaultReferrerPolicy\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-explicit-nopolicy-collapsed",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on Clause B: honours a declared concrete policy, but treats
        # the explicit no-policy choice (`some none`) as if unconfigured, so it
        # yields the built-in default there. Agrees with the spec on `none` and
        # on every `some (some s)`; diverges ONLY at `some none`.
        "module": _swap(
            _BASE, _I_ARMS,
            "  | some (some s) => setting := some s\n"
            "  | some none     => pure ()\n"
            "  | none          => pure ()\n",
        ),
        "refinement": "treating the explicit no-policy choice as if the setting "
                      "were unconfigured advertises the built-in default even "
                      "when the project deliberately opted OUT of a referrer "
                      "policy; the ability to disable the header is pre-existing "
                      "behavior the settings-resolution contract guarantees, so a "
                      "faithful patch that lost it would regress opt-out and NOT "
                      "resolve. NEAR-MISS: it is correct on the whole "
                      "unconfigured branch and on every declared concrete policy "
                      "— its only divergence is the declared no-policy point, "
                      "which is why its witness sits at `some none` rather than "
                      "the `some (some _)` point `weak-override-ignored` uses.",
        "rationale": "REJECT from CLAUSE B (`projectSetting = some v => result = "
                     "v`) at the inner shape `v = none`: at `some none` the spec "
                     "requires `none` (declared no-policy passes through) and the "
                     "rival returns the built-in default `some \"same-origin\"`. "
                     "This probes the third constructor shape of `projectSetting` "
                     "so the binder is exercised over `none`, `some (some _)`, "
                     "and `some none` across the battery.",
        "witness": (
            "-- Refuted where the project explicitly declares no policy: the\n"
            "-- declared no-policy choice must pass through as no policy, not be\n"
            "-- overridden by the built-in default.\n"
            "example : ¬ problem_spec_referrerPolicy (some none)\n"
            "    (implementation_referrerPolicy (some none)) := by\n"
            "  unfold problem_spec_referrerPolicy implementation_referrerPolicy defaultReferrerPolicy\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the built-in default is a
# concrete literal and the two-layer selection is modeled directly, so there is
# no in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
