# refinement.md — django__django-13410

The operation-by-operation correspondence between `model.py`'s implementation
(the `acquire` and `release` impl regions, plus the live `primitive_lock` /
`primitive_release` axioms) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`/`Exsures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The patch edits the POSIX `else:` branch of `django/core/files/locks.py` (the
branch reached when `import fcntl` succeeds), changing two sibling helpers.

## A. The acquisition site — `lock(f, flags)` (`locks.py:109`)

Gold hunk:
```
-        def lock(f, flags):
-            ret = fcntl.flock(_fd(f), flags)
-            return ret == 0
+        def lock(f, flags):
+            try:
+                fcntl.flock(_fd(f), flags)
+                return True
+            except BlockingIOError:
+                return False
```

| # | model.py impl op (`acquire`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `available: bool` | `f`, `flags` arguments of `lock` | R | the helper's only OBSERVABLE dependence on `(f, flags)` is whether the primitive completes normally or signals contention — that single bit is `available` (mapping.md §2). `_fd(f)` is the unchanged trivial fd resolver, unobserved by the spec. |
| A2 | `primitive_lock(available)` inside `try:` | `fcntl.flock(_fd(f), flags)` inside `try:` | A-consumed | `primitive_lock` is the weakest contract on the unchanged `fcntl.flock` that is true of it. Its clauses in full (mapping.md §3.1): `MustTerminate(2)`; the `lock_state()` framing in and out; `answerable_acquisition()`, consumed and not re-established; normal completion ⇒ `available is True`; normal completion ⇒ **`Result() is None`, i.e. THE VALUE IS EMPTY** — the callee's own value carried as itself, with no numeric fact claimed of it, not even "differs from zero"; normal completion ⇒ the SUBJECT description is left holding the requested lock (`Ensures(holds_lock())`); refusal ⇒ `Exsures(LockUnavailable, available is False and lock_state() and holds_lock() == Old(holds_lock()))` (nothing moved in the requested lock). This leg's proof consumes the availability, framing, answerability and state clauses. It does NOT consume the value clause, and that is deliberate: gold discards the return value here, so the value clause is not a fact this leg leans on but the statement that there is nothing to lean on — see §C and mapping.md §3.1b for why stating it is load-bearing and why it cannot be an unsound strengthening. `holds_lock()` is the abstraction of the real `flock(2)` claim THE SUBJECT DESCRIPTION holds (mapping.md §3.3) — per-description rather than an aggregate over the file, single-valued in that subject's own standing and driven in both directions, so this call is what puts the subject into "holding" and only a release by that subject can take it back out. The call also CONSUMES the expendable answerability capability `answerable_acquisition()` (mapping.md §3.2b): `acquire`'s own report is scoped to answered requests, so it spends its single capability on the one acquisition it performs — exactly what the gold `try:` block does, which issues exactly one `flock` request per call. Being a resource rather than a proposition, the capability cannot be interrogated, duplicated or conjured, so neither a second acquisition here nor any acquisition inside `release` can be paid for. G-AX confirms the callee against the real `fcntl.flock` (mapping.md §3.1). |
| A3 | `return True` on the normal-completion path, with the subject still holding the lock | `return True` | I | identical concrete operation — the success outcome is reported as `True`, NOT read off the (discarded) primitive return value. The state A2 established discharges the helper's `Implies(Result() is True, holds_lock())` exit-state obligation, and because the observation is reversible this leg is genuinely IDENTICAL to gold in the state dimension: any interposed state-moving operation (a release, or a release-and-retake) changes `holds_lock()` at the return point and is REJECTED, so no extra effect-producing operation without a gold counterpart can hide inside this leg. |
| A4 | `except LockUnavailable: return False` | `except BlockingIOError: return False` | A-consumed + R | the refusal signal is caught and absorbed into `False`, and NOTHING else happens on this path. `LockUnavailable` ↔ `BlockingIOError` (R, mapping.md §2: user-defined exception stands in for the builtin); the proof consumes the axiom's `Exsures` to discharge `Result() == available` on the `available is False` branch, and its preservation conjunct to discharge `Implies(Result() is False, holds_lock() == Old(holds_lock()))` — which is what makes this leg identical to the gold `except` branch, whose body is a bare `return False`. |

