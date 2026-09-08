---
type: adr-index
status: active
source_of_truth_for:
  - architectural-decisions-index
read_when:
  - architecture-change
  - create-adr
update_when:
  - adr-added
  - adr-status-change
---

# Architectural Decisions

| ADR | Status | Decision |
|---|---|---|
| ADR-0001 | Accepted | Use the generated golden-path baseline and grow infrastructure only when requirements justify it. |
| ADR-0002 | Accepted | The semantic engineering model is the product core; all consumers depend on it. |
| ADR-0003 | Accepted | Keep semantic engineering data and presentation/rendering data strictly separate. |
| ADR-0004 | Accepted | YAML is a serialization format validated into the domain model, not the domain model itself. |
| ADR-0005 | Accepted | Use `ProcessModel` as the process-graph container and S1–S4 validation boundary while `PlantModel` remains the overall aggregate. |

Create an ADR for architecture style changes, databases, external services, authentication, cache, queues, events, deployment, vendor lock-in, and data ownership changes.
