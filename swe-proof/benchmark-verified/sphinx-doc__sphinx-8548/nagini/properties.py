# properties.py — PBT manifest for sphinx-doc__sphinx-8548. NOT a Nagini module;
# a record of adversarially-reasoned falsification cases. The runner
# (swebench_nagini.pbt) parses SPEC_TESTS / AXIOM_TESTS, writes each spec
# `module` to a temp file and runs the Nagini verifier + same_spec against the
# frozen model.py, and runs each axiom `probe` in the instance Docker image.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   resolve_attribute_doc(nm, mro, ens, enm, edoc) -> int resolves attribute
#   name `nm`'s documentation-body code under the MRO-aware lookup. The
#   load-bearing postcondition is
#       Result() == resolved_doc(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm), ToSeq(edoc))
#   i.e. earliest-MRO-owner / first-record resolution (base-class owners count;
#   subject overrides its bases). resolved_doc is a @Pure fold GROUNDED in the
#   args (fully unfolded), so there is no opaque answer-key to echo: an
#   ungrounded-oracle echo would BE the correct answer (used as a positive
#   control), not a wrong echo. The discriminator (G-DIFF / G-PANEL) is the
#   base-only attribute (attr1 documented only on Foo) and the overridden
#   attribute (attr2 on both Bar and Foo, subject wins).
#
#   ALL FOUR list inputs are read-only: Requires/Ensures Acc(list_pred(x), 1/2).
#   => FRAME-MUTATION is mandatory; a rival that WRITES any input to fabricate a
#   resolution cannot re-establish the Ensures Acc(...,1/2) and must fail for
#   INSUFFICIENT PERMISSION (the gold invariants are kept verbatim so the
#   rejection is attributable to the write, not to a missing invariant).
#
#   The function is pure value (returns an int, raises nothing, mutates
#   nothing) => CONTROL-FLOW-EFFECT is N/A (no observable raise/return/effect
#   difference for a value abstraction to miss).
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8548"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The frozen gold impl region (between # impl-start / # impl-end). Every spec
# case is produced by replacing EXACTLY this block (and nothing else), so the
# spec view — and therefore same_spec — is preserved by construction.
_GOLD_IMPL = """    # impl-start
    c = 0
    while c < len(mro):
        # invariants-start
        Invariant(Acc(list_pred(mro), 1 / 2))
        Invariant(Acc(list_pred(ens), 1 / 2))
        Invariant(Acc(list_pred(enm), 1 / 2))
        Invariant(Acc(list_pred(edoc), 1 / 2))
        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
        Invariant(0 <= c and c <= len(mro))
        # every MRO class before `c` owned no record for `nm`
        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), 0) ==
                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), c))
        # The loop consumes the termination obligation: len(mro) - c is the
        # strictly decreasing, bounded-below measure.
        Invariant(MustTerminate(len(mro) - c))
        # invariants-end
        owner = mro[c]
        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found != ABSENT:
            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                                ToSeq(edoc), c) == found)
            return found
        c = c + 1
    return ABSENT
    # impl-end"""


def _swap_impl(new_impl: str) -> str:
    """Replace ONLY the gold impl region with `new_impl` (which must itself be a
    full `# impl-start` ... `# impl-end` block). Guarantees same_spec."""
    if _GOLD_IMPL not in _BASE:
        raise AssertionError("drift: gold impl block not found verbatim in model.py")
    if _BASE.count(_GOLD_IMPL) != 1:
        raise AssertionError("gold impl block not unique in model.py")
    if not new_impl.startswith("    # impl-start") or not new_impl.rstrip().endswith("# impl-end"):
        raise AssertionError("replacement is not a self-contained impl region")
    return _BASE.replace(_GOLD_IMPL, new_impl, 1)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 1 (soundness): grounded-oracle echo.
# resolved_doc is GROUNDED in the args (a fully-unfolded @Pure fold), so the
# postcondition IS the oracle and echoing it is the cheapest CORRECT impl.
# It must verify; if it cannot, the spec is SPEC-TOO-STRONG (or the oracle is
# not actually computable from the args). This doubles as the proof that the
# oracle is grounded, not opaque.
# ---------------------------------------------------------------------------
_POS_ECHO = """    # impl-start
    return resolved_doc(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm), ToSeq(edoc))
    # impl-end"""

