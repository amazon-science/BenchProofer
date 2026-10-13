# properties.py — PBT falsification battery for sphinx-doc__sphinx-9591.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start / # impl-end region; the runner checks each with Nagini verify
# + markers.same_spec. AXIOM_TESTS are real-callee probes run in the instance
# Docker image (sphinx 4.2.0).
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py + refinement.md + mapping.md + instance):
#
#   handle_property_annotation(present: bool, typ: List[int]) -> AnnotationGroup
#
#   Models PyProperty.handle_signature's type-annotation block. The gold patch
#   turns the single inert annotation node `desc_annotation(typ, ': ' + typ)`
#   into `desc_annotation(typ, '', nodes.Text(': '), *_parse_annotation(typ,env))`
#   so a documented type becomes a CROSS-REFERENCE (pending_xref) rather than
#   literal text.
#
#   CARRIER: the annotation group is the FOUR PARALLEL sequences its rendered
#   children induce, plus ONE flag on the node holding them --
#     `is_xref[k]`             True iff child k is a cross-reference
#     `text[k]`                child k's rendered text
#     `is_bare_text[k]`        True iff child k is a BARE TEXT node, i.e. nothing
#                              but the characters it renders; False for EVERY
#                              marked-up inline node, rendered punctuation as much
#                              as a cross-reference
#     `holds_one_bare_text[k]` True iff child k holds exactly ONE inner node and
#                              that node is a bare text run; False for a bare text
#                              child (which holds nothing, being itself the run)
#                              and False for a marked-up child whose label is
#                              split across runs or further marked up
#     `is_annotation_node`     True iff the children are held in an ANNOTATION
#                              node (the node kind a rendered signature uses for a
#                              declared annotation)
#   The real parser splits a COMPOUND annotation into several nodes (xrefs +
#   rendered punctuation), so a fixed-length-2 carrier could not hold the real
#   result at all; the sequence carrier holds any width, and the axioms below
#   supply the real widths.
#   WHY FOUR sequences and a flag, and not two sequences: the carrier has to be
#   INJECTIVE on every distinction the F2P oracle draws, and `assert_node`
#   (sphinx/testing/util.py:48-83) draws four:
#     (a) WRAPPER CLASS. `[desc_annotation, ...]` runs `assert isinstance(node,
#         cls)` on the wrapper BEFORE inspecting any child. Hence the flag; see
#         the wrapper-swap and empty-annotation-node rivals.
#     (b) CHILD KIND vs CHILD TEXT. A bare-str spec (the expected `": "` child) is
#         matched by node EQUALITY, which nodes.Text satisfies -- Text subclasses
#         str -- and which no Element satisfies. So `nodes.Text(': ')` and
#         `addnodes.desc_sig_punctuation('', ': ')` are DIFFERENT renderings the
#         oracle tells apart, while agreeing on cross-reference-ness AND on text.
#         Hence `is_bare_text`; see the separator-as-rendered-punctuation rival.
#     (c) CHILD INSIDE. `[pending_xref, "str"]` requires the cross-reference to
#         have EXACTLY ONE child equal to "str" (`assert len(node) == len(cls)`),
#         so a cross-reference spelling `str` across two inner runs, or wrapping
#         the label in further markup, is rejected while agreeing on kind, on text
#         AND on bare-text-ness. Hence `holds_one_bare_text`; see the
#         rewrite-the-xref-inside rival.
#     (d) TEXT itself, which `text` carries.
#   Each dropped axis is a pair of renderings the carrier would map to ONE value
#   while the oracle separates them -- i.e. an impl the spec would verify and the
#   F2P test would fail. The three added observables are measured against the real
#   patched code by conformance_check.py (G-CONF, 100k inputs, all five axes) and
#   the two new parser axioms by axiom_check.py (G-AX, both config settings).
#
#   READ-ONLY input (frame-mutation MANDATORY):
#     Requires(Acc(list_pred(typ), 1/2))   <- HALF permission on typ
#   Precondition also: Requires(Implies(present, len(typ) > 0)).
#   NOTE the precondition admits the WHOLE non-empty annotation-string domain --
#   `:type:` is `directives.unchanged`, so any text at all can arrive here,
#   including strings the shared parser refuses. Nothing is excluded.
#
#   Load-bearing postcondition clauses:
#     (frame) Ensures(Acc(list_pred(typ), 1/2))       give back typ's 1/2 perm
#     (own)   Ensures(Acc(Result().is_xref) and Acc(Result().text)
#                     and Acc(Result().is_bare_text)
#                     and Acc(Result().holds_one_bare_text)
#                     and Acc(Result().is_annotation_node))
#     (C3 LEN)Ensures(len(Result().is_xref) == len(Result().text))
#             Ensures(len(Result().is_bare_text) == len(Result().is_xref))
#             Ensures(len(Result().holds_one_bare_text) == len(Result().is_xref))
#                 -- one entry per rendered child, in all four sequences
#     (C4 ABS)Ensures(Implies(not present, len(Result().is_xref) == 0))
#     (C5 DOM)Ensures(Implies(present, accepted(ToSeq(typ))))
#                 -- RETURNING A GROUP AT ALL is an assertion that the shared
#                    parser ACCEPTS the declared annotation. The rendering is
#                    delegated to that parser, so the parser's domain is the
#                    domain on which a group exists. Also the definedness
#                    condition of C6/C7 (whose axioms Require `accepted`), which
#                    is why it precedes them in the spec text.
#     (C6 KND)Ensures(Implies(present,
#                 Result().is_xref == PSeq(False) + annotation_kinds(ToSeq(typ))))
#                 -- a separator that is not a cross-reference, then exactly the
#                    parser's node kinds
#     (C7 TXT)Ensures(Implies(present,
#                 Result().text == PSeq(sep_text()) + annotation_texts(ToSeq(typ))))
#                 -- separator text ": ", then exactly the parser's node texts
#     (C10 BARE)Ensures(Implies(present, Result().is_bare_text
#                 == PSeq(True) + annotation_bare_text(ToSeq(typ))))
#                 -- the separator child is a BARE TEXT node, and every child
#                    after it keeps the KIND the shared parser gave it. Carrying
#                    the separator's two characters in a marked-up inline node
#                    (rendered punctuation, an inline wrapper) is a different
#                    child and does not discharge this: C6 and C7 are silent
#                    about it, because such a node is equally not a
#                    cross-reference and carries exactly the same text.
#     (C11 IN)Ensures(Implies(present, Result().holds_one_bare_text
#                 == PSeq(False) + annotation_holds_one_bare_text(ToSeq(typ))))
#                 -- what each child HOLDS, one level in: the separator holds no
#                    inner node (it IS the run it renders), and every child after
#                    it keeps the INSIDE the shared parser gave it. Rebuilding one
#                    of the parser's nodes at the same kind with the same
#                    characters but a different inside -- its label split across
#                    two runs, or wrapped in further markup -- is a different child
#                    and does not discharge this: C6, C7 and C10 are all silent
#                    about it, since such a node is equally a cross-reference,
#                    equally not a bare text node, and carries the same text.
#     (C12 GRP)Ensures(Result().is_annotation_node == present)
#                 -- a declared annotation contributes exactly ONE ANNOTATION node
#                    holding those children, and a declared-nothing contributes no
#                    such node. WHICH node holds them is this operation's own
#                    choice and never the parser's, so no axiom about the parser
#                    can pin it and it has to be stated: putting exactly the right
#                    children inside any other inline wrapper, or contributing them
#                    loose, is a different contribution to the rendered signature.
#     (C8 XREF)Ensures(Implies(present and is_simple_name(ToSeq(typ)),
#                 Result().is_xref == PSeq(False, True)
#                 and Result().text == PSeq(sep_text(), ToSeq(typ))
#                 and Result().is_bare_text == PSeq(True, False)
#                 and Result().holds_one_bare_text == PSeq(False, True)))
#                 -- a SIMPLE type name renders as the separator, a bare text
#                    child holding no inner node, plus ONE cross-reference
#                    carrying that name -- which is not a bare text child, and
#                    which holds that name as exactly ONE bare text run inside it.
#     (C9 REJ)Exsures(AnnotationRejected, Acc(list_pred(typ), 1/2)
#                 and present and not accepted(ToSeq(typ)))
#                 -- an annotation the shared parser REJECTS yields NO annotation
#                    group: the rejection propagates, unabsorbed. C5 and C9 are
#                    jointly exhaustive on a declared annotation -- a group where
#                    the parser accepts, a signal where it rejects, and nothing
#                    else on either side -- so neither arm can be traded for the
#                    other (see the swallow / fallback / always-raise /
#                    refuse-compound rivals below).
#   sep_text() is @Pure, fully unfolded == PSeq(58,32) (": "). is_simple_name /
#   is_name_start / is_name_char are @Pure code-point predicates (a non-empty run
#   of [A-Za-z_][A-Za-z0-9_]*), fully unfolded.
#
#   The DISCRIMINATING content is C6's leading `False` together with C8's
#   `PSeq(False, True)`, C10's leading `True`, C11's leading `False` and C12: the
#   separator does not link, is a BARE TEXT child and holds nothing inside; the
#   simple type name is a CROSS-REFERENCE holding the name as one bare text run;
#   and the whole thing sits in an annotation node -- precisely the pre/post-patch
#   difference plus every other axis the F2P
#   harness compares. The pre-patch (model_prepatch.py) emits ONE inert node
#   `": "+typ` without consulting the shared parser at all, and so fails C5 (it
#   produces a group for annotations the parser does not accept) as well as C6
#   (kinds sequence) and C8 (no xref entry).
#
#   ORACLE GROUNDING: C8 pins the SIMPLE-name case entirely in terms of the input
#   arg `typ` (PSeq(sep_text(), ToSeq(typ)) is fully unfolded), so fabricating
#   that triple directly is a *behaviourally-correct* reimplementation for simple
#   names, not a wrong echo -- BUT ONLY once the parser has been consulted, since
#   C5 can be discharged no other way. It is NOT sufficient for the general case:
#   C6/C7/C10 pin every OTHER annotation shape to the axiomatized parser
#   widths/texts/kinds, which a fabricator cannot guess. POS_FAB below is
#   therefore a POSITIVE CONTROL only in the simple-name arm and must still route
#   the general arm through the axioms; UNGROUNDED_ECHO, which fabricates the same
#   triple WITHOUT consulting the parser, is a REJECT case.
#
#   AXIOMS (A-consumed): accepted / annotation_kinds / annotation_bare_text /
#   annotation_holds_one_bare_text / annotation_texts / rendered_nodes <-> the
#   DOMAIN and the rendered output of the UNCHANGED callee _parse_annotation.
#     accepted(s)      -- the parser's DOMAIN: True iff it yields a node list for
#                         `s`. The parser is PARTIAL: some annotation strings it
#                         refuses outright (it raises rather than rendering), so
#                         the three sequence axioms below carry
#                         Requires(accepted(s)) and are defined only there.
#                      Ensures(Implies(is_simple_name(s), Result()))
#                         -- the relied-on fact: a SIMPLE type name is ALWAYS
#                            accepted, so the discriminating clause C8 is
#                            unconditional on the F2P class.
#     annotation_kinds: Requires(accepted(s))
#                       Ensures(Implies(is_simple_name(s), Result()==PSeq(True)))
#     annotation_bare_text: Requires(accepted(s))
#                       Ensures(len(Result()) == len(annotation_kinds(s)))
#                       Ensures(Implies(is_simple_name(s), Result()==PSeq(False)))
#                         -- the SAME single measurement annotation_kinds' fact
#                            rests on, read on the other flag: a simple name
#                            yields exactly ONE node and that node is a
#                            cross-reference (addnodes.pending_xref), which is an
#                            Element and therefore not a bare text node. No
#                            further claim about the parser is made: outside the
#                            simple-name class only the width is asserted.
#     annotation_holds_one_bare_text: Requires(accepted(s))
#                       Ensures(len(Result()) == len(annotation_kinds(s)))
#                       Ensures(Implies(is_simple_name(s), Result()==PSeq(True)))
#                         -- the SAME single node read one level in: a simple
#                            name's cross-reference holds exactly ONE inner node
#                            and that node is the bare text run spelling the name.
#                            Measured in axiom_check.py under the default config
#                            (the F2P app's), which mapping.md §3.1 records as the
#                            binding one. This is NOT `not annotation_bare_text`:
#                            axiom_check.py finds 1320 real parser nodes that read
#                            False on BOTH (a marked-up node whose label is not one
#                            plain run, e.g. the cross-reference under
#                            python_use_unqualified_type_names = True, whose label
#                            is a pair of pending_xref_condition children).
#     annotation_texts: Requires(accepted(s))
#                       Ensures(len(Result()) == len(annotation_kinds(s)))
#                       Ensures(Implies(is_simple_name(s), Result()==PSeq(s)))
#     rendered_nodes:   the runtime form -- on an accepted string it returns that
#                       string's node list (Ensures accepted(ToSeq(typ)) + the
#                       four sequence equalities); on a rejected one it signals
#                       AnnotationRejected (Exsures ... not accepted(ToSeq(typ))).
#                       Returning normally is ITSELF the witness of acceptance:
#                       the caller does not get to decide the domain. Its kind and
#                       inside sequences are read off the parser's own node list,
#                       so a caller can splice those nodes but has no node of its
#                       own to substitute at those positions. It carries NO
#                       is_annotation_node claim -- a bare node list is not held in
#                       anything, and which node holds the spliced children is the
#                       CALLER's choice, which is why C12 has to state it.
#     Consumed in the gold impl: the single `rendered_nodes(typ)` call discharges
#     C5 on the returning path and C9 on the signalling path, the concatenations
#     discharge C6/C7/C10/C11, the literal `True`/`False` in the two constructor
#     calls discharges C12, and the simple-name Ensures discharge C8. The patch
#     does NOT modify _parse_annotation, so axiomatising it is sound.
#
# F2P: tests/test_domain_py.py::test_pyproperty -- the property's `:type: str`
#      annotation must render as `[desc_annotation, (": ", [pending_xref,"str"])]`
#      instead of the pre-patch `[desc_annotation, ": str"]`. Read through
#      assert_node (sphinx/testing/util.py:48-83) that expectation observes FOUR
#      things, and the carrier records one for each:
#        * the wrapper is a `desc_annotation` and there is exactly one of it
#          -> C12 (`is_annotation_node == present`);
#        * it has exactly TWO children, the first not a link and the second one
#          -> C3 / C6 / C8;
#        * the `": "` entry is a BARE STRING, and assert_node matches a str spec by
#          node EQUALITY -- satisfied by nodes.Text (a str subclass) and by no
#          Element -- so the harness distinguishes the separator's node KIND, not
#          only its characters -> C10;
#        * `[pending_xref, "str"]` requires the cross-reference to have EXACTLY ONE
#          child equal to "str", so a label split across two runs fails
#          `assert len(node) == len(cls)` -> C11.
# P2P: test_function_signatures / test_domain_py_xrefs / test_domain_py_objects /
#      test_resolve_xref_for_properties (ordinary signatures/xrefs must still work).

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9591"
FLOAT_ENCODING = None  # meta.json float_encoding == null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The GOLD impl region. Every rival edits ONLY text inside the
# # impl-start / # impl-end region (same_spec GUARANTEED).
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""


