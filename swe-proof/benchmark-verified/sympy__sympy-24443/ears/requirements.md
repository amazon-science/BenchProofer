# Requirements: Correct homomorphism checking on permutation groups

## Introduction

The group-theory utilities in `sympy.combinatorics.homomorphisms` construct a
`GroupHomomorphism` via the `homomorphism(domain, codomain, gens, images, check=True)`
factory. When `check` is true, the internal helper `_check_homomorphism(domain, codomain, images)`
verifies that the requested generator-to-image assignment actually respects the
domain's defining relations before a homomorphism object is returned.

The verification works by taking each defining relator of the domain's
presentation — a word over the generator symbols, expressed as a sequence of
`(symbol, power)` pairs (the word's `array_form`) — mapping each generator to
its assigned codomain image, forming the ordered product of those images raised
to the corresponding powers, and requiring that product to be the codomain
identity.

For a `PermutationGroup` domain this check was broken: relator words can contain
*inverted* generators, and the routine's attempt to recover the domain generator
from a word element (`r[i] in gens`) failed whenever `r[i]` was an inverse. As a
consequence, even a valid assignment was rejected. Concretely,
`homomorphism(DihedralGroup(3), DihedralGroup(3), DihedralGroup(3).generators, DihedralGroup(3).generators)`
raised `ValueError: The given images do not define a homomorphism` instead of
constructing the (identity) homomorphism, which is in fact an isomorphism.

The goal is to make relator evaluation robust for permutation-group domains
(including inverted generators in relators) while preserving the existing
behavior for free-group and finitely-presented-group domains and codomains.

## Requirement 1: Valid permutation-group generator maps are accepted

**User story:** As a user building a group homomorphism from a `PermutationGroup`,
I want a mapping of the domain's generators to codomain elements that genuinely
respects the group's defining relations to be accepted, so that I can obtain the
homomorphism object instead of a spurious error.

**Acceptance criteria**

1. WHEN `homomorphism` is called with a `PermutationGroup` domain, a `check`
   value that is true, and an `images` assignment (one image per supplied
   generator) that respects every defining relation of the domain, THEN
   `homomorphism` SHALL return a `GroupHomomorphism` object and SHALL NOT raise
   `ValueError`.
2. WHEN `homomorphism` is called with `domain` and `codomain` both equal to
   `DihedralGroup(3)` and with `gens` and `images` both equal to that group's
   `generators` (the identity assignment), THEN `homomorphism` SHALL return a
   `GroupHomomorphism` object without raising.
3. The system SHALL treat a generator map as respecting the domain's defining
   relations if and only if, for every defining relator word, the ordered
   product of the assigned images raised to their respective powers equals the
   codomain identity.
4. IF the supplied generator map does not respect some defining relation of the
   domain, THEN `homomorphism` (with `check` true) SHALL raise `ValueError`
   reporting that the given images do not define a homomorphism.

## Requirement 2: Relator words with inverted generators are handled

**User story:** As a maintainer, I want relator evaluation to be correct for
every element of a relator word, including inverse generators, so that
permutation groups whose relations involve inverses are checked correctly.

**Acceptance criteria**

1. WHEN `_check_homomorphism` evaluates a defining relator of a
   `PermutationGroup` domain whose word contains an inverted generator, THEN it
   SHALL map that word element to the assigned image (using the corresponding
   power, so an inverse contributes a negative power) rather than failing to
   resolve the generator.
2. The system SHALL derive each word element's generator from the relator's
   `(symbol, power)` representation, so that both a generator and its inverse
   resolve to the same domain generator and thus to the same assigned image.
3. WHEN evaluating a relator word, THEN the system SHALL accumulate the images
   in the word's order and raise each image to its associated power, so that the
   computed product reflects the word as written.

## Requirement 3: The resulting homomorphism reflects the intended map

**User story:** As a user, I want the constructed homomorphism to actually act
as the generator assignment I supplied, so that structural queries about it are
correct.

**Acceptance criteria**

1. WHEN a `GroupHomomorphism` is constructed from the identity assignment on
   `DihedralGroup(3)` (each generator mapped to itself), THEN querying whether it
   is an isomorphism SHALL report that it is.
2. WHEN a `GroupHomomorphism` is applied to a domain generator, THEN it SHALL
   return the codomain image that was assigned to that generator.

## Requirement 4: Existing free-group and finitely-presented-group behavior is preserved

**User story:** As an existing user relying on homomorphisms and isomorphisms
between free groups and finitely presented groups, I want that behavior
unchanged, so that the fix does not regress previously working constructions.

**Acceptance criteria**

1. The system SHALL continue to determine the defining relators from the domain
   directly when the domain already exposes relators (a free group or finitely
   presented group), and otherwise from the domain's computed presentation.
2. WHEN `homomorphism` is called with a free-group or finitely-presented-group
   domain and a valid generator assignment, THEN it SHALL construct the
   homomorphism, and SHALL keep correctly identifying whether that homomorphism
   is injective, surjective, and/or an isomorphism.
3. WHEN the codomain is a finitely presented group and equality of the computed
   relator image to the identity cannot be decided directly, THEN the system
   SHALL keep attempting the decision via the codomain's rewriting system before
   concluding.
4. The system SHALL keep validating the caller's arguments: it SHALL reject a
   domain or codomain that is not a supported group type, generators that are
   not a subset of the domain's generators, images that are not elements of the
   codomain, and an image count that does not match the generator count.
5. WHILE `check` is false, `homomorphism` SHALL construct and return the
   `GroupHomomorphism` without performing the relation verification.
