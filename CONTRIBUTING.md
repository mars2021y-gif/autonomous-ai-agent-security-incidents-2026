# Contributing to Autonomous AI Agent Security Incidents (2026)

Thank you for your interest in contributing. This repository provides an empirical benchmark corpus of 109 verified containment failures and an open defense harness against multi-agent confused deputy escalation.

We welcome contributions from researchers, security practitioners, and agent developers.

---

## How You Can Contribute

1. **Submit Empirical Incidents**: Report real-world containment failures or sandbox breakouts observed in autonomous coding or tool-using agents.
2. **Expand the Defense Harness**: Implement and benchmark additional isolation drivers (such as gVisor, Firecracker, or network namespace policies).
3. **Refine Metrics and Falsification Criteria**: Propose improvements to the 193 falsification criteria in the evidence matrix.
4. **Fix Issues and Documentation**: Help improve code clarity, test coverage, and documentation.

---

## Submission Criteria for Incidents

To maintain empirical rigor, all submitted incidents must meet these criteria:

- **Verifiability**: Include primary source telemetry, reproducible test cases, public laboratory disclosures, or bug bounty reports.
- **Containment Vector**: Clearly classify the failure mode (e.g. host socket exposure, ambient token recovery, indirect prompt injection, or multi-agent cascade escalation).
- **Falsification Mapping**: Map findings against the variables defined in `data/AI_Agent_Evidence_Matrix_2026.csv`.

---

## Pull Request Workflow

1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/your-contribution-name
   ```
2. Run test suites locally before submitting:
   ```bash
   python3 -m unittest discover -s agent_supervisor_system/benchmark
   ```
3. Commit with concise, descriptive messages.
4. Open a Pull Request referencing any related issues or RFC discussions.

---

## Licensing of Contributions

By contributing, you agree that your code contributions will be licensed under the [MIT License](LICENSE) and data/documentation contributions will be licensed under [CC-BY-4.0](LICENSE-DATA).
