# Project: Media Outlets

An end-to-end data pipeline that scrapes media articles, enriches them with sentiment analysis, stores them in DynamoDB, and automates distribution to BlueSky with a real-time Streamlit dashboard for monitoring.

## Team Roles

- **Project Manager:** Ridwan 
- **Architect:** Suvo
- **Quality Assurance:** Emily

---

## Project Overview

The Media Outlets project is a comprehensive media intelligence system with the following components:

1. **Media Scraper** – Collects articles from various media outlets
2. **Sentiment Enrichment** – Applies natural language processing to analyse article sentiment
3. **Data Storage** – Persists enriched articles in AWS DynamoDB
4. **BlueSky Automation** – Automatically posts articles and summaries to BlueSky
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

---


## Local Development Setup

### 1. Clone and Navigate to Project

```bash
git clone <repository-url>
cd c25-mamaragan-media-outlets
```

### 2. Create Virtual Environment for each directory (ETL_pipeline/dashboard/bluesky)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

For ETL_pipeline,

Add to your .env:

```bash
ACCESS_KEY_ID={your access key id}
SECRET_ACCESS_KEY={your secret access key}
AWS_REGION=eu-west-2
OPENAI_API_KEY={your openai api key}
```
### 3. Install Dependencies for each venv in each directory

Install dependencies:
```bash
pip install -r requirements.txt
```


### 4. Run Tests

Run the test suite to verify each directory's python scripts:

```bash
pytest -v
```

### 5. Run Streamlit Dashboard Locally

```bash
cd dashboard
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`

---

## Infrastructure & Deployment

The infrastructure is managed with Terraform and deployed to AWS.

### Prerequisites for Deployment

- Terraform CLI installed
- AWS account with appropriate permissions

### Configure Terraform Variables

Create `terraform.tfvars` in the `terraform_resources/` directory:

```hcl
aws_access_key = {your access key id}
aws_secret_key = {your secret key}
resource_prefix = "c25-media-outlets"
aws_region       = "eu-west-2"
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

### Infrastructure Components

- **Lambda Function** – Runs the ETL pipeline on a schedule
- **EventBridge Scheduler** – Triggers the Lambda function at configured intervals
- **DynamoDB Table** – Stores enriched article data
- **ECR Repository** – Container registry for Docker images
- **CloudWatch Logs** – Logging and monitoring

### Build and Push Docker Image to ECR

```bash
cd ETL_pipeline

# Build the Docker image for Linux/AMD64 architecture
docker buildx build --platform linux/amd64 --provenance=False -t pipeline:latest .

# Authenticate with AWS ECR
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-2.amazonaws.com

# Tag the image for ECR
docker tag pipeline:latest <account-id>.dkr.ecr.eu-west-2.amazonaws.com/<repo name>:latest

# Push to ECR
docker push <account-id>.dkr.ecr.eu-west-2.amazonaws.com/<repo-name>:latest
```

**Note:** Replace `<account-id>` with your AWS account ID.
          Replace `<repo-name>` with your repository name.

---

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
├── terraform_resources/       # Infrastructure as Code
│   ├── pipeline.tf            # Lambda and EventBridge configuration
│   ├── database.tf            # DynamoDB configuration
│   ├── main.tf                # AWS provider setup
│   ├── variables.tf           # Terraform variables
│   └── terraform.tfvars       # Terraform variable values
├── dashboard/                 # Streamlit application
├── bluesky_app.py             # BlueSky automation
├── code_review/               # Code review reports
├── articles.csv               # Sample article data
├── enriched_articles.csv      # Enriched article results
├── README.md                  # This file
└── requirements.txt           # Root-level dependencies
```

---

## Contributing

- Follow PEP 8 for Python code style
- Write unit tests for new features
- Run the full test suite before submitting changes
- Update documentation as required

---

## Support

For questions or issues, please contact the project team or review the code review reports in the `code_review/` directory.