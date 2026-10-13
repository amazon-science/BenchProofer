#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14053 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`collect` /
              `upsert`, the order-preserving keep-last collapse) transliterated
              to Python over the real repo types, via the mapping.md row
              bijection `(name, hashed_name) <-> (fst, snd)`. There are NO
              A-tagged ops to leave alone (no axioms in this bundle).
  * ORACLE  — patch.diff's behaviour: the REAL patched
              `HashedFilesMixin.post_process` (gold patch applied at base_commit
              by the harness, G-RESOLVE), driven by a stub `_post_process` that
              emits the fuzzed observation stream. We compare the adjustable-file
              report (mapping.md §3.3) of `list(post_process(...))` against the
              shadow's `collect`.

They must agree on every input the real `_post_process` could produce. Exit 0
iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import re
import sys

SEED = 14053
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean collect/upsert, transliterated ------------
def shadow_collect(events):
    """`collect events` = events.foldl collectStep [] transliterated.

    Order-preserving keep-last upsert keyed by `name` (Obs.fst). Returns the
    report as a list of (name, hashed_name) in first-encounter order with the
    last observed hashed_name -- the adjustable-file report the patched
    post_process yields at the end."""
    order = []
    last = {}
    for name, hashed_name in events:
        if name not in last:
            order.append(name)
        last[name] = hashed_name
    return [(name, last[name]) for name in order]


# --- the oracle: the REAL patched HashedFilesMixin.post_process --------------
def _make_storage(passes):
    """Instantiate the real (patched) HashedFilesMixin subclass whose
    `_post_process` replays `passes` (one list of 4-tuples per invocation).

    The harness has applied patch.diff, so the imported `post_process` IS the
    gold post-patch generator. We override only `_post_process` (unchanged by
    the patch, mapping.md §3.1) to inject the fuzzed stream deterministically."""
    from django.contrib.staticfiles.storage import HashedFilesMixin

    class _Probe(HashedFilesMixin):
        def __init__(self, passes):
            # Replicate HashedFilesMixin.__init__'s pattern compilation without
            # touching the FileSystemStorage MRO (no settings needed).
            self._passes = passes
            self._i = 0
            self._patterns = {}
            self.hashed_files = {}
            for extension, patterns in self.patterns:
                for pattern in patterns:
                    if isinstance(pattern, (tuple, list)):
                        pattern, template = pattern
                    else:
                        template = self.default_template
                    compiled = re.compile(pattern, re.IGNORECASE)
                    self._patterns.setdefault(extension, []).append((compiled, template))

        def _post_process(self, paths, adjustable_paths, hashed_files):
            ps = self._passes[self._i] if self._i < len(self._passes) else []
            self._i += 1
            for tup in ps:
                yield tup

    return _Probe(passes)


def oracle_report(passes, all_names, adjustable):
    """Run the real patched post_process and project out the adjustable-file
    report (mapping.md §3.3): the (name, hashed_name) pairs it yields for the
    adjustable paths, in yield order."""
    paths = {n: (None, n) for n in all_names}
    storage = _make_storage(passes)
    yielded = list(storage.post_process(paths))
    # adjustable-file report = yielded records whose name is adjustable and not
    # an exception record (post-patch yields these once, at the end).
    return [(name, hashed_name)
            for (name, hashed_name, processed) in yielded
            if name in adjustable and not isinstance(processed, Exception)]


# --- fuzzing: stream shapes the real _post_process can produce ----------------
def _consumed_events(passes, adj_names, max_passes):
    """The adjustable observation stream the real patched post_process actually
    *consumes* and collapses, mirroring its consumption + break logic exactly:

      - the initial pass: collect adjustable, non-exception rows (exceptions on
        adjustable files are yielded immediately, not collapsed -- the patch's
        `isinstance(processed, Exception)` guard lives only in this loop);
      - then for i in range(max_passes): consume the next pass, collect ALL its
        adjustable rows, set substitutions from its subst flags, and break after
        the first pass with no substitutions.

    Exceptions are confined to the initial pass by the fuzzer (mapping.md §3.3),
    so the later-pass collapse never sees a non-(name, hashed_name) value. This
    is exactly the stream the model `collect` claims to dedup; the shadow runs
    over it and must equal the oracle's adjustable report."""
    adj = set(adj_names)
    events = []
    # initial pass (passes[0]): exception/non-adjustable handled separately
    for (name, hn, processed, _subst) in (passes[0] if passes else []):
        if name in adj and not isinstance(processed, Exception):
            events.append((name, hn))
    # adjustable passes with early break
    for i in range(max_passes):
        idx = 1 + i
        ps = passes[idx] if idx < len(passes) else []
        substitutions = False
        for (name, hn, _processed, subst) in ps:
            if name in adj:
                events.append((name, hn))
            substitutions = substitutions or subst
        if not substitutions:
            break
    return events


