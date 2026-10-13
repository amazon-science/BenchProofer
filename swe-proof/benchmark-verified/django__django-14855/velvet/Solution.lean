import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The address-resolution facility that turns a named route plus its positional
   argument into a concrete address, relative to a named application context.
   It is a pure function of THREE things jointly: the route name, the positional
   argument, and the application context it is resolved within. The context is
   optional: `some app` resolves the route within the application named `app`;
   `none` leaves the context unspecified and resolves it within the ambient
   default. The result is optional too: `some addr` when the route resolves,
   `none` when no matching route exists for that name/argument.

   Crucially the application context is a genuine determinant of the result:
   resolving the same route+argument under two different contexts may yield two
   different addresses. We pin no concrete address values — the weakest
   sufficient contract is simply that this is a function of all three inputs
   (directive 7). Provenance + executable soundness check (that the real
   facility honours the application context): mapping.md / axiom_check.py
   (G-AX). -/
axiom resolveAddress : List Char → List Char → Option (List Char) → Option (List Char)
-- axioms-end

-- pure-start
/- The rendered display produced for a related object reference:
   * `link addr label` — a hyperlink to the resolved address `addr`, captioned
     with the object's label;
   * `plain label` — the object's label on its own (no hyperlink), used when no
     address could be resolved. -/
inductive Rendered where
  | link (addr : List Char) (label : List Char)
  | plain (label : List Char)
deriving DecidableEq, Inhabited, Repr

/- How a resolution outcome is displayed: a resolved address becomes a captioned
   hyperlink; a failure to resolve falls back to the bare label. -/
def render (addr : Option (List Char)) (label : List Char) : Rendered :=
  match addr with
  | some a => Rendered.link a label
  | none   => Rendered.plain label
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the display for a related object reference shown on a page whose
   application context is named `appName`.

   The route `viewName` together with the object's key `pk` identifies the
   target; the display caption is the object's label `objLabel`. Desired
   behaviour: the target address is resolved WITHIN the page's own application
   context `appName` — not within the ambient default — so that a page served
   under a non-default application context links to the address belonging to
   that same context. When the route resolves, the result is a hyperlink to that
   context-relative address captioned with the label; when it does not resolve,
   the result is the bare label.

   All four inputs are read-only (none `mut`): the routine consumes the route
   name, key, application-context name, and label, and produces the display,
   mutating none of them (directive 5). Strings are modeled per code point as
   `List Char`; the application context is supplied as `some appName` because
   the page always carries a context name (mapping.md §2). The result is pinned
   exactly to the resolution performed within `appName`. -/
noncomputable section
method getAdminUrl (viewName : List Char) (pk : List Char) (appName : List Char)
    (objLabel : List Char) return (out : Rendered)
  ensures out = render (resolveAddress viewName pk (some appName)) objLabel
  do
    -- impl-start
    -- Resolve the route within the page's own application context, then display
    -- the resolved address as a captioned hyperlink, or the bare label if the
    -- route does not resolve.
    match resolveAddress viewName pk (some appName) with
    | some a => return Rendered.link a objLabel
    | none   => return Rendered.plain objLabel
    -- impl-end
end

prove_correct getAdminUrl by
  loom_solve
  all_goals simp_all [render]
