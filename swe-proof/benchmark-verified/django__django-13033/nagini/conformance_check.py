#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13033 (nagini).

SHADOW  — the impl region of model.py `ordering_mode`, copied VERBATIM below
          with the contract calls (Requires/Ensures) stripped; the model IS
          Python, so no transliteration. PSeq is a thin tuple shim; the @Pure
          helpers (PK, path_terminal) copy over as plain functions. There are
          no @ContractOnly callees in this bundle.

ORACLE  — the REAL patched repo function the model models per mapping.md:
          `django.db.models.sql.compiler.SQLCompiler.find_ordering_name`
          (PYTHONPATH=/testbed; the gate applies the gold patch before this
          script runs). The method is driven UNBOUND with a stand-in `self`
          whose `_setup_joins` returns a controlled (field, opts) pair; a
          marker OrderBy planted in `opts.ordering` makes the two possible
          return shapes distinguishable by identity, so the observable is
          exactly which branch the decision predicate selects:
          mode 1 = the related-default-ordering expansion branch,
          mode 0 = the direct-target branch — the model's Result().

BRIDGE  — mapping.md section 2: strings <-> tuples of code points via ord;
          `path_segments` is the split of `name` on the lookup separator
          (the derived relation the precondition encodes, validated by
          axiom_check.py); `relation_own_column` is the field's attribute
          name lifted to code points, or — when the field has no attribute
          name — a sentinel sequence containing a negative value, which no
          real segment can equal (the abstraction mapping.md documents for
          that case). `points_to_relation` / `has_default_ordering` are bool
          identities (the latter is the truthiness of the ordering tuple).
          Names fed to the oracle are non-empty and carry no direction
          prefix, matching the model's carrier (the name after direction
          stripping); every such name yields Requires-satisfying model
          inputs (split always returns >= 1 piece, and the multi-piece
          inequality is a theorem of split, per axiom_check.py).