Discriminating content: the post-patch reports the outcome by CONTROL FLOW
(normal completion ⇒ `True`); the pre-patch DERIVED IT FROM THE RETURN VALUE, and
`fcntl.flock` hands back the empty value on success, so every interrogation of
that value answering "did the request go through?" answered NO and the pre-patch
reported `False` even when the lock WAS acquired — the headline bug.
`model_prepatch.py` reproduces that body: it invokes the primitive, then derives
the report from the value it handed back, with the refusal signal left unhandled
as in the pre-patch. The interrogation is spelled as the one question the empty
value can be asked at all, which has the SAME answer on every granted request as
the pre-patch's numeric test — both are FALSE there — so the body is the
pre-patch's behaviour exactly; the numeric spelling itself is not even a
well-formed question to put to an empty value, which is a second and independent
reason no such body can be justified. It **fails** verification on
`Postcondition of acquire might not hold. Assertion (Result() == available)` —
the value obligation the patch is about, on the granted-acquisition path (G-DIFF).
The unhandled refusal signal is a second defect in the same body.

## B. The release site — `unlock(f)` (`locks.py:113`)

Gold hunk:
```
-        def unlock(f):
-            ret = fcntl.flock(_fd(f), fcntl.LOCK_UN)
-            return ret == 0
+        def unlock(f):
+            fcntl.flock(_fd(f), fcntl.LOCK_UN)
+            return True
```

| # | model.py impl op (`release`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `primitive_release()` | `fcntl.flock(_fd(f), fcntl.LOCK_UN)` | A-consumed | `primitive_release` is the weakest contract on the unchanged `fcntl.flock` (release mode) that is true of it. Its clauses in full (mapping.md §3.2): `MustTerminate(6)`; the `lock_state()` framing in and out; NO answerability capability; a release completes normally and **`Result() is None`, i.e. THE VALUE IS EMPTY** (the same reading as A2, and likewise not consumed by this leg — gold discards it); no `Exsures`; and it leaves THE SUBJECT no longer holding the lock (`Ensures(holds_lock() is False)`, the abstraction of the real `flock(fd, LOCK_UN)` release, mapping.md §3.3). Because the observation is per-description, this asserts only that the subject let go — a compatible claim another description holds on the same file survives, which is what the real callee does in the `test_shared_lock` world. This is the direction that makes the state observation reversible. It carries NO answerability condition, because a release of a held lock always completes — so `release` needs no such scope and, having none, cannot supply one to an acquisition step (mapping.md §3.2b): the gold `unlock` body performs exactly one release and nothing that could be left pending. G-AX confirms it against the real callee (mapping.md §3.2). |
| B2 | `return True` (with the subject no longer holding the lock) | `return True` | I | identical concrete operation — the release outcome is reported as `True` unconditionally, NOT read off the discarded return value. The state B1 established discharges the helper's `holds_lock() is False` exit-state obligation, so a `return True` that skipped B1 cannot verify — and neither can one that re-takes the lock after B1, since that drives the observation back to `True` at the return point. This leg is therefore identical to gold in the state dimension too, and in the answerability dimension: no step that another holder could leave pending can hide inside it. |

Discriminating content: identical translation bug as site A but for release.
`model_prepatch_2.py` reproduces it — invoke the release primitive, then derive
the report from the value it handed back — and **fails** specifically on
`Postcondition of release might not hold. Assertion (Result() is True)`, because
a completed release hands back the empty value and every interrogation asking
"did the release go through?" answers NO — the spec sensing the release bug
(G-DIFF). This is an independently-observable fixed behaviour
(`assertIs(locks.unlock(f1), True)` in both F2P tests), hence its own prepatch.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — how
the primitive's control-flow signal is translated into the returned boolean —
is modelled **directly** as the helpers' control flow (try/normal-return vs.
except-return; unconditional return), an **I**-step over the boolean outcome.
The only consumed axioms, `primitive_lock` and `primitive_release`
(**A-consumed**), cover the **unchanged** library callee `fcntl.flock` the new
code still invokes — never the operation under change. There is no
**A-reference** deep model.

