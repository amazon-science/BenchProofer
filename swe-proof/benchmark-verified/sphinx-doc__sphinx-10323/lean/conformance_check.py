#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sphinx-doc__sphinx-10323.

The bundle models ONE routine: the line-list assembly pipeline of
`LiteralIncludeReader.read` (mapping.md). The soundness-critical decision the
patch changes is the ORDER of the assembly steps — specifically that the
de-indentation pass runs on the SELECTED FILE CONTENT before the author-supplied
`prepend`/`append` lines are added:

    post-patch order:  select -> dedent -> prepend -> append

Pre-patch the de-indentation ran LAST (select -> prepend -> append -> dedent),
so it also stripped leading whitespace from the prepended/appended lines.

The leading selection passes (`selectContent`) and the de-indentation routine
(`dedentCore`/`dedent_lines`) are UNCHANGED by the patch (A-reference). They
appear identically in the oracle and the shadow, so they cancel and this
differential test isolates exactly the R leg — the step ordering — over faithful
deterministic models of both callees.

ORACLE = faithful in-process replica of the POST-PATCH pipeline (dedent before
prepend/append). SHADOW = op-for-op transliteration of
`implementation_assembleLines` (Solution.lean impl region), per refinement.md.

stdlib-only. Pinned seed: 10323 (also in mapping.md).
"""
import random
import sys

SEED = 10323
N = 120_000


# --- faithful deterministic models of the UNCHANGED callees -------------------
# Both are byte-identical between oracle and shadow, so their exact behaviour is
# irrelevant to the diff; what matters is WHEN dedent runs relative to the added
# lines.

def select_content(lines):
    # Stand-in for pyobject/start/end/lines selection: a fixed, deterministic
    # transform of the input line list. Identical on both sides.
    return list(lines)


def dedent_core(lines):
    # Faithful model of dedent_lines with an integer count: strip up to DEDENT
    # leading characters from every line, mirroring `line[dedent:]`. Identical on
    # both sides; the point is only WHICH lines it sees.
    dedent = 2
    new_lines = []
    for line in lines:
        new_line = line[dedent:]
        if line.endswith("\n") and not new_line:
            new_line = "\n"
        new_lines.append(new_line)
    return new_lines


def apply_dedent(opts, lines):
    return dedent_core(lines) if opts["dedent"] else lines


def add_prepend(opts, lines):
    # Faithful to prepend_filter's truthiness guard (`if prepend:`): a
    # present-but-EMPTY prepend inserts nothing, matching the real reader.
    p = opts["prepend"]
    return ([p + "\n"] + lines) if p else lines


def add_append(opts, lines):
    # Faithful to append_filter's truthiness guard (`if append:`).
    a = opts["append"]
    return (lines + [a + "\n"]) if a else lines


# --- ORACLE: faithful replica of the POST-PATCH pipeline ----------------------
def oracle(opts, lines):
    acc = list(lines)
    acc = select_content(acc)
    acc = apply_dedent(opts, acc)       # dedent the selected content first
    acc = add_prepend(opts, acc)
    acc = add_append(opts, acc)
    return acc


# --- SHADOW of implementation_assembleLines (the R/I legs) --------------------
# Mirrors Solution.lean impl region exactly: build the post-patch filter list
# and fold the line list through it.
def shadow(opts, lines):
    filters = [
        lambda ls: select_content(ls),
        lambda ls: apply_dedent(opts, ls),
        lambda ls: add_prepend(opts, ls),
        lambda ls: add_append(opts, ls),
    ]
    acc = list(lines)
    for f in filters:
        acc = f(acc)
    return acc


def disagree(opts, lines):
    got = oracle(opts, lines)
    want = shadow(opts, lines)
    if got != want:
        return (opts, lines, got, want)
    return None


LINES_POOL = [
    "      <plugin>\n",
    "  def baz():\n",
    "      pass\n",
    "\n",
    "x\n",
    "    y\n",
    "no-newline-tail",
    "        deep indent\n",
]
PREPENDS = [None, "class Foo:", "      <plugin>", "  pre", ""]
APPENDS = [None, "# comment", "      </plugin>", "  app", ""]


def _edge_cases():
    cases = []
    # F2P scenario: dedent + prepend + append together (the discriminating case).
    cases.append(({"dedent": True, "prepend": "class Foo:", "append": "# comment"},
                  ["  def baz():\n", "      pass\n", "\n"]))
    # dedent + prepend only
    cases.append(({"dedent": True, "prepend": "      <plugin>", "append": None},
                  ["        <groupId>x</groupId>\n", "      </plugin>\n"]))
    # dedent + append only
    cases.append(({"dedent": True, "prepend": None, "append": "      </plugin>"},
                  ["  a\n", "    b\n"]))
    # dedent, no prepend/append
    cases.append(({"dedent": True, "prepend": None, "append": None},
                  ["    a\n", "      b\n"]))
    # prepend/append with dedent OFF (orders must still agree)
    cases.append(({"dedent": False, "prepend": "class Foo:", "append": "# comment"},
                  ["  def baz():\n"]))
    # empty content
    cases.append(({"dedent": True, "prepend": "p", "append": "a"}, []))
    # present-but-EMPTY prepend/append: the truthiness guard inserts nothing
    cases.append(({"dedent": False, "prepend": "", "append": ""}, ["a\n"]))
    cases.append(({"dedent": True, "prepend": "", "append": ""}, ["  a\n"]))
    return cases


def _rand_case(rng):
    n = rng.randint(0, 6)
    lines = [rng.choice(LINES_POOL) for _ in range(n)]
    opts = {
        "dedent": rng.random() < 0.6,
        "prepend": rng.choice(PREPENDS),
        "append": rng.choice(APPENDS),
    }
    return opts, lines


def main() -> int:
    checked = 0
    for opts, lines in _edge_cases():
        d = disagree(opts, lines)
        if d:
            print(f"DISAGREE edge: oracle={d[2]} shadow={d[3]} opts={d[0]} lines={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        opts, lines = _rand_case(rng)
        d = disagree(opts, lines)
        if d:
            print(f"DISAGREE fuzz: oracle={d[2]} shadow={d[3]} opts={d[0]} lines={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
