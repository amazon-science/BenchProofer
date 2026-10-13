import Mathlib
-- imports-end

/-!
Validating that a time-series table still begins with its required columns, and
reporting a clear error when it does not.

A time-series table carries a list of *required* column names that must appear,
in order, as the leading columns of the table. After any operation that could
disturb the columns, the table is re-checked:

* if checking is switched off, nothing happens;
* if no required columns are configured, nothing happens;
* in the relaxed regime the requirement is only that the present leading columns
  agree with the configured ones as far as they go (the configured list is first
  truncated to the number of present columns);
* if the table has no columns at all (and we are not relaxed), this is reported;
* otherwise, if the leading columns do not match the required ones, this is
  reported;
* finally, once a relaxed table has acquired exactly its required leading
  columns, the relaxed regime is turned off.

When a mismatch is reported the message must be *informative for any number of
required columns*. It names what was expected and what was actually found using a
representation that adapts to the size of the column collection:

* a collection of a single name is shown as that one name wrapped in single
  quotes (verbatim, no escaping — the platform's plain string interpolation);
* a collection of several names is shown as the whole list, each name rendered
  by the platform's canonical value rendering (`repr`) and the renderings
  joined by `", "` inside brackets.

The expected side shows the required column names; the found side shows the
leading present column names, taken to the same length as the required list. The
word "column" is pluralised exactly when more than one column is required. This
guarantees that, for a table requiring several columns, the message lists the
full expected and found column sets rather than only their first entries.
-/

-- axioms-start
-- The mismatch message and the adaptive single-vs-list rendering are modeled
-- DEEPLY over the observable inputs (the configured names, the present names,
-- the toggles); no `axiom` callee contract is consumed. ONE building block is
-- left abstract: the platform's canonical per-element rendering used when a
-- whole list is shown (Python's `repr` of a text value, applied to each
-- element by `str(list)`). That rendering is an UNCHANGED builtin of the
-- surrounding platform — the modeled routine decides WHICH collections are
-- rendered and WHEN the single-name vs whole-list form is used; the
-- per-element escaping rules (double-quote switch when the value embeds a
-- single quote, backslash escapes, control/non-printable escapes per the
-- Unicode tables) belong to the platform. Committing to a concrete Lean
-- approximation of those rules would diverge from the real behavior on names
-- containing quotes/backslashes/control characters, so the element rendering
-- is `opaque`; its binding to the real builtin is validated executably by
-- G-AX (an A-reference fuzzing the real `repr`/`str(list)` over adversarial
-- element strings). No `axiom` about it is consumed: the proof never inspects
-- its behavior.

/-- The platform's canonical rendering of one text value as it appears inside
a rendered list (Python `repr` of a `str`): quote-delimited with the
platform's escaping rules. Left abstract (`opaque`); bound to the real builtin
by G-AX. -/
opaque pyReprStr : String → String
-- axioms-end

-- pure-start
/-- Render one name the way a SINGLE value is shown in a message: the name
verbatim between single quotes (the platform's plain string interpolation
`f"'{x}'"` — no escaping). -/
def pyStrRepr (s : String) : String := "'" ++ s ++ "'"

/-- Render a list of names the way the whole collection is shown in a message
(`str(list)`): each name rendered by the platform's canonical `pyReprStr`,
joined by `", "`, inside brackets (e.g. `['time', 'a']`). The empty list
renders as `[]`. -/
def pyListRepr (xs : List String) : String :=
  "[" ++ String.intercalate ", " (xs.map pyReprStr) ++ "]"

/-- Render a collection of names adapting to its size: a one-name collection is
shown as that single quoted name; any other collection is shown as the whole
list. -/
def renderNames (xs : List String) : String :=
  match xs with
  | [x] => pyStrRepr x
  | _   => pyListRepr xs

/-- The outcome of re-checking a time-series table against its required leading
columns: either a reported error message, or no error together with the updated
value of the relaxed-regime flag. -/
def checkRequiredColumns
    (className : String) (requiredColumnsEnabled : Bool)
    (requiredColumns : Option (List String)) (requiredColumnsRelax : Bool)
    (colnames : List String) : Except String Bool :=
  if !requiredColumnsEnabled then
    .ok requiredColumnsRelax
  else
    match requiredColumns with
    | none => .ok requiredColumnsRelax
    | some reqCols =>
      let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
      let plural := if required.length > 1 then "s" else ""
      if !requiredColumnsRelax && colnames.length == 0 then
        .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
          "' as the first column" ++ plural ++ " but time series has no columns")
      else if colnames.take required.length != required then
        .error (className ++ " object is invalid - expected " ++
          renderNames required ++ " as the first column" ++ plural ++
          " but found " ++ renderNames (colnames.take required.length))
      else
        .ok (if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
              false else requiredColumnsRelax)
-- pure-end

-- post-conditions-start
/-- The check produces exactly the outcome dictated by the rule above: the right
no-op/error decision, and on a mismatch the message naming the full expected and
found column collections (adaptively rendered), with correct pluralisation. -/
def problem_spec_checkRequiredColumns
    (className : String) (requiredColumnsEnabled : Bool)
    (requiredColumns : Option (List String)) (requiredColumnsRelax : Bool)
    (colnames : List String) (result : Except String Bool) : Prop :=
  result = checkRequiredColumns className requiredColumnsEnabled requiredColumns
            requiredColumnsRelax colnames
-- post-conditions-end

-- impl-start
def implementation_checkRequiredColumns
    (className : String) (requiredColumnsEnabled : Bool)
    (requiredColumns : Option (List String)) (requiredColumnsRelax : Bool)
    (colnames : List String) : Except String Bool := Id.run do
  if !requiredColumnsEnabled then
    return .ok requiredColumnsRelax
  match requiredColumns with
  | none => return .ok requiredColumnsRelax
  | some reqCols =>
    let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols
    let plural := if required.length > 1 then "s" else ""
    if !requiredColumnsRelax && colnames.length == 0 then
      return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
        "' as the first column" ++ plural ++ " but time series has no columns")
    else if colnames.take required.length != required then
      -- Pre-patch behavior: the mismatch message reports only the FIRST expected
      -- and the FIRST present column name, regardless of how many columns are
      -- required, so a multi-column requirement yields a message naming a single
      -- pair that need not even differ.
      return .error (className ++ " object is invalid - expected '" ++ required.headD "" ++
        "' as the first column" ++ plural ++ " but found '" ++ colnames.headD "" ++ "'")
    let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then
                      false else requiredColumnsRelax
    return .ok newRelax
-- impl-end

-- proof-start
theorem correct_checkRequiredColumns :
    ∀ (className : String) (requiredColumnsEnabled : Bool)
      (requiredColumns : Option (List String)) (requiredColumnsRelax : Bool)
      (colnames : List String),
      problem_spec_checkRequiredColumns className requiredColumnsEnabled requiredColumns
        requiredColumnsRelax colnames
        (implementation_checkRequiredColumns className requiredColumnsEnabled requiredColumns
          requiredColumnsRelax colnames) := by
  intro className requiredColumnsEnabled requiredColumns requiredColumnsRelax colnames
  unfold problem_spec_checkRequiredColumns checkRequiredColumns
    implementation_checkRequiredColumns
  rfl
-- proof-end