def _gen_case(rng):
    """One fuzzed scenario. Returns (passes, all_names, adjustable, events).

    `passes` is what the stub _post_process replays. We include non-adjustable
    files (yielded immediately in the initial pass) and the occasional exception
    record on an adjustable file in the INITIAL pass (yielded immediately) to
    exercise the real post_process's other legs -- none of which may appear in
    the adjustable report. `events` is computed by `_consumed_events` so it
    matches exactly what the real generator consumes (incl. its early break)."""
    nkeys = rng.randint(0, 6)
    adj_names = ["f%d.css" % j for j in range(nkeys)]
    non_adj = ["n%d.png" % j for j in range(rng.randint(0, 3))]
    all_names = adj_names + non_adj
    hashes = ["h%d" % j for j in range(rng.randint(1, 6))]
    max_passes = HashedFilesMixin_max_passes()

    def mk_pass(subst, allow_nonadj, allow_exc):
        m = rng.randint(0, 6)
        rows = []
        for _ in range(m):
            if allow_nonadj and non_adj and rng.random() < 0.25:
                name = rng.choice(non_adj)
            elif adj_names:
                name = rng.choice(adj_names)
            elif all_names:
                name = rng.choice(all_names)
            else:
                continue
            hn = rng.choice(hashes)
            # occasional exception on an adjustable file -- only in the initial
            # pass, where the patch yields it immediately (mapping.md §3.3).
            if allow_exc and name in adj_names and rng.random() < 0.05:
                rows.append((name, None, ValueError("boom"), False))
            else:
                rows.append((name, hn, True, subst))
        return rows

    # initial pass: non-adjustable files + possible adjustable exceptions
    p0 = mk_pass(subst=False, allow_nonadj=True, allow_exc=True)
    # adjustable passes: only adjustable files, no exceptions
    k = rng.randint(0, 6)
    later = [mk_pass(subst=True, allow_nonadj=False, allow_exc=False)
             for _ in range(k)]
    # occasionally force an early no-substitution pass to exercise the break
    if later and rng.random() < 0.3:
        cut = rng.randrange(len(later))
        later[cut] = [r[:3] + (False,) for r in later[cut]]  # subst -> False
    passes = [p0] + later
    events = _consumed_events(passes, adj_names, max_passes)
    return passes, all_names, set(adj_names), events


def HashedFilesMixin_max_passes():
    from django.contrib.staticfiles.storage import HashedFilesMixin
    return HashedFilesMixin.max_post_process_passes


def _boundary_cases():
    """Deterministic boundary scenarios (plan §4.1 step 4)."""
    cases = []
    # empty stream
    cases.append(([[]], [], set(), []))
    # single adjustable file, single pass
    cases.append(([[("a.css", "h1", True, False)]], ["a.css"], {"a.css"},
                  [("a.css", "h1")]))
    # same file across 3 passes, hash changes then stabilizes -> reported once,
    # last hash
    cases.append((
        [[("a.css", "h1", True, False)],
         [("a.css", "h2", True, True)],
         [("a.css", "h2", False, False)]],
        ["a.css"], {"a.css"}, [("a.css", "h1"), ("a.css", "h2"), ("a.css", "h2")]))
    # two files, interleaved, first-encounter order preserved
    cases.append((
        [[("a.css", "h1", True, False), ("b.css", "h2", True, False)],
         [("b.css", "h3", True, True), ("a.css", "h4", True, True)]],
        ["a.css", "b.css"], {"a.css", "b.css"},
        [("a.css", "h1"), ("b.css", "h2"), ("b.css", "h3"), ("a.css", "h4")]))
    # non-adjustable file present (must not enter the adjustable report)
    cases.append((
        [[("n0.png", "p1", True, False), ("a.css", "h1", True, False)],
         [("a.css", "h2", True, True)]],
        ["a.css", "n0.png"], {"a.css"},
        [("a.css", "h1"), ("a.css", "h2")]))
    # exception on an adjustable file (yielded immediately, not collapsed)
    cases.append((
        [[("a.css", None, ValueError("x"), False), ("b.css", "h1", True, False)]],
        ["a.css", "b.css"], {"a.css", "b.css"},
        [("b.css", "h1")]))
    return cases


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def check(passes, all_names, adjustable, events):
        nonlocal count
        count += 1
        shadow = shadow_collect(events)
        oracle = oracle_report(passes, all_names, adjustable)
        if shadow != oracle:
            disagreements.append((events, shadow, oracle))

    for case in _boundary_cases():
        check(*case)

    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        check(*_gen_case(rng))

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for ev, sh, orc in disagreements:
            print("  events=%r shadow=%r oracle=%r" % (ev, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reportCollected (collect/upsert) agrees with "
          "the real patched post_process adjustable-file report on %d inputs "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
