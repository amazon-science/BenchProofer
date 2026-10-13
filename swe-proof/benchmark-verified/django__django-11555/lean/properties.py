# properties.py — G-PBT spec-lane manifest for django__django-11555 (lean).
# NOT a Lean file; a record of adversarial cases the runner parses.
#
# ---------------------------------------------------------------- DEFENDED SURFACE
# ONE modeled obligation: `theorem correct_expandOrdering`, over
#
#     problem_spec_expandOrdering (items : List OrderingItem)
#                                 (result : List (OrderExpr × Bool)) : Prop :=
#       result = items.flatMap expandOrderingItem
#
# with the FROZEN pure helper pinning, per item:
#
#     expandOrderingItem (.expression e) = [(e, false)]      -- emitted directly
#     expandOrderingItem (.fieldRef n)   = resolveFieldRef (.fieldRef n)
#
# There is exactly ONE input binder, `items : List OrderingItem`, and the whole
# discriminating content of the spec lives in three independently attackable
# top-level facts folded into that single `flatMap` equation:
#
#   C1  per-item DISPATCH: an already-formed ordering expression contributes
#       `[(e, false)]` and is NOT sent to name resolution; a field reference IS.
#   C2  per-item CONTENT: the expression's own identity `e` is carried, and the
#       companion flag is `false` (not `true`), and it contributes exactly one
#       directive (not zero, not itself-plus-a-resolution).
#   C3  COMBINATION: the per-item expansions are concatenated FRONT-TO-BACK in
#       specification order — nothing dropped, reordered, or invented.
#
# The carrier is largely OPAQUE: `OrderExpr` is an `opaque` type with no
# constructor, and `resolveFieldRef` is an `opaque` function with no constraining
# axiom, so `decide` on a bare literal input is useless here. That does NOT make
# the uniqueness lane inexpressible, and the witnesses below take three distinct
# routes to it:
#
#   (i)  attack what IS transparent. The companion flag is a `Bool` literal and
#        the specified expansion of a one-expression specification is a literal
#        singleton, so the flag rival and the drop rival are refuted with NO
#        hypothesis at all — the opaque carrier never enters the goal.
#   (ii) attack the STRUCTURE rather than the content. The inverted-dispatch
#        rival is refuted by a LENGTH argument, which needs nothing about what
#        either resolution contains.
#   (iii) CONDITION on the carrier where the value is genuinely needed: state the
#        refutation at a point described by hypothesis (a distinctness assumption
#        about two expression identities, or one assumption about the shape of a
#        single resolution result) rather than computing it.
#
# Each conditioning hypothesis is kept as weak as the refutation needs — one
# assumption about ONE opaque term, plus a plain distinctness where two
# identities must differ. Every witness below was built against the rival AND
# against the frozen solution and seen to discriminate, and every consistency
# probe (`False` from the binders alone) was confirmed to FAIL, so no refutation
# here rests on assumptions that cannot jointly hold.
#
# The oracle is GROUNDED in the input: `expandOrderingItem` is a total, fully
# defined function of the item, and `resolveFieldRef` appears IDENTICALLY in the
# spec helper and in the implementation, so it cancels in the obligation rather
# than acting as an answer key. Precisely because it is opaque, an impl that
# routes an expression item through it cannot prove
# `resolveFieldRef (.expression e) = [(e, false)]` — which is what makes C1
# attackable at all.
#
# There is no precondition (the obligation binds `∀ items` unguarded), so the
# admissibility lane is a satisfiability check at an F2P-shaped input rather than
# a precondition probe.
#
# ------------------------------------------------- PORT RECORD (nagini sibling)
# Ported, one-for-one in ARGUMENT (mechanics rewritten for this carrier):
#   U1 real-bug/route-through-name-machinery -> no-per-item-dispatch
#   U2 inverted-kind-discriminant            -> inverted-dispatch
#   U3 always-passthrough-never-resolve      -> field-reference-contributes-nothing
#   U4 wrong-passthrough-identity            -> wrong-carried-identity
#   U5 drop-passthrough                      -> expression-contributes-nothing
#   P1 pos-control-explicit-local            -> pos-let-bound-piece
#   P2 pos-control-precomputed-bound         -> pos-dispatch-arms-swapped
#   admissibility-mixed-ordering             -> admiss-mixed-specification
#
# Added here with no nagini counterpart, because this carrier exposes clauses
# nagini's index-aligned int-list abstraction folded away: wrong-companion-flag
# (nagini modeled the produced target as a bare identity tag, so the `false`
# companion flag had no representation at all), expression-emitted-and-also-
# resolved (C2 cardinality from ABOVE), and the two C3 combination-order rivals
# (expansions-combined-back-to-front, specification-walked-back-to-front).
#
# Added by AUDIT, closing two clauses the port left unprobed:
#   field-reference-resolution-reversed-within-item — C3 at WITHIN-item
#     granularity. The two existing order rivals reverse the order of the
#     pieces; neither reverses the order inside one piece, and their
#     two-expression witnesses sit in the region where the distinction is
#     invisible (every piece a singleton).
#   field-reference-resolution-duplicated — the field-reference arm's
#     cardinality from ABOVE. The port probed that arm only from below.
#   companion-flag-computed-from-specification-length — C2's flag clause at a
#     point the existing flag rival cannot reach. Added by a SECOND audit, which
#     found the flag lane probed only by an impl that is wrong at every input:
#     a one-item witness refutes that, so nothing tested whether the flag is a
#     CONSTANT of the per-item expansion rather than a function of the
#     surrounding specification. This rival agrees with the frozen solution on
#     every one-item specification — where 7 of the battery's 11 prior witnesses
#     sit — and diverges from two items up.
#
# Also corrected by audit: the specification-walked-back-to-front rationale
# claimed that rival and the prepend rival "differ from gold" in distinct ways.
# They do not — an induction proves the two impls are the SAME function. The case
# is retained as a syntactic shape probe on the loop header, with the claim fixed.
# A second audit re-derived that induction independently and it CLOSES (exit 0),
# so the corrected claim is machine-confirmed rather than asserted.
#
# Corrected by the second audit: two `rationale` EXCLUSIVITY claims were false,
# each contradicted by the manifest's own contents rather than by the carrier.
#   * field-reference-contributes-nothing claimed its input was "a strictly
#     different sub-domain from every other rival here". Two later
#     field-reference rivals refute at the SAME point; what is actually unique
#     is the direction of the error there, and the claim now says that.
#   * expansions-combined-back-to-front claimed its two-expression shape was one
#     "no other witness here uses". The reverse-walk witness uses exactly it —
#     and provably must, the two impls being the same function. Claim rewritten
#     to the true statement (it is the smallest shape at which piece order has
#     content) with the overlap named.
# Neither error changed an OUTCOME; both would have misled a reader about which
# clause the battery covers, which is what the prose is for.
#
# NOT ported, and why:
#   * frame-mutate-ids / frame-mutate-kinds — nagini's mandatory frame-permission
#     probes. Lean is referentially transparent: there is no fractional
#     permission to under-hold and no in-place write to make, so the class is
#     VACUOUS here. Deliberately NOT given a fabricated substitute. DEMONSTRATED
#     rather than asserted: an audit built the nearest analogue — an impl that
#     rebinds the input binder with `let mut items := items; items := items ++
#     items` and loops over that — and it does not fault on a frame at all. The
#     spec quantifies over the ORIGINAL binder, so the write is invisible to it
#     and the rival degenerates into an ordinary value-level duplication rival,
#     refuted by the same `[(e,false),(e,false)] ≠ [(e,false)]` witness the
#     cardinality lane already carries (built: rival 0, gold 1). There is no
#     permission failure to attribute anything to, which is exactly why the class
#     is vacuous and not merely hard. A SECOND audit rebuilt that analogue from
#     scratch rather than taking the record's word for it: the rebind variant
#     passes the scope check, and its build reports the rival's answer as the
#     duplicated list, refuted at rival 0 / gold 1. Independently confirmed.
#   * the divergence lane — nagini carries no diverge-*/nonterm-* case for this
#     instance, and on lean the class is vacuous in any event:
#     `implementation_expandOrdering` is a total Lean `def` over a `for` loop on
#     a finite list, so a non-terminating rival cannot be written at all. (This
#     is NOT the velvet `partial`-semantics spec hole of the corpus-wide termination-semantics finding.)
#   * AXIOM_TESTS — the axiom lane is G-AX's job; this gate ignores them.
from pathlib import Path

