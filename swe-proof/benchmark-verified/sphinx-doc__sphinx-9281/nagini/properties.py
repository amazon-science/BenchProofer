"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-9281.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. One function is under spec:

    describe(value: Value) -> List[int]
        # every field of `value` is held READ-ONLY:
        Requires(Acc(value.kind, 1/2)); Requires(Acc(value.class_name, 1/2)); ...
        Requires(Acc(list_pred(value.class_name), 1/2)); ... (member/category/fallback)
        Requires(MustTerminate(2))   # total correctness: the rendering must ANSWER
        Ensures (Acc(list_pred(Result())))
        Ensures (Implies(value.kind == 3,
                         ToSeq(Result()) == enum_rendering(ToSeq(value.class_name),
                                                           ToSeq(value.member_name))))
        Ensures (Implies(value.kind == 0, ToSeq(Result()) == ToSeq(value.category_text)))
        Ensures (Implies(value.kind == 1, ToSeq(Result()) == ToSeq(value.category_text)))
        Ensures (Implies(value.kind == 2, ToSeq(Result()) == ToSeq(value.category_text)))
        Ensures (Implies(value.kind == 4, ToSeq(Result()) == ToSeq(value.fallback_text)))

What the spec actually defends, and the attacks it must survive:

  * The LOAD-BEARING, discriminating clause is the `kind == 3` pin:
    `ToSeq(Result()) == enum_rendering(ToSeq(class_name), ToSeq(member_name))`
    where `enum_rendering(c, m) = c + dot() + m` and `dot() = PSeq(46)` (U+002E
    '.'). This is the behaviour the F2P test observes: an `enum.Enum` member
    renders as owning-type-name "." member-name (`MyEnum.FOO == "MyEnum.FOO"`),
    NOT as the generic value-revealing repr fallback (pre-patch `<MyEnum.FOO: 1>`).
    The pre-patch code had NO enum arm, so an enum member fell through to the
    `repr` fallback (`value.fallback_text`); `model_prepatch.py` reproduces that
    and FAILS this very clause (G-DIFF).

  * The oracle is GROUNDED, not an answer-key marker: `enum_rendering` /`dot` are
    @Pure functions OF the input args (`class_name + dot() + member_name`), fully
    unfolded by Viper. There is no opaque marker to echo and no executable
    materialisation of a @Pure PSeq that bypasses the per-element copy/append
    work — the only way to satisfy the `kind == 3` pin is to actually build
    `class_name ++ '.' ++ member_name`. So there is no "wrong oracle echo that
    verifies"; the ungrounded-oracle lane is discharged by an honest positive
    control (`echo-honest`) that re-asserts the pin redundantly (it must verify).

  * EVERY `value.*` field is held READ-ONLY (Acc(value.x, 1/2) AND
    Acc(list_pred(value.x), 1/2), required AND ensured). The mandatory attack is
    FRAME MUTATION (`frame-mutate-member`): an impl that WRITES into
    `value.member_name` (a 1/2 read-only list) to steer/short-circuit the pin
    must fail for INSUFFICIENT PERMISSION (a list-element store needs FULL
    list_pred permission). The gold invariants/Asserts are kept verbatim so the
    rejection is attributable solely to the write.

  * The collection arms (kind 0/1/2) and the generic fallback (kind 4) are
    UNCHANGED behaviour, carried as opaque carrier sequences (`category_text`,
    `fallback_text`); the spec only requires the function reproduce them. The
    structurally-different positive controls reorder the dispatch / disjunction
    (all branches are mutually exclusive on `kind`, so the decision is identical)
    while keeping every gold invariant/Assert — so the gold proof still closes.

  * The one control-flow-effect channel Nagini's default partial-correctness
    semantics leaves open is DIVERGENCE (never reaching a return, so every
    Ensures holds vacuously). The spec closes it with Requires(MustTerminate(2))
    (consumed in each copy loop by an Invariant(MustTerminate(<remaining>))
    measure), and the `w-diverge` rival below pins the rejection. This was the
    audit's P1 witness (atk_8): an endless loop sharing the spec verified under
    the pre-fix contract.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside the `# impl-start`/`# impl-end` region (the per-loop
invariants live there too). `markers.same_spec` elides every impl span (incl.
the nested invariants), so a rejection comes from the POSTCONDITION catching
wrong behaviour (or the permission system), never from a tampered spec. Each
`expect:"reject"` rival carries the refinement argument that its faithful real
patch would NOT resolve the F2P (`test_object_description_enum`).

