#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7205 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (`str` / `bytes`), via the
              mapping.md bijection (`ParamValue.textVal` <-> `str`,
              `ParamValue.bytesVal` <-> ASCII `bytes`, `List Char` <-> `str`).
              `renderParameterDisplay` computes `bracket (quotedRepr param)`;
              `quotedRepr` is the deep model of the A-reference callee
              `saferepr` on both payload shapes and `bracket` is the I-tagged
              `"[{}]".format`. The deep model's equality to the real callee is
              validated separately by G-AX; here G-CONF transliterates the full
              I/R construction and checks it against the patched expression's
              actual behaviour.
  * ORACLE  — `patch.diff`'s behaviour: the patched display expression
              `"[{}]".format(saferepr(param, maxsize=42))` evaluated with the
              REAL repo `saferepr` (the real correctness oracle, G-RESOLVE).

They must agree on every Requires-satisfying (simpleParam) input — text values
of length <= 40 and byte-string values of length <= 39 over the printable-ASCII
(no apostrophe / backslash) alphabet. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the repo
callee only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from _pytest._io.saferepr import saferepr  # patched display uses this callee

SEED = 7205
N_FUZZ = 100_000
MAXSIZE = 42
MAXLEN_TEXT = 40
MAXLEN_BYTES = 39
SIMPLE_ALPHABET = [chr(c) for c in range(32, 127) if chr(c) not in ("'", "\\")]


def shadow_render(param):
    """renderParameterDisplay transliterated: bracket (quotedRepr param).
    quotedRepr (.textVal s) = "'" + s + "'" ; quotedRepr (.bytesVal s) =
    "b'" + s + "'" (the I/deep-model token); bracket t = "[" t "]" (the
    I-tagged "[{}]".format). This is the R/I shadow of the impl. `param` here
    is the real repo value (str or bytes) under the mapping.md bijection."""
    if isinstance(param, bytes):
        quoted = "b'" + param.decode("ascii") + "'"   # quotedRepr (.bytesVal s)
    else:
        quoted = "'" + param + "'"                    # quotedRepr (.textVal s)
    return "[" + quoted + "]"           # bracket (the "[{}]".format wrapping)


def oracle_render(param):
    """patch.diff's behaviour: the patched display expression, with the REAL
    repo saferepr callee."""
    return "[{}]".format(saferepr(param, maxsize=MAXSIZE))


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ""
    yield "a" * MAXLEN_TEXT                             # the text length-40 edge
    yield b""
    yield b"a" * MAXLEN_BYTES                           # the bytes length-39 edge
    yield b"Hello World"                                # the F2P bytes literal
    for s in ("foo", "bar", "spam", "ham", "FOO", "BAR", "arg_same", "foobar"):
        yield s
    for c in SIMPLE_ALPHABET:
        yield c
        yield c.encode("ascii")
    for _ in range(n):
        if rng.random() < 0.5:
            k = rng.randint(0, MAXLEN_TEXT)
            yield "".join(rng.choice(SIMPLE_ALPHABET) for _ in range(k))
        else:
            k = rng.randint(0, MAXLEN_BYTES)
            yield "".join(rng.choice(SIMPLE_ALPHABET)
                          for _ in range(k)).encode("ascii")


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_render(s)
        oracle = oracle_render(s)
        if shadow != oracle:
            disagreements.append((s, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for s, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (s, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderParameterDisplay agrees with "
          "patch.diff behaviour on %d inputs (seed=%d, text + bytes shapes), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
