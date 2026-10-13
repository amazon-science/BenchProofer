#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-14096 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. There are no @Pure helpers with executable bodies; the four
@ContractOnly step callees are realized by performing the REAL repo expression
that defines each candidate resolution (mapping.md section 1 / 3.1). The
user-defined `AttributeAccessError(subject)` stand-in carries the symbol id of
the name a surfaced failure blames.

ORACLE: the REAL patched repo function per mapping.md section 1 —
`SkyCoord.__getattr__` (astropy/coordinates/sky_coordinate.py), invoked
DIRECTLY. Calling it directly is what lets the check cover both paths of the
residual leg: the interpreter only reaches `__getattr__` after ordinary lookup
failed, but the function is also callable outright, and the residual leg then
resolves a name that may SUCCEED — in which case the real function RETURNS that
value rather than raising. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed resolves the patched module.

Type bridge (mapping.md section 2):
  * attribute name (str) <-> symbol id (int): a process-local interning table;
    the observable on the residual leg's failing path is WHICH name the surfaced
    error blames (an identity comparison), modelled by int equality.
  * the four guards <-> bool flags, computed for each (object, name) input from
    the SAME repo state the guards read, in the model's priority order. For a
    few velocity/differential names the repo's passthrough guard itself raises
    (`hasattr` only swallows AttributeError), so no boolean exists to pass and
    the input has NO corresponding model input; those are counted and reported
    as outside-the-bridge, never silently dropped.
  * each *_value parameter <-> an opaque int token; when the shadow returns token
    k the real function must have returned normally with the value the k-th
    resolution yields (checked against that resolution's defining repo
    expression).

EVERY LEG BUT THE ALIAS IS PARTIAL, and that is what this check covers in both
directions. Producing a frame attribute, a frame passthrough, a transform target
or the residual resolution can each itself FAIL, and the real function then
surfaces that failure — with whatever exception the underlying expression raised
(measured: TypeError / ValueError / UnitsError / ConvertError out of the
transform step, not only AttributeError). So the oracle catches every failure,
and a disagreement in EITHER direction (shadow raises / real returns, or shadow
returns / real raises) is reported. The blamed-SUBJECT observable is compared on
the residual leg, which is the leg whose failure subject the spec pins.

