#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadows of
implementation_glossaryTermEntry and implementation_termXrefTarget against the
patch.diff behaviour.

Both impl regions are straight-line: they pass the term/reference text through
unchanged (preserving exact characters, including case). Every op is I (identical
concrete control flow) or R (Python `str` per-code-point ↔ Lean `List Char`
identity). The shadow reproduces the post-patch behaviour op-for-op; we assert
zero disagreements vs an independent reconstruction of the two patched sites over
>= 10^5 fuzzed inputs.

A glossary term / reference text is modeled as a `List Char`; here strings stand
in for it. Inputs are fuzzed over ASCII (mixed upper/lower/digit/punct/space),
where CPython `str.lower()` coincides with the Lean ASCII `Char.toLower` used in
the prepatch (buggy) variants — see mapping.md ASCII fuzz note.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 7440
N = 120_000           # >= 10^5

_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789 _-:."
)


# ---- Lean models (the R/I shadow of the post-patch impls) ---------------

def shadow_glossary_term_entry(termtext):
    """R/I shadow of implementation_glossaryTermEntry (make_glossary_term).
    Returns (key, index_term)."""
    key = termtext              # let key := termtext
    index_term = termtext       # let indexTerm := termtext
    return (key, index_term)


def shadow_term_xref_target(target):
    """R/I shadow of implementation_termXrefTarget (the 'term' role target)."""
    return target               # return target


# ---- Independent reconstruction of the patched sites --------------------

def patched_glossary_term_entry(termtext):
    """Post-patch sphinx/domains/std.py make_glossary_term:
        std.note_object('term', termtext, node_id, ...)   # key = termtext
        indexnode['entries'] = [('single', termtext, ...)] # index term = termtext
    Both the registration key and the index entry term are the un-folded
    `termtext`. We model the two term-derived values as a pair."""
    key = termtext                       # was termtext.lower() pre-patch
    index_term = termtext                # unchanged frame component
    return (key, index_term)


def patched_term_xref_target(target):
    """Post-patch sphinx/domains/std.py: the 'term' role is XRefRole(... ) with
    no lowercase flag, so create_xref_node leaves `target` as written:
        if self.lowercase:   # False for 'term' post-patch
            target = target.lower()
    """
    lowercase = False                    # 'term' role flag, post-patch
    if lowercase:
        target = target.lower()
    return target


def main() -> int:
    rnd = random.Random(SEED)
    disagreements = 0
    examples = []
    for _ in range(N):
        length = rnd.randint(0, 24)
        s = "".join(rnd.choice(_ALPHABET) for _ in range(length))

        if shadow_glossary_term_entry(s) != patched_glossary_term_entry(s):
            disagreements += 1
            if len(examples) < 10:
                examples.append(("glossaryTermEntry", s))
        if shadow_term_xref_target(s) != patched_term_xref_target(s):
            disagreements += 1
            if len(examples) < 10:
                examples.append(("termXrefTarget", s))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements (seed={SEED})")
        for site, ex in examples:
            print(f"  {site}: {ex!r}")
        return 1
    print(f"G-CONF OK: {N} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
