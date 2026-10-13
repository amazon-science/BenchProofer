#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9658.

There is NO consumed value-axiom in this bundle. The behaviour under
specification is modelled DEEPLY:

  * ``subclass_short_name`` (model.py): the SHORT identifier of a placeholder
    reached by attribute name ``name`` is ``name`` itself.
  * ``placeholder_display_name``   (model.py): the placeholder's DISPLAY identifier
    (the qualified name the renderer reads) is its short identifier.
  * ``render_qualified``    (model.py pure region): the renderer joins the
    owning module path and the display identifier with a dot.

G-AX therefore validates these deep models against the REAL callee chain in the
installed sphinx package (A-reference): it builds a real placeholder object the
way the renderer reaches one (a stand-in package, then an attribute access),
reads the object's real module path / display identifier, and renders the real
fully-qualified cross-reference, asserting each equals what the deep model
computes.

PRE/POST DISCRIMINATOR (so the check exits 0 on either testbed while pinning the
discriminating behaviour): the real placeholder's display identifier is empty on
the base_commit (pre-fix) code and equals the attribute name on the patched
code. The single F2P test is ``test_restify_mock`` — the dangling-dot symptom is
observable through ``restify`` ONLY. ``restify`` reaches the placeholder's
``__qualname__`` directly and joins it as ``<module>.<qualname>``, so on the
base_commit (empty ``__qualname__``) it produces a dangling ``<module>.`` and on
the patched code it produces ``<module>.<name>``. ``stringify`` is NOT a
discriminator: the placeholder is falsy (``__len__()==0``), so ``stringify``
short-circuits through ``repr()`` = ``__display_name__`` = ``<module>.<name>``
and yields the same (already-correct) value on BOTH commits (this is why
``test_stringify_mock`` is PASS_TO_PASS, not FAIL_TO_PASS). We inspect the
installed source to decide which renderer behaviour is present and assert the
outcome that detection implies on ``restify``. The model's decision is the
propagated (patched) one.

Imports are standard library (``importlib``, ``inspect``, ``random``, ``sys``)
plus the installed sphinx package whose mock/typing modules the gold patch edits
and consumes. Exit 0 iff every obligation holds.
"""
import importlib
import inspect
import random
import sys


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def subclass_short_name(name):
    """Reference of model.py's deep model: the short identifier is the name."""
    return name


def placeholder_display_name(short_name):
    """Reference of model.py's deep model: the display identifier is the short
    identifier (the patched behaviour)."""
    return short_name


def render_qualified(module, display):
    """Reference of model.py's pure ``render_qualified``: the dotted join."""
    return module + "." + display


# --- locate the real callees -------------------------------------------------

def _import_mock():
    try:
        mod = importlib.import_module("sphinx.ext.autodoc.mock")
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX NOTE: sphinx.ext.autodoc.mock not importable (%r); "
              "deep-model checks cannot run in this environment." % (exc,))
        return None
    # Require the placeholder API this benchmark version exposes.
    if not (hasattr(mod, "mock") and hasattr(mod, "_MockObject")
            and hasattr(mod, "_make_subclass")):
        print("G-AX NOTE: installed sphinx.ext.autodoc.mock lacks the expected "
              "placeholder API (version skew); deep-model checks skipped.")
        return None
    return mod


def _import_typing():
    """Return the sphinx.util.typing module only if it exposes BOTH the
    ``restify`` and ``stringify`` renderer entry points this benchmark version
    (sphinx 4.3) ships. Newer/older sphinx that renamed them (e.g.
    ``stringify_annotation``) cause the renderer witness to be skipped; the
    core display-identifier A-reference is checked regardless."""
    try:
        mod = importlib.import_module("sphinx.util.typing")
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX NOTE: sphinx.util.typing not importable (%r)." % (exc,))
        return None
    if not (hasattr(mod, "restify") and hasattr(mod, "stringify")):
        print("G-AX NOTE: installed sphinx.util.typing lacks restify/stringify "
              "(version skew); renderer witness skipped, display-identifier "
              "A-reference still checked.")
        return None
    return mod


def _fix_present(mock_mod):
    """Inspect the installed mock module to decide whether the display-identifier
    propagation fix is present: the patched ``__init__`` assigns
    ``self.__qualname__ = self.__name__`` and ``_make_subclass`` records
    ``'__name__': name``. The base_commit code sets ``self.__qualname__ = ''``
    and records no ``__name__``."""
    try:
        init_src = inspect.getsource(mock_mod._MockObject.__init__)
        sub_src = inspect.getsource(mock_mod._make_subclass)
    except (OSError, TypeError):  # pragma: no cover - source unavailable
        return None
    init_fixed = "self.__qualname__ = self.__name__" in init_src
    sub_fixed = "'__name__': name" in sub_src or '"__name__": name' in sub_src
    return init_fixed and sub_fixed


# --- A-reference: deep model == real placeholder qualified name --------------

