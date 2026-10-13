#!/usr/bin/env python3
r"""G-CONF differential conformance check for sphinx-doc__sphinx-7462 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so each ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. Both
modeled operations are pure R/I (no A-tagged callee — mapping.md §3).

Two modeled functions, two differential checks:

  #1  `renderSequenceTokens` ⇔ the `ast.Tuple` branch of the nested `unparse` in
      `sphinx.domains.python._parse_annotation`. Observable: the rendered NODE
      list for a top-level comma-separated annotation, compared node-by-node as
      `(node_class_name, node.astext())`.
        SHADOW  — seqTokens transliterated: the member images concatenated with a
                  single comma-space `desc_sig_punctuation` separator between
                  adjacent members; the empty sequence is the two punctuation
                  nodes `(` `)`.  Member images are obtained from the SAME real
                  `_parse_annotation` on each member's source, so the shadow
                  reuses the genuine recursive renderer (the unchanged callee).
        ORACLE  — `_parse_annotation(src)` where `src` parses to a top-level
                  `ast.Tuple` (so unparse(Module) == the Tuple branch's output),
                  the real patched behaviour.

  #2  `renderSequenceText` ⇔ the `ast.Tuple` branch of `sphinx.pycode.ast.unparse`.
      Observable: the rendered source string.
        SHADOW  — seqText transliterated: `", ".join(images)`, or `"()"` when
                  empty.  Member images taken from the same real `unparse`.
        ORACLE  — `unparse(node)` on fuzzed `ast.Tuple` nodes (real patched code).

Any disagreement is a mechanical R/I counterexample (the empty-tuple case being
the discriminating one for each site). Exit 0 iff zero disagreements. stdlib +
sphinx only. Seed pinned (mapping.md §4).
"""
import ast
import random
import sys

SEED = 7462
N_FUZZ = 100_000


# ============================================================================
# Site #2 — sphinx.pycode.ast.unparse (source-text rendering)
# ============================================================================

def shadow_text(images):
    """seqText transliterated: join already-rendered member text by member
    count. The empty sequence is the empty pair `()` (the fix)."""
    if len(images) == 0:
        return "()"
    return ", ".join(images)


def make_tuple_source(elem_sources):
    """Python source that parses to an ast.Tuple with exactly the given element
    source fragments (0, 1, or many)."""
    n = len(elem_sources)
    if n == 0:
        return "()"
    elif n == 1:
        return "(" + elem_sources[0] + ",)"
    else:
        return "(" + ", ".join(elem_sources) + ")"


def fuzz_elem_pool(rng):
    atoms = ["1", "2", "0", "1234", "a", "b", "obj", "os.path", "x.y.z",
             "'str'", '"s"', "b'bytes'", "...", "None", "True", "1.5",
             "- 1", "+ a", "not b", "~ x", "a + b", "[1, 2]", "{1, 2}",
             "{'k': 1}", "lambda: 1", "object()", "Tuple[int, int]"]
    r = rng.random()
    if r < 0.85:
        return rng.choice(atoms)
    k = rng.randint(0, 3)
    return make_tuple_source([rng.choice(atoms) for _ in range(k)])


def fuzz_text_nodes(n, rng):
    """Yield ast.Tuple nodes of varied arity for site #2 (via real parse, so
    member images come from the genuine recursive renderer)."""
    boundary = [
        "()",                 # empty   (the FAIL_TO_PASS case)
        "(1,)",               # single
        "(1, 2, 3)",          # many    (PASS_TO_PASS)
        "(a,)",
        "('s',)",
        "(object(),)",
        "(1, 2)",
        "(a, b, c, d)",
        "((1, 2), 3)",        # nested tuple as a member
        "((),)",              # single member that is itself the empty tuple
        "((), ())",           # two empty-tuple members
        "(None,)",
        "(..., 1)",
    ]
    for src in boundary:
        node = _outer_tuple(ast.parse(src, mode="eval").body)
        if node is not None:
            yield node
    for _ in range(n):
        arity = rng.randint(0, 6)
        elems = [fuzz_elem_pool(rng) for _ in range(arity)]
        src = make_tuple_source(elems)
        try:
            node = _outer_tuple(ast.parse(src, mode="eval").body)
        except SyntaxError:
            continue
        if node is not None:
            yield node


