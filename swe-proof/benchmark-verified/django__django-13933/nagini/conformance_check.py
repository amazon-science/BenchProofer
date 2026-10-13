#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13933 (nagini).

SHADOW  — the impl region of model.py, copied VERBATIM with the contract
          calls (Requires/Ensures/Invariant/Assert and their Acc/list_pred
          arguments) stripped; the model IS Python, so no transliteration.
          PSeq is a thin tuple shim; ToSeq materializes a list; the @Pure
          helpers copy over as plain functions. The shadow works over the
          model's carrier types (List[int] of Unicode code points).

BRIDGE  — mapping.md §2's type abstraction: str <-> List[int] of code
          points (s[k] <-> ord); the template argument is the field's
          configurable invalid-choice message template and the value
          argument is the rejected submitted string. The fuzzer stays
          inside the documented domain: templates whose only %-construct
          is the named %(value)s token (exactly the form the relevant
          repo templates inhabit), and non-empty submitted values (an
          empty submission short-circuits before any error is produced,
          so no message exists to observe there).

ORACLE  — the REAL patched repo behaviour (PYTHONPATH=/testbed, gold patch
          applied by the gate before this script runs): a ModelChoiceField
          configured with the template, driven through `to_python` with a
          value its queryset rejects; the human-readable text of the raised
          ValidationError (via `.messages`, which performs the real
          named-mapping rendering) is the observable. The queryset is a
          minimal stand-in exposing only what `to_python` reads, so every
          lookup misses and the invalid-choice arm is exercised.

Exit 0 iff zero disagreements over the boundary cases + 100000 fuzzed
inputs. Pinned seed: 13933. stdlib + django (the repo under test) only.
"""
import random
import sys

SEED = 13933
N_FUZZ = 100_000

sys.setrecursionlimit(100_000)  # the shadow recurses once per code point

# ---------------------------------------------------------------------------
# Contract shims: nagini_contracts symbols stripped to executable Python.
# ---------------------------------------------------------------------------


class PSeq:
    """Plain tuple shim for nagini's pure sequence type."""

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# ---------------------------------------------------------------------------
# model.py pure region, copied over as plain functions (@Pure stripped).
# ---------------------------------------------------------------------------


def placeholder():
    # '%' '(' 'v' 'a' 'l' 'u' 'e' ')' 's'
    return PSeq(37, 40, 118, 97, 108, 117, 101, 41, 115)


def starts_with_placeholder(s):
    return len(s) >= 9 and s.take(9) == placeholder()


def interpolated(template, value):
    if len(template) == 0:
        return template
    if starts_with_placeholder(template):
        return value + interpolated(template.drop(9), value)
    return template.take(1) + interpolated(template.drop(1), value)


# ---------------------------------------------------------------------------
# model.py impl region, VERBATIM with contract statement lines
# (Requires/Ensures/Invariant/Assert) stripped.
# ---------------------------------------------------------------------------


def render_invalid_choice(template, value):
    return _render(ToSeq(template), value, 0)


def _render(ts, value, i):
    n = len(ts)
    result = []  # type: list
    if i == n:
        return result
    if i + 9 <= n and ts.drop(i).take(9) == placeholder():
        result = _render(ts, value, i + 9)
        # Prepend the rejected value, element by element from its end.
        j = len(value)
        while j > 0:
            vj = value[j - 1]
            result = [vj] + result
            j = j - 1
        return result
    head = ts[i]
    result = _render(ts, value, i + 1)
    result = [head] + result
    return result


# ---------------------------------------------------------------------------
# Bridge: str -> List[int] code points and back (mapping.md §2).
# ---------------------------------------------------------------------------


def shadow_message(template_str, value_str):
    out = render_invalid_choice([ord(c) for c in template_str],
                                [ord(c) for c in value_str])
    return "".join(chr(c) for c in out)


# ---------------------------------------------------------------------------
# Oracle: the REAL patched repo path. A ModelChoiceField whose queryset
# stand-in rejects every lookup; the rendered ValidationError text is the
# observable (rendering happens in `.messages`, the real message machinery).
# ---------------------------------------------------------------------------

_FIELD = None


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False)
    django.setup()


class _NoMatch(Exception):
    pass


class _StandInModel:
    DoesNotExist = _NoMatch


class _StandInQuerySet:
    model = _StandInModel

    def all(self):
        return self

    def get(self, **kwargs):
        raise _NoMatch()


def _field():
    global _FIELD
    if _FIELD is None:
        from django.forms.models import ModelChoiceField
        _FIELD = ModelChoiceField(queryset=_StandInQuerySet())
    return _FIELD


def oracle_message(template_str, value_str):
    from django.core.exceptions import ValidationError
    field = _field()
    field.error_messages['invalid_choice'] = template_str
    try:
        field.to_python(value_str)
        return None
    except ValidationError as e:
        msgs = e.messages
        return msgs[0] if msgs else None


# ---------------------------------------------------------------------------
# Input generation: Requires-satisfying inputs inside the documented domain
# (only %-construct in the template is the %(value)s token; value non-empty
# so the field actually produces an error to observe).
# ---------------------------------------------------------------------------

PH = "%(value)s"
SAFE_CHARS = list("abcXYZ0129 .,;:!?_-=+~@#&<>()[]{}'\"/\\|") + ["é", "•", "→"]


def gen_template(rng):
    parts = []
    segs = rng.randint(0, 6)
    for _ in range(segs):
        if rng.random() < 0.45:
            parts.append(PH)
        else:
            seglen = rng.randint(0, 5)
            parts.append("".join(rng.choice(SAFE_CHARS) for _ in range(seglen)))
    return "".join(parts)


def gen_value(rng):
    vchars = [c for c in SAFE_CHARS if c != "%"]
    vlen = rng.randint(1, 8)  # non-empty: empty submissions raise no error
    return "".join(rng.choice(vchars) for _ in range(vlen))


def boundary_cases():
    templates = [
        PH,
        PH + PH,
        PH + PH + PH,
        "a" + PH + "b",
        PH + " at end",
        "start " + PH,
        "no placeholder at all",
        '"%(value)s" is not one of the available choices.',
        "Select a valid choice. That choice is not one of the available"
        " choices.",
        "Select a valid choice. %(value)s is not one of the available"
        " choices.",
        "%(value)s IS INVALID CHOICE",
        "%(value)s(value)s",
    ]
    values = ["invalid", "foo", "4", "a b c", "X",
              "<script>", "Joe's", "café", "•", '"quoted"']
    for t in templates:
        for v in values:
            yield t, v


def main():
    _setup_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = list(boundary_cases())
    cases += [(gen_template(rng), gen_value(rng)) for _ in range(N_FUZZ)]

    for template, value in cases:
        count += 1
        shadow = shadow_message(template, value)
        oracle = oracle_message(template, value)
        if shadow != oracle:
            disagreements.append((template, value, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for t, v, sh, orc in disagreements:
            print("  template=%r value=%r\n    shadow=%r\n    oracle=%r"
                  % (t, v, sh, orc))
        return 1
    print("G-CONF OK: model.py impl shadow (code-point carrier, mapping.md "
          "bijection) agrees with the real patched invalid-choice message "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
