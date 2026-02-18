# 🎯 Agentic Compliance Intelligence Platform

Transform regulatory changes into instant workforce impact analysis, risk assessment, and automated action execution.

## 🌟 Executive Overview

An AI-powered multi-agent orchestration system that:

- ✅ Interprets regulatory documents
- ✅ Identifies impacted workforce
- ✅ Calculates financial exposure
- ✅ Classifies compliance risk
- ✅ Assesses urgency
- ✅ Recommends actions
- ✅ Executes operational tasks
- ✅ Generates executive reports
- ✅ Logs audit documentation

**All in seconds.**

## 🏗️ Architecture

### Core Intelligence Agents

1. **Legal Intelligence Agent** - Parses regulations, extracts key data, resolves ambiguity
2. **Payroll Impact Agent** - Matches regulations to employees, calculates financial impact
3. **Risk Assessment Agent** - Assigns risk levels, calculates penalty exposure
4. **Urgency Classification Agent** - Evaluates timeline proximity and assigns urgency
5. **Report Generation Agent** - Produces executive-ready reports
6. **Action Execution Agent** - Executes real operational tasks via tool calling

### Execution & Action Tools

- Update payroll configurations
- Notify payroll teams
- Create compliance tickets
- Log audit entries
- Generate executive PDFs
- Tag impacted employees in HRIS
- Schedule compliance review meetings

### Intelligence Features

- **Financial Exposure Modeling** - Monthly, quarterly, annual projections
- **Risk Heatmap** - Country vs risk intensity visualization
- **Workforce Segmentation** - Impact by department, salary band, location
- **Simulation Mode** - What-if scenario analysis

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- MySQL 8.0+
- Groq API Key (or OpenAI/Ollama)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd compliance-platform
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Setup database**
```bash
mysql -u root -p < database_schema.sql
```

5. **Build RAG index** (first time only)
```bash
python -c "from app.rag.rag_engine import build_vector_store; build_vector_store()"
```

6. **Launch the application**
```bash
python app/main.py
```

The Gradio UI will open at `http://localhost:7860`

## 📋 Configuration

### Environment Variables (.env)

```env
# LLM Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.1-8b-instant

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=payroll_db
MYSQL_PORT=3306

# Feature Flags
NOTIFICATION_ENABLED=true
AUTO_EXECUTE_ACTIONS=false
```

### Supported LLM Providers

- **Groq** (recommended for speed): `LLM_PROVIDER=groq`
- **OpenAI**: `LLM_PROVIDER=openai`
- **Ollama** (local): `LLM_PROVIDER=ollama`

## 💡 Usage

### Step 1: Ask a Question

```
"Germany social contribution increased to 22% next month."
```

### Step 2: Instant Analysis

The system outputs:
- Country: Germany
- Impacted Employees: 342
- Annual Cost Increase: €4.3M
- Risk Level: High
- Urgency: Critical
- Confidence: 92%

### Step 3: Available Actions

- 📊 View Impacted Employees
- ⚠️ View Risk Breakdown
- 📈 View Impact Chart
- 🔬 Simulate Delayed Implementation
- 📥 Download Executive Report
- ⚡ Execute Recommended Actions

### Step 4: Action Execution

When you select "Execute Recommended Actions", the system:

1. ✅ Creates payroll update task
2. ✅ Notifies Germany payroll lead
3. ✅ Generates executive compliance memo
4. ✅ Logs regulatory change in audit DB
5. ✅ Creates compliance ticket
6. ✅ Schedules compliance review

## 🔬 Simulation Mode

Test different scenarios:

- **Rate Adjustment**: "What if rate increases to 20%?"
- **Implementation Delay**: "What if we delay 30 days?"
- **Partial Implementation**: "What if 50% implementation?"

The system recalculates:
- Financial impact difference
- Risk score adjustment
- Urgency shift
- Side-by-side comparison

## 📊 Features

### 1. Compliance Analysis Tab

