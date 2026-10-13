#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14053.

The changed reporting operation is modelled DEEPLY in model.py (the
front-recursive folds `first_pass_ids` / `adj_ids` / `failing_adj_count` /
`reported` over the file-id / adjustable-flag / failing-flag streams, and the
matching loop in `collect_reports`), NOT behind a consumed axiom. There is no
`@ContractOnly` axiom and no unchanged callee to axiomatize. G-AX therefore
validates that deep model against the REAL repository function it abstracts --
`HashedFilesMixin.post_process` -- by running the real (patched) generator and
asserting the sequence of file `name`s it yields equals the deep model
`reported(ids, adj, err)`: the FIRST-PASS segment (every plain file, plus every
adjustable file whose examination fails, once each, in enumeration order) then
the SETTLED segment (every adjustable file, once each, same order).

Method (no Django install, no filesystem, no real storage required): we load the
REAL `post_process` AND the REAL `_post_process` straight out of the patched
module (`django/contrib/staticfiles/storage.py`) at the repository root and
compile them standalone with a controlled global namespace, then drive them with
a stub `self` that replaces ONLY the per-file storage I/O
(`open`/`_save`/`exists`/`delete`/`hashed_name`/`clean_name`/`hash_key`/
`url_converter`). We then assert, over boundary + exhaustive small + randomized
fuzz file collections, WITH AND WITHOUT failing files, that:

  (1) the `name`s the real generator yields back to `collect()` are exactly the
      deep model's `reported(ids, adj, err)`;
  (2) their count is `len(ids) + failing_adj_count(ids, adj, err)` -- so a file
      is reported once for a settled outcome (the F2P property
      `assertCountEqual(post_processed, set(post_processed))`) and a failing file
      gets one report of its own on top of it;
  (3) on any collection carrying a failure, the failure report PRECEDES that
      file's settled report, so `collect()` re-raises rather than recording the
      file as successfully post-processed -- the property the PASS_TO_PASS test
      'post_processing indicates the origin of the error when it fails' asserts.

Why the REAL `_post_process` and MIXED-DEPTH names (a corrected blind spot): the
deep model's postcondition constrains the ORDER names are reported in, and that
order comes from `_post_process`'s `sorted(paths, key=path_level, reverse=True)`
traversal (`storage.py:263-267`) — deepest-directory-first, pre-existing at
base_commit and untouched by the gold patch. An earlier revision of this check
supplied its OWN `_post_process` doing `for name in paths` with no sort, and
drew all its file names from same-depth pools ('a','b','c' / 'f0'..'f5' /
'file_0'..), on which that sort is a provable no-op. It therefore replaced and
then could not observe the very ordering it asserted, and passed while the real
callee's report order diverged. This revision runs the real traversal over
mixed-depth names, binds the model streams to the routine's ENUMERATION order
(`enumeration_order(...)`, mapping.md §2 'Enumeration order'), and asserts via
`_assert_suite_exercises_depth_sort()` that the suite contains collections the
sort genuinely reorders. The failing arm gets the same treatment: the failure is
produced by the REAL `except ValueError as exc:` site inside `_post_process`
(`storage.py:300-301`), never fabricated, and
`_assert_suite_exercises_failures()` refuses to pass a suite in which no
collection actually reaches that site.

Domain scope. The deep model covers the CONVERGENT domain, failing examinations
INCLUDED: `err[k]` is the carrier for `isinstance(processed, Exception)`, so the
failure arm is IN-domain and checks (1)-(3) above apply to it. (An earlier
revision placed that arm OUT of domain and asserted it DIVERGED from the model,
justified by `collect()` raising before recording. That covered only the F2P
observable; it is not sound for the failure-path PASS_TO_PASS observable, which
asserts that `collect()` DOES raise — see mapping.md §2 'Domain'.) ONE arm remains
outside: the `('All', None, RuntimeError(...))` non-convergence report
(`storage.py:253-254`), whose `'All'` is not a file identity and which the gold
patch does not touch. We exercise it and assert it emits the sentinel and makes
the real `collect()` (`collectstatic.py:129-134`) re-raise.

