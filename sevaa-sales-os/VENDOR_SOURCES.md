# VENDOR / OPEN-SOURCE REUSE REGISTER

Goal: save implementation time and tokens without importing incompatible licenses or unnecessary code.

## Vetted references

### fastapi/full-stack-fastapi-template
- Repository: https://github.com/fastapi/full-stack-fastapi-template
- License checked: MIT.
- Status: approved as an architecture/reference source.
- Current decision: do **not** vendor the whole repository. The existing SEVAA code already has working FastAPI/auth/migrations/CI; wholesale copying would create duplicate architecture and regression risk.
- Reuse rule: copy only a specific component when it replaces more code than it introduces, preserve required copyright/license notices, and record the exact source path/commit here.

## Rule
Never copy a repository merely because it is available. Before vendoring code: verify license, security relevance, maintenance status, dependency cost, and whether reuse materially shortens the path to paid conversion.