# === POSITIVE CONTROL 1 (soundness) — SIMPLE-NAME FAST PATH =================
# Structurally-different but CORRECT impl: consult the shared parser (as any
# faithful impl must -- the acceptance of the annotation is not the caller's to
# decide), then split on is_simple_name and build the simple-name group DIRECTLY
# as PSeq(False, True) / PSeq(sep_text(), ToSeq(typ)) -- the shape C8 pins,
# grounded in the input arg -- while routing every OTHER annotation shape through
# the axioms (C6/C7 pin those to the real parser, which a fabricator cannot
# guess). This is exactly the rendering the real code produces for `:type: str`,
# so it MUST verify; if it cannot, the spec rejects a faithful correct impl =>
# SPEC-TOO-STRONG.
_POS_FAB = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        if is_simple_name(ToSeq(typ)):
            simple_kinds = PSeq(False, True)  # type: PSeq[bool]
            simple_texts = PSeq(sep_text(), ToSeq(typ))  # type: PSeq[PSeq[int]]
            simple_bares = PSeq(True, False)  # type: PSeq[bool]
            simple_holds = PSeq(False, True)  # type: PSeq[bool]
            return AnnotationGroup(simple_kinds, simple_texts, simple_bares,
                                   simple_holds, True)
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
POS_FAB = _swap(_BASE, _GOLD_IMPL, _POS_FAB)


# === POSITIVE CONTROL 2 (soundness) — LOCAL REORDER + FRAMING ASSERT ========
# Build both sequences into locals in the opposite order, construct the record,
# and carry a framing Assert of the simple-name consequence (C8) before
# returning. No loop, no loop-direction flip, no auto-undischargeable lemma
# (directives 2 & 3 safe): only local construction order is reshaped and every
# obligation is unchanged. MUST verify, else SPEC-TOO-STRONG.
_POS_REORDER = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        grp = AnnotationGroup(kinds, texts, bares, holds, True)
        Assert(Implies(is_simple_name(ToSeq(typ)),
                       grp.is_xref == PSeq(False, True)
                       and grp.is_bare_text == PSeq(True, False)
                       and grp.holds_one_bare_text == PSeq(False, True)))
        Assert(grp.is_annotation_node)
        return grp
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
POS_REORDER = _swap(_BASE, _GOLD_IMPL, _POS_REORDER)


