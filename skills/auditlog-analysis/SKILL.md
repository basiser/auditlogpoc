---
name: auditlog-analysis
description: Analyze SAP BTP audit log review files and generate security findings for a requested period. Use when users ask for audit log analysis, security review, failed logins, suspicious activities, role changes, compliance reviews, audit summaries, monthly reports, daily reports, audit investigations, or security findings.
---

# Overview

Use this skill when the user requests analysis of SAP BTP audit logs.

Examples:

- Analyze audit logs for July 2026
- Analyze audit logs for last month
- Review audit logs for yesterday
- Identify suspicious activities
- Generate audit security report
- Summarize audit findings

Only use data returned by MCP tools.

Never invent audit log records.

Never fabricate security findings.

Never fabricate recommendations.

Only use evidence found in retrieved audit log records.

---

# Tool Usage Rules

For this skill:

Use:

- mcp_auditlog_Joblogs
- mcp_auditlog_reviewfile

Use built-in filesystem tools when saving reports.

Do NOT use:

- get_tickets_data
- analyze_ticket_summary

These tools are ticket-analysis tools and are incompatible with audit log review files.

Use get_execution only when execution details are explicitly requested.

---

# Step 1 - Retrieve Audit Log Jobs

Call:

mcp_auditlog_Joblogs

Retrieve all available audit log jobs.

Do not continue until job data has been retrieved.

---

# Step 2 - Filter Jobs

Only consider jobs where:

status = completed

Ignore:

- pending
- running
- failed
- cancelled

jobs.

---

# Step 3 - Determine Requested Period

Determine the requested period from the user request.

Examples:

- July 2026
- June 2026
- Jan 2026
- 2026-07-09
- yesterday
- today
- last 24 hours
- this month
- last month

Translate relative periods using the current date.

Examples:

- today → current date
- yesterday → current date minus one day
- this month → current month
- last month → previous calendar month

---

# Step 4 - Match Job

Match the requested period against available jobs using:

- job_id
- dump_file
- review_file
- timestamps contained in file names

If multiple jobs match:

Select one job using:

1. Latest timestamp
2. Highest review_count
3. Highest record_count

Use only one selected job.

Never automatically substitute another period.

Example:

User asks:

"Analyze audit logs for last month"

Expected period:

June 2026

If no June 2026 job exists:

Return NO_MATCHING_JOB.

Do NOT automatically select a July job.

---

# Step 4.5 - Validation

If no jobs are returned:

```json
{
  "status": "NO_DATA",
  "reason": "No audit log jobs found"
}
```

Stop processing.

If no completed jobs are available:

```json
{
  "status": "NO_COMPLETED_JOB",
  "reason": "No completed audit log jobs available"
}
```

Stop processing.

If no matching completed job exists:

```json
{
  "status": "NO_MATCHING_JOB",
  "reason": "No completed audit log job found for requested period"
}
```

Stop processing.

---

# Step 5 - Retrieve Review File

Call:

mcp_auditlog_reviewfile

Input:

selected job_id

Retrieve the review file content.

---

# Step 5.5 - Review File Validation

If review file retrieval fails:

```json
{
  "status": "REVIEW_FILE_ERROR",
  "job_id": "<job_id>"
}
```

Stop processing.

If review file is empty:

```json
{
  "status": "EMPTY_REVIEW_FILE",
  "job_id": "<job_id>"
}
```

Stop processing.

---

# Step 6 - Review File Processing Rules

Analyze the review file directly.

Do not aggregate records before analysis.

Do not summarize records before analysis.

Do not use statistical approximation.

Do not use sampling.

Do not analyze only the first N records.

Do not skip records.

Every available review record must be examined.

If the review file is large:

- Read it in multiple passes if required.
- Continue until all records have been reviewed.

The final findings must be based on the complete review file.

If review_count is less than 1000:

Analyze all records directly.

Do not delegate the analysis to another workflow unnecessarily.

---

# Step 7 - Audit Log Analysis

Examine every review record.

Look for:

## Authentication Activities

- Failed logins
- Repeated login failures
- Brute-force-like behavior
- Successful login after multiple failures

## Authorization Activities

- Role assignments
- Role removals
- Permission updates
- Privilege changes

## User Lifecycle Activities

- User creation
- User deletion
- User activation
- User deactivation

## Administrative Activities

- Configuration changes
- Security configuration changes
- Trust configuration changes
- Identity provider changes

## Security-Relevant Activities

- Suspicious patterns
- Unusual user activities
- High-risk administrative actions
- Potential misuse indicators

For every finding:

Identify:

- Event type
- User
- Timestamp
- Operation
- Impact

when available.

---

# Step 8 - Risk Assessment

Determine:

- LOW
- MEDIUM
- HIGH

Risk level must be based only on reviewed audit records.

Never guess.

Never estimate.

---

# Step 9 - Generate Structured Result

Generate:

```json
{
  "status": "SUCCESS",
  "job_id": "",
  "review_count": 0,
  "risk_level": "LOW",
  "summary": "",
  "findings": [],
  "recommendations": []
}
```

Each finding should contain:

```json
{
  "category": "",
  "description": "",
  "impact": ""
}
```

Each recommendation must be actionable.

---

# Step 10 - Save Results

Create:

## Human-readable Report

Path:

download/AuditAnalysis-{job_id}.md

Contents:

- Job Information
- Analysis Scope
- Executive Summary
- Risk Level
- Findings
- Recommendations

## JSON Report

Path:

download/AuditAnalysis-{job_id}.json

Contents:

Structured JSON generated in Step 9.

Use built-in filesystem tools to save the files.

---

# Step 11 - Final Response

Always return JSON.

Return:

```json
{
  "status": "SUCCESS",
  "job_id": "",
  "risk_level": "",
  "report_file": "",
  "json_file": "",
  "summary": "",
  "findings": [],
  "recommendations": []
}
```

Possible status values:

- SUCCESS
- NO_DATA
- NO_COMPLETED_JOB
- NO_MATCHING_JOB
- REVIEW_FILE_ERROR
- EMPTY_REVIEW_FILE

Never return Markdown when JSON is requested.

Never fabricate audit log records.

Never fabricate findings.

Never fabricate recommendations.

All conclusions must be traceable to audit log records retrieved through MCP tools.