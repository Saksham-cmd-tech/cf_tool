## Disclaimer

This tool is not affiliated with Codeforces.

It fetches publicly available problem statements for personal use only.
Users must comply with Codeforces Terms of Service:
https://codeforces.com/terms

This tool does not store or redistribute problems beyond local caching.

# cfmate

A fast, Codeforces CLI — fetch problems, display them cleanly, and test your solutions against sample cases, all from the terminal.

---

## Features

- **`cf get`** — fetch and display any Codeforces problem with clean Rich formatting
- **`cf run`** — run your solution against all sample tests, with pass/fail output and diffs
- **Local cache** — problems are saved to `.cf_cache/` so repeated fetches are instant
- **Multi-language** — Python, C++, C, Java, JavaScript, TypeScript, Ruby, Go, Rust
- **Smart ID inference** — name your file `1829A.py` and skip the `--problem` flag
- **Clean UX** — spinner for loading, no fake delays, no excessive color

---

## Installation

```bash
git clone https://github.com/Saksham-cmd-tech/cf_tool.git
cd cf_tool
pip install -e .
```

This registers the `cf` command globally.

---

## Usage

### Fetch a problem

```bash
cf get 1829A
cf get 2227D --no-cache   # bypass cache
```

### Run your solution

```bash
# Specify the problem explicitly
cf run solution.py --problem 1829A

# Or name your file after the problem — ID is inferred automatically
cf run 1829A.py
cf run 2227D.cpp

# Custom time limit (milliseconds)
cf run solution.py -p 1829A --time-limit 2000
```

### Manage the cache

```bash
cf cache list           # list cached problems
cf cache clear 1829A    # remove one problem
cf cache clear          # remove everything
```

---

## Supported Languages

| Extension | Language   | How it runs              |
|-----------|------------|--------------------------|
| `.py`     | Python 3   | `python3 file.py`        |
| `.cpp`    | C++17      | `g++ -O2` then run       |
| `.c`      | C          | `gcc -O2` then run       |
| `.java`   | Java       | `javac` then `java`      |
| `.js`     | JavaScript | `node file.js`           |
| `.ts`     | TypeScript | `ts-node file.ts`        |
| `.rb`     | Ruby       | `ruby file.rb`           |
| `.go`     | Go         | `go run file.go`         |
| `.rs`     | Rust       | `rustc -O` then run      |

---

## Project Structure

```
cf_tool/
├── cf_tool/
│   ├── __init__.py     # package version
│   ├── cli.py          # Typer CLI entry point
│   ├── scraper.py      # cloudscraper HTTP layer
│   ├── parser.py       # BeautifulSoup HTML → Problem
│   ├── runner.py       # subprocess test execution
│   ├── formatter.py    # Rich terminal output
│   ├── cache.py        # JSON local cache
│   ├── models.py       # Problem + TestCase dataclasses
│   └── utils.py        # LaTeX cleaning, ID parsing, normalization
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Exit Codes

| Code | Meaning                        |
|------|--------------------------------|
| `0`  | All tests passed               |
| `1`  | One or more tests failed / error |

This makes `cf run` composable in shell scripts and CI pipelines.

---

## License

MIT
