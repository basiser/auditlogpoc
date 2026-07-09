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
    start_time: datetime
    end_time: datetime


# Flatten nested JSON structure
# into Excel friendly columns
def flatten_json(
    data,
    parent_key="",
    sep="."
):

    items = {}

    #
    # Parse nested JSON string
    #
    if isinstance(data, str):

        value = data.strip()

        if (
            value.startswith("{")
            or value.startswith("[")
            or value.startswith('"')
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


#
# Review generation logic
#

def create_review_file(
    job_id: str,
    dump_file: str
):

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

                msg = json.loads(
                    row.get(
                        "message",
                        "{}"
                    )
                )

            except Exception:

                msg = {}

            flattened = flatten_json(
                msg,
                "message"
            )

            filter_data = {}

            filter_data.update(
                flattened
            )

            filter_data["category"] = row.get(
                "category"
            )

            filter_data["user"] = row.get(
                "user"
            )

            for field, values in filters.items():

                current_value = filter_data.get(
                    field
                )

                if current_value is None:
                    continue

                if "__NOTEMPTY__" in values:

                    if (
                        current_value is not None
                        and str(current_value).strip() != ""
                    ):
                        ignore = True
                        break

                if str(current_value).lower() in [
                    str(v).lower()
                    for v in values
                    if v != "__NOTEMPTY__"
                ]:

                    ignore = True
                    break

            if ignore:

                ignored_count += 1
                continue

            review_count += 1

            review_row = {
                key: value
                for key, value
                in row.items()
                if key != "message"
            }

            review_row.update(
                flattened
            )

            review_rows.append(
                review_row
            )

    all_columns = []

    for row in review_rows:

        for col in row.keys():

            if col not in all_columns:

                all_columns.append(
                    col
                )

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

    return {
        "review_file": review_file,
        "review_count": review_count,
        "ignored_count": ignored_count,
        "download_url": (
            f"/download/{review_file}"
        )
    }
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


@app.get("/jobs")
def get_jobs():

    jobs = []

    for file in os.listdir(EXPORT_DIR):

        if not file.startswith(
            "Joblog-"
        ):
            continue

        file_path = os.path.join(
            EXPORT_DIR,
            file
        )

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                job_result = json.load(f)

                jobs.append(
                    job_result
                )

        except Exception as ex:

            jobs.append(
                {
                    "file": file,
                    "status": "invalid",
                    "error": str(ex)
                }
            )

    #
    # Sort newest first
    #
    jobs.sort(
        key=lambda x: x.get(
            "job_id",
            ""
        ),
        reverse=True
    )

    return {
        "count": len(jobs),
        "jobs": jobs
    }


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
                "from": req.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "to": req.end_time.strftime("%Y-%m-%dT%H:%M:%S")
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

        review_result = create_review_file(
            job_id=job_id,
            dump_file=filename
        )
        result = {
            "job_id": job_id,
            "status": "completed",

            "record_count": total_records,

            "dump_file": filename,

            "file_path": filepath,

            "file_size_mb": filesize_mb,

            "dump_download_url":
                f"/download/{filename}",

            "review_file":
                review_result["review_file"],

            "review_count":
                review_result["review_count"],

            "ignored_count":
                review_result["ignored_count"],

            "review_download_url":
                review_result["download_url"]
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

    if req.start_time >= req.end_time:
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
        f"{req.start_time.strftime('%Y-%m-%d')}-"
        f"{req.end_time.strftime('%Y-%m-%d')}-"
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
@app.get("/review/{job_id}")
def get_review_file(job_id: str):

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

        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    with open(
        status_file,
        "r",
        encoding="utf-8"
    ) as f:

        job_result = json.load(f)

    status = job_result.get(
        "status"
    )

    #
    # Export/Review still running
    #
    if status != "completed":

        return {
            "job_id": job_id,
            "status": status,
            "message": (
                "Review file is not ready yet"
            )
        }

    review_file = job_result.get(
        "review_file"
    )

    if not review_file:

        return {
            "job_id": job_id,
            "status": "failed",
            "message": (
                "Review file not found"
            )
        }

    review_path = os.path.join(
        EXPORT_DIR,
        review_file
    )

    if not os.path.exists(
        review_path
    ):

        return {
            "job_id": job_id,
            "status": "failed",
            "message": (
                "Review file does not exist"
            )
        }

    return FileResponse(
        path=review_path,
        media_type="text/csv",
        filename=review_file
    )