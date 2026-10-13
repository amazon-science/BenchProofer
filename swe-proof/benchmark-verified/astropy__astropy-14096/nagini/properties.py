# properties.py — PBT manifest for astropy__astropy-14096.
#
# NOT a Nagini module: a record of adversarially-reasoned falsification cases.
# The runner (swebench_nagini.pbt) parses SPEC_TESTS / AXIOM_TESTS and stamps a
# RESULT. Spec cases are full model.py variants built by region-surgery (only the
# text inside # impl-start/# impl-end is edited, so the frozen spec — axioms /
# pure / pre- / post-conditions — is byte-identical and same_spec holds). Axiom
# cases are real-callee probes executed in the instance Docker image.
#
# Defended surface (read model.py + refinement.md + mapping.md):
#   resolve_missing(name, is_alias, alias_value, is_frame_attr, frame_attr_value,
#                   is_frame_passthrough, passthrough_value, is_transform,
#                   transform_value) -> int
#   ALL inputs are plain int/bool. There is NO heap parameter and NO Acc(x,1/2)
#   read-only input, so the FRAME-MUTATION class does NOT apply here (there is
#   nothing on the heap to overwrite) — see 'assessment'. The empty Requires also
#   makes admissibility trivial (the function is total on its inputs).
#
# Load-bearing postcondition clauses (the things an attacker must defeat):
#   (P1) FIVE priority-ordered normal-return Ensures, one per leg (alias >
#        frame_attr > frame_passthrough > transform > residual). Leg 1 (alias) is
#        TOTAL and pins only Result() == alias_value. Legs 2-5 are PARTIAL, and
#        each pins THREE things about the step its guards selected: that step
#        SUCCEEDED (`*_step_succeeds(name)`), the value is that step's value, and
#        the return carries that step's unforgeable capability token
#        (`*_step_performed(name)`). So a normal return is legal only as the
#        selected step's own success passed through: the value is not the
#        resolver's to choose (`return name` / `return alias_value` fail), the
#        token cannot be forged (echoing a pure oracle without performing the step
#        fails), and the selector forbids returning where the step FAILED (so
#        performing a step and SWALLOWING its failure fails).
#   (P2) ONE conditional Exsures covering every failing path. It is unconditional
#        in `not is_alias` (leg 1 is total, so no failure may escape it), and
#        per-leg conditional otherwise: the leg's `*_step_succeeds(name)` must be
#        FALSE (the resolver may not fail where its step succeeded) and the failure
#        must carry that leg's own token (so it may not be fabricated, nor borrowed
#        from a DIFFERENT leg's step).
#   (P3) On leg 5 the Exsures carries one further, DISCRIMINATING observable:
#        RaisedException().subject == residual_step_subject(name), the name the
#        residual resolution found missing. The spec does NOT assume that equals
#        `name`, so a resolver blaming the requested name cannot discharge it.
#        residual_step_subject is an opaque @Pure oracle, so the subject can be
#        neither forged nor obtained without performing the step — and echoing the
#        oracle (raise AttributeAccessError(residual_step_subject(name))) still
#        cannot present the token, since nothing can Fold a bodyless @Predicate
#        into existence.
#
# P1 and P2 together make every leg a CONDUIT for the step its guards selected:
# each leg's two outcomes are exactly that step's two outcomes, on that step's own
# condition, so a leg can neither invent an outcome nor convert one of its step's
# outcomes into the other. Legs 2-5 are partial because the real steps are
# partial: producing a frame attribute, a frame passthrough, a transform target or
# a residual resolution can each itself fail, and the resolver then surfaces that
# failure. A spec pinning any of those legs as TOTAL (an unconditional
# Result() == *_value) would reject a faithful implementation — see mapping.md 3.1.
#
# The F2P regression test (gh-8340) asserts the surfaced AttributeError blames the
# INNER missing name ("random_attr"), NOT the requested property name ("prop"):
#   pytest.raises(AttributeError, match="random_attr"). Each reject rival's
# refinement argument is grounded in exactly that observable.
from pathlib import Path

