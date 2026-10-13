#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11133 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of the `make_bytes` value
dispatch modeled in Solution.lean by executing both sides on the same fuzzed
inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged dispatch of Solution.lean's impl region
              (`makeBytes`/`bodyBytes`) transliterated to Python over the real
              repo types, via the mapping.md bijection:
                  bytes value      -> Body.bytes  -> return the bytes
                  memoryview value -> Body.buffer -> return bytes(view)
                  str value        -> Body.text   -> encodeStr(s)
                  other value      -> Body.other  -> fallback
              The A-tagged free callees `encodeStr`/`fallback` are realised by
              the REAL unchanged encoder (`value.encode(charset)` /
              `str(value).encode(charset)`), per mapping.md §3.2 (A-tagged ->
              run real callee, not a model). The binary branch's A-reference
              (bytes(memoryview)==content) is exercised concretely.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `HttpResponseBase.make_bytes` applied at base_commit (the real
              correctness oracle, G-RESOLVE). The harness applies patch.diff
              before this runs; we call the real method on a real HttpResponse.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys

SEED = 11133
N_FUZZ = 100_000


def _make_response():
    """A real HttpResponse whose make_bytes (patched) is the oracle. Default
    charset is utf-8 (settings.DEFAULT_CHARSET)."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django.conf.global_settings")
    import django.conf
    if not django.conf.settings.configured:
        django.conf.settings.configure()
    from django.http import HttpResponse
    return HttpResponse()


def shadow_make_bytes(resp, value):
    """The R/I shadow: Solution.lean's Body dispatch transliterated. The A-tagged
    encoder callees are realised by the real unchanged encoder on `resp`."""
    charset = resp.charset
    if isinstance(value, bytes):            # Body.bytes b  -> b
        return bytes(value)
    if isinstance(value, memoryview):       # Body.buffer b -> b  (A-reference)
        return bytes(value)
    if isinstance(value, str):              # Body.text s   -> encodeStr s (free input)
        return bytes(value.encode(charset))
    return str(value).encode(charset)       # Body.other    -> fallback (free input)


def oracle_make_bytes(resp, value):
    """patch.diff's behaviour: the real patched make_bytes."""
    return resp.make_bytes(value)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield b""                                   # empty bytes
    yield memoryview(b"")                        # empty buffer
    yield b"My Content"                          # issue example (bytes)
    yield memoryview(b"My Content")              # issue example (memoryview) -- THE FIX
    yield memoryview(b"memoryview")              # F2P test payload
    yield "My Content"                           # str
    yield ""                                     # empty str
    yield 12345                                  # non-string (test_non_string_content)
    yield memoryview(bytes(range(256)))          # all byte values
    yield memoryview(bytearray(b"backed by bytearray"))
    yield b"\x00\x01\xfe\xff"
    yield "café"                                 # non-ascii str
    for _ in range(n):
        k = rng.randint(0, 4)
        m = rng.randint(0, 48)
        raw = bytes(rng.randint(0, 255) for _ in range(m))
        if k == 0:
            yield raw                            # bytes
        elif k == 1:
            yield memoryview(raw)                # memoryview over bytes
        elif k == 2:
            yield memoryview(bytearray(raw))     # memoryview over bytearray
        elif k == 3:
            # a random str (ascii-safe so it encodes under utf-8 deterministically)
            yield "".join(chr(rng.randint(32, 126)) for _ in range(m))
        else:
            yield rng.randint(-10000, 10000)     # other (int)


def main():
    resp = _make_response()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for v in fuzz_inputs(N_FUZZ, rng):
        count += 1
        # memoryview is single-use-ish per consumer; build fresh copies so both
        # sides see identical content (a memoryview is not consumed by bytes(),
        # but keep them independent to avoid any released-buffer surprise).
        if isinstance(v, memoryview):
            backing = bytes(v)
            sv, ov = memoryview(backing), memoryview(backing)
        else:
            sv = ov = v
        shadow = shadow_make_bytes(resp, sv)
        oracle = oracle_make_bytes(resp, ov)
        if shadow != oracle:
            disagreements.append((repr(v)[:80], shadow[:60], oracle[:60]))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for v, sh, orc in disagreements:
            print("  input=%s shadow=%r oracle=%r" % (v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of makeBytes (Body dispatch) agrees with "
          "patch.diff behaviour (real make_bytes) on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
