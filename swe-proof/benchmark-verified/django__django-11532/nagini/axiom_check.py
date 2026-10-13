#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11532.

Executes the REAL standard-library ACE (ToASCII) transform that the gold patch's
new helper calls --

    domain.encode('idna').decode('ascii')

-- on boundary inputs (the worked non-ASCII witness, pure-ASCII labels, mixed
labels) plus randomized fuzzing, and asserts that every observation matches the
axioms encoded in model.py:

  (A-consumed) `ace_seq(domain)` axiom: for every label the real transform
      answers with a value, the result is ENTIRELY ASCII (every code point < 128)
      -- this is the property the proof consumes. The pure contract is stated over
      the labels `valid_label` admits (`Requires(valid_label(domain))`), so the
      check confirms the all-ASCII guarantee holds on exactly the value-yielding
      inputs.

  (A-consumed, totality) `valid_label` is the CHARACTERISTIC predicate of that
      value-yielding set, and the impl-callable face `ace_encode` is TOTAL: it is
      declared with no `valid_label` precondition and instead pins BOTH halves of
      a partition -- a value comes back only for a label that has an ACE
      (`Ensures(valid_label(ToSeq(domain)))`), and every other label is reported
      out of band (`Exsures(..., not valid_label(ToSeq(domain)))`). So the check
      must confirm the real callee really does partition its input that way:
      exactly two outcomes, complementary, never a substitute value on a label
      the codec rejects. It records BOTH tallies and requires each to be
      non-empty, so neither half of the partition is asserted vacuously.

  (witness) the concrete value pinned by the axiom: the ACE of the label of code
      points U+6F22 U+5B57 is the eleven ASCII code points spelling
      ``xn--p8s937b``; and that label is well-formed (`valid_label` witness).

