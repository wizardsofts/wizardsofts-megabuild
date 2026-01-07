# GitHub Copilot Instructions - WizardSofts Megabuild

> **Imports:** [/AGENT.md](/AGENT.md) - All rules from AGENT.md apply first.

This file contains GitHub Copilot specific instructions that extend the universal AGENT.md.

---

## Core Principles (from AGENT.md)

1. **TDD Workflow:** Write failing test → implement → refactor
2. **Single Task:** Work on ONE feature per session
3. **Code Investigation:** 2-level deep investigation before changes
4. **Behavior Change:** Stop & inform user before changing existing behavior
5. **Document Changes:** Update docs alongside code
6. **Security First:** Validate inputs, escape outputs, no hardcoded secrets
7. **Deletion Policy:** Always confirm before removing code/features
8. **Script-First:** Write scripts for repetitive operations

---

## Copilot-Specific Additions

### Code Generation Preferences

**Always include:**
- JSDoc/JavaDoc for all public methods and classes
- Type annotations (explicit over inferred)
- Error handling for external calls
- Input validation for public APIs

**Never generate:**
- Hardcoded credentials or secrets
- Console.log in production code (use proper logging)
- Commented-out code blocks
- Magic numbers without constants

### Suggestion Priorities

When suggesting completions, prioritize:
1. Security (input validation, output encoding)
2. Type safety (generics, null checks)
3. Testability (dependency injection, pure functions)
4. Readability (clear names, small functions)

### Import Preferences

```typescript
// Prefer named imports over default
import { Button, Card } from '@wizwebui/core';  // ✓
import Button from '@wizwebui/core/Button';      // ✗

// Use absolute imports from configured paths
import { formatDate } from '@/utils/date';       // ✓
import { formatDate } from '../../../utils/date'; // ✗
```

### Test Generation

When generating tests:
- Use `describe` blocks for grouping
- Use clear test names: `should <expected behavior> when <condition>`
- Include edge cases (null, empty, boundary values)
- Mock external dependencies

```typescript
describe('calculatePortfolioValue', () => {
  it('should return 0 when portfolio is empty', () => {
    expect(calculatePortfolioValue([])).toBe(0);
  });

  it('should sum all holdings when portfolio has multiple stocks', () => {
    const portfolio = [
      { symbol: 'AAPL', shares: 10, price: 150 },
      { symbol: 'GOOG', shares: 5, price: 2800 },
    ];
    expect(calculatePortfolioValue(portfolio)).toBe(15500);
  });
});
```

### Framework-Specific Patterns

**React/Next.js:**
```typescript
// Use functional components with hooks
const Component: React.FC<Props> = ({ prop }) => {
  const [state, setState] = useState<Type>(initial);

  useEffect(() => {
    // Effect logic
    return () => {/* cleanup */};
  }, [dependencies]);

  return <div>{/* JSX */}</div>;
};
```

**Spring Boot:**
```java
// Use constructor injection
@Service
public class MyService {
    private final Repository repository;

    public MyService(Repository repository) {
        this.repository = repository;
    }
}
```

**Python/FastAPI:**
```python
# Use type hints and Pydantic models
@router.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)) -> ItemResponse:
    """Create a new item."""
    return await item_service.create(db, item)
```

---

## Monorepo Context

This is a monorepo with multiple services. Check `apps/<service>/AGENT.md` for service-specific rules.

| Service | Stack | Key Patterns |
|---------|-------|--------------|
| ws-gateway | Spring Boot | Constructor injection, records for DTOs |
| gibd-quant-web | Next.js 15 | App router, server components |
| gibd-quant-agent | Python/Ray | Type hints, async/await |

---

## Security Reminders

- **NEVER** suggest hardcoded API keys or passwords
- **ALWAYS** suggest parameterized queries for SQL
- **ALWAYS** suggest input validation on user data
- **ALWAYS** suggest output encoding for HTML/JSON responses
- **PREFER** allowlist validation over blocklist

---

*See [/AGENT.md](/AGENT.md) for complete development lifecycle instructions.*
