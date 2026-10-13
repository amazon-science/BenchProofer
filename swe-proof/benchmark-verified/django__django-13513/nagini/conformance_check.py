#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13513 (nagini).

SHADOW
------
The `# impl-start` / `# impl-end` regions of `model.py`, copied VERBATIM with
only the contract calls deleted (`Requires`, `Ensures`, `Invariant`, `Assert`
and the `# invariants-start`/`-end` markers). Both modeled functions are
copied: `assemble_frames` (the modeled changed function) and
`frames_from_traceback` (the per-exception helper it calls). The `@Pure` helpers
`chain_total` and `locations_before` are copied too, and unlike the rest of the
`pure` region they ARE part of the shadow, because the impl regions call them:
`assemble_frames` reads `chain_total(ToSeq(trace_lens))` for the top of the
chain's location numbering and `frames_from_traceback` reads
`locations_before(chain, k)` for the start of the block exception `k` owns.
`chain_total` doubles as the SPEC-level oracle of the postcondition
`len(Result()) == chain_total(ToSeq(trace_lens))`, which this script checks
against the real frame count as a secondary observable. `PSeq` is shimmed as an
immutable tuple-backed sequence (`drop`/`len`/`[]`) exactly as those helpers
use it. There are no `@ContractOnly` callees in this bundle (mapping.md §3:
the behaviour is modeled deeply, nothing is axiomatized), so nothing is left
assumed.

ORACLE
------
The REAL patched repo function is CALLED, not transliterated:

  * `django.views.debug.ExceptionReporter.get_traceback_frames`
    (`django/views/debug.py:397` @ base_commit; mapping.md §1) — driven on real
    exception chains carrying real `TracebackType` chains, for the modeled
    `assemble_frames`.
  * `django.views.debug.ExceptionReporter.get_exception_traceback_frames`
    (the generator the gold patch extracts; mapping.md §1) — driven per
    exception, for the modeled `frames_from_traceback`. When the importable
    Django does not define it (an unpatched or differently-shaped patch), this
    leg is recorded as not-run in the report and the main leg still runs — the
    differential is not weakened, only that sub-leg is unavailable.
  * `ExceptionReporter._get_explicit_or_implicit_cause` — the real chain walker,
    used to re-derive the chain the real code will visit (see "bridge check").

The gate applies patch.diff to /testbed and sets PYTHONPATH, so the imported
`django.views.debug` IS the patched module. Nothing about the patched source is
reimplemented here.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
The model's carrier is `trace_lens: List[int]`, exception-chain order
(index 0 = outermost, last index = innermost cause; the report pops from the
end), where `trace_lens[k]` is the number of VISIBLE nodes in exception k's own
traceback — visible meaning surviving the real code's `__traceback_hide__` skip.
Concretization (`build_chain`):

  * `trace_lens[k] = v` becomes a real exception raised through a recursion that
    lays down `v` frames WITHOUT `__traceback_hide__` plus `h >= 0` frames WITH
    it, interleaved in random order, so the visible-node abstraction is actually
    exercised rather than trivially satisfied (a chain of all-visible nodes would
    never test the skip);
  * the chain link `exceptions[k] -> exceptions[k+1]` becomes either
    `__cause__` (explicit) or `__context__` with `__suppress_context__ = False`
    (implicit) — both link kinds the real `_get_explicit_or_implicit_cause`
    follows are generated;
  * `ExceptionReporter(None, type(head), head, head.__traceback__)` supplies
    `self.tb`, which the patched code uses for the single-exception case
    (mapping.md §2, last row).

