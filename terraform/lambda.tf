data "archive_file" "ingest_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/ingest_lambda"
  output_path = "${path.module}/../build/ingest.zip"
}

data "archive_file" "transform_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/transform_lambda"
  output_path = "${path.module}/../build/transform.zip"
}

resource "aws_lambda_function" "ingest" {
  function_name    = "${var.project_name}-ingest"
  role             = aws_iam_role.lambda_role.arn
  handler          = "app.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.ingest_zip.output_path
  source_code_hash = data.archive_file.ingest_zip.output_base64sha256
  timeout          = 20
  memory_size      = 256
  environment {
    variables = {
      RAW_BUCKET   = aws_s3_bucket.raw.bucket
      PROJECT_NAME = var.project_name
      MBTA_API_URL = var.mbta_api_key == null || var.mbta_api_key == "" ? "https://api-v3.mbta.com/vehicles" : "https://api-v3.mbta.com/vehicles?api_key=${var.mbta_api_key}"
    }
  }
}

resource "aws_lambda_function" "transform" {
  function_name    = "${var.project_name}-transform"
  role             = aws_iam_role.lambda_role.arn
  handler          = "app.handler"
  runtime          = "python3.11"
  filename         = data.archive_file.transform_zip.output_path
  source_code_hash = data.archive_file.transform_zip.output_base64sha256
  timeout          = 60
  memory_size      = 512

  # attach AWS SDK for pandas layer (Python 3.11, us-east-1, x86_64)
  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:22"
  ]

  environment {
    variables = {
      PROJECT_NAME   = var.project_name
      RAW_BUCKET     = aws_s3_bucket.raw.bucket
      CURATED_BUCKET = aws_s3_bucket.curated.bucket
    }
  }
}
