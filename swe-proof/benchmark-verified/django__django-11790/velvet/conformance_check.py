#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11790 (plan section 4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  -- the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md section 2
              bijection (Option Nat <-> (int | None); BoundedField's two facets
              <-> field.max_length and field.widget.attrs['maxlength']). The
              routine derives the effective limit (`resolveLimit`) and sets BOTH
              facets to it. There are no A-tagged callees in the impl, so the
              shadow is pure R/I.
  * ORACLE  -- `patch.diff`'s behaviour: the patched assignment block
                  username_max_length = self.username_field.max_length or 254
                  self.fields['username'].max_length = username_max_length
                  self.fields['username'].widget.attrs['maxlength'] = username_max_length
              executed verbatim over the model's configured limit (int or None),
              observing the resulting (field.max_length, widget maxlength) pair.
              The pre-existing field state (its prior max_length / widget attrs)
              is irrelevant: the patch overwrites max_length and inserts the
              maxlength attribute unconditionally. (The real end-to-end oracle is
              G-RESOLVE; this isolates the limit-assignment leg the Lean model
              pins.)

They must agree on every input over the configured-limit domain (None, or a
non-negative int -- Django's CharField.max_length is a PositiveInteger or None).
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md section 4) for a deterministic verdict.
"""
import random
import sys

SEED = 11790
N_FUZZ = 100_000


# --- the R/I shadow: resolveLimit + the two facet assignments, transliterated -
def resolve_limit(model_limit):
    """`resolveLimit (modelLimit : Option Nat)` transliterated:
        some n => if n = 0 then 254 else n
        none   => 254
    Over the mapping.md bijection Option Nat <-> (int | None)."""
    if model_limit is None:
        return 254
    return 254 if model_limit == 0 else model_limit


def shadow_configure(model_limit):
    """The impl region: derive the limit, then set BOTH length facets to it.
    Returns the observable (field.max_length, widget maxlength) pair."""
    limit = resolve_limit(model_limit)
    # result := { field with maxLength := some limit }
    # result := { result with widgetMaxLength := some limit }
    return (limit, limit)


# --- the ORACLE: the patched assignment block, executed verbatim -------------
def oracle_configure(model_limit):
    """patch.diff's three assignment lines, run exactly. `model_limit` is
    `self.username_field.max_length` (int or None)."""
    # gold hunk:
    username_max_length = model_limit or 254
    field_max_length = username_max_length            # fields['username'].max_length
    widget_maxlength = username_max_length             # widget.attrs['maxlength']
    return (field_max_length, widget_maxlength)


def fuzz_inputs(n, rng):
    # boundary first: unset, the zero/default edge, the F2P matrix values
    yield None         # IntegerUsernameUser: max_length is None -> default 254
    yield 0            # falsy int -> default 254 (Python `or`)
    yield 254          # the default value itself
    yield 255          # CustomEmailField F2P: max_length 255
    yield 1
    yield 75           # a CharField(max_length=75) seen elsewhere in the suite
    yield 150
    for _ in range(n):
        if rng.random() < 0.15:
            yield None
        else:
            yield rng.randint(0, 4096)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for model_limit in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_configure(model_limit)
        oracle = oracle_configure(model_limit)
        if shadow != oracle:
            disagreements.append((model_limit, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  model_limit=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of configureFieldLimit agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
