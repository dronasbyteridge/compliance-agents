-- ============================================
-- Agentic Compliance Intelligence Platform
-- Complete Database Schema
-- ============================================

-- Legislation tracking
CREATE TABLE IF NOT EXISTS legislation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    regulation_type VARCHAR(100),
    previous_rate DECIMAL(10, 4),
    new_rate DECIMAL(10, 4),
    effective_date DATE,
    category VARCHAR(100),
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_country (country),
    INDEX idx_effective_date (effective_date)
);

-- Employee master data
CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(50) PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    annual_salary DECIMAL(15, 2),
    pension_rate DECIMAL(10, 4),
    status VARCHAR(20) DEFAULT 'Active',
    department VARCHAR(100),
    employment_type VARCHAR(50),
    hire_date DATE,
    INDEX idx_country_status (country, status)
);

-- Impact calculation results
CREATE TABLE IF NOT EXISTS impact_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    legislation_id INT NOT NULL,
    impacted_employees INT,
    total_annual_cost_increase DECIMAL(15, 2),
    average_cost_per_employee DECIMAL(15, 2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    INDEX idx_legislation (legislation_id)
);

-- Detailed employee impact
CREATE TABLE IF NOT EXISTS employee_impact_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    legislation_id INT NOT NULL,
    employee_id VARCHAR(50) NOT NULL,
    old_rate DECIMAL(10, 4),
    new_rate DECIMAL(10, 4),
    annual_salary DECIMAL(15, 2),
    annual_cost_increase DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    INDEX idx_legislation (legislation_id),
    INDEX idx_employee (employee_id)
);

-- Compliance audit trail
CREATE TABLE IF NOT EXISTS compliance_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    legislation_id INT NOT NULL,
    action_taken TEXT,
    risk_level VARCHAR(20),
    escalated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    INDEX idx_legislation (legislation_id),
    INDEX idx_risk_level (risk_level)
);

-- Payroll configuration updates
CREATE TABLE IF NOT EXISTS payroll_config_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    regulation_type VARCHAR(100),
    new_rate DECIMAL(10, 4),
    effective_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    INDEX idx_country (country),
    INDEX idx_status (status)
);

-- Notifications log
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_type VARCHAR(50),
    country VARCHAR(100),
    subject VARCHAR(255),
    message TEXT,
    urgency VARCHAR(20),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'sent',
    INDEX idx_country (country),
    INDEX idx_urgency (urgency)
);

-- Compliance tickets
CREATE TABLE IF NOT EXISTS compliance_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    country VARCHAR(100),
    priority VARCHAR(20),
    due_date DATE,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_country (country),
    INDEX idx_priority (priority),
    INDEX idx_status (status)
);

-- Audit log for all actions
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    legislation_id INT,
    action_type VARCHAR(100),
    action_details TEXT,
    performed_by VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    INDEX idx_legislation (legislation_id),
    INDEX idx_action_type (action_type),
    INDEX idx_timestamp (timestamp)
);

-- Generated reports
CREATE TABLE IF NOT EXISTS generated_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    legislation_id INT,
    report_type VARCHAR(50),
    report_data JSON,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(255),
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    INDEX idx_legislation (legislation_id),
    INDEX idx_report_type (report_type)
);

-- Employee tags for tracking
CREATE TABLE IF NOT EXISTS employee_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    tag VARCHAR(100),
    legislation_id INT,
    tagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    INDEX idx_employee (employee_id),
    INDEX idx_tag (tag)
);

-- Scheduled meetings
CREATE TABLE IF NOT EXISTS scheduled_meetings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    meeting_date DATETIME,
    attendees TEXT,
    agenda TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'scheduled',
    INDEX idx_meeting_date (meeting_date),
    INDEX idx_status (status)
);

-- Risk assessment history
CREATE TABLE IF NOT EXISTS risk_assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    legislation_id INT NOT NULL,
    risk_level VARCHAR(20),
    risk_score DECIMAL(5, 2),
    financial_penalty_exposure DECIMAL(15, 2),
    audit_probability DECIMAL(5, 2),
    enforcement_likelihood VARCHAR(20),
    reasoning TEXT,
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    INDEX idx_legislation (legislation_id),
    INDEX idx_risk_level (risk_level)
);

-- Urgency classifications
CREATE TABLE IF NOT EXISTS urgency_classifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    legislation_id INT NOT NULL,
    urgency_level VARCHAR(20),
    days_until_effective INT,
    recommended_timeline VARCHAR(255),
    reasoning TEXT,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    INDEX idx_legislation (legislation_id),
    INDEX idx_urgency_level (urgency_level)
);

-- Simulation scenarios
CREATE TABLE IF NOT EXISTS simulation_scenarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    legislation_id INT,
    scenario_name VARCHAR(255),
    scenario_rate DECIMAL(10, 4),
    implementation_delay_days INT,
    partial_implementation_pct DECIMAL(5, 2),
    base_annual_cost DECIMAL(15, 2),
    scenario_annual_cost DECIMAL(15, 2),
    cost_delta DECIMAL(15, 2),
    risk_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (legislation_id) REFERENCES legislation(id),
    INDEX idx_legislation (legislation_id)
);

-- ============================================
-- Sample Data for Testing
-- ============================================

-- Sample employees
INSERT INTO employees (employee_id, country, annual_salary, pension_rate, status, department, employment_type, hire_date) VALUES
('EMP001', 'Germany', 75000.00, 0.18, 'Active', 'Engineering', 'Full-time', '2020-01-15'),
('EMP002', 'Germany', 82000.00, 0.18, 'Active', 'Sales', 'Full-time', '2019-06-20'),
('EMP003', 'Germany', 68000.00, 0.18, 'Active', 'Marketing', 'Full-time', '2021-03-10'),
('EMP004', 'Germany', 95000.00, 0.18, 'Active', 'Engineering', 'Full-time', '2018-11-05'),
('EMP005', 'Germany', 71000.00, 0.18, 'Active', 'HR', 'Full-time', '2020-08-22'),
('EMP006', 'France', 65000.00, 0.15, 'Active', 'Engineering', 'Full-time', '2019-02-14'),
('EMP007', 'France', 72000.00, 0.15, 'Active', 'Finance', 'Full-time', '2020-05-18'),
('EMP008', 'UK', 60000.00, 0.12, 'Active', 'Operations', 'Full-time', '2021-01-09'),
('EMP009', 'UK', 78000.00, 0.12, 'Active', 'Engineering', 'Full-time', '2019-09-30'),
('EMP010', 'Germany', 88000.00, 0.18, 'Active', 'Product', 'Full-time', '2020-12-01');

-- Sample legislation
INSERT INTO legislation (country, regulation_type, previous_rate, new_rate, effective_date, category, summary) VALUES
('Germany', 'social_contribution', 0.18, 0.22, '2024-04-01', 'Social Security', 'Germany increases social contribution rate from 18% to 22% effective April 2024'),
('France', 'pension_contribution', 0.15, 0.17, '2024-06-01', 'Pension', 'France pension contribution increase to 17%'),
('UK', 'national_insurance', 0.12, 0.135, '2024-05-01', 'National Insurance', 'UK National Insurance rate adjustment');
