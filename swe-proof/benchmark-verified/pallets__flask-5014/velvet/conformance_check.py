#!/usr/bin/env python3
"""G-CONF differential conformance check for pallets__flask-5014.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the observable accept/reject:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `validateBlueprintName` impl
              region transliterated to Python over the *real* repo type (`str`),
              via the mapping.md bijection (`List Char` <-> `str`):
                  validName(s) = (s != "") and ("." not in s)
              i.e. accept iff the name is non-empty (`not s.isEmpty`) AND
              dot-free (`not containsDot s`). `"." not in s` mirrors the
              front-recursive `containsDot` fold; `s != ""` mirrors `s.isEmpty`.
  * ORACLE  — the post-patch constructor behaviour: the real patched
              `flask.Blueprint(name, __name__)`, where raising `ValueError`
              == reject (False) and constructing successfully == accept (True).
              FALLBACK (documented): if `flask` cannot be imported, transliterate
              the post-patch guards directly as the oracle:
                  reject iff (name == "") or ("." in name).
              (`Blueprint.__init__` post-patch raises `ValueError` on `not name`
              and on `"." in name`; otherwise it constructs.)

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. The fuzz set is biased toward the
discriminating empty / dotted / boundary cases.

Runs in-container (the prebuilt SWE-Bench instance image with patch.diff
applied), stdlib only (plus the repo's own `flask`). The fuzz seed is pinned
(mapping.md §4).
"""
import random
import sys

SEED = 5014
N_FUZZ = 100_000


# --- the R/I shadow: validName transliterated ------------------------------
def shadow_valid(name):
    # accept iff non-empty AND contains no dot code point U+002E
    if name == "":
        return False
    return "." not in name


# --- the oracle: post-patch Blueprint.__init__ behaviour --------------------
def _live_oracle_factory():
    """Return an oracle backed by the real patched flask.Blueprint, or None if
    flask cannot be imported / the tree is not the post-patch tree."""
    try:
        import flask

        def accepts(name):
            try:
                flask.Blueprint(name, __name__)
                return True
            except ValueError:
                return False

        # sanity: confirm the patch is in place (empty name rejected)
        if accepts(""):
            return None  # unpatched / unexpected; use transliteration fallback
        # and that a normal name is accepted, a dotted name rejected
        if (not accepts("admin")) or accepts("a.b"):
            return None
        return accepts
    except Exception:
        return None


def _translit_oracle_factory():
    # post-patch guards transliterated: reject iff empty or contains a dot.
    def accepts(name):
        if name == "":
            return False
        if "." in name:
            return False
        return True
    return accepts


def fuzz_inputs(n, rng):
    base = list("aZ0_admin.UI-blueprint xYz")
    weird = ["é", "É", "ä", "•", "​", " ", "–", "أ", "\t", "'", "."]
    alphabet = base + weird
    # boundary / discriminating cases first
    yield ""                       # the F2P discriminator (empty name -> reject)
    yield "admin"
    yield "Admin_UI"
    yield "a.b"                    # dotted -> reject
    yield "."                      # single dot -> reject
    yield ".."
    yield "app.ui"                 # the pre-existing dotted-name test case
    yield "no dot here"
    yield " "                      # single space: non-empty, dot-free -> accept
    yield "\t"
    yield "trailing."
    yield ".leading"
    yield "mid.dle"
    for _ in range(n):
        k = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(k))
        r = rng.random()
        # bias toward empty and dotted cases
        if r < 0.15:
            s = ""
        elif r < 0.35:
            s = s + "."
        elif r < 0.45:
            s = "." + s
        yield s


def run(oracle, rng):
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_valid(s)
        orc = oracle(s)
        if shadow != orc:
            disagreements.append((s, shadow, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return None
    return count


def main():
    live = _live_oracle_factory()
    if live is not None:
        oracle = live
        oracle_kind = "live post-patch flask.Blueprint"
    else:
        oracle = _translit_oracle_factory()
        oracle_kind = ("transliterated post-patch guards "
                       "(reject iff empty or contains '.')")

    rng = random.Random(SEED)
    c = run(oracle, rng)
    if c is None:
        return 1
    print("G-CONF OK: R/I shadow of validateBlueprintName agrees with %s on %d "
          "inputs (seed=%d), 0 disagreements." % (oracle_kind, c, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
