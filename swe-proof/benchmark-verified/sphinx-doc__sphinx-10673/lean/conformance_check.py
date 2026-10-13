#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-10673.

The bundle models ONE behavior: the accepted-entry loop of the table-of-contents
directive's content parser (`TocTree.parse_content`, `sphinx/directives/other.py`).
Its Lean implementation (`implementation_tocEntries`) decides, for each line listed
in a toctree directive body, whether that line becomes an accepted `(title, target)`
entry:

    entries = []
    for entry in content:
        if entry == '':                                   # blank line: skip
            continue
        elif entry in (found_docs | generated_pages):     # accept
            entries.append((None, entry))
        else:                                             # reject (nonexisting)
            pass
    return entries

where `generated_pages` = {'genindex', 'modindex', 'search'} are the builder-
generated reference pages the patch makes valid toctree targets.

This script transliterates that R/I impl into Python (`shadow_entries`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH accepted-entry computation (membership in the UNION
`found_docs | generated_docnames`).

We do NOT stand up Sphinx's directive/environment machinery (heavy; the modeled
value is a pure function of the body lines, the existing-doc name set, and the
fixed generated-page name set). Both legs are total functions over the modeled
abstraction; the edge set exhaustively enumerates small inputs over the relevant
name alphabet (blanks, generated names, existing names, unknown names) and the
fuzz loop samples ~1.2e5 random line lists. The discriminating case — a line
naming a generated page that is NOT an existing document — is covered: the oracle
(post-patch) accepts it, while the pre-patch `in found_docs` code would reject it.

stdlib-only. Pinned seed: 10673 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 10673
N = 120_000

# The builder-generated reference pages the patch makes valid toctree targets.
GENERATED = ("genindex", "modindex", "search")
# A small alphabet of candidate line tokens: a blank line, the generated names,
# some ordinary existing-document names, and some unknown names.
TOKENS = ("", "genindex", "modindex", "search", "foo", "bar", "missing", "self_x")
# Candidate "existing documents" sets (found_docs). Note generated names are NOT
# in found_docs (that is the whole point of the fix).
FOUND_SETS = (
    (),
    ("foo",),
    ("foo", "bar"),
)


# --- ORACLE: the post-patch accepted-entry computation, faithful replica -------
def oracle_entries(content, found_docs, generated_pages):
    accept = set(found_docs) | set(generated_pages)
    out = []
    for entry in content:
        if entry == "":
            continue
        elif entry in accept:
            out.append((None, entry))
        else:
            pass  # nonexisting document -> no entry (warning is a side effect)
    return out


# --- shadow of implementation_tocEntries (the R/I leg) ------------------------
# Mirrors Solution.lean op-for-op: a blank skip, then membership in the list
# append `existingDocs ++ generatedPages`, else reject.
def shadow_entries(content, found_docs, generated_pages):
    entries = []
    union = list(found_docs) + list(generated_pages)
    for entry in content:
        if entry == "":
            pass
        elif entry in union:
            entries = entries + [(None, entry)]
        else:
            pass
    return entries


def disagree(content, found, gen):
    got = oracle_entries(content, found, gen)
    want = shadow_entries(content, found, gen)
    if got != want:
        return (content, found, gen, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # Edge set: exhaustive over short line lists (length 0..3) drawn from TOKENS,
    # crossed with the candidate found_docs sets. generated_pages held at the real
    # fixed value GENERATED.
    for found in FOUND_SETS:
        for length in range(0, 4):
            for content in itertools.product(TOKENS, repeat=length):
                d = disagree(list(content), found, GENERATED)
                if d:
                    print(f"DISAGREE exhaustive content={d[0]!r} found={d[1]!r} "
                          f"gen={d[2]!r}: oracle={d[3]} shadow={d[4]}")
                    print("status=fail")
                    return 1
                checked += 1

    # Random fuzz over a wider alphabet and longer line lists, and varying the
    # generated-page set order (membership is order-independent).
    rnd = _lcg(SEED)
    alpha = ("", "genindex", "modindex", "search", "foo", "bar", "baz",
             "qux", "missing", "index", "search", "")
    found_pool = [(), ("foo",), ("foo", "bar"), ("foo", "bar", "baz"),
                  ("genindex",)]  # incl. the corner where a generated name IS a real doc
    gen_pool = [GENERATED, ("search", "genindex", "modindex"), ("genindex",),
                ("modindex", "search")]

    def pick(seq):
        return seq[next(rnd) % len(seq)]

    for _ in range(N):
        length = next(rnd) % 6
        content = [pick(alpha) for _ in range(length)]
        found = pick(found_pool)
        gen = pick(gen_pool)
        d = disagree(content, found, gen)
        if d:
            print(f"DISAGREE fuzz content={d[0]!r} found={d[1]!r} "
                  f"gen={d[2]!r}: oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
