# First Five Minutes Example

This disposable example demonstrates a permitted source change, a genuine `PASS` verification, and a rejected `BLOCKED` verification.

## Steps

```bash
# 1. Create a disposable Git repository and initialize AI-SDLC Lite
TMP=$(mktemp -d)
cp -r examples/first-five-minutes "$TMP/repo"
mkdir -p "$TMP/evidence"
git -C "$TMP/repo" init -q
git -C "$TMP/repo" config user.name "Example User"
git -C "$TMP/repo" config user.email "example@example.invalid"
ai-sdlc init --repo "$TMP/repo" --apply
ai-sdlc doctor
git -C "$TMP/repo" add .
git -C "$TMP/repo" commit -q -m "Initial baseline"
BASE=$(git -C "$TMP/repo" rev-parse HEAD)
ai-sdlc status --repo "$TMP/repo"

# 2. Make a permitted change to src/greeter.py and run tests
python3 -B -c "p='$TMP/repo/src/greeter.py'; s=open(p).read().replace('name.strip()', '(name or \"\").strip()'); open(p,'w').write(s)"
(cd "$TMP/repo" && python3 -B -m unittest discover -s tests) > "$TMP/evidence/out.txt" 2>&1

# 3. Verify valid result -> PASS (exit 0)
sed "s/<BASELINE_SHA>/$BASE/" "$TMP/repo/result.pass.json" > "$TMP/evidence/result.pass.json"
ai-sdlc verify --repo "$TMP/repo" --result "$TMP/evidence/result.pass.json"

# 4. Verify invalid result (out-of-scope / undeclared change) -> BLOCKED (exit 2)
sed "s/<BASELINE_SHA>/$BASE/" "$TMP/repo/result.blocked.json" > "$TMP/evidence/result.blocked.json"
ai-sdlc verify --repo "$TMP/repo" --result "$TMP/evidence/result.blocked.json"
```
