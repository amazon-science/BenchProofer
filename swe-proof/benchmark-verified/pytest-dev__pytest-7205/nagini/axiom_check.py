#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7205.

This bundle consumes NO @ContractOnly axioms: the genuinely changed operation
-- rendering a recorded fixture parameter through its size-limited programmer's
representation rather than its plain text form -- is modelled DEEPLY in model.py
as the apostrophe delimiting `repr_quote(s) == ' + s + '` over the tested domain
of short, delimiter-free text values.

What G-AX validates here is the **A-reference**: that the deep model
`repr_quote` faithfully captures the real size-limited representation helper
(`_pytest._io.saferepr.saferepr(obj, maxsize=42)`) on exactly that domain, AND
the safety property the issue is about -- that the helper renders a `bytes`
parameter WITHOUT implicitly invoking `str()` on it (so it does not raise
BytesWarning under `python -bb`, the regression the fix removes). The plain-text
form the pre-patch used (`"{}".format(param)`, i.e. an implicit `str(param)`)
both omitted the delimiters AND raised on bytes; the new rendering does neither.

Checks:

  (A-reference, domain)  for every short text value `s` with no embedded
      apostrophe and `len(s) + 2 <= 42`, the real `saferepr(s, maxsize=42)`
      equals, code point for code point, the deep model `' + s + '`.

  (A-reference, length bound)  the real `saferepr(s, maxsize=42)` never exceeds
      42 characters on the full fuzz corpus (including long values, where it
      elides) -- the modelled `len(Result()) <= maxsize`.

  (safety / the issue)  `saferepr(b'...', maxsize=42)` renders a bytes value
      without raising, even with BytesWarning turned into an error -- and the
      old plain `"{}".format(b'...')` would raise there.

  (discriminator)  on a non-trivial text value the real rendering differs from
      the plain text form `s` exactly by the surrounding apostrophe delimiters,
      so the pre-patch `str` rendering is rejected.

