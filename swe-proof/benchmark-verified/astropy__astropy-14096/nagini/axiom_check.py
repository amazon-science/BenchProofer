#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-14096.

Runs INSIDE the instance image (real `astropy`, resolved from /testbed) and
validates the consumed axioms of model.py — the abstractions of the four
candidate-resolution STEPS the fallback resolver invokes, one per partial leg.

Each step axiom (model.py axioms region) claims, for a requested name `name`,
that the step has TWO paths selected by its own `*_succeeds(name)` fact: where
the selector holds the step yields its value, and otherwise it FAILS and the
resolver surfaces that failure. None of the four steps ALWAYS succeeds and none
ALWAYS fails, so this check audits BOTH directions of each — an axiom claiming a
step never returns (or never fails) would be unsound, and would make the
consumer spec reject a faithful impl. The audited steps and the repo expressions
they abstract (mapping.md §3.1) are:

  * leg 2, `frame_attr_step` / `frame_attr_step_succeeds`:
        getattr(self.frame, attr) if attr in self.frame.frame_attributes
        else getattr(self, "_" + attr, None)
  * leg 3, `passthrough_step` / `passthrough_step_succeeds`:
        getattr(self._sky_coord_frame, attr)
  * leg 4, `transform_step` / `transform_step_succeeds`:
        self.transform_to(attr)
  * leg 5, `residual_step` / `residual_step_succeeds` /
    `residual_step_value` / `residual_step_subject`:
        self.__getattribute__(attr)

Leg 5 carries one further observable, and it is the discriminating one:

  (1) `residual_step_subject(name)` is a deterministic function of `name`:
      the symbol id the residual resolution blames when it fails for `name`.

  (2) `residual_step(name)`, where it fails, surfaces an `AttributeError` whose
      blamed subject is `residual_step_subject(name)` — in GENERAL NOT `name`
      itself; where it succeeds it returns `residual_step_value(name)`.

A step's failure is NOT always an `AttributeError` (the transform step also
raises `TypeError`, `ValueError`, `UnitsError`, `ConvertError`), and the model's
single `AttributeAccessError` carrier abstracts ANY failure of the step
(mapping.md §3.1); only on leg 5 is the blamed subject itself observable, so
only there does this check compare subjects.

The discriminating fact the proof relies on (the one the pre-patch violates) is
that `residual_step_subject(name) != name` whenever `name` is a computed
accessor (a property/descriptor) whose body reads a different, genuinely-absent
inner name: the surfaced `AttributeError` blames the inner name, not `name`.

This check constructs real `SkyCoord` subclasses with a property `p` whose body
reads a missing inner attribute `q`, over many distinct (p, q) name pairs
(boundary + fuzz), and asserts the real `obj.__getattribute__(p)`:
  * raises `AttributeError`,
  * whose message blames `q` (the inner missing name), and NOT `p`,
i.e. `residual_step_subject(p) == q != p`, exactly the axiom's Exsures.
It also confirms determinism, the degenerate "plain missing name blames itself"
case (`residual_step_subject(name) == name` there — still a function of
`name`, consistent with the axiom), and — the direction that keeps the axiom
honest — that for names the mechanism RESOLVES (plain class attributes, instance
dict entries, methods, dunders) `obj.__getattribute__(name)` returns normally
and deterministically, so the selector's positive branch is real and
`residual_step_value` is well defined.

For legs 2-4 the check evaluates each step's own repo expression directly and
asserts only what that leg's axiom claims: that the step either yields a value
or fails, that which one it does is stable for a given (object, name), and — the
direction an over-strong `Ensures` would get wrong — that BOTH outcomes are
actually reachable, so no leg may be modelled as total. Leg 4 in particular
fails for real targets (`altaz`, `hadec`, `teme`, `lsr`, `galactocentric`,
`hcrs`, ...), which is exactly why its axiom is partial.