AXIOM LANE: the bundle consumes NO @ContractOnly axiom (meta.axioms == []). The
only modelled callee is the A-reference deep model `enum_rendering`, validated
== the real gold rendering `"%s.%s" % (cls.__name__, member.name)` by
axiom_check.py / G-AX. Per PBT_PLAN §4 (A-reference deep models are checked the
same way) we persist that as an axiom-soundness probe (`enum_rendering` vs the
REAL `enum.Enum` member rendering over boundary + randomized real Enum classes)
and a caller-domain containment probe (every code-point sequence the model can
pass to `enum_rendering` is exactly an arbitrary Unicode-code-point list — a
class/member name — which is precisely what the real callee receives). The
probe imports only the stdlib `enum` module (the same module the patch
dispatches on) and is self-contained, so it runs in any instance image.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9281"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl region of describe.
# ---------------------------------------------------------------------------

# The collection-arm dispatch condition (impl region) and its matching loop
# invariant disjunction (also impl region).
_COLL_COND = "    if value.kind == 0 or value.kind == 1 or value.kind == 2:  # type: ignore\n"
_COLL_INV = "            Invariant(value.kind == 0 or value.kind == 1 or value.kind == 2)  # type: ignore\n"

# The '.' separator append in the enum branch.
_DOT_APPEND = "        result.append(46)  # '.'\n"

# The member-name copy append in the enum branch (the read of a 1/2 list).
_MEMBER_APPEND = "            result.append(value.member_name[j])  # type: ignore\n"

# The member-name copy-loop guard in the enum branch.
_MEMBER_GUARD = "        while j < len(value.member_name):  # type: ignore\n"

# The final gold pin Assert in the enum branch (redundant-assert anchor).
_ENUM_FINAL_ASSERT = (
    "        Assert(ToSeq(result) ==\n"
    "               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore\n"
    "        return result\n"
)

