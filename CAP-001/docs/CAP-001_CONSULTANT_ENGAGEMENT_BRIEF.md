# CAP-001 Consultant Engagement Brief

## Document control

| Field | Value |
|---|---|
| Client | Asterion Industrial Controls Group |
| Engagement | Tier-N supply-chain planning, end-to-end cost and resilience decision support |
| Status | WP8 frozen 1.0 — controlled source for WP9 student-release authoring |
| Date | 27 August 2026 |
| Intended reader | Candidate acting as an independent optimisation consultant |
| Planning window | P01–P12, 4 January–28 March 2027 |
| Reporting currency | EUR |

## 1. The engagement

Asterion Industrial Controls Group is a European manufacturer of industrial
electrical-control and automation equipment. It operates plants in Birmingham,
Dortmund, Katowice and Zaragoza and depends on a multi-tier international
supplier network for raw materials, processed components and finished
assemblies.

Asterion wants a decision-support product that helps its European supply-
planning and category-management teams decide what to source, ship, transform
and hold over the next twelve weeks. The recommendation must protect service,
represent how value accumulates through the supply network and expose the cost
and operational consequences of resilience choices.

You are being engaged to design, build and defend that product. Asterion is not
commissioning an isolated optimisation script or a set of static charts. It
wants a usable application through which its people can maintain a governed
data reality, explore the network, request a plan and understand why the
recommendation changes.

The principal deliverable is a working, end-to-end full-stack decision-support
application. It must provide a business-user interface, persistent governed
data handling and an integrated optimisation workflow. A collection of scripts,
notebooks, static reports, API endpoints or interface mock-ups without that
working application does not satisfy the engagement.

## 2. The decision Asterion needs

For a selected complete dataset and authorised policy configuration, advise
Asterion:

> What sourcing, shipment, production and inventory plan should it use over
> P01–P12; how do service, recursively accumulated end-to-end value and
> resilience affect that plan; and what action should the business take?

The recommendation should distinguish a robust business decision from a merely
feasible calculation. It must identify material trade-offs, operational
caveats, solver limitations and matters requiring management approval or
follow-up.

## 3. Planning context

Each dataset represents one complete deterministic planning reality. The whole
P01–P12 horizon—including dated constraints, disruption assumptions and
recoveries—is available when the P01 plan is prepared. Asterion may therefore
make advance commitments or position inventory for conditions occurring later
in the horizon.

The engagement does not ask you to model an unexpected event revealed after
execution begins. It does not require stochastic programming,
non-anticipativity or frozen decisions inherited from an earlier run.

The terminal demand in the selected dataset is the business requirement to be
served. Asterion expects the recommendation to respect approved relationships,
commercial terms, transport timing, production recipes, capacity, inventory
and service priorities across the complete multi-tier network.

Cost data is available only for the business concern that creates it: external
entry price, a contract, a transport leg, a local transformation, duty,
insurance or another declared value-add. Asterion does not provide a cumulative
cost for an intermediate item or a completed path. The product must calculate
how value accumulates through the network from the decisions it makes.

## 4. Users and decision authority

The primary application users are supply planners and category managers.
Operational, commercial and risk owners approve material exceptions and
consume the final recommendation.

The product must preserve the following distinction:

| Decision | Expected treatment |
|---|---|
| Sourcing, shipment, transformation and inventory quantities | The product recommends these within the selected data and policy |
| Data describing suppliers, materials, recipes, lanes, demand, capacity, cost and stock | An authorised data owner may maintain and publish this business reality |
| Incoterm rules and availability | A commercial data owner may inspect history, make governed changes and publish their effective use |
| Resilience preference or intervention | A planning or risk owner may configure and compare it without rewriting business data |
| Approval or eligibility exception | A named authority must approve it and its effect must remain visible |
| Solver status and optimality claim | The consultant reports only what the available evidence supports |

An override is an explicit business decision, not a hidden modelling shortcut.
Asterion must be able to see the original rule, the authorised change, who
approved it, why it was made and which recommendation it affected.

## 5. What the product must enable

### 5.1 Establish the business reality

A user must be able to bring a complete supplied dataset into the product,
understand its identity and validation state, and select a published version
for analysis. The product must treat all 25 supplied files as starting extracts
for logical business-data masters rather than as a permanent scenario menu.