# ---------------------------------------------------------------------------
# POSITIVE CONTROL 2 (soundness): structurally-different but CORRECT impl.
# Same forward MRO direction (so it stays aligned with the front-recursive
# resolve_from and needs NO induction lemma the verifier can't discharge), but
# the branch shape is reshaped: instead of `if found != ABSENT: ... return`,
# it negates the guard and `continue`s, returning `found` after the loop body's
# decision. It KEEPS the gold loop invariants and the per-step framing Assert
# (directive 2: dropping them would fail the invariant for a PROOF reason, not a
# spec reason). MUST verify.
# ---------------------------------------------------------------------------
_POS_REORDER = """    # impl-start
    c = 0
    result = ABSENT  # type: int
    while c < len(mro):
        # invariants-start
        Invariant(Acc(list_pred(mro), 1 / 2))
        Invariant(Acc(list_pred(ens), 1 / 2))
        Invariant(Acc(list_pred(enm), 1 / 2))
        Invariant(Acc(list_pred(edoc), 1 / 2))
        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
        Invariant(0 <= c and c <= len(mro))
        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), 0) ==
                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), c))
        # The loop consumes the termination obligation.
        Invariant(MustTerminate(len(mro) - c))
        # invariants-end
        found = lookup_owner_doc(mro[c], nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found == ABSENT:
            c = c + 1
            continue
        Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                            ToSeq(edoc), c) == found)
        return found
    return ABSENT
    # impl-end"""