# The WHOLE enum branch verbatim (for the enum-as-fallback pre-patch rival).
_ENUM_BRANCH = (
    "    elif value.kind == 3:  # type: ignore\n"
    "        i = 0\n"
    "        while i < len(value.class_name):  # type: ignore\n"
    "            # invariants-start\n"
    "            Invariant(Acc(value.kind, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(value.kind == 3)  # type: ignore\n"
    "            Invariant(0 <= i and i <= len(value.class_name))  # type: ignore\n"
    "            Invariant(ToSeq(result) == ToSeq(value.class_name).take(i))  # type: ignore\n"
    "            # The loop consumes the termination obligation: the remaining\n"
    "            # count is the strictly decreasing, bounded-below measure.\n"
    "            Invariant(MustTerminate(len(value.class_name) - i))  # type: ignore\n"
    "            # invariants-end\n"
    "            result.append(value.class_name[i])  # type: ignore\n"
    "            i = i + 1\n"
    "        Assert(i == len(value.class_name))  # type: ignore\n"
    "        Assert(ToSeq(value.class_name).take(i) == ToSeq(value.class_name))  # type: ignore\n"
    "        result.append(46)  # '.'\n"
    "        Assert(ToSeq(result) == ToSeq(value.class_name) + dot())  # type: ignore\n"
    "        j = 0\n"
    "        while j < len(value.member_name):  # type: ignore\n"
    "            # invariants-start\n"
    "            Invariant(Acc(value.kind, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(value.kind == 3)  # type: ignore\n"
    "            Invariant(0 <= j and j <= len(value.member_name))  # type: ignore\n"
    "            Invariant(ToSeq(result) ==\n"
    "                      ToSeq(value.class_name) + dot() + ToSeq(value.member_name).take(j))  # type: ignore\n"
    "            # The loop consumes the termination obligation: the remaining\n"
    "            # count is the strictly decreasing, bounded-below measure.\n"
    "            Invariant(MustTerminate(len(value.member_name) - j))  # type: ignore\n"
    "            # invariants-end\n"
    "            result.append(value.member_name[j])  # type: ignore\n"
    "            j = j + 1\n"
    "        Assert(j == len(value.member_name))  # type: ignore\n"
    "        Assert(ToSeq(value.member_name).take(j) == ToSeq(value.member_name))  # type: ignore\n"
    "        Assert(ToSeq(result) ==\n"
    "               ToSeq(value.class_name) + dot() + ToSeq(value.member_name))  # type: ignore\n"
    "        Assert(ToSeq(result) ==\n"
    "               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore\n"
    "        return result\n"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (S1) Structurally-different but CORRECT: the collection-arm membership
# disjunction is reordered to `value.kind == 2 or value.kind == 1 or
# value.kind == 0` in BOTH the dispatch condition AND its loop invariant
# (membership in {0,1,2} is order-independent). All loops/Asserts/invariants are
# otherwise verbatim, so the gold proof still closes. If this fails to verify,
# the postcondition is over-fit to the literal disjunction order => SPEC-TOO-STRONG.
_COLL_COND_REORDER = "    if value.kind == 2 or value.kind == 1 or value.kind == 0:  # type: ignore\n"
_COLL_INV_REORDER = "            Invariant(value.kind == 2 or value.kind == 1 or value.kind == 0)  # type: ignore\n"
_POS_DISJ_REORDER = _swap(
    _swap(_BASE, _COLL_COND, _COLL_COND_REORDER),
    _COLL_INV, _COLL_INV_REORDER,
)

# (S2) ECHO-HONEST. The oracle (`enum_rendering`) is GROUNDED in the input args,
# so the only way to satisfy the `kind == 3` pin is to actually build
# `class_name ++ '.' ++ member_name`; there is no executable materialisation of
# the @Pure PSeq to echo. This control inserts ONE extra redundant Assert right
# before the gold final Assert, re-stating the pin verbatim. It is redundant with
# the gold loop proof and MUST verify. It demonstrates the spec is NOT
# echo-vulnerable (else there would be a wrong echo to reject here).
_ENUM_FINAL_ASSERT_ECHO = (
    "        Assert(ToSeq(result) ==\n"
    "               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore\n"
    "        Assert(ToSeq(result) ==\n"
    "               enum_rendering(ToSeq(value.class_name), ToSeq(value.member_name)))  # type: ignore\n"
    "        return result\n"
)
_ECHO_HONEST = _swap(_BASE, _ENUM_FINAL_ASSERT, _ENUM_FINAL_ASSERT_ECHO)

# (S3) ADMISSIBILITY. In-region witness that the spec admits and pins the
# F2P-shaped input: at the top of the impl, Assert that the oracle
# `enum_rendering` on the code points of "MyEnum" / "FOO" is derivable and
# equals the code points of "MyEnum.FOO" (77,121,69,110,117,109 '.'
# 70,79,79). This is the exact value the F2P test observes. If this Assert
# cannot discharge, the @Pure spec definitions are contradictory or unusable
# on a normal enum-shaped input => PRECOND-TOO-STRONG / SPEC-UNUSABLE. The
# rest of the gold impl is untouched so the postcondition still discharges.
# (A describe/Value self-call probe is no longer usable here: under the
# MustTerminate obligation a same-measure reentrant call is itself an
# obligation violation, which would shadow the admissibility signal.)
_IMPL_HEAD = "    result = []  # type: List[int]\n"
_IMPL_HEAD_ADMISS = (
    "    Assert(enum_rendering(PSeq(77, 121, 69, 110, 117, 109),\n"
    "                          PSeq(70, 79, 79)) ==\n"
    "           PSeq(77, 121, 69, 110, 117, 109, 46, 70, 79, 79))  # 'MyEnum.FOO'\n"
    "    result = []  # type: List[int]\n"
)
_ADMISS = _swap(_BASE, _IMPL_HEAD, _IMPL_HEAD_ADMISS)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (U1) FRAME MUTATION — MANDATORY, the #1 weakness class. Every `value.*` field
# is read-only (Acc(value.x, 1/2) and Acc(list_pred(value.x), 1/2)). This rival
# WRITES into `value.member_name[j]` (the read-only member-name list) right
# before copying it, to try to satisfy/steer the pin on a self-mutated input.
# Under 1/2 permission a list-element store requires FULL list_pred permission,
# so it MUST fail for INSUFFICIENT PERMISSION (not a value mismatch). The gold
# invariants/Asserts are kept verbatim around it, so the failure is attributable
# solely to the write. Rejection source: the PERMISSION SYSTEM.
_MEMBER_APPEND_FRAME = (
    "            value.member_name[j] = 65  # type: ignore   # write to a 1/2 read-only list\n"
    "            result.append(value.member_name[j])  # type: ignore\n"
)
_RIVAL_FRAME = _swap(_BASE, _MEMBER_APPEND, _MEMBER_APPEND_FRAME)

# (U2) THE DISCRIMINATING BUG / partial-domain. This rival makes an enum member
# (kind == 3) render as the generic `repr` FALLBACK (`value.fallback_text`) — the
# exact pre-patch behaviour: pre-gold object_description had NO enum arm, so an
# enum member fell through to `repr(object)` (the ugly value-revealing form).
# This is model_prepatch.py. On the kind∈{0,1,2,4} sub-domain it agrees with
# gold; it diverges precisely on the enum input the F2P test feeds. Its faithful
# real patch is the pre-patch code, which FAILS test_object_description_enum
# (`object_description(MyEnum.FOO)` returns `<MyEnum.FOO: 1>` not `"MyEnum.FOO"`)
# — it would NOT resolve. Rejection source: the `kind == 3` postcondition clause
# `ToSeq(Result()) == enum_rendering(...)`; the impl returns `fallback_text`,
# which the verifier cannot prove equal to `class_name ++ '.' ++ member_name`.
_ENUM_BRANCH_AS_FALLBACK = (
    "    elif value.kind == 3:  # type: ignore\n"
    "        i = 0\n"
    "        while i < len(value.fallback_text):  # type: ignore\n"
    "            # invariants-start\n"
    "            Invariant(Acc(value.kind, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.class_name, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.member_name, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.category_text, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(value.fallback_text, 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.class_name), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.member_name), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.category_text), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(value.fallback_text), 1 / 2))  # type: ignore\n"
    "            Invariant(Acc(list_pred(result)))\n"
    "            Invariant(value.kind == 3)  # type: ignore\n"
    "            Invariant(0 <= i and i <= len(value.fallback_text))  # type: ignore\n"
    "            Invariant(ToSeq(result) == ToSeq(value.fallback_text).take(i))  # type: ignore\n"
    "            # the rival's loop is bounded and carries a proper measure, so\n"
    "            # its rejection is attributable to the kind==3 postcondition,\n"
    "            # NOT to a termination-obligation leak.\n"
    "            Invariant(MustTerminate(len(value.fallback_text) - i))  # type: ignore\n"
    "            # invariants-end\n"
    "            result.append(value.fallback_text[i])  # type: ignore\n"
    "            i = i + 1\n"
    "        Assert(i == len(value.fallback_text))  # type: ignore\n"
    "        Assert(ToSeq(value.fallback_text).take(i) == ToSeq(value.fallback_text))  # type: ignore\n"
    "        return result\n"
)
_RIVAL_ENUM_AS_FALLBACK = _swap(_BASE, _ENUM_BRANCH, _ENUM_BRANCH_AS_FALLBACK)

# (U3) WRONG SEPARATOR / partial-domain near-miss with refinement. The enum arm
# joins with code point 47 ('/') instead of 46 ('.'). It agrees with gold only on
# enum members whose rendering is unaffected by the separator (none, since every
# enum rendering contains exactly one separator). A faithful real patch emitting
# `"%s/%s"` would render `MyEnum/FOO` and FAIL test_object_description_enum
# (which pins `MyEnum.FOO`) — it would NOT resolve. Rejection source: the gold
# Assert `ToSeq(result) == ToSeq(value.class_name) + dot()` (dot() == PSeq(46))
# fails after appending 47, and the `kind == 3` postcondition is violated.
_DOT_APPEND_WRONG = "        result.append(47)  # wrong separator '/'\n"
_RIVAL_WRONG_SEP = _swap(_BASE, _DOT_APPEND, _DOT_APPEND_WRONG)

# (U4) CLASS-NAME-ONLY / partial-domain. The member-name copy loop is neutered
# (guard `while j < 0:`), so the enum rendering becomes just `class_name ++ '.'`
# — the member name is dropped. It agrees with gold only when the member name is
# empty (never, for a real enum member). A faithful real patch emitting
# `"%s." % cls.__name__` would render `MyEnum.` and FAIL
# test_object_description_enum (which pins `MyEnum.FOO`) — it would NOT resolve.
# Rejection source: the gold Assert `ToSeq(value.member_name).take(j) ==
# ToSeq(value.member_name)` (with j stuck at 0) and the final enum postcondition
# clause both fail when member_name is non-empty.
_MEMBER_GUARD_NEUTERED = "        while j < 0:  # type: ignore   # drop the member name\n"
_RIVAL_CLASS_ONLY = _swap(_BASE, _MEMBER_GUARD, _MEMBER_GUARD_NEUTERED)

# (U5) CONTROL-FLOW-EFFECT (vacuity): DIVERGE instead of returning. The rival
# replaces the WHOLE impl region with an endless loop before any return: no
# normal exit is ever reached, so every Ensures (including the kind==3 pin)
# holds vacuously under Nagini's default partial-correctness semantics. This
# was the audit P1 witness (atk_8-class vacuity hole): under the pre-fix
# contract (no MustTerminate) it VERIFIED while sharing the spec.
# Rejection source: the MustTerminate(2) obligation in the pre-conditions —
# the endless loop carries no termination measure, so Nagini reports an
# obligation leak instead of accepting the vacuous proof.
_IMPL_MARKER = "    # impl-start\n"
_RIVAL_DIVERGE = _BASE[: _BASE.index(_IMPL_MARKER)] + (
    "    # impl-start\n"
    "    result = []  # type: List[int]\n"
    "    while True:\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        pass\n"
    "    # impl-end\n"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-disj-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_DISJ_REORDER,
     "rationale": "structurally-different but CORRECT: the collection-arm membership "
                  "disjunction is reordered to `2 or 1 or 0` in both the dispatch condition "
                  "and its loop invariant (membership in {0,1,2} is order-independent). All "
                  "loops/Asserts/invariants otherwise verbatim => the gold proof still closes. "
                  "If it fails to verify, the postcondition is over-fit to the literal "
                  "disjunction order => SPEC-TOO-STRONG."},
    {"id": "echo-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the oracle (enum_rendering) is GROUNDED in the input args, so the only way "
                  "to satisfy the kind==3 pin is to actually build class_name ++ '.' ++ "
                  "member_name; there is no executable materialisation of the @Pure PSeq to "
                  "echo. This inserts one extra redundant Assert re-stating the pin verbatim, "
                  "redundant with the gold loop proof => must verify. Demonstrates the spec is "
                  "NOT echo-vulnerable (else this would be a reject case)."},
    {"id": "admiss-enum-shaped", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "in-region witness that the spec admits and pins the F2P-shaped input: "
                  "Assert(enum_rendering('MyEnum' code points, 'FOO' code points) == "
                  "'MyEnum.FOO' code points) must discharge from the @Pure definitions "
                  "alone. If it cannot, the spec is contradictory/unusable on a normal "
                  "enum-shaped input => PRECOND-TOO-STRONG / SPEC-UNUSABLE."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "frame-mutate-member", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FRAME,
     "refinement": "no faithful real patch corresponds to this: object_description only READS "
                   "its argument to format it (`object.name`, `object.__class__.__name__`); it "
                   "never mutates the value's member name. The rival exists solely to test "
                   "whether the read-only (1/2) precondition can be subverted by writing into "
                   "value.member_name. There is no resolving patch that overwrites the input "
                   "member-name characters, so a verifying rival here would be a pure "
                   "verify⇏resolve artifact (vacuous satisfaction via self-mutation).",
     "rationale": "MANDATORY frame-mutation probe. `value.member_name[j] = 65` writes through a "
                  "1/2 (read-only) list reference and MUST fail for insufficient permission "
                  "(an element store needs FULL list_pred). Rejection source: the PERMISSION "
                  "SYSTEM, not a value mismatch; the gold invariants/Asserts are kept verbatim. "
                  "If it verified => SPEC-TOO-WEAK (frame protection hollow)."},
    {"id": "rival-enum-as-fallback", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ENUM_AS_FALLBACK,
     "refinement": "renders an enum member (kind==3) as the generic repr FALLBACK "
                   "(value.fallback_text) — exactly the pre-patch behaviour (no enum arm, so an "
                   "enum member fell through to repr(object)) and model_prepatch.py. Its "
                   "faithful real patch is the pre-patch object_description, which FAILS "
                   "test_object_description_enum (object_description(MyEnum.FOO) returns "
                   "'<MyEnum.FOO: 1>' not 'MyEnum.FOO') — it would NOT resolve.",
     "rationale": "the discriminating bug + partial-domain. Rejection source: the kind==3 "
                  "postcondition clause `ToSeq(Result()) == enum_rendering(ToSeq(class_name), "
                  "ToSeq(member_name))`; the impl returns fallback_text, which the verifier "
                  "cannot prove equal to class_name ++ '.' ++ member_name. If it verified => "
                  "SPEC-TOO-WEAK (admits the pre-patch fall-through bug)."},
    {"id": "rival-wrong-separator", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONG_SEP,
     "refinement": "joins class_name and member_name with code point 47 ('/') instead of 46 "
                   "('.'). A faithful real patch emitting `\"%s/%s\" % (...)` would render "
                   "`MyEnum/FOO` and FAIL test_object_description_enum (which pins "
                   "`MyEnum.FOO`) — it would NOT resolve.",
     "rationale": "partial-domain near-miss with a real refinement. Rejection source: the gold "
                  "Assert `ToSeq(result) == ToSeq(value.class_name) + dot()` (dot() == PSeq(46)) "
                  "fails after appending 47, and the kind==3 postcondition is violated. If it "
                  "verified => SPEC-TOO-WEAK (separator not pinned)."},
    {"id": "rival-class-name-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_CLASS_ONLY,
     "refinement": "neuters the member-name copy loop (guard `while j < 0:`), so the enum "
                   "rendering is just `class_name ++ '.'` — the member name is dropped. A "
                   "faithful real patch emitting `\"%s.\" % cls.__name__` would render `MyEnum.` "
                   "and FAIL test_object_description_enum (which pins `MyEnum.FOO`) — it would "
                   "NOT resolve.",
     "rationale": "partial-domain (drops the member name). Rejection source: the kept gold "
                  "Assert `ToSeq(value.member_name).take(j) == ToSeq(value.member_name)` (j "
                  "stuck at 0) and the final enum postcondition clause both fail when "
                  "member_name is non-empty. If it verified => SPEC-TOO-WEAK (member name not "
                  "pinned)."},
    {"id": "w-diverge", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE,
     "refinement": "a real patch whose object_description spins forever (an accidental "
                   "infinite loop before assembling/returning the description) never "
                   "returns; describing any value hangs, so the F2P "
                   "test_object_description_enum and every unchanged collection/fallback "
                   "P2P case time out — it does NOT resolve.",
     "rationale": "CONTROL-FLOW-EFFECT / vacuity rival: the whole impl is an endless loop "
                  "before any return, so every Ensures (incl. the kind==3 pin) holds "
                  "vacuously under partial-correctness semantics — this VERIFIED under the "
                  "pre-fix contract (the audit's P1 witness, atk_8 class). Rejection "
                  "source: the MustTerminate(2) termination obligation in the "
                  "pre-conditions; the loop takes no termination measure, so Nagini "
                  "reports an obligation leak. If it verified => SPEC-TOO-WEAK "
                  "(divergence admitted)."},
]


