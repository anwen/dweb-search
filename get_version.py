# git tag -l|tail -1 >.version && git rev-parse --short HEAD >>.version 
import subprocess
import sys
import textwrap

result = subprocess.run(['git', 'tag', '-l'], stdout=subprocess.PIPE)
r = result.stdout.decode('u8').strip()
vtag = r.split('\n')[-1]
# print(vtag)

result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], stdout=subprocess.PIPE)
r = result.stdout.decode('u8').strip()
vhash = r.split('\n')[-1]
# print(vhash)

ver = '{}+{}'.format(vtag, vhash)
# print(ver)


txt = f'''BackendVersion = '{ver}'
'''
# print(txt)

open('version.py', 'w').write(txt)