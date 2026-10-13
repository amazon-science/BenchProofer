#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9711 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python: the backward `while` fold of `anyRequirementUnmet`, i.e.
              `anyUnmet`/`unmet`/`verGt` over the modeled `Requirement` carrier.
              There are NO A-tagged callees in the impl (`verGt` is a deep model,
              tag A-reference, validated separately by G-AX); the shadow is pure
              R/I. It returns whether ANY requirement is unmet.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `sphinx.extension.verify_needs_extensions` applied at base_commit
              (the harness applies patch.diff before this runs), driven through
              minimal duck-typed `app`/`config` mocks. It RAISES
              VersionRequirementError iff at least one loaded extension fails its
              minimum-version requirement — so "oracle raised" is the observable
              we diff against the shadow's boolean.

The mapping.md bijection bridges the carriers: a `Requirement` ↔ one entry of
`config.needs_extensions` plus its `app.extensions` Extension (mapping.md §2).
Inputs are restricted to the modeled numeric-version domain (`require
reqs.all reqWellFormed`); G-AX covers the comparator on that domain, and the
gold patch's textual-fallback branch is out of the modeled scope by construction.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the repo's
own `packaging`/`sphinx`. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 9711
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean verGt/unmet/anyUnmet, transliterated -------

def split_dots(s):
    if s == "":
        return [[]]
    rest = split_dots(s[1:])
    if s[0] == ".":
        return [[]] + rest
    head = rest[0] if rest else []
    return [[s[0]] + head] + rest[1:]


def parse_comp(cs):
    acc = 0
    for c in cs:
        acc = acc * 10 + (ord(c) - ord("0"))
    return acc


def rel_gt(xs, ys):
    if not xs and not ys:
        return False
    if not xs:
        return False if ys[0] > 0 else rel_gt([], ys[1:])
    if not ys:
        return True if xs[0] > 0 else rel_gt(xs[1:], [])
    if xs[0] > ys[0]:
        return True
    if xs[0] < ys[0]:
        return False
    return rel_gt(xs[1:], ys[1:])


def ver_gt(a, b):
    return rel_gt([parse_comp(c) for c in split_dots(a)],
                  [parse_comp(c) for c in split_dots(b)])


def numeric_ver(s):
    comps = split_dots(s)
    return all(len(c) > 0 and all(ch.isdigit() for ch in c) for c in comps)


def unmet(req):
    """unmet (r : Requirement)."""
    if not req["isPresent"]:
        return False
    if not req["isKnown"]:
        return True
    return ver_gt(req["required"], req["present"])


def shadow_any_unmet(reqs):
    """anyRequirementUnmet's backward fold == anyUnmet (front-recursive disj)."""
    acc = False
    for req in reqs:                # order-insensitive (disjunction), as in Lean
        acc = unmet(req) or acc
    return acc


def req_well_formed(req):
    """reqWellFormed: the modeled numeric-version domain (the `require`)."""
    if not numeric_ver(req["required"]):
        return False
    if req["isPresent"] and req["isKnown"] and not numeric_ver(req["present"]):
        return False
    return True


# --- the oracle: REAL patched verify_needs_extensions, via mocks --------------

_UNKNOWN = "unknown version"   # sphinx.extension.Extension default sentinel


def oracle_raises(reqs):
    """patch.diff's behaviour: the patched verify_needs_extensions raises iff at
    least one loaded extension fails its requirement. We bridge the Requirement
    carrier to the real (config, app) types per mapping.md §2."""
    from sphinx.extension import verify_needs_extensions, Extension
    from sphinx.errors import VersionRequirementError

    class _Cfg:
        def __init__(self, needs):
            self.needs_extensions = needs

    class _App:
        def __init__(self):
            self.extensions = {}

    needs = {}
    app = _App()
    for idx, req in enumerate(reqs):
        name = "ext.%d" % idx
        needs[name] = req["required"]
        if req["isPresent"]:
            if req["isKnown"]:
                app.extensions[name] = Extension(name, name,
                                                 version=req["present"])
            else:
                # present but version indeterminate -> the 'unknown version'
                # sentinel (Extension default when no version kwarg is given)
                app.extensions[name] = Extension(name, name)
                assert app.extensions[name].version == _UNKNOWN
        # absent: leave it out of app.extensions (app.extensions.get -> None)
    cfg = _Cfg(needs)
    try:
        verify_needs_extensions(app, cfg)
        return False
    except VersionRequirementError:
        return True


# --- fuzz over the modeled domain ---------------------------------------------

def gen_version(rng):
    n = rng.randint(1, 4)
    comps = []
    for _ in range(n):
        kind = rng.randint(0, 3)
        if kind == 0:
            comps.append(str(rng.randint(0, 9)))
        elif kind == 1:
            comps.append(str(rng.randint(0, 999)))
        elif kind == 2:
            comps.append("0" + str(rng.randint(0, 99)))
        else:
            comps.append("0")
    return ".".join(comps)


def gen_requirement(rng):
    present = gen_version(rng)
    is_present = rng.random() < 0.8
    is_known = rng.random() < 0.85
    return {
        "required": gen_version(rng),
        "present": present,
        "isPresent": is_present,
        "isKnown": is_known,
    }


def boundary_lists():
    """The F2P-derived and structural edge cases."""
    def mk(req, pres, present=True, known=True):
        return {"required": req, "present": pres,
                "isPresent": present, "isKnown": known}
    return [
        [],                                              # empty needs_extensions
        [mk("3.9", "3.10")],                             # fulfilled (the fix)
        [mk("3.11", "3.10")],                            # unfulfilled
        [mk("0.6", "0.10")],                             # issue example, fulfilled
        [mk("0.10", "0.6")],                             # unfulfilled
        [mk("1.0", "x", present=False)],                # absent -> not failed
        [mk("1.0", "x", present=True, known=False)],    # unknown version -> unmet
        [mk("1.0", "1.0")],                              # equal -> fulfilled
        [mk("1.0", "1.0.0")],                            # trailing zero -> equal
        [mk("3.9", "3.10"), mk("3.11", "3.10")],         # mixed: one unmet
        [mk("3.9", "3.10"), mk("0.6", "0.10")],          # both fulfilled
        [mk("3.9", "3.10", present=False),
         mk("3.11", "3.10")],                            # absent + unmet
    ]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def check(reqs):
        nonlocal count
        # enforce the modeled domain (the Solution.lean `require`)
        if not all(req_well_formed(r) for r in reqs):
            return
        count += 1
        shadow = shadow_any_unmet(reqs)
        oracle = oracle_raises(reqs)
        if shadow != oracle:
            disagreements.append((reqs, shadow, oracle))

    for reqs in boundary_lists():
        check(reqs)

    for _ in range(N_FUZZ):
        k = rng.randint(0, 5)
        reqs = [gen_requirement(rng) for _ in range(k)]
        check(reqs)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for reqs, sh, orc in disagreements:
            print("  reqs=%r shadow=%r oracle=%r" % (reqs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of anyRequirementUnmet agrees with patch.diff "
          "behaviour (verify_needs_extensions raises) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
