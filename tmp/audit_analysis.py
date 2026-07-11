#!/usr/bin/env python3
import json
import csv
import io
from collections import Counter, defaultdict

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

# ============ CATEGORIES ============
categories = Counter()
for r in records:
    categories[r.get('category', '')] += 1

print("\n=== RECORDS BY CATEGORY ===")
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

# ============ OPERATIONS ============
operations = Counter()
for r in records:
    op = r.get('message.object.id.crudType', '')
    operations[op] += 1

print("\n=== RECORDS BY OPERATION ===")
for op, count in sorted(operations.items(), key=lambda x: -x[1]):
    print(f"  {op or '(empty)'}: {count}")

# ============ USERS ============
users = Counter()
for r in records:
    users[r.get('user', '')] += 1

print("\n=== RECORDS BY USER ===")
for user, count in sorted(users.items(), key=lambda x: -x[1]):
    print(f"  {user}: {count}")

# ============ SUCCESS/FAILURE ============
success_fail = Counter()
for r in records:
    success_fail[r.get('message.success', '')] += 1

print("\n=== SUCCESS/FAILURE ===")
for s, count in sorted(success_fail.items(), key=lambda x: -x[1]):
    print(f"  {s or '(empty)'}: {count}")

# ============ OBJECT TYPES ============
object_types = Counter()
for r in records:
    object_types[r.get('message.object.type', '')] += 1

print("\n=== OBJECT TYPES ===")
for ot, count in sorted(object_types.items(), key=lambda x: -x[1]):
    print(f"  {ot or '(empty)'}: {count}")

# ============ STATUSES ============
statuses = Counter()
for r in records:
    statuses[r.get('message.status', '')] += 1

print("\n=== STATUSES ===")
for s, count in sorted(statuses.items(), key=lambda x: -x[1]):
    print(f"  {s}: {count}")

# ============ FAILED OPERATIONS ============
failed_ops = []
for i, rec in enumerate(records):
    if rec.get('message.success') == 'FALSE':
        failed_ops.append({
            'index': i,
            'uuid': rec.get('message_uuid', ''),
            'time': rec.get('time', ''),
            'user': rec.get('user', ''),
            'category': rec.get('category', ''),
            'operation': rec.get('message.object.id.crudType', ''),
            'object_type': rec.get('message.object.type', ''),
            'message_id': rec.get('message.id', ''),
            'object_id': rec.get('message.object.id.object_id', ''),
            'action': rec.get('message.data.action', ''),
            'event_code': rec.get('message.data.event_code', '')
        })

print(f"\n=== FAILED OPERATIONS ({len(failed_ops)}) ===")
for fo in failed_ops:
    print(f"  [{fo['time']}] {fo['operation']} on {fo['object_type']} by {fo['user']}")

# ============ DETAILED ANALYSIS ============
print("\n\n========== DETAILED ANALYSIS ==========")

# Role mapping changes
role_records = [r for r in records if r.get('message.object.type') == 'xsrolecollection2samlattribute']
print(f"\n--- Role Mapping Changes: {len(role_records)} ---")
for r in role_records:
    print(f"  [{r.get('time')}] {r.get('message.object.id.crudType')}: "
          f"Role={r.get('message.object.id.rolecollection_name')}, "
          f"Group={r.get('message.object.id.saml_attr_value')}, "
          f"IdP={r.get('message.object.id.saml_idp')}, "
          f"User={r.get('user')}")

# IdP changes
idp_records = [r for r in records if r.get('message.object.type') == 'custom platform idp distribution']
print(f"\n--- IdP Configuration Changes: {len(idp_records)} ---")
for r in idp_records:
    print(f"  [{r.get('time')}] {r.get('message.object.id.crudType')}: User={r.get('user')}")

# Destination operations
dest_records = [r for r in records if r.get('message.object.type') == 'objectId']
print(f"\n--- Destination Operations: {len(dest_records)} ---")
for r in dest_records:
    print(f"  [{r.get('time')}] {r.get('message.object.id.crudType')}: "
          f"Action={r.get('message.data.action')}, "
          f"Object={r.get('message.data.objectId')}, "
          f"Success={r.get('message.success')}, "
          f"User={r.get('user')}")

# Security events
sec_records = [r for r in records if r.get('category') == 'audit.security-events']
print(f"\n--- Security Events: {len(sec_records)} ---")
for r in sec_records:
    print(f"  [{r.get('time')}] Event={r.get('message.data.event_code')}, "
          f"Action={r.get('message.data.action')}, "
          f"Object={r.get('message.data.objectType')}/{r.get('message.data.objectId')}, "
          f"IP={r.get('message.ip')}, "
          f"User={r.get('user')}")