# ---------------------------------------------------------------------------
# ADMISSIBILITY (verify): a positive-control caller proves the precondition
# admits a normal F2P-shaped input. We build the F2P record table inside the
# function-under-spec itself (so we own full list_pred on the locals), call the
# modeled resolver as a helper-free self-contained body, and Assert the result
# equals the grounded oracle for that input — i.e. the Requires are satisfiable
# for the Bar(Foo) shape (attr1 base-only, attr2 overridden, attr3 own). If the
# precondition could not be established for this legitimate input the call site
# would fail => PRECOND-TOO-STRONG.
#
# We do this by KEEPING the gold impl and appending, inside the impl region, an
# unreachable-after-return admissibility witness is impossible (return ends the
# body), so instead the admissibility case is a SEPARATE module: it keeps the
# gold impl verbatim and adds a NEW verified `_admit` function in the impl-free
# module tail. But the runner checks same_spec over the spec view, which elides
# only the impl region — a brand-new top-level function would change the spec
# view. Therefore admissibility is encoded as the gold impl plus an in-region
# `Assert` chain that exercises the Requires on representative concrete values
# WITHOUT adding module-level symbols: we Assert the pure oracle is well-defined
# (its Requires hold) on a constructed PSeq, which is exactly the precondition
# content the caller must establish. This stays inside impl-start/impl-end.
# ---------------------------------------------------------------------------
_ADMISS = """    # impl-start
    # Admissibility witness: the Requires (parallel-length record table, halved
    # permissions) are establishable, and the grounded oracle is well-defined on
    # an F2P-shaped PSeq input (Bar=0, Foo=1, object=2; attr1 base-only on Foo,
    # attr2 overridden, attr3 own). PSeq literals need no list_pred, so this
    # exercises the spec's own domain without extra permissions.
    fmro = PSeq(0, 1, 2)  # type: PSeq[int]
    fens = PSeq(1, 1, 0, 0)  # type: PSeq[int]
    fenm = PSeq(10, 11, 11, 12)  # type: PSeq[int]
    fdoc = PSeq(100, 100, 200, 200)  # type: PSeq[int]
    # resolved_doc is a deeply front-recursive @Pure fold; Nagini does not
    # auto-unfold it to a fixed point on concrete PSeq literals, so each of the
    # three witness equalities is established by an explicit descending-argument
    # unfold ladder (every step is a TRUE pure-function equality, so asserting it
    # is sound and stays inside the impl region — no spec is touched). This is a
    # PROOF nudge for the verifier, not a strengthening of the precondition: the
    # Requires (parallel length, halved permissions) hold for this F2P-shaped
    # input, which the headline asserts at the end of each ladder demonstrate.
    Assert(len(fens) == 4)
    Assert(len(fenm) == 4)
    Assert(len(fdoc) == 4)
    Assert(len(fmro) == 3)
    # --- base-only attr1 (nm=10) resolves to Foo's body (100), not ABSENT ---
    # inner lookup over owner Bar(0): no matching record -> ABSENT
    Assert(lookup_owner_doc(0, 10, fens, fenm, fdoc, 4) == ABSENT)
    Assert(lookup_owner_doc(0, 10, fens, fenm, fdoc, 3) == ABSENT)
    Assert(lookup_owner_doc(0, 10, fens, fenm, fdoc, 2) == ABSENT)
    Assert(lookup_owner_doc(0, 10, fens, fenm, fdoc, 1) == ABSENT)
    Assert(lookup_owner_doc(0, 10, fens, fenm, fdoc, 0) == ABSENT)
    # owner Foo(1): record 0 matches -> 100
    Assert(lookup_owner_doc(1, 10, fens, fenm, fdoc, 0) == 100)
    # owner object(2): no matching record -> ABSENT
    Assert(lookup_owner_doc(2, 10, fens, fenm, fdoc, 4) == ABSENT)
    Assert(lookup_owner_doc(2, 10, fens, fenm, fdoc, 3) == ABSENT)
    Assert(lookup_owner_doc(2, 10, fens, fenm, fdoc, 2) == ABSENT)
    Assert(lookup_owner_doc(2, 10, fens, fenm, fdoc, 1) == ABSENT)
    Assert(lookup_owner_doc(2, 10, fens, fenm, fdoc, 0) == ABSENT)
    # outer MRO walk: Bar ABSENT, object ABSENT, Foo -> 100 (earliest owner wins)
    Assert(resolve_from(10, fmro, fens, fenm, fdoc, 3) == ABSENT)
    Assert(resolve_from(10, fmro, fens, fenm, fdoc, 2) == ABSENT)
    Assert(resolve_from(10, fmro, fens, fenm, fdoc, 1) == 100)
    Assert(resolve_from(10, fmro, fens, fenm, fdoc, 0) == 100)
    Assert(resolved_doc(10, fmro, fens, fenm, fdoc) == 100)
    # --- overridden attr2 (nm=11) resolves to Bar's body (200), not Foo's ---
    # owner Bar(0): record 2 matches -> 200 (subject owns it, so it wins)
    Assert(lookup_owner_doc(0, 11, fens, fenm, fdoc, 4) == ABSENT)
    Assert(lookup_owner_doc(0, 11, fens, fenm, fdoc, 3) == ABSENT)
    Assert(lookup_owner_doc(0, 11, fens, fenm, fdoc, 2) == 200)
    Assert(lookup_owner_doc(0, 11, fens, fenm, fdoc, 1) == 200)
    Assert(lookup_owner_doc(0, 11, fens, fenm, fdoc, 0) == 200)
    # outer MRO walk: Bar(0) owns it at c=0 -> 200 (no fall-through to Foo)
    Assert(resolve_from(11, fmro, fens, fenm, fdoc, 0) == 200)
    Assert(resolved_doc(11, fmro, fens, fenm, fdoc) == 200)
    # --- an undocumented name (nm=99) resolves to ABSENT ---
    Assert(lookup_owner_doc(0, 99, fens, fenm, fdoc, 4) == ABSENT)
    Assert(lookup_owner_doc(0, 99, fens, fenm, fdoc, 3) == ABSENT)
    Assert(lookup_owner_doc(0, 99, fens, fenm, fdoc, 2) == ABSENT)
    Assert(lookup_owner_doc(0, 99, fens, fenm, fdoc, 1) == ABSENT)
    Assert(lookup_owner_doc(0, 99, fens, fenm, fdoc, 0) == ABSENT)
    Assert(lookup_owner_doc(1, 99, fens, fenm, fdoc, 4) == ABSENT)
    Assert(lookup_owner_doc(1, 99, fens, fenm, fdoc, 3) == ABSENT)
    Assert(lookup_owner_doc(1, 99, fens, fenm, fdoc, 2) == ABSENT)
    Assert(lookup_owner_doc(1, 99, fens, fenm, fdoc, 1) == ABSENT)
    Assert(lookup_owner_doc(1, 99, fens, fenm, fdoc, 0) == ABSENT)
    Assert(lookup_owner_doc(2, 99, fens, fenm, fdoc, 4) == ABSENT)
    Assert(lookup_owner_doc(2, 99, fens, fenm, fdoc, 3) == ABSENT)
    Assert(lookup_owner_doc(2, 99, fens, fenm, fdoc, 2) == ABSENT)
    Assert(lookup_owner_doc(2, 99, fens, fenm, fdoc, 1) == ABSENT)
    Assert(lookup_owner_doc(2, 99, fens, fenm, fdoc, 0) == ABSENT)
    Assert(resolve_from(99, fmro, fens, fenm, fdoc, 3) == ABSENT)
    Assert(resolve_from(99, fmro, fens, fenm, fdoc, 2) == ABSENT)
    Assert(resolve_from(99, fmro, fens, fenm, fdoc, 1) == ABSENT)
    Assert(resolve_from(99, fmro, fens, fenm, fdoc, 0) == ABSENT)
    Assert(resolved_doc(99, fmro, fens, fenm, fdoc) == ABSENT)
    # ... then the gold computation for the actual queried name:
    c = 0
    while c < len(mro):
        # invariants-start
        Invariant(Acc(list_pred(mro), 1 / 2))
        Invariant(Acc(list_pred(ens), 1 / 2))
        Invariant(Acc(list_pred(enm), 1 / 2))
        Invariant(Acc(list_pred(edoc), 1 / 2))
        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
        Invariant(0 <= c and c <= len(mro))
        Invariant(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), 0) ==
                  resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                               ToSeq(edoc), c))
        # The loop consumes the termination obligation.
        Invariant(MustTerminate(len(mro) - c))
        # invariants-end
        owner = mro[c]
        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found != ABSENT:
            Assert(resolve_from(nm, ToSeq(mro), ToSeq(ens), ToSeq(enm),
                                ToSeq(edoc), c) == found)
            return found
        c = c + 1
    return ABSENT
    # impl-end"""

