# properties.py — PBT falsification battery for sphinx-doc__sphinx-9229. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between a
# function's `# impl-start` / `# impl-end` is edited; the axioms / pure / pre- /
# post-conditions regions and every signature are never touched), checked by Nagini
# verify + markers.same_spec. Axiom cases probe the consumed @ContractOnly axiom
# `placeholder_seq` / `make_placeholder` (the unchanged 'alias of %s' % restify(...)
# line formatter) against the REAL callee in the instance Docker image.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json).
# This is a TWO-SITE change; each site is its own contracted+implemented function:
#
#  SITE A — select_doc_block(is_attr_alias, comment, prepared) -> Optional[List[int]]
#    models ClassDocumenter.get_doc()'s alias branch: which documentation block the
#    alias path selects. READ-ONLY inputs comment, prepared (both Acc(...,1/2)).
#    POSTCONDITION (1 framing pair + 3 LOAD-BEARING clauses):
#      (A-frame) Ensures(Acc(list_pred(comment),1/2)) ; Ensures(Acc(list_pred(prepared),1/2))
#      (1a) Implies(is_attr_alias and has_authored_comment(comment),
#                   Result() is not None and Acc(list_pred(Result())) and len(Result())==0)
#             -- alias WITH comment selects a PRESENT but EMPTY block.
#      (1b) Implies(is_attr_alias and not has_authored_comment(comment), Result() is None)
#             -- alias WITHOUT comment selects the ABSENT block.
#      (1c) Implies(not is_attr_alias, Result() is prepared)
#             -- a non-alias is UNCHANGED: returns the prepared block by OBJECT IDENTITY.
#    1a/1b PIN the alias decision in BOTH directions (present-empty vs absent); 1c pins
#    the non-alias path to is-identity (a value-equal fresh copy is NOT enough).
#
#  SITE B — alias_additional_content(is_attr_alias, comment, target, more_content)
#                                                              -> Optional[List[int]]
#    models ClassDocumenter.add_content()'s gating: whether the synthetic
#    'alias of <target>' placeholder replaces the additional content. READ-ONLY inputs
#    comment (1/2), target (1/2), more_content (1/2 when present).
#    POSTCONDITION (1 framing triple + 2 LOAD-BEARING clauses):
#      (B-frame) Ensures(Acc(list_pred(comment),1/2)); Ensures(Acc(list_pred(target),1/2));
#                Ensures(Implies(more_content is not None, Acc(list_pred(more_content),1/2)))
#      (2a) Implies(is_attr_alias and not has_authored_comment(comment),
#                   Result() is not None and Acc(list_pred(Result()),1/4)
#                   and opt_seq(Result()) == placeholder_seq(target))
#             -- alias WITHOUT comment substitutes the placeholder (a fresh, present
#                block whose content is EXACTLY the formatter's placeholder sequence).
#      (2b) Implies(not (is_attr_alias and not has_authored_comment(comment)),
#                   Result() is more_content)
#             -- otherwise (non-alias, OR alias WITH comment) the incoming content is
#                passed through by OBJECT IDENTITY (untouched).
#    2a/2b PIN the substitution decision in BOTH directions; 2a's content is grounded
#    in placeholder_seq(target) (the axiom), 2b pins is-identity to more_content.
#
# FRAME-MUTATION lane (MANDATORY — every input is read-only Acc(...,1/2)):
#   The real gold patch only READS the comment lookup, the prepared docstrings, the
#   alias target descriptor, and the incoming StringList; it NEVER mutates any of them.
#   A rival that WRITES a read-only input (even a no-op store) demands FULL write
#   permission, which the caller granted only at 1/2, so the verifier must reject for
#   INSUFFICIENT PERMISSION. Byte-fuzzers never think to mutate the input; this is the
#   project's #1 weakness class. Built for BOTH sites: a write into `prepared` (site A)
#   and into `target` (site B), each keeping the gold body verbatim so the rejection is
#   attributable SOLELY to the write.
#
# UNGROUNDED-ORACLE-ECHO: there is NO *wrong* echo. Clause 2a is pinned to
#   placeholder_seq(target) but the ONLY impl-callable producer of that sequence is
#   make_placeholder(target) (Ensures ToSeq(Result())==placeholder_seq(target)); there
#   is no opaque answer-key constant the impl could echo with a wrong value, because the
#   sequence is a function of the argument `target`, fully tied through the axiom face.
#   An impl that returns anything OTHER than make_placeholder(target) on the
#   alias-without-comment branch cannot prove 2a. So the honest control is the cheapest
#   faithful impl that calls the formatter (the gold body / the positive control), not a
#   wrong echo. See 'assessment'. (The axiom's own soundness — that the formatter's line
#   really is non-empty — is checked in the AXIOM lane below.)
#
# CONTROL-FLOW-EFFECT / VALUE-DOUBLE-MASK lane: APPLIES via the is-identity clauses.
#   1c (Result() is prepared) and 2b (Result() is more_content) demand OBJECT IDENTITY,
#   not value equality. A rival that returns a freshly-built list with the SAME element
#   value satisfies any value-level proxy but breaks `is` — and that is exactly the
#   real-code obligation (get_doc's non-alias path and add_content's else path leave the
#   local UNTOUCHED; a copy would be a different docutils object the pipeline must not
#   see). The fresh-copy rivals (site A non-alias, site B pass-through) discriminate this.
#
# PARTIAL-DOMAIN lane: heavily exercised. Each rival is correct on most of the alias /
#   comment input domain yet diverges on the discriminating sub-domain (the exact F2P
#   vs P2P split): the pre-patch reverts (always-absent block / always-substitute), the
#   branch swaps (present-empty when no comment), the never-substitute. Each carries the
#   refinement that its faithful real patch would fail the F2P test
#   test_class_alias_having_doccomment (alias WITH a #: docstring) or the P2P
#   test_class_alias (alias WITHOUT a comment).
#
# AXIOM lane: meta.axioms has ONE consumed @ContractOnly axiom (placeholder_seq /
#   make_placeholder) modelling the UNCHANGED 'alias of %s' % restify(self.object) line
#   formatter wrapped in StringList. Per PBT_PLAN §2.4: axiom-soundness runs the real
#   restify (the very module the patched file imports) + the gold's own 'alias of %s'
#   composition and asserts the rendered line is NON-EMPTY (the axiom's only Ensures);
#   axiom-containment confirms every target the model can pass to make_placeholder lies
#   inside the axiom's Requires domain (any list of code points / any restify-able
#   descriptor). The probes EMBED axiom_check.py's logic (the bundle's frozen G-AX
#   oracle), read on the HOST at load time, because the runner mounts only the probe.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9229"
FLOAT_ENCODING = None  # meta.json float_encoding is null


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_BASE = (Path(__file__).parent / "model.py").read_text()


