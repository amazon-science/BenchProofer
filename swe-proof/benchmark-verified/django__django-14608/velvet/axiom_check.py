#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14608.

The bundle has ONE kind-A construct: the A-reference `cssClassFor`, a deep model
(Solution.lean pure region) of the UNCHANGED error-collection constructor's
class-string computation — `django.forms.utils.ErrorList.__init__`
(django/forms/utils.py:84-90):

    def __init__(self, initlist=None, error_class=None):
        super().__init__(initlist)
        if error_class is None:
            self.error_class = 'errorlist'
        else:
            self.error_class = 'errorlist {}'.format(error_class)

The model:

    cssClassFor none        = "errorlist"
    cssClassFor (some lbl)  = "errorlist " + lbl

G-AX validates the deep model == the real constructor by executing the REAL
`ErrorList` on boundary labels (None, '', 'nonform', 'nonfield', multi-token,
sentinel chars) plus randomized fuzz, asserting the constructed object's
`.error_class` equals the model on every input, and that the stored message list
(`.data`) round-trips the input messages (the part the patch must preserve).

Imports only the repo callee (`django.forms.utils.ErrorList`); django settings
are configured minimally in-container. Exit 0 iff every obligation holds.
"""
import random
import string
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True, USE_TZ=False, DATABASES={},
            INSTALLED_APPS=['django.forms'], USE_I18N=False,
        )
        django.setup()


def css_class_for(modifier):
    """Model cssClassFor: None -> 'errorlist'; label -> 'errorlist ' + label."""
    if modifier is None:
        return "errorlist"
    return "errorlist " + modifier


def check_class(ErrorList, messages, modifier):
    """Assert the REAL ErrorList(...).error_class == cssClassFor(modifier) and
    its stored data round-trips the messages."""
    if modifier is None:
        el = ErrorList(list(messages))
    else:
        el = ErrorList(list(messages), error_class=modifier)
    observed = el.error_class
    expected = css_class_for(modifier)
    assert observed == expected, (
        "cssClassFor deep model unsound for modifier=%r: ErrorList gave %r, "
        "model gives %r" % (modifier, observed, expected))
    # the messages the construction must preserve (the I/R leg of the impl)
    assert list(el) == list(messages), (
        "ErrorList did not preserve messages %r (stored %r)"
        % (list(messages), list(el)))


def main():
    _configure_django()
    from django.forms.utils import ErrorList

    # --- boundary labels --------------------------------------------------
    boundary_modifiers = [
        None, "", "nonform", "nonfield", "errorlist",
        "a b c", "x", "NONFORM", "non form", "  ", "\t",
        "css-1_2", "é•", "a" * 100,
    ]
    boundary_messages = [
        [],
        ["Please submit at most 1 form."],
        ["Please submit at least 3 forms."],
        ["You may only specify a drink once."],
        ["one", "two", "three"],
        ["with <html> & 'chars'"],
    ]
    for mod in boundary_modifiers:
        for msgs in boundary_messages:
            check_class(ErrorList, msgs, mod)

    # --- randomized fuzz --------------------------------------------------
    rng = random.Random(14608)
    alphabet = string.ascii_letters + string.digits + " -_.:é•<>&'\""
    for _ in range(20000):
        if rng.random() < 0.1:
            mod = None
        else:
            n = rng.randint(0, 20)
            mod = "".join(rng.choice(alphabet) for _ in range(n))
        k = rng.randint(0, 5)
        msgs = ["".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
                for _ in range(k)]
        check_class(ErrorList, msgs, mod)

    # --- the specific modifier the patch uses -----------------------------
    check_class(ErrorList, ["Please submit at most 1 form."], "nonform")
    assert css_class_for("nonform") == "errorlist nonform"

    print("G-AX OK: cssClassFor deep model (== ErrorList.__init__ class string) "
          "sound on %d boundary + 20000 fuzz label/message combinations"
          % (len(boundary_modifiers) * len(boundary_messages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
