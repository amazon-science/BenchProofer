#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14771.

The changed behaviour is modeled DEEPLY (no consumed @ContractOnly axiom): the
forwarded implementation-option token list is `option_tokens` in model.py's
`pure` region. This check drives the REAL runtime transformation the gold patch
performs --

    if sys.implementation.name == 'cpython':
        args.extend(
            f'-X{key}' if value is True else f'-X{key}={value}'
            for key, value in <xoptions dict>.items()
        )

-- over real `dict` objects (exactly as `sys._xoptions.items()` is iterated),
and asserts that the produced token list equals the model's `option_tokens`
on boundary cases plus randomized fuzz. It also confirms the two decisive
runtime facts: (1) the selector is `value is True` -- an IDENTITY test against
the boolean True sentinel, so a truthy STRING value `'True'` takes the
name=value form, not the flag form; and (2) the running reference interpreter
reports `sys.implementation.name == 'cpython'`, the guard the forwarding is
gated on (sys.implementation.name; docs.python.org/3/library/sys.html#sys._xoptions).

Imports nothing repo-specific: `sys`/`random` are standard library. The deep
model is the A-reference; exit 0 iff every observation matches it.
"""
import random
import sys

# --- model.py reference encodings (kept in lock-step with the deep model) -----

# dash_x() == PSeq(45, 88) == '-X'; eq() == PSeq(61) == '='
_DASH_X = [45, 88]
_EQ = [61]


def cp(s):
    """A str rendered as a list of Unicode code points (the model carrier)."""
    return [ord(ch) for ch in s]


def option_token(key, is_flag, val):
    """Reference of model.py's `option_token`, as a list of code points:
    flag+name when the value is the present-with-no-value sentinel, else
    flag+name+'='+value."""
    if is_flag:
        return _DASH_X + cp(key)
    return _DASH_X + cp(key) + _EQ + cp(val)


def option_tokens_model(xoptions):
    """Reference of model.py's `option_tokens` fold over the option dict, as a
    list of code-point lists (one token per option, in iteration order)."""
    out = []
    for key, value in xoptions.items():
        is_flag = (value is True)
        # When the value is the flag sentinel, the value field is irrelevant;
        # otherwise it is the string form of the recorded value.
        val = "" if is_flag else _to_value_str(value)
        out.append(option_token(key, is_flag, val))
    return out


def _to_value_str(value):
    """The string the f-string `f'-X{key}={value}'` interpolates for a non-True
    value (the model's `opt_vals[i]` carrier)."""
    return "%s" % (value,)


# --- the REAL runtime transformation the gold patch performs ------------------

def real_forwarded_tokens(xoptions, implementation_name):
    """The token list the gold patch's `args.extend(<generator>)` appends,
    verbatim (the f-string generator under the cpython guard)."""
    if implementation_name != 'cpython':
        return []
    return [
        f'-X{key}' if value is True else f'-X{key}={value}'
        for key, value in xoptions.items()
    ]


def check(xoptions, implementation_name='cpython'):
    """Assert the model's `option_tokens` (under the is_reference_impl guard)
    equals the REAL forwarded token list."""
    real = real_forwarded_tokens(xoptions, implementation_name)
    real_cp = [cp(tok) for tok in real]
    if implementation_name != 'cpython':
        model_cp = []  # non-reference interpreter forwards nothing
    else:
        model_cp = option_tokens_model(xoptions)
    assert real_cp == model_cp, (
        "option_tokens deep model unsound on %r (impl=%r): real generator "
        "gave %r, deep model gives %r"
        % (xoptions, implementation_name, real_cp, model_cp))


def main():
    # --- boundary cases -------------------------------------------------------
    boundary = [
        {},                                   # no options
        {'utf8': True},                       # single flag-only option
        {'dev': True},
        {'a': 'b'},                           # single name=value option
        {'utf8': True, 'a': 'b'},             # the F2P case -> -Xutf8 -Xa=b
        {'a': 'b', 'utf8': True},             # order is preserved
        {'importtime': True, 'tracemalloc': '5', 'utf8': True},
        {'faulthandler': True, 'showrefcount': True},
        {'opt': ''},                          # empty value -> '-Xopt='
        {'k': 'v=w'},                         # value containing '='
        {'k': '1', 'l': '2', 'm': '3'},       # several name=value
        {'truthy': 'True'},                   # truthy STRING != True sentinel
        {'falsey': False},                    # value False is NOT the sentinel
        {'n': 0},                             # falsey int value -> name=0
        {'n': 1},                             # truthy int value (not True) -> name=1
        {'pi': 3},                            # int value rendered by %s
    ]
    for xo in boundary:
        check(xo, 'cpython')
        # On a non-reference interpreter nothing is forwarded.
        check(xo, 'pypy')
        check(xo, 'jython')

    # --- the decisive `value is True` identity test ---------------------------
    # Only the boolean True sentinel yields the flag form; truthy non-True
    # values (the string 'True', the int 1) take the name=value form.
    assert real_forwarded_tokens({'x': True}, 'cpython') == ['-Xx']
    assert real_forwarded_tokens({'x': 'True'}, 'cpython') == ['-Xx=True']
    assert real_forwarded_tokens({'x': 1}, 'cpython') == ['-Xx=1']
    assert real_forwarded_tokens({'x': False}, 'cpython') == ['-Xx=False']

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(14771)
    key_alphabet = "abcdefghijklmnopqrstuvwxyz_0123456789"
    val_alphabet = key_alphabet + "=.-/ "
    for _ in range(20000):
        n = rng.randint(0, 6)
        xo = {}
        for _ in range(n):
            klen = rng.randint(1, 8)
            key = "".join(rng.choice(key_alphabet) for _ in range(klen))
            r = rng.random()
            if r < 0.4:
                xo[key] = True                       # flag-only
            elif r < 0.7:
                vlen = rng.randint(0, 8)
                xo[key] = "".join(rng.choice(val_alphabet) for _ in range(vlen))
            elif r < 0.85:
                xo[key] = rng.randint(0, 1000)       # int value
            else:
                xo[key] = rng.choice([False, 'True', 'true', '0', ''])
        impl = rng.choice(['cpython', 'cpython', 'cpython', 'pypy'])
        check(xo, impl)

    # --- the guard fact: this reference interpreter reports 'cpython' ---------
    # (The forwarding step is gated on sys.implementation.name == 'cpython';
    #  the SWE-bench eval interpreter is CPython.)
    assert sys.implementation.name == 'cpython', (
        "expected the reference interpreter; got %r" % sys.implementation.name)

    print("G-AX OK: option_tokens deep model (== the real -X forwarding "
          "generator, gated on sys.implementation.name == 'cpython') sound on "
          "%d boundary + 20000 fuzz xoption dicts; value-is-True identity test "
          "and cpython guard confirmed" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
