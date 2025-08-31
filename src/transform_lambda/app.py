import os, io, gzip, json, datetime, logging, boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

log = logging.getLogger()
log.setLevel(logging.INFO)

S3 = boto3.client("s3")
RAW_BUCKET = os.getenv("RAW_BUCKET")
CURATED_BUCKET = os.getenv("CURATED_BUCKET")

def _iter_raw_keys(prefix_date):
    # list latest ~200 raw files for that date
    resp = S3.list_objects_v2(Bucket=RAW_BUCKET, Prefix=f"{prefix_date}/")
    for obj in resp.get("Contents", []):
        if obj["Key"].endswith(".ndjson.gz"):
            yield obj["Key"]

def _read_ndjson_gz(bucket, key):
    b = S3.get_object(Bucket=bucket, Key=key)["Body"].read()
    with gzip.GzipFile(fileobj=io.BytesIO(b)) as gz:
        for line in gz.read().decode("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)

def handler(event, context):
    # default: process today's raw files
    date_str = (datetime.datetime.utcnow()).strftime("%Y-%m-%d")
    records = []
    for key in _iter_raw_keys(date_str):
        for rec in _read_ndjson_gz(RAW_BUCKET, key):
            # normalize just a few useful fields; keep flexible
            d = {}
            d["id"] = rec.get("id")
            attr = (rec.get("attributes") or {})
            d["bearing"] = attr.get("bearing")
            d["current_status"] = attr.get("current_status")
            d["label"] = attr.get("label")
            d["latitude"] = attr.get("latitude")
            d["longitude"] = attr.get("longitude")
            d["speed"] = attr.get("speed")
            d["updated_at"] = attr.get("updated_at")
            # partition helpers
            relationships = rec.get("relationships") or {}
            route = (relationships.get("route") or {}).get("data") or {}
            d["route_id"] = route.get("id")
            records.append(d)

    if not records:
        log.info("no records found; exiting")
        return {"status":"empty"}

    df = pd.DataFrame.from_records(records)
    df["date"] = pd.to_datetime(df["updated_at"]).dt.date.astype(str)

    # write Parquet partitioned by route_id/date
    table = pa.Table.from_pandas(df, preserve_index=False)
    for route_val, grp in df.groupby("route_id"):
        for date_val, grp2 in grp.groupby("date"):
            t = pa.Table.from_pandas(grp2.drop(columns=["date"]), preserve_index=False)
            out_key = f"route_id={route_val or 'unknown'}/date={date_val}/part-{int(datetime.datetime.utcnow().timestamp())}.parquet"
            buf = io.BytesIO()
            pq.write_table(t, buf, compression="snappy")
            buf.seek(0)
            S3.put_object(Bucket=CURATED_BUCKET, Key=out_key, Body=buf.getvalue())
            log.info({"wrote": out_key, "rows": len(grp2)})

    return {"status":"ok","rows": len(df)}