# === ADMISSIBILITY =========================================================
# Insert a probe block right after `# impl-start`, BEFORE any gold obligation
# (so every following obligation is preserved verbatim). It constructs an
# F2P-shaped annotation: present=True with typ = code points of "str"
# ([115,116,114]) and asserts the Requires predicates are establishable AND that
# this input is a simple name, that the shared parser therefore ACCEPTS it, and
# that the axioms then pin its rendering to a single cross-reference which is NOT
# a bare text node (so the discriminating C8 arm, both the xref flag and the
# child-kind flag, is REACHABLE, not vacuous, on the F2P input). If this cannot
# verify, the precondition is unsatisfiable for the normal `:type: str`
# input => PRECOND-TOO-STRONG.
# (We exercise the Requires predicates directly rather than a self-call, which
# would need a permission split the spec does not carry -- a proof gap, not a
# spec defect.)
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: the F2P-shaped annotation `:type: str` (present=True,
    # typ = code points of "str") establishes the Requires predicates
    # (list_pred ownership + the guarded len(typ) > 0 clause), is a simple
    # name, is therefore ACCEPTED by the shared parser (so the returning arm C5
    # is reachable and the signalling arm C9 is not forced), and renders as a
    # single cross-reference that is not a bare text node -- so both halves of
    # the discriminating clause C8 (the xref flag AND the child-kind flag) are
    # reachable on the F2P input, and C10's tail is a real constraint there
    # rather than a vacuous one.
    probe = [115, 116, 114]  # type: List[int]
    Assert(list_pred(probe))
    Assert(len(probe) == 3)
    Assert(Implies(True, len(probe) > 0))
    Assert(ToSeq(probe)[0] == 115)
    Assert(is_simple_name(ToSeq(probe)))
    Assert(accepted(ToSeq(probe)))
    Assert(annotation_kinds(ToSeq(probe)) == PSeq(True))
    Assert(annotation_bare_text(ToSeq(probe)) == PSeq(False))
    Assert(annotation_holds_one_bare_text(ToSeq(probe)) == PSeq(True))
    Assert(annotation_texts(ToSeq(probe)) == PSeq(ToSeq(probe)))"""
ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ============================================

# --- W1 FRAME-MUTATION (MANDATORY: typ is read-only Acc(list_pred(typ),1/2)).
# A rival that WRITES to the read-only `typ` input (appends a code point) before
# building the result. With only HALF permission the write CANNOT be performed
# -- the rival fails for INSUFFICIENT PERMISSION at the mutation, not for a value
# mismatch. Every gold obligation is kept verbatim so the rejection is
# attributable to the write. A byte-fuzzer never constructs this.
_W1_FRAME = """    typ.append(63)
    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
FRAME_TYP_WRITE = _swap(_BASE, _GOLD_IMPL, _W1_FRAME)


# --- W2 SEPARATOR AS CROSS-REFERENCE (value double-mask on the leading kind).
# Emit the separator as a cross-reference instead of a bare text child: is_xref
# True and, faithfully to that (a cross-reference is a marked-up inline node),
# is_bare_text False. The TEXT sequence is still exactly right (C7 holds), so only
# the separator child's KIND diverges -- the link-vs-text distinction a text-only
# proxy would miss. It is rejected by C6's leading False and by C10's leading
# True; the sharper rival W16, which keeps the xref flag right too, isolates C10
# on its own.
_W2_SEPXREF = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(True) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(False) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(True) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
SEP_AS_XREF = _swap(_BASE, _GOLD_IMPL, _W2_SEPXREF)


# --- W3 TYPE AS INERT TEXT (the PRE-PATCH bug; load-bearing discriminator).
# Render the annotation as a second BARE TEXT node carrying the type name
# instead of the parser's cross-reference. Widths and texts match for a simple
# name, but the kinds sequence is PSeq(False, False), violating C6 and C8's
# PSeq(False, True) (and its bare-text sequence PSeq(True, True) violates C10's
# tail, since the parser's node for a simple name is not a bare text node). This
# is the modelled image of the pre-patch
# `desc_annotation(typ, ': ' + typ)`: the type is NOT cross-referenced -- exactly
# the bug the gold patch fixes. It also never consults the shared parser, so it
# additionally claims a group exists for annotations the parser does not accept
# (C5) -- which is what the real pre-patch code does, since it renders `b"x"` as
# the inert text `: b"x"` where the delegating code has no group to render.
_W3_INERT = """    if present:
        kinds = PSeq(False, False)  # type: PSeq[bool]
        texts = PSeq(sep_text(), ToSeq(typ))  # type: PSeq[PSeq[int]]
        bares = PSeq(True, True)  # type: PSeq[bool]
        holds = PSeq(False, False)  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
TYPE_INERT = _swap(_BASE, _GOLD_IMPL, _W3_INERT)


# --- W4 WRONG SEPARATOR TEXT (partial-domain on the leading text).
# Emit the separator text as PSeq(58) (":" only, dropping the trailing space)
# instead of sep_text() == PSeq(58,32). The kinds sequence is correct, but C7's
# text sequence is one code point short in its first entry.
_W4_BADSEP = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(PSeq(58)) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
WRONG_SEP_TEXT = _swap(_BASE, _GOLD_IMPL, _W4_BADSEP)


# --- W5 WRONG TYPE TEXT (partial-domain on the annotation texts).
# Carry the SEPARATOR text in the annotation slot rather than the parser's texts:
# the kinds sequence is right (so the xref flag is right) but C7/C8's text
# sequence is wrong for any typ != ": ", and its fixed width 2 also desyncs from
# the kinds sequence on every compound annotation.
_W5_BADTYPE = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text(), sep_text())  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
WRONG_TYPE_TEXT = _swap(_BASE, _GOLD_IMPL, _W5_BADTYPE)


# --- W6 EMIT WHEN ABSENT (partial-domain / drop the present guard).
# Always emit the group, even when `present` is False. Correct on the
# present==True sub-domain, violates C4 (Implies(not present, len == 0)) on the
# no-annotation sub-domain (the `if not typ` case: no group must appear).
_W6_ALWAYS = """    parsed = rendered_nodes(typ)  # type: AnnotationGroup
    kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
    texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
    bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
    holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
    return AnnotationGroup(kinds, texts, bares, holds, True)"""
EMIT_WHEN_ABSENT = _swap(_BASE, _GOLD_IMPL, _W6_ALWAYS)


# --- W7 DROP THE SEPARATOR (partial-domain: emit only the parsed nodes).
# Return the parser's sequences with no separator prepended. The type IS
# cross-referenced, so a discriminator that only asked "is there an xref?" would
# pass this; C6/C7 reject it because the leading inert ": " child is missing.
_W7_NOSEP = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        return AnnotationGroup(parsed.is_xref, parsed.text, parsed.is_bare_text,
                               parsed.holds_one_bare_text, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
NO_SEPARATOR = _swap(_BASE, _GOLD_IMPL, _W7_NOSEP)


# --- W8 ORDER SWAP (parsed nodes first, separator appended last).
# Both children are present and of the right kinds/texts, only the ORDER is
# reversed, so the rendered annotation reads `str: ` instead of `: str`. Rejected
# by C6/C7, which pin the separator as the FIRST entry of each sequence.
_W8_ORDER = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = parsed.is_xref + PSeq(False)  # type: PSeq[bool]
        texts = parsed.text + PSeq(sep_text())  # type: PSeq[PSeq[int]]
        bares = parsed.is_bare_text + PSeq(True)  # type: PSeq[bool]
        holds = parsed.holds_one_bare_text + PSeq(False)  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
ORDER_SWAP = _swap(_BASE, _GOLD_IMPL, _W8_ORDER)


# --- W9 FIXED WIDTH 2 (the OLD over-strong shape, now a REJECT case).
# Consult the parser (so C5 is discharged) but then IGNORE its node list and emit
# exactly two children -- the separator plus ONE cross-reference carrying the
# WHOLE annotation string. That is right for a simple name and wrong for every
# compound annotation, where the real parser renders several nodes (e.g.
# "List[int]" -> xref "List", punct "[", xref "int", punct "]"). Rejected by
# C6/C7, whose widths and texts come from the axiomatized real parser. This rival
# is exactly the claim an earlier revision of this spec made, so it is the
# regression guard against re-introducing it.
_W9_FIXED2 = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False, True)  # type: PSeq[bool]
        texts = PSeq(sep_text(), ToSeq(typ))  # type: PSeq[PSeq[int]]
        bares = PSeq(True, False)  # type: PSeq[bool]
        holds = PSeq(False, True)  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
FIXED_WIDTH_TWO = _swap(_BASE, _GOLD_IMPL, _W9_FIXED2)


# --- W10 LENGTH DESYNC (violate the one-entry-per-child invariant C3).
# Emit a kinds sequence and a texts sequence of DIFFERENT lengths, so the pair no
# longer describes a well-formed child list. C6/C7 pin both, and C3 pins their
# lengths equal; a spec that only constrained one sequence would miss this.
_W10_DESYNC = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text + PSeq(sep_text())  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
LENGTH_DESYNC = _swap(_BASE, _GOLD_IMPL, _W10_DESYNC)


# --- W11 SWALLOW THE REJECTION (absorb it into the no-annotation rendering).
# Consult the parser, but when it refuses the annotation, catch that and return
# the EMPTY group -- i.e. silently render no annotation at all for a declared
# one, as though the `:type:` option had been absent. Rejected by C5: returning a
# group is an assertion that the parser accepted the string, and here it did not.
# This is the first of the rivals that attack the C5/C9 exhaustiveness pair
# rather than the sequence content: it keeps every accepted-string obligation
# exactly right and diverges ONLY on the rejecting class.
_W11_SWALLOW = """    if present:
        try:
            parsed = rendered_nodes(typ)  # type: AnnotationGroup
        except AnnotationRejected:
            return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
SWALLOW_REJECTION = _swap(_BASE, _GOLD_IMPL, _W11_SWALLOW)


# --- W12 INERT FALLBACK ON REJECTION (the pre-patch rendering as a safety net).
# Consult the parser, and when it refuses, fall back to the PRE-PATCH shape for
# that annotation: one inert text node carrying ": " + the annotation string.
# Every accepted string is rendered exactly right, so only the rejecting class
# diverges -- and there it produces a group where the delegating operation
# produces none. Rejected by C5. This is the subtlest rival in the battery: the
# fallback is what a reader who wanted "never fail" would write, and it is not
# what delegating to the shared parser does.
_W12_FALLBACK = """    if present:
        fell = False  # type: bool
        parsed = AnnotationGroup(no_kinds(), no_texts(), no_kinds(),
                                 no_kinds(), False)  # type: AnnotationGroup
        try:
            parsed = rendered_nodes(typ)
        except AnnotationRejected:
            fell = True
        if fell:
            inert = PSeq(sep_text() + ToSeq(typ))  # type: PSeq[PSeq[int]]
            return AnnotationGroup(PSeq(False), inert, PSeq(True), PSeq(False),
                                   True)
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
INERT_FALLBACK = _swap(_BASE, _GOLD_IMPL, _W12_FALLBACK)


# --- W13 UNGROUNDED ORACLE ECHO (never does the work; derives it from the arg).
# Fabricate the C8 pair -- separator plus one cross-reference carrying the whole
# annotation string -- straight from the argument, never consulting the shared
# parser at all. Behaviourally this is W9 minus the delegation, and it is the
# canonical ungrounded-oracle shape: every value it returns is a syntactic
# function of its inputs. Rejected by C5, which no impl can discharge without
# actually consulting the parser: whether an annotation is accepted is not
# derivable from the annotation's code points inside the model. This case is the
# guard that the Exsures arm did not turn the specification into something an
# echo can satisfy.
_W13_ECHO = """    if present:
        kinds = PSeq(False, True)  # type: PSeq[bool]
        texts = PSeq(sep_text(), ToSeq(typ))  # type: PSeq[PSeq[int]]
        bares = PSeq(True, False)  # type: PSeq[bool]
        holds = PSeq(False, True)  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
UNGROUNDED_ECHO = _swap(_BASE, _GOLD_IMPL, _W13_ECHO)


# --- W14 ALWAYS REJECT (take the signalling arm unconditionally).
# Signal AnnotationRejected for EVERY declared annotation, rendering no
# annotation group ever. This is the degenerate over-use of the C9 arm, and the
# proof that C9 is not a free escape hatch: rejected because C9 requires
# `not accepted(ToSeq(typ))`, and a simple type name IS accepted (the `accepted`
# axiom's Ensures), so this rival cannot signal on `:type: str`.
_W14_ALWAYS_REJECT = """    if present:
        raise AnnotationRejected()
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
ALWAYS_REJECT = _swap(_BASE, _GOLD_IMPL, _W14_ALWAYS_REJECT)


# --- W15 REFUSE EVERY COMPOUND ANNOTATION (reject outside the simple-name arm).
# Render simple type names correctly and signal a rejection for every other
# annotation. This satisfies the discriminating clause C8 on the F2P input and
# still fails, because the parser DOES accept `List[int]`, `int | None`, `...`
# and the rest: C9 may only be taken where the parser genuinely refuses. Pairs
# with W14 to pin the rejecting class exactly, from the other side.
_W15_REFUSE_COMPOUND = """    if present:
        if not is_simple_name(ToSeq(typ)):
            raise AnnotationRejected()
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
REFUSE_COMPOUND = _swap(_BASE, _GOLD_IMPL, _W15_REFUSE_COMPOUND)


# --- W16 SEPARATOR AS RENDERED PUNCTUATION (kind double-mask on child 0).
# Emit the separator as a MARKED-UP inline node -- rendered punctuation carrying
# the same two characters ": " -- instead of a bare text child. Both the kinds
# sequence and the texts sequence are EXACTLY the gold ones (C6, C7 and the whole
# of C8's xref/text content hold: the separator is still not a cross-reference and
# still carries ": ", and the type is still cross-referenced), so every clause
# about which characters appear and which child links is satisfied. Only the
# CHILD-KIND flag of the separator diverges: False where C10 requires True. This
# is the sharpest rival in the battery -- a spec whose carrier recorded only
# "is it a cross-reference?" and "what text does it carry?" could not tell it from
# the gold rendering at all, because the two renderings agree on every one of
# those observations.
_W16_SEP_PUNCT = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(False) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(True) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
SEP_AS_PUNCT = _swap(_BASE, _GOLD_IMPL, _W16_SEP_PUNCT)


# --- W17 DELEGATE THEN DISCARD (consult the parser, render bare text anyway).
# Call the shared parser -- so the refusal really does propagate and C5/C9 are
# both discharged -- and then IGNORE its node list, rendering the annotation as a
# second BARE TEXT child carrying the whole annotation string. Pairs with W3: W3
# renders the same thing without consulting the parser (so it fails C5 too),
# whereas this rival isolates the rendering obligation from the delegation one --
# it fails ONLY because the annotation's child must be a cross-reference and not a
# bare text run (C6/C8/C10). It is also the tail-side probe of the child-kind
# clause: every child it emits is a bare text node, where the parser's own nodes
# are not.
_W17_DELEGATE_DISCARD = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False, False)  # type: PSeq[bool]
        texts = PSeq(sep_text(), ToSeq(typ))  # type: PSeq[PSeq[int]]
        bares = PSeq(True, True)  # type: PSeq[bool]
        holds = PSeq(False, False)  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
