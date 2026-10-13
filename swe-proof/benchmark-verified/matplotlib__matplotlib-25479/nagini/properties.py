# properties.py — PBT falsification battery for matplotlib__matplotlib-25479.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap a
# SINGLE `# impl-start` .. `# impl-end` block (of `colormaps_equal` OR of
# `register_named`) for a new body, leaving the frozen spec — and the OTHER
# function's impl, and the `Cmap.__init__` constructor body (which has NO impl
# markers, so it lives in the spec view) — byte-identical. spec_view elides BOTH
# impl regions, so same_spec is GUARANTEED whenever we touch only the bytes
# strictly between one pair of `# impl-start`/`# impl-end` markers and leave the
# constructor untouched.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#
#  FUNCTION 1 — colormaps_equal(self, other) -> bool  [self, other READ-ONLY]
#    Load-bearing postcondition (the discriminating fix is the ABSENCE of a label
#    term):
#       (E) Result() == (self.colorbar_extend == other.colorbar_extend
#                        and seq_eq(ToSeq(self.lut), ToSeq(other.lut)))
#    The label (`name`) is NOT consulted; equality is colorbar_extend-equal AND
#    lookup-table-content-equal. `seq_eq` is a @Pure, fully GROUNDED/transparent
#    front-recursive content equality of the two arg sequences — there is no
#    opaque answer-key to echo, so there is no "wrong echo" (see 'assessment');
#    the ungrounded-oracle slot is filled by an honest positive control.
#    BOTH operands are read-only (Acc(self.*,1/2), Acc(other.*,1/2)) => the
#    frame-mutation probe is MANDATORY (write self.name / self.lut -> reject for
#    INSUFFICIENT PERMISSION).
#
#  FUNCTION 2 — register_named(reg, name, cmap) -> None  [cmap READ-ONLY; reg full]
#    Load-bearing postconditions:
#       (R1) name in reg
#       (R2) reg[name] is not cmap                 -- independent snapshot
#       (R3) reg[name].name == name                -- the discriminating relabel fix
#       (R4) reg[name].colorbar_extend == cmap.colorbar_extend
#       (R5) ToSeq(reg[name].lut) == ToSeq(cmap.lut)
#       (R6) cmap.name == Old(cmap.name) and cmap.colorbar_extend == Old(...)  -- cmap untouched
#       (R7) Forall k != name: (k in reg) == Old(k in reg)   -- registry frame: membership
#       (R8) Forall k != name, Old(k in reg): reg[k] is Old(reg[k])  -- registry frame: binding
#       (R9) not Old(name in reg)   -- publication happens ONLY under a FREE label
#       (R10) Exsures(LabelAlreadyBound, ...): an ALREADY-BOUND label is REFUSED --
#             the condition is reported out of band, Old(name in reg) held, and the
#             registry is left exactly as it was (every label keeps its membership
#             AND its bound object, the colliding one included), cmap untouched.
#    R9/R10 are the two arms of the publication: a label that is free is published
#    under, a label that is already bound is refused without disturbing anything.
#    An impl may not refuse on a free label (R9 + the Exsures' Old(name in reg)),
#    nor damage the store while refusing (R10's frame legs).
#    `cmap` is read-only (Acc(cmap.*,1/2)) => the cheapest cheat (mutate cmap.name
#    to the registration name and store cmap itself) is exactly the frame-mutation
#    probe and MUST be rejected for INSUFFICIENT PERMISSION.
#
#  The two gold hunks (refinement.md): colors.py __eq__ drops the
#  `self.name != other.name` disjunct (Function 1); cm.py register relabels the
#  stored snapshot to the registration name (Function 2). The two F2P tests
#  (test_colormap_equals: relabelled copy is EQUAL; test_set_cmap_mismatched_name:
#  get_cmap("wrong-cmap").name == "wrong-cmap") exercise precisely (E) and (R3).
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25479"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two whole-impl anchors, captured VERBATIM from model.py. Function 1's block
# is `colormaps_equal`'s impl region; Function 2's is `register_named`'s. Each
# variant swaps exactly ONE of these for a new body wrapped back in the exact
# `# impl-start` / `# impl-end` markers (so the region boundary is preserved and
# spec_view elides all of it). The OTHER function's impl block and the
# constructor stay byte-identical, guaranteeing same_spec.
# ---------------------------------------------------------------------------
_EQ_IMPL = (
    "# impl-start\n"
    "    if self.colorbar_extend != other.colorbar_extend:\n"
    "        return False\n"
    "    if len(self.lut) != len(other.lut):\n"
    "        Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))\n"
    "        Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))\n"
    "        return False\n"
    "    i = 0\n"
    "    while i < len(self.lut):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(self.lut, 1 / 2) and Acc(list_pred(self.lut), 1 / 2))\n"
    "        Invariant(Acc(other.lut, 1 / 2) and Acc(list_pred(other.lut), 1 / 2))\n"
    "        Invariant(len(self.lut) == len(other.lut))\n"
    "        Invariant(0 <= i and i <= len(self.lut))\n"
    "        Invariant(seq_eq(ToSeq(self.lut), ToSeq(other.lut))\n"
    "                  == seq_eq(ToSeq(self.lut).drop(i), ToSeq(other.lut).drop(i)))\n"
    "        # The scan advances one entry per pass and the table is read-only, so\n"
    "        # `len(self.lut) - i + 1` strictly decreases; the guard `i < len(self.lut)`\n"
    "        # keeps it >= 2 whenever the body runs, hence positive.\n"
    "        Invariant(MustTerminate(len(self.lut) - i + 1))\n"
    "        # invariants-end\n"
    "        Assert(ToSeq(self.lut).drop(i)[0] == self.lut[i])\n"
    "        Assert(ToSeq(other.lut).drop(i)[0] == other.lut[i])\n"
    "        Assert(ToSeq(self.lut).drop(i).drop(1) == ToSeq(self.lut).drop(i + 1))\n"
    "        Assert(ToSeq(other.lut).drop(i).drop(1) == ToSeq(other.lut).drop(i + 1))\n"
    "        if not entry_eq(self.lut[i], other.lut[i]):\n"
    "            return False\n"
    "        i = i + 1\n"
    "    Assert(len(ToSeq(self.lut).drop(i)) == 0)\n"
    "    Assert(len(ToSeq(other.lut).drop(i)) == 0)\n"
    "    return True\n"
    "    # impl-end"
)
assert _BASE.count(_EQ_IMPL) == 1, "EQ impl anchor drift"

