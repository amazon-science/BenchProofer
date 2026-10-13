# P2 adversarial audit — astropy__astropy-13398

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1.1/1.2/1.3: ITRS exposes a `location` frame attribute defaulting to Earth center,
and accepts an EarthLocation without error."""
import sys
import numpy as np
import astropy.units as u
from astropy.coordinates import ITRS, EarthLocation

# 1.1 + 1.2: location attribute exists and defaults to geocentre
f = ITRS(x=1000*u.km, y=2000*u.km, z=3000*u.km)
assert 'location' in f.frame_attributes, "ITRS has no 'location' frame attribute"
loc = f.location
gx, gy, gz = loc.to_geocentric()
print("default location geocentric (m):", gx, gy, gz)
tol = 1e-6 * u.m
assert abs(gx) < tol and abs(gy) < tol and abs(gz) < tol, "default location not geocentre"

# 1.3: accepts a location keyword and retains it
site = EarthLocation(lat=52*u.deg, lon=13*u.deg, height=100*u.m)
f2 = ITRS(x=1*u.km, y=2*u.km, z=3*u.km, location=site)
sx, sy, sz = f2.location.to_geocentric()
ex, ey, ez = site.to_geocentric()
print("retained location geocentric (m):", sx, sy, sz)
assert np.isclose(sx.to_value(u.m), ex.to_value(u.m)) and \
       np.isclose(sy.to_value(u.m), ey.to_value(u.m)) and \
       np.isclose(sz.to_value(u.m), ez.to_value(u.m)), "location not retained"

# 1.4: obstime attribute still present, default Cartesian rep
assert 'obstime' in f.frame_attributes
from astropy.coordinates import CartesianRepresentation, CartesianDifferential
assert f.default_representation is CartesianRepresentation
assert f.default_differential is CartesianDifferential
print("PASS: ITRS location attribute present, defaults geocentre, retains, obstime+cartesian intact")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.4 (POSITIVE CONTROL): object along local vertical above a site -> AltAz alt == 90 deg
(within ~1 uas). Also exercises Req 2.1 (ITRS->AltAz transform registered).
Fails at base: ITRS has no `location` attribute and no direct ITRS->AltAz transform."""
import sys
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import ITRS, AltAz, EarthLocation

t = Time('2020-01-01T12:00:00')
site = EarthLocation(lat=42.5*u.deg, lon=-71.0*u.deg, height=200*u.m)
# site-relative vertical: geodetic up direction. Take the site's own geocentric
# position and place object further out along the same geodetic vertical.
lon, lat, height = site.to_geodetic('WGS84')
# object 100 km straight up above site
obj = EarthLocation.from_geodetic(lon, lat, height + 100*u.km)
ox, oy, oz = obj.to_geocentric()
sx, sy, sz = site.to_geocentric()
# site-relative Earth-fixed vector
rel = ITRS(x=(ox-sx), y=(oy-sy), z=(oz-sz), obstime=t, location=site)
aa = rel.transform_to(AltAz(obstime=t, location=site, pressure=0*u.hPa))
print("altitude (deg):", aa.alt.to_value(u.deg))
resid = abs(aa.alt.to_value(u.arcsec) - 90*3600)
print("residual from 90 deg (arcsec):", resid)
assert resid < 1e-6, "altitude not 90 deg within 1 uas"
print("PASS: straight-overhead -> alt 90 deg")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.5: directly-overhead object -> HADec: hour angle == 0, dec == site geodetic latitude
(within ~1 uas)."""
import sys
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import ITRS, HADec, EarthLocation

t = Time('2020-01-01T12:00:00')
site = EarthLocation(lat=42.5*u.deg, lon=-71.0*u.deg, height=200*u.m)
lon, lat, height = site.to_geodetic('WGS84')
obj = EarthLocation.from_geodetic(lon, lat, height + 100*u.km)
ox, oy, oz = obj.to_geocentric()
sx, sy, sz = site.to_geocentric()
rel = ITRS(x=(ox-sx), y=(oy-sy), z=(oz-sz), obstime=t, location=site)
hd = rel.transform_to(HADec(obstime=t, location=site, pressure=0*u.hPa))
print("HA (arcsec):", hd.ha.to_value(u.arcsec), "Dec (deg):", hd.dec.to_value(u.deg))
ha_resid = abs(hd.ha.wrap_at(180*u.deg).to_value(u.arcsec))
dec_resid = abs(hd.dec.to_value(u.arcsec) - lat.to_value(u.deg)*3600)
print("HA residual (arcsec):", ha_resid, "Dec residual from lat (arcsec):", dec_resid)
assert ha_resid < 1e-6, "hour angle not 0"
assert dec_resid < 1e-6, "dec not equal to site latitude"
print("PASS: overhead -> HA 0, Dec = latitude")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2.8: ITRS -> AltAz -> ITRS round-trip identity, WITH refraction on the forward step.
Recovered Earth-fixed Cartesian components match the original."""
import sys
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import ITRS, AltAz, EarthLocation

