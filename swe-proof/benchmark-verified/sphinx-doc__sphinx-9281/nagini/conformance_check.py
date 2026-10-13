#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9281 (nagini).

SHADOW: the impl region of model.py's `describe`, copied verbatim below with
the contract calls (Requires/Ensures/Invariant/Assert and the MustTerminate
obligation) stripped. The model IS Python: the copy loops run directly on a
plain `Value` object carrying List[int] code-point fragments. The @Pure
helpers `dot` / `enum_rendering` copy over as plain list functions (PSeq
concatenation realized as list concatenation); there are no @ContractOnly
callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`sphinx.util.inspect.object_description`. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable.

Type bridge (mapping.md section 2): a real runtime value projects onto a
`Value` as follows.
  * `kind` is the category tag: which arm of the (mutually exclusive,
    patched) dispatch chain the value belongs to, tested in chain order --
    key/value mapping -> 0, unordered collection -> 1, immutable unordered
    collection -> 2, enumerated-type member -> 3, anything else -> 4.
  * For kind 3 the two fragments the changed rendering composes are
    projected INDEPENDENTLY of the oracle: `class_name` is the code points
    of the member's owning type's name, `member_name` the code points of the
    member's own name. The shadow composes them; the oracle renders the real
    member. This arm is the genuine differential content of the check.
  * For kinds 0/1/2/4 the model carries the arm's rendering as an OPAQUE
    input sequence (`category_text` / `fallback_text`): these arms are
    unchanged by the behaviour under specification, and the spec only
    requires the routine reproduce the given rendering on the matching arm.
    The faithful projection of an opaque carrier is therefore the rendering
    the real (unchanged) arm actually produces for that value; the check
    confirms the shadow's element-wise reproduction agrees with the real
    routine's output, exercising the copy loops and the dispatch.
  * str <-> List[int] of Unicode code points via ord()/chr() pointwise.

Input domain: every constructed Value satisfies the Requires (the fields are
plain lists of ints; the permission preconditions are trivially met by any
well-formed Value). Real values are drawn per category: freshly built
enumerated types (boundary shapes + randomized names/member counts, the bulk
of the volume -- the changed arm), plus mappings, unordered collections
(sortable and unsortable element mixes), immutable unordered collections,
and generic fallback values of varied types.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz values.
Pinned fuzz seed: 92810.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import enum
import json
import random
import string
import sys

SEED = 92810
N_FUZZ = 100_000


# --- pure helpers from model.py, contracts stripped, PSeq -> list -----------

def dot():
    # the single separator code point U+002E '.'
    return [46]


def enum_rendering(class_name, member_name):
    """The rendering of an enumerated-type member: the owning type's name, a
    dot, then the member's name."""
    return list(class_name) + dot() + list(member_name)


# --- the Value carrier (model.py), contracts stripped ------------------------

class Value:
    def __init__(self, kind, class_name, member_name, category_text,
                 fallback_text):
        self.kind = kind
        self.class_name = class_name
        self.member_name = member_name
        self.category_text = category_text
        self.fallback_text = fallback_text


# --- the impl region of model.py `describe`, verbatim, contracts stripped ---

def describe(value):
    result = []  # type: list
    if value.kind == 0 or value.kind == 1 or value.kind == 2:
        i = 0
        while i < len(value.category_text):
            result.append(value.category_text[i])
            i = i + 1
        return result
    elif value.kind == 3:
        i = 0
        while i < len(value.class_name):
            result.append(value.class_name[i])
            i = i + 1
        result.append(46)  # '.'
        j = 0
        while j < len(value.member_name):
            result.append(value.member_name[j])
            j = j + 1
        return result
    else:
        i = 0
        while i < len(value.fallback_text):
            result.append(value.fallback_text[i])
            i = i + 1
        return result


# --- bridge: real runtime value -> Value --------------------------------------

def ords(s):
    return [ord(ch) for ch in s]


def category_of(obj):
    """The category tag: which arm of the mutually exclusive dispatch chain
    the value belongs to, tested in chain order (mapping.md section 2)."""
    if isinstance(obj, dict):
        return 0
    elif isinstance(obj, set):
        return 1
    elif isinstance(obj, frozenset):
        return 2
    elif isinstance(obj, enum.Enum):
        return 3
    return 4


def check_value(object_description, obj):
    """Project obj onto a Value, run the shadow, compare against the real
    routine's rendering. Returns an error string on disagreement, else None."""
    real_text = object_description(obj)
    real = ords(real_text)
    kind = category_of(obj)
    if kind == 3:
        # the changed arm: fragments projected independently of the oracle
        v = Value(kind,
                  ords(obj.__class__.__name__),
                  ords(obj.name),
                  [], ords(repr(obj)))
    elif kind == 4:
        # unchanged generic fallback: opaque carrier = the arm's rendering
        v = Value(kind, [], [], [], list(real))
    else:
        # unchanged collection-style arms: opaque carrier = the arm's rendering
        v = Value(kind, [], [], list(real), [])
    shadow = describe(v)
    if shadow != real:
        return ("DISAGREEMENT\n  obj=%r (kind=%d)\n  shadow=%r\n  real=%r"
                % (obj, kind, [chr(c) for c in shadow], real_text))
    return None


