# mapping.md — django__django-13809

Binds every `model.py` symbol to its repository counterpart at
`base_commit = bef6f7584280f1cc80e5e2d80b7ad073a93d26ec`, states the type
abstraction, and gives the provenance of the standard-library `argparse`
semantics the deep model is validated against (G-AX / axiom_check.py). There
are NO consumed axioms.

Repo file under change: `django/core/management/commands/runserver.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `offers_skip_request()` | the `--skip-checks` registration added to `Command.add_arguments` — `parser.add_argument('--skip-checks', action='store_true', help='Skip system checks.')` (`django/core/management/commands/runserver.py:54-57`, post-patch; inserted after the `--noreload` argument at :51-53) | modeled changed site (1): this command offers the skip request on its own invocation parser, unconditionally |
| `startup_action_schedule(skip_checks)` | the start-up validation gate in `Command.inner_run` — the `self.stdout.write("Performing system checks...")` + `self.check(display_num_errors=True)` pair, now guarded by `if not options['skip_checks']:`, followed by the always-run `self.check_migrations()` (`django/core/management/commands/runserver.py:117-121`, pre-patch / :121-126 post-patch) | modeled changed site (2): which start-up actions are emitted given the skip request |
| `ACTION_ANNOUNCE_VALIDATION` (=1) | `self.stdout.write("Performing system checks...\n\n")` (`runserver.py:117` pre-patch) | the announcement action, inside the suppressible pass |
| `ACTION_RUN_VALIDATION` (=2) | `self.check(display_num_errors=True)` (`runserver.py:118` pre-patch) | the validation-run action, inside the suppressible pass |
| `ACTION_MIGRATION_RECHECK` (=3) | `self.check_migrations()` (`runserver.py:121` pre-patch) | the migration re-check, OUTSIDE the guard (always emitted) |
| `skip_checks` (bool param) | the `--skip-checks` token present on the command line → `options['skip_checks'] is True` | invocation-level input: did the operator ask to skip the start-up validation pass |

Why this command needs its own registration (the non-obvious bit, for the
audit, not the consumer spec view): the common machinery
(`BaseCommand.create_parser`, `base.py:315-319`) only adds `--skip-checks` when
`self.requires_system_checks` is truthy. This command sets
`requires_system_checks = []` (`runserver.py:28`) — falsy — so the common
machinery never offers the option for it, and it never runs the common
pre-pass validation. Instead it validates explicitly in `inner_run`. Hence the
fix must (a) register `--skip-checks` on this command's own parser
unconditionally, and (b) guard the explicit `inner_run` validation by the
resulting `options['skip_checks']`. Sites (1) and (2) above are exactly these.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `--skip-checks` token present on the command line | `skip_checks: bool` | token present ↔ `skip_checks == True`; equals `options['skip_checks']` (argparse `store_true`) |
| `options['skip_checks']` (the parsed namespace value) | `skip_checks: bool` (param of `startup_action_schedule`) | the parsed namespace always carries the value once the option is registered (always, here): `False` token-absent, `True` token-present |
| `parser.add_argument('--skip-checks', ...)` is reached unconditionally | `offers_skip_request() == True` | the option is registered ↔ the parser offers the request; registered with no guard ↔ offered unconditionally |
| `self.stdout.write("Performing system checks...")` executed | `ACTION_ANNOUNCE_VALIDATION` present in `Result()` | the announcement side-effect ↔ its action code emitted |
| `self.check(display_num_errors=True)` invoked | `ACTION_RUN_VALIDATION` present in `Result()` | the validation invocation ↔ its action code emitted |
| `self.check_migrations()` invoked | `ACTION_MIGRATION_RECHECK` present in `Result()` | the migration re-check (always) ↔ its action code emitted |
| the start-up control flow `if not options['skip_checks']: write; check; / check_migrations` | the order/contents of `Result()` | the emitted action codes, in start-up order, are the observable schedule the F2P test inspects (message text present + `check` call count) |

`argparse` `store_true` yields `False` by default and `True` when the token is
present; the option is registered with no guard, so it is always accepted for
this command.

## 3. Callee / library-semantics provenance (A-reference — checked by G-AX)

No `@ContractOnly` axiom is consumed. The deep model rests on two semantic
facts about the standard-library argument parser the gold patch builds on
(`argparse`, which Django's `CommandParser` subclasses unchanged). These are
the A-reference obligations validated by `axiom_check.py` against the REAL
`argparse` (stdlib-only import):

### 3.1 Unconditional skip-option exposure ↔ the `add_arguments` hunk (A-reference for `offers_skip_request`)
**Callee:** `argparse.ArgumentParser.add_argument` / `parse_args`. The gold
`Command.add_arguments` registers `--skip-checks` (`action='store_true'`) with
NO guard. A parser built that way always exposes `skip_checks` in its parsed
namespace, defaulting to `False` when the token is absent and `True` when
present. Hence `offers_skip_request() == True` (unconditional).
Source: gold hunk `django/core/management/commands/runserver.py:54-57`; CPython
`Lib/argparse.py` (`store_true` action, `parse_args`); docs
https://docs.python.org/3/library/argparse.html#action (`'store_true'`).

### 3.2 The start-up gate ↔ the `inner_run` hunk (A-reference for `startup_action_schedule`)
**Callee:** `argparse` `store_true` default/presence + the gold `inner_run`
control flow. The gold guards the announcement + validation run by
`if not options['skip_checks']:` and leaves `self.check_migrations()` outside
the guard. Modeled by `startup_action_schedule`: the announce/run actions are
emitted iff `not skip_checks`; the migration re-check is always emitted.

**Soundness check (G-AX):** `axiom_check.py` builds a real `argparse` parser
mirroring the gold `add_arguments` (unconditional `--skip-checks` registration),
then asserts: (a) `skip_checks` is present in the parsed namespace and defaults
to `False` (token absent) / `True` (token present) (R1); and (b) the real
end-to-end start-up gate (`if not options['skip_checks']: announce; run` then
always `migration re-check`) emits an action schedule equal to the model's
`startup_action_schedule` over both token values (R2), with action-level
assertions that neither validation action survives under a skip request and
that the migration re-check survives regardless. Exit 0 iff sound. It imports
only the standard-library `argparse` — the module the gold patch builds on.

## 4. Non-modeled, behaviour-irrelevant detail

The gold `test_patch` also resets `autoreload._exception = None` in
`tests/utils_tests/test_autoreload.py` (a test-isolation fix so the new mock-
based `test_skip_checks`, which patches `run`/`check_migrations`/`check`, does
not leave a captured exception for later tests). It is part of the harness-
applied `test_patch`, not the gold source `patch`, and is pure test plumbing —
not modeled and not in `patch.diff`.
