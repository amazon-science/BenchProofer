"""properties.py — G-PBT falsification battery for django__django-12193 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC_TESTS entry is a
full ``Solution.lean`` variant sharing the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start``/``-- impl-end`` and — for a case that
legitimately re-proves — inside ``-- proof-start``/``-- proof-end`` changes, so
``markers.same_spec`` holds and the single ``theorem correct_buildInputContext``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff the case is in
scope AND the file elaborates with the obligation closed; ``expect:"reject"``
passes iff the case is in scope AND it does NOT verify AND its refutation
``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh battery.
The nagini bundle states the read-only-input guarantee as a FRACTIONAL PERMISSION
on the caller's mapping (the mapping is held at half permission, so any write to
it is unprovable) and its central rivals are frame-mutation rivals rejected for
insufficient permission. Lean has no permissions and is referentially
transparent, so that guarantee is re-expressed structurally: the frozen spec
exposes the caller-visible mapping as an explicit OUTPUT component and pins it
equal to the input. A rival that "writes through" to the caller therefore becomes
a rival that returns a DIFFERENT value in that component, and it is refuted by
evaluation rather than by a permission check. The per-case map (ported /
omitted / re-expressed) is in the module ``assessment``.

DEFENDED SURFACE (one modeled behavior, one obligation). The routine assembles
one rendering context from three inputs — the element's own base attribute
mapping ``base``, the activation flag ``checkTest`` derived from the rendered
value, and the OPTIONAL caller-supplied mapping ``attrs`` — and the
postcondition has exactly two independent top-level conjuncts:

  C1  ``result.contextAttrs = mergeDict base (effectiveAttrs checkTest attrs)``
      — the exposed merged mapping is the base overlaid with the caller-supplied
      mapping (caller entries winning on a key collision, absent ↦ empty),
      additionally carrying the activation marker entry exactly when the flag is
      set. This pins WHICH mapping is overlaid on WHICH, the marker's PAYLOAD,
      the marker's presence/absence per branch, and that NO other entry is
      invented.
  C2  ``result.callerAttrs = attrs``
      — the caller-supplied mapping is read, never written: after the call the
      caller observes it exactly as passed in, whatever the activation flag. This
      is the load-bearing clause (the nagini half-permission requirement,
      restated as an output equality on this carrier).

Both conjuncts are DEFENDED (three ``expect:"verify"`` soundness positives, each
re-proved honestly for its own impl shape, plus one admissibility positive) and
both are ATTACKED: C2 by three rivals that write through to the caller's mapping
on different sub-domains, C1 by five rivals that get the overlay's PRIORITY, the
branch guard (either direction), the marker payload, or the entry set wrong.

WITNESS MECHANICS. This carrier is fully TRANSPARENT — no ``opaque`` leaf, no
consumed ``axiom``, and every operation (``dictSet``, ``mergeDict``,
``effectiveAttrs``) is a concrete computable ``def`` over ``List (String × Bool)``
and ``Option``. So no witness needs to condition on the carrier: each states the
spec predicate directly at ONE concrete input triple and closes by ``decide``
after unfolding. Every witness below was built twice by hand before shipping —
once against its rival (must elaborate) and once against the frozen solution
(must fail) — and gold's failure in each case is ``decide`` proving the
NEGATION of the witness's claim, i.e. gold genuinely satisfying the spec at that
point, not an unknown name or a parse error.

BINDER / POINT SPREAD. The eight reject witnesses probe EIGHT DISTINCT input
triples and move every input binder rather than fixing any at one convenient
value:

  * ``checkTest`` takes BOTH settings — five witnesses at ``true`` (the active
    branch) and three at ``false`` (the inactive branch), so a rival wrong on
    only one branch cannot hide;
  * ``attrs`` ranges over ``none`` (absent), ``some []`` (present but empty),
    ``some`` already carrying the marker entry with the INACTIVE payload, and
    ``some`` carrying one or more unrelated entries — the four shapes the
    optional binder can take;
  * ``base`` ranges over the empty mapping and three distinct non-empty
    mappings, including one whose key COLLIDES with a key of the caller's
    mapping at the OPPOSITE payload. That collision point is what makes the
    overlay's PRIORITY observable: at every non-colliding point the two overlay
    directions agree, so the "caller entries win" half of C1 is only actually
    attacked by ``overlay-keeps-base-on-collision``.

No two rivals share a refutation point. Two of the rivals are deliberate
NEAR-MISSES that agree with gold at every other rival's point and so need their
own: the third C2 rival writes through only when the caller's mapping ALREADY
carries the marker key, and ``overlay-keeps-base-on-collision`` differs from
gold ONLY where the two mappings collide.

AXIOM lane: EMPTY here. This bundle consumes no ``axiom`` — the two outside
operations (overlaying one mapping on another, recording one marker entry) are
spelled out concretely as ``mergeDict``/``dictSet``, i.e. deep-model
A-references validated executably by G-AX. Nagini's three ``AXIOM_TESTS``
(soundness of its two ``@ContractOnly`` mapping callees plus their call-site
containment) belong to the G-AX lane, which this gate ignores, so they are
dropped per the porting map.
"""
from pathlib import Path

