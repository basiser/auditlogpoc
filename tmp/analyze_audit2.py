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
            'message.attributes.0.new.config.platformIdp': row.get('message.attributes.0.new.config.platformIdp', ''),
            'message.attributes.0.new.config.applicationIdp': row.get('message.attributes.0.new.config.applicationIdp', ''),
            'message.attributes.0.new.subdomain': row.get('message.attributes.0.new.subdomain', ''),
            'message.attributes.0.new.globalAccountId': row.get('message.attributes.0.new.globalAccountId', ''),
            'message.attributes.0.new.appName': row.get('message.attributes.0.new.appName', ''),
            'message.attributes.0.new.planId': row.get('message.attributes.0.new.planId', ''),
            'message.attributes.0.new.code': row.get('message.attributes.0.new.code', ''),
            'message.attributes.0.new.amount': row.get('message.attributes.0.new.amount', ''),
            'message.attributes.0.new.id': row.get('message.attributes.0.new.id', ''),
            'message.attributes.0.new.internalSubscriptionId': row.get('message.attributes.0.new.internalSubscriptionId', ''),
            'message.attributes.0.new.rootIdentifier': row.get('message.attributes.0.new.rootIdentifier', ''),
            'message.attributes.0.new.appId': row.get('message.attributes.0.new.appId', ''),
            'message.attributes.0.new.consumerId': row.get('message.attributes.0.new.consumerId', ''),
            'message.attributes.0.new.subaccountId': row.get('message.attributes.0.new.subaccountId', ''),
            'message.attributes.0.new.subscriptionGUID': row.get('message.attributes.0.new.subscriptionGUID', ''),
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
    
    # 7. Summary by event type with details
    print("=" * 80)
    print("SUMMARY BY EVENT TYPE")
    print("=" * 80)
    event_details = defaultdict(list)
    for r in records:
        event_details[r['message.id']].append(r)
    
    for event, recs in sorted(event_details.items(), key=lambda x: -len(x[1])):
        print(f"\n--- {event} ({len(recs)} records) ---")
        users = set(r['user'] for r in recs)
        print(f"  Users: {', '.join(sorted(users))}")
        crud_types = set(r['message.object.id.crudType'] for r in recs if r['message.object.id.crudType'])
        if crud_types:
            print(f"  CRUD Types: {', '.join(sorted(crud_types))}")
        states = set(r['message.attributes.0.new.state'] for r in recs if r['message.attributes.0.new.state'])
        if states:
            print(f"  States: {', '.join(sorted(states))}")
        origins = set(r['message.attributes.0.new.origin'] for r in recs if r['message.attributes.0.new.origin'])
        if origins:
            print(f"  Origins: {', '.join(sorted(origins))}")
        # Show first record details
        r = recs[0]
        print(f"  Sample - Time: {r['time']}, User: {r['user']}, Entity: {r['message.object.id.entity'][:80] if r['message.object.id.entity'] else 'N/A'}")
        if r['message.attributes.0.new.config.providerDescription']:
            print(f"  Provider: {r['message.attributes.0.new.config.providerDescription']}")
        if r['message.attributes.0.new.config.linkText']:
            print(f"  Link Text: {r['message.attributes.0.new.config.linkText']}")
        if r['message.attributes.0.new.url']:
            print(f"  URL: {r['message.attributes.0.new.url']}")
        if r['message.attributes.0.new.originKey']:
            print(f"  Origin Key: {r['message.attributes.0.new.originKey']}")
        if r['message.attributes.0.new.changeMode']:
            print(f"  Change Mode: {r['message.attributes.0.new.changeMode']}")
        if r['message.attributes.0.new.keyId']:
            print(f"  Key ID: {r['message.attributes.0.new.keyId']}")
        if r['message.attributes.0.new.operation']:
            print(f"  Operation: {r['message.attributes.0.new.operation']}")
        if r['message.attributes.0.new.status']:
            print(f"  Status: {r['message.attributes.0.new.status']}")
        if r['message.attributes.0.new.active']:
            print(f"  Active: {r['message.attributes.0.new.active']}")
        if r['message.attributes.0.new.appName']:
            print(f"  App Name: {r['message.attributes.0.new.appName']}")
        if r['message.attributes.0.new.planId']:
            print(f"  Plan: {r['message.attributes.0.new.planId']}")
        if r['message.data.action']:
            print(f"  Data Action: {r['message.data.action']}")
        if r['message.data.objectType']:
            print(f"  Data ObjectType: {r['message.data.objectType']}")
        if r['message.data.event_code']:
            print(f"  Event Code: {r['message.data.event_code']}")
        if r['message.ip']:
            print(f"  IP: {r['message.ip']}")
    
    # Output as JSON for further processing
    print()
    print("=" * 80)
    print("JSON OUTPUT")
    print("=" * 80)
    
    # Build structured analysis
    analysis = {
        "total_records": len(records),
        "event_breakdown": dict(event_counter.most_common()),
        "user_breakdown": dict(user_counter.most_common()),
        "crud_breakdown": dict(crud_counter.most_common()),
        "object_type_breakdown": dict(obj_counter.most_common()),
        "success_breakdown": dict(success_counter.most_common()),
        "user_event_matrix": {user: dict(events.most_common()) for user, events in sorted(user_event.items())}
    }
    print(json.dumps(analysis, indent=2))
    
else:
    print("Could not extract CSV data")