# ============ OUTPUT JSON ============
# Build the structured output
records_by_category = {cat: count for cat, count in sorted(categories.items(), key=lambda x: -x[1])}
records_by_operation = {op or 'NONE': count for op, count in sorted(operations.items(), key=lambda x: -x[1])}

# Detailed failed operations
failed_details = []
for fo in failed_ops:
    failed_details.append({
        'timestamp': fo['time'],
        'user': fo['user'],
        'category': fo['category'],
        'operation': fo['operation'],
        'object_type': fo['object_type'],
        'message_id': fo['message_id']
    })

# Findings
findings = []

# Finding 1: IdP configuration changes with missing usernames
idp_missing_user = [r for r in idp_records if r.get('user') == '<username missing>']
if idp_missing_user:
    findings.append({
        'category': 'Identity Provider Configuration',
        'description': f'{len(idp_missing_user)} updates to custom platform identity provider (OIDC) configuration were performed by an unidentified user ("<username missing>"). The IdP configuration includes auth URLs, token URLs, token keys, client credentials, and scope settings.',
        'impact': 'Unauthorized or unattributed changes to the identity provider configuration could compromise authentication trust, redirect credentials, or weaken security controls.',
        'risk_level': 'HIGH'
    })

# Finding 2: Role mapping changes
role_creates = [r for r in role_records if r.get('message.object.id.crudType') == 'CREATE']
role_deletes = [r for r in role_records if r.get('message.object.id.crudType') == 'DELETE']
if role_creates or role_deletes:
    findings.append({
        'category': 'Role Collection SAML Attribute Mapping',
        'description': f'{len(role_creates)} role-to-SAML-attribute mappings were created and {len(role_deletes)} were deleted by user DGANDIBO@ITS.JNJ.com. Mappings link SAML groups from external IdPs (aaf6lv7c2.accounts.ondemand.com, a6nzgx2e6.accounts.ondemand.com, PJS100_OA2C) to BTP role collections (ZS0-CLS-Security-Admin, ZS0-CLS-Monitor).',
        'impact': 'Role mappings control access to BTP resources. Changes can grant or revoke access for entire groups of users. The creation of mappings to privileged roles like ZS0-CLS-Security-Admin is particularly sensitive.',
        'risk_level': 'HIGH'
    })

# Finding 3: Failed destination creation
failed_dest = [r for r in dest_records if r.get('message.success') == 'FALSE']
if failed_dest:
    for fd in failed_dest:
        findings.append({
            'category': 'Failed Destination Operation',
            'description': f'Destination creation FAILED for "{fd.get("message.data.objectId")}" (Type: RFC) by user {fd.get("user")} at {fd.get("time")}. The destination contained credentials (jco.client.passwd, jco.client.user) and SAP system connection details.',
            'impact': 'Failed operations may indicate configuration errors, permission issues, or attempted unauthorized operations. The destination included RFC connection parameters with user credentials.',
            'risk_level': 'MEDIUM'
        })

# Finding 4: Successful destination creation with credentials
successful_dest_creates = [r for r in dest_records if r.get('message.success') == 'TRUE' and r.get('message.object.id.crudType') == 'CREATE']
if successful_dest_creates:
    for sd in successful_dest_creates:
        findings.append({
            'category': 'Destination Created with Credentials',
            'description': f'Destination "{sd.get("message.data.objectId")}" (Type: RFC) was successfully CREATED by user {sd.get("user")} at {sd.get("time")}. The destination includes RFC connection parameters with hashed credentials (jco.client.passwd, jco.client.user) and SAP system details (mshost, r3name, client).',
            'impact': 'Destinations with credentials provide access to backend SAP systems. Any compromise of the destination service could expose these connections.',
            'risk_level': 'MEDIUM'
        })

# Finding 5: Destination update with configuration changes
dest_updates = [r for r in dest_records if r.get('message.object.id.crudType') == 'UPDATE' and r.get('message.success') == 'TRUE']
if dest_updates:
    for du in dest_updates:
        changed_keys = du.get('message.object.id.object_id', '')
        findings.append({
            'category': 'Destination Configuration Updated',
            'description': f'Destination configuration was UPDATED by user {du.get("user")} at {du.get("time")}. Changed properties include: {changed_keys}. The destination was renamed from "rfc_comet_rab_sustain" to "rfc_comet_rpb_sustain" with type RFC and OnPremise proxy.',
            'impact': 'Changes to destination configurations can alter connectivity to backend systems, potentially redirecting traffic or modifying authentication methods.',
            'risk_level': 'MEDIUM'
        })

