#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9602 (nagini).

SHADOW: the impl regions of model.py's two modeled functions, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped;
List[int] carriers stay plain Python lists. There are no @ContractOnly
callees in this bundle (both changed behaviours are modeled deeply).

ORACLE: the REAL patched repo function per mapping.md — `_parse_annotation`
(sphinx/domains/python.py), which contains all three changed sites (the
constant-rendering branch of its nested `unparse`, the enumerated-subscript
wrap step, and the final node-resolution loop). It is driven on annotation
source strings with a minimal stub env (config attribute read by the
unchanged cross-reference constructor). The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed resolves the patched
module.

Type bridge (mapping.md section 2): each output docutils node maps to a kind
code — pending_xref -> 3 (XREF), desc_sig_punctuation -> 2 (PUNCT),
nodes.literal -> 4 (LIT), non-blank Text -> 1 (NAME). An annotation
`HEAD[a1, ..., an]` yields a flat node list `head [ a1 , ... an ]`; the
modeled body is the slice between the bracket punctuation nodes. The body's
INPUT kind list (the node list as assembled before the wrap/resolution
steps) is derived structurally from the generated arguments: an ellipsis
argument contributes PUNCT, every other argument a NAME, with a PUNCT
separator between arguments — exactly the assembly the subscript branch
produces. Text content maps to List[int] of code points (ord per char);
`is_str` <-> the constant is a piece of text; `is_literal` <-> the head
spelling is one of the two recognised enumeration heads.

Per annotation the check diffs:
  (B2) shadow `resolve_subscript(body_kinds, is_literal)` against the kind
       codes of the real output body slice (and that the head resolved to a
       cross-reference);
  (B1) for each constant argument, shadow `render_literal_value` against the
       rendered text of the corresponding real body node.

