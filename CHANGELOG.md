## v0.4.0 (2026-05-24)

### Features

* add `cf explore` command with fuzzy search across all Codeforces problems
* support pre-filtering in explorer (`cf explore -e <query>`)
* add interactive contest browser (`cf get <contest_id>`)
* integrate global problem cache for fast exploration
* enhance UI for contest browser
* improve UI for explore command
* improve CLI structure and command usability

### Refactor

* extract problem resolution logic into `core.py`
* decouple CLI from business logic
* centralize fetching, parsing, and caching pipeline

### Fixes

* correct Commitizen bump configuration in `.cz.toml`
* resolve cache inconsistencies across commands
* fix CLI edge cases and error handling

### Improvements

* introduce reusable `resolve_problem()` core function
* improve modular architecture (CLI, core, UI separation)
* enhance caching strategy for better performance

### Internal

* add `cache_problems.py` for global problem dataset
* add `explore.py` for interactive problem browsing
* add `question.py` for contest-based navigation

---

## v0.3.2 (2026-05-24)

### Refactor

* extract problem resolution logic into core module
* prepare codebase for modular architecture

---

## v0.3.1 (2026-05-20)

### Changes

* update versioning system
* improve release pipeline setup

---

## v0.2.2 (2026-05-19)

### Features

* add GitHub Actions workflow
* implement initial `cf create` command

### Documentation

* add initial project documentation
