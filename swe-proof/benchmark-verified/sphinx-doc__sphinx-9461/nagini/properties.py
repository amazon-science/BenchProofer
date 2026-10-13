# properties.py — PBT falsification battery for sphinx-doc__sphinx-9461.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap a
# SINGLE `# impl-start` .. `# impl-end` block (of ONE modeled function) for a new
# body and leave the frozen spec (axioms / pure / pre / post-conditions /
# signatures) byte-identical. spec_view elides EVERY impl region, so same_spec is
# GUARANTEED for every case regardless of the proof scaffolding inside.
#
# ----------------------------------------------------------------------------
# Defended surface (from model.py / refinement.md / mapping.md / instance.json).
# Five modeled functions, three F2P-observable behaviours:
#
#  §A property_qualifier_prefix(has_abstract, has_classlevel) -> List[int]:
#       (PA) ToSeq(Result()) == expected_prefix(has_abstract, has_classlevel)
#       The qualifier prefix, GROUNDED in the two flags: `property ` always, the
#       `class ` word present iff has_classlevel, `abstract ` first iff abstract.
#       Discriminating fix = the NEW `class` word (prepatch never emitted it).
#       expected_prefix is @Pure and fully transparent in its args (no opaque
#       answer-key oracle) -> there is NO wrong echo; see 'assessment'.
#       F2P: test_pyproperty (prop2 -> 'class property ').
#
#  §B qualifies_for_property_doc(is_property, is_classlevel_property, member_id):
#       (PB1) Result() == (is_property or is_classlevel_property)   -- the value
#       (PB2) Implies(Result(), documented_as_property(member_id))  -- the GATE
#     property_option_block(is_abstract, is_classlevel_property, member_id):
#       Requires(documented_as_property(member_id))                 -- gated emit
#       (PB3) ToSeq(Result()) == expected_option_block(is_abstract, is_classlevel)
#       Discriminating fix = a @classmethod@property is DISCOVERED (qualifies via
#       the OR) AND emits the NEW `   :classmethod:` option line.
#       F2P: test_class_properties (autoproperty-direct path).
#
#  §C member_retained_in_class_walk(is_classlevel_property, has_descriptive_text,
#                                   member_id):
#       (PC1) Result() == has_descriptive_text                      -- the value
#       (PC2) Implies(Result(), retained_in_class_walk(member_id))  -- the GATE
#     class_walk_option_block(is_abstract, is_classlevel_property, member_id):
#       Requires(retained_in_class_walk(member_id))                 -- gated emit
#       (PC3) ToSeq(Result()) == expected_option_block(is_abstract, is_classlevel)
#       Discriminating fix = a class-level property's text RESOLVES so it is
#       retained on the same footing as an ordinary property (NOT dropped for
#       being class-level). F2P: test_properties (autoclass member-walk path).
#
# ----------------------------------------------------------------------------
# READ-ONLY INPUTS / FRAME-MUTATION:
#   Every modeled function takes ONLY immutable value params (bool / int) plus
#   abstract capability predicates as preconditions; the outputs are FRESH
#   List[int] built locally. There is NO Acc(x, 1/2) read-only REFERENCE input,
#   so the classic write-to-a-half-permission-input frame-mutation probe is N/A
#   here (has_readonly_input = False). The project-equivalent defended surface is
#   the two UNFORGEABLE control-flow capabilities documented_as_property /
#   retained_in_class_walk (@ContractOnly @Predicate, no body): an impl cannot
#   Fold them into existence and they name a SPECIFIC member, so emission cannot
#   be produced for a member the discovery/retention step never established. The
#   attacks below stress exactly this gate (control-flow-effect + capability
#   forgery), which a byte-fuzzer never reaches. See 'assessment'.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9461"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Per-function impl anchors. Each anchor runs from a UNIQUE marker line down to
# the function's `# impl-end`, so _swap edits exactly one impl region and the
# frozen spec is never touched. (The two option-block functions share an
# identical impl body, so they are anchored on their distinct capability
# Requires line.)
# ---------------------------------------------------------------------------

def _block_after(marker):
    """Text from `marker` (inclusive) to the next `# impl-end` (inclusive)."""
    s = _BASE.index(marker)
    e = _BASE.index("# impl-end", s) + len("# impl-end")
    block = _BASE[s:e]
    if _BASE.count(block) != 1:
        raise AssertionError(f"anchor not unique for {marker!r}")
    return block


