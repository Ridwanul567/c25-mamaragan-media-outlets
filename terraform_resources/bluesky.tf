resource "aws_ecr_repository" "bluesky-image-repo" {
  name                 = "${var.resource_prefix}-bluesky-repo"
  image_tag_mutability = "MUTABLE"
}

data "aws_iam_policy_document" "bluesky-role-trust-policy-doc" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = [
      "sts:AssumeRole"
    ]
  }
}

data "aws_iam_policy_document" "bluesky-role-permissions-policy-doc" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:eu-west-2:129033205317:*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Scan",
      "dynamodb:Query",
    ]
    resources = [
      aws_dynamodb_table.media_articles.arn,
      "${aws_dynamodb_table.media_articles.arn}/*"
    ]
  }
}

resource "aws_iam_role" "bluesky-role" {
  name               = "${var.resource_prefix}-bluesky-role"
  assume_role_policy = data.aws_iam_policy_document.bluesky-role-trust-policy-doc.json
}

resource "aws_iam_policy" "bluesky-role-permissions-policy" {
  name   = "${var.resource_prefix}-bluesky-permissions-policy"
  policy = data.aws_iam_policy_document.bluesky-role-permissions-policy-doc.json
}

resource "aws_iam_role_policy_attachment" "bluesky-role-policy-connection" {
  role       = aws_iam_role.bluesky-role.name
  policy_arn = aws_iam_policy.bluesky-role-permissions-policy.arn
}


resource "aws_lambda_function" "bluesky-lambda" {
  function_name = "${var.resource_prefix}-bluesky-lambda"
  role          = aws_iam_role.bluesky-role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.bluesky-image-repo.repository_url}:latest"
  timeout       = 120

  image_config {
    command = ["bluesky_app.handler"]
  }

  environment {
    variables = {
      AWS_REGION_OVERRIDE = var.aws_region
      HANDLE              = var.bluesky_handle
      PASSWORD            = var.bluesky_password
    }
  }
}


data "aws_iam_policy_document" "schedule-bluesky-trust-policy-doc" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
    actions = [
      "sts:AssumeRole"
    ]
  }
}

data "aws_iam_policy_document" "schedule-bluesky-permissions-policy-doc" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:eu-west-2:129033205317:*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [aws_lambda_function.bluesky-lambda.arn]
  }

  statement {
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = [aws_iam_role.bluesky-role.arn]
    condition {
      test     = "StringLike"
      variable = "iam:PassedToService"
      values   = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "schedule-bluesky-role" {
  name               = "${var.resource_prefix}-schedule-bluesky-role"
  assume_role_policy = data.aws_iam_policy_document.schedule-bluesky-trust-policy-doc.json
}

resource "aws_iam_policy" "schedule-bluesky-role-permissions-policy" {
  name   = "${var.resource_prefix}-schedule-bluesky-permissions-policy"
  policy = data.aws_iam_policy_document.schedule-bluesky-permissions-policy-doc.json
}

resource "aws_iam_role_policy_attachment" "schedule-bluesky-role-policy-connection" {
  role       = aws_iam_role.schedule-bluesky-role.name
  policy_arn = aws_iam_policy.schedule-bluesky-role-permissions-policy.arn
}

resource "aws_scheduler_schedule" "bluesky-schedule" {
  name                         = "${var.resource_prefix}-bluesky-schedule"
  group_name                   = "default"
  schedule_expression          = "cron(0 5-23/3 * * ? *)"
  schedule_expression_timezone = "Europe/London"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.bluesky-lambda.arn
    role_arn = aws_iam_role.schedule-bluesky-role.arn
  }
}

output "bluesky_ecr_repository_url" {
  value       = aws_ecr_repository.bluesky-image-repo.repository_url
  description = "The ECR Repository URL for pushing the bluesky lambda image"
}