Input domain: any (object, name) pair. Boundary inputs cover all five legs and,
for each partial one, BOTH of its outcomes: transform targets whose transform
succeeds AND ones whose transform raises (AltAz/HADec lack an observer location,
TEME a scale, the Galactocentric/LSR/heliocentric families need full 3D data); a
subclass descriptor that makes the frame-attribute leg fail; the
computed-accessor scenario where the blamed name differs from the requested name;
plain missing names; names for which no guard selects yet the residual
resolution SUCCEEDS (plain class attributes, instance-dict entries, bound
methods, dunders); and half-built objects lacking `_sky_coord_frame` so every
guard is False by construction. Every REGISTERED FRAME NAME is swept on several
objects, so the transform leg's two outcomes are covered by construction rather
than by a hand-picked list. Fuzz covers randomized property/inner name pairs, a
large randomized missing-name sweep, and randomized resolving class attributes.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz inputs.
Pinned fuzz seed: 14096.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + numpy only.
"""
import json
import random
import re
import string
import sys

import numpy as np

SEED = 14096
N_FUZZ_PLAIN = 95_000
N_FUZZ_PROP = 3_000
N_FUZZ_RESOLVING = 2_000

# --- symbol interning: str name <-> int id ------------------------------------

_INTERN = {}


def intern_id(name_str):
    if name_str not in _INTERN:
        _INTERN[name_str] = len(_INTERN) + 1
    return _INTERN[name_str]


# --- user-defined failure stand-in from model.py, contracts stripped ----------

class AttributeAccessError(Exception):
    def __init__(self, subject):
        self.subject = subject


# --- @ContractOnly callee bridged to the REAL repo mechanism ------------------
# `ordinary_lookup(name)` models re-entering the ordinary attribute-lookup
# mechanism (`obj.__getattribute__(attr)`) for the current object; on the
# modelled (failing) path it surfaces an AttributeError whose blamed subject is
# `standard_lookup_subject(name)`. The bridge calls the REAL mechanism and
# translates its failure into the model's carrier exception.

_CURRENT_OBJ = None  # the coordinate object of the input under test

_BLAME_RE = re.compile(r"has no attribute '([^']*)'")


def _blamed_name(exc):
    m = _BLAME_RE.search(str(exc))
    return m.group(1) if m else None


_ID2NAME = {}

# Subject id for a step failure that blames no name (the repo expression raised
# something other than AttributeError, so there is no 'has no attribute X' name).
_STEP_FAILED = -99

# Sentinel: the input has no corresponding model input (a guard has no truth value).
GUARD_UNDEFINED = object()


def residual_step(name):
    """Both paths of the real residual resolution, per the axiom: it SUCCEEDS for
    `name` and yields the value (`residual_step_value`), or it FAILS and surfaces
    the blamed subject (`residual_step_subject`). Which path it takes is that
    step's own fact (`residual_step_succeeds`), read off here by performing it —
    the bridge does not decide it."""
    attr = _ID2NAME[name]
    try:
        value = _CURRENT_OBJ.__getattribute__(attr)  # REAL step
    except AttributeError as e:
        blamed = _blamed_name(e)
        raise AttributeAccessError(intern_id(blamed))
    return value


# The three PARTIAL domain steps. Each is bridged to the repo expression that
# defines the branch's value (mapping.md section 1), and each is partial: the
# defining expression can itself raise, in which case the step FAILS and the
# resolver surfaces that failure. The step's `*_succeeds` selector is read off by
# performing it, never decided by the bridge. A non-AttributeError failure is a
# real outcome of the repo expression too, so it is translated into the model's
# carrier exception as well — the model's carrier abstracts "this step failed",
# not "it failed with AttributeError".

def _perform(thunk):
    """Perform a partial step: return its value, or raise the model's carrier
    exception if the underlying repo expression failed for any reason."""
    try:
        return thunk()
    except AttributeError as e:
        raise AttributeAccessError(intern_id(_blamed_name(e)))
    except Exception:  # noqa: BLE001 — any failure of the step is a failure
        raise AttributeAccessError(_STEP_FAILED)


def frame_attr_step(name, value):
    attr = _ID2NAME[name]
    return _step_value(_CURRENT_OBJ, attr, TOK_FRAME_ATTR, value)


def passthrough_step(name, value):
    attr = _ID2NAME[name]
    return _step_value(_CURRENT_OBJ, attr, TOK_PASSTHROUGH, value)


def transform_step(name, value):
    attr = _ID2NAME[name]
    return _step_value(_CURRENT_OBJ, attr, TOK_TRANSFORM, value)


def _step_value(obj, attr, token, value):
    """Perform the token's step against the REAL repo expression; on success the
    model returns the branch's opaque token `value`, on failure it surfaces the
    model's carrier exception."""
    _perform(lambda: candidate_value(obj, attr, token))
    return value


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def resolve_missing(name,
                    is_alias, alias_value,
                    is_frame_attr, frame_attr_value,
                    is_frame_passthrough, passthrough_value,
                    is_transform, transform_value):
    if is_alias:
        return alias_value
    if is_frame_attr:
        return frame_attr_step(name, frame_attr_value)
    if is_frame_passthrough:
        return passthrough_step(name, passthrough_value)
    if is_transform:
        return transform_step(name, transform_value)
    return residual_step(name)


# --- bridge: flags + branch-value candidates from real object state -----------
# Tokens for the opaque *_value parameters (disjoint from interned name ids by
# construction: negative).
TOK_ALIAS, TOK_FRAME_ATTR, TOK_PASSTHROUGH, TOK_TRANSFORM = -1, -2, -3, -4


