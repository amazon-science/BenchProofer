#!/usr/bin/env python3
"""G-AX for django__django-13028 — SKIP STUB.

The modeled function `Query.check_filterable` consumes no unchanged external
callee axiom: it calls only the builtins `getattr`/`hasattr` and the object's
own `get_source_expressions`, and recurses on itself. All of these are modeled
structurally over the `Expr` carrier in Solution.lean (see refinement.md /
mapping.md), so there is no `axiom <callee>_prop` to validate.

stdlib-only; emits a JSON status=skip and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "gate": "G-AX",
        "instance": "django__django-13028",
        "status": "skip",
        "reason": "no consumed callee axiom; decision modeled structurally",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
