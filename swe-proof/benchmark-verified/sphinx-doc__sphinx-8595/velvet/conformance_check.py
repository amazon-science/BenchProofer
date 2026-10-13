#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8595 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `decideMembers` / `markAllExposed` / `markByPublished`
              / `selectRequested` over the mode flag (`want_all`), the optional
              published list (`self.__all__`), the roster (the values of
              `get_module_members()`), and the explicit subset
              (`self.options.members`). The bundle has NO axioms (mapping.md §3),
              so the whole shadow is in scope for G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, gold-patched
              `sphinx.ext.autodoc.ModuleDocumenter.get_object_members`. We do not
              build a full Sphinx app; `get_object_members` only reads
              `self.get_module_members()`, `self.__all__`, and
              `self.options.members`, and mutates `member.skipped`. We therefore
              feed it a DUCK-TYPED documenter whose `get_module_members` returns
              real `ObjectMember`s for the case's roster, so the real patched code
              path decides the (checkOrigin, [(name, skipped)…]) result.

Observed projection (exactly what the F2P `test_empty_all` and the documented-set
assertions see): the returned origin-filter flag and, for each returned entry, its
`(__name__, skipped)` pair, in returned order. Field `obj`/`docstring`/`class_`
are unmodeled R-identities and are not compared.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch applied), stdlib
+ the in-image Sphinx only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 8595
N_FUZZ = 100_000


# --- ORACLE setup: the REAL gold-patched get_object_members ------------------

def _load_real():
    """Import the gold-patched ModuleDocumenter.get_object_members and the real
    ObjectMember carrier. The harness applies patch.diff before this runs."""
    from sphinx.ext.autodoc import ModuleDocumenter, ObjectMember
    return ModuleDocumenter.get_object_members, ObjectMember


class _Options:
    def __init__(self, members):
        self.members = members


class _FakeObject:
    __name__ = "target.fake_module"


class _FakeDocumenter:
    """Duck-typed stand-in exposing exactly what get_object_members reads."""
    def __init__(self, roster, all_, options_members, ObjectMember):
        # get_module_members() returns an insertion-ordered dict name -> member.
        self._members = {n: ObjectMember(n, None) for n in roster}
        self.__all__ = all_
        self.options = _Options(options_members)
        self.object = _FakeObject()

    def get_module_members(self):
        # Return a FRESH dict each call (the real one rebuilds members), so a
        # prior case's skipped-mutation never leaks into the next.
        return dict(self._members)


def oracle_result(get_object_members, ObjectMember,
                  roster, all_, options_members, want_all):
    fake = _FakeDocumenter(roster, all_, options_members, ObjectMember)
    check_origin, members = get_object_members(fake, want_all)
    entries = [(m.__name__, bool(m.skipped)) for m in members]
    return (bool(check_origin), entries)


# --- SHADOW: Solution.lean decideMembers, transliterated ---------------------

def shadow_result(roster, all_, options_members, want_all):
    """decideMembers(exposeAll, published, roster, requested) transliterated.

    `roster`          : the candidate entry names, in order (List Int -> str).
    `all_`            : the optional published list (None -> none, list -> some).
    `options_members` : the explicit subset (None/[] both -> []).
    `want_all`        : the mode flag.
    Returns (checkOrigin, [(name, skipped)…]) in modeled order."""
    if want_all:
        if all_ is None:                       # none: full roster, filter by origin
            return (True, [(n, False) for n in roster])
        else:                                  # some pub: mark skipped iff n not in pub
            return (False, [(n, n not in all_) for n in roster])
    else:
        requested = options_members or []
        roster_set = set(roster)
        return (False, [(n, False) for n in requested if n in roster_set])


def main():
    rng = random.Random(SEED)
    try:
        get_object_members, ObjectMember = _load_real()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched get_object_members: %r" % e)
        return 2

    pool = ["foo", "bar", "baz", "qux", "alpha", "beta", "gamma",
            "_priv", "Helper", "CONST"]

    disagreements = []
    count = 0

    def run_case(roster, all_, options_members, want_all):
        nonlocal count
        count += 1
        shadow = shadow_result(roster, all_, options_members, want_all)
        oracle = oracle_result(get_object_members, ObjectMember,
                               roster, all_, options_members, want_all)
        if shadow != oracle:
            disagreements.append((roster, all_, options_members, want_all,
                                  shadow, oracle))

    # --- boundary cases (the issue + the F2P assertion) ----------------------
    base = ["foo", "bar", "baz"]
    boundary = [
        (base, None, None, True),              # no __all__  -> document all, origin
        (base, [],   None, True),              # __all__=[]  -> document NOTHING (the bug)
        (base, ["foo"], None, True),           # subset published
        (base, ["foo", "baz"], None, True),    # multi published
        (base, ["ghost"], None, True),         # published name not in roster
        (base, base, None, True),              # all published
        ([],   [],   None, True),              # empty roster, __all__=[]
        ([],   None, None, True),              # empty roster, no __all__
        (base, None, ["foo"], False),          # explicit subset
        (base, None, [],     False),           # explicit empty subset -> none
        (base, None, None,   False),           # explicit, options.members None -> []
        (base, None, ["foo", "ghost"], False), # requested name missing from roster
        (base, ["foo"], ["bar"], False),       # want_all False ignores __all__
    ]
    for r, a, om, wa in boundary:
        run_case(r, a, om, wa)

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(N_FUZZ):
        k = rng.randint(0, len(pool))
        roster = rng.sample(pool, k)            # distinct names (dict keys)
        want_all = rng.random() < 0.6
        # __all__: None, [], or a random subset (possibly with ghost names)
        ach = rng.random()
        if ach < 0.34:
            all_ = None
        elif ach < 0.5:
            all_ = []
        else:
            all_ = rng.sample(roster, rng.randint(0, len(roster))) if roster else []
            if rng.random() < 0.2:
                all_ = all_ + ["ghost"]
        # options.members: None, [], or a random subset (possibly with ghosts /
        # duplicates / out-of-roster order)
        och = rng.random()
        if och < 0.34:
            options_members = None
        elif och < 0.5:
            options_members = []
        else:
            src = roster + ["ghost"]
            options_members = [rng.choice(src) for _ in range(rng.randint(0, 5))]
        run_case(roster, all_, options_members, want_all)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for r, a, om, wa, sh, orc in disagreements:
            print("  roster=%r __all__=%r options.members=%r want_all=%r "
                  "shadow=%r oracle=%r" % (r, a, om, wa, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectDocumentedMembers agrees with the real "
          "patched ModuleDocumenter.get_object_members on %d inputs (13 boundary "
          "+ fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
