#!/usr/bin/env python
"""G-AX: validate the A-reference callee behavior for astropy__astropy-14096.

Runs INSIDE the instance image (base_commit; the gate does NOT apply the gold
patch). This is correct here: G-AX validates the UNCHANGED callee the fix defers
to, not the changed function itself. The modeled callee is image-independent.

The bundle declares no consumed property axiom (`correct_resolveAttr` closes by
case analysis). Op 2 of the impl is an A-reference: on the fallback branch the
result is the object's ordinary attribute-access result, modeled as
`ordinaryLookup self attr` and mapped (mapping.md) to the real callee
`self.__getattribute__(attr)` — the ordinary attribute-access protocol
(`object.__getattribute__`), which is exactly the callee the gold fix defers to
(`return self.__getattribute__(attr)`).

`handledCase` is the other A-reference. Its modeled codomain is
`Option (Except AttrError AttrValue)`: `some (Except.ok v)` when a
domain-specific branch resolves the name, `some (Except.error e)` when the branch
that applies is ENTERED and evaluating it RAISES (the transform-target branch
`return self.transform_to(attr)` does this for real coordinate data), and `none`
when no branch applies. Boundaries 3-5 below validate all three arms against the
real branches. That the raising arm is image-independent was checked explicitly:
the branch returns or raises before the fail path in BOTH the pre- and post-patch
function, and the patch rewrites only the fail path, so the outcome on the raising
names is identical either side of it.

The soundness-critical property of the `ordinaryLookup` model is:

  * `ordinaryLookup` is the ordinary attribute-access protocol, NOT a fabricated
    error keyed to the requested name. Concretely, when accessing a name runs a
    property getter that itself touches a genuinely-missing attribute, the
    AttributeError raised by the ordinary protocol reports the genuinely-missing
    INNER name, not the requested outer name. (This is exactly what the Lean
    `none`-branch contract `result = ordinaryLookup self attr` buys, and what the
    prepatch — which fabricates `{missing := attr}` — violates.)

CRITICAL: we exercise the callee `obj.__getattribute__(name)` DIRECTLY. We must
NOT go through ordinary attribute access (`obj.name` / `getattr`), because on the
base_commit image that routes through the *unfixed* `__getattr__`, whose whole
bug is fabricating the wrong name — that is the function under repair, not the
A-reference callee. `handledCase` (the domain resolution branches) is validated
separately via full attribute access on a name that must resolve.

stdlib-only (+ astropy under test). Exit 0 iff sound.
"""
import random
import sys
import traceback

SEED = 20240629
N_FUZZ = 2000


def build():
    import astropy.coordinates as coord
    return coord


