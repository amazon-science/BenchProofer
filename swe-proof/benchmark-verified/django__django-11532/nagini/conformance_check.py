#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11532 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls stripped (both impl regions are single return statements and contain no
Requires/Ensures/Invariant/Assert). The @Pure helpers (`all_ascii`,
`seq_host_witness`, `seq_ace_witness`) copy over as plain functions with PSeq
replaced by a plain tuple. The one @ContractOnly callee in the impl region,
`ace_encode`, calls the REAL repo function it binds to per mapping.md
(`django.utils.encoding.punycode`, the new helper added by the patch), bridged
through the documented type refinement.

ORACLES (mapping.md section 1): per modeled function —
  * `ascii_compatible_domain`  <->  `django.utils.encoding.punycode` (the new
    reusable ASCII-compatible-encoding transform);
  * `cached_host_name`         <->  `django.core.mail.utils.CachedDnsName
    .get_fqdn`, with the platform-reported name injected by stubbing
    `socket.getfqdn` (mapping.md section 2 models that callee's return as the
    function INPUT), a fresh cache object per input (the memoization is
    per-instance and value-preserving).

The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the patched functions are importable directly.

TYPE BRIDGE (mapping.md section 2): model carrier List[int] of Unicode code
points <-> repo str, elementwise xs[k] == ord(s[k]). Encode: a candidate
List[int] becomes "".join(chr(c)); decode: an oracle str becomes
[ord(ch) for ch in s]. Specification-side PSeq is not needed at runtime
(the impl regions never touch PSeq), so no shim beyond plain lists. The model's
out-of-band condition is carried by a user-defined exception class (a builtin
exception in an ``Exsures`` crashes the Nagini translator); it refines to the
condition the real stdlib codec reports, so the shadow observes THAT and the
comparison is on which outcome occurred, not on an exception type name.

INPUT DOMAIN: EVERY label is admissible -- the model's precondition restricts
only permissions, not label shape, because the specified behaviour on a label
that has no ASCII-Compatible Encoding is itself observable (no value comes
back; the condition is reported out of band). So this check diffs the FULL
outcome on both sides of that partition: which side the label lands on, and
the value when it lands on the value-yielding side. A label is classified with
the stdlib expression `s.encode('idna')` (an unchanged stdlib callee,
independent of the repo import) and the classification is then CONFIRMED
against the real repo functions rather than used to skip them, so a repo
function that answered an unencodable label with a substitute value would be
caught here. The fuzz loop keeps drawing until >= 1e5 inputs have been diffed,
and requires BOTH sides of the partition to be non-empty so neither half is
checked vacuously. Boundary cases: the worked witness (U+6F22 U+5B57, whose
transform result the model pins), pure-ASCII / mixed / dotted host names,
length extremes near and beyond the 63-octet label limit, already-encoded
forms, and labels with no ACE at all (empty, leading/doubled separators,
over-long).

Pinned fuzz seed: 115320 (recorded here per the G-CONF contract).

