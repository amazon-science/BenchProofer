#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9230 (nagini).

SHADOW: the impl regions of model.py's `parsed_argument_name` and
`parsed_argument_type`, copied verbatim below with the contract calls
(Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
(`empty_seq`, `encode_name`, `last_token`, `joined`) copy over as plain
functions with PSeq realized as an immutable tuple shim; the impl itself
touches only `encode_name` and `ToSeq` (the sequence-valued helpers appear
in contracts only). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
the typed-field-argument decomposition inside
`sphinx.util.docfields.DocFieldTransformer.transform` (the parsed parameter
NAME and the parsed TYPE text of a `:param <type> <name>:` field). The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched module importable. This script never applies any diff
itself. The transform is driven end to end on a genuine docutils field list
(one typed `param` field per case, real `TypedField`, real rendering); the
two observables are read back from the rendered field: the name is the
`literal_strong` xref text and the type text is the `literal_emphasis` xref
text — exactly the two consumption sites mapping.md section 1 binds the
modeled functions to.

Type bridge (mapping.md section 2): a field argument string <-> the List[int]
of its whitespace tokens, one distinct int per token (here: the token's
position index). The shadow's returned List[int] decodes back to text by
mapping SPACE (32) to " " and encode_name(k) = k + 256 back to the k-th
token's string; the decoded name/type are compared string-for-string against
the real transform's outputs. Inputs are generated single-space-separated
(the modelled domain, mapping.md section 2 "Modelled domain"): the argument
is the single-space join of its tokens, so the bridge is a bijection on
every generated input.

Input domain (the Requires): len(tokens) >= 2 — the case where the
decomposition applies (fewer tokens leaves the field untouched, an unchanged
path outside the model, per mapping.md). Every generated token is a
non-empty whitespace-free string, so the join has exactly those tokens.

>= 1e5 Requires-satisfying inputs: structured boundary cases (the issue's
shape, the F2P shape, minimal 2-token runs, duplicate tokens, long runs)
plus 100000 fuzz runs. Pinned fuzz seed: 923000.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib-only imports (plus the repo under test).
"""
import json
import random
import sys

SEED = 923000
N_FUZZ = 100_000

SPACE = 32   # model.py's separator code point


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

class PSeqShim:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeqShim._wrap(self._t[:n])

    def drop(self, n):
        return PSeqShim._wrap(self._t[n:])

    def __add__(self, other):
        return PSeqShim._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeqShim) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


PSeq = PSeqShim


def ToSeq(xs):
    return PSeqShim._wrap(xs)


# --- pure helpers from model.py, contracts stripped ---------------------------

def empty_seq():
    # the empty token sequence
    return PSeq(0).take(0)


def encode_name(t):
    # Encode a token disjointly from the separator code point; tokens are
    # emitted as (token + 256).
    return t + 256


def last_token(run):
    # the final token of a non-empty run
    return run[len(run) - 1]


def joined(run):
    # the single-space-separated rendering of a run of tokens, in order
    if len(run) == 0:
        return empty_seq()
    if len(run) == 1:
        return PSeq(encode_name(run[0]))
    return PSeq(encode_name(run[0])) + PSeq(SPACE) + joined(run.drop(1))


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def parsed_argument_name(tokens):
    last = tokens[len(tokens) - 1]
    result = [encode_name(last)]
    return result


def parsed_argument_type(tokens):
    tokens_s = ToSeq(tokens)
    prefix_len = len(tokens) - 1
    result = []
    i = prefix_len
    while i > 0:
        elt = tokens[i - 1]
        if i == prefix_len:
            # last token of the prefix: no trailing separator
            result = [encode_name(elt)]
        else:
            result = [encode_name(elt), SPACE] + result
        i = i - 1
    return result


# --- bridge: token run <-> field argument string -------------------------------

def decode(seq, token_strs):
    """Decode a model output sequence back to text: SPACE -> ' ', an encoded
    token -> the corresponding token's string (position-index bijection)."""
    parts = []
    for v in seq:
        if v == SPACE:
            parts.append(" ")
        else:
            parts.append(token_strs[v - 256])
    return "".join(parts)


# --- oracle plumbing -----------------------------------------------------------

class _FakeSettings:
    env = None


class _FakeDocument:
    settings = _FakeSettings()


class _FakeState:
    document = _FakeDocument()


class _FakeDirective:
    """The minimal directive surface DocFieldTransformer touches: the field
    type map, a domain name, and the state.document.settings.env chain."""

    def __init__(self, typemap):
        self._typemap = typemap
        self.state = _FakeState()
        self.domain = "py"

    def get_field_type_map(self):
        return self._typemap


def _findall(node, cls):
    if hasattr(node, "findall"):
        return list(node.findall(cls))
    return list(node.traverse(cls))


def real_parse(transformer, nodes, addnodes, fieldarg):
    """Drive the REAL patched transform on a genuine field list carrying one
    typed `param` field whose argument is `fieldarg`; read back the parsed
    (type text, name) from the rendered field's two xref nodes. Returns
    (argtype, argname) or an error string."""
    field_name = nodes.field_name("", "param " + fieldarg)
    paragraph = nodes.paragraph("", "description")
    field_body = nodes.field_body("", paragraph)
    field = nodes.field("", field_name, field_body)
    field_list = nodes.field_list("", field)
    parent = nodes.section()
    parent += field_list
    transformer.transform(field_list)
    new_list = parent.children[0]
    strongs = _findall(new_list, addnodes.literal_strong)
    emphs = _findall(new_list, addnodes.literal_emphasis)
    if len(strongs) != 1 or len(emphs) != 1:
        return None, ("unexpected rendered shape: %d name nodes, %d type "
                      "nodes for fieldarg=%r" % (len(strongs), len(emphs),
                                                 fieldarg))
    return (emphs[0].astext(), strongs[0].astext()), None


def check_one(transformer, nodes, addnodes, token_strs):
    """One differential case: a run of >= 2 whitespace-free tokens. Returns
    an error string on disagreement, else None."""
    # Requires of the modeled functions: len(tokens) >= 2
    assert len(token_strs) >= 2
    assert all(t and not any(c.isspace() for c in t) for t in token_strs)
    fieldarg = " ".join(token_strs)          # the modelled single-space domain

    ids = list(range(len(token_strs)))       # position-index token bijection
    shadow_name = decode(parsed_argument_name(list(ids)), token_strs)
    shadow_type = decode(parsed_argument_type(list(ids)), token_strs)

    real, err = real_parse(transformer, nodes, addnodes, fieldarg)
    if err:
        return "DISAGREEMENT\n  tokens=%r\n  %s" % (token_strs, err)
    real_type, real_name = real
    if (shadow_type, shadow_name) != (real_type, real_name):
        return ("DISAGREEMENT\n  tokens=%r fieldarg=%r\n"
                "  shadow: type=%r name=%r\n"
                "  real:   type=%r name=%r"
                % (token_strs, fieldarg, shadow_type, shadow_name,
                   real_type, real_name))
    return None


def boundary_runs():
    return [
        # the issue's shape and the F2P shape (multi-token type)
        ["dict(str,", "str)", "opc_meta"],
        ["Dict[str,", "str]", "params"],
        ["Tuple[str,", "...]", "items"],
        # minimal 2-token runs (single-token type)
        ["int", "age"],
        ["str", "name"],
        ["x", "y"],
        ["List[int]", "xs"],
        ["Optional[int]", "z"],
        # duplicate token strings (distinct positions, equal text)
        ["x", "x"],
        ["a", "a", "a"],
        ["dict(str,", "dict(str,", "opc_meta"],
        # longer multi-token types
        ["a(b,", "c)", "d(e,", "f)", "name"],
        ["Callable[[int,", "str],", "None]", "cb"],
        ["one", "two", "three", "four", "five", "six", "seven", "n"],
        # awkward token spellings (punctuation-heavy, unicode, single chars)
        ["*", "args"],
        ["**", "kwargs"],
        [".", ".."],
        ["{'k':", "1}", "d"],
        ["étype", "nom"],
        ["a,b;c:d", "e"],
    ]


_TOKEN_POOL = [
    "dict(str,", "str)", "opc_meta", "params", "Dict[str,", "str]",
    "int", "name", "Tuple[str,", "...]", "List[int]", "foo", "bar",
    "SomeClass", "x", "y", "a(b,", "c)", "value", "Optional[int]",
    "*", "**", "{'k':", "1}", "é", "a,b", "z9_",
]

_CHAR_POOL = "abcXYZ019_()[]{},.:*<>|é中"


def rand_run(rng):
    n = rng.randint(2, 8)
    run = []
    for _ in range(n):
        if rng.random() < 0.7:
            run.append(rng.choice(_TOKEN_POOL))
        else:
            k = rng.randint(1, 10)
            run.append("".join(rng.choice(_CHAR_POOL) for _ in range(k)))
    return run


def main():
    from sphinx.util.docfields import (  # REAL patched module
        DocFieldTransformer, TypedField)
    from sphinx import addnodes
    from docutils import nodes

    typed = TypedField("parameter", names=("param",), label="Parameters")
    typemap = {"param": (typed, False)}
    transformer = DocFieldTransformer(_FakeDirective(typemap))

    checked = 0
    for run in boundary_runs():
        err = check_one(transformer, nodes, addnodes, run)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_one(transformer, nodes, addnodes, rand_run(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real typed-field decomposition on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_runs()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
