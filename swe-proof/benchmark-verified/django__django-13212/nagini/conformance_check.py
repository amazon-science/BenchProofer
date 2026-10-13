#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13212 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. The @Pure name-token helpers ``placeholder_value`` /
``placeholder_limit`` copy over as plain functions; ``PSeq`` becomes an
immutable-tuple shim and ``ToSeq`` its constructor. There is no @ContractOnly
callee in this bundle (the behaviour is modelled deeply).

ORACLE: the REAL patched repo behaviour the model models per mapping.md §1 —
the parameter mapping each rejection produces, observed as ``e.params`` of the
``ValidationError`` a real validator raises in-container (the gate applies
patch.diff to /testbed before this script runs):

  * ``build_invalid_params(value)``  <->  the params of every bare rejection
    (regex/URL/email/ip/comma-list/null-character validators, and the
    decimal validator's not-representable rejection);
  * ``build_limit_params(value, limit)``  <->  the params of the decimal
    validator's three magnitude rejections (the limit for each rejection code
    is computed from the validator's own configuration, NOT read back from
    the observed params, so the limit entry of the comparison is
    non-tautological);
  * ``decimal_reject_params(finite, value)``  <->  the params a rejected
    not-representable decimal candidate produces, observed both at the raw
    validator layer and end-to-end through the form field (which exercises
    the modelled control-flow: no field-layer screen intercepts with a
    parameter-less error first). The real counterpart's reachable domain has
    ``finite`` False (a representable candidate never reaches that bare
    rejection — its magnitude rejections are the limit shape checked above),
    matching the model's delegation to the bare-rejection mapping; the
    ``finite`` True closure of the spec is a strengthening with no distinct
    real observation, so the differential domain here is the reachable one.

TYPE BRIDGE (mapping.md §2): the offending input / the numeric limit are
carried as ``List[int]`` of Unicode code points of their string form
(``str(...)``, identity for str inputs); the params dict is
``Dict[int, PSeq[int]]`` from a placeholder-name token to the rendered string
of that placeholder. Bridge of a real observation: key ``'value'`` -> token
``placeholder_value()``, key ``'max'`` -> token ``placeholder_limit()``,
each real entry value ``v`` -> the code points of ``str(v)``. Any other real
key is unbridgeable and reported as a disagreement (the spec closes the key
set).

>= 1e5 Requires-satisfying inputs (every readable code-point list satisfies
the Requires; the differential domain is the set of real rejection events,
each yielding one shadow-vs-oracle comparison): curated boundary rejections +
guaranteed-rejecting fuzz across seven bare-rejection validator families +
fuzzed decimal magnitude rejections (all three codes) + not-representable
decimal shapes raw and through the form. Pinned fuzz seed: 13212.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from decimal import Decimal, InvalidOperation

SEED = 13212


# --- PSeq shim: immutable sequence -------------------------------------------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __iter__(self):
        return iter(self._t)

    def __eq__(self, other):
        if isinstance(other, PSeq):
            return self._t == other._t
        return NotImplemented

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def placeholder_value():
    """Name token of the placeholder bound to the offending input."""
    return 0


def placeholder_limit():
    """Name token of the placeholder bound to a numeric limit."""
    return 1


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def build_invalid_params(value):
    params = {}  # type: dict
    params[placeholder_value()] = ToSeq(value)
    return params


def build_limit_params(value, limit):
    params = {}  # type: dict
    params[placeholder_limit()] = ToSeq(limit)
    params[placeholder_value()] = ToSeq(value)
    return params


def decimal_reject_params(finite, value):
    return build_invalid_params(value)


# --- bridge -------------------------------------------------------------------

KEY_TOKEN = {"value": placeholder_value(), "max": placeholder_limit()}
TOKEN_NAME = {v: k for k, v in KEY_TOKEN.items()}


def codes(s):
    return [ord(ch) for ch in s]