Imports: the standard library only. Exit 0 iff every observation matches the
model on the modelled domain (failures included) AND the one out-of-domain arm is
confirmed to abort the caller.
"""
import ast
import itertools
import os
import random
import re
import sys
import textwrap
from io import BytesIO as _BytesIO


# --- locate and load the REAL post_process from the patched module -----------

def _find_storage_source():
    """Path to django/contrib/staticfiles/storage.py for the repo this check
    runs against (the patched module). In the G-AX container the repo is at
    /testbed; also probe the importable package and the cwd so it runs on the
    host."""
    rel = 'django/contrib/staticfiles/storage.py'
    candidates = []
    env_root = os.environ.get('REPO_ROOT')
    if env_root:
        candidates.append(os.path.join(env_root, rel))
    candidates.append('/testbed/' + rel)
    try:
        import django  # noqa: F401  (only to locate the installed package dir)
        candidates.append(os.path.join(os.path.dirname(django.__file__),
                                       'contrib/staticfiles/storage.py'))
    except Exception:
        pass
    candidates.append(os.path.join(os.getcwd(), rel))
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    raise RuntimeError("could not locate %s; set REPO_ROOT to the repo root" % rel)


def _load_real_functions():
    """Extract the REAL `post_process` AND the REAL `_post_process` from the
    patched module and compile them into standalone functions with a controlled
    global namespace (no package import).

    Loading `_post_process` too is essential, not incidental: the deep model's
    postcondition constrains the ORDER in which names are reported, and that
    order is produced by `_post_process`'s
    `sorted(paths, key=path_level, reverse=True)` traversal
    (`storage.py:262-267`). Supplying our own `_post_process` would replace the
    very behaviour whose faithfulness this check claims to validate, so the
    ordering could not be refuted. We therefore run the real traversal and stub
    only the per-file storage I/O it calls."""
    path = _find_storage_source()
    src = open(path).read()
    mod = ast.parse(src)
    found = {}
    for node in ast.walk(mod):
        if isinstance(node, ast.FunctionDef) and node.name in (
                'post_process', '_post_process') and node.name not in found:
            found[node.name] = node
    for want in ('post_process', '_post_process'):
        if want not in found:
            raise RuntimeError("%s not found in %s" % (want, path))
    # Controlled globals: matches_patterns and isinstance are ours; `os` is the
    # real module (`_post_process` uses os.sep in its sort key); ContentFile is
    # a minimal stand-in; everything else the bodies reference lives on `self`.
    ns = {
        'matches_patterns': _matches_patterns,
        'isinstance': isinstance,
        'range': range,
        'len': len,
        'sorted': sorted,
        'RuntimeError': RuntimeError,
        'ValueError': ValueError,
        'os': os,
        'ContentFile': _ContentFile,
    }
    for name, node in found.items():
        exec(compile(textwrap.dedent(ast.get_source_segment(src, node)),
                     path, 'exec'), ns)
    return ns['post_process'], ns['_post_process']


class _ContentFile:
    """Minimal stand-in for django.core.files.base.ContentFile: `_post_process`
    wraps the (possibly rewritten) content in one before saving it."""

    def __init__(self, content):
        self.content = content

    def read(self):
        return self.content

    def seek(self, n):
        pass


# `matches_patterns(path, patterns)` -- the real one tests fnmatch against the
# storage's _patterns. We encode adjustability directly: a path is adjustable
# iff it is a member of the `patterns` set we hand the stub self as `_patterns`.
def _matches_patterns(path, patterns):
    return path in patterns


# --- model.py deep-model reference (kept in lock-step with model.py) ---------

def m_first_pass_ids(ids, adj, err):
    # model.py `first_pass_ids`: reported while the FIRST pass runs -- not
    # adjustable, OR examination fails (a failure is handed over as the pass
    # reaches the file, adjustable or not).
    return [i for i, a, e in zip(ids, adj, err) if a == 0 or e != 0]


def m_adj_ids(ids, adj):
    return [i for i, a in zip(ids, adj) if a != 0]


def m_failing_adj_count(ids, adj, err):
    # model.py `failing_adj_count`: files reported in BOTH segments.
    return sum(1 for a, e in zip(adj, err) if a != 0 and e != 0)


def m_reported(ids, adj, err):
    # model.py `reported`: first-pass segment then settled segment
    return m_first_pass_ids(ids, adj, err) + m_adj_ids(ids, adj)


# --- stub `self` so the REAL post_process runs without storage --------------

class _StubStorage:
    """Minimal stand-in carrying exactly what the post_process /_post_process
    bodies read. The REAL `_post_process` is bound onto this class (see below),
    so its depth-sorted traversal is exercised, not replaced; only storage I/O
    is stubbed.

    By default every file's `processed` is a non-Exception value and the
    substitution loop converges (the hashed name settles, so
    `old_hashed_name == hashed_name` and the loop breaks). Two optional knobs
    drive the other two report arms:
      * `error_names`  -- these files carry content whose rewrite raises, so the
                          real `except ValueError as exc` arm fires and reports
                          an `Exception` as `processed`. This arm is IN the
                          modelled domain: the `err` stream is its carrier
                          (mapping.md §2 'Domain: the failure arm is IN').
      * `never_converge` -- adjustable files keep substituting forever, so the
                          repeat loop exhausts max_post_process_passes and the
                          `('All', None, RuntimeError(...))` arm fires. That arm
                          is the one remaining OUT-OF-DOMAIN case (D3)."""

    keep_intermediate_files = False

    def __init__(self, adjustable_names, max_passes,
                 error_names=frozenset(), never_converge=False,
                 settle_calls=1):
        # `_patterns` has the real {extension: [(pattern, template)]} shape: its
        # KEYS are consulted through matches_patterns (exact membership, since
        # our names carry no glob metachars) and its .items() by the adjustable
        # rewrite loop. Each key carries one real url(...) pattern so that an
        # errored file's content actually reaches url_converter (which raises
        # ValueError -> the real Exception arm); for non-errored files the
        # substitution is content-preserving.
        _url_pat = re.compile(r"""url\(['"]{0,1}\s*(.*?)["']{0,1}\)""")
        self._patterns = {name: [(_url_pat, 'url("%s")')]
                          for name in sorted(adjustable_names)}
        self.max_post_process_passes = max_passes
        self.hashed_files = {}
        self._error_names = set(error_names)
        self._never_converge = never_converge
        self._settle_calls = settle_calls
        self._hash_calls = {}

    # `_post_process` is NOT defined here: the REAL one (loaded from the patched
    # module, with its `sorted(paths, key=path_level, reverse=True)` traversal)
    # is bound onto this class below. Only the storage I/O it calls is stubbed.

    def open(self, path):
        # An errored file gets content carrying a url(...) reference, so the
        # real rewrite loop invokes our url_converter, which raises ValueError
        # -- reproducing the real `yield name, None, exc, False` arm faithfully
        # (`storage.py`, the `except ValueError as exc` inside _post_process)
        # instead of fabricating the Exception from a stub helper.
        if path in self._error_names:
            return _BytesIO(b'a { background: url("dep.png"); }')
        return _BytesIO(b'content of ' + path.encode())

    def exists(self, name):
        return False

    def delete(self, name):
        pass

    def _save(self, name, content):
        return name

    def clean_name(self, name):
        return name

    def hash_key(self, name):
        return name

    def hashed_name(self, name, content=None, filename=None):
        """Deterministic per-file hash that SETTLES: after `_settle_calls` calls
        for a given file the value stops changing, so the real convergence test
        `old_hashed_name == hashed_name` holds and the repeat loop breaks
        (in-domain). `_never_converge` keeps it changing forever, driving the
        out-of-domain `('All', None, RuntimeError(...))` arm."""
        k = self._hash_calls.get(name, 0)
        self._hash_calls[name] = k + 1
        if self._never_converge and name in self._patterns:
            return '%s.%d.hash' % (name, k)
        return '%s.%d.hash' % (name, min(k, self._settle_calls))

    def url_converter(self, name, hashed_files, template=None):
        """The real one returns the regex-substitution callable applied to an
        adjustable file's content. For a file in `_error_names` it raises
        ValueError, which the real `_post_process` catches and reports as
        `yield name, None, exc, False` -- the out-of-domain Exception arm,
        produced by the REAL code path rather than fabricated by a stub."""
        def converter(matchobj):
            if name in self._error_names:
                raise ValueError('post-processing %r failed' % name)
            return matchobj.group(0)
        return converter

    def update(self, *a, **k):  # self.hashed_files.update(...) target is a dict
        pass


REAL_POST_PROCESS, REAL__POST_PROCESS = _load_real_functions()

# Bind the REAL `_post_process` onto the stub storage: `post_process` calls
# `self._post_process(...)`, so this is what makes the real depth-sorted
# traversal (`sorted(paths, key=path_level, reverse=True)`) the one under test.
_StubStorage._post_process = REAL__POST_PROCESS


def path_level(name):
    """The real `_post_process`'s sort key (`storage.py:262-267`)."""
    return len(name.split(os.sep))