t = Time('2020-01-01T12:00:00')
site = EarthLocation(lat=35.0*u.deg, lon=100.0*u.deg, height=1000*u.m)
# arbitrary site-relative earth-fixed vector (a few km up and to the side)
rel = ITRS(x=3*u.km, y=5*u.km, z=40*u.km, obstime=t, location=site)
aa = rel.transform_to(AltAz(obstime=t, location=site,
                            pressure=1000*u.hPa, temperature=10*u.deg_C,
                            relative_humidity=0.3, obswl=0.5*u.micron))
back = aa.transform_to(ITRS(obstime=t, location=site))
o = rel.cartesian.xyz.to_value(u.km)
r = back.cartesian.xyz.to_value(u.km)
print("orig (km):", o)
print("recovered (km):", r)
diff = np.max(np.abs(o - r))
print("max component diff (km):", diff, " (mm):", diff*1e6)
# round-trip must recover components; refraction add/remove is not exactly
# reversible at machine precision, so use a ~1 micron (1e-9 km) *arcsec-scale*
# tolerance: 1e-6 km == 1 mm is generous; observed residual ~2e-8 km.
assert diff < 1e-6, "round-trip not identity within ~1 mm"
print("PASS: ITRS->AltAz(refracted)->ITRS round-trip identity")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.1: direct ITRS-route AltAz agrees with celestial (CIRS) route for a distant
finite-distance source, azimuth+alt within ~0.1 mas and distance within ~10 cm,
both with zero and positive pressure.
Also Req 2.6/2.7 (refraction on/off) implicitly exercised."""
import sys
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import ITRS, AltAz, CIRS, EarthLocation, SkyCoord

t = Time('2020-06-15T04:00:00')
site = EarthLocation(lat=-30.0*u.deg, lon=20.0*u.deg, height=1500*u.m)

# a distant source with a finite distance, given in CIRS about the site (topocentric)
usph = CIRS(ra=83.0*u.deg, dec=-20.0*u.deg, distance=1.5e8*u.km,
            obstime=t, location=site)

for pressure in (0*u.hPa, 1000*u.hPa):
    aa_frame = AltAz(obstime=t, location=site, pressure=pressure,
                     temperature=5*u.deg_C, relative_humidity=0.2, obswl=0.55*u.micron)
    # celestial route
    aa_cel = usph.transform_to(aa_frame)
    # ITRS route: CIRS -> ITRS(site) then ITRS -> AltAz
    itrs = usph.transform_to(ITRS(obstime=t, location=site))
    aa_itrs = itrs.transform_to(aa_frame)

    dsky = aa_cel.separation(aa_itrs).to_value(u.arcsec) * 1000.0  # mas
    ddist = abs(aa_cel.distance.to_value(u.m) - aa_itrs.distance.to_value(u.m))
    print(f"pressure={pressure}: sky sep (mas)={dsky:.6g}, dist diff (m)={ddist:.6g}")
    assert dsky < 0.1, f"sky separation {dsky} mas exceeds 0.1 mas at pressure {pressure}"
    assert ddist < 0.10, f"distance diff {ddist} m exceeds 10 cm at pressure {pressure}"

print("PASS: direct ITRS route agrees with celestial route (AltAz)")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.3 + 4.4 + 5.2: CIRS -> ITRS(same location) -> CIRS round-trip.
Same obstime: RA/Dec recovered (topocentric round-trip identity, Req 4.3).
Different obstime: RA/Dec do NOT match (Req 4.4)."""
import sys
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import ITRS, CIRS, EarthLocation

t = Time('2020-01-01T00:00:00')
t2 = Time('2020-07-01T00:00:00')
site = EarthLocation(lat=19.8*u.deg, lon=-155.5*u.deg, height=4200*u.m)

cirs = CIRS(ra=120.0*u.deg, dec=25.0*u.deg, distance=2.0e7*u.km,
            obstime=t, location=site)

