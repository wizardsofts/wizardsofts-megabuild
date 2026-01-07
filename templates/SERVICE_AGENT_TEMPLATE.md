# Agent Instructions - <SERVICE_NAME>

> **Inherits from:** [/AGENT.md](/AGENT.md)
> **This file contains service-specific overrides and additions.**

---

## Service Overview

Brief description of what this service does and its role in the system.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Java 21 / TypeScript 5.x / Python 3.11 |
| Framework | Spring Boot / Next.js / FastAPI |
| Database | PostgreSQL / Redis / Neo4j |
| Build | Maven / npm / pip |
| Testing | JUnit 5 / Jest / pytest |

---

## Service-Specific Rules

### Testing (Override from AGENT.md)

- **Minimum coverage:** X% (if different from global 80%)
- **Required tests:** List specific test requirements

```
# Example code showing required test patterns
```

### Code Style (Override)

- List any code style overrides from global rules
- Specific patterns required for this service

### Security Rules (Addition)

- Service-specific security requirements
- Authentication/authorization rules
- Data handling requirements

---

## Local Development

### Prerequisites

```bash
# Required services/dependencies
```

### Run Service

```bash
# Command to start the service locally
```

### Run Tests

```bash
# Commands to run different test suites
```

---

## Common Tasks

### Task 1: <Common Task Name>

1. Step 1
2. Step 2
3. Step 3

### Task 2: <Another Common Task>

1. Step 1
2. Step 2

---

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VAR_NAME` | Description | `value` |

### Profiles/Environments

| Profile | Use Case |
|---------|----------|
| `local` | Local development |
| `prod` | Production |

---

## Troubleshooting

### Common Issue 1

```bash
# Diagnostic commands and solutions
```

### Common Issue 2

```bash
# Diagnostic commands and solutions
```

---

*Inherits all other rules from [/AGENT.md](/AGENT.md)*
