# properties.py — PBT falsification battery for django__django-13401.
#
# NOT a Nagini module; a manifest of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT.
#
# Defended surface (read from model.py + refinement.md + mapping.md + the gold
# patch + the single F2P test_abstract_inherited_fields):
#
#   This is a MULTI-SITE change: three relational operations on a schema
#   attribute `Attr(rank:int, owned:bool, okey:PSeq[int])` are independently
#   fixed so a field's OWNER identity (not just its creation rank) participates.
#   All three postconditions pin the result to a @Pure deep reference that is
#   GROUNDED in the inputs (no opaque answer-key oracle):
#
#     * attr_eq  -> Result() == eq_ref(self_, other)
#                   = (rank== AND same_owner): both ownerless, or both own an
#                     equal (label,name) key.
#     * attr_lt  -> Result() == lt_ref(self_, other)
#                   = rank-first order; equal-rank tie-break: ownerless precedes
#                     owned, then lex_lt on the flattened identity key.
#     * attr_hash_key -> Result() == hash_ref(self_)
#                   = PSeq(rank,1)+okey when owned, else PSeq(rank,0): the KEY
#                     now carries the owner, so attributes differing in owner
#                     produce DISTINCT keys (the set de-dup the issue is about).
#
# READ-ONLY inputs (Acc(...,1/4)) on EVERY function:
#   * attr_eq/attr_lt:  self_.{rank,owned,okey} AND other.{rank,owned,okey} at 1/4
#   * attr_hash_key:    self_.{rank,owned,okey} at 1/4
#   -> FRAME-MUTATION is MANDATORY (a rival that writes a half-permission field
#      to fabricate the answer must be rejected for INSUFFICIENT PERMISSION).
#
# UNGROUNDED-ORACLE ECHO: N/A. eq_ref/lt_ref/hash_ref are @Pure helpers fully
# unfolded over the attributes' own fields (no @ContractOnly answer-key, no
# exact-marker). There is no wrong echo an impl could return without doing the
# work — echoing eq_ref/lt_ref/hash_ref IS doing the work. So instead of an
# echo-reject we add honest cheapest-impl positive controls (return the @Pure
# helper directly), which MUST verify.
#
# Region-surgery: every variant is _BASE with a single _swap INSIDE one
# # impl-start / # impl-end block, so the frozen spec (class Attr + axioms +
# pure helpers lex_lt/same_owner/eq_ref/lt_ref/hash_ref + every pre/post pair +
# the three signatures) is never touched -> same_spec is guaranteed True.

from pathlib import Path

INSTANCE = "django__django-13401"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The three gold impl blocks, verbatim, used as anchors for region surgery.
_EQ_IMPL = (
    "    return (\n"
    "        self_.rank == other.rank and\n"
    "        same_owner(self_, other)\n"
    "    )\n"
    "    # impl-end"
)
_LT_IMPL = (
    "    if (\n"
    "        self_.rank != other.rank or\n"
    "        not self_.owned and not other.owned\n"
    "    ):\n"
    "        return self_.rank < other.rank\n"
    "    elif self_.owned != other.owned:\n"
    "        return not self_.owned  # the owner-less attribute precedes\n"
    "    else:\n"
    "        return lex_lt(self_.okey, other.okey)\n"
    "    # impl-end"
)
_HASH_IMPL = (
    "    if self_.owned:\n"
    "        return PSeq(self_.rank, 1) + self_.okey\n"
    "    return PSeq(self_.rank, 0)\n"
    "    # impl-end"
)


# ---------------------------------------------------------------------------
# 1. FRAME-MUTATION (MANDATORY — every input is Acc(...,1/4) read-only)
# ---------------------------------------------------------------------------

# 1a. attr_eq: write the half-permission field `self_.rank` (a no-op identity
#     write) before returning the correct value. The gold postcondition
#     (Result()==eq_ref) is kept verbatim, so the rejection is attributable to
#     the WRITE needing full permission, not to a value mismatch.
_FM_EQ = _swap(
    _BASE,
    _EQ_IMPL,
    "    self_.rank = self_.rank\n"
    "    return (\n"
    "        self_.rank == other.rank and\n"
    "        same_owner(self_, other)\n"
    "    )\n"
    "    # impl-end",
)

