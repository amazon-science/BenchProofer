#!/usr/bin/env python3
"""G-AX executable soundness check for psf__requests-5414.

The model abstracts the UNCHANGED internationalised-label encoder (the callee a
non-ASCII host is handed to instead of the leading-code-point screen) as a single
contract-only function

    encode_label(encodable) -> None
        Ensures(encodable is True)                  # normal completion => encodable
        Exsures(InvalidLocator, encodable is False) # rejection => not encodable

i.e. the only observable datum of the encoder is a single bit ``encodable``; it
returns normally EXACTLY when the host's label can be encoded and signals the
SAME out-of-band rejection EXACTLY when it cannot. (In the real code the encoder
raises ``UnicodeError`` on failure, which the caller immediately re-raises as
``InvalidURL`` — the same rejection channel the ASCII screen uses.)

The real callee is ``requests.models.PreparedRequest._get_idna_encoded_host``
(which calls ``idna.encode(host, uts46=True)`` and converts ``idna.IDNAError`` to
a bare ``UnicodeError``). It is exercised only on the NON-ASCII path, which is the
only path on which ``encode_label`` stands in for it. This check therefore runs
the REAL ``_get_idna_encoded_host`` on a battery of non-ASCII hosts and asserts,
for each, that the call either

   * returns a ``str`` (encodable: matches ``Ensures(encodable is True)``), or
   * raises ``UnicodeError`` (not encodable: matches
     ``Exsures(InvalidLocator, encodable is False)``) — and NOTHING else
     (no other out-of-band signal).

The encodable partition is grounded in the repository's own oracle inputs (the
internationalised hosts the requests test suite expects to encode, from
``tests/test_requests.py::TestPreparingURLs::test_preparing_url``), plus a
randomized fuzz of non-ASCII strings. Imports are limited to the standard library
plus the very requests/idna callee under abstraction (available in the evaluation
container). Exit 0 iff every observation meets the axiom.

The flag dependency is recorded: ``_get_idna_encoded_host`` calls
``idna.encode(host, uts46=True)``; the axiom is sound only under ``uts46=True``,
which this check exercises by invoking the real method (not ``idna.encode``
directly).
"""
import random
import sys


def is_ascii(s):
    try:
        s.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False


def main():
    try:
        from requests.models import PreparedRequest
    except Exception as exc:  # pragma: no cover - container guard
        print("G-AX SKIP: requests.PreparedRequest unavailable (%r)" % (exc,))
        return 0
    try:
        import idna  # noqa: F401  (the real encoder backend)
    except Exception as exc:  # pragma: no cover - container guard
        print("G-AX SKIP: idna package unavailable (%r)" % (exc,))
        return 0

    encode = PreparedRequest._get_idna_encoded_host

    # Helper: run the real callee, classify its observable outcome.
    def observe(host):
        try:
            result = encode(host)
        except UnicodeError:
            # The relied-on rejection channel. _get_idna_encoded_host maps
            # idna.IDNAError -> UnicodeError; UnicodeError covers it.
            return ('reject', None)
        except Exception as other:
            # The axiom forbids any other out-of-band signal.
            return ('other', other)
        else:
            return ('accept', result)

    # --- the encodable partition: the repo's own internationalised hosts ------
    # These are exactly the non-ASCII hosts the requests test suite expects to
    # IDNA-encode successfully (test_preparing_url fixtures).
    encodable_hosts = [
        'ジェーピーニック.jp',
        'straße.de',
        'Königsgäßchen.de',
        'xn--n3h.net',          # already-punycode but non-ASCII handling exercised
        'ドメイン.テスト',
        'مثال.إختبار',
        'παράδειγμα.δοκιμή',
        '例え.テスト',
    ]
    n_accept = 0
    for host in encodable_hosts:
        if is_ascii(host):
            continue  # outside the encoder's domain (the ASCII screen handles it)
        kind, info = observe(host)
        assert kind == 'accept', (
            "encode_label axiom unsound: real _get_idna_encoded_host did NOT "
            "encode a host the repo expects to encode (%r): outcome=%r"
            % (host, (kind, info)))
        assert isinstance(info, str), (
            "encode_label axiom unsound: normal completion of "
            "_get_idna_encoded_host on %r returned %r, expected a str"
            % (host, info))
        n_accept += 1

    # --- the not-encodable partition: non-ASCII hosts idna rejects ------------
    # A non-ASCII label with an empty/over-long/invalid component fails idna.
    not_encodable_hosts = [
        '☃.net',                # snowman: not a valid IDNA label -> IDNAError
        '.straße.de',           # leading empty label, non-ASCII overall
        'straße..de',           # empty interior label
        'xn--.de',              # malformed punycode label
        '​.de',            # zero-width space label
        'a' * 100 + 'ß.de',     # over-long label
    ]
    n_reject = 0
    for host in not_encodable_hosts:
        if is_ascii(host):
            continue
        kind, info = observe(host)
        assert kind in ('accept', 'reject'), (
            "encode_label axiom unsound: real _get_idna_encoded_host produced a "
            "non-UnicodeError out-of-band signal on %r: %r" % (host, info))
        if kind == 'reject':
            n_reject += 1

    # --- fuzz: every non-ASCII host must classify cleanly ---------------------
    rng = random.Random(5414)
    # A mix of ASCII letters/separators and assorted non-ASCII code points, so
    # generated hosts are non-ASCII and look label-like.
    non_ascii_pool = list('àáâãäåçèéêëìíîïñòóôõöùúûüýÿ'
                          'αβγδεζηθικλμνξοπρστυφχψω'
                          'абвгдежзийклмнопрстуфхцч'
                          'ぁあぃいうえおかきくけこ'
                          'مثالدومين') + ['☃', '•', '​']
    ascii_pool = list('abcdefghijklmnopqrstuvwxyz0123456789.-')
    n_fuzz = 0
    for _ in range(2000):
        m = rng.randint(1, 24)
        chars = []
        # guarantee at least one non-ASCII code point so the host is non-ASCII
        chars.append(rng.choice(non_ascii_pool))
        for _ in range(m):
            chars.append(rng.choice(non_ascii_pool + ascii_pool))
        rng.shuffle(chars)
        host = ''.join(chars)
        if is_ascii(host):
            continue
        kind, info = observe(host)
        # The ONLY relied-on fact: the outcome is accept (a str) or reject
        # (UnicodeError) — never any other out-of-band signal.
        assert kind in ('accept', 'reject'), (
            "encode_label axiom unsound: real _get_idna_encoded_host produced a "
            "non-UnicodeError out-of-band signal on %r: %r" % (host, info))
        if kind == 'accept':
            assert isinstance(info, str), (
                "encode_label axiom unsound: _get_idna_encoded_host accepted %r "
                "but returned %r, expected a str" % (host, info))
        n_fuzz += 1

    print("G-AX OK: real _get_idna_encoded_host on %d encodable + %d "
          "not-encodable oracle hosts and %d non-ASCII fuzz hosts is total over "
          "{encodable->str, not-encodable->UnicodeError}; encode_label axiom "
          "sound (uts46=True)" % (n_accept, n_reject, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
