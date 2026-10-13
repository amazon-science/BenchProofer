#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_postProcess
against the patch.diff behaviour (the post-patch `post_process` consumption).

The impl region is entirely R/I content (two `for` loops + an order-preserving
upsert + a final emission), so this runs a real fuzz. The modeled INPUT is the
record stream the unchanged inner processor `_post_process` yields: a first-pass
record list and a list of later-pass record lists (see mapping.md). Each record
also carries the per-pass flag saying that pass still had to rewrite a reference
inside that file — not part of the reported item, but what decides whether the run
continues and hence whether the allowance of passes ran out. There is no A-tagged
callee inside the orchestration, so every op is reproduced directly.

`shadow(...)` reproduces the Lean impl op-for-op. `patched(...)` is an
independent reconstruction of the POST-patch `post_process` body's consumption
logic (the gold patch.diff), written as a real Python GENERATOR so that the
observable it is fuzzed on is the one mapping.md claims: first pass yields
non-adjustable/error records and collects adjustable ones into an
insertion-ordered dict; later passes overwrite the dict and stop early on a pass
that rewrote nothing; if the allowance of passes instead ran out with the run still
rewriting, one extra error item is handed over; then the accumulated name mapping
is committed to the storage instance; then `yield from dict.values()`.

The compared value is therefore a PAIR — the items the caller has received before
the commit executes, and the items it receives after — recovered by draining the
generator one item at a time and watching a commit flag flip, which is exactly how
a real consumer (`collectstatic.collect`, which raises on the first exception item
and never resumes) observes it. `OutReport` in Solution.lean is that pair.

We assert zero disagreements over >=10^5 fuzzed record-stream inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14053          # pinned in mapping.md
N = 120_000           # >= 10^5


# A record is (name, hashed_name, processed, rewrote) where processed is either a
# bool (Except.ok) or the sentinel ("ERR", msg) (Except.error), and `rewrote` is
# the per-pass flag saying that pass still had to rewrite a reference inside the
# file. `rewrote` is NOT part of the reported item, but it decides whether the
# terminal item below belongs in the report, so it is carried on the record.
def is_error(rec):
    processed = rec[2]
    return isinstance(processed, tuple) and len(processed) == 2 and processed[0] == "ERR"


def to_item(rec):
    # the reported triple drops the per-pass flag
    return (rec[0], rec[1], rec[2])


# The extra item reported when the further passes end with the run still
# rewriting: it stands for no single source file and carries a signalled error.
ALLOWANCE_ITEM = ("All", None, ("ERR", "Max post-process passes exceeded."))


def upsert(pairs, key, val):
    """append-if-new, replace-in-place-if-present; preserves insertion order.
    `pairs` is a list of (key, item)."""
    for i, (k, _) in enumerate(pairs):
        if k == key:
            pairs[i] = (key, val)
            return
    pairs.append((key, val))


def shadow(adjustable, first_pass, later_passes):
    """R/I shadow of implementation_postProcess (op-for-op).

    Returns the `OutReport` pair (items handed over before the commit, items
    handed over after it)."""
    early = []
    collected = []          # list of (name, item) — the order-preserving dict
    for r in first_pass:
        name = r[0]
        if (name not in adjustable) or is_error(r):
            early = early + [to_item(r)]
        else:
            upsert(collected, name, to_item(r))
    unsettled = False
    for pass_recs in later_passes:
        # this pass's own flag replaces the previous pass's, so after the last
        # pass it says whether THAT pass was still rewriting
        unsettled = any(r[3] for r in pass_recs)
        for r in pass_recs:
            upsert(collected, r[0], to_item(r))
    return (early + ([ALLOWANCE_ITEM] if unsettled else []),
            [v for (_, v) in collected])


