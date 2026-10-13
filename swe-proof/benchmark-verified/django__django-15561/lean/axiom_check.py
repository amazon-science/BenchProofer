#!/usr/bin/env python3
"""G-AX — callee-axiom soundness for django__django-15561.

SKIP STUB. The modeled function (`_field_should_be_altered`) consumes NO callee
axiom property in its correctness proof:

  * The only unchanged callee it invokes is `quote_name` (identifier quoting),
    declared `opaque quoteIdentifier : String → String` and applied IDENTICALLY
    on both sides of the column-name comparison in BOTH `problem_spec` and
    `implementation`. The proof therefore needs no property of it (it cancels
    syntactically); it is an A-reference, not an A-consumed axiom.
  * Every other operation (deconstruct components, the ignored-attribute pop, the
    structural tuple comparison) is modeled DEEPLY in the spec, so there is no
    `axiom <callee>_prop` to validate.

There is consequently nothing for G-AX to run. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no callee axioms declared (behavior modeled deeply; "
          "quote_name is an A-reference applied identically both sides)")
    sys.exit(0)