Input domain: render_literal_value's Requires restricts textual values to
printable ASCII (32..126) excluding the apostrophe (39) and reverse solidus
(92); string constants are generated from exactly that alphabet.
resolve_subscript's Requires admits any kind list in 1..4; the real
assembly produces NAME/PUNCT bodies, and generation covers those over heads
in both conventions (recognised enumeration heads and ordinary heads,
including a dotted non-recognised spelling). Boundary cases cover the
single-string enumeration, mixed value kinds, both head spellings, the empty
string constant, ellipsis bodies, and identifier arguments.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz annotations
(each exercising B2 once and B1 per constant argument). Pinned fuzz seed:
9602.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (sphinx/docutils are the system under test).
"""
import json
import random
import string
import sys
import warnings

SEED = 9602
N_FUZZ = 100_000


def _codes(s):
    return [ord(c) for c in s]


def _str(codes):
    return "".join(chr(c) for c in codes)


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def render_literal_value(value, is_str):
    if is_str:
        result = [39] + value + [39]
        return result
    else:
        out = []
        i = len(value)
        while i > 0:
            out = [value[i - 1]] + out
            i = i - 1
        return out


def resolve_subscript(kinds, is_literal):
    # Wrap each text node iff this is an enumerated (Literal) subscript.
    wrapped = []
    i = len(kinds)
    while i > 0:
        k = kinds[i - 1]
        if is_literal and k == 1:
            wrapped = [4] + wrapped
        else:
            wrapped = [k] + wrapped
        i = i - 1
    # Resolve: wrapped -> plain text; non-blank text -> cross-reference; else
    # pass through.
    out = []
    j = len(wrapped)
    while j > 0:
        w = wrapped[j - 1]
        if w == 4:
            out = [1] + out
        elif w == 1:
            out = [3] + out
        else:
            out = [w] + out
        j = j - 1
    return out


def main():
    warnings.filterwarnings("ignore")
    sys.path.insert(0, "/testbed")
    from sphinx.domains.python import _parse_annotation
    from sphinx import addnodes
    from docutils import nodes

    class _Cfg:
        python_use_unqualified_type_names = False

    class _Env:
        config = _Cfg()
        ref_context = {}

    env = _Env()

    def node_kind(n):
        if isinstance(n, addnodes.pending_xref):
            return 3
        if isinstance(n, addnodes.desc_sig_punctuation):
            return 2
        if isinstance(n, nodes.literal):
            return 4
        if isinstance(n, nodes.Text):
            return 1
        return 0

    RECOGNISED_HEADS = ("Literal", "typing.Literal")

    checked = [0]

    # argument spec: ("str", content) | ("num", python_value) | ("name", ident)
    #              | ("ellipsis",)

    def arg_source(a):
        if a[0] == "str":
            return "'" + a[1] + "'"
        if a[0] == "num":
            return repr(a[1])
        if a[0] == "name":
            return a[1]
        return "..."

    def arg_input_kind(a):
        return 2 if a[0] == "ellipsis" else 1

    def check_annotation(head, args):
        src = head + "[" + ", ".join(arg_source(a) for a in args) + "]"
        is_literal = head in RECOGNISED_HEADS

        # --- bridge: the body's input kind list (pre-wrap assembly) ----------
        body_kinds = []
        for idx, a in enumerate(args):
            if idx > 0:
                body_kinds.append(2)  # separator
            body_kinds.append(arg_input_kind(a))

        # --- shadow (B2) -------------------------------------------------------
        shadow_body = resolve_subscript(body_kinds, is_literal)

        # --- oracle ------------------------------------------------------------
        real = _parse_annotation(src, env)
        real_kinds = [node_kind(n) for n in real]
        # expected flat shape: head, '[', body..., ']'
        if (len(real_kinds) != len(body_kinds) + 3
                or real_kinds[1] != 2 or real_kinds[-1] != 2):
            return ("DISAGREEMENT annotation=%r\n  real node shape %r does "
                    "not bracket a %d-node body"
                    % (src, real_kinds, len(body_kinds)))
        if real_kinds[0] != 3:
            return ("DISAGREEMENT annotation=%r\n  head resolved to kind %d, "
                    "expected a cross-reference" % (src, real_kinds[0]))
        real_body = real_kinds[2:-1]
        if shadow_body != real_body:
            return ("DISAGREEMENT annotation=%r\n  body input kinds=%r "
                    "is_literal=%r\n  shadow body kinds: %r\n"
                    "  real body kinds:   %r"
                    % (src, body_kinds, is_literal, shadow_body, real_body))
        checked[0] += 1

        # --- shadow (B1): each constant argument's rendered text --------------
        for idx, a in enumerate(args):
            if a[0] not in ("str", "num"):
                continue
            pos = 2 + 2 * idx  # body node of argument idx in the flat list
            real_text = real[pos].astext()
            if a[0] == "str":
                shadow_text = _str(render_literal_value(_codes(a[1]), True))
            else:
                shadow_text = _str(render_literal_value(_codes(repr(a[1])),
                                                        False))
            if shadow_text != real_text:
                return ("DISAGREEMENT annotation=%r arg %d=%r\n"
                        "  shadow rendered text: %r\n"
                        "  real rendered text:   %r"
                        % (src, idx, a, shadow_text, real_text))
            checked[0] += 1
        return None

    def run(head, args):
        err = check_annotation(head, args)
        if err:
            print(err)
            sys.exit(1)

    # --- boundary inputs -------------------------------------------------------
    boundary = [
        ("Literal", [("str", "abc")]),
        ("typing.Literal", [("str", "read"), ("str", "write")]),
        ("Literal", [("num", 1), ("str", "a"), ("num", True)]),
        ("Literal", [("str", "")]),                    # empty string constant
        ("Literal", [("str", " ")]),                   # blank-content string
        ("Literal", [("ellipsis",)]),
        ("Literal", [("name", "x")]),                  # identifier argument
        ("Literal", [("num", 1.5)]),
        ("Literal", [("name", "None")]),
        ("List", [("name", "int")]),
        ("Tuple", [("name", "int"), ("str", "s"), ("num", 3)]),
        ("Tuple", [("name", "int"), ("ellipsis",)]),
        ("Union", [("name", "int"), ("name", "str")]),
        ("t.Literal", [("str", "abc")]),               # dotted, NOT recognised
        ("MyThing", [("name", "foo"), ("str", "bar")]),
    ]
    for head, args in boundary:
        run(head, args)

    # --- fuzz -------------------------------------------------------------------
    rng = random.Random(SEED)
    heads = ["Literal", "typing.Literal", "List", "Tuple", "Union", "Dict",
             "MyThing", "foo.Bar", "t.Literal"]
    # Requires domain for textual values: printable ASCII minus ' and \
    str_alpha = "".join(chr(c) for c in range(32, 127) if c not in (39, 92))
    idents = ["int", "str", "bool", "bytes", "foo", "Bar", "x", "value",
              "None", "True"]

    def rand_arg(rng):
        r = rng.random()
        if r < 0.35:
            n = rng.randint(0, 10)
            return ("str", "".join(rng.choice(str_alpha) for _ in range(n)))
        if r < 0.55:
            k = rng.random()
            if k < 0.4:
                return ("num", rng.randint(0, 10 ** rng.randint(1, 6)))
            if k < 0.7:
                return ("num", rng.choice([True, False]))
            return ("num", round(rng.uniform(0, 1000), rng.randint(1, 6)))
        if r < 0.9:
            return ("name", rng.choice(idents))
        return ("ellipsis",)

    for _ in range(N_FUZZ):
        head = rng.choice(heads)
        args = [rand_arg(rng) for _ in range(rng.randint(1, 5))]
        run(head, args)

    print("G-CONF OK: shadow impls == real annotation rendering/resolution "
          "on %d checks (%d boundary annotations + %d fuzz annotations, "
          "seed %d)." % (checked[0], len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