# --- input generation ----------------------------------------------------------

class _Unsortable(object):
    """Distinct instances with no ordering: drives the collection arms'
    sorted() fall-through path."""

    def __repr__(self):
        return "unsortable"


def boundary_values():
    class MyEnum(enum.Enum):
        FOO = 1
        BAR = 2

    class ValuedEnum(enum.Enum):
        ValueA = 10
        ValueB = 20

    class StrEnum(enum.Enum):
        A = "alpha"
        B = "beta"

    class SingleMember(enum.Enum):
        ONLY = object()

    class AnIntEnum(enum.IntEnum):
        X = 1
        Y = 2

    class Underscored(enum.Enum):
        _hidden_like = 1
        Mixed_Case_99 = 2

    class Greek(enum.Enum):
        # non-ASCII identifiers: code points above 127 through the bridge
        αλφα = 1
        ωμεγα = 2

    vals = [
        MyEnum.FOO, MyEnum.BAR,
        ValuedEnum.ValueA, ValuedEnum.ValueB,
        StrEnum.A, StrEnum.B,
        SingleMember.ONLY,
        AnIntEnum.X, AnIntEnum.Y,
        Underscored._hidden_like, Underscored.Mixed_Case_99,
        Greek.αλφα, Greek.ωμεγα,
        # mappings
        {}, {1: 2}, {"b": 1, "a": 2}, {1: {2: 3}}, {"k": MyEnum.FOO},
        # unordered collections (sortable / singleton / unsortable elements)
        set(), {1}, {3, 1, 2}, {"x", "y"}, {_Unsortable(), _Unsortable()},
        # immutable unordered collections
        frozenset(), frozenset({1}), frozenset({3, 1, 2}),
        frozenset({_Unsortable(), _Unsortable()}),
        # generic fallback values of varied types
        0, 1, -7, 3.5, True, None, "text", "", b"bytes",
        (1, 2), [1, 2, 3], _Unsortable(), object, len,
    ]
    return vals


NAME_START = string.ascii_letters + "_"
NAME_REST = string.ascii_letters + string.digits + "_"
RESERVED = {"mro", "name", "value"}


def random_identifier(rng):
    n = rng.randint(1, 12)
    s = rng.choice(NAME_START)
    s += "".join(rng.choice(NAME_REST) for _ in range(n - 1))
    return s


def random_member_name(rng):
    while True:
        mname = random_identifier(rng)
        # the functional creation API reserves _sunder_/__dunder__ shapes
        if mname.startswith("_") or mname.endswith("_") or mname in RESERVED:
            continue
        return mname


def fuzz_values(rng, n):
    """Yield n randomized real values, weighted toward the enumerated-type
    category (the changed arm)."""
    produced = 0
    while produced < n:
        pick = rng.random()
        if pick < 0.45:
            # a fresh enumerated type with 1..4 members; every member is one
            # input value
            k = rng.randint(1, min(4, n - produced))
            members = {}
            while len(members) < k:
                mname = random_member_name(rng)
                if mname not in members:
                    members[mname] = len(members) + 1
            cls = enum.Enum(random_identifier(rng), members)
            for mname in members:
                yield cls[mname]
                produced += 1
        elif pick < 0.60:
            # mapping with sortable homogeneous keys
            m = rng.randint(0, 5)
            yield {rng.randint(-50, 50): rng.randint(-50, 50)
                   for _ in range(m)}
            produced += 1
        elif pick < 0.72:
            # unordered collection (occasionally unsortable elements)
            m = rng.randint(0, 5)
            if rng.random() < 0.1:
                yield {_Unsortable() for _ in range(max(m, 1))}
            else:
                yield {rng.randint(-50, 50) for _ in range(m)}
            produced += 1
        elif pick < 0.82:
            # immutable unordered collection
            m = rng.randint(0, 5)
            yield frozenset(rng.randint(-50, 50) for _ in range(m))
            produced += 1
        else:
            # generic fallback values
            choice = rng.randint(0, 5)
            if choice == 0:
                yield rng.randint(-10**6, 10**6)
            elif choice == 1:
                yield rng.random() * 100 - 50
            elif choice == 2:
                yield "".join(rng.choice(NAME_REST)
                              for _ in range(rng.randint(0, 8)))
            elif choice == 3:
                yield tuple(rng.randint(0, 9)
                            for _ in range(rng.randint(0, 4)))
            elif choice == 4:
                yield [rng.randint(0, 9) for _ in range(rng.randint(0, 4))]
            else:
                yield None
            produced += 1


def main():
    from sphinx.util.inspect import object_description  # REAL patched callee

    checked = 0
    n_boundary = 0
    for obj in boundary_values():
        err = check_value(object_description, obj)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for obj in fuzz_values(rng, N_FUZZ):
        err = check_value(object_description, obj)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real rendering routine on %d inputs "
          "(%d boundary + %d fuzz, seed %d)." % (checked, n_boundary,
                                                 N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