INSTANCE = "astropy__astropy-14096"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The entire gold impl body (between the markers). Editing only this block keeps
# the spec regions untouched, so every variant is same_spec with model.py.
_GOLD_IMPL = """    if is_alias:
        return alias_value
    if is_frame_attr:
        return frame_attr_step(name, frame_attr_value)
    if is_frame_passthrough:
        return passthrough_step(name, passthrough_value)
    if is_transform:
        return transform_step(name, transform_value)
    return residual_step(name)"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


# ------------------------------------------------------------------ POSITIVE
# A structurally-DIFFERENT but CORRECT impl: the four guards rewritten as an
# elif-chain with the residual leg in the trailing `else`. Same control semantics
# (priority order preserved; every leg still performs its own step).
# No new proof obligation is introduced (no loops / lemmas), so this MUST verify;
# if it cannot, the spec is SPEC-TOO-STRONG.
_POS_ELIF = """    if is_alias:
        return alias_value
    elif is_frame_attr:
        return frame_attr_step(name, frame_attr_value)
    elif is_frame_passthrough:
        return passthrough_step(name, passthrough_value)
    elif is_transform:
        return transform_step(name, transform_value)
    else:
        return residual_step(name)"""

# A second correct shape: handle the residual leg FIRST via the negated
# disjunction, then the four guarded steps. Each leg still performs its own step,
# so every leg is still a conduit; different executable shape, identical
# behaviour.
_POS_GUARDNEG = """    if not (is_alias or is_frame_attr or is_frame_passthrough or is_transform):
        return residual_step(name)
    if is_alias:
        return alias_value
    if is_frame_attr:
        return frame_attr_step(name, frame_attr_value)
    if is_frame_passthrough:
        return passthrough_step(name, passthrough_value)
    # only is_transform remains
    return transform_step(name, transform_value)"""

# ------------------------------------------------------------------ ADMISSIBILITY
# The Requires is empty, so the function is total; a normal in-domain call (alias
# resolves) must verify. This minimal correct impl exercises the resolving path
# and confirms the precondition admits an F2P-shaped input (else PRECOND-TOO-STRONG).
# It keeps the fail-branch delegation so the no-resolution obligations still hold.
_ADMISS = """    # Admissibility: a representative in-domain call (some resolution applies)
    # is accepted; every leg still performs its own step.
    if is_alias:
        return alias_value
    if is_frame_attr:
        return frame_attr_step(name, frame_attr_value)
    if is_frame_passthrough:
        return passthrough_step(name, passthrough_value)
    if is_transform:
        return transform_step(name, transform_value)
    return residual_step(name)"""


# ------------------------------------------------------------------ REJECT rivals
# Every rival below edits ONLY the impl region, so the frozen spec is
# byte-identical and same_spec holds.
_L5 = "    return residual_step(name)"
_L4 = ("    if is_transform:\n"
       "        return transform_step(name, transform_value)")
_L3 = ("    if is_frame_passthrough:\n"
       "        return passthrough_step(name, passthrough_value)")
_L2 = ("    if is_frame_attr:\n"
       "        return frame_attr_step(name, frame_attr_value)")
_L1 = "    if is_alias:\n        return alias_value"


# (1) the historic spec-too-weak hole: leg 5 RETURNS NORMALLY with a value of its
# own choosing (echoes the requested name). Must REJECT on P1's leg-5 clause.
_ATK_RETURN_NAME = _swap(_GOLD_IMPL, _L5,
    "    # WRONG: fabricate a normal return on the residual leg.\n"
    "    return name")

# (2) leg 5 returns alias_value (another self-chosen normal return). REJECT on P1.
_ATK_RETURN_ALIAS = _swap(_GOLD_IMPL, _L5,
    "    # WRONG: vacuous normal return of an unrelated resolving value.\n"
    "    return alias_value")

# (3) the PRE-PATCH behaviour: raises, but blames the REQUESTED name itself.
# REJECT on P2/P3 (leg-5 selector + subject mismatch).
_ATK_RAISE_NAME = _swap(_GOLD_IMPL, _L5,
    "    # WRONG (pre-patch): fabricate a fresh failure naming the requested name.\n"
    "    raise AttributeAccessError(name)")

# (4) raises with an UNRELATED forged subject (a resolving value token). REJECT on P3.
_ATK_RAISE_TOKEN = _swap(_GOLD_IMPL, _L5,
    "    # WRONG: raise, but blame an arbitrary unrelated token.\n"
    "    raise AttributeAccessError(alias_value)")

# (4b) the ORACLE-ECHO cheat (directive 8): raise while ECHOING the pure subject
# oracle, without ever performing the residual step. The subject equality holds by
# construction, so P3's subject clause alone cannot reject it; it must REJECT on
# the capability token residual_step_performed(name) (a bodyless @Predicate cannot
# be Fold-ed) — and on the leg's selector, which an unperformed step never fixes.
_ATK_ECHO_ORACLE = _swap(_GOLD_IMPL, _L5,
    "    # WRONG: echo the pure oracle; never perform the residual step.\n"
    "    raise AttributeAccessError(residual_step_subject(name))")

# (4c) the VALUE-ECHO cheat: the mirror image on leg 5's other path. Returns the
# pure residual_step_value(name) oracle, matching the value by construction, but
# never performs the step. REJECT on P1's leg-5 token + selector conjuncts.
_ATK_ECHO_VALUE = _swap(_GOLD_IMPL, _L5,
    "    # WRONG: echo the pure value oracle; never perform the residual step.\n"
    "    return residual_step_value(name)")

# (4d) the SWALLOW cheat on leg 5, aimed squarely at the conduit property: it DOES
# perform the step (so it legitimately holds the token) but catches the step's
# failure and returns a value instead of surfacing it. The token clause cannot
# reject this one — only P1's residual_step_succeeds(name) conjunct can.
_ATK_SWALLOW_FAIL = _swap(_GOLD_IMPL, _L5,
    "    # WRONG: perform the step, then swallow its failure and return a value.\n"
    "    try:\n"
    "        return residual_step(name)\n"
    "    except AttributeAccessError:\n"
    "        return residual_step_value(name)")

# (4e) the INVERTED-PATH cheat on leg 5: perform the step, and when it SUCCEEDS,
# raise anyway. REJECT on P2's (not residual_step_succeeds(name)).
_ATK_INVERT_RAISE = _swap(_GOLD_IMPL, _L5,
    "    # WRONG: perform the step, then fail even where it succeeded.\n"
    "    v = residual_step(name)\n"
    "    raise AttributeAccessError(residual_step_subject(name))")

# (5) PARTIAL-DOMAIN priority inversion: check frame_attr BEFORE alias. Correct
# wherever at most one guard is true, but on (is_alias AND is_frame_attr) it takes
# the frame-attr leg while P1's leg-1 clause pins alias_value. REJECT on that clause.
_ATK_SWAP_ALIAS_FRAME = _swap(_GOLD_IMPL, _L1 + "\n" + _L2 + "\n",
                              _L2 + "\n" + _L1 + "\n")

# (6) PARTIAL-DOMAIN dropped branch: omit the transform leg. On the sub-domain
# (only is_transform true) the impl falls through to the residual step, so it
# neither establishes transform_step_succeeds(name) nor holds the transform token.
_ATK_DROP_TRANSFORM = _swap(
    _GOLD_IMPL, _L4 + "\n",
    "    # WRONG: dropped the transform resolution leg entirely.\n")

# ---- rivals aimed at the PARTIALITY of legs 2-4 (the branches whose totality the
# ---- old spec over-claimed). Each is correct exactly where the leg's clause still
# ---- pins the value, and wrong where a total reading would have let it drift.

# (7) SWALLOW on a partial DOMAIN leg: perform the transform step but catch its
# failure and return the branch value anyway — i.e. behave as though the leg were
# total. This is the shape a spec that pins leg 4 unconditionally cannot see.
# REJECT on P1's leg-4 transform_step_succeeds(name) conjunct.
_ATK_SWALLOW_TRANSFORM = _swap(_GOLD_IMPL, _L4,
    "    if is_transform:\n"
    "        # WRONG: swallow the transform step's failure and return anyway.\n"
    "        try:\n"
    "            return transform_step(name, transform_value)\n"
    "        except AttributeAccessError:\n"
    "            return transform_value")

# (8) UNGROUNDED-ORACLE ECHO on a partial domain leg: branch on the pure selector
# oracle and produce both outcomes from the arguments, never performing the step.
# Every value equality holds by construction; REJECT on the leg's token.
_ATK_ECHO_TRANSFORM = _swap(_GOLD_IMPL, _L4,
    "    if is_transform:\n"
    "        # WRONG: derive both outcomes from the oracles; never perform the step.\n"
    "        if transform_step_succeeds(name):\n"
    "            return transform_value\n"
    "        raise AttributeAccessError(name)")

# (9) BORROWED TOKEN: on the passthrough leg, perform a DIFFERENT leg's step. It
# holds a token, and the value equality even holds, but not THIS leg's token/
# selector. REJECT on P1's leg-3 passthrough_step_succeeds(name).
_ATK_WRONG_TOKEN = _swap(_GOLD_IMPL, _L3,
    "    if is_frame_passthrough:\n"
    "        # WRONG: perform another leg's step and pass this leg's value off as its own.\n"
    "        return frame_attr_step(name, passthrough_value)")

# (10) INVERT on a partial domain leg: perform the frame-attribute step, then fail
# even where it succeeded. REJECT on P2's (not frame_attr_step_succeeds(name)).
_ATK_INVERT_FRAME_ATTR = _swap(_GOLD_IMPL, _L2,
    "    if is_frame_attr:\n"
    "        # WRONG: perform the step, then fail even where it succeeded.\n"
    "        v = frame_attr_step(name, frame_attr_value)\n"
    "        raise AttributeAccessError(name)")

# (11) leg 1 treated as PARTIAL: route the alias leg through the residual step.
# The alias leg is the one TOTAL step (its repo form cannot fail), so P1's
# unconditional Implies(is_alias, Result() == alias_value) rejects this.
_ATK_ALIAS_MAY_FAIL = _swap(_GOLD_IMPL, _L1,
    "    if is_alias:\n"
    "        # WRONG: make the total alias leg partial.\n"
    "        return residual_step(name)")


SPEC_TESTS = [
    {
        "id": "pos-elif-chain",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_ELIF),
        "rationale": "structurally-different correct impl (if-chain -> elif/else); "
                     "priority order preserved and every leg still performs its own "
                     "step. No new loop/lemma obligation, so it must verify; if not, "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-guard-negation-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_GUARDNEG),
        "rationale": "correct impl that handles the residual leg FIRST via the negated "
                     "disjunction, then the four guarded steps; behaviourally "
                     "identical, different shape. Must verify (soundness).",
    },
    {
        "id": "admiss-in-domain-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "Requires is only MustTerminate, so a representative F2P-shaped "
                     "input is accepted. If this cannot verify, PRECOND-TOO-STRONG.",
    },
    {
        "id": "atk-return-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_RETURN_NAME),
        "refinement": "Its faithful real patch would `return attr` on the residual "
                      "leg instead of surfacing that leg's outcome. The F2P test "
                      "test_subclass_property_exception_error does `with "
                      "pytest.raises(AttributeError, match='random_attr'): c.prop` — "
                      "a normal return raises NO AttributeError, so the test reports "
                      "DID NOT RAISE and the patch does NOT resolve.",
        "rationale": "rejects on P1's leg-5 clause: a normal return must be the "
                     "residual step's own success passed through — "
                     "residual_step_succeeds(name) and "
                     "Result() == residual_step_value(name) and the token. Returning "
                     "`name` establishes none of them.",
    },
    {
        "id": "atk-return-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_RETURN_ALIAS),
        "refinement": "A real patch returning some unrelated resolving value on the "
                      "residual leg likewise never raises, so the F2P test's "
                      "pytest.raises(AttributeError, ...) fails: not resolved.",
        "rationale": "rejects on P1's leg-5 clause: alias_value is neither "
                     "residual_step_value(name) nor accompanied by the token.",
    },
    {
        "id": "atk-raise-requested-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_RAISE_NAME),
        "refinement": "This is the PRE-PATCH behaviour: raise AttributeError naming "
                      "the requested attr (`'...' object has no attribute 'prop'`). "
                      "The F2P test asserts match='random_attr' (the INNER name), so a "
                      "failure blaming 'prop' does NOT match and the patch does NOT "
                      "resolve — exactly the regression gh-8340 addresses.",
        "rationale": "rejects on P2/P3: the leg-5 selector "
                     "(not residual_step_succeeds(name)) is not established, and "
                     "RaisedException().subject must equal residual_step_subject(name), "
                     "which the opaque @Pure oracle is NOT assumed to equal `name`.",
    },
    {
        "id": "atk-raise-forged-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_RAISE_TOKEN),
        "refinement": "Raising while blaming an arbitrary unrelated value (not the "
                      "name the residual resolution found missing) cannot match the "
                      "F2P's match='random_attr'. Not resolved.",
        "rationale": "rejects on P3: the forged subject is not "
                     "residual_step_subject(name), and the impl holds no token.",
    },
    {
        "id": "atk-echo-oracle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_ECHO_ORACLE),
        "refinement": "A faithful real patch for this impl must produce, on the "
                      "residual leg, 'the name that resolution WOULD find missing' "
                      "while never performing the resolution — but the repo has no "
                      "standalone oracle for that value, so any materialization "
                      "either performs the step after all (a different impl) or "
                      "fabricates a message and cannot in general match the inner "
                      "missing name. Diverges from the pinned conduit behaviour.",
        "rationale": "rejects on P3's EFFECT clause: the failure must carry "
                     "residual_step_performed(name), granted ONLY by the step itself; "
                     "echoing the @Pure oracle satisfies the subject equality but "
                     "cannot present the unforgeable token, and the leg's selector is "
                     "never established either.",
    },
    {
        "id": "atk-echo-value-oracle",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_ECHO_VALUE),
        "refinement": "The mirror of the echo cheat on leg 5's returning path: a real "
                      "patch would have to produce 'the value the residual resolution "
                      "WOULD yield' without performing it, but the only way to obtain "
                      "that value is to perform the step. An impl that does not "
                      "perform it cannot surface that step's outcome.",
        "rationale": "rejects on P1's leg-5 EFFECT clause: the returned value must be "
                     "accompanied by residual_step_performed(name); echoing the @Pure "
                     "value oracle matches the value but cannot present the token.",
    },
    {
        "id": "atk-swallow-step-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_SWALLOW_FAIL),
        "refinement": "A real patch that wrapped the residual leg in try/except and "
                      "returned a value instead of letting the AttributeError "
                      "propagate would make the F2P scenario raise NOTHING: "
                      "test_subclass_property_exception_error would report DID NOT "
                      "RAISE. Not resolved.",
        "rationale": "rejects on P1's leg-5 selector conjunct "
                     "residual_step_succeeds(name): this impl DOES perform the step, so "
                     "it holds the token legitimately and neither the token nor the "
                     "value clause can reject it — only the selector can, because it "
                     "returns normally where the step FAILED. This is the rival that "
                     "makes the conduit property load-bearing.",
    },
    {
        "id": "atk-invert-step-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_INVERT_RAISE),
        "refinement": "A real patch that performed the residual leg and then raised "
                      "regardless would turn every name that leg resolves (plain class "
                      "attributes, dunders, bound methods) into an AttributeError, "
                      "breaking ordinary attribute access on SkyCoord instances that "
                      "the P2P suite exercises. Not resolved.",
        "rationale": "rejects on P2's (not residual_step_succeeds(name)): the leg may "
                     "surface a failure only where its step failed, so raising after a "
                     "successful step is illegal.",
    },
    {
        "id": "atk-priority-swap-alias-frame",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_SWAP_ALIAS_FRAME),
        "refinement": "Checking the frame-attribute resolution before the frame-name "
                      "alias inverts the documented priority (sky_coordinate.py: "
                      "_is_name is tried first). On any object where both apply the "
                      "real patch would return the wrong resolution, changing "
                      "observable attribute resolution the P2P suite pins.",
        "rationale": "PARTIAL-DOMAIN: rejects on P1's leg-1 clause "
                     "Implies(is_alias, Result()==alias_value) on the sub-domain "
                     "is_alias AND is_frame_attr.",
    },
    {
        "id": "atk-drop-transform-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_DROP_TRANSFORM),
        "refinement": "Dropping the transform resolution means a transformable target "
                      "name (only is_transform true) is no longer resolved by that "
                      "leg, breaking the transform-resolution behaviour the P2P "
                      "transform tests exercise — not resolved.",
        "rationale": "PARTIAL-DOMAIN: on the sub-domain (only is_transform true) the "
                     "impl performs the RESIDUAL step, so it establishes neither "
                     "transform_step_succeeds(name) nor the transform token that P1's "
                     "leg-4 clause requires.",
    },
    {
        "id": "atk-swallow-transform-step",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_SWALLOW_TRANSFORM),
        "refinement": "The transform step is PARTIAL in the repo: for a registered "
                      "frame name whose transform cannot be carried out on this "
                      "coordinate, `self.transform_to(attr)` itself raises, and the "
                      "resolver surfaces that failure. An impl that catches it and "
                      "returns the branch value instead reports a value where the real "
                      "function fails, so it is not behaviourally equal to the gold "
                      "patch on that class of names.",
        "rationale": "rejects on P1's leg-4 conjunct transform_step_succeeds(name): the "
                     "leg performs the step, so it holds the token legitimately and "
                     "the value equality even holds — only the selector sees that it "
                     "returned where the step FAILED. This is the rival a spec that "
                     "pinned leg 4 as TOTAL could not express at all.",
    },
    {
        "id": "atk-echo-transform-step",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_ECHO_TRANSFORM),
        "refinement": "An UNGROUNDED-ORACLE echo on the transform leg: it derives both "
                      "outcomes from its arguments and the pure selector without ever "
                      "carrying out the transform. No repo expression yields 'whether "
                      "the transform would succeed' without attempting it, and on the "
                      "failing side it blames the requested name rather than surfacing "
                      "the step's own failure. Not the gold behaviour.",
        "rationale": "rejects on P1's leg-4 EFFECT clause: the return must carry "
                     "transform_step_performed(name), an opaque bodyless @Predicate "
                     "whose sole producers are the step's own two paths, so nothing "
                     "can Fold it into existence.",
    },
    {
        "id": "atk-borrowed-step-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_WRONG_TOKEN),
        "refinement": "On the passthrough leg it performs a DIFFERENT leg's step and "
                      "passes that off as this leg's work. In the repo the two legs "
                      "read different state and can succeed or fail independently, so "
                      "this reports one leg's outcome for the other — not the gold "
                      "behaviour.",
        "rationale": "rejects on P1's leg-3 conjuncts: each leg's token and selector "
                     "are per-step, so a token earned by frame_attr_step does not "
                     "discharge passthrough_step_succeeds(name) or "
                     "passthrough_step_performed(name).",
    },
    {
        "id": "atk-invert-frame-attr-step",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_INVERT_FRAME_ATTR),
        "refinement": "Performing the frame-attribute step and then failing anyway "
                      "turns every successfully-produced frame attribute into an "
                      "AttributeError, breaking the frame-attribute access the P2P "
                      "suite exercises. Not resolved.",
        "rationale": "rejects on P2's per-leg conjunct "
                     "(not frame_attr_step_succeeds(name)): a leg may fail only where "
                     "its own step failed.",
    },
    {
        "id": "atk-alias-leg-made-partial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ATK_ALIAS_MAY_FAIL),
        "refinement": "The alias leg is the one TOTAL step in the repo (`return self` "
                      "cannot fail). Routing it through the residual step changes the "
                      "outcome for every frame-name alias — the P2P suite's alias "
                      "accesses would resolve differently or fail. Not resolved.",
        "rationale": "rejects on P1's leg-1 clause, which is unconditional: "
                     "Implies(is_alias, Result() == alias_value) admits no selector or "
                     "token escape, so the alias leg cannot be made partial. This is "
                     "the control confirming the repair did NOT relax leg 1.",
    },
]


# ------------------------------------------------------------------ AXIOM lane
# The @ContractOnly step axioms model the FIVE candidate resolutions, each an
# UNCHANGED callee the resolver invokes. Four of them are PARTIAL and each states
# both of its paths, tied to its own @Pure selector:
#   * frame_attr_step / passthrough_step / transform_step: where
#     `*_step_succeeds(name)` they return the branch value, otherwise they fail.
#   * residual_step: where `residual_step_succeeds(name)` it yields
#     `residual_step_value(name)`; otherwise it fails, surfacing an
#     AttributeAccessError whose subject == `residual_step_subject(name)` — the
#     name that resolution found missing, which the proof crucially does NOT
#     assume equals `name`.
# None of them is claimed to ALWAYS fail nor to ALWAYS return, which is why every
# consumer clause is conditional on the step's own selector rather than asserting
# a total branch.
#
# The probes EXECUTE the real callee (never scrape source). axiom_check.py is the
# G-AX ground truth; we embed its proven construction. Files opened utf-8. The
# callees are unchanged by the patch, so apply_gold is not required (we set False;
# the soundness facts hold on the unpatched repo, per mapping.md §3.1).

# Read the bundle's G-AX oracle on the HOST at load time; the runner mounts ONLY
# the probe at /work, so its source is embedded into the probe string below.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# axiom-soundness probe: run the real SkyCoord.__getattribute__ and confirm the
# Exsures (surfaces an AttributeError blaming the INNER missing name, != requested
# name) + determinism, over boundary + fuzz pairs. This IS axiom_check.py's main().
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC

# axiom-containment probe: the axiom Requires domain is unconstrained (name: int,
# i.e. ANY attribute name). The model passes ONLY its own input `name` to
# residual_step / residual_step_subject (impl: `return residual_step(name)`),
# never a derived value. So every caller-reachable input is trivially in-domain.
# We confirm soundly that the real callee ACCEPTS arbitrary names (no domain
# precondition the model could violate): for boundary/sentinel names + fuzz, the
# real __getattribute__ either resolves or raises AttributeError — it never rejects
# a name as out-of-domain. A reachable name the callee could not accept would mean
# AXIOM-TOO-WEAK-FOR-CALLER; none exists.
_AX_CONTAIN_PROBE = r'''#!/usr/bin/env python3
"""axiom-containment probe for astropy__astropy-14096.

