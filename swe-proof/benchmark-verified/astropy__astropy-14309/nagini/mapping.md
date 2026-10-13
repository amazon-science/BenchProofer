# mapping.md — astropy__astropy-14309

Binds every `model.py` symbol to its repository counterpart at
`base_commit = cdb66059a2feb44ee49021874605ba90801f9986`, states the type
abstraction, and gives the provenance of the modeled decision.

Repo file under change: `astropy/io/fits/connect.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `is_recognised_input(stream_present, sig_matches, path_present, path_recognised, n_trailing, first_trailing_accepted)` | `is_fits(origin, filepath, fileobj, *args, **kwargs)` — `astropy/io/fits/connect.py:48` (body 62-72) | the modeled changed function (a format-detection predicate). The patch turns the one-armed `if filepath.lower().endswith(...): return True` (body 68-71) into `return filepath.lower().endswith(...)` (a total boolean for the present-path branch), so the present-path branch never falls through to `isinstance(args[0], ...)`. |
| `decided(...)` | the priority cascade of `is_fits` (the `if fileobj / elif filepath / return isinstance(args[0], ...)` chain, `connect.py:62-72`) | pure spec: the verdict the predicate must produce as a total function of the classification facts |
| `R_TRUE / R_FALSE / R_FAULT` | the `bool` results `True` / `False`, and the `IndexError` raised when `args[0]` indexes an empty `args` (`connect.py:72`) | pure spec: result codes (`R_FAULT` = the out-of-range fault the present-path branch must never reach) |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): the one-armed conditional
`if filepath.lower().endswith((...)): return True` at `connect.py:68-71`, which
has **no `else`** and so falls through to `return isinstance(args[0], ...)` at
`connect.py:72` when the suffix is not recognised.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `fileobj is not None` (`connect.py:62`) | `stream_present: bool` | one identity/None test ↔ one boolean bit |
| `sig == FITS_SIGNATURE` (`connect.py:66`), the leading-bytes comparison | `sig_matches: bool` | one bytes comparison ↔ one boolean bit (the stream branch's verdict; unchanged by the patch, modeled only as the result of an opaque test) |
| `filepath is not None` (`connect.py:67`) | `path_present: bool` | one None test ↔ one boolean bit |
| `filepath.lower().endswith((".fits", ".fits.gz", ".fit", ".fit.gz", ".fts", ".fts.gz"))` (`connect.py:68-70`) | `path_recognised: bool` | the suffix test ↔ one boolean bit. The exact suffix set and the `str.lower()` normalisation are unchanged by the patch and outside the modeled delta; only the *control flow consuming this boolean* changes. |
| `len(args)` (the trailing positional `*args` tuple) | `n_trailing: int >= 0` | the count of trailing positional arguments; `args[0]` is in range iff `n_trailing >= 1` |
| `isinstance(args[0], (HDUList, TableHDU, BinTableHDU, GroupsHDU))` (`connect.py:72`) | `first_trailing_accepted: bool` | one isinstance test on `args[0]` ↔ one boolean bit, meaningful only when `n_trailing >= 1` (the `Requires(Implies(first_trailing_accepted, n_trailing >= 1))` domain fact) |
| `True` / `False` returns; `IndexError` from `args[0]` on empty `args` | `R_TRUE` (1) / `R_FALSE` (0) / `R_FAULT` (-1) | the two boolean verdicts and the out-of-range fault sentinel |

`str`/`bytes` indexing and `isinstance` are not expressible in Nagini, so the
suffix test, signature comparison, and object-kind test are R-refined to opaque
boolean bits; the change is a pure control-flow decision over those bits and the
argument count, which Nagini expresses directly.

**Total correctness.** The contract carries `Requires(MustTerminate(2))`: the
real predicate is a straight-line cascade that always delivers a verdict, so
the model demands the same — a diverging body (unbounded self-recursion or an
infinite loop) would satisfy the value postconditions only vacuously and is
rejected by the termination obligation.

## 3. Callee provenance (kind-A — none consumed; decision-equivalence by G-AX)

This bundle consumes **no `@ContractOnly` axiom** and references **no stdlib
deep-model**: the `axioms` region of `model.py` is empty. The modeled delta is a
control-flow decision over boolean classification bits + an argument count,
modeled **deeply** as the pure cascade `decided` (model.py `pure` region). The
sub-operations the cascade branches on — `fileobj is not None`,
`sig == FITS_SIGNATURE`, `filepath is not None`, the `str.endswith` suffix test,
`len(args)`, and `isinstance(args[0], ...)` — are all **unchanged** by the patch
(R-refinements into boolean / int inputs), not axiomatized callees. The patch
changes only how the present-path branch's boolean is consumed (return it vs.
discard it and fall through).

**Soundness check (G-AX):** because no axiom is consumed, G-AX reduces to a
DECISION-EQUIVALENCE check. `axiom_check.py` calls the REAL
`astropy.io.fits.connect.is_fits` on the F2P input and on a fuzz of
present-path / present-stream / trailing-argument configurations, observes its
result (a bool, or an `IndexError`), and asserts it equals the model's `decided`
verdict computed from the same classification bits. It also confirms the
pre-patch divergence is real (an unrecognised present path with no trailing
argument raises `IndexError` under the one-armed fall-through, i.e. the
`R_FAULT` the patch eliminates). It imports only `astropy.io.fits` (the package
the change lives in); nothing model-specific. Exit 0 iff sound.