The check is valid on the UNPATCHED repo because every axiomatised step
(`__getattribute__`, `transform_to`, the frame-attribute and passthrough
`getattr` expressions) is unchanged by the patch; only `__getattr__`'s fail
branch changes. Imports only `astropy.coordinates` (the package under test) and
the standard library. Exit 0 iff every observation meets the axiom.
"""
import random
import re
import string
import sys

import astropy.coordinates as coord
from astropy.coordinates import SkyCoord


def _blamed_name(exc):
    """Extract the attribute name an AttributeError blames, from its message
    ('... object has no attribute 'NAME'')."""
    m = re.search(r"has no attribute '([^']*)'", str(exc))
    return m.group(1) if m else None


def _make_coord():
    """A concrete SkyCoord (the regression object), constructed exactly as in
    the issue / F2P test."""
    return SkyCoord("00h42m30s", "+41d12m00s", frame="icrs")


def _subclass_with_property(prop_name, inner_name):
    """Build a SkyCoord subclass with a property `prop_name` whose body reads a
    (missing) inner attribute `inner_name`, then return an instance."""
    def getter(self):
        return getattr(self, inner_name)
    cls = type(
        "custom_coord_%s" % prop_name,
        (SkyCoord,),
        {prop_name: property(getter)},
    )
    return cls("00h42m30s", "+41d12m00s", frame="icrs")


def check_property_blames_inner(prop_name, inner_name):
    """Axiom (2): a property `prop_name` reading a missing inner `inner_name`
    surfaces an AttributeError blaming `inner_name`, not `prop_name`."""
    obj = _subclass_with_property(prop_name, inner_name)
    # The ordinary mechanism the fallback re-enters is __getattribute__.
    try:
        obj.__getattribute__(prop_name)
    except AttributeError as e:
        blamed = _blamed_name(e)
        assert blamed == inner_name, (
            "axiom unsound: __getattribute__(%r) (property reading %r) blamed "
            "%r, axiom requires the inner missing name %r"
            % (prop_name, inner_name, blamed, inner_name))
        assert blamed != prop_name, (
            "axiom unsound: surfaced error blamed the requested name %r "
            "(the pre-patch behaviour), not the underlying subject %r"
            % (prop_name, inner_name))
        # determinism: a second invocation blames the same subject
        try:
            obj.__getattribute__(prop_name)
        except AttributeError as e2:
            assert _blamed_name(e2) == blamed, (
                "axiom unsound: residual_step_subject not deterministic for %r"
                % prop_name)
            return
        raise AssertionError("expected AttributeError on second invocation")
    raise AssertionError(
        "axiom unsound: __getattribute__(%r) did not raise (property reads "
        "missing %r)" % (prop_name, inner_name))


def check_plain_missing_blames_itself(name):
    """Degenerate case: a plain missing name (no property) blames itself — still
    a deterministic function of `name`, consistent with the axiom."""
    obj = _make_coord()
    try:
        obj.__getattribute__(name)
    except AttributeError as e:
        blamed = _blamed_name(e)
        assert blamed == name, (
            "degenerate case: __getattribute__(%r) blamed %r, expected the "
            "name itself" % (name, blamed))
        return
    raise AssertionError(
        "degenerate case: __getattribute__(%r) did not raise" % name)


def check_resolving_name_returns(obj, name):
    """Axioms (2, resolving path) + `residual_step_value` / the positive branch
    of `residual_step_succeeds`: for a name the ordinary mechanism RESOLVES it
    returns normally (it does NOT raise) and does so deterministically, so the
    value is a function of `name` in this context. This is the direction an
    `Ensures(False)`-style axiom would get wrong."""
    try:
        first = obj.__getattribute__(name)
    except AttributeError as e:
        raise AssertionError(
            "axiom unsound: __getattribute__(%r) raised AttributeError (%s) but "
            "the ordinary mechanism resolves this name — the axiom's resolving "
            "path claims a normal return" % (name, e))
    # determinism of the resolved value (identity or equality, for values whose
    # __eq__ is array-valued or otherwise exotic)
    second = obj.__getattribute__(name)
    same = first is second
    if not same:
        try:
            same = bool(first == second)
        except Exception:
            same = repr(first) == repr(second)
    assert same, (
        "axiom unsound: residual_step_value not deterministic for %r (%r vs %r)"
        % (name, first, second))


def check_selector_is_exclusive(obj, name):
    """The selector `residual_step_succeeds(name)` is a genuine either/or: the
    mechanism resolves the name or fails for it, never both and never neither.
    Any other outcome (e.g. a non-AttributeError escape) would mean the axiom's
    two paths do not cover the callee's behaviour."""
    try:
        obj.__getattribute__(name)
        resolved = True
    except AttributeError:
        resolved = False
    except Exception as e:  # noqa: BLE001
        raise AssertionError(
            "axiom unsound: __getattribute__(%r) escaped with a "
            "non-AttributeError %s: %s — outside the axiom's two paths"
            % (name, type(e).__name__, e))
    # re-probe: the selector must be stable for the same (object, name)
    try:
        obj.__getattribute__(name)
        again = True
    except AttributeError:
        again = False
    assert resolved == again, (
        "axiom unsound: residual_step_succeeds(%r) not stable (%s then %s)"
        % (name, resolved, again))
    return resolved


