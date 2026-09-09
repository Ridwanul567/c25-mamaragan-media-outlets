resource "aws_dynamodb_table" "media_articles" {
  name         = "${var.resource_prefix}-articles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "article_id"

  attribute {
    name = "article_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.media_articles.name
  description = "The deployed DynamoDB table name"
}