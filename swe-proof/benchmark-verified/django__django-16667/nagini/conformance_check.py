#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16667 (nagini).

SHADOW: the impl region of model.py's ``value_from_components``, copied
VERBATIM below (it contains no contract calls to strip). The @Pure helpers of
the pure region (``zero_zero_zero`` / ``absent_text``) copy over on a small
immutable-tuple PSeq shim and serve as internal cross-checks of the shadow's
branch outputs. The @ContractOnly callees are bound to the REAL repo-relied
functions per mapping.md section 3:

  * ``construct_date``   -> the platform calendar-date constructor
                            ``datetime.date(int(y), int(m), int(d))`` applied
                            to the probe's submitted components; its two
                            low-level rejection classes are re-raised as the
                            model's user-defined stand-ins (mapping.md sec. 2).
  * ``render_success``   -> ``date_value.strftime(input_format)`` with the
                            repo's own input-format derivation
                            (``get_format`` + ``sanitize_strftime_format``,
                            both unchanged callees).
  * ``render_out_of_range`` -> the repo's permissive pseudo-date rendering
                            ``"%s-%s-%s" % (y or 0, m or 0, d or 0)``.
  * ``retrieve_raw``     -> the raw datadict lookup under the field's own
                            (undecomposed) name, ``data.get(name)``.

ORACLE: the REAL patched repo method the model models per mapping.md
section 1 -- ``SelectDateWidget.value_from_datadict`` from
``django.forms.widgets``. The gate applies patch.diff to /testbed and sets
PYTHONPATH=/testbed before this script runs, so the import resolves to the
patched module.

TYPE BRIDGE (mapping.md section 2): the three submitted components (each
``Optional[str]``) lower to the booleans ``all_blank`` / ``all_present`` plus
the outcome tag ``kind`` (0 accepted / 1 out-of-range / 2 capacity-overflow),
classified by running the very constructor the widget invokes on the same
components. The repo return value (``str`` or ``None``) lifts to a
``List[int]`` of Unicode code points via ``ord``, with an absent value
lifting to the empty list; that encoding is sound here because every
text-producing branch of both sides yields non-empty text or the identical
raw datadict value (mapping.md section 2).

INPUT PLAN (>= 1e5 Requires-satisfying inputs): a full cross product of
boundary component pools (absent / blank / in-range / out-of-range /
non-numeric / whitespace-padded / signed / huge-magnitude values on either
side of the native conversion limit) crossed with raw-name datadict variants,
plus 100000 random fuzz probes over mixed component generators (pinned seed
16667). Every probe satisfies the model's preconditions by construction
(``all_blank`` implies ``all_present``; ``kind`` in {0,1,2}).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plus the patched repo for the oracle).
"""
import datetime
import json
import random
import sys

SEED = 16667
N_FUZZ = 100000
FIELD = "mydate"


# --- PSeq shim: immutable sequence with the operations the model uses --------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, copied as plain functions ----------------------

def zero_zero_zero():
    # the constant all-zero pseudo-date sentinel as code points
    return PSeq(48, 45, 48, 45, 48)


def absent_text():
    # the empty code-point sequence -- the rendering of an absent value
    return PSeq(48).take(0)


# --- the model's user-defined rejection stand-ins (model.py) -----------------

class DateOutOfRange(Exception):
    pass


class DateCapacityOverflow(Exception):
    pass


# --- per-probe context: the concrete submitted components + datadict ---------

_CTX = {"y": None, "m": None, "d": None, "data": None, "date_value": None}


# --- @ContractOnly callees bound to the REAL repo-relied functions -----------

def construct_date(kind):
    """REAL callee (mapping.md section 3.1): the platform calendar-date
    constructor on the probe's submitted components. Its two low-level
    rejection classes are re-raised as the model's stand-ins; a consistency
    assert documents the kind bridge (the driver classified kind by running
    this same call)."""
    y, m, d = _CTX["y"], _CTX["m"], _CTX["d"]
    try:
        _CTX["date_value"] = datetime.date(int(y), int(m), int(d))
    except ValueError:
        assert kind == 1, "kind bridge inconsistency (out-of-range)"
        raise DateOutOfRange()
    except OverflowError:
        assert kind == 2, "kind bridge inconsistency (capacity-overflow)"
        raise DateCapacityOverflow()
    assert kind == 0, "kind bridge inconsistency (accepted)"
    return 0


def render_success():
    """REAL callee (mapping.md section 3.2): the canonical rendering of the
    constructed date via the repo's own input-format derivation."""
    from django.utils import formats
    from django.utils.formats import get_format
    input_format = get_format("DATE_INPUT_FORMATS")[0]
    input_format = formats.sanitize_strftime_format(input_format)
    return [ord(ch) for ch in _CTX["date_value"].strftime(input_format)]


def render_out_of_range():
    """REAL callee (mapping.md section 3.3): the repo's permissive pseudo-date
    rendering from the submitted components."""
    y, m, d = _CTX["y"], _CTX["m"], _CTX["d"]
    return [ord(ch) for ch in "%s-%s-%s" % (y or 0, m or 0, d or 0)]


def retrieve_raw():
    """REAL callee (mapping.md section 3.4): the raw datadict lookup under the
    field's own (undecomposed) name; absent lifts to the empty list."""
    v = _CTX["data"].get(FIELD)
    return [] if v is None else [ord(ch) for ch in v]