def _outer_tuple(node):
    return node if isinstance(node, ast.Tuple) else None


def check_site2(rng):
    from sphinx.pycode.ast import unparse

    disagreements = []
    count = 0
    for node in fuzz_text_nodes(N_FUZZ, rng):
        count += 1
        images = [unparse(e) for e in node.elts]   # unchanged recursive renderer
        shadow = shadow_text(images)                # R/I shadow of the impl
        oracle = unparse(node)                      # real patched ast.Tuple branch
        if shadow != oracle:
            disagreements.append((ast.dump(node), shadow, oracle))
            if len(disagreements) >= 5:
                break
    return count, disagreements


# ============================================================================
# Site #1 — sphinx.domains.python._parse_annotation (display-token rendering)
# ============================================================================

def node_sig(node):
    """Observable signature of a docutils node: (class name, rendered text)."""
    return (type(node).__name__, node.astext())


def sigs(nodes):
    return [node_sig(n) for n in nodes]


def shadow_tokens(member_images, punct_factory):
    """seqTokens transliterated to the node domain.

    `member_images` is the list of per-member rendered node-lists (each itself a
    list of nodes, obtained from the real renderer). `punct_factory(text)` builds
    a `desc_sig_punctuation` node carrying `text` — the only node KIND this
    operation creates (mapping.md §2.3).

      empty      -> [ '(' , ')' ]               (two punctuation nodes)
      non-empty  -> member_0 + SEP + member_1 + SEP + ... + member_k
                    with one comma-space separator between adjacent members.
    """
    if len(member_images) == 0:
        return [punct_factory("("), punct_factory(")")]
    out = []
    for i, img in enumerate(member_images):
        if i > 0:
            out.append(punct_factory(", "))
        out.extend(img)
    return out


def annot_tuple_source(elem_sources):
    """Source for a TOP-LEVEL comma-separated annotation that parses to an
    ast.Tuple (so _parse_annotation's unparse(Module) == the Tuple branch).

    We CONTROL the member source strings directly (rather than reconstructing
    them from a parsed node), so the per-member render and the whole-annotation
    render use exactly the same source — no dependency on py3.9+ ast.unparse."""
    n = len(elem_sources)
    if n == 0:
        return "()"
    elif n == 1:
        return elem_sources[0] + ","      # bare trailing comma -> 1-tuple
    else:
        return ", ".join(elem_sources)    # bare comma list -> n-tuple


def fuzz_annot_elem(rng):
    """Annotation element sources whose top-level parse is a single expression
    (never itself a bare comma list), so member arity stays controlled.

    DOMAIN NOTE (site #1 only): the inner `unparse` of `_parse_annotation` at
    `base_commit` supports only Attribute/Index/List/Module/Name/Subscript/Tuple
    nodes. A member that parses to anything else (e.g. `ast.Constant` such as
    `None`/`True`/`1`/`...`) raises `SyntaxError` INSIDE the tuple loop, so the
    real `_parse_annotation` aborts the modeled `ast.Tuple` branch entirely and
    falls through to its UNCHANGED outer `except SyntaxError: make_xref(annotation)`
    fallback — a code path neither modeled operation describes. Such members are
    therefore OUTSIDE the modeled operation's domain (the operation assembles
    already-rendered member images; a member that the surrounding renderer cannot
    render is not a valid input). The atom pool below contains only renderer-
    supported member sources, and `check_site1` additionally guards structurally
    against any input whose oracle is the fallback (belt and suspenders)."""
    atoms = ["int", "str", "bytes", "object", "float", "bool",
             "os.path", "a.b.c", "List[int]", "Dict[str, int]",
             "Optional[int]", "Callable[[int], int]", "Tuple[int, str]",
             "x", "y", "Foo", "Bar"]
    return rng.choice(atoms)


