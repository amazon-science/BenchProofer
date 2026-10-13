#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9258 (nagini).

Refutation target: does model.py's MODEL agree with the REAL patched repository
function it claims to model? No other gate covers this leg (G-VERIFY: impl meets
spec; G-PBT: no wrong impl meets the spec; neither looks at the repo).

SHADOW (provenance "direct" — the model IS Python)
--------------------------------------------------
The `# impl-start`/`# impl-end` regions of model.py's `render_nodes`,
`next_sep_idx`, `sep_end_idx`, `strip_left_idx`, `copy_span`, `split_render`,
`first_bar_idx` and `slice_trim`, copied VERBATIM below with only the contract
calls deleted (`Requires`, `Ensures`, `Invariant`, `Assert`, `Acc`, `Old`) plus
their `# invariants-start`/`# invariants-end` marker lines. Nothing is renamed,
restructured or "simplified": the loop shapes, the `while True` + `break`, the
`j >= n` / `p >= n` tests, the `+ 0` index readings and the append order are
byte-for-byte the model's. Four `else:` branches (two in `render_nodes`, two in
`split_render`) hold nothing but an `Assert`, so stripping leaves them as an
explicit `pass`; that is the only edit. After the `Assert` lines are stripped,
both top-level impls still call their real helper functions (`render_nodes` and
`split_render` -> `next_sep_idx` -> `sep_end_idx` -> `strip_left_idx`, and
`copy_span`), so every helper impl region is copied verbatim too and is genuinely
executed. `first_bar_idx` and `slice_trim` are no longer reached from either
top-level impl — they are the bar-position and trimmed-segment helpers, which the
kind-only scan does not use — so they are called directly, once per input, and
checked against the pure specs their own postconditions name.

The `@Pure` helpers the regions and their postconditions depend on (`is_space`,
`first_bar`, `strip_left`, `strip_right`, `seg_text`, `kinds`, `no_other_sep`,
`well_formed`, `sep_end`, `next_sep`, `rendered`, `marks`) are copied verbatim
minus contracts as well. They are used for (a) the self-consistency assertions
`render_nodes(cps) == rendered(cps, 0)` and `split_render(cps) == marks(cps, 0)`,
which trip if a shadow was mis-copied from its impl region, and (b) reporting
which inputs have the bar-only `well_formed` shape. NEITHER modeled function has
a domain precondition, so no input is filtered out of either comparison;
`well_formed` and `kinds` are exercised here as pure functions in their own right
(`kinds` is the bar-only kind reading validated by G-AX §3.1).

There are NO `@ContractOnly` callees in this bundle (meta.json `axioms: []`,
model.py `axioms` region), so nothing is axiomatized-and-assumed here; the
tokenisation is a deep model and this script exercises it against the real code.

`PSeq` is realized by the standard immutable-tuple shim used across this corpus
(`take`/`drop`/`+`/`len`/`[]`/`==`), and `ToSeq(list)` materializes one.

ORACLE (called, not transliterated)
-----------------------------------
The REAL patched `sphinx.domains.python.PyXrefMixin.make_xrefs`
(`sphinx/domains/python.py:304`, the changed `delims` line 307 — mapping.md §1).
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH, so the patched module is imported and CALLED; this script applies no
diff and reproduces no regex. It is driven through a real `PyField` instance
(`PyField.make_xrefs is PyXrefMixin.make_xrefs` — asserted at startup), and the
patched delimiter is asserted present in `inspect.getsource` at startup so a
failed patch-apply can never read as a green run.

Unlike the velvet/lean siblings — which transliterate the regex tokeniser into
Python because Lean cannot call it — the nagini shadow is Python, so here the
tokeniser is NOT reimplemented: `re.split`/`re.match` are reached by calling the
real method. The only stubbed thing is the `BuildEnvironment` argument (a
two-method stand-in supplying `ref_context` and `get_domain().process_field_xref`)
because a live env needs a full Sphinx app build. That stub is consumed only by
the `make_xref` CALLEE, strictly after the split/classify logic under
specification has already decided each node's kind, so it cannot mask a
divergence in the modeled behaviour.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
The model works over `List[int]` code points; the real function takes a `str` and
returns `List[Node]`. Forward: `cps = [ord(ch) for ch in target]`.

Backward, node KIND: the k-th real node is a cross-reference iff
`isinstance(node, addnodes.pending_xref)`, else it is the literal separator node
— exactly mapping.md §2's node-kind abstraction.

Backward, node TEXT (this is what makes the node stream observable rather than
assumed): the real function takes the `innernode` factory each node's text is
built from as an ARGUMENT, and calls it exactly once per produced node with that
node's own piece of the input — in the cross-reference branch through the xref
builder (`docfields.py:69`, `refnode += contnode or innernode(target, target)`),
in the separator branch directly (`python.py:319`). A recording stand-in is
therefore passed in as `innernode`, and the text of the k-th node is read
straight off the k-th call. `len(calls) == len(nodes)` is asserted on EVERY
input, so "exactly once per node, in order" is measured rather than assumed. The
stand-in builds and returns the same `emphasis` node the default factory would,
and the split/classify logic under specification never consults the result, so it
cannot change what is being measured.

