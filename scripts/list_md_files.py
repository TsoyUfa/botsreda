import os

root_dir = "/Users/anton_tsoy/Desktop/Обсидиан"

results = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    # skip hidden directories
    dirnames[:] = [d for d in dirnames if not d.startswith('.')]
    for filename in filenames:
        if filename.endswith('.md'):
            filepath = os.path.join(dirpath, filename)
            results.append(filepath)

print(f"Total markdown files found: {len(results)}")
for r in sorted(results):
    print(r)
