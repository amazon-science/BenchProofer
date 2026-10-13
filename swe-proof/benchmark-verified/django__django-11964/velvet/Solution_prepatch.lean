import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The textual rendering of the member's underlying
--  value is modeled DEEPLY in the `pure` region below: an integer payload is
--  rendered in its usual decimal form (`toString`), a text payload is its own
--  characters. Nothing the proof consumes is left to an axiom, so there is no
--  axiom_check.py and G-AX is skipped.)
-- axioms-end

-- pure-start
/- The payload an enumerated member carries. The two shapes the modeled domain
   distinguishes are the only ones the rendering reacts to differently:
     * `intVal n` — a numeric payload;
     * `strVal s` — a textual payload (a sequence of code points). -/
inductive MemberValue where
  | intVal (n : Int)
  | strVal (s : List Char)
  deriving Inhabited

/- An enumerated member, reduced to the only data the rendering observes:
     * `value`        — its underlying payload (numeric or textual);
     * `defaultLabel` — the generic object rendering a member carries by default
                        (the qualified `Owner.NAME` token, e.g. the literal
                        `MyChoice.FIRST_CHOICE` shown in the problem statement). -/
structure Member where
  value : MemberValue
  defaultLabel : List Char
  deriving Inhabited

/- Render a payload as text: a numeric payload becomes its decimal text form,
   a textual payload is exactly its own code points. This is the textual form of
   the value "cast to str" — decimal digits (with a leading minus for a negative
   number, no separators or leading zeros) for a number, identity for text. -/
@[grind] def renderValue : MemberValue → List Char
  | .intVal n => (toString n).toList
  | .strVal s => s
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render an enumerated member as text. The result must be the textual form of
   the member's own underlying value — so that a member used as a plain value
   (rendered into templates, sent to other systems, compared as text) shows
   the value it stands for, not a generic object token. `member` is a read-only
   input and is not mutated (directive 5). -/
method memberToStr (member : Member) return (out : List Char)
  ensures out = renderValue member.value
  ensures (∀ n : Int, member.value = MemberValue.intVal n → out = (toString n).toList)
  ensures (∀ s : List Char, member.value = MemberValue.strVal s → out = s)
  do
    -- impl-start
    -- Pre-image skeleton: a member renders via the generic default object token
    -- (its `defaultLabel`, the qualified `Owner.NAME` form), NOT the textual form
    -- of its underlying value. The frozen spec requires `renderValue member.value`,
    -- so prove_correct MUST fail (G-DIFF).
    let result : List Char := member.defaultLabel
    return result
    -- impl-end

prove_correct memberToStr by
  loom_solve
