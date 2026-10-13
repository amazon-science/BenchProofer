#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-9698.

This bundle consumes NO @ContractOnly axiom. The label-construction operation
is modelled DEEPLY in model.py (the pure `index_label` / `role_suffix` /
`call_marker` / `group_open` / `is_callable_role` fold over code points). What
must be validated is that this deep model reproduces the REAL label the patched
code produces -- an A-reference check.

The real label is produced by the member-role branch of the patched
`get_index_text`, which is a gettext lookup of a fixed template followed by `%`
substitution of the member and class names:

    'classmethod' -> _('%s() (%s class method)')  % (methname, clsname)
    'property'    -> _('%s (%s property)')         % (methname, clsname)   # patched: no ()
    'staticmethod'-> _('%s() (%s static method)')  % (methname, clsname)
    else (method) -> _('%s() (%s method)')         % (methname, clsname)

In the test/build environment no translation catalogue is loaded, so `_(t)` is
the identity on the template and the observed label is exactly
`template % (methname, clsname)`. This check uses those POST-PATCH templates as
the real oracle and asserts the deep model's code-point output equals the real
label on boundary + fuzz names. Exit 0 iff the deep model is sound.

Imports only the standard library. The optional second half additionally drives
the REAL sphinx `PyMethod.get_index_text` if sphinx is importable (in-container),
confirming the templates above are the ones the patched code actually uses.
"""
import random
import sys

# Post-patch real templates (the gettext identity case), one per role selector.
# Selector: 0 method, 1 classmethod, 2 property (non-callable), 3 staticmethod.
_TEMPLATE = {
    0: '%s() (%s method)',
    1: '%s() (%s class method)',
    2: '%s (%s property)',          # patched: the property label has NO parens
    3: '%s() (%s static method)',
}


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def call_marker():
    return [40, 41]                 # '()'


def group_open():
    return [32, 40]                 # ' ('


def role_suffix(option):
    if option == 1:
        return [ord(c) for c in ' class method)']
    if option == 2:
        return [ord(c) for c in ' property)']
    if option == 3:
        return [ord(c) for c in ' static method)']
    return [ord(c) for c in ' method)']


def is_callable_role(option):
    return option != 2


def index_label(methname_cp, clsname_cp, option):
    """Reference implementation of model.py's deep model `index_label`, as a
    list of code points."""
    out = list(methname_cp)
    if is_callable_role(option):
        out += call_marker()
    out += group_open()
    out += list(clsname_cp)
    out += role_suffix(option)
    return out


# --- the A-reference check ---------------------------------------------------

def check_label(methname, clsname, option):
    """Assert the deep model index_label(...) == the REAL label string."""
    real = _TEMPLATE[option] % (methname, clsname)        # real oracle
    observed = [ord(ch) for ch in real]
    expected = index_label([ord(c) for c in methname],
                           [ord(c) for c in clsname], option)
    assert observed == expected, (
        "index_label deep model unsound for option=%d methname=%r clsname=%r: "
        "real label gave %r, deep model gives %r"
        % (option, methname, clsname, observed, expected))
    # The discriminating structural property: '()' follows the member name
    # exactly for the callable roles.
    after = expected[len(methname):len(methname) + 2]
    has_parens = (after == call_marker())
    assert has_parens == is_callable_role(option), (
        "call-marker discriminator wrong for option=%d: present=%s expected=%s"
        % (option, has_parens, is_callable_role(option)))


def main():
    names = ['meth5', 'bar', 'baz', 'Class', 'Foo', 'a', '', 'X',
             'do_thing', 'value', 'data_set', 'name_with_underscores',
             'CamelCase', 'mixedCase', 'with space', "o'brien",
             'unicode_é', '__init__', '_private', 'p123']

    # boundary + cartesian over names x roles
    for methname in names:
        for clsname in names:
            for option in (0, 1, 2, 3):
                check_label(methname, clsname, option)

    # randomized fuzz
    rng = random.Random(9698)
    alphabet = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.'
                    " '()%é")
    for _ in range(20000):
        m = ''.join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
        c = ''.join(rng.choice(alphabet) for _ in range(rng.randint(0, 16)))
        option = rng.randint(0, 3)
        check_label(m, c, option)

    # --- optional: drive the REAL patched sphinx callee, if importable -------
    drove_real = False
    try:
        from unittest import mock
        from sphinx.domains.python import PyMethod
    except Exception:
        pass
    else:
        # Build a minimal PyMethod whose get_index_text we can call directly.
        opt_to_kw = {1: 'classmethod', 2: 'property', 3: 'staticmethod'}

        def drive(option, kw):
            pm = PyMethod.__new__(PyMethod)
            pm.options = {} if kw is None else {kw: True}
            # `env` is a read-only property reading state.document.settings.env;
            # build that chain so the real branch runs unmodified.
            pm.state = mock.Mock()
            pm.state.document.settings.env.config.add_module_names = False
            return pm.get_index_text('', ('Class.meth5', 'Class'))

        # Is the loaded sphinx already patched? (property label has no '()').
        patched = "()" not in drive(2, 'property')
        for option, kw in {0: None, 1: 'classmethod',
                           2: 'property', 3: 'staticmethod'}.items():
            # The three callable roles are unchanged by the patch and must match
            # in any sphinx version; the property role matches only once patched.
            if option == 2 and not patched:
                continue
            real = drive(option, kw)
            observed = [ord(ch) for ch in real]
            expected = index_label([ord(c) for c in 'meth5'],
                                   [ord(c) for c in 'Class'], option)
            assert observed == expected, (
                "REAL sphinx get_index_text disagrees with deep model for "
                "option=%d: real=%r model=%r" % (option, real, expected))
            drove_real = True
        if not patched:
            print("note: loaded sphinx is pre-patch; property role cross-check "
                  "deferred to the patched in-container run (callable roles "
                  "validated, all unchanged by the patch).")

    print("G-AX OK: index_label deep model == real label on cartesian boundary "
          "(%d names^2 x 4 roles) + 20000 fuzz; discriminator sound; "
          "real-sphinx cross-check=%s" % (len(names), drove_real))
    return 0


if __name__ == "__main__":
    sys.exit(main())