INSTANCE = "django__django-12193"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two frozen regions every case edits. Both anchors lie ENTIRELY inside the
# region they name (the impl body between the impl markers; the tactic body
# between the proof markers, below the byte-identical theorem STATEMENT), and
# both are unique in the file — so the manifest breaks loudly if the frozen
# solution ever drifts.
# ---------------------------------------------------------------------------
_IMPL = """  -- Work on a local mapping seeded from the caller-supplied one (empty if absent);
  -- the caller's own object is never touched.
  let mut cur := attrs.getD []
  if checkTest then
    cur := dictSet cur markerKey true
  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }"""

_PROOF = """  intro base checkTest attrs
  unfold problem_spec_buildInputContext implementation_buildInputContext effectiveAttrs
  cases checkTest <;> exact ⟨rfl, rfl⟩"""


def _rival(body):
    """A variant that changes ONLY the impl body, keeping the frozen tactic
    script. A rival is expected to reject; the witness — not the tactic failure —
    is what attributes the rejection to the spec."""
    return _swap(_BASE, _IMPL, body)


def _positive(body, proof):
    """A variant that reshapes the impl AND re-proves it honestly for the new
    shape. The theorem statement is untouched (only the tactic body moves), no
    helper lemma is added, and no assumption token is used."""
    return _swap(_swap(_BASE, _IMPL, body), _PROOF, proof)


