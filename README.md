# Project: Media Outlets

A media intelligence platform that collects articles and enriches them with sentiment analysis. It identifies trending figures and posts alerts to BlueSky when positive sentiment thresholds are met. Daily topic summaries are published alongside a real-time Streamlit dashboard for analytics.

## Team Roles

- **Project Manager:** Ridwan
- **Architect:** Suvo
- **Quality Assurance:** Emily

---

## Project Overview

The Media Outlets project is a comprehensive media intelligence system comprising the following components:

1. **Media Scraper** – Collects articles from various media outlets
2. **Sentiment Enrichment** – Uses OpenAI to analyse article sentiment via natural language processing
3. **Data Storage** – Persists enriched articles in AWS DynamoDB
4. **BlueSky Automation** – Scans recent articles, identifies trending figures with positive sentiment, and posts alerts and daily summaries to BlueSky
5. **Streamlit Dashboard** – Real-time visualisation and monitoring of processed articles

### Architecture Flow

```
Articles Scraped → Enrichment Pipeline → DynamoDB Storage → BlueSky Distribution
                                                ↓
                                Streamlit Dashboard (Monitoring)
```

---

## Prerequisites

- **Python 3.9+**
- **Docker** 
- **Terraform CLI** 
- **Git**
- **OpenAI API Key**
---


## Local Development Setup

### 1. Clone and Navigate to Project

```bash
git clone <repository-url>
cd c25-mamaragan-media-outlets
```

### 2. Create Virtual Environment for Each Directory

Create and activate a virtual environment in each directory (`ETL_pipeline/`, `dashboard/`, `bluesky/`):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

For the ETL pipeline, create a `.env` file with:

```bash
ACCESS_KEY_ID={your access key id}
SECRET_ACCESS_KEY={your secret access key}
AWS_REGION=eu-west-2
OPENAI_API_KEY={your openai api key}
```

For the BlueSky module, create a `.env` file with:

```bash
HANDLE={your handle name}
PASSWORD={your handle password}
```

For the dashboard module, create a `.env` file with:

```bash
DASHBOARD_PASSWORD={your dashboard password}
```


### 3. Install Dependencies

In each directory, install the required Python dependencies:
```bash
pip install -r requirements.txt
```


### 4. Run Tests

Run the test suite to verify the Python scripts:

```bash
pytest -v
```

### 5. Run the Streamlit Dashboard Locally

```bash
cd dashboard
streamlit run app.py
```

The dashboard is available at `http://localhost:8501`

---

## Infrastructure and Deployment

Infrastructure is managed with Terraform and deployed to AWS.

### Deployment Prerequisites

- Terraform CLI installed
- AWS account with appropriate permissions

### Configure Terraform Variables

Create `terraform.tfvars` in the `terraform_resources/` directory:

```hcl
aws_access_key   = "{your access key id}"
aws_secret_key   = "{your secret key}"
resource_prefix  = "c25-media-outlets"
aws_region       = "eu-west-2"
vpc_id           = "{your vpc id}"
dashboard_password = "{your streamlit dashboard password}"
bluesky_handle   = "{your bluesky bot handle}"
bluesky_password = "{your bluesky bot password}"
```

### Deploy Infrastructure

```bash
cd terraform_resources

# Initialise Terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply
```

**Note:** Lambda functions may not be created until their Docker images are pushed to ECR. Perform the steps below to push the images, then run `terraform apply` again.

### Infrastructure Components

- **Pipeline Lambda Function** – Runs the ETL pipeline on a schedule
- **BlueSky Lambda Function** – Scans recent articles for sentiment and keyword frequency; surfaces trending figures and posts alerts when mention thresholds are reached with positive sentiment; publishes daily topic summaries
- **EventBridge Scheduler** – Triggers Lambda functions at configured intervals
- **DynamoDB Table** – Stores enriched article data
- **ECR Repositories** – Container registries for Docker images (Pipeline, Dashboard, and BlueSky)
- **ECS Fargate** – Hosts the Streamlit dashboard for continuous availability
- **CloudWatch Logs** – Logging and monitoring for all Lambda functions