INSTANCE = "django__django-11555"
FLOAT_ENCODING = None

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ------------------------------------------------------------------ ANCHORS
# Every anchor below lies ENTIRELY inside the impl region or the proof region,
# and each is unique in the frozen file, so `same_spec` holds by construction
# and no case can touch the spec, the helper, or the opaque declarations.

# The whole per-item dispatch (impl region only).
_DISPATCH = (
    "    match item with\n"
    "    | .expression e =>\n"
    "        -- Already a directive: emit it directly (flagged `false`) and move on,\n"
    "        -- skipping name resolution.\n"
    "        results := results ++ [(e, false)]\n"
    "    | .fieldRef _ =>\n"
    "        results := results ++ resolveFieldRef item\n"
)
assert _BASE.count(_DISPATCH) == 1, "DISPATCH anchor drift"

# The expression arm's emission line alone (impl region only).
_EMIT = "        results := results ++ [(e, false)]\n"
assert _BASE.count(_EMIT) == 1, "EMIT anchor drift"

# The field-reference arm's line alone (impl region only).
_RESOLVE = "        results := results ++ resolveFieldRef item\n"
assert _BASE.count(_RESOLVE) == 1, "RESOLVE anchor drift"

# The loop header (impl region only).
_FORHEAD = "  for item in items do\n"
assert _BASE.count(_FORHEAD) == 1, "FORHEAD anchor drift"

# The whole impl body, for variants that reshape it entirely.
_IMPL = (
    "def implementation_expandOrdering\n"
    "    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do\n"
    "  let mut results : List (OrderExpr × Bool) := []\n"
    + _FORHEAD + _DISPATCH +
    "  return results\n"
)
assert _BASE.count(_IMPL) == 1, "IMPL anchor drift"

# The whole frozen proof region body, for variants that must reprove.
_PROOF_START = "-- proof-start\n"
_PROOF_END = "-- proof-end"
_PROOF = _BASE[_BASE.index(_PROOF_START) + len(_PROOF_START):_BASE.index(_PROOF_END)]
assert _BASE.count(_PROOF) == 1, "PROOF anchor drift"

# The frozen obligation's `intro` line (proof region only) — the hook an
# admissibility ground instance hangs off, leaving the STATEMENT byte-identical.
_INTRO = "  intro items\n"
assert _BASE.count(_INTRO) == 1, "INTRO anchor drift"


# ==================================================================== RIVALS
# Each rival edits only the impl region (the proof region is left carrying the
# frozen script, which is exactly what a `expect="reject"` case wants: the
# obligation must fail). The load-bearing evidence is the `witness`, not the
# tactic breakage.

# --- R1: NO per-item dispatch — every item routed through name resolution.
#         (The shape that exhibits the reported failure; attacks C1.)
_R_NO_DISPATCH = _swap(
    _BASE, _DISPATCH,
    "    -- No dispatch: every item, including an already-formed ordering\n"
    "    -- expression, is handed to name resolution.\n"
    "    results := results ++ resolveFieldRef item\n",
)

# --- R2: dispatch present but the companion FLAG is inverted. (Attacks C2.)
_R_WRONG_FLAG = _swap(
    _BASE, _EMIT,
    "        results := results ++ [(e, true)]\n",
)

# --- R3: the ordering expression is recognised but contributes NOTHING.
#         (Attacks C2: one directive is required, zero are produced.)
_R_DROP_EMIT = _swap(
    _BASE, _EMIT,
    "        results := results\n",
)

# --- R4: the ordering expression is emitted AND ALSO routed through name
#         resolution. (Attacks C1/C2: exactly one contribution is required.)
_R_EMIT_AND_RESOLVE = _swap(
    _BASE, _EMIT,
    "        results := results ++ [(e, false)] ++ resolveFieldRef item\n",
)

