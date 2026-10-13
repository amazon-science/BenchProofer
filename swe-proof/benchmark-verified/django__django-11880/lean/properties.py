# properties.py — G-PBT falsification battery for django__django-11880 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region is edited; the frozen proof body is left in place on rejects), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   duplicateField : (self : FormField) (fw fe fv : ObjId) → FormField
#   Producing an INDEPENDENT duplicate of a form field. The postcondition is a
#   conjunction of SIX independent top-level clauses, each pinning one modeled
#   output component of the result against the inputs (self / the fresh identities
#   fw, fe, fv):
#     (W) result.widgetId  = fw            — widget object gets a FRESH identity;
#     (E) result.errMsgId  = fe            — error-message mapping gets a FRESH
#                                            identity (THE load-bearing fix clause:
#                                            with the precondition fe ≠ self.errMsgId
#                                            this is exactly assertIsNot(copy.error_
#                                            messages, orig.error_messages));
#     (Ec) result.errMsg   = self.errMsg   — the mapping's CONTENTS are preserved;
#     (V) result.validId   = fv            — validator list gets a FRESH identity;
#     (Vc) result.validators = self.validators — the list's CONTENTS are preserved;
#     (R) result.required  = self.required — the immutable scalar is preserved (frame).
#   The carrier is fully transparent: FormField / ObjId (Nat) / MsgDict
#   (List (Nat×Nat)) / List Nat / Bool all derive DecidableEq and the impl is a
#   total `Id.run do` def, so `decide` computes the spec at any concrete literal —
#   witnesses need NO conditioning on an opaque callee.
#
# CARRIER NOTE (how the nagini rivals map here). The nagini sibling worked over
# fractional read permission on three list-valued attributes (msg_codes, msg_values,
# validators), and its load-bearing clause bundle (D) was DISTINCTNESS + FULL
# OWNERSHIP: the duplicate's collections must be FRESH objects, not the half-owned
# aliases of self. This backend models identity DIRECTLY as an ObjId tag alongside
# the contents, so nagini's "distinct object / full ownership" clause becomes the
# transparent identity clauses (W)/(E)/(V) — `result.errMsgId = fe` with the
# freshness precondition `fe ≠ self.errMsgId`. Nagini's content/length clause (C)
# becomes the content clauses (Ec)/(Vc). The lean carrier ADDS two modeled
# components the nagini list-only surface did not carry — the widget identity (W)
# and the immutable scalar frame (R) — so those get their own attackers here.
#
# NAGINI CASES AND THEIR DISPOSITION:
#   * pos-reorder (soundness)        -> PORTED as pos-reorder (below).
#   * alias-msg (uniqueness, THE pre-patch bug) -> PORTED as weak-alias-msg-identity.
#   * alias-validators (uniqueness)  -> PORTED as weak-alias-validators-identity.
#   * wrong-value (uniqueness, content clause C) -> PORTED as
#     weak-wrong-msg-content / weak-wrong-val-content (the content clauses
#     (Ec)/(Vc)).
#   * drop-last-msg (uniqueness, content clause C, PARTIAL DOMAIN) -> PORTED as
#     weak-droplast-msg-content. An earlier revision of this file recorded it as
#     "subsumed" by weak-wrong-msg-content on the ground that both violate the
#     same clause (result.errMsg ≠ self.errMsg). That is true at CLAUSE level and
#     is nevertheless the wrong test: nagini's drop-last is a PARTIAL-DOMAIN
#     attack ("correct on every field whose mapping is empty"), whereas every
#     other rival here diverges from the frozen impl at EVERY input of interest.
#     A near-miss confined to a sub-domain was therefore pinned by no witness, so
#     nothing established that the content clause is checked pointwise over the
#     whole mapping rather than just "the mapping is somehow populated". The lane
#     is expressible here — `self.errMsg.dropLast` agrees with the frozen impl on
#     the empty mapping and differs on every non-empty one — so it is landed
#     rather than argued away.
#   * frame-mut / frame-rebind (uniqueness, PERMISSION-mutation) -> VACUOUS here.
#     Lean is referentially transparent: there is no aliasing and no fractional
#     permission, so "write into / rebind the read-only source self" is not an
#     expressible impl (self is an immutable value argument). The whole
#     permission-mutation lane is N/A on lean. The FRAME obligation it protected —
#     "components of self are not perturbed" — survives here as the pinned clauses
#     (Ec)/(Vc)/(R), and (R) is directly attacked by weak-perturb-required. See
#     'assessment'.
#   * admiss (admissibility) -> PORTED as admiss-f2p-shaped. An earlier revision
#     of this file recorded this lane as N/A, on the ground that the freshness
#     preconditions are "trivially satisfiable" so there is nothing to defend.
#     That is an ARGUMENT, not a demonstration, and it is the wrong test: what
#     PRECOND-TOO-STRONG means on a total carrier is the obligation being
#     UNSATISFIABLE at exactly an F2P-shaped input — a field carrying a custom
#     error-message override (a NON-EMPTY mapping) plus a validator, together with
#     three fresh identities. "Trivially satisfiable" is exactly the claim a case
#     can machine-check, so it is checked rather than asserted: the positive
#     discharges the three freshness hypotheses AND the spec predicate at that
#     concrete input, by evaluation, as a `have`, before closing the frozen
#     obligation verbatim.
#   * AXIOM_TESTS -> dropped (G-AX's lane). The duplication is modeled DEEPLY (fresh
#     identity + preserved contents), so there is no consumed axiom anyway.
#
# TWO LEAN-CARRIER-ONLY ATTACKERS (no nagini counterpart, added for clause coverage
# of components the list-only nagini surface did not model): weak-stale-widget
# attacks (W); weak-perturb-required attacks (R).
from pathlib import Path

