"""properties.py — PBT falsification battery for django__django-11149.

NOT a Nagini module: a manifest of adversarial cases the runner
(swebench_nagini.pbt) executes (host verify + same_spec for spec cases; Docker
for axiom cases). Each spec variant is built by region-surgery on the FROZEN
model.py — editing ONLY text inside an impl region (`# impl-start`/`# impl-end`,
including the nested `# invariants-start`/`# invariants-end`) so the spec
signature is provably untouched (markers.same_spec == True).

================================  DEFENDED SURFACE  ===========================

Five modeled functions, all over the SAME read-only carrier `held: PSet[int]`
(the actor's held permission codes for the target record):

  target_decision(held, required)            -> Result() == holds_any(held, required)
  inline_inspect_decision(held, ins, mod)    -> Result() == ((ins in held) or (mod in held))
  inline_create_decision(held, ins, mod)     -> Result() == (mod in held)
  inline_modify_decision(held, ins, mod)     -> Result() == (mod in held)
  inline_remove_decision(held, ins, mod)     -> Result() == (mod in held)

Load-bearing clauses:
  * `target_decision`  postcondition is pinned to `holds_any`, the existential
    `Exists j: 0<=j<len(required) and required[j] in held` — the FULL "holds any
    of the required codes", not just the first. A rival that checks only the
    first required code passes on inspect ({ins,mod} with ins held) but FAILS
    when only a LATER required code is held (held={mod}); the spec must reject it.
  * The THREE editing decisions (create/modify/remove) pin `Result() == (mod in
    held)` — the BUG FIX. The pre-patch returned the VIEW rule (delegated to
    `has_view_permission`, i.e. required = {inspect, modify}); a rival using
    `PSeq(inspect_code, modify_code)` for any of the three is exactly the
    regression — correct when `mod in held`, WRONG on the inspect-only sub-domain
    (held={ins}: it returns True, the spec demands False). This is precisely what
    the F2P tests `test_inline_add_m2m_view_only_perm` /
    `test_inline_change_m2m_view_only_perm` assert (a view-only actor must NOT be
    able to add/change/delete the auto-created M2M inline).

READ-ONLY input (directive 5): every function requires AND ensures
`Acc(set_pred(held), 1/2)` — `held` is read-only.  has_readonly_input = True =>
the FRAME-MUTATION reject case is MANDATORY.  Here the frame attack takes the
form available against a `set_pred`-guarded input: a rival whose loop demands
FULL write permission `Acc(set_pred(held), 1)` (the permission an impl that
intends to *mutate* the actor's grant would need). With only the 1/2 the
precondition grants, the verifier rejects it for INSUFFICIENT PERMISSION on
`set_pred(held)` — attributable to the permission system, not the value
postcondition. (Note: the PSet carrier is itself immutable, so an in-place
`.add`/index-write does not exist; the genuine, attributable permission failure
is the full-permission demand, which is what we use. Confirmed it fails with
"There might be insufficient permission to access set_pred(held)".)

UNGROUNDED-ORACLE (directive 2): N/A. `holds_any` is a @Pure helper but a FULLY
GROUNDED total function of the inputs (`Exists j: 0<=j<len(required) and
required[j] in held`) — there is no opaque answer-key to echo without doing the
work; "echoing" `holds_any(held, required)` IS computing the spec. We therefore
include honest positive controls (a structurally-different correct impl + the
cheapest correct delegation) instead of a wrong-echo reject.

VALUE-DOUBLE-MASK: N/A — the result is a single bool, not an index/structural
claim mediated by a value proxy that could drop disagreeing indices.

CONTROL-FLOW-EFFECT: N/A — the decisions are pure total booleans; there is no
raise / return-channel / side-effect distinction invisible to the value
abstraction, so a capability-token rival has nothing to discriminate.

AXIOMS: none. meta.axioms == [], deep_model_references == [], no @ContractOnly
callee (refinement.md §C / mapping.md §3). AXIOM_TESTS = [].

All six SPEC cases were pre-validated on the host verifier during construction:
the three reject rivals fail (frame-mut => insufficient permission; first-only =>
holds_any postcondition; create-view-rule => `mod in held` postcondition), and
the two positive controls + the admissibility caller verify, each with
same_spec == True.
"""
from pathlib import Path