# --- R5: a field reference contributes nothing (its resolution is discarded).
#         (Attacks C1 on the other arm.)
_R_DROP_RESOLVE = _swap(
    _BASE, _RESOLVE,
    "        results := results\n",
)

# --- R5b: exactly ONE directive is emitted with the right flag, but the
#          identity it carries is taken from the name-resolution result instead
#          of from the item itself. (Attacks C2's carried-identity component,
#          which every other rival here leaves intact.)
_R_WRONG_IDENTITY = _swap(
    _BASE, _EMIT,
    "        -- One directive is emitted, but the identity it carries is taken\n"
    "        -- from the name-resolution result rather than from the item.\n"
    "        let alt : OrderExpr × Bool := (resolveFieldRef item).headD (e, false)\n"
    "        results := results ++ [(alt.1, false)]\n",
)

# --- R6: INVERTED dispatch — expressions routed through name resolution and
#         field references passed over. (Attacks C1 on BOTH arms at once.)
_R_INVERTED = _swap(
    _BASE, _DISPATCH,
    "    match item with\n"
    "    | .expression _ =>\n"
    "        results := results ++ resolveFieldRef item\n"
    "    | .fieldRef _ =>\n"
    "        results := results\n",
)

# --- R7: per-item expansions COMBINED back-to-front. (Attacks C3.)
_R_PREPEND = _swap(
    _BASE, _DISPATCH,
    "    match item with\n"
    "    | .expression e =>\n"
    "        results := [(e, false)] ++ results\n"
    "    | .fieldRef _ =>\n"
    "        results := resolveFieldRef item ++ results\n",
)

# --- R8: the SPECIFICATION is walked back-to-front (per-item expansion right,
#         combination order wrong). (Attacks C3 from the traversal side.)
_R_REVERSE_WALK = _swap(
    _BASE, _FORHEAD,
    "  for item in items.reverse do\n",
)

# --- R9: every per-item expansion and the combination order are gold, but a
#         field reference's OWN resolution list is emitted in reverse. (Attacks
#         C3 at the WITHIN-item granularity, which R7/R8 do not reach: they
#         reverse the order of the pieces, this reverses the order INSIDE one
#         piece. Agrees with the frozen solution on every specification whose
#         field references resolve to at most one directive each.)
_R_WITHIN_ITEM_REVERSED = _swap(
    _BASE, _RESOLVE,
    "        results := results ++ (resolveFieldRef item).reverse\n",
)

# --- R9b: the companion flag is not a constant at all — it is computed from a
#          GLOBAL property of the specification (its length), so the flag is
#          right on every one-item specification and wrong from two items up.
#          (Attacks C2's flag component at a POINT the existing flag rival
#          cannot: that one is wrong everywhere, so a one-item witness catches
#          it; this one agrees with the frozen solution on exactly the region
#          where most of this battery's witnesses live.)
_R_FLAG_FROM_LENGTH = _swap(
    _BASE, _EMIT,
    "        results := results ++ [(e, decide (items.length > 1))]\n",
)

# --- R10: a field reference's resolution is emitted TWICE. (Attacks the
#          field-reference arm's CARDINALITY from above — the mirror of
#          _R_DROP_RESOLVE, which attacks it from below. Every other rival here
#          leaves the field-reference arm's cardinality alone in one direction
#          or the other.)
_R_DUP_RESOLVE = _swap(
    _BASE, _RESOLVE,
    "        results := results ++ resolveFieldRef item ++ resolveFieldRef item\n",
)


# ============================================================== POSITIVES
# Structurally different but CORRECT impls; each one REPROVES the frozen
# obligation with a byte-identical STATEMENT and no new declaration, axiom,
# `sorry`, or `native_decide`. Both proofs were built and close.

# --- P1: the two dispatch arms are written in the opposite order. The proof
#         is the frozen one with the arms reordered to match.
_P_ARMS_SWAPPED = _swap(
    _swap(
        _BASE, _DISPATCH,
        "    match item with\n"
        "    | .fieldRef _ =>\n"
        "        results := results ++ resolveFieldRef item\n"
        "    | .expression e =>\n"
        "        results := results ++ [(e, false)]\n",
    ),
    _PROOF,
    "theorem helper_expandOrdering (items : List OrderingItem)\n"
    "    (init : List (OrderExpr × Bool)) :\n"
    "    Id.run (forIn items init (fun item r =>\n"
    "        (match item with\n"
    "          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)\n"
    "          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])\n"
    "          : Id (ForInStep (List (OrderExpr × Bool))))))\n"
    "      = init ++ items.flatMap expandOrderingItem := by\n"
    "  induction items generalizing init with\n"
    "  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]\n"
    "  | cons a as ih =>\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      cases a with\n"
    "      | expression e =>\n"
    "          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]\n"
    "      | fieldRef name =>\n"
    "          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]\n"
    "\n"
    "theorem correct_expandOrdering :\n"
    "    ∀ (items : List OrderingItem),\n"
    "      problem_spec_expandOrdering items (implementation_expandOrdering items) := by\n"
    "  intro items\n"
    "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
    "  have h2 : (Id.run do\n"
    "        let r ← forIn items [] fun item r =>\n"
    "            match item with\n"
    "            | OrderingItem.fieldRef _ => do\n"
    "              pure PUnit.unit\n"
    "              pure (ForInStep.yield (r ++ resolveFieldRef item))\n"
    "            | OrderingItem.expression e => do\n"
    "              pure PUnit.unit\n"
    "              pure (ForInStep.yield (r ++ [(e, false)]))\n"
    "        pure r)\n"
    "      = Id.run (forIn items [] (fun item r =>\n"
    "        (match item with\n"
    "          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)\n"
    "          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])\n"
    "          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl\n"
    "  rw [h2, helper_expandOrdering]\n"
    "  simp\n",
)

