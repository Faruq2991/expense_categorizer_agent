# DevOps Strategy for Expense Categorizer

**Author:** Senior DevOps Engineer, Meta
**Audience:** Junior DevOps/Software Engineers

---

## 1. Introduction

Team,

Welcome to the DevOps guide for the Expense Categorizer project. The goal of this document is to provide a clear, step-by-step roadmap for building, testing, and deploying this application in a consistent, automated, and reliable manner.

Our philosophy is simple: **Automate everything that can be automated.** This reduces manual errors, ensures our environments are identical from local development to production, and allows us to deploy with confidence.

We will cover:
-   **Project Structure:** Understanding how our repository is organized.
-   **Local Development:** Ensuring a consistent setup for every engineer.
-   **Containerization with Docker:** Packaging our application for portability.
-   **Continuous Integration & Deployment (CI/CD):** Automating our testing and deployment pipeline.
-   **Infrastructure as Code (IaC):** Managing our cloud resources programmatically.
-   **Deployment to Google Cloud Platform (GCP):** Our initial cloud deployment target.
-   **Future State: Kubernetes:** A look ahead at scaling our deployment.

Let's get started.

---

## 2. Project Structure Overview

Before we build, let's understand what we have. The project is organized as follows:

```
/
├── app/                  # Core application logic (FastAPI, agent, tools)
├── data/                 # SQLite database, schema, and seed data
├── tests/                # Unit and integration tests
├── .github/workflows/    # (To be created) CI/CD pipeline definitions
├── terraform/            # (To be created) Infrastructure as Code files
├── Dockerfile            # (To be created) Instructions to build our container
├── .dockerignore         # (To be created) Files to exclude from the container
├── requirements.txt      # Python dependencies
└── streamlit_app.py      # Frontend application
```

This structure separates our application code (`app`), data (`data`), tests (`tests`), and infrastructure definitions (`terraform`, `Dockerfile`). This separation is crucial for a clean and maintainable DevOps process.

---

## 3. Local Development Environment

A consistent local setup is the foundation of a solid DevOps practice. Every engineer must follow these steps to avoid "it works on my machine" issues.

### 3.1. Virtual Environment

We will use a Python virtual environment to isolate our project dependencies.

1.  **Create the virtual environment:**
    ```bash
    python3 -m venv venv
    ```
2.  **Activate it:**
    *   **macOS/Linux:** `source venv/bin/activate`
    *   **Windows:** `.\venv\Scripts\activate`
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3.2. Environment Variables

The application requires an `OPENAI_API_KEY`. For local development, create a `.env` file in the project root (this is in our `.gitignore` and should **never** be committed).

```
# .env
OPENAI_API_KEY="your-openai-api-key"
```

Our application will load this automatically.

---

## 4. Containerization with Docker

Docker allows us to package our application and its dependencies into a lightweight, portable container. This ensures that our application runs the same way everywhere.

### 4.1. The `Dockerfile`

Create a file named `Dockerfile` in the project root:

```dockerfile
# Use an official lightweight Python image.
FROM python:3.11-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the dependencies file and install them.
# This is done in a separate step to leverage Docker layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container.
COPY . .

# Expose the port the app runs on.
EXPOSE 8000

# Define the command to run the application.
# We use uvicorn to run our FastAPI app.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2. The `.dockerignore` File

To keep our Docker image small and clean, create a `.dockerignore` file in the project root:

```
# Ignore virtual environment, IDE files, and local data
venv
.idea
.vscode
__pycache__
*.pyc
.pytest_cache
.env
data/keywords.db
```

### 4.3. Building and Running Locally

1.  **Build the image:**
    ```bash
    docker build -t expense-categorizer .
    ```
2.  **Run the container:**
    ```bash
    docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY expense-categorizer
    ```

You should now be able to access the API at `http://localhost:8000`.

---

## 5. CI/CD Pipeline with GitHub Actions

We will use GitHub Actions to automate our testing and deployment process.

Create the following file at `.github/workflows/main.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: pytest

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: '${{ secrets.GCP_SA_KEY }}'

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1

      - name: Configure Docker
        run: gcloud auth configure-docker us-central1-docker.pkg.dev

      - name: Build and Push Docker Image
        run: |
          docker build -t us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/expense-categorizer/app:${{ github.sha }} .
          docker push us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/expense-categorizer/app:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: '${{ secrets.GCP_SA_KEY }}'

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: expense-categorizer
          region: us-central1
          image: us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/expense-categorizer/app:${{ github.sha }}
          env_vars: |
            OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}
```

**Action Items:**
1.  Create a service account in GCP with "Artifact Registry Writer" and "Cloud Run Admin" roles.
2.  Create a JSON key for this service account.
3.  Add the following secrets to your GitHub repository settings:
    *   `GCP_PROJECT_ID`: Your Google Cloud project ID.
    *   `GCP_SA_KEY`: The content of the JSON service account key file.
    *   `OPENAI_API_KEY`: Your OpenAI API key.

---

## 6. Infrastructure as Code (IaC) with Terraform

We will use Terraform to define and manage our cloud infrastructure. This ensures our infrastructure is version-controlled and reproducible.

Create a `terraform` directory with a `main.tf` file:

```terraform
# terraform/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.51.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = "us-central1"
}

variable "gcp_project_id" {
  description = "The GCP project ID."
}

resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
}

resource "google_project_service" "artifactregistry_api" {
  service = "artifactregistry.googleapis.com"
}

resource "google_artifact_registry_repository" "repo" {
  location      = "us-central1"
  repository_id = "expense-categorizer"
  format        = "DOCKER"
  depends_on = [
    google_project_service.artifactregistry_api
  ]
}
```

**How to use:**
1.  Install Terraform.
2.  Navigate to the `terraform` directory.
3.  Run `terraform init`.
4.  Run `terraform plan -var="gcp_project_id=your-gcp-project-id"`.
5.  Run `terraform apply -var="gcp_project_id=your-gcp-project-id"`.

This will set up the necessary APIs and the Artifact Registry repository for our CI/CD pipeline.

---

## 7. Deployment to Google Cloud Platform (GCP)

Our CI/CD pipeline will handle the deployment to GCP Cloud Run. Cloud Run is a serverless platform that will automatically scale our container up and down based on traffic, even to zero.

The `deploy` job in our `main.yml` file takes care of this. Once a change is pushed to `main`, and the tests and build succeed, it will automatically deploy the new version of our application to Cloud Run.

---

## 8. Future State: Kubernetes Deployment

As our application grows, we may need more control over our infrastructure. Migrating to Google Kubernetes Engine (GKE) would be the next logical step.

### Migration Steps:

1.  **Provision a GKE Cluster:** We would add a `google_container_cluster` resource to our `terraform/main.tf` file to create a GKE cluster.
2.  **Create Kubernetes Manifests:** We would create Kubernetes YAML files (e.g., `deployment.yaml`, `service.yaml`) to define how our application should run in the cluster.
    *   `deployment.yaml`: Defines the desired state for our application pods (replicas, container image, etc.).
    *   `service.yaml`: Exposes our application to the internet via a LoadBalancer.
3.  **Update CI/CD Pipeline:** We would modify the `deploy` job in our `main.yml` to:
    *   Authenticate to the GKE cluster.
    *   Use `kubectl apply -f <manifests-directory>` to deploy our application to the cluster.

This move would give us more fine-grained control over scaling, networking, and resource management, but also comes with increased complexity. We will cross that bridge when we get there.

---

This document should serve as your guide for all DevOps-related activities on this project. If you have any questions, don't hesitate to ask. Let's build something great, the right way.
