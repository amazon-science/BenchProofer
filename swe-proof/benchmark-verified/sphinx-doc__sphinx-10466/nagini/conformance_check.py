#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10466 (nagini).

SHADOW: the impl regions of model.py (`insert_sorted` and `canonical_positions`),
copied verbatim below with the contract calls (Requires/Ensures/Invariant/
Assert) stripped. At runtime those bodies use only plain Python lists, so no
sequence shim is needed on the shadow path; the @Pure helpers `ins`/`dedup_sort`
(which are stated over PSeq) copy over on top of a small immutable-tuple PSeq
shim and are exercised as an internal cross-check on the boundary inputs only.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo behaviour the model models per mapping.md — the
position list that `sphinx.builders.gettext.Catalog.__iter__` builds for a
message from its recorded occurrence metadata and hands to `Message` (read back
via `Message.locations`, which stores the list content unchanged). The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched module importable. For each generated input a Catalog is
populated with one message whose metadata holds exactly the generated
occurrence list (source, line, uuid triples, uuids synthetic), then iterated.
One boundary case additionally goes through the public `Catalog.add` /
`MsgOrigin` API to confirm the direct-population harness feeds `__iter__` the
same shape the public path does.

TYPE BRIDGE (mapping.md section 2): a position is a `(source, line)` tuple; the
model carries it as a single integer key under the order- and equality-
preserving identification "tuple -> its index in the sorted-distinct universe
of the input's tuples". The modeled operation observes only `<` and `==` on
elements, so the bijection is observationally exact (validated independently by
axiom_check.py). Here each input's tuples are encoded to keys, the shadow runs
on the key list, and the shadow output is decoded back to tuples for the
element-for-element comparison with the real reported list.