def compute_flags(obj, attr, graph):
    """The four domain-resolution guards, read from the same repo state the
    fallback resolver consults (mapping.md section 1), in priority order. The
    resolver wraps all four in an outer `"_sky_coord_frame" in self.__dict__`
    test, so on an object without that entry every guard is False by
    construction and the no-resolution leg is taken unconditionally."""
    if "_sky_coord_frame" not in obj.__dict__:
        return False, False, False, False
    is_alias = obj._is_name(attr)
    is_frame_attr = attr in graph.frame_attributes
    is_frame_passthrough = (not attr.startswith("_")
                            and hasattr(obj._sky_coord_frame, attr))
    frame_cls = graph.lookup_name(attr)
    is_transform = (frame_cls is not None
                    and obj.frame.is_transformable_to(frame_cls))
    return is_alias, is_frame_attr, is_frame_passthrough, is_transform


def candidate_value(obj, attr, token):
    """The value the token's domain resolution yields, per its defining repo
    expression (mapping.md section 1)."""
    if token == TOK_ALIAS:
        return obj
    if token == TOK_FRAME_ATTR:
        if attr in obj.frame.frame_attributes:
            return getattr(obj.frame, attr)
        return getattr(obj, "_" + attr, None)
    if token == TOK_PASSTHROUGH:
        return getattr(obj._sky_coord_frame, attr)
    if token == TOK_TRANSFORM:
        return obj.transform_to(attr)
    raise AssertionError("unknown token %r" % (token,))


def eq_obs(a, b):
    """Observable equality for branch values (opaque tokens in the model): ==
    lifted over array-valued results, with identity / repr fallbacks."""
    if a is b:
        return True
    try:
        r = (a == b)
        return bool(np.all(r))
    except Exception:
        return type(a) is type(b) and repr(a) == repr(b)


def ordinary_lookup_resolves(obj, attr):
    """The mechanism's path selector, read from the REAL mechanism: True iff
    ordinary lookup RESOLVES `attr` on `obj` rather than failing for it."""
    try:
        obj.__getattribute__(attr)
        return True
    except AttributeError:
        return False


def check_one(obj, attr, graph):
    """Diff shadow vs the real patched fallback on one (object, name) input.
    Returns an error string on disagreement, None on agreement, and the sentinel
    GUARD_UNDEFINED when the input has no corresponding model input at all (see
    below).  Counted and reported, never silently dropped."""
    global _CURRENT_OBJ
    name_id = intern_id(attr)
    _ID2NAME[name_id] = attr

    # The model takes the four guards as BOOLEAN INPUTS, so an input only
    # corresponds to a model input when each guard actually has a truth value for
    # it.  For a handful of velocity/differential names the repo's passthrough
    # guard `hasattr(self._sky_coord_frame, attr)` itself raises (hasattr only
    # swallows AttributeError), so no boolean exists to pass; such an input lies
    # outside the type bridge (mapping.md section 2) rather than being a
    # disagreement.  They are counted and printed so the coverage claim stays
    # honest.
    try:
        is_alias, is_fa, is_pt, is_tr = compute_flags(obj, attr, graph)
    except Exception as e:  # noqa: BLE001
        return (GUARD_UNDEFINED, attr, type(e).__name__)

    _CURRENT_OBJ = obj
    shadow_ret = shadow_exc = None
    try:
        shadow_ret = resolve_missing(name_id,
                                     is_alias, TOK_ALIAS,
                                     is_fa, TOK_FRAME_ATTR,
                                     is_pt, TOK_PASSTHROUGH,
                                     is_tr, TOK_TRANSFORM)
    except AttributeAccessError as e:
        shadow_exc = e

    # The real function's failing outcomes are NOT limited to AttributeError: a
    # partial domain step can surface whatever its own repo expression raises
    # (measured: TypeError / ValueError / UnitsError / ConvertError out of the
    # transform step).  The model abstracts all of them as "this leg failed",
    # so every failure is caught here and compared as a failure.
    real_ret = real_exc = None
    got_real = False
    try:
        real_ret = type(obj).__getattr__(obj, attr)  # REAL patched function
        got_real = True
    except Exception as e:  # noqa: BLE001
        real_exc = e

    ctx = "attr=%r obj=%s flags=(alias=%s,frame_attr=%s,passthrough=%s,transform=%s)" % (
        attr, type(obj).__name__, is_alias, is_fa, is_pt, is_tr)

    if shadow_exc is not None:
        if got_real:
            return ("DISAGREEMENT %s\n  shadow raised (subject=%r) but real "
                    "returned %r" % (ctx, _name_of(shadow_exc.subject), real_ret))
        # Both failed.  The blamed-subject observable is pinned by the model only
        # on the RESIDUAL leg (that is the leg whose failure the spec constrains
        # by subject); on a partial DOMAIN leg the model records only that the
        # step failed, so agreement is "both failed".
        if not (is_alias or is_fa or is_pt or is_tr):
            real_blamed = _blamed_name(real_exc)
            shadow_blamed = _name_of(shadow_exc.subject)
            if real_blamed != shadow_blamed:
                return ("DISAGREEMENT %s\n  shadow failure blames %r\n  real "
                        "failure blames %r" % (ctx, shadow_blamed, real_blamed))
        return None

    # shadow returned normally
    if not got_real:
        return ("DISAGREEMENT %s\n  shadow returned %r but real raised "
                "%r" % (ctx, shadow_ret, real_exc))
    if not (is_alias or is_fa or is_pt or is_tr):
        # No domain guard selected, so the shadow's value came from the residual
        # step.  The real function must pass the same value through.
        if not eq_obs(real_ret, shadow_ret):
            return ("DISAGREEMENT %s\n  shadow took the residual leg and returned "
                    "%r\n  real returned %r" % (ctx, shadow_ret, real_ret))
        return None
    # A domain guard selected: the shadow returned that branch's opaque token.
    cand = candidate_value(obj, attr, shadow_ret)
    if not eq_obs(real_ret, cand):
        return ("DISAGREEMENT %s\n  shadow took branch token %r whose value "
                "is %r\n  real returned %r" % (ctx, shadow_ret, cand, real_ret))
    return None