Exit 0 iff zero disagreements over >= 1e5 inputs; on disagreement, print the
input and both outputs, exit 1. stdlib only.
"""
import json
import random
import sys

SEED = 115320
N_FUZZ_VALID = 100_000


# --- pure helpers from model.py (decorators stripped, PSeq -> tuple) ----------

def all_ascii(s):
    """Every code point of the sequence is an ASCII code point (< 128).
    Front-recursive so a single unfold is available per loop step."""
    if len(s) == 0:
        return True
    return s[0] < 128 and all_ascii(s[1:])


def seq_host_witness():
    """The non-ASCII domain label of the worked witness (code points
    U+6F22 U+5B57)."""
    return (28450, 23383)


def seq_ace_witness():
    """The standard ACE of seq_host_witness(): the eleven ASCII code points
    spelling ``xn--p8s937b``."""
    return (120, 110, 45, 45, 112, 56, 115, 57, 51, 55, 98)


# --- @ContractOnly callee: calls the REAL repo function (mapping.md) ----------

_REAL_TRANSFORM = None  # bound to the imported repo helper in main()


def ace_encode(domain):
    """Impl-callable face of the ACE transform. @ContractOnly in model.py, so
    per the G-CONF contract it invokes the REAL repo function it binds to,
    bridged List[int] <-> str."""
    return [ord(ch) for ch in _REAL_TRANSFORM("".join(chr(c) for c in domain))]


# --- impl regions of model.py, verbatim (contracts stripped) ------------------

def ascii_compatible_domain(domain):
    return ace_encode(domain)


def cached_host_name(platform_name):
    return ascii_compatible_domain(platform_name)


# --- partition classifier (the valid_label characteristic predicate) ----------

def is_valid_label(label):
    """valid_label(domain): the label HAS an ASCII-Compatible Encoding, i.e. the
    standard idna ToASCII transform answers it with a value. This is not an
    input filter -- both sides of the partition are admissible input and both
    are diffed. Classified with the stdlib codec, not the repo import, so the
    expectation is independent of the code under test."""
    try:
        label.encode('idna').decode('ascii')
    except (UnicodeError, UnicodeDecodeError):
        return False
    return True


# --- differential ---------------------------------------------------------------

def _outcome(fn, arg, decode):
    """Run one side and report its FULL observable outcome as a tagged pair:
    ("value", codepoints) when a value comes back, ("out-of-band", None) when the
    condition is reported instead. `decode` normalises the two carriers to the
    same comparable form (the shadow already answers in code points, the repo
    answers in `str`). Any other exception type is reported as itself so an
    unrelated crash is never silently read as the out-of-band outcome."""
    try:
        out = fn(arg)
    except (UnicodeError, UnicodeDecodeError):
        return ("out-of-band", None)
    except Exception as exc:                      # noqa: BLE001 - diagnostic
        return ("other-exception", "%s: %s" % (type(exc).__name__, exc))
    return ("value", decode(out))


def _as_codepoints(s):
    """Repo carrier `str` -> model carrier List[int] (mapping.md section 2)."""
    return [ord(ch) for ch in s]


def _already_codepoints(xs):
    """Shadow carrier: already a List[int]; copied so the comparison is by
    value and cannot alias the shadow's own result."""
    return list(xs)


def check_case(oracles, label, expect_value):
    """Diff both shadow functions against their repo oracles on one label (str
    form), on BOTH sides of the partition. `expect_value` is the independently
    classified side. Returns an error string on disagreement, else None."""
    real_transform, fresh_fqdn = oracles
    codepoints = [ord(ch) for ch in label]
    want = "value" if expect_value else "out-of-band"

    for name, shadow_fn, real_fn in (
            ("transform", ascii_compatible_domain, real_transform),
            ("cached host name", cached_host_name, fresh_fqdn)):
        shadow = _outcome(shadow_fn, list(codepoints), _already_codepoints)
        real = _outcome(real_fn, label, _as_codepoints)
        if shadow != real:
            return ("DISAGREEMENT (%s)\n  input=%r (codepoints %r)\n"
                    "  shadow=%r\n  real=%r"
                    % (name, label, codepoints, shadow, real))
        # The classification is CONFIRMED, not assumed: a real function that
        # answered an unencodable label with a substitute value (or refused an
        # encodable one) disagrees with the stdlib-derived expectation here.
        if real[0] != want:
            return ("DISAGREEMENT (%s: outcome side)\n  input=%r (codepoints %r)"
                    "\n  expected side=%r\n  real=%r"
                    % (name, label, codepoints, want, real))
    return None


def boundary_labels():
    witness = "".join(chr(c) for c in seq_host_witness())
    return [
        witness,                                   # the worked witness label
        "".join(chr(c) for c in seq_ace_witness()),  # its already-ASCII form
        "a", "z", "0", "9",
        "example", "example.com", "mail.example.com", "localhost",
        "test-host", "a-b-c", "django", "EXAMPLE", "MiXeD.CaSe",
        "127", "127.0.0.1",
        "a" * 60, "a" * 63,                        # near the label-length limit
        "sub." + "b" * 30 + ".example",
        "héllo", "münchen", "日本", "中国",
        "домен", "españa",
        witness + ".example.com",                  # non-ASCII label, dotted
        "www." + witness,
        # --- no ACE: the out-of-band side of the partition -------------------
        "a..b", ".lead", "sub..dom", "..", "a" * 64, "x." + "y" * 70,
        "\u3002abc", witness + ".." + witness,
    ]


ASCII_ALPHA = ([chr(c) for c in range(ord('a'), ord('z') + 1)]
               + [chr(c) for c in range(ord('0'), ord('9') + 1)] + ['-'])