def bridge_real(real_params):
    """Lower a real params mapping to the model carrier: name-token ->
    code-point tuple of the entry's string form. Returns (mapping, None) or
    (None, error string) if a key is outside the modelled name-token space."""
    out = {}
    for k, v in (real_params or {}).items():
        if k not in KEY_TOKEN:
            return None, "real params carry unbridgeable key %r" % (k,)
        out[KEY_TOKEN[k]] = tuple(codes(str(v)))
    return out, None


def shadow_plain(shadow_map):
    return dict((k, tuple(v)) for k, v in shadow_map.items())


def diff_report(tag, input_repr, shadow_map, real_params):
    """Compare shadow map vs bridged real params; return error string or None."""
    bridged, err = bridge_real(real_params)
    if err is not None:
        return ("DISAGREEMENT [%s] on input %s:\n  shadow = %r\n  real params = %r\n  (%s)"
                % (tag, input_repr, shadow_plain(shadow_map), real_params, err))
    plain = shadow_plain(shadow_map)
    if plain != bridged:
        return ("DISAGREEMENT [%s] on input %s:\n  shadow (impl region) = %r\n"
                "  real (patched repo, bridged) = %r\n  raw real params = %r"
                % (tag, input_repr, plain, bridged, real_params))
    return None


# --- oracle harness ------------------------------------------------------------

def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True, DATABASES={}, INSTALLED_APPS=[],
                           USE_I18N=False)
    django.setup()


def observe_rejection(callable_validator, value):
    """Call a real validator; return its error's params mapping, or a
    sentinel if it accepted (generation slip, not an observation)."""
    from django.core.exceptions import ValidationError
    try:
        callable_validator(value)
    except ValidationError as e:
        return getattr(e, "params", None)
    return _ACCEPTED


_ACCEPTED = object()


# --- differential drivers --------------------------------------------------------

class Counter(object):
    def __init__(self):
        self.n = 0


def check_bare(validator, value, counter):
    """One bare-rejection comparison: shadow build_invalid_params vs the real
    rejection's params."""
    real = observe_rejection(validator, value)
    if real is _ACCEPTED:
        return None  # not a rejection event; no observation
    shadow = build_invalid_params(codes(str(value)))
    counter.n += 1
    return diff_report("bare", repr(value), shadow, real)


LIMIT_OF_CODE = {
    "max_digits": lambda d, p: d,
    "max_decimal_places": lambda d, p: p,
    "max_whole_digits": lambda d, p: d - p,
}


def check_decimal(dv, d_cfg, p_cfg, value, counter_limit, counter_bare):
    """One decimal-validator comparison. A magnitude rejection compares
    against build_limit_params (limit derived from the validator's own
    configuration and the rejection code); a not-representable rejection
    compares against decimal_reject_params with the finiteness bit read off
    the candidate itself."""
    from django.core.exceptions import ValidationError
    try:
        dv(value)
    except ValidationError as e:
        code = getattr(e, "code", None)
        real = getattr(e, "params", None)
        vstr = str(value)
        if code in LIMIT_OF_CODE:
            limit = LIMIT_OF_CODE[code](d_cfg, p_cfg)
            shadow = build_limit_params(codes(vstr), codes(str(limit)))
            counter_limit.n += 1
            return diff_report("limit/%s" % code, repr(vstr), shadow, real)
        # bare rejection of a candidate: the modelled decimal routing
        shadow = decimal_reject_params(value.is_finite(), codes(vstr))
        counter_bare.n += 1
        return diff_report("decimal-bare", repr(vstr), shadow, real)
    return None


