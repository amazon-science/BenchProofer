#!/usr/bin/env python3
"""G-CONF for django__django-11532.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_hostName` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`django.core.mail.utils.CachedDnsName.get_fqdn`, over >=1e5 fuzzed inputs.
Zero disagreements => exit 0.

Type bijection (mapping.md):
  st : NameHolder      <-> the CachedDnsName holder, whose whole modeled state is
                           its one storage slot: `slot = none` <-> the instance
                           has no `_fqdn` attribute, `slot = some n` <-> the
                           attribute is present and holds `n`
  reportedName         <-> the host name socket.getfqdn() reports (str)
  result : NameHolder x String
                       <-> (the holder's slot AFTER the call, the value returned)
  aceEncode            <-> str.encode('idna').decode('ascii')  (unchanged codec)

Both components of the modeled result are compared, so this gate checks the
STATE effect (the slot is occupied afterwards, by exactly the served name) as
well as the returned value. That is what makes the occupancy clause in
problem_spec_hostName a claim about the real callee rather than about the model
alone: a run where get_fqdn returned the right name but left the slot empty
would be a disagreement here.

The slot's two shapes are BOTH driven: for each fuzzed reported name the pair
(slot = absent, slot = some stored) is exercised, so the settle path and the
reuse path are each checked against the real callee.

stdlib-only; no hypothesis required. Pinned seed = 11532 (mapping.md).
"""
import random
import socket
import sys
from unittest import mock

from django.core.mail.utils import CachedDnsName

SEED = 11532
N = 100_000


def ace_encode(name: str) -> str:
    """`aceEncode` realized as the real unchanged IDNA/ACE codec."""
    return name.encode('idna').decode('ascii')


def shadow(slot, reported_name: str):
    """R/I transliteration of implementation_hostName.

        let mut holder := st
        if holder.slot = none then
          holder := { holder with slot := some (aceEncode reportedName) }
        let served := holder.slot.getD (aceEncode reportedName)
        return (holder, served)

    `Option String` <-> `str | None`, so every emptiness test is `is None`
    (a stored empty name is `some ""`, not absence). The `getD` default is
    unreachable after the branch above -- the slot is occupied on both arms --
    so the encoder is invoked exactly once, on the settle path, which is where
    the real callee invokes it too.
    """
    holder = slot
    if holder is None:
        holder = ace_encode(reported_name)
    served = holder
    return holder, served


def real_get_fqdn(slot, reported_name: str):
    """Drive the REAL patched get_fqdn on a holder in the given slot state, with
    socket.getfqdn -> reported_name, and read BOTH observables back: the slot
    state afterwards and the returned value."""
    dns = CachedDnsName()
    if hasattr(dns, '_fqdn'):
        delattr(dns, '_fqdn')
    if slot is not None:
        dns._fqdn = slot
    with mock.patch.object(socket, 'getfqdn', return_value=reported_name):
        value = dns.get_fqdn()
    after = dns._fqdn if hasattr(dns, '_fqdn') else None
    return after, value


def gen_names(rng: random.Random, count: int):
    # Fixed boundary / regression names.
    fixed = [
        "example.com",
        "localhost",
        "EXAMPLE.COM",
        "mail.example.co.uk",
        "a.b.c.d",
        "xn--p8s937b",            # already-ACE
        "host123",
        "sub.domain-name.org",
    ]
    for s in fixed:
        yield s
    # Unicode-label hosts whose ACE form is non-trivial (these are exactly the
    # inputs the issue is about).
    unicode_labels = [
        "漢字",            # han zi  -> xn--p8s937b
        "正宗",            # zheng zong
        "über",               # uber (umlaut)
        "münchen.de",
        "例え.テスト",
        "café.fr",
    ]
    for s in unicode_labels:
        yield s
    # Fuzz: random ASCII label hosts + random unicode-augmented hosts.
    ascii_chars = "abcdefghijklmnopqrstuvwxyz0123456789-"
    extra = "éüñ漢字åα中"
    n_done = len(fixed) + len(unicode_labels)
    for _ in range(count - n_done):
        nlabels = rng.randint(1, 3)
        labels = []
        for _ in range(nlabels):
            ln = rng.randint(1, 8)
            pool = ascii_chars + (extra if rng.random() < 0.5 else "")
            label = "".join(rng.choice(pool) for _ in range(ln))
            # IDNA labels may not start/end with hyphen; keep it simple/legal-ish.
            label = label.strip("-") or "a"
            labels.append(label)
        yield ".".join(labels)


def gen_inputs(rng: random.Random):
    """(slot, reportedName) pairs. Every name is driven on BOTH slot shapes, so
    half the cases exercise settling and half exercise reuse. The occupied slot
    carries names deliberately DIFFERENT from the reported one (including the
    empty name, the falsy boundary a `not self._fqdn` reading would get wrong),
    so a rival that re-settles an occupied slot is separated from one that
    serves it."""
    stored_pool = ["", "cached.example.org", "xn--p8s937b", "OLD.NAME",
                   "held-value", "漢字"]
    i = 0
    for name in gen_names(rng, N // 2):
        yield None, name
        yield stored_pool[i % len(stored_pool)], name
        i += 1


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    checked = 0
    for slot, name in gen_inputs(rng):
        # An input that the REAL codec rejects (UnicodeError) is outside the
        # modeled domain (the patched get_fqdn would raise too) -- require the
        # shadow to raise on exactly the same inputs.
        shadow_err = real_err = None
        s = r = None
        try:
            s = shadow(slot, name)
        except Exception as e:                       # noqa: BLE001
            shadow_err = type(e).__name__
        try:
            r = real_get_fqdn(slot, name)
        except Exception as e:                       # noqa: BLE001
            real_err = type(e).__name__
        checked += 1
        if shadow_err is not None or real_err is not None:
            # Both must raise (same error class) or both succeed.
            if shadow_err != real_err:
                disagreements += 1
                if len(examples) < 10:
                    examples.append((slot, name, f"err:{shadow_err}",
                                     f"err:{real_err}"))
            continue
        if s != r:
            disagreements += 1
            if len(examples) < 10:
                examples.append((slot, name, s, r))

    print(f"G-CONF django__django-11532: {checked} inputs, "
          f"{disagreements} disagreements")
    if disagreements:
        for slot, name, s, r in examples:
            print(f"  DISAGREE slot={slot!r} name={name!r} shadow={s!r} real={r!r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
