# Engineering Rules & Team Collaboration Guide

## Document: `docs/rules.md`
**Project:** MetaInspector Desktop (Instagram & Threads Checker)  
**Team Structure:** 2 Developers (Developer 1 & Developer 2)  
**Version Control:** Git & GitHub  

---

## 1. Git Workflow & Branching Strategy

### 1.1 Branch Hierarchy
```
main (Production / Stable Releases only)
  └── dev (Active integration branch)
        ├── feature/core-scraper
        ├── feature/desktop-gui
        ├── feature/sheets-exporter
        └── fix/threads-modal-selector
```

1. **`main` Branch:** Protected. Contains only verified, build-ready code. No direct commits allowed.
2. **`dev` Branch:** Integration branch where completed features are merged after testing.
3. **`feature/*` Branches:** Individual branches created by either developer for specific modules.
4. **`fix/*` Branches:** Dedicated branches for bug fixes.

---

## 2. Pull Request (PR) & Merge Rules

1. **Never Push Directly to `main` or `dev`:** Every change must originate from a `feature/*` or `fix/*` branch.
2. **Peer Review Rule:** Every Pull Request into `dev` must be reviewed and approved by the other developer before merging.
3. **Squash and Merge:** When merging a PR, use **Squash and Merge** to maintain a clean, readable linear Git history.
4. **Delete Feature Branch:** Always delete the feature branch after successful merge.
5. **PR Description Requirements:** Every PR must include:
   - Summary of changes made.
   - Files added, edited, or removed.
   - Proof of testing (screenshot, terminal output, or test command results).

---

## 3. Commit Message Standards (Conventional Commits)

All commit messages must follow the Conventional Commits specification:

| Prefix | Usage | Example |
| :--- | :--- | :--- |
| `feat:` | A new feature or capability | `feat: add 5-worker parallel browser pool` |
| `fix:` | A bug fix | `fix: resolve dynamic svg click on Threads header` |
| `docs:` | Documentation updates | `docs: update PRD and architecture diagrams` |
| `perf:` | Performance improvements | `perf: block images and video streams in Playwright` |
| `refactor:`| Code restructuring without feature change | `refactor: extract ban linking into modular engine` |
| `test:` | Adding or updating tests | `test: add edge-case unit test for private accounts` |

---

## 4. Coding Standards & Best Practices

1. **PEP 8 Compliance:** All Python code must adhere to PEP 8 styling conventions.
2. **Explicit Type Hinting:** All functions and methods must use type annotations (`str`, `dict`, `list[str]`, `Optional[int]`).
3. **Docstring Mandate:** Every function and class must include a brief docstring explaining its purpose, inputs, and outputs.
4. **Fail-Safe Scraper Selectors:**
   - Never rely on single, fragile CSS selectors for Meta DOM elements.
   - Always implement multi-language fallback locators (e.g., `:text('About this account'), :text('Bu hesap hakkında')`).
   - Use dynamic polling with reasonable timeouts (`max 8–10s`) instead of hardcoded `time.sleep()`.
5. **No Silent Failures:** Never write empty `except:` blocks. Always catch specific exceptions, log the error message, and record it in the results dictionary.

---

## 5. Security & Gitignore Mandates

To protect client privacy and credentials, the repository must enforce the following `.gitignore` rules:

```gitignore
# Python artifacts
__pycache__/
*.py[cod]
*.spec
dist/
build/

# Browser profiles and session data (CRITICAL: NEVER COMMIT)
browser_profile/
*.session
cookies.json
tokens.json

# Local databases and logs
*.db
*.sqlite
logs/
debug/

# Secret and configuration overrides
.env
config_local.py

# Client input and output data
usernames.txt
results/
*.csv
*.xlsx
```

> [!CAUTION]
> **Strict Rule:** Never commit passwords, session cookies, client username files, or API keys to GitHub. Any accidental commit of credentials must be removed immediately using `git filter-repo` or history rewrites.