Users must be able to maintain supported business facts without losing their
history. They must be able to see what changed, what is currently effective and
which published dataset version includes the change.

All Incoterm rules must be visible in the application. A commercial data owner
must be able to create, inspect, revise, activate, deactivate or retire them
subject to validation and authority. The product must show which commercial
relationships are affected and must reflect an effective Incoterm change in a
subsequent planning result.

### 5.2 Understand the supply network

A user must have an intuitive visual way to explore the selected supply graph.
They must be able to locate a supplier, plant, material or demand point, follow
relevant upstream and downstream relationships and inspect the business facts
that explain those relationships.

When data or results change, the user must be able to relate the change back to
the affected parts of the graph. Asterion is interested in whether the
experience supports understanding; it does not prescribe a graph technology,
layout or interaction design.

### 5.3 Publish a controlled dataset version

A user must be able to prepare changes as a draft, understand affected
relationships and resolve validation failures before publication. Publication
must create a complete, immutable and identifiable dataset version across all
25 logical masters. A previously published version and a run that used it must
remain reproducible.

The product must accept another valid complete dataset that was not named or
anticipated when the product was built. It must not borrow facts from BASE or
another package and must not retain stale state from a previous selection.

### 5.4 Configure and request a decision

A user must be able to select the published dataset version and a separately
versioned policy configuration used for a run. They must be able to apply a
quantitative resilience intervention, vary meaningful permitted preferences
and request an authorised exception without editing the underlying business
data.

The product must reproduce the published BASE service and objective-quality
controls through its own submitted recursive-value route. The published
reference is calibration evidence rather than model input, a prescribed
allocation or a globally optimal answer.

### 5.5 Understand the recommendation

For each result, a user must be able to understand:

- what is ordered, shipped, transformed, held and served in each relevant week;
- which demand is at risk and why;
- which capacities, approvals, lanes, materials, suppliers or shared resources
  constrain the decision;
- how material value accumulates from external sources through receipts,
  transformations, inventory and served demand;
- where relevant cost is added and how Incoterm responsibility affects it;
- how the submitted BASE result compares with the published reference and why
  any material aggregate differences arise;
- how a data-version or policy change affected the decision;
- what resilience benefit was obtained and what cost, service, inventory or
  concentration trade-off it created; and
- whether the result is valid, stale, infeasible, incomplete, time-limited or
  otherwise qualified.

The final decision summary must connect these facts to a recommendation and
state the limitations under which Asterion should act.

## 6. Supplied planning examples

Asterion supplies BASE and five example planning realities. They illustrate
normal operations and several kinds of disruption affecting capacity,
logistics, availability, regional exposure and demand.

These packages are examples of data that the product must handle. They are not
the complete set of scenarios that a user may explore, and the product must not
be limited to their identifiers or transformations. A high-quality engagement
will use selected examples to explain material business mechanisms and will
also demonstrate that a user can author and solve another valid data reality.

## 7. Questions the engagement must answer

1. Can terminal demand be served over P01–P12, and where is service at risk?
2. What movements and transformations support the proposed plan?
3. How is a selected entity connected upstream and downstream?
4. Where does end-to-end value accumulate, and which cost responsibilities
   affect it?
5. Which operational and commercial facts constrain the recommendation?
6. Does the submitted BASE result faithfully reproduce the published reference
   controls, and what explains any material aggregate differences?
7. What changed between two data realities or policy configurations, and why
   did the plan change?
8. Which resilience intervention is worth considering, and what trade-off does
   it create?
9. What should Asterion do, who must approve it and what should be monitored?

## 8. Engagement success

The engagement is successful when Asterion receives:

- a defensible twelve-week recommendation backed by an explicit algebraic MILP
  or MINLP formulation;
- a usable end-to-end decision-support application rather than a model-only
  demonstration;
- independently validated physical and end-to-end value evidence;
- honest solver and optimality statements;
- an application that works with governed data versions and policy
  configurations rather than hard-coded scenarios;
- an interpretable explanation of decisions, trade-offs and limitations; and
- reproducible evidence that another consultant can challenge.

Asterion does not require you to match a private allocation, use a particular
modelling library, reproduce an author application or claim a global optimum
that your evidence cannot support. You own the solution design and must be able
to defend it.
