VedOps - AI-Powered DevSecOps Platform



Local-First, Autonomous AI-Powered DevSecOps Platform



🚀 Overview
VedOps is a cutting-edge, local-first, AI-powered DevSecOps platform designed to automate and streamline the entire software delivery lifecycle. Powered by Streamlit and driven by configurable Large Language Models (LLMs), VedOps leverages 8 specialized AI agents to handle code analysis, builds, security scanning, deployment, testing, monitoring, and optimization. Whether you're running it offline or integrating with cloud services, VedOps delivers enterprise-grade automation with a focus on security, scalability, and performance.
✨ Key Features

🤖 8 Specialized AI Agents: Autonomous agents orchestrate every stage of the DevSecOps pipeline.
🔧 Flexible LLM Integration: Supports OpenAI, Anthropic, Google Gemini, Ollama, Azure OpenAI, and custom APIs.
🏠 Local-First Design: Fully functional offline with optional cloud integrations for maximum flexibility.
🔒 Enterprise-Grade Security: Comprehensive SAST/DAST scanning and automated vulnerability remediation.
📊 Real-Time Observability: Prometheus and Grafana integration for intelligent monitoring and alerting.
🐳 Containerized Deployment: Docker and Kubernetes-ready with auto-scaling capabilities.
⚡ Performance Optimized: Parallel execution, caching, and resource-efficient workflows.
🛡️ Production Resilience: Built-in circuit breakers, retry logic, and health monitoring for reliability.

🏗️ Architecture
VedOps is powered by a modular architecture with 8 specialized AI agents that work in orchestrated harmony to deliver a seamless DevSecOps experience.
Core Agents



Agent
Role
Responsibilities



Varuna 🌊
Code Intake & Analysis
Repository scanning, dependency analysis, code quality checks


Agni 🔥
Build & Containerization
Automated builds, multi-stage Docker images, artifact management


Yama ⚔️
Security & Compliance
SAST/DAST scanning, vulnerability detection, compliance enforcement


Vayu 💨
Orchestration & Deployment
Kubernetes orchestration, infrastructure provisioning, auto-scaling


Hanuman 🛡️
Testing & Resilience
Automated unit/integration testing, performance validation, chaos engineering


Krishna 🧠
Governance & Decision
Pipeline orchestration, decision automation, audit trails


Advanced Agents



Agent
Role
Responsibilities



Observability Agent 📊
Monitoring & Alerting
Real-time metrics, anomaly detection, proactive alerting


Optimization Agent ⚡
Performance & Scaling
Resource optimization, cost management, dynamic scaling


🛠️ Getting Started
Prerequisites

Python: 3.9 or higher
Docker: Required for containerized deployments (optional)
Kubernetes: For orchestration and scaling (optional)
Git: For cloning the repository
LLM API Keys: For your chosen provider (OpenAI, Anthropic, etc.)
System Requirements: 4GB RAM (8GB recommended), 2 CPU cores, 10GB disk space

Installation

Clone the Repository:
git clone https://github.com/Dubeysatvik123/vedops.git
cd vedops


Install Python Dependencies:
pip install -r requirements.txt


Initialize the Database:
python -c "from utils.database import DatabaseManager; DatabaseManager().init_database()"


Launch VedOps:
streamlit run app.py


Access the Platform:Open your browser to http://localhost:8501.


Using the Official Docker Image
To use the official VedOps Docker image from Docker Hub, follow these steps:

Pull the Official Image:
docker pull dubeysatvik123/vedops:latest


Run the Container:
docker run -p 8501:8501 --env-file .env dubeysatvik123/vedops:latest


Access the Platform:Open your browser to http://localhost:8501.


Note: Ensure you have a .env file configured with the necessary environment variables (see Environment Variables below). You can specify a specific version of the image by replacing :latest with a version tag, e.g., :v1.0.0.
Docker Deployment (Build from Source)
If you prefer to build the Docker image from source:
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t vedops .
docker run -p 8501:8501 --env-file .env vedops

