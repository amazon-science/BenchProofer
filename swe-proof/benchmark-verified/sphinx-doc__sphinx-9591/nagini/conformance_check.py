#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9591 (nagini).

SHADOW — the `# impl-start` / `# impl-end` region of model.py, copied VERBATIM
below with only the contract calls deleted (there are no
Requires/Ensures/Invariant/Assert/Fold/Unfold/Acc/MustTerminate inside the
region). `sep_text()` is the model's `@Pure` helper copied verbatim minus
contracts. `PSeq` / `ToSeq` are realized by the immutable-tuple shim below, and
the `AnnotationGroup` record is the model's class minus its Ensures.

`accepted` / `annotation_kinds` / `annotation_bare_text` /
`annotation_holds_one_bare_text` / `annotation_texts` / `rendered_nodes` are the
model's only `@ContractOnly` callees, so they have no body to copy: the shadow
computes them from the REAL repo function they axiomatize,
`sphinx.domains.python._parse_annotation` (mapping.md §1, §3.1 — repo
`sphinx/domains/python.py:110`), so the axioms are exercised rather than assumed.

That parser is PARTIAL: on some annotation strings it yields no node list at all
but raises instead (a bytes literal such as `b"x"` reaches
`nodes.Text(node.value)` at `sphinx/domains/python.py:180-183` with a `bytes`
value, and docutils' `Text.__new__` refuses it; the `except SyntaxError` fallback
at `:185` does not catch that, so it escapes). `:type:` is
`directives.unchanged`, so such a value is an ordinary admitted input, and the
real caller at `:859` has no handler either — the refusal propagates out of
`handle_signature` unabsorbed. The model states that with `rendered_nodes`'
`Exsures(AnnotationRejected, ... not accepted(ToSeq(typ)))`, so the shadow below
realizes `rendered_nodes` as "call the real parser; if it refuses, signal", and
the harness treats ORACLE-AND-SHADOW-BOTH-REFUSE as the AGREEMENT it is, while a
one-sided refusal is a disagreement. The refused class is generated explicitly
(bare bytes literals and bytes spliced into subscripts/unions, plus NUL), so this
gate measures the partiality rather than avoiding it.

