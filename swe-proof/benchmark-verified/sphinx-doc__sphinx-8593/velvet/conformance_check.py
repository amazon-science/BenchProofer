#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8593 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `buildMembers` / `lookupDocs` / `joinNL` over the
              candidate name roster (`dir(self.object)`) and the per-name
              documentation lines (`self.analyzer.attr_docs` at keys `('', name)`).
              The bundle has NO axioms (mapping.md §3), so the whole shadow is in
              scope for G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, gold-patched
              `sphinx.ext.autodoc.ModuleDocumenter.get_module_members`. We do not
              build a full Sphinx app; that method only reads `self.analyzer`
              (its `attr_docs`) and `self.object` (via `dir`, `safe_getattr`,
              `inspect.getannotations`), and returns an insertion-ordered dict of
              `ObjectMember`s. We therefore feed it a DUCK-TYPED documenter whose
              `self.object` is a synthetic module exposing the case's names and
              whose `self.analyzer.attr_docs` holds the case's doc lines, so the
              real patched code path collects the members.

Observed projection (exactly what the downstream `filter_members` /
`extract_metadata` pipeline — and the F2P tests — read off each collected member):
the member's `(__name__, docstring)` pair, in returned (insertion) order. The
member's `object`/`class_`/`skipped` are unmodeled R-identities and not compared.

Both sides are driven on the SAME name roster (`dir(self.object)`) so the
candidate set is identical; the only thing under test is whether each collected
member carries the documentation text assembled from its recorded lines, in the
right order. They must agree on every input. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch applied), stdlib
+ the in-image Sphinx only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
import types

SEED = 8593
N_FUZZ = 100_000


# --- ORACLE setup: the REAL gold-patched get_module_members ------------------

def _load_real():
    """Import the gold-patched ModuleDocumenter.get_module_members. The harness
    applies patch.diff before this runs."""
    from sphinx.ext.autodoc import ModuleDocumenter
    return ModuleDocumenter.get_module_members


class _Analyzer:
    """Stand-in for ModuleAnalyzer exposing only `attr_docs`."""
    def __init__(self, attr_docs):
        self.attr_docs = attr_docs


class _FakeModuleDocumenter:
    """Duck-typed stand-in exposing exactly what get_module_members reads:
    `self.analyzer` (with `.attr_docs`) and `self.object`."""
    def __init__(self, obj, analyzer):
        self.object = obj
        self.analyzer = analyzer


def _make_object(names, values):
    """A synthetic module object exposing `names` as real attributes (so `dir`,
    `safe_getattr`, and `inspect.getannotations` all behave like the real thing).
    Annotation-only members are not exercised here (no `__annotations__`), so the
    roster the real method iterates is exactly `dir(obj)`."""
    mod = types.ModuleType("target.fake_module")
    for n, v in zip(names, values):
        setattr(mod, n, v)
    return mod


def oracle_result(get_module_members, obj, attr_docs):
    analyzer = _Analyzer(attr_docs)
    fake = _FakeModuleDocumenter(obj, analyzer)
    members = get_module_members(fake)
    # insertion-ordered dict name -> ObjectMember
    return [(m.__name__, m.docstring) for m in members.values()]


# --- SHADOW: Solution.lean buildMembers, transliterated ----------------------

def shadow_lookup_docs(name, attr_docs):
    """lookupDocs n attrDocs — the recorded documentation lines for `name`
    (keyed by ('', name) in attr_docs), or [] if none."""
    return attr_docs.get(('', name), [])


def shadow_join_nl(lines):
    """joinNL lines — join the documentation lines with a single '\\n' between
    consecutive lines ([] -> '', [x] -> x, x::xs -> x + '\\n' + join xs)."""
    return "\n".join(lines)


def shadow_result(names, attr_docs):
    """buildMembers attrDocs names — one entry per name (in order), each carrying
    the documentation text assembled from its recorded lines."""
    return [(n, shadow_join_nl(shadow_lookup_docs(n, attr_docs))) for n in names]


def main():
    rng = random.Random(SEED)
    try:
        get_module_members = _load_real()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched get_module_members: %r" % e)
        return 2

    pool = ["foo", "bar", "baz", "qux", "alpha", "beta",
            "_priv", "_PUBLIC_CONSTANT", "PRIVATE_CONSTANT", "Helper"]
    doc_lines_pool = [
        ":meta public:", ":meta private:", "a docstring().", "", "line one",
        "second line", "  indented", "value None",
    ]

    disagreements = []
    count = 0

    def run_case(names, values, attr_docs):
        nonlocal count
        count += 1
        obj = _make_object(names, values)
        # Drive BOTH sides on the exact roster the real method iterates.
        roster = dir(obj)
        shadow = shadow_result(roster, attr_docs)
        oracle = oracle_result(get_module_members, obj, attr_docs)
        if shadow != oracle:
            disagreements.append((roster, attr_docs, shadow, oracle))

    # --- boundary cases (the issue + the F2P assertions) ---------------------
    # The reported bug: a private-named module variable with `:meta public:` must
    # carry that doc text so it is later honoured; a public-named one with
    # `:meta private:` likewise.
    boundary = [
        # name -> doc lines
        (["_PUBLIC_CONSTANT"], {('', '_PUBLIC_CONSTANT'): [":meta public:"]}),
        (["PRIVATE_CONSTANT"], {('', 'PRIVATE_CONSTANT'): [":meta private:"]}),
        (["_PUBLIC_CONSTANT", "PRIVATE_CONSTANT"],
         {('', '_PUBLIC_CONSTANT'): [":meta public:"],
          ('', 'PRIVATE_CONSTANT'): [":meta private:"]}),
        (["foo"], {}),                                  # no recorded docs
        (["foo"], {('', 'foo'): []}),                   # present but empty lines
        (["foo"], {('', 'foo'): ["a", "b", "c"]}),      # multi-line join
        (["foo", "bar"], {('', 'bar'): ["only bar"]}),  # one of several has docs
        ([], {}),                                        # no members
        (["foo"], {('', 'ghost'): ["unused"]}),          # doc for absent name
    ]
    for names, ad in boundary:
        run_case(names, [None] * len(names), ad)

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(N_FUZZ):
        k = rng.randint(0, len(pool))
        names = rng.sample(pool, k)                      # distinct names
        values = [rng.choice([None, 0, "x", 1.5]) for _ in names]
        attr_docs = {}
        for n in names:
            r = rng.random()
            if r < 0.4:
                continue                                 # no recorded docs
            elif r < 0.55:
                attr_docs[('', n)] = []                  # present but empty
            else:
                nlines = rng.randint(1, 4)
                attr_docs[('', n)] = [rng.choice(doc_lines_pool)
                                      for _ in range(nlines)]
        # occasionally record docs for a name not in the roster (never looked up)
        if rng.random() < 0.1:
            attr_docs[('', "ghost")] = [rng.choice(doc_lines_pool)]
        run_case(names, values, attr_docs)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for roster, ad, sh, orc in disagreements:
            print("  roster=%r attr_docs=%r\n    shadow=%r\n    oracle=%r"
                  % (roster, ad, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of collectMemberDocs agrees with the real "
          "patched ModuleDocumenter.get_module_members on %d inputs (9 boundary "
          "+ fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
