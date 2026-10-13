#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-12262 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of the single modeled function
`bindTagArguments` (the per-bit argument-binding scan of
`django.template.library.parse_bits` + its final missing-argument check). There
are NO axioms in this bundle: the two callees the scan consults
(`token_kwargs([bit], parser)` and `parser.compile_filter(bit)`) are UNCHANGED
and folded into the free input `bits` (each bit pre-classified as keyword/name or
positional). So the whole impl region is R/I (conf_skip=false).

  * SHADOW  — Solution.lean's `stepBit` / `finalize` / `parseBits` model,
              transliterated to Python over the mapping.md bijection
              (`unhandled_kwargs` ↔ `pendingKeywordOnly`, `kwonly` ↔
              `keywordOnlyParams`, `kwargs` keys ↔ `recorded`, the raised error
              ↔ an `Err` tag, success ↔ None).
  * ORACLE  — `patch.diff`'s behaviour: the GOLD-PATCHED `parse_bits` per-bit
              loop + final check, transliterated VERBATIM with the fixed line
              `param not in kwonly` and the real control flow:

                  args, kwargs = [], {}
                  unhandled_params = list(params)
                  unhandled_kwargs = [k for k in kwonly
                                      if not kwonly_defaults or k not in kwonly_defaults]
                  for bit in bits:                      # bit pre-classified
                      if bit.is_keyword:
                          param = bit.name
                          if param not in params and param not in kwonly and varkw is None:
                              return ('unexpected', param)
                          elif param in kwargs:
                              return ('duplicate', param)
                          else:
                              kwargs[param] = ...
                              if param in unhandled_params:
                                  unhandled_params.remove(param)
                              elif param in unhandled_kwargs:
                                  unhandled_kwargs.remove(param)
                      else:
                          if kwargs:
                              return ('positional_after_keyword', None)
                          else:
                              if unhandled_params:
                                  unhandled_params.pop(0)
                              elif varargs is None:
                                  return ('too_many_positional', None)
                  if defaults is not None:
                      unhandled_params = unhandled_params[:-len(defaults)]
                  if unhandled_params or unhandled_kwargs:
                      return ('missing', unhandled_params + unhandled_kwargs)
                  return None

ORACLE CHOICE — why we transliterate the patched loop instead of running the
real `parse_bits`:
  Exercising the real `parse_bits` requires a live template Parser, a
  FilterExpression compiler, and `token_kwargs` token parsing — i.e. the F2P
  Django template harness — purely to read back which TemplateSyntaxError (if
  any) is raised. The two callees it invokes (`token_kwargs`, `compile_filter`)
  are UNCHANGED by the patch and only (a) classify a bit as keyword/positional
  and (b) build the stored value; neither the value nor any token-parsing detail
  enters the binding/error decision beyond that classification. So we abstract
  them into pre-classified bits (mapping.md §3) and take the gold-patched
  decision logic, transliterated verbatim, as the oracle.

