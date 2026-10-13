#!/usr/bin/env python3
"""G-CONF for django__django-13012 — skip stub (conf_skip=true).

The impl region (`implementation_wrapperGroupByCols`) is composed ENTIRELY of a
single A-reference op (refinement.md): `return e.innerCols`, which mirrors the
patched method's verbatim delegation
`return self.expression.get_group_by_cols(alias=alias)`. The inner expression's
`get_group_by_cols` is the unchanged real callee, modeled deeply as the input
field `e.innerCols`. There is no standalone R/I data transformation whose Python
shadow could be built without re-implementing the real inner callee, so there is
nothing for a cross-language differential test to exercise.

Per the worker spec, an all-A-tagged impl sets meta.json conf_skip=true and ships
this skip stub.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13012",
    "reason": "impl region is a single A-reference op (verbatim forward of the "
              "wrapped expression's group-by columns); no standalone R/I op to "
              "transliterate for a cross-language differential test",
}))
sys.exit(0)
