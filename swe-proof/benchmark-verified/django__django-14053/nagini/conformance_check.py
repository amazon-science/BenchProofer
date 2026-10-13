#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14053 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
(`first_pass_ids` / `adj_ids` / `failing_adj_count` / `reported` /
`lemma_split_len`) are copied over as plain functions running on a small
tuple-based PSeq shim (take/drop/concat/index/len are all the operations they
use). The impl itself uses only plain Python lists, so it runs unchanged. There
are no @ContractOnly callees in this bundle.

ORACLE: the REAL repo generator the model models per mapping.md §1 —
`django.contrib.staticfiles.storage.HashedFilesMixin.post_process`, imported
from the reference tree (the gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes it importable). The oracle class
SUBCLASSES the real mixin, so it inherits BOTH the real `post_process` under
test AND the real `_post_process` helper — including the latter's
`sorted(paths, key=path_level, reverse=True)` traversal (`storage.py:262-267`)
AND its `except ValueError as exc: yield name, None, exc, False` arm
(`storage.py:300-301`). ONLY storage I/O is stubbed:
  * `open` / `_save` / `exists` / `delete` / `hashed_name` — the per-file value
    machinery, which does not affect WHICH `name`s are reported. `hashed_name`
    is deterministic and SETTLES after `settle_pass` calls per file, so the real
    convergence test `old_hashed_name == hashed_name` eventually holds and the
    run converges strictly inside the pass budget — the modelled CONVERGENT
    domain (the one out-of-domain arm is non-convergence, mapping.md §2). The
    pass budget and the settle point are both fuzzed, since the modelled output
    must be pass-count-invariant;
  * `url_converter` — for a file in `error_names` the converter raises
    ValueError, so the REAL `except ValueError as exc` arm inside
    `_post_process` fires and the file's examination genuinely fails. This arm
    is IN the modelled domain: the `err` stream is its carrier. Note the real
    code path invokes `url_converter` only inside `if name in adjustable_paths:`
    (`storage.py:291`), so flagging a PLAIN file reaches nothing — the
    unreachable flag binding of mapping.md §2, which the model is insensitive to
    and which this script therefore also feeds in on purpose;
  * `self._patterns` has the real `{extension: [(pattern, template)]}` shape,
    keyed by the adjustable file names, so the module's real `matches_patterns`
    (fnmatchcase-based) classifies a file as adjustable iff its name is a key
    (names carry no glob metachars), and each key carries one real `url(...)`
    pattern so an errored file's content actually reaches `url_converter`;
  * the observed value is the sequence of `name`s the real generator yields
    back to its caller.

Why NOT stub `_post_process`: the postcondition constrains the reported ORDER,
which is produced by `_post_process`'s depth-first sort, and the reported
MULTIPLICITY of a failing file, which is produced by that helper emitting two
quadruples for one file in one pass (the exception quadruple at
`storage.py:300-301` and then the terminal one at `storage.py:332`). A stub
replaces the very behaviour under validation. A same-depth name pool makes the
depth sort a provable no-op, and a suite with no failing files never reaches the
`err` clause at all; this script drives MIXED-DEPTH names WITH and WITHOUT
failing files and asserts (see the two suite guards in `main`) that a large
fraction of cases are genuinely reordered by the sort and that a large fraction
carry a file that really fails.

Type bridge (mapping.md §2): file identity codes `ids: List[int]` map
bijectively to file names via `_name_for(id, depth)` — a `.css` file at a
chosen directory depth, distinct per id, none containing fnmatch metachars; the
parallel `adj: List[int]` stream maps to membership of the file's name in the
adjustable set (`adj[k] != 0` <=> adjustable); the parallel `err: List[int]`
stream maps to membership in the error set (`err[k] != 0` <=> that file's
examination raises); the yielded triple projects to its `name` component,
mapped back to the id. Crucially the streams are presented in the routine's
ENUMERATION order (`enumeration_order(...)` =
`sorted(names, key=path_level, reverse=True)`), which is the binding
mapping.md §2 "Enumeration order" states and the order the postcondition is
written against — NOT raw `paths` iteration order. Outputs compare with `==` on
List[int] (an ORDERED comparison, so it refutes order divergence).