# The verbatim loop body of `colormaps_equal` (between the length guard and the
# trailing exit asserts), reused by the positive control / partial-domain attacks
# so they keep the gold proof obligations intact and differ only as intended.
_EQ_LOOP_AND_TAIL = (
    "    i = 0\n"
    "    while i < len(self.lut):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(self.lut, 1 / 2) and Acc(list_pred(self.lut), 1 / 2))\n"
    "        Invariant(Acc(other.lut, 1 / 2) and Acc(list_pred(other.lut), 1 / 2))\n"
    "        Invariant(len(self.lut) == len(other.lut))\n"
    "        Invariant(0 <= i and i <= len(self.lut))\n"
    "        Invariant(seq_eq(ToSeq(self.lut), ToSeq(other.lut))\n"
    "                  == seq_eq(ToSeq(self.lut).drop(i), ToSeq(other.lut).drop(i)))\n"
    "        # The scan advances one entry per pass and the table is read-only, so\n"
    "        # `len(self.lut) - i + 1` strictly decreases; the guard `i < len(self.lut)`\n"
    "        # keeps it >= 2 whenever the body runs, hence positive.\n"
    "        Invariant(MustTerminate(len(self.lut) - i + 1))\n"
    "        # invariants-end\n"
    "        Assert(ToSeq(self.lut).drop(i)[0] == self.lut[i])\n"
    "        Assert(ToSeq(other.lut).drop(i)[0] == other.lut[i])\n"
    "        Assert(ToSeq(self.lut).drop(i).drop(1) == ToSeq(self.lut).drop(i + 1))\n"
    "        Assert(ToSeq(other.lut).drop(i).drop(1) == ToSeq(other.lut).drop(i + 1))\n"
    "        if not entry_eq(self.lut[i], other.lut[i]):\n"
    "            return False\n"
    "        i = i + 1\n"
    "    Assert(len(ToSeq(self.lut).drop(i)) == 0)\n"
    "    Assert(len(ToSeq(other.lut).drop(i)) == 0)\n"
    "    return True\n"
)


def _eq(body_lines: str) -> str:
    """Swap colormaps_equal's whole impl block (markers re-emitted)."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _EQ_IMPL, new_block)


_REG_IMPL = (
    "# impl-start\n"
    "    # The already-bound label is refused before anything is built or stored.\n"
    "    if name in reg:\n"
    "        raise LabelAlreadyBound()\n"
    "    snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)\n"
    "    # The published snapshot is relabelled to the chosen registration label, so\n"
    "    # that a later lookup by that label yields a mapping whose own label matches\n"
    "    # the label it was looked up under.\n"
    "    snapshot.name = name\n"
    "    reg[name] = snapshot\n"
    "    # impl-end"
)
assert _BASE.count(_REG_IMPL) == 1, "REG impl anchor drift"


def _reg(body_lines: str) -> str:
    """Swap register_named's whole impl block (markers re-emitted)."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _REG_IMPL, new_block)