**Clause accounting (no unaudited slack).** Every clause of both axioms is either
CONSUMED by the helpers' postconditions or is the value clause, and the value
clause is accounted for separately and deliberately:

  * consumed: the `lock_state()` framing, `available is True` / the `Exsures`'
    `available is False` (which discharge `Result() == available`), both
    directions of the `holds_lock()` state observation and the `Exsures`'
    preservation conjunct (which discharge the three exit-state clauses), the
    answerability capability spent at the acquisition call site, and the
    `MustTerminate` measures;
  * NOT consumed, by design: `Ensures(Result() is None)` on both primitives. The
    gold hunks discard the primitive's return value, so no faithful body leans on
    it. It is stated because the emptiness of that value is the behavioural fact
    the reported outcome turns on, and because stating it makes every
    value-derived report PROVABLY WRONG rather than merely unproven: a body that
    decides the report by asking the value whether it is "set" is proved to take
    the FALSE branch on a granted acquisition and so fails
    `Result() == available`. It is what the pre-patch controls fail on (the
    Discriminating-content notes above), which is the sense in which it is live.
    And it cannot be an unsound strengthening in the way a stand-in number would
    be: it says of the value exactly what the real callee makes true of it —
    `axiom_check.py` asserts the real value IS the empty one and, as negative
    controls, that it does not count as "set", does not order against a number,
    does not enter arithmetic and does not compare equal to zero, each control
    paired with the opposite answer a number gives. A numeric carrier would claim
    strictly MORE than the callee does, and more in the one direction that decides
    the report, which is why none is used.

The state observation `lock_state()` / `holds_lock()` gives **A-consumed effect**
clauses, NOT kind-3. They do not encode the answer (the returned boolean is still
the grounded `Result() == available` / `Result() is True`), they are not a
copyable field, and `holds_lock()` is not a function of the result and is not
readable by any implementation (`@Pure @ContractOnly`), so it is not an oracle.
They are the abstraction of the real `flock(2)` claim THE SUBJECT DESCRIPTION
holds — a fact about the unchanged callee `fcntl.flock` (it actually gives the
subject the requested claim, and `LOCK_UN` ends it), the same callee §3.1/§3.2
already audit — recorded so the spec can require that a reported outcome describes
the standing the caller is handed **at the return point**. The observation is
per-open-file-description, matching what `flock(2)` tracks: it says the SUBJECT
holds (or has let go of) the lock, and says nothing about a compatible claim
another description may hold on the same file. That indexing is what keeps the
clauses faithful in the shared-holder world of the instance's own
`test_shared_lock`, where the subject's release leaves an aggregate "is any lock
in force" probe still answering yes while the subject's claim is genuinely gone;
`axiom_check.py` asserts both halves of that on the real callee.

Why a STATE observation and not a monotone capability token. A token that is only
ever added witnesses "the primitive was invoked somewhere on this path". That fact
survives the inverse operation, so a body could take the lock, give it straight
back, and still present the token while returning `True` — value-identical to
gold, world-opposite to gold, and admitted. Pinning the state instead
(single-valued, moved in both directions by the two primitives, mapping.md §3.3)
makes the claim positional: `holds_lock()` at the return point is determined by
the state-moving operation performed **last**, so undoing the acquisition
**falsifies** the postcondition rather than merely failing to establish it. The
three obligations that follow — success ⇒ the subject holds the requested lock on
exit, failure ⇒ the subject's standing in the requested lock is exactly as it was
found, release ⇒ the subject no longer holds the lock on exit —
are each faithful to the issue (a non-blocking caller "requires a valid return
value to know if they have successfully acquired the lock": the value is only
worth anything if the lock it reports is the lock the caller then has), and the
F2P tests fail for exactly the implementations they exclude — `test_exclusive_lock`
observes f1's claim still standing via f2's refused non-blocking requests
after `lock(f1, LOCK_EX)` returned `True` (an exclusive claim, so there the
subject-indexed and aggregate readings coincide). So these clauses strengthen the spec
toward the *behaviour the tests check*, without smuggling the edit.