# 1b. attr_lt: write the half-permission field `self_.owned` before computing
#     the correct order. Must be rejected for INSUFFICIENT PERMISSION.
_FM_LT = _swap(
    _BASE,
    _LT_IMPL,
    "    self_.owned = self_.owned\n"
    "    if (\n"
    "        self_.rank != other.rank or\n"
    "        not self_.owned and not other.owned\n"
    "    ):\n"
    "        return self_.rank < other.rank\n"
    "    elif self_.owned != other.owned:\n"
    "        return not self_.owned  # the owner-less attribute precedes\n"
    "    else:\n"
    "        return lex_lt(self_.okey, other.okey)\n"
    "    # impl-end",
)

# 1c. attr_hash_key: write the half-permission field `self_.okey` before
#     building the correct key. Must be rejected for INSUFFICIENT PERMISSION.
_FM_HASH = _swap(
    _BASE,
    _HASH_IMPL,
    "    self_.okey = self_.okey\n"
    "    if self_.owned:\n"
    "        return PSeq(self_.rank, 1) + self_.okey\n"
    "    return PSeq(self_.rank, 0)\n"
    "    # impl-end",
)


# ---------------------------------------------------------------------------
# 2. PARTIAL-DOMAIN (correct on most of the F2P/P2P domain, diverges on a
#    targeted sub-domain). Each rival is the cheapest WRONG behaviour a faithful
#    patch could ship that still passes the bulk of inputs.
# ---------------------------------------------------------------------------

# 2a. attr_eq: ignore the owner — equal iff ranks are equal (the PRE-PATCH bug,
#     exactly the issue). Correct on all distinct-rank pairs and on equal-rank
#     SAME-owner pairs; WRONG on equal-rank DIFFERENT-owner pairs (the F2P:
#     three abstract-inherited fields share creation_counter 0 but belong to
#     different models). A real patch that kept rank-only equality is the
#     pre-fix code: the F2P assertNotEqual(abstract, inherit1) FAILS.
_PD_EQ_RANKONLY = _swap(
    _BASE,
    _EQ_IMPL,
    "    return self_.rank == other.rank\n"
    "    # impl-end",
)

# 2b. attr_eq: require BOTH same rank and a literal owner-key equality even when
#     both are ownerless (drops the `not a.owned` short-circuit). Two ownerless
#     fields with empty okey still compare equal here (okey==okey), but two
#     ownerless fields whose okey sequences DIFFER would wrongly compare unequal.
#     In the model a bare/ownerless field's okey is unconstrained, so the spec
#     must reject pinning equality to okey-agreement for ownerless attributes:
#     eq_ref says ownerless attributes are equal regardless of okey. A faithful
#     patch comparing getattr(model,None) would treat two ownerless fields as
#     equal (None==None) irrespective of any residual key; this rival diverges
#     on ownerless pairs with mismatched residual keys and would not resolve the
#     P2P backward-compat ordering of bare fields.
_PD_EQ_OWNERLESS = _swap(
    _BASE,
    _EQ_IMPL,
    "    return self_.rank == other.rank and self_.okey == other.okey\n"
    "    # impl-end",
)

# 2c. attr_lt: drop the owner tie-break — order by rank only (the PRE-PATCH bug
#     for __lt__). Correct on every distinct-rank pair and on equal-rank
#     ownerless pairs; WRONG on equal-rank owned pairs (returns False both ways,
#     no strict order). The F2P asserts assertLess(abstract, inherit1) with all
#     three at creation_counter 0; rank-only __lt__ returns False, so
#     assertLess FAILS -> a faithful rank-only patch does NOT resolve.
_PD_LT_RANKONLY = _swap(
    _BASE,
    _LT_IMPL,
    "    return self_.rank < other.rank\n"
    "    # impl-end",
)

