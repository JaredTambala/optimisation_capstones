# CAP-001 WP9 Professional Release Contract

## Document control

| Field | Value |
|---|---|
| Work package | WP9 — professional candidate release |
| Status | Implementation contract 1.1 |
| Date | 27 August 2026 |
| Governing design | Frozen WP8 engagement design, with assessment mechanics superseded by this contract |
| Decision owner | Capstone owner |
| Release effect | Governs assembly of the candidate release candidate; does not authorise final issue before the no-release gate |

## 1. Purpose

WP9 turns the frozen WP8 engagement into a professional training pack. The
candidate is a mature practitioner engaged to design, build and defend a
decision product. The release therefore defines the client outcome, supplied
data, mathematical and evidence boundaries, and assessment expectations. It
does not prescribe how the practitioner structures or operates their project.

The release is an engagement pack, not a mass-deployment scaffold or a uniform
programmatic-grading harness.

## 2. Candidate-owned delivery choices

The candidate owns:

- repository and directory structure;
- application architecture, framework and persistence technology;
- algebraic modelling library and compatible solver workflow;
- configuration representation and parameter-management approach;
- installation, test, solve and application-launch commands;
- graph technology, layout and interaction design;
- synchronous, asynchronous or controlled stored-result implementation; and
- the organisation of reports, code and supporting evidence.

The release must not contain a candidate submission manifest, supplied solver
configuration, fixed random seeds, prescribed commands, placeholder executable
scripts or a preferred source-tree layout. It may name technologies as
non-exclusive examples in explanatory guidance.

## 3. Required release contents

The candidate release contains:

1. the consultant brief and normative task requirements projected from the
   frozen WP8 sources;
2. concise application/evidence, model/status, AI-accountability and
   production-readiness guidance;
3. all six complete supplied dataset packages, each containing its own 25 CSV
   snapshots and immutable source manifest;
4. raw-data, result and application-evidence schemas;
5. the data dictionary, cost policy and supplied-example catalogue;
6. the miniature fixture and accounting walkthrough;
7. the approved public BASE benchmark and its non-prescriptive reproduction
   contract;
8. the concise candidate assessment rubric, without evaluator mechanics,
   hidden gates or scoring-policy commentary; and
9. a release manifest and checksums produced by private author-side assembly.

## 4. Machine-readable boundary

Machine-readable contracts are justified only where they protect supplied-data
meaning, provenance or independently verifiable result evidence. They do not
define the candidate's internal application design.

The release may therefore prescribe:

- the supplied CSV schemas and package manifests;
- standard exported result schemas;
- standard exported master-record, dataset-version and change evidence;
- benchmark and fixture contracts; and
- release checksums.

The release must not prescribe:

- an executable project manifest;
- a deployment description;
- a solver-option file;
- an application configuration file;
- an internal database schema; or
- a fixed command or path used to operate the candidate's product.

## 5. Supplied dataset semantics

Each supplied package is an immutable starting snapshot containing all 25
source tables. BASE and SCN-01 through SCN-05 are examples and source
provenance, not the runtime domain of the candidate's product.

The complete P01–P12 horizon in a selected package is known when its P01 plan
is created. An imported CSV row becomes the first version of a logical master
record inside the candidate's persistent application. The source CSV is
preserved; it is not itself the mutable or versioned master table.

The candidate's product must accept another complete schema-valid package with
an arbitrary identifier and provide the same supported behaviour.

## 6. Incoterm source and application semantics

The supplied Incoterm snapshot identifies the six initial modelling
abstractions and whether each is active. Its code schema permits another unique
schema-valid abstraction rather than enumerating only the supplied codes.

Effective dating, audit history, predecessor identity, authority and retirement
are applied when the source rows are imported into the application's master
data. Referenced history cannot be erased. A term is usable only when the
effective record and referencing contract are active.

## 7. Result and evidence identity

Every exported run is identified by an arbitrary published dataset version,
the resolved master-record set, a policy configuration and a method
configuration. Supplied package labels may remain as optional provenance but
cannot determine application behaviour.

Per-run and recursive-run evidence follows the frozen WP8 contract.
Comparison-set evidence consists of:

- a BASE benchmark reproduction record;
- a dataset-version comparison; and
- a policy-configuration comparison.

There is no `scenario_results.csv`, closed scenario comparison, synthetic
standard-cost baseline or dedicated recursive-cost reconciliation file.

## 8. Professional operating evidence

Instead of completing a supplied YAML manifest, the candidate documents in
their own README:

- prerequisites and installation;
- how to run tests;
- how to reproduce the submitted BASE evidence;
- how to launch and use the application;
- how to initiate or retrieve a solve;
- where standard exported evidence and reports can be found;
- the chosen stack, modelling library and solver route; and
- material environment, runtime and licensing assumptions.

The submitted work is reviewed through those documented instructions and its
observable outcomes. The rubric identifies the assessment categories; it does
not prescribe a grading workflow to the candidate.

## 9. Author-side release controls

The author repository retains a deterministic allow-list assembler and
clean-room validator. These controls validate the material issued by the
capstone author. They do not evaluate a candidate submission and are not
candidate implementation requirements.

The assembler must fail if the candidate pack contains a private generator,
`cap001_model`, viability harness, hidden test, hidden threshold, evaluator
prompt or unapproved reference material. The public BASE benchmark is an
explicit allow-list item.

Candidate submissions are reviewed against the published rubric using
evidence-grounded professional judgement. The assessor-side method is a
private, versioned AI-agent system prompt. It must not behave as a deterministic
submission evaluator, use a hidden allocation as an answer key, or turn file,
command or keyword checks into undisclosed pass/fail gates. The candidate
receives the task, evidence obligations and rubric, not the private review
workflow.

## 10. WP9 non-scope

WP9 does not:

- build an exemplar application or optimiser;
- provide candidate project code;
- implement WP10 scoring, caps, resubmission or calibration policy;
- require one operating system, programming language, framework or solver;
- sign off a production deployment; or
- issue the final student release before the later no-release gate.

## 11. Acceptance conditions

WP9 is accepted only when:

- all six complete packages and all public supporting material are assembled;
- the brief and requirements contain no WP1 placeholders or author-only prose;
- no student-facing YAML or prescribed project scaffold remains;
- dataset, Incoterm, version-lineage and output contracts implement the frozen
  WP8 position;
- the public pack contains the approved benchmark but no private model or
  calibration evidence;
- candidate-facing assessment material is limited to the concise rubric;
- the private AI review guide requires contextual, cited judgement and
  prohibits deterministic grading of submissions;
- manifests, hashes, schemas and row counts reproduce;
- a clean-room reader can understand the engagement and verify the supplied
  material without access to the private repository; and
- all inherited dataset, benchmark and repository tests pass.