def patched_generator(adjustable, first_pass, later_passes, storage):
    """Independent reconstruction of the POST-patch post_process consumption
    (the gold patch.diff), as a generator, using a real Python dict
    (insertion-ordered). `storage` is a one-key dict standing in for the storage
    instance whose name mapping the invocation commits to."""
    adjustable_set = set(adjustable)
    processed_adjustable_paths = {}     # name -> (name, hashed_name, processed)
    hashed_files = {}
    # first pass
    for name, hashed_name, processed, _rewrote in first_pass:
        hashed_files[name] = hashed_name
        if name not in adjustable_set or is_error((name, hashed_name, processed)):
            yield (name, hashed_name, processed)
        else:
            processed_adjustable_paths[name] = (name, hashed_name, processed)
    # later passes: each pass recomputes its own rewriting flag from scratch, and
    # the run stops early on a pass that rewrote nothing (so `later_passes` is
    # exactly the passes that executed — see rand_case, which truncates it the
    # same way the real loop would).
    substitutions = False
    for pass_recs in later_passes:
        substitutions = False
        for name, hashed_name, processed, rewrote in pass_recs:
            hashed_files[name] = hashed_name
            processed_adjustable_paths[name] = (name, hashed_name, processed)
            substitutions = substitutions or rewrote
        if not substitutions:
            break
    # the allowance ran out with the run still rewriting: reported BEFORE the
    # commit, so a consumer that abandons the report on it has been handed it
    # while the shared mapping still holds its pre-call contents.
    if substitutions:
        yield ALLOWANCE_ITEM
    # the commit of the accumulated mapping to the shared instance
    storage["committed"] = True
    storage["hashed_files"].update(hashed_files)
    # yield from values()
    yield from processed_adjustable_paths.values()


def patched(adjustable, first_pass, later_passes):
    """Drain `patched_generator` one item at a time, splitting the item sequence
    at the instant the commit flag flips — the split a real incremental consumer
    observes. Returns the same `OutReport` pair shape as `shadow`."""
    storage = {"committed": False, "hashed_files": {}}
    gen = patched_generator(adjustable, first_pass, later_passes, storage)
    before, after = [], []
    for item in gen:
        # `storage["committed"]` is read at the moment the item is handed over,
        # i.e. before the generator is resumed, exactly as a consumer would.
        (after if storage["committed"] else before).append(item)
    return (before, after)


def rand_processed(rng):
    roll = rng.random()
    if roll < 0.15:
        return ("ERR", rng.choice(["ValueError", "boom", ""]))
    return rng.choice([True, False])


def rand_record(rng, names, rewrote=None):
    name = rng.choice(names)
    hashed = rng.choice([None] + [name + "." + h for h in ("aaa", "bbb", "ccc")])
    if rewrote is None:
        rewrote = rng.random() < 0.5
    return (name, hashed, rand_processed(rng), rewrote)


def rand_pass(rng, names, rewriting):
    """A single later pass. `rewriting` says whether this pass must report at
    least one rewritten reference (i.e. whether the run continues after it)."""
    n = rng.randint(0, 4)
    if rewriting:
        n = max(1, n)
    recs = [rand_record(rng, names, rewrote=False) for _ in range(n)]
    if rewriting:
        i = rng.randrange(len(recs))
        recs[i] = recs[i][:3] + (True,)
    return recs


def rand_case(rng):
    n_names = rng.randint(0, 5)
    names = ["f%d" % i for i in range(max(1, n_names))]
    # adjustable is an arbitrary subset of names
    adjustable = [nm for nm in names if rng.random() < 0.5]
    first_pass = [rand_record(rng, names) for _ in range(rng.randint(0, 6))]
    # `later_passes` is by construction the passes that EXECUTED (mapping.md), so
    # every pass but the last reported a rewrite — a pass that reports none ends
    # the run. Whether the LAST one reported a rewrite is free: it did iff the
    # allowance of passes ran out with the run still moving. Both endings are
    # generated, so the fuzz exercises the terminal item and its absence.
    n_passes = rng.randint(0, 4)
    last_rewriting = rng.random() < 0.5
    later_passes = [rand_pass(rng, names, rewriting=(i < n_passes - 1 or last_rewriting))
                    for i in range(n_passes)]
    return adjustable, first_pass, later_passes


