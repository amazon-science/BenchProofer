# refinement.md — django__django-11292

Maps every op in each `Solution.lean` `do` block to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed**, **A-reference**,
**I** (identical concrete op). No axioms in this bundle, so no A rows. No
kind-3 (changed-inexpressible) ops.

## Method `registeredCommandOptions` (models the `create_parser` change)

Patch hunk (`base.py`, in `create_parser`):

```python
+        if self.requires_system_checks:
+            parser.add_argument(
+                '--skip-checks', action='store_true',
+                help='Skip system checks.',
+            )
         self.add_arguments(parser)
         return parser
```

| # | `do`-block op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let out := if requiresSystemChecks then commonOptions ++ ["--skip-checks"] else commonOptions` | `if self.requires_system_checks: parser.add_argument('--skip-checks', …)` | **R** | The parser's accepted-option **set** is modeled as a `List String` (`commonOptions`). `parser.add_argument('--skip-checks', action='store_true')` adds exactly one recognised option string `--skip-checks` to that set; the guard is the same `requires_system_checks` boolean. Bijection: `parser` accepts option `s` ⟺ `s ∈ out` (mapping.md §2). `action='store_true'`/`help=` affect only default value and help text, not membership — outside the modeled carrier. |
| 2 | `return out` | `self.add_arguments(parser); return parser` | **I** | `add_arguments` adds the command-specific options, already folded into the free frame `commonOptions` (unchanged by the patch — pre and post both run it); returning the augmented parser ≡ returning the augmented option list. |

The new postcondition content is the pair of exact structural equations
`requiresSystemChecks = true → out = commonOptions ++ ["--skip-checks"]` and
`requiresSystemChecks = false → out = commonOptions`, stated directly on the
input carrier (no named pure-def indirection — an ungrounded-oracle echo has
nothing to echo), together with the membership corollaries
`("--skip-checks" ∈ out) = requiresSystemChecks` and frame preservation
`∀ s ∈ commonOptions, s ∈ out`.

## Method `shouldRunSystemChecks` (models the `execute` gate)

Patch hunk (`base.py`, in `execute`):

```python
-        if self.requires_system_checks and not options.get('skip_checks'):
+        if self.requires_system_checks and not options['skip_checks']:
             self.check()
```

| # | `do`-block op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 3 | `let result := requiresSystemChecks && (! skipRequested)` | `requires_system_checks and not options['skip_checks']` | **R** | `&&`/`!` are the Lean refinements of Python `and`/`not` over the bool bijection (mapping.md §2). The op's *value* `requires_system_checks and not options['skip_checks']` is identical pre/post patch; the patch only changes `.get('skip_checks')` (defaulting to `None`/falsey) to `['skip_checks']` (direct key access). Under the bijection `skipRequested : Bool` both spellings denote the same boolean once the key is guaranteed present — which is exactly what method 1 guarantees for the gated commands (mapping.md §1). So the modeled value is `requiresSystemChecks ∧ ¬skipRequested`. |
| 4 | `return result` | `if … : self.check()` | **R** | The branch *taken* (`self.check()` invoked) ⟺ the gate boolean is true. We model the decision `result : Bool` (= "checks run"), not the side-effecting call; bijection mapping.md §2 row "self.check() is invoked". |

## Independently-fixed behaviour & the prepatch (G-DIFF)

There is **one** independently-observable fixed behaviour for the F2P test
`test_skip_checks`: passing `--skip-checks` on the command line must be
*accepted by the parser* and must *suppress the checks*. The decisive, newly
introduced step is the conditional **registration** of the flag (op 1): without
it, `--skip-checks` is an unrecognised option and the command errors out before
`execute` is ever reached — so the test cannot pass regardless of the gate.

`Solution_prepatch.lean` therefore reverts op 1 to the pre-patch skeleton
(`let out := commonOptions` — no flag is ever registered) while keeping the
byte-identical spec. Its postcondition `("--skip-checks" ∈ out) =
requiresSystemChecks` then fails for any command with
`requiresSystemChecks = true` (the tested `set_option` configuration), so
`prove_correct` cannot close → G-DIFF.

The `execute` gate (method 2) is not independently observable in the buggy→fixed
direction here: pre-patch `execute` *already* honoured `skip_checks` via
`.get()`, so a separate gate-prepatch would not correspond to a distinct
real-world bug. Method 2 exists for spec **strength** (directive 4): it forbids a
"register the flag but ignore it" impl from verifying. Its R-leg is still
G-CONF-checked.