We differential-test SHADOW vs ORACLE over the F2P boundary scenarios named in
the issue/test_patch plus 10^5 fuzzed configurations (random parameter lists,
flags, defaults, and bit sequences). Exit 0 iff zero disagreements. stdlib only.
"""
import random
import sys

SEED = 12262
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean (stepBit / finalize / parseBits) transliterated ----
# A bit is ('kw', name) or ('pos',). Error outcomes are tuples matching `Err`:
#   ('unexpected', p) ('duplicate', p) ('positional_after_keyword', None)
#   ('too_many_positional', None) ('missing', [names])   ; None == success.

def shadow_parse(bits, positional_params, keyword_only_params,
                 keyword_only_defaults, accepts_extra_keywords,
                 accepts_extra_positional, has_defaults, num_defaults):
    recorded = []
    pending_positional = list(positional_params)
    pending_keyword_only = [k for k in keyword_only_params
                            if k not in keyword_only_defaults]
    error = None
    for bit in bits:
        if error is not None:
            break  # inert once an error is recorded (real scan stops)
        if bit[0] == 'kw':
            p = bit[1]
            # FIXED test: full declared keyword-only set.
            if (p not in positional_params and p not in keyword_only_params
                    and not accepts_extra_keywords):
                error = ('unexpected', p)
            elif p in recorded:
                error = ('duplicate', p)
            else:
                recorded = recorded + [p]
                if p in pending_positional:
                    pending_positional = _erase(pending_positional, p)
                elif p in pending_keyword_only:
                    pending_keyword_only = _erase(pending_keyword_only, p)
        else:  # positional
            if recorded:
                error = ('positional_after_keyword', None)
            else:
                if not pending_positional:
                    if not accepts_extra_positional:
                        error = ('too_many_positional', None)
                else:
                    pending_positional = pending_positional[1:]
    # finalize
    if error is not None:
        return error
    if has_defaults:
        # Lean `List.take (length - numDefaults)` — Nat TRUNCATED subtraction
        # (clamps at 0), matching the oracle's `unhandled_params[:-len(defaults)]`
        # which yields [] once len(defaults) exceeds the remaining pending count.
        keep = max(0, len(pending_positional) - num_defaults)
        leftover = pending_positional[:keep]
    else:
        leftover = pending_positional
    missing = leftover + pending_keyword_only
    if not missing:
        return None
    return ('missing', list(missing))


def _erase(xs, x):
    """List.erase: drop first occurrence."""
    out = list(xs)
    if x in out:
        out.remove(x)
    return out


# ---- ORACLE: gold-patched parse_bits decision logic, verbatim ---------------

def oracle_parse(bits, positional_params, keyword_only_params,
                 keyword_only_defaults, accepts_extra_keywords,
                 accepts_extra_positional, has_defaults, num_defaults):
    # params / kwonly / kwonly_defaults / varkw / varargs / defaults bound to the
    # abstracted inputs (mapping.md §2). takes_context stripping is already folded
    # into positional_params (mapping.md §4).
    params = list(positional_params)
    kwonly = list(keyword_only_params)
    kwonly_defaults = set(keyword_only_defaults)
    varkw_is_none = not accepts_extra_keywords
    varargs_is_none = not accepts_extra_positional

    kwargs = {}
    unhandled_params = list(params)
    unhandled_kwargs = [k for k in kwonly
                        if not kwonly_defaults or k not in kwonly_defaults]
    for bit in bits:
        if bit[0] == 'kw':
            param = bit[1]
            # GOLD-PATCHED line:
            if param not in params and param not in kwonly and varkw_is_none:
                return ('unexpected', param)
            elif param in kwargs:
                return ('duplicate', param)
            else:
                kwargs[param] = True
                if param in unhandled_params:
                    unhandled_params.remove(param)
                elif param in unhandled_kwargs:
                    unhandled_kwargs.remove(param)
        else:
            if kwargs:
                return ('positional_after_keyword', None)
            else:
                try:
                    unhandled_params.pop(0)
                except IndexError:
                    if varargs_is_none:
                        return ('too_many_positional', None)
    if has_defaults:
        # defaults is a non-empty tuple of length num_defaults
        unhandled_params = unhandled_params[:-num_defaults] if num_defaults else unhandled_params
    if unhandled_params or unhandled_kwargs:
        return ('missing', unhandled_params + unhandled_kwargs)
    return None


# ---- F2P boundary scenarios (issue + test_patch) ---------------------------
# Names as small ints (opaque). greeting=1, kwarg=1, one=2, two=3.

BOUNDARY = [
    # (label, bits, pos, kwonly, kwdef, varkw, varargs, hasdef, ndef)
    # simple_keyword_only_default kwarg=37  -> success (kwarg has a default)
    ("kw_only_default_supplied", [('kw', 1)], [], [1], [1], False, False, False, 0),
    # simple_keyword_only_default (no arg)  -> success
    ("kw_only_default_omitted", [], [], [1], [1], False, False, False, 0),
    # simple_keyword_only_param (no arg)    -> missing 'kwarg'
    ("kw_only_required_omitted", [], [], [1], [], False, False, False, 0),
    # simple_keyword_only_param kwarg=42 kwarg=37 -> duplicate
    ("kw_only_required_twice", [('kw', 1), ('kw', 1)], [], [1], [], False, False, False, 0),
    # simple_keyword_only_default kwarg=42 kwarg=37 -> duplicate
    ("kw_only_default_twice", [('kw', 1), ('kw', 1)], [], [1], [1], False, False, False, 0),
    # genuinely unexpected keyword (not declared, no **kwargs)
    ("genuinely_unexpected", [('kw', 9)], [], [1], [1], False, False, False, 0),
    # accepted via **kwargs
    ("extra_via_varkw", [('kw', 9)], [], [1], [1], True, False, False, 0),
    # one positional default: simple_one_default 37 -> success; two has default
    ("one_default_one_pos", [('pos',)], [2, 3], [], [], False, False, True, 1),
    # simple_one_default (no args) -> missing 'one'
    ("one_default_none", [], [2, 3], [], [], False, False, True, 1),
    # too many positionals
    ("too_many_pos", [('pos',), ('pos',)], [2], [], [], False, False, False, 0),
    # positional after keyword
    ("pos_after_kw", [('kw', 1), ('pos',)], [2], [1], [1], False, False, False, 0),
    # keyword used for a positional param (consumes it)
    ("kw_for_positional", [('kw', 2)], [2], [], [], False, False, False, 0),
]


def run_boundary():
    bad = []
    for case in BOUNDARY:
        label, args = case[0], case[1:]
        s = shadow_parse(*args)
        o = oracle_parse(*args)
        if s != o:
            bad.append((label, s, o))
    return bad


# ---- Fuzz ------------------------------------------------------------------

def run_fuzz(rng, n):
    bad = []
    checks = 0
    NAME_POOL = list(range(6))  # small pool to force collisions/dups
    for _ in range(n):
        # random declared parameter sets (disjoint-ish, drawn from the pool)
        names = rng.sample(NAME_POOL, k=rng.randint(0, len(NAME_POOL)))
        rng.shuffle(names)
        cut = rng.randint(0, len(names))
        positional_params = names[:cut]
        keyword_only_params = names[cut:]
        # some keyword-only params carry defaults
        keyword_only_defaults = [k for k in keyword_only_params if rng.random() < 0.5]
        accepts_extra_keywords = rng.random() < 0.4
        accepts_extra_positional = rng.random() < 0.4
        has_defaults = bool(positional_params) and rng.random() < 0.5
        num_defaults = rng.randint(1, len(positional_params)) if has_defaults and positional_params else 0
        if num_defaults == 0:
            has_defaults = False
        # random bit sequence
        nbits = rng.randint(0, 6)
        bits = []
        for _ in range(nbits):
            if rng.random() < 0.6:
                bits.append(('kw', rng.choice(NAME_POOL)))
            else:
                bits.append(('pos',))
        args = (bits, positional_params, keyword_only_params,
                keyword_only_defaults, accepts_extra_keywords,
                accepts_extra_positional, has_defaults, num_defaults)
        s = shadow_parse(*args)
        o = oracle_parse(*args)
        checks += 1
        if s != o:
            bad.append((args, s, o))
            if len(bad) >= 8:
                break
    return bad, checks


def main():
    rng = random.Random(SEED)
    bad_b = run_boundary()
    if bad_b:
        print("G-CONF FAIL (boundary): %r" % (bad_b,))
        return 1
    bad_f, checks = run_fuzz(rng, N_FUZZ)
    if bad_f:
        print("G-CONF FAIL: %d disagreement(s): %r" % (len(bad_f), bad_f[:8]))
        return 1
    print("G-CONF OK: R/I shadow of bindTagArguments agrees with the gold-patched "
          "parse_bits decision logic on %d checks (%d boundary F2P scenarios + %d "
          "fuzz, seed=%d), 0 disagreements."
          % (len(BOUNDARY) + checks, len(BOUNDARY), checks, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
