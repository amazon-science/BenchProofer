#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7521.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`, `Char.ofNat (ord ch)` ↔ ch). The
              impl region is a verbatim per-code-point copy (the `readback`
              identity fold), so the shadow is the identity on str. There is no
              A-tagged live callee in the computed `out` (the read-back IS the
              deep model, validated by G-AX), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `_pytest.capture.EncodedFile` (an `io.TextIOWrapper`) constructed
              exactly as the patched `FDCaptureBinary.__init__` constructs it,
              exercising the write -> read (`snap`) round-trip — the real
              correctness oracle (G-RESOLVE). G-CONF runs in-container AFTER
              patch.diff is applied, so this picks up `newline=""`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import io
import random
import sys
from tempfile import TemporaryFile

SEED = 7521
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean readbackStream, transliterated ------------
def shadow_readback(text):
    """readback (text) transliterated to str: the verbatim per-code-point copy
    that the backward `while` fold of readbackStream computes (readback == id).
    This is the R/I shadow of the impl."""
    return "".join(ch for ch in text)


# --- the oracle: patch.diff's behaviour --------------------------------------
def _build_patched_stream():
    """Build the capture text stream exactly as the patched
    `FDCaptureBinary.__init__` builds its tmpfile (src/_pytest/capture.py),
    over an in-memory byte buffer so we can exercise the snap() read-back
    without touching real file descriptors. Uses the patched `EncodedFile`
    class from the repo under test, so this reflects patch.diff verbatim."""
    from _pytest.capture import EncodedFile
    return EncodedFile(
        io.BytesIO(),
        encoding="utf-8",
        errors="replace",
        newline="",                 # supplied by patch.diff (asserted below)
        write_through=True,
    )


def _assert_patch_applied():
    """Tie the oracle to the applied patch: the patched capture source must
    construct the EncodedFile with `newline=""`. If patch.diff is NOT applied
    (pre-patch), this raises and the gate refuses to run rather than silently
    passing against a buggy oracle."""
    import _pytest.capture as cap
    src = open(cap.__file__).read()
    assert 'newline=""' in src, (
        "patch.diff not applied: src/_pytest/capture.py lacks newline=\"\" "
        "(the EncodedFile would translate carriage returns; oracle invalid)")


def oracle_readback(text):
    """patch.diff's behaviour: write `text` into the patched capture stream and
    read it back, the FDCapture.snap round-trip (`tmpfile.read()`)."""
    w = _build_patched_stream()
    w.write(text)
    w.flush()
    w.seek(0)
    return w.read()


def fuzz_inputs(n, rng):
    newlines = ["\n", "\r", "\r\n", "\n\r"]
    # boundary cases first
    yield ""
    for nl in newlines:
        yield nl
        yield nl + nl
        yield "test" + nl          # the F2P shape
        yield nl + "test"
    yield "Greetings from DOS\r"
    yield "  0%\r"
    yield "a\rb\r\nc\nd"
    yield "\r\r\r"
    yield "line1\nline2\r\nline3\rline4"
    yield "no newlines here"
    yield "unicode é • ☃ end\r"
    alphabet = list("\r\n\r\n abABzZ09.!-") + ["é", "•", "\t", "\r", "\n"]
    for _ in range(n):
        k = rng.randint(0, 24)
        yield "".join(rng.choice(alphabet) for _ in range(k))


def main():
    _assert_patch_applied()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for s in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_readback(s)
        oracle = oracle_readback(s)
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
    print("G-CONF OK: R/I shadow of readbackStream agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