INSTANCE = "django__django-11880"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors (each lies ENTIRELY inside impl-start/impl-end and is unique) ----------
_WIDGET_LINE = "  result := { result with widgetId := fw }\n"
_ERRMSG_LINE = "  result := { result with errMsgId := fe, errMsg := self.errMsg }\n"
_VALID_LINE = "  result := { result with validId := fv, validators := self.validators }\n"
_RETURN_LINE = "  return result\n"
# The three middle rebinds as one block (used by the reorder positive).
_MIDDLE = _WIDGET_LINE + _ERRMSG_LINE + _VALID_LINE
# The full impl def (used by the single-literal positive).
_FULL_IMPL = (
    "def implementation_duplicateField\n"
    "    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do\n"
    "  let mut result := self\n"
    "  result := { result with widgetId := fw }\n"
    "  result := { result with errMsgId := fe, errMsg := self.errMsg }\n"
    "  result := { result with validId := fv, validators := self.validators }\n"
    "  return result"
)
# The frozen proof body, and the `intro` line that opens it. Both live ENTIRELY
# inside proof-start/proof-end and are unique. Used by the reproved positives,
# which keep the frozen `theorem correct_duplicateField` STATEMENT byte-identical
# (variant_scope requires that) and edit only the tactic body — which a variant is
# explicitly permitted to do, and which a positive over a non-defeq reshape MUST
# do, since `rfl` closes only for a syntactically-matching impl.
_INTRO_LINE = "  intro self fw fe fv _ _ _\n"
_PROOF_BODY = (
    "  intro self fw fe fv _ _ _\n"
    "  unfold problem_spec_duplicateField implementation_duplicateField\n"
    "  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩\n"
)
for _a in (_WIDGET_LINE, _ERRMSG_LINE, _VALID_LINE, _RETURN_LINE, _MIDDLE,
           _FULL_IMPL, _INTRO_LINE, _PROOF_BODY):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — a CORRECT impl in a DIFFERENT shape must still
# VERIFY (else SPEC-TOO-STRONG). All three keep the frozen `theorem correct_*`
# STATEMENT byte-identical, and none introduces a lemma, axiom or sorry.
#
# The first two additionally keep the frozen PROOF BODY, which still closes
# because each computes the same output component-by-component. That is worth
# stating precisely rather than treating as a virtue: keeping the frozen `rfl`
# script and closing means the kernel identifies these impls with gold — they are
# DEFINITIONALLY equal reshapes, so they cannot detect a spec that admits only
# gold's own normal form. pos-rebuilt-mapping is the case that covers that gap:
# extensionally equal, NOT defeq, and therefore obliged to reprove the affected
# clause (which variant_scope permits — only the statement is frozen, the tactic
# body may differ).
# ===========================================================================