# ===========================================================================
# AXIOM LANE — A-reference deep model `enum_rendering` (meta.axioms == []; the
# only modelled callee is the A-reference deep model validated by G-AX). Per
# PBT_PLAN §4, A-reference deep models are checked the same way as axioms: the
# deep model must equal the real callee on every caller-reachable input.
# ===========================================================================

# Embed the bundle oracle (axiom_check.py) reference behaviour directly so the
# probe is self-contained (the runner mounts only the probe at /work; model.py /
# axiom_check.py are NOT in-container). The probe imports only the stdlib `enum`
# module (the very module the gold patch dispatches on).

_AX_SOUND_PROBE = r'''
import enum, random, string, sys

def dot():
    # model.py pure helper `dot`: the single separator code point U+002E.
    return [46]

def enum_rendering(class_name, member_name):
    # model.py deep model: owning-type name ++ '.' ++ member name (code points).
    return list(class_name) + dot() + list(member_name)

def real_gold_rendering(member):
    # the REAL rendering the gold patch emits for an enum member:
    #   "%s.%s" % (member.__class__.__name__, member.name)
    text = "%s.%s" % (member.__class__.__name__, member.name)
    return [ord(ch) for ch in text]

def check_member(member):
    class_name = [ord(ch) for ch in member.__class__.__name__]
    member_name = [ord(ch) for ch in member.name]
    expected = real_gold_rendering(member)              # real callee/formatting
    observed = enum_rendering(class_name, member_name)  # deep model
    assert observed == expected, (
        "enum_rendering deep model UNSOUND on %r: gold %r != deep model %r"
        % (member, expected, observed))
    assert observed == class_name + [46] + member_name
    assert chr(46) == "."

def main():
    # --- boundary cases: the issue's own example + edges --------------------
    class MyEnum(enum.Enum):
        FOO = 1
        BAR = 2
    class ValuedEnum(enum.Enum):
        ValueA = 10
        ValueB = 20
    class StrEnum(enum.Enum):
        A = "alpha"
        B = "beta"
    class SingleMember(enum.Enum):
        ONLY = object()
    class IntEnumK(enum.IntEnum):
        X = 1
        Y = 2
    class Underscored(enum.Enum):
        Mixed_Case_99 = 2

    boundary = [
        MyEnum.FOO, MyEnum.BAR,
        ValuedEnum.ValueA, ValuedEnum.ValueB,
        StrEnum.A, StrEnum.B,
        SingleMember.ONLY,
        IntEnumK.X, IntEnumK.Y,
        Underscored.Mixed_Case_99,
    ]
    for m in boundary:
        check_member(m)
        # The pre-patch fall-through (repr) MUST differ from the gold rendering
        # wherever the default Enum repr applies (the behaviour the F2P observes).
        r = repr(m)
        if "=" in r or ":" in r:
            assert real_gold_rendering(m) != [ord(c) for c in r], (
                "gold rendering must differ from the ugly repr for %r" % (m,))

    # --- randomized fuzz: many freshly-built real Enum classes --------------
    rng = random.Random(9281)
    start = string.ascii_letters + "_"
    rest = string.ascii_letters + string.digits + "_"
    def ident():
        n = rng.randint(1, 12)
        s = rng.choice(start) + "".join(rng.choice(rest) for _ in range(n - 1))
        return s
    n_classes = 5000
    for _ in range(n_classes):
        cname = ident()
        k = rng.randint(1, 4)
        members = {}
        used = set()
        while len(members) < k:
            mname = ident()
            if mname in used or mname.startswith("_") or mname.endswith("_"):
                continue
            used.add(mname)
            members[mname] = len(members) + 1
        EnumCls = enum.Enum(cname, members)
        for mname in members:
            check_member(EnumCls[mname])

    print("AX-SOUND OK: enum_rendering deep model == real "
          "'%%s.%%s'%%(cls.__name__, member.name) on %d boundary + %d randomized "
          "real enum.Enum classes" % (len(boundary), n_classes))
    sys.exit(0)

main()
'''

