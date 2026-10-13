# properties.py — PBT manifest for django__django-14238.
#
# NOT a Nagini module; an adversarial falsification battery the runner
# (swebench_nagini.pbt) parses.  Each SPEC_TESTS case is a FULL model.py variant
# that shares the FROZEN spec (markers.same_spec) and edits ONLY the impl region
# (between `# impl-start` and `# impl-end`); it is checked by re-running Nagini.
# AXIOM_TESTS are self-contained Docker probes for the A-reference deep model.
#
# Defended surface (read model.py):
#   subclass_check(owner, base_one, base_two, candidate : Cls) -> bool
#   * EVERY param is READ-ONLY: held at Acc(x.cid,1/4) and Acc(x.anc,1/4) in BOTH
#     Requires AND Ensures (1/4 framed back unchanged; writing needs full 1/1).
#   * LOAD-BEARING postcondition:
#       Result() == ( is_subtype(candidate, base_one)
#                  or is_subtype(candidate, base_two)
#                  or is_subtype(candidate, owner) )
#   * is_subtype is a @Pure helper GROUNDED in the args (`base.cid in sub.anc`),
#     fully unfolded by the verifier — NOT an opaque answer-key oracle, so there
#     is no "wrong echo" to build (see assessment).  The discriminating content
#     of the gold change is structural-subtype membership (a proper subclass of a
#     registered base is a member) vs the pre-patch identity membership.
#
from pathlib import Path

INSTANCE = "django__django-14238"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl region body (between the markers).  Every variant is built
# by _swap on this unique block, so edits are confined to the impl region and
# same_spec is guaranteed.
_GOLD_IMPL = (
    "    if is_subtype(candidate, base_one):\n"
    "        return True\n"
    "    if is_subtype(candidate, base_two):\n"
    "        return True\n"
    "    return is_subtype(candidate, owner)"
)
assert _GOLD_IMPL in _BASE, "impl drift: gold impl body not found verbatim"


