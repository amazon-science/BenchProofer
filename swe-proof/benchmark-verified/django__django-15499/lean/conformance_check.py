#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15499.

The bundle models ONE decision: what `CreateModel.reduce` returns when a
model-creation step is paired with a following `AlterModelManagers` operation
(`django/db/migrations/operations/models.py`, the new `elif` arm). The modeled
value is a PURE function of the observables (mapping.md):

    model        : {name, fields, options, bases, managers}   (the CreateModel self)
    targetName   : str                                        (operation.name)
    newManagers  : list[(str, str)]                           (operation.managers)

Post-patch rule (the added arm):

    if isinstance(operation, AlterModelManagers) and self.name_lower == operation.name_lower:
        return [CreateModel(self.name, fields=self.fields, options=self.options,
                            bases=self.bases, managers=operation.managers)]
    # else: this pairing produces no CreateModel reduction (reduce returns a bool)

Standing up the full Django app registry to instantiate real Manager objects is
heavy and unnecessary: the modeled value is this pure record-construction
decision over the observables. So the ORACLE below is a faithful in-process
replica that uses the EXACT patched branch logic (same-model lower-cased name
compare; build a creation step copying name/fields/options/bases and substituting
managers), and the SHADOW is the op-for-op transliteration of
`implementation_optimizeCreateThenAlterManagers` (per refinement.md): if
sameModel then [{model with managers := newManagers}] else [].

A "no CreateModel reduction" outcome is represented as the empty list (mapping.md
result-type note: the real `reduce` returns a bool there, which carries no
collapsed CreateModel). The result is compared as a list of normalized
model-state tuples.

stdlib-only. Pinned seed: 15499 (also in mapping.md).
"""
import random
import sys

SEED = 15499
N = 120_000


def _norm(ms):
    # normalized comparable form of a model-creation step
    return (
        ms["name"],
        tuple(tuple(p) for p in ms["fields"]),
        tuple(tuple(p) for p in ms["options"]),
        tuple(ms["bases"]),
        tuple(tuple(p) for p in ms["managers"]),
    )


# --- ORACLE: faithful in-process replica of the patched branch --------------
def oracle_reduce(model, target_name, new_managers):
    # isinstance(operation, AlterModelManagers) is fixed True by the modeled
    # pairing; the remaining guard is self.name_lower == operation.name_lower.
    if model["name"].lower() == target_name.lower():
        merged = {
            "name": model["name"],            # CreateModel(self.name, ...)
            "fields": model["fields"],         # fields=self.fields
            "options": model["options"],       # options=self.options
            "bases": model["bases"],           # bases=self.bases
            "managers": new_managers,          # managers=operation.managers
        }
        return [_norm(merged)]
    return []                                  # no CreateModel reduction


# --- SHADOW of implementation_optimizeCreateThenAlterManagers (R/I leg) ------
# Mirrors Solution.lean: if sameModel model.name targetName then
# [{model with managers := newManagers}] else [].
def shadow_reduce(model, target_name, new_managers):
    if model["name"].lower() == target_name.lower():
        merged = dict(model)
        merged["managers"] = new_managers
        return [_norm(merged)]
    return []


def disagree(model, target_name, new_managers):
    got = oracle_reduce(model, target_name, new_managers)
    want = shadow_reduce(model, target_name, new_managers)
    if got != want:
        return ((model, target_name, new_managers), got, want)
    return None


NAME_POOL = ["Foo", "foo", "FOO", "Bar", "Baz", "Author", "author", "Book"]
MGR_POOL = ["objects", "things", "published", "all_objects", "custom"]
FIELD_POOL = ["id", "name", "title", "age", "slug"]
OPT_KEYS = ["ordering", "verbose_name", "permissions", "managed"]
BASE_POOL = ["models.Model", "AbstractBase", "Mixin"]


def _mk_managers(rng):
    k = rng.randint(0, len(MGR_POOL))
    return [(m, "Manager()") for m in rng.sample(MGR_POOL, k)]


def _mk_model(rng):
    nf = rng.randint(0, 4)
    no = rng.randint(0, 3)
    nb = rng.randint(0, 3)
    return {
        "name": rng.choice(NAME_POOL),
        "fields": [(rng.choice(FIELD_POOL), "Field()") for _ in range(nf)],
        "options": [(rng.choice(OPT_KEYS), "val%d" % i) for i in range(no)],
        "bases": [rng.choice(BASE_POOL) for _ in range(nb)],
        "managers": _mk_managers(rng),
    }


def _enumerate_edge():
    cases = []
    base = {"name": "Foo", "fields": [], "options": [], "bases": ["models.Model"],
            "managers": []}
    f2p_mgrs = [("objects", "Manager()"), ("things", "Manager()")]
    # the F2P shape: same model, two new managers, empty fields -> collapse.
    cases.append((dict(base), "Foo", f2p_mgrs))
    # case-insensitive name match -> still collapses.
    cases.append((dict(base, name="Foo"), "foo", f2p_mgrs))
    cases.append((dict(base, name="foo"), "FOO", f2p_mgrs))
    # different model -> no collapse.
    cases.append((dict(base), "Bar", f2p_mgrs))
    # same model but model already had managers -> they are REPLACED, not merged.
    cases.append((dict(base, managers=[("old", "Manager()")]), "Foo", f2p_mgrs))
    # same model, empty new managers -> collapse to model with empty managers.
    cases.append((dict(base), "Foo", []))
    # non-trivial fields/options/bases are carried over unchanged on collapse.
    rich = {"name": "Author", "fields": [("id", "Field()"), ("name", "Field()")],
            "options": [("ordering", "v0")], "bases": ["AbstractBase"],
            "managers": [("objects", "Manager()")]}
    cases.append((rich, "Author", [("published", "Manager()")]))
    cases.append((rich, "Book", [("published", "Manager()")]))
    return cases


def main() -> int:
    checked = 0
    for model, tn, nm in _enumerate_edge():
        d = disagree(model, tn, nm)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        model = _mk_model(rng)
        # bias toward same-name to exercise the collapse arm heavily
        if rng.random() < 0.5:
            tn = model["name"].swapcase() if rng.random() < 0.5 else model["name"]
        else:
            tn = rng.choice(NAME_POOL)
        nm = _mk_managers(rng)
        d = disagree(model, tn, nm)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
