# Architecture and Engineering Guidelines

## 1. Security & Authentication
- Never allow hardcoded credentials, passwords, tokens, API keys, or plain-text database connection strings in code.
- All database queries must use parameterized queries (Prepared Statements or ORM). String concatenation in SQL statements is strictly prohibited (BLOCKER).
- Endpoints handling user data must enforce permission and scope validation in the request handler.

## 2. Design Patterns & Code Quality
- Exception handling: Do not swallow exceptions with empty `catch (Exception e) {}` or `except Exception: pass` blocks.
- Dependency injection must be performed via constructors or interfaces, avoiding direct service instantiation with `new`.
- Functions and methods must not exceed 50 lines of code (Code Smell / Complexity Warning).

## 3. Testing Strategy
- Every new endpoint, service, or business rule implementation must include corresponding unit or integration tests within the same Pull Request.