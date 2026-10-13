#!/usr/bin/env python3
r"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-25479.

The bundle models TWO functions (both on the fix list, each with its own F2P
test):

* `Colormap.__eq__` (lib/matplotlib/colors.py): POST-PATCH equality is
      isinstance(other, Colormap)
      and self.colorbar_extend == other.colorbar_extend
      and np.array_equal(self._lut, other._lut)
  i.e. the display NAME is no longer compared.

* `ColormapRegistry.register` (lib/matplotlib/cm.py): the stored copy's display
  name is forced to the registration name:
      stored = cmap.copy(); if stored.name != name: stored.name = name

ORACLE = a faithful in-process replica of the POST-PATCH behaviour of each
function, written independently from the real source. SHADOW = the R/I
translation of the Lean `implementation_colormapEq` / `implementation_register`,
following the type bijection in mapping.md:

  Colormap object  <->  (name: str, flag: int, table: list[list[int]])
    name             <->  cmap.name                (identity)
    flag             <->  cmap.colorbar_extend     (injective int code)
    table            <->  cmap._lut as rows        (np.array_equal is
                                                     shape-then-elementwise;
                                                     a list of rows makes list ==
                                                     capture BOTH shape and
                                                     entries)
  cmap.copy()        <->  identity on the modeled fields (structural no-op)

The two legs must agree on every input over a corpus that crosses:
  - equal vs different display names (the eq discriminator),
  - equal vs different flag,
  - equal / different / different-length tables (the np.array_equal size case),
  - registration name equal to / different from the colormap's own name.

stdlib-only; deterministic built-in LCG fuzzer. Pinned seed: 25479 (mapping.md).
"""
import sys

SEED = 25479
N = 120_000


# ---------------------------------------------------------------------------
# A minimal Colormap-like carrier for the modeled fields.
# ---------------------------------------------------------------------------
class CM:
    __slots__ = ("name", "flag", "table")

    def __init__(self, name, flag, table):
        self.name = name
        self.flag = flag
        self.table = list(table)

    def copy(self):
        return CM(self.name, self.flag, list(self.table))


# ---------------------------------------------------------------------------
# ORACLE: independent replica of the POST-PATCH real behaviour.
# ---------------------------------------------------------------------------
def oracle_eq(a, b):
    # post-patch Colormap.__eq__ : name NOT compared.
    if a.flag != b.flag:
        return False
    # np.array_equal: False if shapes differ, else element-wise all-equal.
    # table is a list of rows; shape = (#rows, row lengths), entries per row.
    if len(a.table) != len(b.table):
        return False
    for ra, rb in zip(a.table, b.table):
        if len(ra) != len(rb):        # differing row width => differing shape
            return False
        if any(x != y for x, y in zip(ra, rb)):
            return False
    return True


def oracle_register(name, cmap):
    stored = cmap.copy()
    if stored.name != name:
        stored.name = name
    return (stored.name, stored.flag, list(stored.table))


# ---------------------------------------------------------------------------
# SHADOW: R/I translation of the Lean implementations.
# ---------------------------------------------------------------------------
def shadow_eq(a, b):
    # implementation_colormapEq
    if a.flag != b.flag:           # if a.flag != b.flag then return false
        return False
    return a.table == b.table      # return a.table == b.table  (list ==)


def shadow_register(name, cmap):
    # implementation_register
    stored = cmap.copy()           # let mut stored := cmap  (structural copy)
    if stored.name != name:        # if stored.name != name then
        stored.name = name         #   stored := { stored with name := name }
    return (stored.name, stored.flag, list(stored.table))


# ---------------------------------------------------------------------------
# fuzzer
# ---------------------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


NAMES = ["viridis", "test-cmap", "wrong-cmap", "", "A", "some_cmap_name"]
FLAGS = [0, 1, 2, -1]


def _rand_table(rnd):
    # a list of rows (0..3 rows, each 0..3 entries) so shape varies across the
    # corpus -- exercises the np.array_equal shape sensitivity.
    rows = next(rnd) % 4            # 0..3 rows
    out = []
    for _ in range(rows):
        width = next(rnd) % 4       # 0..3 entries
        out.append([(next(rnd) % 7) - 3 for _ in range(width)])
    return out


def _rand_cm(rnd):
    return CM(NAMES[next(rnd) % len(NAMES)],
              FLAGS[next(rnd) % len(FLAGS)],
              _rand_table(rnd))


def _edge_pairs():
    base = CM("viridis", 1, [[1, 2, 3], [4, 5, 6]])
    return [
        (base, CM("viridis", 1, [[1, 2, 3], [4, 5, 6]])),   # identical -> equal
        (base, CM("test-cmap", 1, [[1, 2, 3], [4, 5, 6]])), # diff name only -> EQUAL (fix)
        (base, CM("viridis", 0, [[1, 2, 3], [4, 5, 6]])),   # diff flag -> not equal
        (base, CM("viridis", 1, [[1, 2, 3]])),              # fewer rows -> not equal (shape)
        (base, CM("viridis", 1, [[1, 2], [4, 5]])),         # narrower rows -> not equal (shape)
        (base, CM("viridis", 1, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])),  # more rows
        (base, CM("viridis", 1, [[9, 9, 9], [4, 5, 6]])),   # diff entries -> not equal
        (CM("", 0, []), CM("x", 0, [])),                    # empty tables, diff name -> equal
    ]


def _edge_regs():
    return [
        ("wrong-cmap", CM("test-cmap", 1, [[1, 2, 3]])),  # name differs -> updated
        ("viridis", CM("viridis", 1, [[1, 2, 3]])),       # name already matches
        ("k", CM("", 0, [])),                              # empty cmap name
    ]


def main() -> int:
    checked = 0

    # eq edges
    for a, b in _edge_pairs():
        if oracle_eq(a, b) != shadow_eq(a, b):
            print(f"DISAGREE eq edge: a=({a.name},{a.flag},{a.table}) "
                  f"b=({b.name},{b.flag},{b.table}) "
                  f"oracle={oracle_eq(a, b)} shadow={shadow_eq(a, b)}")
            print("status=fail")
            return 1
        # symmetry too
        if oracle_eq(b, a) != shadow_eq(b, a):
            print("DISAGREE eq edge (swapped)")
            print("status=fail")
            return 1
        checked += 2

    # register edges
    for name, cmap in _edge_regs():
        if oracle_register(name, cmap) != shadow_register(name, cmap):
            print(f"DISAGREE register edge: name={name!r} "
                  f"cmap=({cmap.name},{cmap.flag},{cmap.table})")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        a = _rand_cm(rnd)
        b = _rand_cm(rnd)
        if oracle_eq(a, b) != shadow_eq(a, b):
            print(f"DISAGREE eq fuzz: a=({a.name},{a.flag},{a.table}) "
                  f"b=({b.name},{b.flag},{b.table})")
            print("status=fail")
            return 1
        checked += 1

        name = NAMES[next(rnd) % len(NAMES)]
        c = _rand_cm(rnd)
        if oracle_register(name, c) != shadow_register(name, c):
            print(f"DISAGREE register fuzz: name={name!r} "
                  f"cmap=({c.name},{c.flag},{c.table})")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0 (seed={SEED})")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