Independently cross-checked: `node.astext()` is compared against the recorded
text on every node. They coincide except in one documented case, which the check
states exactly rather than tolerating: when a cross-reference piece begins with
'.' or '~', the `make_xref` CALLEE deliberately re-writes the DISPLAYED text to
`piece[1:]` / `piece.split('.')[-1]` (`python.py:293-301`). So the modeled
observable is each node's PIECE OF THE INPUT — the tokenisation, which is what
the change under specification decides — and the display rewrite downstream of it
is pinned as a known exact function of that piece, not waved past.

Encoding of a node list into the model's carrier: each node contributes its
piece's code points followed by -1 (cross-reference) or -2 (literal separator);
the list is closed by -3. Code points are non-negative, so the encoding is
injective: one model sequence means one node list.

Inputs are generated as `str`. NEITHER comparison applies a filter: both modeled
obligations are stated for every specification, so every input drawn is counted
for both. `well_formed` is evaluated per input only to report how many of them
have the bar-only shape.

INPUTS
------
>= 1e5 inputs for EACH observable, both measured on all of them. Both obligations
are domain-free, so every stratum is unfiltered — including every shape the
bar-only `well_formed` predicate throws out, which is exactly the region an
unpinned spec would leave free.

Strata 1-4 have the bar-only `well_formed` shape by construction or by filtering
(the predicate is a pure function of the input, not a precondition any more):
  1. boundary list — empty-ish/singleton/the F2P shape `int | str`, both impl
     branches (the `j >= n` break and the separator-emit path), 1..k bars, padded
     and unpadded bars, dotted names, embedded non-delimiting `or`/`.`;
  2. non-bar-shape boundary list, asserted to be REJECTED by `well_formed`
     (`List[int]`, `Dict[str, str]`, `str or int`, `|`, ` | `, leading/trailing
     bars), so that predicate is shown to discriminate rather than admit
     everything — and both obligations are measured on these inputs as well;
  3. structured union specs — names joined by padded bars, the realistic shape
     the change targets, so the patched `\\s*\\|\\s*` branch is exercised
     densely and not routed around;
  4. seeded fuzz over the FULL delimiter alphabet — type-name chars, ASCII
     space, bar, `[ ] ( ) , .`, `o`, `r`, AND the non-ASCII whitespace the real
     `\\s` class matches (TAB, NL, VT, FF, NBSP, NEL, EM/IDEOGRAPHIC SPACE,
     NNBSP, U+2028, U+001C). The unicode-whitespace code points are included
     deliberately: `no_other_sep`/`strip_*` recognise only code point 32 as a
     space while the real regex `\\s` matches all of them, so this is precisely
     where the model's domain predicate and the real tokeniser can disagree.
     Omitting them would produce a green run that certifies nothing.

Stratum 5 is the FULL domain, unfiltered, and is where both obligations do their
hardest work:
  5. seeded fuzz over the same alphabet with NO `well_formed` filter, plus a
     boundary list of the shapes `well_formed` rejects — brackets, commas, `or`,
     `...`, bare/leading/trailing/doubled bars, whitespace-only segments, the
     empty string, and '.'/'~'-prefixed targets (which drive the documented
     display rewrite). Every draw is counted, none discarded.

OBSERVABLES
-----------
PRIMARY = the whole node STREAM pinned by `render_nodes`'s postcondition
`ToSeq(Result()) == rendered(ToSeq(target), 0)`: node count, per-node kind AND
per-node exact carried text, over the WHOLE input domain. A disagreement here
fails the gate.

ALSO PRIMARY = the node-KIND sequence pinned by `split_render`'s postcondition
`ToSeq(Result()) == marks(ToSeq(target), 0)`: node count and per-node kind, over
the WHOLE input domain as well. A disagreement here fails the gate too. It is a
projection of the stream above, so it is additionally checked to BE that
projection on every input — a kind sequence that drifted from the stream the same
file pins would be a contradiction inside one model.

Nothing is recorded as a merely-secondary observable any more. The earlier
version of this script measured the cross-reference payload
(`slice_trim`/`seg_text`) but let it print without affecting the exit code,
because the payload was then outside the modeled output; the divergences it
printed were real (the trimmed segment is not the text the real node carries).
The payload is now INSIDE the modeled output, via the node stream, and the model
of it is the untrimmed span — so it is measured as a first-class observable and
it drives the exit code. `seg_text` survives as the trimmed-segment reading of a
bar-separated name, checked against its executable counterpart `slice_trim`; the
check that it equals the real carried text is deliberately gone rather than
downgraded, because that equality is false and the node stream states the true
relation instead.