# 2d. attr_lt: keep the rank-first branch and the owner-presence tie-break but
#     ORDER OWNED-BEFORE-OWNERLESS (flip `not self_.owned` to `self_.owned`).
#     Correct on distinct ranks and on equal-rank both-owned pairs; WRONG on the
#     equal-rank ownerless-vs-owned sub-domain. The gold orders ownerless first
#     ("Order no-model fields first" — required for backward compat). A patch
#     ordering owned-first would invert that boundary case; the P2P
#     test_field_ordering and the gold tie-break direction would diverge.
_PD_LT_FLIP_PRESENCE = _swap(
    _BASE,
    _LT_IMPL,
    "    if (\n"
    "        self_.rank != other.rank or\n"
    "        not self_.owned and not other.owned\n"
    "    ):\n"
    "        return self_.rank < other.rank\n"
    "    elif self_.owned != other.owned:\n"
    "        return self_.owned  # WRONG: owner-bearing attribute precedes\n"
    "    else:\n"
    "        return lex_lt(self_.okey, other.okey)\n"
    "    # impl-end",
)

# 2e. attr_hash_key: drop the owner from the key — return PSeq(rank, 0) always
#     (collapse the ownership flag). Correct for ownerless attributes; WRONG for
#     owned attributes (loses the owner identity entirely). This is the
#     pre-patch hash bug: two equal-rank fields with different owners hash to the
#     same key and collapse in a set, so the F2P
#     assertNotEqual(hash(abstract), hash(inherit1)) FAILS.
_PD_HASH_DROP_OWNER = _swap(
    _BASE,
    _HASH_IMPL,
    "    empty = PSeq(self_.rank, 0)  # type: PSeq[int]\n"
    "    return empty\n"
    "    # impl-end",
)

# 2f. attr_hash_key: build the owner-aware key but use the SAME tag byte (1) for
#     owned AND ownerless, and append okey unconditionally. For owned attributes
#     this matches hash_ref's owned branch; for OWNERLESS attributes hash_ref is
#     PSeq(rank,0) but this rival returns PSeq(rank,1)+okey. The flag byte and a
#     residual okey differ, so the ownerless sub-domain diverges; a patch whose
#     ownerless key spuriously carried the owner-present tag and a residual key
#     would not reproduce the gold key tuple (creation_counter, None, None).
_PD_HASH_BADTAG = _swap(
    _BASE,
    _HASH_IMPL,
    "    return PSeq(self_.rank, 1) + self_.okey\n"
    "    # impl-end",
)


# ---------------------------------------------------------------------------
# 3. UNGROUNDED-ORACLE ECHO — N/A (postconditions are grounded). See header.
#    We add a value-level "double-mask" style attack on the hash KEY instead:
#    a key that AGREES with hash_ref under the abstraction's typical inputs but
#    drops a discriminating component on a sub-domain. Covered by 2e/2f, which
#    are the genuine ways the de-dup property fails. No additional case.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 4. CONTROL-FLOW-EFFECT — N/A (see assessment). All three functions are pure
#    value-returning queries with no raise path, no side effect, and outputs
#    fully pinned to a deep reference; there is no raise/return/effect channel
#    invisible to the value abstraction, so no capability-token case applies.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 5. POSITIVE CONTROLS (soundness — structurally different but CORRECT impls
#    that MUST verify; else SPEC-TOO-STRONG). These keep the spec untouched and
#    only reshape the executable form (reordered branches / typed-local reads /
#    direct @Pure-helper return). The @Pure helpers are grounded in the inputs,
#    so a direct return is a faithful cheapest-impl, NOT an ungrounded echo.
# ---------------------------------------------------------------------------

# 5a. attr_eq: return the grounded @Pure reference directly (cheapest faithful
#     impl). eq_ref IS the work (rank== AND same_owner), fully unfolded over the
#     args' read-only fields, so this is correct and must verify.
_POS_EQ_DIRECT = _swap(
    _BASE,
    _EQ_IMPL,
    "    return eq_ref(self_, other)\n"
    "    # impl-end",
)

# 5b. attr_lt: branch-REORDERED correct impl. Handle the equal-rank owned
#     tie-break FIRST (when both owned and ranks equal), else fall back to the
#     gold rank-first / presence logic. Same decision as lt_ref on every input,
#     different executable shape; the postcond proof (Result()==lt_ref) is
#     re-established by lt_ref's own definition, no extra lemma needed.
_POS_LT_REORDER = _swap(
    _BASE,
    _LT_IMPL,
    "    if self_.rank == other.rank and self_.owned and other.owned:\n"
    "        return lex_lt(self_.okey, other.okey)\n"
    "    elif self_.rank == other.rank and self_.owned != other.owned:\n"
    "        return not self_.owned\n"
    "    else:\n"
    "        return self_.rank < other.rank\n"
    "    # impl-end",
)