INPUT DOMAIN: the Requires is just list permission — any finite list of keys.
Real occurrence lists are finite lists of (source: str, line: int) pairs, in
scan order, duplicates allowed (the same place may be recorded repeatedly).
Generation draws sources from small pools (plus random strings, so
lexicographic ordering among sources is well exercised) and small line ranges,
making duplicates and per-source line ties frequent.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz lists.
Pinned fuzz seed: 1046600.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random).
"""
import json
import random
import sys

SEED = 1046600
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(xs):
    return PSeq._wrap(xs)


# --- pure region of model.py, copied verbatim (decorators dropped) -----------

def ins(x, s):
    if len(s) == 0:
        return PSeq(x)
    if x < s[0]:
        return PSeq(x) + s
    if x == s[0]:
        return s
    return PSeq(s[0]) + ins(x, s.drop(1))


def dedup_sort(s):
    if len(s) == 0:
        return PSeq(0).take(0)
    return ins(s[len(s) - 1], dedup_sort(s.take(len(s) - 1)))


# --- impl regions of model.py, verbatim, contract calls stripped -------------

def insert_sorted(xs, key):
    # impl-start
    # Scan front-to-back, emitting each element until the slot for `key` is
    # found.
    out = []  # type: list
    j = 0
    placed = False  # type: bool
    while j < len(xs):
        cur = xs[j]
        if placed:
            out = out + [cur]
        elif cur < key:
            out = out + [cur]
        elif cur > key:
            out = out + [key]
            out = out + [cur]
            placed = True
        else:
            out = out + [cur]
            placed = True
        j = j + 1
    if not placed:
        out = out + [key]
    return out
    # impl-end


def canonical_positions(recorded):
    # impl-start
    result = []  # type: list
    i = 0
    while i < len(recorded):
        key = recorded[i]
        result = insert_sorted(result, key)
        i = i + 1
    return result
    # impl-end


# --- oracle: the patched repo behaviour ---------------------------------------

def real_positions(gettext_mod, pairs):
    """Reported position list the patched Catalog.__iter__ produces for one
    message whose metadata records exactly `pairs` (in that order, duplicates
    kept), read back through Message.locations."""
    cat = gettext_mod.Catalog()
    msg = "conformance-probe"
    cat.messages.append(msg)
    cat.metadata[msg] = [(source, line, "uid%d" % k)
                         for k, (source, line) in enumerate(pairs)]
    out = list(cat)
    assert len(out) == 1, "harness drift: expected exactly one message"
    return list(out[0].locations)


def real_positions_public_api(gettext_mod, pairs):
    """Same observable, but populated through the public add()/MsgOrigin path
    (sanity check that direct metadata population matches the public path)."""
    cat = gettext_mod.Catalog()
    msg = "conformance-probe"
    for source, line in pairs:
        cat.add(msg, gettext_mod.MsgOrigin(source, line))
    out = list(cat)
    assert len(out) == 1, "harness drift: expected exactly one message"
    return list(out[0].locations)


# --- bridge + differential check ----------------------------------------------

def check_pairs(gettext_mod, pairs, cross_check_pure=False):
    """Encode `pairs` to integer keys (order/equality-preserving), run the
    shadow on the keys, decode, and compare with the real reported list.
    Returns an error string on disagreement, else None."""
    universe = sorted(set(pairs))
    key_of = {t: k for k, t in enumerate(universe)}
    inv = {k: t for t, k in key_of.items()}
    keys = [key_of[t] for t in pairs]        # Requires: a plain list of ints

    shadow_keys = canonical_positions(keys)  # shadow (impl region)
    decoded = [inv[k] for k in shadow_keys]

    real = real_positions(gettext_mod, pairs)  # oracle (patched repo)

    if decoded != real:
        return ("DISAGREEMENT\n  recorded pairs=%r\n  keys=%r\n"
                "  shadow(decoded)=%r\n  real=%r"
                % (pairs, keys, decoded, real))
    if cross_check_pure:
        # internal consistency: the impl region computes the pure dedup_sort
        # (boundary inputs only; the oracle comparison above is the verdict).
        if ToSeq(shadow_keys) != dedup_sort(ToSeq(keys)):
            return ("SHADOW SELF-INCONSISTENCY\n  keys=%r\n  impl=%r\n  pure=%r"
                    % (keys, shadow_keys, list(dedup_sort(ToSeq(keys))._t)))
    return None


def boundary_inputs():
    a, b, c = "/a.rst", "/b.rst", "../rel/c.rst"
    return [
        [],                                        # message with no occurrences
        [(a, 1)],
        [(a, 1), (a, 1)],                          # same place twice
        [(a, 1), (a, 1), (a, 2), (b, 1)],          # duplicate + others, in scan order
        [(b, 9), (a, 3), (b, 1), (a, 3)],          # unsorted arrival, repeats
        [(a, 2), (a, 1)],                          # same source, lines reversed
        [(b, 1), (a, 1)],                          # same line, sources reversed
        [(a, 1), (b, 1), (c, 1)],                  # source-only ordering
        [(a, 0), (a, 0), (a, 0), (a, 0)],          # all duplicates, line 0
        [(c, 5), (b, 5), (a, 5), (c, 5), (b, 5)],
        [(a, i) for i in range(10, 0, -1)],        # strictly descending lines
        [(a, 1), (a, 1)] * 8,                      # heavy multiplicity
    ]


def rand_input(rng, sources, max_len=20, max_line=150):
    n = rng.randint(0, max_len)
    out = []
    for _ in range(n):
        if rng.random() < 0.1:
            # occasional arbitrary source string: exercises lexicographic order
            src = "".join(rng.choice("abz/._-") for _ in range(rng.randint(1, 12)))
        else:
            src = rng.choice(sources)
        line = rng.randint(0, max_line) if rng.random() < 0.5 else rng.randint(0, 8)
        out.append((src, line))
    return out


def main():
    sys.path.insert(0, "/testbed")
    from sphinx.builders import gettext as gettext_mod  # REAL patched module

    checked = 0
    boundary = boundary_inputs()
    for pairs in boundary:
        err = check_pairs(gettext_mod, pairs, cross_check_pure=True)
        if err:
            print(err)
            return 1
        checked += 1

    # public-API harness sanity on one non-trivial boundary case
    pairs = boundary[3]
    if real_positions(gettext_mod, pairs) != real_positions_public_api(gettext_mod, pairs):
        print("HARNESS DRIFT: direct population != public add()/MsgOrigin path on %r" % (pairs,))
        return 1

    rng = random.Random(SEED)
    sources = ["/a.rst", "/b.rst", "/c.rst", "../../m/one.rst", "../../m/two.rst"]
    for _ in range(N_FUZZ):
        err = check_pairs(gettext_mod, rand_input(rng, sources))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real reported position list on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