def enumeration_order(file_names):
    """The order the REAL `_post_process` visits files: deepest-directory-first,
    Python's stable sort breaking ties by `paths` iteration order. This is the
    order the model's `ids`/`adj` streams are bound to (mapping.md §2
    'Enumeration order'); it PRE-EXISTS at base_commit and the gold patch does
    not touch it."""
    return sorted(file_names, key=path_level, reverse=True)


def real_yielded_triples(file_names, adjustable_names, max_passes=5,
                         error_names=frozenset(), never_converge=False,
                         settle_calls=1):
    """Run the REAL post_process (over the REAL `_post_process`) and return the
    list of (name, hashed_name, processed) triples it yields back to collect()."""
    storage = _StubStorage(adjustable_names, max_passes,
                           error_names=error_names,
                           never_converge=never_converge,
                           settle_calls=settle_calls)
    paths = {name: (storage, name) for name in file_names}
    out = []
    for triple in REAL_POST_PROCESS(storage, paths, dry_run=False):
        name, hashed_name, processed = triple
        out.append((name, hashed_name, processed))
    return out


def real_yielded_names(file_names, adjustable_names, max_passes=5,
                       error_names=frozenset()):
    """Run the REAL post_process over a collection of files (some adjustable,
    some possibly failing) and return the list of `name`s it yields back to
    collect()."""
    return [t[0] for t in real_yielded_triples(file_names, adjustable_names,
                                               max_passes=max_passes,
                                               error_names=error_names)]