# 5c. attr_hash_key: bind the key into a typed local before returning (read-only
#     respected — no write to any half-permission field). Different shape from
#     the bare returns, must verify.
_POS_HASH_LOCAL = _swap(
    _BASE,
    _HASH_IMPL,
    "    if self_.owned:\n"
    "        owned_key = PSeq(self_.rank, 1) + self_.okey  # type: PSeq[int]\n"
    "        return owned_key\n"
    "    bare_key = PSeq(self_.rank, 0)  # type: PSeq[int]\n"
    "    return bare_key\n"
    "    # impl-end",
)


# ---------------------------------------------------------------------------
# 6. ADMISSIBILITY — a self-call confirming the precondition admits a normal
#    F2P-shaped input. The F2P builds three fields sharing creation_counter 0
#    that belong to three distinct models (AbstractModel, InheritAbstractModel1,
#    InheritAbstractModel2): so equal rank, all owned, distinct (app_label,
#    model_name) keys -> not equal, ordered by model name, hashed apart. We
#    construct exactly that shape inside the attr_eq impl region, exercise all
#    three operations, and assert the F2P observable. If the precondition
#    rejected this normal input -> PRECOND-TOO-STRONG.
# ---------------------------------------------------------------------------
_ADMISS = _swap(
    _BASE,
    _EQ_IMPL,
    "    # build the F2P-shaped trio: equal rank, all owned, distinct keys\n"
    "    k1 = PSeq(1, 0, 2)  # type: PSeq[int]\n"
    "    k2 = PSeq(1, 0, 3)  # type: PSeq[int]\n"
    "    a = Attr(0, True, k1)\n"
    "    b = Attr(0, True, k2)\n"
    "    Assert(not eq_ref(a, b))            # distinct owners at equal rank\n"
    "    # unfold the front-recursive @Pure lex_lt bottom-up so the verifier can\n"
    "    # evaluate it over the PSeq literals (k1, k2 agree on the first two code\n"
    "    # points, differ at index 2: 2 < 3); needed for the lt_ref tie-break.\n"
    "    Assert(lex_lt(k1.drop(2), k2.drop(2)))  # PSeq(2) < PSeq(3): heads differ\n"
    "    Assert(lex_lt(k1.drop(1), k2.drop(1)))  # PSeq(0,2) < PSeq(0,3): recurse\n"
    "    Assert(lt_ref(a, b))                # ordered by identity key (k1 < k2)\n"
    "    Assert(hash_ref(a) != hash_ref(b))  # keys differ -> hash apart\n"
    "    # a bare ownerless field precedes an owned one at equal rank (P2P-ish)\n"
    "    empty = PSeq()  # type: PSeq[int]\n"
    "    bare = Attr(0, False, empty)\n"
    "    Assert(lt_ref(bare, a))\n"
    "    return (\n"
    "        self_.rank == other.rank and\n"
    "        same_owner(self_, other)\n"
    "    )\n"
    "    # impl-end",
)


