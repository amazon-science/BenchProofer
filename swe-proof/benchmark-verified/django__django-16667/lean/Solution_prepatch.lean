import Mathlib
-- imports-end

/-!
Coercing a tripartite date entry into the string a date field will later parse.

A date entry collected from three separate components — a year, a month and a
day, each arriving as text — is reduced to a single textual value before any
field-level parsing happens. The reduction attempts to read the three components
as a calendar date. Three situations can arise from that attempt, and in EVERY
one of them the reduction must successfully hand on a value (it is total — it
never fails to produce an outcome):

  * the three components denote a representable calendar date — the value handed
    on is that date rendered in the field's canonical input format;
  * the three components are well-formed text but do NOT denote a representable
    calendar date (an impossible month or day, an out-of-range year, or
    non-numeric text) — the value handed on is a pseudo-ISO string built from the
    raw components, each empty component shown as a single zero
    (`"<y>-<m>-<d>"`, e.g. `"2017-0-23"`);
  * a component, though syntactically a number, is so large that it cannot be
    accommodated as a calendar component at all — the value handed on is the
    all-zero sentinel `"0-0-0"`.

A value being handed on is modeled as `some s`; the totality requirement is that
the outcome is `some …` in every situation (never `none`). The all-zero sentinel
is itself not a representable calendar date, so a field parsing it afterwards
rejects the entry as invalid rather than accepting it. The canonical rendering of
a representable date and the pseudo-ISO fallback for a non-representable-but-well-
formed entry are unchanged across all of this.
-/

-- axioms-start
-- No unchanged outside callee contract is consumed by this specification. The
-- classification of the entry (representable / well-formed-but-not-a-date /
-- out-of-range magnitude) and the canonical rendering of a representable date
-- are produced by surrounding machinery and enter this computation as arbitrary
-- inputs (`c`, `rendered`); this computation only dispatches on them. No
-- `opaque`/`axiom` callee declaration is therefore needed.
-- axioms-end

-- pure-start
/-- The outcome of attempting to read the three textual components as a calendar
date.
* `valid`          — the components denote a representable calendar date;
* `malformed`      — the components are well-formed text but do not denote a
                     representable calendar date;
* `unrepresentable`— a component's numeric magnitude is too large to be
                     accommodated as a calendar component. -/
inductive DateEntry where
  | valid
  | malformed
  | unrepresentable
  deriving DecidableEq, Repr

/-- The pseudo-ISO fallback `"<y>-<m>-<d>"`, where an empty component is shown as
a single `"0"` (modeling `"%s-%s-%s" % (y or 0, m or 0, d or 0)`). -/
def pseudoIso (y m d : String) : String :=
  (if y = "" then "0" else y) ++ "-" ++
  (if m = "" then "0" else m) ++ "-" ++
  (if d = "" then "0" else d)
-- pure-end

-- post-conditions-start
/-- The value handed on is pinned in every outcome (directive 5 frame: no case
left unconstrained). `c` is the entry classification; `rendered` is the canonical
rendering produced when the entry is a representable date; `y`/`m`/`d` are the raw
textual components. The result is modeled as `Option String`: `some s` means the
value `s` is handed on, `none` means no value is produced. The reduction is TOTAL
— a value is handed on in every situation: a representable date is rendered
canonically (`some rendered`); a well-formed but non-representable entry yields
the pseudo-ISO fallback (`some (pseudoIso y m d)`); an entry whose magnitude
cannot be accommodated yields the all-zero sentinel (`some "0-0-0"`). The
totality of the third case is the discriminating clause: the value must be
produced (not absent) AND equal `"0-0-0"`. -/
def problem_spec_coerceDateEntry
    (c : DateEntry) (rendered y m d : String) (result : Option String) : Prop :=
  (c = DateEntry.valid → result = some rendered) ∧
  (c = DateEntry.malformed → result = some (pseudoIso y m d)) ∧
  (c = DateEntry.unrepresentable → result = some "0-0-0")
-- post-conditions-end

-- impl-start
def implementation_coerceDateEntry
    (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
  -- Only the representable date and the well-formed-but-not-a-date outcomes are
  -- handled; an entry whose magnitude cannot be accommodated is not handled at
  -- all — no value is produced for it (modeling the uncaught failure that
  -- aborts the reduction, `none`).
  match c with
  | DateEntry.valid => return some rendered
  | DateEntry.malformed => return some (pseudoIso y m d)
  | DateEntry.unrepresentable => return none
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- impl it cannot close: the specification pins the unrepresentable-magnitude
-- outcome to `some "0-0-0"` (a value IS handed on), but this impl produces `none`
-- for that outcome, so the third conjunct
-- (`c = DateEntry.unrepresentable → result = some "0-0-0"`) reduces to
-- `none = some "0-0-0"`, which is not derivable.
theorem correct_coerceDateEntry :
    ∀ (c : DateEntry) (rendered y m d : String),
      problem_spec_coerceDateEntry c rendered y m d
        (implementation_coerceDateEntry c rendered y m d) := by
  intro c rendered y m d
  unfold problem_spec_coerceDateEntry implementation_coerceDateEntry
  cases c <;> refine ⟨?_, ?_, ?_⟩ <;> intro h <;> simp_all [Id.run, pure]
-- proof-end