Result bridge: the shadow returns `List[int]`, one entry per report entry, each
entry being the CHAIN LOCATION NUMBER of the location it reports (mapping.md §2):
the exceptions own consecutive, pairwise-disjoint blocks of numbers in chain
order, `trace_lens[k]` wide, so exception `k`'s own node `j` is the number
`locations_before(trace_lens, k) + j`. One int therefore names BOTH whose trace
the entry comes from and which node of that trace it is. The real function
returns a list of frame dicts, in report order; every real frame dict carries
`'tb'`, the actual traceback node it was built from, so each real frame is
attributed to the exception that owns that node and to that node's position among
the visible nodes of that exception's own traceback — the pair the model's entry
encodes, which this script re-encodes the same way before comparing. The
comparison is therefore the whole report, entry by entry, and the observables are
separated so a disagreement says which one broke:

  * COUNT. `len(shadow) == len(real_frames)`, cross-checked against
    `chain_total`, the postcondition's own fold.
  * PER-ENTRY CONTENT, PLACEMENT AND ATTRIBUTION. `real chain location numbers
    == shadow` elementwise. This pins what the report READ POSITIONALLY shows:
    each exception contributing its OWN locations, in trace order, as one
    contiguous block, blocks in chain-consumption order. A per-exception
    reversal, an exchange of two blocks, or a block generated from a DIFFERENT
    exception of the chain — including one whose trace happens to record the same
    number of locations — keeps the count exactly and breaks this, because the
    numbers a block carries belong to one exception alone.
  * PER-EXCEPTION ATTRIBUTION / ORDER. The same fact read as blocks: the
    run-lengths of the real report's consecutive same-owner groups against the
    blocks of the shadow's own report. The shadow's block boundaries are an
    observable of its output — inside one exception's block the numbers ascend by
    exactly 1, and the next block starts at a strictly lower number, since the
    report consumes the chain from the innermost cause (which owns the HIGHEST
    numbers) downwards — so the consumption order is read off the VERBATIM impl
    region's own result, with no order-revealing substitute helper.
  * READ-ONLY INPUT. `Requires(Acc(list_pred(trace_lens), 1/2))` and the
    matching `Ensures` say the assembly mutates nothing it is given; the shadow's
    input list is compared before/after each call.

BRIDGE CHECK (so a wrong bridge cannot look like agreement)
-----------------------------------------------------------
Before comparing, each constructed chain is re-derived from the head exception
using the REAL `_get_explicit_or_implicit_cause` and the real code's own
`__traceback_hide__` skip rule, and the resulting visible-node lengths must equal
the `trace_lens` that was generated. A mismatch is reported as a BRIDGE error
(exit 1), never silently absorbed: it would mean the real function was being fed
something other than the model's input.

