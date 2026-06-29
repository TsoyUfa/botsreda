import os

dirs = ["/Users/anton_tsoy/Desktop/Обсидиан/9. Застройщики", "/Users/anton_tsoy/Desktop/Обсидиан/life/Застройщики"]

for d in dirs:
    if os.path.exists(d):
        print(f"--- Files in {d}:")
        for dirpath, dirnames, filenames in os.walk(d):
            for filename in filenames:
                if filename.endswith('.md'):
                    print(os.path.join(dirpath, filename))
    else:
        print(f"--- {d} does not exist")
