#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14792 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helper ``present_and_nonempty``
copies over as a plain function (the impl itself inlines the same test).
``PSeq[int]`` becomes a plain Python list of Unicode code points; the
``TimeZone`` model class becomes a minimal plain-attribute shim carrying the
same two fields. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL repo function the model models per mapping.md —
``django.utils.timezone._get_timezone_name(timezone)``. The gate applies the
diff to /testbed before this script runs; PYTHONPATH=/testbed makes the module
importable. This script never applies any diff itself.

Type bridge (mapping.md section 2): for a real tzinfo object ``tz``,
  tz.tzname(None)  (Optional[str])  -> short_label: Optional[List[int]]
                                       (None <-> absent, '' <-> empty list,
                                        a str <-> its code points)
  str(tz)          (str)            -> full_name: List[int]
and the real helper's returned str maps to the shadow's returned code-point
list the same way. The model's Requires are permission/termination only, so
every real tzinfo object yields a Requires-satisfying input.

Inputs: the real time-zone families the target test exercises
(datetime.timezone fixed offsets named/unnamed, pytz named + Etc/GMT zones,
zoneinfo named + Etc/GMT zones when available) as boundary cases, plus
>= 1e5 fuzz cases built from synthetic tzinfo objects whose two textual
observations are drawn independently (including None and the empty string for
the short label) so every branch of the selection is hit with arbitrary
content. Pinned fuzz seed: 147920.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + pytz/zoneinfo only (the modules the helper's own
test suite uses); no hypothesis needed.
"""
import datetime
import json
import random
import string
import sys

SEED = 147920
N_FUZZ = 100_000


# --- PSeq / TimeZone shims -----------------------------------------------------

class TimeZone:
    """Plain shim for model.py's TimeZone: carries the two observations."""

    def __init__(self, short_label, full_name):
        self.short_label = short_label  # Optional[List[int]]
        self.full_name = full_name      # List[int]


# --- pure region of model.py, contracts stripped -------------------------------

def present_and_nonempty(label):
    return label is not None and len(label) > 0


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def resolve_timezone_name(tz):
    label = tz.short_label
    if label is not None and len(label) > 0:
        return label
    return tz.full_name


# --- bridge: real tzinfo object <-> model carriers ------------------------------

def _codepoints(s):
    return [ord(ch) for ch in s]


def _carriers(tz):
    raw = tz.tzname(None)
    short_label = None if raw is None else _codepoints(raw)
    full_name = _codepoints(str(tz))
    return short_label, full_name


def check_one(real_fn, tz, label):
    short_label, full_name = _carriers(tz)
    shadow = resolve_timezone_name(TimeZone(short_label, full_name))
    real = _codepoints(real_fn(tz))
    if shadow != real:
        print("DISAGREEMENT on %s\n"
              "  tzname(None)=%r  str(tz)=%r\n"
              "  shadow=%r (%r)\n  real  =%r (%r)"
              % (label, tz.tzname(None), str(tz),
                 shadow, "".join(chr(c) for c in shadow),
                 real, "".join(chr(c) for c in real)))
        return False
    return True


# --- synthetic tzinfo: independent control of the two observations -------------

class SyntheticTZ(datetime.tzinfo):
    """A tzinfo whose short label and full rendering are arbitrary,
    independently chosen values (label may be None or '')."""

    def __init__(self, label, rendering):
        self._label = label
        self._rendering = rendering

    def tzname(self, dt):
        return self._label

    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def dst(self, dt):
        return datetime.timedelta(0)

    def __str__(self):
        return self._rendering

    def __repr__(self):
        return "SyntheticTZ(label=%r, rendering=%r)" % (self._label,
                                                        self._rendering)


def _rand_text(rng, alphabet, max_len):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, max_len)))


def main():
    from django.utils.timezone import _get_timezone_name as real_fn

    try:
        import pytz
    except ImportError:
        pytz = None
    try:
        import zoneinfo
    except ImportError:
        try:
            from backports import zoneinfo
        except ImportError:
            zoneinfo = None

    checked = 0
    ok = True

    # --- boundary: the real zone families the target test exercises ---------
    boundary = [(datetime.timezone.utc, "datetime.timezone.utc")]
    for h in range(-14, 15):
        for m in (0, 30, 45):
            off = datetime.timedelta(hours=h, minutes=m if h >= 0 else -m)
            boundary.append((datetime.timezone(off),
                             "datetime.timezone(%dh%dm)" % (h, m)))
            boundary.append((datetime.timezone(off, name="X/Custom%d" % h),
                             "datetime.timezone named %d" % h))
    named = ["Europe/Madrid", "America/Chicago", "Asia/Tokyo", "UTC",
             "Australia/Sydney", "America/New_York", "Europe/London",
             "Pacific/Auckland", "Africa/Cairo", "America/Sao_Paulo"]
    etc = ["Etc/GMT"] + ["Etc/GMT%+d" % n for n in range(-14, 13) if n != 0]
    if pytz is not None:
        for name in named + etc:
            try:
                boundary.append((pytz.timezone(name), "pytz %s" % name))
            except pytz.UnknownTimeZoneError:
                pass
        boundary.append((pytz.utc, "pytz.utc"))
    if zoneinfo is not None:
        for name in named + etc:
            try:
                boundary.append((zoneinfo.ZoneInfo(name), "zoneinfo %s" % name))
            except Exception:
                pass
    # explicit selection corners via synthetic objects: absent label, empty
    # label, label == rendering, label != rendering, empty-adjacent content
    boundary += [
        (SyntheticTZ(None, "Some/Zone"), "synthetic absent label"),
        (SyntheticTZ("", "Some/Zone"), "synthetic empty label"),
        (SyntheticTZ("+10", "Etc/Something"), "synthetic differing label"),
        (SyntheticTZ("Same", "Same"), "synthetic equal observations"),
        (SyntheticTZ(" ", "Some/Zone"), "synthetic whitespace label"),
        (SyntheticTZ("é☃", "Uni/Code"), "synthetic non-ascii label"),
        (SyntheticTZ(None, ""), "synthetic absent label empty rendering"),
        (SyntheticTZ("", ""), "synthetic both empty"),
        (SyntheticTZ("x", ""), "synthetic label with empty rendering"),
    ]
    n_boundary = 0
    for tz, label in boundary:
        ok = check_one(real_fn, tz, label) and ok
        checked += 1
        n_boundary += 1
        if not ok:
            return 1

    # --- fuzz: >= 1e5 synthetic observation pairs, pinned seed --------------
    rng = random.Random(SEED)
    alphabet = string.ascii_letters + string.digits + "+-/_: .é☃"
    for i in range(N_FUZZ):
        r = rng.random()
        if r < 0.25:
            label = None
        elif r < 0.40:
            label = ""
        else:
            label = _rand_text(rng, alphabet, 12)
        rendering = _rand_text(rng, alphabet, 24)
        tz = SyntheticTZ(label, rendering)
        if not check_one(real_fn, tz, "fuzz #%d" % i):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched name-resolution helper on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
