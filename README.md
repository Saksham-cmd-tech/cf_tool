# cfmate — Fast Codeforces CLI for Competitive Programming

**cfmate** is a fast, developer-friendly CLI tool for Codeforces that lets you fetch problems, view them in a clean format, and test your solutions directly from the terminal.

It is designed to eliminate context switching and streamline the competitive programming workflow.

---

## 🚀 Why cfmate?

Competitive programming usually involves:

* switching between browser and editor
* manually copying test cases
* repeatedly fetching problem statements

**cfmate solves this by bringing everything into your terminal.**

With cfmate, you can:

* fetch problems instantly
* run solutions with sample tests
* cache problems locally for speed
* stay fully inside your development environment

---

## ✨ Features

### 🔍 Problem Fetching

Fetch any Codeforces problem directly:

```bash
cf get 1829A
```

* Displays formatted problem statement
* Includes input/output format
* Shows sample test cases
* Uses clean terminal rendering

---

### 🧪 Solution Testing

Run your solution against sample tests:

```bash
cf run solution.py --problem 1829A
```

* Executes all sample test cases
* Shows pass/fail results
* Displays clear output differences
* Returns proper exit codes (useful for scripting)

---

### ⚡ Smart Caching System

* Problems are stored locally in `.cf_cache/`
* Eliminates repeated network requests
* Provides instant access after first fetch

---

### 🧠 Smart Problem Detection

You don’t always need to specify the problem:

```bash
cf run 1829A.py
```

* Automatically extracts problem ID from filename
* Reduces command verbosity

---

### 🌐 Multi-language Support

Supports multiple programming languages:

| Language   | Execution           |
| ---------- | ------------------- |
| Python     | `python3 file.py`   |
| C++        | `g++ -O2` then run  |
| C          | `gcc -O2` then run  |
| Java       | `javac` + `java`    |
| JavaScript | `node file.js`      |
| TypeScript | `ts-node file.ts`   |
| Go         | `go run file.go`    |
| Rust       | `rustc -O` then run |
| Ruby       | `ruby file.rb`      |

---

### 🎯 Clean Developer Experience

* Minimal and readable terminal output
* No unnecessary clutter
* Fast execution and feedback loop

---

## 📦 Installation

Install directly from PyPI:

```bash
pip install cfmate
```

---

## ⚡ Quick Start

### 1. Fetch a problem

```bash
cf get 1829A
```

---

### 2. Solve it in your editor

Create a file:

```bash
1829A.py
```

---

### 3. Run tests

```bash
cf run 1829A.py
```

---

## 📘 Detailed Usage

### Fetching Problems

```bash
cf get <problem_id>
```

⚠️ If `cf get` is not working or shows a loading/Cloudflare error, run:

```bash
playwright install chromium
```
This installs the browser required for fetching problems.

Examples:

```bash
cf get 1829A
cf get 2227D --no-cache
```

Options:

* `--no-cache` → force re-fetch from Codeforces

---

### Running Solutions

```bash
cf run <file> [options]
```

Examples:

```bash
cf run solution.py --problem 1829A
cf run 1829A.py
cf run 2227D.cpp
```

Options:

* `--problem` / `-p` → specify problem ID manually
* `--time-limit` → override execution time limit

Example:

```bash
cf run solution.py -p 1829A --time-limit 2000
```

---

### Creating Files and Folders

```bash
cf create <target> [lang]
```

Modes:

```bash
cf create 2227        # create contest2227/ folder
cf create A py        # create 2227A.py inside current contest folder
cf create 2227A py    # create folder + file
```

Behavior:

* Creates `contest<id>/` folder if not present
* Generates file using language template
* Automatically infers problem ID
* Optionally fetches and caches the problem

---

### Cache Management

```bash
cf cache <command>
```

Commands:

```bash
cf cache list
cf cache clear 1829A
cf cache clear
```

---

## 🗂 Cache System (Detailed)

### Location

Cache is stored in:

```bash
.cf_cache/
```

Each problem is stored as a JSON file:

```bash
.cf_cache/
  ├── 1829A.json
  ├── 2227D.json
```

When using `cf create`, cache is stored inside the contest folder:

```bash
contest2227/
  ├── 2227A.py
  └── .cf_cache/
      └── 2227A.json
```

---

### Cache Behavior

| Scenario          | Behavior                        |
| ----------------- | ------------------------------- |
| Not cached        | Fetch from Codeforces and store |
| Cached            | Load instantly                  |
| Corrupted cache   | Re-fetch automatically          |
| `--no-cache` used | Skip cache and overwrite        |

---

### Benefits

* Faster repeated runs
* Reduced network usage
* Offline access after first fetch

---

## 🧪 Exit Codes

| Code | Meaning                  |
| ---- | ------------------------ |
| `0`  | All tests passed         |
| `1`  | One or more tests failed |

Useful for:

* scripting
* CI pipelines
* automation

---

## ⚠️ Disclaimer

This tool is not affiliated with Codeforces.

It fetches publicly available problem statements for personal use only.
All problem content belongs to Codeforces: https://codeforces.com

Users are responsible for complying with Codeforces Terms:
https://codeforces.com/terms

This tool does not store or redistribute problems beyond local caching.

---

## 🔗 Links

* PyPI: https://pypi.org/project/cfmate/
* GitHub: https://github.com/Saksham-cmd-tech/cf_tool.git

---

## 📄 License

MIT