DELEGATE_DISCARD = _swap(_BASE, _GOLD_IMPL, _W17_DELEGATE_DISCARD)


# --- W18 WRAPPER SWAP (the group is NOT an annotation node).
# Emit exactly the gold children, in the gold order, at the gold kinds, with the
# gold insides -- and hold them in something that is NOT an annotation node (any
# other inline wrapper, or contributed loose into the signature). Every clause
# about the CHILDREN (C3/C5/C6/C7/C8/C10/C11) is satisfied verbatim: this rival
# differs from gold in exactly one bit. Rejected by C12
# (`Result().is_annotation_node == present`). WHICH node holds the group is the
# emitting operation's own choice -- the parser makes no such choice, so its
# axioms cannot pin it -- and it is the FIRST thing the F2P oracle checks
# (`assert_node(..., [desc_annotation, ...])` matches the wrapper's class before
# it looks at a single child). A carrier that recorded only the children would map
# this rendering and the gold one to the same value.
_W18_WRAPPER_SWAP = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, False)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
WRAPPER_SWAP = _swap(_BASE, _GOLD_IMPL, _W18_WRAPPER_SWAP)


# --- W19 REWRITE THE CROSS-REFERENCE'S INSIDE (same kind, same text, wrong run).
# Consult the parser and keep its node list's WIDTH, its KINDS and its TEXTS
# exactly -- so C3, C5, C6, C7 and the xref/text/bare-text halves of C8 all hold
# -- but report the tail's child-INSIDE axis as the parser's child-KIND axis
# instead of its own. Behaviourally this is a caller that does not splice the
# parser's nodes but REBUILDS each one at the same kind with the same characters
# and a different inside: a cross-reference whose label is split across two runs,
# or wrapped in further markup, reads False where the parser's own node reads
# True. Rejected by C11
# (`holds_one_bare_text == PSeq(False) + annotation_holds_one_bare_text(typ)`),
# and by nothing else: there is no axiom relating annotation_bare_text to
# annotation_holds_one_bare_text, so substituting one for the other is not
# derivable. This is the tail-side twin of W16 and the sharpest rival against the
# fourth sequence -- the F2P oracle sees it, because `[pending_xref, "str"]`
# requires the cross-reference to have EXACTLY ONE child equal to "str", which a
# two-run label does not.
_W19_XREF_INTERIOR = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.is_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)"""
XREF_INTERIOR = _swap(_BASE, _GOLD_IMPL, _W19_XREF_INTERIOR)


# --- W20 CONTRIBUTE AN EMPTY ANNOTATION NODE WHEN NOTHING WAS DECLARED.
# Render the declared case exactly as gold, and in the no-annotation case emit an
# annotation node holding NO children rather than contributing nothing at all.
# The child sequences stay empty, so C4 (`not present -> len == 0`) is satisfied
# and every sequence clause holds; only the group flag diverges, True where C12
# requires False. Pairs with W18 from the other side, pinning
# `is_annotation_node == present` at both ends: W18 fails to contribute the
# annotation node when one is due, this one contributes one when none is. An
# empty `desc_annotation` is not nothing -- the F2P assertion counts the
# signature's children.
_W20_EMPTY_GROUP_NODE = """    if present:
        parsed = rendered_nodes(typ)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq[bool]
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq[PSeq[int]]
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq[bool]
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq[bool]
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), True)"""
EMPTY_GROUP_NODE = _swap(_BASE, _GOLD_IMPL, _W20_EMPTY_GROUP_NODE)


SPEC_TESTS = [
    {
        "id": "pos-simple-name-fast-path",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_FAB,
        "rationale": "structurally-different CORRECT impl: consult the shared "
        "parser, then branch on is_simple_name and build the simple-name group "
        "DIRECTLY as PSeq(False, True) / PSeq(sep_text(), ToSeq(typ)) (the shape "
        "C8 pins, grounded in the input arg), routing every other annotation "
        "shape through the axioms. This is exactly what the real code renders for "
        "`:type: str`. MUST verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-local-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl: build the two "
        "sequences into locals in the opposite order, then construct the record "
        "and carry a framing Assert of the simple-name consequence. No loop / no "
        "loop-direction flip / no auto-undischargeable lemma (directives 2 & 3 "
        "safe). MUST verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-type-str",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a positive-control block constructs the F2P-shaped "
        "annotation `:type: str` (typ = code points of \"str\" = [115,116,114]) "
        "and asserts the Requires predicates (list_pred ownership + the guarded "
        "len(typ) > 0 clause) hold, that it IS a simple name, that the shared "
        "parser therefore ACCEPTS it (so the returning arm C5 is reachable and "
        "the signalling arm C9 is not forced on the F2P input), and that the "
        "axioms then pin the parser output to a single cross-reference -- so the "
        "precondition admits the normal property type annotation AND the "
        "discriminating clause is reachable on it, else PRECOND-TOO-STRONG. "
        "NOTE the precondition is the whole non-empty annotation-string domain "
        "and admits the rejecting class too (see W11-W15).",
    },
    {
        "id": "frame-typ-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_TYP_WRITE,
        "refinement": "a faithful real patch mutating the type-name carrier (e.g. "
        "`typ += '?'` on the str the property options hold) before building the "
        "annotation would corrupt the rendered type name AND the desc_annotation's "
        "raw-source argument `typ`; test_pyproperty asserts the rendered xref text "
        "is exactly \"str\", and other property/signature P2P tests read the same "
        "options-derived type -- a mutated `typ` renders the wrong name and would "
        "NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: writing `typ` needs full "
        "permission but only Acc(list_pred(typ),1/2) is held (and the frame "
        "Ensures must return that 1/2 intact). MANDATORY frame-mutation probe for "
        "the read-only input; a byte-fuzzer never constructs it.",
    },
    {
        "id": "separator-as-xref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SEP_AS_XREF,
        "refinement": "a faithful real patch emitting the separator as a "
        "cross-reference (e.g. routing the literal \": \" through type_to_xref / "
        "the shared annotation parser instead of nodes.Text(': ')) would make the "
        "F2P assertion `[desc_annotation, (\": \", [pending_xref,\"str\"])]` fail: "
        "the first child must be a plain Text node, not a pending_xref -- the "
        "harness compares node kinds and would NOT resolve.",
        "rationale": "rejected by C6, whose kinds sequence must begin with False "
        "(the separator does not link), and by C10, whose bare-text sequence must "
        "begin with True (a cross-reference is a marked-up inline node, not a bare "
        "text child). Value double-mask: the whole text sequence still matches, "
        "only the separator child's kind diverges -- the exact link-vs-text "
        "distinction a text-only proxy misses.",
    },
    {
        "id": "type-as-inert-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": TYPE_INERT,
        "refinement": "this IS the pre-patch shape -- rendering the type as inert "
        "literal text (`desc_annotation(typ, ': ' + typ)` / a single Text run) "
        "instead of a cross-reference. test_pyproperty now expects "
        "`[pending_xref, \"str\"]` for the type; an inert Text node fails the "
        "assert_node node-kind comparison -- it is exactly the bug the gold patch "
        "fixes and does NOT resolve (matches model_prepatch.py / G-DIFF).",
        "rationale": "rejected by C6 and by C8's PSeq(False, True): the "
        "annotation's node MUST be a cross-reference, and by C10, since a bare "
        "text child is not the kind of node the parser yields for a simple name. "
        "The widths and texts match "
        "for a simple name, so the rejection isolates the child's kind -- the "
        "load-bearing discriminator of the fix. It never consults the shared "
        "parser either, so it also violates C5 by claiming a group for "
        "annotations the parser does not accept.",
    },
    {
        "id": "wrong-separator-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WRONG_SEP_TEXT,
        "refinement": "a faithful real patch emitting the separator as nodes.Text("
        "':') (dropping the trailing space) would render `:str` flush against the "
        "type instead of the expected `: str`; test_pyproperty's leading child "
        "text is exactly \": \" -- a one-character-short separator fails the "
        "comparison and would NOT resolve.",
        "rationale": "rejected by C7, whose first text entry is sep_text() == "
        "PSeq(58,32): the separator text MUST be \": \" (both code points). "
        "(partial-domain: one code point short.)",
    },
    {
        "id": "wrong-type-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WRONG_TYPE_TEXT,
        "refinement": "a faithful real patch whose cross-reference carried wrong "
        "target text (not the type name) would render an xref to the wrong target; "
        "test_pyproperty asserts the pending_xref's text is exactly \"str\" -- a "
        "node carrying \": \" (or any text != the type name) fails and would NOT "
        "resolve.",
        "rationale": "rejected by C7/C8's text sequence: the annotation's node "
        "MUST carry the parser's text (the type name for a simple name). The "
        "kinds sequence is correct here, so the rejection isolates the text "
        "clause. (partial-domain: correct only for the degenerate typ == \": \".)",
    },
    {
        "id": "emit-when-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": EMIT_WHEN_ABSENT,
        "refinement": "a faithful real patch that emitted the `: <type>` "
        "annotation group unconditionally (dropping the `if typ:` guard) would "
        "attach a spurious `: ` annotation to properties with NO declared type; "
        "the P2P property/object tests (and the no-annotation arm of "
        "test_pyproperty) would see an extra desc_annotation child where none is "
        "expected -- it would NOT resolve.",
        "rationale": "rejected by C4 `Implies(not present, "
        "len(Result().is_xref) == 0)`: when no annotation is declared, NO group "
        "may be produced. (partial-domain: correct on present==True, wrong on the "
        "no-annotation sub-domain.)",
    },
    {
        "id": "no-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": NO_SEPARATOR,
        "refinement": "a faithful real patch that spliced only the shared "
        "parser's nodes and dropped `nodes.Text(': ')` would render the type "
        "flush against the object name with no `: ` separator; test_pyproperty's "
        "assert_node expects the leading \": \" child, so the node list is one "
        "child short and it would NOT resolve.",
        "rationale": "rejected by C6/C7: both sequences must begin with the "
        "separator entry (False / sep_text()). NOTE this rival DOES "
        "cross-reference the type, so a discriminator that only asked \"is there "
        "an xref anywhere?\" would wrongly accept it -- this case pins that the "
        "separator child is independently required.",
    },
    {
        "id": "order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": ORDER_SWAP,
        "refinement": "a faithful real patch appending the separator AFTER the "
        "parsed annotation (`desc_annotation(typ, '', *annotations, "
        "nodes.Text(': '))`) would render `str: ` instead of `: str`; "
        "test_pyproperty compares the children in order, with \": \" first, so "
        "the reversed group fails the assertion and would NOT resolve.",
        "rationale": "rejected by C6/C7, which pin the separator as the FIRST "
        "entry of each sequence. Both children are present with the right kinds "
        "and texts -- only the ORDER diverges, so the rejection isolates "
        "ordering from content.",
    },
    {
        "id": "fixed-width-two",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FIXED_WIDTH_TWO,
        "refinement": "a faithful real patch that emitted the separator plus ONE "
        "cross-reference of the WHOLE annotation string (e.g. "
        "`desc_annotation(typ, '', nodes.Text(': '), type_to_xref(typ, "
        "self.env))` instead of splicing the parser's nodes) renders a compound "
        "annotation as a single link whose target is the entire string: "
        "`:type: List[int]` becomes one xref with reftarget \"List[int]\" rather "
        "than xref \"List\" + punctuation \"[\" + xref \"int\" + punctuation "
        "\"]\", so the inner type is not linked and the punctuation is not "
        "rendered as such -- the P2P annotation/xref tests compare those child "
        "kinds and it would NOT resolve.",
        "rationale": "rejected by C6/C7, whose widths and texts come from the "
        "axiomatized real parser: correct for a simple name, wrong for every "
        "compound annotation. This rival is precisely the over-strong "
        "fixed-width-2 claim an earlier revision of this spec made (the "
        "`List[int]` witness: the real code renders FIVE children), so it is the "
        "regression guard against re-introducing it.",
    },
    {
        "id": "length-desync",
        "kind": "uniqueness",
        "expect": "reject",
        "module": LENGTH_DESYNC,
        "refinement": "a faithful real patch appending a trailing `nodes.Text(': "
        "')` after the parsed annotation would emit an extra separator child "
        "beyond the ones the group should have; test_pyproperty compares the "
        "full child list, so a spurious trailing child fails the assertion and "
        "would NOT resolve.",
        "rationale": "rejected by C3 (len(is_xref) == len(text)) together with "
        "C7: the two parallel sequences must describe ONE child list, one entry "
        "each. A spec that constrained only the kinds sequence would miss this.",
    },
    {
        "id": "swallow-rejection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SWALLOW_REJECTION,
        "refinement": "a faithful real patch that wrapped the delegation in "
        "`try: annotations = _parse_annotation(typ, self.env) / except "
        "Exception: annotations = []` would render NO annotation for a declared "
        "type the parser refuses, silently dropping documented information; the "
        "documented `:type:` would vanish from the output rather than the build "
        "reporting anything, and a property whose declared type the parser "
        "refuses would be indistinguishable from one with no declared type -- "
        "not what delegating to the shared parser does.",
        "rationale": "rejected by C5 (`Implies(present, accepted(ToSeq(typ)))`): "
        "returning a group is itself an assertion that the shared parser accepted "
        "the annotation, and on the rejecting class it did not. Every "
        "accepted-string obligation is kept exactly right here, so the rejection "
        "isolates the C5/C9 exhaustiveness pair from the sequence content.",
    },
    {
        "id": "inert-fallback-on-rejection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": INERT_FALLBACK,
        "refinement": "a faithful real patch that caught the parser's refusal and "
        "fell back to the old `addnodes.desc_annotation(typ, ': ' + typ)` "
        "rendering for that annotation would leave the refused class rendered as "
        "inert text -- the very rendering the change replaces -- so a documented "
        "type would be cross-referenced or not depending on whether the parser "
        "happened to accept it, and the operation would never propagate the "
        "refusal at all.",
        "rationale": "rejected by C5: on the rejecting class the delegating "
        "operation yields NO group, and this rival yields the pre-patch inert one. "
        "The subtlest rival in the battery -- it renders every accepted string "
        "exactly right and is what a reader who wanted \"never fail\" would "
        "write, so it pins that the two arms C5/C9 are exhaustive and cannot be "
        "traded for a substitute rendering.",
    },
    {
        "id": "ungrounded-oracle-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNGROUNDED_ECHO,
        "refinement": "a faithful real patch that built `nodes.Text(': ')` plus "
        "one xref of the raw option string without ever calling the shared "
        "annotation parser would render every compound annotation as a single "
        "link to the whole string (`:type: List[int]` -> one xref with reftarget "
        "\"List[int]\") and would silently accept annotations the parser refuses "
        "-- the P2P annotation/xref tests compare those child kinds and it would "
        "NOT resolve.",
        "rationale": "UNGROUNDED-ORACLE probe: every value this rival returns is "
        "a syntactic function of its own arguments -- it does the work nowhere. "
        "Rejected by C5, which no impl can discharge without actually consulting "
        "the shared parser, since whether an annotation is accepted is not "
        "derivable from its code points inside the model; and by C6/C7 on every "
        "compound annotation. This is the guard that the C9 signalling arm did "
        "not turn the specification into something an echo can satisfy.",
    },
    {
        "id": "always-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": ALWAYS_REJECT,
        "refinement": "a faithful real patch that raised for every declared type "
        "annotation would break the documented build outright: test_pyproperty's "
        "`:type: str` property could not be rendered at all, so the F2P test "
        "errors rather than merely mismatching and it would NOT resolve.",
        "rationale": "rejected by C9, which may only be taken where the parser "
        "genuinely refuses (`not accepted(ToSeq(typ))`) -- and a SIMPLE type name "
        "is always accepted (the `accepted` axiom's Ensures). Degenerate over-use "
        "of the signalling arm; proves C9 is not a free escape hatch that lets an "
        "impl abandon the rendering obligation.",
    },
    {
        "id": "refuse-compound",
        "kind": "uniqueness",
        "expect": "reject",
        "module": REFUSE_COMPOUND,
        "refinement": "a faithful real patch that delegated only for simple type "
        "names and raised for anything else would break every documented generic "
        "or union annotation (`:type: List[int]`, `:type: int | None`) while "
        "leaving `:type: str` working; the P2P annotation/xref tests document "
        "compound annotations, so the build errors on them and it would NOT "
        "resolve.",
        "rationale": "rejected by C9's `not accepted(ToSeq(typ))`: the shared "
        "parser DOES accept `List[int]`, `int | None`, `...` and the rest, so a "
        "rejection may not be signalled there. It satisfies the discriminating "
        "clause C8 on the F2P input and still fails -- pairs with always-reject to "
        "pin the rejecting class exactly, from the other side, so the signalling "
        "arm cannot be widened past the annotations the parser really refuses.",
    },
    {
        "id": "separator-as-rendered-punctuation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": SEP_AS_PUNCT,
        "refinement": "a faithful real patch emitting the separator as rendered "
        "punctuation rather than a bare text node -- "
        "`desc_annotation(typ, '', addnodes.desc_sig_punctuation('', ': '), "
        "*annotations)` -- renders the same two characters, in the same place, "
        "still not as a link, and still followed by the parser's cross-reference. "
        "It does NOT resolve: test_pyproperty's assert_node compares the first "
        "child against the bare string \": \", and sphinx.testing.util.assert_node "
        "matches a str spec by node EQUALITY, which nodes.Text satisfies (Text is "
        "a str subclass) and an Element such as desc_sig_punctuation cannot. The "
        "observed failure is `The node '[0]' is not ': ': <desc_sig_punctuation: "
        "<#text: ': '>>`.",
        "rationale": "rejected by C10, whose leading entry is True: the separator "
        "child is a BARE TEXT node. KIND double-mask -- the kinds sequence and the "
        "texts sequence are byte-identical to the gold impl's, so C3/C6/C7 and "
        "C8's xref and text halves ALL hold; only the child-kind flag of the "
        "separator diverges. A carrier that recorded only cross-reference-ness and "
        "text could not distinguish this rendering from the gold one, which is "
        "exactly why the third sequence is part of the carrier.",
    },
    {
        "id": "delegate-then-discard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DELEGATE_DISCARD,
        "refinement": "a faithful real patch that called the shared parser (so a "
        "refused annotation still propagates) and then rendered the annotation as "
        "text anyway -- `annotations = _parse_annotation(typ, self.env)` followed "
        "by `desc_annotation(typ, '', nodes.Text(': '), nodes.Text(typ))` -- "
        "produces the pre-patch appearance for every accepted annotation: the "
        "documented type is not a link. test_pyproperty expects "
        "`[pending_xref, \"str\"]` for the type child and would NOT resolve.",
        "rationale": "rejected by C6/C8 (the annotation's child must be a "
        "cross-reference) and by C10 (a bare text child where the parser's node is "
        "a marked-up one). Pairs with W3, which renders the same thing WITHOUT "
        "consulting the parser: because this rival does delegate, C5 and C9 are "
        "both discharged, so the rejection isolates the rendering obligation from "
        "the delegation obligation -- and it is the tail-side probe of the "
        "child-kind clause, since it re-kinds the parser's own nodes.",
    },
    {
        "id": "wrapper-swap-not-an-annotation-node",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WRAPPER_SWAP,
        "refinement": "a faithful real patch that built the same children and put "
        "them in a different node -- e.g. `signode += "
        "addnodes.desc_sig_punctuation(typ, '', nodes.Text(': '), *annotations)`, "
        "or appended `nodes.Text(': ')` and the parsed nodes straight onto "
        "`signode` with no wrapper at all -- renders the same characters, with the "
        "documented type still a cross-reference, still after the name. It does "
        "NOT resolve: test_pyproperty's expectation is "
        "`[desc_annotation, (': ', [pending_xref, 'str'])]`, and "
        "sphinx.testing.util.assert_node checks the node's CLASS against "
        "desc_annotation before it inspects any child, so the wrapperless variant "
        "fails on the signature's child count and the wrong-wrapper variant on "
        "`assert isinstance(node, cls)`.",
        "rationale": "rejected by C12 (`is_annotation_node == present`) and by "
        "nothing else -- every child clause C3/C5/C6/C7/C8/C10/C11 is satisfied "
        "verbatim, so this rival differs from gold in exactly one observable bit. "
        "WHICH node holds the group is the emitting operation's own choice and not "
        "the parser's, so no axiom about the parser can pin it; it has to be "
        "stated, and C12 states it.",
    },
    {
        "id": "rewrite-the-xref-inside",
        "kind": "uniqueness",
        "expect": "reject",
        "module": XREF_INTERIOR,
        "refinement": "a faithful real patch that did not splice the parser's own "
        "nodes but REBUILT each at the same kind with the same characters and a "
        "different inside -- e.g. re-creating the cross-reference and giving it its "
        "label as two adjacent text runs (`xref += nodes.Text('s'); xref += "
        "nodes.Text('tr')`), or wrapping the label in further inline markup -- "
        "renders identically in HTML and agrees on every kind and every character. "
        "It does NOT resolve: test_pyproperty's `[pending_xref, 'str']` requires "
        "the cross-reference to have EXACTLY ONE child equal to 'str', and "
        "assert_node's `assert len(node) == len(cls)` fails on a two-run label.",
        "rationale": "rejected by C11 (`holds_one_bare_text == PSeq(False) + "
        "annotation_holds_one_bare_text(typ)`). It reports the tail's child-INSIDE "
        "axis as the parser's child-KIND axis, which nothing in the spec lets it "
        "substitute: there is no axiom relating annotation_bare_text to "
        "annotation_holds_one_bare_text, and axiom_check.py measures 1320 real "
        "parser nodes that read False on both, so they are not complements. Kinds, "
        "texts, widths and the bare-text axis are all byte-identical to gold, so "
        "the rejection is attributable to the child-inside clause alone -- the "
        "tail-side twin of separator-as-rendered-punctuation.",
    },
    {
        "id": "empty-annotation-node-when-none-declared",
        "kind": "uniqueness",
        "expect": "reject",
        "module": EMPTY_GROUP_NODE,
        "refinement": "a faithful real patch that hoisted the wrapper out of the "
        "`if typ:` guard -- `signode += addnodes.desc_annotation(typ or '', '')` "
        "unconditionally, filling it only when an annotation was declared -- "
        "renders no visible characters for an undeclared type. It does NOT "
        "resolve: the P2P property/signature assertions enumerate the signature's "
        "children positionally, so an extra empty desc_annotation shifts them.",
        "rationale": "rejected by C12 from the other side: the child sequences are "
        "empty, so C4 and every sequence clause hold, and only the group flag "
        "diverges -- True where `is_annotation_node == present` requires False. "
        "Pairs with wrapper-swap to pin the flag at both ends, the way "
        "always-reject and refuse-compound pin the signalling class at both ends: "
        "one rival fails to contribute the annotation node when one is due, the "
        "other contributes one when none is.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — the A-consumed axioms accepted / annotation_kinds /
# annotation_texts / rendered_nodes <-> the DOMAIN and the rendered output of
# _parse_annotation, the UNCHANGED callee. Probes import the REAL
# sphinx.domains.python._parse_annotation and EXECUTE it (directive 4: never
# scrape source). apply_gold=True is harmless: _parse_annotation is unchanged by
# the patch (only its caller changes). Self-contained, stdlib + sphinx only; all
# file reads UTF-8 (directive 5); nothing relies on a bundle file being mounted
# in-container (directive 6).
# ---------------------------------------------------------------------------

_AX_SOUND_PROBE = r'''
"""axiom-soundness for accepted / annotation_kinds / annotation_texts /
rendered_nodes <-> the domain and rendered output of _parse_annotation
(UNCHANGED callee).

