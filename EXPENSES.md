# Project Cost Analysis: Media Outlets

## Executive Summary

The following document outlines the estimated operational costs for the Media Outlets Platform on AWS infrastructure. The platform comprises three main components: an article collection pipeline, a distributed database layer, and a public-facing dashboard. Monthly operational expenses are estimated at **USD $20.93**, with an annualised cost of **USD $251.16**.

---

## 1. Article Collection Pipeline

### 1.1 Elastic Container Registry (ECR)

| Component | Specification |
|-----------|---------------|
| Monthly Storage | 350 MB |
| Monthly Cost | USD $0.0342 |

The ECR repository stores the containerised application image for the data collection pipeline.

### 1.2 Lambda Function

**Operational Parameters:**
- Invocation Frequency: 7 requests per day (scheduled every 3 hours, 5:00 AM – 11:00 PM)
- Average Request Duration: 4.2 seconds
- Memory Allocation: 128 MB
- Ephemeral Storage: 512 MB

**Cost Calculation:**
- Monthly Compute: 1,117.83 GB-seconds
- Monthly Invocations: 213 requests
- **Monthly Cost: USD $0.00** (within AWS Lambda free tier limits)

*Note: AWS Lambda free tier includes 1 million requests and 400,000 GB-seconds of compute time monthly.*

### 1.3 EventBridge Scheduler

**Status:** No charge

EventBridge handles the scheduled triggering of the pipeline function. Monthly event volume (approximately 6,490 events) remains well within the free tier allocation of 14 million monthly invocations.

---

## 2. Database Layer

### 2.1 DynamoDB Table

**Configuration:**
- Capacity Mode: On-Demand
- Table Class: Standard
- Estimated Storage: 1 GB (supporting approximately 1 million articles at 1 KB average item size)
- Consistency Model: Eventually Consistent

**Operational Workload:**
- Write Operations: 7 per day (scheduled synchronously with pipeline execution, 5:00 AM – 11:00 PM)
- Read Operations: 100 external clients performing 10 read operations daily
- **Monthly Cost: USD $0.00** (low volume remains within on-demand free tier)

**Scaling Scenario:**
Should the platform scale to support 5,000 concurrent dashboard users with an average of 100 read operations per user daily, the estimated additional cost would be approximately **USD $1.00 per month**.

---

## 3. BlueSky Integration Module

### 3.1 Lambda Function

**Operational Parameters:**
- Invocation Frequency: 7 requests per day (scheduled every 3 hours, 5:05 AM – 11:05 PM)
- Average Request Duration: 5.0 seconds
- Memory Allocation: 128 MB
- Ephemeral Storage: 512 MB

**Cost Calculation:**
- Monthly Compute: 1,117.83 GB-seconds
- Monthly Invocations: 213 requests
- **Monthly Cost: USD $0.00** (within AWS Lambda free tier limits)

### 3.2 EventBridge Scheduler

**Status:** No charge

EventBridge manages function scheduling with negligible event volume relative to service limits.

---

## 4. Dashboard Application

### 4.1 Elastic Container Registry (ECR)

| Component | Specification |
|-----------|---------------|
| Monthly Storage | 200 MB |
| Monthly Cost | USD $0.0195 |

The ECR repository stores the containerised dashboard application image.

### 4.2 Elastic Container Service (Fargate)

**Configuration:**
- Deployment Model: Fargate serverless containers
- Task Count: 1 persistent task
- Availability: Continuous operation (24/7)
- **Monthly Cost: USD $20.73**

---

## Cost Summary

| Component | Monthly Cost (USD) |
|-----------|-------------------|
| Pipeline ECR | 0.0342 |
| Pipeline Lambda | 0.0000 |
| Pipeline Scheduler | 0.0000 |
| DynamoDB | 0.0000 |
| BlueSky Lambda | 0.0000 |
| BlueSky Scheduler | 0.0000 |
| Dashboard ECR | 0.0195 |
| Dashboard Fargate | 20.73 |
| **Total Monthly** | **$20.93** |
| **Total Annual** | **$251.16** |

---

## Notes

- All costs are calculated based on current AWS pricing (as of the date of this document).
- The platform currently operates within AWS free tier limits for serverless compute resources (Lambda, EventBridge, DynamoDB).
- Primary recurring expense is the Fargate container for continuous dashboard availability.
- Scaling scenarios have been evaluated in relevant sections for operational planning.