#!/usr/bin/env python3
"""G-CONF for django__django-12262.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_parseTagArgs` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`django.template.library.parse_bits`, over >=1e5 fuzzed inputs. Zero
disagreements => exit 0.

Bridge (mapping.md): `bits` raw tokens are produced from the abstract `Tok`
list — `Tok.keyword k v` -> the bit string ``"k=v"`` and `Tok.positional s` ->
the bit string ``s`` — and fed to the REAL `parse_bits` with a REAL template
`Parser`, so the real `token_kwargs` / `compile_filter` perform the lexical
classification and value compilation (the A-reference boundary).

Observed channels (compiled values are opaque at the boundary):
  * on success: (len(args), [key for key in kwargs])   # ordered kwargs keys
  * on TemplateSyntaxError: the exact message string

stdlib-only beyond Django itself.
"""
import os
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False,
        DATABASES={}, INSTALLED_APPS=[], TEMPLATES=[],
    )
    django.setup()

from django.template.base import Parser
from django.template.library import parse_bits
from django.template.exceptions import TemplateSyntaxError


# ---- value literals that compile_filter accepts (kept simple + total) ----
VALUE_POOL = ["1", "2", "'x'", "'y'", "0", "42", "37"]
NAME_POOL = ["a", "b", "c", "kwarg", "one", "two", "context", "greeting"]


def make_parser():
    return Parser([])


# ---------------------------------------------------------------------------
# Oracle: the REAL patched parse_bits.
# ---------------------------------------------------------------------------
def oracle(bits, params, varargs, varkw, defaults, kwonly, kwonly_defaults,
           takes_context, name):
    parser = make_parser()
    try:
        args, kwargs = parse_bits(
            parser, list(bits), list(params), varargs, varkw, defaults,
            list(kwonly), kwonly_defaults, takes_context, name)
        # Compiled values are FilterExpressions; `.token` is the source value
        # string, so comparing tokens validates that each value is preserved
        # through the Tok -> bit -> token_kwargs/compile_filter round-trip.
        return ("ok",
                [a.token for a in args],
                [(k, v.token) for k, v in kwargs.items()])
    except TemplateSyntaxError as e:
        return ("err", str(e))
    except IndexError:
        # takes_context with an empty declared-parameter list: parse_bits
        # indexes params[0] and crashes. The Lean model bridges this distinct
        # (uncaught-crash) failure mode as the dedicated msgIndexError value.
        return ("err", "IndexError: list index out of range")


# ---------------------------------------------------------------------------
# Shadow: R/I transliteration of implementation_parseTagArgs (Lean).
# `toks` is the list of (kind, *) tuples mirroring `Tok`.
# ---------------------------------------------------------------------------
def msg_unexpected(name, param):
    return "'%s' received unexpected keyword argument '%s'" % (name, param)


def msg_multiple(name, param):
    return "'%s' received multiple values for keyword argument '%s'" % (name, param)


def msg_positional_after_kw(name):
    return ("'%s' received some positional argument(s) after some "
            "keyword argument(s)" % name)


def msg_too_many(name):
    return "'%s' received too many positional arguments" % name


def msg_missing(name, names):
    return ("'%s' did not receive value(s) for the argument(s): %s"
            % (name, ", ".join("'%s'" % p for p in names)))


def msg_context(name):
    return ("'%s' is decorated with takes_context=True so it must "
            "have a first argument of 'context'" % name)


def required_keyword_only(kwonly, kwonly_defaults):
    return [k for k in kwonly
            if not kwonly_defaults or k not in kwonly_defaults]


def shadow(toks, params, has_varargs, has_varkw, defaults_count, kwonly,
           kwonly_defaults, takes_context, name):
    params = list(params)
    if takes_context:
        if params and params[0] == "context":
            params = params[1:]
        elif params:
            return ("err", msg_context(name))
        else:
            # Mirror of Lean `Except.error msgIndexError`: the real routine's
            # uncaught IndexError on an empty declared-parameter list.
            return ("err", "IndexError: list index out of range")
    args = []
    kwargs = []  # ordered (key, value) assoc list
    pending_positional = list(params)
    pending_keyword = required_keyword_only(kwonly, kwonly_defaults)
    for tok in toks:
        if tok[0] == "keyword":
            param = tok[1]
            if (param not in params) and (param not in kwonly) and (not has_varkw):
                return ("err", msg_unexpected(name, param))
            elif any(k == param for k, _ in kwargs):
                return ("err", msg_multiple(name, param))
            else:
                kwargs.append((param, tok[2]))
                if param in pending_positional:
                    pending_positional.remove(param)
                elif param in pending_keyword:
                    pending_keyword.remove(param)
        else:  # positional
            if kwargs:
                return ("err", msg_positional_after_kw(name))
            else:
                args.append(tok[1])
                if not pending_positional:
                    if not has_varargs:
                        return ("err", msg_too_many(name))
                else:
                    pending_positional.pop(0)
    if defaults_count is not None:
        if defaults_count == 0:
            # `[:-0]` == `[:0]` == []: the Python negative-slice quirk — a
            # present-but-empty defaults tuple drops ALL pending positionals.
            pending = []
        else:
            # Truncated (Nat) subtraction, mirroring Lean `take (len - n)`.
            keep = max(0, len(pending_positional) - defaults_count)
            pending = pending_positional[:keep]
    else:
        pending = list(pending_positional)
    if pending or pending_keyword:
        return ("err", msg_missing(name, pending + pending_keyword))
    return ("ok", list(args), [(k, v) for k, v in kwargs])