# ---------------------------------------------------------------------------
# FRAME-MUTATION 1 (uniqueness/reject, MANDATORY): the rival WRITES to the
# read-only `ens` record-owner column to fabricate a base-class record under the
# subject's own owner, then runs the (buggy own-owner-only) lookup — so a
# base-only attribute appears to resolve. With only Acc(list_pred(ens), 1/2),
# the assignment `ens[0] = mro[0]` needs WRITE permission the function does not
# hold, so it fails for INSUFFICIENT PERMISSION. The gold invariants are NOT
# present here (the body is a single-pass own-owner scan after the write), which
# is fine: the rejection must come from the write, and we keep no spurious
# invariant that could independently fail.
# REFINEMENT: its faithful real patch would mutate the caller's record table
# (rewrite attr_docs owners) before lookup — destroying the (owner,name)->doc
# provenance Sphinx relies on (attr1 would be re-attributed to Bar). It would
# crash / corrupt every P2P that re-reads attr_docs and would NOT resolve
# test_inherited_instance_variable for the right reason (it relabels rather than
# walks the MRO). A verifying mutator would be a verify-without-correctness break.
# ---------------------------------------------------------------------------
_FRAME_MUT_ENS = """    # impl-start
    if len(mro) == 0 or len(ens) == 0:
        return ABSENT
    # WRITE to a read-only input (only Acc(list_pred(ens),1/2) held): re-stamp
    # the first record's owner to the subject so an own-owner-only scan finds it.
    ens[0] = mro[0]
    own = mro[0]
    found = lookup_owner_doc(own, nm, ToSeq(ens), ToSeq(enm), ToSeq(edoc), 0)
    return found
    # impl-end"""

