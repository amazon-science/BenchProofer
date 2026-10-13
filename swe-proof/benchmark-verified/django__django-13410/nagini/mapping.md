# mapping.md — django__django-13410

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 580a4341cb0b4cbfc215a70afc004875a7e815f4`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/core/files/locks.py` (the POSIX `else:` branch,
the one reached when `import fcntl` succeeds — `os.name != 'nt'`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `acquire(available)` | `lock(f, flags)` — `django/core/files/locks.py:109` (POSIX `else` branch) | modeled changed function #1 (the lock-acquisition helper) |
| `release()` | `unlock(f)` — `django/core/files/locks.py:113` (POSIX `else` branch) | modeled changed function #2 (the lock-release helper) |
| `primitive_lock(available)` *(axiom — A-consumed)* | `fcntl.flock` — CPython stdlib `Modules/fcntlmodule.c` (called at `locks.py:110` pre-patch / inside the new `try` post-patch) | unchanged low-level callee the acquisition helper wraps |
| `primitive_release()` *(axiom — A-consumed)* | `fcntl.flock(_fd(f), fcntl.LOCK_UN)` — same CPython callee, release mode (`locks.py:114`) | unchanged low-level callee the release helper wraps |
| `LockUnavailable` (exception) | the `OSError` / `BlockingIOError` `fcntl.flock` raises on contention | user-defined stand-in (builtin-exception `Exsures` crashes the translator) |
| the primitives' normal-completion value, carried as the model language's OWN EMPTY VALUE (`Ensures(Result() is None)`, declared return type `Optional[int]`) | the empty value `None` that `fcntl.flock` returns on success | carried as the callee's ACTUAL value rather than as a stand-in number, so the model claims about it exactly what is true of it and nothing more. That is load-bearing, not stylistic: the empty value answers NONE of the questions a number answers — it does not count as "set", it does not order against a number, and it does not enter arithmetic — so the reported boolean cannot be derived from it at all and must be taken from the control flow, which is where the outcome actually is. A stand-in number would be a strictly STRONGER claim than the callee makes, and stronger in the one direction that decides the report: every number answers those questions, and answers them whichever way that particular number happens to fall. §3.1 states the clause; `axiom_check.py` checks it in both directions. |
| `lock_state()` *(abstract `@ContractOnly @Predicate`, no body)* | the kernel-level lock WORLD the `flock(2)` calls operate on | a framing resource threaded unchanged through every operation; it carries no value information and restricts no input, so it is not a domain restriction |
| `answerable_acquisition()` *(abstract `@ContractOnly @Predicate`, no body)* | the standing that ONE acquisition request has to be ANSWERED by the kernel — granted, or refused with `EWOULDBLOCK` — rather than left PENDING (`flock(2)` without `LOCK_NB` blocks until the incompatible holder yields), and to be settled outright rather than decided against an unresolved rival claim | the ANSWERABILITY capability, modelled as an EXPENDABLE RESOURCE. It is asymmetric between the two operations because the primitive is: `flock(fd, LOCK_EX)` can block indefinitely, while `flock(fd, LOCK_UN)` on a lock the caller holds always completes (§3.2). `primitive_lock` CONSUMES it and does not re-establish it, so one capability authorises exactly ONE answered acquisition; `primitive_release` and `release` require none. Being a resource rather than a proposition it can only be RECEIVED and SPENT: nothing creates it, nothing duplicates it, and there is no fact for a body to interrogate or branch on — so a release body cannot supply one to an acquisition step, and no body can issue a second answered acquisition on one authorisation. It carries no value information and restricts no input: both booleans and both of `acquire`'s control-flow paths remain live. |
| `holds_lock()` *(`@Pure @ContractOnly`, readable only inside contracts)* | the kernel-level STATE "does THIS open file description hold the advisory lock IT REQUESTED, RIGHT NOW" — the subject's own `flock(2)` claim, as `/proc/locks` attributes records to descriptions. `flock` locks are **per-open-file-description, not per-file**, so this is NOT an aggregate "is any lock in force" bit: a compatible (shared) claim another description holds on the same file is a *different* record and is not part of this observation. Indexed to the lock the request named as well as to the description | the SINGLE-VALUED state observation. Both primitives pin it, in OPPOSITE directions (`primitive_lock` normal completion ⇒ `holds_lock()`; `primitive_release` ⇒ `holds_lock() is False`), so it is REVERSIBLE and records what the world currently IS rather than which operations once ran. That is what lets a postcondition constrain the state a helper hands back AT ITS RETURN POINT, and what makes "acquired then gave it up again" observably different from "acquired". No implementation can read or echo it (`@Pure @ContractOnly` is contract-only). |

The unchanged trivial helper `_fd(f)` (`locks.py:24-26`, `f.fileno() if
hasattr(f, 'fileno') else f`) merely resolves the file-descriptor argument; it
does not participate in the bug and is abstracted away (the helper observes only
the primitive's control-flow outcome, not which fd it locked).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the file/fd argument `f` (and `flags`) the helper receives | the abstract boolean `available` (whether the requested lock can currently be acquired) | the helper's only OBSERVABLE dependence on `f`/`flags` is whether the primitive completes normally or signals contention; that single bit is `available`. `_fd(f)`/`flags` themselves are unobserved by the spec. |
| `fcntl.flock(...)`'s success return value `None` | the model language's own empty value (`Ensures(Result() is None)`) | IDENTITY rather than a refinement: the carrier IS the value the callee returns. No numeric fact is claimed of it — not an exact number, and not even the weaker "differs from zero" — because the callee hands back no number at all. This is exactly what the pre-patch's value test gets wrong: it puts a question to the value that the value does not answer, and every such interrogation reports a granted acquisition as a failure. `axiom_check.py` asserts both directions (the real value IS the empty one; it answers no numeric interrogation) and pairs each negative control with the answer a stand-in number would have given, so the numeric reading is refuted by measurement. |
| `fcntl.flock(...)` raising `OSError`/`BlockingIOError` on contention | `primitive_lock` raising `LockUnavailable` | a builtin exception inside `Exsures` crashes Nagini, so a user-defined class stands in; semantics: "did not complete normally → the lock was not available". |
| the helpers' `bool` return (`True`/`False`) | model `bool` (`True`/`False`) | identical concrete type. |
| the `flock(2)` claim THE SUBJECT DESCRIPTION holds at a given instant (does *this* open file description hold the lock it asked for?) — per-description, not per-file, and not an aggregate over other holders | the single-valued observation `holds_lock()` over the framed world `lock_state()` | the boolean value the helper returns carries NO trace of the world behind it: `return True`, a real acquisition, and an acquisition immediately undone are all value-indistinguishable. The state is modelled as an observation moved in BOTH directions by the two primitives (§3.3), which is what makes "report success ⇒ the lock is in force WHEN YOU RETURN" expressible — a strictly stronger claim than "the operation was performed somewhere along the way". |

`str`/full-heap modelling is unnecessary for the *value* behaviour (the returned
boolean is plain bool/int). The lock/unlock SIDE-EFFECT, which the boolean cannot
witness, is the one piece of state the spec must observe; it is modelled as the
two abstract capability predicates above rather than a concrete heap so that the
ONLY way to produce it is to invoke the effect-performing primitive.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `primitive_lock` ↔ `fcntl.flock` (A-consumed)
**Callee:** CPython `fcntl.flock(fd, operation)`. Per the documented contract
(https://docs.python.org/3/library/fcntl.html#fcntl.flock) it performs a
`flock(2)` system call and:

  * **returns `None`** when the operation succeeds, and
  * **raises an `OSError`** when it fails — specifically `BlockingIOError`
    (errno `EWOULDBLOCK`/`EAGAIN`) when a `LOCK_NB` (non-blocking) request
    cannot be granted because another holder owns an incompatible lock.

The axiom's LIVE CLAUSES, in full (so the correspondence below can be audited
clause by clause):

  * `Requires(MustTerminate(2))` — an answered request is one bounded kernel
    operation that delivers its answer (§5);
  * `Requires(lock_state())` / `Ensures(lock_state())` — the framing resource,
    threaded unchanged; it constrains no input value (§3.3);
  * `Requires(answerable_acquisition())`, CONSUMED and not re-established — the
    expendable standing to have ONE acquisition answered (§3.2b);
  * `Ensures(available is True)` — a normal completion is reachable only on the
    available case;
  * `Ensures(Result() is None)` — THE VALUE IS EMPTY. The normal-completion value
    is the model language's own empty value, which is what the real callee hands
    back, so this is the callee's value carried as itself. No numeric fact is
    claimed of it: not an exact number, and not even the weaker "differs from
    zero". Both of those would be claims the callee does not make, and both would
    be stronger in the one direction that decides the reported boolean, because a
    number answers questions the empty value refuses (is it "set", how does it
    order, what is it minus itself) and a body could then read a definite outcome
    off a value that carries none;
  * `Ensures(holds_lock())` — on the normal-completion path ONLY, the subject is
    left holding the lock it requested;
  * `Exsures(LockUnavailable, available is False and lock_state() and holds_lock() == Old(holds_lock()))`
    — the unavailable case signals out of band and moves nothing in the requested
    lock.

The axiom does NOT claim the callee never raises — the raise path is modelled
explicitly (and leaves the state where it found it: nothing was acquired there).
Every clause is the weakest form that is true of the real callee: the state and
availability clauses are what the helper's postconditions `Result() == available`,
`Implies(Result() is True, holds_lock())` and
`Implies(Result() is False, holds_lock() == Old(holds_lock()))` consume, and the
value clause is the weakest true statement about a value that carries nothing —
which is what makes every value-derived report provably wrong rather than merely
unproven (see §3.1b).

### 3.1b Why the value clause is stated at all, and what it rules out

The clause `Ensures(Result() is None)` is not consumed by the faithful helper
bodies: they discard the primitive's return value, exactly as the gold hunks do.
It is stated because the emptiness of that value is the behavioural fact the
whole reported outcome turns on, and stating it is what makes a value-derived
report PROVABLY WRONG instead of merely unproven. With the clause, a body that
reports the outcome by asking the value whether it is "set" is proved to take the
FALSE branch on a granted acquisition, so `Result() == available` fails; the same
body under a numeric carrier is proved to take the TRUE branch and verifies,
while its faithful transliteration reports a granted acquisition as a failure —
the very bug the behaviour exists to rule out. The clause therefore cannot be an
unsound strengthening: it says of the value precisely what the real callee makes
true of it, and `axiom_check.py` checks that in both directions, pairing each
negative control with the answer a stand-in number would have given. It is also
what the pre-patch controls fail on (`model_prepatch.py` /
`model_prepatch_2.py`, G-DIFF), which is the sense in which it is live.

The gold patch catches `BlockingIOError`; the problem statement's suggested
patch catches the broader `OSError`. `BlockingIOError` ⊂ `OSError`, and the
F2P tests only ever trigger the non-blocking-contention path (which raises
`BlockingIOError`), so both spellings absorb exactly the tested contention into
`False`. The model's single `LockUnavailable` abstracts the contention signal;
`axiom_check.py` fuzzes the real `fcntl.flock` and asserts it raises `OSError`
on non-blocking contention (covering both spellings).

### 3.2 `primitive_release` ↔ `fcntl.flock(fd, LOCK_UN)` (A-consumed)
**Callee:** the same CPython `fcntl.flock`, invoked with `fcntl.LOCK_UN` to
release a lock the caller holds. Releasing a held lock succeeds and returns
`None`; it does not signal contention. The axiom's live clauses are
`Requires(MustTerminate(6))`, the `lock_state()` framing, NO answerability
capability (§3.2b), `Ensures(Result() is None)` — THE VALUE IS EMPTY, on the same
reading and for the same reason as §3.1/§3.1b — no `Exsures`, and the release
having taken effect leaves the subject NOT holding the lock
(`Ensures(holds_lock() is False)`), the weakest contract the release helper's
postconditions `Result() is True` and `holds_lock() is False` need. This second
direction is what makes the state observation reversible (§3.3).

**Soundness check (G-AX):** `axiom_check.py` runs the real `fcntl.flock` on real
file descriptors of a temporary file: (a) a first holder acquiring `LOCK_EX` /
`LOCK_EX|LOCK_NB` / `LOCK_SH` / `LOCK_SH|LOCK_NB` hands back the empty value;
(b) a second descriptor requesting an incompatible lock non-blocking raises
`OSError`; (c) `LOCK_UN` hands back the empty value without raising. Each
observation of a normal-completion value goes through one checker that asserts
the value IS the empty one AND, as NEGATIVE CONTROLS, that it does not count as
"set", does not order against a number, does not enter arithmetic, and does not
compare equal to zero — each control paired with the answer a stand-in number
gives, which is the opposite one. So the reading the model does not license is
refuted against the real module rather than merely avoided in prose. This is the
same locking mechanism the F2P tests (`test_exclusive_lock`,
`test_shared_lock`) exercise. It imports only stdlib `fcntl`/`os`/`tempfile`;
on a non-POSIX host (no `fcntl`) the modelled branch does not exist and the
check is vacuously sound. Exit 0 iff sound.

### 3.2b The answerability capability `answerable_acquisition()` (A-consumed, from the same callee)
`flock(2)` is asymmetric in one respect the boolean report cannot show. An
**acquisition** without `LOCK_NB` blocks until an incompatible holder releases —
the kernel may leave the request PENDING indefinitely, delivering neither of the
two answers. A **release** of a lock the caller holds has nobody to wait for and
always completes. (`man 2 flock`: "If a process uses `open()` ... requests for a
conflicting lock block, unless `LOCK_NB` is specified"; `LOCK_UN` removes an
existing lock held by this process.) That is a fact about the unchanged callee,
the same one §3.1/§3.2 audit — not a new callee and not a new trust point.

The model records it as `answerable_acquisition()`, an abstract
`@ContractOnly @Predicate` (no body) **consumed** by `primitive_lock` and held by
`acquire`, and deliberately NOT required by `primitive_release` or `release`.
Modelling it as an expendable RESOURCE rather than as a proposition is
load-bearing: a proposition is something a body could interrogate — it could ask
whether the standing happens to hold and proceed on the strength of the answer,
helping itself to an entitlement nobody granted it — whereas a resource can only
be received and spent, with nothing to test and no way to conjure or duplicate it.
Consequences:

  * the release helper's obligation to report back is **unconditional**, which is
    strictly stronger than a contract that quietly allowed a possibly-pending
    step inside it;
  * because the capability is a resource that nothing creates and nothing
    duplicates, a release body has nothing with which to pay for an acquisition
    step, and cannot obtain the standing by testing for it (there is no fact to
    test) — so "release by acquiring first, then releasing" cannot be proved, even
    though it reaches gold's exact final state;
  * because `primitive_lock` CONSUMES the capability without re-establishing it,
    one authorisation buys exactly ONE answered acquisition — so a body that issues
    REPEATED acquisition requests for the lock cannot be proved either: the
    standing for the first request is spent on the first, and the caller asked for
    one lock and is owed one answer;
  * it restricts no input: `acquire` receives it as scope, both boolean values
    stay admissible, and both control-flow paths stay reachable (the battery's
    admissibility case verifies with `Assert(available is True)` on the normal
    path and `Assert(available is False)` on the refusal path).

Executable grounding: the pending case cannot be *asserted* by a terminating
probe (a hang is what it predicts), so `axiom_check.py` establishes the
asymmetry's observable half — a release always completes and never raises, while
a conflicting non-blocking acquisition is refused — and the `properties.py`
case-12 refinement records the measured outcome of the pending route on the real
callee (blocking ⇒ the F2P's `unlock(f1)` hangs; non-blocking ⇒ it raises).

### 3.3 The lock-state observation `lock_state()` / `holds_lock()` (A-consumed effect)
The boolean a helper returns carries no trace of the world behind it — `return
True`, a real acquisition, and a real acquisition that is immediately undone are
all value-indistinguishable. But the syscall *does* have a real, observable
state: after a granted acquisition the subject description holds the claim it
asked for (a third party's incompatible non-blocking request is refused —
`test_exclusive_lock`), and after a release the subject no longer holds it. The
observation is PER-OPEN-FILE-DESCRIPTION, which is what `flock(2)` actually
tracks: releasing one description's shared claim does not clear a compatible
claim another description holds on the same file (`test_shared_lock` is exactly
that world — after `unlock(f1)` an aggregate "is any lock in force" probe still
answers yes, while `f1`'s own claim is genuinely gone). An aggregate reading
would therefore assert something the real callee does not do; the subject-indexed
reading is what the clauses below mean and what the real callee honours. That
state is modelled as:

  * `lock_state()` — an abstract `@ContractOnly @Predicate` with **no body**: the
    lock world, threaded unchanged through every operation. Purely framing; it
    carries no value information and constrains no input, so both boolean inputs
    to the helper remain admissible (the PBT admissibility case establishes both
    control-flow paths under it).
  * `holds_lock()` — a `@Pure @ContractOnly` observation of that world: "does the
    subject description hold the lock it requested right now". Being
    `@ContractOnly` it is readable only inside contracts, so no implementation can
    compute or echo it. It reports the SUBJECT's claim only; other descriptions'
    compatible claims are outside it.

The two primitives pin this observation in **opposite directions**:
`primitive_lock`'s normal completion ensures `holds_lock()`, and
`primitive_release` ensures `holds_lock() is False`; the refusal path ensures the
observation is unmoved (`holds_lock() == Old(holds_lock())`). So the observation
is **single-valued and reversible**: at any program point it reflects the
state-moving operation performed **last**, not the set of operations ever
performed.

That reversibility is the load-bearing property, and it is what distinguishes
this from a monotone capability token. A token that only ever accumulates
witnesses "the primitive was invoked at some point on this path" — a fact that
survives the inverse operation, so a body may take the lock, give it back, and
still present the token. A reversible state observation witnesses "the lock is in
force **at this program point**", so a body that undoes the acquisition before
returning does not merely fail to prove the postcondition, it **falsifies** it.
The helpers' obligations are therefore claims about the world the caller actually
receives: `Implies(Result() is True, holds_lock())` on acquire (report success ⇒
the lock is in force on exit), `holds_lock() is False` on release (report a
release ⇒ the lock is not in force on exit), and
`Implies(Result() is False, holds_lock() == Old(holds_lock()))` on acquire (report
failure ⇒ nothing moved).

This adds no new callee and no new soundness obligation beyond "the real
`fcntl.flock` acquires on a granted request and releases on `LOCK_UN`", the same
callee §3.1/§3.2 already audit; `axiom_check.py` exercises exactly that by
observing real contention (a lock in force) and a real release. There is no
answer-key oracle and no copyable field: `holds_lock()` is not a function of the
result and cannot be read by an implementation, only constrained by contracts.

## 4. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl region (primitives
grounded in the real `fcntl.flock` on a shadow file) differentially against the
real patched `django.core.files.locks.lock`/`unlock` in-container, comparing
the returned booleans and the held/freed lock effects observed by a third
descriptor's non-blocking probe. Pinned fuzz seed: **13410** (the instance
number); 100000 fuzz trials plus a full boundary enumeration of
holder/request compatibility scenarios.

## 5. Total correctness (`MustTerminate`)

Each helper is a bounded, loop-free wrapper around a single primitive
invocation, and on an ANSWERED request (the modelled scope — see model.py's
SCOPE paragraph and §3.1: the primitive either completes normally or signals out
of band) each real helper delivers its boolean. A request the kernel leaves
PENDING (a blocking wait on a lock another holder keeps) is not one of the two
answered outcomes and is outside what a boolean report can describe; the
abstraction and these obligations range over answered requests only, which is
also exactly the domain `axiom_check.py` and `conformance_check.py` instantiate. Nagini
verifies partial correctness by default, so without an explicit obligation a
diverging implementation (an endless loop before the return, or bare
self-recursion) would satisfy every `Ensures` clause vacuously while never
reporting to its caller — and such an implementation is not the repo behaviour
(the F2P tests observe an actual returned value). The helpers therefore carry
`Requires(MustTerminate(10))` (`acquire`) / `Requires(MustTerminate(14))`
(`release`) and the axiomatized primitives `Requires(MustTerminate(2))`
(`primitive_lock`) / `Requires(MustTerminate(6))` (`primitive_release`): each
callee measure is strictly smaller than its caller's, which lets a helper invoke
its primitive without leaking the obligation, while an implementation that loops
or re-invokes the helper itself fails the obligation leak check. The obligation encodes only "the operation completes", which is
exactly the modelled callee behaviour §3.1/§3.2 already audit (a bounded
kernel operation that returns or raises); it adds no new callee fact.