# §A prefix: the impl-start block is unique (only function building 'property').
_PREFIX_IMPL = _block_after(
    "    # impl-start\n    result = []  # type: List[int]\n    if has_abstract:")
# §B discovery: unique impl-start block (only one with `if is_property:`).
_DISC_IMPL = _block_after(
    "    # impl-start\n    if is_property:")
# §B emission (property_option_block): anchor on its capability Requires line.
_POPT_IMPL = _block_after("    Requires(documented_as_property(member_id))")
# §C retention: unique impl-start block (only one with `text_resolves =`).
_RETAIN_IMPL = _block_after(
    "    # impl-start\n    text_resolves = has_descriptive_text")
# §C walk emission (class_walk_option_block): anchor on its capability Requires.
_WOPT_IMPL = _block_after("    Requires(retained_in_class_walk(member_id))")


def _swap_prefix(new_impl):
    return _swap(_BASE, _PREFIX_IMPL, new_impl)


def _swap_disc(new_impl):
    return _swap(_BASE, _DISC_IMPL, new_impl)


def _swap_popt(new_impl):
    return _swap(_BASE, _POPT_IMPL, new_impl)


def _swap_retain(new_impl):
    return _swap(_BASE, _RETAIN_IMPL, new_impl)


def _swap_wopt(new_impl):
    return _swap(_BASE, _WOPT_IMPL, new_impl)


# Code-point literals (mirrors of the pure-region words/lines).
_ABSTRACT = "[97, 98, 115, 116, 114, 97, 99, 116]"
_CLASS = "[99, 108, 97, 115, 115]"
_PROPERTY = "[112, 114, 111, 112, 101, 114, 116, 121]"
_SPACE = "[32]"
_LINE_ABSTRACT = ("[32, 32, 32, 58, 97, 98, 115, 116, 114, 97, 99, 116,\n"
                  "                           109, 101, 116, 104, 111, 100, 58]")
_LINE_CLASS = ("[32, 32, 32, 58, 99, 108, 97, 115, 115,\n"
               "                           109, 101, 116, 104, 111, 100, 58]")

# The verbatim POPT/WOPT capability-Requires prefix shared by the two emission
# impl blocks (everything from the Requires line up to and including the
# `# impl-start` marker), reused so a variant changes only the body.
_POPT_HEAD = _POPT_IMPL[:_POPT_IMPL.index("# impl-start") + len("# impl-start")]
_WOPT_HEAD = _WOPT_IMPL[:_WOPT_IMPL.index("# impl-start") + len("# impl-start")]


def _popt_body(body):
    return _POPT_HEAD + "\n" + body.rstrip("\n") + "\n    # impl-end"


def _wopt_body(body):
    return _WOPT_HEAD + "\n" + body.rstrip("\n") + "\n    # impl-end"


