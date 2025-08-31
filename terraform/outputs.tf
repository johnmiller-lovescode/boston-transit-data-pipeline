output "raw_bucket" { value = aws_s3_bucket.raw.bucket }
output "curated_bucket" { value = aws_s3_bucket.curated.bucket }
output "ingest_lambda_name" { value = aws_lambda_function.ingest.function_name }
output "transform_lambda_name" { value = aws_lambda_function.transform.function_name }
