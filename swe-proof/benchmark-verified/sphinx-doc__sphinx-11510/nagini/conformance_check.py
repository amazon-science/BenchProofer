#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-11510 (nagini).

Refutes (never proves) the refinement leg: does model.py's impl region actually
agree with the REAL patched repository function it claims to model?

SHADOW
------
The impl region of `model.py` (`forward_with_source_read`, between
`# impl-start` / `# impl-end`) copied VERBATIM below, with only the contract
calls removed (`Requires`/`Ensures`/`Assert`).  Nothing is renamed,
restructured or "simplified".  Its dependencies come over the same way:

  * `transformed` — the `@Pure` helper of the pure region, verbatim, over a
    `PSeq` shim (immutable sequence: `take`/`drop`/`+`/`len`/`[]`/`==`,
    materialized by `ToSeq`).
  * `emit_and_collect` — a `@ContractOnly` axiom, so it has no body to copy.
    Per mapping.md section 3.1 its repository counterpart is the REAL
    `sphinx.events.EventManager.emit('source-read', docname, arg)` wrapped by
    the line<->text round trip that surrounds it in the patch closure.  The
    realization below therefore CALLS that real dispatcher (a real
    `EventManager` with real registered `source-read` listeners) rather than
    modelling it, so the axiom is exercised instead of assumed.  `hook` is the
    same composite lifted to line granularity — the model leaves it
    uninterpreted, and this check consequently pins WHICH region is offered to
    it, never what it computes (that is the specification's own scoping).

ORACLE CHOICE — the real patched function is CALLED, not transliterated
-----------------------------------------------------------------------
mapping.md section 1 binds `forward_with_source_read` to the `_insert_input`
closure the gold patch installs inside `Include.run`
(`sphinx/directives/other.py`, patch hunk `@@ -369,6 +371,40 @@`).  A closure is
not importable, so the sibling velvet/lean checks transliterate the patched
source.  This check does NOT: it constructs a real
`sphinx.directives.other.Include` instance, lets the REAL patched `Include.run`
execute far enough to install the closure on the state machine
(`self.state_machine.insert_input = _insert_input`), lifts the installed
closure back off the instance, and calls it.  Everything downstream of it is
also real: the closure computes its docname through the real
`sphinx.util.osutil.os_path` + `sphinx.project.Project.path2doc`, emits through
the real `EventManager`, and forwards through the real
`docutils.statemachine.StateMachine.insert_input`, from which the forwarded
line sequence is read back out of the state machine's `input_lines`.  So the
oracle is the patched repository code itself; if the patch's slice offsets,
concatenation order or marker handling were anything other than what model.py
claims, this check fails.

The construction is guarded, not trusted: `_assert_oracle_is_patched_closure`
hard-fails (exit 1) unless the lifted attribute really is
`Include.run.<locals>._insert_input`, unless the patched source markers are
present in `Include.run`, and unless the listener gate behaves as the patch
specifies (no `source-read` listener => no closure installed).  A green verdict
therefore cannot come from having quietly tested nothing.

NEGATIVE CONTROLS
-----------------
`_negative_controls` runs five mutants of the shadow (body/marker split at
`-1` and `-3`, markers concatenated before the body, markers dropped, whole
sequence offered to the hook) and REQUIRES each to be refuted by the boundary
inputs.  If any mutant agrees with the real closure everywhere, the check is
vacuous and exits 1.  This is the evidence that the check is capable of failing.

TYPE BRIDGE (mapping.md section 2, inverted)
--------------------------------------------
The model carrier is `List[int]` of opaque per-line identities; the real
closure wants `list[str]` of gathered lines.  The bridge is a dynamic
bijection: `_intern(s) -> int` / `_unintern(i) -> str`, memoized both ways, so
every line string that occurs (generated input lines and any novel line a
listener emits) has exactly one int identity and distinct contents get
distinct ints.  Generation happens on the `str` side (the real function's
side), lowering to ints for the shadow, then the real closure's forwarded
`list[str]` is lifted to `List[int]` and the two are compared as int
sequences; injectivity makes that equivalent to comparing strings, but the
bridge is exercised explicitly in both directions.  Generated line strings
contain NO `str.splitlines()` line-boundary character, which is exactly the
modelled regime mapping.md section 2 states ("each entry of `include_lines`
is one line"); listener OUTPUT is deliberately unrestricted and does inject
every boundary character, since `hook` is arbitrary.

INPUT DOMAIN — Requires-satisfying only
---------------------------------------
`Requires(Acc(list_pred(lines), 1/2))` and `Requires(len(lines) >= 2)`.  Every
generated input has `len(lines) >= 2` (the two framing markers are always
present, which is the modelled regime) and the input list is never aliased or
mutated.  The domain is NOT widened to `len(lines) < 2`: the model's
`transformed` treats a short sequence as all-body purely to stay total, the
impl's precondition excludes it, and the real closure's `[:-2]`/`[-2:]` would
disagree there — testing it would be testing outside the specification rather
than refuting it.  That exclusion is recorded here rather than left implicit.

The impl region is straight-line (no branches), so branch coverage is total by
construction; the `len < 2` arm of the pure helper `transformed` is the one
arm the Requires makes unreachable, as noted above.  The input space is
infinite (arbitrary line strings), so boundary cases are enumerated
exhaustively first — empty body, single body line, both F2P gathered shapes,
the issue's `&REPLACE_ME;` case, all-empty bodies, bodies whose content
repeats the marker text, multiple listeners in priority order — and seeded
fuzz then fills the count.

Exit 0 iff zero disagreements.  On a disagreement the input and both outputs
are printed and the exit code is 1.  stdlib + the real Sphinx/docutils callees
only.  Pinned seed: 11510 (recorded in mapping.md section G-CONF).
"""
import json
import random
import sys

from docutils.statemachine import StateMachine, StringList
from sphinx.directives.other import Include
from sphinx.events import EventManager
from sphinx.project import Project
from sphinx.util.osutil import os_path

SEED = 11510
N_FUZZ = 100_000
# how often the pure helper `transformed` is cross-checked too (it costs a
# third real event dispatch per input); reported in the summary, not silent.
TRANSFORMED_EVERY = 5


# --------------------------------------------------------------------------
# Nagini carrier shim: PSeq is an immutable sequence; ToSeq materializes one.
# --------------------------------------------------------------------------
class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
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

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq(%r)" % (list(self._t),)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --------------------------------------------------------------------------
# Type bridge (mapping.md section 2, inverted): opaque int line identity <-> str
# line content.  A dynamic bijection, so it is total on whatever line contents
# occur, including novel lines a listener emits.
# --------------------------------------------------------------------------
_S2I = {}
_I2S = []


def _intern(s):
    i = _S2I.get(s)
    if i is None:
        i = len(_I2S)
        _S2I[s] = i
        _I2S.append(s)
    return i


def _unintern(i):
    return _I2S[i]


def lower(lines_int):
    """List[int] (model carrier) -> list[str] (repo reality)."""
    return [_unintern(i) for i in lines_int]


def lift(lines_str):
    """list[str] (repo reality) -> List[int] (model carrier)."""
    return [_intern(s) for s in lines_str]


# --------------------------------------------------------------------------
# The live @ContractOnly axiom realization.  `emit_and_collect` has no body in
# model.py; mapping.md section 3.1 binds it to the REAL
# EventManager.emit('source-read', ...) together with the line<->text round trip
# the patch closure wraps around it.  We call the real dispatcher.
# --------------------------------------------------------------------------
class _FakeApp(object):
    """The minimum the REAL EventManager touches (`app.pdb`, passed to
    handlers as the first positional argument)."""
    pdb = False

    def __init__(self):
        self.events = EventManager(self)


APP = _FakeApp()
# The transform the registered listener currently applies.  Swapped per input;
# the dispatch itself is always the real EventManager.
CURRENT = {"fns": [lambda t: t], "docnames": []}


def _listener_a(app, docname, source):
    CURRENT["docnames"].append(docname)
    source[0] = CURRENT["fns"][0](source[0])


def _listener_b(app, docname, source):
    fns = CURRENT["fns"]
    if len(fns) > 1:
        source[0] = fns[1](source[0])


APP.events.connect("source-read", _listener_a, priority=500)
APP.events.connect("source-read", _listener_b, priority=800)

DOCNAME_HOLDER = {"docname": "index"}
EVENT_TEXTS = []


def emit_and_collect(body):
    """Realization of the `@ContractOnly` axiom of model.py's axioms region.

    mapping.md section 3.1: `text = "\\n".join(body)` / `emit('source-read',
    docname, arg)` / `text = arg[0]` / `text.splitlines()`.  The `emit` is the
    REAL `sphinx.events.EventManager.emit`; the join/splitlines pair is the
    axiom's documented abstraction boundary (the line<->text round trip), which
    is what lifts the dispatcher's text-level effect to the line granularity
    the model works at.  Takes and returns the model carrier.
    """
    text = "\n".join(lower(body))
    EVENT_TEXTS.append(text)
    arg = [text]
    APP.events.emit("source-read", DOCNAME_HOLDER["docname"], arg)
    text = arg[0]
    return lift(text.splitlines())


def hook(body):
    """`hook` over the PSeq carrier: the same composite, lifted.  Uninterpreted
    in model.py, so the specification (and hence this check) pins only which
    region is offered to it."""
    return ToSeq(emit_and_collect(list(body._t)))


# --------------------------------------------------------------------------
# pure region of model.py, verbatim (no contracts to strip in this one).
# --------------------------------------------------------------------------
def transformed(lines):
    if len(lines) < 2:
        return hook(lines)
    return hook(lines.take(len(lines) - 2)) + lines.drop(len(lines) - 2)


# --------------------------------------------------------------------------
# SHADOW: the impl region of model.py, VERBATIM, contract calls stripped
# (the four `Assert(...)` lines removed; nothing else touched).
# --------------------------------------------------------------------------
def forward_with_source_read(lines):
    # impl-start
    n = len(lines)
    # Split off the authored body (all but the final two framing markers) and
    # the two framing markers, mirroring `lines[:-2]` / `lines[-2:]`.
    body = lines[:n - 2]
    markers = lines[n - 2:]
    # Offer the body to the content-transformation hook (emit the event); its
    # (possibly rewritten) result replaces the body region.
    new_body = emit_and_collect(body)
    # Re-attach the framing markers, in their original positions, after the
    # transformed body, and forward the result.
    result = new_body + markers
    return result
    # impl-end


# --------------------------------------------------------------------------
# ORACLE: the REAL patched `_insert_input` closure, lifted off a real Include
# instance and called.  Not a transliteration.
# --------------------------------------------------------------------------
class _Installed(Exception):
    """Raised by the fake env once the patched `Include.run` has installed the
    closure, to stop `run()` before it needs a real docutils document."""


class _Holder(object):
    pass


class _SpyStringList(StringList):
    """The state machine's `input_lines`.  `StateMachine.insert_input` (real
    docutils) inserts two padding strings and then the forwarded
    `StringList(include_lines, source)`; we record the latter, which IS the
    line sequence the patch forwards to the parser."""

    def __init__(self, *a, **k):
        StringList.__init__(self, *a, **k)
        self.forwarded = []

    def insert(self, i, item, source=None, offset=0):
        if source is None and isinstance(item, StringList):
            self.forwarded.append(list(item.data))
        return StringList.insert(self, i, item, source=source, offset=offset)


class _Env(object):
    """Stands in for the BuildEnvironment the closure reads: `env.app.events`
    (a real EventManager) and `env.path2doc` (the real Project.path2doc).
    `relfn2path` raises once the closure is installed."""

    def __init__(self, app, project):
        self.app = app
        self._project = project

    def path2doc(self, filename):
        return self._project.path2doc(filename)

    def relfn2path(self, name):
        raise _Installed()

    def note_included(self, filename):
        raise _Installed()


PROJECT = Project("/testbed/tests/roots/test-directive-include",
                  {".rst": "restructuredtext"})
ENV = _Env(APP, PROJECT)


def _build_include():
    """Run the REAL patched `Include.run` far enough to install the closure,
    then hand back the instance and its state machine."""
    inc = Include.__new__(Include)
    sm = StateMachine([], initial_state="Body")
    sm.input_lines = _SpyStringList([], source="<index>")
    sm.line_offset = 0
    doc = _Holder()
    settings = _Holder()
    settings.env = ENV
    doc.settings = settings
    state = _Holder()
    state.document = doc
    inc.state = state
    inc.state_machine = sm
    inc.arguments = ["foo.rst"]
    try:
        inc.run()
    except _Installed:
        pass
    return inc, sm


INCLUDE, SM = _build_include()
ORACLE_CLOSURE = SM.insert_input


def oracle(lines_str, path):
    """Call the REAL patched closure and read back the forwarded lines."""
    SM.input_lines = _SpyStringList([], source="<index>")
    SM.line_offset = 0
    passed = list(lines_str)
    ORACLE_CLOSURE(passed, path)
    fwd = SM.input_lines.forwarded
    if len(fwd) != 1:
        raise AssertionError("real closure forwarded %d sequences, expected 1"
                             % len(fwd))
    return fwd[0], passed


# --------------------------------------------------------------------------
# Guards: the oracle really is the patched closure, and the patch's listener
# gate really behaves as claimed.  A failure here exits 1; it never degrades
# into a quiet pass.
# --------------------------------------------------------------------------
def _assert_oracle_is_patched_closure():
    import inspect

    qn = getattr(ORACLE_CLOSURE, "__qualname__", "")
    if "_insert_input" not in qn:
        raise AssertionError(
            "oracle is not the patched closure: state_machine.insert_input is "
            "%r (qualname %r) -- is the gold patch applied?"
            % (ORACLE_CLOSURE, qn))
    src = inspect.getsource(Include.run)
    for needle in ('def _insert_input(include_lines, path)',
                   'include_lines[:-2]',
                   'include_lines[-2:]',
                   '"source-read"'):
        if needle not in src:
            raise AssertionError(
                "patched Include.run source lacks %r -- wrong oracle" % needle)
    # the patch installs the closure ONLY when a source-read listener exists.
    saved = APP.events.listeners.get("source-read")
    APP.events.listeners["source-read"] = []
    try:
        inc2, sm2 = _build_include()
        if getattr(sm2.insert_input, "__qualname__", "") != \
                getattr(StateMachine.insert_input, "__qualname__", "?"):
            if "_insert_input" in getattr(sm2.insert_input, "__qualname__", ""):
                raise AssertionError(
                    "patch installed the closure with no source-read listener")
    finally:
        APP.events.listeners["source-read"] = saved
    # the real docname routing the closure uses is genuinely exercised.
    if ENV.path2doc(os_path("baz/baz.rst")) != "baz/baz":
        raise AssertionError("real os_path/path2doc routing unexpected: %r"
                             % ENV.path2doc(os_path("baz/baz.rst")))


# --------------------------------------------------------------------------
# Mutants of the shadow, used as negative controls.
# --------------------------------------------------------------------------
def _mutant_off1(lines):
    n = len(lines)
    return emit_and_collect(lines[:n - 1]) + lines[n - 1:]


def _mutant_off3(lines):
    n = len(lines)
    k = max(0, n - 3)
    return emit_and_collect(lines[:k]) + lines[k:]


def _mutant_swapped(lines):
    n = len(lines)
    return lines[n - 2:] + emit_and_collect(lines[:n - 2])


def _mutant_no_markers(lines):
    n = len(lines)
    return emit_and_collect(lines[:n - 2])


def _mutant_whole_body(lines):
    n = len(lines)
    return emit_and_collect(lines) + lines[n - 2:]


MUTANTS = [("body_split_at_-1", _mutant_off1),
           ("body_split_at_-3", _mutant_off3),
           ("markers_before_body", _mutant_swapped),
           ("markers_dropped", _mutant_no_markers),
           ("whole_sequence_offered", _mutant_whole_body)]


# --------------------------------------------------------------------------
# Listener families.  The hook is arbitrary, so listener OUTPUT ranges over the
# full str.splitlines() boundary alphabet even though input lines never do.
# --------------------------------------------------------------------------
def _t_identity(t):
    return t


def _t_magical(t):
    return t.replace("#magical", "amazing")


def _t_replace_me(t):
    return t.replace("&REPLACE_ME;", "REPLACED")


def _t_upper(t):
    return t.upper()


def _t_prefix(t):
    return "PRE:" + t


def _t_suffix(t):
    return t + ":POST"


def _t_empty(t):
    return ""


def _t_double(t):
    return t + t


def _t_strip_hash(t):
    return t.replace("#", "")


def _t_nl_to_cr(t):
    return t.replace("\n", "\r")


def _t_nl_to_crlf(t):
    return t.replace("\n", "\r\n")


def _t_trailing_nl(t):
    return t + "\n"


def _t_trailing_cr(t):
    return t + "\r"


def _t_trailing_crlf(t):
    return t + "\r\n"


def _t_leading_nl(t):
    return "\n" + t


def _t_exotic(t):
    return "\x0b" + t + "\x0c tail\x1cA\x1dB\x1eC\x85D E "


def _t_lone_cr(t):
    return "\r"


def _t_blank_lines(t):
    return t.replace("\n", "\n\n")


TRANSFORMS = [
    ("identity", _t_identity),
    ("magical", _t_magical),          # F2P nested-includes listener
    ("replace_me", _t_replace_me),    # the issue's own substitution
    ("upper", _t_upper),
    ("prefix", _t_prefix),
    ("suffix", _t_suffix),
    ("const_empty", _t_empty),
    ("double", _t_double),
    ("strip_hash", _t_strip_hash),
    ("nl_to_cr", _t_nl_to_cr),
    ("nl_to_crlf", _t_nl_to_crlf),
    ("trailing_nl", _t_trailing_nl),
    ("trailing_cr", _t_trailing_cr),
    ("trailing_crlf", _t_trailing_crlf),
    ("leading_nl", _t_leading_nl),
    ("exotic_boundaries", _t_exotic),
    ("lone_cr", _t_lone_cr),
    ("blank_lines", _t_blank_lines),
]

PATHS = ["foo.rst", "baz/baz.rst", "/testbed/tests/roots/test-directive-include/foo.rst",
         "text.txt", "a/b/c.rst"]

MARKER = '.. end of inclusion from "foo.rst"'

# Boundary inputs.  Every one has len >= 2 (the Requires); no generated line
# contains a str.splitlines() boundary character (the modelled regime).
BOUNDARY_LINES = [
    ["", MARKER],                                    # empty authored body
    ["one body line", "", MARKER],                   # singleton body
    # F2P test_include_source_read_event_nested_includes (foo.rst gathered)
    ["The #magical foo.", "", MARKER],
    # F2P test_include_source_read_event (baz/baz.rst, :start-line: 4)
    ["", "Baz was here.", "", '.. end of inclusion from "baz/baz.rst"'],
    ["Baz", "===", "", ".. include:: foo.rst", "", "Baz was here.", "", MARKER],
    ["x&REPLACE_ME;y", "z", "", MARKER],             # the issue's case
    ["", "", "", MARKER],                            # all-empty body
    ["", ""],                                        # both lines are markers
    ["a", "b"],                                      # body empty, 2 markers
    ["body", MARKER, MARKER],                        # marker text as content
    ["#magical", "#magical", "", MARKER],
    ["   indented", "\ttabbed", "", MARKER],
    ["line with spaces", "", "", "", MARKER],        # trailing blank body lines
    ["This is plain text.", "", MARKER],
]


def _fuzz_lines(rng):
    """Random gathered-line sequences.  len >= 2 always (the Requires); tokens
    are break-free single lines (the modelled regime)."""
    toks = ["The #magical foo.", "", "Baz was here.", "Baz", "===", "---",
            "&REPLACE_ME;", "x&REPLACE_ME;y", "#magical", ".. include:: foo.rst",
            "abc", "a b c", "   indented", "\ttabbed", "1", "2",
            "This is plain text.", "&amp;", "section", MARKER, "   ", "z"]
    nbody = rng.randint(0, 8)
    body = [rng.choice(toks) for _ in range(nbody)]
    return body + [rng.choice(["", "   ", "x"]),
                   '.. end of inclusion from "%s"' % rng.choice(PATHS)]


def _check(lines_str, path, tname, fns, do_transformed):
    """One differential observation.  Returns None on agreement, else a report."""
    CURRENT["fns"] = fns
    CURRENT["docnames"] = []
    DOCNAME_HOLDER["docname"] = ENV.path2doc(os_path(path))
    del EVENT_TEXTS[:]

    # --- oracle: the REAL patched closure ---------------------------------
    got_str, passed = oracle(lines_str, path)
    oracle_ints = lift(got_str)
    oracle_event_docnames = list(CURRENT["docnames"])

    # frame claim: the model reads `lines` at a fractional permission and never
    # mutates it, so the real closure must not mutate the list it is handed.
    if passed != list(lines_str):
        return ("real closure mutated its input list", lines_str, passed, None)

    # --- shadow: the impl region, verbatim --------------------------------
    CURRENT["docnames"] = []
    del EVENT_TEXTS[:]
    lines_int = lift(lines_str)
    lines_int_before = list(lines_int)
    shadow_ints = forward_with_source_read(lines_int)
    if lines_int != lines_int_before:
        return ("shadow mutated its input list", lines_str, lines_int, None)

    if shadow_ints != oracle_ints:
        return ("shadow != real patched closure", lines_str,
                lower(shadow_ints), got_str)

    # the axiom's "body is offered" content, against the real dispatch: the
    # event text is exactly the join of the authored body, markers excluded.
    if EVENT_TEXTS != ["\n".join(lines_str[:-2])]:
        return ("event text != join(body)", lines_str, EVENT_TEXTS,
                ["\n".join(lines_str[:-2])])
    if oracle_event_docnames != [DOCNAME_HOLDER["docname"]]:
        return ("real closure emitted docnames %r" % (oracle_event_docnames,),
                lines_str, oracle_event_docnames, [DOCNAME_HOLDER["docname"]])

    # the model's own postconditions, evaluated against the REAL output.
    if len(oracle_ints) < 2:
        return ("Ensures len(Result()) >= 2 violated", lines_str, got_str, None)
    if got_str[-2:] != list(lines_str[-2:]):
        return ("framing markers not preserved verbatim", lines_str,
                got_str[-2:], list(lines_str[-2:]))

    # the pure helper `transformed`, over the PSeq carrier.
    if do_transformed:
        CURRENT["docnames"] = []
        del EVENT_TEXTS[:]
        want = transformed(ToSeq(lift(lines_str)))
        if want != ToSeq(oracle_ints):
            return ("transformed() != real patched closure", lines_str,
                    lower(list(want._t)), got_str)
    return None


def _negative_controls():
    """Every mutant of the shadow must be refuted by the boundary inputs; a
    mutant that survives means this check is vacuous."""
    survivors = []
    for mname, mfn in MUTANTS:
        killed = False
        for lines_str in BOUNDARY_LINES:
            for tname, tfn in TRANSFORMS[:6]:
                CURRENT["fns"] = [tfn]
                CURRENT["docnames"] = []
                DOCNAME_HOLDER["docname"] = "index"
                del EVENT_TEXTS[:]
                got_str, _ = oracle(lines_str, "foo.rst")
                del EVENT_TEXTS[:]
                try:
                    mut = mfn(lift(lines_str))
                except Exception:
                    killed = True
                    break
                if mut != lift(got_str):
                    killed = True
                    break
            if killed:
                break
        if not killed:
            survivors.append(mname)
    return survivors


def _report(status, checked, extra=None):
    obj = {"status": status, "checked": checked, "seed": SEED,
           "oracle": "sphinx/directives/other.py Include.run.<locals>."
                     "_insert_input (real patched closure, called)",
           "shadow": "model.py impl region verbatim (direct)",
           "unsupported": []}
    if extra:
        obj.update(extra)
    return json.dumps(obj, sort_keys=True)


def main():
    try:
        _assert_oracle_is_patched_closure()
    except AssertionError as e:
        print("G-CONF FAIL (oracle guard): %s" % e)
        print(_report("fail", 0, {"reason": "oracle guard: %s" % e}))
        return 1

    survivors = _negative_controls()
    if survivors:
        print("G-CONF FAIL: shadow mutants survived the boundary inputs, so "
              "this check is vacuous: %r" % (survivors,))
        print(_report("fail", 0, {"reason": "vacuous: mutants survived",
                                 "surviving_mutants": survivors}))
        return 1

    checked = 0
    n_transformed = 0

    # --- boundary inputs, exhaustively over the listener families ---------
    for lines_str in BOUNDARY_LINES:
        for tname, tfn in TRANSFORMS:
            for path in PATHS:
                checked += 1
                n_transformed += 1
                bad = _check(lines_str, path, tname, [tfn], True)
                if bad is None:
                    continue
                why, inp, a, b = bad
                print("G-CONF FAIL (boundary): %s" % why)
                print("  lines=%r transform=%s path=%r" % (inp, tname, path))
                print("  shadow=%r" % (a,))
                print("  oracle=%r" % (b,))
                print(_report("fail", checked, {"reason": why}))
                return 1
    # two listeners at once: the real EventManager dispatches in priority order.
    for lines_str in BOUNDARY_LINES:
        for tname, tfn in TRANSFORMS:
            checked += 1
            n_transformed += 1
            bad = _check(lines_str, "baz/baz.rst", tname + "+upper",
                         [tfn, _t_upper], True)
            if bad is not None:
                why, inp, a, b = bad
                print("G-CONF FAIL (two listeners): %s" % why)
                print("  lines=%r transform=%s" % (inp, tname))
                print("  shadow=%r\n  oracle=%r" % (a, b))
                print(_report("fail", checked, {"reason": why}))
                return 1

    n_boundary = checked

    # --- seeded fuzz ------------------------------------------------------
    rng = random.Random(SEED)
    for k in range(N_FUZZ):
        lines_str = _fuzz_lines(rng)
        tname, tfn = TRANSFORMS[rng.randrange(len(TRANSFORMS))]
        fns = [tfn]
        if rng.random() < 0.25:
            fns = [tfn, TRANSFORMS[rng.randrange(len(TRANSFORMS))][1]]
        path = PATHS[rng.randrange(len(PATHS))]
        do_t = (k % TRANSFORMED_EVERY == 0)
        checked += 1
        if do_t:
            n_transformed += 1
        bad = _check(lines_str, path, tname, fns, do_t)
        if bad is not None:
            why, inp, a, b = bad
            print("G-CONF FAIL (fuzz): %s" % why)
            print("  lines=%r transform=%s path=%r" % (inp, tname, path))
            print("  shadow=%r" % (a,))
            print("  oracle=%r" % (b,))
            print(_report("fail", checked, {"reason": why}))
            return 1

    print("G-CONF OK: model.py impl region (verbatim shadow, @ContractOnly "
          "emit_and_collect realized by the REAL EventManager.emit) agrees with "
          "the REAL patched Include.run._insert_input closure on %d "
          "Requires-satisfying inputs (%d boundary incl. both F2P gathered "
          "shapes, %d seeded fuzz, seed=%d); pure helper transformed() "
          "cross-checked on %d of them; %d shadow mutants all refuted; "
          "0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED, n_transformed, len(MUTANTS)))
    print(_report("pass", checked,
                  {"boundary": n_boundary, "fuzz": N_FUZZ,
                   "transformed_checked": n_transformed,
                   "mutants_refuted": len(MUTANTS),
                   "disagreements": 0}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
