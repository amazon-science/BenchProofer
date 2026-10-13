# refinement.md — django__django-10973

The operation-by-operation correspondence between `model.py`'s implementation
(the `password_env_value` impl region, and the deep `pgpass_quote_seq` model
used by the prepatch differential) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed**
where the proof uses the axiom's `Ensures`, **A-reference** where a deep model
is validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The password-exposure site — `runshell_db` (`client.py`)

Gold hunk (the password handling):
```
-        temp_pgpass = None
         sigint_handler = signal.getsignal(signal.SIGINT)
+        subprocess_env = os.environ.copy()
+        if passwd:
+            subprocess_env['PGPASSWORD'] = str(passwd)
         try:
-            if passwd:
-                # Create temporary .pgpass file.
-                temp_pgpass = NamedTemporaryFile(mode='w+')
-                ... print(_escape_pgpass(host) or '*', ..., _escape_pgpass(passwd), sep=':', ...)
-                os.environ['PGPASSFILE'] = temp_pgpass.name
             signal.signal(signal.SIGINT, signal.SIG_IGN)
-            subprocess.check_call(args)
+            subprocess.run(args, check=True, env=subprocess_env)
```

| # | model.py impl op (`password_env_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `passwd: List[int]` | `passwd = conn_params.get('password', '')` (a `str`) | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | the result is `ToSeq(passwd)` — the verbatim copy of `passwd`, code point by code point, built by the forward loop | `subprocess_env['PGPASSWORD'] = str(passwd)` | R + I | `str(passwd)` is the identity on the code-point carrier (passwd is already `str`; mapping.md §2). The model's loop copies each code point unchanged: `Result() == passwd`. No transformation is applied — identical concrete behaviour up to the `str ↔ List[int]` refinement. |
| A3 | populated (`len(Result()) > 0`) iff `len(passwd) > 0` | the env var `PGPASSWORD` is assigned iff `if passwd:` (i.e. `passwd` non-empty) | I | the presence guard is the same truthiness test; for a `str`, truthy ⇔ non-empty ⇔ `len > 0`. |
| A4 | `Result()` returned (a `List[int]`) | `subprocess.run(args, check=True, env=subprocess_env)` reads `PGPASSWORD` from `subprocess_env` | R | the value the child sees for the password is exactly the assigned value; `subprocess.run`/`os.environ.copy()` do not transform it (the F2P mock reads `env.get('PGPASSWORD')`, the assigned string). No axiom needed — the value is observed verbatim. |

The discriminating content of the change — the password is exposed **verbatim**
(`str(passwd)`) rather than passed through the legacy `_escape_pgpass` quoting
(`\\`→`\\\\`, `:`→`\\:`) embedded in a `.pgpass` file line — lives in the
postcondition `ToSeq(Result()) == ToSeq(passwd)`. The pre-patch code quoted the
password; `model_prepatch.py` reproduces that quoting (`pgpass_quote_seq`) and
**fails** that postcondition whenever the password contains a colon or a
backslash, which is exactly the spec sensing the change (G-DIFF). The F2P tests
`test_column` (`some:password` → `some:password`, not `some\:password`) and
`test_basic`/`test_accent` (the raw password) observe precisely this.

## B. Behaviour deliberately not re-modeled (kind I, unchanged)

The gold patch does NOT change:
- the `args` command-line construction (`['psql', '-U', user, '-h', host, '-p',
  str(port), dbname]`, each appended on truthiness) — byte-identical pre/post;
- the SIGINT save → `SIG_IGN` → restore-in-`finally` dance — byte-identical.

These are unchanged plumbing (kind I), not the fix, so they are not modeled as
separate functions. The F2P `test_sigint_handler` and the `subprocess_args`
assertions exercise them, but they pass both before and after the patch; no
`model_prepatch` variant is warranted for them (a prepatch must keep the spec
byte-identical, and nothing about them differs). The only independently-fixed,
differentially-observable behaviour is the password exposure (site A), which has
its failing `model_prepatch.py`.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — how the password is exposed to the child — is modeled **deeply**
(the verbatim copy in `password_env_value`, A2, pinned by
`ToSeq(Result()) == ToSeq(passwd)`), not hidden behind an axiom about the
function under change. The legacy quoting `pgpass_quote_seq` appears only as the
**A-reference** the prepatch differential is stated against and that G-AX
validates `== _escape_pgpass`; it is defined exclusively in `model_prepatch.py`,
inside a module-level `impl` region that the spec view elides, so it never
enters `model.py`'s consumer-visible regions (SPEC_GUIDE directive 6 — no
removed-mechanism narration in the spec view). There is **no consumed axiom**
(`A-consumed`):
the new code introduces `os.environ.copy()` / `subprocess.run(..., env=...)`,
but neither transforms the password value the tests observe, so the proof needs
no contract about them (mapping.md §3.2).

## D. verify(model) ⇒ resolved

`password_env_value` verifies only if its output equals the password **verbatim**
(A2) and is populated iff the password is non-empty (A3). By R (`str ↔
List[int]`, `str()` identity) the verified value equals the `str(passwd)` the
gold patch assigns to `PGPASSWORD`, exposed unchanged through
`subprocess.run(..., env=subprocess_env)` (A4). By G-AX the deep model
`pgpass_quote_seq` equals the real removed `_escape_pgpass` (A-reference) and
the post-patch value equals the raw password on boundary + fuzz. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement on the changed behaviour — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(here: A-reference fidelity, G-AX) and refinement fidelity (this document,
G-EQ).
