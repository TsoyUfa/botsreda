import os

root_dir = "/Users/anton_tsoy/Desktop/Обсидиан"
keyword = "Альтима строй"

results = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    # skip hidden directories
    dirnames[:] = [d for d in dirnames if not d.startswith('.')]
    for filename in filenames:
        if filename.startswith('.'):
            continue
        filepath = os.path.join(dirpath, filename)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if keyword in content:
                    results.append((filepath, len(content)))
        except Exception:
            pass

print("Search results:")
for r in results:
    print(r[0], r[1])
