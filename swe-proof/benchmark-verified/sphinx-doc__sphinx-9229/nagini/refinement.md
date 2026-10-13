# refinement.md — sphinx-doc__sphinx-9229

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_doc_block` and `alias_additional_content` impl regions, plus the
`make_placeholder` / `placeholder_seq` axioms) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** where the proof uses the axiom's `Ensures`, **A-reference** where
a deep model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This is a **two-site** change; both sites are modeled as their own contracted
function (SPEC_GUIDE §3 "multiple changed functions"), and there is one
independently-failing `model_prepatch` per site (G-DIFF).

## Site A — `ClassDocumenter.get_doc` (`sphinx/ext/autodoc/__init__.py:1676`)

Gold hunk (alias branch):
```
   if self.doc_as_attr:
       # Don't show the docstring of the class when it is an alias.
-      return None
+      comment = self.get_variable_comment()
+      if comment:
+          return []
+      else:
+          return None
```
Model: `select_doc_block(is_attr_alias, comment, prepared)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `is_attr_alias: bool` | `self.doc_as_attr` | I | the same boolean alias flag. |
| A2 | `comment: List[int]` (read-only input) | `comment = self.get_variable_comment()` | R | `Optional[List[str]]` ↔ `List[int]`: the only consumed property is truthiness; `None`/`[]` (both falsy) collapse to the empty-list case (mapping.md §1, §2). `get_variable_comment`'s body (`list(attr_docs.get(key, []))` guarded by `PycodeError`) is the unchanged source-analysis lookup upstream of this parameter; modeled as the parameter, not axiomatized. |
| A3 | `if has_authored_comment(comment): return [] (a present empty List[int])` | `if comment: return []` | R + I | `has_authored_comment(comment) == len(comment) > 0` ↔ Python truthiness of the comment list (I on the branch logic). `[]` ↔ a present, non-None empty `List[int]` (R on the carrier). |
| A4 | `else: return None` | `else: return None` | I | the absent block. |
| A5 | `return prepared` (the non-alias path) | falls through to the unchanged remainder of `get_doc` that returns `[prepare_docstring(...) …]` | R | the non-alias branch is UNCHANGED by the patch; modeled as returning the read-only `prepared` carrier as-is (`Result() is prepared`). The carrier abstracts the unchanged prepared-docstrings value; no behaviour of that path is re-modeled. |

The discriminating content — alias **with** comment yields a PRESENT block
(`[]`, not `None`) — lives in clause **(1a)** of `select_doc_block`'s
postcondition. `model_prepatch.py` reverts the impl to the pre-patch
`if is_attr_alias: return None` and **fails** that clause
(`Result() is not None` does not hold), which is exactly the spec sensing the
change (G-DIFF).

## Site B — `ClassDocumenter.add_content` (`sphinx/ext/autodoc/__init__.py:1724`)

Gold hunk:
```
-  if self.doc_as_attr:
+  if self.doc_as_attr and not self.get_variable_comment():
       try:
           more_content = StringList([_('alias of %s') % restify(self.object)], source='')
       except AttributeError:
           pass
```
Model: `alias_additional_content(is_attr_alias, comment, target, more_content)`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `is_attr_alias and not has_authored_comment(comment)` | `self.doc_as_attr and not self.get_variable_comment()` | R + I | identical gating boolean (I); `not has_authored_comment(comment)` ↔ `not self.get_variable_comment()` is the falsy-comment test (R on the carrier, as A2). |
| B2 | `result = make_placeholder(target); return result` | `more_content = StringList([_('alias of %s') % restify(self.object)], source='')` | A-consumed | the synthetic placeholder is the unchanged formatter output; modeled by the `make_placeholder` / `placeholder_seq` axiom (the patch does not change this line, only re-gates it). The proof consumes `Ensures(ToSeq(Result()) == placeholder_seq(target))` and `len(placeholder_seq) > 0` (mapping.md §3.1). |
| B3 | `return more_content` (the else path) | the local `more_content` is left untouched and passed to `super().add_content(more_content)` | I + R | the pass-through (`Result() is more_content`) is the faithful skeleton of "the local is not reassigned" (I on the data flow); `Optional[StringList]` ↔ `Optional[List[int]]` (R on the carrier). |

The discriminating content — alias **with** comment leaves `more_content`
untouched (no placeholder substituted) — lives in clause **(2b)**. The
`try/except AttributeError` of the gold (a defensive guard for an invalid class
object) is NOT a behaviour the change introduces and is not exercised by the
F2P/P2P tests (all targets are valid classes), so it is not modeled; the placeholder
is always producible for the tested targets (its `restify` succeeds), which the
non-emptiness axiom captures. `model_prepatch_2.py` reverts the gate to
`if is_attr_alias:` and **fails** clause (2b)
(`Result() is more_content` does not hold for an alias with a comment), the spec
sensing site B's change (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The two operations that genuinely
*changed* are the two gating decisions (which block `get_doc` selects; whether
`add_content` substitutes the placeholder) — both modeled **deeply** as explicit
branch logic on `has_authored_comment`, NOT hidden behind an axiom about the
functions under change. The only consumed axiom, `make_placeholder` /
`placeholder_seq` (**A-consumed**, site B), covers the **unchanged** line
formatter (`'alias of %s' % restify(...)` wrapped in `StringList`) the new code
still invokes; the patch only re-gates when it runs. There is no A-reference
deep model (no whole-string fold is re-validated against a stdlib callee here).

## D. verify(model) ⇒ resolved

`select_doc_block` verifies only if an alias with a comment selects a PRESENT
block and an alias without a comment selects the ABSENT block (clauses 1a/1b),
and the non-alias path is unchanged (1c). `alias_additional_content` verifies
only if the placeholder is substituted exactly when the alias has no comment
(2a) and the incoming content is passed through otherwise (2b). By R (the
`Optional[List[str]]`/`StringList`/`List[List[str]]` ↔ `Optional[List[int]]`
carrier bijections and the truthiness equivalence), these two verified functions
are the two gold hunks; by A-consumed the substituted line is the unchanged
`'alias of %s' % restify(...)` formatter (G-AX confirms its non-emptiness).
Therefore an implementation satisfying this spec, refined by the map above, is
the gold patch up to type refinement and one audited callee — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
