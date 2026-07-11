import csv
import io
import json
import re
from collections import Counter, defaultdict

# Read the CSV data from the file
with open('/large_tool_results/call_00_2uJO2KpgoEEEQR671d6z4977', 'r') as f:
    content = f.read()

# Extract the actual CSV data from the JSON wrapper
match = re.search(r'"result":"(.*)"\}', content, re.DOTALL)
if match:
    csv_data = match.group(1)
    # Unescape the CSV data
    csv_data = csv_data.replace('\\r\\n', '\n').replace('\\n', '\n')
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_data))
    
    records = []
    for row in reader:
        record = {
            'time': row.get('time', ''),
            'user': row.get('user', ''),
            'category': row.get('category', ''),
            'message.id': row.get('message.id', ''),
            'message.success': row.get('message.success', ''),
            'message.object.type': row.get('message.object.type', ''),
            'message.object.id.entity': row.get('message.object.id.entity', ''),
            'message.attributes.0.name': row.get('message.attributes.0.name', ''),
            'message.attributes.0.old': row.get('message.attributes.0.old', ''),
            'message.attributes.0.new.id': row.get('message.attributes.0.new.id', ''),
            'message.attributes.0.new.state': row.get('message.attributes.0.new.state', ''),
            'message.attributes.0.new.origin': row.get('message.attributes.0.new.origin', ''),
            'message.attributes.0.new.type': row.get('message.attributes.0.new.type', ''),
            'message.attributes.0.new.operation': row.get('message.attributes.0.new.operation', ''),
            'message.attributes.0.new.status': row.get('message.attributes.0.new.status', ''),
            'message.attributes.0.new.name': row.get('message.attributes.0.new.name', ''),
            'message.attributes.0.new.active': row.get('message.attributes.0.new.active', ''),
            'message.attributes.0.new.originKey': row.get('message.attributes.0.new.originKey', ''),
            'message.attributes.0.new.changeMode': row.get('message.attributes.0.new.changeMode', ''),
            'message.attributes.0.new.keyId': row.get('message.attributes.0.new.keyId', ''),
            'message.object.id.crudType': row.get('message.object.id.crudType', ''),
            'message.object.id.origin': row.get('message.object.id.origin', ''),
            'message.data.action': row.get('message.data.action', ''),
            'message.data.objectType': row.get('message.data.objectType', ''),
            'message.data.event_code': row.get('message.data.event_code', ''),
            'message.ip': row.get('message.ip', ''),
            'message.attributes.0.new.url': row.get('message.attributes.0.new.url', ''),
            'message.attributes.0.new.config.providerDescription': row.get('message.attributes.0.new.config.providerDescription', ''),
            'message.attributes.0.new.config.linkText': row.get('message.attributes.0.new.config.linkText', ''),
            'message.attributes.0.new.config.originKeyCfuaa': row.get('message.attributes.0.new.config.originKeyCfuaa', ''),
            'message.attributes.0.new.config.platformIdp': row.get('message.attributes.0.new.config.platformIdp', ''),
            'message.attributes.0.new.config.applicationIdp': row.get('message.attributes.0.new.config.applicationIdp', ''),
            'message.attributes.0.new.subdomain': row.get('message.attributes.0.new.subdomain', ''),
            'message.attributes.0.new.globalAccountId': row.get('message.attributes.0.new.globalAccountId', ''),
            'message.attributes.0.new.appName': row.get('message.attributes.0.new.appName', ''),
            'message.attributes.0.new.planId': row.get('message.attributes.0.new.planId', ''),
            'message.attributes.0.new.code': row.get('message.attributes.0.new.code', ''),
            'message.attributes.0.new.amount': row.get('message.attributes.0.new.amount', ''),
        }
        records.append(record)
    
    print(f"Total records: {len(records)}")
    print()
    
    # 1. Event type breakdown
    print("=" * 80)
    print("EVENT TYPE BREAKDOWN (message.id)")
    print("=" * 80)
    event_counter = Counter()
    for r in records:
        event_counter[r['message.id']] += 1
    for event, count in event_counter.most_common():
        print(f"  {event}: {count}")
    
    print()
    
    # 2. User breakdown
    print("=" * 80)
    print("USER BREAKDOWN")
    print("=" * 80)
    user_counter = Counter()
    for r in records:
        user_counter[r['user']] += 1
    for user, count in user_counter.most_common():
        print(f"  {user}: {count}")
    
    print()
    
    # 3. CRUD operations
    print("=" * 80)
    print("CRUD OPERATIONS (message.object.id.crudType)")
    print("=" * 80)
    crud_counter = Counter()
    for r in records:
        crud_counter[r['message.object.id.crudType']] += 1
    for crud, count in crud_counter.most_common():
        print(f"  {crud}: {count}")
    
    print()
    
    # 4. Object types
    print("=" * 80)
    print("OBJECT TYPES")
    print("=" * 80)
    obj_counter = Counter()
    for r in records:
        obj_counter[r['message.object.type']] += 1
    for obj, count in obj_counter.most_common():
        print(f"  {obj}: {count}")
    
    print()
    
    # 5. Success/Failure
    print("=" * 80)
    print("SUCCESS/FAILURE")
    print("=" * 80)
    success_counter = Counter()
    for r in records:
        success_counter[r['message.success']] += 1
    for s, count in success_counter.most_common():
        print(f"  success={s}: {count}")
    
    print()
    
    # 6. Group by user and event
    print("=" * 80)
    print("USER x EVENT TYPE MATRIX")
    print("=" * 80)
    user_event = defaultdict(Counter)
    for r in records:
        user_event[r['user']][r['message.id']] += 1
    for user, events in sorted(user_event.items()):
        print(f"\n  User: {user}")
        for event, count in events.most_common():
            print(f"    {event}: {count}")
    
    print()
    
    # 7. Detailed records by event type
    print("=" * 80)
    print("DETAILED RECORDS BY EVENT TYPE")
    print("=" * 80)
    for r in records:
        print(f"\n  Time: {r['time']}")
        print(f"  User: {r['user']}")
        print(f"  Event: {r['message.id']}")
        print(f"  Success: {r['message.success']}")
        print(f"  Object Type: {r['message.object.type']}")
        print(f"  Entity: {r['message.object.id.entity']}")
        print(f"  Attribute: {r['message.attributes.0.name']}")
        print(f"  Old: {r['message.attributes.0.old'][:100] if r['message.attributes.0.old'] else 'N/A'}")
        print(f"  New State: {r['message.attributes.0.new.state']}")
        print(f"  New Type: {r['message.attributes.0.new.type']}")
        print(f"  Origin: {r['message.attributes.0.new.origin']}")
        print(f"  CRUD: {r['message.object.id.crudType']}")
        print(f"  Origin Key: {r['message.attributes.0.new.originKey']}")
        print(f"  Change Mode: {r['message.attributes.0.new.changeMode']}")
        print(f"  Key ID: {r['message.attributes.0.new.keyId']}")
        print(f"  URL: {r['message.attributes.0.new.url']}")
        print(f"  Provider: {r['message.attributes.0.new.config.providerDescription']}")
        print(f"  Link Text: {r['message.attributes.0.new.config.linkText']}")
        print(f"  Platform IDP: {r['message.attributes.0.new.config.platformIdp']}")
        print(f"  App Name: {r['message.attributes.0.new.appName']}")
        print(f"  Plan: {r['message.attributes.0.new.planId']}")
        print(f"  Operation: {r['message.attributes.0.new.operation']}")
        print(f"  Status: {r['message.attributes.0.new.status']}")
        print(f"  Active: {r['message.attributes.0.new.active']}")
        print(f"  Data Action: {r['message.data.action']}")
        print(f"  Data ObjectType: {r['message.data.objectType']}")
        print(f"  Event Code: {r['message.data.event_code']}")
        print(f"  IP: {r['message.ip']}")
        print("-" * 40)
    
else:
    print("Could not extract CSV data")
