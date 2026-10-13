#!/usr/bin/env python3
"""G-AX for django__django-15525.

This bundle declares NO `axiom <callee>_prop`, so there is no consumed-axiom
over-approximation for this gate to validate against the real repo callee.
What the correctness proof of `correct_resolveRecord` consumes is of two kinds,
neither of which is an axiom:

  * `lookupByKey` and `coerceId` are opaque constants that appear term-identically
    in BOTH `problem_spec_resolveRecord` and `implementation_resolveRecord`. The
    proof only case-splits on the lookup's result; it relies on no functional
    property of either.

  * the key-derivation step is not a global constant at all — it is an ARGUMENT
    (`derive : KeyDerivation`), and what the proof assumes about it
    (`derivationAvailability data store hasKey derive`: a key comes back under
    `hasKey` for the record assembled on the target store, nothing comes back
    when `hasKey` is false, and nothing at all is assumed about the step on any
    other record) is a THEOREM HYPOTHESIS of `correct_resolveRecord`, discharged
    by whoever instantiates the obligation rather than asserted by the bundle. An
    unsatisfiable hypothesis would make the obligation vacuous, so that risk is
    carried where it can be measured: `properties.py` case
    `admiss-f2p-shaped-input` PROVES the hypothesis at a concrete F2P-shaped
    point and discharges all four postcondition clauses there.

The three properties of the real callee the spec leans on — the derivation's
store-dependence, its partiality in the model (`AttributeError`) and its
partiality in the store (`DoesNotExist` off the target alias) — are validated by
G-CONF, which drives the R/I skeleton and a transcription of the patched control
flow over all three (see `conformance_check.py`, including its two negative
controls).

Exit 0 (skip): no consumed callee-property axiom exists for this bundle.
"""
import json
import sys

print(json.dumps({
    "gate": "G-AX",
    "instance": "django__django-15525",
    "status": "skip",
    "reason": ("no `_prop` callee axiom: `lookupByKey`/`coerceId` are opaque "
               "constants appearing identically in spec and impl (proof "
               "consumes only term-identity, no property), and what the proof "
               "assumes about the key-derivation step is a THEOREM HYPOTHESIS "
               "(`derivationAvailability` on the `derive` argument), not an "
               "axiom declaration; its satisfiability is exhibited by the "
               "G-PBT admissibility case and the callee's store-dependence and "
               "partiality are validated by G-CONF."),
}))
sys.exit(0)
