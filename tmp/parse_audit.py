import csv
import io
import json

# Read the CSV data from the file
with open('/large_tool_results/call_00_2uJO2KpgoEEEQR671d6z4977', 'r') as f:
    content = f.read()

# Extract the actual CSV data from the JSON wrapper
# The file contains: {"executionId":"...","status":"FINISHED",...,"outputValues":{"result":"CSV_DATA_HERE"}}
import re
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
        }
        records.append(record)
    
    print(f"Total records: {len(records)}")
    print(json.dumps(records, indent=2))
else:
    print("Could not extract CSV data")