def reachable_failures(file_names, adjustable_set, error_names):
    """The files whose examination ACTUALLY fails in the real code path.

    Only an adjustable file can fail: the substitution loop that can raise lives
    inside `if name in adjustable_paths:` (`storage.py:291`), so `url_converter`
    is never invoked for a plain file. This is the real code path's own guard,
    not a narrowing of the check -- mapping.md §2 'Unreachable flag
    combination'."""
    return set(file_names) & set(adjustable_set) & set(error_names)


def model_streams(file_names, adjustable_set, error_names=frozenset()):
    """The model's three streams for a collection, in the routine's ENUMERATION
    order -- the binding mapping.md §2 'Enumeration order' states and the order
    the postcondition is written against. (NOT raw `paths` iteration order:
    `_post_process` traverses sorted(paths, key=path_level, reverse=True).)"""
    ids = enumeration_order(file_names)
    adj = [1 if n in adjustable_set else 0 for n in ids]
    failing = reachable_failures(file_names, adjustable_set, error_names)
    err = [1 if n in failing else 0 for n in ids]
    return ids, adj, err


# --- the checks --------------------------------------------------------------

def check_collection(file_names, adjustable_set, error_names=frozenset()):
    """Assert the real post_process yields each file's name exactly the way the
    deep model `reported` says: every file once for its settled outcome, plus one
    extra report for every file whose examination fails, handed over BEFORE that
    file's settled report."""
    ids, adj, err = model_streams(file_names, adjustable_set, error_names)
    expected = m_reported(ids, adj, err)

    triples = real_yielded_triples(file_names, adjustable_set,
                                   error_names=error_names)
    observed = [t[0] for t in triples]

    assert observed == expected, (
        "deep model unsound: files=%r adjustable=%r errors=%r\n  real "
        "post_process yielded %r\n  model `reported`   %r" %
        (file_names, sorted(adjustable_set), sorted(error_names),
         observed, expected))

    # (2) the count postcondition: #files + one per failing adjustable file.
    n_failing = m_failing_adj_count(ids, adj, err)
    assert len(observed) == len(file_names) + n_failing, (
        "report count wrong: files=%r adjustable=%r errors=%r yielded=%r "
        "expected %d+%d" % (file_names, sorted(adjustable_set),
                            sorted(error_names), observed,
                            len(file_names), n_failing))
    # ...and equivalently: every name once, except a failing file twice.
    for n in file_names:
        want = 2 if n in reachable_failures(file_names, adjustable_set,
                                            error_names) else 1
        assert observed.count(n) == want, (
            "multiplicity wrong for %r (want %d): files=%r adjustable=%r "
            "errors=%r yielded=%r" % (n, want, file_names,
                                      sorted(adjustable_set),
                                      sorted(error_names), observed))

    # (3) a failure is handed over BEFORE the same file's settled report, so
    #     collect() re-raises instead of recording the file as post-processed.
    for n in reachable_failures(file_names, adjustable_set, error_names):
        exc_at = [k for k, t in enumerate(triples)
                  if t[0] == n and isinstance(t[2], Exception)]
        settled_at = [k for k, t in enumerate(triples)
                      if t[0] == n and not isinstance(t[2], Exception)]
        assert exc_at and settled_at, (
            "expected both a failure report and a settled report for %r: "
            "files=%r adjustable=%r errors=%r triples=%r" %
            (n, file_names, sorted(adjustable_set), sorted(error_names),
             triples))
        assert min(exc_at) < min(settled_at), (
            "failure report for %r does not precede its settled report "
            "(collect() would record it as post-processed and only then "
            "raise): files=%r triples=%r" % (n, file_names, triples))

    # The precondition also admits err set on a PLAIN file, which the real code
    # path cannot produce. Assert the model's value there coincides with err
    # cleared, so the spec claims nothing about an unreachable state
    # (mapping.md §2 'Unreachable flag combination').
    raw_err = [1 if n in set(error_names) else 0 for n in ids]
    assert m_reported(ids, adj, raw_err) == expected, (
        "model is sensitive to the unreachable plain+failing flag combination: "
        "files=%r adjustable=%r errors=%r" %
        (file_names, sorted(adjustable_set), sorted(error_names)))