_AX_CONTAIN_PROBE = r'''
import enum, random, string, sys

# CONTAINMENT (AXIOM-TOO-WEAK-FOR-CALLER check, recast for the A-reference deep
# model). The model passes enum_rendering EXACTLY two arguments:
#   class_name = ToSeq(value.class_name), member_name = ToSeq(value.member_name)
# i.e. arbitrary List[int] of Unicode code points (the code points of the
# owning-type name and the member name). enum_rendering's "domain" is the FULL
# space of code-point sequences (PSeq[int]) — it is a total @Pure fold with no
# Requires restriction (mapping.md: class_name/member_name are arbitrary
# List[int]). So every input the model can reach is trivially in the deep
# model's domain. We confirm CONTAINMENT operationally: for real enum.Enum
# members, the code-point sequences the model would feed (ord*(cls.__name__),
# ord*(member.name)) are exactly the sequences the deep model is total over, and
# the real callee accepts them — there is no caller-reachable input outside the
# deep model's domain. (Covering MORE than the caller reaches would be SOUND, not
# a defect; here the domain is the whole code-point-sequence space, so coverage
# is exact-or-superset by construction.)

def is_codepoint_list(xs):
    return isinstance(xs, list) and all(isinstance(x, int) and 0 <= x <= 0x10FFFF for x in xs)

def main():
    rng = random.Random(92810)
    start = string.ascii_letters + "_"
    rest = string.ascii_letters + string.digits + "_"
    # include a non-ASCII glyph to exercise the full Unicode-code-point range the
    # model's PSeq[int] domain admits (a class/member name CAN contain non-ASCII).
    def ident(allow_unicode=False):
        n = rng.randint(1, 12)
        s = rng.choice(start) + "".join(rng.choice(rest) for _ in range(n - 1))
        if allow_unicode and rng.random() < 0.3:
            s = s + "é中"  # e-acute + a CJK char
        return s
    checked = 0
    for _ in range(2000):
        cname = ident(allow_unicode=True)
        members = {}
        used = set()
        k = rng.randint(1, 4)
        while len(members) < k:
            mname = ident(allow_unicode=True)
            if mname in used or mname.startswith("_") or mname.endswith("_"):
                continue
            used.add(mname)
            members[mname] = len(members) + 1
        EnumCls = enum.Enum(cname, members)
        for mname in members:
            m = EnumCls[mname]
            cn = [ord(ch) for ch in m.__class__.__name__]
            mn = [ord(ch) for ch in m.name]
            # the two args the model passes to enum_rendering for this member:
            assert is_codepoint_list(cn), "class_name arg not a code-point list: %r" % (cn,)
            assert is_codepoint_list(mn), "member_name arg not a code-point list: %r" % (mn,)
            checked += 1
    # empty-name boundary (the model's List[int] domain admits the empty list):
    assert is_codepoint_list([])
    print("AX-CONTAIN OK: every caller-reachable enum_rendering input "
          "(ord*(cls.__name__), ord*(member.name)) is a Unicode-code-point list "
          "inside the deep model's total domain; %d members checked" % checked)
    sys.exit(0)

main()
'''

