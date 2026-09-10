resource "aws_ecr_repository" "pipeline-image-repo" {
  name = "${var.resource_prefix}-pipeline-repo"
  image_tag_mutability = "MUTABLE"
}

data "aws_iam_policy_document" "pipeline-role-trust-policy-doc" {
    statement {
      effect = "Allow"
      principals {
        type = "Service"
        identifiers = [ "lambda.amazonaws.com" ]
      }
      actions = [
        "sts:AssumeRole"
      ]
    }
}

data "aws_iam_policy_document" "pipeline-role-permissions-policy-doc" {
    statement {
      effect = "Allow"
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
      ]
      resources = [ "arn:aws:logs:eu-west-2:129033205317:*" ]
    }

    statement {
      effect = "Allow"
      actions = [
        "dynamodb:*"
      ]
      resources = [ "*" ]
    }
}

resource "aws_iam_role" "pipeline-role" {
    name = "${var.resource_prefix}-pipeline-role"
    assume_role_policy = data.aws_iam_policy_document.pipeline-role-trust-policy-doc.json
}

resource "aws_iam_policy" "pipeline-role-permissions-policy" {
    name = "${var.resource_prefix}-pipeline-permissions-policy"
    policy = data.aws_iam_policy_document.pipeline-role-permissions-policy-doc.json
}

resource "aws_iam_role_policy_attachment" "pipeline-role-policy-connection" {
  role = aws_iam_role.pipeline-role.name
  policy_arn = aws_iam_policy.pipeline-role-permissions-policy.arn
}


resource "aws_lambda_function" "pipeline-lambda" {
  function_name = "${var.resource_prefix}-pipeline-lambda"
  role = aws_iam_role.pipeline-role.arn
  package_type = "Image"
  image_uri = "${aws_ecr_repository.pipeline-image-repo.repository_url}:latest"
  timeout = 120
}


data "aws_iam_policy_document" "schedule-pipeline-trust-policy-doc" {
    statement {
      effect = "Allow"
      principals {
        type = "Service"
        identifiers = [ "scheduler.amazonaws.com" ]
      }
      actions = [
        "sts:AssumeRole"
      ]
    }
}

data "aws_iam_policy_document" "schedule-pipeline-permissions-policy-doc" {
    statement {
      effect = "Allow"
      actions = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
      ]
      resources = [ "arn:aws:logs:eu-west-2:129033205317:*" ]
    }

    statement {
      effect = "Allow"
      actions = [
        "lambda:InvokeFunction"
      ]
      resources = [ aws_lambda_function.pipeline-lambda.arn ]
    }

    statement {
        effect   = "Allow"
        actions   = ["iam:PassRole"]
        resources = [aws_iam_role.pipeline-role.arn]
        condition {
        test     = "StringLike"
        variable = "iam:PassedToService"
        values   = ["lambda.amazonaws.com"]
        }
    }
}

resource "aws_iam_role" "schedule-pipeline-role" {
    name = "${var.resource_prefix}-schedule-pipeline-role"
    assume_role_policy = data.aws_iam_policy_document.schedule-pipeline-trust-policy-doc.json
}

resource "aws_iam_policy" "schedule-pipeline-role-permissions-policy" {
    name = "${var.resource_prefix}-schedule-pipeline-permissions-policy"
    policy = data.aws_iam_policy_document.schedule-pipeline-permissions-policy-doc.json
}

resource "aws_iam_role_policy_attachment" "schedule-pipeline-role-policy-connection" {
  role = aws_iam_role.schedule-pipeline-role.name
  policy_arn = aws_iam_policy.schedule-pipeline-role-permissions-policy.arn
}

resource "aws_scheduler_schedule" "pipeline-schedule" {
  name                         = "${var.resource_prefix}-pipeline-schedule"
  group_name = "default"
  schedule_expression          = "cron(0 */3 * * ? *)"
  schedule_expression_timezone = "Europe/London"
  
  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.pipeline-lambda.arn
    role_arn = aws_iam_role.schedule-pipeline-role.arn
  }
}
