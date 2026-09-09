data "aws_ecr_repository" "pipeline-image-repo" {
  name = "${var.resource_prefix}-pipeline-repo"
}

data "aws_ecr_image" "pipeline-image-version" {
  repository_name = data.aws_ecr_repository.pipeline-image-repo.name
  image_tag       = "latest"
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
  image_uri = data.aws_ecr_image.pipeline-image-version.image_uri
  timeout = 120
}
