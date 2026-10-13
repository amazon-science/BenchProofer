# refinement.md — operation correspondence (django__django-10973)

Maps every op in `implementation_dbShellCommand` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`DatabaseClient.runshell_db`) assembles the `psql` argument
vector (UNCHANGED by the fix) and supplies the password to the spawned process.
The fix replaces the temp-`.pgpass`-file mechanism with passing the password to
the child process via its environment, then invokes the client via
`subprocess.run(..., env=subprocess_env)`. The two observable outputs (exactly
what the F2P tests' mock captures: `(self.subprocess_args, env.get('PGPASSWORD'))`)
are the argument vector and the child-process password value.

| # | Lean impl op | patch.diff / base counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut args := ["psql"]` | `args = [cls.executable_name]` with `executable_name = 'psql'` | I | identical: literal head; `psql` is a class literal, unchanged by the fix |
| 2 | `if user ≠ "" then args := args ++ ["-U", user]` | `if user: args += ['-U', user]` | R | str↔String; Python truthiness of a str ↔ `≠ ""` (mapping.md) |
| 3 | `if host ≠ "" then args := args ++ ["-h", host]` | `if host: args += ['-h', host]` | R | as row 2 |
| 4 | `if port ≠ "" then args := args ++ ["-p", port]` | `if port: args += ['-p', str(port)]` | R | as row 2; conn_params port is already a str so `str(port) = port` (mapping.md) |
| 5 | `args := args ++ [dbname]` | `args += [dbname]` | I | identical unconditional append |
| 6 | `let mut passwordEnv := none; if passwd ≠ "" then passwordEnv := some passwd` | `subprocess_env = os.environ.copy(); if passwd: subprocess_env['PGPASSWORD'] = str(passwd)` | R | the **changed op** modeled deeply: the child-process password slot holds the supplied password iff a password is given, else is absent. `str(passwd) = passwd` (already a str). The rest of the copied environment is irrelevant to the observable contract (only the password entry is observed) and is out of model scope (mapping.md). NOT axiomatized. |
| 7 | `return (args, passwordEnv)` | `subprocess.run(args, check=True, env=subprocess_env)` | I | the observable inputs handed to the invocation are the argument vector and the child-process password; the spawn effect, `check=True`, and the SIGINT save/restore are unobserved by the contract (out of model scope, mapping.md) |

No A-consumed rows: the proof discharges the two-component structure directly; no
UNCHANGED callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: there is no callee abstracted behind a deep model needing
G-AX validation. No changed-inexpressible op.

The discriminating clause is row 6 (component `.2`). Post-fix the child-process
password is `some passwd` whenever `passwd ≠ ""`. The prepatch routes the
password through a side channel (the temp credentials file) and never sets the
child-process password slot, so its `.2` is always `none`. For any `passwd ≠ ""`
this contradicts the frozen `problem_spec_dbShellCommand`'s second conjunct
(`result.2 = some passwd`), so the prepatch `correct_dbShellCommand` cannot close
— the G-DIFF signal.
