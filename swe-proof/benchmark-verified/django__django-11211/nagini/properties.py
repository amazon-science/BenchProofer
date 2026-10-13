# properties.py — PBT manifest for django__django-11211. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) executes + stamps.
#
# Defended surface (frozen spec of prepare_key(value: Value) -> Value):
#   READ-ONLY input  : value held at Acc(value.is_none,1/2) & Acc(value.canon,1/2)
#                       & Acc(value.key,1/2) & Acc(value.is_canon_form,1/2)
#                       -> frame-mutation MANDATORY.
#   post clauses      :
#     (P1) Result().is_none == value.is_none                     (faithfulness)
#     (P2) Result().canon   == value.canon                       (faithfulness)
#     (P3) Implies(not value.is_none, Result().key == value.canon)  <- DISCRIMINATING
#     (P4) Implies(value.is_none,     Result().key == value.key)
#     (P5) Implies(not value.is_none, Result().is_canon_form)       <- DISCRIMINATING
#     (P6) Implies(not value.is_none,
#                  matches_target_key(Result(), value.canon))       <- the join predicate
#     (P7) Implies(value.is_none,
#                  Result().is_canon_form == value.is_canon_form)
#   The join key has TWO halves and both are pinned: the numeric part (P3) and the
#   FORM the key is held in (P5), because the in-Python join compares keys with the
#   host language's equality and a key outside the canonical object form never
#   compares equal to one inside it however its number reads. P6 states P3+P5 as
#   the predicate they exist to satisfy. A rival that delivers only the number
#   (the `overapprox-right-number-wrong-form` case below) is the shape that once
#   verified against a numeric-only spec while its patch left the prefetch join
#   resolving to nothing; it must now reject.
#   The oracle is GROUNDED: the load-bearing key is value.canon (a function of the
#   input arg) and the load-bearing form is a constant True, NOT an opaque @Pure
#   answer-key. matches_target_key is a transparent conjunction of the result's own
#   facets, so it cannot be echoed off the input to discharge P5 — see the
#   `oracle-echo-form-from-input` case.
#   Axioms base_prepare / canonicalize are A-consumed @ContractOnly callees; the
#   axiom lane re-runs the REAL callees (Field.get_prep_value / UUIDField.to_python)
#   in-container and asserts each axiom's Ensures (all four facets) + the join-key
#   match + the demonstration that a same-numbered key in another form misses.
#
# Region surgery: every SPEC_TESTS module is built by _swap on the frozen model.py,
# editing ONLY text inside the # impl-start / # impl-end region, so same_spec holds.

from pathlib import Path