def check_decimal_form(field, raw, counter):
    """End-to-end through the form field: the rejection a not-representable
    candidate produces after field-layer cleaning must carry the same mapping
    the shadow builds — i.e. no field-layer screen intercepted with a
    parameter-less error."""
    from django.core.exceptions import ValidationError
    try:
        field.clean(raw)
    except ValidationError as e:
        err = e.error_list[0]
        real = getattr(err, "params", None)
        d = Decimal(raw)
        shadow = decimal_reject_params(d.is_finite(), codes(str(d)))
        counter.n += 1
        return diff_report("decimal-form", repr(raw), shadow, real)
    return "decimal-form: field unexpectedly accepted %r" % (raw,)


# --- input generation --------------------------------------------------------------

def bare_boundary_cases(validators_mod):
    v = validators_mod
    return [
        (v.validate_integer, "-42.5"),
        (v.validate_integer, "abc"),
        (v.validate_integer, ""),
        (v.validate_email, "a"),
        (v.validate_email, "a@b\n.com"),
        (v.validate_email, "a\n@b.com"),
        (v.validate_slug, "\u4f60 \u597d"),
        (v.validate_unicode_slug, "\u4f60 \u597d"),
        (v.validate_ipv4_address, "256.1.1.1"),
        (v.validate_ipv6_address, "1:2"),
        (v.validate_ipv46_address, "256.1.1.1"),
        (v.validate_comma_separated_integer_list, "a,b,c"),
        (v.int_list_validator(), "-1,2,3"),
        (v.URLValidator(), "no_scheme"),
        (v.URLValidator(), "http://test[.com"),
        (v.URLValidator(), "http://[::1:2::3]/"),
        (v.URLValidator(), "http://" + ".".join(["a" * 35 for _ in range(9)])),
        (v.RegexValidator("[0-9]+"), "xxxxxx"),
        (v.ProhibitNullCharactersValidator(), "a\x00b"),
        (v.ProhibitNullCharactersValidator(), "\x00"),
    ]


_TEXT = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_PUNCT = " .,-_:;/@#%&+=!?'\"()[]{}"
_UNI = "\u00e9\u2022\u4f60\u597d\U0001F600\u00a0\u3000"
_ALPHABET = _TEXT + _PUNCT + _UNI


def rand_text(rng, lo=0, hi=14):
    n = rng.randint(lo, hi)
    return "".join(rng.choice(_ALPHABET) for _ in range(n))


def gen_bare_fuzz(rng, validators_mod):
    """Yield (validator, guaranteed-rejecting value) pairs. Each family gets a
    marker that forces rejection by construction; a rare accept is skipped by
    the driver without counting."""
    v = validators_mod
    integer = v.validate_integer
    slug = v.validate_slug
    uslug = v.validate_unicode_slug
    commas = v.validate_comma_separated_integer_list
    nullv = v.ProhibitNullCharactersValidator()
    ipv4 = v.validate_ipv4_address
    ipv6 = v.validate_ipv6_address
    ip46 = v.validate_ipv46_address
    email = v.validate_email
    url = v.URLValidator()

    for _ in range(30000):
        yield integer, rand_text(rng) + "x" + rand_text(rng, 0, 4)
    for _ in range(12000):
        yield slug, rand_text(rng) + " " + rand_text(rng, 0, 4)
    for _ in range(6000):
        yield uslug, rand_text(rng) + "!" + rand_text(rng, 0, 4)
    for _ in range(10000):
        yield commas, rand_text(rng, 0, 6) + "q" + rand_text(rng, 0, 4)
    for _ in range(10000):
        s = rand_text(rng, 0, 6) + "\x00" + rand_text(rng, 0, 4)
        yield nullv, s
    for _ in range(6000):
        yield ipv4, rand_text(rng, 0, 8) + "z"
    for _ in range(3000):
        yield ipv6, rand_text(rng, 0, 8) + "z"
    for _ in range(3000):
        yield ip46, rand_text(rng, 0, 8) + "z"
    for _ in range(3000):
        # no '@' at all -> always rejected
        yield email, rand_text(rng, 0, 10).replace("@", "a")
    for _ in range(2000):
        # no scheme separator -> always rejected
        yield url, rand_text(rng, 1, 10).replace(":", "x").replace("/", "y")