# same-obstime, same-location round-trip -> identity (Req 4.3)
itrs = cirs.transform_to(ITRS(obstime=t, location=site))
back = itrs.transform_to(CIRS(obstime=t, location=site))
dra = (back.ra - cirs.ra).wrap_at(180*u.deg).to_value(u.mas)
ddec = (back.dec - cirs.dec).to_value(u.mas)
print("same-obstime round-trip dRA(mas)=", dra, " dDec(mas)=", ddec)
assert abs(dra) < 1.0 and abs(ddec) < 1.0, "topocentric same-obstime round-trip not identity"

# different obstime -> should NOT match (Req 4.4). Mirror the gold test:
# ITRS + final CIRS both at a DIFFERENT obstime than the source (epoch shift
# actually applied; not simply reversed back to the source frame).
itrs2 = cirs.transform_to(ITRS(obstime=t2, location=site))
back2 = itrs2.transform_to(CIRS(obstime=t2, location=site))
dra2 = abs((back2.ra - cirs.ra).wrap_at(180*u.deg).to_value(u.arcsec))
ddec2 = abs((back2.dec - cirs.dec).to_value(u.arcsec))
print("diff-obstime round-trip dRA(arcsec)=", dra2, " dDec(arcsec)=", ddec2)
assert (dra2 > 1.0 or ddec2 > 1.0), "diff-obstime round-trip unexpectedly matched"

print("PASS: CIRS<->ITRS location-aware round-trip (identity same t, drift diff t)")
sys.exit(0)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
"""Req 5.1/5.3 (regression, SHALL keep): geocentric (default-location) round-trips.
CIRS->ITRS->CIRS at same obstime recovers RA/Dec; GCRS->ITRS->GCRS recovers RA/Dec."""
import sys
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import ITRS, CIRS, GCRS

t = Time('2019-03-21T18:00:00')

# geocentric CIRS <-> ITRS default location
cirs = CIRS(ra=45.0*u.deg, dec=-10.0*u.deg, distance=1.0e6*u.km, obstime=t)
itrs = cirs.transform_to(ITRS(obstime=t))
back = itrs.transform_to(CIRS(obstime=t))
dra = (back.ra - cirs.ra).wrap_at(180*u.deg).to_value(u.mas)
ddec = (back.dec - cirs.dec).to_value(u.mas)
print("geocentric CIRS round-trip dRA(mas)=", dra, "dDec(mas)=", ddec)
assert abs(dra) < 1.0 and abs(ddec) < 1.0, "geocentric CIRS round-trip regressed"

# GCRS <-> ITRS round-trip
gcrs = GCRS(ra=200.0*u.deg, dec=33.0*u.deg, distance=5.0e5*u.km, obstime=t)
itrs2 = gcrs.transform_to(ITRS(obstime=t))
back2 = itrs2.transform_to(GCRS(obstime=t))
dra2 = (back2.ra - gcrs.ra).wrap_at(180*u.deg).to_value(u.mas)
ddec2 = (back2.dec - gcrs.dec).to_value(u.mas)
print("GCRS<->ITRS round-trip dRA(mas)=", dra2, "dDec(mas)=", ddec2)
assert abs(dra2) < 1.0 and abs(ddec2) < 1.0, "GCRS<->ITRS round-trip regressed"

