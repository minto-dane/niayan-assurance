# SPDX-License-Identifier: MIT
# Independent reference encoding; does not import Nia implementation code.
import hashlib
import json
cases = [('minimum', ['bus','app','','t','s','b'], 1, 0, 0),
         ('maximum', ['A'*200,'B'*200,'C'*160,'D'*160,'E'*256,'F'*1024],
          2**63-1, 1, 24)]
for name, fields, user_id, backend, capability in cases:
    data = b''.join(len(x.encode('ascii')).to_bytes(2, 'big') + x.encode('ascii')
                    for x in ['NIA-ACCESS-PROMPT-v1', *fields])
    data += bytes([backend, capability]) + user_id.to_bytes(8, 'big')
    data += bytes([1])*32 + bytes([2])*32 + bytes([3])*32
    print(json.dumps({'case': name, 'bytes': len(data),
                      'sha256': hashlib.sha256(data).hexdigest()}))
