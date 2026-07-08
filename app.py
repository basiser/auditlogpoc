from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, date
import requests
import csv
import os
import json
import threading

app = FastAPI(title="Audit Log Exporter")

EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


class AuditRequest(BaseModel):
    audit_token: str
    subaccount_id: str
    start_date: date
    end_date: date

class ReviewRequest(BaseModel):
    job_id: str

# Flatten nested JSON structure
# into Excel friendly columns
def flatten_json(
    data,
    parent_key="",
    sep="."
):

    items = {}

    #
    # Parse nested JSON string recursively
    #
    if isinstance(data, str):

        value = data.strip()

        if (
            (value.startswith("{")
             and value.endswith("}"))
            or
            (value.startswith("[")
             and value.endswith("]"))
        ):

            try:

                data = json.loads(
                    value
                )

            except Exception:
                pass

    if isinstance(data, dict):

        for k, v in data.items():

            new_key = (
                f"{parent_key}{sep}{k}"
                if parent_key
                else k
            )

            items.update(
                flatten_json(
                    v,
                    new_key,
                    sep
                )
            )

    elif isinstance(data, list):

        for i, v in enumerate(data):

            new_key = (
                f"{parent_key}{sep}{i}"
            )

            items.update(
                flatten_json(
                    v,
                    new_key,
                    sep
                )
            )

    else:

        items[parent_key] = data

    return items

@app.get("/health")
def health():
    return {
        "status": "UP"
    }


