# Private model-viability harness

This package is retained as private authoring infrastructure for CAP-001. It is
not student starter code, a reference submission, or a required architecture.

Its purpose is narrow:

- load the controlled raw contracts;
- detect physical infeasibility in fixture or generated data;
- produce a local-fact physical seed and check that recursive-cost semantics can
  be formulated;
- reconcile quantities and values independently; and
- help calibrate whether generated cases contain meaningful decisions.

The package was frozen on 18 August 2026. CN-005 later required narrow contract
maintenance and one BASE benchmark build; that incumbent is calibration
evidence, not a reference submission. Do not extend the package into a
production solver, output pipeline or application. Reopen it only when a
controlled contract changes, generated data exposes a feasibility/accounting
defect, calibration fails to create meaningful trade-offs, or the smoke tests
stop running in the authoring environment.

The governing specification, decision configuration, data contracts, student
brief and assessment rubric remain authoritative. The implementation here does
not prescribe Pyomo or any other modelling library for student submissions.
