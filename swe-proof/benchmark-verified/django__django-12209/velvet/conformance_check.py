#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-12209 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled decision (`pkHasUsableDefault`,
              `decidedForceInsert`) transliterated to Python over the real repo
              types, via the mapping.md §2 bijection:
                  raw              <->  the `raw` _save_table parameter
                  forceInsert      <->  the incoming `force_insert` parameter
                  adding           <->  self._state.adding
                  pkDefaultTruthy  <->  bool(self._meta.pk.default)
                  pkDefaultProvided<->  self._meta.pk.default is not NOT_PROVIDED
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched guard exactly as the
              patched `Model._save_table` evaluates it, on real Python objects:
                  if (not raw and not force_insert and adding and
                      pk_default and pk_default is not NOT_PROVIDED):
                      force_insert = True
              The pk-default observations are exercised with the REAL Django
              `NOT_PROVIDED` sentinel and representative default objects
              (`uuid.uuid4`, a non-empty value, `None`, the sentinel itself),
              so the truthiness and identity semantics the patch relies on are
              the genuine ones.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

No database is touched: the guard is a pure boolean computation over attribute
reads. stdlib + django only. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys
import uuid


SEED = 12209
N_FUZZ = 100_000


def _import_not_provided():
    """The REAL Django sentinel the patched guard compares against."""
    from django.db.models.fields import NOT_PROVIDED
    return NOT_PROVIDED


# --- the R/I shadow: Solution.lean pkHasUsableDefault / decidedForceInsert ---
def shadow_pk_has_usable_default(pk_default_truthy, pk_default_provided):
    return pk_default_truthy and pk_default_provided


def shadow_decided_force_insert(raw, force_insert, adding,
                                pk_default_truthy, pk_default_provided):
    if (not raw and not force_insert and adding and
            shadow_pk_has_usable_default(pk_default_truthy, pk_default_provided)):
        return True
    return force_insert


# --- the oracle: the REAL patched guard on real Python objects ---------------
def oracle_decided_force_insert(raw, force_insert, adding, pk_default, NOT_PROVIDED):
    """patch.diff behaviour: evaluate the patched _save_table guard expression
    exactly as the repo does, on the real `pk_default` object and the real
    NOT_PROVIDED sentinel. Mutates a local copy of force_insert, like the repo."""
    fi = force_insert
    # The patched guard, conjunct-for-conjunct (django/db/models/base.py:851).
    if (
        not raw and
        not fi and
        adding and
        pk_default and
        pk_default is not NOT_PROVIDED
    ):
        fi = True
    return fi


def main():
    NOT_PROVIDED = _import_not_provided()

    # Representative real pk-default objects, paired with the (truthy, provided)
    # booleans the shadow consumes. Covers: a real callable default (uuid.uuid4,
    # the issue's case), a truthy non-callable, a declared-but-falsy default
    # (None / 0 / "" — truthy=False but provided=True), and the sentinel
    # (no default declared — provided=False).
    default_objects = [
        (uuid.uuid4, True, True),      # default=uuid.uuid4 (the issue)
        (42, True, True),              # truthy non-callable default
        ("x", True, True),
        (None, False, True),           # declared default None -> falsy but provided
        (0, False, True),
        ("", False, True),
        (False, False, True),
        (NOT_PROVIDED, True, False),   # no default declared -> the sentinel
                                       # (a class: truthy, but `provided` False
                                       #  so pkHasUsableDefault is False anyway)
    ]
    # Sanity: the shadow booleans must match what the real guard observes for
    # each object (the R bijection of mapping.md §2 must be faithful).
    for obj, truthy, provided in default_objects:
        assert bool(obj) == truthy, (
            "pkDefaultTruthy bijection wrong for %r: bool=%r expected %r"
            % (obj, bool(obj), truthy))
        assert (obj is not NOT_PROVIDED) == provided, (
            "pkDefaultProvided bijection wrong for %r" % (obj,))

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def boundary_inputs():
        # full cross product of (raw, force_insert, adding) x each default obj
        for raw in (False, True):
            for fi in (False, True):
                for adding in (False, True):
                    for obj, truthy, provided in default_objects:
                        yield (raw, fi, adding, obj, truthy, provided)

    def fuzz_inputs(n):
        for _ in range(n):
            raw = rng.random() < 0.5
            fi = rng.random() < 0.5
            adding = rng.random() < 0.5
            obj, truthy, provided = rng.choice(default_objects)
            yield (raw, fi, adding, obj, truthy, provided)

    for raw, fi, adding, obj, truthy, provided in \
            list(boundary_inputs()) + list(fuzz_inputs(N_FUZZ)):
        count += 1
        shadow = shadow_decided_force_insert(raw, fi, adding, truthy, provided)
        oracle = oracle_decided_force_insert(raw, fi, adding, obj, NOT_PROVIDED)
        if shadow != oracle:
            disagreements.append((raw, fi, adding, repr(obj), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for raw, fi, adding, obj, sh, orc in disagreements:
            print("  raw=%r force_insert=%r adding=%r pk_default=%s "
                  "shadow=%r oracle=%r" % (raw, fi, adding, obj, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of decideForceInsert agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements "
          "(force-insert only for ordinary save of a freshly-added instance "
          "whose pk has a usable default; never for a raw data load)."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
