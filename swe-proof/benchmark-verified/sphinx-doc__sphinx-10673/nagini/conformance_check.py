#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-10673 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped, plus the @Pure helpers
`mem` / `known` / `kept` copied over as plain functions. `PSeq[int]` /
`ToSeq(list)` are realised by a tiny immutable-sequence shim providing exactly
the operations the model uses (len, [0]/[i], drop, take, +, ==). There is no
@ContractOnly callee in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`sphinx.directives.other.TocTree.parse_content` (the per-entry classification
loop that decides which listed targets are retained in the resulting entry
list). The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched code importable. `parse_content` is a
method reading only `self.env`, `self.config` and `self.content`, so it is
invoked unbound on a stub carrier object:

  * `self.content` is the fuzzed list of target names, in order;
  * `self.env.found_docs` is the fuzzed discovered-document family (plus the
    current document's own name, which the method always removes from its
    working copy and which is outside the bridged id space);
  * the always-provided reference-page family is what the method derives from
    `self.env.domains['std'].initial_data['labels']`; the stub env exposes a
    label table whose keys are the fuzzed generated-family names — injecting
    the family here is exactly the modeling boundary (the model takes it as
    an input list). One boundary scenario additionally uses the REAL
    `StandardDomain.initial_data['labels']` keys as the generated family, so
    the true provenance is exercised at least once;
  * `self.env.doc2path` / `note_reread` are inert stubs (the rejection branch
    calls them for diagnostics only); `exclude_patterns` is empty and the
    glob flag is off — glob patterns, URL targets, 'self' targets and
    suffix-stripping are outside the modeled domain (mapping.md §2), and the
    bridged names are chosen so every normalization step is the identity.

TYPE BRIDGE (mapping.md §2): document names are modeled as opaque int ids;
the bridge maps each id injectively to a distinct plain name ("n<id>") that
carries no source suffix, no URL shape, no glob character and no path
separator, so equality/membership of ids matches equality/membership of
names exactly. The oracle's output is the ordered list of retained docnames
in the toctree node's entry list, mapped back to ids and compared with `==`.