INSTANCE = "django__django-11211"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact two-line gold impl body inside the impl region (the unique swap anchor).
_GOLD_IMPL = (
    "    coerced = base_prepare(value)  # type: Value\n"
    "    return canonicalize(coerced)\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: anchor not found: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


def _impl(body: str) -> str:
    """Return full model.py source with the gold impl body replaced by `body`
    (body must be the lines BETWEEN # impl-start and # impl-end, already indented)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---------------------------------------------------------------------------
# SPEC LANE
# ---------------------------------------------------------------------------
SPEC_TESTS = [

    # --- POSITIVE CONTROL (soundness) --------------------------------------
    # Structurally different but CORRECT: branch on emptiness and build the
    # result with the SAME two A-consumed callees, but composed via an explicit
    # local and an is_none split rather than the straight-line composition. This
    # keeps every gold proof obligation (it still uses both axioms' Ensures) and
    # only reshapes the executable control flow. Must verify (else SPEC-TOO-STRONG).
    {
        "id": "pos-control-branch-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    coerced = base_prepare(value)  # type: Value\n"
            "    if coerced.is_none:\n"
            "        return canonicalize(coerced)\n"
            "    else:\n"
            "        result = canonicalize(coerced)  # type: Value\n"
            "        Assert(matches_target_key(result, value.canon))\n"
            "        return result\n"
        ),
        "rationale": (
            "A correct impl that reshapes control flow (explicit is_none branch + "
            "named local) while still consuming both A-consumed axioms must verify; "
            "if it cannot, the postcondition over-constrains a faithful impl "
            "(SPEC-TOO-STRONG). It keeps base_prepare then canonicalize, so both "
            "axiom Ensures still discharge P1-P7 on both branches; the extra Assert "
            "shows the join predicate P6 is DERIVABLE from the axioms and is not a "
            "clause only the literal gold text can meet."
        ),
    },

    # --- ADMISSIBILITY ------------------------------------------------------
    # A caller builds an F2P-shaped Value (a non-empty TEXTUAL storage form: its
    # join key is not the canonical identity AND it is not held in the canonical
    # object form — is_none=False, canon=7, key=3, is_canon_form=False) and runs
    # the specified preparation pipeline on it, then asserts the discriminating
    # guarantee (both halves, and the join predicate) holds for that concrete
    # input. Verifies iff the contracts admit a normal prefetch input (else
    # PRECOND-TOO-STRONG). Probe lives in the impl region; the contract of
    # prepare_key is untouched.
    {
        "id": "admiss-textual-form-caller",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # admissibility probe: a non-empty TEXTUAL storage form (key 3 !=\n"
            "    # canon 7, and not held in the canonical object form) is an\n"
            "    # F2P-shaped input the prefetch join feeds.\n"
            "    probe = Value(False, 7, 3, False)  # type: Value\n"
            "    probe_c = base_prepare(probe)  # type: Value\n"
            "    prepared = canonicalize(probe_c)  # type: Value\n"
            "    Assert(prepared.key == 7)\n"
            "    Assert(prepared.is_none == False)\n"
            "    Assert(prepared.canon == 7)\n"
            "    Assert(prepared.is_canon_form)\n"
            "    Assert(matches_target_key(prepared, 7))\n"
            "    coerced = base_prepare(value)  # type: Value\n"
            "    return canonicalize(coerced)\n"
        ),
        "rationale": (
            "The contracts must admit a normal non-empty storage-form input "
            "(is_none=False, canon!=key, is_canon_form=False) — exactly what the "
            "prefetch join feeds when the holder's key was stored as text. The probe "
            "asserts both halves of the canonical-key guarantee AND the join "
            "predicate for that input, derived through the same axiom pipeline the "
            "impl uses. Note the input form is deliberately NOT constrained by any "
            "Requires: no carrier well-formedness precondition was added, so the "
            "admitted domain still contains textual, integer and already-canonical "
            "forms. If the Requires could not be established for it, "
            "PRECOND-TOO-STRONG."
        ),
    },

    # --- THE RECORDED REFUTATION (now closed) ------------------------------
    # Delivers the right NUMBER in whatever form the input happened to be held
    # in: Result().key == value.canon (P3 holds!) and P1/P2/P4 hold, but the
    # prepared key is not established to be in the canonical object form. This
    # is the shape that verified against the earlier numeric-only spec, and whose
    # corresponding real patch (return self.to_python(value).int) leaves the
    # in-Python prefetch join resolving to nothing.
    {
        "id": "overapprox-right-number-wrong-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # over-approximation: right numeric key, unconstrained FORM. The\n"
            "    # empty branch is faithful, so the rejection is attributable purely\n"
            "    # to the form half of the join key.\n"
            "    if value.is_none:\n"
            "        return Value(True, value.canon, value.key, value.is_canon_form)\n"
            "    return Value(False, value.canon, value.canon, value.is_canon_form)\n"
        ),
        "refinement": (
            "The corresponding real patch is `return self.to_python(value).int`: it "
            "canonicalizes and then hands back the 128-bit number instead of the "
            "canonical uuid.UUID. The prefetch join is a dict keyed by the target's "
            "(pk, class) pair and looked up with the holder's (prepared, class) pair "
            "(django/db/models/query.py:1746-1749 build, :1770 look up; "
            "django/contrib/contenttypes/fields.py:210 target key, :205 holder key). "
            "hash(u) == hash(u.int) but u != u.int, so the lookup lands in the right "
            "bucket and then compares UNEQUAL: the relation resolves to None and "
            "test_prefetch_GFK_uuid_pk FAILS (measured: F2P 0/1, P2P 76/76). It must "
            "be rejected at the spec level."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P5: Implies(not value.is_none, "
            "Result().is_canon_form). The returned form facet is copied from the "
            "input, which no Requires constrains, so it is not provably True. P6 "
            "fails for the same reason. P1-P4 all hold, which is what makes this the "
            "sharp test of the form half. Must reject."
        ),
    },

    # --- FRAME-MUTATION (MANDATORY: read-only input) -----------------------
    # value is held at Acc(.,1/2). This rival tries to satisfy P3 vacuously by
    # OVERWRITING the read-only input's join key (value.key = value.canon) and
    # returning the input. With only 1/2 permission on value.key this WRITE is
    # ill-typed: it must fail for INSUFFICIENT PERMISSION, not for a value reason.
    # We keep the gold spec verbatim so the rejection is attributable to the write.
    {
        "id": "frame-mutate-write-input-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # frame-mutation attack: overwrite the read-only input to make\n"
            "    # its own key the canonical identity, then return it. Requires\n"
            "    # WRITE permission on value.key, but only Acc(value.key,1/2) is held.\n"
            "    value.key = value.canon\n"
            "    return value\n"
        ),
        "refinement": (
            "Mutating the caller's stored value in place is NOT what the real patched "
            "method does (it returns to_python(value), a fresh canonical uuid.UUID; it "
            "never rebinds the holder's object_pk). A faithful real patch shaped like "
            "this would corrupt the holder's stored object_pk and would not resolve "
            "test_prefetch_GFK_uuid_pk (and breaks P2P). It must be rejected at the "
            "spec level for insufficient permission."
        ),
        "rationale": (
            "REJECTION SOURCE = permission system: value.key is held at Acc(.,1/2) "
            "(read-only), so the assignment value.key = value.canon is ill-typed "
            "(insufficient permission to write). This is the #1 weakness class and "
            "must reject."
        ),
    },

    # --- FRAME-MUTATION on the FORM facet ----------------------------------
    # The same attack aimed at the newly pinned facet: forge BOTH halves of the
    # join key in the read-only input and return it. Must fail for insufficient
    # permission on value.is_canon_form — i.e. the new facet is protected by the
    # same frame the older ones are, not silently writable.
    {
        "id": "frame-mutate-write-input-form",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # frame-mutation attack on the form facet: stamp the canonical form\n"
            "    # flag and the canonical number onto the READ-ONLY input, then return\n"
            "    # it. Needs WRITE permission on value.is_canon_form; only\n"
            "    # Acc(value.is_canon_form,1/2) is held.\n"
            "    value.is_canon_form = True\n"
            "    value.key = value.canon\n"
            "    return value\n"
        ),
        "refinement": (
            "The real patched method cannot re-label the form of the caller's stored "
            "value: a str stays a str until to_python parses it into a NEW uuid.UUID. "
            "A patch that mutated the holder's own object_pk in place would corrupt "
            "the holder row and still not produce a matchable key. Rejected for "
            "insufficient permission on the newly pinned facet, which shows the form "
            "flag cannot be forged through the frame."
        ),
        "rationale": (
            "REJECTION SOURCE = permission system: value.is_canon_form is held at "
            "Acc(.,1/2) (read-only), so the assignment is ill-typed (insufficient "
            "permission to write). Must reject."
        ),
    },

    # --- FRAME-MUTATION variant: also write canon -------------------------
    # A second framing attack that overwrites BOTH input facets it would need to
    # forge a passing return value (value.key=value.canon trivially holds after a
    # write of value.canon too). Still a half-permission write -> reject.
    {
        "id": "frame-mutate-write-input-both",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # frame-mutation attack (variant): rewrite both join facets of the\n"
            "    # read-only input so the returned input trivially satisfies P3.\n"
            "    value.canon = value.key\n"
            "    value.key = value.canon\n"
            "    return value\n"
        ),
        "refinement": (
            "Rewriting the input's canonical identity to its stored key is the "
            "OPPOSITE of canonicalizing (it makes canon follow the raw key). A "
            "faithful real patch doing this would map every stored str to its own "
            "raw identity, never the canonical UUID, and would NOT resolve the F2P "
            "(the join still mismatches). Must be rejected for insufficient "
            "permission on the read-only value."
        ),
        "rationale": (
            "REJECTION SOURCE = permission system: value.canon / value.key are "
            "Acc(.,1/2) read-only; writing either is ill-typed. Also violates P2 "
            "(canon must be preserved) — but the verifier rejects on permission "
            "first."
        ),
    },

    # --- PARTIAL-DOMAIN: drops canonicalization (the prepatch shape) -------
    # Correct on the EMPTY sub-domain (P4/P7 hold, key and form pass through) but
    # WRONG on every non-empty value: returns base_prepare(value) whose key is the
    # as-stored join key and whose form is the as-stored form, so P5 (and P3) fail.
    # This is exactly the pre-patch behaviour.
    {
        "id": "partial-domain-drop-canonicalize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # partial-domain: only the base coercion, NO canonicalize. Correct\n"
            "    # for None / already-canonical values; wrong for any stored form\n"
            "    # whose raw key != its canonical identity or that is not held in\n"
            "    # the canonical object form.\n"
            "    return base_prepare(value)\n"
        ),
        "refinement": (
            "This is the pre-patch UUIDField behaviour (no own get_prep_value, only "
            "inherited Field.get_prep_value). It is exactly model_prepatch.py, which "
            "fails the canonical-form clause. A real patch shaped this way leaves the "
            "stored str keyed by itself and still a str, so the GFK prefetch join "
            "silently returns None and test_prefetch_GFK_uuid_pk FAILS (the "
            "documented prepatch_models fails_on)."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P5 (reported first): base_prepare "
            "preserves the form facet (axiom), so Result().is_canon_form == "
            "value.is_canon_form, which no Requires makes True. P3 fails for the "
            "matching reason on the numeric half. Must reject."
        ),
    },

    # --- PARTIAL-DOMAIN: canonicalize only what is already canonical -------
    # Guards the canonicalizing step on the value ALREADY being in the canonical
    # object form, so it is correct exactly where nothing needed doing and is the
    # identity precisely on the inputs the F2P exercises.
    {
        "id": "partial-domain-canon-form-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # partial-domain guard: only canonicalize a value that is ALREADY in\n"
            "    # the canonical object form; hand any other form straight back.\n"
            "    coerced = base_prepare(value)  # type: Value\n"
            "    if coerced.is_canon_form:\n"
            "        return canonicalize(coerced)\n"
            "    return coerced\n"
        ),
        "refinement": (
            "The real patch of this shape is `if isinstance(value, uuid.UUID): return "
            "self.to_python(value); return value` — it does nothing on exactly the "
            "textual stored form the prefetch join has to match, which is the only "
            "case that ever needed preparing. The F2P stores object_pk as text, so "
            "this patch leaves the join key a str and test_prefetch_GFK_uuid_pk still "
            "FAILS. Must reject."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P5/P3 on the else-branch: with "
            "coerced.is_canon_form false and value non-empty, the returned value has "
            "is_canon_form == False and key == value.key, neither of which discharges "
            "the non-empty obligation. Must reject."
        ),
    },

    # --- PARTIAL-DOMAIN: canonical only when already-canonical -------------
    # An impl that returns the value's stored key for non-empty inputs but
    # fabricates is_none/canon faithfully AND stamps the canonical form flag —
    # i.e. it delivers the FORM half but keeps the raw NUMBER. Correct on inputs
    # that happen to be already canonical (key==canon) but wrong on a textual
    # storage form (key != canon). The mirror image of the recorded refutation.
    {
        "id": "partial-domain-keep-raw-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # partial-domain: build a faithful-looking result that PRESERVES\n"
            "    # is_none and canon (P1,P2 hold) and claims the canonical FORM, but\n"
            "    # keeps the RAW join key for non-empty values. Passes only when key\n"
            "    # already equals canon.\n"
            "    result = Value(value.is_none, value.canon, value.key, True)  # type: Value\n"
            "    return result\n"
        ),
        "refinement": (
            "Returning a value in the canonical form but carrying the raw join key is "
            "precisely the defect the added preparation exists to remove: a stored str "
            "form keeps its own key, so the in-Python prefetch dict keys it "
            "differently from the uuid.UUID pk and the join misses. A faithful real "
            "patch of this shape (e.g. `return uuid.UUID(int=0) if False else value` "
            "style metadata-only normalisation) does NOT resolve "
            "test_prefetch_GFK_uuid_pk."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P3: this returns Result().key == "
            "value.key, which for a non-empty value with key != canon is not == "
            "value.canon. P1, P2, P5 and P7 hold, so the rejection is purely the "
            "numeric half of the discriminating clause. It also fails P4 nothing — "
            "the empty branch is faithful. Must reject."
        ),
    },

    # --- BOUNDARY TOKEN SWAP: the emptiness guard, inverted ----------------
    # Swaps which side of the emptiness boundary gets the canonicalizing
    # treatment: an EMPTY value is turned into a non-empty canonical key and a
    # non-empty one is prepared correctly. Tests that the empty/non-empty
    # boundary token in the postcondition is load-bearing in both directions.
    {
        "id": "boundary-swap-emptiness-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # boundary token swap: treat the EMPTY value as the one needing a\n"
            "    # canonical key, and prepare the non-empty ones normally.\n"
            "    if value.is_none:\n"
            "        return Value(False, value.canon, value.canon, True)\n"
            "    coerced = base_prepare(value)  # type: Value\n"
            "    return canonicalize(coerced)\n"
        ),
        "refinement": (
            "A real patch of this shape invents an identifier where the holder stored "
            "none (`if value is None: return uuid.UUID(int=0)`). The GFK prefetch "
            "would then look up a non-existent target for every holder row with a "
            "null object_pk, and `get_prep_value(None)` returning a UUID breaks the "
            "NULL round-trip that P2P covers (get_db_prep_value(None) must stay None, "
            "django/db/models/fields/__init__.py:2332-2333). Must reject."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P1: Result().is_none == value.is_none "
            "fails on the empty branch (it returns is_none=False for an empty input). "
            "P4/P7 fail there too. The non-empty branch is gold, so the rejection is "
            "attributable purely to the boundary swap. Must reject."
        ),
    },

    # --- ORACLE ECHO: read the form flag off the input instead of establishing it
    # matches_target_key is the spec's own join predicate. This rival tries to
    # discharge P5/P6 by ECHOING that predicate on the INPUT (which is not
    # constrained to satisfy it) rather than by canonicalizing. If the predicate
    # were an opaque answer-key this would verify; because it is a transparent
    # conjunction of the RESULT's facets, echoing the input proves nothing.
    {
        "id": "oracle-echo-form-from-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # oracle echo: take the form flag from the spec's own join predicate\n"
            "    # applied to the INPUT, and pair it with the canonical number.\n"
            "    echoed = matches_target_key(value, value.canon)  # type: bool\n"
            "    return Value(value.is_none, value.canon, value.canon, echoed)\n"
        ),
        "refinement": (
            "A real patch of this shape asks whether the stored value ALREADY looks "
            "like a matchable key and, if not, hands back something unmatchable "
            "anyway (`return value if isinstance(value, uuid.UUID) else "
            "self.to_python(value).int`). On the F2P's textual object_pk the echo is "
            "False, so the prepared key is a bare int, the join misses and "
            "test_prefetch_GFK_uuid_pk FAILS. Must reject."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P5: matches_target_key(value, "
            "value.canon) is not provably True for an arbitrary admitted input (a "
            "textual form has is_canon_form False and key != canon), so the echoed "
            "flag is not provably True either. The spec's predicate is grounded in "
            "the result's own facets, not an opaque oracle, so it cannot be used as "
            "an answer-key. Must reject."
        ),
    },

    # --- OVER-APPROXIMATION: the form half only ----------------------------
    # The exact complement of the recorded refutation: stamp the canonical form
    # flag on every result while keeping the raw number. Confirms neither half of
    # the join key can be traded for the other.
    {
        "id": "overapprox-form-only-raw-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # over-approximation of the FORM half alone: always claim the\n"
            "    # canonical object form, never canonicalize the number.\n"
            "    return Value(value.is_none, value.canon, value.key, True)\n"
        ),
        "refinement": (
            "A real patch of this shape wraps without parsing: `return "
            "uuid.UUID(int=0) if value is None else value` produces the right TYPE "
            "only when the value already had it, and for a stored str it either "
            "raises or keeps the str. Delivering the form without the number leaves "
            "the join comparing a different 128-bit value, so the F2P still FAILS. "
            "Must reject."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P3: Result().key == value.key is not "
            "provably == value.canon for a non-empty value. It also breaks P7 on the "
            "empty branch (it claims the canonical form for an empty value). Must "
            "reject."
        ),
    },

    # --- SUPPORTING near-miss: invent a wrong canonical key ----------------
    # Cheap supporting case: builds a result with a fabricated key (a constant 0)
    # for non-empty values. Fails P3 unless canon happens to be 0. Carries a real
    # refinement so it is not corruption-only.
    {
        "id": "support-fabricated-zero-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # supporting near-miss: fabricate a constant join key (0). Faithful\n"
            "    # on is_none/canon and in the canonical form, but the number is\n"
            "    # invented, not canonical.\n"
            "    result = Value(value.is_none, value.canon, 0, True)  # type: Value\n"
            "    return result\n"
        ),
        "refinement": (
            "Hard-coding the prepared join key to a constant cannot match the "
            "related object's uuid.UUID pk except for the int=0 UUID; a real patch "
            "doing this would break the prefetch join for every real pk and would "
            "not resolve the F2P. Supporting near-miss with a genuine refinement."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P3: Result().key == 0 is not provably "
            "== value.canon for an arbitrary non-empty value. Must reject."
        ),
    },

    # --- SUPPORTING near-miss: the two numeric facets swapped --------------
    # Argument-order confusion in the carrier construction: the canonical
    # identity and the as-stored key change places. Catches a spec that pinned
    # the facets only up to permutation.
    {
        "id": "support-swap-canon-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # supporting near-miss: swap the canonical identity and the stored\n"
            "    # key when building the result.\n"
            "    return Value(value.is_none, value.key, value.canon, True)\n"
        ),
        "refinement": (
            "A real patch of this shape reports the stored raw value as the record's "
            "identity while keying by the parsed one; the holder side and the target "
            "side then disagree about which number identifies the row, so the "
            "prefetch join is no more correct than before and the F2P still FAILS. "
            "Supporting near-miss."
        ),
        "rationale": (
            "REJECTION SOURCE = postcondition P2: Result().canon == value.canon "
            "fails, since the result's canon facet is value.key. Must reject."
        ),
    },

    # --- DIVERGENCE: never deliver the prepared key ------------------------
    # Computes the CORRECT result and then loops forever before returning it.
    # Under partial-correctness semantics every Ensures clause holds vacuously,
    # so this verifies against any spec without a termination obligation. It must
    # be rejected by prepare_key's method-level MustTerminate(14): loop
    # invariants alone do not reject it.
    {
        "id": "divergence-nonterminating-body",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # divergence: prepare the key correctly, then never hand it back.\n"
            "    coerced = base_prepare(value)  # type: Value\n"
            "    out = canonicalize(coerced)  # type: Value\n"
            "    n = 0  # type: int\n"
            "    while n >= 0:\n"
            "        Invariant(n >= 0)\n"
            "        Invariant(Acc(out.is_none) and Acc(out.canon) and "
            "Acc(out.key) and Acc(out.is_canon_form))\n"
            "        n = n + 1\n"
            "    return out\n"
        ),
        "refinement": (
            "A real patch that never returns delivers no join key at all: the "
            "prefetch call hangs and test_prefetch_GFK_uuid_pk cannot pass (the "
            "harness records a timeout, not a resolution). The postconditions say "
            "nothing about it under partial correctness, which is why the obligation "
            "is stated at the method level rather than left to the loop."
        ),
        "rationale": (
            "REJECTION SOURCE = the termination obligation: 'Obligation leak check "
            "failed. Loop might not take all unsatisfied obligations from the "
            "context.' prepare_key carries Requires(MustTerminate(14)); the loop "
            "cannot discharge it, so the body is rejected even though every value "
            "clause holds vacuously. The loop guard n >= 0 over unbounded ints is "
            "not statically dead, so this is a genuine rejection and not a "
            "translation error. Must reject."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — both @ContractOnly callees are A-consumed; re-run the REAL
# callees (Field.get_prep_value / UUIDField.to_python) in the instance image.
# apply_gold=True: the axioms describe the post-gold UUIDField.to_python /
# inherited Field.get_prep_value (both are unchanged by the gold patch, so the
# behaviour is identical pre/post — apply_gold is harmless here).
#
# We embed the bundle's own axiom_check.py source (read on the HOST at load time)
# into a self-contained probe, since the runner mounts ONLY the probe at /work
# (model.py / axiom_check.py are NOT in-container).
# ---------------------------------------------------------------------------

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


# axiom-soundness probe: run the REAL callees over boundary + fuzz and assert the
# axioms' Ensures + the join-key match (the bundle's own validated logic).
_SOUNDNESS_PROBE = (
    "import sys\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "ns = {'__name__': '__axiom_check__'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), ns)\n"
    "rc = ns['main']()\n"
    "print('axiom-soundness probe rc =', rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)


# axiom-containment probe: enumerate EXACTLY the callee-inputs the MODEL can
# reach and assert each lies in the axiom's Requires domain. The model's Requires
# on prepare_key is Acc(value.is_none,1/2) & Acc(value.canon,1/2) & Acc(value.key,1/2)
# & Acc(value.is_canon_form,1/2) — i.e. ANY Value (None / canonical uuid.UUID /
# textual str form / int form), with NO well-formedness constraint tying the form
# flag to the key. base_prepare and canonicalize have the SAME Requires (fractional
# perm on the four facets), so the only domain obligation is: every value
# get_prep_value can receive in the prefetch path (uuid.UUID / 32-hex str /
# hyphenated str / int / None) is accepted by BOTH real callees WITHOUT raising. We
# confirm the real callees accept exactly that reachable set (no ValidationError on
# the well-formed stored representation the prefetch join feeds) AND that each
# non-empty output is in the canonical object form, which is the form half of the
# canonicalize axiom. A reachable input that the callee rejects (or that lands
# outside the axiom's no-raise domain) would be AXIOM-TOO-WEAK-FOR-CALLER.
_CONTAINMENT_PROBE = (
    "import sys, uuid\n"
    "def _cfg():\n"
    "    import django\n"
    "    from django.conf import settings\n"
    "    if not settings.configured:\n"
    "        settings.configure(\n"
    "            INSTALLED_APPS=['django.contrib.contenttypes','django.contrib.auth'],\n"
    "            DATABASES={'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},\n"
    "        )\n"
    "    django.setup()\n"
    "try:\n"
    "    _cfg()\n"
    "except Exception as exc:\n"
    "    print('CONTAINMENT SKIP: Django not configurable: %r' % (exc,)); sys.exit(0)\n"
    "from django.db import models\n"
    "field = models.UUIDField()\n"
    "base = models.Field()\n"
    "u = uuid.UUID(int=0x1a8e4c5b2d3f4061a2b3c4d5e6f70819)\n"
    "# EXACTLY the inputs the model/caller can reach in the prefetch path:\n"
    "reachable = [None, u, u.hex, str(u), u.int]\n"
    "labels = ['None','uuid','hex32','hyphen','int']\n"
    "for lab, v in zip(labels, reachable):\n"
    "    # base_prepare domain: Field.get_prep_value must accept (no raise) ->\n"
    "    coerced = base.get_prep_value(v)\n"
    "    # canonicalize domain: UUIDField.to_python must accept the coerced value\n"
    "    # WITHOUT raising ValidationError (the no-raise sub-domain the axiom covers).\n"
    "    out = field.to_python(coerced)\n"
    "    if v is None:\n"
    "        assert out is None, 'None reachable input not preserved: %r' % (out,)\n"
    "    else:\n"
    "        assert isinstance(out, uuid.UUID), (\n"
    "            'reachable input %s=%r outside no-raise canonical domain: to_python -> %r'\n"
    "            % (lab, v, out))\n"
    "        assert out == uuid.UUID(int=u.int), (\n"
    "            'reachable input %s=%r canonicalized to a different identity: %r'\n"
    "            % (lab, v, out))\n"
    "    print('reachable %-7s -> in axiom domain (no raise), out=%r' % (lab, out))\n"
    "print('axiom-containment OK: every caller-reachable get_prep_value input lies '\n"
    "      'in both axioms no-raise Requires domain, and every non-empty one comes '\n"
    "      'back in the canonical object form')\n"
    "sys.exit(0)\n"
)


AXIOM_TESTS = [
    {
        "id": "ax-sound-callees",
        "axiom": "base_prepare+canonicalize",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": (
            "Runs the REAL Field.get_prep_value + UUIDField.to_python over boundary "
            "(int=0, int=2^128-1, int=1, uuid4, uuid1) + 5000 fuzz UUIDs in every "
            "storage form (uuid/hex32/hyphen/int) + None, asserting base_prepare's "
            "identity-on-facets Ensures (including the FORM facet) and canonicalize's "
            "canonical-form + canonical-key Ensures (Result().is_canon_form and "
            "Result().key == value.canon for non-empty; passthrough for None), plus "
            "the decisive join-key match (stored str form == uuid pk form) and the "
            "demonstration that a same-numbered key outside the canonical object form "
            "resolves against nothing (hash equal, == unequal, dict miss). Any "
            "disagreement => AXIOM-UNSOUND. This is the bundle's own G-AX logic."
        ),
    },
    {
        "id": "ax-cover-reachable-domain",
        "axiom": "base_prepare+canonicalize",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": (
            "Enumerates EXACTLY the inputs the model/caller can reach in the prefetch "
            "path (None / uuid.UUID / 32-hex str / hyphenated str / int) and asserts "
            "each lies inside BOTH axioms' Requires no-raise domain: Field.get_prep_value "
            "accepts it and UUIDField.to_python canonicalizes it WITHOUT raising "
            "ValidationError, into the canonical object form with the same identity. "
            "The axiom deliberately omits the raise path (malformed input), which the "
            "caller never reaches — covering only the reachable set is SOUND. A "
            "reachable input outside this domain would be AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
