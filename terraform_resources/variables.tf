variable "aws_access_key" {
  description = "AWS Access Key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
}

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

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "c25-ecs-cluster"
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "dashboard_password" {
  type        = string
  description = "Password for Streamlit dashboard access"
  sensitive   = true
}

variable "bluesky_handle" {
  type        = string
  description = "Bluesky bot account handle"
  sensitive   = true
}

variable "bluesky_password" {
  type        = string
  description = "Bluesky bot account password"
  sensitive   = true
}