Input domain (the model's Requires): three equal-length parallel streams,
distinct ids (the input is keyed). Boundary cases cover the empty collection,
single plain / single adjustable / single adjustable-and-failing (the shape the
failure-path hidden test uses), all-plain, all-adjustable, all-failing, mixed
flags, plain-and-flagged (unreachable) bindings, tight pass budgets, and depth
patterns that make the real sort reorder (ascending, descending, tied, and
single-depth no-op); fuzz draws sizes 0..16, random adjustable subsets, random
error subsets drawn independently of adjustability, random distinct (possibly
negative) ids, random pass budget / settle pass, and random per-file directory
depths 1..4.

>= 1e5 Requires-satisfying inputs: 34 boundary + 100000 fuzz collections.
Pinned fuzz seed: 14053.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import io
import json
import os
import random
import re
import sys

SEED = 14053
N_FUZZ = 100_000

# The REAL mixin: we subclass it so the oracle inherits the REAL
# `_post_process` (with its depth-sorted traversal and its ValueError arm) and
# the REAL `post_process`.
from django.contrib.staticfiles.storage import HashedFilesMixin as _REAL_MIXIN


# --- PSeq shim: the pure helpers use only construction, concat, take/drop, ---
# --- indexing and len; a tuple carrier provides all of them ------------------

class PSeq:
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

    def __getitem__(self, i):
        return self._t[i]

    def __len__(self):
        return len(self._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t


def to_seq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, decorators + contract calls stripped --------

def first_pass_ids(ids, adj, err):
    if len(ids) == 0 or len(adj) == 0 or len(err) == 0:
        return PSeq(0).take(0)
    rest = first_pass_ids(ids.drop(1), adj.drop(1), err.drop(1))
    if adj[0] == 0 or err[0] != 0:
        return PSeq(ids[0]) + rest
    return rest


def adj_ids(ids, adj):
    if len(ids) == 0 or len(adj) == 0:
        return PSeq(0).take(0)
    rest = adj_ids(ids.drop(1), adj.drop(1))
    if adj[0] != 0:
        return PSeq(ids[0]) + rest
    return rest


def failing_adj_count(ids, adj, err):
    if len(ids) == 0 or len(adj) == 0 or len(err) == 0:
        return 0
    rest = failing_adj_count(ids.drop(1), adj.drop(1), err.drop(1))
    if adj[0] != 0 and err[0] != 0:
        return 1 + rest
    return rest


def reported(ids, adj, err):
    return first_pass_ids(ids, adj, err) + adj_ids(ids, adj)


def lemma_split_len(ids, adj, err):
    if len(ids) == 0:
        return True
    return lemma_split_len(ids.drop(1), adj.drop(1), err.drop(1))


# --- the impl region of model.py, verbatim (contract calls stripped) ---------

def collect_reports(ids, adj, err):
    # First pass: report the plain files, and any file whose examination fails,
    # as the pass reaches them; collect the adjustable files for the settled
    # segment.
    first = []  # type: list
    collected = []  # type: list
    i = len(ids)
    while i > 0:
        fid = ids[i - 1]
        fa = adj[i - 1]
        fe = err[i - 1]
        if fa == 0 or fe != 0:
            # Plain files, and any failing examination, go straight to the
            # caller at this position in the enumeration.
            first = [fid] + first
        if fa != 0:
            # Adjustable files are revisited across the internal passes but are
            # collected, keyed by file, so each is held only once; they are
            # reported at the end with their final outcome.
            collected = [fid] + collected
        i = i - 1
    # Report the first pass followed by the settled adjustable files, once each.
    result = first + collected
    return result


# --- oracle: the REAL post_process, driven on the modelled domain ------------

_URL_PAT = re.compile(r"""url\(['"]{0,1}\s*(.*?)["']{0,1}\)""")


def path_level(name):
    """The real `_post_process`'s sort key (`storage.py:262-267`)."""
    return len(name.split(os.sep))


def enumeration_order(file_names):
    """The order the REAL `_post_process` visits files:
    `sorted(paths, key=path_level, reverse=True)` — deepest-directory-first,
    Python's stable sort breaking ties by `paths` iteration order. This is the
    order the model's `ids`/`adj`/`err` streams are bound to (mapping.md §2
    "Enumeration order"), and it PRE-EXISTS at base_commit."""
    return sorted(file_names, key=path_level, reverse=True)


class _StubStorage(_REAL_MIXIN):
    """Subclass of the REAL HashedFilesMixin: it inherits the REAL
    `_post_process` (including its `sorted(paths, key=path_level,
    reverse=True)` traversal and its `except ValueError as exc` arm) and the
    REAL `post_process` under test. ONLY storage I/O is stubbed —
    `open`/`_save`/`exists`/`delete`/`hashed_name`/`url_converter` — so the
    traversal ORDER and the failure MULTIPLICITY the postcondition constrains
    are produced by the real code rather than by a stub.

    Confined to the CONVERGENT domain: `hashed_name` stops changing once a file
    has been hashed `settle_pass` times, so `old_hashed_name == hashed_name` and
    the substitution loop converges strictly inside the pass budget (no
    `('All', None, RuntimeError(...))` report). Files in `error_names` fail
    their examination through the real ValueError arm, which is IN domain."""

    keep_intermediate_files = False

    def __init__(self, adjustable_names, max_passes, settle_pass,
                 error_names=frozenset()):
        # `_patterns` has the real shape {extension: [(pattern, template)]}:
        # its KEYS are consulted by matches_patterns (fnmatchcase — literal
        # names carry no glob metachars, so a name matches exactly itself) and
        # its .items() by the adjustable rewrite loop. Each key carries ONE real
        # url(...) pattern, so an errored file's content reaches url_converter
        # exactly once per pass (the one-pattern-per-file binding mapping.md §2
        # states); a non-errored file's content has no url(...) reference, so
        # the substitution is a no-op for it.
        self._patterns = {name: [(_URL_PAT, 'url("%s")')]
                          for name in sorted(adjustable_names)}
        self.max_post_process_passes = max_passes
        self.hashed_files = {}
        self._settle_pass = settle_pass
        self._error_names = set(error_names)
        self._hash_calls = {}

    # --- storage I/O stubs (the ONLY things replaced) ---
    def open(self, path):
        # An errored file gets content carrying a url(...) reference, so the
        # real rewrite loop invokes our url_converter and the real
        # `except ValueError as exc: yield name, None, exc, False` arm fires,
        # rather than the failure being fabricated by a stub.
        if path in self._error_names:
            return io.BytesIO(b'a { background: url("dep.png"); }')
        return io.BytesIO(b'content of %s' % path.encode())

    def exists(self, name):
        return False

    def delete(self, name):
        pass

    def _save(self, name, content):
        return name

    def hashed_name(self, name, content=None, filename=None):
        """Deterministic, and it SETTLES: the value stops changing after
        `_settle_pass` calls for this file, so the real convergence test
        `old_hashed_name == hashed_name` eventually holds -> in-domain."""
        k = self._hash_calls.get(name, 0)
        self._hash_calls[name] = k + 1
        return '%s.%d.hash' % (name, min(k, self._settle_pass))

    def url_converter(self, name, hashed_files, template=None):
        """The real one returns the regex-substitution callable applied to an
        adjustable file's content; for a file in `_error_names` ours raises
        ValueError, which the REAL `_post_process` catches and reports as
        `yield name, None, exc, False`."""
        def converter(matchobj):
            if name in self._error_names:
                raise ValueError('post-processing %r failed' % name)
            return matchobj.group(0)
        return converter


def real_reported_names(post_process, file_names, adjustable_names,
                        max_passes, settle_pass, error_names=frozenset()):
    """Run the REAL post_process (over the REAL depth-sorted _post_process)
    and return the list of `name`s it yields back to its caller."""
    storage = _StubStorage(adjustable_names, max_passes, settle_pass,
                           error_names=error_names)
    paths = {name: (storage, name) for name in file_names}
    return [triple[0]
            for triple in post_process(storage, paths, dry_run=False)]


# --- one differential case ----------------------------------------------------

def _name_for(i, depth):
    """A file name at directory depth `depth` (>=1), bijective in `i` and free
    of fnmatch metachars. Mixed depths are ESSENTIAL: on a same-depth pool the
    real `_post_process`'s `sorted(..., key=path_level, reverse=True)` is a
    no-op, so a same-depth-only suite cannot observe the traversal order at
    all."""
    stem = 'f%d' % i if i >= 0 else 'fn%d' % (-i)
    return '/'.join(['d%d' % k for k in range(depth - 1)] + [stem + '.css'])


def _reachable_failure(adj, err):
    """Does this case make some file's examination REALLY fail? Only an
    adjustable file can: the substitution loop that can raise lives inside
    `if name in adjustable_paths:` (`storage.py:291`), so `url_converter` is
    never invoked for a plain file (mapping.md §2 'Unreachable flag
    combination')."""
    return any(a != 0 and e != 0 for a, e in zip(adj, err))


def check_case(post_process, ids, adj, err, max_passes, settle_pass,
               depths=None):
    """Bridge ids/adj/err -> a file collection, run shadow and real, compare.

    Per mapping.md §2 "Enumeration order" the streams are bound to the order
    the routine ENUMERATES the files, so the collection is built and then
    re-indexed into `enumeration_order(...)`; the shadow is evaluated on the
    streams in that same order. `depths` assigns a directory depth per file
    (defaulting to mixed depths) so the real depth sort actually reorders."""
    if depths is None:
        depths = [1 + (k % 4) for k in range(len(ids))]
    names = [_name_for(i, d) for i, d in zip(ids, depths)]
    assert len(set(names)) == len(names), 'name bridge must be injective'
    name_to_id = dict(zip(names, ids))
    id_to_adj = dict(zip(ids, adj))
    id_to_err = dict(zip(ids, err))
    adjustable = {n for n, a in zip(names, adj) if a != 0}
    # bound to the RAW error stream, including files that are flagged but plain
    # (unreachable under the bridge; the model is insensitive to them, and this
    # feeds that binding in on purpose rather than filtering it out).
    errored = {n for n, e in zip(names, err) if e != 0}

    # ids/adj/err re-presented in the routine's enumeration order (the binding
    # the postcondition is stated against).
    enum_names = enumeration_order(names)
    enum_ids = [name_to_id[n] for n in enum_names]
    enum_adj = [id_to_adj[i] for i in enum_ids]
    enum_err = [id_to_err[i] for i in enum_ids]

    shadow_out = collect_reports(enum_ids, enum_adj, enum_err)

    raw = real_reported_names(post_process, names, adjustable,
                              max_passes, settle_pass, error_names=errored)
    try:
        real_out = [name_to_id[n] for n in raw]
    except KeyError:
        return ("DISAGREEMENT (real yielded a name outside the collection)\n"
                "  ids=%r adj=%r err=%r max_passes=%r settle_pass=%r\n"
                "  shadow=%r\n  real names=%r"
                % (ids, adj, err, max_passes, settle_pass, shadow_out, raw))

    if shadow_out != real_out:
        return ("DISAGREEMENT\n  ids=%r adj=%r err=%r max_passes=%r "
                "settle_pass=%r\n  shadow=%r\n  real=%r"
                % (ids, adj, err, max_passes, settle_pass,
                   shadow_out, real_out))
    return None


def _sort_reorders(ids, depths):
    """True iff the real depth sort actually permutes this collection, i.e. the
    case can observe the traversal order at all."""
    if depths is None:
        depths = [1 + (k % 4) for k in range(len(ids))]
    names = [_name_for(i, d) for i, d in zip(ids, depths)]
    return enumeration_order(names) != names


def boundary_cases():
    # (ids, adj, err, max_passes, settle_pass, depths) — settle_pass <
    # max_passes keeps the run convergent (in-domain). `depths` is the per-file
    # directory depth; None = the mixed-depth default. Cases below deliberately
    # include depth patterns that make the real depth sort a REORDERING
    # (ascending, descending, tied, and single-depth-so-no-op), and both
    # failing and non-failing collections.
    return [
        ([], [], [], 5, 1, None),                          # empty collection
        ([7], [0], [0], 5, 1, None),                       # one plain file
        ([7], [1], [0], 5, 1, None),                       # one adjustable file
        ([7], [1], [1], 5, 1, None),   # one adjustable file, examination FAILS
        ([7], [0], [1], 5, 1, None),   # flagged but PLAIN (unreachable binding)
        ([7], [1], [0], 2, 1, None),                       # tightest budget
        ([7], [1], [1], 2, 1, None),                       # ditto, failing
        ([1, 2], [0, 0], [0, 0], 5, 1, [1, 2]),        # all plain, sort REORDERS
        ([1, 2], [0, 0], [0, 0], 5, 1, [1, 1]),        # all plain, sort no-op
        ([1, 2], [1, 1], [0, 0], 5, 2, [3, 1]),        # all adjustable
        ([1, 2], [1, 1], [1, 1], 5, 2, [3, 1]),        # all adjustable, all fail
        ([1, 2], [1, 1], [1, 0], 5, 2, [1, 3]),        # first of two fails
        ([1, 2], [1, 1], [0, 1], 5, 4, [1, 3]),        # second of two fails
        ([1, 2, 3], [0, 1, 0], [0, 0, 0], 5, 2, [1, 2, 3]),   # ascending depth
        ([1, 2, 3], [0, 1, 0], [0, 1, 0], 5, 2, [1, 2, 3]),   # ditto, failing
        ([1, 2, 3], [1, 0, 1], [0, 0, 0], 5, 3, [3, 2, 1]),   # descending depth
        ([1, 2, 3], [1, 0, 1], [1, 0, 1], 5, 3, [3, 2, 1]),   # ditto, failing
        ([1, 2, 3], [1, 0, 1], [0, 1, 0], 3, 1, [2, 2, 2]),   # ties; err on plain
        ([10, 20, 30, 40], [1, 1, 0, 0], [0, 0, 0, 0], 4, 2, [1, 4, 2, 3]),
        ([10, 20, 30, 40], [1, 1, 0, 0], [1, 0, 0, 0], 4, 2, [1, 4, 2, 3]),
        ([10, 20, 30, 40], [0, 0, 1, 1], [0, 0, 0, 1], 4, 2, [4, 1, 3, 2]),
        ([10, 20, 30, 40], [1, 0, 1, 0], [1, 1, 1, 1], 3, 2, [2, 2, 1, 1]),
        ([0, -1, 5], [0, 1, 1], [0, 0, 0], 5, 2, None),    # zero / negative ids
        ([0, -1, 5], [0, 1, 1], [1, 1, 0], 5, 2, None),    # ditto, failing
        ([-3, -2, -1], [1, 1, 1], [0, 0, 1], 5, 1, [3, 1, 2]),
        ([100, 5, 60, 2, 9], [0, 1, 0, 1, 0], [0, 0, 0, 0, 0], 5, 3, None),
        ([100, 5, 60, 2, 9], [0, 1, 0, 1, 0], [0, 1, 0, 1, 0], 5, 3, None),
        ([1, 2, 3, 4, 5, 6], [1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0], 6, 4, None),
        ([1, 2, 3, 4, 5, 6], [1, 1, 1, 0, 0, 0], [0, 0, 1, 0, 0, 1], 6, 4, None),
        ([1, 2, 3, 4, 5, 6], [0, 1, 0, 1, 0, 1], [0, 0, 0, 0, 0, 0], 2, 1,
         [1, 2, 3, 3, 2, 1]),
        ([8], [5], [0], 5, 2, None),               # non-0 flag other than 1
        ([8], [5], [7], 5, 2, None),               # non-0 err flag other than 1
        ([8, 9], [-2, 0], [-3, 0], 5, 2, None),    # negative non-0 flags
        ([3, 1, 4, 1000000, 5], [1, 0, 1, 1, 0], [1, 0, 0, 1, 0], 6, 5, None),
        (list(range(30)), [1 if k % 3 == 0 else 0 for k in range(30)],
         [1 if k % 5 == 0 else 0 for k in range(30)], 5, 2,
         [1 + (k % 5) for k in range(30)]),        # many files, 5 depths
    ]


def rand_case(rng):
    n = rng.randint(0, 16)
    ids = rng.sample(range(-1000, 1000), n)            # distinct (keyed input)
    adj = [rng.choice([0, 0, 1, 2, -1]) for _ in range(n)]
    # error flags drawn INDEPENDENTLY of adjustability, so both the reachable
    # failures and the unreachable plain-and-flagged bindings occur; a third of
    # the cases carry no failure at all.
    if rng.random() < 0.34:
        err = [0] * n
    else:
        err = [rng.choice([0, 0, 1, 3, -2]) for _ in range(n)]
    max_passes = rng.randint(2, 6)
    # settle strictly inside the budget -> the substitution loop converges
    # (in-domain: no ('All', None, RuntimeError) report).
    settle_pass = rng.randint(0, max_passes - 1)
    # MIXED depths, so the real `sorted(paths, key=path_level, reverse=True)`
    # genuinely permutes the collection (a same-depth pool makes it a no-op).
    depths = [rng.randint(1, 4) for _ in range(n)]
    return ids, adj, err, max_passes, settle_pass, depths


def main():
    # REAL repo function (PYTHONPATH=/testbed; gold patch applied by the gate).
    # `_StubStorage` subclasses the REAL mixin, so the oracle runs the REAL
    # `post_process` over the REAL depth-sorted `_post_process`.
    post_process = _REAL_MIXIN.post_process

    # Guards: the suite must actually EXERCISE (a) the depth sort and (b) the
    # failure arm. If every case had a same-depth pool the sort would be a
    # no-op and an ordering postcondition could not be refuted; if no case made
    # a file really fail, the `err` clause would never be reached.
    reordering = 0
    failing = 0

    checked = 0
    for ids, adj, err, max_passes, settle_pass, depths in boundary_cases():
        # sanity: the copied pure helpers agree with the copied impl (the
        # model's own Ensures, checked on the shadow side only)
        assert list(reported(to_seq(ids), to_seq(adj), to_seq(err))._t) == \
            collect_reports(ids, adj, err)
        assert (len(collect_reports(ids, adj, err))
                == len(ids) + failing_adj_count(to_seq(ids), to_seq(adj),
                                                to_seq(err)))
        assert lemma_split_len(to_seq(ids), to_seq(adj), to_seq(err))
        e = check_case(post_process, ids, adj, err, max_passes, settle_pass,
                       depths)
        if e:
            print(e)
            return 1
        checked += 1
        if _sort_reorders(ids, depths):
            reordering += 1
        if _reachable_failure(adj, err):
            failing += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        ids, adj, err, max_passes, settle_pass, depths = rand_case(rng)
        e = check_case(post_process, ids, adj, err, max_passes, settle_pass,
                       depths)
        if e:
            print(e)
            return 1
        checked += 1
        if _sort_reorders(ids, depths):
            reordering += 1
        if _reachable_failure(adj, err):
            failing += 1

    assert reordering > N_FUZZ // 10, (
        "suite does not exercise the real depth-sorted traversal (only %d of %d "
        "cases are reordered by it) -- an ordering postcondition cannot be "
        "refuted on same-depth pools" % (reordering, checked))
    assert failing > N_FUZZ // 10, (
        "suite does not exercise the real failure arm (only %d of %d cases make "
        "a file's examination actually fail) -- the `err` clause of the "
        "postcondition would be untested" % (failing, checked))

    print("G-CONF OK: shadow impl (contract-stripped collect_reports) == real "
          "HashedFilesMixin.post_process yielded-name stream on %d "
          "inputs (%d boundary + %d fuzz, seed %d) over the modelled convergent "
          "domain, failing examinations INCLUDED. The oracle inherits the REAL "
          "`_post_process` (only storage I/O and url_converter are stubbed), so "
          "its `sorted(paths, key=path_level, reverse=True)` traversal and its "
          "`except ValueError as exc` arm are exercised, not replaced: %d of the "
          "%d cases are genuinely REORDERED by that sort and %d make a file's "
          "examination really fail, and the streams are bound to that "
          "enumeration order per mapping.md §2 'Enumeration order'."
          % (checked, len(boundary_cases()), N_FUZZ, SEED, reordering, checked,
             failing))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)",
                      "depth_reordered_cases": reordering,
                      "failing_cases": failing}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
