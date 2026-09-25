# Security Policy

## Data Classification

All company data is classified into one of four tiers: **Public**, **Internal**, **Confidential**,
and **Restricted**. Public data may be shared freely. Internal data is for employee use only.
Confidential data (customer records, financial reports, contracts) requires manager approval to
share externally. Restricted data (credentials, encryption keys, unreleased financials) may only be
accessed by named individuals on an approved access list, and every access is logged.

## Access Control

Access to systems follows the principle of least privilege: employees receive only the permissions
required for their role, granted through role-based access control (RBAC). Access reviews happen
quarterly, and any account inactive for 90 days is automatically disabled. All production systems
require multi-factor authentication (MFA). Passwords must be at least 14 characters and are rotated
every 180 days; reuse of the last 10 passwords is blocked.

## Encryption Standards

Data at rest is encrypted using AES-256. Data in transit uses TLS 1.2 or higher. Encryption keys are
stored in a dedicated key management service and rotated annually, or immediately upon suspected
compromise.

## Incident Response

Suspected security incidents must be reported to the Security team within 1 hour of discovery via the
#security-incidents channel or the security hotline. The Security team triages incidents within 4
business hours, assigns a severity level (P1-P4), and coordinates remediation. A post-incident review
is required for all P1 and P2 incidents within 5 business days of resolution.
