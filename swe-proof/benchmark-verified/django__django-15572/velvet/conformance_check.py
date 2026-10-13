#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15572 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`collectConfiguredDirs` / `collectLoaderDirs`, i.e. the pure
              folds `collectConfigured` / `collectLoader`) transliterated to
              Python over the *real* repo type (`str` directory entries), via
              the mapping.md bijection (`List Char` ↔ `str`, `entry ≠ []` ↔
              `entry != ""` ↔ Python truthiness of a `str`).
  * ORACLE  — `patch.diff`'s behaviour: the two patched generator expressions of
              `django.template.autoreload.get_template_directories`,
              transliterated VERBATIM from the gold patch:
                  items.update(cwd / to_path(dir)
                               for dir in backend.engine.dirs if dir)
                  items.update(cwd / to_path(directory)
                               for directory in loader.get_dirs()
                               if directory and not is_django_path(directory))

The two A-tagged opaque callees of the impl region — `normalizePath`
(= `cwd / to_path(...)`) and `isFrameworkOwned` (= `is_django_path(...)`) — are
out of scope for G-CONF (they are validated, where applicable, by G-AX). Per the
worker prompt, an A-tagged callee is run as the SAME function on BOTH sides, so
its behaviour cancels and the differential test isolates the only R/I content:
the emptiness/ownership FILTER that the patch adds. We use deterministic
stand-ins for both callees (identical on shadow and oracle); any disagreement is
therefore a pure filter-fidelity counterexample.

WHY THE ORACLE IS THE PATCHED GENERATOR EXPRESSIONS (not a live call):
  `get_template_directories()` reads global Django template engine state
  (`engines.all()`, each backend's `engine.dirs` / loader `get_dirs()`), which
  requires a configured settings module and instantiated backends; the F2P test
  drives it through `@override_settings(TEMPLATES=...)`. The observable the test
  checks is the *set of retained, normalised directories*. So, per the worker
  prompt, the ORACLE is the patched generator expressions transliterated
  verbatim; the SHADOW is Solution.lean's folds transliterated. They must agree
  on every input list of entries.

This mirrors the F2P test `test_template_dirs_ignore_empty_path`:
  DIRS = [""]  ->  get_template_directories() == set()   (empty entry skipped)

Runs stdlib only; the fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. Exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 15572
N_FUZZ = 100_000


# --- A-tagged opaque callees: identical deterministic stand-ins both sides ----
# These model `normalizePath` (= cwd / to_path(entry)) and `isFrameworkOwned`
# (= is_django_path(entry)). G-CONF holds them out of scope by using the SAME
# function on shadow and oracle, so they cancel and the filter R/I leg is
# isolated. The concrete behaviour is irrelevant as long as it is deterministic
# and identical on both sides.
def normalize_path(entry):
    return "/cwd/" + entry            # cwd / to_path(entry): order-/content-faithful


def is_framework_owned(entry):
    return entry.startswith("/django/")   # is_django_path stand-in


# --- the R/I shadow: Solution.lean collectConfigured / collectLoader ----------
def shadow_configured(entries):
    """collectConfigured (entries) transliterated to str: keep non-empty
    entries, normalise each, in order."""
    out = []
    for e in entries:
        if e != "":                   # keepConfigured: decide (entry ≠ [])
            out.append(normalize_path(e))
    return out


def shadow_loader(entries):
    """collectLoader (entries): keep non-empty AND not framework-owned."""
    out = []
    for e in entries:
        if e != "" and not is_framework_owned(e):   # keepLoader
            out.append(normalize_path(e))
    return out


# --- the oracle: patch.diff's two patched generator expressions, verbatim -----
def oracle_configured(entries):
    """`cwd / to_path(dir) for dir in backend.engine.dirs if dir`."""
    return [normalize_path(dir) for dir in entries if dir]


def oracle_loader(entries):
    """`cwd / to_path(directory) for directory in loader.get_dirs()
        if directory and not is_django_path(directory)`."""
    return [
        normalize_path(directory)
        for directory in entries
        if directory and not is_framework_owned(directory)
    ]


def fuzz_lists(n, rng):
    # boundary cases first (plan §4.1 step 4)
    boundary = [
        [],                          # no entries
        [""],                        # the F2P case: single empty entry
        ["", "", ""],                # all empty
        ["a"],                       # single non-empty
        ["", "a"], ["a", ""],        # empty mixed with non-empty
        ["/django/x"],               # framework-owned (loader site drops it)
        ["", "/django/x"],           # empty + framework-owned
        ["/django/x", "a", ""],      # all three categories
        ["a", "b", "c"],             # no empties
        [" "],                       # whitespace is NON-empty (truthy str)
    ]
    for lst in boundary:
        yield lst
    # randomized fuzz over lists of str entries (incl. "" and framework paths)
    pieces = ["", "a", "b", " ", "x/y", "/django/z", "/django/", "tmpl", "0"]
    for _ in range(n):
        k = rng.randint(0, 8)
        yield [rng.choice(pieces) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for entries in fuzz_lists(N_FUZZ, rng):
        count += 1
        for site, sh_fn, orc_fn in (
            ("configured", shadow_configured, oracle_configured),
            ("loader", shadow_loader, oracle_loader),
        ):
            sh = sh_fn(entries)
            orc = orc_fn(entries)
            if sh != orc:
                disagreements.append((site, entries, sh, orc))
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d input lists:"
              % (len(disagreements), count))
        for site, entries, sh, orc in disagreements:
            print("  site=%s entries=%r shadow=%r oracle=%r"
                  % (site, entries, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of collectConfiguredDirs/collectLoaderDirs "
          "agrees with patch.diff behaviour on %d input lists x2 sites "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
