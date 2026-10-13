# properties.py — PBT falsification battery for django__django-15315.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant whose ONLY edit is inside the
# `# impl-start`/`# impl-end` region (region-surgery => same_spec guaranteed);
# each is checked by Nagini verify + markers.same_spec against the frozen spec.
# AXIOM_TESTS probe the real builtin `hash` callee in the instance image.
#
# DEFENDED SURFACE (reasoned, not corrupted):
#   located_value(self: Descriptor) -> int
#     Requires/Ensures: Acc(self.{order,has_owner}, 1/2) unconditionally;
#                       Acc(self.{owner_label,owner_name}, 1/2) ONLY under
#                       Implies(self.has_owner, ...) -- the owner-derived
#                       attributes EXIST only once attached (the real repo's
#                       `self.model` is absent before contribute_to_class and
#                       reading it raises AttributeError), so an impl may read
#                       them only after establishing attachment.
#     Requires(MustTerminate(2)) -- total correctness: the bounded straight-line
#                       delegation must terminate; forbids diverging rivals that
#                       satisfy every value postcondition vacuously. (The
#                       Descriptor constructor carries MustTerminate(1) so a
#                       caller under obligation may construct descriptors.)
#     load-bearing postcondition:  Ensures(Result() == hash_int(self.order))
#       => the located-value is a function of the creation-order identity ALONE,
#          independent of the attachment flag and both owner-derived attributes.
#   axiom hash_int : @Pure @ContractOnly, NO Ensures; proof consumes only that
#       it is a deterministic function of its single int argument.
#
# The gold patch replaces `hash((creation_counter, app_label_or_None,
# model_name_or_None))` with `hash(self.creation_counter)`. F2P
# `test_hash_immutability` hashes an UNattached IntegerField, then attaches it
# to a model and re-hashes, asserting EQUALITY. Any impl whose located-value
# depends on the attachment flag or owner attributes breaks that test.
from pathlib import Path

