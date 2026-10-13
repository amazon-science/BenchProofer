# refinement.md — pytest-dev__pytest-7432

Operation correspondence between `implementation_skipLocationRewrite` and the
gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed and no A-reference callee exists: the changed
behavior (the location-rewrite decision being independent of the expected-failure
dispatch) is modeled DEEPLY as a pure Boolean control-flow decision over the
observable conditions the hook reads. Every row is **R** or **I**. The R/I legs
are differential-tested by G-CONF (exhaustive over the 128-point Boolean input
space plus seeded fuzz); G-AX is a skip stub (no consumed callee axiom).

## The gold patch

```python
             else:
                 rep.outcome = "passed"
                 rep.wasxfail = xfailed.reason
-    elif (
+
+    if (
         item._store.get(skipped_by_mark_key, True)
         and rep.skipped
         and type(rep.longrepr) is tuple
     ):
```

The patch turns the final `elif` of the expected-failure dispatch chain into a
standalone `if`, so the skip-location rewrite is no longer gated behind the
earlier dispatch arms (notably `elif item.config.option.runxfail: pass`). All
surrounding arms and the rewrite body are unchanged.

## `implementation_skipLocationRewrite` ↔ `pytest_runtest_makereport`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `(unexpSuccess … longreprIsTuple : Bool)` parameters | the conditions the hook tests: `unexpectedsuccess_key in item._store and rep.when=="call"`; `item.config.option.runxfail`; `call.excinfo and isinstance(call.excinfo.value, xfail.Exception)`; `not rep.skipped and xfailed`; `item._store.get(skipped_by_mark_key, True)`; `rep.skipped`; `type(rep.longrepr) is tuple` | R | each Python truth-condition ↦ a plain `Bool` observation (mapping.md type bijection) |
| `if unexpSuccess then pure () else if runxfail then pure () else if xfailRaised then pure () else if notSkippedXfail then pure ()` | the `if … elif item.config.option.runxfail: pass elif … elif …:` expected-failure dispatch chain | I | mutually-exclusive dispatch; none of these arms mutates the skip location. Bodies that mutate `rep.outcome`/`rep.wasxfail`/`rep.longrepr` for xfail are out of scope (they do not affect the modeled skip-location decision) and abstracted to `pure ()` |
| `if skippedByMark && repSkipped && longreprIsTuple then locationRewritten := true` | `if (item._store.get(skipped_by_mark_key, True) and rep.skipped and type(rep.longrepr) is tuple): … rep.longrepr = str(filename), line+1, reason` | I | the EDITED control-flow: the rewrite is now a standalone `if`, INDEPENDENT of the dispatch chain. The unchanged body (deriving `filename`, `line` from `item.reportinfo()` and reassigning `rep.longrepr`) always executes when the condition holds; whether it executes is the modeled observable `locationRewritten` |
| `let mut locationRewritten := false; … return locationRewritten` | "was `rep.longrepr` rewritten to the item location?" | R | the observable outcome ↦ `Bool` |

The result is the precise observable the F2P test checks: with `-rs --runxfail`
on a `@pytest.mark.skip` test, the skip summary must report
`test_sample.py:2: unconditional skip` (item location) — i.e. the rewrite fired.

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the rewrite is the FINAL `elif` arm of the dispatch
  chain (`else if skippedByMark && repSkipped && longreprIsTuple then …`), so it
  is suppressed whenever any earlier dispatch condition holds. For
  `runxfail = true` with the mark-skipped triple condition holding
  (`skippedByMark = repSkipped = longreprIsTuple = true`), the impl returns
  `false` while the spec demands `true`. The carried gold proof of
  `correct_skipLocationRewrite` (a `cases … <;> rfl` enumeration) fails to close
  on exactly that point. This is the single fixed behavior.
  (FAIL_TO_PASS: `TestXFail::test_xfail_run_with_skip_mark[test_input1-expected1]`,
  the `-rs --runxfail` case.)
