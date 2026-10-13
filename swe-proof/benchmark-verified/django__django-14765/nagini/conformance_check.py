#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14765 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Exsures/Invariant/Assert) stripped. The model IS
Python; the carrier `List[int]` is a plain Python list here, so no shim is
needed. There are no @Pure helpers and no @ContractOnly callees in this
bundle (axioms/pure regions are empty per mapping.md section 3).

ORACLE: the REAL repo function the model models per mapping.md —
`django.db.migrations.state.ProjectState.__init__`, observed through the
`real_apps` argument it processes and the `self.real_apps` attribute it
assigns. The gate applies the diff to /testbed before this script runs
(PYTHONPATH=/testbed); this script never applies any diff itself.

Type bridge (mapping.md section 2, all R-refinements):
  present            <-> the real argument is not None
  is_expected_kind   <-> the runtime kind test: the present argument is an
                         instance of the expected unordered kind (set)
  List[int] carrier  <-> the present collection's membership; each distinct
                         label maps to a distinct int through a per-case
                         bijection (the shadow copies elements opaquely, so
                         the encoding is observation-preserving)
  Result()           <-> the stored attribute; object identity refines to
                         membership equality, so the stored set's membership
                         is compared against the decoded shadow list's
                         membership
  OffKindCollection  <-> the internal-contract violation (AssertionError)
                         the real constructor raises for a present off-kind
                         collection

Requires-satisfying inputs: the model's only precondition is a permission
(read access to the input list), which every concrete Python input satisfies;
the whole (real_apps kind x membership) domain is therefore fair game.
>= 1e5 inputs: structured boundary cases (absent; empty/non-empty sets; a set
subclass; empty/non-empty off-kind collections of several runtime kinds)
plus 100000 fuzz configurations. Pinned fuzz seed: 1476502 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 1476502
N_FUZZ = 100_000


class OffKindCollection(Exception):
    """Shadow-side stand-in for the internal-contract violation construction
    reports when a present collection is not the expected unordered kind."""


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def build_state(real_apps, present, is_expected_kind):
    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        raise OffKindCollection()
    # Present-and-expected: the stored collection preserves the supplied
    # membership unchanged. Materialised here as a same-membership sequence so
    # the result carries full permission while the input stays read-only
    # (refinement.md: the real store is by reference, contents preserved — an
    # R-refinement of object identity to membership equality).
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        result.append(real_apps[i])
        i = i + 1
    return result

# --- end of impl region -------------------------------------------------------


# Outcome codes shared by both sides of the diff.
OUT_NORMAL = "normal"
OUT_OFFKIND = "off-kind-violation"


def shadow_outcome(real_apps_arg):
    """Bridge one real input to the model's inputs, run the shadow, and map
    its observable outcome back to (outcome, stored-membership-of-labels)."""
    present = real_apps_arg is not None
    is_expected_kind = present and isinstance(real_apps_arg, set)
    if is_expected_kind:
        labels = list(real_apps_arg)  # membership, in iteration order
    else:
        # absent, or present off-kind: the carrier's contents are irrelevant
        # on those paths (the shadow returns empty / raises before reading
        # them), and an off-kind input need not even be iterable.
        labels = []
    # per-case bijection label <-> int (the model's List[int] carrier)
    encode = {}
    decode = {}
    encoded = []
    for lab in labels:
        if lab not in encode:
            code = len(encode)
            encode[lab] = code
            decode[code] = lab
        encoded.append(encode[lab])
    try:
        result = build_state(encoded, present, is_expected_kind)
    except OffKindCollection:
        return (OUT_OFFKIND, None)
    return (OUT_NORMAL, frozenset(decode[c] for c in result))


def real_outcome(ProjectState, real_apps_arg):
    """Run the REAL constructor and map its observable outcome: normal
    construction -> the stored attribute's membership; the internal-contract
    violation (AssertionError) -> the off-kind code. Any other exception is
    surfaced as its own outcome string (a disagreement with the shadow)."""
    try:
        state = ProjectState(real_apps=real_apps_arg)
    except AssertionError:
        return (OUT_OFFKIND, None)
    except Exception as exc:  # anything else disagrees with both model paths
        return ("unexpected-exception: %r" % (exc,), None)
    stored = state.real_apps
    if not isinstance(stored, set):
        return ("stored-attribute-not-a-set: %r" % (stored,), None)
    return (OUT_NORMAL, frozenset(stored))


def check_one(ProjectState, real_apps_arg, describe):
    shadow = shadow_outcome(real_apps_arg)
    real = real_outcome(ProjectState, real_apps_arg)
    if shadow != real:
        return ("DISAGREEMENT\n  input real_apps=%s\n  shadow=%r\n  real=%r"
                % (describe, shadow, real))
    return None


class LabelSet(set):
    """A subclass of the expected kind: the runtime kind test accepts it."""


def boundary_cases():
    """Structured cases covering every branch: absent; present expected-kind
    (empty, singleton, many, subclass); present off-kind of assorted runtime
    kinds (empty and non-empty)."""
    cases = []
    # absent
    cases.append(None)
    # present, expected kind
    cases.append(set())
    cases.append({"contenttypes"})
    cases.append({"contenttypes", "auth"})
    cases.append({"a", "b", "c", "d", "e"})
    cases.append({""})  # empty-string label is still a member
    cases.append(LabelSet())
    cases.append(LabelSet({"contenttypes", "sites"}))
    # present, off-kind: ordered / immutable / mapping / other kinds,
    # both empty and non-empty (the kind decides, not the length)
    cases.append(["contenttypes"])
    cases.append([])
    cases.append(["contenttypes", "auth"])
    cases.append(("contenttypes",))
    cases.append(())
    cases.append(frozenset())          # frozen variant is NOT the exact kind
    cases.append(frozenset({"auth"}))
    cases.append({"contenttypes": True})
    cases.append({})
    cases.append("contenttypes")       # a str is iterable but off-kind
    cases.append(0)                    # non-collection objects too
    cases.append(42)
    cases.append(object())
    return cases


LABEL_POOL = ["contenttypes", "auth", "sites", "admin", "sessions",
              "messages", "staticfiles", "myapp", "a", "b", "c", "", "x1",
              "app_with_long_label_name", "UPPER", "unicode_é"]


def fuzz_case(rng):
    kind = rng.randrange(8)
    n = rng.randint(0, 8)
    members = rng.sample(LABEL_POOL, min(n, len(LABEL_POOL)))
    if kind == 0:
        return None
    if kind == 1:
        return set(members)
    if kind == 2:
        return LabelSet(members)
    if kind == 3:
        return list(members)
    if kind == 4:
        return tuple(members)
    if kind == 5:
        return frozenset(members)
    if kind == 6:
        return dict.fromkeys(members)
    return rng.choice([rng.randint(-5, 5), object(), rng.choice(LABEL_POOL)])


def main():
    # REAL repo symbol (the constructor the model models, per mapping.md):
    from django.db.migrations.state import ProjectState

    checked = 0
    n_boundary = 0
    for arg in boundary_cases():
        err = check_one(ProjectState, arg, repr(arg))
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        arg = fuzz_case(rng)
        err = check_one(ProjectState, arg, repr(arg))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real constructor's collection handling "
          "on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
