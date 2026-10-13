#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-7440.

Validates the ONE kind-A obligation of this bundle (refinement.md A2,
mapping.md §3.1):

  (A-reference) the deep model `registeredKey` (Solution.lean pure region) ==
      the REAL object-registry round-trip. `registeredKey` claims the key under
      which a glossary term becomes observable is the term text VERBATIM — case
      preserved, no normalization. The real registry is exercised directly:

          StandardDomain.note_object('term', name, node_id, location=None)
          -> later -> StandardDomain.get_objects()  yields  (name, name, 'term', …)

      We assert that for every `name` registered, `get_objects()` reports that
      exact `name` back, unchanged (so the registry is identity-on-name, which is
      what `registeredKey = id` encodes). If the registry case-folded or otherwise
      normalized the key, this check would fail and expose the model as unsound.

The function under change (`make_glossary_term`) is NOT axiomatized here; only the
unchanged registry it calls is. Imports the repo under test (`sphinx`) + stdlib.
Exit 0 iff every obligation holds.
"""
import random
import sys

from sphinx.domains.std import StandardDomain


# --- a minimal BuildEnvironment stub: just enough for StandardDomain ----------
# StandardDomain.__init__ touches env.domaindata, env.app.registry.enumerable_nodes;
# get_objects touches env.all_docs / env.titles (kept empty); note_object uses
# env.docname. Nothing here influences how a registered name is keyed or echoed.

class _Registry:
    enumerable_nodes = {}


class _App:
    registry = _Registry()


class _Env:
    def __init__(self):
        self.domaindata = {}
        self.docname = "index"
        self.all_docs = {}
        self.titles = {}
        self.app = _App()


def fresh_domain():
    return StandardDomain(_Env())


# --- the deep model (Solution.lean `registeredKey`) ---------------------------

def registered_key(term_text):
    """registeredKey: the term text verbatim (identity)."""
    return term_text


# --- the check ----------------------------------------------------------------

def check_registry_identity(names):
    """Register each name as a 'term' in a fresh real StandardDomain, then assert
    get_objects() reports it back verbatim — i.e. recorded/reported key ==
    registered_key(name) == name (the A-reference)."""
    dom = fresh_domain()
    for i, name in enumerate(names):
        # node_id is irrelevant to the key; make it unique and well-formed.
        dom.note_object('term', name, 'term-%d' % i, location=None)

    # collect the keys the registry reports for the 'term' object type
    reported = {}
    for entry in dom.get_objects():
        name, dispname, typ = entry[0], entry[1], entry[2]
        if typ == 'term':
            reported.setdefault(name, dispname)

    for name in names:
        key = registered_key(name)
        assert key in reported, (
            "registry dropped term %r: get_objects() reported keys %r; "
            "deep model registeredKey(%r)=%r expected present"
            % (name, sorted(reported), name, key))
        # get_objects yields (name, name, …): reported name == display name == key
        assert reported[key] == key, (
            "registry altered term key %r: get_objects() reported display %r "
            "for key %r (expected verbatim)" % (name, reported[key], key))
        # the verbatim key must be exactly the term text the model returns
        assert key == name, (
            "deep model registeredKey unsound: registeredKey(%r)=%r, "
            "real registry keys verbatim" % (name, key))


def main():
    # --- boundary names: the F2P terms, mixed case, separators, unicode -------
    boundary = [
        "term1", "TERM2", "term3", "term4",      # the four F2P glossary terms
        "MySQL", "mysql", "MYSQL",               # the issue's motivating case
        "a", "A", "Z", "z",
        "Term", "TERM", "tErM",
        "term with spaces", "Term : classifier",
        "term-4", "term_4", "TERM-4",
        "café", "CAFÉ", "Straße", "Ω", "ω",
        "0", "9term", "Term9",
    ]
    # register them all together in one domain (also exercises distinctness:
    # 'mysql' and 'MySQL' and 'MYSQL' must remain three separate keys)
    check_registry_identity(boundary)
    # and each one alone (no interaction effects)
    for name in boundary:
        if name:
            check_registry_identity([name])

    # distinct-case keys are NOT merged: registering three case variants must
    # leave three reported keys (the bug was collapsing them under .lower()).
    dom = fresh_domain()
    for i, nm in enumerate(["mysql", "MySQL", "MYSQL"]):
        dom.note_object('term', nm, 'term-%d' % i, location=None)
    term_keys = sorted(e[0] for e in dom.get_objects() if e[2] == 'term')
    assert term_keys == ["MYSQL", "MySQL", "mysql"], (
        "case-distinct term keys collapsed: %r" % term_keys)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(7440)
    alphabet = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_")
    alphabet += ["é", "Ω", "ß", "•"]
    for _ in range(20000):
        n = rng.randint(1, 24)
        name = "".join(rng.choice(alphabet) for _ in range(n))
        check_registry_identity([name])

    print("G-AX OK: registeredKey deep model (== real StandardDomain "
          "note_object/get_objects round-trip, identity-on-name) sound on "
          "%d boundary + 20000 fuzz term names; case-distinct keys preserved."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
