# Engineering Certification Enablement Guide (Synthetic)

> Synthetic demonstration document. Not real organisational policy. All module names, hours, and pass rates are fabricated for demonstration purposes.

---

## Role-to-Certification Mapping

| Role | Primary Certification | Advancement Path |
|---|---|---|
| Cloud Engineer | AZ-204: Developing Solutions for Azure | AZ-305: Azure Solutions Architect |
| DevOps Engineer | AZ-400: DevOps Engineer Expert | — |
| Data Engineer | DP-203: Data Engineering on Azure | — |
| Security Engineer | SC-200: Security Operations Analyst | — |

All certifications are available on Microsoft Learn. Use the Microsoft Learn MCP tool to fetch current exam objectives, module lists, and practice assessments for each certification.

---

## AZ-204 — Developing Solutions for Azure

**Recommended study hours:** 20  
**Pass threshold:** 75% practice score + 18h minimum study  
**Microsoft Learn path:** "Develop solutions for Microsoft Azure"

### Skill Areas and Topic Breakdown

**API Development (35% of exam weight)**
- Build and implement APIs using Azure API Management (APIM)
- Create RESTful services with Azure App Service Web Apps
- Configure authentication using OAuth 2.0 and Azure Active Directory (Entra ID)
- Implement Azure API Management policies: rate limiting, caching, transformation
- Use Azure Functions HTTP triggers as lightweight API endpoints
- Secure APIs with managed identities and role-based access control (RBAC)
- Key Microsoft Learn modules: "Build and run a web application with the MEAN stack on an Azure Linux virtual machine", "Expose hybrid services securely with Azure Relay"

**Azure Functions (30% of exam weight)**
- Create serverless functions with timer, blob, queue, and HTTP triggers
- Implement durable functions: orchestrator, activity, entity patterns
- Configure function bindings for Azure Storage, Cosmos DB, Service Bus
- Manage function app scaling: consumption plan vs. premium plan
- Implement retry policies and error handling in serverless workflows
- Deploy functions using Azure DevOps and GitHub Actions pipelines
- Key Microsoft Learn modules: "Create serverless logic with Azure Functions", "Chain Azure Functions together using input and output bindings"

**Storage (35% of exam weight)**
- Work with Azure Blob Storage: containers, lifecycle policies, SAS tokens
- Implement Azure Table Storage and Azure Queue Storage patterns
- Use Cosmos DB: partition key design, consistency levels, change feed
- Configure Azure Cache for Redis: cache-aside pattern, eviction policies
- Implement content delivery with Azure CDN
- Design storage tiers: hot, cool, archive — and automate tiering with lifecycle policies
- Key Microsoft Learn modules: "Store data in Azure", "Choose a data storage approach in Azure"

### Recommended Study Strategy for AZ-204
1. **Weeks 1–2:** API Development — build a sample REST API with APIM and Entra ID auth
2. **Week 3:** Azure Functions — implement a durable function workflow end-to-end
3. **Week 4+:** Storage — practise Cosmos DB partition design and blob lifecycle policies
4. Complete at least 3 Microsoft Learn practice assessments before booking
5. Use the Microsoft Learn sandbox environments to get hands-on time without incurring costs

---

## AZ-305 — Azure Solutions Architect Expert

**Recommended study hours:** 30  
**Pass threshold:** 75% practice score + 27h minimum study  
**Prerequisite:** AZ-204 or equivalent hands-on Azure development experience  
**Microsoft Learn path:** "Microsoft Azure Architect Design"

### Skill Areas and Topic Breakdown

**Architecture and Design (40% of exam weight)**
- Design for high availability: availability zones, availability sets, regional pairs
- Implement Azure Well-Architected Framework: reliability, security, cost, performance, operations
- Design multi-region architectures with Azure Traffic Manager and Front Door
- Plan disaster recovery: RTO/RPO targets, Azure Site Recovery, geo-redundant storage
- Design landing zones using the Cloud Adoption Framework (CAF)
- Key Microsoft Learn modules: "Architect great solutions in Azure", "Design for availability and recoverability in Azure"