## D. verify(model) ⇒ resolved

`acquire` verifies only if it returns `available` exactly — `True` on the
normal-completion path and `False` on the caught-refusal path (A2–A4) — AND, on
the success path, the subject holds the requested lock at the return point, AND, on the failure
path, the lock state is exactly what it was on entry. `release` verifies only if
it returns `True` after a normal release AND the subject no longer holds it at the
return point (B1–B2).

That closes three distinct flanks, all in the state dimension the boolean cannot
see:

  * **bypass** — a no-op that echoes the boolean without invoking the primitive
    cannot ESTABLISH the required state (`holds_lock()` is not readable by an
    implementation and nothing else moves it), so it does not verify;
  * **inverse effect** — a body that invokes the primitive and then performs the
    inverse operation before returning FALSIFIES the required state, because the
    observation is single-valued and reversible. This is the flank a monotone
    capability token left open, and it is where the previous audit's `atk_4`
    (acquire-then-release, reporting `True`) landed: its faithful refinement drops
    f1's lock on the way out, so `test_exclusive_lock`'s subsequent
    `locks.lock(f2, LOCK_EX|LOCK_NB)` is granted and returns `True` where the test
    asserts `False`. Under the exit-state clause that body no longer verifies;
  * **frame break on the failure path** — a body that moves the state while
    reporting `False` (value-identical to gold on every input, differing only in
    what it does to the world when it fails) violates the preservation clause;
  * **pending step on the release path** — a body that reaches gold's exact final
    state by the wrong route: acquire first, then release, then report `True`.
    Value-identical to gold, exit-state-identical to gold, net-effect-identical to
    gold — and still not gold, because an acquisition is the operation another
    holder can leave PENDING while a release of a held lock always completes
    (mapping.md §3.2b). Measured on the real callee, its faithful refinements make
    the F2P's `unlock(f1)` hang (blocking) or raise (non-blocking). The spec
    rejects it by making the acquisition primitive CONSUME `answerable_acquisition()`
    while leaving the release helper's contract unconditional: the fact is
    contract-only and unmanufacturable, so a release body has nothing to hand to
    an acquisition step.

So the model permits NO extra state-moving operation without a gold counterpart
anywhere in either helper: legs A3 and B2 are identical to gold in the state
dimension as well as the value dimension.

Both helpers additionally carry a `MustTerminate` obligation
(`acquire` = 10, `release` = 14, over the primitives' 2 and 6; mapping.md §4): a
diverging implementation — an endless loop before the return, or self-recursion —
would satisfy the value/state postconditions only vacuously while never delivering
the boolean the tests read; the obligation leak check rejects it, so a verifying
implementation actually ANSWERS on every tested input, as the gold helpers do. The
primitives' strictly smaller measures let the faithful bodies invoke them without
leaking the obligation, so the gold translation still verifies. The obligation
ranges over the ANSWERED requests the abstraction models (mapping.md §5): a
blocking request the kernel leaves pending is not one of the two outcomes a
boolean report can describe, and is not what the patch changed (both the base and
the patched helper block identically there).

By R (`(f,flags)` ↔ `available`, `LockUnavailable` ↔ `BlockingIOError`, the
callee's success value ↔ the model language's own empty value — an IDENTITY, not
a stand-in — the `flock(2)` lock state ↔ `holds_lock()` over
`lock_state()`) the verified helpers equal the gold
`try: flock(...); return True except BlockingIOError: return False` and
`flock(..., LOCK_UN); return True` on the tested inputs — in both the value and
the state dimension; by G-AX the real `fcntl.flock` meets the `primitive_lock` /
`primitive_release` axioms (A-consumed). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