INSTANCE = "django__django-11149"
FLOAT_ENCODING = None  # meta.float_encoding is null; integer permission codes, no --float-encoding

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors — every one lies strictly inside an impl region (impl-start/impl-end,
# or the nested invariants block), so same_spec is preserved by construction.
# ---------------------------------------------------------------------------

# (1) frame-mutation: the loop framing invariant of target_decision.
_FRAME_INV_OLD = "        Invariant(Acc(set_pred(held), 1 / 2))\n"
_FRAME_INV_NEW = "        Invariant(Acc(set_pred(held), 1))\n"

# (2) positive control: the whole target_decision impl body (front-to-back
#     short-circuit loop) replaced by a found-flag accumulator (no early return).
_TGT_IMPL_OLD = (
    "    # impl-start\n"
    "    i = 0\n"
    "    while i < len(required):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(set_pred(held), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(required))\n"
    "        # The loop consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure len(required) - i.\n"
    "        Invariant(MustTerminate(len(required) - i))\n"
    "        Invariant(Forall(int, lambda k: Implies(\n"
    "            0 <= k and k < i, not (required[k] in held))))\n"
    "        # invariants-end\n"
    "        if required[i] in held:\n"
    "            return True\n"
    "        i = i + 1\n"
    "    return False\n"
    "    # impl-end"
)
_TGT_IMPL_PC = (
    "    # impl-start\n"
    "    # POSITIVE CONTROL: a structurally-different but correct impl — a\n"
    "    # found-flag accumulator that scans the whole list (no early return).\n"
    "    found = False\n"
    "    i = 0\n"
    "    while i < len(required):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(set_pred(held), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(required))\n"
    "        Invariant(MustTerminate(len(required) - i))\n"
    "        Invariant(found == Exists(int, lambda k:\n"
    "            0 <= k and k < i and required[k] in held))\n"
    "        # invariants-end\n"
    "        if required[i] in held:\n"
    "            found = True\n"
    "        i = i + 1\n"
    "    return found\n"
    "    # impl-end"
)
# (2b) first-only WRONG rival of target_decision (uniqueness / partial-domain).
_TGT_IMPL_FIRST = (
    "    # impl-start\n"
    "    # WRONG: only consults the FIRST required code; correct when the first\n"
    "    # element decides, but drops the existential over the rest.\n"
    "    if len(required) > 0:\n"
    "        return required[0] in held\n"
    "    return False\n"
    "    # impl-end"
)

# (3) per-decision view-rule rivals — swap PSeq(modify_code) -> the {inspect,
#     modify} view rule (the pre-patch regression) for create / modify / remove.
def _viewrule_anchor(comment):
    return (
        comment
        + "    Ensures(Result() == (modify_code in held))\n"
        "    # post-conditions-end\n"
        "    # impl-start\n"
        "    required = PSeq(modify_code)\n"
    )


_CREATE_OLD = _viewrule_anchor(
    "    # Create is permitted iff the actor holds the MODIFY code; the inspect code\n"
    "    # alone must NOT permit it.\n"
)
_MODIFY_OLD = _viewrule_anchor(
    "    # Modify is permitted iff the actor holds the MODIFY code.\n"
)
_REMOVE_OLD = _viewrule_anchor(
    "    # Remove is permitted iff the actor holds the MODIFY code.\n"
)


def _to_viewrule(anchor):
    return anchor.replace(
        "    required = PSeq(modify_code)\n",
        "    required = PSeq(inspect_code, modify_code)\n",
    )


# (4) cheapest-correct positive control: create decision delegating with the
#     correct single-code list but spelled inline (a different-but-correct shape).
_CREATE_CHEAP_NEW = (
    "    # Create is permitted iff the actor holds the MODIFY code; the inspect code\n"
    "    # alone must NOT permit it.\n"
    "    Ensures(Result() == (modify_code in held))\n"
    "    # post-conditions-end\n"
    "    # impl-start\n"
    "    # cheapest correct impl: the grounded membership test itself.\n"
    "    return modify_code in held\n"
)
_CREATE_CHEAP_OLD = _CREATE_OLD + "    return target_decision(held, required)\n"
_CREATE_CHEAP_REPL = _CREATE_CHEAP_NEW

# (5) admissibility caller: inside inline_inspect_decision, assert the
#     precondition admits a normal F2P-shaped input (distinct codes + read perm),
#     then delegate exactly as the gold does.
_INSPECT_IMPL_OLD = (
    "    # impl-start\n"
    "    required = PSeq(inspect_code, modify_code)\n"
    "    return target_decision(held, required)\n"
    "    # impl-end"
)
_INSPECT_IMPL_ADMISS = (
    "    # impl-start\n"
    "    # ADMISSIBILITY: the precondition accepts a normal F2P-shaped input --\n"
    "    # distinct inspect/modify codes and a read-only held set are available.\n"
    "    Assert(inspect_code != modify_code)\n"
    "    Assert(Acc(set_pred(held), 1 / 2))\n"
    "    required = PSeq(inspect_code, modify_code)\n"
    "    return target_decision(held, required)\n"
    "    # impl-end"
)


SPEC_TESTS = [
    # ---- POSITIVE CONTROL (soundness): different shape, must verify ----------
    {
        "id": "pos-control-flag-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _TGT_IMPL_OLD, _TGT_IMPL_PC),
        "rationale": "A structurally-different correct target_decision (found-flag "
                     "accumulator scanning the WHOLE list, no early return; the "
                     "invariant tracks found == Exists over the scanned prefix). It "
                     "keeps the Acc(set_pred(held),1/2) framing invariant and a "
                     "prefix-existential invariant the proof needs, so it discharges "
                     "the holds_any postcondition. Verifies on host (24.7s). If a "
                     "faithful correct impl could NOT verify => SPEC-TOO-STRONG.",
    },
    # ---- ADMISSIBILITY: precondition accepts an F2P-shaped input -------------
    {
        "id": "admiss-distinct-codes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _INSPECT_IMPL_OLD, _INSPECT_IMPL_ADMISS),
        "rationale": "inline_inspect_decision asserts its own precondition facts "
                     "(inspect_code != modify_code; Acc(set_pred(held),1/2) present) "
                     "before delegating exactly as the gold does. The asserts "
                     "discharge, proving the Requires admits a normal input (the "
                     "view-only / change scenarios of the F2P tests). If it could "
                     "not => PRECOND-TOO-STRONG.",
    },
    # ---- POSITIVE CONTROL (cheapest correct create) --------------------------
    {
        "id": "pos-control-create-inline-membership",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _CREATE_CHEAP_OLD, _CREATE_CHEAP_REPL),
        "rationale": "Cheapest correct create decision: `return modify_code in held` "
                     "directly (the grounded membership test that holds_any unfolds "
                     "to for a singleton required list). A different shape from the "
                     "gold delegation that still satisfies Result()==(modify_code in "
                     "held). Confirms the spec is not accidentally tied to the helper "
                     "call shape; must verify.",
    },
    # ---- FRAME-MUTATION (uniqueness, MANDATORY): write to a read-only input ---
    {
        "id": "frame-mut-write-perm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FRAME_INV_OLD, _FRAME_INV_NEW),
        "refinement": "An impl that needs FULL write permission on set_pred(held) is "
                      "one that intends to MUTATE the actor's permission grant (the "
                      "read-only `held`). A faithful real patch that wrote to the "
                      "user's permissions to make a decision come out 'allowed' would "
                      "corrupt shared auth state and could never resolve the F2P "
                      "(which assert a view-only actor is DENIED add/change/delete) "
                      "while leaving everyone else's grants intact; it is the opposite "
                      "of the read-only permission check the gold performs.",
        "rationale": "Rejection comes from the PERMISSION SYSTEM: the loop invariant "
                     "demands Acc(set_pred(held),1) but the precondition grants only "
                     "Acc(set_pred(held),1/2). Verifier: 'Loop invariant might not "
                     "hold on entry. There might be insufficient permission to access "
                     "set_pred(held).' (host-confirmed). The gold invariants are kept "
                     "verbatim except the 1/2 -> 1, so the rejection is attributable "
                     "to the write-permission demand alone.",
    },
    # ---- PARTIAL-DOMAIN (uniqueness): first-element-only existential ---------
    {
        "id": "uniq-first-required-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TGT_IMPL_OLD, _TGT_IMPL_FIRST),
        "refinement": "Returning `required[0] in held` is correct only when the FIRST "
                      "required code decides. For the inspect decision required = "
                      "PSeq(inspect_code, modify_code); an actor with only the MODIFY "
                      "code (held={modify_code}) is correctly view-permitted (modify "
                      "subsumes inspect), but this rival returns (inspect_code in "
                      "held) == False. A faithful real patch that only checked the "
                      "first requested permission would deny a change-permitted actor "
                      "the view inline (and break the documented 'change implies "
                      "view'), failing test_inline_change_m2m_change_perm's "
                      "has_view_permission == True assertion.",
        "rationale": "Rejection comes from target_decision's postcondition "
                     "Result()==holds_any(held,required): the existential over the "
                     "WHOLE required list is not satisfied by the first element alone "
                     "(host-confirmed: 'Assertion (Result() == holds_any(held, "
                     "required)) might not hold').",
    },
    # ---- PARTIAL-DOMAIN (uniqueness): the create-decision regression ---------
    {
        "id": "uniq-create-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _CREATE_OLD, _to_viewrule(_CREATE_OLD)),
        "refinement": "Using required = PSeq(inspect_code, modify_code) for the CREATE "
                      "decision is the pre-patch regression itself (has_add_permission "
                      "delegated to has_view_permission, i.e. the {view,change} rule). "
                      "An actor holding only the inspect/view code (held={inspect_code}) "
                      "then gets create=True, but the fix demands create=False. This "
                      "is exactly the body of FAIL_TO_PASS "
                      "test_inline_add_m2m_view_only_perm "
                      "(has_add_permission must be False for a view-only user), so the "
                      "faithful real patch does NOT resolve.",
        "rationale": "Rejection comes from inline_create_decision's postcondition "
                     "Result()==(modify_code in held): on held={inspect_code} the "
                     "view-rule impl returns True while the spec demands False "
                     "(host-confirmed at model.py inline_create_decision).",
    },
    # ---- PARTIAL-DOMAIN supporting cases: same regression on modify / remove -
    {
        "id": "uniq-modify-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _MODIFY_OLD, _to_viewrule(_MODIFY_OLD)),
        "refinement": "Same regression for the MODIFY decision (has_change_permission "
                      "delegating to the {view,change} view rule). A view-only actor "
                      "(held={inspect_code}) would be allowed to change the M2M inline "
                      "— the precise behaviour FAIL_TO_PASS "
                      "test_inline_change_m2m_view_only_perm forbids "
                      "(has_change_permission must be False). Faithful patch does NOT "
                      "resolve.",
        "rationale": "inline_modify_decision postcondition Result()==(modify_code in "
                     "held): inspect-only returns True under the view rule, spec "
                     "demands False.",
    },
    {
        "id": "uniq-remove-view-rule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _REMOVE_OLD, _to_viewrule(_REMOVE_OLD)),
        "refinement": "Same regression for the REMOVE decision (has_delete_permission "
                      "delegating to the {view,change} view rule). A view-only actor "
                      "(held={inspect_code}) would be allowed to delete entries in the "
                      "auto-created M2M inline — the editability the bug report and "
                      "the view-only F2P tests forbid (has_delete_permission must be "
                      "False). Faithful patch does NOT resolve.",
        "rationale": "inline_remove_decision postcondition Result()==(modify_code in "
                     "held): inspect-only returns True under the view rule, spec "
                     "demands False.",
    },
]

# No @ContractOnly axiom and no A-reference deep model in this bundle
# (meta.axioms == [], deep_model_references == []; refinement.md §C). The only
# refinement facts are R-refinements validated by axiom_check.py as a sanity
# oracle (codename distinctness; any == existential membership); there is no
# axiom Ensures to fuzz, so the axiom lane is vacuous.
AXIOM_TESTS = []