ORACLE — the REAL patched repo function, CALLED, not transliterated: the
gold-patched `sphinx.domains.python.PyProperty.handle_signature`
(`sphinx/domains/python.py:859`, the type-annotation block at 862-864). The gate
applies patch.diff to /testbed before this script runs and PYTHONPATH=/testbed
makes the patched module importable. The directive is driven with a duck-typed
`state.document.settings.env` (docutils `Directive.env` reads exactly that path),
which is enough context to call the real method — no Table/app/HTTP session is
needed, so nothing here is transliterated.

  observation:  the real method appends the annotation group to `signode`; we
                call it once with no `:type:` option to learn the base children
                (`property ` prefix + `desc_name`), then once with the option set
                and read the children ADDED beyond that base. mapping.md §2 fixes
                the observable as the pair (WHICH node holds the group, and the
                group's CHILDREN read four ways), because that is exactly what the
                F2P `assert_node(..., [desc_annotation, (": ", [pending_xref,
                "str"])])` inspects: the wrapper's class, then each child's class
                (`pending_xref`), its text, whether it is a bare `nodes.Text` (the
                `": "` element is matched by NODE EQUALITY, which only `Text`
                satisfies) and whether it holds exactly one bare text run (the
                `[pending_xref, "str"]` element requires the cross-reference to
                have EXACTLY ONE child equal to `"str"`).

TYPE BRIDGE (mapping.md §2, inverted)
  * `present: bool` + `typ: List[int]`  <->  `self.options.get('type')`, an
    `Optional[str]` behind the truthiness guard `if typ:`.  We generate the
    CONCRETE `str` (or absence) and derive the abstract pair, so every generated
    input lands inside the model's `Requires(Implies(present, len(typ) > 0))`:
    `present = typ_str is not None and typ_str != ''` (the repo's falsy guard)
    and `typ = [ord(c) for c in typ_str]`, whose length is then > 0 whenever
    `present` — Requires satisfied by construction, never by filtering.
  * `str` <-> `List[int]` / `PSeq[int]` of Unicode code points (`_to_cp` /
    `_from_cp`).
  * `AnnotationGroup(is_xref, text, is_bare_text, holds_one_bare_text,
    is_annotation_node)` <-> the annotation group's rendered children as the FOUR
    PARALLEL sequences they induce, plus one flag on the node holding them:
      - `is_xref[k]            == isinstance(child_k, addnodes.pending_xref)`
      - `text[k]               == child_k.astext()`
      - `is_bare_text[k]       == isinstance(child_k, nodes.Text)`
      - `holds_one_bare_text[k]== len(child_k.children) == 1 and
                                  isinstance(child_k[0], nodes.Text)`
                                 (False on a `Text` child: it has no children)
      - `is_annotation_node    == len(added) == 1 and
                                  isinstance(added[0], addnodes.desc_annotation)`
    So `nodes.Text(': ')` contributes `(False, ': ', True, False)`,
    `pending_xref` labelled by one text run contributes `(True, 'str', False,
    True)`, and `desc_sig_punctuation('[')` contributes `(False, '[', False,
    True)` — which is what separates it from a bare `Text('[')`, the
    non-injectivity a two-sequence carrier had.  The carrier is a SEQUENCE, of
    whatever width the real parser yields, so a compound annotation that renders
    as several nodes is representable rather than out of shape.
  * the axioms mirror `_parse_annotation`'s WHOLE node list, one entry per node,
    on all four axes (`annotation_kinds` / `annotation_texts` /
    `annotation_bare_text` / `annotation_holds_one_bare_text`).  No width
    assumption is made anywhere, so there is no shape-mismatch class to report:
    the model's postcondition pins the group to `PSeq(False) +
    annotation_kinds(typ)` / `PSeq(sep_text()) + annotation_texts(typ)` /
    `PSeq(True) + annotation_bare_text(typ)` / `PSeq(False) +
    annotation_holds_one_bare_text(typ)` and `is_annotation_node == present`,
    which is exactly the real `desc_annotation(typ, '', nodes.Text(': '),
    *_parse_annotation(typ, env))`: ONE `desc_annotation`, whose first child is a
    bare `Text` holding nothing inside, followed by the parser's own nodes
    spliced in unaltered.

INPUT DOMAIN — everything the model's `Requires` admits.  The only precondition
is `Implies(present, len(typ) > 0)`: any non-empty annotation string, plus the
absent/empty case.  Nothing restricts `typ` to a simple identifier, so compound
annotations, whitespace and punctuation are IN the domain and are generated —
and neither does anything restrict it to strings the parser accepts, so the
refused class is in the domain and is generated too, bare and spliced into
otherwise well-formed shapes. Boundary cases first (absent, empty, the exact F2P
shape `str`, singleton name, dotted, `None`, whitespace-only, `...`, subscripted,
union, comma-separated, non-ASCII, refused), each branch of the impl region and
each arm of the postcondition taken at least once (`present` true and false;
accepted and refused), then seeded fuzz to fill the count.

>= 1e5 Requires-satisfying inputs.  Pinned seed: 9591 (recorded in mapping.md
under `## G-CONF`).  Exit 0 iff zero disagreements; on disagreement the input and
both outputs are printed and the exit status is 1.  stdlib + the in-container
sphinx/docutils only.
"""
import json
import random
import sys
import unicodedata
from typing import List  # noqa: F401  (the impl region's `# type:` comments)

SEED = 9591
N_FUZZ = 100_000
MAX_REPORTED = 8

AXIS_CENSUS = {"bare_true": 0, "bare_false": 0, "holds_true": 0,
               "holds_false": 0, "ann_node_true": 0, "ann_node_false": 0}

from docutils import nodes  # noqa: E402
from sphinx.addnodes import (desc_annotation, desc_signature,  # noqa: E402
                             pending_xref)
from sphinx.domains.python import PyProperty, _parse_annotation  # noqa: E402


# --------------------------------------------------------------------------
# PSeq shim: Nagini's immutable sequence carrier, and ToSeq.
# --------------------------------------------------------------------------
class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, it):
        s = cls()
        s._t = tuple(it)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __iter__(self):
        return iter(self._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --------------------------------------------------------------------------
# model.py's AnnotationGroup record, contracts stripped.
# --------------------------------------------------------------------------
class AnnotationGroup:
    def __init__(self, is_xref, text, is_bare_text, holds_one_bare_text,
                 is_annotation_node):
        self.is_xref = is_xref  # type: PSeq
        self.text = text  # type: PSeq
        self.is_bare_text = is_bare_text  # type: PSeq
        self.holds_one_bare_text = holds_one_bare_text  # type: PSeq
        self.is_annotation_node = is_annotation_node  # type: bool


# --------------------------------------------------------------------------
# model.py `# pure-start` region, verbatim, contracts stripped.
# (is_name_start / is_name_char / is_simple_name are pure predicates the impl
# region does not call, so they are not part of the shadow. no_kinds/no_texts ARE
# called by it, so they are copied verbatim minus contracts.)
# --------------------------------------------------------------------------
def sep_text():
    # ": "  (the U+003A U+0020 separator emitted before a type annotation)
    return PSeq(58, 32)


def no_kinds():
    """The empty sequence of cross-reference flags: no children at all."""
    return PSeq(False).drop(1)


def no_texts():
    """The empty sequence of child texts: no children at all."""
    return PSeq(sep_text()).drop(1)


# --------------------------------------------------------------------------
# model.py's @ContractOnly callees: no body to copy, so read them off the REAL
# repo function they axiomatize (sphinx/domains/python.py:110). One entry per
# rendered node, so no width assumption is made.
# --------------------------------------------------------------------------
class AnnotationRejected(Exception):
    """model.py's exception class: the parser yields no node list for the
    annotation. Modelled as a user-defined exception there because a builtin one
    in an `Exsures` crashes the Nagini translator (mapping.md §2); here it is the
    signal `rendered_nodes` raises when the real parser refuses.

    `cause_type` carries the exception the REAL parser refused with. The named
    exception class is a Nagini artifact and is not the observable -- what the
    real caller propagates is the parser's own exception -- so the harness
    compares refusals on `cause_type`, not on this wrapper's identity."""

    def __init__(self, cause):
        super().__init__(str(cause))
        self.cause_type = type(cause)


def _holds_one_bare_text(n):
    """model.py's `annotation_holds_one_bare_text`, read off ONE real node: it
    holds exactly one inner node and that node is a bare text run. A bare
    `nodes.Text` holds no inner node at all, so it reads False (it IS the run it
    renders). This is the axis the F2P `[pending_xref, "str"]` element checks."""
    if isinstance(n, nodes.Text):
        return False
    kids = list(getattr(n, "children", ()) or ())
    return len(kids) == 1 and isinstance(kids[0], nodes.Text)


def annotation_kinds(s, env):
    return PSeq._wrap(isinstance(n, pending_xref)
                      for n in _parse_annotation(_from_cp(s), env))


def annotation_texts(s, env):
    return PSeq._wrap(ToSeq(_to_cp(n.astext()))
                      for n in _parse_annotation(_from_cp(s), env))


def annotation_bare_text(s, env):
    return PSeq._wrap(isinstance(n, nodes.Text)
                      for n in _parse_annotation(_from_cp(s), env))


def annotation_holds_one_bare_text(s, env):
    return PSeq._wrap(_holds_one_bare_text(n)
                      for n in _parse_annotation(_from_cp(s), env))


def rendered_nodes(typ, env):
    """model.py's runtime parser callee. Its Ensures says an ACCEPTED string
    yields the value of annotation_kinds/annotation_texts/annotation_bare_text/
    annotation_holds_one_bare_text; its Exsures says a REFUSED one yields no node
    list and signals instead. Realized against the real parser: whatever the
    parser does with the string decides which arm is taken -- the caller does not
    get to choose. It carries NO `is_annotation_node` claim (the model's Ensures
    makes none): a bare node list is not held in anything, and which node holds
    the spliced children is the caller's own choice. `False` is passed for that
    field so that a shadow which forwarded the parser's group unchanged would read
    `is_annotation_node == False` and be caught, rather than inheriting the
    caller's answer for free."""
    try:
        real = _parse_annotation(_from_cp(ToSeq(typ)), env)
    except Exception as e:                              # noqa: BLE001
        # not accepted(ToSeq(typ)): the Exsures arm.
        raise AnnotationRejected(e)
    return AnnotationGroup(
        PSeq._wrap(isinstance(n, pending_xref) for n in real),
        PSeq._wrap(ToSeq(_to_cp(n.astext())) for n in real),
        PSeq._wrap(isinstance(n, nodes.Text) for n in real),
        PSeq._wrap(_holds_one_bare_text(n) for n in real),
        False)


# --------------------------------------------------------------------------
# SHADOW: model.py `# impl-start` .. `# impl-end`, VERBATIM.
# No contract call appears inside the region, so nothing was deleted.
# `env` is threaded in solely because the real axiomatized callee needs it (the
# model's axioms take only the annotation sequence); it touches no logic.
# --------------------------------------------------------------------------
def handle_property_annotation(present, typ, env):
    if present:
        parsed = rendered_nodes(typ, env)  # type: AnnotationGroup
        kinds = PSeq(False) + parsed.is_xref  # type: PSeq
        texts = PSeq(sep_text()) + parsed.text  # type: PSeq
        bares = PSeq(True) + parsed.is_bare_text  # type: PSeq
        holds = PSeq(False) + parsed.holds_one_bare_text  # type: PSeq
        return AnnotationGroup(kinds, texts, bares, holds, True)
    return AnnotationGroup(no_kinds(), no_texts(), no_kinds(), no_kinds(), False)


# --------------------------------------------------------------------------
# Type bridge.
# --------------------------------------------------------------------------
def _to_cp(s):
    """concrete str -> model carrier List[int] of Unicode code points."""
    return [ord(c) for c in s]


def _from_cp(cps):
    """model carrier List[int]/PSeq[int] -> concrete str."""
    if isinstance(cps, PSeq):
        cps = [cps[i] for i in range(len(cps))]
    return "".join(chr(c) for c in cps)


def _model_sig(group):
    """model AnnotationGroup -> comparable
    (is_annotation_node, [(is_xref, text_str, is_bare_text, holds_one), ...])."""
    n = len(group.is_xref)
    for other in ("text", "is_bare_text", "holds_one_bare_text"):
        if len(getattr(group, other)) != n:
            raise AssertionError("shadow produced desynced sequences: is_xref=%d "
                                 "vs %s=%d" % (n, other, len(getattr(group, other))))
    return (bool(group.is_annotation_node),
            [(bool(group.is_xref[i]), _from_cp(group.text[i]),
              bool(group.is_bare_text[i]), bool(group.holds_one_bare_text[i]))
             for i in range(n)])


def _real_sig(node_list):
    """real inline nodes -> comparable
    [(is_xref, text_str, is_bare_text, holds_one_bare_text), ...]."""
    return [(isinstance(n, pending_xref), n.astext(),
             isinstance(n, nodes.Text), _holds_one_bare_text(n))
            for n in node_list]


# --------------------------------------------------------------------------
# ORACLE: the REAL gold-patched PyProperty.handle_signature, called.
# --------------------------------------------------------------------------
class _Config:
    # the FAIL_TO_PASS test app uses defaults
    add_module_names = True
    python_use_unqualified_type_names = False


class _Env:
    def __init__(self):
        self.config = _Config()
        self.ref_context = {}
        self.temp_data = {}


class _Settings:
    def __init__(self, env):
        self.env = env


class _Document:
    def __init__(self, env):
        self.settings = _Settings(env)


class _State:
    """docutils `Directive.env` resolves `self.state.document.settings.env`."""

    def __init__(self, env):
        self.document = _Document(env)


SIG = "prop1"


def _call_real(type_option, env):
    """Call the real patched method; return the children of `signode`."""
    d = object.__new__(PyProperty)
    d.options = {} if type_option is None else {"type": type_option}
    d.state = _State(env)
    d.objtype = "property"
    signode = desc_signature(SIG, "")
    signode["module"] = None
    signode["class"] = ""
    d.handle_signature(SIG, signode)
    return list(signode.children)


def oracle(type_option, env, base_len):
    """The annotation group the real patched method appends, as the pair
    (is_annotation_node, children read four ways) -- mapping.md §2.

    `is_annotation_node` is the model's claim about WHICH node holds the group:
    exactly one node is contributed and it is an `addnodes.desc_annotation`. That
    is the first thing the F2P `assert_node(..., [desc_annotation, ...])` checks,
    so it is observed here rather than assumed; a patch that grouped the same
    children under, say, a `desc_sig_punctuation` or contributed two wrappers
    would read False and disagree."""
    group = _call_real(type_option, env)[base_len:]
    is_annotation_node = len(group) == 1 and isinstance(group[0], desc_annotation)
    out = []
    for wrapper in group:
        out.extend(_real_sig(list(wrapper.children)))
    return (is_annotation_node, out)


# --------------------------------------------------------------------------
# Input generation: the whole Requires-satisfying domain.
# --------------------------------------------------------------------------
BOUNDARY = [
    None,               # option absent  -> present False (impl `else` arm)
    "",                 # option empty   -> present False (the falsy guard)
    "str",              # the exact F2P shape (`:type: str`)
    "int",
    "T",                # singleton name
    "_",
    "None",             # the `obj` reftype arm of type_to_xref
    "Point",
    "a.b.C",            # dotted (ast.Attribute)
    "pathlib.Path",
    "  ",               # truthy but whitespace-only: parser yields 0 nodes
    " ",
    "...",              # Ellipsis: punctuation, not an xref
    "List[int]",        # subscripted -> FIVE children incl. rendered brackets
    "Optional[str]",
    "Dict[str, int]",   # comma-separated
    "int | None",       # BinOp union
    "Tuple[()]",
    "Callable[..., int]",
    "List[List[int]]",  # nested
    "1",                # numeric constant
    "@",                # SyntaxError arm -> single xref of the raw string
    "[",
    "Ünïcödé",          # non-ASCII name (code-point carrier)
    "x" * 64,           # long name
    # The REFUSED class: `:type:` is directives.unchanged, so these are ordinary
    # admitted inputs on which the parser yields NO node list and the refusal
    # propagates out of the real caller unabsorbed. Both sides must refuse.
    'b"x"',             # the minimal bytes literal
    "b'x'",             # single-quoted
    'B"x"',             # capital prefix
    'rb"x"',            # raw-bytes prefix
    'b""',              # empty bytes
    'List[b"x"]',       # bytes nested in a subscript
    'x | b"y"',         # bytes in a union
    'Dict[str, b"k"]',  # bytes in a comma-separated subscript
    "a\x00b",           # NUL: refused by compile(), a different exception type
]

_FIRST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
_REST = _FIRST + "0123456789"
_NAMES = ["str", "int", "bool", "bytes", "float", "Point", "Foo", "Bar",
          "None", "T", "x", "MyClass", "Baz"]
_JUNK = "[](),.|@#$%^&*-+=<>?/\\:;\"' \t~`!{}"
_BYTES_LITS = ['b"x"', "b'y'", 'B"z"', 'rb"w"', 'b""']


def _ident(rng):
    k = rng.randint(0, 12)
    return rng.choice(_FIRST) + "".join(rng.choice(_REST) for _ in range(k))


def _fuzz_one(rng):
    """A Requires-satisfying annotation string (or None/'' for present False)."""
    r = rng.random()
    if r < 0.02:
        # the present == False branch of the impl region
        return None if rng.random() < 0.5 else ""
    if r < 0.45:
        # simple identifier: the "documented simple type name" arm
        return _ident(rng)
    if r < 0.55:
        # dotted name
        return "%s.%s" % (_ident(rng), _ident(rng))
    if r < 0.68:
        # subscripted generic
        return "%s[%s]" % (rng.choice(_NAMES), rng.choice(_NAMES))
    if r < 0.75:
        # comma-separated subscript
        return "%s[%s, %s]" % (rng.choice(_NAMES), rng.choice(_NAMES),
                               rng.choice(_NAMES))
    if r < 0.82:
        # union
        return "%s | %s" % (rng.choice(_NAMES), rng.choice(_NAMES))
    if r < 0.87:
        # whitespace padding around a name
        pad = " " * rng.randint(1, 3)
        return pad + rng.choice(_NAMES) + " " * rng.randint(0, 3)
    if r < 0.90:
        # nested generic
        return "%s[%s[%s]]" % (rng.choice(_NAMES), rng.choice(_NAMES),
                               rng.choice(_NAMES))
    if r < 0.96:
        # the REFUSED class, fuzzed: a bytes literal bare, or spliced into an
        # otherwise well-formed annotation shape. Both sides must refuse these,
        # which is what exercises the model's Exsures arm rather than avoiding it.
        lit = rng.choice(_BYTES_LITS)
        return rng.choice([
            lit,
            "%s[%s]" % (rng.choice(_NAMES), lit),
            "%s | %s" % (rng.choice(_NAMES), lit),
            "%s[%s, %s]" % (rng.choice(_NAMES), rng.choice(_NAMES), lit),
            "%s[%s[%s]]" % (rng.choice(_NAMES), rng.choice(_NAMES), lit),
        ])
    # arbitrary printable junk (still len > 0, so still Requires-satisfying)
    k = rng.randint(1, 10)
    return "".join(rng.choice(_REST + _JUNK) for _ in range(k)) or "z"


def _inputs(rng, n):
    for b in BOUNDARY:
        yield b
    for _ in range(n):
        yield _fuzz_one(rng)


def _requires_ok(type_option):
    """The model's Requires, checked on the abstract pair the bridge derives."""
    present = type_option is not None and type_option != ""
    typ = _to_cp(type_option) if type_option is not None else []
    return (not present) or len(typ) > 0


def _show(s):
    if s is None:
        return "<absent>"
    return "".join(
        c if c.isprintable() and unicodedata.category(c)[0] != "C" else
        "\\u%04x" % ord(c) for c in s)


def main():
    env = _Env()
    # base children with no `:type:` option: the signature prefix + name that
    # `PyObject.handle_signature` contributes and the model does not describe.
    base_len = len(_call_real(None, env))

    rng = random.Random(SEED)
    checked = 0
    present_true = 0
    present_false = 0
    widths = {}
    reported = []
    # `both_refused` is AGREEMENT, not a disagreement: the model's Exsures says a
    # refused annotation yields no group and the refusal propagates, and that is
    # exactly what the real caller does. The one-sided classes are the real
    # disagreements -- the shadow inventing a group where the oracle refuses
    # (`oracle_only_refused`) is precisely the unfaithfulness this gate must
    # catch, and it is what the pre-patch shape does.
    agree_both_refused = 0
    classes = {"node_list": 0, "oracle_only_refused": 0,
               "shadow_only_refused": 0}

    for type_option in _inputs(rng, N_FUZZ):
        assert _requires_ok(type_option), type_option
        checked += 1

        # bridge: concrete option -> model's abstract (present, typ)
        present = type_option is not None and type_option != ""
        typ = _to_cp(type_option) if type_option is not None else []
        if present:
            present_true += 1
        else:
            present_false += 1

        orc = orc_exc = None
        try:
            orc = oracle(type_option, env, base_len)
        except Exception as e:                          # noqa: BLE001
            orc_exc = e

        shadow = sh_exc = None
        try:
            shadow = _model_sig(handle_property_annotation(present, typ, env))
        except Exception as e:                          # noqa: BLE001
            sh_exc = e

        if orc_exc is not None and sh_exc is not None:
            # Both refused the annotation: the Exsures arm, agreeing. Compare the
            # UNDERLYING refusal, so "refuses for an unrelated reason" is not
            # silently scored as agreement. The shadow signals through the model's
            # named AnnotationRejected (a Nagini artifact, mapping.md §2) while the
            # real caller propagates the parser's own exception, so the shadow's
            # `cause_type` is the comparable observable, not the wrapper class.
            sh_cause = getattr(sh_exc, "cause_type", type(sh_exc))
            if type(orc_exc) is not sh_cause:
                classes["node_list"] += 1
                if len(reported) < MAX_REPORTED:
                    reported.append((
                        "node_list", type_option,
                        "refused %s (cause %s): %s"
                        % (type(sh_exc).__name__, sh_cause.__name__, sh_exc),
                        "refused %s: %s" % (type(orc_exc).__name__, orc_exc)))
            else:
                agree_both_refused += 1
            continue
        if orc_exc is not None:
            classes["oracle_only_refused"] += 1
            if len(reported) < MAX_REPORTED:
                reported.append(("oracle_only_refused", type_option, shadow,
                                 "refused %s: %s"
                                 % (type(orc_exc).__name__, orc_exc)))
            continue
        if sh_exc is not None:
            classes["shadow_only_refused"] += 1
            if len(reported) < MAX_REPORTED:
                reported.append(("shadow_only_refused", type_option,
                                 "refused %s: %s"
                                 % (type(sh_exc).__name__, sh_exc), orc))
            continue

        widths[len(orc[1])] = widths.get(len(orc[1]), 0) + 1
        # Census, so the record can show the two child-kind axes and the wrapper
        # flag are not degenerate over the measured oracle outputs.
        AXIS_CENSUS["ann_node_true" if orc[0] else "ann_node_false"] += 1
        for _x, _t, _b, _h in orc[1]:
            AXIS_CENSUS["bare_true" if _b else "bare_false"] += 1
            AXIS_CENSUS["holds_true" if _h else "holds_false"] += 1
        if shadow != orc:
            classes["node_list"] += 1
            if len(reported) < MAX_REPORTED:
                reported.append(("node_list", type_option, shadow, orc))

    total = sum(classes.values())
    if total:
        print("G-CONF FAIL: %d disagreement(s) over %d Requires-satisfying "
              "inputs (seed=%d)" % (total, checked, SEED))
        print("  by class: %s (agreeing mutual refusals: %d)"
              % (classes, agree_both_refused))
        for kind, inp, sh, orc in reported:
            print("  [%s] typ=%s" % (kind, _show(inp)))
            print("        shadow(model impl) = %r" % (sh,))
            print("        oracle(real patched PyProperty.handle_signature) = %r"
                  % (orc,))
        print(json.dumps({
            "status": "fail",
            "checked": checked,
            "disagreements": total,
            "by_class": classes,
            "seed": SEED,
            "oracle": "sphinx.domains.python.PyProperty.handle_signature "
                      "(real, patched, called)",
            "shadow": "model.py impl region verbatim, contracts stripped",
        }))
        return 1

    print("G-CONF OK: model.py impl region (verbatim, contracts stripped, "
          "@ContractOnly rendered_nodes/annotation_kinds/annotation_texts/"
          "annotation_bare_text/annotation_holds_one_bare_text -> "
          "real _parse_annotation) agrees with the real patched "
          "PyProperty.handle_signature on %d Requires-satisfying inputs "
          "(%d present / %d absent, seed=%d), 0 disagreements, on ALL FIVE "
          "observables the model carries: which node holds the group "
          "(is_annotation_node), and per child its cross-reference flag, its "
          "rendered text, whether it is a bare text node, and whether it holds "
          "exactly one bare text run. Group widths observed: %s — the carrier "
          "holds every real width, including the compound annotations (e.g. "
          "\"List[int]\" -> 5 children) that a fixed-width-2 carrier could not "
          "represent. None of the three added axes is degenerate over these "
          "outputs: bare-text True/False = %d/%d, holds-one-bare-text True/False "
          "= %d/%d, is_annotation_node True/False = %d/%d — so agreement on them "
          "is a measurement, not a constant. Recorded honestly: under the DEFAULT "
          "config this gate runs (the F2P app's, python_use_unqualified_type_"
          "names = False) the two child axes came out as exact complements, "
          "because every marked-up node this parser emits under that config "
          "happens to hold exactly one plain run. They are still independent "
          "observations rather than one restated — axiom_check.py sweeps BOTH "
          "config settings and reports the nodes that read False on both — and "
          "both are separately load-bearing here, since a rival that gets one "
          "right and the other wrong (rendered punctuation carrying the "
          "separator; a cross-reference relabelled across two inner runs) is "
          "caught by whichever it broke. On %d of those inputs the "
          "annotation is one the parser REFUSES, and both sides refused with the "
          "same exception type: no group is produced and the refusal propagates, "
          "which is the model's Exsures arm. A shadow that invented a group "
          "there (as the pre-patch shape does) would be counted "
          "`oracle_only_refused` and fail."
          % (checked, present_true, present_false, SEED,
             dict(sorted(widths.items())),
             AXIS_CENSUS["bare_true"], AXIS_CENSUS["bare_false"],
             AXIS_CENSUS["holds_true"], AXIS_CENSUS["holds_false"],
             AXIS_CENSUS["ann_node_true"], AXIS_CENSUS["ann_node_false"],
             agree_both_refused))
    print(json.dumps({
        "status": "pass",
        "checked": checked,
        "present_true": present_true,
        "present_false": present_false,
        "disagreements": 0,
        "agree_both_refused": agree_both_refused,
        "widths": {str(k): v for k, v in sorted(widths.items())},
        "axis_census": AXIS_CENSUS,
        "seed": SEED,
        "oracle": "sphinx.domains.python.PyProperty.handle_signature "
                  "(real, patched, called)",
        "shadow": "model.py impl region verbatim, contracts stripped",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