# pos-reorder: the three fresh-object replacements applied in a DIFFERENT order
# (validators, then error-message mapping, then widget — gold does widget first).
# Every output component is identical to gold's, so all six clauses hold and the
# frozen `refine ⟨rfl, …⟩` still closes. If it FAILS => SPEC-TOO-STRONG (postcondition
# over-fit to one syntactic sequencing of independent field updates).
_POS_REORDER = _swap(
    _BASE,
    _MIDDLE,
    _VALID_LINE + _ERRMSG_LINE + _WIDGET_LINE,
)

# pos-single-literal: a structurally-DIFFERENT correct impl that drops the imperative
# do-block entirely and builds the duplicate as ONE structure-update literal. Same
# output on every input, so the frozen proof body still closes after unfolding. If it
# FAILS => SPEC-TOO-STRONG (postcondition over-fit to the mutable-accumulator shape).
_POS_LITERAL = _swap(
    _BASE,
    _FULL_IMPL,
    "def implementation_duplicateField\n"
    "    (self : FormField) (fw fe fv : ObjId) : FormField :=\n"
    "  { self with widgetId := fw, errMsgId := fe, errMsg := self.errMsg,\n"
    "              validId := fv, validators := self.validators }",
)

# pos-rebuilt-mapping: a CORRECT impl whose mapping contents are REBUILT
# element-by-element (`.map (fun p => (p.1, p.2))`, the identity on pairs) rather
# than handed over as the same list value. Extensionally identical to gold on
# every input, but NOT definitionally equal to `self.errMsg`, so the frozen
# `refine ⟨rfl, …⟩` cannot close the content clause and the case must REPROVE it
# (`simp`, on the frozen statement, with no new lemma/axiom/sorry).
#
# This is the positive the other two could not be. pos-reorder and
# pos-single-literal are both DEFEQ to gold — measured: each keeps the frozen
# proof body and still closes, which is precisely what "defeq" means here — so
# neither exercises the spec's tolerance for a reshape the kernel does not
# identify with gold. Without this case, a spec strong enough to admit only
# impls literally sharing gold's normal form would pass the soundness lane.
# Its faithful real analogue is a duplication that reconstructs the mapping
# entry-by-entry instead of delegating to a single copy call — a correct copy
# either way. If it FAILS => SPEC-TOO-STRONG.
_POS_REBUILT = _swap(
    _swap(
        _BASE, _ERRMSG_LINE,
        "  result := { result with errMsgId := fe,\n"
        "                          errMsg := self.errMsg.map (fun p => (p.1, p.2)) }\n",
    ),
    _PROOF_BODY,
    "  intro self fw fe fv _ _ _\n"
    "  unfold problem_spec_duplicateField implementation_duplicateField\n"
    "  refine ⟨rfl, rfl, ?_, rfl, rfl, rfl⟩\n"
    "  simp\n",
)


# ===========================================================================
# ADMISSIBILITY (PRECOND-TOO-STRONG) — the frozen obligation must be SATISFIABLE
# at an F2P-shaped input. The obligation carries three real hypotheses
# (fw ≠ self.widgetId, fe ≠ self.errMsgId, fv ≠ self.validId), so "there is no
# precondition" is not available as a reason to skip this lane; and even where it
# were, the analogue on a total carrier is the obligation being unsatisfiable at
# exactly that input. Both are checked here by EVALUATION.
# ===========================================================================

# The F2P-shaped input: a field carrying ONE custom error-message override — a
# NON-EMPTY mapping, which is the whole point of the scenario, since an empty
# mapping makes the content clauses vacuous — plus one validator, plus three
# identities distinct from the field's own three.
_F2P_FIELD = (
    "{ widgetId := 0, errMsgId := 1, errMsg := [(7, 11)], validId := 2, "
    "validators := [13], required := true }"
)