- Executive summary
- Legal interpretation
- Key metrics (country, rate, effective date)
- Financial impact (annual/monthly)
- Risk & urgency assessment
- Detailed recommendations
- Action items with priorities
- Impact visualization charts
- Employee details table
- CSV export

### 2. Action Execution Tab

Automated execution of:
- Payroll configuration updates
- Team notifications
- Ticket creation
- Audit logging
- Report generation
- Meeting scheduling

### 3. Simulation Mode Tab

What-if analysis with:
- Adjustable scenario rate
- Implementation delay slider
- Partial implementation percentage
- Real-time cost comparison
- Risk score adjustment
- Visual scenario comparison

## 🗄️ Database Schema

The platform uses a comprehensive MySQL schema with tables for:

- Legislation tracking
- Employee master data
- Impact calculations
- Compliance audit trail
- Payroll configurations
- Notifications log
- Compliance tickets
- Audit log
- Generated reports
- Employee tags
- Scheduled meetings
- Risk assessments
- Urgency classifications
- Simulation scenarios

See `database_schema.sql` for complete schema.

## 🔧 Project Structure

```
compliance-platform/
├── app/
│   ├── agents/
│   │   ├── compliance_manager.py      # Main orchestration
│   │   ├── legal_agent.py             # Legal interpretation
│   │   ├── payroll_agent.py           # Payroll analysis
│   │   ├── risk_agent.py              # Risk assessment
│   │   ├── urgency_agent.py           # Urgency classification
│   │   ├── report_agent.py            # Report generation
│   │   └── action_execution_agent.py  # Action execution
│   ├── tools/
│   │   ├── impact_tool.py             # Impact calculations
│   │   ├── action_tools.py            # Execution tools
│   │   ├── simulation_tool.py         # Scenario simulation
│   │   └── notification_tool.py       # Notifications
│   ├── rag/
│   │   ├── rag_engine.py              # RAG implementation
│   │   └── ...
│   ├── db/
│   │   └── db.py                      # Database connection
│   ├── ui/
│   │   └── gradio_app.py              # Gradio interface
│   ├── config.py                      # Configuration
│   └── main.py                        # Entry point
├── data/
│   └── sample_legislation.pdf         # Sample regulations
├── database_schema.sql                # Database setup
├── requirements.txt                   # Python dependencies
├── .env                               # Environment config
└── README.md                          # This file
```

## 🔐 Security & Compliance

- All actions are logged in audit trail
- Database transactions ensure data integrity
- Configurable auto-execution thresholds
- Role-based action approval (configurable)
- Full traceability for regulatory audits

## 🎯 Key Benefits

1. **Speed**: Analysis in seconds vs hours/days
2. **Accuracy**: AI-powered interpretation with confidence scores
3. **Automation**: Reduce manual operational tasks
4. **Visibility**: Executive-ready reports and dashboards
5. **Traceability**: Complete audit trail
6. **Proactive**: Urgency detection and risk classification
7. **Flexible**: Simulation mode for scenario planning

## 🛠️ Troubleshooting

### Database Connection Issues
```bash
# Verify MySQL is running
mysql -u root -p

# Check database exists
SHOW DATABASES;
```

### RAG Index Issues
```bash
# Rebuild FAISS index
python -c "from app.rag.rag_engine import build_vector_store; build_vector_store()"
```

### LLM API Issues
```bash
# Test Groq connection
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"
```

## 📈 Future Enhancements

- [ ] Multi-country batch processing
- [ ] Real-time regulation monitoring
- [ ] Integration with major HRIS systems
- [ ] Advanced ML-based risk prediction
- [ ] Mobile app for executives
- [ ] Slack/Teams integration
- [ ] PDF report generation with charts
- [ ] Email notification system

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## 📧 Support

For support, email [your-email] or open an issue on GitHub.

---

**Built with ❤️ using OpenAI Agents SDK, Gradio, and MySQL**