@app.get("/download/{filename}")
def download_file(filename: str):

    filepath = os.path.join(EXPORT_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return FileResponse(
        path=filepath,
        media_type="text/csv",
        filename=filename
    )


@app.get("/job/{job_id}")
def get_job_status(job_id: str):

    status_file = None

    for file in os.listdir(EXPORT_DIR):

        if (
            file.startswith("Joblog-")
            and job_id in file
        ):

            status_file = os.path.join(
                EXPORT_DIR,
                file
            )

            break

    if not status_file:

        return {
            "job_id": job_id,
            "status": "running"
        }

    with open(
        status_file,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def export_job(
    job_id: str,
    req: AuditRequest,
    filename: str,
    filepath: str,
    joblog_filename: str
):

    url = (
        "https://auditlog-management.cfapps.us10.hana.ondemand.com"
        "/auditlog/v2/auditlogrecords"
    )

    headers = {
        "Authorization": f"Bearer {req.audit_token}"
    }

    total_records = 0
    writer = None

    try:

        with open(
            filepath,
            mode="w",
            newline="",
            encoding="utf-8"
        ) as csvfile:

            # First request
            params = {
                "from": req.start_date.strftime("%Y-%m-%d"),
                "to": req.end_date.strftime("%Y-%m-%d")
            }

            while True:

                response = requests.get(
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=300
                )

                response.raise_for_status()

                logs = response.json()

                if not isinstance(logs, list):
                    raise Exception(
                        "Unexpected API response format"
                    )

                if len(logs) == 0:
                    break

                if writer is None:

                    fieldnames = list(logs[0].keys())

                    writer = csv.DictWriter(
                        csvfile,
                        fieldnames=fieldnames,
                        extrasaction="ignore"
                    )

                    writer.writeheader()

                for record in logs:
                    writer.writerow(record)

                total_records += len(logs)

                print(
                    f"Page completed: "
                    f"records={len(logs)}, "
                    f"total={total_records}"
                )

                paging_header = response.headers.get(
                    "paging"
                )

                print(
                    f"Paging Header: {paging_header}"
                )

                if not paging_header:

                    print(
                        "Paging header not found. "
                        "Reached last page."
                    )

                    break

                if not paging_header.startswith(
                    "handle="
                ):

                    print(
                        "Invalid paging header. "
                        "Reached last page."
                    )

                    break

                handle = paging_header.replace(
                    "handle=",
                    "",
                    1
                )

                if not handle.strip():

                    print(
                        "Empty handle returned. "
                        "Reached last page."
                    )

                    break

                # Next page request
                params = {
                    "handle": handle
                }

        filesize_mb = round(
            os.path.getsize(filepath) / 1024 / 1024,
            2
        )

        result = {
            "job_id": job_id,
            "status": "completed",
            "record_count": total_records,
            "file_name": filename,
            "file_path": filepath,
            "file_size_mb": filesize_mb,
            "download_url": f"/download/{filename}"
        }

    except Exception as ex:

        result = {
            "job_id": job_id,
            "status": "failed",
            "error": str(ex)
        }

    # Save job execution result

    status_file = os.path.join(
       EXPORT_DIR,
       joblog_filename
    )

    with open(
        status_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=2
        )


@app.post("/export")
def export_audit_log(req: AuditRequest):

    if req.start_date >= req.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date"
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    job_id = f"JOB_{timestamp}"

    # Common name shared by all files
    # belonging to the same export job

    base_name = (
        f"{req.subaccount_id}-"
        f"{req.start_date.strftime('%Y-%m-%d')}-"
        f"{req.end_date.strftime('%Y-%m-%d')}-"
        f"{job_id}"
    )

    # Raw audit log dump file

    filename = (
        f"Dump-{base_name}.csv"
    )

    # Job execution log file

    joblog_filename = (
        f"Joblog-{base_name}.json"
    )

    filepath = os.path.join(
        EXPORT_DIR,
        filename
    )

    thread = threading.Thread(
        target=export_job,
        args=(
            job_id,
            req,
            filename,
            filepath,
            joblog_filename
        )
    )

    thread.start()

    return {
        "status": "initiated",
        "job_id": job_id,
        "file_name": filename
    }
    
@app.post("/review")
def generate_review_file(req: ReviewRequest):

    dump_file = None

    for file in os.listdir(EXPORT_DIR):

        if (
            file.startswith("Dump-")
            and req.job_id in file
        ):
            dump_file = file
            break

    if not dump_file:

        raise HTTPException(
            status_code=404,
            detail="Dump file not found"
        )

    dump_path = os.path.join(
        EXPORT_DIR,
        dump_file
    )

    review_file = dump_file.replace(
        "Dump-",
        "Review-"
    )

    review_path = os.path.join(
        EXPORT_DIR,
        review_file
    )

    #
    # Load review filter definitions
    #
    with open(
        "filters.json",
        "r",
        encoding="utf-8"
    ) as f:

        filters = json.load(f)

    review_rows = []

    review_count = 0
    ignored_count = 0

    with open(
        dump_path,
        newline="",
        encoding="utf-8"
    ) as source:

        reader = csv.DictReader(source)

        for row in reader:

            ignore = False

            try:

                #
                # Parse message JSON
                #
                msg = json.loads(
                    row.get(
                        "message",
                        "{}"
                    )
                )

            except Exception:

                msg = {}

            #
            # Flatten message JSON
            #
            flattened = flatten_json(
                msg,
                "message"
            )

            #
            # Filter category
            #
            if (
                row.get(
                    "category"
                )
                in filters.get(
                    "category",
                    []
                )
            ):
                ignore = True

            #
            # Filter user
            #
            if (
                row.get(
                    "user"
                )
                in filters.get(
                    "user",
                    []
                )
            ):
                ignore = True

            #
            # Filter object type
            #
            if (
                flattened.get(
                    "message.object.type"
                )
                in filters.get(
                    "message.object.type",
                    []
                )
            ):
                ignore = True

            #
            # Filter data action
            #
            if (
                flattened.get(
                    "message.data.action"
                )
                in filters.get(
                    "message.data.action",
                    []
                )
            ):
                ignore = True

            #
            # Filter message text
            #
            if (
                flattened.get(
                    "message.object.id.message"
                )
                in filters.get(
                    "message.object.id.message",
                    []
                )
            ):
                ignore = True

            #
            # Filter loggedBy
            #
            if (
                flattened.get(
                    "message.object.id.loggedBy"
                )
                in filters.get(
                    "message.object.id.loggedBy",
                    []
                )
            ):
                ignore = True

            if ignore:

                ignored_count += 1

                continue

            review_count += 1

            #
            # Keep original columns
            #
            review_row = {
                key: value
                for key, value
                in row.items()
                if key != "message"
            }

            #
            # Add flattened message columns
            #
            review_row.update(
                flattened
            )

            review_rows.append(
                review_row
            )

    #
    # Build dynamic columns
    #
    all_columns = []

    for row in review_rows:

        for col in row.keys():

            if col not in all_columns:

                all_columns.append(
                    col
                )

    #
    # Write review file
    #
    with open(
        review_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as target:

        writer = csv.DictWriter(
            target,
            fieldnames=all_columns,
            extrasaction="ignore"
        )

        writer.writeheader()

        for row in review_rows:

            writer.writerow(
                row
            )

    print(
        f"Review completed. "
        f"job_id={req.job_id}, "
        f"review_count={review_count}, "
        f"ignored_count={ignored_count}"
    )

    return {
        "status": "completed",
        "job_id": req.job_id,
        "review_count": review_count,
        "ignored_count": ignored_count,
        "review_file": review_file,
        "download_url": (
            f"/download/{review_file}"
        )
    }