SPEC_TESTS = [
    # --- FRAME-MUTATION (mandatory: every input is read-only at 1/4) ---
    {
        "id": "frame-mutation-attr_eq-write-rank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FM_EQ,
        "refinement": (
            "Field.__eq__ is a pure observer: it READS creation_counter and the "
            "model identity and never mutates the field. A faithful patch does not "
            "write self.creation_counter while computing equality; a rival that "
            "writes the input to fabricate the answer is not the gold __eq__ and "
            "would corrupt the live Field objects the test pulls into a set, so it "
            "would not resolve test_abstract_inherited_fields."
        ),
        "rationale": (
            "self_.rank is held at Acc(...,1/4) (read-only). The write "
            "`self_.rank = self_.rank` needs full permission and is rejected for "
            "INSUFFICIENT PERMISSION by the fractional-permission system; the value "
            "postcondition Result()==eq_ref is kept verbatim so the rejection is "
            "attributable to the write."
        ),
    },
    {
        "id": "frame-mutation-attr_lt-write-owned",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FM_LT,
        "refinement": (
            "Field.__lt__ is a pure comparator used by bisect/sorted; a faithful "
            "patch never writes hasattr(self,'model') (an attribute presence flag) "
            "while comparing. Mutating it corrupts the field's owner state, which "
            "the same test later hashes and equates, so the rival would not resolve."
        ),
        "rationale": (
            "self_.owned is held at Acc(...,1/4) (read-only). The write "
            "`self_.owned = self_.owned` needs full permission and is rejected for "
            "INSUFFICIENT PERMISSION; the value postcondition Result()==lt_ref is "
            "kept verbatim."
        ),
    },
    {
        "id": "frame-mutation-attr_hash_key-write-okey",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _FM_HASH,
        "refinement": (
            "Field.__hash__ builds a key from the field's identity and never "
            "mutates the field. A rival that writes self.model's identity key to "
            "produce the hash key is not the gold __hash__ and would corrupt the "
            "field, so it would not resolve the F2P hash-apart assertions."
        ),
        "rationale": (
            "self_.okey is held at Acc(...,1/4) (read-only). The write "
            "`self_.okey = self_.okey` needs full permission and is rejected for "
            "INSUFFICIENT PERMISSION; the value postcondition Result()==hash_ref "
            "is kept verbatim."
        ),
    },
    # --- PARTIAL-DOMAIN ---
    {
        "id": "partial-domain-attr_eq-rank-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_EQ_RANKONLY,
        "refinement": (
            "Rank-only equality is the PRE-PATCH bug the issue reports: two fields "
            "sharing creation_counter but belonging to different models compare "
            "equal and one is de-duplicated from a set. The F2P explicitly asserts "
            "assertNotEqual(abstract_model_field, inherit1_model_field) for three "
            "fields that all share creation_counter 0; rank-only __eq__ returns True "
            "-> assertNotEqual FAILS, so this faithful patch does NOT resolve."
        ),
        "rationale": (
            "The postcondition Result()==eq_ref(self_,other) is violated whenever "
            "rank== but same_owner is False (equal-rank, different-owner pair); "
            "rejection comes from the equality postcondition clause."
        ),
    },
    {
        "id": "partial-domain-attr_eq-okey-on-ownerless",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_EQ_OWNERLESS,
        "refinement": (
            "Pinning equality to okey-agreement even for ownerless attributes "
            "diverges from getattr(self,'model',None)==getattr(other,'model',None), "
            "which makes two ownerless fields equal (None==None) regardless of any "
            "residual identity bytes. A patch that compared a residual owner key for "
            "model-less fields would wrongly distinguish bare fields and break the "
            "backward-compat equality of ownerless fields exercised by P2P "
            "test_field_ordering, so it would not resolve."
        ),
        "rationale": (
            "eq_ref's same_owner short-circuits `not a.owned` to True for ownerless "
            "pairs; this rival instead requires okey==okey, so for an ownerless pair "
            "with differing residual okey it returns False while eq_ref returns True "
            "-> Result()==eq_ref is violated on the ownerless sub-domain."
        ),
    },
    {
        "id": "partial-domain-attr_lt-rank-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_LT_RANKONLY,
        "refinement": (
            "Rank-only ordering is the PRE-PATCH __lt__: at equal creation_counter "
            "it returns False both ways, giving no strict order between the "
            "abstract-inherited fields. The F2P asserts assertLess(abstract, "
            "inherit1) with all three at creation_counter 0; rank-only __lt__ "
            "returns False -> assertLess FAILS, so this faithful patch does NOT "
            "resolve."
        ),
        "rationale": (
            "The postcondition Result()==lt_ref is violated on equal-rank owned "
            "pairs where lt_ref uses the tie-break (returns True for the "
            "smaller-key one) but the rival returns rank<rank == False; rejection "
            "comes from the order postcondition clause."
        ),
    },
    {
        "id": "partial-domain-attr_lt-flip-presence",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_LT_FLIP_PRESENCE,
        "refinement": (
            "The gold __lt__ orders no-model (ownerless) fields FIRST among "
            "equal-rank fields ('Order no-model fields first' — required so the "
            "backward-compat creation-order is preserved). Flipping the tie-break "
            "to order owned-first inverts that boundary; a patch that ordered "
            "model-bearing fields ahead of bare ones at equal rank would re-order "
            "the very cases the issue warns must NOT be re-ordered, breaking the "
            "P2P sort order, so it would not resolve."
        ),
        "rationale": (
            "On an equal-rank pair where exactly one is owned, lt_ref returns "
            "`not self_.owned` but the rival returns `self_.owned`; these disagree "
            "(one is the negation of the other), so Result()==lt_ref is violated."
        ),
    },
    {
        "id": "partial-domain-attr_hash_key-drop-owner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_HASH_DROP_OWNER,
        "refinement": (
            "Dropping the owner from the hash key is the PRE-PATCH __hash__ "
            "(hash(self.creation_counter)). Two equal-rank fields with different "
            "owners then hash to the same key and collapse in a set — exactly the "
            "de-dup the issue reports. The F2P asserts "
            "assertNotEqual(hash(abstract), hash(inherit1)); a key dropping the "
            "owner makes the hashes equal -> assertNotEqual FAILS, so this faithful "
            "patch does NOT resolve."
        ),
        "rationale": (
            "The postcondition Result()==hash_ref is violated for owned attributes "
            "(hash_ref returns PSeq(rank,1)+okey but the rival returns PSeq(rank,0)); "
            "rejection comes from the hash-key postcondition clause."
        ),
    },
    {
        "id": "partial-domain-attr_hash_key-bad-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _PD_HASH_BADTAG,
        "refinement": (
            "Tagging EVERY field with the owner-present byte (1) and appending okey "
            "unconditionally diverges from the gold key for ownerless fields, whose "
            "gold tuple is (creation_counter, None, None). A patch whose ownerless "
            "key carried a spurious owner tag plus residual identity bytes would "
            "give a bare field a key indistinguishable in shape from an owned one, "
            "mis-grouping bare fields in a hashed collection, so it would not "
            "resolve the backward-compat hashing the P2P preserves."
        ),
        "rationale": (
            "For an ownerless attribute hash_ref returns PSeq(rank,0) but the rival "
            "returns PSeq(rank,1)+okey; the second element (0 vs 1) and the trailing "
            "okey differ, so Result()==hash_ref is violated on the ownerless "
            "sub-domain."
        ),
    },
    # --- POSITIVE CONTROLS (must verify; else SPEC-TOO-STRONG) ---
    {
        "id": "positive-attr_eq-direct-ref",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EQ_DIRECT,
        "rationale": (
            "Returns the grounded @Pure reference eq_ref(self_,other) directly. "
            "eq_ref is fully unfolded over the args' read-only fields (rank== AND "
            "same_owner), so this is the cheapest FAITHFUL impl (not an ungrounded "
            "echo). A correct impl must verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "positive-attr_lt-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LT_REORDER,
        "rationale": (
            "Branch-reordered correct comparator: handles the equal-rank both-owned "
            "tie-break first, then the presence tie-break, else rank-first. Same "
            "decision as lt_ref on every input; the postcond is re-established by "
            "lt_ref's own definition (no extra lemma). A structurally-different "
            "correct impl must verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "positive-attr_hash_key-typed-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_HASH_LOCAL,
        "rationale": (
            "Binds each key into a typed local before returning (read-only "
            "respected — no write to any half-permission field). Same values as the "
            "gold returns, different shape. Must verify (else SPEC-TOO-STRONG)."
        ),
    },
    # --- ADMISSIBILITY (must verify; else PRECOND-TOO-STRONG) ---
    {
        "id": "admissibility-f2p-shaped-trio",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "Builds the F2P-shaped trio (equal rank, all owned, distinct identity "
            "keys, plus a bare ownerless field) and asserts the F2P observable via "
            "the deep references: not equal, ordered by identity key, hashed apart, "
            "and bare-before-owned at equal rank. The preconditions must admit this "
            "normal input (else PRECOND-TOO-STRONG)."
        ),
    },
]

# No @ContractOnly axioms (meta.json axioms == []). eq_ref/same_owner, lt_ref/
# lex_lt and hash_ref are A-reference deep models validated executably against
# native getattr-equality / tuple-order / builtin-hash by axiom_check.py (G-AX),
# NOT consumed contracts. The axiom lane is therefore vacuous here.
AXIOM_TESTS = []
