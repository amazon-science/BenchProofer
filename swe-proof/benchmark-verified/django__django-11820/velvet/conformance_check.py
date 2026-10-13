#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11820 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of the single modeled function
`checkOrderingRef` (the related-ordering-reference walk of
`Model._check_ordering`). There are NO axioms in this bundle: the three schema
accessors are free inputs (mapping.md §2/§3), so the whole impl region is R/I
(conf_skip=false).

  * SHADOW  — Solution.lean's `stepWalk`/`orderingRefInvalid` fold,
              transliterated to Python over the mapping.md bijection
              (`Option Model` ↔ `_cls`/`None`, `Option Field` ↔ `fld`/`None`,
              `Bool` ↔ "an E015 error was appended for this reference").
  * ORACLE  — `patch.diff`'s behaviour: the GOLD-PATCHED inner walk of
              `_check_ordering`, transliterated VERBATIM with its real
              try/except control flow:

                  _cls, fld, raised = cls0, None, False
                  for part in parts:
                      try:
                          if part == 'pk':            # the alias branch (fix 1)
                              fld = _cls._meta.pk
                          else:
                              fld = _cls._meta.get_field(part)
                          if fld.is_relation:
                              _cls = fld.get_path_info()[-1].to_opts.model
                          else:
                              _cls = None             # terminate descent (fix 2)
                      except (FieldDoesNotExist, AttributeError):
                          if fld is None or fld.get_transform(part) is None:
                              raised = True            # models.E015 appended
                  return raised

ORACLE CHOICE — why we transliterate the patched walk instead of running the
real `Model._check_ordering`:
  The real method needs a fully-configured app registry: concrete model classes
  with a `Meta.ordering`, migrated `Options`, a field/relation graph, the lookup
  registry, etc. — essentially the F2P Django test harness — purely to read back
  one boolean (did this reference raise E015). The field/relation/transform
  resolution it performs is UNCHANGED by the patch; only HOW the resolved
  metadata is threaded across the chain of parts changes. So, per the worker
  prompt, the ORACLE is the patched control flow transliterated verbatim, and
  the unchanged resolution is abstracted into the free accessors
  `lookup`/`alias_field`/`has_transform` — the SAME closures are handed to both
  SHADOW and ORACLE, so the only thing under differential test is the
  control-flow threading the patch actually edits (mapping.md §3).

