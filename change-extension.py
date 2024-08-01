import os
import sys
def main():
    path = "/apps/nttech/sbharmar/portal-clab-test/lib/snapshot/configs/all_configs/"
    count = 1

    for root, dirs, files in os.walk(path):
        for i in files:
            #print(i)
            os.rename(os.path.join(root, i), os.path.join(root, i + ".cfg"))
            count += 1


if __name__ == '__main__':
    main()

