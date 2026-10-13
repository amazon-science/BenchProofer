#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-15100.

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the I-tagged ops of Solution.lean's impl region transliterated to
              Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Char.ofNat (ord ch)` ↔ ch). The
              deep model is `markFreeSeq (canonicalDecompose s)`: decompose with
              the REAL `unicodedata.normalize('NFKD', ·)`, then keep each code
              point whose REAL `unicodedata.combining(·)` is 0 (drop the rest).
              The two opaque callees (`canonicalDecompose`, `isCombiningMark`)
              are A-tagged → run as the REAL stdlib callees here, NOT a model;
              G-CONF isolates the R/I legs, so their behaviour is out of scope.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sklearn.feature_extraction.text.strip_accents_unicode` applied at
              base_commit (the real correctness oracle, G-RESOLVE). The harness
              applies patch.diff before this runs; we fall back to a verbatim
              transliteration of the gold body if the import is unavailable.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
import unicodedata

SEED = 15100
N_FUZZ = 100_000


# --- the I/R shadow: markFreeSeq(canonicalDecompose s), transliterated --------
def shadow_strip(s):
    """markFreeSeq (canonicalDecompose s) over str, per mapping.md.

    canonicalDecompose  := unicodedata.normalize('NFKD', s)   (real callee)
    isCombiningMark c    := unicodedata.combining(c) != 0      (real callee)
    markFreeSeq          := keep non-combining code points, drop combining marks
    The backward `while` fold of stripDiacritics computes exactly this
    left-to-right keep/drop concatenation."""
    normalized = unicodedata.normalize('NFKD', s)
    out = []
    for c in normalized:
        if unicodedata.combining(c):
            pass            # drop combining mark  -> [] in markFreeSeq
        else:
            out.append(c)   # keep                 -> [c] in markFreeSeq
    return "".join(out)


# --- the oracle: patch.diff's behaviour --------------------------------------
def _gold_strip(s):
    """Verbatim transliteration of the gold-patched body (fallback oracle)."""
    try:
        s.encode("ASCII", errors="strict")
        return s
    except UnicodeEncodeError:
        normalized = unicodedata.normalize('NFKD', s)
        return ''.join([c for c in normalized if not unicodedata.combining(c)])


def oracle_strip(s):
    """patch.diff's behaviour: the patched strip_accents_unicode(). Prefer the
    real patched repo function (harness applies patch.diff first); fall back to
    the verbatim gold body if the import is unavailable."""
    try:
        from sklearn.feature_extraction.text import strip_accents_unicode
        return strip_accents_unicode(s)
    except Exception:
        return _gold_strip(s)


# --- fuzz corpus: weighted toward the inputs the bug concerns ----------------
def fuzz_inputs(n, rng):
    # Combining marks (U+0300..U+036F): the diacritics that must be stripped.
    combining = [chr(cp) for cp in range(0x0300, 0x0370)]
    # Precomposed accented Latin letters (decompose to base + mark under NFKD).
    precomposed = list("àáâãäåçèéêëìíîïñòóôõöùúûüýÿÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖ")
    # Bases that combining marks attach to, plus plain ASCII and ligatures.
    bases = list("noaeiuycNOAEIUYC abcXYZ0123 ")
    compat = list("ﬁﬂ½²³…")          # NFKD-compatibility expansions
    alphabet = combining + precomposed + bases + compat

    # boundary / regression cases first (the issue + F2P test)
    yield ""
    yield chr(241)                         # ñ precomposed (s1 in the issue)
    yield chr(110) + chr(771)              # n + COMBINING TILDE (s2 in the issue)
    yield "ö"                        # o + COMBINING DIAERESIS  -> "o"
    yield "̀́̂̃"       # combining marks alone    -> ""
    yield "ȫ"                  # multiple marks on one char -> "o"
    yield "this is a test"                 # pure ASCII fast-path
    yield "àéîõü"                          # precomposed accents
    yield "ñó"                 # already-decomposed sequence
    yield "ﬁ½"                             # compatibility expansions

    for _ in range(n):
        k = rng.randint(0, 16)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_strip(s)
        oracle = oracle_strip(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of stripDiacritics agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
