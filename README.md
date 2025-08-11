# VedOps - AI-Powered DevSecOps Platform

<div align="center">

![VedOps Logo](https://img.shields.io/badge/VedOps-AI%20DevSecOps-blue?style=for-the-badge&logo=kubernetes)

**Local-First, Autonomous AI-Powered DevSecOps Platform**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Compatible-green.svg)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 🚀 Overview

VedOps is a comprehensive, local-first AI-powered DevSecOps platform that automates the entire software delivery lifecycle through specialized AI agents. Built with Streamlit and powered by configurable LLM providers, VedOps provides enterprise-grade automation for code analysis, building, security scanning, deployment, testing, and monitoring.

### ✨ Key Features

- **🤖 8 Specialized AI Agents** - Autonomous agents handling different aspects of DevSecOps
- **🔧 Configurable LLM Support** - OpenAI, Anthropic, Google, Ollama, Azure OpenAI, and custom APIs
- **🏠 Local-First Architecture** - Works completely offline with optional cloud integrations
- **🔒 Enterprise Security** - Comprehensive SAST/DAST scanning with automated vulnerability patching
- **📊 Real-Time Monitoring** - Prometheus/Grafana integration with intelligent alerting
- **🐳 Container-Ready** - Docker and Kubernetes deployment with auto-scaling
- **⚡ Performance Optimized** - Parallel execution, caching, and resource optimization
- **🛡️ Production-Grade Resilience** - Circuit breakers, retry logic, and health monitoring

## 🏗️ Architecture

VedOps operates through 8 specialized AI agents working in orchestrated harmony:

### Core Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| **Varuna** 🌊 | Code Intake & Analysis | Repository analysis, dependency detection, code quality assessment |
| **Agni** 🔥 | Build & Dockerization | Automated builds, containerization, multi-stage Docker optimization |
| **Yama** ⚔️ | Security & Compliance | SAST/DAST scanning, vulnerability assessment, compliance validation |
| **Vayu** 💨 | Orchestration & Deployment | Kubernetes deployment, infrastructure provisioning, scaling |
| **Hanuman** 🛡️ | Testing & Resilience | Automated testing, performance validation, chaos engineering |
| **Krishna** 🧠 | Governance & Decision | Pipeline orchestration, decision making, audit logging |

### Advanced Agents

| Agent | Role | Responsibilities |
|-------|------|-----------------|
| **Observability Agent** 📊 | Monitoring & Alerting | Real-time monitoring, anomaly detection, intelligent alerting |
| **Optimization Agent** ⚡ | Performance & Scaling | Resource optimization, cost management, auto-scaling |

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker (optional, for containerization)
- Kubernetes cluster (optional, for deployment)
- Git

### Installation

1. **Clone the repository**
\`\`\`bash
git clone https://github.com/Dubeysatvik123/vedops.git
cd vedops
\`\`\`

2. **Install dependencies**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. **Initialize the database**
\`\`\`bash
python -c "from utils.database import DatabaseManager; DatabaseManager().init_database()"
\`\`\`

4. **Start VedOps**
\`\`\`bash
streamlit run app.py
\`\`\`

5. **Access the platform**
Open your browser to `http://localhost:8501`

### Docker Deployment

\`\`\`bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t vedops .
docker run -p 8501:8501 vedops
\`\`\`

### Kubernetes Deployment

\`\`\`bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n vedops
\`\`\`

## ⚙️ Configuration

### LLM Provider Setup

VedOps supports multiple LLM providers. Configure your preferred provider in the web interface:

#### OpenAI
\`\`\`yaml
provider: openai
api_key: sk-your-openai-key
model: gpt-4
base_url: https://api.openai.com/v1  # optional
\`\`\`

#### Anthropic Claude
\`\`\`yaml
provider: anthropic
api_key: sk-ant-your-claude-key
model: claude-3-sonnet-20240229
\`\`\`

#### Google Gemini
\`\`\`yaml
provider: google
api_key: your-google-api-key
model: gemini-pro
\`\`\`

#### Local Ollama
\`\`\`yaml
provider: ollama
base_url: http://localhost:11434
model: llama2
\`\`\`

#### Azure OpenAI
\`\`\`yaml
provider: azure_openai
api_key: your-azure-key
endpoint: https://your-resource.openai.azure.com/
deployment_name: gpt-4
api_version: 2023-12-01-preview
\`\`\`

#### Custom API
\`\`\`yaml
provider: custom
api_key: your-custom-key
base_url: https://your-custom-api.com/v1
model: your-model
\`\`\`

### Environment Variables

Create a `.env` file in the project root:

\`\`\`env
# Database
DATABASE_URL=sqlite:///vedops.db

# Security
SECRET_KEY=your-secret-key-here

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Cloud Providers (Optional)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AZURE_SUBSCRIPTION_ID=your-azure-subscription
GCP_PROJECT_ID=your-gcp-project
\`\`\`

## 📖 Usage Guide

### 1. Project Onboarding

1. **Upload Code**: Drag and drop a ZIP file or connect to a Git repository
2. **Configure Settings**: Set deployment preferences and resource requirements
3. **Select LLM Provider**: Choose and configure your preferred AI model
4. **Start Pipeline**: Click "Start DevSecOps Pipeline" to begin automation

### 2. Pipeline Execution

The pipeline executes through these stages:

\`\`\`mermaid
graph LR
    A[Code Upload]  B[Varuna Analysis]
    B  C[Agni Build]
    C  D[Yama Security]
    D  E[Vayu Deploy]
    E  F[Hanuman Test]
    F  G[Krishna Govern]
    G  H[Monitor & Optimize]
\`\`\`

### 3. Monitoring & Observability

- **Real-time Dashboard**: View pipeline progress and system metrics
- **Security Reports**: Detailed vulnerability assessments and remediation
- **Performance Metrics**: Resource usage, response times, and optimization suggestions
- **Audit Logs**: Complete trail of all pipeline activities and decisions

### 4. Advanced Features

#### Parallel Execution
Enable parallel agent execution for compatible tasks:
```python
# In pipeline configuration
parallel_execution = True
max_parallel_agents = 4
# Vedopsopen