### Build and Push Docker Images to ECR

#### Pipeline Image

The Pipeline Lambda function collects articles from media outlets, enriches them with sentiment analysis, and stores the results in DynamoDB. The function runs on an EventBridge Schedule (every 3 hours, 5:00 AM – 11:00 PM UK time).

```bash
cd ETL_pipeline

# Build the Docker image for Linux/AMD64 architecture
docker buildx build --platform linux/amd64 --provenance=False -t pipeline:latest .

# Authenticate with AWS ECR
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-2.amazonaws.com

# Tag the image for ECR
docker tag pipeline:latest <account-id>.dkr.ecr.eu-west-2.amazonaws.com/<pipeline-repo-name>:latest

# Push to ECR
docker push <account-id>.dkr.ecr.eu-west-2.amazonaws.com/<pipeline-repo-name>:latest
```

#### BlueSky Image

The BlueSky Lambda function scans articles from the past 3 hours, analyses sentiment and keyword frequency, and identifies trending figures. It automatically posts to BlueSky when a figure reaches a mention threshold with strongly positive sentiment, and publishes a daily summary of top entertainment topics. The function runs on an Eventbridge Schedule (every 3 hours, 5:10 AM – 11:10 PM UK time) and reads enriched articles from DynamoDB.

```bash
cd bluesky

# Build the Docker image for Linux/AMD64 architecture
docker buildx build --platform linux/amd64 --provenance=False -t bluesky:latest .

# Authenticate with AWS ECR
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-2.amazonaws.com

# Tag the image for ECR
docker tag bluesky:latest <account-id>.dkr.ecr.eu-west-2.amazonaws.com/<bluesky-repo-name>:latest

# Push to ECR
docker push <account-id>.dkr.ecr.eu-west-2.amazonaws.com/<bluesky-repo-name>:latest
```

**Note:** Replace `<account-id>` with your AWS account ID and `<pipeline-repo-name>` and `<bluesky-repo-name>` with the respective ECR repository names from the Terraform output.

---

Once deployed, access the dashboard at the ECS task IP address on port 8501.

## File Structure

```
c25-mamaragan-media-outlets/
├── ETL_pipeline/              # Core data processing
│   ├── collect_data.py        # Article scraping logic
│   ├── enrich_data.py         # Sentiment enrichment
│   ├── write_data.py          # Database storage
│   ├── pipeline.py            # Orchestration
│   ├── test_*.py              # Unit tests
│   ├── Dockerfile             # Container configuration
│   └── requirements.txt        # Python dependencies
├── bluesky/                   # BlueSky automation Lambda
│   ├── bluesky_app.py         # Lambda handler; sentiment analysis and threshold posting
│   ├── media_articles.py      # Article retrieval and analysis
│   ├── test_*.py              # Unit tests
│   ├── Dockerfile             # Container configuration
│   └── requirements.txt        # Python dependencies
├── terraform_resources/       # Infrastructure as Code
│   ├── pipeline.tf            # Lambda and EventBridge for ETL
│   ├── bluesky.tf             # Lambda and EventBridge for BlueSky
│   ├── dashboard.tf           # ECS Fargate dashboard
│   ├── database.tf            # DynamoDB configuration
│   ├── main.tf                # AWS provider setup
│   ├── variables.tf           # Terraform variables
│   └── terraform.tfvars       # Terraform variable values
├── dashboard/                 # Streamlit application
│   ├── app.py                 # Main application entry point
│   ├── src/                   # Application modules
│   ├── Dockerfile             # Container configuration
│   └── requirements.txt        # Python dependencies
├── code_review/               # Code review reports
├── README.md                  # This file
├── EXPENSES.md                # Cost analysis
├── articles.csv               # Sample article data
└── enriched_articles.csv      # Enriched article results
```

---

## Contributing

- Follow PEP 8 style guidelines for Python code
- Write unit tests for all new features
- Run the full test suite before submitting changes
- Update documentation to reflect changes

---

## Support

For questions or issues, contact the project team or review the code review reports in the `code_review/` directory.