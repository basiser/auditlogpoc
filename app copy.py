from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime,date
import requests
import csv
import os

app = FastAPI(title="Audit Log Exporter")

EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


class AuditRequest(BaseModel):
    audit_token: str
    subaccount_id: str
    start_date: date
    end_date: date


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


@app.post("/export")
def export_audit_log(req: AuditRequest):

    if req.start_date >= req.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date"
        )

    filename = (
        f"audit_{req.subaccount_id}_"
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    )

    filepath = os.path.join(
        EXPORT_DIR,
        filename
    )

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
                    raise HTTPException(
                        status_code=500,
                        detail="Unexpected API response format"
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

        return {
            "status": "success",
            "record_count": total_records,
            "file_name": filename,
            "file_path": filepath,
            "file_size_mb": filesize_mb,
            "download_url": f"/download/{filename}"
        }

    except requests.exceptions.RequestException as ex:

        raise HTTPException(
            status_code=500,
            detail=f"Audit Log API call failed: {str(ex)}"
        )

    except Exception as ex:

        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(ex)}"
        )