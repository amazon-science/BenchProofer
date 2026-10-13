# mapping.md — pytest-dev__pytest-7432

## Symbol binding (file:line @ base_commit e6e300e729)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_skipLocationRewrite` / `problem_spec_skipLocationRewrite` / `correct_skipLocationRewrite` | the skip-location rewrite decision inside the report hook `pytest_runtest_makereport` | `src/_pytest/skipping.py:260-305` @ base_commit (edited line: the `elif (` at hunk line 294 → standalone `if (`) |
| `skipLocationCondition skippedByMark repSkipped longreprIsTuple` / the rewrite guard | `if (item._store.get(skipped_by_mark_key, True) and rep.skipped and type(rep.longrepr) is tuple):` | `src/_pytest/skipping.py:294-298` (pre-patch: `elif (…)`) |

The modeled function is `pytest_runtest_makereport`, a `hookwrapper` that
post-processes the test report `rep`. It runs a chain of mutually-exclusive
expected-failure cases, then (post-patch) an INDEPENDENT block that, for a result
skipped by a skip mark whose `longrepr` is a `(filename, line, reason)` tuple,
rewrites `rep.longrepr` so the reported location points at the test item
(`item.reportinfo()`), not at the internal site where the skip was raised:

```python
if unexpectedsuccess_key in item._store and rep.when == "call":
    ...                                  # rep.outcome = "failed"
elif item.config.option.runxfail:
    pass                                 # don't interfere
elif call.excinfo and isinstance(call.excinfo.value, xfail.Exception):
    ...
elif not rep.skipped and xfailed:
    ...
if (                                     # POST-PATCH: standalone `if` (was `elif`)
    item._store.get(skipped_by_mark_key, True)
    and rep.skipped
    and type(rep.longrepr) is tuple
):
    _, _, reason = rep.longrepr
    filename, line = item.reportinfo()[:2]
    rep.longrepr = str(filename), line + 1, reason
```

PRE-PATCH the rewrite was the trailing `elif` of the chain, so it only fired when
NONE of the earlier conditions held. `--runxfail` sets
`item.config.option.runxfail`, taking the `elif … runxfail: pass` arm, which
suppressed the rewrite even for a mark-skipped result — so the reported location
fell back to the internal `skipping.py` site, which is the reported bug.

The observable is whether the location rewrite fired. The F2P test runs a
`@pytest.mark.skip` test with `-rs --runxfail` and asserts the skip summary shows
the test's own location (`test_sample.py:2: unconditional skip`).

## Modeled decision / configuration

This bundle models the **control-flow decision** "was the skip-location rewrite
performed?" as a pure Boolean function of the conditions the hook reads. The
bodies that mutate `rep.outcome`/`rep.wasxfail`/`rep.longrepr` inside the
expected-failure arms, and the unchanged computation of the rewritten location
itself (`item.reportinfo()`, `line + 1`), are not altered by the patch and are
out of scope — only the *gating* of the rewrite changed, so only that decision is
modeled. This is precisely the behavior the F2P test discriminates.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python truth-condition | Lean | bijection |
|---|---|---|
| `unexpectedsuccess_key in item._store and rep.when == "call"` | `unexpSuccess : Bool` | `True ↦ true` |
| `item.config.option.runxfail` | `runxfail : Bool` | the `--runxfail` option flag |
| `call.excinfo and isinstance(call.excinfo.value, xfail.Exception)` | `xfailRaised : Bool` | a raised expected-failure signal |
| `not rep.skipped and xfailed` | `notSkippedXfail : Bool` | non-skipped result carrying an xfail mark |
| `item._store.get(skipped_by_mark_key, True)` | `skippedByMark : Bool` | skipped by a skip mark |
| `rep.skipped` | `repSkipped : Bool` | reported outcome is "skipped" |
| `type(rep.longrepr) is tuple` | `longreprIsTuple : Bool` | location is the structured triple |
| "was `rep.longrepr` rewritten to the item location?" | `result : Bool` | `True ↦ true` |

## Callee provenance + flag dependencies

- No callee axiom is consumed and no A-reference is declared. The changed
  behavior is a control-flow decision modeled DEEPLY as a pure Boolean function;
  per SPEC_GUIDE §3 a deeply-modeled changed decision is never axiomatized.
- Flag dependency: the discriminating input is `runxfail` (the `--runxfail`
  option). G-CONF enumerates the full 2**7 Boolean cube, so the
  `runxfail = true` × mark-skipped-triple case (the bug) is covered exhaustively.

## G-CONF fuzz seed

`SEED = 7432` (pinned in `conformance_check.py`).