# --- the caller's own consumption rule, and the failure arm IN-domain --------

class _CollectAborted(Exception):
    """collect() re-raised a post-processing Exception (collectstatic.py:134)."""


def collect_post_processed(triples):
    """Faithful model of how collectstatic's collect() consumes post_process's
    output stream into stats['post_processed'] (collectstatic.py:128-140):
      * on the FIRST (name, _, processed) with isinstance(processed, Exception)
        it writes "Post-processing '%s' failed!" and `raise processed` -> we
        raise _CollectAborted, recording nothing more;
      * else if `processed` is truthy it appends `name` to post_processed.
    Returns the list of names that reach stats['post_processed']."""
    post_processed = []
    for name, _hashed, processed in triples:
        if isinstance(processed, Exception):
            raise _CollectAborted(name)
        if processed:
            post_processed.append(name)
    return post_processed


def check_failure_arm_in_domain(file_names, adjustable_set, error_names):
    """The `isinstance(processed, Exception)` first-pass arm is IN the modelled
    domain: `err` is its carrier. On top of check_collection's (1)-(3) we assert
    the caller-visible consequence, which is what the failure-path PASS_TO_PASS
    test observes:
    (a) collect() ABORTS (re-raises) exactly when some file's examination really
        fails -- and does not abort when none does; and
    (b) it aborts NAMING that file, and WITHOUT having recorded it as
        successfully post-processed. A routine that withheld the failure would
        fail both halves: collect() would not raise at all and would record the
        file's settled report instead."""
    # (1)-(3): the reported sequence, count and failure-before-settled ordering.
    check_collection(file_names, adjustable_set, error_names)

    triples = real_yielded_triples(file_names, adjustable_set,
                                   error_names=error_names)
    failing = reachable_failures(file_names, adjustable_set, error_names)
    ids, adj, err = model_streams(file_names, adjustable_set, error_names)

    try:
        recorded = collect_post_processed(triples)
        aborted_on = None
    except _CollectAborted as exc:
        recorded = None
        aborted_on = exc.args[0]

    if failing:
        assert aborted_on is not None, (
            "expected collect() to re-raise on a failing examination: files=%r "
            "adj=%r errors=%r triples=%r" %
            (file_names, sorted(adjustable_set), sorted(error_names), triples))
        # (b) it aborts on a file that really failed, and the model puts that
        #     name in the FIRST-PASS segment -- which is the same statement.
        assert aborted_on in failing, (
            "collect() aborted on %r, which is not a failing file: files=%r "
            "errors=%r" % (aborted_on, file_names, sorted(error_names)))
        assert aborted_on in m_first_pass_ids(ids, adj, err), (
            "collect() aborted on %r but the model does not report it in the "
            "first-pass segment: files=%r adj=%r errors=%r" %
            (aborted_on, file_names, sorted(adjustable_set),
             sorted(error_names)))
    else:
        assert aborted_on is None, (
            "no file fails but collect() raised: files=%r adj=%r errors=%r "
            "triples=%r" %
            (file_names, sorted(adjustable_set), sorted(error_names), triples))
        # with nothing failing, every file is recorded exactly once
        assert sorted(recorded) == sorted(file_names), (
            "recorded set wrong with no failure: files=%r recorded=%r" %
            (file_names, recorded))