SPEC_TESTS = [

    # ===================== SOUNDNESS / POSITIVE CONTROLS ====================

    # §A POSITIVE CONTROL (structural reshape, must verify). Build the prefix via
    # an explicitly typed intermediate local and a single accumulator step per
    # word, keeping the EXACT concatenation order (abstract, then class, then
    # property, each + space). Straight-line build (no loops/invariants), so no
    # framing lemma is needed; a correct different shape must verify, else
    # SPEC-TOO-STRONG.
    {
        "id": "pos-prefix-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_prefix(
            "    # impl-start\n"
            "    result = []  # type: List[int]\n"
            f"    word_a = {_ABSTRACT}  # type: List[int]\n"
            f"    word_c = {_CLASS}  # type: List[int]\n"
            f"    word_p = {_PROPERTY}  # type: List[int]\n"
            f"    sep = {_SPACE}  # type: List[int]\n"
            "    if has_abstract:\n"
            "        result = result + word_a + sep\n"
            "    if has_classlevel:\n"
            "        result = result + word_c + sep\n"
            "    result = result + word_p + sep\n"
            "    return result\n"
            "    # impl-end"
        ),
        "rationale": "a correct but structurally-different prefix build (typed "
                     "intermediate locals, same concatenation order) must verify "
                     "against PA. Straight-line, no loop invariant to drop; else "
                     "SPEC-TOO-STRONG.",
    },

    # §B discovery POSITIVE CONTROL (branch reorder, must verify). Check the
    # class-level branch FIRST, then the plain-property branch -- a different
    # control flow with the SAME value (OR is commutative) and the SAME capability
    # grant on every qualifying branch. Must verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-disc-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_disc(
            "    # impl-start\n"
            "    if is_classlevel_property:\n"
            "        establish_documented(member_id)\n"
            "        return True\n"
            "    if is_property:\n"
            "        establish_documented(member_id)\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "rationale": "reordered branches (class-level first) compute the same "
                     "OR value and grant the capability on every qualifying "
                     "branch, satisfying PB1+PB2; must verify, else SPEC-TOO-STRONG.",
    },

    # §B emission POSITIVE CONTROL (typed-local reshape, must verify). Build the
    # option block via typed intermediate locals, same line order (abstract then
    # class). Must verify against PB3, else SPEC-TOO-STRONG.
    {
        "id": "pos-popt-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_popt(_popt_body(
            "    result = []  # type: List[int]\n"
            f"    la = {_LINE_ABSTRACT}  # type: List[int]\n"
            f"    lc = {_LINE_CLASS}  # type: List[int]\n"
            "    if is_abstract:\n"
            "        result = result + la\n"
            "    if is_classlevel_property:\n"
            "        result = result + lc\n"
            "    return result\n"
        )),
        "rationale": "a correct different shape (typed line locals, same order) "
                     "must verify against PB3; else SPEC-TOO-STRONG.",
    },

    # §C retention POSITIVE CONTROL (logically-equivalent guard, must verify).
    # Decide via `if has_descriptive_text:` directly (gold uses an intermediate
    # `text_resolves` local) and grant the retention capability on the retain
    # branch. Same value + same grant => must verify, else SPEC-TOO-STRONG.
    {
        "id": "pos-retain-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap_retain(
            "    # impl-start\n"
            "    if has_descriptive_text:\n"
            "        establish_retained(member_id)\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "rationale": "drops the intermediate local but keeps the value "
                     "(Result()==has_descriptive_text) and the retain-branch "
                     "capability grant (PC1+PC2); must verify, else SPEC-TOO-STRONG.",
    },

    # ========================= ADMISSIBILITY =========================

    # ADMISSIBILITY of the GATED emission path (must verify). Inside the discovery
    # function's impl, on an F2P-shaped class-level-property input, mint the
    # capability via the discovery decision then SELF-CALL property_option_block
    # -- exercising that Requires(documented_as_property(member_id)) is actually
    # establishable for a normal member. If the precondition could not be met for
    # a legitimate discovered member, this call site fails => PRECOND-TOO-STRONG.
    # The discovery function still returns its correct gold value afterwards.
    {
        "id": "admiss-gated-emit",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_disc(
            "    # impl-start\n"
            "    # Admissibility self-call: a discovered class-level property is an\n"
            "    # F2P-shaped in-domain input; minting the capability via the\n"
            "    # discovery decision must establish property_option_block's Requires.\n"
            "    if is_classlevel_property:\n"
            "        establish_documented(member_id)\n"
            "        Assert(documented_as_property(member_id))\n"
            "        probe = property_option_block(False, True, member_id)\n"
            "        Assert(Acc(list_pred(probe)))\n"
            "        # documented_as_property is a @Predicate (a resource): the gated\n"
            "        # emission call above EXHALES the instance to satisfy its Requires\n"
            "        # and does not return it, so re-mint it for THIS function's own\n"
            "        # capability-granting postcondition (Implies(Result(), ...)). This\n"
            "        # is a proof-engineering step on the predicate resource, not a\n"
            "        # spec change -- the precondition itself WAS satisfiable (the\n"
            "        # probe call's Requires discharged); see assessment.\n"
            "        establish_documented(member_id)\n"
            "        return True\n"
            "    if is_property:\n"
            "        establish_documented(member_id)\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "rationale": "the capability precondition must ADMIT a normal discovered "
                     "member: minting documented_as_property then calling the gated "
                     "emission must verify and yield a well-formed block; else "
                     "PRECOND-TOO-STRONG. (documented_as_property is a @Predicate / "
                     "resource: the gated-emission call consumes the minted instance, "
                     "so a second mint restores the one this function's own "
                     "postcondition needs -- a proof step, not a spec relaxation.)",
    },

    # ADMISSIBILITY of the WALK gated emission (must verify). Same idea on the
    # retention->walk-emission gate: mint retained_in_class_walk via the retention
    # decision and self-call class_walk_option_block.
    {
        "id": "admiss-walk-emit",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap_retain(
            "    # impl-start\n"
            "    # Admissibility self-call for the retention->walk-emission gate.\n"
            "    text_resolves = has_descriptive_text\n"
            "    if text_resolves:\n"
            "        establish_retained(member_id)\n"
            "        Assert(retained_in_class_walk(member_id))\n"
            "        probe = class_walk_option_block(False, True, member_id)\n"
            "        Assert(Acc(list_pred(probe)))\n"
            "        # retained_in_class_walk is a @Predicate (a resource): the walk\n"
            "        # emission call above EXHALES the instance to satisfy its Requires\n"
            "        # and does not return it, so re-mint it for THIS function's own\n"
            "        # capability-granting postcondition (Implies(Result(), ...)). A\n"
            "        # proof-engineering step on the predicate resource, not a spec\n"
            "        # change -- the precondition itself WAS satisfiable.\n"
            "        establish_retained(member_id)\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "rationale": "the retained_in_class_walk precondition must admit a retained "
                     "class-level property: minting it then calling the walk "
                     "emission must verify; else PRECOND-TOO-STRONG. "
                     "(retained_in_class_walk is a @Predicate / resource: the walk "
                     "emission call consumes the minted instance, so a second mint "
                     "restores the one this function's own postcondition needs -- a "
                     "proof step, not a spec relaxation.)",
    },

    # ============================ UNIQUENESS / REJECT ============================

    # §A ATTACK (PARTIAL-DOMAIN, = model_prepatch.py). Never emit the `class`
    # word: build the prefix as it was pre-patch (property always, abstract iff
    # abstract). CORRECT on has_classlevel=False, WRONG on has_classlevel=True
    # (yields `property ` where the spec wants `class property `). Must reject by
    # PA.
    {
        "id": "weak-prefix-no-class",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_prefix(
            "    # impl-start\n"
            "    result = []  # type: List[int]\n"
            "    if has_abstract:\n"
            f"        result = result + {_ABSTRACT}\n"
            f"        result = result + {_SPACE}\n"
            f"    result = result + {_PROPERTY}\n"
            f"    result = result + {_SPACE}\n"
            "    return result\n"
            "    # impl-end"
        ),
        "refinement": "this is the PRE-PATCH prefix assembly (model_prepatch.py): "
                      "no `class` word is ever contributed. A class-level property "
                      "(:classmethod:) then renders `property ` instead of "
                      "`class property `. test_pyproperty asserts prop2's signature "
                      "prefix is exactly `class property ` => the faithful real "
                      "patch (no `class` word) FAILS test_pyproperty; it does NOT "
                      "resolve. (= model_prepatch.py, G-DIFF.)",
        "rationale": "violates PA: ToSeq(Result()) omits word_class()+space() on "
                     "has_classlevel=True, so != expected_prefix(False, True).",
    },

    # §A ATTACK (PARTIAL-DOMAIN, wrong order). Emit `class` BEFORE `abstract`
    # (swap the two optional blocks). CORRECT unless BOTH flags set; WRONG on
    # (has_abstract=True, has_classlevel=True): `class abstract property ` vs the
    # spec's `abstract class property `. Must reject by PA.
    {
        "id": "weak-prefix-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_prefix(
            "    # impl-start\n"
            "    result = []  # type: List[int]\n"
            "    if has_classlevel:\n"
            f"        result = result + {_CLASS}\n"
            f"        result = result + {_SPACE}\n"
            "    if has_abstract:\n"
            f"        result = result + {_ABSTRACT}\n"
            f"        result = result + {_SPACE}\n"
            f"    result = result + {_PROPERTY}\n"
            f"    result = result + {_SPACE}\n"
            "    return result\n"
            "    # impl-end"
        ),
        "refinement": "this emits `class` before `abstract`. The gold "
                      "get_signature_prefix appends `abstract` first then `class` "
                      "(`abstract class property `); an abstract class-level "
                      "property would here render `class abstract property `. The "
                      "real ordered ' '.join produces `abstract class property `, "
                      "so the rendered signature differs from the gold output on the "
                      "both-flags member and any test observing that ordering "
                      "diverges => the faithful real patch does NOT resolve.",
        "rationale": "violates PA on (has_abstract=True, has_classlevel=True): "
                     "ToSeq(Result()) == class++space++abstract++space++property++space "
                     "!= expected_prefix(True, True) which is abstract-first.",
    },

    # §B ATTACK (PARTIAL-DOMAIN, = model_prepatch_2.py discovery revert). Qualify
    # ONLY when is_property; drop the class-level branch entirely. WRONG on a
    # class-level property (is_property=False, is_classlevel_property=True): real
    # True, this returns False. Must reject by PB1.
    {
        "id": "weak-disc-property-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_disc(
            "    # impl-start\n"
            "    if is_property:\n"
            "        establish_documented(member_id)\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "refinement": "this is the PRE-PATCH discovery (model_prepatch_2.py): "
                      "can_document_member returns isproperty(member) only, so a "
                      "@classmethod@property (isproperty(member)==False) is NEVER "
                      "admitted and is documented nowhere. test_class_properties "
                      "documents prop2 (a class-level property) and asserts its "
                      "directive output is present => with no discovery the prop2 "
                      "block is absent and the F2P FAILS; the faithful real patch "
                      "does NOT resolve. (= model_prepatch_2.py, G-DIFF.)",
        "rationale": "violates PB1: Result()==is_property != "
                     "(is_property or is_classlevel_property) when "
                     "is_property=False and is_classlevel_property=True.",
    },

    # §B ATTACK (WRONG VALUE, AND for OR). Qualify only when BOTH predicates hold
    # (a member that is BOTH a plain property and a class-level property -- which
    # never co-occur in reality). WRONG on every real member: prop1 (True,False)
    # and prop2 (False,True) both then return False. Must reject by PB1.
    {
        "id": "weak-disc-and-not-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_disc(
            "    # impl-start\n"
            "    if is_property:\n"
            "        if is_classlevel_property:\n"
            "            establish_documented(member_id)\n"
            "            return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "refinement": "this admits a member only when it is BOTH a plain property "
                      "AND a class-level property -- a combination that never "
                      "occurs (a member is one or the other). So every real "
                      "@property and every real @classmethod@property is rejected "
                      "by can_document_member and documented nowhere; both "
                      "test_class_properties (prop2) and the plain-property paths "
                      "(prop1) lose their documentation => the F2P/P2P FAIL. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "violates PB1: Result()==(is_property and is_classlevel_property) "
                     "!= (is_property or is_classlevel_property) on (True,False) and "
                     "(False,True).",
    },

    # §B ATTACK (CONTROL-FLOW-EFFECT, capability gate PB2). Return the CORRECT
    # value (is_property or is_classlevel_property) but NEVER call
    # establish_documented -- so the qualifying branch grants no capability. The
    # value clause PB1 passes, but PB2 (Implies(Result(), documented_as_property))
    # cannot be discharged: the abstract predicate has no body, an impl cannot
    # Fold it, so it must reject. This is the capability/control-flow probe the
    # value abstraction alone cannot sense.
    {
        "id": "cflow-disc-no-establish",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_disc(
            "    # impl-start\n"
            "    if is_property or is_classlevel_property:\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "refinement": "this returns the right discovery VALUE but never performs "
                      "the 'register this member as documentable' effect. In the "
                      "real autodoc pipeline can_document_member returning True is "
                      "not enough: import_object must succeed and the documenter "
                      "must actually proceed to emit add_directive_header. A patch "
                      "where can_document_member says True but import_object bails "
                      "(no self.object / self.isclassmethod set) emits NO directive "
                      "for the member -- prop2's :classmethod: line and block are "
                      "absent and test_class_properties / test_properties FAIL. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "violates PB2: Implies(Result(), documented_as_property(member_id)) "
                     "cannot be established without establish_documented (the SOLE "
                     "producer); the @ContractOnly @Predicate has no body so it "
                     "cannot be Folded. Rejected by the capability gate.",
    },

    # §B ATTACK (CAPABILITY FORGERY, wrong member). Mint the capability for a
    # DIFFERENT member id (a fixed constant) but return True for THIS member. PB1
    # holds, but PB2 needs documented_as_property(member_id) for the actual
    # member_id, which is NOT what was established. Must reject -- the capability
    # is per-member and unforgeable.
    {
        "id": "cflow-disc-wrong-member",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_disc(
            "    # impl-start\n"
            "    if is_property or is_classlevel_property:\n"
            "        establish_documented(member_id + 1)\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "refinement": "this establishes documentability for a DIFFERENT member "
                      "(member_id+1) than the one queried. In the real pipeline the "
                      "discovery/emission are about ONE specific member object; "
                      "documenting some other member does not make THIS one appear. "
                      "The queried member's directive block is still missing, so "
                      "test_class_properties FAILS for it. The faithful real patch "
                      "does NOT resolve.",
        "rationale": "violates PB2: documented_as_property(member_id) is required "
                     "but only documented_as_property(member_id+1) was established; "
                     "the capability names the specific member and is unforgeable.",
    },

    # §B emission ATTACK (PARTIAL-DOMAIN, = model_prepatch_2.py emission revert).
    # Emit ONLY the abstractness line; no class-level line branch. WRONG on a
    # class-level property (is_classlevel_property=True): the `   :classmethod:`
    # line is missing. Must reject by PB3.
    {
        "id": "weak-popt-no-classline",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_popt(_popt_body(
            "    result = []  # type: List[int]\n"
            "    if is_abstract:\n"
            f"        result = result + {_LINE_ABSTRACT}\n"
            "    return result\n"
        )),
        "refinement": "this is the PRE-PATCH emission (model_prepatch_2.py): "
                      "add_directive_header never adds the `   :classmethod:` line. "
                      "test_class_properties asserts prop2's directive output "
                      "contains `   :classmethod:` at the expected index => without "
                      "the line the F2P FAILS; the faithful real patch does NOT "
                      "resolve. (= model_prepatch_2.py, G-DIFF.)",
        "rationale": "violates PB3: ToSeq(Result()) omits line_class() on "
                     "is_classlevel_property=True, so != "
                     "expected_option_block(is_abstract, True).",
    },

    # §B emission ATTACK (WRONG ORDER). Emit the class-level line BEFORE the
    # abstractness line. WRONG on (is_abstract=True, is_classlevel_property=True):
    # `:classmethod:` then `:abstractmethod:` vs the spec's abstract-first block.
    # Must reject by PB3.
    {
        "id": "weak-popt-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_popt(_popt_body(
            "    result = []  # type: List[int]\n"
            "    if is_classlevel_property:\n"
            f"        result = result + {_LINE_CLASS}\n"
            "    if is_abstract:\n"
            f"        result = result + {_LINE_ABSTRACT}\n"
            "    return result\n"
        )),
        "refinement": "this emits `   :classmethod:` before `   :abstractmethod:`. "
                      "The real add_directive_header adds the abstractmethod line "
                      "first then the classmethod line; for an abstract class-level "
                      "property the directive output order would differ from the "
                      "gold, so the rendered block differs and the directive-output "
                      "assertion diverges => the faithful real patch does NOT "
                      "resolve.",
        "rationale": "violates PB3 on (is_abstract=True, is_classlevel_property=True): "
                     "ToSeq(Result()) == line_class()++line_abstract() != "
                     "expected_option_block(True, True) which is abstract-first.",
    },

    # §C ATTACK (PARTIAL-DOMAIN, = model_prepatch_3.py retention revert). A
    # class-level property's text does NOT resolve in the walk
    # (text_resolves = has_descriptive_text and not is_classlevel_property), so it
    # is dropped. WRONG on (is_classlevel_property=True, has_descriptive_text=True):
    # real True, this returns False. Must reject by PC1.
    {
        "id": "weak-retain-drop-classlevel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_retain(
            "    # impl-start\n"
            "    text_resolves = has_descriptive_text and not is_classlevel_property\n"
            "    if text_resolves:\n"
            "        establish_retained(member_id)\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "refinement": "this is the PRE-PATCH retention (model_prepatch_3.py): a "
                      "class-level property's descriptive text is treated as "
                      "unresolved, so a @classmethod@property WITH a docstring is "
                      "dropped from the autoclass member walk and documented "
                      "nowhere. test_properties (autoclass path) asserts prop2's "
                      "block is present in the class documentation => with the "
                      "member filtered out the whole prop2 block is absent and the "
                      "F2P FAILS; the faithful real patch does NOT resolve. "
                      "(= model_prepatch_3.py, G-DIFF.)",
        "rationale": "violates PC1: Result()==(has_descriptive_text and not "
                     "is_classlevel_property) != has_descriptive_text when "
                     "is_classlevel_property=True and has_descriptive_text=True.",
    },

    # §C ATTACK (CONTROL-FLOW-EFFECT, retention capability gate PC2). Return the
    # CORRECT value (has_descriptive_text) but NEVER call establish_retained.
    # PC1 passes; PC2 (Implies(Result(), retained_in_class_walk(member_id)))
    # cannot be discharged without the sole producer. Must reject.
    {
        "id": "cflow-retain-no-establish",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_retain(
            "    # impl-start\n"
            "    if has_descriptive_text:\n"
            "        return True\n"
            "    return False\n"
            "    # impl-end"
        ),
        "refinement": "this returns the right retention VALUE but never performs "
                      "the 'keep this walked member' effect. In the real "
                      "filter_members walk, computing keep=True is not enough -- the "
                      "member must actually be appended to `ret` and carried forward "
                      "to be documented. A patch that decides keep but drops the "
                      "member from the walk output emits no block for it, so prop2's "
                      "block is absent and test_properties FAILS. The faithful real "
                      "patch does NOT resolve.",
        "rationale": "violates PC2: Implies(Result(), retained_in_class_walk(member_id)) "
                     "cannot be established without establish_retained (the SOLE "
                     "producer); the abstract predicate has no body and cannot be "
                     "Folded. Rejected by the capability gate.",
    },

    # §C walk-emission ATTACK (PARTIAL-DOMAIN). class_walk_option_block drops the
    # class-level line (same defect as weak-popt-no-classline but on the
    # retention-gated walk emission, which test_properties observes). Must reject
    # by PC3.
    {
        "id": "weak-wopt-no-classline",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_wopt(_wopt_body(
            "    result = []  # type: List[int]\n"
            "    if is_abstract:\n"
            f"        result = result + {_LINE_ABSTRACT}\n"
            "    return result\n"
        )),
        "refinement": "the autoclass-walk emission omits the `   :classmethod:` "
                      "line for a retained class-level property. test_properties "
                      "(the autoclass member-walk path) asserts prop2's block "
                      "contains `   :classmethod:` => without it the F2P FAILS; the "
                      "faithful real patch does NOT resolve. (Same emission defect "
                      "as the prepatch_2 emission, here on the walk-gated path "
                      "test_properties observes.)",
        "rationale": "violates PC3: ToSeq(Result()) omits line_class() on "
                     "is_classlevel_property=True, so != "
                     "expected_option_block(is_abstract, True).",
    },
]


