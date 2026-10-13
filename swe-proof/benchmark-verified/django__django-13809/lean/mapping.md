# mapping.md — django__django-13809

## Symbol binding (file:line @ base_commit bef6f7584280f1cc80e5e2d80b7ad073a93d26ec)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_serverStartup` / `problem_spec_serverStartup` | `Command.inner_run` of the `runserver` management command | `django/core/management/commands/runserver.py:107-158` |
| `skipChecks : Bool` | the `skip_checks` option (`options['skip_checks']`) | new `--skip-checks` argument (`runserver.py:add_arguments`, `runserver.py:37-53`) |
| `StartupAction` (pure helper) | one observable step the startup routine performs | see action table below |

The modeled function is the development server's startup routine (`inner_run`).
It is the only function whose behavior changes (the `add_arguments` change merely
registers the option that feeds `skip_checks`) and the only one observed by the
FAIL_TO_PASS test (`test_skip_checks`), which asserts:
* with `skip_checks=True`: the "Performing system checks..." announcement is
  absent from stdout **and** `self.check()` is not called;
* with `skip_checks=False`: the announcement is present **and** `self.check()` is
  called.

### What the routine does (base_commit)

```python
def inner_run(self, *args, **options):
    autoreload.raise_last_exception()
    threading = options['use_threading']
    shutdown_message = options.get('shutdown_message', '')
    quit_command = ...
    self.stdout.write("Performing system checks...\n\n")   # announce
    self.check(display_num_errors=True)                    # run checks
    self.check_migrations()                                # migration check
    now = datetime.now()...
    self.stdout.write(... banner ...)                      # banner
    try:
        handler = self.get_handler(*args, **options)
        run(self.addr, int(self.port), handler, ...)       # serve
    except OSError ...
```

At base_commit the system-check step (announcement + `self.check()`) is performed
**unconditionally**. The post-fix routine performs it only when `skip_checks` is
false:

```python
    if not options['skip_checks']:
        self.stdout.write('Performing system checks...\n\n')
        self.check(display_num_errors=True)
    self.check_migrations()
    ...
```

### `StartupAction` constructor ↔ Python expression bijection

We model the routine's observable behavior as the ordered list of side-effecting
steps it performs, abstracting away the steps that are pure setup / never
observed by the test (raising a deferred exception, reading options, computing
`quit_command`, the `try/except OSError` error-formatting). Only the steps whose
presence/order is observable as a behavior are carried; the test observes the
announcement and the check call, and the routine's fixed downstream order.

| `StartupAction` ctor | Python step | location | notes |
|---|---|---|---|
| `announceChecks` | `self.stdout.write("Performing system checks...\n\n")` | `runserver.py:117` (pre) / gated (post) | the announcement the test greps for. |
| `runChecks` | `self.check(display_num_errors=True)` | `runserver.py:118` (pre) / gated (post) | the system-check call the test asserts (not) called. |
| `checkMigrations` | `self.check_migrations()` | `runserver.py:121` | always performed, after the (optional) system-check step. |
| `writeBanner` | `self.stdout.write(... version/settings/addr/port ...)` | `runserver.py:123-135` | always performed; the startup banner. |
| `serve` | `run(self.addr, int(self.port), handler, ...)` | `runserver.py:139-140` | always performed; begins serving. |

### Input bijection

| Lean input | Python meaning |
|---|---|
| `skipChecks : Bool` | `options['skip_checks']` — truthiness of the new `--skip-checks` flag. `true` ⇒ the system-check step is omitted; `false` ⇒ it is performed (announcement then checks), ahead of the always-performed tail. |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| the ordered sequence of observable side-effecting steps `inner_run` performs | `List StartupAction` | each list element ↔ one observable step, in execution order. |
| `options['skip_checks']` (bool) | `skipChecks : Bool` | identity on the boolean control. |
| announcement write + `self.check()` call (the system-check step) | `[announceChecks, runChecks]` prefix | present iff `not skip_checks`. |
| `self.check_migrations()`, banner write, `run(...)` | `tailSteps = [checkMigrations, writeBanner, serve]` | the fixed downstream order, always emitted. |

The routine returns no value (it runs the server); we model it as a pure function
returning the observable action trace it emits up to the point it begins serving.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — gating the
  system-check step on the `skip_checks` control — is modeled DEEPLY as a gated
  list construction over the observable actions, not axiomatized (SPEC_GUIDE §3).
  The individual callees (`self.check`, `self.check_migrations`, `run`, the
  stdout writes) are not contracted by the proof; their *occurrence and order in
  the trace* is the modeled content, so there is no opaque callee whose contract
  the proof consumes. `axiom_check.py` is a skip stub.
- **Flag dependency.** The new `--skip-checks` argument (added in
  `add_arguments`) sets `options['skip_checks']`. Its truthiness is the only
  determinant of the trace; this is captured exactly by the `skipChecks` input.
  Note: `call_command(...)` defaults `skip_checks` to `True` when the caller does
  not pass it (`django/core/management/__init__.py`), but the F2P test passes it
  explicitly in both states, so both `skipChecks` values are exercised.
- **Always-performed tail.** `check_migrations`, the banner write, and `run`
  are emitted unconditionally in both pre- and post-patch code (directive 5:
  pinned to their fixed value in both branches of the spec).

## G-CONF fuzz seed

Pinned LCG seed: **13809** (see `conformance_check.py` `SEED`). The input domain
is the single boolean `skip_checks`; the corpus enumerates both values
exhaustively and additionally fuzzes ≥1e5 LCG-drawn booleans, diffing the R/I
shadow against an in-process replica of the post-patch control flow (system-check
step performed iff `not skip_checks`; fixed tail always performed).
