#!/usr/bin/env python3
"""G-AX for sympy__sympy-19495 — SKIP STUB.

The modeled branch is spelled out deeply in `implementation_freeSubs`: it keeps
the original bound variable and applies the ordinary symbolic substitution
(`subsCond` at the `Boolean` condition, `subsSet` at the `Set` base) — two names
for the one genuine, unchanged substitution callee `Basic.subs`, taken at the two
kinds it is applied to — then hands the three components to the genuine, unchanged
set-assembly callee `ConditionSet.__new__` (`mkSet` ↔ `self.func`). All three are
A-REFERENCES, exercised in-process and validated against the real behavior by
G-CONF (conformance_check.py), not consumed contracts. Each is OPAQUE with no
constraining axiom: `mkSet` in particular is opaque in both directions, since its
result carrier `AsmSet` exposes no components — the real routine canonicalises, so
an assembled set need not have any — and is accepted by no routine, since the real
routines are undefined or re-entrant on an assembled set (G-CONF LEG 5).

The three remaining opaque names are in the same position. `symExpr` is the
inclusion of the bound-variable kind into the expression kind, which on the
modeled side is the identity (a `Symbol` already IS an expression), so there is no
behavior for an axiom to describe. `isTrue` (`is S.true`) and `mkMemberSet`
(`ConditionSet(v, Contains(v, base), base)`, one fused routine — see mapping.md
§"Carrier discipline") are reached only by the prepatch impl and by rivals, are
likewise unconstrained, and their domains are measured by G-CONF's LEG 2/LEG 3/LEG
5 rather than asserted by an axiom.

There are no `axiom <callee>_prop` declarations in Solution.lean for the proof to
consume, so there is nothing for G-AX to validate. Exit 0 with status=skip.
stdlib-only. (If the proof agent later introduces a `_prop` axiom, this stub is
replaced with the corresponding executable check.)
"""
import json
import sys

print(json.dumps({"status": "skip",
                  "reason": "no consumed axioms; mkSet/subsCond/subsSet are A-references validated by G-CONF"}))
sys.exit(0)