def _name_of(sym_id):
    for k, v in _INTERN.items():
        if v == sym_id:
            return k
    return None


# --- input generation ----------------------------------------------------------

def _rand_name(rng):
    n = rng.randint(3, 12)
    first = rng.choice(string.ascii_letters + "_")
    rest = "".join(rng.choice(string.ascii_letters + string.digits + "_")
                   for _ in range(n - 1))
    return first + rest


def main():
    from astropy.coordinates import SkyCoord
    from astropy.coordinates import frame_transform_graph as graph

    base = SkyCoord("00h42m30s", "+41d12m00s", frame="icrs")
    fk4 = SkyCoord("00h42m30s", "+41d12m00s", frame="fk4",
                   equinox="B1950", obstime="J1975")
    galactic = base.galactic

    class WithClassAttr(SkyCoord):
        CLASS_CONST = 12345
        OTHER_CONST = "sentinel"

    resolving_obj = WithClassAttr("00h42m30s", "+41d12m00s", frame="icrs")
    # a half-built object: no `_sky_coord_frame`, so the resolver's outer guard is
    # False and every input takes the no-resolution leg by construction.
    half_built = WithClassAttr.__new__(WithClassAttr)

    def subclass_with_property(prop_name, inner_name):
        def getter(self):
            return getattr(self, inner_name)
        cls = type("custom_coord_%s" % prop_name, (SkyCoord,),
                   {prop_name: property(getter)})
        return cls("00h42m30s", "+41d12m00s", frame="icrs")

    checked = 0
    n_boundary = 0
    n_outside_bridge = 0
    outside_bridge_seen = []

    def run(obj, attr):
        nonlocal checked, n_outside_bridge
        err = check_one(obj, attr, graph)
        if isinstance(err, tuple) and err and err[0] is GUARD_UNDEFINED:
            # No model input corresponds to this repo input (a guard has no truth
            # value).  Counted and reported, not silently skipped.
            n_outside_bridge += 1
            outside_bridge_seen.append((err[1], err[2]))
            return
        if err:
            print(err)
            sys.exit(1)
        checked += 1

    # --- boundary: all four resolving branches --------------------------------
    boundary = [
        (base, "icrs"),          # frame-name alias -> returns the object
        (fk4, "fk4"),
        (base, "equinox"),       # frame attribute (absent on frame -> shadow slot)
        (base, "obstime"),
        (fk4, "equinox"),        # frame attribute present on the frame
        (fk4, "obstime"),
        (base, "ra"),            # frame passthrough
        (base, "dec"),
        (base, "cartesian"),
        (base, "spherical"),
        (galactic, "l"),
        (galactic, "b"),
        (base, "fk5"),           # transform targets whose transform SUCCEEDS
        (base, "fk4"),
        (base, "galactic"),
        (base, "gcrs"),
        (fk4, "icrs"),
        (galactic, "icrs"),
        (base, "cirs"),
        (base, "itrs"),
        (base, "supergalactic"),
        (base, "precessedgeocentric"),
        (base, "geocentricmeanecliptic"),
        # transform targets whose guard SELECTS the transform leg but whose
        # transform then FAILS — the leg is PARTIAL and the resolver surfaces that
        # failure.  AltAz/HADec need an observer `location` and TEME a `scale`,
        # which a bare coordinate lacks; the Galactocentric/LSR/heliocentric
        # families need full 3D position (and velocity) data.  These are the
        # inputs a spec pinning the transform leg as TOTAL gets wrong.
        (base, "altaz"),
        (base, "hadec"),
        (base, "teme"),
        (base, "lsr"),
        (base, "lsrd"),
        (base, "lsrk"),
        (base, "galacticlsr"),
        (base, "galactocentric"),
        (base, "hcrs"),
        (base, "heliocentricmeanecliptic"),
        (base, "heliocentrictrueecliptic"),
        (base, "heliocentriceclipticiau76"),
        (fk4, "altaz"),
        (fk4, "hadec"),
        (fk4, "galactocentric"),
        (galactic, "altaz"),
        (galactic, "teme"),
    ]
    # --- boundary: failing path — computed accessor blames a different name ---
    prop_pairs = [
        ("prop", "random_attr"),
        ("p", "q"),
        ("foo", "bar"),
        ("value", "nonexistent"),
        ("longPropertyName", "shortq"),
    ]
    # --- boundary: failing path — plain missing names blame themselves --------
    # names whose passthrough GUARD itself raises on a coordinate without
    # velocity data: `hasattr` only swallows AttributeError, so the guard has no
    # truth value and the input has no corresponding model input.  Probed
    # explicitly so the outside-the-bridge count is exercised, not assumed empty.
    guard_undefined_names = ["radial_velocity", "pm_dec", "pm_ra_cosdec",
                             "proper_motion", "sphericalcoslat", "velocity"]
    plain_missing = ["random_attr", "totally_absent", "no_such_thing",
                     "zzz", "missing123", "_equinox_like_private",
                     "_hidden", "nonframe"]

    # --- boundary: NO domain resolution applies but ordinary lookup RESOLVES --
    # the no-resolution leg's returning path: the real function passes the
    # mechanism's value straight through instead of raising.
    resolving_leg = [
        (resolving_obj, "CLASS_CONST"),      # plain class attribute
        (resolving_obj, "OTHER_CONST"),
        (resolving_obj, "_sky_coord_frame"),  # instance-dict entry
        (resolving_obj, "_is_name"),          # bound method
        (resolving_obj, "__class__"),         # dunders
        (resolving_obj, "__dict__"),
        (resolving_obj, "__doc__"),
        (resolving_obj, "__module__"),
        (resolving_obj, "__reduce__"),
        (base, "_sky_coord_frame"),
        (fk4, "__class__"),
        (galactic, "_is_name"),
        # half-built objects: outer guard False, both mechanism paths
        (half_built, "CLASS_CONST"),          # resolves
        (half_built, "OTHER_CONST"),
        (half_built, "__class__"),
        (half_built, "__dict__"),
        (half_built, "totally_absent_xyz"),   # fails
        (half_built, "_priv_absent"),
        (half_built, "ra"),                   # would resolve if frame present
        (half_built, "icrs"),                 # would be an alias if frame present
        (half_built, "equinox"),
        (half_built, "galactic"),
    ]

    for obj, attr in boundary:
        run(obj, attr)
        n_boundary += 1
    for obj, attr in resolving_leg:
        run(obj, attr)
        n_boundary += 1
    for p, q in prop_pairs:
        run(subclass_with_property(p, q), p)
        n_boundary += 1
    for nm in plain_missing:
        run(base, nm)
        run(fk4, nm)
        n_boundary += 2
    for nm in guard_undefined_names:
        run(base, nm)
        run(fk4, nm)

    # --- fuzz: randomized property/inner pairs (failing path, subject != name)
    rng = random.Random(SEED)
    done = 0
    while done < N_FUZZ_PROP:
        p, q = _rand_name(rng), _rand_name(rng)
        if p == q or hasattr(base, p) or hasattr(base, q):
            continue
        run(subclass_with_property(p, q), p)
        done += 1

    # --- fuzz: randomized missing names on several objects --------------------
    objs = [base, fk4, galactic, resolving_obj, half_built]
    done = 0
    while done < N_FUZZ_PLAIN:
        nm = _rand_name(rng)
        obj = objs[done % len(objs)]
        run(obj, nm)
        done += 1

    # --- fuzz: randomized names that ordinary lookup RESOLVES ----------------
    # A subclass carrying a randomly-named class attribute: no domain resolution
    # applies, yet the mechanism resolves the name, so the real function must
    # RETURN the value. This is the input class an "always fails" model of the
    # mechanism gets wrong; it is swept explicitly.
    done = 0
    while done < N_FUZZ_RESOLVING:
        nm = _rand_name(rng)
        if hasattr(base, nm):
            continue
        cls = type("resolving_%d" % done, (SkyCoord,), {nm: 4242 + done})
        o = cls("00h42m30s", "+41d12m00s", frame="icrs")
        _, _, pt, tr = compute_flags(o, nm, graph)
        if pt or tr:
            continue
        run(o, nm)
        # and on a half-built instance of the same class (outer guard False)
        run(cls.__new__(cls), nm)
        done += 1

    # --- boundary: PARTIAL frame-attribute leg.  The branch's value expression
    # `getattr(self, "_" + attr, None)` runs a subclass descriptor, which can
    # itself fail; then the frame-attribute leg FAILS and the resolver surfaces
    # that failure rather than a value.
    for i, fa_name in enumerate(sorted(graph.frame_attributes)):
        if fa_name in base.frame.frame_attributes:
            continue
        raising = type("raising_fa_%d" % i, (SkyCoord,), {
            "_" + fa_name: property(
                lambda self: (_ for _ in ()).throw(TypeError("step failed")))})
        run(raising("00h42m30s", "+41d12m00s", frame="icrs"), fa_name)
        n_boundary += 1

    # --- sweep EVERY registered frame name on several objects.  This is the class
    # the transform leg lives in, and its two outcomes (transform succeeds /
    # transform raises) are both present in it; sweeping the whole registry rather
    # than a hand-picked list is what keeps the transform leg's partiality covered.
    for obj in (base, fk4, galactic):
        for nm in sorted(graph.get_names()):
            run(obj, nm)
            n_boundary += 1

    print("G-CONF OK: shadow impl == real fallback resolver on %d inputs "
          "(%d boundary + %d fuzz, seed %d), covering BOTH paths of EVERY "
          "partial leg (each leg's failure surfaced, and each leg's value "
          "passed through). %d input(s) lay outside the type bridge (a guard "
          "has no truth value, so no model input corresponds): %s"
          % (checked, n_boundary,
             N_FUZZ_PROP + N_FUZZ_PLAIN + 2 * N_FUZZ_RESOLVING, SEED,
             n_outside_bridge, sorted(set(outside_bridge_seen)) or "none"))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "outside_bridge": n_outside_bridge,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
