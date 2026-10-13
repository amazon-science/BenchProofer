# refinement.md — pytest-dev__pytest-6197

Correspondence between `Solution.lean`'s `gatherEntries` impl and `patch.diff`
(the gold patch removes the eager `self._mount_obj_if_needed()` call from the
top of `Package.collect`, and refactors `PyobjMixin.obj` so the underlying
object is mounted lazily on first access instead of being forced during the
directory walk). `patch.diff` is the gold verbatim (applies at base_commit,
resolves — G-RESOLVE).

Each step is tagged **R** (type refinement), **A** (axiomatized callee —
A-consumed / A-reference), or **I** (identical concrete op). EVERY step is R, A,
or I. There are no kind-3 (changed-inexpressible) steps.

## A. The directory walk — `Package.collect`

Gold hunk (the load-bearing change, `src/_pytest/python.py:628-630`):
```
     def collect(self):
-        self._mount_obj_if_needed()
         this_path = self.fspath.dirpath()
         init_module = this_path.join("__init__.py")
         ...
```

| # | Solution.lean impl op (`gatherEntries`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | `if initMatches then collected := collected ++ [initNode]` | `if init_module.check(file=1) and path_matches_patterns(...): yield Module(init_module, self)` (`python.py:631-635`) | **I** | UNCHANGED leading yield: when the package's own `__init__.py` matches the configured pattern, its collector is produced first. The pattern test enters as the Boolean `initMatches`, the collector as the token `initNode` (R data entry). |
| A2 | `collected := entries.foldl (fun acc e => if e.boundary \|\| !e.isFile then acc else acc ++ e.yields) collected` | `for path in this_path.visit(...): <skip boundary paths>; if is_file: yield from self._collectfile(path)` (`python.py:637-655`) | **I** | UNCHANGED gathering loop, transliterated op-for-op: boundary paths and directories contribute nothing; each non-boundary regular file contributes its `_collectfile` resolution (`yields`, entering as data — R). The fold is the front-to-back generator order. |
| A3 | the result's second component is `false` — the walk never loads the directory's own initialization file | the **removed** line `self._mount_obj_if_needed()` (`python.py:629`) | **I** | the CHANGED op, modeled deeply as the value of the load-event observable. Pre-patch the first statement of the walk forces `self._obj = self._getobj()` = `self._importtestmodule()` — the directory's own `__init__.py` is loaded (its top-level code runs) merely because the directory is scanned; the event observable is `true`. The fix deletes that statement; the event observable is `false`. The spec pins `out.2 = false`. Because the event is a RESULT component (not a resettable `mut` slot), an implementation that fires the load cannot erase it before returning — see §F. |

## B. Supporting refactor — `PyobjMixin.obj` / `Module.__init__`

Gold also (i) splits `PyobjMixin.obj` into a property whose getter mounts lazily
(`python.py:251-271`), changing `get_unpacked_marks(obj)` →
`get_unpacked_marks(self.obj)`; and (ii) deletes `Module.__init__`
(`python.py:432-440`), which had set `_ALLOW_MARKERS = False` for `__init__.py`
modules.