Pinned seed: SEED = 92580 (recorded in mapping.md §G-CONF).
Exit 0 iff zero node-stream and zero kind-sequence disagreements.
stdlib + the repo under test only.
"""
import json
import random
import sys

SEED = 92580
N_FUZZ_INDOMAIN = 100_000
N_FUZZ_FULL = 150_000
N_STRUCTURED = 4_000
MAX_LEN = 24
MAX_REPORT = 8

# model.py carrier constants (mapping.md §2): '|' == 124, ' ' == 32.
BAR = 124
SPACE = 32

# the model's helpers are front-recursive; MAX_LEN keeps depth small, but raise
# the limit so a long boundary case can never masquerade as a disagreement.
sys.setrecursionlimit(10000)


# --- PSeq shim: the immutable Viper sequence, ops used by the pure region -----

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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


PSeq = PSeqShim


def ToSeq(xs):
    return PSeqShim._wrap(xs)


# --- model.py `pure` region, verbatim minus contracts -------------------------

def is_space(c):
    return ((9 <= c and c <= 13) or (28 <= c and c <= 32) or c == 133 or
            c == 160 or c == 5760 or (8192 <= c and c <= 8202) or
            c == 8232 or c == 8233 or c == 8239 or c == 8287 or c == 12288)


def first_bar(s, i):
    if i >= len(s):
        return i
    if s[i] == 124:
        return i
    return first_bar(s, i + 1)


def kinds(s, i):
    if first_bar(s, i) >= len(s):
        return PSeq(True)
    return PSeq(True) + (PSeq(False) + kinds(s, first_bar(s, i) + 1))


def strip_left(s, i, j):
    if i >= j:
        return i
    if i >= len(s):
        return i
    if not is_space(s[i]):
        return i
    return strip_left(s, i + 1, j)


def strip_right(s, i, j):
    if i >= j:
        return j
    if j - 1 >= len(s):
        return j
    if not is_space(s[j - 1]):
        return j
    return strip_right(s, i, j - 1)


def seg_text(s, i, j):
    a = strip_left(s, i, j)
    b = strip_right(s, a, j)
    return s.take(b).drop(a)


def no_other_sep(s, i):
    if i >= len(s):
        return True
    if s[i] == 91 or s[i] == 93 or s[i] == 40 or s[i] == 41 or s[i] == 44:
        return False
    if s[i] == 46 and i + 2 < len(s) and s[i + 1] == 46 and s[i + 2] == 46:
        return False
    if (is_space(s[i]) and i + 3 < len(s) and s[i + 1] == 111 and
            s[i + 2] == 114 and is_space(s[i + 3])):
        return False
    return no_other_sep(s, i + 1)


def well_formed(s, i):
    if not no_other_sep(s, i):
        return False
    if len(seg_text(s, i, first_bar(s, i))) == 0:
        return False
    if first_bar(s, i) >= len(s):
        return True
    return well_formed(s, first_bar(s, i) + 1)


def sep_end(s, i):
    a = strip_left(s, i, len(s))
    if a < len(s) and (s[a] == 91 or s[a] == 93 or s[a] == 40 or s[a] == 41 or
                       s[a] == 44):
        c = strip_left(s, a + 1, len(s))
        if (c + 2 < len(s) and s[c] == 111 and s[c + 1] == 114 and
                is_space(s[c + 2])):
            return strip_left(s, c + 3, len(s)) + 0
        return strip_left(s, a + 1, len(s)) + 0
    if (i < len(s) and is_space(s[i]) and a + 2 < len(s) and s[a] == 111 and
            s[a + 1] == 114 and is_space(s[a + 2])):
        return strip_left(s, a + 2, len(s)) + 0
    if a < len(s) and s[a] == 124:
        return strip_left(s, a + 1, len(s)) + 0
    if i + 2 < len(s) and s[i] == 46 and s[i + 1] == 46 and s[i + 2] == 46:
        return i + 3
    return -1


def next_sep(s, i):
    if i >= len(s):
        return i + 0
    if sep_end(s, i) >= 0:
        return i + 0
    return next_sep(s, i + 1)


def rendered(s, i):
    if next_sep(s, i) >= len(s):
        if i < len(s):
            return (s.take(len(s)).drop(i) + PSeq(-1)) + PSeq(-3)
        return PSeq(-3)
    if next_sep(s, i) > i:
        return ((s.take(next_sep(s, i)).drop(i) + PSeq(-1)) +
                (s.take(sep_end(s, next_sep(s, i))).drop(next_sep(s, i)) +
                 PSeq(-2))) + rendered(s, sep_end(s, next_sep(s, i)))
    return (s.take(sep_end(s, next_sep(s, i))).drop(i) + PSeq(-2)) + \
        rendered(s, sep_end(s, next_sep(s, i)))


def marks(s, i):
    if next_sep(s, i) >= len(s):
        if i < len(s):
            return PSeq(True)
        return PSeq(True).drop(1)
    if next_sep(s, i) > i:
        return (PSeq(True) + PSeq(False)) + marks(s, sep_end(s, next_sep(s, i)))
    return PSeq(False) + marks(s, sep_end(s, next_sep(s, i)))


# --- model.py `impl` regions, VERBATIM minus contract calls -------------------
# split_render: model.py's `# impl-start` .. `# impl-end`, contracts stripped.

def split_render(target):
    result = []  # type: List[bool]
    n = len(target)
    i = 0
    while True:
        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                # the trailing text is one cross-reference.
                result.append(True)
            else:
                pass
            break
        e = sep_end_idx(target, j) + 0
        if j > i:
            # the text before the separator is one cross-reference.
            result.append(True)
        else:
            pass
        # the separator itself is one literal node.
        result.append(False)
        i = e
    return result


# first_bar_idx: model.py lines 258-273.

def first_bar_idx(s, i):
    k = i
    while k < len(s):
        if s[k] == 124:
            return k
        k = k + 1
    return k


# slice_trim: model.py lines 287-328.

def slice_trim(s, i, j):
    a = i
    while a < j and is_space(s[a]):
        a = a + 1
    # `a` is now strip_left(s, i, j); reference that nested form directly so the
    # final equality with seg_text needs no nested-application congruence.
    b = j
    while b > a and is_space(s[b - 1]):
        b = b - 1
    out = []  # type: List[int]
    t = a
    while t < b:
        out.append(s[t])
        t = t + 1
    return out


# render_nodes / next_sep_idx / sep_end_idx / strip_left_idx / copy_span:
# model.py's `# impl-start` .. `# impl-end` regions, verbatim minus contracts.
# The two `else:` branches that held nothing but an `Assert` become `pass`.

def render_nodes(target):
    out = []  # type: List[int]
    n = len(target)
    i = 0
    while True:
        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                # the trailing text is one cross-reference carrying it verbatim.
                copy_span(out, target, i, n)
                out.append(-1)
            else:
                pass
            out.append(-3)
            break
        e = sep_end_idx(target, j) + 0
        if j > i:
            # the text before the separator is one cross-reference carrying
            # exactly the specification's characters over [i, j).
            copy_span(out, target, i, j)
            out.append(-1)
        else:
            pass
        # the separator itself is one literal node carrying [j, e) verbatim.
        copy_span(out, target, j, e)
        out.append(-2)
        i = e
    return out


def next_sep_idx(s, i):
    k = i
    while k < len(s):
        if sep_end_idx(s, k) >= 0:
            return k
        k = k + 1
    return k


def sep_end_idx(s, i):
    n = len(s)
    a = strip_left_idx(s, i, n)
    if a < n and (s[a] == 91 or s[a] == 93 or s[a] == 40 or s[a] == 41 or
                  s[a] == 44):
        c = strip_left_idx(s, a + 1, n)
        if (c + 2 < n and s[c] == 111 and s[c + 1] == 114 and
                is_space(s[c + 2])):
            return strip_left_idx(s, c + 3, n)
        return strip_left_idx(s, a + 1, n)
    if (i < n and is_space(s[i]) and a + 2 < n and s[a] == 111 and
            s[a + 1] == 114 and is_space(s[a + 2])):
        return strip_left_idx(s, a + 2, n)
    if a < n and s[a] == 124:
        return strip_left_idx(s, a + 1, n)
    if i + 2 < n and s[i] == 46 and s[i + 1] == 46 and s[i + 2] == 46:
        return i + 3
    return -1


def strip_left_idx(s, i, j):
    a = i
    while a < j and is_space(s[a]):
        a = a + 1
    return a


def copy_span(out, s, i, j):
    t = i
    while t < j:
        out.append(s[t])
        t = t + 1


# --- the type bridge (mapping.md §2, inverted) --------------------------------

def to_codepoints(target):
    """repo `str` -> model `List[int]` carrier."""
    return [ord(ch) for ch in target]


def real_node_kinds(nodes_out, pending_xref):
    """real `List[Node]` -> model `List[bool]` of node kinds: True for the
    `make_xref(sub_target)` cross-reference branch, False for the literal
    `innernode`/`contnode` separator branch."""
    return [isinstance(nd, pending_xref) for nd in nodes_out]


def decode_stream(carrier):
    """The model carrier read back as `[(piece, "xref"|"sep")]`, so a reported
    disagreement is legible. Inverse of `encode_stream` (which is injective)."""
    out = []
    buf = []
    for v in carrier:
        if v == -3:
            break
        if v == -1 or v == -2:
            out.append(("".join(buf), "xref" if v == -1 else "sep"))
            buf = []
        else:
            buf.append(chr(v))
    return out


def encode_stream(pieces_and_kinds):
    """real `List[(piece, is_xref)]` -> the model's `List[int]` carrier: each
    node's code points, then -1 (cross-reference) or -2 (literal separator);
    -3 closes the list. Non-negative code points make this injective."""
    out = []
    for piece, is_xref in pieces_and_kinds:
        out.extend(ord(ch) for ch in piece)
        out.append(-1 if is_xref else -2)
    out.append(-3)
    return out


# --- oracle plumbing: the recording `innernode` factory ----------------------
# The real function BUILDS each node's text through the `innernode` argument, so
# passing a recorder in reads each node's piece of the input off the real code
# rather than re-deriving it. Not a stub of anything under specification: the
# split/classify logic never inspects what comes back, and the object returned is
# the very node the default factory would have built.

def _make_recorder(nodes_mod):
    class _RecordingInner:
        def __init__(self):
            self.texts = []

        def __call__(self, rawsource, text, *children, **attrs):
            self.texts.append(text)
            return nodes_mod.emphasis(rawsource, text, *children, **attrs)

    return _RecordingInner


# --- oracle plumbing: the BuildEnvironment stand-in --------------------------
# Consumed only by the make_xref CALLEE, after the split/classify logic under
# specification has already fixed every node kind.

class _StubDomain:
    def process_field_xref(self, pnode):
        pass


class _StubEnv:
    def __init__(self):
        self.ref_context = {}

    def get_domain(self, name):
        return _StubDomain()


# --- input generation: every stratum filtered by the model's own Requires ----

BOUNDARY_IN = [
    # the F2P / problem-statement shape
    "int | str",
    "bytes | str",
    "bytes | str | None",
    # singleton: the `p >= n` break on the first iteration (no separator emit)
    "int",
    "S",
    "SomeClass",
    "mod.Class",
    # the separator-emit branch, unpadded / padded / asymmetric / wide
    "int|str",
    "a|b",
    "int  |  str",
    "foo |bar",
    "x| y",
    "int   |   str",
    # many bars: the loop iterates
    "a | b | c",
    "a | b | c | d",
    "a|b|c|d|e|f|g|h",
    "List | Dict | Tuple | Set",
    "mod.Class | other.Class",
    # embedded-but-non-delimiting 'or' and single dots
    "colored | factor",
    "a or",
    "or | ore",
    "x.y.z | a.b.c",
    # interior spaces inside a segment (trimming exercised on both ends)
    "a b | c d",
    " int | str",
    "int | str ",
    # non-ASCII whitespace PADDING a bar keeps the bar-only shape (consumed into
    # the separator exactly as an ASCII space is; each segment still names a type)
    "int\t|\tstr",
    "a\n|\nb",
    "x\xa0|\xa0y",
    "int\u3000|\u3000str",
    "a \t| \tb",
    "aorb | c",
    "ore\t| int",
]

# these MUST fall outside the bar-only `well_formed` shape; asserted, so that
# predicate is shown to discriminate instead of admitting everything. Both
# obligations are measured on them (neither has a domain clause).
BOUNDARY_OUT = [
    "",                     # empty: seg_text empty -> rejected
    "|",
    " | ",
    "|int",
    "int|",
    "a||b",
    "List[int]",
    "Dict[str, str]",
    "Tuple[str, ...]",
    "str or int",
    "...",
    "a, b",
    "Optional[int] | str",
    # An `or` bounded by ANY whitespace is a separator; a segment of nothing but
    # whitespace names no type. Both are out of domain exactly as their
    # ASCII-space counterparts ("str or int", "int|", " | ") are.
    "a\tor\tb", "int\tor\tstr", "a\nor\nb", "x\xa0or\xa0y",
    "a\u3000or\u3000b", "a\tor\tb\t|\tc",
    "a|\t", "\t|a", "a|\t|b", "a|\xa0", "\xa0|a", "\x0b|ce\r",
    "\u3000|a", "int\t|\t", "\n|\n",
]

# Stratum 5: no domain claim at all. Every shape the bar-only `well_formed`
# predicate rejects, plus the '.'/'~'-prefixed targets that drive the documented
# display rewrite. Both obligations are measured on all of it.
BOUNDARY_FULL = [
    # bracket / comma / `or` / ellipsis separators: rejected by no_other_sep, so
    # these are the shapes only a domain-free obligation reaches
    "List[int] | str",
    "Tuple[int, str] | None",
    "Dict[str, List[int]]",
    "Callable[[int], str]",
    "int or str | bytes",
    "a or b or c",
    "[int or str]",
    "int[str] or None",
    "a...b | c",
    "...|...",
    "a...", "...a", "..", "....", "...",
    "( )", ",,,", " or ", "[]", "(),", "a,b,c",
    # bars in the shapes the bar-only predicate throws out
    "|", " | ", "|int", "int|", "a||b", "a | | b", "|||",
    # whitespace-only and empty
    "", " ", "\t", "   ", "\xa0",
    # the documented display rewrite: '.'-  and '~'-prefixed cross-references
    ".foo", "~mod.Class", ".mod.Class | ~other.Thing", "~a", ".",
    "int | .foo", "int | ~mod.Cls", "~List[int]", ".a, .b",
    # mixed separator vocabulary in one input
    "Dict[str, int] | List[str] or None",
    "a[b]|c,d...e or f",
]

_NAMES = ["int", "str", "bytes", "None", "List", "Dict", "X", "Foo_1", "T2",
          "SomeClass", "mod.Class", "a", "or", "ore", "colored"]
_PADS = ["", " ", "  ", "   "]

# The full delimiter alphabet PLUS the non-ASCII whitespace the real `\s`
# matches. The model's space test is `c == 32` only, so these code points are
# exactly where the model and the real tokeniser can part company; excluding
# them would make this check unable to fail.
_UNICODE_WS = ["\t", "\n", "\x0b", "\x0c", "\r", "\x1c", "\x85", "\xa0",
               " ", " ", " ", "　"]
_FUZZ_ALPHABET = (list("abcdeFGHIJ_0129")
                  + [" ", " ", " ", "|", "|", ".", "o", "r"]
                  + ["[", "]", "(", ")", ","]
                  + _UNICODE_WS)


def structured_specs(rng, n):
    """Realistic union specs: 1..5 names joined by padded bars. The shape the
    gold patch targets, so the changed branch is densely exercised."""
    for _ in range(n):
        k = rng.randint(1, 5)
        parts = [rng.choice(_NAMES) for _ in range(k)]
        out = parts[0]
        for idx in range(k - 1):
            out += rng.choice(_PADS) + "|" + rng.choice(_PADS) + parts[idx + 1]
        yield out


# stratum 5's alphabet: strata 1-4's alphabet plus the two prefix characters
# whose display rewrite the bridge pins. Kept separate so strata 1-4 draw exactly
# the sequence they drew before this observable was added.
_FULL_ALPHABET = _FUZZ_ALPHABET + ["~", ".", "~", "."]


def full_fuzz_specs(rng, n):
    """Stratum 5: random strings over the full alphabet with NO filter. Neither
    obligation has a precondition, so every draw is counted; discarding any would
    be re-introducing a domain the spec does not have."""
    for _ in range(n):
        k = rng.randint(0, MAX_LEN)
        yield "".join(rng.choice(_FULL_ALPHABET) for _ in range(k))


def fuzz_specs(rng, n_indomain, budget):
    """Random strings over the full delimiter + unicode-whitespace alphabet.
    Yields only inputs the model's `well_formed` accepts, so this stratum is
    dense in the bar-only shape; `budget` bounds the draws so an unexpectedly
    thin predicate cannot spin forever. Stratum 5 draws the same alphabet with no
    filter at all."""
    produced = 0
    drawn = 0
    while produced < n_indomain and drawn < budget:
        drawn += 1
        k = rng.randint(0, MAX_LEN)
        t = "".join(rng.choice(_FUZZ_ALPHABET) for _ in range(k))
        if well_formed(ToSeq(to_codepoints(t)), 0):
            produced += 1
            yield t
    if produced < n_indomain:
        # never silently under-cover: say so on stdout.
        print("NOTE: fuzz stratum produced only %d/%d bar-only-shape inputs in "
              "%d draws" % (produced, n_indomain, drawn))


def main():
    # --- import and CALL the real patched repo function ----------------------
    import inspect
    from docutils import nodes as du_nodes
    from sphinx import addnodes
    from sphinx.domains.python import PyField, PyXrefMixin

    # guard: a failed patch-apply, or a PyField that does not inherit the
    # modeled method, must never read as a green run.
    assert PyField.make_xrefs is PyXrefMixin.make_xrefs, (
        "PyField.make_xrefs is not PyXrefMixin.make_xrefs; oracle would not be "
        "the modeled symbol")
    src = inspect.getsource(PyXrefMixin.make_xrefs)
    assert r"\s*\|\s*" in src, (
        "patched delimiter alternative not present in make_xrefs source; the "
        "gold patch did not apply, so this run would test the WRONG code:\n"
        + src)

    field = PyField("type", names=("type",), rolename="class")
    env = _StubEnv()
    Recorder = _make_recorder(du_nodes)

    def oracle(target):
        """CALL the real patched make_xrefs. Returns (node kinds, encoded node
        stream). The stream's per-node text is read off the real code's own
        `innernode` calls; nothing about the tokenisation is re-derived here."""
        rec = Recorder()
        nodes_out = field.make_xrefs("class", "py", target, innernode=rec,
                                    env=env)
        # measured, not assumed: one factory call per produced node, in order.
        assert len(rec.texts) == len(nodes_out), (
            "innernode was called %d times for %d nodes on %r; the recorder "
            "would not be reading node texts" % (len(rec.texts),
                                                 len(nodes_out), target))
        ks = real_node_kinds(nodes_out, addnodes.pending_xref)
        # independent bridge: what each node ends up DISPLAYING must equal the
        # recorded piece, except for the one documented rewrite the make_xref
        # callee performs on a '.'- or '~'-prefixed cross-reference target
        # (sphinx/domains/python.py:293-301). Stated exactly, so a recorder that
        # saw a different string than the node was built from cannot pass.
        for idx in range(len(nodes_out)):
            nd, piece, is_xref = nodes_out[idx], rec.texts[idx], ks[idx]
            want = piece
            if is_xref and piece[:1] == ".":
                want = piece[1:]
            elif is_xref and piece[:1] == "~":
                want = piece.split(".")[-1]
            assert nd.astext() == want, (
                "node %d displays %r but was built from %r on input %r"
                % (idx, nd.astext(), piece, target))
        return ks, encode_stream(list(zip(rec.texts, ks)))

    # --- the non-bar-shape boundary list must be REJECTED by `well_formed`, the
    # bar-only predicate (and is still fully checked by BOTH obligations) ------
    for t in BOUNDARY_OUT:
        assert not well_formed(ToSeq(to_codepoints(t)), 0), (
            "input %r was expected to fall outside the bar-only shape but "
            "well_formed admitted it; that predicate is not discriminating"
            % (t,))

    stream_bad = []
    kind_bad = []
    checked_stream = 0
    checked_kinds = 0
    n_well_formed = 0          # how many inputs the bar-only predicate admits
    branch_break_first = 0     # split_render: `j >= n` with `i < n` (tail xref)
    branch_break_empty = 0     # split_render: `j >= n` with `i == n` (no tail)
    branch_separator = 0       # split_render: `j > i` (text, then separator)
    branch_bare_sep = 0        # split_render: `j == i` (separator, no text)
    br_sep = 0                 # render_nodes: at least one separator node
    br_tail_text = 0           # render_nodes: `j >= n` with `i < n` (tail xref)
    br_tail_empty = 0          # render_nodes: `j >= n` with `i == n` (no tail)
    br_empty_piece = 0         # render_nodes: `j == i` (separator, no text node)

    def check_one(target):
        nonlocal checked_stream, checked_kinds, n_well_formed
        nonlocal branch_break_first, branch_break_empty
        nonlocal branch_separator, branch_bare_sep
        nonlocal br_sep, br_tail_text, br_tail_empty, br_empty_piece
        cps = to_codepoints(target)
        s = ToSeq(cps)
        real_kinds, real_stream = oracle(target)

        # --- PRIMARY: the whole node stream. NO domain restriction, because
        # `render_nodes` has no precondition beyond access to its argument. ----
        checked_stream += 1
        shadow_stream = render_nodes(cps)
        # self-consistency: the verbatim impl must realize its own postcondition
        # spec `rendered`; trips if the shadow was mis-copied.
        assert ToSeq(shadow_stream) == rendered(s, 0), (
            "shadow %r != rendered %r on %r — the copied impl region does not "
            "match the model's own pure spec"
            % (shadow_stream, rendered(s, 0), target))
        if -2 in shadow_stream:
            br_sep += 1
        if shadow_stream[-2:] == [-2, -3] or shadow_stream == [-3]:
            br_tail_empty += 1
        else:
            br_tail_text += 1
        model_nodes = decode_stream(shadow_stream)
        for k in range(len(model_nodes)):
            # a separator node with no cross-reference node in front of it is
            # exactly render_nodes' `j == i` branch (nothing to emit for [i, j)).
            if (model_nodes[k][1] == "sep"
                    and (k == 0 or model_nodes[k - 1][1] == "sep")):
                br_empty_piece += 1
                break
        if shadow_stream != real_stream and len(stream_bad) < MAX_REPORT:
            stream_bad.append((target, shadow_stream, real_stream))

        # --- the kind-only view: node KINDS, on EVERY input -------------------
        # `split_render` carries no domain clause either, so no filter is
        # applied here: a kind sequence is claimed for every specification,
        # including the ones carrying a bracket, comma, `or` or an ellipsis.
        checked_kinds += 1
        if well_formed(s, 0):
            n_well_formed += 1
        shadow = split_render(cps)
        # self-consistency: the verbatim impl must realize its own postcondition
        # spec `marks`; trips if the shadow was mis-copied.
        assert ToSeq(shadow) == marks(s, 0), (
            "shadow %r != marks %r on %r — the copied impl region does not "
            "match the model's own pure spec" % (shadow, marks(s, 0), target))
        # the kind sequence is the kind projection of the node stream, so the
        # two shadows must agree with each other as well.
        assert shadow == [v == -1 for v in shadow_stream
                          if v == -1 or v == -2], (
            "kind shadow %r is not the kind projection of stream shadow %r on "
            "%r" % (shadow, shadow_stream, target))
        if len(shadow) == 0:
            branch_break_empty += 1
        elif shadow[-1]:
            branch_break_first += 1
        else:
            branch_break_empty += 1
        for k in range(len(shadow)):
            if not shadow[k]:
                if k == 0 or not shadow[k - 1]:
                    branch_bare_sep += 1
                else:
                    branch_separator += 1
                break
        if shadow != real_kinds and len(kind_bad) < MAX_REPORT:
            kind_bad.append((target, shadow, real_kinds))

        # the two impl regions that the kind-only scan no longer calls
        # (`first_bar_idx` / `slice_trim`, the bar-position and trimmed-segment
        # helpers) are still shipped in model.py, so they are still executed
        # here and still checked against the pure specs their postconditions
        # name. Nothing about the real code is claimed by this pair.
        p = first_bar_idx(cps, 0)
        assert p == first_bar(s, 0), (
            "first_bar_idx shadow %r != first_bar %r on %r"
            % (p, first_bar(s, 0), target))
        assert ToSeq(slice_trim(cps, 0, p)) == seg_text(s, 0, p), (
            "slice_trim shadow %r != seg_text %r on %r"
            % (slice_trim(cps, 0, p), seg_text(s, 0, p), target))

    # strata 1-4 draw exactly the sequence they drew before the node stream was
    # added: same order, same seed, same alphabet.
    for t in BOUNDARY_IN:
        assert well_formed(ToSeq(to_codepoints(t)), 0), (
            "boundary case %r was meant to have the bar-only shape but "
            "well_formed rejects it" % (t,))
        check_one(t)
    n_boundary = checked_stream

    rng = random.Random(SEED)
    for t in structured_specs(rng, N_STRUCTURED):
        check_one(t)
    n_structured = checked_stream - n_boundary

    for t in fuzz_specs(rng, N_FUZZ_INDOMAIN, N_FUZZ_INDOMAIN * 60):
        check_one(t)
    n_fuzz = checked_stream - n_boundary - n_structured

    # stratum 5: the full domain, unfiltered.
    for t in BOUNDARY_OUT + BOUNDARY_FULL:
        check_one(t)
    for t in full_fuzz_specs(rng, N_FUZZ_FULL):
        check_one(t)
    n_full = checked_stream - n_boundary - n_structured - n_fuzz

    # --- verdict -------------------------------------------------------------
    if stream_bad:
        print("G-CONF FAIL: the MODEL disagrees with the real patched "
              "make_xrefs on the modeled node STREAM (count, kind and each "
              "node's piece of the input).")
        print("Oracle: sphinx.domains.python.PyXrefMixin.make_xrefs "
              "(called, patched). Shadow: model.py impl region, verbatim.")
        for t, sh, rl in stream_bad:
            print("  input=%r (codepoints=%r)" % (t, to_codepoints(t)))
            print("      no precondition -> the spec CLAIMS this input")
            print("      shadow/model stream = %r" % (sh,))
            print("      real patched stream = %r" % (rl,))
            print("      model as nodes = %r" % (decode_stream(sh),))
            print("      real  as nodes = %r" % (decode_stream(rl),))
    if kind_bad:
        print("G-CONF FAIL: the MODEL disagrees with the real patched "
              "make_xrefs on the node-KIND sequence.")
        for t, sh, rl in kind_bad:
            print("  input=%r (codepoints=%r)" % (t, to_codepoints(t)))
            print("      no precondition -> the spec CLAIMS this input")
            print("      shadow/model kinds = %r" % (sh,))
            print("      real patched kinds = %r" % (rl,))

    bad = bool(stream_bad or kind_bad)
    status = "fail" if bad else "pass"
    if not bad:
        print("G-CONF OK: verbatim shadow of model.py's impl regions agrees "
              "with the real patched PyXrefMixin.make_xrefs on ALL %d inputs. "
              "Node STREAM (count + kind + each node's piece of the input, the "
              "whole modeled output of render_nodes) and node KIND sequence "
              "(the whole modeled output of split_render) both checked on all "
              "%d with NO domain restriction (%d boundary + %d structured + %d "
              "bar-only fuzz + %d full-domain, seed=%d); %d of those inputs lie "
              "outside the bar-only `well_formed` shape, i.e. carry a bracket, "
              "comma, `or` or ellipsis separator, and both obligations are "
              "measured there too. render_nodes branches all taken (%d with a "
              "separator, %d ending in text, %d ending at a separator, %d with "
              "an empty leading/adjacent piece); split_render branches all "
              "taken (%d ending in a cross-reference, %d ending at a separator "
              "or empty, %d emitting text before a separator, %d emitting a "
              "separator with no text in front of it); 0 disagreements."
              % (checked_stream, checked_stream,
                 n_boundary, n_structured, n_fuzz, n_full, SEED,
                 checked_kinds - n_well_formed,
                 br_sep, br_tail_text, br_tail_empty, br_empty_piece,
                 branch_break_first, branch_break_empty,
                 branch_separator, branch_bare_sep))
    print(json.dumps({
        "gate": "G-CONF",
        "instance": "sphinx-doc__sphinx-9258",
        "backend": "nagini",
        "status": status,
        "shadow": "direct (model.py impl regions, contracts stripped, verbatim)",
        "oracle": "called: sphinx.domains.python.PyXrefMixin.make_xrefs "
                  "(patched, via PyField); per-node text read off the real "
                  "code's own innernode calls",
        "checked": checked_stream,
        "checked_stream_full_domain": checked_stream,
        "checked_kinds_full_domain": checked_kinds,
        "checked_outside_well_formed": checked_kinds - n_well_formed,
        "checked_well_formed_shape": n_well_formed,
        "boundary": n_boundary,
        "structured": n_structured,
        "fuzz": n_fuzz,
        "full_domain": n_full,
        "out_of_domain_rejected": len(BOUNDARY_OUT),
        "branch_tail_xref": branch_break_first,
        "branch_tail_empty": branch_break_empty,
        "branch_separator": branch_separator,
        "branch_bare_separator": branch_bare_sep,
        "branch_stream_separator": br_sep,
        "branch_stream_tail_text": br_tail_text,
        "branch_stream_tail_empty": br_tail_empty,
        "branch_stream_empty_piece": br_empty_piece,
        "seed": SEED,
        "stream_disagreements_sampled": len(stream_bad),
        "stream_disagreements": [
            {"input": t, "model": decode_stream(sh), "real": decode_stream(rl)}
            for t, sh, rl in stream_bad],
        "kind_disagreements_sampled": len(kind_bad),
        "kind_disagreements": [
            {"input": t, "model": sh, "real": rl} for t, sh, rl in kind_bad],
    }))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
