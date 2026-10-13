#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7440 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged op of Solution.lean's impl region transliterated to
              Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`). The impl returns the verbatim
              registration key `registeredKey termText` = the term text as
              written, with no normalization.
  * ORACLE  — `patch.diff`'s behaviour: drive the term text through the REAL,
              gold-patched `make_glossary_term` (the changed function) and read
              the key back through the REAL `StandardDomain.get_objects()` (the
              unchanged registry, the A-reference — run as the real callee here,
              not the model). This is the genuine correctness oracle: the harness
              applies patch.diff at base_commit before this runs (G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. (On the UNpatched tree the oracle
lower-cases, so this check correctly DISAGREES on any term with an upper-case
letter — that is the discriminating signal the gold patch removes.)

Runs in-container (the prebuilt SWE-Bench instance image), repo `sphinx` +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from docutils import nodes
from sphinx.domains.std import StandardDomain, make_glossary_term

SEED = 7440
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean registeredKey, transliterated -------------

def shadow_key(term_text):
    """registeredKey(termText) = the term text verbatim (identity). The impl op
    returns exactly the term text as written, with no case folding."""
    return term_text


# --- the oracle: real gold-patched make_glossary_term + real registry --------

class _Registry:
    enumerable_nodes = {}


class _App:
    registry = _Registry()


class _Env:
    """Minimal BuildEnvironment stub: just enough for StandardDomain +
    make_glossary_term's node_id-given branch. None of it influences how the key
    is keyed or echoed."""
    def __init__(self):
        self.domaindata = {}
        self.docname = "index"
        self.all_docs = {}
        self.titles = {}
        self.app = _App()
        self._dom = StandardDomain(self)

    def get_domain(self, name):
        return self._dom


def oracle_key(term_text):
    """Run the real make_glossary_term on a term whose text is `term_text`, then
    read back the 'term' key the registry reports via the real get_objects().
    Returns the single registered term key (or None if none registered)."""
    env = _Env()
    textnodes = [nodes.Text(term_text)]
    # Pass node_id explicitly so make_glossary_term takes the "node_id given"
    # branch (no document / make_id / RemovedInSphinx40Warning path). The key it
    # registers is independent of node_id.
    make_glossary_term(env, textnodes, None, "glossary.rst", 1,
                       node_id='term-x', document=None)
    keys = [e[0] for e in env.get_domain('std').get_objects() if e[2] == 'term']
    if len(keys) != 1:
        return ("<%d-keys>" % len(keys), keys)
    return keys[0]


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4) — the F2P terms + the issue case
    yield "term1"
    yield "TERM2"
    yield "term3"
    yield "term4"
    yield "MySQL"
    yield "mysql"
    yield "MYSQL"
    yield "A"
    yield "a"
    yield "Term"
    yield "TERM"
    yield "café"
    yield "CAFÉ"
    yield "Straße"
    yield "term-4"
    yield "term_4"
    yield "Mixed Case Term"
    # randomized: word-like strings over a mixed-case + punctuation alphabet.
    # term.astext([Text(s)]) is identity on s for these (no newlines/tabs), so
    # the differential isolates the registration-key op, not text serialization.
    alphabet = list(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.:;#")
    alphabet += ["é", "É", "ß", "Ω", "ω", "•"]
    for _ in range(n):
        k = rng.randint(1, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        # guard: only compare where text serialization is identity, so the
        # differential targets the registration-key op (mapping.md §2, A1).
        if nodes.Text(s).astext() != s:
            continue
        count += 1
        shadow = shadow_key(s)
        oracle = oracle_key(s)
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
    print("G-CONF OK: R/I shadow of registerGlossaryName (verbatim term key) "
          "agrees with patch.diff behaviour (real make_glossary_term + "
          "get_objects) on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