def check_nonconvergence_arm_out_of_domain(file_names, adjustable_set):
    """Forcing the substitution loop to never converge exercises the
    `('All', None, RuntimeError(...))` arm, which is OUTSIDE the modelled
    carrier: 'All' is not a file identity, so no `ids` entry corresponds to it.
    The arm is nonetheless observable to the caller — the PASS_TO_PASS test
    `test_import_loop` asserts collect() raises RuntimeError('Max post-process
    passes exceeded') and writes "Post-processing 'All' failed!". The arm is
    UNTOUCHED CONTEXT in the gold patch, so it is preserved by construction under
    any refinement of the map (refinement.md 'Scope actually claimed': no licence
    to alter it); this check pins that preservation EXECUTABLY rather than by
    prose alone. We assert:
    (a) the RAW yielded stream contains the sentinel 'All' report (so it is not
        the deep model `reported`, which never emits it);
    (b) the sentinel report PRECEDES every settled report, which is where the
        gold routine places it — between the repeat-pass loop and the closing
        `yield from processed_adjustable_paths.values()` (`storage.py:253-260`);
    (c) collect() ABORTS (re-raises the RuntimeError) on that report, naming
        'All', so the settled reports that follow it never reach
        stats['post_processed'];
    (d) the file reports emitted BEFORE the sentinel are exactly the model's
        first-pass segment — i.e. the arm is additive: it inserts one sentinel,
        it does not disturb the modelled part of the stream."""
    # need at least one adjustable file for the repeat loop to keep substituting
    if not (set(file_names) & set(adjustable_set)):
        return
    triples = real_yielded_triples(file_names, adjustable_set,
                                   max_passes=3, never_converge=True)
    raw_names = [t[0] for t in triples]
    ids, adj, err = model_streams(file_names, adjustable_set)
    model = m_reported(ids, adj, err)
    assert 'All' in raw_names, (
        "expected non-convergence 'All' report: files=%r adj=%r raw=%r"
        % (file_names, sorted(adjustable_set), raw_names))
    assert raw_names != model, (
        "non-convergence stream expected to diverge from model: raw=%r model=%r"
        % (raw_names, model))
    # (b)+(d): the sentinel sits exactly between the first-pass segment and the
    #     settled segment.
    at = raw_names.index('All')
    assert raw_names[:at] == m_first_pass_ids(ids, adj, err), (
        "non-convergence arm disturbed the modelled first-pass segment: "
        "before-sentinel=%r first_pass=%r" %
        (raw_names[:at], m_first_pass_ids(ids, adj, err)))
    assert raw_names[at + 1:] == m_adj_ids(ids, adj), (
        "non-convergence arm disturbed the modelled settled segment: "
        "after-sentinel=%r settled=%r" %
        (raw_names[at + 1:], m_adj_ids(ids, adj)))
    # (c): the caller aborts on the sentinel, so nothing after it is recorded.
    try:
        collect_post_processed(triples)
        aborted_on = None
    except _CollectAborted as exc:
        aborted_on = exc.args[0]
    assert aborted_on == 'All', (
        "expected collect() to re-raise on the 'All' report: files=%r adj=%r "
        "aborted_on=%r triples=%r" %
        (file_names, sorted(adjustable_set), aborted_on, triples))


def _mixed_depth_names(n, rng=None):
    """`n` distinct names at MIXED directory depths, so the real
    `sorted(paths, key=path_level, reverse=True)` traversal genuinely permutes
    the collection. A same-depth pool would make that sort a no-op and the
    reported ORDER unobservable (the blind spot this check previously had)."""
    out = []
    for k in range(n):
        depth = (rng.randint(1, 4) if rng is not None else 1 + (k % 4))
        prefix = ''.join('d%d/' % j for j in range(depth - 1))
        out.append('%sfile_%d.css' % (prefix, k))
    return out