Ensures under test (model.py axioms region):
  * DOMAIN, STRONG ARM: `accepted` Ensures Implies(is_simple_name(s), Result())
    -- a SIMPLE type name (model.py's is_simple_name over code points) must ALWAYS
    be accepted, i.e. the parser must never refuse one. This is the only totality
    the axioms claim: the parser is PARTIAL, and `accepted(s)` means exactly
    "the parser yields a node list for s".
  * REJECTION IS REAL: the rejecting class is non-empty and is what
    `rendered_nodes`' Exsures describes -- a refused annotation yields NO node
    list. Checked so the signalling arm is grounded in observed behaviour rather
    than assumed, and so a later revision cannot quietly re-assert totality.
  * LENGTH AGREEMENT: len(annotation_texts(s)) == len(annotation_kinds(s)) on
    every ACCEPTED s -- both sequences are read off the same node list, one entry
    per node.
  * SIMPLE NAME RENDERING: for an accepted simple name, annotation_kinds(s) ==
    PSeq(True) and annotation_texts(s) == PSeq(s) -- exactly ONE node, and it IS
    a cross-reference carrying the name.

The bridge is mapping.md's: is_xref == isinstance(node, addnodes.pending_xref)
and text == node.astext(). This probe runs the REAL callee under BOTH config
settings and tries to make it DISAGREE (refuse a simple name / wrong width /
non-xref / wrong text / accept something it in fact refuses), including the
compound annotations that broke an earlier revision of this spec and the
refused class the domain axiom exists for. Exit 0 iff sound.
"""
import random
import string
import sys
import warnings

warnings.simplefilter("ignore")

from sphinx.domains.python import _parse_annotation   # the unchanged callee
from sphinx import addnodes


class _FakeConfig:
    def __init__(self, unqualified):
        self.python_use_unqualified_type_names = unqualified


class _FakeEnv:
    """Minimal env: _parse_annotation/type_to_xref read only
    config.python_use_unqualified_type_names and ref_context."""
    def __init__(self, unqualified=False):
        self.config = _FakeConfig(unqualified)
        self.ref_context = {}


FIRST = string.ascii_letters + "_"
REST = FIRST + string.digits


def is_simple_name(s):
    """model.py's @Pure is_simple_name, on the str side of the bridge."""
    return len(s) > 0 and s[0] in FIRST and all(c in REST for c in s)


fail = []
n_accepted = 0
n_refused = 0


def check(s, unqualified):
    """Assert the axioms on `s`. Returns True iff the parser accepted it."""
    global n_accepted, n_refused
    env = _FakeEnv(unqualified)
    # DOMAIN. `accepted(s)` IS "the parser yields a node list", so observing a
    # refusal is not unsoundness by itself -- the axioms are partial and the
    # Exsures arm describes exactly this. What WOULD be unsound is refusing a
    # SIMPLE NAME, which the strong arm of `accepted` forbids.
    try:
        out = _parse_annotation(s, env)
    except Exception as e:
        n_refused += 1
        if is_simple_name(s):
            fail.append("AXIOM-UNSOUND: _parse_annotation(%r, unq=%s) REFUSED a "
                        "SIMPLE NAME with %r, but accepted() Ensures "
                        "Implies(is_simple_name(s), Result())"
                        % (s, unqualified, e))
        return False
    n_accepted += 1
    if not isinstance(out, list):
        fail.append("AXIOM-UNSOUND: non-list for %r (unq=%s): %r"
                    % (s, unqualified, out))
        return True
    # LENGTH AGREEMENT is structural: kinds and texts are both read off `out`.
    kinds = [isinstance(n, addnodes.pending_xref) for n in out]
    texts = [n.astext() for n in out]
    if len(kinds) != len(texts):
        fail.append("AXIOM-UNSOUND: width disagreement for %r" % (s,))
        return True
    # SIMPLE NAME: exactly one node, a cross-reference carrying the name.
    if is_simple_name(s):
        if kinds != [True]:
            fail.append("AXIOM-UNSOUND on simple name %r (unq=%s): kinds=%r "
                        "!= [True] (annotation_kinds must be PSeq(True))"
                        % (s, unqualified, kinds))
            return True
        if out[0].get("reftarget") != s:
            fail.append("AXIOM-UNSOUND on simple name %r (unq=%s): reftarget=%r "
                        "!= name" % (s, unqualified, out[0].get("reftarget")))
        if not unqualified and texts != [s]:
            fail.append("AXIOM-UNSOUND on simple name %r (default config): "
                        "texts=%r != [name] (annotation_texts must be PSeq(s))"
                        % (s, texts))
    return True


# --- boundary: simple names (the strong arm of `accepted`) AND the compound /
# --- degenerate annotations, AND the REFUSED class the domain axiom exists for.
boundary = [
    # simple names (is_simple_name TRUE): must ALWAYS be accepted
    "str", "int", "bytes", "bool", "float", "object", "None",
    "X", "a", "Z", "T", "MyType", "_Private", "Foo123", "_", "__",
    "class", "def", "lambda", "match", "case", "True", "False",
    # NOT simple names but ACCEPTED: only width + the sequence axioms claimed
    "café", "Ω", "naïve", "foo.Bar", "a.b.c.D", "pathlib.Path",
    "List[int]", "Optional[str]", "Dict[str, int]", "int | None",
    "Tuple[()]", "Tuple[int, ...]", "Callable[..., int]", "...",
    "List[List[int]]", "a|b|c", "(1,2)", "{1:2}", "lambda x: x", "f(x)",
    "x[y][z]", "*args", "**kw", "Literal['a']", "Annotated[int, 'x']",
    "1", "1.2", "1.2.3", "-1", "0x1f", "@", "[", "]", "~", "%", "#c",
    "  ", " ", "\t", "\n", "", "  str  ", "\tint", "a  |  b",
    "Dict[ str , int ]", "not x", "x and y", "x if y else z", "[1,2]", "{}",
]
# The REFUSED class: annotation strings the parser does not render at all. None
# is a simple name, so none of them may make the strong arm fail; every one must
# land on the Exsures arm.
refused_expected = [
    'b"x"', "b'x'", 'B"x"', 'rb"x"', 'b""', 'List[b"x"]', 'x | b"y"',
    'Dict[str, b"k"]', 'b"x" | None', "a\x00b", '"\ud800"',
]
for s in boundary:
    check(s, unqualified=False)
    check(s, unqualified=True)
for s in refused_expected:
    if check(s, unqualified=False):
        fail.append("DOMAIN CLAIM WRONG: %r was expected to be REFUSED (the "
                    "class rendered_nodes' Exsures describes) but the parser "
                    "accepted it -- the recorded rejecting class is stale" % (s,))

# --- exhaustive over every length-1 and length-2 ASCII identifier -------------
# All simple names, so all must be accepted AND render as one xref.
for c in FIRST:
    check(c, unqualified=False)
    check(c, unqualified=True)
for a in FIRST:
    for b in REST:
        check(a + b, unqualified=False)

# --- randomized fuzz: simple names, compound/junk annotations, AND bytes
# --- literals spliced into otherwise well-formed annotations ------------------
JUNK = "[](),.|@#$%^&*-+=<>?/\\:;\"' \t~`!{}"
NAMES = ["str", "int", "bool", "Point", "None", "T", "MyClass", "x"]
BYTES_LITS = ['b"x"', "b'y'", 'B"z"', 'rb"w"', 'b""']
rng = random.Random(9591)


def ident():
    return rng.choice(FIRST) + "".join(
        rng.choice(REST) for _ in range(rng.randint(0, 12)))


for _ in range(20000):
    r = rng.random()
    if r < 0.32:
        s = ident()
    elif r < 0.42:
        s = "%s.%s" % (ident(), ident())
    elif r < 0.54:
        s = "%s[%s]" % (rng.choice(NAMES), rng.choice(NAMES))
    elif r < 0.64:
        s = "%s[%s, %s]" % (rng.choice(NAMES), rng.choice(NAMES),
                            rng.choice(NAMES))
    elif r < 0.73:
        s = "%s | %s" % (rng.choice(NAMES), rng.choice(NAMES))
    elif r < 0.79:
        s = " " * rng.randint(1, 3) + rng.choice(NAMES) + " " * rng.randint(0, 3)
    elif r < 0.85:
        s = "%s[%s[%s]]" % (rng.choice(NAMES), rng.choice(NAMES),
                            rng.choice(NAMES))
    elif r < 0.92:
        # bytes literals, bare and spliced into well-formed annotation shapes:
        # the REFUSED class, fuzzed so the domain split is exercised broadly.
        lit = rng.choice(BYTES_LITS)
        s = rng.choice([lit, "%s[%s]" % (rng.choice(NAMES), lit),
                        "%s | %s" % (rng.choice(NAMES), lit),
                        "%s[%s, %s]" % (rng.choice(NAMES), rng.choice(NAMES),
                                        lit)])
    else:
        s = "".join(rng.choice(REST + JUNK) for _ in range(rng.randint(1, 10)))
    check(s, unqualified=False)
    if rng.random() < 0.2:
        check(s, unqualified=True)

if fail:
    print("AXIOM-UNSOUND accepted/annotation_kinds/annotation_texts:")
    for f in fail[:20]:
        print("  " + f)
    sys.exit(1)
print("G-PBT axiom-soundness OK over %d observations (%d accepted / %d refused): "
      "the real _parse_annotation is PARTIAL, and the split is exactly the one "
      "the axioms describe -- it NEVER refused a simple name (accepted()'s strong "
      "arm holds, so the discriminating clause is unconditional on that class), "
      "it refused every one of the %d recorded refused-class annotations (so "
      "rendered_nodes' Exsures arm is grounded, not assumed), and on every "
      "accepted string its two sequences agree in width with every SIMPLE name "
      "yielding exactly ONE pending_xref carrying that name. Covered: %d boundary "
      "annotations (simple, compound, degenerate, empty, refused) + every "
      "length-1/2 ASCII identifier + 20000 fuzz strings (incl. bytes literals "
      "bare and spliced into subscripts/unions) x both config settings; no "
      "violation."
      % (n_accepted + n_refused, n_accepted, n_refused, len(refused_expected),
         len(boundary)))
sys.exit(0)
'''


_AX_CONTAIN_PROBE = r'''
"""axiom-containment for accepted / annotation_kinds / annotation_texts /
rendered_nodes.

The model calls `rendered_nodes(typ)` at exactly ONE site, inside `if present:`,
and reaches the two sequence axioms only through that call's Ensures. Those
axioms carry Requires(accepted(s)), and `rendered_nodes` establishes exactly
that on its returning path -- so containment is discharged BY THE CALLEE'S OWN
CONTRACT, not by an assumption at the call site: an annotation the parser refuses
leaves the sequence axioms uninvoked and takes the Exsures arm instead. There is
therefore no reachable input outside the axioms' domain, and no scope ceiling to
disposition.

What this probe checks is that the domain split the model relies on is the REAL
one, over the FULL admitted domain (the precondition admits every non-empty
annotation string -- `:type:` is directives.unchanged):
  (a) for the simple names the strong arm covers, the parser accepts and yields
      exactly one cross-reference carrying the name (so the discriminating clause
      is discharged, not vacuous);
  (b) for the compound annotations the strong arm does NOT cover, the parser
      still accepts and returns a well-formed node list of SOME width, which is
      what the general clauses pin via annotation_kinds/annotation_texts -- the
      widths are recorded so the reader can see they are not 2;
  (c) for the refused class, the parser yields NO node list, which is the arm
      rendered_nodes' Exsures describes -- so the two arms between them cover
      every admitted input, with nothing falling through.
Exit 0 iff all three hold over the whole admitted domain.
"""
import string
import sys
import warnings

warnings.simplefilter("ignore")

from sphinx.domains.python import _parse_annotation
from sphinx import addnodes


class _FakeConfig:
    def __init__(self, unqualified=False):
        self.python_use_unqualified_type_names = unqualified


class _FakeEnv:
    def __init__(self, unqualified=False):
        self.config = _FakeConfig(unqualified)
        self.ref_context = {}


env = _FakeEnv(unqualified=False)
fail = []

FIRST = string.ascii_letters + "_"
REST = FIRST + string.digits

# (a) The SIMPLE-name arm the discriminating clause consumes. `str` is the F2P
# input (test_pyproperty uses `:type: str`).
simple = ["str", "int", "bytes", "object", "None", "T", "MyType", "X", "Point",
          "_", "Foo123", "class"]
for name in simple:
    try:
        out = _parse_annotation(name, env)
    except Exception as e:
        fail.append("simple name %r was REFUSED (%r), but accepted() Ensures "
                    "Implies(is_simple_name(s), Result()) -- the model could not "
                    "then guarantee a group for `:type: str` at all" % (name, e))
        continue
    if not (isinstance(out, list) and len(out) == 1):
        fail.append("simple name %r reached %d nodes, not a single xref -- the "
                    "annotation_kinds Ensures PSeq(True) would be unsound"
                    % (name, len(out) if isinstance(out, list) else -1))
        continue
    n0 = out[0]
    if not isinstance(n0, addnodes.pending_xref):
        fail.append("simple name %r -> first node %s not a pending_xref"
                    % (name, type(n0).__name__))
    elif n0.get("reftarget") != name or n0.astext() != name:
        fail.append("simple name %r -> reftarget=%r text=%r"
                    % (name, n0.get("reftarget"), n0.astext()))

# (b) The COMPOUND / degenerate arm: accepted, so the general clauses pin the
# group to the parser's ACTUAL widths and texts and all containment needs is a
# well-formed node list. Widths are recorded to show they are emphatically not
# the fixed 2 an earlier revision claimed.
compound = ["List[int]", "Optional[str]", "Dict[str, int]", "int | None",
            "Tuple[()]", "Callable[..., int]", "...", "  ", "", "a.b.C",
            "List[List[int]]", "@", "1"]
widths = []
for name in compound:
    try:
        out = _parse_annotation(name, env)
    except Exception as e:
        fail.append("%r was expected to be ACCEPTED but the parser REFUSED it "
                    "(%r) -- the recorded domain split is stale" % (name, e))
        continue
    if not isinstance(out, list):
        fail.append("non-list node list for %r: %r" % (name, out))
        continue
    kinds = [isinstance(n, addnodes.pending_xref) for n in out]
    if len(kinds) != len(out):
        fail.append("width disagreement for %r" % (name,))
    widths.append("%r -> %d node(s)" % (name, len(out)))

# (c) The REFUSED arm: the parser yields no node list, so the sequence axioms are
# never invoked and the Exsures arm is the one that applies. These are ordinary
# `:type:` values -- the option is directives.unchanged, so the precondition
# admits them and nothing in the model excludes them.
refused = ['b"x"', "b'x'", 'B"x"', 'rb"x"', 'b""', 'List[b"x"]', 'x | b"y"',
           'Dict[str, b"k"]', 'b"x" | None', "a\x00b"]
refusals = []
for name in refused:
    try:
        out = _parse_annotation(name, env)
    except Exception as e:
        refusals.append("%r -> %s" % (name, type(e).__name__))
        continue
    fail.append("%r was expected to be REFUSED (the arm rendered_nodes' Exsures "
                "describes) but the parser accepted it, yielding %d node(s) -- "
                "the recorded domain split is stale"
                % (name, len(out) if isinstance(out, list) else -1))

if fail:
    print("AXIOM-CONTAINMENT-BROKEN accepted/annotation_kinds/annotation_texts:")
    for f in fail[:20]:
        print("  " + f)
    sys.exit(1)
print("G-PBT axiom-containment OK: the sequence axioms Require accepted(s), and "
      "rendered_nodes establishes exactly that on its returning path, so every "
      "input at which the model invokes them is in domain BY THE CALLEE'S OWN "
      "CONTRACT -- containment is discharged with NO scope ceiling to "
      "disposition. The strong SIMPLE-name arm (which discharges the "
      "discriminating clause on the F2P `:type: str`) holds on %d simple names, "
      "each accepted and rendered as exactly one pending_xref carrying the name; "
      "the general clauses hold over the compound arm, whose real widths are "
      "[%s] -- not the fixed 2 an earlier revision claimed; and the refused arm "
      "is real, with %d admitted annotation strings yielding no node list at all "
      "[%s], which is the arm the Exsures describes. The two arms cover every "
      "admitted input."
      % (len(simple), "; ".join(widths), len(refusals), "; ".join(refusals)))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-annotation-parser",
        "axiom": "accepted/annotation_kinds/annotation_texts/rendered_nodes",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "the real _parse_annotation (unchanged callee) must satisfy "
        "the axioms' Ensures: the DOMAIN's strong arm (a SIMPLE name is always "
        "accepted -- never refused), width agreement between the kinds and texts "
        "sequences on every accepted string, and for a SIMPLE name exactly one "
        "pending_xref carrying that name. The probe fuzzes simple names, compound "
        "annotations (List[int], unions, Ellipsis), degenerate inputs (empty, "
        "whitespace-only, junk), the REFUSED class (bytes literals bare and "
        "spliced into subscripts/unions, NUL) and every length-1/2 ASCII "
        "identifier under both config settings, treating a refused simple name / "
        "wrong width / non-xref / wrong text as AXIOM-UNSOUND, and ALSO treating "
        "an accepted member of the recorded refused class as a stale domain "
        "claim -- so the partiality the Exsures arm rests on is measured, not "
        "assumed. Mirrors and strengthens axiom_check.py / G-AX.",
    },
    {
        "id": "ax-contain-annotation-parser",
        "axiom": "accepted/annotation_kinds/annotation_texts/rendered_nodes",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "the sequence axioms Require accepted(s) and the model "
        "reaches them only through rendered_nodes, whose returning path "
        "establishes precisely that -- so containment is discharged by the "
        "callee's own contract and every reachable input is in domain, with no "
        "scope ceiling to disposition. The probe checks that the domain split the "
        "model relies on is the REAL one over the whole admitted domain: the "
        "strong simple-name arm (which discharges the discriminating clause on "
        "the F2P `:type: str`) really holds, the compound arm the general clauses "
        "pin returns well-formed node lists whose widths are NOT the fixed 2 an "
        "earlier revision claimed, and the refused arm the Exsures describes is "
        "non-empty and covers the rest -- so the two arms leave no admitted input "
        "falling through.",
    },
]
