import pathlib

d = pathlib.Path(r'F:\soft\00selfmade\skill-c++\skill-c++\chapters')
FENCE = chr(96) * 3
for f in sorted(d.glob('ch*.md')):
    t = f.read_text(encoding='utf-8')
    fences = t.count(FENCE)
    print('=' * 62)
    print(f.name, '| chars=', len(t), '| 代码围栏数=', fences,
          '| 配对=', fences % 2 == 0)
    print('  结尾:', repr(t.rstrip()[-40:]))
    print('  小节:', [l[3:].strip() for l in t.splitlines() if l.startswith('## ')])
