# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CaseLoad is a web application that provides analytics on CVE (Common Vulnerabilities and Exposures) tracker data from multiple Jira projects. It helps leadership understand macro trends around CVE work affecting engineering teams.

## Technology Stack

- **Backend**: Python with Flask
- **Database**: SQLite (cache for Jira data, re-loadable from source)
- **Analytics**: Python (potentially pandas)
- **Data Source**: Jira API

## Architecture

The application has three functional areas:

1. **Web UI** - Flask-based responsive web interface with visualizations and tabulated data
2. **Analytics** - Python modules for CVE trend analysis
3. **Data** - Jira API integration with SQLite caching

## Data Model

Core entities:
- **Team** - identified by name, owns one or more Jira projects
- **Jira Project** - associated with a Team, has dependent Projects
- **Tracker** - Jira issue (by key), linked to a CVE
- **CVE** - identified by CVE key, has URL, creation date, embargoed status

Project dependencies represent fix ordering (one project must deliver before another can proceed).

## Analytics Views

**Top Down**: Organization-wide CVE impact (tracker counts, SLA compliance, severity breakdown, closure reasons)

**Bottoms Up**: Per-CVE blast radius (affected teams, date skew, dependency visualization)