# ---------------------------------------------------------------------------
# Bridge: toks -> bits.
# ---------------------------------------------------------------------------
def toks_to_bits(toks):
    bits = []
    for tok in toks:
        if tok[0] == "keyword":
            bits.append("%s=%s" % (tok[1], tok[2]))
        else:
            bits.append(tok[1])
    return bits


def rand_names(rng, lo, hi):
    n = rng.randint(lo, hi)
    return [rng.choice(NAME_POOL) for _ in range(n)]


def rand_toks(rng):
    n = rng.randint(0, 5)
    toks = []
    for _ in range(n):
        if rng.random() < 0.55:
            toks.append(("keyword", rng.choice(NAME_POOL), rng.choice(VALUE_POOL)))
        else:
            toks.append(("positional", rng.choice(VALUE_POOL)))
    return toks


def rand_case(rng):
    params = rand_names(rng, 0, 3)
    kwonly = rand_names(rng, 0, 3)
    has_varargs = rng.random() < 0.4
    has_varkw = rng.random() < 0.4
    # `defaults` is either None (no positional defaults) or a tuple of length
    # in [0 .. len(params)]. The empty tuple (count 0) is exercised too: the
    # real code's `unhandled_params[:-len(defaults)]` is then `[:-0]==[:0]`, the
    # negative-slice quirk that drops ALL pending names — modeled faithfully by
    # the shadow/Lean (`some 0` -> pending = []).
    if not params or rng.random() < 0.3:
        defaults_count = None
    elif rng.random() < 0.15:
        defaults_count = 0
    else:
        defaults_count = rng.randint(1, len(params))
    # kwonly_defaults: None ~40%, else a subset of kwonly
    if rng.random() < 0.4 or not kwonly:
        kwonly_defaults_keys = None
    else:
        k = rng.randint(0, len(kwonly))
        kwonly_defaults_keys = rng.sample(kwonly, k)
    takes_context = rng.random() < 0.3
    # A context-decorated tag normally declares its leading `context` parameter,
    # but the degenerate misconfiguration (takes_context with an EMPTY declared
    # parameter list, where the real parse_bits raises an uncaught IndexError at
    # `params[0]`) is now modeled explicitly (Lean `msgIndexError`), so the
    # differential DOES exercise it: keep the empty list ~20% of the time in
    # that configuration, ensure the common realizable shape the rest.
    if takes_context and not params and rng.random() < 0.8:
        params = ["context"]
    name = rng.choice(["hello", "hi", "simple_keyword_only_default",
                       "simple_keyword_only_param", "inclusion_keyword_only_default"])
    toks = rand_toks(rng)
    return (params, kwonly, has_varargs, has_varkw, defaults_count,
            kwonly_defaults_keys, takes_context, name, toks)


def to_python_inputs(params, kwonly, has_varargs, has_varkw, defaults_count,
                     kwonly_defaults_keys, takes_context, name, toks):
    """Build the concrete arguments parse_bits expects from the abstract case."""
    bits = toks_to_bits(toks)
    varargs = "args" if has_varargs else None
    varkw = "kwargs" if has_varkw else None
    if defaults_count is None:
        defaults = None
    else:
        defaults = tuple(range(defaults_count))  # only its length is read
    if kwonly_defaults_keys is None:
        kwonly_defaults = None
    else:
        kwonly_defaults = {k: 0 for k in kwonly_defaults_keys}
    return (bits, params, varargs, varkw, defaults, kwonly, kwonly_defaults,
            takes_context, name)


def main():
    rng = random.Random(12262)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        case = rand_case(rng)
        (params, kwonly, has_varargs, has_varkw, defaults_count,
         kwonly_defaults_keys, takes_context, name, toks) = case
        (bits, p, varargs, varkw, defaults, kwo, kwod, tc, nm) = to_python_inputs(*case)
        o = oracle(bits, p, varargs, varkw, defaults, kwo, kwod, tc, nm)
        s = shadow(toks, params, has_varargs, has_varkw, defaults_count, kwonly,
                   kwonly_defaults_keys, takes_context, name)
        if o != s:
            disagreements += 1
            if first is None:
                first = (case, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
