# mapping.md — django__django-13809

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = bef6f7584280f1cc80e5e2d80b7ad073a93d26ec`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and the pinned G-CONF fuzz seed.

Repo file under change: `django/core/management/commands/runserver.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `runStartupChecks (skipChecks) (mut announced) (mut checked)` | the system-checks block of `Command.inner_run(self, *args, **options)` — `django/core/management/commands/runserver.py:107` (block at lines 117–118, post-patch guarded at 117–120) | the modeled changed function: the startup-time system-checks gating |
| `skipChecks : Bool` (read-only param) | `options['skip_checks']` — the value of the `--skip-checks` request flag (registered by `add_arguments`, `runserver.py:50` post-patch; for non-runserver commands the same flag is registered by `BaseCommand.add_arguments`, `base.py:315`) | request flag: skip the system checks |
| `announced : Bool` (mut observable) | the occurrence of `self.stdout.write("Performing system checks...\n\n")` — `runserver.py:117` | effect-1 observable: the progress announcement was emitted |
| `checked : Bool` (mut observable) | the occurrence of `self.check(display_num_errors=True)` — `runserver.py:118` | effect-2 observable: the system-check routine was invoked |

The companion gold hunk in `add_arguments` (`runserver.py:50–53` post-patch)
registers the `--skip-checks` argparse option (`action='store_true'`). It is a
**declarative argument registration** with no algorithmic content: it only makes
`options['skip_checks']` available to `inner_run`. It is the source of the
`skipChecks` input and is not separately modeled (nothing to compute or pin); its
effect is fully captured by `skipChecks` being a free boolean input to the
modeled routine. See refinement.md §B.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `options['skip_checks']` (argparse `store_true` flag — always a bool) | `skipChecks : Bool` | Python `bool` ↔ Lean `Bool`; `True ↔ true`, `False ↔ false`. `store_true` guarantees the key is present and boolean (default `False`). |
| "the announcement `self.stdout.write("Performing system checks...\n\n")` executed" | `announced : Bool` | occurrence flag: `True`/`true` iff that statement ran on this invocation. The F2P test observes it via `self.assertIn/assertNotIn('Performing system checks...', output)`. |
| "the invocation `self.check(display_num_errors=True)` executed" | `checked : Bool` | occurrence flag: `True`/`true` iff `self.check(...)` was called. The F2P test observes it via the mocked `check.assert_called()` / `assert_not_called()`. |

Entry state: at the point in `inner_run` reached just before the system-checks
block, neither effect has happened yet — so `announced = false`, `checked =
false` on entry (the two `require` clauses). This matches the per-invocation
truncation in the F2P test (`self.output.truncate(0)` between the two calls, and
a fresh `mocked_check` assertion regime per call).

The argument value `display_num_errors=True` passed to `self.check` is NOT
modeled: the bundle pins only WHETHER `check` is invoked, not what it computes
(the check routine is unchanged; the test mocks it). Likewise the announcement's
exact text is matched by the test as a fixed literal and carries no input-derived
content, so it is abstracted to the single occurrence flag `announced`.

## 3. Callee provenance

There are **no axiomatized callees** and **no deep-model references** in this
bundle. The two operations whose occurrence is observed —
`self.stdout.write(...)` and `self.check(...)` — are modeled DIRECTLY as boolean
occurrence flags (`announced`, `checked`), because the behavior the issue and the
F2P test demand is solely *whether each effect happens under the flag*, not any
value either effect computes. Neither is an unchanged callee whose return
contract the proof consumes; both are effects whose presence/absence is the
modeled behavior itself. Hence no `axiom_check.py` (G-AX is skipped, as in
django__django-12276).

No flag-dependent callees: `skipChecks` is itself the controlling flag and is a
free boolean input fuzzed over both values by G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13809`** so the
consumer-side verdict is reproducible. The input domain is a single boolean
(`skip_checks`), so the seed governs only the redundant fuzz pass over
`{False, True}`; both values are also covered exhaustively.
