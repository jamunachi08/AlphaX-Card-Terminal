import os, re, sys

PATTERN = re.compile(r'(<<<<<<<|=======|>>>>>>>)')

bad = []
for dirpath, dirnames, filenames in os.walk("."):
    if ".git" in dirnames:
        dirnames.remove(".git")
    for fn in filenames:
        path = os.path.join(dirpath, fn)
        # skip binary-ish
        if fn.endswith((".png",".jpg",".jpeg",".gif",".pdf",".zip",".woff",".woff2",".ttf",".eot")):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                if PATTERN.search(f.read()):
                    bad.append(path)
        except Exception:
            continue

if bad:
    print("Merge-conflict markers found in:")
    for p in bad:
        print(" -", p)
    sys.exit(1)

print("OK: No merge-conflict markers found.")