The consumed axioms residual_step_subject / residual_step have an
UNCONSTRAINED Requires domain (name: int = any attribute name). The model's impl
passes ONLY its own input `name` to them (`return residual_step(name)`), never a
derived/narrowed value, so every caller-reachable input lies in the axiom domain
by construction. This probe confirms soundly, against the REAL callee, that
object.__getattribute__ on a SkyCoord accepts arbitrary attribute names without
any out-of-domain rejection: it either returns a value or raises AttributeError
(the modelled failing path). No name is rejected as outside the callee's domain,
so the axiom domain (all names) covers everything the caller can reach. Exit 0 iff
every probed name is accepted into the lookup (resolves or raises AttributeError).
"""
import random
import string
import sys

from astropy.coordinates import SkyCoord


def _make_coord():
    return SkyCoord("00h42m30s", "+41d12m00s", frame="icrs")


def _accepts(obj, name):
    """The lookup mechanism accepts `name` into its domain iff calling
    __getattribute__(name) either returns or raises AttributeError (the modelled
    failing path). Any OTHER outcome (e.g. TypeError on a malformed key) would be
    an out-of-domain name the axiom does not cover -> containment failure."""
    try:
        obj.__getattribute__(name)
        return True  # resolved normally: in-domain
    except AttributeError:
        return True  # the modelled failing path: in-domain
    except Exception as e:  # noqa: BLE001
        print("CONTAINMENT FAIL: __getattribute__(%r) raised non-AttributeError "
              "%s: %s" % (name, type(e).__name__, e))
        return False


def main():
    obj = _make_coord()

    # boundary + sentinel names the caller could reach (incl. dunders, empties,
    # very long, unicode-ish ascii, names colliding with real attributes).
    boundary = [
        "prop", "random_attr", "a", "_", "__weird__", "x" * 200,
        "name", "frame", "ra", "dec", "transform_to", "0starts_digit",
        "has space", "", "_sky_coord_frame",
    ]
    for nm in boundary:
        if not _accepts(obj, nm):
            return 1

    rng = random.Random(140962)
    n = 0
    while n < 200:
        ln = rng.randint(0, 16)
        nm = "".join(rng.choice(string.ascii_letters + string.digits + "_")
                     for _ in range(ln))
        if not _accepts(obj, nm):
            return 1
        n += 1

    print("CONTAINMENT OK: real __getattribute__ accepts every caller-reachable "
          "name (resolves or raises AttributeError) over %d boundary + %d fuzz "
          "names; the unconstrained axiom domain covers all reachable inputs."
          % (len(boundary), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-getattribute-blames-inner",
        "axiom": "residual_step",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": False,  # __getattribute__ is UNCHANGED by the patch (mapping.md §3.1)
        "probe": _AX_SOUND_PROBE,
        "rationale": "executes the real SkyCoord.__getattribute__ (G-AX ground "
                     "truth, axiom_check.py): a property reading a missing inner attr "
                     "surfaces an AttributeError blaming the INNER name (not the "
                     "requested name) + determinism, over boundary + 300 fuzz pairs, "
                     "and the degenerate plain-missing case blames itself. If the "
                     "real callee disagreed with the Exsures, AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-name-domain",
        "axiom": "residual_step_subject",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": False,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "the axiom Requires is unconstrained (any name) and the model "
                     "passes only its own input `name`; this confirms the real callee "
                     "accepts every caller-reachable name (resolves or raises "
                     "AttributeError), so no reachable input falls outside the axiom "
                     "domain. A non-AttributeError rejection would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