**Governance (30% of exam weight)**
- Implement Azure Policy, Blueprints, and Management Groups
- Design identity solutions with Azure Active Directory (Entra ID): hybrid identity, PIM
- Apply cost management strategies: budgets, cost allocation, reserved instances
- Design tagging taxonomies and resource naming conventions
- Configure Azure Monitor, Log Analytics, and diagnostic settings at scale
- Key Microsoft Learn modules: "Control and organize Azure resources with Azure Resource Manager", "Manage resources in Azure"

**Networking (30% of exam weight)**
- Design hub-and-spoke virtual network topologies
- Configure VPN Gateway and ExpressRoute for hybrid connectivity
- Implement Azure Firewall, NSGs, and Application Gateway with WAF
- Design private endpoints and service endpoints for PaaS security
- Plan DNS resolution across hybrid environments
- Key Microsoft Learn modules: "Architect network infrastructure in Azure", "Connect your on-premises network to Azure"

### Recommended Study Strategy for AZ-305
1. Revisit AZ-204 concepts — architect design builds heavily on developer knowledge
2. **Weeks 1–2:** Architecture patterns — build a multi-region reference architecture
3. **Weeks 3–4:** Governance — deploy a policy-compliant landing zone in a sandbox
4. **Weeks 5–6+:** Networking — configure hub-spoke topology end-to-end
5. Use the Microsoft Learn case study format to practise architect-level scenario questions

---

## AZ-400 — DevOps Engineer Expert

**Recommended study hours:** 25  
**Pass threshold:** 75% practice score + 22h minimum study  
**Microsoft Learn path:** "DevOps Engineer"

### Skill Areas and Topic Breakdown

**CI/CD (40% of exam weight)**
- Design and implement Azure Pipelines: YAML pipelines, multi-stage deployments
- Configure GitHub Actions workflows: secrets management, environments, approvals
- Implement deployment strategies: blue-green, canary, rolling, feature flags
- Set up artifact management with Azure Artifacts: npm, NuGet, Maven feeds
- Configure release gates: automated approval, rollback triggers
- Integrate static code analysis and security scanning (SAST/DAST) into pipelines
- Key Microsoft Learn modules: "Build applications with Azure DevOps", "Deploy applications with Azure DevOps"

**Monitoring (30% of exam weight)**
- Configure Azure Monitor alerts, action groups, and dashboards
- Implement Application Insights: distributed tracing, custom metrics, availability tests
- Set up Log Analytics workspaces and KQL queries for operational insights
- Design SLIs, SLOs, and error budgets aligned to business requirements
- Implement chaos engineering principles with Azure Chaos Studio
- Key Microsoft Learn modules: "Monitor and report on Azure resources", "Capture Web Application Logs with App Service Diagnostics"

**GitHub Actions (30% of exam weight)**
- Implement reusable workflows and composite actions
- Configure matrix builds for cross-platform testing
- Manage environment secrets and OIDC-based Azure authentication (no long-lived secrets)
- Set up branch protection rules and required status checks
- Use GitHub Advanced Security: code scanning, secret scanning, Dependabot
- Key Microsoft Learn modules: "Automate your workflow with GitHub Actions", "Manage repository changes by using pull requests on GitHub"

### Recommended Study Strategy for AZ-400
1. **Weeks 1–2:** CI/CD — migrate a sample app to a multi-stage Azure Pipelines or GitHub Actions workflow
2. **Weeks 3–4:** Monitoring — instrument an app with Application Insights end-to-end
3. **Week 5+:** GitHub Actions — implement OIDC auth to Azure and secure multi-environment deployments

---

## DP-203 — Data Engineering on Azure

**Recommended study hours:** 22  
**Pass threshold:** 75% practice score + 20h minimum study  
**Microsoft Learn path:** "Azure Data Engineer Associate"

### Skill Areas and Topic Breakdown

**Data Pipelines (40% of exam weight)**
- Design and implement Azure Data Factory (ADF) pipelines: linked services, datasets, activities
- Build end-to-end ELT/ETL flows with mapping data flows in ADF
- Implement Azure Synapse Pipelines for large-scale data movement
- Configure incremental loads and watermark patterns for CDC
- Set up trigger-based and tumbling window scheduling
- Integrate with Azure Event Hubs and Azure IoT Hub as pipeline sources
- Key Microsoft Learn modules: "Introduction to Azure Data Factory", "Petabyte-scale ingestion with Azure Data Factory"

