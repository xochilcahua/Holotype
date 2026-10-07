# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Teo Monroy
"""Find top-level references to names that only get defined in a LATER module.

The split turned one working line into a ReferenceError: a top-level
addEventListener(..., confirmReset) sat 1,800 lines ABOVE function confirmReset in the
monolith, which was fine because both were in the same <script> and function
declarations hoist. Split across two files there is no hoisting, so the name does not
exist yet when the line runs. The browser test caught that one, but only because it
throws immediately -- the same pattern anywhere that is NOT reached at load time would
stay hidden until someone clicked the thing.

So this walks every module in load order, collects the names each one DECLARES, and
flags any statement at the very start of a line (top level, not inside a function body)
that mentions a name first declared in a LATER module. Function declarations are
excluded from the "declared earlier" set, because they are hoisted within their own
file but NOT across files.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
order = []
for l in open(os.path.join(ROOT, 'index.html'), encoding='utf-8'):
    m = re.search(r'<script src="(src/[^"]+)"', l)
    if m and not m.group(1).startswith('copy/'):   # generated translation data: strings, not code
        order.append(m.group(1))

DECL = re.compile(r'^(?:const|let|var|class|function)\s+([A-Za-z_$][\w$]*)')
STMT = re.compile(r'^[A-Za-z_$(]')
IDENT = re.compile(r'\b([A-Za-z_$][\w$]*)\b')

BUILTIN = set('''
if for while switch return function const let var class new this typeof instanceof
document window localStorage Math JSON Object Array String Number Boolean Promise Set Map
Intl Date console fetch true false null undefined NaN isNaN parseInt parseFloat
setTimeout clearTimeout setInterval requestAnimationFrame structuredClone
encodeURIComponent decodeURIComponent RegExp Error Symbol Proxy Reflect WeakMap BigInt
globalThis
'''.split())

declared = {}          # name -> index of the module that FIRST declares it
for i, rel in enumerate(order):
    for line in open(os.path.join(ROOT, rel), encoding='utf-8').read().split('\n'):
        m = DECL.match(line)
        if m and m.group(1) not in declared:
            declared[m.group(1)] = i

problems = []
for i, rel in enumerate(order):
    src = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    depth = 0
    in_comment = False
    for lineno, line in enumerate(src.split('\n'), 1):
        stripped = line.strip()
        # Track /* ... */ as well as //: the generated file headers are block comments
        # whose continuation lines begin with ordinary words, and reading those as
        # code reported axes.js "using" a name it was only describing in prose.
        if in_comment:
            if '*/' in stripped:
                in_comment = False
            continue
        if stripped.startswith('/*') and '*/' not in stripped[2:]:
            in_comment = True
            continue
        code = line
        if depth == 0 and STMT.match(code) and not stripped.startswith('//'):
            # Only the part of the statement BEFORE the first "=>" runs immediately.
            # Anything inside a callback is resolved when the callback FIRES, by which
            # time every module has loaded -- flagging those reported four false hits,
            # including the confirmReset case this check was written to catch.
            immediate = code.split('=>', 1)[0]
            for ident in set(IDENT.findall(immediate)):
                if ident in BUILTIN or ident not in declared:
                    continue
                if declared[ident] > i:
                    problems.append((rel, lineno, ident, order[declared[ident]]))
        depth += line.count('{') - line.count('}')
        if depth < 0:
            depth = 0

print('%d modules, %d declared names' % (len(order), len(declared)))
if not problems:
    print('no top-level reference resolves to a later module')
else:
    seen = set()
    print('\nTOP-LEVEL USE OF A LATER-DEFINED NAME (%d):' % len(problems))
    for rel, lineno, ident, where in problems:
        key = (rel, ident)
        if key in seen:
            continue
        seen.add(key)
        print('  %-30s line %-5d uses %-22s declared in %s'
              % (rel, lineno, ident, where))