def _frame_attr_expr(obj, attr):
    """Leg 2's repo expression verbatim (sky_coordinate.py:881-885)."""
    if attr in obj.frame.frame_attributes:
        return getattr(obj.frame, attr)
    return getattr(obj, "_" + attr, None)


def _passthrough_expr(obj, attr):
    """Leg 3's repo expression verbatim (sky_coordinate.py:889-890)."""
    return getattr(obj._sky_coord_frame, attr)


def _transform_expr(obj, attr):
    """Leg 4's repo expression verbatim (sky_coordinate.py:893-895)."""
    return obj.transform_to(attr)


def check_step_outcome(step, obj, attr, expect_succeeds, label):
    """A step axiom's two paths: the step either yields a value or FAILS, which
    one is stable for a given (object, name), and the observed outcome is the one
    the axiom's `*_succeeds` selector is claimed to record.

    A step's failure is not restricted to `AttributeError` (leg 4 raises
    `TypeError` / `UnitsError` / `ConvertError` too) — the model's carrier
    abstracts ANY failure — so this catches `Exception`. Asserting the expected
    direction is what keeps the axiom from being over-strong: if a step this
    check expects to FAIL were to succeed, a partial axiom would be too weak,
    and if a step expected to succeed were to fail, a TOTAL axiom would be
    unsound (that is the defect this leg structure exists to avoid)."""
    def once():
        try:
            step(obj, attr)
            return True, None
        except Exception as e:  # noqa: BLE001
            return False, e

    ok, exc = once()
    assert ok == expect_succeeds, (
        "axiom unsound: %s step for %r %s, expected it to %s%s"
        % (label, attr, "succeeded" if ok else "failed",
           "succeed" if expect_succeeds else "fail",
           "" if ok else " (%s: %s)" % (type(exc).__name__, str(exc)[:80])))
    again, _ = once()
    assert ok == again, (
        "axiom unsound: %s_step_succeeds(%r) not stable (%s then %s)"
        % (label, attr, ok, again))
    return ok


def _rand_name(rng):
    n = rng.randint(3, 12)
    first = rng.choice(string.ascii_letters + "_")
    rest = "".join(rng.choice(string.ascii_letters + string.digits + "_")
                   for _ in range(n - 1))
    return first + rest


