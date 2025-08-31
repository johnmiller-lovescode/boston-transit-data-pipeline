variable "project_name" {
  type    = string
  default = "boston-transit"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "raw_bucket_name" {
  type    = string
  default = null
}

variable "curated_bucket_name" {
  type    = string
  default = null
}

# NEW: MBTA API key (kept out of state output)
variable "mbta_api_key" {
  type      = string
  sensitive = true
  default   = null
}
