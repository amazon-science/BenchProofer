# mapping.md — django__django-11532

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a5308514fb4bc5086c9a16a8a24a945eeebb073c`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo files under change: `django/utils/encoding.py` (new helper),
`django/core/mail/utils.py` (the F2P-tested cached-host-name site), plus four
behaviour-identical call-site swaps (`django/core/mail/message.py`,
`django/core/validators.py` ×2, `django/utils/html.py` ×2).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `ascii_compatible_domain(domain)` | the new helper `punycode(domain)` — `django/utils/encoding.py` (added after `escape_uri_path`, ~line 218 post-patch); body `return domain.encode('idna').decode('ascii')` | the modeled new reusable transform (ASCII-compatible / ToASCII encoding of a domain label) |
| `cached_host_name(platform_name)` | `CachedDnsName.get_fqdn(self)` — `django/core/mail/utils.py:14-17` | the F2P-tested changed function: the cached host name, now obtained by passing `socket.getfqdn()` through the transform |
| `ace_seq(domain)` *(axiom — A-consumed)* | `str.encode('idna').decode('ascii')` — CPython stdlib `encodings/idna.py` (`Codec.encode` → ToASCII per RFC 3490), invoked by the new `punycode` helper | unchanged stdlib callee: the pure ACE value of a well-formed label |
| `ace_encode(domain)` *(axiom — A-consumed, impl face)* | same `str.encode('idna').decode('ascii')` | impl-callable face of the same callee, TOTAL: on a label with an ACE it yields a freshly-built ASCII list equal to `ace_seq`; on any other label it yields no value and reports the codec's out-of-band condition |
| `valid_label(domain)` *(axiom — A-consumed, characteristic predicate)* | the implicit set of labels on which `encode('idna')` answers with a value rather than raising `UnicodeError` | the characteristic predicate of the callee's value-yielding set — used to state BOTH halves of the outcome partition, not to exclude an input |
| `LabelNotEncodable` | the condition the codec reports when a label has no ACE (`UnicodeError` out of `encode('idna')`, propagated by the gold helper, which has no handler) | carrier for the out-of-band outcome; user-defined because a builtin exception in an `Exsures` crashes the Nagini translator. No incidental detail (type identity, message) is pinned — only which of the two outcomes occurred |
| `all_ascii(s)` *(deep pure spec)* | the observable property: every code point of the ACE result is < 128 | pure spec: the all-ASCII predicate, modeled deeply (front-recursive fold) |
| `seq_host_witness()` / `seq_ace_witness()` | the worked example: hostname `漢字` (U+6F22 U+5B57) → ACE `xn--p8s937b` | pure spec: the witness label and its ACE, as code-point sequences |

The pre-patch repo symbol the change replaces at the cached-host-name site
(for the refinement audit, not referenced from the consumer spec view):
`self._fqdn = socket.getfqdn()` (`utils.py:16`) — the raw platform name cached
with NO ACE transform applied.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the `domain` argument of `punycode`, the `socket.getfqdn()` return, the cached `_fqdn`, the `punycode` return) | `List[int]` of Unicode code points | `s[k]` ↔ `xs[k] == ord(s[k])`; `len(s)` ↔ `len(xs)`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `socket.getfqdn()` call (`utils.py:16`) | the input parameter `platform_name: List[int]` of `cached_host_name` | the value the platform reports for the host name; the cached-host-name function reads it once. Modeled as the function input (an unchanged callee whose return is the modeled input) — the patch does not change `socket.getfqdn`; it only wraps its result. |
| the `self._fqdn = ...` cache assignment + `hasattr` memoization (`utils.py:15,16`) | omitted (caching is observationally the identity on the value) | the memoization only avoids re-calling `socket.getfqdn`; the cached VALUE is what the F2P test observes (it is read out as the Message-ID domain). Modeled as the returned value. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `ace_seq` / `ace_encode` ↔ `str.encode('idna').decode('ascii')` (A-consumed)
**Callee:** CPython `str.encode('idna')` (the `idna` codec, `Lib/encodings/idna.py`,
`Codec.encode`), implementing the IDNA **ToASCII** operation of RFC 3490
(nameprep + Punycode + the `xn--` ACE prefix), then `.decode('ascii')`. This is
exactly the body of the gold patch's new `punycode()` helper
(`return domain.encode('idna').decode('ascii')`).

The axiom encodes the **weakest** property the proof consumes:

  for any **well-formed** label (one on which the codec returns normally),
  the result is **all-ASCII** (every code point < 128).

This is necessarily true: the final step is `.decode('ascii')`, which raises
unless every byte is < 128; so any value that returns at all is all-ASCII.
A concrete **witness** pins one non-ASCII label so the proof is not vacuous and
the F2P-observed value is fixed:

  `漢字` (U+6F22 U+5B57) → `xn--p8s937b` (the eleven ASCII code points
  `120,110,45,45,112,56,115,57,51,55,98`).

`encode('idna')` raises `UnicodeError` on labels the standard's label-shape rules
reject (empty labels, over-long labels, doubled/leading separators). The gold
helper has **no** handler around its body, so that condition PROPAGATES to its
caller and is part of the callee's observable behaviour, not an excluded case.
The axiom therefore encodes the callee as TOTAL over a two-outcome partition:

  * `ace_seq(domain)` is the PURE face and is stated where a value exists
    (`Requires(valid_label(domain))`), giving the all-ASCII property and the
    witness value;
  * `ace_encode(domain)` is the impl-callable face and is declared with **no**
    label-shape precondition. It pins both halves: a value comes back only for a
    label that has an ACE (`Ensures(valid_label(ToSeq(domain)))`, so no
    substitute value can be invented for a label with none), and every other
    label is reported out of band with the label unchanged
    (`Exsures(LabelNotEncodable, … and not valid_label(ToSeq(domain)))`).

`valid_label` is thus the characteristic predicate of the value-yielding set; the
two `Ensures`/`Exsures` clauses make the partition complementary by construction.
All of these bind to the single stdlib callee.

**Flag/configuration dependency:** the `idna` codec takes no options; the ACE
prefix `xn--` and the nameprep/Punycode algorithm are fixed by RFC 3490 and are
identical across every supported CPython 3.x (including the interpreter in this
instance's image). No `quote=`-style flag applies.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`str.encode('idna').decode('ascii')` on the worked witness, on boundary labels
covering both sides of the partition (pure-ASCII, mixed, and labels with no ACE
at all: empty, doubled/leading separators, over-long), and on 40 000 randomized
labels over an ASCII + non-ASCII alphabet, the second half biased toward the
out-of-band side. It asserts (a) the witness label yields a value and its ACE is
exactly `xn--p8s937b`; (b) every label the callee answers with a value gets an
all-ASCII result; (c) the two outcomes are complementary and exhaustive — a label
the codec rejects is never also answered with a value, so neither half of the
contract over-claims; and (d) BOTH tallies are non-empty, so neither half is
checked vacuously. Imports only the standard library. Exit 0 iff sound.
