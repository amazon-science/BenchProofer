#!/usr/bin/env python3
"""G-AX for django__django-13121 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled strategy-selection decision (`expressionSqlStrategy`) is all R (validated
by G-CONF). It is a pure function of the two operand field types, whether the
operator is subtraction, and whether the backend natively supports durations —
all plain data per mapping.md. The three downstream SQL-generation strategies
(`DurationExpression.as_sql`, `TemporalSubtraction.as_sql`, the generic
`combine_expression` path) are observed only as the IDENTITY of the strategy
chosen at this site, never invoked or contracted. There is therefore no callee
contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13121",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
