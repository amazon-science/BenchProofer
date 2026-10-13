# Requirements: Direct topocentric transformations between ITRS and observed (AltAz / HADec) frames

## Introduction

In `astropy.coordinates`, the International Terrestrial Reference System frame
(`ITRS`) is an Earth-fixed Cartesian frame, while `AltAz` and `HADec` are the
"observed" horizontal frames tied to a site on the Earth's surface (an
`EarthLocation`). Historically the only way to go from an Earth-fixed position
of a nearby object (e.g. a satellite, an aircraft, a mountaintop) to an
observed `AltAz`/`HADec` direction was to route through the celestial
intermediate frames (`CIRS`/`GCRS`/`ICRS`). Because that route applies the
difference between geocentric and topocentric stellar aberration, it gives
counter-intuitive and apparently inaccurate results for near-Earth objects
whose positions are already expressed in an Earth-fixed frame.

This change adds a **direct** path that stays within the terrestrial frame: it
lets `ITRS` carry an observing-site `location`, and adds transformations
`ITRS <-> AltAz` and `ITRS <-> HADec` that convert by pure geometric rotation
about the site (plus optional atmospheric refraction), treating the Earth-fixed
position as time-invariant. The affected code lives in
`astropy/coordinates/builtin_frames` — the `ITRS` frame class and the frame
transformation graph that connects `ITRS`, `AltAz`, `HADec`, `CIRS`, and
`TETE`. The goal: an observer can subtract a site's Earth-fixed position from an
object's Earth-fixed position, place the result in a site-located `ITRS` frame,
and transform straight to `AltAz`/`HADec` (and back) with the geometrically
correct answer, while all pre-existing geocentric behavior is preserved.

## Requirement 1: ITRS frame carries an observing-site location

**User story:** As an astronomer working with Earth-fixed positions of nearby
objects, I want the `ITRS` frame to accept an observing-site location so that I
can express positions relative to a site and transform them to observed
horizontal coordinates.

**Acceptance criteria**

1. The `ITRS` frame SHALL expose a `location` frame attribute that holds an
   `~astropy.coordinates.EarthLocation` (an Earth-fixed observing site).
2. WHEN an `ITRS` frame is constructed without specifying `location`, THEN the
   frame SHALL default that attribute to the centre of the Earth (a geocentric
   location at the Earth-fixed origin).
3. WHEN an `ITRS` frame is constructed with a `location` keyword set to an
   `EarthLocation`, THEN the frame SHALL accept it and retain that value as the
   frame's `location`, without raising an error about an unexpected keyword.
4. The `ITRS` frame SHALL continue to expose its existing `obstime` attribute
   and its existing default Cartesian representation and differential.

## Requirement 2: Direct ITRS <-> AltAz / HADec transformations

**User story:** As an observer of near-Earth objects, I want to transform an
Earth-fixed position directly to and from `AltAz` and `HADec` about my site so
that I get topocentric horizontal coordinates without spurious aberration
effects introduced by routing through celestial frames.

**Acceptance criteria**

1. The system SHALL register frame transformations connecting `ITRS` with both
   `AltAz` and `HADec` in both directions (`ITRS -> AltAz`, `AltAz -> ITRS`,
   `ITRS -> HADec`, `HADec -> ITRS`), so that `transform_to` between these
   frames succeeds directly.
2. WHEN transforming an `ITRS` coordinate to an `AltAz` or `HADec` frame whose
   `location` and `obstime` already match the input frame's `location` and
   `obstime`, THEN the system SHALL treat the Earth-fixed position as
   time-invariant and produce the observed direction by a purely geometric
   rotation about the site, WITHOUT applying any stellar-aberration change.
3. WHEN transforming an `ITRS` coordinate to an `AltAz` or `HADec` frame whose
   `location` or `obstime` differs from the input's, THEN the system SHALL
   first bring the input to the output frame's `location` and `obstime` (via the
   Earth-fixed self-transform, which routes through the celestial intermediate
   frame and thereby accounts for the aberration difference) before performing
   the geometric rotation.
4. WHEN an object is positioned exactly along the local vertical above a site
   (its site-relative Earth-fixed vector points to the local zenith) and is
   transformed to that site's `AltAz` frame, THEN the resulting altitude SHALL
   equal 90 degrees (to within about 1 microarcsecond).
5. WHEN that same directly-overhead object is transformed to that site's
   `HADec` frame, THEN the resulting hour angle SHALL equal 0 and the resulting
   declination SHALL equal the site's geodetic latitude (each to within about 1
   microarcsecond).