# --- P2: the per-item expansion is hoisted into a `let`-bound piece appended
#         once, instead of two arms each doing their own append.
_P_LET_PIECE = _swap(
    _swap(
        _BASE, _DISPATCH,
        "    let piece : List (OrderExpr × Bool) :=\n"
        "      match item with\n"
        "      | .expression e => [(e, false)]\n"
        "      | .fieldRef _   => resolveFieldRef item\n"
        "    results := results ++ piece\n",
    ),
    _PROOF,
    "theorem helper_expandOrdering (items : List OrderingItem)\n"
    "    (init : List (OrderExpr × Bool)) :\n"
    "    Id.run (forIn items init (fun item r =>\n"
    "        (ForInStep.yield (r ++\n"
    "          (match item with\n"
    "           | OrderingItem.expression e => [(e, false)]\n"
    "           | OrderingItem.fieldRef _ => resolveFieldRef item))\n"
    "          : Id (ForInStep (List (OrderExpr × Bool))))))\n"
    "      = init ++ items.flatMap expandOrderingItem := by\n"
    "  induction items generalizing init with\n"
    "  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]\n"
    "  | cons a as ih =>\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [Id.run, bind] at ih ⊢\n"
    "      cases a with\n"
    "      | expression e =>\n"
    "          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]\n"
    "      | fieldRef name =>\n"
    "          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]\n"
    "\n"
    "theorem correct_expandOrdering :\n"
    "    ∀ (items : List OrderingItem),\n"
    "      problem_spec_expandOrdering items (implementation_expandOrdering items) := by\n"
    "  intro items\n"
    "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
    "  have h2 : (Id.run do\n"
    "        let r ← forIn items [] fun item r =>\n"
    "            let piece : List (OrderExpr × Bool) :=\n"
    "              match item with\n"
    "              | OrderingItem.expression e => [(e, false)]\n"
    "              | OrderingItem.fieldRef _ => resolveFieldRef item\n"
    "            do\n"
    "            pure PUnit.unit\n"
    "            pure (ForInStep.yield (r ++ piece))\n"
    "        pure r)\n"
    "      = Id.run (forIn items [] (fun item r =>\n"
    "        (ForInStep.yield (r ++\n"
    "          (match item with\n"
    "           | OrderingItem.expression e => [(e, false)]\n"
    "           | OrderingItem.fieldRef _ => resolveFieldRef item))\n"
    "          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl\n"
    "  rw [h2, helper_expandOrdering]\n"
    "  simp\n",
)


# ========================================================== ADMISSIBILITY
# No precondition exists to be too strong, so the analogue here is: the modeled
# behavior is SATISFIABLE at a normal, F2P-shaped input — a specification that
# MIXES an already-formed ordering expression with a field reference. A ground
# instance is discharged as a `have` inside the existing tactic body, then the
# frozen obligation is closed verbatim. The theorem STATEMENT is untouched.
_ADMISS = _swap(
    _BASE, _INTRO,
    "  intro items\n"
    "  have _ground : ∀ (e : OrderExpr),\n"
    "      problem_spec_expandOrdering\n"
    "        [OrderingItem.expression e, OrderingItem.fieldRef \"id\"]\n"
    "        (implementation_expandOrdering\n"
    "          [OrderingItem.expression e, OrderingItem.fieldRef \"id\"]) := by\n"
    "    intro e\n"
    "    unfold problem_spec_expandOrdering implementation_expandOrdering\n"
    "    simp only [Id.run, expandOrderingItem, List.flatMap_cons, List.flatMap_nil,\n"
    "      List.append_nil]\n"
    "    rfl\n",
)


