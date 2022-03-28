import sys


print('```yaml')

for line in open(sys.argv[-1]).readlines():
    print(line.rstrip())

print('```')
