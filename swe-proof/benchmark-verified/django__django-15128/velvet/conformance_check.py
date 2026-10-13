#!/usr/bin/env python3
r"""G-CONF differential conformance for django__django-15128 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `refinement.md`: the deep
model of Solution.lean (`relabeling` / `relabelFrom`, the backward fold the
`buildRelabeling` `do` block computes) transliterated to Python, differential-
tested against `patch.diff`'s relabeling-map construction over many
(alias-sequence, preserved-set, prefix) triples. Exit 0 iff zero disagreements.

ORACLE CHOICE — why we transliterate the patched comprehension VERBATIM instead
of driving a live `Query`:
  The changed operation is the dict comprehension at the end of `Query.bump_prefix`
  (django/db/models/sql/query.py, gold-patched):

      self.change_aliases({
          alias: '%s%d' % (self.alias_prefix, pos)
          for pos, alias in enumerate(self.alias_map)
          if alias not in exclude
      })

  This builds the old->new alias rename map. It is a PURE function of three
  values: the ordered alias sequence (`list(self.alias_map)`), the fresh prefix
  (`self.alias_prefix`), and the `exclude` set. The surrounding machinery
  (`change_aliases` applying the map, `combine` choosing `exclude={initial_alias}`)
  is UNCHANGED by — or downstream of — the modeled construction; the only thing
  the patch changes is which entries the comprehension emits (the `if alias not
  in exclude` filter) and the renaming of the `outer_query`/`other_query` /
  `exclude` parameters. So the ORACLE is the patched comprehension transliterated
  verbatim, and the SHADOW is the deep model `relabeling` from Solution.lean.

  The whole-query AssertionError the issue reports (`set(change_map).isdisjoint(
  change_map.values())` in `change_aliases`) is a DOWNSTREAM consequence of this
  map on a live ORM; the spec pins the map's CONTENT (which is what determines
  whether keys and values can intersect), and G-VERIFY + G-DIFF carry that
  behaviour. This gate mechanically checks the map's content matches the patch.

The mapping.md §2 bijection used here:
  aliases (List String)            <->  list(self.alias_map)   (insertion order;
                                         dict keys are unique  -> distinct strs)
  preserved (List String)          <->  the `exclude` set
  newPrefix (String)               <->  self.alias_prefix (the bumped prefix)
  out (List (String x String))     <->  the change_map, compared as a dict
  newPrefix ++ toString pos        <->  '%s%d' % (prefix, pos)
  preserved.contains a             <->  alias in exclude

stdlib only. Fuzz seed pinned (mapping.md §4).
"""
import random
import string
import sys

SEED = 15128
N_FUZZ = 100_000


# ---- ORACLE: patch.diff comprehension, transliterated verbatim ------------
def oracle_relabel(aliases, prefix, exclude):
    """The gold-patched rename-map construction (bump_prefix, post-patch).
    `aliases` is list(self.alias_map); `enumerate` numbers EVERY alias, the
    `if` filter only decides emission — an excluded alias still consumes its
    position so later names are unaffected by the omission."""
    return {
        alias: '%s%d' % (prefix, pos)
        for pos, alias in enumerate(aliases)
        if alias not in exclude
    }


# ---- SHADOW: Solution.lean `relabeling` / `relabelFrom`, transliterated ----
def shadow_relabel(aliases, prefix, exclude):
    """relabeling newPrefix preserved aliases, transliterated. relabelFrom walks
    the sequence carrying a position counter that advances for EVERY element;
    a preserved alias contributes no entry, the rest map to prefix++toString pos.
    Returned as a dict to compare against the oracle's change_map."""
    out = {}
    pos = 0
    for a in aliases:
        if a not in exclude:               # not (preserved.contains a)
            out[a] = prefix + str(pos)
        pos += 1                           # counter advances unconditionally
    return out


def rand_alias(rng):
    """A table alias: a prefix letter + small int, like Django's T4/T5 or AB12."""
    letters = ''.join(rng.choice(string.ascii_uppercase)
                      for _ in range(rng.randint(1, 2)))
    return '%s%d' % (letters, rng.randint(0, 30))


def cases(rng):
    """Yield (aliases, prefix, exclude) test points. Aliases are DISTINCT
    (they are dict keys in the repo)."""
    # boundary cases first (plan §4.1 step 4)
    yield ([], 'T', set())
    yield (['T0'], 'T', set())
    yield (['T0'], 'T', {'T0'})                         # the only alias excluded
    yield (['T4', 'T5'], 'T', set())
    yield (['T4', 'T5'], 'T', {'T4'})                   # base-table preserved
    yield (['T4', 'T5'], 'T', {'T5'})                   # exclude a middle/last
    yield (['T4', 'T5', 'T6'], 'U', {'T4'})             # issue-shaped trio
    yield (['A0', 'A1', 'A2'], 'A', {'A0', 'A2'})       # multiple preserved
    yield (['T1', 'T2'], 'T', {'ZZ'})                   # exclude not present
    yield (['T1', 'T2', 'T3'], 'T', set())              # nothing excluded
    for _ in range(N_FUZZ):
        n = rng.randint(0, 8)
        # distinct aliases
        seen, aliases = set(), []
        while len(aliases) < n:
            a = rand_alias(rng)
            if a not in seen:
                seen.add(a)
                aliases.append(a)
        prefix = rng.choice(string.ascii_uppercase)
        # exclude: a random subset of the aliases, plus occasionally a stray
        exclude = set(a for a in aliases if rng.random() < 0.35)
        if rng.random() < 0.2:
            exclude.add(rand_alias(rng))                # may not be present
        yield (aliases, prefix, exclude)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for aliases, prefix, exclude in cases(rng):
        count += 1
        o = oracle_relabel(aliases, prefix, exclude)
        s = shadow_relabel(aliases, prefix, exclude)
        if o != s:
            disagreements.append((aliases, prefix, sorted(exclude), s, o))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for al, pf, ex, sh, orc in disagreements:
            print("  aliases=%r prefix=%r exclude=%r shadow=%r oracle=%r"
                  % (al, pf, ex, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildRelabeling agrees with patch.diff "
          "rename-map construction over %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
