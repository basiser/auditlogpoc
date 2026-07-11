#!/usr/bin/env python3
import json
import csv
import io
from collections import Counter

# Read the file
with open('/large_tool_results/call_00_WLql5H6zzIiYzOoVL5bP5995', 'r') as f:
    content = f.read()

# Parse the JSON wrapper
data = json.loads(content)
tsv_data = data['outputValues']['result']

# Parse TSV
reader = csv.DictReader(io.StringIO(tsv_data), delimiter='\t')

records = []
for row in reader:
    records.append(row)

print(f"Total records parsed: {len(records)}")

# Analyze
categories = Counter()
operations = Counter()
users = Counter()
success_fail = Counter()
object_types = Counter()
statuses = Counter()

failed_ops = []

for i, rec in enumerate(records):
    cat = rec.get('category', '')
    op = rec.get('message.object.id.crudType', '')
    user = rec.get('user', '')
    success = rec.get('message.success', '')
    obj_type = rec.get('message.object.type', '')
    status = rec.get('message.status', '')
    time_val = rec.get('time', '')
    
    categories[cat] += 1
    operations[op] += 1
    users[user] += 1
    success_fail[success] += 1
    object_types[obj_type] += 1
    statuses[status] += 1
    
    if success == 'FALSE':
        failed_ops.append({
            'index': i,
            'uuid': rec.get('message_uuid', ''),
            'time': time_val,
            'user': user,
            'category': cat,
            'operation': op,
            'object_type': obj_type,
            'message_id': rec.get('message.id', '')
        })

print(f"\n=== CATEGORIES ===")
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

print(f"\n=== OPERATIONS ===")
for op, count in sorted(operations.items(), key=lambda x: -x[1]):
    print(f"  {op or '(empty)'}: {count}")

print(f"\n=== USERS ===")
for user, count in sorted(users.items(), key=lambda x: -x[1]):
    print(f"  {user}: {count}")

print(f"\n=== SUCCESS/FAILURE ===")
for s, count in sorted(success_fail.items(), key=lambda x: -x[1]):
    print(f"  {s or '(empty)'}: {count}")

print(f"\n=== OBJECT TYPES ===")
for ot, count in sorted(object_types.items(), key=lambda x: -x[1]):
    print(f"  {ot}: {count}")

print(f"\n=== STATUSES ===")
for s, count in sorted(statuses.items(), key=lambda x: -x[1]):
    print(f"  {s}: {count}")

print(f"\n=== FAILED OPERATIONS ({len(failed_ops)}) ===")
for fo in failed_ops:
    print(f"  [{fo['time']}] {fo['operation']} on {fo['object_type']} by {fo['user']} - msg_id={fo['message_id']}")

# Now let's do detailed analysis
print("\n\n=== DETAILED ANALYSIS ===")

# Role mapping changes
role_records = [r for r in records if r.get('message.object.type') == 'xsrolecollection2samlattribute']
print(f"\nRole Mapping Changes: {len(role_records)}")
for r in role_records:
    print(f"  [{r.get('time')}] {r.get('message.object.id.crudType')}: Role={r.get('message.object.id.rolecollection_name')}, Group={r.get('message.object.id.saml_attr_value')}, IdP={r.get('message.object.id.saml_idp')}, User={r.get('user')}")

# IdP changes
idp_records = [r for r in records if r.get('message.object.type') == 'custom platform idp distribution']
print(f"\nIdP Configuration Changes: {len(idp_records)}")
for r in idp_records:
    print(f"  [{r.get('time')}] {r.get('message.object.id.crudType')}: User={r.get('user')}")

# Destination operations
dest_records = [r for r in records if r.get('message.object.type') == 'objectId']
print(f"\nDestination Operations: {len(dest_records)}")
for r in dest_records:
    print(f"  [{r.get('time')}] {r.get('message.object.id.crudType')}: Action={r.get('message.data.action')}, Object={r.get('message.data.objectId')}, Success={r.get('message.success')}, User={r.get('user')}")

# Security events
sec_records = [r for r in records if r.get('category') == 'audit.security-events']
print(f"\nSecurity Events: {len(sec_records)}")
for r in sec_records:
    print(f"  [{r.get('time')}] Event={r.get('message.data.event_code')}, Action={r.get('message.data.action')}, Object={r.get('message.data.objectType')}/{r.get('message.data.objectId')}, IP={r.get('message.ip')}, User={r.get('user')}")