SPEC_TESTS = [
    # =================================================== C1: per-item dispatch
    {
        "id": "no-per-item-dispatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_NO_DISPATCH,
        "rationale": "Attacks C1 (per-item dispatch). Every item, including an "
                     "already-formed ordering expression, is sent to the "
                     "name-resolution routine, so a single-element specification "
                     "holding one expression expands to "
                     "`resolveFieldRef (.expression e)` where the frozen helper "
                     "requires `[(e, false)]`. `resolveFieldRef` is `opaque` with "
                     "no constraining axiom, so that equality is not provable and "
                     "the spec refutes the rival wherever the two differ. This is "
                     "the headline weakness: the ENTIRE discriminating content of "
                     "the modeled behavior is that this dispatch exists.",
        "refinement": "Its faithful real patch has no per-item dispatch at all: "
                      "every item of the related model's default ordering "
                      "specification is handed to name resolution, which treats "
                      "its argument as a textual name. Handed an already-built "
                      "ordering expression it fails, so the query errors out and "
                      "the F2P test "
                      "test_order_by_ptr_field_with_default_ordering_by_expression "
                      "does not resolve. This is the reported failure.",
        "witness": (
            "-- Wherever name resolution of an expression item disagrees with the\n"
            "-- single directive the specification demands, the rival's answer\n"
            "-- differs from the specified expansion. One weak assumption about\n"
            "-- ONE opaque term.\n"
            "example (e : OrderExpr)\n"
            "    (hres : resolveFieldRef (OrderingItem.expression e) ≠ [(e, false)]) :\n"
            "    ¬ problem_spec_expandOrdering [OrderingItem.expression e]\n"
            "        (implementation_expandOrdering [OrderingItem.expression e]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp [Id.run, expandOrderingItem]\n"
            "  exact hres\n"
        ),
    },
    {
        "id": "inverted-dispatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_INVERTED,
        "rationale": "Attacks C1 on BOTH arms at once: the dispatch is back to "
                     "front — an already-formed ordering expression is routed "
                     "through name resolution and a field reference is passed over "
                     "contributing nothing. Refuted STRUCTURALLY rather than by "
                     "content: on a two-item specification the specified expansion "
                     "has length `1 + |resolveFieldRef (.fieldRef \"a\")|` while "
                     "the rival's has length "
                     "`|resolveFieldRef (.expression e)|`, so whenever those "
                     "differ the two lists cannot be equal. The length argument "
                     "needs nothing about what either resolution CONTAINS, which "
                     "is why it lands on an opaque carrier.",
        "refinement": "Its faithful real patch inverts the dispatch: field-reference "
                      "items are emitted raw with the no-re-apply flag instead of "
                      "being resolved, while the already-built ordering expression "
                      "is the one sent to name resolution. So it both reproduces the "
                      "original failure on the F2P input AND stops textual field "
                      "names in a default ordering specification from being expanded "
                      "into concrete columns, breaking the default-ordering P2P "
                      "tests too. Doubly not the modeled behavior.",
        "witness": (
            "-- Structural refutation: the two expansions have different lengths\n"
            "-- whenever the assumed inequality holds, so no content knowledge\n"
            "-- about the opaque resolution results is needed.\n"
            "example (e : OrderExpr)\n"
            "    (hlen : (resolveFieldRef (OrderingItem.expression e)).length\n"
            "          ≠ (resolveFieldRef (OrderingItem.fieldRef \"a\")).length + 1) :\n"
            "    ¬ problem_spec_expandOrdering\n"
            "        [OrderingItem.expression e, OrderingItem.fieldRef \"a\"]\n"
            "        (implementation_expandOrdering\n"
            "          [OrderingItem.expression e, OrderingItem.fieldRef \"a\"]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  intro h\n"
            "  apply hlen\n"
            "  have hl := congrArg List.length h\n"
            "  simpa [Id.run, expandOrderingItem, Nat.add_comm] using hl\n"
        ),
    },
    {
        "id": "field-reference-contributes-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_RESOLVE,
        "rationale": "Attacks C1 on the field-reference arm, the near-miss the "
                     "headline rival leaves untouched: the expression dispatch is "
                     "exactly right, but a field reference's resolution is computed "
                     "and then discarded. Refuted at a specification holding ONE "
                     "field reference and no expression at all — the sub-domain "
                     "no EXPRESSION-side rival can reach, since the whole "
                     "expression arm is absent there — where the rival yields the "
                     "empty list and the spec demands "
                     "`resolveFieldRef (.fieldRef \"id\")`. (Two later "
                     "field-reference rivals share this input point; what is "
                     "unique to this case is the DIRECTION of the error at it — "
                     "the arm's contribution collapsed to nothing, versus "
                     "reordered within itself or contributed twice.)",
        "refinement": "Its faithful real patch keeps the new guard but drops the "
                      "recursive expansion of the remaining items, so textual field "
                      "names in a related model's default ordering specification "
                      "are never turned into concrete column directives. The F2P "
                      "input's specification mixes an expression with a plain name, "
                      "so the resulting ordering is short and the rows come back in "
                      "the wrong order; the default-ordering P2P tests break as "
                      "well.",
        "witness": (
            "-- At a specification of one field reference the rival contributes\n"
            "-- nothing; whenever that reference resolves to anything at all, the\n"
            "-- specified expansion is non-empty.\n"
            "example (hres : resolveFieldRef (OrderingItem.fieldRef \"id\") ≠ []) :\n"
            "    ¬ problem_spec_expandOrdering [OrderingItem.fieldRef \"id\"]\n"
            "        (implementation_expandOrdering [OrderingItem.fieldRef \"id\"]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp [Id.run, expandOrderingItem]\n"
            "  exact fun h => hres h.symm\n"
        ),
    },

    # ==================================================== C2: per-item content
    {
        "id": "wrong-companion-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_WRONG_FLAG,
        "rationale": "Attacks C2's flag component, the one part of the modeled "
                     "behavior that is fully TRANSPARENT (a `Bool` literal, no "
                     "opaque term involved) — so this witness needs no hypothesis "
                     "at all. The dispatch is right and the expression's identity "
                     "is carried, but it is emitted paired with `true` where the "
                     "frozen helper requires `false`. Without this rival the flag "
                     "conjunct of the postcondition would be unattacked, and an "
                     "impl that got it backwards would slip through.",
        "refinement": "Its faithful real patch appends the already-built ordering "
                      "expression with the flag that says the surrounding sort "
                      "direction IS to be re-applied to it. Downstream that flag "
                      "decides whether the directive is treated as a reference to "
                      "an already-selected expression, which suppresses re-emitting "
                      "it in the select list and changes the aggregate handling — so "
                      "the query built for the F2P input orders differently from the "
                      "sequence the test asserts. Not the modeled behavior.",
        "witness": (
            "-- Fully concrete: no assumption about the carrier is needed, since\n"
            "-- the flag is a Bool literal on both sides.\n"
            "example (e : OrderExpr) :\n"
            "    ¬ problem_spec_expandOrdering [OrderingItem.expression e]\n"
            "        (implementation_expandOrdering [OrderingItem.expression e]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp only [Id.run, expandOrderingItem, List.flatMap_cons,\n"
            "    List.flatMap_nil, List.append_nil]\n"
            "  show ¬ ([((e : OrderExpr), true)] = [((e : OrderExpr), false)])\n"
            "  simp\n"
        ),
    },
    {
        "id": "wrong-carried-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_WRONG_IDENTITY,
        "rationale": "Attacks C2's IDENTITY component — the one part of the "
                     "per-item content that every other rival here gets right. "
                     "The dispatch fires correctly, exactly one directive is "
                     "emitted, and its flag is `false`; only the identity carried "
                     "in that directive is wrong, taken from the name-resolution "
                     "result rather than from the item itself. Without this rival "
                     "an impl that emitted the right SHAPE around the wrong "
                     "expression would verify, since no other witness varies what "
                     "the carried identity is. Refuted by CONDITIONING on the "
                     "carrier: assume the resolution of an expression item is one "
                     "directive naming some other identity, and that the two "
                     "identities differ. Both assumptions are about ONE opaque "
                     "term plus a plain distinctness, and the probe confirms they "
                     "can hold jointly.",
        "refinement": "Its faithful real patch emits a directive built around a "
                      "DIFFERENT expression than the one the specification listed "
                      "— a freshly constructed one, or the wrong local — so the "
                      "identity is not preserved through the expansion. The F2P "
                      "input sorts by the very expression the specification "
                      "carries, so the query is ordered by something else and the "
                      "rows come back in a sequence the test does not assert. "
                      "Nothing about it is the modeled behavior, so it would not "
                      "resolve.",
        "witness": (
            "-- Wherever an expression item's name resolution names a DIFFERENT\n"
            "-- identity, the rival carries that one instead of the item's own,\n"
            "-- so its directive differs from the specified one.\n"
            "example (e e2 : OrderExpr)\n"
            "    (hres : resolveFieldRef (OrderingItem.expression e) = [(e2, false)])\n"
            "    (hne : e2 ≠ e) :\n"
            "    ¬ problem_spec_expandOrdering [OrderingItem.expression e]\n"
            "        (implementation_expandOrdering [OrderingItem.expression e]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp [Id.run, expandOrderingItem, hres, List.headD, pure, bind]\n"
            "  exact hne\n"
        ),
    },
    {
        "id": "expression-contributes-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DROP_EMIT,
        "rationale": "Attacks C2's cardinality component from below: the ordering "
                     "expression is recognised as needing no resolution (so "
                     "nothing fails) but is then silently skipped, contributing zero "
                     "directives where the spec requires exactly one. Like the "
                     "flag rival this is refutable with NO hypothesis — the "
                     "specified expansion of a one-expression specification is a "
                     "literal singleton, and `[] ≠ [(e, false)]` needs nothing "
                     "about the opaque carrier.",
        "refinement": "Its faithful real patch recognises an already-built ordering "
                      "expression as needing no resolution but then omits it from "
                      "the expansion entirely. Nothing errors out, but the query is "
                      "missing the directive it must sort by, so the F2P input's "
                      "rows come back in an order the test does not assert. Subtler "
                      "than the reported failure and still not the modeled "
                      "behavior.",
        "witness": (
            "-- Concrete AND evaluated: with the Id-monad carrier in the simp set\n"
            "-- (`pure`/`bind`) the rival's loop is actually RUN at this one-expression\n"
            "-- specification, and its answer comes out empty where the specified\n"
            "-- expansion is the literal singleton. Nothing about the opaque carrier is\n"
            "-- needed.\n"
            "--\n"
            "-- Evaluating rather than leaving the carrier wrapped is what makes the\n"
            "-- frozen solution's REJECTION of this witness mean something. There the\n"
            "-- same script reduces the same side to `[(e, false)]` and stops at\n"
            "-- `[(e, false)] = []` -- the frozen value exhibited against the claimed\n"
            "-- one -- while the identical script PROVES the opposite claim\n"
            "-- (`... = [(e, false)]`, i.e. that the frozen solution DOES satisfy the\n"
            "-- specification at this input). So the failure there is claim-dependent,\n"
            "-- not a carrier that never reduced. `List.nil_append` is in the set for\n"
            "-- that direction: it is the frozen `results ++ [(e, false)]` that needs it.\n"
            "example (e : OrderExpr) :\n"
            "    ¬ problem_spec_expandOrdering [OrderingItem.expression e]\n"
            "        (implementation_expandOrdering [OrderingItem.expression e]) := by\n"
            "  have hval : implementation_expandOrdering [OrderingItem.expression e]\n"
            "      = ([] : List (OrderExpr × Bool)) := by\n"
            "    simp only [implementation_expandOrdering, Id.run, List.forIn_cons,\n"
            "      List.forIn_nil, pure, bind, List.nil_append]\n"
            "  unfold problem_spec_expandOrdering\n"
            "  rw [hval]\n"
            "  simp [expandOrderingItem]\n"
        ),
    },
    {
        "id": "expression-emitted-and-also-resolved",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_EMIT_AND_RESOLVE,
        "rationale": "Attacks C2's cardinality component from ABOVE — the mirror of "
                     "the drop rival, and the near-miss that AGREES with the frozen "
                     "solution on any specification whose expression items resolve "
                     "to nothing. It emits the correct directive and then ALSO "
                     "appends the expression's name resolution, so it contributes "
                     "one directive too many wherever that resolution is non-empty. "
                     "Refuted at exactly that sub-domain, which is why it gets its "
                     "own hypothesis rather than sharing the headline rival's.",
        "refinement": "Its faithful real patch emits the already-built ordering "
                      "expression directly but then ALSO falls through into name "
                      "resolution on that same item. Name resolution treats its "
                      "argument as a textual name, so on the F2P input the query "
                      "fails exactly as it did originally and the test does not "
                      "resolve. (Even were the fall-through harmless, the directive "
                      "would be duplicated and the ordering wrong.)",
        "witness": (
            "-- Wherever an expression item's name resolution is non-empty, the\n"
            "-- rival emits strictly more than the single specified directive.\n"
            "example (e : OrderExpr)\n"
            "    (hres : resolveFieldRef (OrderingItem.expression e) ≠ []) :\n"
            "    ¬ problem_spec_expandOrdering [OrderingItem.expression e]\n"
            "        (implementation_expandOrdering [OrderingItem.expression e]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp only [Id.run, expandOrderingItem, List.flatMap_cons,\n"
            "    List.flatMap_nil, List.append_nil]\n"
            "  show ¬ (([] ++ [((e : OrderExpr), false)]\n"
            "      ++ resolveFieldRef (OrderingItem.expression e))\n"
            "      = [((e : OrderExpr), false)])\n"
            "  simp\n"
            "  exact hres\n"
        ),
    },

    # ======================================================= C3: combination
    {
        "id": "expansions-combined-back-to-front",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_PREPEND,
        "rationale": "Attacks C3 (the combination order). Both dispatch arms are "
                     "right and every per-item expansion is right; only the way "
                     "they are combined is reversed. Refuted at a specification of "
                     "TWO DISTINCT ordering expressions — the only shape at which "
                     "piece ORDER has content, since a one-item specification "
                     "cannot exhibit a reordering at all — where the rival returns "
                     "the pair swapped. The hypothesis is a plain distinctness "
                     "assumption about the two carried identities, not a claim "
                     "about the resolver. (The reverse-walk rival shares this "
                     "input point, and provably must: an audit proved the two "
                     "impls are the SAME function — see that case's rationale.)",
        "refinement": "Its faithful real patch builds the expansion by inserting "
                      "each item's directives at the front of the accumulator "
                      "instead of extending it, so a related model's default "
                      "ordering is applied in reverse precedence. On the F2P input "
                      "the primary and secondary sort keys trade places and the rows "
                      "come back in a different sequence from the one the test "
                      "asserts; the multi-key default-ordering P2P tests break too.",
        "witness": (
            "-- Two distinct ordering expressions come out swapped, so under the\n"
            "-- distinctness assumption the two lists differ.\n"
            "example (e1 e2 : OrderExpr) (hne : e1 ≠ e2) :\n"
            "    ¬ problem_spec_expandOrdering\n"
            "        [OrderingItem.expression e1, OrderingItem.expression e2]\n"
            "        (implementation_expandOrdering\n"
            "          [OrderingItem.expression e1, OrderingItem.expression e2]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp only [Id.run, expandOrderingItem, List.flatMap_cons,\n"
            "    List.flatMap_nil, List.append_nil]\n"
            "  show ¬ (([((e2 : OrderExpr), false)] ++ ([((e1 : OrderExpr), false)] ++ []))\n"
            "      = [((e1 : OrderExpr), false)] ++ [((e2 : OrderExpr), false)])\n"
            "  simp\n"
            "  exact fun _ => hne\n"
        ),
    },
    {
        "id": "specification-walked-back-to-front",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_REVERSE_WALK,
        "rationale": "Attacks C3 from the traversal side rather than the "
                     "accumulator side: the per-item expansion and the append "
                     "direction are both gold, but the specification itself is "
                     "walked in reverse, so the expansions are concatenated in "
                     "reverse specification order. Kept as a SHAPE probe, not as "
                     "an independent clause: an audit proved by induction that "
                     "this rival and the prepend rival denote the SAME function "
                     "(`∀ items, implR7 items = implR8 items` closes), so it adds "
                     "no discriminating power over that one — the two are the same "
                     "wrongness reached by reversing either end. It is retained "
                     "because the two impls are syntactically far apart (a "
                     "reversed traversal versus a reversed accumulator) and a "
                     "battery that only ever mutated the accumulator would leave "
                     "the loop HEADER unprobed; its rejection is still earned, its "
                     "witness still discriminates, and the earlier claim that the "
                     "two 'differ from gold' in DISTINCT ways was overstated and is "
                     "corrected here.",
        "refinement": "Its faithful real patch iterates the related model's default "
                      "ordering specification in reverse, so the expansion applies "
                      "the sort keys in the opposite precedence. On the F2P input "
                      "the rows come back ordered by the secondary key first, which "
                      "is not the sequence the test asserts; the multi-key "
                      "default-ordering P2P tests break as well.",
        "witness": (
            "-- Same distinctness assumption, same failing shape: reversing the\n"
            "-- walk swaps the two expressions' directives.\n"
            "example (e1 e2 : OrderExpr) (hne : e1 ≠ e2) :\n"
            "    ¬ problem_spec_expandOrdering\n"
            "        [OrderingItem.expression e1, OrderingItem.expression e2]\n"
            "        (implementation_expandOrdering\n"
            "          [OrderingItem.expression e1, OrderingItem.expression e2]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp only [Id.run, expandOrderingItem, List.flatMap_cons,\n"
            "    List.flatMap_nil, List.append_nil, List.reverse_cons,\n"
            "    List.reverse_nil, List.nil_append, List.cons_append]\n"
            "  show ¬ (([] ++ [((e2 : OrderExpr), false)]) ++ [((e1 : OrderExpr), false)]\n"
            "      = [((e1 : OrderExpr), false)] ++ [((e2 : OrderExpr), false)])\n"
            "  simp\n"
            "  exact fun _ => hne\n"
        ),
    },

    {
        "id": "field-reference-resolution-reversed-within-item",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_WITHIN_ITEM_REVERSED,
        "rationale": "Attacks C3 at a granularity the two combination-order "
                     "rivals cannot reach. They reverse the order of the PIECES; "
                     "this reverses the order INSIDE one piece — a field "
                     "reference's own resolution list is emitted back-to-front "
                     "while the per-item dispatch, the companion flags, the "
                     "cardinalities and the front-to-back concatenation of pieces "
                     "are all exactly gold. It therefore agrees with the frozen "
                     "solution on every specification whose field references each "
                     "resolve to at most ONE directive, which is why neither "
                     "existing order rival touches it: their two-expression "
                     "witnesses are in that agreement region. Refuted by "
                     "CONDITIONING on the carrier at the smallest point where the "
                     "clause has content — one field reference whose resolution is "
                     "a two-element list of distinct directives.",
        "refinement": "Its faithful real patch keeps the per-item dispatch but "
                      "reverses each resolved name's own directive list before "
                      "extending the accumulator. A multi-part lookup on a related "
                      "model resolves to several concrete column directives, so "
                      "those columns are applied in the opposite precedence within "
                      "the single ordering item — the rows come back sorted by the "
                      "last column of the lookup first, which is not the sequence "
                      "the default-ordering tests assert.",
        "witness": (
            "-- Conditioned at the smallest point where within-item order has\n"
            "-- content: ONE field reference resolving to two distinct directives.\n"
            "-- The rival emits them swapped; the specification emits them as the\n"
            "-- resolution gives them.\n"
            "example (a b : OrderExpr × Bool)\n"
            "    (hres : resolveFieldRef (OrderingItem.fieldRef \"id\") = [a, b])\n"
            "    (hne : a ≠ b) :\n"
            "    ¬ problem_spec_expandOrdering [OrderingItem.fieldRef \"id\"]\n"
            "        (implementation_expandOrdering [OrderingItem.fieldRef \"id\"]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp [Id.run, expandOrderingItem, hres, pure, bind]\n"
            "  exact fun _ => hne\n"
        ),
    },
    {
        "id": "companion-flag-computed-from-specification-length",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_FLAG_FROM_LENGTH,
        "rationale": "Attacks C2's flag component at a point the existing flag "
                     "rival cannot reach. That one pairs the expression with "
                     "`true` unconditionally, so it is wrong at EVERY input and a "
                     "one-item witness refutes it; this one computes the flag from "
                     "a global property of the specification (its length), so it "
                     "agrees with the frozen solution on every one-item "
                     "specification — the region where most of this battery's "
                     "witnesses sit — and diverges only from two items up. The "
                     "clause it probes is that the flag is a CONSTANT of the "
                     "per-item expansion, not a function of the surrounding "
                     "specification: `expandOrderingItem` is applied per item by "
                     "`flatMap`, so an item's contribution cannot depend on how "
                     "many other items accompany it. Refuted with NO hypothesis, "
                     "since the flag is a `Bool` literal on both sides once the "
                     "length is evaluated.",
        "refinement": "Its faithful real patch derives the no-re-apply flag from "
                      "the shape of the ordering specification as a whole rather "
                      "than fixing it per directive — so a single-item default "
                      "ordering is expanded correctly while any multi-item one "
                      "flags every already-built expression as needing the "
                      "surrounding direction re-applied. The F2P input's "
                      "specification carries more than one item, so its expression "
                      "gets the wrong flag and the query orders differently from "
                      "the sequence the test asserts. Passes the single-key "
                      "default-ordering tests, which is what makes it the "
                      "dangerous shape.",
        "witness": (
            "-- Concrete: at a two-expression specification the length exceeds\n"
            "-- one, so the rival flags BOTH directives `true` where the\n"
            "-- specification demands `false`. No assumption about the carrier.\n"
            "example (e1 e2 : OrderExpr) :\n"
            "    ¬ problem_spec_expandOrdering\n"
            "        [OrderingItem.expression e1, OrderingItem.expression e2]\n"
            "        (implementation_expandOrdering\n"
            "          [OrderingItem.expression e1, OrderingItem.expression e2]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp only [Id.run, expandOrderingItem, List.flatMap_cons,\n"
            "    List.flatMap_nil, List.append_nil]\n"
            "  show ¬ ([((e1 : OrderExpr), true), ((e2 : OrderExpr), true)]\n"
            "      = [((e1 : OrderExpr), false)] ++ [((e2 : OrderExpr), false)])\n"
            "  simp\n"
        ),
    },
    {
        "id": "field-reference-resolution-duplicated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_DUP_RESOLVE,
        "rationale": "Attacks the field-reference arm's CARDINALITY from ABOVE — "
                     "the direction no other rival covers. The battery already "
                     "probes that arm from below (its resolution discarded "
                     "entirely) and the expression arm from both sides, but "
                     "nothing catches a field reference whose resolution is "
                     "contributed too MANY times. The dispatch, the identities, "
                     "the flags and the piece order are all gold; only the "
                     "multiplicity of one arm's contribution is wrong. Refuted at "
                     "a specification of one field reference, on the weakest "
                     "hypothesis that makes the clause non-vacuous: that the "
                     "reference resolves to anything at all.",
        "refinement": "Its faithful real patch extends the accumulator with the "
                      "resolved directives and then falls through to extend it "
                      "again with the same resolution — a duplicated extend rather "
                      "than a dispatch error. Every textual name in a related "
                      "model's default ordering contributes its columns twice, so "
                      "the ordering carries repeated keys and the query's sort "
                      "sequence is not the one the default-ordering tests assert.",
        "witness": (
            "-- Wherever the reference resolves to anything at all, contributing\n"
            "-- its resolution twice differs from contributing it once.\n"
            "example (hres : resolveFieldRef (OrderingItem.fieldRef \"id\") ≠ []) :\n"
            "    ¬ problem_spec_expandOrdering [OrderingItem.fieldRef \"id\"]\n"
            "        (implementation_expandOrdering [OrderingItem.fieldRef \"id\"]) := by\n"
            "  unfold problem_spec_expandOrdering implementation_expandOrdering\n"
            "  simp [Id.run, expandOrderingItem, pure, bind]\n"
            "  exact hres\n"
        ),
    },

    # ================================================ POSITIVES (soundness)
    {
        "id": "pos-dispatch-arms-swapped",
        "kind": "soundness",
        "expect": "verify",
        "module": _P_ARMS_SWAPPED,
        "rationale": "A structurally different but observationally IDENTICAL impl: "
                     "the two dispatch arms are written in the opposite order. The "
                     "obligation is REPROVEN — the frozen induction is carried over "
                     "with its arms reordered to match the new match expression — "
                     "with the theorem STATEMENT byte-identical, no new "
                     "declaration, no new axiom, no `sorry`. Must verify; a "
                     "rejection would be SPEC-TOO-STRONG, i.e. the spec pinning the "
                     "SHAPE of the dispatch rather than its behavior.",
    },
    {
        "id": "pos-let-bound-piece",
        "kind": "soundness",
        "expect": "verify",
        "module": _P_LET_PIECE,
        "rationale": "A more strongly restructured correct impl: instead of two arms "
                     "each extending the accumulator, the per-item expansion is "
                     "computed into a `let`-bound local and appended once, so the "
                     "loop body has a single append site. Same content, same "
                     "front-to-back direction. Reproven by the same induction "
                     "generalized over the accumulator, statement byte-identical. "
                     "Must verify; a rejection would be SPEC-TOO-STRONG.",
    },

    # ==================================================== ADMISSIBILITY
    {
        "id": "admiss-mixed-specification",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "The obligation binds every specification with no "
                     "precondition, so the analogue of PRECOND-TOO-STRONG here is "
                     "unsatisfiability at a normal input. A ground instance is "
                     "discharged at the F2P-shaped specification that MIXES an "
                     "already-formed ordering expression with a plain field "
                     "reference — the exact combination the reported failure needs "
                     "— as a `have` inside the existing tactic body, after which the "
                     "frozen obligation is closed verbatim. If the modeled behavior "
                     "were unsatisfiable at that mixed input this case would fail. "
                     "Nothing is assumed: the theorem STATEMENT is untouched, no new "
                     "declaration, axiom or `sorry`. The ground `have` is "
                     "LOAD-BEARING, not decoration: an audit built that same "
                     "instance against two wrong impls and it FAILS on both (the "
                     "no-dispatch shape and the drop-emission shape), with `rfl` "
                     "reporting the two sides not definitionally equal — so it "
                     "discharges only because the modeled behavior really does hold "
                     "at that concrete mixed specification.",
    },
]
