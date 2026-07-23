"""Scope point 1: categorize every create_model(...) call so we only auto-collapse
the cases that are safe (no execution-time args), and flag the rest."""

import json
import re
import glob
import collections

MAIN = {"algorithms", "applications", "tutorials"}
SAFE_KWARGS = {"constraints", "preferences"}  # these move cleanly onto synthesize()
RISKY_KWARGS = ["execution_preferences", "classical_execution_function", "out_file"]


def balanced_close(s: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def group(path: str) -> str:
    top = path.split("/")[0]
    return "main" if top in MAIN else ("community" if top == "community" else "other")


cat = collections.Counter()
kinds_freq = collections.Counter()
samples = collections.defaultdict(list)

for p in sorted(glob.glob("**/*.ipynb", recursive=True)):
    nb = json.load(open(p))
    code = "\n".join(
        "".join(c.get("source", []))
        for c in nb.get("cells", [])
        if c.get("cell_type") == "code"
    )
    if "create_model(" not in code:
        continue

    calls = []
    for m in re.finditer(r"create_model\(", code):
        close = balanced_close(code, m.end() - 1)
        calls.append(code[m.end() : close])

    kinds = set()
    for inner in calls:
        for kw in SAFE_KWARGS | set(RISKY_KWARGS):
            if re.search(rf"\b{kw}\s*=", inner):
                kinds.add(kw)
    kinds_freq.update(kinds)

    risky = kinds & set(RISKY_KWARGS)
    multi = len([c for c in calls]) > 1
    if risky:
        c = f"RISKY (keep create_model): {sorted(risky)}"
    elif multi:
        c = "REVIEW: multiple create_model calls"
    elif not kinds:
        c = "SAFE: create_model(main), no kwargs"
    else:
        c = f"SAFE: only {sorted(kinds)}"
    cat[c] += 1
    if len(samples[c]) < 4:
        samples[c].append(f"{group(p)}: {p}")

print(f"notebooks using create_model: {sum(cat.values())}\n")
for c, n in cat.most_common():
    print(f"  {n:3d}  {c}")
print("\nkwarg frequency:", dict(kinds_freq))
print("\nsamples per category:")
for c, ps in samples.items():
    print(f"  [{c}]")
    for x in ps:
        print(f"      {x}")