def fuzz_annot_elem_lists(n, rng):
    """Yield lists of member source strings (the controlled inputs)."""
    boundary_elems = [
        [],                       # "()"  empty tuple  (the FAIL_TO_PASS case)
        ["int"],                  # 1-tuple
        ["int", "str"],           # 2-tuple
        ["int", "str", "bytes"],
        ["List[int]"],
        ["Dict[str, int]", "int"],
        ["Optional[int]"],
        ["Callable[[int], int]", "str"],
        ["a.b.c"],
        ["Tuple[int, str]", "bool", "None"],
    ]
    for elems in boundary_elems:
        yield elems
    for _ in range(n):
        arity = rng.randint(0, 5)
        yield [fuzz_annot_elem(rng) for _ in range(arity)]


def check_site1(rng):
    from sphinx.domains.python import _parse_annotation
    from sphinx.addnodes import desc_sig_punctuation

    def punct(text):
        return desc_sig_punctuation('', text)

    def member_image(src):
        """The real renderer's node list for one member source, via the same
        public entry; the unchanged recursive renderer (opaque input)."""
        return list(_parse_annotation(src))

    disagreements = []
    count = 0
    for elem_sources in fuzz_annot_elem_lists(N_FUZZ, rng):
        src = annot_tuple_source(elem_sources)
        # Confirm the controlled source parses to a top-level ast.Tuple of the
        # expected arity; otherwise skip (keeps the oracle == the Tuple branch).
        try:
            top = ast.parse(src, mode="exec").body[0].value
        except (SyntaxError, AttributeError, IndexError):
            continue
        if not isinstance(top, ast.Tuple) or len(top.elts) != len(elem_sources):
            continue
        oracle = list(_parse_annotation(src))            # real patched behaviour
        # Domain guard: if any member is not renderer-supported (e.g. an
        # `ast.Constant`), the inner `unparse` raises `SyntaxError` inside the
        # tuple loop and `_parse_annotation` aborts the modeled `ast.Tuple`
        # branch, returning its UNCHANGED outer fallback `[make_xref(annotation)]`
        # — a single `pending_xref` carrying the whole source. That input is
        # outside the modeled operation's domain (no member image exists), so it
        # is not a counterexample to the tuple-assembly refinement; skip it. The
        # empty-tuple case "()" and every renderer-supported member reach the
        # real tuple branch and are checked normally.
        if (len(oracle) == 1
                and type(oracle[0]).__name__ == "pending_xref"
                and oracle[0].astext() == src):
            continue
        count += 1
        member_images = [member_image(s) for s in elem_sources]
        shadow = shadow_tokens(member_images, punct)     # R/I shadow of the impl
        if sigs(shadow) != sigs(oracle):
            disagreements.append((src, sigs(shadow), sigs(oracle)))
            if len(disagreements) >= 5:
                break
    return count, disagreements


# ============================================================================

def main():
    rng = random.Random(SEED)

    c1, d1 = check_site1(rng)
    c2, d2 = check_site2(rng)

    if d1 or d2:
        print("G-CONF FAIL: R/I disagreement(s).")
        for src, sh, orc in d1:
            print("  [site1 tokens] src=%r shadow=%r oracle=%r" % (src, sh, orc))
        for dump, sh, orc in d2:
            print("  [site2 text]   node=%s shadow=%r oracle=%r" % (dump, sh, orc))
        return 1

    print("G-CONF OK: R/I shadow of renderSequenceTokens agrees with patch.diff "
          "behaviour (real _parse_annotation) on %d annotations, and "
          "renderSequenceText agrees with real ast.unparse on %d tuple nodes "
          "(seed=%d), 0 disagreements." % (c1, c2, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
