import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two carrier values this operation consumes — the
--  guessed media type and the compression-encoding label — are produced by an
--  unchanged upstream type-sniffer that is shared, untouched, by every branch;
--  its outputs are taken directly as the inputs of the modeled function
--  (provenance in mapping.md §3), so there is no outside contract for the proof
--  to consume and no `axiom` declaration.)
-- axioms-end

-- pure-start
/- The dedicated media type for a compression encoding label. When a file's name
   advertises a compression scheme, the response must announce that scheme's own
   media type rather than the media type of the wrapped (uncompressed) payload,
   so that a client does not silently inflate the bytes. Each recognised
   compression label has exactly one dedicated media type; an unrecognised or
   absent label (`none`) has none (`none`), and the wrapped payload's type is
   used instead (see `resolvedMediaType`). -/
def compressionMediaType (encoding : Option String) : Option String :=
  match encoding with
  | some "br"       => some "application/x-brotli"
  | some "bzip2"    => some "application/x-bzip"
  | some "compress" => some "application/x-compress"
  | some "gzip"     => some "application/gzip"
  | some "xz"       => some "application/x-xz"
  | _               => none

/- The media type announced for a payload, given the type guessed for its name
   (`guessed`) and any compression-encoding label (`encoding`). A recognised
   compression label wins and contributes its dedicated media type; otherwise
   the guessed type is used; and when neither is available the generic binary
   media type `application/octet-stream` is the fallback. -/
def resolvedMediaType (guessed encoding : Option String) : String :=
  (compressionMediaType encoding |>.orElse (fun _ => guessed)).getD
    "application/octet-stream"
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the media type to announce for a payload from two read-only inputs:
   the media type guessed for the payload's name (`guessed`, absent as `none`)
   and the payload's compression-encoding label (`encoding`, absent as `none`).

   Desired behaviour: when the name advertises a recognised compression scheme,
   the announced media type is that scheme's OWN dedicated media type — never the
   media type of the wrapped, uncompressed payload — so a client is not led to
   transparently decompress it. When there is no recognised compression scheme,
   the guessed media type is announced; and when even that is absent, the generic
   binary media type is announced. The result is therefore always a present
   (non-absent) media type.

   Both inputs are read-only and neither is declared `mut` (directive 5): the
   resolution only reads the guess and the encoding label, mutating nothing. -/
method resolveMediaType (guessed : Option String) (encoding : Option String)
    return (out : String)
  ensures out = resolvedMediaType guessed encoding
  do
    -- impl-start
    -- Pre-image skeleton: the compression-override table recognises only the
    -- three classic schemes and omits the `br` and `compress` labels, so a file
    -- named with one of those two schemes falls through to the wrapped payload's
    -- guessed media type. The frozen spec requires `resolvedMediaType`, which
    -- announces every recognised scheme's dedicated media type, so this MUST
    -- fail to verify on the `br` / `compress` cases.
    let chosen :=
      (match encoding with
       | some "bzip2" => some "application/x-bzip"
       | some "gzip"  => some "application/gzip"
       | some "xz"    => some "application/x-xz"
       | _            => none).orElse (fun _ => guessed)
    return chosen.getD "application/octet-stream"
    -- impl-end

prove_correct resolveMediaType by
  loom_solve
  simp [resolvedMediaType]
