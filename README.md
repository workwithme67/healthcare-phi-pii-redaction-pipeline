# SOAR Incident Containment Engine

## Overview

The SOAR (Security Orchestration, Automation, and Response) Incident Containment Engine is a cybersecurity automation platform designed to streamline incident response operations. The system ingests security alerts, enriches them using threat intelligence APIs, calculates risk scores, and executes automated response actions through predefined playbooks.

## Features

* Alert Ingestion and Management
* Threat Intelligence Enrichment
* Risk Scoring Engine
* Automated Response Playbooks
* Incident Timeline Tracking
* Role-Based Access Control (RBAC)
* Interactive Dashboard
* Incident Reporting

## Tech Stack

### Backend

* Python
* FastAPI

### Database

* SQLite

### Frontend

* React.js / HTML, CSS, JavaScript

### APIs

* VirusTotal API
* AbuseIPDB API
* IPInfo API

## Project Workflow

1. Receive security alert
2. Extract indicators (IP, domain, hash)
3. Enrich data using threat intelligence APIs
4. Calculate risk score
5. Execute response playbook
6. Display results on dashboard

## Installation

```bash
git clone <repository-url>
cd soar-incident-containment-engine
pip install -r requirements.txt
uvicorn main:app --reload
```

## API Endpoints

### Create Alert

```http
POST /alerts
```

### Get Alerts

```http
GET /alerts
```

### Risk Assessment

```http
GET /risk-score/{ip}
```

## Future Enhancements

* Real-time alert monitoring
* MITRE ATT&CK mapping
* Email notifications
* PDF incident reports
* Cloud deployment

## Author

Jigyasu Labana

## Internship

Cyber Security Internship Project – Infotact Solutions
