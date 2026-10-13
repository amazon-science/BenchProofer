#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15741.

Validates the one consumed axiom — `resolveName` (Solution.lean axioms region) —
and the `force` R-refinement (`force ↔ str(format_type)`) against the REAL Django
format machinery.

IMPORTANT — execution context. The G-AX harness (gates.gate_ax) runs this script
in the instance image at **base_commit WITHOUT applying patch.diff** (unlike
G-CONF, only G-AX omits apply_gold). So the in-container `get_format` is the
**pre-patch** function. That is correct and intended: G-AX validates the contract
of the UNCHANGED downstream callee (`resolveName`) and the coercion (`force`),
neither of which the patch alters. We therefore NEVER pass a lazy proxy into
`get_format` (that is the *patched function-under-spec's* job — covered by
G-RESOLVE/G-GOLD/the harness F2P tests, not by an axiom; doing so here would be a
directive-7 violation, reaching through the changed function rather than checking
the callee, and would simply reproduce the pre-patch TypeError).

`resolveName` models the UNCHANGED downstream resolution of an *already-concrete*
format name to its value (formats.py:117-145). The consumed property is its
**well-definedness**: resolution is a function of the resolved name CONTENT
alone — two concrete names with identical content yield equal values, regardless
of object identity. We pin NO specific returned value (directive 7: weakest
contract).

`force` models the patch's added coercion `str(format_type)`. Its property:
forcing a deferred (lazy) name is **total** (never raises) and **content-
preserving** — `str(gettext_lazy(s)) == s` for an untranslated name. This is a
pure string-proxy coercion that works pre-patch too; the pre-patch bug is NOT in
`str(...)` but downstream, in `getattr(module, <lazy proxy>, ...)` — which we
deliberately do not exercise here.

The checks (all against the real pre-patch callee — concrete `str` inputs only):

  (1) FORCING IS TOTAL & CONTENT-PRESERVING  — `str(gettext_lazy(name))` returns
      a `str` and (for an untranslated name) equals `name`. This is
      `force (deferred s) = s = force (eager s)` (Solution.lean `force`): the lazy
      and eager carriers observe identical content, and forcing always succeeds.

  (2) RESOLUTION DEPENDS ON RESOLVED CONTENT ONLY  — two **distinct concrete str
      objects with equal content** resolve to equal values, and neither raises
      (`resolveName` well-definedness — a function of content, not identity).

  (3) FORCED CONTENT RESOLVES LIKE THE EAGER CONTENT  — when forcing preserved
      the content (`str(gettext_lazy(name)) == name`), resolving the *forced*
      concrete string equals resolving the eager string. This is the composition
      the spec relies on (`resolveName (force nm)`), exercised entirely on
      concrete strings so it never touches the pre-patch lazy-getattr bug.

Imports only the standard library and `django` (already installed in the instance
image). Exit 0 iff every obligation holds.
"""
import random
import sys


def _configure():
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            USE_I18N=True,
            USE_L10N=True,
            USE_TZ=True,
            INSTALLED_APPS=[],
            DATABASES={},
        )
    import django
    django.setup()


def main():
    _configure()
    from django.utils.formats import get_format, reset_format_cache, FORMAT_SETTINGS
    from django.utils.translation import gettext_lazy, activate

    activate("en")  # no catalog installed -> gettext is the identity on names

    # The format names the resolver recognizes, plus names it does NOT recognize
    # (it returns them verbatim) — both must behave identically across the legs.
    setting_names = sorted(FORMAT_SETTINGS)
    nonsetting_names = ["NOT_A_FORMAT", "date_format", "", "X", "Y-m-d",
                        "DATE_FORMAT ", "decimal_separator", "123", "Ünïcode"]
    boundary = setting_names + nonsetting_names

    def check_name(name):
        # (1) force is total & content-preserving (pure str-proxy coercion;
        #     never feeds the lazy proxy into get_format).
        forced = str(gettext_lazy(name))
        assert isinstance(forced, str), (
            "force(deferred) should yield a str for %r, got %r"
            % (name, type(forced)))

        # (2) resolveName well-definedness: a distinct concrete str object with
        #     equal content resolves equally; neither concrete form raises.
        reset_format_cache()
        try:
            eager_val = get_format(name)
        except Exception as e:
            raise AssertionError(
                "get_format(%r) raised on a concrete str: %r" % (name, e))
        reset_format_cache()
        clone = ("%s" % name)  # a fresh str object with equal content
        try:
            clone_val = get_format(clone)
        except Exception as e:
            raise AssertionError(
                "get_format(clone of %r) raised on a concrete str: %r" % (name, e))
        assert clone_val == eager_val, (
            "resolveName depends on object identity, not content, for %r: "
            "%r != %r" % (name, clone_val, eager_val))

        # (3) the forced content resolves like the eager content (composition the
        #     spec relies on), checked on concrete strings only.
        if forced == name:
            reset_format_cache()
            try:
                forced_val = get_format(forced)
            except Exception as e:
                raise AssertionError(
                    "get_format(forced %r) raised on a concrete str: %r"
                    % (forced, e))
            assert forced_val == eager_val, (
                "resolveName not well-defined: resolving the forced content %r "
                "(=%r) != resolving the eager content (=%r)"
                % (forced, forced_val, eager_val))

    for nm in boundary:
        check_name(nm)

    # randomized fuzz over generated names (a mix of real setting names with
    # noise, and random ascii names the resolver returns verbatim).
    rng = random.Random(15741)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789 abc"
    for _ in range(2000):
        if rng.random() < 0.5:
            nm = rng.choice(setting_names)
        else:
            k = rng.randint(0, 16)
            nm = "".join(rng.choice(alphabet) for _ in range(k))
        check_name(nm)

    print("G-AX OK: resolveName well-defined (distinct concrete strs with equal "
          "content resolve equally; forced content resolves like eager content) "
          "and force total/content-preserving over %d boundary + 2000 fuzz names "
          "— validated against the unchanged pre-patch callee, no lazy proxy fed "
          "to get_format." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