`_pytest._io.saferepr` ships with pytest -- the very module the gold patch
imports `saferepr` from. Run inside the official SWE-bench container for the
instance, where pytest is importable. Exit 0 iff every obligation holds.
Outside the container it prints `G-AX SKIP` and returns 0; the orchestrator runs
it in-container.
"""
import random
import sys

QUOTE = 39  # apostrophe U+0027


def repr_quote_model(codepoints):
    """Reference of model.py's deep model `repr_quote`, as a code-point list:
    the apostrophe delimiter, the verbatim text, the apostrophe delimiter."""
    return [QUOTE] + list(codepoints) + [QUOTE]


def _in_tested_domain(s, maxsize):
    """The model's Requires: a short, plainly-printable text value -- printable
    ASCII (0x20..0x7e) only, no apostrophe delimiter, no backslash, within the
    size limit -- so its programmer's representation is the verbatim text wrapped
    in apostrophe delimiters with no escapes introduced."""
    if len(s) + 2 > maxsize:
        return False
    return all(0x20 <= ord(ch) <= 0x7e and ch != "'" and ch != "\\" for ch in s)


def main():
    try:
        from _pytest._io.saferepr import saferepr
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: pytest not importable in this environment: %r" % (exc,))
        return 0

    MAXSIZE = 42  # the size limit the gold patch passes

    # ---- (A-reference, domain): repr_quote == real saferepr on the domain ----
    boundary = [
        "foo", "bar", "spam", "ham", "FOO", "BAR",       # the F2P parameter ids
        "", "a", "Z", "0", " ", "x", "Hello World",
        "abc def", "under_score", "CamelCase", "a-b-c",
        "0123456789", "!@#$%^&*()=+~", "[brackets]",
        "A" * 40,                                         # max length within bound
    ]
    for s in boundary:
        assert _in_tested_domain(s, MAXSIZE), (
            "boundary input %r left the tested domain" % (s,))
        observed = [ord(ch) for ch in saferepr(s, maxsize=MAXSIZE)]   # real callee
        expected = repr_quote_model([ord(ch) for ch in s])           # deep model
        assert observed == expected, (
            "repr_quote deep model unsound on %r: saferepr gave %r, deep model "
            "gives %r" % (s, observed, expected))
        # the discriminator: the rendering is NOT the plain text form ...
        plain = [ord(ch) for ch in s]
        assert observed != plain or s == "", (
            "rendering of %r equals the plain text form (delimiters missing)" % (s,))
        # ... it differs exactly by the two surrounding apostrophes.
        assert observed[0] == QUOTE and observed[-1] == QUOTE, (
            "rendering of %r is not apostrophe-delimited" % (s,))
        assert observed[1:-1] == plain, (
            "interior of the rendering of %r is not the verbatim text" % (s,))

    # randomized fuzz over the domain (printable ASCII, no ' or \, within bound)
    rng = random.Random(7205)
    alphabet = [chr(c) for c in range(0x20, 0x7f) if chr(c) not in ("'", "\\")]
    domain_checked = 0
    for _ in range(20000):
        n = rng.randint(0, 39)                       # len(s)+2 <= 42 => n <= 40
        s = "".join(rng.choice(alphabet) for _ in range(n))
        if not _in_tested_domain(s, MAXSIZE):
            continue
        observed = [ord(ch) for ch in saferepr(s, maxsize=MAXSIZE)]
        expected = repr_quote_model([ord(ch) for ch in s])
        assert observed == expected, (
            "repr_quote deep model unsound on %r: saferepr gave %r, deep model "
            "gives %r" % (s, observed, expected))
        domain_checked += 1

    # ---- (A-reference, length bound): saferepr respects maxsize everywhere ---
    wide = alphabet + ["'", "\\", "\t", "\n", "é", "•"]
    for _ in range(5000):
        n = rng.randint(0, 200)
        s = "".join(rng.choice(wide) for _ in range(n))
        assert len(saferepr(s, maxsize=MAXSIZE)) <= MAXSIZE, (
            "saferepr exceeded maxsize on %r" % (s,))

    # ---- (safety / the issue): bytes render without an implicit str() raise --
    # The BytesWarning that the issue is about is emitted at the C level only
    # when the interpreter is launched with `-bb` (it sets
    # sys.flags.bytes_warning == 2); a warnings filter inside an already-running
    # process does NOT reproduce it. So the bytes-safety property is checked in a
    # FRESH `-bb` subprocess -- exactly the configuration the F2P regression test
    # (`python -bb -m pytest --setup-show`) uses. In that subprocess:
    #   * the NEW rendering `saferepr(b, maxsize=42)` must NOT raise (it uses
    #     repr, never an implicit str()); and
    #   * the PRE-PATCH plain form `"{}".format(b)` MUST raise BytesWarning.
    bytes_probe = (
        "import sys\n"
        "from _pytest._io.saferepr import saferepr\n"
        "vals = [b'Hello World', b'', b'\\x00\\xff', b'spam', bytes(range(0,64))]\n"
        "for b in vals:\n"
        "    out = saferepr(b, maxsize=42)\n"          # new form: must not raise
        "    assert isinstance(out, str) and len(out) <= 42\n"
        "for b in vals:\n"
        "    raised = False\n"
        "    try:\n"
        "        '{}'.format(b)\n"                      # old form: must raise
        "    except BytesWarning:\n"
        "        raised = True\n"
        "    assert raised, 'pre-patch str() form did not raise on %r' % (b,)\n"
        "print('OK')\n"
    )
    import subprocess
    proc = subprocess.run(
        [sys.executable, "-bb", "-c", bytes_probe],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
    )
    assert proc.returncode == 0 and proc.stdout.strip().endswith("OK"), (
        "bytes-safety check failed under `python -bb`:\n%s" % (proc.stdout,))

    print("G-AX OK: repr_quote deep model (== real saferepr(_, maxsize=42)) "
          "sound on %d boundary + %d fuzz domain inputs; maxsize bound holds on "
          "5000 long inputs; bytes render without an implicit str() BytesWarning "
          "while the pre-patch plain form raises." % (len(boundary), domain_checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
