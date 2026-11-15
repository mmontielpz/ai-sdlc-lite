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
ai-sdlc status --repo "$TMP/repo"
ai-sdlc baseline --repo "$TMP/repo" --out "$TMP/evidence/baseline.json"

# 2. Make a permitted change to src/greeter.py and run tests
python3 -B -c "p='$TMP/repo/src/greeter.py'; s=open(p).read().replace('name.strip()', '(name or \"\").strip()'); open(p,'w').write(s)"
(cd "$TMP/repo" && python3 -B -m unittest discover -s tests) > "$TMP/evidence/out.txt" 2>&1

# 3. Verify valid result -> PASS (exit 0)
python3 -B -c "import json; b=json.load(open('$TMP/evidence/baseline.json'))['baseline_sha']; d=json.load(open('$TMP/repo/result.pass.json')); d['baseline_sha']=b; json.dump(d, open('$TMP/evidence/result.pass.json','w'))"
ai-sdlc verify --repo "$TMP/repo" --result "$TMP/evidence/result.pass.json" --baseline-record "$TMP/evidence/baseline.json"

# 4. Verify invalid result (out-of-scope / undeclared change) -> BLOCKED (exit 2)
python3 -B -c "import json; b=json.load(open('$TMP/evidence/baseline.json'))['baseline_sha']; d=json.load(open('$TMP/repo/result.blocked.json')); d['baseline_sha']=b; json.dump(d, open('$TMP/evidence/result.blocked.json','w'))"
ai-sdlc verify --repo "$TMP/repo" --result "$TMP/evidence/result.blocked.json" --baseline-record "$TMP/evidence/baseline.json"
```
