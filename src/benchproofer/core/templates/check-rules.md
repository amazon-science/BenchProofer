* `./check` judges a copy of the bundle, laid out as Benchproofer lays out the bundle you
  leave, with every gate a program decides, at level `oracle` whatever level it is given;
  nothing it records reaches the bundle. It prints a line as it starts each gate and each run
  of `conformance.py`, then each gate's verdict with its summary whole and where its evidence
  is, or that it did not run the gate; the review's gates are not among those it judges. Each
  `--only GATE` runs that gate alone. Each gate keeps its own time limits, a run of
  `conformance.py` or `axioms.py` stopping after $program_limit seconds, and all of them
  together can take tens of minutes.