6. WHEN the target `AltAz`/`HADec` frame has zero atmospheric `pressure`, THEN
   the system SHALL apply no refraction correction and produce purely geometric
   ("topocentric") horizontal coordinates.
7. WHEN the target `AltAz`/`HADec` frame has a positive atmospheric `pressure`,
   THEN the system SHALL apply an atmospheric refraction correction to the
   altitude, computed from the frame's `pressure`, `temperature`,
   `relative_humidity`, and `obswl` attributes.
8. WHEN a coordinate is transformed from `ITRS` to `AltAz` (or `HADec`) and then
   transformed back to the original site-located `ITRS` frame, THEN the
   recovered Earth-fixed Cartesian components SHALL match the original
   components (round-trip identity), including when refraction was applied on the
   forward step.
9. The site's geodetic longitude, latitude, and height used to orient the
   observed frame SHALL be derived from the frame's `location` on the WGS84
   ellipsoid.

## Requirement 3: Agreement with the celestial-route transformation

**User story:** As a user who trusts the existing `CIRS`/`ICRS`-mediated route
for topocentric observations, I want the new direct path to agree with it so
that switching to the direct path does not change my results.

**Acceptance criteria**

1. WHEN a distant celestial position with a finite distance is transformed to a
   site's `AltAz` frame via `ITRS`, THEN the resulting azimuth and altitude
   SHALL agree with the result of the pre-existing celestial-route transform to
   the same `AltAz` frame to within about 0.1 milliarcsecond, and the distance
   SHALL agree to within about 10 centimetres, both with zero pressure and with
   a positive pressure that adds refraction.
2. WHEN the same comparison is performed for a site's `HADec` frame, THEN the
   resulting hour angle and declination SHALL agree with the celestial-route
   result to within about 0.1 milliarcsecond and the distance to within about 10
   centimetres, both with and without refraction.
3. IF refraction was added on transforming into an observed frame with positive
   pressure, THEN transforming out of that observed frame SHALL remove the
   refraction so that a subsequent transform to a zero-pressure observed frame
   reproduces the unrefracted direction (to within about 0.1 milliarcsecond).

## Requirement 4: Location-aware CIRS/TETE <-> ITRS transformations

**User story:** As a user building site-located Earth-fixed coordinates, I want
the intermediate rotation transforms between `ITRS` and `CIRS`/`TETE` to respect
the ITRS site location so that topocentric round-trips are consistent.

**Acceptance criteria**

1. WHEN transforming between `CIRS` and `ITRS` (either direction), THEN the
   system SHALL carry the observing-site `location` through the transformation
   rather than forcing the geocentre, so that the `ITRS` result is referred to
   the same site as the `CIRS` frame.
2. WHEN transforming between `TETE` and `ITRS` (either direction), THEN the
   system SHALL likewise carry the observing-site `location` through the
   transformation.
3. WHEN a `CIRS` coordinate at a given `location` and `obstime` is transformed to
   an `ITRS` frame at the same `location` and then transformed back to the
   original `CIRS` frame, THEN the recovered right ascension and declination
   SHALL match the originals (topocentric round-trip identity).
4. WHEN that same `CIRS -> ITRS -> CIRS` round-trip is performed with the
   `ITRS`/target frames at a different `obstime` than the source, THEN the
   recovered right ascension and declination SHALL NOT match the originals
   (the epoch difference is meaningfully applied).

## Requirement 5: Preservation of existing geocentric behavior (regression)

**User story:** As an existing astropy user, I want all current geocentric and
celestial transformations to keep working unchanged so that adding site-located
ITRS support does not regress established results.

**Acceptance criteria**

1. WHEN geocentric `CIRS` and `ITRS` coordinates (with the default geocentric
   location) are round-tripped `CIRS -> ITRS -> CIRS` at the same `obstime`, THEN
   the recovered right ascension and declination SHALL match the originals, and
   the system SHALL keep this behavior.
2. WHEN the geocentric `CIRS <-> ITRS` round-trip is performed across different
   `obstime` values, THEN the recovered right ascension and declination SHALL
   NOT match the originals, preserving the established time-dependent behavior.
3. The system SHALL keep the existing `GCRS <-> ITRS` round-tripping behavior
   intact.
4. The system SHALL keep the existing indirect `CIRS <-> AltAz`/`HADec`
   ("straight overhead" via the celestial route) behavior intact, including that
   a source constructed to appear at the zenith for a geocentric observer yields
   altitude 90 degrees (and hour angle 0, declination equal to the site
   latitude) through that route.
5. The system SHALL keep all other existing `ICRS`/`GCRS`/`CIRS`/`TETE`/`TEME`
   transformations and their round-trips (including precessed-geocentric and
   TEME loopbacks) working as before.