SPEC_TESTS = [

    # ===================================================================
    # FUNCTION 1 — colormaps_equal
    # ===================================================================

    # --------------------------------------------------------- soundness (1)
    # POSITIVE CONTROL A (low-risk local-variable reshape). Bind the
    # extension-flag comparison to a local boolean and branch on it; keep the
    # length guard, the whole loop, and EVERY gold framing assert VERBATIM. This
    # is a genuinely different executable shape that is still correct and that
    # introduces no new proof obligation (no fold/append-direction lemma). If it
    # cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-eq-localbool",
        "kind": "soundness",
        "expect": "verify",
        "module": _eq(
            "    ext_eq = self.colorbar_extend == other.colorbar_extend\n"
            "    if not ext_eq:\n"
            "        return False\n"
            "    if len(self.lut) != len(other.lut):\n"
            "        Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))\n"
            "        Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))\n"
            "        return False\n"
            + _EQ_LOOP_AND_TAIL
        ),
        "rationale": "a correct impl with a DIFFERENT executable shape (the "
                     "colorbar_extend comparison hoisted into a local bool and "
                     "branched on) must verify; it keeps every gold invariant/assert "
                     "and the whole content loop verbatim, so no new proof obligation "
                     "is created. Else SPEC-TOO-STRONG.",
    },

    # --------------------------------------------------------- admissibility (1)
    # ADMISSIBILITY: a self-call caller builds two fresh Cmaps over fresh lists
    # (the constructor establishes full permission to name/colorbar_extend/lut)
    # and invokes colormaps_equal on them — a normal, F2P-shaped in-domain input.
    # The call site must establish colormaps_equal's Requires (passing halves of
    # the constructor's full permissions is admissible). The probe runs at the TOP
    # of the impl (reachable), then the gold body continues. If the Requires cannot
    # be met for a legitimate input => PRECOND-TOO-STRONG.
    {
        "id": "admiss-eq-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _eq(
            "    # Admissibility self-call: two fresh Cmaps over fresh lists are an\n"
            "    # F2P-shaped in-domain input; if the precondition could not be\n"
            "    # established for them, this call site would fail => PRECOND-TOO-STRONG.\n"
            "    la = []  # type: List[int]\n"
            "    lb = []  # type: List[int]\n"
            "    pa = Cmap(0, False, la)\n"
            "    pb = Cmap(1, False, lb)\n"
            "    if len(self.lut) > 0:   # keeps the callee's obligation level below ours\n"
            "        probe = colormaps_equal(pa, pb)\n"
            "        Assert(probe == (pa.colorbar_extend == pb.colorbar_extend\n"
            "                         and seq_eq(ToSeq(pa.lut), ToSeq(pb.lut))))\n"
            + _EQ_IMPL.split("# impl-start\n", 1)[1].rsplit("\n    # impl-end", 1)[0] + "\n"
        ),
        "rationale": "the precondition must admit a normal F2P-shaped input: two "
                     "freshly-constructed Cmaps (full perms from the constructor). The "
                     "self-call establishes colormaps_equal's Requires (halves of the "
                     "constructor's full permissions) and the post fact is derivable; "
                     "else PRECOND-TOO-STRONG.",
    },

    # ------------------------------------------------------------- uniqueness
    # ATTACK 1 (FRAME-MUTATION on self.name, MANDATORY — read-only input). The
    # impl OVERWRITES the read-only self.name to make the operands' labels match
    # before deciding. Only Acc(self.name, 1/2) is held, so the WRITE needs full
    # permission and the verifier MUST reject for INSUFFICIENT PERMISSION (not a
    # value mismatch). Gold body kept verbatim so the rejection is attributable
    # solely to the illegal write.
    {
        "id": "frame-mutate-eq-self-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    # ILLEGAL: write to a read-only (Acc 1/2) input field.\n"
            "    self.name = other.name\n"
            + _EQ_IMPL.split("# impl-start\n", 1)[1].rsplit("\n    # impl-end", 1)[0] + "\n"
        ),
        "refinement": "the real Colormap.__eq__ is a pure read-only comparison; the "
                      "gold fix REMOVES the name disjunct, it never reassigns "
                      "self.name. A patch that writes self.name = other.name mutates "
                      "the live colormap object the caller still holds (e.g. corrupts "
                      "the label of a registered builtin) and the F2P "
                      "test_colormap_equals — which constructs cm_copy with a "
                      "DIFFERENT name and asserts equality WITHOUT the label being "
                      "altered — would observe a clobbered name on subsequent "
                      "assertions. The faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants only "
                     "Acc(self.name, 1/2); a write needs full permission. Insufficient "
                     "permission, not a value mismatch. Mandatory frame-mutation probe.",
    },

    # ATTACK 2 (FRAME-MUTATION on self.lut, MANDATORY — read-only input). The impl
    # mutates the read-only lookup-table list (appends) to force a length/content
    # match. Only Acc(list_pred(self.lut), 1/2) is held => insufficient permission
    # to mutate the list contents.
    {
        "id": "frame-mutate-eq-self-lut",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    # ILLEGAL: mutate a read-only (Acc 1/2) lookup-table list.\n"
            "    self.lut.append(0)\n"
            + _EQ_IMPL.split("# impl-start\n", 1)[1].rsplit("\n    # impl-end", 1)[0] + "\n"
        ),
        "refinement": "Colormap.__eq__ compares _lut via np.array_equal — it never "
                      "appends to or mutates self._lut. A patch that appends to "
                      "self._lut corrupts the colormap's lookup table in place, "
                      "breaking every later render/colorbar P2P that depends on the "
                      "intact lut, and changing the very content the equality is "
                      "supposed to read. The faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: only Acc(list_pred(self.lut), "
                     "1/2) is held; mutating the list needs full permission. "
                     "Insufficient permission. Second mandatory frame-mutation probe.",
    },

    # ATTACK 3 (PARTIAL-DOMAIN — the bug-delta / prepatch_eq). Re-introduce the
    # pre-patch label disjunct: `if self.name != other.name: return False`. CORRECT
    # on every pair whose labels match (the common case), WRONG on a
    # relabelled-but-content-equal pair (Result()==False but (E)'s RHS==True). Must
    # reject by postcondition (E) — the discriminating fix is the ABSENCE of any
    # label term.
    {
        "id": "weak-eq-label-reintroduced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    # PRE-PATCH BUG: label re-introduced into the comparison.\n"
            "    if self.name != other.name:\n"
            "        return False\n"
            + _EQ_IMPL.split("# impl-start\n", 1)[1].rsplit("\n    # impl-end", 1)[0] + "\n"
        ),
        "refinement": "this is exactly the PRE-PATCH __eq__ (model_prepatch_eq.py): "
                      "equality also requires self.name == other.name. The F2P "
                      "test_colormap_equals does `cm_copy = cmap.copy(); "
                      "cm_copy.name = 'Test'; assert cm_copy == cmap` — a relabelled "
                      "copy with an identical lut. With the label disjunct present, "
                      "cm_copy != cmap and the F2P FAILS. The faithful real patch does "
                      "NOT resolve (G-DIFF).",
        "rationale": "violates postcondition (E): on a relabelled-but-content-equal "
                     "pair Result() is False but (colorbar_extend-equal AND seq_eq) is "
                     "True. The label term (E) deliberately omits cannot be smuggled "
                     "back in.",
    },

    # ATTACK 4 (VALUE-DROP — ignore the extension flag). Drop the colorbar_extend
    # guard entirely; decide on lookup-table content alone. CORRECT whenever the
    # extension flags match, WRONG when they differ but the luts are equal
    # (Result()==True but (E)'s RHS==False). Must reject by postcondition (E).
    {
        "id": "weak-eq-ignore-extend",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    # WRONG: the colorbar_extend guard is dropped; equality decided on\n"
            "    # lut content alone.\n"
            "    if len(self.lut) != len(other.lut):\n"
            "        Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))\n"
            "        Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))\n"
            "        return False\n"
            + _EQ_LOOP_AND_TAIL
        ),
        "refinement": "the real __eq__ keeps the `self.colorbar_extend != "
                      "other.colorbar_extend` disjunct (the gold hunk removes ONLY "
                      "the name disjunct). The F2P test_colormap_equals does "
                      "`cm_copy.colorbar_extend = not cmap.colorbar_extend; "
                      "assert cm_copy != cmap` — content-equal but extension-flipped. "
                      "An impl that ignores colorbar_extend returns equal and the F2P "
                      "FAILS. The faithful real patch does NOT resolve.",
        "rationale": "violates postcondition (E): when colorbar_extend differs but "
                     "luts are equal, Result() is True but (colorbar_extend-equal AND "
                     "seq_eq) is False.",
    },

    # ATTACK 5 (PARTIAL-DOMAIN, off-by-one tail). Stop the content loop one element
    # early (`while i < len(self.lut) - 1`), so the final lut entry is never
    # compared. CORRECT on every pair whose luts agree on the last entry, WRONG when
    # they differ only in the last entry (Result()==True but seq_eq==False). Must
    # reject: returning True needs seq_eq over the FULL sequences, which the loop no
    # longer establishes for the dropped tail.
    {
        "id": "weak-eq-truncate-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    if self.colorbar_extend != other.colorbar_extend:\n"
            "        return False\n"
            "    if len(self.lut) != len(other.lut):\n"
            "        Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))\n"
            "        Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))\n"
            "        return False\n"
            "    i = 0\n"
            "    while i < len(self.lut) - 1:\n"
            "        # invariants-start\n"
            "        Invariant(Acc(self.lut, 1 / 2) and Acc(list_pred(self.lut), 1 / 2))\n"
            "        Invariant(Acc(other.lut, 1 / 2) and Acc(list_pred(other.lut), 1 / 2))\n"
            "        Invariant(len(self.lut) == len(other.lut))\n"
            "        Invariant(0 <= i and i <= len(self.lut))\n"
            "        Invariant(seq_eq(ToSeq(self.lut), ToSeq(other.lut))\n"
            "                  == seq_eq(ToSeq(self.lut).drop(i), ToSeq(other.lut).drop(i)))\n"
            "        # this variant stops one entry early, so one fewer iteration\n"
            "        # remains: `len(self.lut) - i` strictly decreases and the guard\n"
            "        # `i < len(self.lut) - 1` keeps it >= 2 whenever the body runs.\n"
            "        Invariant(MustTerminate(len(self.lut) - i))\n"
            "        # invariants-end\n"
            "        Assert(ToSeq(self.lut).drop(i)[0] == self.lut[i])\n"
            "        Assert(ToSeq(other.lut).drop(i)[0] == other.lut[i])\n"
            "        Assert(ToSeq(self.lut).drop(i).drop(1) == ToSeq(self.lut).drop(i + 1))\n"
            "        Assert(ToSeq(other.lut).drop(i).drop(1) == ToSeq(other.lut).drop(i + 1))\n"
            "        if not entry_eq(self.lut[i], other.lut[i]):\n"
            "            return False\n"
            "        i = i + 1\n"
            "    return True\n"
        ),
        "refinement": "this never compares the LAST lookup-table entry. Two colormaps "
                      "differing only in their final lut value (e.g. one over-colour "
                      "changed) would be reported equal. The real np.array_equal "
                      "compares the WHOLE array, so the F2P sizes/mutation cases and "
                      "any P2P that distinguishes such luts diverge. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "to `return True` the postcondition needs seq_eq over the FULL "
                     "sequences; at loop exit the invariant only gives "
                     "seq_eq(full) == seq_eq(drop(len-1)), and the last element's "
                     "equality is never established — so True cannot be proven. "
                     "Off-by-one partial-domain probe.",
    },

    # ===================================================================
    # FUNCTION 2 — register_named
    # ===================================================================

    # --------------------------------------------------------- soundness (2)
    # POSITIVE CONTROL B (structurally different, still correct). Instead of
    # constructing the snapshot with the supplied label then relabelling it, build
    # it directly with the registration `name` (the relabel folded into
    # construction). The constructor's Ensures give snapshot.name == name,
    # colorbar_extend / lut copied from cmap, and a fresh object (reg[name] is not
    # cmap). All postconditions (R1..R6) hold; cmap is read-only and untouched. If
    # it cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-reg-construct-relabel",
        "kind": "soundness",
        "expect": "verify",
        "module": _reg(
            "    # The chosen label is refused if it is already bound, before\n"
            "    # anything is built or stored.\n"
            "    if name in reg:\n"
            "        raise LabelAlreadyBound()\n"
            "    # Fold the relabel into construction: build the snapshot directly\n"
            "    # under the registration label rather than relabelling afterwards.\n"
            "    snapshot = Cmap(name, cmap.colorbar_extend, cmap.lut)\n"
            "    reg[name] = snapshot\n"
        ),
        "rationale": "a correct impl with a DIFFERENT shape (relabel folded into the "
                     "constructor call, no separate `snapshot.name = name`) must "
                     "verify: the constructor Ensures snapshot.name == name and copies "
                     "colorbar_extend / lut from cmap, giving R1..R6 with cmap "
                     "untouched. Else SPEC-TOO-STRONG.",
    },

    # ------------------------------------------------------------- uniqueness
    # ATTACK 6 (FRAME-MUTATION on cmap.name, MANDATORY — read-only input). The
    # cheapest cheat: relabel the SUPPLIED mapping in place (cmap.name = name) and
    # store cmap itself, skipping the independent snapshot. Only Acc(cmap.name, 1/2)
    # is held, so the WRITE needs full permission and the verifier MUST reject for
    # INSUFFICIENT PERMISSION (before any R2/R6 value check). The other gold post-
    # conditions are untouched so the rejection is attributable to the illegal write.
    {
        "id": "frame-mutate-reg-cmap-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    # The chosen label is refused if it is already bound, before\n"
            "    # anything is built or stored.\n"
            "    if name in reg:\n"
            "        raise LabelAlreadyBound()\n"
            "    # ILLEGAL: relabel the read-only (Acc 1/2) supplied mapping in place\n"
            "    # and store it directly, skipping the independent snapshot.\n"
            "    cmap.name = name\n"
            "    reg[name] = cmap\n"
        ),
        "refinement": "the real register does `self._cmaps[name] = cmap.copy()` and "
                      "relabels the COPY; it never mutates the supplied cmap. A patch "
                      "that writes cmap.name = name and stores cmap itself corrupts the "
                      "caller's live colormap (the F2P test_set_cmap_mismatched_name "
                      "asserts the SUPPLIED cmap keeps name 'test-cmap' while the "
                      "REGISTERED lookup yields 'wrong-cmap'; with aliasing both would "
                      "read 'wrong-cmap') and breaks reg[name] is not cmap. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants only "
                     "Acc(cmap.name, 1/2); a write needs full permission. Insufficient "
                     "permission, not a value mismatch. Mandatory frame-mutation probe.",
    },

    # ATTACK 7 (the bug-delta / prepatch_register). Drop the relabel step: store an
    # independent snapshot that keeps the SUPPLIED mapping's label. CORRECT on every
    # registration where cmap.name == name, WRONG when they differ (reg[name].name
    # == cmap.name != name). Must reject by postcondition (R3).
    {
        "id": "weak-reg-drop-relabel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    # The chosen label is refused if it is already bound, before\n"
            "    # anything is built or stored.\n"
            "    if name in reg:\n"
            "        raise LabelAlreadyBound()\n"
            "    # PRE-PATCH BUG: snapshot keeps the supplied mapping's label; the\n"
            "    # relabel-to-registration-name step is dropped.\n"
            "    snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)\n"
            "    reg[name] = snapshot\n"
        ),
        "refinement": "this is exactly the PRE-PATCH register (model_prepatch_register.py): "
                      "the stored copy keeps cmap's own label. The F2P "
                      "test_set_cmap_mismatched_name registers a cmap named "
                      "'test-cmap' under name='wrong-cmap' and asserts "
                      "get_cmap('wrong-cmap').name == 'wrong-cmap'. Without the "
                      "relabel the stored snapshot's name is 'test-cmap' and the F2P "
                      "FAILS. The faithful real patch does NOT resolve (G-DIFF).",
        "rationale": "violates postcondition (R3): reg[name].name == cmap.name, which "
                     "is not provably equal to `name` (they are arbitrary distinct "
                     "tokens). The discriminating relabel is exactly this dropped step.",
    },

    # ATTACK 8 (VALUE-DROP — colorbar_extend not carried into the snapshot). Build
    # the snapshot with a fixed extension flag (False) instead of cmap's, then
    # relabel correctly. CORRECT only when cmap.colorbar_extend is False, WRONG when
    # it is True (reg[name].colorbar_extend == False != cmap.colorbar_extend). Must
    # reject by postcondition (R4).
    {
        "id": "weak-reg-drop-extend",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    # The chosen label is refused if it is already bound, before\n"
            "    # anything is built or stored.\n"
            "    if name in reg:\n"
            "        raise LabelAlreadyBound()\n"
            "    # WRONG: the snapshot is built with a fixed extension flag, not the\n"
            "    # supplied mapping's, though the relabel is performed correctly.\n"
            "    snapshot = Cmap(cmap.name, False, cmap.lut)\n"
            "    snapshot.name = name\n"
            "    reg[name] = snapshot\n"
        ),
        "refinement": "the real register stores cmap.copy(), which preserves "
                      "colorbar_extend; the issue scenario registers a colormap built "
                      "with .with_extremes(over='r') whose extension state must survive "
                      "registration so the stored copy still compares EQUAL to the "
                      "supplied cmap (`cmap_returned == cmap` in "
                      "test_set_cmap_mismatched_name). Hardwiring the flag to False "
                      "makes the stored copy unequal to the supplied cmap and the F2P "
                      "FAILS. The faithful real patch does NOT resolve.",
        "rationale": "violates postcondition (R4): reg[name].colorbar_extend is fixed "
                     "False, not provably equal to cmap.colorbar_extend. The snapshot "
                     "must carry the supplied mapping's observable extension state.",
    },

    # ATTACK 9 (SIDE-WRITE — clobber an UNRELATED registry entry). Perform the
    # correct snapshot + relabel + store, then ALSO bind the snapshot under a
    # second, unrelated label (the audit's atk_5 shape: after the gold hunks,
    # additionally do `self._cmaps["plasma"] = self._cmaps[name]`). All the
    # per-entry postconditions R1..R6 still hold for the chosen label, so this
    # verifies unless the spec carries a registry FRAME clause. Must reject by
    # the frame postconditions (R7/R8): for every k != name, membership is
    # preserved ((k in reg) == Old(k in reg)) and any pre-existing entry keeps
    # its exact bound object (reg[k] is Old(reg[k])). Writing name+1 flips that
    # key's membership when absent, or rebinds it when present — either way a
    # frame clause is violated.
    {
        "id": "weak-reg-side-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    # The chosen label is refused if it is already bound, before\n"
            "    # anything is built or stored.\n"
            "    if name in reg:\n"
            "        raise LabelAlreadyBound()\n"
            "    # WRONG: correct registration PLUS a side-write that rebinds an\n"
            "    # unrelated label to the new snapshot (clobbering whatever mapping\n"
            "    # that label held, or inventing a new entry).\n"
            "    snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)\n"
            "    snapshot.name = name\n"
            "    reg[name] = snapshot\n"
            "    reg[name + 1] = snapshot\n"
        ),
        "refinement": "the real register writes exactly one store key "
                      "(self._cmaps[name] = cmap.copy(), then relabels that same "
                      "stored object). A patch that additionally rebinds another "
                      "registry name — e.g. self._cmaps['plasma'] = self._cmaps[name] "
                      "— hijacks a builtin colormap: hidden tests "
                      "test_double_register_builtin_cmap and test_colormap_invalid "
                      "FAIL (the builtin's identity/content is corrupted). The "
                      "faithful real patch does NOT resolve.",
        "rationale": "violates the registry frame postconditions (R7/R8): for "
                     "k = name + 1 != name, membership/binding is not preserved. "
                     "This is the G-EQ atk_5 counterexample lifted into the battery; "
                     "the frame clauses are exactly what reject it.",
    },

    # ATTACK 9b (REFUSAL-ARM DROP — publish under an ALREADY-BOUND label). Do the
    # correct snapshot + relabel + store UNCONDITIONALLY, i.e. with no refusal at
    # all, so a label that already resolves to a live mapping is silently rebound
    # to a snapshot of the supplied one. CORRECT on every registration under a FREE
    # label (the two agree there), WRONG whenever the label is already bound: the
    # previously stored mapping is destroyed. Must reject by (R9).
    {
        "id": "weak-reg-publish-over-bound-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    # WRONG: no refusal -- publish unconditionally, silently replacing\n"
            "    # whatever mapping the chosen label was already bound to.\n"
            "    snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)\n"
            "    snapshot.name = name\n"
            "    reg[name] = snapshot\n"
        ),
        "refinement": "the real registration REFUSES an already-registered name on its "
                      "default path (`if name in self: if not force: raise ValueError(f'A "
                      "colormap named \"{name}\" is already registered.')`, cm.py:130-136, "
                      "pre-existing at base_commit and untouched by the gold patch). An "
                      "impl that instead overwrites silently changes behaviour the P2P "
                      "test_double_register_builtin_cmap (test_colors.py:140-152) asserts "
                      "— it requires ValueError on exactly this collision — so it clobbers "
                      "registered and builtin colormaps. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "violates postcondition (R9) `not Old(name in reg)`: returning "
                     "normally claims the label was FREE beforehand, which an "
                     "unconditional store cannot establish. The publication has two "
                     "arms and this variant implements only one.",
    },

    # ATTACK 9c (REFUSAL-ARM ABUSE — refuse on EVERY label). Report the out-of-band
    # condition unconditionally and publish nothing at all. CORRECT exactly on the
    # refusal arm (an already-bound label), WRONG on the whole publishing domain:
    # it does no work, so it is the do-nothing cheat the refusal arm would admit if
    # the Exsures did not pin the condition to a genuine collision. Must reject
    # because the exceptional postcondition asserts Old(name in reg).
    {
        "id": "weak-reg-refuse-every-label",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    # WRONG: report the out-of-band condition unconditionally and publish\n"
            "    # nothing, on a FREE label as well as an already-bound one.\n"
            "    raise LabelAlreadyBound()\n"
        ),
        "refinement": "the real registration refuses ONLY an already-registered name; "
                      "under a fresh name it stores the relabelled snapshot (measured: "
                      "register(cmap, name='label-60') on a registry not holding "
                      "'label-60' stores it, with the stored copy's own name equal to "
                      "'label-60'). An impl that always raises registers nothing, so the "
                      "F2P test_set_cmap_mismatched_name — which registers under "
                      "'wrong-cmap' and then looks it up — FAILS. The faithful real patch "
                      "does NOT resolve.",
        "rationale": "violates the EXCEPTIONAL postcondition: Exsures(LabelAlreadyBound, "
                     "... and Old(name in reg) ...) requires that a refusal be reported "
                     "only for a label that WAS already bound, which a refusal on a free "
                     "label cannot establish. This is the do-nothing/no-work probe for "
                     "the arm the refusal added.",
    },

    # ATTACK 9d (REFUSAL-WITH-DAMAGE — refuse, but clobber on the way out). Take the
    # refusal arm correctly for an already-bound label, but ALSO rebind a DIFFERENT
    # label to the newly built snapshot before reporting. The condition is reported
    # exactly when it should be, yet a live binding the refusal exists to protect is
    # destroyed. Must reject by the Exsures' registry frame legs (R10).
    {
        "id": "weak-reg-refuse-but-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    # WRONG: the refusal is reported for the right labels, but a DIFFERENT\n"
            "    # label is clobbered on the way out.\n"
            "    if name in reg:\n"
            "        spoil = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)\n"
            "        reg[name + 1] = spoil\n"
            "        raise LabelAlreadyBound()\n"
            "    snapshot = Cmap(cmap.name, cmap.colorbar_extend, cmap.lut)\n"
            "    snapshot.name = name\n"
            "    reg[name] = snapshot\n"
        ),
        "refinement": "the real registration raises BEFORE `self._cmaps[name] = "
                      "cmap.copy()`, so on the refusal path the store is not written at "
                      "all (measured: after the ValueError the colliding entry is still "
                      "the very same object, with its own name/extend/lut unchanged, and "
                      "no other key is added). An impl that damages any entry while "
                      "refusing corrupts the registry the refusal exists to protect, "
                      "breaking test_double_register_builtin_cmap. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "violates the EXCEPTIONAL postcondition's frame legs (R10): for "
                     "k = name + 1 != name, membership/binding is not preserved on the "
                     "refusal path. Reporting the condition is not sufficient; the "
                     "registry must be left exactly as it was.",
    },

    # ATTACK 10 (VALUE-COLLAPSE on the entrywise relation). Decide entry equality
    # by plain token equality instead of `entry_eq`, i.e. treat an INDETERMINATE
    # entry as equal to an entry carrying the same indeterminate value. CORRECT on
    # every table whose entries are all determinate (the two relations coincide
    # there), WRONG on a table carrying an indeterminate entry: this returns True
    # where (E)'s RHS is False, since seq_eq threads entry_eq, which no entry
    # satisfies against an indeterminate one. The loop is reshaped to a running
    # flag so the variant is self-consistent and the rejection lands on the
    # POSTCONDITION rather than on a stale invariant hint.
    {
        "id": "weak-eq-collapse-indeterminate-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    if self.colorbar_extend != other.colorbar_extend:\n"
            "        return False\n"
            "    if len(self.lut) != len(other.lut):\n"
            "        Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))\n"
            "        Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))\n"
            "        return False\n"
            "    i = 0\n"
            "    all_tokens_match = True\n"
            "    while i < len(self.lut):\n"
            "        # invariants-start\n"
            "        Invariant(Acc(self.lut, 1 / 2) and Acc(list_pred(self.lut), 1 / 2))\n"
            "        Invariant(Acc(other.lut, 1 / 2) and Acc(list_pred(other.lut), 1 / 2))\n"
            "        Invariant(len(self.lut) == len(other.lut))\n"
            "        Invariant(0 <= i and i <= len(self.lut))\n"
            "        Invariant(MustTerminate(len(self.lut) - i + 1))\n"
            "        # invariants-end\n"
            "        # WRONG: plain token equality ignores whether the entry carries a\n"
            "        # determinate value at all.\n"
            "        if self.lut[i] != other.lut[i]:\n"
            "            all_tokens_match = False\n"
            "        i = i + 1\n"
            "    return all_tokens_match\n"
        ),
        "refinement": "the real lookup tables are float arrays compared elementwise, "
                      "and an entry holding no determinate numeric value compares "
                      "unequal to every entry — itself included — so a table carrying "
                      "one is equal to NO table. An impl deciding entries by plain "
                      "token identity reports such a pair EQUAL where the real "
                      "comparison reports unequal, so it diverges from the real callee "
                      "on every table reachable through the documented "
                      "set-the-extremes API. The faithful real patch does NOT resolve.",
        "rationale": "violates postcondition (E): on a pair of tables carrying an "
                     "indeterminate entry at the same index with the same value, this "
                     "returns True while (E)'s RHS is False, because seq_eq threads "
                     "entry_eq and entry_eq holds of no indeterminate entry.",
    },

    # ATTACK 11 (CARRIER-COLLAPSE on the extension flag). Compare only whether each
    # flag is the zero value rather than comparing the flag values, collapsing the
    # flag's multi-valued domain to two classes. CORRECT whenever both flags are
    # zero or both are the same nonzero value, WRONG on two DISTINCT nonzero flag
    # values with equal tables (Result()==True but (E)'s RHS==False). Must reject by
    # postcondition (E), which compares the flags themselves.
    {
        "id": "weak-eq-collapse-extend-carrier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    # WRONG: only the flag's zero/nonzero class is compared, not the flag.\n"
            "    sa = 0\n"
            "    if self.colorbar_extend != 0:\n"
            "        sa = 1\n"
            "    sb = 0\n"
            "    if other.colorbar_extend != 0:\n"
            "        sb = 1\n"
            "    if sa != sb:\n"
            "        return False\n"
            "    if len(self.lut) != len(other.lut):\n"
            "        Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))\n"
            "        Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))\n"
            "        return False\n"
            + _EQ_LOOP_AND_TAIL
        ),
        "refinement": "the real comparison tests the extension flags themselves, and "
                      "the flag's documented value domain holds several mutually "
                      "distinguishable values, all reachable through the documented "
                      "public attribute. Two mappings carrying DIFFERENT such values "
                      "with identical tables are unequal for the real callee; an impl "
                      "that only distinguishes the zero value from the rest reports "
                      "them equal. The faithful real patch does NOT resolve.",
        "rationale": "violates postcondition (E): with two distinct nonzero flag "
                     "values and equal tables, Result() is True but "
                     "(self.colorbar_extend == other.colorbar_extend) is False.",
    },

    # ATTACK 12 (CARRIER-COLLAPSE on the stored flag, register site). Carry only the
    # supplied flag's zero/nonzero class into the snapshot instead of the flag value.
    # CORRECT whenever the supplied flag is zero or one, WRONG for any other flag
    # value. Must reject by postcondition (R4).
    {
        "id": "weak-reg-collapse-extend-carrier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    # The chosen label is refused if it is already bound, before\n"
            "    # anything is built or stored.\n"
            "    if name in reg:\n"
            "        raise LabelAlreadyBound()\n"
            "    # WRONG: only the flag's zero/nonzero class is carried into the\n"
            "    # snapshot, not the supplied mapping's flag value.\n"
            "    se = 0\n"
            "    if cmap.colorbar_extend != 0:\n"
            "        se = 1\n"
            "    snapshot = Cmap(cmap.name, se, cmap.lut)\n"
            "    snapshot.name = name\n"
            "    reg[name] = snapshot\n"
        ),
        "refinement": "the real register stores cmap.copy(), which carries the whole "
                      "__dict__ across and so preserves the extension flag's exact "
                      "value, not merely whether it is set. A stored snapshot that "
                      "kept only the flag's zero/nonzero class would no longer compare "
                      "equal to the supplied mapping whenever that mapping carries any "
                      "other flag value — breaking the registered-copy-equals-supplied "
                      "property the F2P asserts. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "violates postcondition (R4): reg[name].colorbar_extend is the "
                     "collapsed class, not provably equal to cmap.colorbar_extend for "
                     "a flag value outside {0, 1}.",
    },

    # ATTACK 13 (UNGROUNDED-ORACLE ECHO). Derive the verdict from cheap properties
    # of the arguments — flag equality plus table LENGTH — without ever performing
    # the entrywise comparison. CORRECT on every same-length pair whose entries all
    # agree, WRONG on any same-length pair differing in an entry. Must reject by
    # postcondition (E): returning True needs seq_eq over the full sequences, which
    # nothing here establishes.
    {
        "id": "echo-eq-length-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    # ECHO: the verdict is read off the arguments' shape; no entrywise\n"
            "    # comparison is ever performed.\n"
            "    if self.colorbar_extend != other.colorbar_extend:\n"
            "        return False\n"
            "    if len(self.lut) != len(other.lut):\n"
            "        Assert(len(ToSeq(self.lut)) != len(ToSeq(other.lut)))\n"
            "        Assert(not seq_eq(ToSeq(self.lut), ToSeq(other.lut)))\n"
            "        return False\n"
            "    return True\n"
        ),
        "refinement": "the real comparison decides table equality elementwise over the "
                      "whole array; two equal-length tables differing in any entry are "
                      "unequal. An impl answering from the lengths alone reports every "
                      "same-length pair equal, so the F2P's mutated-table assertion "
                      "(equal shapes, changed contents) reads EQUAL and fails. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "violates postcondition (E): to return True the spec demands "
                     "seq_eq over the FULL sequences; equal length establishes none of "
                     "the entrywise facts, so True cannot be proven. This is the "
                     "ungrounded-oracle slot: the answer is derived from the arguments "
                     "rather than from the work.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — A-reference deep models grounded in the REAL matplotlib callee.