def _assert_suite_exercises_depth_sort(collections):
    """Refuse to pass on a suite that cannot observe the traversal order: at
    least some collection must be genuinely REORDERED by the real depth sort."""
    reordered = sum(1 for files in collections
                    if enumeration_order(files) != list(files))
    assert reordered > 0, (
        "suite does not exercise the real depth-sorted traversal: none of the "
        "%d collections is reordered by sorted(paths, key=path_level, "
        "reverse=True), so an ordering postcondition cannot be refuted"
        % len(collections))
    return reordered


def _assert_suite_exercises_failures(cases):
    """Refuse to pass on a failure suite that never actually fails. `cases` are
    (files, adjustable_set, error_names) triples. For each we run the REAL
    routine and require that some case genuinely reaches the real `ValueError`
    site -- i.e. the yielded stream really does carry an `Exception` `processed`
    (`storage.py:300-301`), not merely that we named some `error_names`. Naming a
    PLAIN file in `error_names` reaches nothing (mapping.md §2 'Unreachable flag
    combination'), so without this guard a suite of only plain-error cases would
    pass while testing none of the failure clause."""
    with_failure = 0
    for files, adjset, errs in cases:
        triples = real_yielded_triples(files, adjset, error_names=errs)
        if any(isinstance(t[2], Exception) for t in triples):
            with_failure += 1
    assert with_failure > 0, (
        "failure suite is vacuous: none of the %d cases makes the real "
        "_post_process reach its `except ValueError as exc` arm, so the "
        "`err`-stream clause of the postcondition is never exercised"
        % len(cases))
    return with_failure