AXIOM_TESTS = [
    {"id": "ax-sound-enum-rendering", "axiom": "enum_rendering",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_SOUND_PROBE,
     "rationale": "A-reference deep-model soundness (PBT_PLAN §4): enum_rendering(class_name, "
                  "member_name) = class_name ++ '.' ++ member_name must equal the REAL gold "
                  "rendering `\"%s.%s\" % (member.__class__.__name__, member.name)` on every "
                  "real enum.Enum member. The probe builds boundary + 5000 randomized real "
                  "Enum classes, runs the real `%s.%s` formatting, and asserts equality with "
                  "the deep model on the corresponding code-point sequences (also that the "
                  "gold rendering differs from the ugly pre-patch repr). If the real callee "
                  "ever disagrees => AXIOM-UNSOUND. Imports only stdlib `enum`."},
    {"id": "ax-contain-enum-rendering", "axiom": "enum_rendering",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_CONTAIN_PROBE,
     "rationale": "containment (AXIOM-TOO-WEAK-FOR-CALLER recast): the model feeds "
                  "enum_rendering exactly (ToSeq(value.class_name), ToSeq(value.member_name)) — "
                  "arbitrary Unicode-code-point lists. enum_rendering is a total @Pure fold "
                  "with no Requires restriction, so its domain is the whole code-point-sequence "
                  "space; every caller-reachable input (incl. non-ASCII names and the empty "
                  "name) lies inside it. A reachable input outside the domain would be "
                  "AXIOM-TOO-WEAK-FOR-CALLER; the probe confirms none exists."},
]
