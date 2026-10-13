#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12276 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. `UploadControl` copies over as a plain
class. The single @ContractOnly callee, `generic_requires_value`, is realized
by calling the REAL unchanged inherited base repo function
(`django.forms.widgets.Widget.use_required_attribute`, per mapping.md §3.1)
on a widget of the file-upload family whose hidden state matches the `hidden`
argument.

ORACLE: the REAL patched repo function the model models per mapping.md §1 —
`django.forms.widgets.FileInput.use_required_attribute(self, initial)`. The
gate applies patch.diff to /testbed before this script runs; PYTHONPATH=
/testbed makes the patched module importable.

Type bridge (mapping.md §2):
  - `control.hidden`  <-> `self.is_hidden` on the widget. A stock FileInput
    has is_hidden == False; the hidden==True side of the model's free field
    is realized by a subclass of the same family whose input type is the
    hidden one, so is_hidden == True while method resolution is unchanged.
  - `value_present`   <-> the truth value of `initial`. The repo method only
    truth-tests `initial`, so any object bridges through bool(initial); the
    fuzz battery draws `initial` from many Python types covering both
    truthiness cases (None, strings, ints, containers, bools, file-like
    objects, objects with custom __bool__ / __len__).

Input domain: Requires demands only read access to `control.hidden`, so
every (hidden: bool, initial: object) pair is Requires-satisfying.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz draws.
Pinned fuzz seed: 12276.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the package under test) only.
"""
import json
import random
import sys

SEED = 12276
N_FUZZ = 100_000


def _configure_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={}, USE_TZ=False)
    import django
    django.setup()


# --- shim for the model's minimal control object ------------------------------

class UploadControl:
    def __init__(self, hidden):
        self.hidden = hidden


# --- @ContractOnly callee: realized by the REAL repo base function ------------
# generic_requires_value(hidden) delegates to the real unchanged inherited
# base decision, evaluated on a widget of the file-upload family whose
# is_hidden equals `hidden`. Bound lazily after Django import (see main()).

_WIDGET_FOR_HIDDEN = {}


def generic_requires_value(hidden):
    from django.forms.widgets import Widget
    w = _WIDGET_FOR_HIDDEN[hidden]
    assert w.is_hidden == hidden
    # The base decision reads only the widget's hidden state; the second
    # argument is ignored by the base, so a placeholder is passed.
    return Widget.use_required_attribute(w, None)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def requires_value(control, value_present):
    return generic_requires_value(control.hidden) and not value_present


# --- fuzz battery for `initial` (the truthiness-observed object) --------------

class _FileLike:
    def __init__(self, url):
        self.url = url


class _FalsyObj:
    def __bool__(self):
        return False


class _SizedObj:
    def __init__(self, n):
        self._n = n

    def __len__(self):
        return self._n


_BOUNDARY_INITIALS = [
    None, "", 0, 0.0, [], (), {}, set(), False, _FalsyObj(), _SizedObj(0),
    "resume.txt", "x", " ", 1, -1, [0], (0,), {"a": 1}, {0}, True,
    _SizedObj(5), _FileLike("/media/f.txt"), object(),
]


def _rand_initial(rng):
    kind = rng.randrange(10)
    if kind == 0:
        return None
    if kind == 1:
        n = rng.randrange(0, 8)
        return "".join(rng.choice("abcxyz .-_/") for _ in range(n))
    if kind == 2:
        return rng.randrange(-3, 4)
    if kind == 3:
        return [rng.randrange(0, 2) for _ in range(rng.randrange(0, 4))]
    if kind == 4:
        return {k: 1 for k in range(rng.randrange(0, 3))}
    if kind == 5:
        return bool(rng.randrange(2))
    if kind == 6:
        return _SizedObj(rng.randrange(0, 4))
    if kind == 7:
        return rng.choice([_FalsyObj(), _FileLike("/m/%d" % rng.randrange(9))])
    if kind == 8:
        return rng.uniform(-1.0, 1.0) if rng.randrange(2) else 0.0
    return tuple(range(rng.randrange(0, 3)))


def check_one(real_widget, hidden, initial):
    """Diff shadow vs the real patched method on one (hidden, initial) pair;
    return an error string on disagreement, else None."""
    control = UploadControl(hidden)
    value_present = bool(initial)  # the type bridge for `initial`
    shadow = requires_value(control, value_present)
    real = real_widget.use_required_attribute(initial)
    if bool(shadow) != bool(real) or not isinstance(shadow, bool):
        return ("DISAGREEMENT\n  hidden=%r initial=%r (value_present=%r)\n"
                "  shadow=%r\n  real=%r"
                % (hidden, initial, value_present, shadow, real))
    return None


def main():
    _configure_django()
    from django.forms.widgets import FileInput  # REAL patched oracle class

    # hidden==True realized within the same widget family (same method
    # resolution as the oracle), so both values of the model's free field
    # are exercised against the real method.
    class _HiddenFileInput(FileInput):
        input_type = "hidden"

    visible = FileInput()
    hidden_w = _HiddenFileInput()
    assert visible.is_hidden is False and hidden_w.is_hidden is True
    _WIDGET_FOR_HIDDEN[False] = visible
    _WIDGET_FOR_HIDDEN[True] = hidden_w
    oracles = {False: visible, True: hidden_w}

    checked = 0
    n_boundary = 0
    for hidden in (False, True):
        for initial in _BOUNDARY_INITIALS:
            err = check_one(oracles[hidden], hidden, initial)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        hidden = bool(rng.randrange(2))
        initial = _rand_initial(rng)
        err = check_one(oracles[hidden], hidden, initial)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real method on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