print("PASS: geocentric CIRS and GCRS round-trips preserved")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Req 2.4 (POSITIVE CONTROL): object along local vertical above a site -> AltAz alt == 90 deg
(within ~1 uas). Also exercises Req 2.1 (ITRS->AltAz transform registered).
Fails at base: ITRS has no `location` attribute and no direct ITRS->AltAz transform."""
import sys
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import ITRS, AltAz, EarthLocation

t = Time('2020-01-01T12:00:00')
site = EarthLocation(lat=42.5*u.deg, lon=-71.0*u.deg, height=200*u.m)
# site-relative vertical: geodetic up direction. Take the site's own geocentric
# position and place object further out along the same geodetic vertical.
lon, lat, height = site.to_geodetic('WGS84')
# object 100 km straight up above site
obj = EarthLocation.from_geodetic(lon, lat, height + 100*u.km)
ox, oy, oz = obj.to_geocentric()
sx, sy, sz = site.to_geocentric()
# site-relative Earth-fixed vector
rel = ITRS(x=(ox-sx), y=(oy-sy), z=(oz-sz), obstime=t, location=site)
aa = rel.transform_to(AltAz(obstime=t, location=site, pressure=0*u.hPa))
print("altitude (deg):", aa.alt.to_value(u.deg))
resid = abs(aa.alt.to_value(u.arcsec) - 90*3600)
print("residual from 90 deg (arcsec):", resid)
assert resid < 1e-6, "altitude not 90 deg within 1 uas"
print("PASS: straight-overhead -> alt 90 deg")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy__astropy-13398: direct topocentric ITRS<->AltAz/HADec transforms. 7 probes, each exit 0 iff its criterion holds; all run in the official image via nl_attack.

Coverage:
- probe_1: Req 1.1/1.2/1.3/1.4 - ITRS exposes `location` frame attr, defaults to geocentre, retains a supplied EarthLocation, keeps obstime + Cartesian rep/differential.
- probe_2 (POSITIVE CONTROL): Req 2.4/2.1 - object on local vertical above a site -> AltAz alt == 90 deg within 1 uas.
- probe_3: Req 2.5 - overhead object -> HADec HA==0, Dec==site geodetic latitude within 1 uas.
- probe_4: Req 2.8 - ITRS->AltAz(refraction added)->ITRS round-trip recovers Earth-fixed Cartesian components (residual ~2e-8 km; tol 1 mm).
- probe_5: Req 3.1 (+2.6/2.7) - direct ITRS route agrees with celestial (CIRS) route to <0.1 mas sky and <10 cm distance, at pressure 0 and 1000 hPa.
- probe_6: Req 4.3/4.4 - CIRS<->ITRS(site) round-trip: identity at same obstime, meaningful drift when final frame obstime differs.
- probe_7: Req 5.1/5.3 (regression) - geocentric CIRS<->ITRS and GCRS<->ITRS round-trips preserved.

Runs:
- PATCHED: all 7 HOLD (exit 0).
- BASE: probes 1-6 VIOLATED (no ITRS location / no direct transforms); probe_7 HOLDS at base (regression behavior pre-exists). Positive control probe_2 fails at base, holds patched => discriminates; prepatch reproduced.
- CANDIDATE weak.diff (gold patch MINUS the intermediate_rotation_transforms.py hunks, i.e. CIRS/TETE<->ITRS still force EARTH_CENTER, violating Req 4): REJECTED by probe_5 with a real 8769 mas disagreement between direct and celestial routes at pressure 0 (probes 1-4,6,7 still hold). This shows the suite discriminates a requirements-incomplete implementation.

Calibration notes: probe_4's initial 1e-9 km tolerance and probe_6's initially reversible diff-obstime round-trip were my modeling errors (not spec violations); corrected to mirror the gold hidden tests (test_itrs_topo_to_altaz_with_refraction, test_cirs_itrs_topo). No genuine violation found on the gold-patched tree; no probe-conforming alternative that also fails the harness was found.

Verdict: SOUND - >=5 probes hold on patched, positive control discriminates (fails base), and a plausible partial fix is rejected by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 7 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 7 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (7):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Req 2.4 (POSITIVE CONTROL): object along local vertical above a site -> AltAz alt == 90 deg
(within ~1 uas). Also exercises Req 2.1 (ITRS->AltAz transform registered).
Fails at base: ITRS has no `location` attribute and no direct ITRS->AltAz transform."""
import sys
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import ITRS, AltAz, EarthLocation

t = Time('2020-01-01T12:00:00')
site = EarthLocation(lat=42.5*u.deg, lon=-71.0*u.deg, height=200*u.m)
# site-relative vertical: geodetic up direction. Take the site's own geocentric
# position and place object further out along the same geodetic vertical.
lon, lat, height = site.to_geodetic('WGS84')
# object 100 km straight up above site
obj = EarthLocation.from_geodetic(lon, lat, height + 100*u.km)
ox, oy, oz = obj.to_geocentric()
sx, sy, sz = site.to_geocentric()
# site-relative Earth-fixed vector
rel = ITRS(x=(ox-sx), y=(oy-sy), z=(oz-sz), obstime=t, location=site)
aa = rel.transform_to(AltAz(obstime=t, location=site, pressure=0*u.hPa))
print("altitude (deg):", aa.alt.to_value(u.deg))
resid = abs(aa.alt.to_value(u.arcsec) - 90*3600)
print("residual from 90 deg (arcsec):", resid)
assert resid < 1e-6, "altitude not 90 deg within 1 uas"
print("PASS: straight-overhead -> alt 90 deg")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy__astropy-13398: direct topocentric ITRS<->AltAz/HADec transforms. 7 probes, each exit 0 iff its criterion holds; all run in the official image via nl_attack.