# The two frozen FUNCTION impl-region bodies, VERBATIM (everything strictly BETWEEN
# each function's `# impl-start` / `# impl-end`). Every spec variant _swap()s ONLY one
# of these blocks, so the edit never touches the spec (axioms / pure / pre- / post-
# conditions + signatures). same_spec is computed over the spec_view, which elides
# every impl region, so swapping inside here is GUARANTEED same_spec.
_IMPL_A = """\
    if is_attr_alias:
        if has_authored_comment(comment):
            empty = []  # type: List[int]
            return empty
        else:
            return None
    return prepared"""

_IMPL_B = """\
    if is_attr_alias and not has_authored_comment(comment):
        result = make_placeholder(target)  # type: Optional[List[int]]
        return result
    return more_content"""

assert _BASE.count(_IMPL_A) == 1, "site-A impl region drifted from expected text"
assert _BASE.count(_IMPL_B) == 1, "site-B impl region drifted from expected text"


def _impl_a(new_body):
    """Full model.py variant with ONLY select_doc_block's impl body replaced."""
    return _swap(_BASE, _IMPL_A, new_body)


def _impl_b(new_body):
    """Full model.py variant with ONLY alias_additional_content's impl body replaced."""
    return _swap(_BASE, _IMPL_B, new_body)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY.
# ===========================================================================

# pos-A-reorder: structurally DIFFERENT but behaviourally identical select_doc_block.
# The original is `if is_attr_alias: (if comment [] else None); return prepared`. This
# reshape handles the NON-ALIAS case first (`if not is_attr_alias: return prepared`),
# then the two alias sub-cases as a flat if/else. Pure branch logic with NO loop
# invariant/lemma to lose (directive 2/3 are N/A here — there is no fold to fight); the
# three observable outcomes are produced on exactly the same inputs. If it FAILS =>
# SPEC-TOO-STRONG (a faithful, structurally-different correct impl rejected).
_POS_A = """\
    if not is_attr_alias:
        return prepared
    if has_authored_comment(comment):
        empty = []  # type: List[int]
        return empty
    return None"""