# Finding 6: Security events - encryption key creation
sec_events = sec_records
for se in sec_events:
    if se.get('message.data.action') == 'Create' and se.get('message.data.objectType') == 'EncryptionKey':
        findings.append({
            'category': 'Encryption Key Created',
            'description': f'Encryption key "{se.get("message.data.objectId")}" was created by the SAP Job Scheduler service (user: SAP) from IP 127.0.0.1 at {se.get("time")}. This is a system-level cryptographic operation.',
            'impact': 'Encryption key creation is a sensitive operation. While performed by the system, any compromise of encryption keys could lead to data exposure.',
            'risk_level': 'MEDIUM'
        })
    elif 'authorization.Success' in se.get('message.data.event_code', ''):
        findings.append({
            'category': 'Authorization Success Events',
            'description': f'Authorization success event "{se.get("message.data.event_code")}" from IP {se.get("message.ip")} at {se.get("time")}. User: {se.get("user")}.',
            'impact': 'These are routine authorization success events for the Document Information Extraction service. Multiple successful authorizations from different IPs (10.0.72.1, 10.0.136.3) indicate normal service operation.',
            'risk_level': 'LOW'
        })

# Finding 7: Missing usernames pattern
missing_user_count = sum(1 for r in records if r.get('user') == '<username missing>')
if missing_user_count > 0:
    findings.append({
        'category': 'Unidentified User Activity',
        'description': f'{missing_user_count} out of {len(records)} records have "<username missing>" as the user. These include all {len(idp_records)} IdP configuration updates and potentially other operations.',
        'impact': 'Inability to attribute configuration changes to specific users hinders accountability, auditability, and incident response. This is a significant audit gap.',
        'risk_level': 'HIGH'
    })

# Recommendations
recommendations = [
    {
        'category': 'Identity Provider Changes',
        'recommendation': 'Investigate all custom platform identity provider (OIDC) updates performed by unidentified users. Ensure that service accounts or automated processes are properly identified in audit logs with meaningful usernames.',
        'priority': 'HIGH'
    },
    {
        'category': 'User Attribution',
        'recommendation': 'Configure all BTP services and automation tools to use identifiable service accounts or technical users instead of producing "<username missing>" entries in audit logs. Review IAM configuration for the platform IdP distribution service.',
        'priority': 'HIGH'
    },
    {
        'category': 'Role Mapping Review',
        'recommendation': 'Review all SAML attribute-to-role-collection mappings created by DGANDIBO@ITS.JNJ.com. Verify that the mappings to ZS0-CLS-Security-Admin and ZS0-CLS-Monitor role collections are authorized and follow the principle of least privilege.',
        'priority': 'HIGH'
    },
    {
        'category': 'Destination Security',
        'recommendation': 'Audit all RFC destinations created with CONFIGURED_USER authentication type. Verify that credentials stored in destinations are rotated regularly and that destinations use encrypted communication where possible.',
        'priority': 'MEDIUM'
    },
    {
        'category': 'Failed Operations Investigation',
        'recommendation': 'Investigate the failed destination creation for "rfc_panda_mulesoft_migration" by KRenduch@ITS.JNJ.com. Determine if this was a permission issue, configuration error, or security control preventing unauthorized access.',
        'priority': 'MEDIUM'
    },
    {
        'category': 'Encryption Key Monitoring',
        'recommendation': 'Monitor encryption key creation events (AVATAR_DB_PRIVATE_KEY_15) to ensure they follow established key management procedures and rotation policies.',
        'priority': 'MEDIUM'
    },
    {
        'category': 'Audit Log Completeness',
        'recommendation': 'Enable detailed user attribution for all BTP services. Configure audit log policies to capture complete user identity information for all administrative operations.',
        'priority': 'HIGH'
    }
]

# Build final output
output = {
    'status': 'SUCCESS',
    'job_id': 'JOB_20260709040929',
    'review_count': len(records),
    'risk_level': 'HIGH',
    'summary': f'Analysis of {len(records)} audit log review records from the SAP BTP audit log review file. '
               f'Found {len(idp_records)} identity provider configuration changes (all with missing usernames), '
               f'{len(role_records)} role collection SAML attribute mapping changes, '
               f'{len(dest_records)} destination operations, '
               f'{len(sec_records)} security events, and '
               f'{len(failed_ops)} failed operations. '
               f'Overall risk level is HIGH due to unattributed IdP configuration changes and sensitive role mapping modifications.',
    'total_records': len(records),
    'records_by_category': records_by_category,
    'records_by_operation': records_by_operation,
    'failed_operations': failed_details,
    'findings': findings,
    'recommendations': recommendations
}

print("\n\n========== FINAL JSON OUTPUT ==========")
print(json.dumps(output, indent=2))

# Save to file
with open('/tmp/audit_analysis_output.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n\nSaved to /tmp/audit_analysis_output.json")
