# What is CaseLoad?

CaseLoad is a web based application that performs analytics on CVE tracker data coming from multiple Jira projects for a large organization of engineers creating software products and services. Its primary goal is to provide insight into the trends and implications of the CVE trackers as they are raised by a product security team. The audience is primarily leadership and organization decision makers who want to understand the macro trends around the CVE work being placed upon their engineering teams.

# How should it be accessed?

CaseLoad should be entirely browser driven, with a responsive and modern UI. It favors visualizations and tabulated data as well as textual narratives describing what is being presented.

# How is it designed?

CaseLoad is written in python, fetching Jira data dynamically and storing it into a sqlite database. It is composed of several functional areas:

* Web UI (based on flask)
* Analytics (using plain python, maybe pandas)
* Data (using Jira API, sqlite)

It is expected that the number and types of analytics will change over time so we want to keep the data model as flexible as possible both in terms of ingestion (e.g. new data sources) and format (e.g. new types of analysis). Currently we will use Jira as the primary data source, but it is possible that other vulnerabilty related data sources will be made available (e.g. from a centralized build system) and vulnerabilities will need to be from that data as well.

We also need to maintain a list of Jira projects 'in-scope' for the organization and their dependencies. The dependency graph should indicate that for certain CVEs, one project may not be able to work on it until another project has delivered the fix. We can represent this dependency graph in the database itself.

The sqlite cache should be re-loadable at anytime from the data sources. When the CaseLoad app starts it can be instructed to synchronize the cache, meaning it pulls new Jira trackers it hasn't yet seen (created after the last sync datetime). We don't need to be too careful here as overwriting existing trackers in the database should be idempotent.

# How is it deployed?

CaseLoad should run comfortably on a laptop. In the future it might also be deployed to an OpenShift server where it can be accessed at a group level.

# What sort of analytics are available?

First and foremost, CaseLoad should provdie analytics that aren't easily done through simple Jira dashboards and queries. 
CaseLoad provides two main views- "Top Down" and "Bottoms Up".

## Top Down

What is the CVE Tracker impact to the overall organiation? What are the macro trends we're seeing for a specific time range:

* Overall number of trackers raised ("the problem space")
    * Historical trends as well- Trackers per week, etc.
* Time budgets from created→due date→SLA compared to guidelines ("the correctness")
    * How many teams actually hit their Due Dates?
    * How many teams actually hit their SLAs?
    * Number of Trackers that had Due Date changed
* Number of components for a single CVE ("inter-product blizzards")
* Number of products for a single CVE ("intra-product blizzards")
* Number of trackers closed ['obsolete', "won't do", 'Not a Bug', 'Duplicate'] ("the accuracy")
    * Breakdown on each category- why were they closed this way?
* Number of trackers by Severity / CVSS Score


## Bottoms Up

Enter a CVE and get the 'blast radius' for the organization.

* how many trackers
* how many teams affected
* consistency in Due Date and SLAs across trackers ("date skew")
* visualize dependencies across trackers (who needs to go first, who is waiting, when is a fix ready, etc.)


## Data Model

The data model should be based on a few core concepts:

* a Team
    * identified by a name
    * having one or more Jira projects
* a Jira Project
    * identified by Project name
    * associated with a Team
    * having one or more dependent Projects
* a Tracker
    * identified by the Jira Key
    * associated with a CVE
    * having all relevant Jira details
* a CVE
    * identified by the CVE key
    * having a CVE page URL
    * having a creation date
    * having an embargoed status