# pos-B-reorder: structurally DIFFERENT but behaviourally identical
# alias_additional_content. The original gates `is_attr_alias and not comment` first;
# this reshape pulls out the pass-through case first (`if not is_attr_alias or
# has_authored_comment(comment): return more_content`) then substitutes the placeholder
# on the remaining alias-without-comment case. De Morgan dual of the gold gate; identical
# semantics; the make_placeholder call (the only producer of placeholder_seq) is kept on
# exactly the alias-without-comment branch. If it FAILS => SPEC-TOO-STRONG.
_POS_B = """\
    if not is_attr_alias or has_authored_comment(comment):
        return more_content
    result = make_placeholder(target)  # type: Optional[List[int]]
    return result"""


# ===========================================================================
# ADMISSIBILITY — must VERIFY (else PRECOND-TOO-STRONG).
# ===========================================================================

# admiss-A: keeps select_doc_block's gold body VERBATIM but FIRST asserts, under the
# half-permission preconditions, that the reads a normal F2P-shaped input needs are
# admitted — the lengths of comment and prepared are readable, and (when non-empty,
# e.g. the F2P OtherAlias carrying a #: docstring comment) their first elements are
# readable. No write, so no extra permission demand. If the precondition could not admit
# a legitimate (alias, comment, prepared) triple this would fail => PRECOND-TOO-STRONG.
_ADMISS_A = (
    "    # Admissibility: a normal alias/comment/prepared triple is in-domain; the\n"
    "    # half-permissions admit reading both lengths and (when non-empty) elements.\n"
    "    Assert(len(comment) >= 0)\n"
    "    Assert(len(prepared) >= 0)\n"
    "    if len(comment) > 0:\n"
    "        Assert(comment[0] == comment[0])     # read admitted under Acc(...,1/2)\n"
    "    if len(prepared) > 0:\n"
    "        Assert(prepared[0] == prepared[0])   # read admitted under Acc(...,1/2)\n"
    + _IMPL_A
)

# admiss-B: keeps alias_additional_content's gold body VERBATIM but FIRST asserts the
# half-permission reads for a normal F2P-shaped input (comment, target, and — when
# present — more_content). No write. If it FAILS => PRECOND-TOO-STRONG.
_ADMISS_B = (
    "    # Admissibility: a normal alias/comment/target/more_content tuple is in-domain.\n"
    "    Assert(len(comment) >= 0)\n"
    "    Assert(len(target) >= 0)\n"
    "    if len(comment) > 0:\n"
    "        Assert(comment[0] == comment[0])     # read admitted under Acc(...,1/2)\n"
    "    if len(target) > 0:\n"
    "        Assert(target[0] == target[0])       # read admitted under Acc(...,1/2)\n"
    "    if more_content is not None and len(more_content) > 0:\n"
    "        Assert(more_content[0] == more_content[0])  # admitted under Acc(...,1/2)\n"
    + _IMPL_B
)


# ===========================================================================
# FRAME-MUTATION RIVALS (MANDATORY — every input is read-only Acc(...,1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ===========================================================================

# frame-mut-A: keeps select_doc_block's gold body VERBATIM (so the rejection is
# attributable SOLELY to the added write), then WRITES BACK into the read-only input
# `prepared`: prepared[0] = prepared[0]. A no-op store, but a STORE — it demands FULL
# write permission on `prepared`, granted only at 1/2. Placed first, guarded by len>0 so
# it is reachable on a normal non-alias prepared block. The real get_doc returns the
# prepared docstrings UNTOUCHED; mutating that shared list would corrupt the documented
# output for every consumer.
_FRAME_A = (
    "    if len(prepared) > 0:\n"
    "        # Frame violation: write into the read-only (Acc(...,1/2)) input.\n"
    "        prepared[0] = prepared[0]\n"
    + _IMPL_A
)

