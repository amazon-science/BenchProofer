#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-22719 — skip stub.

The bundle consumes NO unchanged-callee axiom. The single `opaque` declaration,
`looksNumeric` (= `UnitData._str_is_convertible`), is declared for SIGNATURE only
so it can appear in the executable impl: the notification decision depends only on
the sequence-level conjunction of its per-element results and on the sequence
length, never on its value for any particular string. The proof consumes no
`looksNumeric_prop` property, so there is no callee contract to validate against
the real repo beyond totality (which is its declared Lean type, `String → Bool`).
The behavior the patch changes — gating each notification on the sequence being
non-empty (`values.size` / `data.size`) — is modeled DEEPLY as `!_.isEmpty && …`
over the observable inputs, which SPEC_GUIDE §3 forbids axiomatizing. The R legs
are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-22719",
    "reason": "no consumed callee axiom; the one opaque callee is signature-only "
              "(A-reference, cancels in the decision) and the changed guard is "
              "modeled deeply; impl is all R/I (validated by G-CONF)",
}))
sys.exit(0)