# ===========================================================================
# AXIOM lane. There are NO consumed @ContractOnly axioms (meta.axioms == []).
# The kind-A items are THREE A-references (deep models validated == the real
# callees): expected_prefix == real ' '.join assembly; expected_option_block +
# discovery decision == real isproperty-based can_document_member / emission;
# member_retained_in_class_walk == real getdoc-driven keep. The capabilities
# documented_as_property / retained_in_class_walk are abstract control-flow
# tokens, NOT callee axioms (no Ensures over a value the proof reads as data) --
# there is no value-axiom Requires-domain to contain, so axiom-containment is
# vacuous and there is no caller-reachable input outside any axiom domain.
#
# The single axiom-lane probe re-runs the bundle's host-validated G-AX oracle
# (axiom_check.py) IN-CONTAINER with the gold patch applied, so the three
# A-references are grounded in the REAL sphinx callees (real ' '.join, real
# sphinx.util.inspect.isproperty / getdoc over live @property and
# @classmethod@property members) -- it CALLS the real routines (never scrapes
# source). The runner mounts ONLY this probe at /work, so axiom_check.py's source
# is read on the HOST at load time and embedded verbatim into the probe string.
# axiom_check.py opens no files (no utf-8 codec concern); it exits 0 iff sound.
# ===========================================================================
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-prefix-emission-retention",
        "axiom": "expected_prefix / expected_option_block+discovery / "
                 "member_retained_in_class_walk (3 A-references)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness: the three deep models must equal the "
                     "REAL gold callees at the code-point / decision level over the "
                     "full boolean cube + the F2P-observed forms + live members. "
                     "A-ref1 expected_prefix == real ' '.join(words)+' '; A-ref2 "
                     "expected_option_block == real add_directive_header emission AND "
                     "the discovery decision == real can_document_member using the "
                     "real sphinx.util.inspect.isproperty over a live @property and "
                     "@classmethod@property; A-ref3 retention == the real "
                     "getdoc-driven keep over live prop1/prop2/prop_nodoc. Any "
                     "mismatch => an A-reference is unsound. No @ContractOnly value "
                     "axiom exists, so axiom-containment is vacuous (no "
                     "caller-reachable input outside any axiom domain).",
    },
]