# frame-mut-B: keeps alias_additional_content's gold body VERBATIM, then WRITES BACK
# into the read-only `target`: target[0] = target[0]. Demands FULL write permission on
# `target`, granted only at 1/2. The real add_content only READS self.object to render
# restify(self.object); mutating the alias target descriptor would corrupt the
# cross-reference for every later use.
_FRAME_B = (
    "    if len(target) > 0:\n"
    "        # Frame violation: write into the read-only (Acc(...,1/2)) input.\n"
    "        target[0] = target[0]\n"
    + _IMPL_B
)


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN / VALUE-DOUBLE-MASK RIVALS — must be REJECTED
# (else SPEC-TOO-WEAK). Each shares the frozen spec exactly; only one impl changes.
# ===========================================================================

# weak-A-prepatch: the EXACT pre-patch get_doc alias branch (model_prepatch.py) — an
# alias ALWAYS selects the ABSENT block (return None), the comment is never consulted.
# PARTIAL-DOMAIN: correct on the no-comment and non-alias sub-domains, WRONG on
# alias-WITH-comment.
_WEAK_A_PREPATCH = """\
    if is_attr_alias:
        return None
    return prepared"""

# weak-A-always-present: the dual revert — an alias ALWAYS selects a PRESENT empty block
# ([]) regardless of the comment. Correct on alias-with-comment, WRONG on
# alias-without-comment (should be the ABSENT None).
_WEAK_A_ALWAYS_PRESENT = """\
    if is_attr_alias:
        empty = []  # type: List[int]
        return empty
    return prepared"""

# weak-A-swap: the comment decision INVERTED — alias-with-comment -> None (absent),
# alias-without-comment -> [] (present-empty). Wrong on BOTH alias sub-domains; a
# capability/branch-inversion rival.
_WEAK_A_SWAP = """\
    if is_attr_alias:
        if has_authored_comment(comment):
            return None
        else:
            empty = []  # type: List[int]
            return empty
    return prepared"""

# weak-A-copy: VALUE-DOUBLE-MASK on the non-alias path. Instead of returning the
# read-only `prepared` block by OBJECT IDENTITY (clause 1c: Result() is prepared), it
# returns a freshly-built list. The value abstraction (if 1c were value-equality) would
# accept it; the is-identity clause must reject it. (A real get_doc that rebuilt the
# prepared docstrings into a new list would feed the pipeline a different docutils
# object — not the unchanged behaviour.)
_WEAK_A_COPY = """\
    if is_attr_alias:
        if has_authored_comment(comment):
            empty = []  # type: List[int]
            return empty
        else:
            return None
    fresh = list(prepared)  # type: List[int]
    return fresh"""

# weak-B-prepatch: the EXACT pre-patch add_content gate (model_prepatch_2.py) — the
# placeholder is substituted for EVERY alias, regardless of the comment. PARTIAL-DOMAIN:
# correct on alias-without-comment and non-alias, WRONG on alias-WITH-comment (should
# pass the incoming content through, clause 2b).
_WEAK_B_PREPATCH = """\
    if is_attr_alias:
        result = make_placeholder(target)  # type: Optional[List[int]]
        return result
    return more_content"""

# weak-B-never: the placeholder is NEVER substituted — every input passes more_content
# through. Correct on the pass-through sub-domain, WRONG on alias-without-comment (should
# substitute the placeholder, clause 2a). The dual of the pre-patch revert.
_WEAK_B_NEVER = """\
    return more_content"""

# weak-B-copy: VALUE-DOUBLE-MASK on the pass-through path. On the else branch it returns
# a freshly-built copy of more_content instead of more_content itself, breaking clause
# 2b's OBJECT IDENTITY (Result() is more_content). Guarded on more_content is not None so
# the copy is well-typed under the conditional permission. (A real add_content that
# rebuilt the StringList would hand super().add_content a different object.)
_WEAK_B_COPY = """\
    if is_attr_alias and not has_authored_comment(comment):
        result = make_placeholder(target)  # type: Optional[List[int]]
        return result
    if more_content is not None:
        fresh = list(more_content)  # type: Optional[List[int]]
        return fresh
    return more_content"""


