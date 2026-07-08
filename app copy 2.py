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

    # Load review filter definitions

    with open(
        "filters.json",
        "r",
        encoding="utf-8"
    ) as f:

        filters = json.load(f)

    review_count = 0
    ignored_count = 0

    with open(
        dump_path,
        newline="",
        encoding="utf-8"
    ) as source, open(
        review_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as target:

        reader = csv.DictReader(source)

        writer = csv.DictWriter(
            target,
            fieldnames=reader.fieldnames
        )

        writer.writeheader()

        for row in reader:

            ignore = False

            # Filter category

            if row.get("category") in filters["category"]:
                ignore = True

            # Filter user

            if row.get("user") in filters["user"]:
                ignore = True

            try:

                # Parse Audit Log JSON message

                msg = json.loads(
                    row.get("message", "{}")
                )

                object_type = (
                    msg.get("object", {})
                    .get("type")
                )

                if (
                    object_type
                    in filters[
                        "message.object.type"
                    ]
                ):
                    ignore = True

                data_action = (
                    msg.get("data", {})
                    .get("action")
                )

                if (
                    data_action
                    in filters[
                        "message.data.action"
                    ]
                ):
                    ignore = True

                object_message = (
                    msg.get("object", {})
                    .get("id", {})
                    .get("message")
                )

                if (
                    object_message
                    in filters[
                        "message.object.id.message"
                    ]
                ):
                    ignore = True

                # Ignore non-empty data field

                if (
                    msg.get("data", {})
                    .get("data")
                ):
                    ignore = True

                # Ignore non-empty message field

                if (
                    msg.get("data", {})
                    .get("message")
                ):
                    ignore = True

            except Exception:
                pass

            if ignore:

                ignored_count += 1

            else:

                review_count += 1

                writer.writerow(row)

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