INPUTS (>= 1e5 satisfying `Requires(trace_lens[k] >= 0)`)
---------------------------------------------------------
1. Named boundary cases: empty chain, single exception with empty / non-empty
   trace, the exact FAIL_TO_PASS shape `[1, 0]` (built both synthetically and by
   replaying the F2P test's own raise/`__context__` code verbatim), empty in
   leading / middle / trailing position, all-empty, all-hidden traces.
2. EXHAUSTIVE enumeration of the sub-domain `len(trace_lens) <= 4` with each
   `trace_lens[k] in {0, 1, 2}`, crossed with ALL 2**(k-1) link-kind patterns
   (778 chains). The full modeled domain is infinite (unbounded chain length and
   unbounded trace lengths), so this exhaustive block is a floor, not the whole
   space; the fuzz below extends past it.
3. Seeded fuzz to fill the count: chain length 0..6, per-exception visible length
   0..5 (zero deliberately frequent, since an empty trace is the branch the gold
   patch changed), hidden nodes 0..2, random link kinds.

Every branch of both impl regions is taken: `assemble_frames`'s chain loop not
entered (`n == 0`) and entered, with the block it appends empty
(`trace_lens[i-1] == 0`) and non-empty; `frames_from_traceback` with
`trace_len == 0` and `> 0`.

Pinned fuzz seed: 13513 (recorded in mapping.md §G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib only (hypothesis is not needed: the
input domain is a list of small non-negative ints, enumerated then seeded-fuzzed
directly, which keeps the boundary block exhaustive and the run reproducible).
"""
import itertools
import json
import random
import sys
from typing import List  # noqa: F401 — named by the copied `# type:` comments

SEED = 13513
N_FUZZ = 100_000
MAX_REPORTED = 5


# =============================================================================
# PSeq shim — the immutable sequence `chain_total` reads (drop / len / [])
# =============================================================================

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, items):
        s = cls()
        s._t = tuple(items)
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

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    """model.py `ToSeq`: materialize a PSeq from a list."""
    return PSeq._wrap(lst)


# =============================================================================
# @Pure helpers from model.py, contracts/decorator stripped. Both are CALLED by
# the impl regions below, so they are part of the shadow; `chain_total` also
# serves as the SPEC-level oracle of the postcondition
# `len(Result()) == chain_total(ToSeq(trace_lens))`.
# =============================================================================

def chain_total(lens):
    """Total report-entry count for a chain: the sum of the per-exception trace
    lengths. Front-recursive so a single unfold is available per loop step."""
    if len(lens) == 0:
        return 0
    return lens[0] + chain_total(lens.drop(1))


def locations_before(lens, k):
    """Where exception `k`'s own block of chain location numbers begins: the
    number of locations owned by the exceptions BEFORE it in chain order."""
    return chain_total(lens) - chain_total(lens.drop(k))


# =============================================================================
# SHADOW — the impl regions of model.py, VERBATIM, contract calls stripped
# =============================================================================

def frames_from_traceback(chain, k):
    # impl-start
    result = []  # type: List[int]
    # where this exception's own block of chain location numbers begins
    start = locations_before(chain, k)
    trace_len = chain[k]
    i = 0
    while i < trace_len:
        result.append(start + i)
        i = i + 1
    return result
    # impl-end


def blocks_from_locations(report):
    """The run-lengths of the report's per-exception blocks, read straight off the
    report the shadow produced. An entry carries the chain location number it
    describes; inside one exception's block those numbers ascend by exactly 1
    (its own trace order over the consecutive numbers it owns), and the block the
    report lays down NEXT belongs to an exception EARLIER in the chain, which owns
    strictly lower numbers -- the report consumes the innermost cause, the owner
    of the highest numbers, first. So `value != previous + 1` marks a block
    boundary exactly, and an empty trace contributes no entry and so no boundary.
    The shadow's consumption order is therefore an observable of its own output --
    no order-revealing substitute helper is needed."""
    groups = []
    prev = None
    for value in report:
        if prev is None or value != prev + 1:
            groups.append(0)
        groups[-1] += 1
        prev = value
    return groups


def assemble_frames(trace_lens):
    # impl-start
    frames = []  # type: List[int]
    # The report consumes the chain from the end (innermost cause first), then
    # the remaining exceptions in turn; each exception's own entries are appended
    # as one block, drawn from THAT exception's own trace, so every exception
    # contributes its own entries independently of the rest.
    n = len(trace_lens)
    i = n
    # `suffix` is the part of the chain already consumed and `base` the number of
    # entries it contributed -- the two quantities the report's shape is read off.
    suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
    base = 0
    # `head` is where the block of location numbers owned by the exceptions NOT
    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
    total = chain_total(ToSeq(trace_lens))
    head = total
    while i > 0:
        # the block for the exception whose turn it is, drawn from ITS OWN trace:
        # the helper is told which exception of this chain it serves.
        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
        m = len(contribution)
        frames.extend(contribution)
        # This exception is consumed: fold its block into the chain suffix. The
        # suffix one exception longer starts with THIS exception's trace length
        # and continues with the suffix just consumed ...
        i = i - 1
        longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
        suffix = longer
        base = base + m
        head = head - m
    return frames
    # impl-end


# =============================================================================
# ORACLE — the REAL patched repo function, imported and called
# =============================================================================

def _load_real():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={})
        django.setup()
    from django.views.debug import ExceptionReporter
    return django, ExceptionReporter


DJANGO, ExceptionReporter = _load_real()
# The gold patch extracts this generator; it is the repo counterpart of the
# modeled `frames_from_traceback` (mapping.md §1).
HAS_PER_EXC = hasattr(ExceptionReporter, 'get_exception_traceback_frames')
# The gold patch promotes the local closure to this method; used to re-derive
# the chain the real code walks. Falls back to the pre-patch closure's logic
# ONLY for the bridge derivation (never for an observable under comparison).
HAS_CAUSE_METHOD = hasattr(ExceptionReporter, '_get_explicit_or_implicit_cause')


def real_frames(excs):
    """Drive the REAL patched `get_traceback_frames` on a constructed chain."""
    if not excs:
        reporter = ExceptionReporter(None, None, None, None)
    else:
        head = excs[0]
        reporter = ExceptionReporter(None, type(head), head, head.__traceback__)
    return reporter, reporter.get_traceback_frames()


def real_per_exception_frames(reporter, exc):
    """Drive the REAL patched `get_exception_traceback_frames` for ONE
    exception — the repo counterpart of `frames_from_traceback`."""
    return list(reporter.get_exception_traceback_frames(exc, exc.__traceback__))


# =============================================================================
# TYPE BRIDGE — model `List[int]` of visible-node counts <-> real chain
# =============================================================================

class _ConfMarker(Exception):
    """The exception type raised to lay down a controlled traceback."""


def _emit(pattern, i):
    """Lay down one traceback node per element of `pattern`; 'h' nodes carry
    `__traceback_hide__` (the real code skips them), 'v' nodes do not. The
    terminal raising frame is itself hidden, so `pattern` alone determines the
    visible-node count (the bridge check below re-derives it and would catch a
    phantom node here)."""
    if i == len(pattern):
        __traceback_hide__ = True       # noqa: F841 — read via f_locals
        raise _ConfMarker('boom')
    if pattern[i] == 'h':
        __traceback_hide__ = True       # noqa: F841 — read via f_locals
        _emit(pattern, i + 1)
    else:
        _emit(pattern, i + 1)


def _make_exc(pattern):
    """A real exception whose `__traceback__` has exactly the nodes `pattern`
    describes (after dropping this builder's own frame)."""
    exc = None
    try:
        _emit(tuple(pattern), 0)
    except _ConfMarker as e:
        exc = e
    # node 0 is _make_exc's own frame; drop it so the chain is exactly `pattern`
    exc.__traceback__ = exc.__traceback__.tb_next
    exc.__cause__ = None                # NB: also sets __suppress_context__
    exc.__context__ = None
    exc.__suppress_context__ = False
    return exc


def build_chain(trace_lens, link_kinds, hidden):
    """Concretize a model input: `trace_lens[k]` visible nodes for exception k
    (chain order, index 0 = outermost), `hidden[k]` extra hidden nodes
    interleaved, `link_kinds[k]` in {'explicit', 'implicit'} joining k to k+1."""
    n = len(trace_lens)
    excs = []
    for k in range(n):
        pattern = ['v'] * trace_lens[k] + ['h'] * hidden[k]
        _SHUFFLER.shuffle(pattern)
        excs.append(_make_exc(pattern))
    for k in range(n - 1):
        nxt = excs[k + 1]
        if link_kinds[k] == 'explicit':
            excs[k].__cause__ = nxt          # sets __suppress_context__ = True
        else:
            excs[k].__context__ = nxt
            excs[k].__suppress_context__ = False
    return excs


def _visible_nodes(tb):
    """The real code's own visibility rule: a node whose frame has
    `__traceback_hide__` truthy is skipped (`django/views/debug.py`, the
    `while tb is not None` walk)."""
    n = 0
    while tb is not None:
        if not tb.tb_frame.f_locals.get('__traceback_hide__'):
            n += 1
        tb = tb.tb_next
    return n


def _cause_of(reporter, exc):
    if HAS_CAUSE_METHOD:
        return reporter._get_explicit_or_implicit_cause(exc)
    explicit = getattr(exc, '__cause__', None)
    suppress_context = getattr(exc, '__suppress_context__', None)
    implicit = getattr(exc, '__context__', None)
    return explicit or (None if suppress_context else implicit)


def derive_chain(reporter, head):
    """Re-derive, via the REAL cause walker, the chain the real function will
    visit and each member's visible-node count. Returns (exceptions,
    visible_lens) in chain order (outermost first)."""
    excs = []
    v = head
    while v:
        excs.append(v)
        v = _cause_of(reporter, v)
        if v in excs:
            break
    return excs, [_visible_nodes(e.__traceback__) for e in excs]


def _owner_index(excs):
    """`id(tb node) -> (owning exception, that node's 0-based position among the
    VISIBLE nodes of that exception's own traceback, in traceback order)`.
    Returns None if a node is shared between two exceptions (attribution would be
    ambiguous; reported as a bridge error rather than absorbed)."""
    owner = {}
    for k, exc in enumerate(excs):
        tb = exc.__traceback__
        pos = 0
        while tb is not None:
            if id(tb) in owner:
                return None             # a node shared between exceptions
            if not tb.tb_frame.f_locals.get('__traceback_hide__'):
                owner[id(tb)] = (k, pos)
                pos += 1
            tb = tb.tb_next
    return owner


def real_groups_and_locations(excs, frames, trace_lens):
    """Attribute each real frame dict to the exception owning its `'tb'` node and
    to that node's position within THAT exception's own visible traceback, then
    re-encode the pair the way the model does: the CHAIN LOCATION NUMBER
    `locations_before(trace_lens, k) + pos`, which names the owner and the node
    together (mapping.md §2). Returns `(group_lengths, entry_locations)` in real
    output order: the run-lengths of consecutive same-owner groups, and the
    per-frame location number — the observables the model's report carries. None
    if attribution is ambiguous."""
    owner = _owner_index(excs)
    if owner is None:
        return None
    lens = ToSeq(list(trace_lens))
    starts = [locations_before(lens, k) for k in range(len(trace_lens))]
    groups = []
    locations = []
    prev = None
    for f in frames:
        if 'tb' not in f:
            return None
        got = owner.get(id(f['tb']))
        if got is None:
            return None                 # a frame from a node we did not build
        k, pos = got
        if k >= len(starts):
            return None                 # an owner outside the derived chain
        locations.append(starts[k] + pos)
        if k != prev:
            groups.append(0)
            prev = k
        groups[-1] += 1
    return groups, locations


# =============================================================================
# the differential
# =============================================================================

_SHUFFLER = random.Random(SEED ^ 0x5EED)


class Disagreement(Exception):
    def __init__(self, kind, tl, detail):
        Exception.__init__(self, kind)
        self.kind = kind
        self.tl = tl
        self.detail = detail


def check_case(trace_lens, link_kinds, hidden, label):
    """Run shadow and real oracle on one model input; raise on disagreement."""
    trace_lens = list(trace_lens)
    excs = build_chain(trace_lens, link_kinds, hidden)

    reporter, frames = real_frames(excs)

    # --- bridge check: the real code must see exactly the model's input -------
    if excs:
        seen, derived = derive_chain(reporter, excs[0])
        if len(seen) != len(excs) or derived != trace_lens:
            raise Disagreement(
                "BRIDGE", trace_lens,
                "real chain walk derived lens=%r (chain of %d) but the model "
                "input was %r (chain of %d)"
                % (derived, len(seen), trace_lens, len(excs)))

    # --- SHADOW ---------------------------------------------------------------
    before = list(trace_lens)
    shadow = assemble_frames(trace_lens)
    if trace_lens != before:
        raise Disagreement(
            "READ-ONLY", before,
            "shadow mutated its input: %r -> %r" % (before, trace_lens))

    # --- primary observable: total report length ------------------------------
    if len(shadow) != len(frames):
        raise Disagreement(
            "COUNT", trace_lens,
            "shadow len=%d vs REAL get_traceback_frames len=%d"
            % (len(shadow), len(frames)))

    # --- spec-level cross-check: the postcondition's own fold ----------------
    spec = chain_total(ToSeq(trace_lens))
    if spec != len(frames):
        raise Disagreement(
            "SPEC", trace_lens,
            "chain_total=%d vs REAL get_traceback_frames len=%d"
            % (spec, len(frames)))

    # --- per-entry content and placement (the report read POSITIONALLY) ------
    attributed = real_groups_and_locations(excs, frames, trace_lens)
    if attributed is None:
        raise Disagreement("BRIDGE", trace_lens,
                           "could not attribute real frames to exceptions")
    groups, locations = attributed
    # Every position of the real report, entry by entry: the real frame sitting
    # there reports the chain location -- whose exception AND which node of that
    # exception's own trace -- that the shadow puts there. This is the whole
    # report, not just its length, and because a location number belongs to one
    # exception alone it also pins each block to its owner.
    if locations != shadow:
        raise Disagreement(
            "ENTRY", trace_lens,
            "REAL per-entry chain location numbers (output order) %r vs the "
            "shadow's report %r" % (locations, shadow))
    # ... and the same fact read as blocks: the run-lengths of the real report's
    # per-exception groups against the blocks of the shadow's own report.
    shadow_groups = blocks_from_locations(shadow)
    if groups != shadow_groups:
        raise Disagreement(
            "ORDER", trace_lens,
            "REAL per-exception group lengths (output order) %r vs the "
            "shadow's own consumption order %r" % (groups, shadow_groups))

    # --- frames_from_traceback vs the REAL extracted generator ---------------
    if HAS_PER_EXC:
        owner = _owner_index(excs)
        for k, exc in enumerate(excs):
            lens = ToSeq(list(trace_lens))
            model_one = frames_from_traceback(lens, k)
            real_one = real_per_exception_frames(reporter, exc)
            if len(model_one) != len(real_one):
                raise Disagreement(
                    "PER-EXC", trace_lens,
                    "exception %d: frames_from_traceback(chain, %d) len=%d vs "
                    "REAL get_exception_traceback_frames len=%d"
                    % (k, k, len(model_one), len(real_one)))
            # entry by entry too: the j-th frame the real generator yields for
            # this exception is the j-th visible location of its own traceback,
            # i.e. the j-th chain location number THIS exception owns. A block
            # drawn from another exception of the same trace length would carry
            # that exception's numbers instead and is caught here.
            real_one_loc = [
                None if owner is None or owner.get(id(f.get('tb'))) is None
                else (locations_before(lens, owner[id(f.get('tb'))][0])
                      + owner[id(f.get('tb'))][1])
                for f in real_one]
            if real_one_loc != model_one:
                raise Disagreement(
                    "PER-EXC", trace_lens,
                    "exception %d: REAL get_exception_traceback_frames yields "
                    "chain location numbers %r vs frames_from_traceback(chain, "
                    "%d) = %r" % (k, real_one_loc, k, model_one))
    return len(frames)


# --- the FAIL_TO_PASS scenario, replayed from the test's own source ----------

def f2p_scenario():
    """`test_innermost_exception_without_traceback` verbatim: an exception with
    a 1-node traceback whose `__context__` was attached but never raised (so it
    has NO traceback of its own) — model input [1, 0]."""
    try:
        try:
            raise RuntimeError('Oops')
        except Exception as exc:
            new_exc = RuntimeError('My context')
            exc.__context__ = new_exc
            raise
    except Exception:
        exc_type, exc_value, tb = sys.exc_info()
    reporter = ExceptionReporter(None, exc_type, exc_value, tb)
    return reporter, reporter.get_traceback_frames()


def check_f2p():
    """The real F2P scenario, against the shadow, through the bridge."""
    reporter, frames = f2p_scenario()
    excs, derived = derive_chain(reporter, reporter.exc_value)
    shadow = assemble_frames(list(derived))
    if len(shadow) != len(frames):
        raise Disagreement(
            "F2P", derived,
            "F2P scenario: shadow len=%d vs REAL get_traceback_frames len=%d"
            % (len(shadow), len(frames)))
    attributed = real_groups_and_locations(excs, frames, derived)
    if attributed is None:
        raise Disagreement("BRIDGE", derived,
                           "F2P scenario: could not attribute real frames")
    if attributed[1] != shadow:
        raise Disagreement(
            "F2P", derived,
            "F2P scenario: REAL per-entry chain location numbers %r vs the "
            "shadow's report %r" % (attributed[1], shadow))
    return derived, len(frames)


# --- input corpus ------------------------------------------------------------

def named_boundaries():
    """(trace_lens, link_kinds, hidden) triples, hand-picked."""
    def mk(tl, kinds=None, hidden=None):
        n = len(tl)
        if kinds is None:
            kinds = ['implicit'] * max(0, n - 1)
        if hidden is None:
            hidden = [0] * n
        return (tl, kinds, hidden)

    return [
        mk([]),                              # no exceptions at all
        mk([0]),                             # one exception, empty trace
        mk([1]),                             # one exception, one node
        mk([4]),                             # one exception, several nodes
        mk([1, 0]),                          # the FAIL_TO_PASS shape
        mk([1, 0], ['explicit']),            # same, explicit __cause__ link
        mk([0, 1]),                          # empty outer, non-empty inner
        mk([0, 0]),                          # all empty
        mk([0, 0, 0]),
        mk([2, 0, 3]),                       # empty in the middle
        mk([0, 0, 5]),
        mk([5, 0, 0]),
        mk([4, 3, 2, 1]),                    # all non-empty
        mk([1, 2, 3, 4, 5, 6]),              # longer chain
        mk([0], None, [3]),                  # trace of ONLY hidden nodes
        mk([1, 0], None, [2, 2]),            # hidden nodes on both sides
        mk([0, 0], None, [1, 1]),            # all hidden, two exceptions
        mk([2, 0, 2], ['explicit', 'implicit'], [1, 3, 1]),   # mixed links
        mk([2, 0, 2], ['implicit', 'explicit'], [0, 2, 0]),
        mk([1] * 8),                          # eight singletons
    ]


def exhaustive_small():
    """EXHAUSTIVE over the sub-domain: len(trace_lens) <= 4, each entry in
    {0,1,2}, ALL link-kind patterns. 778 chains. (The full modeled domain is
    infinite — unbounded chain length and unbounded trace lengths — so this is
    a floor that the fuzz block extends past.)"""
    for n in range(0, 5):
        for tl in itertools.product((0, 1, 2), repeat=n):
            for kinds in itertools.product(('implicit', 'explicit'),
                                           repeat=max(0, n - 1)):
                yield (list(tl), list(kinds), [0] * n)


def fuzz(rng, count):
    for _ in range(count):
        n = rng.randint(0, 6)
        tl = []
        for _ in range(n):
            # empty traces deliberately frequent: an exception with an empty
            # trace is the branch the gold patch changed.
            tl.append(0 if rng.random() < 0.35 else rng.randint(1, 5))
        hidden = [rng.randint(0, 2) for _ in range(n)]
        kinds = [rng.choice(('implicit', 'explicit')) for _ in range(max(0, n - 1))]
        yield (tl, kinds, hidden)


def main():
    checked = 0
    branch = {"outer_skipped": 0, "outer_taken": 0,
              "inner_skipped": 0, "inner_taken": 0}
    total_frames = 0
    failures = []

    def run(triple, label):
        nonlocal checked, total_frames
        tl, kinds, hidden = triple
        try:
            got = check_case(tl, kinds, hidden, label)
        except Disagreement as d:
            failures.append((label, d))
            return
        checked += 1
        total_frames += got
        if not tl:
            branch["outer_skipped"] += 1
        else:
            branch["outer_taken"] += 1
            if any(n == 0 for n in tl):
                branch["inner_skipped"] += 1
            if any(n > 0 for n in tl):
                branch["inner_taken"] += 1

    # 1. the real FAIL_TO_PASS scenario, replayed from the test source
    try:
        f2p_lens, f2p_count = check_f2p()
        checked += 1
    except Disagreement as d:
        failures.append(("f2p", d))
        f2p_lens, f2p_count = None, None

    # 2. named boundaries
    for t in named_boundaries():
        run(t, "boundary")
        if len(failures) >= MAX_REPORTED:
            break

    # 3. exhaustive small sub-domain
    if len(failures) < MAX_REPORTED:
        n_exh = 0
        for t in exhaustive_small():
            run(t, "exhaustive")
            n_exh += 1
            if len(failures) >= MAX_REPORTED:
                break
    else:
        n_exh = 0

    # 4. seeded fuzz
    if len(failures) < MAX_REPORTED:
        rng = random.Random(SEED)
        for t in fuzz(rng, N_FUZZ):
            run(t, "fuzz")
            if len(failures) >= MAX_REPORTED:
                break

    if failures:
        print("G-CONF FAIL: %d disagreement(s) after %d inputs"
              % (len(failures), checked))
        for label, d in failures:
            print("  [%s/%s] trace_lens=%r: %s" % (label, d.kind, d.tl, d.detail))
        print(json.dumps({"status": "fail", "checked": checked,
                          "seed": SEED,
                          "disagreements": len(failures),
                          "first": failures[0][1].detail}))
        return 1

    version = ".".join(str(p) for p in DJANGO.VERSION[:3])
    print("G-CONF OK: nagini impl-region shadow (assemble_frames + "
          "frames_from_traceback, verbatim) agrees with the REAL patched "
          "django.views.debug.ExceptionReporter.get_traceback_frames on %d "
          "chains (F2P %r -> %d frames; %d named boundaries; %d exhaustive "
          "len<=4 x lens in {0,1,2} x all link kinds; %d seeded fuzz, "
          "seed=%d) on Django %s; total %d real frames compared; count, "
          "per-entry chain location number (owner + node) and placement, "
          "per-exception attribution/pop order, chain_total postcondition and "
          "read-only input all agree; 0 disagreements."
          % (checked, f2p_lens, f2p_count or 0, len(named_boundaries()), n_exh,
             N_FUZZ, SEED, version, total_frames))
    print(json.dumps({
        "status": "pass",
        "checked": checked,
        "seed": SEED,
        "disagreements": 0,
        "oracle": "django.views.debug.ExceptionReporter.get_traceback_frames "
                  "(called, patched in-container)",
        "oracle_per_exception":
            "ExceptionReporter.get_exception_traceback_frames (called)"
            if HAS_PER_EXC else "absent in the importable Django (leg not run)",
        "shadow": "model.py impl regions, verbatim, contracts stripped",
        "compared": "count + per-entry chain location number, i.e. owner "
                    "exception + node within its own trace (elementwise) + "
                    "per-exception block order + read-only input",
        "django": version,
        "gold_marker_present": HAS_PER_EXC,
        "exhaustive_subdomain": n_exh,
        "fuzz": N_FUZZ,
        "real_frames_compared": total_frames,
        "branches": branch,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
