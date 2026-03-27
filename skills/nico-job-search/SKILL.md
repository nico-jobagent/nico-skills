---
name: nico-job-search
description: Search job boards for postings and add them as proposed jobs to Nico Job Agent
user-invocable: true
---

## Overview

This skill integrates with the Nico Job Agent API to:
1. Search configured job boards for job postings
2. Check if jobs already exist in Nico (by URL or company name)
3. Parse job posting URLs to extract details
4. Create new proposed jobs for review

## Configuration

Set these environment variables:
- `NICO_API_KEY`: Your Nico API key (required)
- `NICO_API_URL`: Nico API base URL (default: `https://staging.nico-jobagent.com`)

## Workflow

When searching for jobs:

1. **Search job boards** for matching positions
2. **For each job URL found:**
   - Check if it already exists: `python3 scripts/nico_client.py search --url "<job_url>"`
   - If exists (`"exists": true`), skip it
   - If not exists, parse the URL: `python3 scripts/nico_client.py parse-url --url "<job_url>"`
   - Create the job: `python3 scripts/nico_client.py create --title "<title>" --company "<company>" --url "<url>" --location "<location>" --work-mode "<work_mode>"`

3. **Report results** to the user

## Commands

### Check if job exists by URL

```bash
python3 scripts/nico_client.py search --url "https://company.com/jobs/123"
```

Returns:
```json
{"exists": true, "count": 1, "job_applications": [...]}
```
or
```json
{"exists": false, "count": 0}
```

### Check if job exists by company name

```bash
python3 scripts/nico_client.py search --company-name "Acme Inc"
```

### Parse a job posting URL

Extract job details (title, company, location, work mode) from a job posting URL:

```bash
python3 scripts/nico_client.py parse-url --url "https://jobs.lever.co/company/123"
```

Returns parsed data that can be used to create a job.

### Create a proposed job

```bash
python3 scripts/nico_client.py create \
  --title "Software Engineer" \
  --company "Acme Inc" \
  --url "https://company.com/jobs/123" \
  --location "Berlin, Germany" \
  --work-mode "remote"
```

Work mode options: `remote`, `remote-optional`, `hybrid`, `on-site`

### List proposed jobs

```bash
python3 scripts/nico_client.py list --status draft
```

## Example Session

User: "Find me senior backend engineering jobs in Berlin"

1. Search configured job sites for "senior backend engineer Berlin"
2. For each job found:
   ```bash
   # Check if already in Nico
   python3 scripts/nico_client.py search --url "https://example.com/jobs/senior-backend"

   # If not found, parse the URL
   python3 scripts/nico_client.py parse-url --url "https://example.com/jobs/senior-backend"

   # Create the job with parsed data
   python3 scripts/nico_client.py create \
     --title "Senior Backend Engineer" \
     --company "Example Corp" \
     --url "https://example.com/jobs/senior-backend" \
     --location "Berlin, Germany" \
     --work-mode "hybrid"
   ```
3. Report: "Added 5 new proposed jobs to Nico"

## Notes

- Jobs created by this skill have status `proposed` and require owner approval
- The `parse-url` command uses Nico's built-in parsers to extract job details
- Duplicate detection is by exact URL match
- Company names are matched case-insensitively