Coverage:
- probe_1: Req 1.1/1.2/1.3/1.4 - ITRS exposes `location` frame attr, defaults to geocentre, retains a supplied EarthLocation, keeps obstime + Cartesian rep/differential.
- probe_2 (POSITIVE CONTROL): Req 2.4/2.1 - object on local vertical above a site -> AltAz alt == 90 deg within 1 uas.
- probe_3: Req 2.5 - overhead object -> HADec HA==0, Dec==site geodetic latitude within 1 uas.
- probe_4: Req 2.8 - ITRS->AltAz(refraction added)->ITRS round-trip recovers Earth-fixed Cartesian components (residual ~2e-8 km; tol 1 mm).
- probe_5: Req 3.1 (+2.6/2.7) - direct ITRS route agrees with celestial (CIRS) route to <0.1 mas sky and <10 cm distance, at pressure 0 and 1000 hPa.
- probe_6: Req 4.3/4.4 - CIRS<->ITRS(site) round-trip: identity at same obstime, meaningful drift when final frame obstime differs.
- probe_7: Req 5.1/5.3 (regression) - geocentric CIRS<->ITRS and GCRS<->ITRS round-trips preserved.

Runs:
- PATCHED: all 7 HOLD (exit 0).
- BASE: probes 1-6 VIOLATED (no ITRS location / no direct transforms); probe_7 HOLDS at base (regression behavior pre-exists). Positive control probe_2 fails at base, holds patched => discriminates; prepatch reproduced.
- CANDIDATE weak.diff (gold patch MINUS the intermediate_rotation_transforms.py hunks, i.e. CIRS/TETE<->ITRS still force EARTH_CENTER, violating Req 4): REJECTED by probe_5 with a real 8769 mas disagreement between direct and celestial routes at pressure 0 (probes 1-4,6,7 still hold). This shows the suite discriminates a requirements-incomplete implementation.

Calibration notes: probe_4's initial 1e-9 km tolerance and probe_6's initially reversible diff-obstime round-trip were my modeling errors (not spec violations); corrected to mirror the gold hidden tests (test_itrs_topo_to_altaz_with_refraction, test_cirs_itrs_topo). No genuine violation found on the gold-patched tree; no probe-conforming alternative that also fails the harness was found.

Verdict: SOUND - >=5 probes hold on patched, positive control discriminates (fails base), and a plausible partial fix is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe probe.py ran green on gold-patched tree: default location==EARTH_CENTER, location kwarg accepted, straight-overhead alt=90/ha=0/dec=52deg within 1 uas, refraction changes altitude by >1 mas when pressure>0, AltAz->ITRS round-trip recovers x/y/z. Requirements pin the full changed observable behavior (the direct ITRS<->observed path plus the location-carrying intermediate transforms), not a narrow branch or helper. Modeling boundary is correct and biconditional-adequate.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is highly detailed: it includes a full draft implementation (itrs_to_observed_mat/itrs_to_observed/observed_to_itrs), the ITRS<->AltAz/HADec transform registration, to_geodetic('WGS84'), the location attribute, the subtract-site->topocentric-ITRS->transform pattern, and names test_straight_overhead(). The requirements localize the change to public modules/classes (builtin_frames, ITRS/CIRS/TETE) and translate behavior using only public API attributes (location, obstime, pressure, temperature, relative_humidity, obswl). None of the gold-patch fix-invented identifiers leak: itrs_to_altaz_mat, itrs_to_hadec_mat, altaz_to_hadec_mat, add_refraction, remove_refraction, CELMIN/SELMIN/NORTH_POLE, and the new file itrs_observed_transforms.py are all absent. No test names/paths, parametrization ids, or quoted test/gold code appear. Borderline-but-acceptable: (1) tolerances (~0.1 mas, ~10 cm, ~1 uas) match the test atols but state required precision of a behavior rather than transmitting test code; (2) 'precessed-geocentric and TEME loopbacks' (Req 5.5) faintly echoes PASS_TO_PASS names but describes well-known astropy regression behaviors, not test identifiers or parametrization; (3) refraction requirements go beyond the problem_statement (which deferred refraction) yet are expressed via public frame attributes, not the hidden erfa-based algorithm. Nothing reconstructs the hidden tests.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
