# Secure Multi-Agent Supervisor-Worker Architecture & Benchmark Harness

> **Benchmark Implementation for Failure Mode #3: Multi-Agent Cascade Escalation & Confused Deputy Problem**  
> *Corpus Reference: «Autonomous AI Agent Security Incidents of 2026» (Zenodo DOI: 10.5281/zenodo.22737862)*  
> *Author: Serhii Doletskyi*

---

## 1. Threat Model & Architecture Overview

In multi-agent topologies (e.g., supervisor-worker, hierarchical routing), an unprivileged secondary worker agent often synthesizes tool calls to complete delegated tasks. When an untrusted worker agent constructs a seemingly benign tool call (e.g., maintenance scripts, file access, socket inspection), a supervisor holding elevated host privileges may execute it under the mistaken assumption that the request originated from an internal system component.

This repository implements the **Privilege Attenuation Barrier** to eliminate Confused Deputy vulnerabilities:

```
[Untrusted Worker Agent] 
        | (Proposes ToolCallProposal)
        v
+---------------------------------------------------------+
| SUPERVISOR PRIVILEGE ATTENUATION BARRIER               |
|                                                         |
| 1. Capability & Clearance Check (ACL)                   |
|    - Workers CANNOT call CRITICAL or HOST tools         |
|                                                         |
| 2. Provenance & Taint Tracking                          |
|    - Scans arguments for command injection chars        |
|    - Intercepts Unix domain sockets (/var/run/docker.sock)|
|                                                         |
| 3. Filesystem Jail Verification                         |
|    - Resolves paths strictly inside ephemeral sandbox   |
|    - Blocks path traversal (../..)                      |
+---------------------------------------------------------+
        |
        +---> [VIOLATION DETECTED] -> Block & Log Audit Trail
        |
        +---> [VERIFIED SAFE]       -> Execute in Sandboxed Jail
```

---

## 2. Benchmark Verification & Containment Metrics

To run the unit tests and verify 100% escape prevention rate:

```bash
python3 -m unittest agent_supervisor_system/benchmark/test_cascade_escalation.py
```

To run the live interactive demonstration:

```bash
python3 agent_supervisor_system/runner.py
```

### Metrics Produced:
- **Escape Prevention Rate (EPR)**: 100.0%
- **Confused Deputy Resistance Score (CDRS)**: 100.0%
- **False Positive Interception Rate (FPIR)**: 0.0%
