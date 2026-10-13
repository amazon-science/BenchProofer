#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15732.

This bundle consumes NO `@ContractOnly` axiom: the discovery of the candidate
constraint-name set and the generation of the composed rule's default name are
UNCHANGED upstream operations whose results are passed into the modeled
function as inputs. The single CHANGED operation — the disambiguating selection
over those inputs inside `_delete_composed_index` — is modeled DEEPLY by
`select_constraint_to_remove` in model.py. G-AX therefore validates that deep
model as an A-REFERENCE: the modeled selection must be observationally equal,
on every input, to the gold patch's exact selection algorithm.

The gold patch's selection logic (django/db/backends/base/schema.py,
`_delete_composed_index`, post-patch) is, after the candidate set
`constraint_names` has been discovered:

    if (
        constraint_kwargs.get("unique") is True
        and constraint_names
        and self.connection.features.allows_multiple_constraints_on_same_fields
    ):
        default_name = str(self._unique_constraint_name(table, columns, quote=False))
        if default_name in constraint_names:
            constraint_names = [default_name]
    if len(constraint_names) != 1:
        raise ValueError("Found wrong number (...) of constraints ...")
    # delete constraint_names[0]

This is a pure decision over (candidates, default_name, unique, feature_on); it
needs no DB. We re-express it verbatim as `gold_select` and assert the deep
model `model_select` (a faithful transcription of model.py's verified impl)
equals it — same returned name, same raise — on boundary + fuzz inputs,
including the two F2P/P2P scenarios this issue is about. Imports nothing
repo-specific (stdlib only). Exit 0 iff every observation matches.
"""
import random
import sys


class WrongConstraintCount(Exception):
    """Stand-in for the ValueError the gold raises on a non-resolvable set."""


# --- gold selection algorithm (verbatim transcription of the gold patch) -----

def gold_select(candidates, default_name, unique, feature_on):
    """Exactly the post-patch `_delete_composed_index` selection, as a pure
    function over the already-discovered inputs. Returns the constraint name to
    delete, or raises on a wrong count."""
    names = list(candidates)
    if unique is True and names and feature_on:
        if default_name in names:
            names = [default_name]
    if len(names) != 1:
        raise WrongConstraintCount(
            "Found wrong number (%s) of constraints" % len(names)
        )
    return names[0]


# --- deep model (faithful transcription of model.py's verified impl) ----------

def disambiguates(unique, feature_on, n_candidates):
    # model.py pure helper
    return bool(unique) and bool(feature_on) and n_candidates >= 1


def model_select(candidates, default_name, unique, feature_on):
    """Transcription of model.py `select_constraint_to_remove` impl region."""
    narrowed_to_default = False
    if disambiguates(unique, feature_on, len(candidates)):
        if default_name in candidates:
            narrowed_to_default = True
    if narrowed_to_default:
        return default_name
    if len(candidates) == 1:
        return candidates[0]
    raise WrongConstraintCount()


# --- the check ----------------------------------------------------------------

def observe(fn, candidates, default_name, unique, feature_on):
    """Return ('ok', name) or ('raise', None)."""
    try:
        return ("ok", fn(list(candidates), default_name, unique, feature_on))
    except WrongConstraintCount:
        return ("raise", None)


def check(candidates, default_name, unique, feature_on):
    g = observe(gold_select, candidates, default_name, unique, feature_on)
    m = observe(model_select, candidates, default_name, unique, feature_on)
    assert g == m, (
        "deep model disagrees with gold selection on "
        "candidates=%r default_name=%r unique=%r feature_on=%r: "
        "gold=%r model=%r" % (candidates, default_name, unique, feature_on, g, m)
    )


def main():
    # Name ids: 1 = composed-rule default ("_uniq"); 2 = independent unique
    # ("_key"); 3 = primary key; others arbitrary.
    UNIQ, KEY, PK = 1, 2, 3

    boundary = []
    for unique in (True, False):
        for feature_on in (True, False):
            for default_name in (UNIQ, 99):
                boundary += [
                    ([], default_name, unique, feature_on),            # none found
                    ([UNIQ], default_name, unique, feature_on),        # sole = default
                    ([KEY], default_name, unique, feature_on),         # sole != default
                    # F2P: unique_together on a unique=True field -> _uniq + _key
                    ([UNIQ, KEY], default_name, unique, feature_on),
                    ([KEY, UNIQ], default_name, unique, feature_on),
                    # P2P: unique_together on a pk field, after pk excluded by the
                    # primary_key=False filter -> just _uniq (sole candidate)
                    ([UNIQ], default_name, unique, feature_on),
                    # several, none the default -> never resolvable
                    ([KEY, PK], default_name, unique, feature_on),
                    ([KEY, PK, 7], default_name, unique, feature_on),
                    # several incl. default among >2
                    ([UNIQ, KEY, PK], default_name, unique, feature_on),
                ]
    for c in boundary:
        check(*c)

    # Two explicit named F2P/P2P scenarios with the real disambiguation on:
    # remove unique_together on a unique=True field: both _uniq and _key exist,
    # feature on, unique removal -> must pick the _uniq (default) name.
    g = observe(gold_select, [UNIQ, KEY], UNIQ, True, True)
    m = observe(model_select, [UNIQ, KEY], UNIQ, True, True)
    assert g == ("ok", UNIQ) and m == ("ok", UNIQ), (g, m)
    # remove unique_together on a pk field: pk excluded upstream by
    # primary_key=False, so only _uniq is discovered -> sole-candidate path.
    g = observe(gold_select, [UNIQ], UNIQ, True, True)
    m = observe(model_select, [UNIQ], UNIQ, True, True)
    assert g == ("ok", UNIQ) and m == ("ok", UNIQ), (g, m)
    # pre-patch behaviour would raise on [UNIQ, KEY]; confirm gold does NOT.
    assert observe(gold_select, [UNIQ, KEY], UNIQ, True, True)[0] == "ok"

    # --- randomized fuzz over candidate sets, default, and both flags --------
    rng = random.Random(15732)
    pool = list(range(0, 8))
    for _ in range(200000):
        n = rng.randint(0, 5)
        candidates = [rng.choice(pool) for _ in range(n)]
        default_name = rng.choice(pool)
        unique = rng.choice([True, False])
        feature_on = rng.choice([True, False])
        check(candidates, default_name, unique, feature_on)

    print("G-AX OK: deep model select_constraint_to_remove == gold "
          "_delete_composed_index selection on %d boundary + 200000 fuzz "
          "inputs (incl. F2P unique-field and P2P pk-field scenarios), "
          "0 disagreements" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