#
# meta.json has axioms == [] (NO consumed @ContractOnly axiom): both behaviours
# are modelled DEEPLY. The two kind-A entries are A-REFERENCES (refinement.md §C):
#   (1) colormaps_equal / seq_eq  ==  the real Colormap.__eq__ (post-gold:
#       label-free, colorbar_extend-equal AND np.array_equal(_lut, _lut));
#   (2) register_named / Cmap-copy == the real ColormapRegistry.register
#       (post-gold: independent snapshot relabelled to the registration name) +
#       Colormap.copy().
# There is NO @ContractOnly axiom whose Requires domain a caller could escape, so
# there is no separate axiom-containment obligation (no axiom domain exists). The
# single callee-level obligation is that each deep model EQUALS the real callee on
# every caller-reachable input — exactly what the bundle's host-validated G-AX
# oracle (axiom_check.py) checks against REAL matplotlib (boundary + 4000 + 300
# fuzz). We re-run that oracle IN-CONTAINER (apply_gold=True, so the real callees
# are post-gold) as the axiom-lane probe, embedding axiom_check.py verbatim from
# the HOST at load (the runner mounts ONLY the probe script). It imports only the
# stdlib + matplotlib (the very package the gold patch edits), CALLS the real
# callees (never scrapes source), and reads no files (no utf-8 codec concern).
# ---------------------------------------------------------------------------
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-eq-and-register",
        "axiom": "Colormap.__eq__ label-free (A-ref 1) + register snapshot-relabel (A-ref 2)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness/containment: the model's two deep "
                     "characterisations must equal the REAL post-gold matplotlib "
                     "callees on every input the model can reach — (1) "
                     "Colormap.__eq__ is colorbar_extend-equal AND "
                     "np.array_equal(_lut) with the LABEL irrelevant (equal copy, "
                     "relabelled copy [the fix => equal], flipped extension, "
                     "mutated/truncated lut, non-Colormap comparand, + 4000 fuzz); "
                     "(2) register stores an independent snapshot under the "
                     "registration name whose own .name equals that name regardless "
                     "of the supplied label, the supplied cmap untouched, the snapshot "
                     "EQUAL to it (the issue's exact viridis/with_extremes scenario + "
                     "300 fuzz pairs). Exit 0 iff every observation is sound; any "
                     "mismatch => the A-reference is unsound. No @ContractOnly axiom "
                     "and no caller-reachable input outside any axiom domain (no axiom "
                     "domain exists).",
    },
]