# Discharged BEFORE the frozen obligation is closed verbatim: the `have` asserts
# the three freshness hypotheses AND the spec predicate at that concrete input,
# and `decide` computes all four over the transparent carrier. Nothing is
# assumed — no new declaration, no axiom, no sorry — and the frozen
# `theorem correct_duplicateField` statement plus its frozen three-line tactic
# body follow the `have` unchanged.
_ADMISS_HAVE = (
    "  have admissible :\n"
    f"      (3 : ObjId) ≠ ({_F2P_FIELD} : FormField).widgetId ∧\n"
    f"      (4 : ObjId) ≠ ({_F2P_FIELD} : FormField).errMsgId ∧\n"
    f"      (5 : ObjId) ≠ ({_F2P_FIELD} : FormField).validId ∧\n"
    "      problem_spec_duplicateField\n"
    f"        {_F2P_FIELD} 3 4 5\n"
    "        (implementation_duplicateField\n"
    f"          {_F2P_FIELD} 3 4 5) := by\n"
    "    unfold problem_spec_duplicateField implementation_duplicateField\n"
    "    decide\n"
)
_ADMISS = _swap(_BASE, _INTRO_LINE, _INTRO_LINE + _ADMISS_HAVE)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly and edits ONLY the impl region; the frozen proof body is left in
# place (it will not close for the reshaped impl — that is the default outcome of
# reshaping — so the module build fails, and the gate reads the WITNESS, checked in
# a file with the obligation removed, not the rival's own build).
# ===========================================================================

# weak-alias-msg-identity: THE pre-patch bug. Omit the fresh-identity replacement of
# the error-message mapping, so the duplicate keeps the shallow copy's SHARED mapping
# identity: result.errMsgId stays self.errMsgId (contents still equal). Attacks the
# load-bearing clause (E).
_RIV_ALIAS_MSG = _swap(_BASE, _ERRMSG_LINE, "")

# weak-alias-validators-identity: symmetric alias on the OTHER container — omit the
# fresh-identity replacement of the validator list, so result.validId stays
# self.validId. Attacks clause (V).
_RIV_ALIAS_VAL = _swap(
    _BASE, _VALID_LINE,
    "  result := { result with validators := self.validators }\n",
)

# weak-wrong-msg-content: allocate a FRESH error-message mapping (identity fe, clause E
# holds) but fill it with the WRONG contents (empty) instead of self's. Attacks the
# content clause (Ec): identity/freshness satisfied, contents mangled. This is the
# lean image of nagini's wrong-value / drop-last-msg content attacks.
_RIV_WRONG_MSG = _swap(
    _BASE, _ERRMSG_LINE,
    "  result := { result with errMsgId := fe, errMsg := [] }\n",
)

# weak-wrong-val-content: fresh validator list (identity fv, clause V holds) with the
# WRONG contents (empty). Attacks the content clause (Vc).
_RIV_WRONG_VAL = _swap(
    _BASE, _VALID_LINE,
    "  result := { result with validId := fv, validators := [] }\n",
)

# weak-droplast-msg-content: the PARTIAL-DOMAIN content attack (nagini's
# drop-last-msg). Allocate a FRESH error-message mapping (identity fe, clause E
# holds) carrying self's contents MINUS the last entry. Unlike every other rival
# here, this one AGREES with the frozen impl on a whole sub-domain — every field
# whose mapping is empty — and diverges only on the non-empty mappings the F2P
# scenario is about. Attacks (Ec) pointwise rather than wholesale.
_RIV_DROPLAST_MSG = _swap(
    _BASE, _ERRMSG_LINE,
    "  result := { result with errMsgId := fe, errMsg := self.errMsg.dropLast }\n",
)

# weak-stale-widget: omit the fresh-identity replacement of the widget, so
# result.widgetId stays self.widgetId. Attacks clause (W). (No nagini counterpart —
# the list-only nagini surface did not model the widget identity; this covers a
# modeled clause the nagini rivals could not reach.)
_RIV_STALE_WIDGET = _swap(_BASE, _WIDGET_LINE, "")

# weak-perturb-required: correctly build all three containers but FLIP the immutable
# scalar. Attacks the FRAME clause (R): result.required must equal self.required. This
# is the lean image of nagini's frame lane — not via an illegal write to a read-only
# input (inexpressible here), but by refuting the pinned-frame clause the frame
# obligation reduces to on a referentially-transparent carrier.
_RIV_PERTURB_REQ = _swap(
    _BASE, _RETURN_LINE,
    "  result := { result with required := !self.required }\n" + _RETURN_LINE,
)


