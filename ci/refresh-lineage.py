#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
"""Preview/record exact source successors without changing imported history."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import engineering as eng


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--acknowledge-source-change',action='store_true')
    parser.add_argument('--adr')
    parser.add_argument('--reason')
    args=parser.parse_args()
    if args.write and not (args.acknowledge_source_change and args.adr and args.reason):
        parser.error('--write requires --acknowledge-source-change, --adr and --reason')
    root=Path(__file__).resolve().parents[2]
    if args.adr:
        if not re.fullmatch('ADR-[0-9]{4}',args.adr):parser.error('Invalid ADR identifier')
        eng.resolve_ref(root,'assurance/docs/engineering/adr/'+args.adr+'.ja.md')
    path=root/'assurance/engineering/lineage-amendments.json'
    data=eng.load_json(path);old={x['path']:x for x in data['amendments']};amendments=[];changes=[]
    for row in eng.load_json(root/'assurance/engineering/lineage-merge.json')['restored']:
        current=hashlib.sha256(eng.read_regular(root/row['path'])).hexdigest()
        if current==row['sha256']:continue
        if row['path'] in old and old[row['path']]['to_sha256']==current:
            amendments.append(old[row['path']]);continue
        change=dict(path=row['path'],from_sha256=row['sha256'],to_sha256=current,
                    adr='assurance/docs/engineering/adr/'+(args.adr or 'ADR-required')+'.ja.md',
                    scope=args.reason or 'Review and provide --reason',
                    validation='source-inspected; native-validation-recorded-separately; independent-review-pending')
        changes.append(change);amendments.append(change)
    print(json.dumps({'write':args.write,'changes':changes,'production_approval':False},indent=2))
    if args.write:
        data['amendments']=amendments
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