We fuzz random synthetic schemas + part chains (boundary chains first, incl. the
two F2P scenarios), exercising both fixed behaviors. Exit 0 iff zero
disagreements. stdlib only; fuzz seed pinned (mapping.md §5).
"""
import random
import sys

SEED = 11820
N_FUZZ = 100_000


# ---- exception kinds mirroring the real callees ---------------------------
class FieldDoesNotExist(Exception):
    pass


# ---- a random synthetic schema -> the three free accessors ----------------
# A Field is modeled as the pair (is_rel, rel_model); mapping.md §2.
def build_schema(rng):
    num_models = rng.randint(1, 4)
    models = list(range(num_models))

    def rand_field():
        is_rel = rng.random() < 0.5
        return (is_rel, rng.choice(models))

    # get_field table: (model, part_name) -> Field, else "raises".
    field_table = {}
    for m in models:
        for name in range(5):
            if rng.random() < 0.6:
                field_table[(m, name)] = rand_field()
    # the identity-alias field (_meta.pk) per model: always present.
    alias_table = {m: rand_field() for m in models}
    # registered transforms keyed on (Field, part_name) -> bool.
    transform_keys = set()
    for is_rel in (False, True):
        for rm in models:
            for name in range(5):
                if rng.random() < 0.25:
                    transform_keys.add(((is_rel, rm), name))

    def lookup(model, name):
        """get_field: returns Field or None (None == raises FieldDoesNotExist)."""
        return field_table.get((model, name))

    def alias_field(model):
        """_meta.pk of the model."""
        return alias_table[model]

    def has_transform(fld, name):
        return (fld, name) in transform_keys

    return models, lookup, alias_field, has_transform


# ---- SHADOW: Solution.lean transliterated ----------------------------------
def flag_on_unresolved(has_transform, last, part_name):
    # `flagOnUnresolved`: with no field resolved yet there is nothing to host a
    # transform, so flag; otherwise flag unless the part is a transform of last.
    if last is None:
        return True
    return not has_transform(last, part_name)


def step_walk(lookup, alias_field, has_transform, st, part):
    """`stepWalk` transliterated. st = (cur, last, flag); part = (name, is_alias)."""
    cur, last, flag = st
    name, is_alias = part
    if cur is None:
        return (None, last, flag or flag_on_unresolved(has_transform, last, name))
    m = cur
    if is_alias:
        f = alias_field(m)
        return ((f[1] if f[0] else None), f, flag)
    f = lookup(m, name)
    if f is not None:
        return ((f[1] if f[0] else None), f, flag)
    return (m, last, flag or flag_on_unresolved(has_transform, last, name))


def shadow_invalid(lookup, alias_field, has_transform, cls0, parts):
    """`orderingRefInvalid`: foldl stepWalk from initState, read the flag."""
    st = (cls0, None, False)  # initState cls0
    for part in parts:
        st = step_walk(lookup, alias_field, has_transform, st, part)
    return st[2]


# ---- ORACLE: gold-patched _check_ordering walk, verbatim -------------------
def oracle_invalid(lookup, alias_field, has_transform, cls0, parts):
    _cls = cls0
    fld = None
    raised = False
    for (name, is_alias) in parts:
        try:
            if is_alias:               # part == 'pk'
                if _cls is None:
                    raise AttributeError  # None._meta.pk
                fld = alias_field(_cls)
            else:
                if _cls is None:
                    raise AttributeError  # None._meta.get_field(part)
                got = lookup(_cls, name)
                if got is None:
                    raise FieldDoesNotExist
                fld = got
            if fld[0]:                 # fld.is_relation
                _cls = fld[1]          # descend into the related model
            else:
                _cls = None            # terminate descent (fix 2)
        except (FieldDoesNotExist, AttributeError):
            if fld is None or has_transform(fld, name) is False:
                raised = True
    return raised


# ---- fuzz inputs -----------------------------------------------------------
def fuzz_inputs(n, rng):
    # Boundary chains first (plan §4.1 step 4) — incl. the two F2P scenarios.
    # Schemas for boundary cases are tiny and explicit, handed inline below.
    yield "boundary"
    for _ in range(n):
        models, lookup, alias_field, has_transform = build_schema(rng)
        cls0 = rng.choice(models)
        k = rng.randint(0, 5)
        parts = []
        for _ in range(k):
            name = rng.randint(0, 4)
            is_alias = rng.random() < 0.3
            parts.append((name, is_alias))
        yield (lookup, alias_field, has_transform, cls0, parts)


def boundary_checks():
    """The two F2P scenarios, asserted against BOTH shadow and oracle so a
    transcription error in either is caught even before the random sweep."""
    out = []
    # Models: Child=0, Parent=1. Field name encoding: parent=0, field1=1,
    # field2=2. is_alias marks the 'pk' part.
    # Child.parent -> relation to Parent; Parent.field1 -> non-relation.
    field_table = {
        (0, 0): (True, 1),    # Child.parent : relation -> Parent
        (1, 1): (False, 1),   # Parent.field1 : non-relation
    }
    alias_table = {0: (False, 0), 1: (False, 1)}  # pk of each model (non-rel)
    transform_keys = set()   # no registered transforms

    def lookup(m, name):
        return field_table.get((m, name))

    def alias_field(m):
        return alias_table[m]

    def has_transform(fld, name):
        return (fld, name) in transform_keys

    # (a) parent__pk  ->  must NOT be flagged (fix 1).
    parts_a = [(0, False), (0, True)]   # parent, then pk(alias)
    out.append(("parent__pk", lookup, alias_field, has_transform, 0, parts_a, False))
    # (b) parent__field1__field2  ->  MUST be flagged (fix 2).
    parts_b = [(0, False), (1, False), (2, False)]  # parent, field1, field2
    out.append(("parent__field1__field2", lookup, alias_field, has_transform, 0, parts_b, True))
    # (c) empty chain -> never flagged.
    out.append(("empty", lookup, alias_field, has_transform, 0, [], False))
    # (d) single nonexistent field, no transform -> flagged.
    out.append(("missing", lookup, alias_field, has_transform, 0, [(3, False)], True))
    return out


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Boundary scenarios: shadow == oracle AND both == the expected E015 verdict.
    for name, lk, af, ht, cls0, parts, expected in boundary_checks():
        count += 1
        s = shadow_invalid(lk, af, ht, cls0, parts)
        o = oracle_invalid(lk, af, ht, cls0, parts)
        if s != o:
            disagreements.append(("boundary:%s shadow!=oracle" % name, s, o))
        elif s != expected:
            disagreements.append(("boundary:%s != expected E015 verdict" % name,
                                  s, expected))

    # Random sweep: shadow vs oracle over fuzzed schemas + chains.
    for item in fuzz_inputs(N_FUZZ, rng):
        if item == "boundary":
            continue
        lk, af, ht, cls0, parts = item
        count += 1
        s = shadow_invalid(lk, af, ht, cls0, parts)
        o = oracle_invalid(lk, af, ht, cls0, parts)
        if s != o:
            disagreements.append((("cls0=%r parts=%r" % (cls0, parts)), s, o))
        if len(disagreements) >= 8:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d checks:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  %r shadow/oracle/expected=%r/%r" % d)
        return 1
    print("G-CONF OK: R/I shadow of checkOrderingRef agrees with the gold-patched "
          "_check_ordering walk on %d checks (boundary F2P scenarios + fuzz, "
          "seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
