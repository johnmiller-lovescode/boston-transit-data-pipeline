import os, json, gzip, io, datetime, logging
from urllib import request
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
S3 = boto3.client("s3")

MBTA_API_URL = os.getenv("MBTA_API_URL", "https://api.mbta.com/vehicles")
RAW_BUCKET = os.getenv("RAW_BUCKET")
PROJECT_NAME = os.getenv("PROJECT_NAME", "boston-transit")

def fetch_mbta():
    req = request.Request(MBTA_API_URL)
    with request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def to_ndjson(records):
    buf = io.StringIO()
    for rec in records:
        buf.write(json.dumps(rec, separators=(",",":")) + "\n")
    return buf.getvalue().encode("utf-8")

def put_gz_bytes(bucket, key, data_bytes):
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, compresslevel=5) as gz:
        gz.write(data_bytes)
    out.seek(0)
    S3.put_object(Bucket=bucket, Key=key, Body=out.getvalue(),
                  ContentType="application/x-ndjson", ContentEncoding="gzip")

def handler(event, context):
    if not RAW_BUCKET:
        raise RuntimeError("RAW_BUCKET env var is required")
    payload = fetch_mbta()
    records = payload.get("data") if isinstance(payload, dict) else None
    if not records:
        records = [payload]

    now = datetime.datetime.utcnow()
    date_prefix = now.strftime("%Y-%m-%d")
    ts = int(now.timestamp())
    key = f"{date_prefix}/ingest-{ts}.ndjson.gz"

    ndjson_bytes = to_ndjson(records)
    put_gz_bytes(RAW_BUCKET, key, ndjson_bytes)

    logger.info({"wrote_bytes": len(ndjson_bytes), "s3_key": key, "count": len(records)})
    return {"status": "ok", "count": len(records), "s3_key": key}