def main():
    # --- boundary: the exact regression scenario (gh-8340 / F2P test) --------
    check_property_blames_inner("prop", "random_attr")

    # --- boundary: a spread of distinct (property, inner) name pairs ---------
    boundary_pairs = [
        ("prop", "random_attr"),
        ("p", "q"),
        ("foo", "bar"),
        ("custom", "_hidden_missing"),
        ("value", "nonexistent"),
        ("_priv", "alsoMissing"),
        ("longPropertyName", "shortq"),
        ("a1", "b2"),
    ]
    for p, q in boundary_pairs:
        if p != q:
            check_property_blames_inner(p, q)

    # --- degenerate: plain missing names blame themselves --------------------
    for name in ["random_attr", "totally_absent", "no_such_thing",
                 "zzz", "missing123"]:
        check_plain_missing_blames_itself(name)

    # --- the RESOLVING path: the mechanism returns normally for names it -----
    # resolves. These are names for which the fallback resolver's four domain
    # resolutions do NOT apply, yet ordinary lookup succeeds (class attributes,
    # instance-dict entries, bound methods, dunders) — precisely the inputs an
    # axiom asserting "the mechanism never returns" would mis-model.
    class _WithClassAttr(SkyCoord):
        CLASS_CONST = 12345

    resolving_obj = _WithClassAttr("00h42m30s", "+41d12m00s", frame="icrs")
    resolving_names = [
        "CLASS_CONST",        # a plain class attribute
        "_sky_coord_frame",   # an instance-dict entry
        "_is_name",           # a bound method
        "__class__",          # dunders resolved by the ordinary machinery
        "__dict__",
        "__doc__",
        "__module__",
        "__reduce__",
    ]
    for name in resolving_names:
        check_resolving_name_returns(resolving_obj, name)
        assert check_selector_is_exclusive(resolving_obj, name) is True, (
            "selector disagrees: %r resolves but the exclusivity probe says "
            "otherwise" % name)

    # the selector's negative branch on the same object, for contrast
    n_selector = len(resolving_names)
    for name in ["random_attr", "totally_absent", "_priv_absent",
                 "__deepcopy__", "__getstate__"]:
        assert check_selector_is_exclusive(resolving_obj, name) is False, (
            "selector disagrees: %r does not resolve but the exclusivity probe "
            "says otherwise" % name)
        n_selector += 1

    # --- randomized fuzz: many distinct property/inner pairs -----------------
    rng = random.Random(14096)
    checked = 0
    safe = 0
    # keep the count modest: each pair builds a real SkyCoord (non-trivial cost)
    while checked < 300:
        p = _rand_name(rng)
        q = _rand_name(rng)
        # property/inner must differ AND neither may shadow a real SkyCoord
        # attribute (we need both lookups to genuinely fail).
        if p == q:
            continue
        try:
            base = _make_coord()
            if hasattr(base, p) or hasattr(base, q):
                safe += 1
                if safe > 5000:
                    break
                continue
        except Exception:
            continue
        check_property_blames_inner(p, q)
        checked += 1

    # --- legs 2-4: each step axiom is PARTIAL, and both directions are real --
    # This is the audit that keeps the leg structure honest. For every step the
    # check exercises names on which the real repo expression SUCCEEDS and names
    # on which it FAILS. A step with no reachable failure could be modelled
    # total; a step with no reachable success would make a partial axiom
    # vacuous. Leg 4's failing names are exactly the class the faithfulness
    # witness came from.
    step_obj = _make_coord()

    class _RaisingFrameAttr(SkyCoord):
        # a descriptor named `_<frame_attr>` whose read raises, so leg 2's
        # `getattr(self, "_" + attr, None)` fallback branch itself fails
        @property
        def _equinox(self):
            raise TypeError("descriptor raises")

    raising_obj = _RaisingFrameAttr("00h42m30s", "+41d12m00s", frame="icrs")

    n_step = 0
    # leg 2 — frame attribute
    for attr in ["equinox", "obstime", "location", "pressure", "obswl"]:
        check_step_outcome(_frame_attr_expr, step_obj, attr, True, "frame_attr")
        n_step += 1
    check_step_outcome(_frame_attr_expr, raising_obj, "equinox", False,
                       "frame_attr")
    n_step += 1
    # leg 3 — frame passthrough
    for attr in ["ra", "dec", "distance", "frame_attributes"]:
        check_step_outcome(_passthrough_expr, step_obj, attr, True, "passthrough")
        n_step += 1
    check_step_outcome(_passthrough_expr, step_obj, "definitely_absent", False,
                       "passthrough")
    n_step += 1
    # leg 4 — transform target: BOTH directions, and the failing side is the
    # class the spec must not model as total.
    transform_ok = ["fk5", "fk4", "galactic", "gcrs", "icrs", "cirs", "itrs",
                    "supergalactic", "precessedgeocentric",
                    "geocentricmeanecliptic"]
    transform_fail = ["altaz", "hadec", "teme", "lsr", "lsrd", "lsrk",
                      "galacticlsr", "galactocentric", "hcrs",
                      "heliocentricmeanecliptic", "heliocentrictrueecliptic"]
    for attr in transform_ok:
        check_step_outcome(_transform_expr, step_obj, attr, True, "transform")
        n_step += 1
    for attr in transform_fail:
        check_step_outcome(_transform_expr, step_obj, attr, False, "transform")
        n_step += 1

    print("G-AX OK: residual_step / residual_step_subject / "
          "residual_step_value / residual_step_succeeds axioms sound — real "
          "SkyCoord.__getattribute__ blames the inner missing name (not the "
          "requested name) on %d boundary + %d fuzz property pairs; degenerate "
          "plain-missing case blames itself; the RESOLVING path returns normally "
          "and deterministically on %d names; the resolve/fail selector is "
          "exclusive and stable on %d names; all deterministic. The leg 2/3/4 "
          "step axioms (frame_attr_step / passthrough_step / transform_step) "
          "are PARTIAL and both directions are reachable on %d real "
          "(object, name) probes — %d transform targets succeed and %d FAIL "
          "(altaz/hadec/teme/lsr/galactocentric/hcrs/...), so no leg may be "
          "modelled as total; each step's outcome is stable."
          % (len(boundary_pairs) + 1, checked, len(resolving_names), n_selector,
             n_step, len(transform_ok), len(transform_fail)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
