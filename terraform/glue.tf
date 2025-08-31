resource "aws_glue_catalog_database" "transit" {
  name = "${var.project_name}_db"
}

resource "aws_glue_catalog_table" "vehicles" {
  name          = "vehicles"
  database_name = aws_glue_catalog_database.transit.name
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.curated.bucket}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "id"
      type = "string"
    }
    columns {
      name = "bearing"
      type = "double"
    }
    columns {
      name = "current_status"
      type = "string"
    }
    columns {
      name = "label"
      type = "string"
    }
    columns {
      name = "latitude"
      type = "double"
    }
    columns {
      name = "longitude"
      type = "double"
    }
    columns {
      name = "speed"
      type = "double"
    }
    columns {
      name = "updated_at"
      type = "string"
    }
    # IMPORTANT: do NOT include route_id here because it's a partition key
  }

  partition_keys {
    name = "route_id"
    type = "string"
  }
  partition_keys {
    name = "date"
    type = "string"
  }
}
