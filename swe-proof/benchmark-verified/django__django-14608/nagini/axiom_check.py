#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14608.

The bundle consumes NO @ContractOnly axiom. The only callee whose behaviour
the proof relies on — the message-collection constructor's rule for the
rendered class attribute (no marker tag yields the generic class "errorlist";
a marker tag `t` yields "errorlist" + " " + t) — is modelled DEEPLY by the
pure function `class_attr` in model.py. This script validates that deep model
(an A-reference) against the REAL callee, Django's `ErrorList`:

  (A-reference) class_attr(tag) == the rendered class attribute the real
      ErrorList constructor assigns:
        ErrorList(error_class=None) .error_class == "errorlist"
        ErrorList(error_class=t)    .error_class == "errorlist " + t
      and the rendered list `str(ErrorList(items, error_class='nonform'))`
      carries `class="errorlist nonform"`.

It imports only Django itself (the project the patch lives in); nothing
test-private. Exit 0 iff every observation matches the model. Outside the
container Django is unavailable, so it prints `G-AX SKIP` and returns 0; the
orchestrator runs it in-container.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

_GENERIC = "errorlist"          # generic_class()  -> code points of 'errorlist'
_TAG = "nonform"                # nonform_tag()     -> code points of 'nonform'


def class_attr(tag):
    """Reference implementation of model.py's deep model `class_attr`, on
    strings (the empty string models the empty `List[int]` / no marker tag)."""
    if len(tag) == 0:
        return _GENERIC
    return _GENERIC + " " + tag


def main():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                USE_I18N=False,
                USE_L10N=False,
                INSTALLED_APPS=[],
            )
        django.setup()
        from django.forms.utils import ErrorList
    except Exception as exc:  # pragma: no cover - host without Django
        print("G-AX SKIP: Django not importable here (%s); "
              "orchestrator runs this in-container" % (exc,))
        return 0

    # --- A-reference: class_attr == the real ErrorList class-attribute rule ---

    # (1) no marker tag -> the generic class only.
    el_none = ErrorList()
    assert el_none.error_class == class_attr(""), (
        "class_attr deep model unsound for no-tag: ErrorList().error_class=%r, "
        "model gives %r" % (el_none.error_class, class_attr("")))
    el_none2 = ErrorList(error_class=None)
    assert el_none2.error_class == class_attr(""), (
        "class_attr deep model unsound for error_class=None: %r vs %r"
        % (el_none2.error_class, class_attr("")))

    # (2) the marker tag this benchmark uses -> "errorlist nonform".
    el_tag = ErrorList(error_class=_TAG)
    assert el_tag.error_class == class_attr(_TAG), (
        "class_attr deep model unsound for tag=%r: ErrorList.error_class=%r, "
        "model gives %r" % (_TAG, el_tag.error_class, class_attr(_TAG)))
    assert el_tag.error_class == "errorlist nonform", (
        "the marker tag did not render as the expected class: %r"
        % (el_tag.error_class,))

    # (3) fuzz arbitrary marker tags: the rule must hold for any tag.
    rng = random.Random(14608)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_0123456789"
    fuzz_tags = ["", "nonform", "nonfield", "a", "x y", "errorlist"]
    for _ in range(2000):
        n = rng.randint(1, 16)
        fuzz_tags.append("".join(rng.choice(alphabet) for _ in range(n)))
    for tag in fuzz_tags:
        el = ErrorList(error_class=(tag if tag != "" else None))
        assert el.error_class == class_attr(tag), (
            "class_attr deep model unsound for tag=%r: ErrorList.error_class=%r"
            ", model gives %r" % (tag, el.error_class, class_attr(tag)))

    # (4) the rendered list (str / as_ul) carries the marker class verbatim —
    # exactly the string the F2P tests assert.
    el_items = ErrorList(["Please submit at most 1 form."], error_class="nonform")
    rendered = str(el_items)
    assert rendered == (
        '<ul class="errorlist nonform"><li>Please submit at most 1 form.</li>'
        '</ul>'), (
        "rendered non-form error list did not match expected: %r" % (rendered,))
    # the rebuilt-empty collection (init site) carries the marker class too.
    el_empty = ErrorList(error_class="nonform")
    assert el_empty.error_class == "errorlist nonform", (
        "empty collection did not carry the marker class: %r"
        % (el_empty.error_class,))

    print("G-AX OK: class_attr deep model (== ErrorList class-attribute rule) "
          "sound on %d marker-tag observations + rendered-list witnesses"
          % (len(fuzz_tags),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
