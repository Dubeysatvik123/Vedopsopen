<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VedOps - AI-Powered DevSecOps Platform</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #e2e8f0;
            line-height: 1.6;
            overflow-x: hidden;
        }

        .hero {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            position: relative;
            background: radial-gradient(ellipse at center, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
        }

        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
            animation: float 20s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(180deg); }
        }

        .logo {
            width: 120px;
            height: 120px;
            background: linear-gradient(45deg, #3b82f6, #8b5cf6, #06b6d4);
            border-radius: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            margin-bottom: 2rem;
            animation: pulse 3s ease-in-out infinite;
            box-shadow: 0 0 50px rgba(59, 130, 246, 0.3);
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); box-shadow: 0 0 50px rgba(59, 130, 246, 0.3); }
            50% { transform: scale(1.05); box-shadow: 0 0 80px rgba(59, 130, 246, 0.5); }
        }

        .hero h1 {
            font-size: clamp(3rem, 8vw, 6rem);
            font-weight: 800;
            background: linear-gradient(45deg, #3b82f6, #8b5cf6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
            animation: slideUp 1s ease-out;
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .hero .subtitle {
            font-size: 1.5rem;
            color: #94a3b8;
            margin-bottom: 3rem;
            animation: slideUp 1s ease-out 0.2s both;
        }

        .badges {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 3rem;
            animation: slideUp 1s ease-out 0.4s both;
        }

        .badge {
            background: rgba(59, 130, 246, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(59, 130, 246, 0.2);
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .badge:hover {
            background: rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.4);
            transform: translateY(-2px);
        }

        .cta-buttons {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            justify-content: center;
            animation: slideUp 1s ease-out 0.6s both;
        }

        .btn {
            padding: 1rem 2rem;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: linear-gradient(45deg, #3b82f6, #8b5cf6);
            color: white;
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(59, 130, 246, 0.4);
        }

        .btn-secondary {
            background: transparent;
            color: #e2e8f0;
            border: 2px solid rgba(226, 232, 240, 0.2);
        }

        .btn-secondary:hover {
            background: rgba(226, 232, 240, 0.1);
            border-color: rgba(226, 232, 240, 0.4);
            transform: translateY(-3px);
        }

        .section {
            padding: 5rem 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }

        .section h2 {
            font-size: 2.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 3rem;
            background: linear-gradient(45deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 4rem;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 2rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
        }

        .feature-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(59, 130, 246, 0.3);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
        }

        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
        }

        .feature-card h3 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #f1f5f9;
        }

        .workflow {
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            padding: 3rem;
            margin: 4rem 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .agents-flow {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 1rem;
            margin: 3rem 0;
        }

        .agent {
            background: linear-gradient(45deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
            backdrop-filter: blur(10px);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            min-width: 150px;
            transition: all 0.3s ease;
            position: relative;
        }

        .agent:hover {
            transform: translateY(-5px);
            background: linear-gradient(45deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
            box-shadow: 0 15px 30px rgba(59, 130, 246, 0.2);
        }

        .agent::after {
            content: '→';
            position: absolute;
            right: -20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.5rem;
            color: #64748b;
        }

        .agent:last-child::after {
            display: none;
        }

        .agent-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            display: block;
        }

        .quick-start {
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .code-block {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-family: 'JetBrains Mono', monospace;
            overflow-x: auto;
        }

        .floating-elements {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        }

        .floating-circle {
            position: absolute;
            border-radius: 50%;
            background: linear-gradient(45deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
            animation: floatRandom 15s ease-in-out infinite;
        }

        .circle-1 {
            width: 80px;
            height: 80px;
            top: 20%;
            left: 10%;
            animation-delay: 0s;
        }

        .circle-2 {
            width: 60px;
            height: 60px;
            top: 60%;
            right: 15%;
            animation-delay: 3s;
        }

        .circle-3 {
            width: 40px;
            height: 40px;
            top: 80%;
            left: 20%;
            animation-delay: 6s;
        }

        @keyframes floatRandom {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            25% { transform: translate(30px, -30px) rotate(90deg); }
            50% { transform: translate(-20px, 20px) rotate(180deg); }
            75% { transform: translate(40px, 10px) rotate(270deg); }
        }

        @media (max-width: 768px) {
            .hero h1 {
                font-size: 3rem;
            }
            
            .hero .subtitle {
                font-size: 1.2rem;
            }
            
            .cta-buttons {
                flex-direction: column;
                align-items: center;
            }
            
            .agents-flow {
                flex-direction: column;
                align-items: center;
            }
            
            .agent::after {
                content: '↓';
                right: 50%;
                top: 100%;
                transform: translateX(50%);
            }
        }

        .fade-in {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease-out;
        }

        .fade-in.visible {
            opacity: 1;
            transform: translateY(0);
        }
    </style>
</head>
<body>
    <div class="floating-elements">
        <div class="floating-circle circle-1"></div>
        <div class="floating-circle circle-2"></div>
        <div class="floating-circle circle-3"></div>
    </div>

    <section class="hero">
        <div class="logo">🚀</div>
        <h1>VedOps</h1>
        <p class="subtitle">AI-Powered DevSecOps Platform</p>
        
        <div class="badges">
            <span class="badge">🐍 Python 3.9+</span>
            <span class="badge">⚡ Streamlit</span>
            <span class="badge">🐳 Docker Ready</span>
            <span class="badge">☸️ Kubernetes</span>
            <span class="badge">📄 MIT License</span>
        </div>

        <div class="cta-buttons">
            <a href="#quick-start" class="btn btn-primary">
                🚀 Get Started
            </a>
            <a href="#features" class="btn btn-secondary">
                📖 Learn More
            </a>
        </div>
    </section>

    <section class="section fade-in" id="why">
        <h2>🌟 Why VedOps?</h2>
        <div style="text-align: center; font-size: 1.2rem; color: #94a3b8; max-width: 800px; margin: 0 auto;">
            <p>Software delivery pipelines are <strong>slow, manual, and error-prone</strong>. Security scans are often skipped due to time pressure, and DevOps engineers juggle multiple tools for code analysis, builds, security, deployment, and monitoring.</p>
            <br>
            <p><strong>VedOps changes that.</strong></p>
            <p>It's an <strong>autonomous, AI-powered DevSecOps platform</strong> that <strong>orchestrates your entire SDLC</strong> — from code analysis to deployment — using <strong>specialized AI agents</strong>.</p>
        </div>
    </section>

    <section class="section fade-in" id="features">
        <h2>✨ Key Features</h2>
        <div class="features-grid">
            <div class="feature-card">
                <span class="feature-icon">🤖</span>
                <h3>8 Specialized AI Agents</h3>
                <p>Each dedicated to a stage in the DevSecOps pipeline with autonomous execution and decision-making capabilities.</p>
            </div>
            <div class="feature-card">
                <span class="feature-icon">⚡</span>
                <h3>End-to-End Automation</h3>
                <p>From repo analysis → build → security scan → deployment → testing → monitoring, fully automated.</p>
            </div>
            <div class="feature-card">
                <span class="feature-icon">🔒</span>
                <h3>Enterprise Security</h3>
                <p>Automated SAST/DAST scanning with intelligent vulnerability auto-fixing capabilities.</p>
            </div>
            <div class="feature-card">
                <span class="feature-icon">🏠</span>
                <h3>Local-First Architecture</h3>
                <p>Fully functional without internet. Supports Ollama and local LLMs for complete privacy.</p>
            </div>
            <div class="feature-card">
                <span class="feature-icon">🌐</span>
                <h3>Multi-LLM Support</h3>
                <p>OpenAI, Anthropic, Google Gemini, Azure OpenAI, and custom API integration.</p>
            </div>
            <div class="feature-card">
                <span class="feature-icon">📊</span>
                <h3>Smart Observability</h3>
                <p>Prometheus/Grafana dashboards with AI-driven scaling and cost optimization.</p>
            </div>
        </div>
    </section>

    <section class="section fade-in" id="workflow">
        <h2>🏗️ Workflow</h2>
        <div class="workflow">
            <h3 style="text-align: center; margin-bottom: 2rem; color: #f1f5f9;">Architecture Overview</h3>
            
            <div class="agents-flow">
                <div class="agent">
                    <span class="agent-icon">🌊</span>
                    <strong>Varuna</strong>
                    <p>Repository & dependency analysis</p>
                </div>
                <div class="agent">
                    <span class="agent-icon">🔥</span>
                    <strong>Agni</strong>
                    <p>Build & Dockerize the app</p>
                </div>
                <div class="agent">
                    <span class="agent-icon">⚔️</span>
                    <strong>Yama</strong>
                    <p>Security scans & compliance</p>
                </div>
                <div class="agent">
                    <span class="agent-icon">💨</span>
                    <strong>Vayu</strong>
                    <p>Deploy to Kubernetes/Docker</p>
                </div>
                <div class="agent">
                    <span class="agent-icon">🛡️</span>
                    <strong>Hanuman</strong>
                    <p>Testing & resilience checks</p>
                </div>
                <div class="agent">
                    <span class="agent-icon">🧠</span>
                    <strong>Krishna</strong>
                    <p>Governance & audit logging</p>
                </div>
                <div class="agent">
                    <span class="agent-icon">📊</span>
                    <strong>Observer</strong>
                    <p>Monitoring & alerts</p>
                </div>
                <div class="agent">
                    <span class="agent-icon">⚡</span>
                    <strong>Optimizer</strong>
                    <p>Resource & cost tuning</p>
                </div>
            </div>
        </div>
    </section>

    <section class="section fade-in" id="quick-start">
        <h2>🚀 Quick Start</h2>
        <div class="quick-start">
            <h3 style="margin-bottom: 1rem; color: #f1f5f9;">Prerequisites</h3>
            <ul style="margin-bottom: 2rem; color: #94a3b8;">
                <li>Python 3.9+</li>
                <li>Docker (optional but recommended)</li>
                <li>Kubernetes cluster (optional)</li>
                <li>Git</li>
            </ul>

            <h3 style="margin-bottom: 1rem; color: #f1f5f9;">Installation</h3>
            <div class="code-block">
<pre style="color: #e2e8f0; margin: 0;">git clone https://github.com/Dubeysatvik123/vedops.git
cd vedops
pip install -r requirements.txt
python -c "from utils.database import DatabaseManager; DatabaseManager().init_database()"
streamlit run app.py</pre>
            </div>
            
            <p style="text-align: center; margin-top: 1rem;">
                Visit: <strong style="color: #3b82f6;">http://localhost:8501</strong>
            </p>
        </div>
    </section>

    <section class="section fade-in">
        <h2>🤝 Contributing</h2>
        <div style="text-align: center; font-size: 1.2rem; color: #94a3b8; max-width: 600px; margin: 0 auto;">
            <p>We welcome contributions! Join our community and help make DevSecOps more accessible with AI.</p>
            <div style="margin-top: 2rem;">
                <a href="#" class="btn btn-primary">📋 Contributing Guide</a>
                <a href="#" class="btn btn-secondary">🐛 Report Issues</a>
            </div>
        </div>
    </section>

    <footer style="text-align: center; padding: 3rem; color: #64748b; border-top: 1px solid rgba(255, 255, 255, 0.1);">
        <p>MIT License – Made with ❤️ by the VedOps Community</p>
    </footer>

    <script>
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.fade-in').forEach(el => {
            observer.observe(el);
        });

        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Add some interactive hover effects
        document.querySelectorAll('.feature-card, .agent').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-10px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    </script>
</body>
</html>