def gen_finite_decimal(rng):
    sign = rng.choice(["", "-"])
    ip = "".join(rng.choice("0123456789") for _ in range(rng.randint(0, 8)))
    fp = "".join(rng.choice("0123456789") for _ in range(rng.randint(0, 8)))
    if not ip and not fp:
        ip = "7"
    s = sign + (ip or "0")
    if fp or rng.random() < 0.3:
        s += "." + fp
    if rng.random() < 0.2:
        s += "E" + rng.choice(["+", "-", ""]) + str(rng.randint(0, 6))
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    if not d.is_finite():
        return None
    return d


NOTFINITE_SHAPES = ["NaN", "-NaN", "sNaN", "-sNaN", "Infinity", "-Infinity",
                    "NaN123", "-NaN45", "sNaN7", "NaN000123456789"]


def main():
    configure_django()
    from django.core import validators
    from django import forms

    rng = random.Random(SEED)
    c_bare = Counter()
    c_limit = Counter()
    c_dec_bare = Counter()
    c_form = Counter()

    # 1) curated boundary bare rejections
    for validator, value in bare_boundary_cases(validators):
        err = check_bare(validator, value, c_bare)
        if err:
            print(err)
            return 1

    # 2) fuzzed bare rejections across seven validator families
    for validator, value in gen_bare_fuzz(rng, validators):
        err = check_bare(validator, value, c_bare)
        if err:
            print(err)
            return 1

    # 3) decimal magnitude rejections (all three codes) + boundary trio
    dv_boundary = validators.DecimalValidator(max_digits=2, decimal_places=1)
    for s in ("123", "0.12", "12"):
        err = check_decimal(dv_boundary, 2, 1, Decimal(s), c_limit, c_dec_bare)
        if err:
            print(err)
            return 1
    dvs = []
    for d_cfg in range(1, 5):
        for p_cfg in range(0, d_cfg + 1):
            dvs.append((validators.DecimalValidator(max_digits=d_cfg,
                                                    decimal_places=p_cfg),
                        d_cfg, p_cfg))
    for _ in range(30000):
        d = gen_finite_decimal(rng)
        if d is None:
            continue
        dv, d_cfg, p_cfg = dvs[rng.randrange(len(dvs))]
        err = check_decimal(dv, d_cfg, p_cfg, d, c_limit, c_dec_bare)
        if err:
            print(err)
            return 1

    # 4) not-representable decimal candidates, raw validator layer
    for _ in range(400):
        for s in NOTFINITE_SHAPES:
            d = Decimal(s)
            dv, d_cfg, p_cfg = dvs[rng.randrange(len(dvs))]
            err = check_decimal(dv, d_cfg, p_cfg, d, c_limit, c_dec_bare)
            if err:
                print(err)
                return 1

    # 5) not-representable candidates end-to-end through the form field:
    #    exercises the modelled routing (no field-layer parameter-less screen)
    field = forms.DecimalField(max_digits=2, decimal_places=1)
    for s in ["NaN", "-NaN", "Infinity", "-Infinity", "NaN123"]:
        err = check_decimal_form(field, s, c_form)
        if err:
            print(err)
            return 1

    total = c_bare.n + c_limit.n + c_dec_bare.n + c_form.n
    if total < 100000:
        print("INSUFFICIENT: only %d comparisons (bare=%d limit=%d "
              "decimal-bare=%d form=%d)" % (total, c_bare.n, c_limit.n,
                                            c_dec_bare.n, c_form.n))
        return 1
    print("G-CONF OK: shadow impl == real patched rejection params on %d "
          "rejection events (bare=%d, limit=%d, decimal-bare=%d, form=%d); "
          "0 disagreements. Seed %d."
          % (total, c_bare.n, c_limit.n, c_dec_bare.n, c_form.n, SEED))
    print(json.dumps({"checked": total, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