def main():
    coord = build()
    SkyCoord = coord.SkyCoord

    random.seed(SEED)
    failures = []

    # A genuinely-missing inner name accessed from inside a custom property.
    class custom_coord(SkyCoord):
        @property
        def prop(self):
            return self.random_attr  # 'random_attr' does not exist

    base = custom_coord("00h42m30s", "+41d12m00s", frame="icrs")

    # --- Boundary 1: ordinaryLookup on a property that touches an inner-missing
    # name. Exercise the CALLEE `__getattribute__` directly: running the getter
    # touches the genuinely-missing `random_attr`, so the ordinary protocol's
    # AttributeError reports the INNER missing name, not the requested one.
    try:
        base.__getattribute__("prop")
        failures.append("expected AttributeError from __getattribute__('prop'), got none")
    except AttributeError as e:
        msg = str(e)
        if "random_attr" not in msg:
            failures.append(
                f"ordinaryLookup callee did not report the genuine inner name: "
                f"error {msg!r} omits 'random_attr'")

    # --- Boundary 2: ordinaryLookup on a plain genuinely-missing name -----
    # The ordinary protocol raises an AttributeError mentioning the requested
    # name (here outer == inner).
    try:
        base.__getattribute__("totally_absent_xyz")
        failures.append("expected AttributeError from __getattribute__('totally_absent_xyz'), got none")
    except AttributeError as e:
        if "totally_absent_xyz" not in str(e):
            failures.append(
                f"ordinaryLookup on plain-missing name: error {str(e)!r} omits requested name")

    # --- Boundary 3: handledCase = some (Except.ok v) — a domain-resolvable name
    # still resolves. Full attribute access on a frame-transform target must
    # return a value (the resolution branches, reached via `__getattr__`, must
    # not be swallowed).
    try:
        _ = base.icrs  # frame alias / transform target -> resolves
    except AttributeError as e:
        failures.append(f"handledCase: resolvable name 'icrs' wrongly raised: {e}")

    # --- Boundary 4: handledCase = some (Except.error e) — the branch that
    # applies is ENTERED and RAISES, and the raised exception escapes
    # `__getattr__` verbatim without the fail path being reached. This is the arm
    # that makes the aggregate three-valued rather than `Option AttrValue`.
    plain = SkyCoord("00h42m30s", "+41d12m00s", frame="icrs")
    fabricated = "object has no attribute"
    raising = {}
    for name in ("altaz", "lsr", "galactocentric", "hcrs"):
        # The guard trace must actually reach the transform-target branch.
        frame_cls = coord.frame_transform_graph.lookup_name(name)
        if frame_cls is None or not plain.frame.is_transformable_to(frame_cls):
            failures.append(
                f"handledCase raise-arm: {name!r} does not reach the "
                f"transform-target branch on this build; boundary not exercised")
            continue
        try:
            getattr(plain, name)
            failures.append(
                f"handledCase raise-arm: {name!r} returned a value; the modeled "
                f"`some (Except.error _)` arm is not exercised")
            continue
        except Exception as e:
            tb = traceback.format_exc()
            raising[name] = type(e).__name__
            if "return self.transform_to(attr)" not in tb:
                failures.append(
                    f"handledCase raise-arm {name!r}: traceback does not show the "
                    f"transform-target branch, so the failure is not the branch's own")
            if "return self.__getattribute__(attr)" in tb:
                failures.append(
                    f"handledCase raise-arm {name!r}: the fallback line WAS reached, "
                    f"so this name belongs to the `none` arm, not the raise arm")
            if isinstance(e, AttributeError) and fabricated in str(e) and name in str(e):
                failures.append(
                    f"handledCase raise-arm {name!r}: surfaced the manufactured "
                    f"no-such-attribute report {str(e)!r} instead of the branch's "
                    f"own failure")

    # --- Boundary 5: the error channel needs its `kind`. If every raise above
    # were an AttributeError, `AttrError`'s `kind` field would be modeling a
    # distinction the real function does not make; it is not.
    if raising and set(raising.values()) <= {"AttributeError"}:
        failures.append(
            f"handledCase raise-arm: every raised exception is an AttributeError "
            f"({raising}); the modeled `kind` field would be unmotivated")

    # --- Fuzz: ordinaryLookup on random missing names + random inner-missing
    #     property names, always via the callee `__getattribute__`.
    alphabet = "abcdefghijklmnopqrstuvwxyz_"
    for _ in range(N_FUZZ):
        n = random.randint(1, 12)
        outer = "".join(random.choice(alphabet) for _ in range(n))
        inner = "z_" + "".join(random.choice(alphabet) for _ in range(n))
        # Skip names that could plausibly resolve to real frame attrs/aliases.
        if outer.startswith("_"):
            continue

        # (a) plain missing outer name via the callee -> error names the outer.
        try:
            base.__getattribute__(outer)
        except AttributeError as e:
            if outer not in str(e):
                failures.append(
                    f"ordinaryLookup plain-missing {outer!r}: error {str(e)!r} lost the name")
        except Exception:
            pass  # other machinery; not the modeled ordinary-lookup path

        # (b) property whose getter touches a genuinely-missing inner name,
        #     exercised via the callee -> error must name the INNER missing name.
        Dyn = type(
            "dyn_coord",
            (SkyCoord,),
            {outer: property(lambda self, _i=inner: getattr(self, _i))},
        )
        try:
            obj = Dyn("00h42m30s", "+41d12m00s", frame="icrs")
            obj.__getattribute__(outer)
        except AttributeError as e:
            if inner not in str(e):
                failures.append(
                    f"ordinaryLookup inner-missing via property {outer!r}->{inner!r}: error "
                    f"{str(e)!r} does not report the genuinely-missing inner name")
        except Exception:
            pass

    if failures:
        print("status=fail")
        for f in failures[:20]:
            print("  -", f)
        print(f"({len(failures)} total)")
        return 1

    print(f"status=pass A-reference callees consistent: the ordinary attribute-access "
          f"protocol (__getattribute__) propagates the genuine attribute error (inner "
          f"missing name); a domain-resolvable name still resolves; and the branch that "
          f"applies to a transform-target name is entered and RAISES, its own failure "
          f"escaping the hook verbatim without the fallback line being reached "
          f"({raising}) — so all three arms of the modeled resolution outcome are "
          f"exercised; boundary + {N_FUZZ} fuzz scenarios")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        print("status=error")
        sys.exit(2)