def _impl(body):
    """Replace the gold impl body with `body` (keeps markers intact)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # -- POSITIVE CONTROL (soundness): structurally-different but CORRECT -----
    # Reorder the three rungs (owner-leg first, then the two registered bases)
    # and collapse to a single short-circuit boolean expression bound to a typed
    # local.  Semantically identical disjunction, different executable shape; the
    # postcondition is order-insensitive so the gold proof obligation still
    # discharges.  Must VERIFY (else SPEC-TOO-STRONG).
    {
        "id": "pos-reorder-expr",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    decision = is_subtype(candidate, owner) or is_subtype(candidate, base_two) or is_subtype(candidate, base_one)  # type: bool\n"
            "    return decision"
        ),
        "rationale": "a correct impl with reordered rungs / single bool expr must "
                     "verify; the postcondition is an order-insensitive disjunction "
                     "of grounded @Pure calls, so the gold proof still discharges. "
                     "If it fails => SPEC-TOO-STRONG.",
    },

    # -- POSITIVE CONTROL #2: nested-if shape, owner leg interleaved ----------
    # Different control structure (compute each leg into a local, OR at the end)
    # but the same total decision.  Keeps the proof trivial (no induction needed).
    {
        "id": "pos-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    a = is_subtype(candidate, base_one)  # type: bool\n"
            "    b = is_subtype(candidate, base_two)  # type: bool\n"
            "    c = is_subtype(candidate, owner)  # type: bool\n"
            "    return a or b or c"
        ),
        "rationale": "structurally different (three locals, single return) but the "
                     "identical disjunction; must verify (else SPEC-TOO-STRONG).",
    },

    # -- ADMISSIBILITY: precondition admits a normal F2P-shaped call ----------
    # Keep the gold decision but first Assert that the @Pure oracle is callable
    # and unfolds correctly from the held 1/4 permission (is_subtype needs only
    # 1/8 per arg).  If the Requires were too strong this Assert / the is_subtype
    # calls could not be established for an in-domain input => PRECOND-TOO-STRONG.
    {
        "id": "admiss-unfold",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    Assert(is_subtype(candidate, owner) == (owner.cid in candidate.anc))\n"
            "    Assert(is_subtype(candidate, base_one) == (base_one.cid in candidate.anc))\n"
            "    if is_subtype(candidate, base_one):\n"
            "        return True\n"
            "    if is_subtype(candidate, base_two):\n"
            "        return True\n"
            "    return is_subtype(candidate, owner)"
        ),
        "rationale": "the precondition must admit a normal input: the 1/4 perms must "
                     "establish is_subtype's 1/8 Requires and unfold the @Pure body. "
                     "If the Assert / calls cannot be discharged => PRECOND-TOO-STRONG.",
    },

    # -- FRAME-MUTATION (MANDATORY; reject): write a read-only input ----------
    # All params are held at 1/4 permission — read-only.  This rival WRITES
    # candidate.cid (forcing identity with base_one) to make a cheap check pass.
    # Writing a field needs FULL Acc(candidate.cid) = 1/1; only 1/4 is held, so
    # this MUST be rejected for INSUFFICIENT PERMISSION.  The gold spec/postcond
    # are kept verbatim so the rejection is attributable to the write.
    {
        "id": "frame-write-cid",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    candidate.cid = base_one.cid  # frame violation: needs full perm\n"
            "    if is_subtype(candidate, base_one):\n"
            "        return True\n"
            "    if is_subtype(candidate, base_two):\n"
            "        return True\n"
            "    return is_subtype(candidate, owner)"
        ),
        "refinement": "the faithful real patch — mutating the candidate class's "
                      "identity inside __subclasscheck__ — would corrupt the class "
                      "object and could not resolve the F2P (it does not implement "
                      "structural-subtype membership; it falsifies identity). The "
                      "spec must reject the write itself.",
        "rationale": "params held at Acc(.,1/4): a write to candidate.cid needs full "
                     "1/1 permission and is rejected by the permission system (NOT by "
                     "the postcondition). Frame-mutation, the #1 weakness class.",
    },

    # -- FRAME-MUTATION #2 (reject): write candidate.anc ----------------------
    # A subtler vacuous satisfier: overwrite the candidate's ancestry set so the
    # grounded is_subtype reads back TRUE.  Again needs full perm on candidate.anc
    # (only 1/4 held) => rejected for insufficient permission.
    {
        "id": "frame-write-anc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    candidate.anc = owner.anc  # frame violation: needs full perm to write\n"
            "    return is_subtype(candidate, owner)"
        ),
        "refinement": "rewriting the candidate's MRO/ancestry inside the membership "
                      "test is not the gold change (structural membership against the "
                      "REAL ancestry); it would mutate shared class state and not "
                      "resolve the F2P. The spec rejects the write.",
        "rationale": "Acc(candidate.anc,1/4) is read-only; assigning candidate.anc "
                     "needs full permission => insufficient-permission rejection.",
    },

    # -- PARTIAL-DOMAIN #1 (reject): drop the base_two rung (the prepatch-shaped
    #    partial fix).  Correct on the BigAutoField-subclass F2P, WRONG on the
    #    SmallAutoField sub-domain.  Shares the spec; must be rejected by the
    #    postcondition's `or is_subtype(candidate, base_two)` clause.
    {
        "id": "partial-drop-base2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_subtype(candidate, base_one):\n"
            "        return True\n"
            "    return is_subtype(candidate, owner)"
        ),
        "refinement": "a real patch that only checked issubclass(subclass, "
                      "BigAutoField) (dropping SmallAutoField) leaves the "
                      "SmallAutoField branch buggy: a SmallAutoField subclass set as "
                      "DEFAULT_AUTO_FIELD still fails Options._get_default_pk_class's "
                      "issubclass(pk_class, AutoField) guard, so the F2P "
                      "test_default_auto_field_setting (small-side) / "
                      "test_issubclass_of_autofield would not all pass.",
        "rationale": "rejected by the postcondition clause "
                     "`or is_subtype(candidate, base_two)`: for a candidate that is a "
                     "subtype of base_two only, the gold disjunction is True but this "
                     "impl returns is_subtype(candidate, owner)=False.",
    },

    # -- PARTIAL-DOMAIN #2 (reject): the EXACT pre-patch bug — identity --------
    # membership instead of structural-subtype membership.  This is the bug the
    # gold patch fixes (subclass in self._subclasses -> issubclass(...)).  Uses
    # cid equality (identity) on the two bases.  WRONG for any proper subclass of
    # a registered base; the discriminating F2P input.
    {
        "id": "partial-identity-membership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if candidate.cid == base_one.cid:\n"
            "        return True\n"
            "    if candidate.cid == base_two.cid:\n"
            "        return True\n"
            "    return is_subtype(candidate, owner)"
        ),
        "refinement": "this IS the pre-patch behaviour (subclass in self._subclasses): "
                      "identity membership. For a user subclass MyBigAutoField the "
                      "decision is False, so issubclass(MyBigAutoField, AutoField) is "
                      "False -> test_issubclass_of_autofield and "
                      "test_default_auto_field_setting_bigautofield_subclass FAIL. The "
                      "faithful real patch (pre-patch source) is exactly what the gold "
                      "fix replaces; it does NOT resolve (G-DIFF / model_prepatch.py).",
        "rationale": "rejected by the postcondition: identity `candidate.cid == "
                     "base_one.cid` is strictly weaker than `is_subtype(candidate, "
                     "base_one)` (base_one.cid in candidate.anc) — a proper subclass "
                     "makes is_subtype True but cid-equality False, so the disjunction "
                     "differs from Result().",
    },

    # -- PARTIAL-DOMAIN #3 (reject): drop the owner (super) leg ---------------
    # Keeps both registered-base rungs but returns False instead of the owner
    # leg.  Correct for registered-base subclasses, WRONG for an owner-subclass
    # (e.g. a direct AutoField subclass) that the super().__subclasscheck__ leg
    # must accept.
    {
        "id": "partial-drop-owner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_subtype(candidate, base_one):\n"
            "        return True\n"
            "    if is_subtype(candidate, base_two):\n"
            "        return True\n"
            "    falsy = False  # type: bool\n"
            "    return falsy"
        ),
        "refinement": "dropping super().__subclasscheck__(subclass) makes the "
                      "metaclass reject a candidate that is an ordinary subclass of "
                      "AutoField itself (the owner leg). isinstance/issubclass of an "
                      "AutoField subclass would break — the unchanged super() leg is "
                      "load-bearing; such a patch would not pass the autofield "
                      "PASS_TO_PASS / F2P suite.",
        "rationale": "rejected by the postcondition clause "
                     "`or is_subtype(candidate, owner)`: for an owner-subtype that is "
                     "neither base's subtype, the gold disjunction is True but this "
                     "impl returns False.",
    },

    # -- PARTIAL-DOMAIN #4 (reject): swap one base for owner (subtle drift) ---
    # Checks owner TWICE and never base_two.  A near-miss that looks like the
    # gold shape but silently omits the base_two sub-domain.
    {
        "id": "partial-dup-owner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if is_subtype(candidate, base_one):\n"
            "        return True\n"
            "    if is_subtype(candidate, owner):\n"
            "        return True\n"
            "    return is_subtype(candidate, owner)"
        ),
        "refinement": "checking owner twice and never base_two means a SmallAutoField "
                      "subclass (subtype of base_two only) is wrongly rejected — same "
                      "failure mode as partial-drop-base2; would not resolve the "
                      "small-side default-pk / issubclass F2P.",
        "rationale": "rejected by `or is_subtype(candidate, base_two)`: the impl never "
                     "consults base_two, so it differs from Result() on a base_two-only "
                     "subtype.",
    },

    # -- OVER-ACCEPT (reject): always return True -----------------------------
    # Trivial too-permissive rival: accepts everything.  Correct on members,
    # WRONG on every non-member (Unrelated, plain IntegerField).  Cheap
    # supporting case; rejected by the postcondition for non-members.
    {
        "id": "over-accept-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    truthy = True  # type: bool\n"
            "    return truthy"
        ),
        "refinement": "accepting every class as an AutoField subclass would make "
                      "isinstance/issubclass of unrelated classes True, breaking "
                      "test_isinstance_of_autofield and the non-AutoField default-pk "
                      "guards; not a resolving patch.",
        "rationale": "rejected by the postcondition: for a candidate that is a subtype "
                     "of none of base_one/base_two/owner the gold disjunction is False "
                     "but this returns True.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# There is NO @ContractOnly axiom in this bundle (meta.axioms == []).  The
# structural-subtype query is a deep model (A-reference) `is_subtype`, validated
# == the real Python `issubclass` / `type.__subclasscheck__` by axiom_check.py
# (G-AX).  Per PBT_PLAN §2.4 an A-reference deep model is checked the same way
# as an axiom (deep model == real callee on every CALLER-REACHABLE input).  We
# carry ONE strong soundness+containment probe that EXECUTES the real builtin
# (never scrapes source) over the structural class replica + the real Django
# AutoFieldMeta when importable, mirroring/strengthening axiom_check.py.

# Read the bundle oracle on the HOST at load time and embed it into the probe
# (the runner mounts ONLY the probe at /work; axiom_check.py is NOT in-container).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AX_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "# --- embedded bundle oracle (axiom_check.py), read on host at load time ---\n"
    "_ORACLE_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '_embedded_axiom_check'}\n"
    "exec(compile(_ORACLE_SRC, 'axiom_check.py', 'exec'), g)\n"
    "# Run the oracle's main(): it EXECUTES the real issubclass / "
    "type.__subclasscheck__\n"
    "# on every ordered pair of the structural replica (and the real Django\n"
    "# AutoFieldMeta when importable in-container), asserting the deep model\n"
    "# is_subtype == the real callee, and the modeled decision == the real\n"
    "# metaclass decision.  Exit 0 iff every obligation holds.\n"
    "rc = g['main']()\n"
    "print('A-reference deep model soundness+containment: PASS' if rc == 0 "
    "else 'FAIL')\n"
    "sys.exit(rc)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-ref-is_subtype-sound",
        "axiom": "is_subtype",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "A-reference deep model: is_subtype(sub,base) == "
                     "(base.cid in sub.anc) must EQUAL the real Python "
                     "issubclass / type.__subclasscheck__ on every caller-reachable "
                     "(sub,base) pair, and subclass_check's modeled decision must "
                     "equal the real metaclass decision (issubclass(cand,(b1,b2)) or "
                     "super().__subclasscheck__). The probe executes the REAL callee "
                     "(no source scraping) over the structural replica + real Django "
                     "AutoFieldMeta when importable. A disagreement => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-ref-is_subtype-containment",
        "axiom": "is_subtype",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_PROBE
                 + "# Containment note: subclass_check only ever passes Cls "
                   "carriers\n"
                   "# (cid:int, anc:PSet[int] with cid in anc) to is_subtype; the "
                   "real\n"
                   "# callee is total over all class pairs, so every caller-reachable "
                   "input\n"
                   "# (any (sub,base) class pair) lies in the callee's domain — the "
                   "probe\n"
                   "# above exercises the full universe, establishing containment.\n",
        "rationale": "containment: every (sub,base) the model can reach is a pair of "
                     "ordinary classes; is_subtype/issubclass is total over class "
                     "pairs (no excluded sub-domain), so the caller never reaches an "
                     "input outside the deep model's domain. A reachable input the "
                     "deep model mishandled would have failed the soundness probe.",
    },
]
