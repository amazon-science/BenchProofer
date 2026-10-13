# RELAXED_LEAKAGE — django__django-14011 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file). This bundle's own P2 audit
(`verdict.md`, overall status ACCEPTED) reached exactly this disposition —
its leakage sub-review's verdict is **RELAXED**, and it records as required
correction D1: "Set `meta.json gates.G-LEAK.status = 'relaxed'` (currently
'pass'), update note" and "Add in-bundle RELAXED_LEAKAGE.md". This file plus
the meta flag IS that prescribed correction. The identical repair pattern is
already applied and green in `benchmark-verified/sphinx-doc__sphinx-9673/*`
and `benchmark-verified/django__django-15252/nagini`.

## The mismatch

The gold patch (`django/core/servers/basehttp.py` @ base e4430f22c8) gives
`ThreadedWSGIServer` TWO behaviors:

1. **Release** (`close_request` → `_close_connections` →
   `connections.close_all()`): close every DB connection after each request.
   This is fully public — the problem_statement's title literally is
   "ThreadedWSGIServer doesn't close database connections after each thread"
   and its body is the #22414 teardown race. `releaseAll` leaks NOTHING.

2. **Install handoff** (`process_request_thread`): before handling the
   request, install the parent-supplied override connections into the
   worker's registry with override precedence:

   ```python
   if self.connections_override:
       for alias, conn in self.connections_override.items():
           connections[alias] = conn
   ```

   plus the `connections_override=` constructor kwarg. Modeled by
   `installPreferred` with `ensures out = preferred ++ registry` and the
   docstring "it must operate against the handles handed to it, not against
   freshly-created handles for the same aliases."

The leaking lines in this bundle's spec view are the `installPreferred`
contract and docstring: they disclose that a worker is HANDED a set of
parent-supplied preferred bindings that take precedence over its own
registry — the gold's `connections_override` handoff mechanism. An attacker
reading only the problem_statement could never reconstruct this second
behavior; the recorded G-PANEL-3 LEAKAGE finding is factually correct about
the leak's existence.

## Why the leak is unavoidable

The handoff discriminator vocabulary is **absent from the solver-visible
`problem_statement`** (re-verified 2026-08-05, hints_text excluded):
`connections_override` 0, `override` 0, `preferred` 0, `precedence` 0,
`parent` 0, `share` 0, `install` 0, `fresh` 0, `worker` 0, `binding` 0,
`alias` 0, `resolv*` 0, `suppl*` 0. The PS even proposes the OPPOSITE remedy
(revert to the non-threaded `WSGIServer`). The handoff mechanism lives ONLY
in `hints_text` (override ×1, thread-sharing ×3, sqlite ×3 — excluded from
the leakage baseline) and in the hidden `test_patch`
(`_create_server(..., connections_override=...)`).

Yet a faithful spec MUST pin the handoff:

- All 17 FAIL_TO_PASS tests break at base in `setUpClass` because the
  test_patch's rewritten `LiveServerThread._create_server` passes
  `connections_override=` to a server class that rejects the kwarg
  (`TypeError`) — the constructor acceptance is the R-leg framing of
  `installPreferred` taking `preferred`.
- The DB-visibility F2P tests ("Data written to the database by a view can
  be read", "Fixtures ... visible to the live server thread",
  `test_check_model_instance_from_subview`, `test_view_calls_subview`)
  observe exactly the install effect: on in-memory sqlite, a worker without
  the handoff lazily creates a FRESH connection = a fresh EMPTY database.
- `Solution_prepatch.lean` (install reverted, `out = registry`) genuinely
  fails G-DIFF on `out = preferred ++ registry`, length, and membership.
  Drop the install contract and that prepatch verifies, so G-DIFF could not
  fire and wrong (non-resolving) implementations would satisfy the spec.

A spec derivable from the problem_statement alone could model only the
close-after-request behavior. Faithful + non-leaking is therefore provably
impossible here — the definition of a `problem_statement ↔ gold` mismatch.
The de-narration into neutral "registry/preferred/handles" vocabulary is
already done; the *behavior itself* (handing parent connections to the
worker with precedence) is the leak, and no renaming removes it.

## Core soundness is intact (per the recorded P2 audit of THIS bundle)

Quoting the recorded `verdict.md` (overall ACCEPTED):

- **G-VERIFY: pass** — `Solution.lean` verifies (exit 0).
- **G-DIFF: pass** — `Solution_prepatch.lean` exit 1 (three install
  ensures); `Solution_prepatch_2.lean` exit 1 (two release ensures);
  spec regions byte-identical (same_spec True).
- **G-EQ: pass (SOUND/TIGHT)** — 7 wrong impls (incl. both prepatch-class
  bugs) all rejected on the discriminating clauses; positive control
  verifies; no kind-3 steps; no consumed axioms.
- **G-PANEL-2: FAITHFUL** — shadow == real post-gold callee on 100,007
  inputs (seed 14011), 0 disagreements; both A-reference deep models
  validated == real callees on boundary + 40,000 fuzz (G-AX SOUND),
  including the never-instantiated/AttributeError path.
- **G-MUT: 20/20 killed. G-CONF: pass. G-RESOLVE: resolved**
  (`patch.diff` == gold verbatim).

Only the secondary no-leakage property is relaxed, for this one documented
facet (the parent-connections install-handoff contract of
`installPreferred`). The "verify ⇒ resolved" guarantee is unaffected.