>= 1e5 Requires-satisfying inputs: structured boundary cases + 100000 fuzz
cases. Pinned fuzz seed: 13033. Exit 0 iff zero disagreements; on
disagreement print the input and both outcomes and exit 1. stdlib only.
"""
import random
import string
import sys

SEED = 13033
N_FUZZ = 100_000
LOOKUP_SEP = "__"


# ---------------------------------------------------------------------------
# PSeq shim: plain tuple-backed stand-in for nagini's pure sequence type.
# ---------------------------------------------------------------------------

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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)


# ---------------------------------------------------------------------------
# model.py pure region, copied over as plain functions (@Pure and the
# contract lines stripped).
# ---------------------------------------------------------------------------

def PK():
    # 'pk' -- the primary-key shortcut token.
    return PSeq(112, 107)


def path_terminal(path_segments):
    """The terminal segment of a non-empty lookup path."""
    return path_segments[len(path_segments) - 1]


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM, contract statement lines stripped.
# ---------------------------------------------------------------------------

def ordering_mode(name,
                  path_segments,
                  relation_own_column,
                  points_to_relation,
                  has_default_ordering):
    if (points_to_relation and has_default_ordering
            and relation_own_column != path_terminal(path_segments)
            and name != PK()):
        return 1
    return 0


# ---------------------------------------------------------------------------
# Bridge: real strings -> the model's code-point carriers.
# ---------------------------------------------------------------------------

def to_pts(s):
    return PSeq._wrap(ord(c) for c in s)


def shadow_mode(name, attname, points_to_relation, has_default_ordering):
    name_pts = to_pts(name)
    path_segments = PSeq._wrap(to_pts(seg) for seg in name.split(LOOKUP_SEP))
    if attname is None:
        # no attribute name: the comparison is vacuously an inequality;
        # modelled by a carrier value distinct from every possible segment
        # (a negative entry, unreachable by ord) -- mapping.md section 2.
        relation_own_column = PSeq(-1)
    else:
        relation_own_column = to_pts(attname)
    return ordering_mode(name_pts, path_segments, relation_own_column,
                         points_to_relation, has_default_ordering)


# ---------------------------------------------------------------------------
# Oracle: the REAL patched find_ordering_name, driven unbound with stand-ins
# exposing only what the decision predicate and the two branches read.
# ---------------------------------------------------------------------------

def make_oracle():
    import django.conf
    if not django.conf.settings.configured:
        django.conf.settings.configure()
    from django.db.models.sql.compiler import SQLCompiler
    from django.db.models.expressions import OrderBy, Value

    class _Field:
        pass

    class _Opts:
        pass

    class _AliasEntry:
        pass  # no join_cols attribute -> getattr default fires

    class _Query:
        alias_map = {"T1": _AliasEntry()}

        @staticmethod
        def trim_joins(targets, joins, path):
            return targets, joins[-1], None

    class _Self:
        query = _Query()

    marker = OrderBy(Value(1))
    leaf = Value(1)

    def oracle(name, attname, points_to_relation, has_default_ordering):
        field = _Field()
        field.is_relation = points_to_relation
        if attname is not None:
            field.attname = attname
        opts = _Opts()
        # the predicate consumes only the truthiness of the ordering tuple;
        # the marker lets us observe which branch produced the result.
        opts.ordering = (marker,) if has_default_ordering else ()
        me = _Self()
        me._setup_joins = lambda pieces, o, alias: (
            field, ["tgt"], "T1", ["T1"], [], opts,
            lambda t, a: leaf)
        results = SQLCompiler.find_ordering_name(me, name, opts)
        assert len(results) == 1, results
        item, is_ref = results[0]
        assert is_ref is False
        # expansion branch returns the planted ordering item itself; the
        # direct-target branch constructs a fresh expression around `leaf`.
        return 1 if item is marker else 0

    return oracle


# ---------------------------------------------------------------------------
# Input generation. Domain: non-empty names without a direction prefix (the
# model's `name` is the post-direction-stripping string), attname a string or
# absent, the two booleans free. All such inputs satisfy the model's Requires
# once bridged (split yields >= 1 segment; multi-segment split output never
# equals the whole input -- the invariant axiom_check.py validates).
# ---------------------------------------------------------------------------

IDENT = string.ascii_lowercase + string.digits + "_"


def boundary_cases():
    cases = []
    names = [
        "pk",
        "root_id",
        "record",
        "record__root_id",     # multi-segment path ending in the column token
        "record__root",
        "record__root__id",
        "a__b__c__d",
        "x__",
        "a____b",
        "_",
        "a_b",
        "a_b__c_d",
        "x",
        "id",
        "record__pk",
    ]
    attnames = [None, "root_id", "record", "pk", "record__root_id", "id", ""]
    for n in names:
        for a in attnames:
            for rel in (True, False):
                for ordd in (True, False):
                    cases.append((n, a, rel, ordd))
    return cases


def gen_case(rng):
    k = rng.randint(1, 4)
    segs = ["".join(rng.choice(IDENT) for _ in range(rng.randint(0, 6)))
            for _ in range(k)]
    name = LOOKUP_SEP.join(segs)
    if not name:
        name = rng.choice(IDENT.replace("_", "")) or "x"
    r = rng.random()
    if r < 0.25:
        attname = segs[-1]              # column token == terminal segment
    elif r < 0.40:
        attname = name                  # column token == whole path
    elif r < 0.50:
        attname = None                  # field without an attribute name
    elif r < 0.55:
        attname = "pk"
    else:
        attname = "".join(rng.choice(IDENT)
                          for _ in range(rng.randint(0, 6)))
    return (name, attname,
            rng.random() < 0.7,   # points_to_relation, biased toward the
            rng.random() < 0.7)   # guarded region
                                  # has_default_ordering likewise


def main():
    oracle = make_oracle()
    rng = random.Random(SEED)
    disagreements = []
    checked = 0

    cases = boundary_cases()
    cases += [gen_case(rng) for _ in range(N_FUZZ)]

    for name, attname, rel, ordd in cases:
        if not name or name.startswith("-"):
            continue
        checked += 1
        s = shadow_mode(name, attname, rel, ordd)
        o = oracle(name, attname, rel, ordd)
        if s != o:
            disagreements.append((name, attname, rel, ordd, s, o))
            if len(disagreements) >= 10:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), checked, SEED))
        for name, attname, rel, ordd, s, o in disagreements:
            print("  name=%r attname=%r is_relation=%r has_ordering=%r\n"
                  "    shadow mode=%r  real mode=%r"
                  % (name, attname, rel, ordd, s, o))
        return 1

    print("G-CONF OK: model.py impl shadow agrees with the real patched "
          "find_ordering_name branch selection on %d inputs (seed=%d), "
          "0 disagreements." % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