INPUT DOMAIN (the model's Requires): any three int lists. Boundary cases
mirror the empty/singleton/duplicate/mixed-family grid of axiom_check.py;
fuzz draws small lists over a small id domain so the families and the
targets overlap frequently.

>= 1e5 Requires-satisfying inputs: 16 boundary + 100000 fuzz triples.
Pinned fuzz seed: 106731.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import logging
import random
import sys

# the rejection/duplicate branches emit diagnostics through the logging
# module; silence them so 100k fuzz cases don't flood stderr
logging.disable(logging.CRITICAL)

SEED = 106731
N_FUZZ = 100_000


# --- PSeq / ToSeq shim (immutable sequence with the ops the model uses) ------

class Seq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _from(cls, it):
        s = cls()
        s._t = tuple(it)
        return s

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def drop(self, n):
        return Seq._from(self._t[n:])

    def take(self, n):
        return Seq._from(self._t[:n])

    def __add__(self, other):
        return Seq._from(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, Seq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


PSeq = Seq


def ToSeq(lst):
    return Seq._from(lst)


# --- pure helpers from model.py, decorators + contracts stripped -------------

def mem(x, s):
    if len(s) == 0:
        return False
    return s[0] == x or mem(x, s.drop(1))


def known(x, found, gen):
    return mem(x, found) or mem(x, gen)


def kept(entries, found, gen):
    if len(entries) == 0:
        return PSeq(0).take(0)
    if known(entries[0], found, gen):
        return PSeq(entries[0]) + kept(entries.drop(1), found, gen)
    return kept(entries.drop(1), found, gen)


# --- the impl region of model.py, verbatim (contract calls stripped) ---------

def select_toctree_entries(entries, found, generated):
    result = []  # type: list
    i = len(entries)
    while i > 0:
        x = entries[i - 1]
        cons = PSeq(x) + ToSeq(entries).drop(i)
        if known(x, ToSeq(found), ToSeq(generated)):
            old_seq = ToSeq(result)
            result = [x] + result
        else:
            pass
        i = i - 1
    return result


# --- oracle: the real patched per-entry classification -----------------------

class _StubEnv:
    """Carrier for the collaborators parse_content reads off self.env."""

    def __init__(self, docname, found_docs, generated_labels):
        self.docname = docname
        self.found_docs = found_docs
        self.domains = {"std": _StubDomain(generated_labels)}

    def doc2path(self, docname, base=True):
        return docname + ".rst"

    def note_reread(self):
        pass


class _StubDomain:
    def __init__(self, labels):
        self.initial_data = {"labels": labels}


class _StubConfig:
    source_suffix = [".rst"]
    exclude_patterns = []


class _StubSelf:
    def __init__(self, env, content):
        self.env = env
        self.config = _StubConfig()
        self.content = content
        self.options = {}


CURRENT_DOC = "index"  # the directive's own document; outside the id space


def _name(i):
    # injective id -> plain docname: no suffix, no URL, no glob char, no '/',
    # never equal to the current document's name or the literal 'self'
    return "n%d" % i


def real_select(parse_content, entries_ids, found_ids, gen_ids,
                gen_names_override=None):
    """Run the REAL patched parse_content and return the ids of the retained
    targets, in order."""
    if gen_names_override is not None:
        # a fixed name table for the generated family (real provenance case)
        gname = dict(gen_names_override)
    else:
        gname = {i: _name(i) for i in gen_ids}
    name_of = {}
    for i in found_ids + entries_ids:
        name_of[i] = gname.get(i, _name(i))
    for i in gen_ids:
        name_of[i] = gname[i]
    id_of = {v: k for k, v in name_of.items()}

    entry_names = [name_of[i] for i in entries_ids]
    found_docs = {name_of[i] for i in found_ids} | {CURRENT_DOC}
    labels = {name_of[i]: (name_of[i], "", name_of[i]) for i in gen_ids}

    env = _StubEnv(CURRENT_DOC, found_docs, labels)
    carrier = _StubSelf(env, entry_names)
    toctree = {"glob": False, "entries": [], "includefiles": []}
    parse_content(carrier, toctree)
    return [id_of[docname] for (_title, docname) in toctree["entries"]]


def check_case(parse_content, entries, found, generated,
               gen_names_override=None):
    shadow_out = select_toctree_entries(entries, found, generated)
    real_out = real_select(parse_content, entries, found, generated,
                           gen_names_override)
    if shadow_out != real_out:
        return ("DISAGREEMENT\n  entries=%r found=%r generated=%r\n"
                "  shadow=%r\n  real=%r"
                % (entries, found, generated, shadow_out, real_out))
    return None


def boundary_cases():
    return [
        ([], [], []),
        ([1], [], []),                 # in neither family -> rejected
        ([1], [1], []),                # discovered only -> retained
        ([1], [], [1]),                # reference-page family only -> retained
        ([1, 1], [], [1]),             # duplicate listed target, kept twice
        ([1, 1], [1], []),             # duplicate over the discovered family
        ([1, 2, 3], [2], [3]),         # mixed: 1 rejected, 2 and 3 retained
        ([3, 2, 1], [2], [3]),         # order preserved
        ([5], [5], [5]),               # name in both families
        ([1, 2, 3, 4, 5], [1, 2], [3, 4]),
        ([2, 9, 2, 9, 2], [2], []),    # interleaved duplicates
        ([7], [7, 7, 7], []),          # duplicated family members
        ([4], [], [4, 4]),
        ([0], [0], []),                # id 0
        ([10, 11, 12, 13], [], [11, 13]),
    ]


def main():
    from sphinx.directives.other import TocTree
    parse_content = TocTree.parse_content

    checked = 0
    for entries, found, generated in boundary_cases():
        err = check_case(parse_content, entries, found, generated)
        if err:
            print(err)
            return 1
        checked += 1

    # real-provenance scenario: the generated family is the REAL standard
    # domain's always-provided label table (imported from the patched repo),
    # its members absent from the discovered family yet all retained in order
    from sphinx.domains.std import StandardDomain
    real_labels = sorted(StandardDomain.initial_data["labels"].keys())
    gen_ids = list(range(100, 100 + len(real_labels)))
    override = dict(zip(gen_ids, real_labels))
    err = check_case(parse_content, gen_ids + [1, 999], [1], gen_ids,
                     gen_names_override=override)
    if err:
        print(err)
        return 1
    checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        nf = rng.randint(0, 8)
        ng = rng.randint(0, 4)
        ne = rng.randint(0, 12)
        # small id domain so the families overlap with the targets frequently
        found = [rng.randint(0, 20) for _ in range(nf)]
        generated = [rng.randint(0, 20) for _ in range(ng)]
        entries = [rng.randint(0, 20) for _ in range(ne)]
        err = check_case(parse_content, entries, found, generated)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real retained-entry classification on "
          "%d inputs (%d boundary + 1 real-provenance + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