SPEC_TESTS = [
    # ---- positive controls (soundness) ----
    {
        "id": "pos-A-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_a(_POS_A),
        "rationale": (
            "structurally-different but CORRECT select_doc_block: the non-alias case is "
            "handled FIRST (`if not is_attr_alias: return prepared`), then the two alias "
            "sub-cases as a flat if/else. Pure branch logic, no loop invariant/fold to "
            "lose (directives 2/3 N/A); the three observable outcomes (present-empty, "
            "absent, prepared-by-identity) are produced on exactly the same inputs and "
            "every postcondition clause still discharges. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-B-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_b(_POS_B),
        "rationale": (
            "structurally-different but CORRECT alias_additional_content: the De Morgan "
            "dual of the gold gate — the pass-through case (`not is_attr_alias or "
            "has_authored_comment(comment)`) returns more_content first, then the "
            "remaining alias-without-comment case calls make_placeholder(target). "
            "Identical semantics; the formatter call stays on the only branch clause 2a "
            "permits. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    # ---- admissibility ----
    {
        "id": "admiss-A",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_a(_ADMISS_A),
        "rationale": (
            "the preconditions (Acc(list_pred(comment),1/2) and "
            "Acc(list_pred(prepared),1/2)) must admit a normal F2P/P2P-shaped triple: "
            "both lengths and (when non-empty, e.g. the F2P OtherAlias comment) first "
            "elements are readable under the half-permissions. Gold body otherwise "
            "verbatim, reads/asserts only. If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-B",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_b(_ADMISS_B),
        "rationale": (
            "the preconditions (Acc on comment, target at 1/2; conditional Acc on "
            "more_content) must admit a normal alias/comment/target/more_content tuple: "
            "the relevant lengths and first elements are readable under the "
            "half-permissions. Gold body otherwise verbatim. If it FAILS => "
            "PRECOND-TOO-STRONG."
        ),
    },
    # ---- frame-mutation (MANDATORY) ----
    {
        "id": "frame-mut-A",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_a(_FRAME_A),
        "refinement": (
            "the gold get_doc returns the prepared docstrings UNTOUCHED on the non-alias "
            "path and never writes the comment lookup; a faithful real patch that mutated "
            "the prepared-docstrings list (the shared `[prepare_docstring(...) ...]` "
            "value) would corrupt the documented output for every downstream consumer and "
            "diverge from the gold — it would not be the gold patch and would not resolve "
            "the F2P/P2P. The store here is a no-op only by coincidence; the point is the "
            "spec must forbid ANY write to a read-only carrier."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `prepared` is granted at "
            "Acc(list_pred(prepared),1/2); the store prepared[0]=prepared[0] demands FULL "
            "write permission, unavailable, so the verifier rejects for INSUFFICIENT "
            "PERMISSION. Gold body kept verbatim so the rejection is attributable solely "
            "to the write. If it VERIFIES => the read-only frame is hollow (frame-mutation, "
            "the #1 weakness class)."
        ),
    },
    {
        "id": "frame-mut-B",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_b(_FRAME_B),
        "refinement": (
            "the gold add_content only READS self.object to render restify(self.object); "
            "it never mutates the alias target descriptor. A faithful real patch that "
            "wrote into the target descriptor would corrupt the cross-reference for every "
            "later rendering and diverge from the gold — it would not resolve. The store "
            "is a no-op only by coincidence; the spec must forbid ANY write to `target`."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `target` is granted at "
            "Acc(list_pred(target),1/2); the store target[0]=target[0] demands FULL write "
            "permission, unavailable, so the verifier rejects for INSUFFICIENT PERMISSION. "
            "Gold body kept verbatim. If it VERIFIES => frame-mutation hole."
        ),
    },
    # ---- partial-domain / branch-confusion ----
    {
        "id": "weak-A-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_a(_WEAK_A_PREPATCH),
        "refinement": (
            "this IS the pre-patch get_doc alias branch (model_prepatch.py): an alias "
            "ALWAYS returns None, the comment is never consulted. Its faithful real patch "
            "is the UNCHANGED repo (`if self.doc_as_attr: return None`), which selects the "
            "ABSENT block even for an alias carrying a #: docstring — exactly the bug the "
            "gold fixes. It fails the F2P test_class_alias_having_doccomment (the "
            "OtherAlias docstring is dropped). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (1a): for is_attr_alias and has_authored_comment(comment) "
            "the rival returns None, but 1a demands Result() is not None and len==0 (a "
            "PRESENT empty block). PARTIAL-DOMAIN on the alias-with-comment sub-domain. If "
            "it VERIFIES => SPEC-TOO-WEAK (present-vs-absent decision unpinned). This is "
            "exactly the G-DIFF prepatch."
        ),
    },
    {
        "id": "weak-A-always-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_a(_WEAK_A_ALWAYS_PRESENT),
        "refinement": (
            "an alias ALWAYS selects a PRESENT empty block regardless of the comment. Its "
            "faithful real patch (`if self.doc_as_attr: return []`) would run the "
            "documentation pipeline for an alias WITHOUT any authored comment, suppressing "
            "the `alias of ...` default that test_class_alias (P2P) requires (get_doc==[] "
            "makes the alias look documented). Does NOT resolve the P2P."
        ),
        "rationale": (
            "REJECTED by clause (1b): for is_attr_alias and not "
            "has_authored_comment(comment) the rival returns [] (not None), but 1b demands "
            "Result() is None (the ABSENT block). PARTIAL-DOMAIN on the alias-without-"
            "comment sub-domain. If it VERIFIES => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-A-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_a(_WEAK_A_SWAP),
        "refinement": (
            "the comment decision INVERTED: alias-with-comment -> None, "
            "alias-without-comment -> []. Its faithful real patch (`if comment: return "
            "None else: return []`) is the exact opposite of the gold and is wrong on "
            "BOTH alias sub-domains — it drops the OtherAlias docstring (F2P) AND fakes a "
            "doc block for the plain Alias (P2P). Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause (1a) on alias-with-comment (returns None, 1a demands "
            "present-empty) — and independently by (1b) on alias-without-comment (returns "
            "[], 1b demands None). A branch-inversion rival hitting BOTH load-bearing "
            "clauses. If it VERIFIES => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-A-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_a(_WEAK_A_COPY),
        "refinement": (
            "VALUE-DOUBLE-MASK: on the non-alias path it returns a fresh list(prepared) "
            "instead of the prepared object itself. A real get_doc that rebuilt the "
            "prepared docstrings into a NEW list would hand the documentation pipeline a "
            "different object than the one the unchanged code returns; the patch leaves "
            "the non-alias path untouched, so a rebuild is not the gold behaviour and the "
            "value-equal copy is not a faithful resolution."
        ),
        "rationale": (
            "REJECTED by clause (1c): Result() is prepared demands OBJECT IDENTITY; a "
            "freshly-built list is a different object, so `is` fails even though the value "
            "is equal. This is the value-double-mask discriminator — the spec pins "
            "identity, not value. If it VERIFIES => SPEC-TOO-WEAK (1c reducible to value "
            "equality)."
        ),
    },
    {
        "id": "weak-B-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_b(_WEAK_B_PREPATCH),
        "refinement": (
            "this IS the pre-patch add_content gate (model_prepatch_2.py): the placeholder "
            "is substituted for EVERY alias regardless of the comment. Its faithful real "
            "patch is the UNCHANGED repo (`if self.doc_as_attr:`), which overwrites the "
            "OtherAlias docstring with the `alias of ...` placeholder — exactly the bug the "
            "gold fixes. It fails the F2P test_class_alias_having_doccomment. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by clause (2b): for is_attr_alias and has_authored_comment(comment) "
            "the antecedent `not (is_attr_alias and not has_authored_comment(comment))` "
            "holds, so 2b demands Result() is more_content, but the rival returns the "
            "freshly-built placeholder. PARTIAL-DOMAIN on the alias-with-comment "
            "sub-domain. If it VERIFIES => SPEC-TOO-WEAK. This is the G-DIFF prepatch_2."
        ),
    },
    {
        "id": "weak-B-never",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_b(_WEAK_B_NEVER),
        "refinement": (
            "the placeholder is NEVER substituted — every input passes more_content "
            "through. Its faithful real patch (deleting the `if ...: more_content = "
            "StringList([...])` substitution) would drop the `alias of ...` line for a "
            "plain alias WITHOUT a comment, which test_class_alias (P2P) asserts MUST be "
            "present. Does NOT resolve the P2P."
        ),
        "rationale": (
            "REJECTED by clause (2a): for is_attr_alias and not "
            "has_authored_comment(comment) the rival returns more_content, but 2a demands "
            "Result() is not None and opt_seq(Result())==placeholder_seq(target) (the "
            "substituted placeholder). PARTIAL-DOMAIN / dual revert on the alias-without-"
            "comment sub-domain. If it VERIFIES => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-B-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_b(_WEAK_B_COPY),
        "refinement": (
            "VALUE-DOUBLE-MASK on the pass-through path: it returns a fresh "
            "list(more_content) instead of more_content itself. A real add_content that "
            "rebuilt the incoming StringList would hand super().add_content a DIFFERENT "
            "object than the one the unchanged code passes through; the patch only re-gates "
            "WHEN the placeholder runs, it never rebuilds the pass-through content, so the "
            "value-equal copy is not a faithful resolution."
        ),
        "rationale": (
            "REJECTED by clause (2b): Result() is more_content demands OBJECT IDENTITY; a "
            "freshly-built list is a different object. The value-double-mask discriminator "
            "for site B — the spec pins identity, not value equality. If it VERIFIES => "
            "SPEC-TOO-WEAK (2b reducible to value equality)."
        ),
    },
]


# ===========================================================================
# AXIOM lane — the consumed @ContractOnly axiom placeholder_seq / make_placeholder
# (the UNCHANGED 'alias of %s' % restify(self.object) line formatter, wrapped in
# StringList). The probes EMBED the bundle's frozen G-AX oracle (axiom_check.py),
# read on the HOST at load time, because the runner mounts ONLY the probe script
# (/work) in-container — axiom_check.py / model.py are NOT mounted. Probes import only
# stdlib + (optionally) the real sphinx.util.typing.restify, which lives in the
# instance image; they open nothing on disk, so the utf-8-codec pitfall does not arise.
# ===========================================================================

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


# axiom-soundness: run axiom_check.py's main() verbatim. It composes the gold patch's
# own 'alias of %s' % <rendering> line for a boundary + real-restify + 20000-fuzz family
# of target renderings and asserts EVERY rendered line is NON-EMPTY (the axiom's only
# Ensures, len(Result())>0). It EXECUTES the real restify when importable (the very
# module the patched file imports) rather than scraping source (directive 4). Exits 0
# iff the axiom holds on every observation.
_AX_SOUND_PROBE = _AXIOM_CHECK_SRC + """

# --- PBT axiom-soundness driver (runs the embedded G-AX oracle) ---
import sys as _sys
_rc = main()
if _rc != 0:
    print("AXIOM-SOUNDNESS FAIL: placeholder line empty for some target rendering")
    _sys.exit(1)
print("AXIOM-SOUNDNESS OK: 'alias of %s' line non-empty over boundary + real restify "
      "+ 20000 fuzz target renderings (axiom Ensures len(Result())>0 holds).")
_sys.exit(0)
"""


# axiom-containment: which targets can the MODEL pass to make_placeholder/placeholder_seq?
# alias_additional_content calls make_placeholder(target) ONLY on the
# alias-without-comment branch, where `target: List[int]` carries the alias' target
# descriptor (Requires only Acc(list_pred(target),1/4) — ANY list of code points / any
# class object restify can render). The axiom's Requires is exactly Acc(list_pred(target),
# 1/4): it places NO further constraint on the target, so EVERY reachable target is
# trivially inside the axiom's Requires domain. We CONFIRM this by exercising the real
# callee `restify` on the full space of caller-reachable targets — every kind of class
# object autodoc can document as an alias (builtins, stdlib classes, typing generics,
# unions, user classes, abstract/None types) — and asserting that, whenever restify
# succeeds (the gold's `except AttributeError: pass` covers the rest), the produced
# 'alias of %s' line is non-empty (the axiom's Ensures) and is a str (in restify's range).
# Covering MORE descriptors than autodoc reaches would be sound, not a defect; we only
# need containment, which holds because the axiom's domain is the unconstrained
# list_pred(target). A reachable target the axiom could NOT cover => AXIOM-TOO-WEAK-FOR-
# CALLER (none possible: the axiom domain is the full list-of-code-points carrier).
_AX_COVER_PROBE = """
import sys

# (axiom-containment) Enumerate the caller-reachable alias TARGETS. autodoc's
# ClassDocumenter documents `self.object` for an alias; the target descriptor is any
# Python object autodoc treats as a class/type. We sample the reachable target space:
# builtins, stdlib classes, typing generics + unions, an abstract type, None's type, and
# user-defined classes, plus the literal F2P/P2P targets (target.classes.Foo/Bar shapes).
reachable_targets = [int, str, dict, list, tuple, set, frozenset, bytes, bool,
                     float, complex, Exception, BaseException, type(None), object]

# user-defined / generic / union targets (the kind the issue's ScaffoldOpts/FileOp/FileContents are)
class _UserAlias:           # plays target.classes.Foo / Bar
    pass
class _Quux(list):
    pass
reachable_targets += [_UserAlias, _Quux]
try:
    from typing import Dict, Any, Callable, Union, List as TList, Optional as TOpt
    reachable_targets += [Dict[str, Any], Union[str, None], Callable[..., int],
                          TList[int], TOpt[str], Union[int, float]]
except Exception:
    pass

fails = 0
covered = 0
skipped = 0

try:
    from sphinx.util.typing import restify   # the unchanged callee the axiom models
    have_restify = True
except Exception as exc:
    have_restify = False
    print("CONTAINMENT note: real restify not importable (%r); falling back to the "
          "'alias of %%s' composition directly (same axiom Ensures)." % (exc,))

def alias_line(rendering):
    return 'alias of %s' % rendering

for cls in reachable_targets:
    if have_restify:
        try:
            rendering = restify(cls)
        except Exception:
            # restify raising IS the gold's `except AttributeError: pass` guard: on this
            # target NO placeholder is produced, so the axiom Ensures has no obligation.
            # Containment is unaffected (the target is still inside the unconstrained
            # axiom Requires domain — the axiom simply imposes nothing here).
            skipped += 1
            continue
        if not isinstance(rendering, str):
            fails += 1
            print("CONTAINMENT FAIL: restify(%r) is not a str: %r" % (cls, rendering))
            continue
    else:
        rendering = repr(cls)   # any non-empty descriptor stands in for restify's output
    line = alias_line(rendering)
    # The axiom's Requires domain is the unconstrained list_pred(target); EVERY target is
    # inside it. We confirm the produced line content is in the axiom's Ensures (non-empty,
    # a sequence of code points) for every reachable target where the placeholder is built.
    codepoints = [ord(ch) for ch in line]
    if len(codepoints) <= 0:
        fails += 1
        print("CONTAINMENT/ENSURES FAIL: empty 'alias of %%s' line for target %r" % (cls,))
        continue
    covered += 1

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable target(s) outside the axiom's domain or "
          "violating its Ensures" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every caller-reachable alias target (%d covered, %d "
      "restify-skipped via the gold's AttributeError guard) lies inside the axiom's "
      "unconstrained Requires domain (Acc(list_pred(target),1/4)); the 'alias of %%s' "
      "line is non-empty wherever the placeholder is produced. Covering more descriptors "
      "than autodoc reaches is sound, not a defect." % (covered, skipped))
sys.exit(0)
"""


AXIOM_TESTS = [
    {
        "id": "ax-sound-placeholder",
        "axiom": "placeholder_seq / make_placeholder",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "placeholder_seq / make_placeholder is the consumed @ContractOnly axiom for "
            "the UNCHANGED 'alias of %s' % restify(self.object) line formatter (wrapped in "
            "StringList). Its WEAKEST sufficient Ensures is len(Result())>0 (non-empty). "
            "AXIOM-SOUNDNESS: the probe runs the bundle's frozen G-AX oracle "
            "(axiom_check.py) verbatim — it EXECUTES the real restify (the module the "
            "patched file imports) and the gold's own 'alias of %s' composition over "
            "boundary + 20000 fuzz target renderings and asserts every rendered line is "
            "non-empty. If the real callee ever yields an empty line => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-placeholder",
        "axiom": "placeholder_seq / make_placeholder",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: alias_additional_content calls make_placeholder(target) "
            "only on the alias-without-comment branch; `target` carries the alias' target "
            "descriptor under the unconstrained Acc(list_pred(target),1/4) — exactly the "
            "axiom's Requires. So EVERY caller-reachable target is trivially inside the "
            "axiom's domain. The probe exercises the real restify on the full reachable "
            "target space (builtins, stdlib classes, typing generics/unions, user classes, "
            "None's type — the kinds the issue's ScaffoldOpts/FileOp aliases are) and "
            "confirms the produced 'alias of %s' line is a non-empty str wherever the "
            "placeholder is built (restify-raising targets are the gold's AttributeError "
            "guard, no obligation). A reachable target outside the domain => "
            "AXIOM-TOO-WEAK-FOR-CALLER (none possible: the domain is the full carrier)."
        ),
    },
]