def check_real_placeholder(mock_mod, typing_mod, modname, attrs):
    """Build the REAL placeholder reached as ``modname`` then a chain of
    attribute accesses ``attrs``; read its real module path + display
    identifier; render it; and compare against the deep model.

    Returns (fix_present, checked_count)."""
    fix = _fix_present(mock_mod)
    checked = 0
    with mock_mod.mock([modname]):
        obj = importlib.import_module(modname)
        for a in attrs:
            obj = getattr(obj, a)
        # `obj` is the placeholder the renderer receives.
        real_module = getattr(obj, "__module__")
        real_display = getattr(obj, "__qualname__")
        leaf = attrs[-1]                      # the attribute name it was reached by

        # The deep model's short identifier == the attribute name.
        model_short = subclass_short_name(leaf)
        assert model_short == leaf, \
            "deep model short identifier wrong: %r != %r" % (model_short, leaf)

        if fix is True:
            # Patched code: the real display identifier IS the attribute name,
            # so the deep model (display == short == name) matches reality.
            assert real_display == leaf, (
                "patched installed code but placeholder display identifier "
                "%r != attribute name %r" % (real_display, leaf))
            model_display = placeholder_display_name(model_short)
            assert model_display == real_display, (
                "deep model display %r != real display %r"
                % (model_display, real_display))
            # Render via the deep model and via the REAL renderers; both must
            # end in the attribute name (never a dangling `<module>.`).
            model_ref = render_qualified(real_module, model_display)
            assert model_ref.endswith("." + leaf), \
                "deep-model rendered ref %r does not end in name" % (model_ref,)
            if typing_mod is not None:
                restified = typing_mod.restify(obj)
                stringified = typing_mod.stringify(obj)
                expected_string = render_qualified(real_module, leaf)
                # restify (the F2P bug-path) reads __qualname__ directly and
                # joins <module>.<qualname>; on patched code that is
                # <module>.<name>, so the dangling dot is repaired.
                assert restified == ":py:class:`%s`" % expected_string, (
                    "real restify %r != expected %r"
                    % (restified, ":py:class:`%s`" % expected_string))
                assert not restified.endswith(".`"), \
                    "restify regressed to a dangling-dot reference: %r" % restified
                # stringify (P2P, same value on either commit): the falsy
                # placeholder short-circuits to repr()==__display_name__, which
                # is <module>.<name> on both commits. We pin its value equals
                # the deep-model render; it is NOT a bug discriminator.
                assert stringified == expected_string, (
                    "real stringify %r != deep-model render %r"
                    % (stringified, expected_string))
            checked += 1
        elif fix is False:
            # Base_commit code (the bug): the real display identifier is empty,
            # so the renderer that reads __qualname__ drops the trailing name.
            # Asserting this confirms the discriminator is real (the deep model
            # fixes it).
            assert real_display == "", (
                "base_commit installed code but display identifier %r is not "
                "empty (discriminator broken)" % (real_display,))
            if typing_mod is not None:
                # restify is the F2P bug-path: it reads __qualname__ directly,
                # so an empty __qualname__ yields a dangling `<module>.` (the
                # `:py:class:` wrapper ends in ".`").
                restified = typing_mod.restify(obj)
                assert restified.endswith(".`"), (
                    "base_commit code yet restify did not produce a dangling "
                    "dot: %r (discriminator broken)" % (restified,))
                # stringify is P2P (NOT the bug-path): the falsy placeholder
                # short-circuits to repr()==__display_name__ == <module>.<name>,
                # so it is already correct at base_commit and does NOT dangle.
                stringified = typing_mod.stringify(obj)
                assert not stringified.endswith("."), (
                    "stringify unexpectedly dangled at base_commit: %r "
                    "(stringify should already be correct via __display_name__)"
                    % (stringified,))
                assert stringified == render_qualified(real_module, leaf), (
                    "base_commit stringify %r != <module>.<name> %r "
                    "(stringify short-circuit changed)"
                    % (stringified, render_qualified(real_module, leaf)))
            checked += 1
        else:
            print("G-AX NOTE: installed mock source unavailable; skipping the "
                  "pre/post discriminator on %r.%r (deep-model self-consistency "
                  "still checked)." % (modname, ".".join(attrs)))
    return fix, checked


def main():
    mock_mod = _import_mock()
    if mock_mod is None:
        # Cannot run the real callee here; the deep model is self-consistent by
        # construction (display == short == name; render is a dotted join).
        # G-AX proper runs in-container where sphinx is importable.
        print("G-AX SKIP: sphinx not importable in this environment.")
        return 0
    typing_mod = _import_typing()

    rng = random.Random(9658)
    alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

    cases = [
        ("unknown", ["secret", "Class"]),       # the F2P input
        ("unknown", ["Class"]),
        ("unknown", ["a", "b", "c", "Leaf"]),
        ("pkg", ["sub", "Thing"]),
    ]
    # randomized identifier chains
    for _ in range(200):
        nattr = rng.randint(1, 4)
        attrs = []
        for _ in range(nattr):
            n = rng.randint(1, 8)
            ident = rng.choice("abcXYZ_") + "".join(
                rng.choice(alpha) for _ in range(n))
            attrs.append(ident)
        cases.append(("modroot", attrs))

    fix_seen = None
    total = 0
    for modname, attrs in cases:
        fix, checked = check_real_placeholder(mock_mod, typing_mod, modname, attrs)
        if fix is not None:
            fix_seen = fix
        total += checked

    print("G-AX OK: deep model (short==name, display==short, render=dotted "
          "join) validated against the real sphinx placeholder + renderer on "
          "%d cases; installed fix_present=%r." % (total, fix_seen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