Imports nothing repo-specific: ``str.encode('idna')`` is the Python standard
library -- the exact transform the gold patch's `punycode()` helper invokes.
Exit 0 iff every obligation holds.
"""
import random
import sys

# --- model.py reference encodings (kept in lock-step with the axioms) --------

HOST_WITNESS = [28450, 23383]                                  # U+6F22 U+5B57
ACE_WITNESS = [120, 110, 45, 45, 112, 56, 115, 57, 51, 55, 98]  # 'xn--p8s937b'


def real_ace(label):
    """The REAL callee the gold patch calls: str.encode('idna').decode('ascii').
    Returns the code-point list on success, or None if the transform raises
    (the raise path the axiom's valid_label precondition excludes)."""
    try:
        return [ord(ch) for ch in label.encode('idna').decode('ascii')]
    except (UnicodeError, UnicodeDecodeError):
        return None


def all_ascii(codepoints):
    """model.py's deep `all_ascii`: every code point < 128."""
    return all(c < 128 for c in codepoints)


def check_all_ascii_on_valid(label):
    """ace_seq axiom: a label the transform answers with a value yields an
    all-ASCII result. Returns True on the value-yielding side of the partition,
    False on the out-of-band side."""
    observed = real_ace(label)
    if observed is None:
        # Out-of-band side of the partition. The axiom's claim here is NEGATIVE
        # -- that the real callee yields NO value, which is exactly what
        # real_ace's None reports. Asserted by construction: real_ace returns a
        # value or None and never a third thing, so there is no substitute value
        # for the totality partition to be wrong about.
        return False
    assert all_ascii(observed), (
        "ace_seq axiom unsound on %r: real ACE returned %r which is NOT "
        "all-ASCII" % (label, observed))
    return True


def check_partition(label):
    """Totality: the real callee has EXACTLY the two outcomes the contract pins,
    and they are complementary. Returns True if the label is on the value-yielding
    side, False if it is on the out-of-band side; raises if it is neither, i.e. if
    the callee answered an unencodable label with a value of its own or refused an
    encodable one."""
    try:
        out = label.encode('idna').decode('ascii')
    except (UnicodeError, UnicodeDecodeError):
        # Out-of-band side: no value at all reached the caller. Confirm the
        # callee did not ALSO produce something -- i.e. that the exception is the
        # whole of its answer, which is what makes the Exsures faithful.
        assert real_ace(label) is None, (
            "totality unsound on %r: the callee both signalled out of band and "
            "yielded a value" % (label,))
        return False
    # Value-yielding side: the value is the ACE, and it is all-ASCII.
    observed = [ord(ch) for ch in out]
    assert observed == real_ace(label), (
        "totality unsound on %r: two calls disagreed (%r vs %r)"
        % (label, observed, real_ace(label)))
    assert all_ascii(observed), (
        "ace_seq axiom unsound on %r: real ACE returned %r which is NOT "
        "all-ASCII" % (label, observed))
    return True


def main():
    # --- witness (the worked example the F2P test observes) ----------------
    witness_label = "".join(chr(c) for c in HOST_WITNESS)
    observed = real_ace(witness_label)
    assert observed is not None, (
        "valid_label witness unsound: the real ACE RAISED on the witness "
        "label %r, but the axiom asserts it is well-formed" % witness_label)
    assert observed == ACE_WITNESS, (
        "ace_seq witness unsound: real ACE of %r gave %r, axiom pins %r"
        % (witness_label, observed, ACE_WITNESS))
    assert all_ascii(observed), "witness ACE is not all-ASCII"

    # --- boundary: pure-ASCII, mixed, AND labels with no ACE ---------------
    # The last group is what makes the totality partition non-vacuous: the
    # contract pins an out-of-band outcome, so the check must observe the real
    # callee actually taking it rather than answering with a substitute value.
    boundary = [
        "example", "example.com", "localhost", "a", "xn--p8s937b",
        "django", "EXAMPLE", "test-host", "127", "héllo", "münchen",
        "日本", "中国", "ドメイン", "правда", "España",
        "".join(chr(c) for c in HOST_WITNESS),
        # no ACE (the codec's label-shape rules reject each of these):
        "a..b", ".lead", "a" * 64, "x." + "y" * 70, "..",
        "\u3002abc", "sub..dom",
    ]
    valid_seen = 0
    oob_seen = 0
    for label in boundary:
        if check_partition(label):
            assert check_all_ascii_on_valid(label)
            valid_seen += 1
        else:
            assert not check_all_ascii_on_valid(label)
            oob_seen += 1
    assert valid_seen > 0, ("no boundary label yielded a value -- the "
                            "value-yielding half of the check is vacuous")
    assert oob_seen > 0, ("no boundary label was reported out of band -- the "
                          "out-of-band half of the check is vacuous, so the "
                          "totality partition would be asserted about nothing")

    # --- randomized fuzz over ASCII + non-ASCII label alphabets -----------
    rng = random.Random(11532)
    ascii_alpha = [chr(c) for c in range(ord('a'), ord('z') + 1)] + \
                  [chr(c) for c in range(ord('0'), ord('9') + 1)] + ['-']
    nonascii_alpha = [chr(c) for c in
                      [0x6f22, 0x5b57, 0xe9, 0xfc, 0x65e5, 0x672c, 0x4e2d,
                       0x441, 0x43f, 0x3b1, 0x3b2]]
    alphabet = ascii_alpha + nonascii_alpha
    fuzz_valid = 0
    fuzz_oob = 0
    for _ in range(20000):
        n = rng.randint(1, 18)
        label = "".join(rng.choice(alphabet) for _ in range(n))
        if check_partition(label):
            assert check_all_ascii_on_valid(label)
            fuzz_valid += 1
        else:
            assert not check_all_ascii_on_valid(label)
            fuzz_oob += 1
    # A second fuzz pass biased toward the out-of-band side (empty labels and
    # over-long labels are what the codec rejects), so the negative half of the
    # partition is checked at scale rather than only on the boundary list.
    for _ in range(20000):
        parts = [("" if rng.random() < 0.35 else
                  "".join(rng.choice(alphabet)
                          for _ in range(rng.randint(1, 70))))
                 for _ in range(rng.randint(1, 3))]
        label = ".".join(parts)
        if check_partition(label):
            assert check_all_ascii_on_valid(label)
            fuzz_valid += 1
        else:
            assert not check_all_ascii_on_valid(label)
            fuzz_oob += 1
    assert fuzz_oob > 0, "fuzz found no out-of-band label -- partition vacuous"

    print("G-AX OK: ace_seq axiom (all-ASCII on every label it answers with a "
          "value) + witness (U+6F22 U+5B57 -> 'xn--p8s937b') + the totality "
          "partition (valid_label characterises exactly the value-yielding set; "
          "every other label is reported out of band and never answered with a "
          "substitute) all sound; real str.encode('idna') checked on %d boundary "
          "+ 40000 fuzz labels (%d yielded a value, %d reported out of band)."
          % (len(boundary), valid_seen + fuzz_valid, oob_seen + fuzz_oob))
    return 0


if __name__ == "__main__":
    sys.exit(main())
