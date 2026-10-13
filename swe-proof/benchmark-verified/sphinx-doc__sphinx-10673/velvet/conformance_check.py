#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10673 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List String` ↔ a Python list/set of docname strings; `.contains`
              ↔ set membership; the backward `while` fold ↔ a left-to-right
              filter in request order). The whole impl region is R/I — there are
              NO axioms and NO deep-model references in this bundle
              (conf_skip=false). The shadow is `selectToctreeEntries`/
              `retainedEntries`/`targetExists` transliterated.

  * ORACLE  — `patch.diff`'s behaviour: the patched toctree directive accepts a
              non-glob, non-URL, non-'self' entry into `toctree['entries']`
              exactly when

                  docname in self.env.found_docs | generated_docnames

              (`sphinx/directives/other.py`, post-patch). We transliterate that
              acceptance predicate verbatim — `docname in (found_docs |
              generated_docnames)` — and reconstruct the resulting ordered entry
              list the directive appends, which is precisely what the F2P test
              reads back as `app.env.tocs['index']` entry names.

              `generated_docnames` is the key set of the std domain's `labels`
              initial data; G-AX (axiom_check.py) pins that this set is exactly
              {'genindex','modindex','search'} in the real repo, so here we drive
              the oracle with that real set plus fuzzed extra source/auto names.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Scope (mapping.md §2): the modeled decision is the per-entry validity test of
`parse_content` for plain (non-glob, non-URL, non-'self') entries — the only
behaviour the F2P `test_toctree_index` observes through the retained
`toctree['entries']`. Suffix stripping and `docname_join` are observationally
identity on the simple, suffixless, top-level docnames exercised here and by the
test (mapping.md §2); the glob branch is out of modeled scope (refinement.md §C).

stdlib only; the fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 10673
N_FUZZ = 100_000

# The reference targets the project provides automatically — the keys of the std
# domain's `labels` initial data at base_commit. G-AX pins this is exactly the
# set the real repo exposes; here it is the autoTargets carrier.
GENERATED = ["genindex", "modindex", "search"]


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def shadow_target_exists(source_docs, auto_targets, name):
    """`targetExists`: a name resolves to a real source file OR an auto target."""
    return name in source_docs or name in auto_targets


def shadow_select(requested, source_docs, auto_targets):
    """`selectToctreeEntries` post-image: the requested entries that resolve, in
    request order (the backward `while` fold computes exactly this left-to-right
    filter — `retainedEntries`)."""
    return [e for e in requested
            if shadow_target_exists(source_docs, auto_targets, e)]


# ---- ORACLE: patch.diff acceptance predicate, transliterated --------------

def oracle_select(requested, found_docs, generated_docnames):
    """patch.diff behaviour: the patched directive appends an entry iff

        docname in self.env.found_docs | generated_docnames

    (sphinx/directives/other.py, post-patch). Build the ordered list it appends
    to `toctree['entries']` — exactly the entry names the F2P test reads back."""
    valid = set(found_docs) | set(generated_docnames)
    out = []
    for entry in requested:
        # plain entry: ref == docname == entry (no suffix, no title, top level)
        docname = entry
        if docname in valid:
            out.append(docname)
        # else: the directive emits a "nonexisting/excluded document" warning and
        # does NOT append — the entry is dropped from toctree['entries'].
    return out


# ---- fuzzing ---------------------------------------------------------------

def rand_name(rng):
    return "".join(rng.choice("abcdefghijklmnop") for _ in range(rng.randint(1, 6)))


def fuzz_cases(n, rng):
    # boundary cases first (plan §4.1 step 4) -----------------------------
    # the exact F2P scenario: genindex/modindex/search requested, only 'foo' has
    # a source file, current doc 'index' excluded from the requested list.
    yield (["genindex", "modindex", "search"], ["foo"], GENERATED)
    yield (["foo", "genindex", "modindex", "search"], ["foo"], GENERATED)
    yield ([], ["foo"], GENERATED)
    yield (["genindex"], [], GENERATED)
    yield (["missing"], ["foo"], GENERATED)              # neither -> dropped
    yield (["foo"], ["foo"], GENERATED)                  # source only -> kept
    yield (["search", "search"], ["a"], GENERATED)       # duplicate auto target
    yield (["genindex", "missing", "foo"], ["foo"], GENERATED)
    yield (["GENINDEX"], ["foo"], GENERATED)             # case sensitive -> drop
    yield (["genindex", "modindex", "search"], [], [])   # no auto -> all dropped
    # randomized fuzz ----------------------------------------------------
    for _ in range(n):
        # a pool of candidate source docs and the (possibly extended) auto set
        n_src = rng.randint(0, 6)
        source_docs = [rand_name(rng) for _ in range(n_src)]
        auto = list(GENERATED)
        # occasionally add extra synthetic auto targets (extra std labels)
        if rng.random() < 0.3:
            auto += [rand_name(rng) for _ in range(rng.randint(1, 3))]
        # requested entries drawn from sources, autos, and pure-miss names
        pool = source_docs + auto + [rand_name(rng) for _ in range(3)]
        k = rng.randint(0, 8)
        requested = [rng.choice(pool) for _ in range(k)] if pool else []
        yield (requested, source_docs, auto)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for requested, source_docs, auto in fuzz_cases(N_FUZZ, rng):
        count += 1
        shadow = shadow_select(requested, source_docs, auto)
        # oracle: found_docs == source_docs, generated_docnames == auto
        oracle = oracle_select(requested, source_docs, auto)
        if shadow != oracle:
            disagreements.append((requested, source_docs, auto, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for req, src, auto, sh, orc in disagreements:
            print("  requested=%r source=%r auto=%r shadow=%r oracle=%r"
                  % (req, src, auto, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectToctreeEntries agrees with patch.diff "
          "acceptance behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