# ---------------------------------------------------------------------------
# FRAME-MUTATION 2 (uniqueness/reject, supporting): mutate `mro` itself
# (append the unrelated record owners so every documented owner sits on the
# MRO). Needs write permission on `mro` it does not hold => insufficient
# permission. Supporting case for the same #1 weakness class (a different
# read-only input mutated), still carrying a real refinement.
# REFINEMENT: a faithful patch appending arbitrary record owners to getmro()
# would resolve documentation for classes NOT in the inheritance chain (e.g. an
# unrelated class that happens to define a same-named attribute), violating the
# MRO-scoping the issue is about and breaking P2P (test_instance_variable would
# leak unrelated docs). It does NOT resolve for the right reason.
# ---------------------------------------------------------------------------
_FRAME_MUT_MRO = """    # impl-start
    j = 0
    while j < len(ens):
        # Termination measure carried so the rejection stays attributable to
        # the WRITE below, not to a missing termination measure.
        Invariant(MustTerminate(len(ens) - j))
        # WRITE to read-only `mro` (only Acc(list_pred(mro),1/2) held):
        mro.append(ens[j])
        j = j + 1
    c = 0
    while c < len(mro):
        Invariant(MustTerminate(len(mro) - c))
        owner = mro[c]
        found = lookup_owner_doc(owner, nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found != ABSENT:
            return found
        c = c + 1
    return ABSENT
    # impl-end"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN 1 (uniqueness/reject): the PRE-PATCH rule — match records only
# against the subject's OWN owner (mro[0]); never scan the base classes. This is
# the canonical partial-domain rival: CORRECT on every own-owner / overridden
# name (attr2, attr3) but WRONG on every base-only name (attr1 -> ABSENT where
# the spec requires Foo's body). This is exactly model_prepatch.py's rule and is
# what the discriminating F2P (test_inherited_instance_variable) was written to
# catch.
# REFINEMENT: this IS the pre-patch behaviour; the gold patch exists precisely
# to fix it. A faithful real patch with this logic does NOT resolve
# test_inherited_instance_variable (attr1's inherited doc is missing) — verified
# by G-DIFF (model_prepatch fails the postcondition) and G-RESOLVE.
# ---------------------------------------------------------------------------
_PARTIAL_OWN_ONLY = """    # impl-start
    if len(mro) == 0:
        return ABSENT
    own = mro[0]
    found = lookup_owner_doc(own, nm, ToSeq(ens), ToSeq(enm), ToSeq(edoc), 0)
    return found
    # impl-end"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN 2 (uniqueness/reject): IGNORE MRO precedence — return the FIRST
# record in table order that names `nm` whose owner is anywhere on the MRO,
# regardless of which MRO position that owner occupies. Correct whenever the
# record table happens to be subject-first ordered (the common F2P fixture
# layout where Bar's records precede Foo's), but WRONG for an overridden name
# whose base record is recorded BEFORE the subject record. Diverges from
# earliest-MRO-owner precedence on the override sub-domain.
# REFINEMENT: a faithful patch that fills `members` by first-record-globally
# instead of MRO-front-to-back would pick the base class's docstring for an
# overridden attribute when the base's comment was parsed first — producing the
# wrong (un-overridden) documentation. It diverges from gold on the override
# case and would fail a P2P asserting the subclass's own attribute doc wins.
# ---------------------------------------------------------------------------
_PARTIAL_GLOBAL_FIRST = """    # impl-start
    j = 0
    while j < len(ens):
        # invariants-start
        Invariant(Acc(list_pred(mro), 1 / 2))
        Invariant(Acc(list_pred(ens), 1 / 2))
        Invariant(Acc(list_pred(enm), 1 / 2))
        Invariant(Acc(list_pred(edoc), 1 / 2))
        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
        Invariant(0 <= j and j <= len(ens))
        # termination measure so the reject is attributable to the
        # postcondition (precedence), not to a missing measure
        Invariant(MustTerminate(len(ens) - j))
        # invariants-end
        if enm[j] == nm:
            c = 0
            while c < len(mro):
                # invariants-start
                Invariant(Acc(list_pred(mro), 1 / 2))
                Invariant(Acc(list_pred(ens), 1 / 2))
                Invariant(Acc(list_pred(enm), 1 / 2))
                Invariant(Acc(list_pred(edoc), 1 / 2))
                Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
                Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
                Invariant(0 <= c and c <= len(mro))
                Invariant(0 <= j and j < len(ens))
                Invariant(MustTerminate(len(mro) - c))
                # invariants-end
                if mro[c] == ens[j]:
                    return edoc[j]
                c = c + 1
        j = j + 1
    return ABSENT
    # impl-end"""