INSTANCE = "django__django-15315"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen impl region body (exactly the gold return, indented 4 spaces).
_GOLD_IMPL = "    return hash_int(self.order)"
assert _BASE.count(_GOLD_IMPL) == 1, "drift: gold impl body not found uniquely"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body):
    """Return a full model.py whose impl region body is replaced by new_body.
    Edits ONLY between # impl-start / # impl-end, so same_spec holds."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


SPEC_TESTS = [
    # ----------------------------------------------------------------- 1. FRAME-MUTATION (MANDATORY)
    # All four fields are Acc(...,1/2) read-only. A rival that WRITES self.order
    # (here, a self-assignment that is still a write) to "establish" the result
    # cannot type-check: a 1/2 permission does not admit a field store. The spec
    # must reject this for INSUFFICIENT PERMISSION, not for a value mismatch.
    # Refinement: the faithful real patch corresponding to "Field.__hash__
    # mutates self.creation_counter" is not the gold body (gold is a pure
    # `return hash(self.creation_counter)`); a __hash__ that rebinds
    # creation_counter would corrupt the field's identity/ordering and is a
    # different program that would not match the gold and would break the
    # creation_counter-ordering P2P tests (test_field_ordering etc.).
    {
        "id": "frame-mutate-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    self.order = self.order  # WRITE under only Acc(self.order,1/2)\n"
            "    return hash_int(self.order)"
        ),
        "refinement": "A __hash__ that writes self.creation_counter is not the "
                      "gold pure-read body; rebinding creation_counter would "
                      "change field identity/ordering and break the "
                      "creation_counter-based ordering P2P tests, so its "
                      "faithful real patch does not resolve.",
        "rationale": "MUST reject for insufficient permission: located_value "
                     "holds only Acc(self.order,1/2), which forbids any store. "
                     "Rejection comes from the permission system, not the "
                     "postcondition.",
    },
    # Second frame-mutation: write an owner field (also Acc(...,1/2)) to try to
    # make the located-value owner-independent by zeroing the owner attribute.
    {
        "id": "frame-mutate-owner-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    self.owner_label = self.order  # WRITE under Acc(self.owner_label,1/2)\n"
            "    return hash_int(self.order)"
        ),
        "refinement": "Mutating an owner-derived attribute inside __hash__ has "
                      "no gold counterpart (gold reads nothing but "
                      "creation_counter); a __hash__ with side effects on "
                      "_meta-derived state is a different, test-breaking program.",
        "rationale": "MUST reject for insufficient permission on "
                     "self.owner_label (held at most at 1/2, and only under "
                     "has_owner). Permission system, not value mismatch.",
    },

    # ----------------------------------------------------------------- 2. UNGROUNDED-ORACLE / WRONG-ARGUMENT
    # The oracle hash_int(self.order) is GROUNDED in the input arg; there is no
    # value-free "answer-key" to echo, so the classic echo attack does not
    # apply (stated in 'assessment'). The meaningful adversarial move is to call
    # the SAME oracle on the WRONG argument: hash_int(self.owner_label). Because
    # hash_int is @ContractOnly with no Ensures, the verifier cannot prove
    # hash_int(owner_label) == hash_int(order) for arbitrary distinct args, so
    # the postcondition Result()==hash_int(self.order) is unprovable => reject.
    # Refinement: hashing app_label instead of creation_counter is exactly the
    # owner-dependence the issue removes; the field's hash would change when it
    # gains/loses an owner => breaks test_hash_immutability.
    {
        "id": "wrong-arg-owner-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return hash_int(self.owner_label)"),
        "refinement": "Returning hash of an owner-derived attribute makes the "
                      "field hash depend on _meta state, which changes across "
                      "attachment => fails F2P test_hash_immutability; not the "
                      "gold body.",
        "rationale": "Rejection: the UNCONDITIONAL read of self.owner_label "
                     "lacks permission (owner attrs are readable only under "
                     "Implies(self.has_owner, ...) -- they do not exist "
                     "unattached, mirroring the real AttributeError); and even "
                     "guarded it could not discharge "
                     "Result()==hash_int(self.order) since hash_int is opaque.",
    },
    # Wrong-argument variant: hash of order+owner_label (the prepatch shape, but
    # unconditional). Folds owner state into the located value.
    {
        "id": "wrong-arg-order-plus-owner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return hash_int(self.order + self.owner_label)"),
        "refinement": "hash(creation_counter + app_label) is the pre-fix style "
                      "owner-folding hash; the located value moves when "
                      "owner_label becomes available => fails "
                      "test_hash_immutability; not the gold body.",
        "rationale": "Rejection: unconditional self.owner_label read lacks "
                     "permission (readable only under has_owner); and the "
                     "owner-folded value could not discharge "
                     "Result()==hash_int(self.order) anyway (hash_int opaque).",
    },

    # ----------------------------------------------------------------- 3. PARTIAL-DOMAIN
    # Correct on the UNATTACHED sub-domain (has_owner False), wrong once
    # attached: folds owner attributes in on the has_owner branch. This is the
    # exact prepatch bug. The F2P test hashes BEFORE attach (has_owner False ->
    # correct) and AFTER attach (has_owner True -> owner-folded), then asserts
    # equality. A faithful real patch with this branch keeps the
    # owner-dependence and FAILS test_hash_immutability.
    {
        "id": "partial-domain-attached",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if self.has_owner:\n"
            "        return hash_int(self.order + self.owner_label + self.owner_name)\n"
            "    return hash_int(self.order)"
        ),
        "refinement": "This is the pre-fix tuple-hash behaviour (owner-derived "
                      "terms folded in once attached). test_hash_immutability "
                      "attaches the field then re-hashes; the attached hash "
                      "differs from the unattached hash => test FAILS. Faithful "
                      "real patch does not resolve.",
        "rationale": "Rejection from Result()==hash_int(self.order) on the "
                     "has_owner branch (verifier: assertion might not hold), "
                     "mirroring model_prepatch.py:77.",
    },
    # Partial-domain on a specific order value (diverge only when order==0).
    {
        "id": "partial-domain-order-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if self.order == 0:\n"
            "        return hash_int(self.owner_name)\n"
            "    return hash_int(self.order)"
        ),
        "refinement": "Diverges from the order-only hash on a single creation "
                      "order; a real __hash__ that special-cases one "
                      "creation_counter and hashes an owner attribute there "
                      "would make that field's hash attachment-dependent and "
                      "break test_hash_immutability for that field.",
        "rationale": "Rejection: reading self.owner_name without first "
                     "establishing self.has_owner lacks permission (owner "
                     "attrs exist only when attached); and on the order==0 "
                     "branch hash_int(owner_name) is not provably equal to "
                     "hash_int(0) either.",
    },

    # ----------------------------------------------------------------- 4. UNGUARDED OWNER-ATTRIBUTE READ (the G-EQ attack class)
    # The audited attack (atk_1: `_shadow = self.model._meta.app_label` before
    # `return hash(self.creation_counter)`) returned the RIGHT value but read
    # an owner attribute UNCONDITIONALLY. In the real program an unattached
    # field has no `model` attribute, so that read raises AttributeError and
    # the F2P test_hash_immutability ERRORs (verified: eval log shows
    # AttributeError: 'IntegerField' object has no attribute 'model').
    # The spec now grants owner-attribute permission only under
    # Implies(self.has_owner, ...), so the unconditional read MUST be rejected
    # for insufficient permission even though the returned value is correct.
    {
        "id": "unguarded-owner-read-shadow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    _shadow = self.owner_label  # type: int  # UNCONDITIONAL owner read\n"
            "    return hash_int(self.order)"
        ),
        "refinement": "Faithful real patch: `_shadow = self.model._meta."
                      "app_label` then `return hash(self.creation_counter)` -- "
                      "verified NON-resolving (F2P test_hash_immutability "
                      "errors with AttributeError on the unattached field).",
        "rationale": "MUST reject for insufficient permission on "
                     "self.owner_label: permission is conditional on "
                     "self.has_owner, which this body never establishes. This "
                     "is exactly the audited G-EQ attack shape.",
    },
    # Guarded-read positive control: reading owner attrs UNDER the attachment
    # guard and still returning the order-only hash is harmless in the real
    # program (hasattr-guarded read; its faithful patch resolves -- verified
    # in eval logs) so the spec MUST admit it; else SPEC-TOO-STRONG.
    {
        "id": "pos-control-guarded-owner-read",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if self.has_owner:\n"
            "        _x = self.owner_label  # type: int\n"
            "        _y = self.owner_name  # type: int\n"
            "    return hash_int(self.order)"
        ),
        "rationale": "Reading owner attributes only under the attachment flag "
                     "is permitted (Implies grants the permission there) and "
                     "the order-only return still discharges the "
                     "postcondition; its faithful real patch (hasattr-guarded "
                     "reads + hash(creation_counter)) resolves, so the spec "
                     "must verify it (else SPEC-TOO-STRONG).",
    },

    # ----------------------------------------------------------------- 4b. DIVERGENCE (total correctness)
    # A non-terminating rival: an infinite loop in place of the return. Under
    # partial correctness this would VERIFY (every value postcondition holds
    # vacuously on the unreachable exit), yet its faithful real patch — a
    # __hash__ that never returns — hangs every hash-container lookup and the
    # F2P test, so it does NOT resolve. Requires(MustTerminate(1)) makes the
    # verifier demand a termination measure the bare loop cannot supply.
    {
        "id": "diverge-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # Divergence: never return; value postconditions hold vacuously.\n"
            "    while True:\n"
            "        pass"
        ),
        "refinement": "A located-value operation that never returns hangs every "
                      "hash-based lookup (and the F2P test) forever; a "
                      "non-returning real patch does not resolve.",
        "rationale": "MUST reject: the precondition carries MustTerminate(2), "
                     "so every loop needs a decreasing termination measure; "
                     "the bare infinite loop supplies none. If it VERIFIES => "
                     "SPEC-TOO-WEAK (divergence unconstrained).",
    },

    # ----------------------------------------------------------------- 5. POSITIVE CONTROL (soundness)
    # Structurally DIFFERENT but CORRECT: bind the hashed value to a typed local
    # first, then return it. No framing/loop obligations exist here (single pure
    # return), so this keeps the whole gold proof and MUST verify. If it cannot,
    # SPEC-TOO-STRONG.
    {
        "id": "pos-control-local-bind",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    v = hash_int(self.order)  # type: int\n"
            "    return v"
        ),
        "rationale": "A correct order-only impl in a different syntactic shape "
                     "(local-variable reshape) must verify; else SPEC-TOO-STRONG.",
    },
    # Second positive control: branch-reorder that returns the SAME value on
    # both branches (independent of has_owner). Correct (order-only) and a
    # different control shape; both branches discharge Result()==hash_int(order).
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if self.has_owner:\n"
            "        return hash_int(self.order)\n"
            "    else:\n"
            "        return hash_int(self.order)"
        ),
        "rationale": "An order-only impl with an explicit (vacuous) has_owner "
                     "branch is still correct on both branches; must verify "
                     "(else SPEC-TOO-STRONG).",
    },

    # ----------------------------------------------------------------- 6. ADMISSIBILITY
    # The precondition (permissions on the touched fields, conditional on
    # attachment for the owner-derived ones, plus MustTerminate(2)) must admit
    # a normal F2P-shaped input: an unattached descriptor (has_owner False) and
    # an attached one are both in-domain, and stability across attachment is
    # provable from the postcondition. A same-measure self-call would violate
    # the termination measure, so admissibility is shown by constructing both
    # F2P shapes, asserting the reads the spec admits, and proving the
    # located-value the postcondition pins is attachment-independent via the
    # shared pure oracle (hash_int(order) mentions neither has_owner nor the
    # owner attributes). If this fails => PRECOND-TOO-STRONG.
    {
        "id": "admiss-call-and-stability",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    # admissibility: both F2P shapes (unattached / attached) satisfy\n"
            "    # the Requires footprint; the order-only value is stable across\n"
            "    # attachment (the property test_hash_immutability checks)\n"
            "    unattached = Descriptor(7, False, 0, 0)\n"
            "    Assert(unattached.order == 7)          # read admitted\n"
            "    Assert(not unattached.has_owner)       # read admitted\n"
            "    attached = Descriptor(7, True, 101, 202)\n"
            "    Assert(attached.has_owner)             # read admitted\n"
            "    Assert(attached.owner_label == 101)    # owner read under attachment\n"
            "    # order-only oracle => stable under attachment:\n"
            "    Assert(hash_int(unattached.order) == hash_int(attached.order))\n"
            "    return hash_int(self.order)"
        ),
        "rationale": "The Requires (conditional Acc 1/2 footprint + "
                     "MustTerminate(2)) is establishable for fresh Descriptors "
                     "of both F2P shapes; owner reads are admitted once "
                     "attached; and hash_int(order) is provably equal for equal "
                     "orders regardless of attachment, which IS the stability "
                     "property. If this fails, PRECOND-TOO-STRONG.",
    },
]

# ----------------------------------------------------------------- AXIOM lane
# Single A-consumed @ContractOnly axiom: hash_int (the builtin `hash` on one
# int). The proof consumes ONLY determinism. axiom_check.py is the bundle's
# ground-truth oracle; we read it on the HOST and embed it (the runner mounts
# ONLY the probe at /work). Probes import stdlib only, print a diagnostic, and
# sys.exit(0) iff the obligation holds.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

# axiom-soundness probe: execute the REAL builtin `hash` on int boundaries +
# fuzz and assert determinism (the only Ensures-free property the proof needs).
# Reuses the bundle's check_hash_int_deterministic logic by embedding the
# oracle source and calling it directly.
_SOUND_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "# --- embedded bundle oracle (axiom_check.py) -----------------------------\n"
    + _AXIOM_CHECK_SRC.replace(
        'if __name__ == "__main__":\n    sys.exit(main())',
        '# (driver replaced below)\n',
    )
    + "\n"
    "# --- axiom-soundness driver ---------------------------------------------\n"
    "def _drive():\n"
    "    # determinism of the real callee on int boundaries + sentinels + fuzz\n"
    "    import random\n"
    "    bnd = [0,1,-1,2,-2,7,42,2**31,2**31-1,-(2**31),2**63,2**63-1,-(2**63),\n"
    "           2**64,-(2**64),10**18,-(10**18)]\n"
    "    for v in bnd:\n"
    "        check_hash_int_deterministic(v)\n"
    "    rng = random.Random(15315)\n"
    "    for _ in range(20000):\n"
    "        check_hash_int_deterministic(rng.randint(-(10**12), 10**12))\n"
    "    # the only thing the model passes to hash_int is self.order (an int):\n"
    "    # confirm determinism holds across two independent processes-equivalent\n"
    "    # repeated calls for the same int (function-of-its-argument).\n"
    "    for v in bnd:\n"
    "        assert hash(v) == hash(v), 'hash_int non-deterministic for %r' % v\n"
    "    print('AXIOM-SOUND: hash_int deterministic on %d boundary + 20000 fuzz '\n"
    "          'integers (real builtin hash)' % len(bnd))\n"
    "\n"
    "_drive()\n"
    "sys.exit(0)\n"
)

# axiom-containment probe: enumerate EXACTLY the callee-inputs the MODEL can
# reach. located_value calls hash_int(self.order) ONLY; self.order is typed int
# (Descriptor.order: int). So every reachable callee-input is an int, which is
# in hash_int's Requires domain (value: int). Covering more (e.g. floats/strings)
# would be sound, not a defect; the check is containment of reachable inputs.
_CONTAIN_PROBE = (
    "# -*- coding: utf-8 -*-\n"
    "import sys\n"
    "# The model's located_value passes EXACTLY hash_int(self.order) to the\n"
    "# axiom; self.order has model type `int` (Descriptor.order: int). No other\n"
    "# call site exists. hash_int's Requires domain is `value: int`. Therefore\n"
    "# every caller-reachable callee-input is an int and lies inside the axiom\n"
    "# domain. We confirm the real builtin `hash` ACCEPTS every int the caller\n"
    "# can reach (boundaries the model could carry as a creation order) -- i.e.\n"
    "# the domain is non-vacuous and the callee is total on it.\n"
    "reachable_orders = [0,1,-1,2,-2,7,42,123456789,2**31,2**31-1,-(2**31),\n"
    "                    2**63,2**63-1,-(2**63),2**64,-(2**64),10**18,-(10**18)]\n"
    "for o in reachable_orders:\n"
    "    assert isinstance(o, int), 'reachable order not int: %r' % (o,)\n"
    "    h = hash(o)  # real callee accepts every reachable int\n"
    "    assert isinstance(h, int), 'hash(int) did not return int for %r' % (o,)\n"
    "print('AXIOM-CONTAINMENT: every caller-reachable hash_int input is an int '\n"
    "      '(self.order: int) and lies in the axiom Requires domain; real hash '\n"
    "      'total over %d reachable orders' % len(reachable_orders))\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "ax-sound-hash_int",
        "axiom": "hash_int",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUND_PROBE,
        "rationale": "hash_int's consumed property is determinism (a function of "
                     "its single int arg). The real builtin hash satisfies it on "
                     "all probed ints; if it did not, AXIOM-UNSOUND.",
    },
    {
        "id": "ax-contain-hash_int",
        "axiom": "hash_int",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAIN_PROBE,
        "rationale": "The model reaches hash_int only via hash_int(self.order) "
                     "with self.order: int; every reachable input is an int, "
                     "inside the axiom domain. A reachable input outside would "
                     "be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