Kubernetes Deployment
Deploy VedOps on a Kubernetes cluster for scalable, production-grade setups:
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n vedops

To use the official Docker image in Kubernetes, update the k8s/deployment.yaml to reference dubeysatvik123/vedops:latest.
⚙️ Configuration
LLM Provider Setup
Configure your preferred LLM provider via the VedOps web interface or in config.yaml:
OpenAI
provider: openai
api_key: sk-your-openai-key
model: gpt-4o
base_url: https://api.openai.com/v1

Anthropic Claude
provider: anthropic
api_key: sk-ant-your-claude-key
model: claude-3.5-sonnet

Google Gemini
provider: google
api_key: your-google-api-key
model: gemini-1.5-pro

Local Ollama
provider: ollama
base_url: http://localhost:11434
model: llama3

Azure OpenAI
provider: azure_openai
api_key: your-azure-key
endpoint: https://your-resource.openai.azure.com/
deployment_name: gpt-4o
api_version: 2023-12-01-preview

Custom API
provider: custom
api_key: your-custom-key
base_url: https://your-custom-api.com/v1
model: your-model

Environment Variables
Create a .env file in the project root to configure database, security, and monitoring settings:
# Database
DATABASE_URL=sqlite:///vedops.db

# Security
SECRET_KEY=your-secure-random-key

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

Advanced Configuration

Parallel Execution: Enable parallel agent execution for faster pipelines:# In pipeline configuration
parallel_execution = True
max_parallel_agents = 4


Caching: Enable caching for repetitive tasks to improve performance:cache_enabled: true
cache_ttl: 3600  # Cache timeout in seconds



📖 Usage Guide
1. Onboarding a Project

Upload Code: Drag and drop a ZIP file or connect a Git repository via the web interface.
Configure Pipeline: Specify deployment targets, resource limits, and LLM provider.
Run Pipeline: Click "Start DevSecOps Pipeline" to initiate the automated workflow.

2. Pipeline Workflow
The VedOps pipeline follows a structured flow, executed by the AI agents:
graph LR
    A[Code Upload] --> B[Varuna: Code Analysis]
    B --> C[Agni: Build & Containerization]
    C --> D[Yama: Security Scanning]
    D --> E[Vayu: Deployment]
    E --> F[Hanuman: Testing]
    F --> G[Krishna: Governance]
    G --> H[Observability & Optimization]

3. Monitoring & Observability

Real-Time Dashboard: Monitor pipeline progress, system metrics, and agent activity.
Security Reports: View detailed vulnerability scans and automated remediation steps.
Performance Insights: Track resource usage, latency, and optimization recommendations.
Audit Logs: Access a complete history of pipeline actions and decisions.

4. Extensibility

Custom Agents: Extend VedOps by adding custom AI agents for specific tasks.
API Integrations: Connect with external tools via REST APIs or webhooks.
Plugin Support: Integrate third-party tools for CI/CD, monitoring, or security.

🛠️ Troubleshooting

LLM Connection Issues: Verify API keys and endpoint URLs in config.yaml.
Database Errors: Ensure DATABASE_URL is correctly set and the database is initialized.
Docker Issues: Check Docker service status and ensure port 8501 is available.
Kubernetes Failures: Verify manifests in the k8s/ directory and cluster connectivity.

For detailed logs, enable debug mode:
streamlit run app.py --logger.level=debug

🤝 Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a feature branch: git checkout -b feature/your-feature.
Commit changes: git commit -m "Add your feature".
Push to the branch: git push origin feature/your-feature.
Open a pull request.

Please follow the Code of Conduct and review the Contributing Guidelines.
📜 License
VedOps is licensed under the MIT License.
📬 Contact
For support or inquiries, reach out via:

GitHub Issues: Dubeysatvik123/vedops
Email: support@vedops.dev
Slack: Join our community Slack (request an invite via email)
