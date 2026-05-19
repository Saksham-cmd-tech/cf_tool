"""
templates.py — Starter boilerplate for each supported language.

Each template is production-ready for competitive programming:
- Fast I/O where applicable
- Standard imports pre-loaded
- A clear entry point
"""

from __future__ import annotations

TEMPLATES: dict[str, tuple[str, str]] = {
    "py": (
        ".py",
        """\
import sys
input = sys.stdin.readline

def solve():
    pass

if __name__ == "__main__":
    solve()
""",
    ),
    "cpp": (
        ".cpp",
        """\
#include <bits/stdc++.h>
using namespace std;

void solve() {

}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t = 1;
    // cin >> t;
    while (t--) solve();

    return 0;
}
""",
    ),
    "c": (
        ".c",
        """\
#include <stdio.h>

void solve() {

}

int main() {
    int t = 1;
    // scanf("%d", &t);
    while (t--) solve();

    return 0;
}
""",
    ),
    "java": (
        ".java",
        """\
import java.io.*;
import java.util.*;

public class {classname} {
    static BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
    static StringTokenizer st;
    static PrintWriter out = new PrintWriter(System.out);

    static String next() throws IOException {
        while (st == null || !st.hasMoreTokens())
            st = new StringTokenizer(br.readLine());
        return st.nextToken();
    }

    static int nextInt() throws IOException {
        return Integer.parseInt(next());
    }

    public static void solve() throws Exception {

    }

    public static void main(String[] args) throws Exception {
        int t = 1;
        // t = nextInt();
        while (t-- > 0) solve();
        out.flush();
    }
}
""",
    ),
    "js": (
        ".js",
        """\
const fs = require('fs');
const input = fs.readFileSync(0, 'utf-8').trim().split('\\n');
let idx = 0;

function next() {
    return input[idx++];
}

function solve() {

}

solve();
""",
    ),
    "ts": (
        ".ts",
        """\
const fs = require('fs');
const input = fs.readFileSync(0, 'utf-8').trim().split('\\n');
let idx = 0;

function next(): string {
    return input[idx++];
}

function solve(): void {

}

solve();
""",
    ),
    "rb": (
        ".rb",
        """\
def solve
  t = 1
  # t = gets.to_i
  t.times do
    # solve
  end
end

solve
""",
    ),
    "go": (
        ".go",
        """\
package main

import (
\t"bufio"
\t"fmt"
\t"os"
)

var reader = bufio.NewReader(os.Stdin)
var writer = bufio.NewWriter(os.Stdout)

func solve() {

}

func main() {
\tdefer writer.Flush()

\tt := 1
\t// fmt.Fscan(reader, &t)
\tfor i := 0; i < t; i++ {
\t\tsolve()
\t}
}
""",
    ),
    "rs": (
        ".rs",
        """\
use std::io::{self, Read};

fn solve(input: &str) {

}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    solve(&input);
}
""",
    ),
}

# Accepted aliases (e.g. "python" → "py", "c++" → "cpp")
ALIASES: dict[str, str] = {
    "python": "py",
    "python3": "py",
    "c++": "cpp",
    "c#": "cs",
    "javascript": "js",
    "typescript": "ts",
    "ruby": "rb",
    "golang": "go",
    "rust": "rs",
}


def resolve_lang(raw: str) -> str | None:
    """
    Normalize a language input to its canonical shorthand.

    Returns None if the language is not recognized.

    Examples:
        "python"  → "py"
        "cpp"     → "cpp"
        "C++"     → "cpp"
        "unknown" → None
    """
    key = raw.strip().lower()
    key = ALIASES.get(key, key)
    return key if key in TEMPLATES else None


def get_extension(lang: str) -> str:
    """Return the file extension for a canonical lang key, e.g. 'cpp' → '.cpp'."""
    return TEMPLATES[lang][0]


def get_template(lang: str, problem_id: str = "") -> str:
    """
    Return the boilerplate content for a language.

    For Java, replaces {classname} with the problem ID so the public class
    name matches the filename (required by javac).
    """
    content = TEMPLATES[lang][1]
    if lang == "java":
        classname = problem_id if problem_id else "Solution"
        content = content.replace("{classname}", classname)
    return content


SUPPORTED_LANGS = list(TEMPLATES.keys())