def _witness(base, flag, caller, note):
    """`¬ problem_spec ... (implementation ...)` at one concrete input triple.

    Fully transparent carrier, so the refutation is stated at literal inputs and
    closed by evaluation. The head binds NOTHING, so there are no hypotheses that
    could be jointly unsatisfiable and the consistency probe does not apply.
    """
    return (
        f"{note}"
        f"example : ¬ problem_spec_buildInputContext {base} {flag} {caller}\n"
        f"    (implementation_buildInputContext {base} {flag} {caller}) := by\n"
        "  unfold problem_spec_buildInputContext implementation_buildInputContext\n"
        "    effectiveAttrs\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # SOUNDNESS POSITIVES — a structurally DIFFERENT but CORRECT impl must
    # still verify, else the spec is over-fit to the frozen spelling
    # (SPEC-TOO-STRONG). Each is re-proved for its own shape inside the proof
    # region; statement byte-identical, no new lemma, no assumption token. All
    # three confirmed by a real build.
    # =====================================================================
    {
        "id": "pos-guard-inverted-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Ports nagini (S1) "branch-reorder": handle the INACTIVE case first and
        # return early, falling through to the marker-recording case last.
        "module": _positive(
            "  let mut cur := attrs.getD []\n"
            "  if !checkTest then\n"
            "    return { contextAttrs := mergeDict base cur, callerAttrs := attrs }\n"
            "  cur := dictSet cur markerKey true\n"
            "  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }",
            _PROOF,
        ),
        "rationale": "PORT of the nagini branch-reorder positive. The activation "
                     "guard is inverted and the inactive case leaves by an early "
                     "return, so the two branches are emitted in the opposite "
                     "order and the marker-recording step is no longer nested "
                     "under a positive test. Identical behavior on both "
                     "sub-domains, so C1 and C2 both hold and it MUST verify — "
                     "otherwise the postcondition is pinned to one particular "
                     "branch ORDER rather than to the input→output relation. "
                     "Re-proved honestly: the frozen `cases checkTest` split "
                     "still closes both goals by `rfl` for the new shape.",
    },
    {
        "id": "pos-let-bound-context",
        "kind": "soundness",
        "expect": "verify",
        # Ports nagini (S2) "local-variable reshape": stage the prepared mapping
        # and the whole result through pure `let`s instead of a mutable local
        # updated under an `if` statement.
        "module": _positive(
            "  let cur : AttrMap := if checkTest then dictSet (attrs.getD []) markerKey true\n"
            "    else attrs.getD []\n"
            "  let ctx : InputContext := { contextAttrs := mergeDict base cur, callerAttrs := attrs }\n"
            "  return ctx",
            _PROOF,
        ),
        "rationale": "PORT of the nagini local-variable-reshape positive. The "
                     "mutable local updated inside an imperative `if` is replaced "
                     "by a single pure `let` bound to an `if`-EXPRESSION, and the "
                     "result record is itself staged through a typed local rather "
                     "than built in the return. Same two components from the same "
                     "operations, so it MUST verify — else the spec is over-fit to "
                     "the imperative mutable-accumulator spelling rather than to "
                     "the values C1 and C2 pin. Re-proved honestly with the frozen "
                     "tactic body, which still closes for the reshaped term.",
    },
    {
        "id": "pos-match-on-optional",
        "kind": "soundness",
        "expect": "verify",
        # No nagini counterpart: nagini's caller mapping is a plain dict, so
        # there is no optional to case-split on. Added because `attrs` is an
        # `Option` on THIS carrier and the frozen impl handles absence with a
        # default rather than a match — a positive that splits the optional
        # explicitly checks the spec is not pinned to the defaulting spelling.
        "module": _positive(
            "  match attrs with\n"
            "  | none =>\n"
            "    let cur : AttrMap := if checkTest then dictSet [] markerKey true else []\n"
            "    return { contextAttrs := mergeDict base cur, callerAttrs := none }\n"
            "  | some d =>\n"
            "    let cur : AttrMap := if checkTest then dictSet d markerKey true else d\n"
            "    return { contextAttrs := mergeDict base cur, callerAttrs := some d }",
            "  intro base checkTest attrs\n"
            "  unfold problem_spec_buildInputContext implementation_buildInputContext effectiveAttrs\n"
            "  cases attrs <;> cases checkTest <;> exact ⟨rfl, rfl⟩",
        ),
        "rationale": "CORRECT impl that case-splits the OPTIONAL caller mapping "
                     "explicitly instead of collapsing absence to the empty "
                     "mapping by a default, and re-forms the caller-visible "
                     "component per branch (`none` / `some d`) rather than "
                     "returning the input unexamined. Behaviorally identical on "
                     "all four (presence × flag) combinations, so C1 and C2 hold "
                     "and it MUST verify — else the spec is over-fit to the "
                     "defaulting spelling, or C2 is accidentally pinned to the "
                     "SYNTACTIC identity of the input rather than to its value. "
                     "Re-proved honestly: the tactic body gains the `cases attrs` "
                     "split the new shape needs; statement byte-identical.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input.
    # =====================================================================
    {
        "id": "admiss-ground-present-mapping",
        "kind": "admissibility",
        "expect": "verify",
        # The frozen obligation is unconditionally quantified (`∀ base checkTest
        # attrs, ...`) with NO precondition hypothesis, so nagini's
        # `admiss-present-dict` — which probes that its half-permission Requires
        # really admits a normal present mapping — has no precondition to
        # exercise here. The honest analogue is to discharge the POSTCONDITION
        # itself by evaluation at the reported scenario's own input, as a ground
        # `have`, and then close the frozen obligation verbatim.
        "module": _swap(
            _BASE, _PROOF,
            "  have _ground : problem_spec_buildInputContext [(\"id\", true)] true\n"
            "      (some [(markerKey, false)])\n"
            "      (implementation_buildInputContext [(\"id\", true)] true\n"
            "        (some [(markerKey, false)])) := by\n"
            "    unfold problem_spec_buildInputContext implementation_buildInputContext effectiveAttrs\n"
            "    decide\n" + _PROOF,
        ),
        "rationale": "PORT of the nagini admissibility probe onto a carrier with "
                     "no precondition to test. The obligation is discharged by "
                     "EVALUATION at the reported scenario's shape — a non-empty "
                     "base mapping, the activation flag SET, and a caller-supplied "
                     "mapping that is present and already carries the marker key "
                     "with the inactive payload — as a ground `have`, before the "
                     "frozen tactic body closes the general statement unchanged. "
                     "This shows the spec is satisfiable and non-vacuous at a "
                     "real input rather than only provable schematically: if the "
                     "ground `have` could not close, C1 and C2 would be jointly "
                     "unsatisfiable somewhere in the reachable domain. No new "
                     "lemma (a local `have` inside the proof region), statement "
                     "byte-identical, no assumption token. Confirmed by a real "
                     "build.",
    },

    # =====================================================================
    # UNIQUENESS RIVALS — expect "reject". Each carries (a) a `refinement`
    # arguing its faithful real patch would NOT resolve, so a rival that
    # VERIFIED would be a true verify-does-not-imply-resolve break rather than
    # an artifact, and (b) a `witness` pinning the violation at one concrete
    # input, seen to elaborate against the rival and to FAIL on gold.
    # ---------------------------------------------------------------------
    # C2 — the read-only-input clause (nagini's frame-mutation class, restated
    # as an output equality). Three rivals write through to the caller's
    # mapping on three different sub-domains.
    # =====================================================================
    {
        "id": "write-through-when-active",
        "kind": "uniqueness",
        "expect": "reject",
        # PORT of nagini (W1) frame-mutate-return-self, the MANDATORY case and
        # the reported defect itself: when the flag is set, the marker entry
        # reaches back into the caller-supplied mapping, so the caller observes
        # it afterwards. On nagini this is unprovable for insufficient
        # permission; here the caller-visible component simply comes out
        # different from the input.
        "module": _rival(
            "  let mut cur := attrs.getD []\n"
            "  let mut callerView := attrs\n"
            "  if checkTest then\n"
            "    cur := dictSet cur markerKey true\n"
            "    callerView := attrs.map (fun d => dictSet d markerKey true)\n"
            "  return { contextAttrs := mergeDict base cur, callerAttrs := callerView }"
        ),
        "refinement": "this is the pre-fix behavior the bundle's own "
                      "`Solution_prepatch.lean` carries: on the active branch the "
                      "marker is recorded into the caller-supplied mapping rather "
                      "than into a private one, so the caller's mapping is "
                      "observably changed by the call. The FAIL_TO_PASS test "
                      "passes a mapping "
                      "already carrying the marker key with the inactive payload, "
                      "calls the routine with the flag active, and then asserts "
                      "the caller's own mapping still holds the INACTIVE payload — "
                      "under this rival it holds the active one, so the assertion "
                      "fails. The companion array-widget test, which reuses ONE "
                      "caller mapping across a sequence of sub-elements and "
                      "expects the sub-element after an active one to expose NO "
                      "attributes at all, fails for the same reason: the first "
                      "active sub-element leaves the shared mapping carrying the "
                      "marker. It does NOT resolve — it IS the reported defect.",
        "rationale": "attacks C2 (`result.callerAttrs = attrs`) on the ACTIVE "
                     "sub-domain of `checkTest`. C1 still holds exactly (the "
                     "exposed merged mapping is unchanged), so the rejection is "
                     "attributable to C2 alone — this is the whole point of the "
                     "frozen spec exposing the caller-visible mapping as an "
                     "output component instead of leaving it unconstrained.",
        "witness": _witness(
            '[("id", true)]', "true", "(some [])",
            "-- Refuted on the ACTIVE branch at a PRESENT-but-empty caller\n"
            "-- mapping: the spec pins the caller-visible component to `some []`,\n"
            "-- the rival returns it carrying the marker entry. Fully concrete, so\n"
            "-- plain evaluation decides it.\n"),
    },
    {
        "id": "write-through-both-branches",
        "kind": "uniqueness",
        "expect": "reject",
        # PORT of nagini (W2) frame-mutate-return-fresh in its stronger flavour:
        # the write-through happens on BOTH branches (recording the flag's own
        # value as the payload), so the caller's mapping is changed even when the
        # flag is CLEAR. Isolates C2 from C1 on the inactive sub-domain, which the
        # previous rival leaves untouched.
        "module": _rival(
            "  let mut cur := attrs.getD []\n"
            "  if checkTest then\n"
            "    cur := dictSet cur markerKey true\n"
            "  return { contextAttrs := mergeDict base cur,\n"
            "           callerAttrs := attrs.map (fun d => dictSet d markerKey checkTest) }"
        ),
        "refinement": "a real patch that recorded the flag's own value into the "
                      "caller-supplied mapping unconditionally — leaving a private "
                      "mapping for the exposed result, so the rendered output is "
                      "right — would still change the caller's mapping on EVERY "
                      "call. The FAIL_TO_PASS test asserts the caller's mapping is "
                      "unchanged after the call, and this rival introduces the "
                      "marker key into a mapping that did not have it (or "
                      "overwrites the payload of one that did) whichever way the "
                      "flag went, so the assertion fails. The array-widget test "
                      "additionally reuses one caller mapping across sub-elements "
                      "and expects the inactive sub-element to expose no "
                      "attributes; a mapping polluted on the inactive branch too "
                      "defeats that. It does NOT resolve.",
        "rationale": "attacks C2 on the INACTIVE sub-domain of `checkTest`, the "
                     "sub-domain the previous rival gets right — so the two are "
                     "refuted for genuinely different reasons and may not share a "
                     "point. C1 holds exactly here (the exposed merged mapping is "
                     "built from a private mapping and is correct on both "
                     "branches), so again only C2 fires.",
        "witness": _witness(
            "[]", "false", "(some [])",
            "-- Refuted on the INACTIVE branch: the spec pins the caller-visible\n"
            "-- component to `some []`, the rival returns it carrying the marker\n"
            "-- key with the inactive payload — an entry the caller never had.\n"),
    },
    {
        "id": "write-through-only-when-key-present",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of `write-through-when-active`: the write-through is
        # narrowed to callers whose mapping ALREADY carries the marker key, so
        # no NEW key is ever introduced and the rival agrees with gold at the
        # first rival's refutation point. It is wrong only on the narrower
        # sub-domain, and gets its own point there.
        "module": _rival(
            "  let mut cur := attrs.getD []\n"
            "  let mut callerView := attrs\n"
            "  if checkTest then\n"
            "    cur := dictSet cur markerKey true\n"
            "    callerView := attrs.map (fun d => if d.any (fun p => p.1 == markerKey)\n"
            "      then dictSet d markerKey true else d)\n"
            "  return { contextAttrs := mergeDict base cur, callerAttrs := callerView }"
        ),
        "refinement": "a real patch that overwrote the marker entry in the "
                      "caller-supplied mapping only when that mapping already "
                      "carried the key — reasoning that overwriting an existing "
                      "entry 'adds nothing' — is exactly the shape the "
                      "FAIL_TO_PASS test is built to catch: that test supplies a "
                      "mapping whose marker key IS present with the inactive "
                      "payload and asserts the payload is still inactive after the "
                      "call. Under this rival it has been flipped to active, so "
                      "the assertion fails and the patch does NOT resolve — even "
                      "though the array-widget test, which starts from a mapping "
                      "with no marker key at all, would pass. That asymmetry is "
                      "why it is carried as a separate near-miss.",
        "rationale": "attacks C2 on the narrower sub-domain where the caller's "
                     "mapping already carries the marker key. It AGREES with gold "
                     "at `write-through-when-active`'s point (a present-but-empty "
                     "caller mapping: no key, so no write-through), so it must be "
                     "refuted at its OWN point — the reported scenario's input — "
                     "or its rationale would claim a sub-domain the manifest never "
                     "demonstrates.",
        "witness": _witness(
            "[]", "true", "(some [(markerKey, false)])",
            "-- Refuted at the point that DISTINGUISHES this near-miss: the caller\n"
            "-- mapping already carries the marker key with the inactive payload.\n"
            "-- The spec pins the caller-visible component to that exact input; the\n"
            "-- rival hands back the payload flipped. (At a caller mapping without\n"
            "-- the key this rival agrees with gold, which is why it needs its own\n"
            "-- point rather than sharing the first rival's.)\n"),
    },

    # =====================================================================
    # C1 — the exposed-merged-mapping clause. Five rivals: both partial-domain
    # collapses of the activation guard, the wrong marker payload, an invented
    # extra entry, and the overlay taken with the wrong PRIORITY on a key
    # collision.
    # =====================================================================
    {
        "id": "always-active",
        "kind": "uniqueness",
        "expect": "reject",
        # PORT of nagini (W3) always-selected / (W7) else-sets-checked. On this
        # carrier the two nagini rivals COLLAPSE into one: nagini's W3 drops the
        # inactive branch and W7 makes the inactive branch record the marker, but
        # since the frozen impl's only per-branch difference IS the marker
        # recording, both spell the same total function here. Carried once.
        "module": _rival(
            "  let cur := dictSet (attrs.getD []) markerKey true\n"
            "  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }"
        ),
        "refinement": "a real patch that recorded the marker entry "
                      "unconditionally — dropping the activation test — marks the "
                      "element active for values that should leave it inactive. "
                      "The PASS_TO_PASS rendering tests for the empty, absent and "
                      "negative values each pin the rendered element to carry NO "
                      "marker attribute, and the array-widget test pins the "
                      "sub-element following an active one to expose no attributes "
                      "at all rather than a marker; all of them fail. It does NOT "
                      "resolve.",
        "rationale": "PARTIAL-DOMAIN attack on C1: correct on the active "
                     "sub-domain of `checkTest`, wrong on the inactive one, where "
                     "`effectiveAttrs checkTest attrs` is the caller's mapping "
                     "with NO marker entry added. C2 holds exactly, so only C1 "
                     "fires. Ports BOTH nagini partial-domain rivals in that "
                     "direction (always-selected and the mis-indented "
                     "else-branch merge), which are the same total function on "
                     "this carrier.",
        "witness": _witness(
            '[("class", true)]', "false", "none",
            "-- Refuted on the INACTIVE branch at an ABSENT caller mapping, the\n"
            "-- shape the ordinary rendering path uses: the spec pins the exposed\n"
            "-- merged mapping to the base alone, the rival adds the marker entry.\n"),
    },
    {
        "id": "never-active",
        "kind": "uniqueness",
        "expect": "reject",
        # PORT of nagini (W4) never-selected: the mirror partial-domain collapse
        # — the marker is never recorded at all.
        "module": _rival(
            "  let cur := attrs.getD []\n"
            "  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }"
        ),
        "refinement": "a real patch that dropped the marker-recording step "
                      "entirely and simply forwarded its inputs never marks any "
                      "element active. The PASS_TO_PASS rendering tests for the "
                      "positive, integer and arbitrary-value cases each pin the "
                      "rendered element to CARRY the marker attribute, and the "
                      "array-widget test pins the first sub-element to expose "
                      "exactly the marker; all fail. It does NOT resolve. (Note "
                      "this rival keeps the caller's mapping pristine, so it "
                      "passes the FAIL_TO_PASS mutation assertion — which is "
                      "precisely why C1 has to be defended separately from C2: a "
                      "spec pinning only the no-write guarantee would admit it.)",
        "rationale": "PARTIAL-DOMAIN attack on C1 from the other side: correct on "
                     "the inactive sub-domain, wrong on the active one, where "
                     "`effectiveAttrs` requires the marker entry present with the "
                     "active payload. C2 holds exactly.",
        "witness": _witness(
            "[]", "true", "none",
            "-- Refuted on the ACTIVE branch at an ABSENT caller mapping — the\n"
            "-- minimal point at which the marker is required: the spec pins the\n"
            "-- exposed merged mapping to carry the marker entry, the rival\n"
            "-- returns the empty mapping.\n"),
    },
    {
        "id": "wrong-marker-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # PORT of nagini (W5) wrong-flag-false: the marker entry is recorded on
        # the right branch, into a private mapping, with the WRONG payload.
        "module": _rival(
            "  let mut cur := attrs.getD []\n"
            "  if checkTest then\n"
            "    cur := dictSet cur markerKey false\n"
            "  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }"
        ),
        "refinement": "a real patch that recorded the marker entry with the "
                      "inactive payload for an ACTIVE value renders the element "
                      "unmarked (the rendering layer omits a marker attribute "
                      "whose payload is negative). The PASS_TO_PASS rendering "
                      "tests for the positive and arbitrary-value cases pin the "
                      "marker attribute PRESENT, and the array-widget test pins "
                      "the first sub-element's attributes to exactly the marker "
                      "with the active payload — an inactive payload makes those "
                      "comparisons unequal. It does NOT resolve.",
        "rationale": "value-level attack on C1: the branch guard, the target "
                     "mapping and the entry SET are all right, only the marker's "
                     "PAYLOAD is wrong. `effectiveAttrs` pins it to the active "
                     "value on the active branch, so this cannot satisfy C1. C2 "
                     "holds exactly. Probed at a caller mapping carrying one "
                     "unrelated entry, so the failure is the payload and not a "
                     "missing carry-through.",
        "witness": _witness(
            "[]", "true", '(some [("id", true)])',
            "-- Refuted on the ACTIVE branch at a caller mapping holding one\n"
            "-- unrelated entry: the spec pins the marker entry's payload to the\n"
            "-- active value, the rival records the inactive one while carrying the\n"
            "-- unrelated entry through correctly.\n"),
    },
    {
        "id": "invents-extra-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # PORT of nagini (W6) spurious-key: the correct merge, plus one extra
        # attribute entry the caller never supplied and the base never had.
        "module": _rival(
            "  let mut cur := attrs.getD []\n"
            "  if checkTest then\n"
            "    cur := dictSet (dictSet cur markerKey true) \"disabled\" true\n"
            "  return { contextAttrs := mergeDict base cur, callerAttrs := attrs }"
        ),
        "refinement": "a real patch that injected a second, unrelated attribute "
                      "alongside the marker renders an attribute nothing asked "
                      "for. The array-widget test compares the first "
                      "sub-element's attribute mapping for EQUALITY against "
                      "exactly the marker entry, so any extra entry makes the "
                      "mappings unequal and the test fails; the PASS_TO_PASS "
                      "rendering tests compare rendered markup and would see the "
                      "stray attribute too. It does NOT resolve.",
        "rationale": "attacks the entry-SET half of C1: `effectiveAttrs` (and "
                     "hence `mergeDict base (effectiveAttrs ...)`) determines the "
                     "exposed mapping EXACTLY, so an entry outside the base, the "
                     "caller's mapping and the marker cannot satisfy it. The "
                     "marker itself is recorded correctly and C2 holds, so the "
                     "rejection is attributable to the invented entry alone. "
                     "Probed with a non-empty base AND a non-empty caller "
                     "mapping, so the extra entry is the only discrepancy.",
        "witness": _witness(
            '[("id", true)]', "true", '(some [("name", false)])',
            "-- Refuted on the ACTIVE branch with BOTH mappings non-empty (so the\n"
            "-- overlay itself is exercised) but at DISJOINT key sets, so the extra\n"
            "-- entry is the only discrepancy: the spec pins the exposed mapping to\n"
            "-- the base overlaid with the caller's mapping plus the marker, and\n"
            "-- the rival carries one further entry beyond that set.\n"),
    },
    {
        "id": "overlay-keeps-base-on-collision",
        "kind": "uniqueness",
        "expect": "reject",
        # NO nagini counterpart, and it closes a real gap in this port. Nagini's
        # spec pins the not-selected branch by a BOTH-DIRECTIONS key/value
        # equality against the caller's mapping alone (there is no second mapping
        # in its model to overlay), so collision priority is not a distinction it
        # can get wrong. On THIS carrier the routine merges TWO mappings and C1
        # pins which one wins, yet every other rival here differs from gold at a
        # point where the base and the caller's mapping share NO key — and at such
        # a point both overlay directions agree. So the "caller entries win" half
        # of C1 was asserted by the manifest and attacked by nothing. This rival
        # takes the overlay the other way round: an entry already present in the
        # base is KEPT, so a caller entry cannot override it.
        "module": _rival(
            "  let mut cur := attrs.getD []\n"
            "  if checkTest then\n"
            "    cur := dictSet cur markerKey true\n"
            "  -- Overlay taken with the priority REVERSED: an attribute name\n"
            "  -- already carried by the base mapping keeps the base's payload, so\n"
            "  -- a caller-supplied entry cannot override it.\n"
            "  let merged := cur.foldl (fun acc p =>\n"
            "    if acc.any (fun q => q.1 == p.1) then acc else acc ++ [p]) base\n"
            "  return { contextAttrs := merged, callerAttrs := attrs }"
        ),
        "refinement": "a real patch that merged the two attribute mappings with "
                      "the priority reversed — letting the element's OWN base "
                      "attributes win over the caller-supplied ones instead of the "
                      "other way round — silently ignores every caller override of "
                      "an attribute the element already declares. That is the "
                      "opposite of what the caller-supplied mapping is for: the "
                      "rendering layer's whole contract is that a caller may "
                      "override a declared attribute for one rendering. The "
                      "PASS_TO_PASS rendering tests that supply an attribute the "
                      "element also declares would render the element's value "
                      "rather than the supplied one and their markup comparisons "
                      "fail. Worse for the reported scenario: the activation "
                      "marker is recorded into the caller-side mapping, so when the "
                      "element's own mapping already declares that attribute with "
                      "the inactive payload, the marker is DROPPED and an active "
                      "input renders unmarked. It does NOT resolve.",
        "rationale": "attacks the PRIORITY half of C1: `mergeDict base extra` sets "
                     "each entry of `extra` INTO `base`, so on a key collision the "
                     "caller's payload is the one C1 pins. This rival is a "
                     "deliberate NEAR-MISS — it agrees with gold at every input "
                     "where the base and the effective caller mapping have "
                     "disjoint key sets, which is every point the other seven "
                     "reject cases use, so it needs and gets a colliding point of "
                     "its own. C2 holds exactly (the caller's mapping is returned "
                     "untouched), so only C1 fires, and only its priority clause.",
        "witness": _witness(
            '[("id", true)]', "false", '(some [("id", false)])',
            "-- Refuted at a key COLLISION: the base mapping and the caller's\n"
            "-- mapping both carry the SAME attribute name at OPPOSITE payloads.\n"
            "-- The spec pins the exposed mapping to the caller's payload; this\n"
            "-- rival keeps the base's. Stated on the INACTIVE branch so the marker\n"
            "-- plays no part and the collision is the sole discrepancy. This is\n"
            "-- the only point in the battery where the two overlay directions\n"
            "-- disagree at all, so it is the only point that can attribute a\n"
            "-- rejection to the priority clause.\n"),
    },
]


# ===========================================================================
# PORT ACCOUNTING — see the module `assessment` in the submitted payload for the
# narrative. In brief, nagini's 9 SPEC_TESTS map onto this bundle's 12 cases as:
#
#   nagini S1 pos-reorder            -> pos-guard-inverted-early-return
#   nagini S2 pos-local              -> pos-let-bound-context
#   (no nagini counterpart)          -> pos-match-on-optional  [carrier-specific:
#                                       `attrs` is an `Option` here]
#   nagini admiss-present-dict       -> admiss-ground-present-mapping
#                                       [re-expressed: no precondition to probe,
#                                        so the postcondition is discharged by
#                                        evaluation at that input instead]
#   nagini W1 frame-mutate-self      -> write-through-when-active
#   nagini W2 frame-mutate-fresh     -> write-through-both-branches
#   (no nagini counterpart)          -> write-through-only-when-key-present
#                                       [near-miss added so the reported
#                                        scenario's own input is probed]
#   nagini W3 always-selected   \
#   nagini W7 else-sets-checked  >   -> always-active  [the two nagini rivals are
#                                       the SAME total function on this carrier]
#   nagini W4 never-selected         -> never-active
#   nagini W5 wrong-flag-false       -> wrong-marker-payload
#   nagini W6 spurious-key           -> invents-extra-entry
#   (no nagini counterpart)          -> overlay-keeps-base-on-collision
#                                       [carrier-specific gap, added by AUDIT.
#                                        Nagini's model has only ONE mapping to
#                                        return, so overlay PRIORITY is not a
#                                        distinction it can get wrong and no
#                                        nagini rival covers it. This carrier
#                                        merges TWO mappings and C1 pins which
#                                        wins, but every ported rival happened to
#                                        be refuted at a point with DISJOINT key
#                                        sets, where both directions agree — so
#                                        the priority clause was claimed by the
#                                        manifest's own prose and attacked by
#                                        nothing. Verified by hand before adding:
#                                        the rival's witness elaborates (exit 0)
#                                        and FAILS on the frozen solution (exit 1,
#                                        `decide` refuting the concrete claim).]
#
# Nagini's 3 AXIOM_TESTS are dropped: the axiom lane is G-AX's, and this bundle
# consumes no axiom in any case.
#
# Nagini carries NO divergence / non-termination rival for this instance, so
# there is nothing in that lane to port. On this backend the class would be
# vacuous regardless: `implementation_buildInputContext` is a total Lean `def`,
# so a diverging implementation cannot be written at all.
#
# Nagini's frame/permission-mutation CLASS is not vacuous here, unlike most
# ports: it is re-expressed structurally, because the frozen spec exposes the
# caller-visible mapping as an explicit output component (C2). The three
# write-through rivals ARE that class, refuted by evaluation instead of by a
# permission check.
# ===========================================================================