def _wit(self_lit, fw, fe, fv, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at one concrete
    literal input, closed by `decide` (the whole carrier derives DecidableEq).
    Elaborates against a rival that diverges from the spec there, and FAILS on gold
    (which satisfies the spec at every input). Binds nothing, so it needs no
    consistency probe."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_duplicateField\n"
        f"    {self_lit} {fw} {fe} {fv}\n"
        f"    (implementation_duplicateField\n"
        f"      {self_lit} {fw} {fe} {fv}) := by\n"
        f"  unfold problem_spec_duplicateField implementation_duplicateField\n"
        f"  decide"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REORDER,
        "rationale": (
            "A CORRECT duplication in a different shape: the three fresh-object "
            "replacements are applied in a different order (validators, mapping, "
            "widget) than gold (widget first). Independent field updates, so every "
            "output component — and thus all six postcondition clauses — is identical "
            "to gold's; the frozen `theorem correct_duplicateField` statement is "
            "byte-identical and the frozen proof body still closes. If it FAILS => "
            "SPEC-TOO-STRONG (the postcondition would be over-fit to one sequencing "
            "of independent updates). Ports the nagini pos-reorder soundness control."
        ),
    },
    {
        "id": "pos-single-literal",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LITERAL,
        "rationale": (
            "A structurally-different CORRECT impl that drops the imperative "
            "mutable-accumulator do-block and builds the duplicate as ONE "
            "structure-update literal. Same output on every input, so the frozen "
            "proof body still closes after unfolding — no reproof, no new "
            "lemma/axiom/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to the accumulator shape)."
        ),
    },
    {
        "id": "pos-rebuilt-mapping",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REBUILT,
        "rationale": (
            "A CORRECT impl whose error-message mapping is REBUILT entry-by-entry "
            "(the identity map on pairs) instead of being handed over as the same "
            "list value: extensionally equal to gold's output on every input, but "
            "NOT definitionally equal, so the frozen `refine ⟨rfl, …⟩` cannot "
            "close the content clause and this case REPROVES it with `simp` on the "
            "byte-identical frozen statement — no new lemma, axiom or sorry. This "
            "is the only positive here that is not defeq to gold: the other two "
            "each retain the frozen proof body and still close, which means the "
            "kernel identifies them with gold and they cannot detect a spec that "
            "admits only gold's own normal form. Its faithful real analogue is a "
            "duplication that reconstructs the mapping entry-by-entry rather than "
            "delegating to one copy call — correct either way. If it FAILS => "
            "SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (the obligation must be SATISFIABLE) ----
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "The frozen obligation carries THREE real hypotheses (fw ≠ "
            "self.widgetId, fe ≠ self.errMsgId, fv ≠ self.validId), so this lane "
            "is not vacuous here: if they were jointly unsatisfiable at a normal "
            "input, `correct_duplicateField` would be a universally-quantified "
            "vacuity and the whole bundle would attest to nothing. This positive "
            "discharges them, AND the spec predicate itself, at a concrete "
            "F2P-shaped input — a field carrying one custom error-message "
            "override (a NON-EMPTY mapping, so the content clauses are not "
            "vacuous) plus one validator, with three identities distinct from the "
            "field's own — by EVALUATION, as a `have`, before closing the frozen "
            "obligation verbatim. The `have` is informative rather than a "
            "tautology, audited by control: with the spec claim NEGATED the same "
            "shape does NOT close (`decide` refutes it), and with one freshness "
            "hypothesis stated falsely (0 ≠ widgetId, where widgetId IS 0) it "
            "does not close either. If it FAILS => PRECOND-TOO-STRONG."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-alias-msg-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALIAS_MSG,
        "refinement": (
            "This is the PRE-PATCH behavior verbatim: the duplicate omits the fresh "
            "allocation of the error-message mapping, so it keeps the shallow copy's "
            "SHARED mapping object (contents still equal). Its faithful real patch is "
            "the unpatched routine, which the F2P rejects via "
            "assertIsNot(field_copy.error_messages, field.error_messages): the "
            "duplicate and original share one mapping object, so mutating one field's "
            "messages is visible through every copy. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (E): result.errMsgId = fe with the precondition "
            "fe ≠ self.errMsgId. An alias leaves result.errMsgId = self.errMsgId ≠ fe. "
            "Witness varies the fe binder (fresh identity) against a self whose "
            "errMsgId differs from it. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # self.errMsgId=5, fe=9: gold's result.errMsgId=9=fe; rival's stays 5≠9.
        "witness": _wit(
            "{ widgetId := 1, errMsgId := 5, errMsg := [(2,3)], validId := 7, "
            "validators := [4], required := true }", 2, 9, 8,
            "aliased mapping keeps self's identity 5, spec demands the fresh fe=9"),
    },
    {
        "id": "weak-alias-validators-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALIAS_VAL,
        "refinement": (
            "Copies the error-message mapping correctly but omits the fresh allocation "
            "of the validator list, so the duplicate re-shares self's validator-list "
            "object. A patch that fixed the error messages but left the validators "
            "aliased would re-share the validator list across deep-copied fields — the "
            "validator-independence guarantee (a copy's validators must be its own "
            "object) breaks. It does NOT resolve, and it guards against 'fixing only "
            "one container while re-sharing the other'."
        ),
        "rationale": (
            "REJECTED by clause (V): result.validId = fv with fv ≠ self.validId. An "
            "alias leaves result.validId = self.validId ≠ fv. Witness varies the fv "
            "binder against a self whose validId differs from it. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # self.validId=12, fv=22: gold's result.validId=22; rival's stays 12≠22.
        "witness": _wit(
            "{ widgetId := 10, errMsgId := 11, errMsg := [(1,1)], validId := 12, "
            "validators := [9], required := false }", 20, 21, 22,
            "aliased validator list keeps self's identity 12, spec demands fresh fv=22"),
    },
    {
        "id": "weak-wrong-msg-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_MSG,
        "refinement": (
            "Allocates a FRESH error-message mapping (so the distinctness/identity "
            "clause is satisfied and the F2P assertIsNot passes) but fills it with the "
            "WRONG contents (empty) instead of self's. A real patch that produced a "
            "duplicate whose error-message mapping is a fresh object with dropped/blank "
            "contents would give copies whose error messages differ from the original "
            "— error-message-content behavior breaks even though the objects are "
            "distinct. It does NOT resolve. (This is the content-clause attack: nagini's "
            "wrong-value AND drop-last-msg both live here.)"
        ),
        "rationale": (
            "REJECTED by the content clause (Ec): result.errMsg = self.errMsg is "
            "violated (result.errMsg = [] ≠ self.errMsg) whenever self's mapping is "
            "non-empty. Witness makes self.errMsg non-empty. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # self.errMsg=[(5,6)] non-empty; rival's result.errMsg=[]≠[(5,6)].
        "witness": _wit(
            "{ widgetId := 50, errMsgId := 51, errMsg := [(5,6)], validId := 52, "
            "validators := [5], required := true }", 60, 61, 62,
            "fresh mapping with wrong (empty) contents ≠ self's [(5,6)]"),
    },
    {
        "id": "weak-wrong-val-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_WRONG_VAL,
        "refinement": (
            "Allocates a FRESH validator list (identity clause satisfied) but with the "
            "WRONG contents (empty). A real patch yielding a duplicate whose validator "
            "list is a fresh but empty/mangled object would drop the field's validators "
            "on every copy — validation behavior breaks even though the list object is "
            "distinct. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the content clause (Vc): result.validators = self.validators "
            "is violated (result.validators = [] ≠ self.validators) whenever self's "
            "list is non-empty. Witness makes self.validators non-empty. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # self.validators=[8] non-empty; rival's result.validators=[]≠[8].
        "witness": _wit(
            "{ widgetId := 70, errMsgId := 71, errMsg := [(7,7)], validId := 72, "
            "validators := [8], required := false }", 80, 81, 82,
            "fresh validator list with wrong (empty) contents ≠ self's [8]"),
    },
    {
        "id": "weak-droplast-msg-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DROPLAST_MSG,
        "refinement": (
            "Allocates a FRESH error-message mapping (so the distinctness/identity "
            "clause holds and the F2P assertIsNot passes) carrying self's contents "
            "MINUS the last entry. A real patch that copied all-but-the-last "
            "error-message entry would silently drop one override message on every "
            "duplicated field, while leaving fields with no overrides at all "
            "completely unaffected — so it looks correct on the simplest inputs and "
            "loses a message on exactly the fields that configure one. It does NOT "
            "resolve. This is the lean image of nagini's drop-last-msg."
        ),
        "rationale": (
            "REJECTED by the content clause (Ec): result.errMsg = self.errMsg is "
            "violated because dropping the final entry leaves a strictly shorter "
            "mapping on every NON-EMPTY input. This is the battery's only "
            "PARTIAL-DOMAIN rival: it AGREES with the frozen impl on the whole "
            "sub-domain of empty mappings and diverges on the rest, so it tests "
            "that (Ec) is enforced pointwise over the mapping and not merely that "
            "the mapping is somehow populated. Every other rival here diverges at "
            "every input of interest, which a spec pinning only a coarse property "
            "of the mapping would also catch. The witness therefore uses a "
            "TWO-entry mapping, so the near-miss is a dropped tail rather than an "
            "emptied mapping. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # self.errMsg=[(2,3),(4,4)]; rival's result.errMsg=[(2,3)]≠[(2,3),(4,4)].
        # A one-entry mapping would collapse this rival onto weak-wrong-msg-content
        # (both would yield []), which is the distinction the case exists to make.
        "witness": _wit(
            "{ widgetId := 1, errMsgId := 5, errMsg := [(2,3),(4,4)], validId := 7, "
            "validators := [4], required := true }", 2, 9, 8,
            "dropped-tail mapping [(2,3)] ≠ self's [(2,3),(4,4)]"),
    },
    {
        "id": "weak-stale-widget",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_STALE_WIDGET,
        "refinement": (
            "Omits the fresh allocation of the widget object, so the duplicate keeps "
            "the shallow copy's SHARED widget identity. A real patch that deep-copied "
            "the messages/validators but left the widget shared would give copies that "
            "share one widget object — mutating one field's widget is visible through "
            "every copy, the widget-independence guarantee breaks. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (W): result.widgetId = fw with fw ≠ self.widgetId. A "
            "stale widget leaves result.widgetId = self.widgetId ≠ fw. Witness varies "
            "the fw binder against a self whose widgetId differs from it. If it "
            "VERIFIES => SPEC-TOO-WEAK. (No nagini counterpart: the widget identity is "
            "a lean-carrier-only modeled clause.)"
        ),
        # self.widgetId=30, fw=40: gold's result.widgetId=40; rival's stays 30≠40.
        "witness": _wit(
            "{ widgetId := 30, errMsgId := 31, errMsg := [(3,3)], validId := 32, "
            "validators := [3], required := true }", 40, 41, 42,
            "stale widget keeps self's identity 30, spec demands fresh fw=40"),
    },
    {
        "id": "weak-perturb-required",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PERTURB_REQ,
        "refinement": (
            "Builds all three containers correctly but FLIPS the immutable scalar the "
            "duplicate must carry unchanged. A real patch that perturbed an immutable "
            "scalar attribute during duplication would give copies whose scalar "
            "configuration differs from the original — every consumer relying on the "
            "duplicate preserving the field's scalar settings breaks. It does NOT "
            "resolve. This is the lean image of the nagini FRAME lane: not an illegal "
            "write to a read-only input (inexpressible on a referentially-transparent "
            "carrier), but a refutation of the pinned-frame clause the frame obligation "
            "reduces to here."
        ),
        "rationale": (
            "REJECTED by the frame clause (R): result.required = self.required is "
            "violated (result.required = !self.required). Witness pins a concrete "
            "self.required so the flip is observable. If it VERIFIES => SPEC-TOO-WEAK "
            "(a modeled output component would be left unconstrained)."
        ),
        # self.required=true; rival's result.required=false≠true.
        "witness": _wit(
            "{ widgetId := 90, errMsgId := 91, errMsg := [(9,9)], validId := 92, "
            "validators := [1], required := true }", 100, 101, 102,
            "flipped scalar false ≠ self.required true"),
    },
]


# No @ContractOnly axioms and no opaque callees: each duplication step (fresh
# identity + preserved contents) and the scalar frame are modeled DEEPLY over the
# transparent FormField carrier, so the axiom lane is vacuous here and belongs to
# G-AX regardless.
AXIOM_TESTS = []