These are **R**/**I** support for A3, not independently-observable behavior:
- The `obj` property refactor relocates *where* the mount happens (lazy, on
  first `.obj` access) without changing *what* mounting computes — `self._obj`
  is still `self._getobj()`, marks still extended once. Under the model this is
  subsumed by A3 (the handle is mounted on demand, never eagerly during the
  walk); it adds no observable the spec must separately pin. **R** (relocation,
  identity on observable content).
- Deleting `Module.__init__` removes a now-unnecessary `_ALLOW_MARKERS` tweak
  that only mattered while mounting was eager; with lazy mounting it is dead.
  No new observable. **I** (removal of a now-unreachable special case).

No separate failing prepatch is needed for site B: there is no independently
fixed *behavior* there — the F2P observable (a directory's `__init__.py` is not
imported during the walk) is produced entirely by A3 (the removed eager mount).
Site A's prepatch (which reports the load event `true`) already exercises
exactly the discriminating clause. A prepatch must keep the spec byte-identical
(G-DIFF), so there is nothing distinct to encode for B.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
elision of the eager mount — is modeled **deeply** as the value of the
load-event RESULT component (A3, I-tagged): the walk reports whether it loaded
the directory's own initialization file, and the spec pins that report to
`false`. There is no consumed axiom and no A-reference: the removed callee
(`_importtestmodule`) is not re-derived or contracted; the spec asserts only
that the walk does not perform it (the event component is `false`).

## D. verify(Solution) ⇒ resolved; prepatch fails

`gatherEntries` verifies only if both `out.2 = false` (forced by A3: the walk
never loads the initializer) and
`out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries`
(forced by A1+A2: the exact gathered sequence) hold, under TOTAL correctness
(the walk provably terminates). By R (mapping.md §2) the verified post-state
equals: after `Package.collect` walks the directory, the package's own
`__init__.py` has NOT been imported at all, and the gathered children are
exactly the sequence the scan yields.

The F2P tests assert exactly this:
- `test_does_not_eagerly_collect_packages` writes an `__init__.py` whose
  top-level code fails; if the walk eagerly imports it, collection errors —
  the test passes only if the walk never loads it (`out.2 = false`).
- `test_does_not_put_src_on_path` relies on the same elision (an `src/`
  package layout's `__init__.py` is not imported during collection).

The PASS_TO_PASS suite (the broad `test_collection.py` battery) requires the
walk to still gather the same entries — the `out.1 = ...` clause pins the
FULL walk (leading init item + per-path contributions in order), so a walk
that drops, reorders, duplicates, or invents entries fails.

The prepatch (`Solution_prepatch.lean`) performs the eager load (it reports
the event `true`, the buggy `self._mount_obj_if_needed()` at the top of
`collect`). `prove_correct` fails on exactly the discriminating clause:
```
case «ensures_2: out.2 = false»
⊢ False        -- the walk loaded the initializer; the spec pins false
```
This is the precise regression the issue reports ("pytest tries to collect /
import any `__init__.py` file"). G-DIFF passes.

## F. Spec-strength: the load EVENT as a result component

Two earlier versions of this bundle encoded the load event as `mut` state
slots (`indexModule : Option Nat` with `ensures indexModule = none`, then an
added `imports : Nat` with `ensures imports = 0`). Both were TOO-WEAK for the
same structural reason: a `mut` slot is resettable, so an implementation that
performs the forbidden load and then restores the slot
(`slot := fired; slot := initial`) satisfies any final-state frame on the slot
while the event has already fired in the real world (the F2P repro's failing
`__init__.py` top-level code would already have run). Velvet's postconditions
constrain final values only; no final-state predicate over a resettable slot
can pin an event.

The repair moves the event INTO the returned value: `gatherEntries` returns
`List Nat × Bool`, whose second component is defined (mapping.md §2) as
"whether the walk loaded the directory's own initialization file", and the
spec pins `ensures out.2 = false`. A return value is assigned once, at the
return point — there is no later write that could erase it — so the
fire-then-reset family is structurally excluded: any implementation whose
walk performs the load corresponds, under the bijection, to a run that
returns `true` in that component and fails the spec. The event is now a
first-class observable of the modeled function, exactly what the F2P test
grades.

The output clause is simultaneously STRENGTHENED from the earlier pass-through
(`out = entries`, which took the gathered sequence as given and returned it
unchanged) to the full walk
(`out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries`):
the enumeration itself — leading init item when the pattern matches, then the
per-path boundary/file dispatch in visit order — is now modeled deeply, so the
spec also excludes implementations that gather the wrong sequence.

Verification SEMANTICS: `loom.semantics.termination "total"`
(TotalCorrectness). Under partial correctness a non-terminating impl vacuously
satisfies every postcondition — its Lean file verifies, yet the corresponding
patch (an infinite loop at the top of `Package.collect`) hangs collection and
fails every hidden test. Total correctness closes that loophole; the real
`Package.collect` walks a finite directory tree and returns, so totality is
faithful.

G-CONF runs (`conf_skip=false`): the impl region is now the executable
enumeration (leading item + fold), which has a direct R/I shadow;
`conformance_check.py` diffs the transliterated shadow against a faithful
in-process replica of the post-patch generator over 200k seeded inputs.
No axioms ⇒ no G-AX.

## E. Trust points

The single trust point is refinement fidelity (this doc, G-EQ): that the
removed eager mount (A3) is the load-bearing fix, that the load-event result
component faithfully carries it, and that the supporting `obj`/`Module`
refactor (§B) adds no independently-observable behavior. G-VERIFY pins the
event and the full gathered sequence; G-DIFF confirms the spec sees the bug;
G-CONF diffs the enumeration shadow against the post-patch generator. No axiom
soundness (G-AX) trust point exists (no axioms).
