import os
dir_name = "."
test = os.listdir(dir_name)
for item in test:
    if (item.endswith(".txt") or item.endswith(".json")) and item != 'int.txt':
        os.remove(os.path.join(dir_name, item))
