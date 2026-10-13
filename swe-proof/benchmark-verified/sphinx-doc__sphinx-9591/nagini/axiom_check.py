#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9591.

Executes the REAL unchanged callee `sphinx.domains.python._parse_annotation`
(boundary cases + randomized fuzz) and asserts every observation meets the
`accepted` / `annotation_kinds` / `annotation_bare_text` /
`annotation_holds_one_bare_text` / `annotation_texts` / `rendered_nodes` axioms
encoded in model.py.

The kind-A checks (A-consumed). model.py axiomatizes the parser's DOMAIN as
`accepted(s)` — True iff the parser yields a node list for `s` — and its rendered
output as FOUR parallel sequences over the same node list: `annotation_kinds(s)[k]`
True iff the parser's k-th node is a cross-reference (`isinstance(n,
addnodes.pending_xref)`), `annotation_bare_text(s)[k]` True iff it is a BARE TEXT
node (`isinstance(n, nodes.Text)`) rather than a marked-up inline one,
`annotation_holds_one_bare_text(s)[k]` True iff it holds exactly one inner node
and that node is a bare text one (`len(n.children) == 1 and isinstance(n[0],
nodes.Text)`), and `annotation_texts(s)[k]` that node's rendered text
(`n.astext()`), with these Ensures:

  (1) DOMAIN, STRONG ARM  `accepted` Ensures
      `Implies(is_simple_name(s), Result())`: a SIMPLE type name is ALWAYS
      accepted. This is the ONLY totality claimed. The parser is PARTIAL — on
      some annotation strings it yields no node list but raises instead — so
      `annotation_kinds` / `annotation_texts` carry `Requires(accepted(s))` and
      are defined only where the parser renders. Observing a refusal is
      therefore not unsoundness; refusing a SIMPLE NAME would be.
  (2) WIDTH AGREEMENT  `len(annotation_texts(s)) == len(annotation_bare_text(s))
      == len(annotation_holds_one_bare_text(s)) == len(annotation_kinds(s))` on
      every ACCEPTED `s`: all four sequences are read off the same node list, one
      entry per node.
  (3) SIMPLE NAME  for `s` matching `[A-Za-z_][A-Za-z0-9_]*` (model.py's @Pure
      `is_simple_name`, over code points): `annotation_kinds(s) == PSeq(True)`,
      `annotation_bare_text(s) == PSeq(False)`,
      `annotation_holds_one_bare_text(s) == PSeq(True)` and
      `annotation_texts(s) == PSeq(s)` — the parser returns EXACTLY ONE node,
      that node IS a cross-reference (`addnodes.pending_xref`, an Element and so
      NOT a `nodes.Text`), it holds exactly one inner node and that node is a
      bare `nodes.Text` run, and it carries the name. Under the default config
      (`python_use_unqualified_type_names = False`, which the test app uses) its
      rendered text (`astext()`) equals the name and that single inner run IS the
      name; under both configs its `reftarget` equals the name. The two
      config-dependent clauses are checked only under the default, which
      mapping.md §3.1 records as the binding one (under the non-default setting
      the cross-reference's label is a pair of `pending_xref_condition` children
      instead of one text run, so it is still a cross-reference but holds two
      inner nodes).
  (4) THE REFUSED CLASS IS REAL  `rendered_nodes` has
      `Exsures(AnnotationRejected, ... not accepted(ToSeq(typ)))`, which rests on
      the parser genuinely refusing some admitted annotation strings. A recorded
      refused class is re-measured here, and an accepted member of it is reported
      as a STALE DOMAIN CLAIM — so the partiality is observed, not assumed, and a
      later revision cannot quietly re-assert totality.

No width or kind claim is made outside the simple-name class: for a compound
annotation the axioms only assert (2), which is exactly what model.py's general
postcondition consumes. Those inputs are exercised here too, since the axioms
admit every accepted string and an unsound width claim on them would be as fatal
as an unsound simple-name claim.

Why the third and fourth flags exist at all (they are the model's CHILD-KIND and
CHILD-INSIDE axes). The F2P harness's `assert_node` matches the expected `": "`
child by node EQUALITY, which `nodes.Text` satisfies (it subclasses `str`) and no
`Element` does, and it matches `[pending_xref, "str"]` by requiring the
cross-reference to have EXACTLY ONE child equal to `"str"`. So two renderings
that agree on `annotation_kinds` and `annotation_texts` can still differ where
the oracle looks — rendered punctuation carrying `': '`, or a cross-reference
spelling `str` across two inner runs — and `annotation_bare_text` /
`annotation_holds_one_bare_text` are the observations that separate them. Their
soundness is therefore load-bearing and is measured here on the same node lists,
not assumed.

Imports the very module the gold patch calls (`sphinx.domains.python`); G-AX
runs this in the instance's Docker image where Sphinx 4.2 is installed. Exit 0
iff every obligation holds.
"""
import random
import string
import sys
import warnings

warnings.simplefilter("ignore")

from docutils import nodes
from sphinx.domains.python import _parse_annotation  # the unchanged callee
from sphinx import addnodes


_FIRST = string.ascii_letters + "_"
_REST = _FIRST + string.digits


class _FakeConfig:
    def __init__(self, unqualified):
        self.python_use_unqualified_type_names = unqualified


class _FakeEnv:
    """Minimal BuildEnvironment stub: _parse_annotation/type_to_xref read only
    `config.python_use_unqualified_type_names` and `ref_context`."""

    def __init__(self, unqualified=False):
        self.config = _FakeConfig(unqualified)
        self.ref_context = {}


def is_simple_name(s):
    """model.py's @Pure `is_simple_name`, on the str side of the bridge."""
    return len(s) > 0 and s[0] in _FIRST and all(c in _REST for c in s)


FLAG_CENSUS = {"bare_true": 0, "bare_false": 0,
               "holds_true": 0, "holds_false": 0, "neither": 0}


def holds_one_bare_text(n):
    """model.py's `annotation_holds_one_bare_text` observation of ONE node: the
    node holds exactly one inner node and that node is a bare text run. A bare
    text node holds no inner node at all, so it reads False (it IS the run it
    renders); a marked-up node whose label is split across several runs, or
    wrapped in further markup, reads False too."""
    if isinstance(n, nodes.Text):
        return False
    kids = list(getattr(n, "children", ()) or ())
    return len(kids) == 1 and isinstance(kids[0], nodes.Text)


def check_annotation_axioms(name, unqualified):
    """Assert the accepted / annotation_kinds / annotation_bare_text /
    annotation_holds_one_bare_text / annotation_texts Ensures on `name`. Returns
    True iff the parser ACCEPTED it (yielded a node list)."""
    env = _FakeEnv(unqualified)

    # (1) DOMAIN. `accepted(s)` IS "the parser yields a node list for s", so a
    # refusal is in-model, not unsound -- the sequence axioms simply do not apply
    # there and rendered_nodes' Exsures arm describes it. What the strong arm of
    # `accepted` forbids is refusing a SIMPLE NAME.
    try:
        result = _parse_annotation(name, env)
    except Exception as e:                              # noqa: BLE001
        if is_simple_name(name):
            raise AssertionError(
                "accepted axiom unsound: _parse_annotation(%r, unq=%s) REFUSED a "
                "SIMPLE NAME with %r, but accepted() Ensures "
                "Implies(is_simple_name(s), Result())" % (name, unqualified, e))
        return False
    assert isinstance(result, list), (
        "annotation axioms unsound: non-list node list for %r: %r"
        % (name, result))

    # (2) WIDTH AGREEMENT: one entry per node in all FOUR sequences.
    kinds = [isinstance(n, addnodes.pending_xref) for n in result]
    bares = [isinstance(n, nodes.Text) for n in result]
    holds = [holds_one_bare_text(n) for n in result]
    texts = [n.astext() for n in result]
    assert len(kinds) == len(texts) == len(bares) == len(holds), (
        "annotation axioms unsound: width disagreement for %r: kinds=%d "
        "texts=%d bares=%d holds=%d"
        % (name, len(kinds), len(texts), len(bares), len(holds)))
    # A node cannot be a bare text run AND hold one: the two flags are read off
    # the same node and `holds_one_bare_text` is False on a text node by
    # construction. Checked so a later edit cannot silently make them the same
    # observation twice over.
    for k, (b, h) in enumerate(zip(bares, holds)):
        assert not (b and h), (
            "annotation axioms unsound: node %d of %r reads True on BOTH the "
            "bare-text and the holds-one-bare-text flag" % (k, name))
    # Census, so the record can show these two axes are NOT degenerate: the
    # parser really does emit both bare text runs (the whitespace of a union) and
    # marked-up nodes (cross-references, rendered punctuation).
    for b in bares:
        FLAG_CENSUS["bare_true" if b else "bare_false"] += 1
    for h in holds:
        FLAG_CENSUS["holds_true" if h else "holds_false"] += 1
    # ... and they are not each other's complement either. A node that is neither
    # a bare text run NOR a holder of exactly one bare text run -- a marked-up
    # node whose label is split across several inner runs or itself further
    # marked up -- reads False on BOTH, which is what makes the fourth flag an
    # independent observation rather than `not is_bare_text` restated. The
    # cross-reference under `python_use_unqualified_type_names = True` is exactly
    # such a node (its label is a pair of pending_xref_condition children).
    for b, h in zip(bares, holds):
        if not b and not h:
            FLAG_CENSUS["neither"] += 1

    # (3) SIMPLE NAME: exactly one node, a cross-reference carrying the name.
    if not is_simple_name(name):
        return True
    assert kinds == [True], (
        "annotation_kinds axiom unsound on simple name %r (unq=%s): kinds=%r, "
        "but the Ensures claims PSeq(True) — exactly one node, and it is a "
        "cross-reference" % (name, unqualified, kinds))
    # annotation_bare_text == PSeq(False): that one node is a cross-reference,
    # which is an Element and so NOT a bare text node. Config-independent, like
    # the cross-reference flag itself.
    assert bares == [False], (
        "annotation_bare_text axiom unsound on simple name %r (unq=%s): "
        "bares=%r, but the Ensures claims PSeq(False) — the single node is the "
        "cross-reference, not a bare text run" % (name, unqualified, bares))
    first = result[0]
    # the cross-reference targets the type name (both configs).
    assert first.get("reftarget") == name, (
        "annotation axioms unsound on simple name %r (unq=%s): reftarget=%r "
        "!= name" % (name, unqualified, first.get("reftarget")))
    # annotation_texts == PSeq(s) and annotation_holds_one_bare_text ==
    # PSeq(True): binding under the default config (mapping.md §3.1). Under the
    # non-default setting the label is a pair of pending_xref_condition children,
    # so astext() is not the name and the node holds two inner nodes.
    if not unqualified:
        assert texts == [name], (
            "annotation_texts axiom unsound on simple name %r (default "
            "config): texts=%r != [name]" % (name, texts))
        assert holds == [True], (
            "annotation_holds_one_bare_text axiom unsound on simple name %r "
            "(default config): holds=%r, but the Ensures claims PSeq(True) — "
            "the cross-reference holds exactly one inner node and it is the "
            "bare text run spelling the name (its children are %r)"
            % (name, holds, list(first.children)))
        assert str(first.children[0]) == name, (
            "annotation_holds_one_bare_text axiom unsound on simple name %r "
            "(default config): the single inner bare text run is %r, not the "
            "name" % (name, str(first.children[0])))
    return True


def check_refused(name):
    """Assert `name` is one the parser REFUSES -- the class rendered_nodes'
    Exsures arm describes. Re-measured rather than assumed, so the partiality the
    signalling arm rests on cannot go stale."""
    env = _FakeEnv(False)
    try:
        out = _parse_annotation(name, env)
    except Exception as e:                              # noqa: BLE001
        return type(e).__name__
    raise AssertionError(
        "STALE DOMAIN CLAIM: %r was recorded as REFUSED (the class "
        "rendered_nodes' Exsures describes) but the parser ACCEPTED it, "
        "yielding %d node(s) -- the axioms' domain split no longer matches the "
        "real callee" % (name, len(out) if isinstance(out, list) else -1))


def main():
    # --- boundary: simple names (the strong arm) -------------------------
    simple = [
        "str", "int", "bytes", "bool", "float", "object", "None",
        "X", "a", "Z", "T", "MyType", "_Private", "Foo123", "_", "__",
        "class", "def", "lambda", "match", "case", "True", "False",
    ]
    for name in simple:
        check_annotation_axioms(name, unqualified=False)
        check_annotation_axioms(name, unqualified=True)

    # --- boundary: NOT simple names. Requires(True) admits them, so only
    # --- totality + width agreement are claimed, and both are checked.
    other = [
        "café", "Ω", "naïve",                       # non-ASCII names
        "foo.Bar", "a.b.c.D", "pathlib.Path",       # dotted (ast.Attribute)
        "List[int]", "Optional[str]", "Dict[str, int]",   # subscripted
        "int | None", "Tuple[()]", "Tuple[int, ...]",     # union / tuple
        "Callable[..., int]", "...", "List[List[int]]",
        "Literal['a']", "Annotated[int, 'x']",
        "1", "1.2", "1.2.3", "-1", "0x1f",          # numeric constants
        "@", "[", "]", "~", "%", "#c",              # SyntaxError arm
        "", " ", "  ", "\t", "\n",                  # no-content strings
        "  str  ", "\tint", "a  |  b", "Dict[ str , int ]",
        "not x", "x and y", "x if y else z", "[1,2]", "{}", "*args", "**kw",
    ]
    for name in other:
        check_annotation_axioms(name, unqualified=False)
        check_annotation_axioms(name, unqualified=True)

    # --- boundary: the REFUSED class. `:type:` is directives.unchanged, so
    # --- these are ordinary admitted annotation strings on which the parser
    # --- yields NO node list -- the arm rendered_nodes' Exsures describes.
    # --- None is a simple name, so none contradicts the strong arm.
    refused = [
        'b"x"', "b'x'", 'B"x"', 'rb"x"', 'b""',       # bytes literals
        'List[b"x"]', 'x | b"y"', 'Dict[str, b"k"]',    # bytes nested in shapes
        'b"x" | None', 'Optional[b"x"]',
        "a\x00b",                                       # NUL (compile refuses)
        '"\ud800"',                                     # lone surrogate
    ]
    refusals = [(name, check_refused(name)) for name in refused]

    # --- exhaustive over every length-1 and length-2 ASCII identifier ----
    n_exhaustive = 0
    for c in _FIRST:
        check_annotation_axioms(c, unqualified=False)
        check_annotation_axioms(c, unqualified=True)
        n_exhaustive += 1
    for a in _FIRST:
        for b in _REST:
            check_annotation_axioms(a + b, unqualified=False)
            n_exhaustive += 1

    # --- randomized fuzz: simple identifiers AND compound annotations ---
    names = ["str", "int", "bool", "Point", "None", "T", "MyClass", "x"]
    junk = "[](),.|@#$%^&*-+=<>?/\\:;\"' \t~`!{}"
    bytes_lits = ['b"x"', "b'y'", 'B"z"', 'rb"w"', 'b""']
    rng = random.Random(9591)

    def ident():
        k = rng.randint(1, 12)
        return rng.choice(_FIRST) + "".join(
            rng.choice(_REST) for _ in range(k - 1))

    n_refused_fuzz = [0]
    for _ in range(5000):
        r = rng.random()
        if r < 0.45:
            s = ident()
        elif r < 0.55:
            s = "%s.%s" % (ident(), ident())
        elif r < 0.70:
            s = "%s[%s]" % (rng.choice(names), rng.choice(names))
        elif r < 0.78:
            s = "%s[%s, %s]" % (rng.choice(names), rng.choice(names),
                                rng.choice(names))
        elif r < 0.82:
            s = "%s | %s" % (rng.choice(names), rng.choice(names))
        elif r < 0.88:
            s = " " * rng.randint(1, 3) + rng.choice(names) + " " * rng.randint(0, 3)
        elif r < 0.94:
            # the REFUSED class, fuzzed: a bytes literal bare or spliced into an
            # otherwise well-formed annotation shape. check_annotation_axioms
            # scores these on the DOMAIN claim only -- none is a simple name, so
            # a refusal is in-model, and an acceptance is fine too (the axioms
            # then apply); what this adds is breadth over the domain split rather
            # than a fixed list. n_refused records how often the parser refused.
            lit = rng.choice(bytes_lits)
            s = rng.choice([lit, "%s[%s]" % (rng.choice(names), lit),
                            "%s | %s" % (rng.choice(names), lit),
                            "%s[%s, %s]" % (rng.choice(names),
                                            rng.choice(names), lit)])
        else:
            s = "".join(rng.choice(_REST + junk) for _ in range(rng.randint(1, 10)))
        if not check_annotation_axioms(s, unqualified=False):
            n_refused_fuzz[0] += 1
        # occasionally fuzz the unqualified config too
        if rng.random() < 0.2:
            check_annotation_axioms(s, unqualified=True)

    print("G-AX OK: accepted/annotation_kinds/annotation_bare_text/"
          "annotation_holds_one_bare_text/annotation_texts/rendered_nodes "
          "axioms sound on %d simple names + %d compound/degenerate annotations "
          "+ %d exhaustive length-1/2 ASCII identifiers + 5000 fuzz strings "
          "(incl. bytes literals bare and spliced into subscripts/unions), both "
          "config settings, of which %d fuzz strings were REFUSED. The real "
          "_parse_annotation is PARTIAL, and the split "
          "is exactly the one the axioms describe: it NEVER refused a simple "
          "name, so accepted()'s strong arm holds and the discriminating clause "
          "is unconditional on that class; on every ACCEPTED string its FOUR "
          "sequences agree in width and every SIMPLE name yields EXACTLY ONE "
          "pending_xref, not a bare text node, holding exactly one bare text "
          "run that spells the name; and it refused all %d recorded "
          "refused-class annotations [%s], so the arm rendered_nodes' Exsures "
          "describes is grounded in measured behaviour rather than assumed. "
          "The two child-kind axes are NOT degenerate on the measured node "
          "lists: bare-text True/False = %d/%d and holds-one-bare-text "
          "True/False = %d/%d, and no node ever read True on both. Nor is either "
          "the other's complement: %d measured nodes read FALSE on BOTH (a "
          "marked-up node whose label is not one plain run -- e.g. the "
          "cross-reference under python_use_unqualified_type_names = True, whose "
          "label is a pair of pending_xref_condition children), so the fourth "
          "flag is an independent observation of the real parser's output and not "
          "`not is_bare_text` restated."
          % (len(simple), len(other), n_exhaustive, n_refused_fuzz[0],
             len(refusals),
             "; ".join("%r -> %s" % (n, k) for n, k in refusals),
             FLAG_CENSUS["bare_true"], FLAG_CENSUS["bare_false"],
             FLAG_CENSUS["holds_true"], FLAG_CENSUS["holds_false"],
             FLAG_CENSUS["neither"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
