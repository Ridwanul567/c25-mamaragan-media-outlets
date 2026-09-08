variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-2"
}

variable "resource_prefix" {
  description = "Naming prefix for all project resources"
  type        = string
  default     = "c25-mamaragan-media-outlets"
}