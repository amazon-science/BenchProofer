import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (One building block is left abstract; no `axiom` is consumed. The message
--  construction is modeled DEEPLY in the `pure` region below from concrete
--  string operations over the inputs. The single abstract leaf is the
--  platform's canonical rendering of one text value as it appears INSIDE a
--  rendered sequence: quote-delimited with the platform's own escaping rules
--  (the delimiter can switch, and escape/control characters are escaped, when
--  the value embeds such characters). That rendering is an UNCHANGED builtin
--  of the surrounding platform — the behaviour modeled here decides WHICH
--  collections are rendered and WHEN the single-name form vs the
--  whole-sequence form is used, while the per-character escaping rules belong
--  to the platform. Committing to a concrete approximation of those rules
--  here would diverge from the real behaviour on names containing
--  quote/escape/control characters, so the element rendering is `opaque`; its
--  binding to the real builtin is validated executably by G-AX
--  (axiom_check.py fuzzes the real builtin over adversarial names). The proof
--  never inspects its behaviour. The decision of WHICH branch of the
--  surrounding check fires, and the relaxation bookkeeping, are unchanged
--  control flow reached identically and are not modeled here — only the
--  message construction is. See refinement.md §B and mapping.md §3.)

/- The platform's canonical rendering of one text value as it appears inside a
   rendered sequence of values: quote-delimited with the platform's escaping
   rules. Left abstract (`opaque`); bound to the real builtin by G-AX. -/
opaque renderedName : List Char → List Char
-- axioms-end

-- pure-start
/- A column name is a sequence of characters; a collection of column names is a
   sequence of those. The message renders names for the reader. -/

/- One column name, rendered the way a SINGLE value is shown on its own: the
   name verbatim surrounded by apostrophes — plain interpolation, no escaping
   (e.g. the name `time` renders as `'time'`). -/
def quoted (s : List Char) : List Char := ['\''] ++ s ++ ['\'']

/- A comma-and-space separated run of names as they appear inside a rendered
   sequence — each name rendered by the platform's canonical `renderedName` —
   with no surrounding brackets. Front-recursive (one unfold available per
   leading element):
     []            ↦ (nothing)
     [x]           ↦ renderedName x
     x :: y :: ys  ↦ renderedName x, <rest>
   The two-element-or-more arm keeps the recursion structural. -/
def joinRendered : List (List Char) → List Char
  | []             => []
  | [x]            => renderedName x
  | x :: (y :: ys) => renderedName x ++ ", ".toList ++ joinRendered (y :: ys)

/- A whole collection of names rendered as a bracketed list, the way a sequence
   of names is displayed: `[` then the comma-separated canonically-rendered
   names then `]` (e.g. names `time`, `a` render as `['time', 'a']`; the empty
   collection renders as `[]`). -/
def bracketList (xs : List (List Char)) : List Char := ['['] ++ joinRendered xs ++ [']']

/- Render a collection of column names for display. A collection holding exactly
   one name is shown as that single quoted name — plain interpolation, no
   escaping (e.g. `'time'`); a collection of any other size (none, or two or
   more) is shown as the bracketed list, each element in its canonical rendered
   form (e.g. `['time', 'a']` or `[]`). This single/many distinction is the
   whole point of the rendering: a one-name collection reads as a scalar, a
   many-name collection reads as the explicit list it is. -/
def renderColumnList : List (List Char) → List Char
  | [x] => quoted x
  | xs  => bracketList xs

/- The full invalidity message for the required-columns check, given the table's
   class name, the names that were required as the leading columns, and the names
   actually present. The names actually compared against are the leading prefix
   of the present names, as many as were required. The message names the expected
   leading columns and the present leading columns using the display rendering
   above, and uses a plural noun exactly when more than one column was required:

     <Class> object is invalid - expected <expected> as the first column<s?> but found <found>

   where <expected> renders the required names and <found> renders the present
   leading names. Grounded in the three input sequences plus the platform's
   canonical per-element rendering (the one abstract leaf; directive 8). -/
def errorMessage (className : List Char) (required present : List (List Char)) : List Char :=
  let found := present.take required.length
  className ++ " object is invalid - expected ".toList ++ renderColumnList required
    ++ " as the first column".toList ++ (if required.length > 1 then ['s'] else [])
    ++ " but found ".toList ++ renderColumnList found
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the message reported when a table's leading columns do not match the
   columns it requires. `className` is the table's class name; `required` is the
   sequence of names required as the leading columns; `present` is the sequence
   of names actually present. All three are read-only (not `mut`): the message is
   computed and nothing is mutated (directive 5).

   Desired behaviour: the message must name the expected leading columns and the
   present leading columns using the display rendering — a single required (resp.
   present) name shown as a quoted scalar, several shown as the bracketed list —
   so that when more than one column is required the message reports the actual
   collections rather than only their first element, and pluralizes accordingly.
   The present names compared are the leading prefix of those present, as many as
   were required. -/
method requiredColumnsError (className : List Char) (required : List (List Char))
    (present : List (List Char)) return (out : List Char)
  ensures out = errorMessage className required present
  do
    -- impl-start
    -- Compare against the leading prefix of the present names, as many as were
    -- required; render both the required and the present-prefix collections for
    -- display (single name → quoted scalar, otherwise → bracketed list);
    -- pluralize the noun when more than one column was required; assemble.
    let found := present.take required.length
    let expectedStr := renderColumnList required
    let foundStr := renderColumnList found
    let plural : List Char := if required.length > 1 then ['s'] else []
    let msg := className ++ " object is invalid - expected ".toList ++ expectedStr
      ++ " as the first column".toList ++ plural ++ " but found ".toList ++ foundStr
    return msg
    -- impl-end

prove_correct requiredColumnsError by
  loom_solve
  simp_all [errorMessage]