def main() -> int:
    rng = random.Random(SEED)

    # Deterministic boundary cases first (incl. the F2P duplicate-yield scenario).
    fixed = [
        # empty
        ([], [], []),
        # the exact duplicate-report scenario: one adjustable file in the first
        # pass + a later pass that settles it
        (["a"], [("a", "a.111", True, False), ("b", "b.x", False, False)],
         [[("a", "a.222", True, False)]]),
        # adjustable file processed across several passes -> reported once, latest
        (["a"], [("a", "a.1", True, False)],
         [[("a", "a.2", True, True)], [("a", "a.3", True, False)]]),
        # non-adjustable yielded immediately
        (["a"], [("b", "b.1", True, False), ("c", "c.1", False, False)], []),
        # error on an adjustable file is yielded immediately (not collected)
        (["a"], [("a", None, ("ERR", "ValueError"), False)], []),
        # no later passes
        (["a", "b"], [("a", "a.1", True, False), ("b", "b.1", True, False)], []),
        # later pass introduces a brand-new adjustable name
        (["a", "z"], [("a", "a.1", True, False)], [[("z", "z.1", True, False)]]),
        # the allowance runs out with the run still rewriting: terminal item
        (["a"], [("a", "a.1", True, False)], [[("a", "a.2", True, True)]]),
        # ... and it is reported even when nothing was collected at all
        ([], [], [[("b", "b.1", True, True)]]),
        # a pass that reports nothing at all ends the run: no terminal item
        (["a"], [("a", "a.1", True, False)], [[]]),
        # several passes, all still rewriting to the very last one
        (["a"], [("a", "a.1", True, False)],
         [[("a", "a.2", True, True)], [("a", "a.3", True, True)]]),
    ]
    cases = fixed + [rand_case(rng) for _ in range(N)]

    disagreements = 0
    examples = []
    allowance_seen = 0
    for adjustable, first_pass, later_passes in cases:
        got = shadow(adjustable, first_pass, later_passes)
        want = patched(adjustable, first_pass, later_passes)
        if ALLOWANCE_ITEM in want[0] or ALLOWANCE_ITEM in want[1]:
            allowance_seen += 1
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((adjustable, first_pass, later_passes, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for a, fp, lp, g, w in examples:
            print(f"  adj={a} fp={fp} lp={lp}\n    shadow={g}\n    patched={w}")
        return 1

    # Discrimination control: the pair observable must be strictly finer than the
    # flat concatenation, otherwise `OutReport`'s second component is decoration.
    # `full_buffer` hands the caller nothing until every pass has ended and the
    # mapping is committed. It agrees with `patched` on the concatenation on every
    # input, and must disagree on the pair on at least one.
    def full_buffer(adjustable, first_pass, later_passes):
        before, after = shadow(adjustable, first_pass, later_passes)
        return ([], before + after)

    flat_agree = 0
    pair_split = 0
    for adjustable, first_pass, later_passes in cases:
        want = patched(adjustable, first_pass, later_passes)
        fb = full_buffer(adjustable, first_pass, later_passes)
        if fb[0] + fb[1] == want[0] + want[1]:
            flat_agree += 1
        if fb != want:
            pair_split += 1
    if flat_agree != len(cases):
        print(f"G-CONF FAIL: control broke on {len(cases) - flat_agree} inputs")
        return 1
    if pair_split == 0:
        print("G-CONF FAIL: pair observable separates nothing (vacuous)")
        return 1
    if allowance_seen == 0:
        print("G-CONF FAIL: the exhausted-allowance item was never exercised")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED}); "
          f"pair observable separates the full-buffer control on {pair_split} "
          f"of {len(cases)} inputs while the flat concatenation separates none; "
          f"the exhausted-allowance item was exercised on {allowance_seen} inputs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