def main():
    # --- boundary collections ----------------------------------------------
    # Mixed depths throughout: ascending, descending, tied and single-depth,
    # so the real depth-first traversal is a genuine reordering in most cases.
    boundary = [
        ([], set()),
        (['a.css'], set()),                   # one plain file
        (['a.css'], {'a.css'}),               # one adjustable file
        (['a.css', 'd0/b.css'], set()),       # two plain, sort REORDERS
        (['a.css', 'b.css'], set()),          # two plain, sort is a no-op
        (['a.css', 'd0/b.css'], {'a.css', 'd0/b.css'}),        # two adjustable
        (['d0/d1/a.css', 'b.css', 'd0/c.css'], {'b.css'}),     # descending
        (['a.css', 'd0/b.css', 'd0/d1/c.css'], {'a.css', 'd0/d1/c.css'}),
        (['css/base.css', 'css/dashboard.css', 'img/logo.png'],
         {'css/base.css', 'css/dashboard.css'}),  # the issue's scenario
        (['d0/d1/d2/x.css', 'y.css', 'd0/z.css', 'd0/w.css'],
         {'d0/d1/d2/x.css', 'd0/z.css'}),     # deep + ties
    ]
    for files, adjset in boundary:
        check_collection(files, adjset)
    _assert_suite_exercises_depth_sort([f for f, _ in boundary])

    # --- exhaustive small: every adjustable-subset of up to 5 files ---------
    exhaustive = []
    for n in range(0, 6):
        files = _mixed_depth_names(n)
        exhaustive.append(files)
        for r in range(0, n + 1):
            for combo in itertools.combinations(files, r):
                check_collection(files, set(combo))
                # each adjustable-subset again with EVERY single file failing,
                # so the `err` clause is exercised across the whole small space
                for f in files:
                    check_collection(files, set(combo), {f})
    _assert_suite_exercises_depth_sort(exhaustive)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(14053)
    fuzz_reordered = 0
    fuzz_with_failure = 0
    for _ in range(20000):
        n = rng.randint(0, 16)
        files = _mixed_depth_names(n, rng)          # distinct names (keyed)
        adjset = {f for f in files if rng.random() < 0.5}
        # a third of the runs carry failing files (drawn independently of
        # adjustability, so plain-and-flagged unreachable bindings occur too)
        errs = ({f for f in files if rng.random() < 0.3}
                if rng.random() < 0.34 else set())
        check_collection(files, adjset, errs)
        if enumeration_order(files) != list(files):
            fuzz_reordered += 1
        if reachable_failures(files, adjset, errs):
            fuzz_with_failure += 1
    assert fuzz_reordered > 2000, (
        "fuzz does not exercise the depth sort: only %d of 20000 collections "
        "are reordered by it" % fuzz_reordered)
    assert fuzz_with_failure > 1000, (
        "fuzz does not exercise the failure arm: only %d of 20000 collections "
        "carry a file that really fails" % fuzz_with_failure)

    # --- the failure arm, IN-domain (the repaired clause) --------------------
    # `err` is a modelled carrier, so these assert EQUALITY with `reported`
    # (via check_collection) plus the caller-visible consequence: collect()
    # re-raises, naming the file, without recording it as post-processed.
    failure_cases = [
        (['css/base.css', 'css/dashboard.css', 'img/logo.png'],
         {'css/base.css', 'css/dashboard.css'}, {'css/base.css'}),
        (['a.css', 'd0/b.css', 'd0/d1/c.css'], {'a.css', 'd0/b.css'}, {'a.css'}),
        (['a.css', 'd0/b.css', 'c.css'], {'d0/b.css'}, {'d0/b.css'}),
        (['a.css'], {'a.css'}, {'a.css'}),          # the P2P fixture's shape
        (['a.css'], {'a.css'}, set()),              # same shape, nothing fails
        (['a.css'], set(), {'a.css'}),              # flagged but PLAIN: no fail
        (['a.css', 'd0/b.css'], {'a.css', 'd0/b.css'},
         {'a.css', 'd0/b.css'}),                    # every file fails
        (['d0/d1/a.css', 'b.css'], {'d0/d1/a.css'}, {'d0/d1/a.css'}),
    ]
    for files, adjset, errs in failure_cases:
        check_failure_arm_in_domain(files, adjset, errs)
    # fuzz the failure arm too
    fuzz_failure_cases = []
    for _ in range(2000):
        n = rng.randint(1, 12)
        files = _mixed_depth_names(n, rng)
        adjset = {f for f in files if rng.random() < 0.5}
        errs = {f for f in files if rng.random() < 0.3}
        fuzz_failure_cases.append((files, adjset, errs))
        check_failure_arm_in_domain(files, adjset, errs)
    # refuse a vacuous failure suite: some case must really raise ValueError
    _assert_suite_exercises_failures(failure_cases)
    _assert_suite_exercises_failures(fuzz_failure_cases)

    # --- the one remaining OUT-OF-DOMAIN arm (D3) ----------------------------
    # Non-convergence arm: substitutions never settle -> 'All' RuntimeError.
    nonconv_cases = [
        (['css/base.css', 'css/dashboard.css', 'img/logo.png'],
         {'css/base.css', 'css/dashboard.css'}),
        (['a.css', 'd0/b.css', 'd0/d1/c.css'], {'a.css', 'd0/d1/c.css'}),
        (['a.css'], {'a.css'}),
    ]
    for files, adjset in nonconv_cases:
        check_nonconvergence_arm_out_of_domain(files, adjset)
    for _ in range(2000):
        n = rng.randint(1, 12)
        files = _mixed_depth_names(n, rng)
        adjset = {f for f in files if rng.random() < 0.5}
        check_nonconvergence_arm_out_of_domain(files, adjset)

    print("G-AX OK: deep model `reported(ids, adj, err)` "
          "(first-pass segment ++ settled segment) == real "
          "HashedFilesMixin.post_process yielded names on %d boundary + "
          "exhaustive(files<=5, all adjustable-subsets x each single failure) + "
          "20000 fuzz collections, with length == len(ids) + "
          "failing_adj_count(ids, adj, err), per-file multiplicity 1 (2 for a "
          "file that really fails) and the failure report preceding that file's "
          "settled report; %d fuzz collections carry a real failure. The failure "
          "arm is IN domain: on %d+2000 failure cases collect() re-raises naming "
          "the failing file and never records it, and with nothing failing it "
          "does not raise at all. The one out-of-domain arm (non-convergence "
          "'All') is pinned as UNTOUCHED CONTEXT on %d+2000 cases: it inserts "
          "the sentinel exactly between the two modelled segments (both of which "
          "it leaves equal to the model), and collect() aborts on it naming "
          "'All' -- which is what the PASS_TO_PASS test test_import_loop reads."
          % (len(boundary), fuzz_with_failure, len(failure_cases),
             len(nonconv_cases)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