**Storage (30% of exam weight)**
- Design Azure Data Lake Storage Gen2 (ADLS) hierarchical namespace and ACLs
- Implement Delta Lake format for ACID transactions in data lakes
- Configure Azure Synapse Analytics dedicated SQL pools: distributions, indexing strategies
- Choose between row-store and column-store indexes for analytical workloads
- Manage Parquet, ORC, and Avro file formats for performance
- Implement data partitioning strategies for lake and warehouse
- Key Microsoft Learn modules: "Introduction to Azure Data Lake storage", "Store data with Azure Blob storage"

**Stream Processing (30% of exam weight)**
- Implement Azure Stream Analytics jobs: windowing functions, reference data joins
- Use Azure Event Hubs for high-throughput event ingestion at scale
- Process streams with Apache Spark Structured Streaming in Azure Databricks / Synapse
- Design lambda and kappa architectures for real-time and batch processing
- Implement late-arriving data handling and watermarking strategies
- Key Microsoft Learn modules: "Enable reliable messaging for Big Data applications using Azure Event Hubs", "Implement a stream processing solution with Azure Stream Analytics"

---

## SC-200 — Security Operations Analyst

**Recommended study hours:** 20  
**Pass threshold:** 75% practice score + 18h minimum study  
**Microsoft Learn path:** "Security Operations Analyst Associate"

### Skill Areas and Topic Breakdown

**Threat Detection (35% of exam weight)**
- Investigate incidents using Microsoft Sentinel workbooks and hunting queries
- Write KQL detection rules for anomaly detection and behavioural analytics
- Configure UEBA (User and Entity Behaviour Analytics) in Sentinel
- Triage alerts using the Sentinel incident queue and MITRE ATT&CK mapping
- Integrate threat intelligence feeds (TAXII, STIX) into Sentinel
- Key Microsoft Learn modules: "Introduction to Microsoft Sentinel", "Create detections and perform investigations using Microsoft Sentinel"

**Microsoft Sentinel (35% of exam weight)**
- Deploy Sentinel workspace: data connectors, analytics rules, automation rules
- Build playbooks using Azure Logic Apps for automated incident response (SOAR)
- Configure data retention, archiving, and cost optimisation for large workspaces
- Implement Sentinel SIEM and SOAR patterns for SOC workflows
- Use Sentinel workbooks for security dashboards and reporting
- Key Microsoft Learn modules: "Connect Microsoft services to Microsoft Sentinel", "Create and manage Microsoft Sentinel playbooks"

**Microsoft Defender (30% of exam weight)**
- Configure Microsoft Defender for Endpoint: onboarding, policies, automated investigation
- Use Microsoft Defender for Cloud for workload protection and secure score
- Investigate incidents across Microsoft 365 Defender (unified XDR portal)
- Configure Defender for Identity for Active Directory threat detection
- Implement attack surface reduction (ASR) rules
- Key Microsoft Learn modules: "Mitigate threats using Microsoft Defender for Endpoint", "Protect against threats with Microsoft Defender for Cloud"

---

## Microsoft Learn MCP Integration

The ASCENT Curator agent queries the **Microsoft Learn MCP** (Model Context Protocol) server at runtime to:
1. Fetch current exam objective weights and topic breakdowns
2. Retrieve recommended Microsoft Learn modules for each skill area
3. Pull practice assessment scores and module completion data
4. Surface learning path links for the learner's specific certification goal

This ensures certification guidance is always grounded in current Microsoft documentation rather than static internal content. When the Microsoft Learn MCP server is available, cited content will include direct links to `learn.microsoft.com` modules alongside internal knowledge base sources.

---

## General Study Recommendations

- **Practice over passive reading:** Hands-on labs on Microsoft Learn sandbox environments improve retention significantly compared to video-only study.
- **Use practice assessments early:** Taking a Microsoft Learn practice assessment at the start of study (before preparation) reveals knowledge gaps faster than sequential module completion.
- **Spaced repetition:** Revisit challenging topics across multiple sessions rather than in a single long block.
- **Booking discipline:** Only book the exam once achieving 75%+ on at least two separate practice assessments taken on different days.
- **Community resources:** Microsoft Tech Community, Stack Overflow Azure tags, and GitHub issue trackers for Azure SDKs all surface real-world implementation patterns that appear in scenario-based exam questions.