# --- impl region of model.py, verbatim ----------------------------------------

def value_from_components(all_blank, all_present, kind):
    if all_blank:
        empty = []  # type: List[int]
        return empty
    if all_present:
        try:
            date_token = construct_date(kind)
            return render_success()
        except DateOutOfRange:
            return render_out_of_range()
        except DateCapacityOverflow:
            result = [48, 45, 48, 45, 48]  # type: List[int]
            return result
    return retrieve_raw()


# --- bridge: classify the constructor outcome for the submitted components ---

def classify_kind(y, m, d):
    """kind <-> how the real constructor behaves on the components
    (mapping.md section 2)."""
    try:
        datetime.date(int(y), int(m), int(d))
    except ValueError:
        return 1
    except OverflowError:
        return 2
    return 0


# --- oracle: the real patched repo method -------------------------------------

def _make_oracle():
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    import django
    django.setup()
    from django.forms.widgets import SelectDateWidget
    return SelectDateWidget()


def lift(value):
    """str/None -> code points; absent lifts to the empty list."""
    return [] if value is None else [ord(ch) for ch in value]


# --- differential driver -------------------------------------------------------

_ABSENT = object()


def check(widget, y, m, d, raw):
    """Run shadow and oracle on one probe; return an error string on
    disagreement, else None."""
    data = {}
    if y is not None:
        data[FIELD + "_year"] = y
    if m is not None:
        data[FIELD + "_month"] = m
    if d is not None:
        data[FIELD + "_day"] = d
    if raw is not _ABSENT:
        data[FIELD] = raw

    all_blank = (y == m == d == "")
    all_present = (y is not None and m is not None and d is not None)
    kind = 0
    if all_present and not all_blank:
        kind = classify_kind(y, m, d)

    _CTX["y"], _CTX["m"], _CTX["d"] = y, m, d
    _CTX["data"] = data
    _CTX["date_value"] = None

    shadow = value_from_components(all_blank, all_present, kind)
    real = lift(widget.value_from_datadict(data, {}, FIELD))
    if shadow != real:
        return ("DISAGREEMENT at y=%r m=%r d=%r raw=%r "
                "(all_blank=%r all_present=%r kind=%r):\n"
                "  shadow (impl region)       = %r\n"
                "  real (patched repo method) = %r"
                % (y, m, d,
                   ("<absent>" if raw is _ABSENT else raw),
                   all_blank, all_present, kind, shadow, real))
    # internal cross-checks against the pure-region helpers
    if all_blank and ToSeq(shadow) != absent_text():
        return "INTERNAL: all-blank branch is not the absent rendering"
    if all_present and not all_blank and kind == 2 \
            and ToSeq(shadow) != zero_zero_zero():
        return "INTERNAL: capacity-overflow branch is not the sentinel"
    return None


# --- input generation ----------------------------------------------------------

BIG = str(sys.maxsize + 1)          # just past the native conversion limit
BIGNEG = str(-sys.maxsize - 2)
HUGE = str(2 ** 200)

YEARS = [None, "", "0", "1", "999", "1000", "1900", "2016", "2023", "9999",
         "10000", "-1", str(sys.maxsize), BIG, BIGNEG, HUGE, "abc", " 7 ",
         "07"]
MONTHS = [None, "", "0", "1", "2", "12", "13", "-1", BIG, "abc", "06"]
DAYS = [None, "", "0", "1", "28", "29", "30", "31", "32", "-1", BIG, "abc",
        "1_0"]
RAWS = [_ABSENT, None, "", "2008-4-1", "free text &"]

SMALL_NUMS = [str(i) for i in range(0, 33)] + \
             ["99", "100", "999", "1000", "2016", "2023", "9999", "10000"]
WEIRD = ["abc", "1x", "+", "-", "+7", "1_0", "٤", "2.5", "1e2", "0x10",
         "nan", "\t3\n", "00", " "]


def gen_component(rng):
    r = rng.random()
    if r < 0.08:
        return None
    if r < 0.22:
        return ""
    if r < 0.60:
        mag = rng.choice([1, 1, 1, 2, 2, 4, 4, 5, 10, 19, 20, 40])
        s = "".join(rng.choice("0123456789") for _ in range(mag))
        if rng.random() < 0.15:
            s = "-" + s
        if rng.random() < 0.10:
            s = " " + s + " "
        return s
    if r < 0.80:
        return rng.choice(SMALL_NUMS)
    return rng.choice(WEIRD)


def gen_raw(rng):
    r = rng.random()
    if r < 0.50:
        return _ABSENT
    if r < 0.60:
        return ""
    if r < 0.75:
        return "2008-4-1"
    n = rng.randint(1, 8)
    return "".join(rng.choice("01239-a&. ") for _ in range(n))


def main():
    widget = _make_oracle()

    checked = 0
    boundary = 0
    for y in YEARS:
        for m in MONTHS:
            for d in DAYS:
                for raw in RAWS:
                    err = check(widget, y, m, d, raw)
                    if err:
                        print(err)
                        return 1
                    checked += 1
                    boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        y = gen_component(rng)
        m = gen_component(rng)
        d = gen_component(rng)
        err = check(widget, y, m, d, gen_raw(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched widget method on %d probes "
          "(%d boundary cross-product + %d fuzz, seed %d); 0 disagreements."
          % (checked, boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
