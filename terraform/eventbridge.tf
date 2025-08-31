resource "aws_cloudwatch_event_rule" "five_min" {
  name                = "${var.project_name}-five-min"
  schedule_expression = "rate(5 minutes)"
}
resource "aws_cloudwatch_event_target" "ingest_target" {
  rule      = aws_cloudwatch_event_rule.five_min.name
  target_id = "lambda"
  arn       = aws_lambda_function.ingest.arn
}
resource "aws_lambda_permission" "allow_events" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.five_min.arn
}
