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
findings = []

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
    
    # Role mapping changes
    if obj_type == 'xsrolecollection2samlattribute':
        findings.append({
            'type': 'role_mapping_change',
            'index': i,
            'time': time_val,
            'user': user,
            'operation': op,
            'role': rec.get('message.object.id.rolecollection_name', ''),
            'saml_attr_value': rec.get('message.object.id.saml_attr_value', ''),
            'saml_idp': rec.get('message.object.id.saml_idp', '')
        })
    
    # IdP changes
    if obj_type == 'custom platform idp distribution':
        findings.append({
            'type': 'idp_configuration_change',
            'index': i,
            'time': time_val,
            'user': user,
            'operation': op
        })
    
    # Destination operations
    if obj_type == 'objectId':
        data_action = rec.get('message.data.action', '')
        data_object_id = rec.get('message.data.objectId', '')
        findings.append({
            'type': 'destination_operation',
            'index': i,
            'time': time_val,
            'user': user,
            'operation': op,
            'action': data_action,
            'object_id': data_object_id,
            'success': success,
            'status': status
        })
    
    # Security events
    if cat == 'audit.security-events':
        findings.append({
            'type': 'security_event',
            'index': i,
            'time': time_val,
            'user': user,
            'event_code': rec.get('message.data.event_code', ''),
            'ip': rec.get('message.ip', ''),
            'action': rec.get('message.data.action', ''),
            'object_type': rec.get('message.data.objectType', ''),
            'object_id': rec.get('message.data.objectId', '')
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
    print(f"  [{fo['time']}] {fo['operation']} on {fo['object_type']} by {fo['user']}")

findings_by_type = Counter()
for f in findings:
    findings_by_type[f['type']] += 1

print(f"\n=== FINDINGS BY TYPE ===")
for ft, count in sorted(findings_by_type.items(), key=lambda x: -x[1]):
    print(f"  {ft}: {count}")

# Role mapping details
role_f = [f for f in findings if f['type'] == 'role_mapping_change']
print(f"\n=== ROLE MAPPING CHANGES ({len(role_f)}) ===")
for rf in role_f:
    print(f"  [{rf['time']}] {rf['operation']}: Role={rf['role']}, Group={rf['saml_attr_value']}, IdP={rf['saml_idp']}, User={rf['user']}")

# IdP changes
idp_f = [f for f in findings if f['type'] == 'idp_configuration_change']
print(f"\n=== IDP CONFIGURATION CHANGES ({len(idp_f)}) ===")
for idpf in idp_f:
    print(f"  [{idpf['time']}] {idpf['operation']}: User={idpf['user']}")

# Destination ops
dest_f = [f for f in findings if f['type'] == 'destination_operation']
print(f"\n=== DESTINATION OPERATIONS ({len(dest_f)}) ===")
for df in dest_f:
    print(f"  [{df['time']}] {df['operation']}: Action={df['action']}, Object={df['object_id']}, Success={df['success']}, User={df['user']}")

# Security events
sec_f = [f for f in findings if f['type'] == 'security_event']
print(f"\n=== SECURITY EVENTS ({len(sec_f)}) ===")
for sf in sec_f:
    print(f"  [{sf['time']}] Event={sf['event_code']}, Action={sf['action']}, Object={sf['object_id']}, IP={sf['ip']}, User={sf['user']}")
