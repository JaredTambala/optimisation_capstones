# CAP-001 Professional Candidate Pack

You are acting as an independent optimisation consultant to Asterion Industrial
Controls Group. Start with `CAPSTONE_BRIEF.md`, then read
`TASK_REQUIREMENTS.md`, `APPLICATION_AND_EVIDENCE_GUIDE.md` and
`ASSESSMENT_RUBRIC.md`.

## Your principal deliverable

You must build, submit and defend a working end-to-end full-stack
decision-support application. It must give business users an interactive
interface, persistent governed data, an integrated algebraic MILP or MINLP
optimisation workflow, and interpretable results. A model plus scripts,
notebooks, APIs, static reports or interface mock-ups is not a substitute for
the working application.

You choose the architecture, framework, modelling library, solver route,
persistence technology and repository structure. That design freedom does not
make the application optional.

## What is supplied

- six complete, interchangeable 25-table planning datasets: BASE, SCN-01, SCN-02, SCN-03, SCN-04, SCN-05;
- a data dictionary and machine-readable schemas for source data, standard
  result evidence and application data-governance evidence;
- a miniature accounting fixture with published reconciliation controls;
- a non-prescriptive BASE benchmark that your own submitted model must reproduce
  at the published service and objective-quality grain; and
- guidance on cost policy, example datasets, AI-assisted work and production
  readiness.

Every dataset contains the whole P01–P12 planning reality known when the P01
plan is prepared. The named packages are examples, not a closed scenario menu.
Your product must also accept a new complete schema-valid dataset identity.

## What is deliberately not supplied

There is no starter application, solver configuration, submission manifest,
required repository tree or prescribed command vocabulary. Select and justify
your own application architecture, algebraic modelling library, MILP or MINLP
formulation, solver route, persistence design and test strategy.

Your own README must tell an independent reviewer how to install the product, run its tests,
reproduce BASE, launch and use the application, initiate or retrieve a solve,
find the submitted evidence, and understand runtime or licensing assumptions.

## Integrity

`release_manifest.json` identifies every supplied file. `CHECKSUMS.sha256`
provides a portable digest list. Source CSVs are immutable starting snapshots;
the application must import their rows into governed, history-preserving
logical masters before user changes are published as a new dataset version.