# ---------------------------------------------------------------------------
# PARTIAL-DOMAIN 3 (uniqueness/reject): LATEST-MRO-owner wins (base overrides
# subject) — scan the MRO back-to-front and return the last MRO class that owns
# a matching record. Correct for every name documented on exactly one MRO class
# (attr1 base-only, attr3 own), but WRONG on the overridden sub-domain: attr2
# (on both Bar and Foo) resolves to FOO's body instead of Bar's. Inverts the
# precedence the change installs.
# REFINEMENT: a faithful patch walking getmro() back-to-front (or overwriting
# `members[name]` unconditionally instead of guarding with `name not in
# members`) yields the most-base docstring for an overridden attribute, the
# opposite of Python's override semantics. It does NOT resolve the override
# expectation and diverges from gold on attr2.
# ---------------------------------------------------------------------------
_PARTIAL_LATEST = """    # impl-start
    c = len(mro) - 1
    result = ABSENT  # type: int
    while c >= 0:
        # invariants-start
        Invariant(Acc(list_pred(mro), 1 / 2))
        Invariant(Acc(list_pred(ens), 1 / 2))
        Invariant(Acc(list_pred(enm), 1 / 2))
        Invariant(Acc(list_pred(edoc), 1 / 2))
        Invariant(len(ToSeq(ens)) == len(ToSeq(enm)))
        Invariant(len(ToSeq(enm)) == len(ToSeq(edoc)))
        Invariant(-1 <= c and c < len(mro))
        # termination measure so the reject is attributable to the
        # postcondition (inverted precedence), not to a missing measure
        Invariant(MustTerminate(c + 1))
        # invariants-end
        found = lookup_owner_doc(mro[c], nm, ToSeq(ens), ToSeq(enm),
                                 ToSeq(edoc), 0)
        if found != ABSENT:
            result = found
        c = c - 1
    return result
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-grounded-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_ECHO),
        "rationale": "resolved_doc is grounded in the args (a fully-unfolded "
                     "@Pure fold), so the cheapest correct impl is to echo it; "
                     "if this cannot verify the spec is SPEC-TOO-STRONG. Also "
                     "demonstrates the oracle is grounded (not an opaque "
                     "answer-key), so no WRONG echo exists.",
    },
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_impl(_POS_REORDER),
        "rationale": "structurally-different CORRECT impl: same forward MRO "
                     "direction (no induction lemma needed) but negated guard "
                     "+ continue and a single tail return; keeps the gold loop "
                     "invariants and per-step framing Assert. Must verify "
                     "(else SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_impl(_ADMISS),
        "rationale": "the precondition must admit a normal F2P-shaped input. "
                     "Asserts the grounded oracle is well-defined on the "
                     "Bar(Foo) shape (base-only attr1->Foo, overridden "
                     "attr2->Bar, absent->ABSENT) inside the impl region; if "
                     "the Requires could not be established for this legitimate "
                     "input it would be PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mut-ens",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_FRAME_MUT_ENS),
        "refinement": "a faithful patch that re-stamps record owners (rewrites "
                      "attr_docs keys to the subject's qualname) before lookup "
                      "destroys the (owner,name)->doc provenance: attr1 would be "
                      "re-attributed to Bar and every P2P re-reading attr_docs "
                      "would see corrupted owners. It relabels instead of "
                      "walking the MRO and would NOT resolve "
                      "test_inherited_instance_variable for the right reason.",
        "rationale": "MANDATORY frame-mutation: `ens[0] = mro[0]` writes a "
                     "read-only input held only at Acc(list_pred(ens),1/2). "
                     "Rejection comes from the PERMISSION SYSTEM (insufficient "
                     "write permission), independent of the postcondition.",
    },
    {
        "id": "frame-mut-mro-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_FRAME_MUT_MRO),
        "refinement": "appending arbitrary record owners to getmro() would "
                      "resolve documentation for classes NOT on the inheritance "
                      "chain (an unrelated class defining a same-named "
                      "attribute), violating MRO scoping and leaking unrelated "
                      "docs into P2P (test_instance_variable). Does not resolve "
                      "for the right reason.",
        "rationale": "supporting frame-mutation on a DIFFERENT read-only input: "
                     "`mro.append(...)` needs write permission on `mro` held "
                     "only at Acc(list_pred(mro),1/2). Rejected by the "
                     "permission system.",
    },
    {
        "id": "weak-own-owner-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_PARTIAL_OWN_ONLY),
        "refinement": "this IS the pre-patch rule (match only mro[0]); the gold "
                      "patch exists to fix it. A faithful patch with this logic "
                      "leaves attr1 (base-only) absent and does NOT resolve "
                      "test_inherited_instance_variable — confirmed by G-DIFF "
                      "(model_prepatch fails the postcondition) and G-RESOLVE.",
        "rationale": "partial-domain: correct on own-owner/overridden names, "
                     "wrong on every base-only name. Rejected by the "
                     "postcondition Result()==resolved_doc(...) at the base-only "
                     "sub-domain.",
    },
    {
        "id": "weak-global-first-record",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_PARTIAL_GLOBAL_FIRST),
        "refinement": "filling members by first-record-globally (instead of "
                      "MRO front-to-back) picks the base class's docstring for "
                      "an overridden attribute whenever the base's comment was "
                      "parsed first — the wrong, un-overridden documentation. "
                      "Diverges from gold on the override case and fails a P2P "
                      "asserting the subclass's own doc wins.",
        "rationale": "partial-domain: correct when records are subject-first "
                     "ordered, wrong on the override sub-domain where a base "
                     "record precedes the subject record. Rejected by the "
                     "earliest-MRO-owner precedence in resolved_doc.",
    },
    {
        "id": "weak-latest-mro-owner",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_impl(_PARTIAL_LATEST),
        "refinement": "walking getmro() back-to-front (or overwriting "
                      "members[name] unconditionally) yields the most-base "
                      "docstring for an overridden attribute — the opposite of "
                      "Python override semantics. attr2 would resolve to Foo's "
                      "body, not Bar's; does not resolve the override "
                      "expectation and diverges from gold on attr2.",
        "rationale": "partial-domain: correct on singly-documented names, wrong "
                     "on the overridden sub-domain (latest wins inverts the "
                     "earliest-MRO precedence). Rejected by the postcondition.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane. This bundle has NO consumed @ContractOnly axiom (meta.axioms ==
# []). The membership/precedence rule is modeled DEEPLY in the frozen spec
# (resolve_from / lookup_owner_doc, an A-reference). The plan still requires the
# A-reference deep model to be checked == the real callee on every
# caller-reachable input. We carry the existing axiom_check.py soundness logic
# into the Docker lane as an A-reference soundness probe:
#   - (containment / soundness, combined) re-run the faithful transcription of
#     the patched get_class_members loop over the same abstract record table and
#     assert resolve_from agrees per-name on boundary + fuzz hierarchies; AND
#   - drive the REAL sphinx.pycode parser + (when importable) the REAL patched
#     get_class_members on the Bar(Foo) fixture and assert the
#     attribute->documentation map equals the model.
# This is the soundness side. Containment is structural here: the model only
# ever reaches owner/name/doc int codes drawn from its OWN (mro, ens, enm, edoc)
# inputs — the same domain the deep model is total over (resolve_from's Requires
# are just parallel-length + index bounds, which the caller's Requires already
# guarantee) — so there is no callee-input the model can reach outside the deep
# model's domain. The probe below exercises that totality on fuzzed inputs.
#
# We embed axiom_check.py's source at manifest-load time (HOST read) because the
# runner mounts ONLY the probe script in-container; the probe then runs its
# checks and exits 0 iff every real-callee observation matches the model.
# ---------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_AREF_PROBE = (
    "# A-reference soundness probe (sphinx-doc__sphinx-8548): the deep model\n"
    "# resolve_from/lookup_owner_doc must equal the real patched\n"
    "# get_class_members behaviour on every caller-reachable input. We execute\n"
    "# the embedded axiom_check.py oracle (which CALLS the real sphinx parser /\n"
    "# get_class_members, never scrapes source) under gold-applied Sphinx.\n"
    "import sys\n"
    "\n"
    "AXIOM_CHECK_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "\n"
    "ns = {'__name__': '_aref_probe', '__file__': 'axiom_check_embedded.py'}\n"
    "try:\n"
    "    exec(compile(AXIOM_CHECK_SRC, 'axiom_check_embedded.py', 'exec'), ns)\n"
    "except Exception as e:\n"
    "    print('PROBE-ERROR loading embedded axiom_check.py:', repr(e))\n"
    "    sys.exit(1)\n"
    "\n"
    "# (1) deep model == faithful transcription of the patched loop on 8\n"
    "#     boundary + 20000 fuzz hierarchies (stdlib-only, always runs).\n"
    "try:\n"
    "    ns['fuzz_loop_equivalence']()\n"
    "    print('OK: resolve_from == patched-loop transcription (boundary+20000 fuzz)')\n"
    "except AssertionError as e:\n"
    "    print('A-REFERENCE UNSOUND (deep model != patched loop):', e)\n"
    "    sys.exit(1)\n"
    "\n"
    "# (2) record-table abstraction validated against the REAL sphinx.pycode\n"
    "#     parser, and the model resolution over the REAL keys matches the F2P\n"
    "#     attribute documentation.\n"
    "parser_ok = ns['check_real_parser']()\n"
    "if parser_ok is True:\n"
    "    print('OK: model resolution == REAL sphinx.pycode parser keys (Bar(Foo) attr1/attr2/attr3)')\n"
    "elif parser_ok is None:\n"
    "    print('PROBE-ERROR: sphinx.pycode.parser not importable under gold-applied image')\n"
    "    sys.exit(1)\n"
    "\n"
    "# (3) REAL patched get_class_members end-to-end on a synthesised Bar(Foo)\n"
    "#     module; its attribute->documentation map must equal the model.\n"
    "real_ok = ns['check_real_sphinx']()\n"
    "if real_ok is True:\n"
    "    print('OK: REAL get_class_members == model (Bar(Foo): attr1=foo, attr2=bar, attr3=bar)')\n"
    "elif real_ok is None:\n"
    "    print('NOTE: real get_class_members not importable here; (1)+(2) carried the soundness check')\n"
    "\n"
    "print('A-REFERENCE SOUND: deep model resolve_from agrees with the real patched collection logic')\n"
    "sys.exit(0)\n"
)

AXIOM_TESTS = [
    {
        "id": "aref-resolve-from-soundness",
        "axiom": "resolve_from / lookup_owner_doc",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AREF_PROBE,
        "rationale": "no consumed @ContractOnly axiom; the changed decision "
                     "logic is the A-reference deep model resolve_from. It must "
                     "equal the real patched get_class_members on every "
                     "caller-reachable input. The probe runs the patched-loop "
                     "transcription on boundary+20000 fuzz hierarchies and the "
                     "REAL sphinx.pycode parser + get_class_members on Bar(Foo); "
                     "any disagreement (base-only attr1 dropped, override "
                     "precedence inverted, unrelated owner leaked) exits non-zero "
                     "=> A-reference unsound. Containment is structural: the "
                     "model reaches only int codes from its own parallel-length "
                     "inputs, the exact domain resolve_from is total over.",
    },
]