NONASCII_ALPHA = [chr(c) for c in
                  [0x6f22, 0x5b57, 0xe9, 0xfc, 0xf1, 0x65e5, 0x672c, 0x4e2d,
                   0x56fd, 0x441, 0x43f, 0x3b1, 0x3b2, 0x11d, 0x131]]
ALPHABET = ASCII_ALPHA + NONASCII_ALPHA


def rand_oob_label(rng):
    """A candidate biased toward the out-of-band side: labels that are empty or
    far past the 63-octet limit are what the standard label-shape rules reject.
    Still classified independently -- some draws land on the value side."""
    n_labels = rng.randint(1, 3)
    parts = []
    for _ in range(n_labels):
        if rng.random() < 0.4:
            parts.append("")
        else:
            n = rng.randint(1, 70)
            parts.append("".join(rng.choice(ALPHABET) for _ in range(n)))
    return ".".join(parts)


def rand_label(rng):
    """A random host-name candidate: 1-3 dot-separated labels over an
    ASCII + non-ASCII alphabet (screened for validity by the caller)."""
    n_labels = 1 if rng.random() < 0.7 else rng.randint(2, 3)
    parts = []
    for _ in range(n_labels):
        n = rng.randint(1, 18)
        parts.append("".join(rng.choice(ALPHABET) for _ in range(n)))
    return ".".join(parts)


def main():
    global _REAL_TRANSFORM
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass

    # REAL patched repo functions (mapping.md section 1).
    from django.utils.encoding import punycode
    from django.core.mail import utils as mail_utils

    _REAL_TRANSFORM = punycode

    def fresh_fqdn(platform_name):
        """Oracle for the cached host name: a fresh cache object per input
        (the memoization is per-instance), with the platform-name callee
        stubbed to report `platform_name` (mapping.md section 2 models that
        callee's return as the model input)."""
        saved = mail_utils.socket.getfqdn
        mail_utils.socket.getfqdn = lambda *a, **kw: platform_name
        try:
            return mail_utils.CachedDnsName().get_fqdn()
        finally:
            mail_utils.socket.getfqdn = saved

    oracles = (punycode, fresh_fqdn)

    checked = 0
    n_boundary = 0
    n_value = 0
    n_oob = 0
    for label in boundary_labels():
        expect_value = is_valid_label(label)
        err = check_case(oracles, label, expect_value)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1
        n_value += 1 if expect_value else 0
        n_oob += 0 if expect_value else 1
    if n_boundary == 0:
        print("ERROR: no boundary label was diffed")
        return 1

    rng = random.Random(SEED)
    fuzz = 0
    while fuzz < N_FUZZ_VALID:
        # Draw from the general generator most of the time and from an
        # out-of-band-biased generator the rest, so both halves of the partition
        # are diffed at scale.
        label = rand_label(rng) if rng.random() < 0.7 else rand_oob_label(rng)
        expect_value = is_valid_label(label)
        err = check_case(oracles, label, expect_value)
        if err:
            print(err)
            return 1
        fuzz += 1
        checked += 1
        n_value += 1 if expect_value else 0
        n_oob += 0 if expect_value else 1
    if n_value == 0 or n_oob == 0:
        print("ERROR: only one side of the partition was exercised "
              "(%d value-yielding, %d out-of-band) -- the differential would "
              "be vacuous on the other half" % (n_value, n_oob))
        return 1

    # Sanity: the pinned witness value survived the diff above via the real
    # transform; assert the pure-helper encoding agrees with itself too.
    witness_out = ascii_compatible_domain(list(seq_host_witness()))
    if tuple(witness_out) != seq_ace_witness() or not all_ascii(witness_out):
        print("DISAGREEMENT (witness)\n  input=%r\n  shadow=%r\n  pinned=%r"
              % (list(seq_host_witness()), witness_out, list(seq_ace_witness())))
        return 1

    print("G-CONF OK: shadow impl == real repo transform + cached-host-name "
          "oracle on %d inputs (%d boundary + %d fuzz, seed %d), on BOTH sides "
          "of the partition (%d yielded a value, %d reported out of band, every "
          "side independently confirmed against the stdlib codec)."
          % (checked, n_boundary, fuzz, SEED, n_value, n_oob))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "boundary": n_boundary, "fuzz": fuzz,
                      "value_yielding": n_value, "out_of_band": n_oob,
                      "shadow": "contract-stripped impl regions; ContractOnly "
                                "callee bound to the real repo helper"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
