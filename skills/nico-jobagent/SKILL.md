---
name: nico-jobagent
description: Search Nico Job Agent's global job index to discover openings, and add job postings as proposed jobs
user-invocable: true
---

## Overview

This skill integrates with the Nico Job Agent API to:
1. **Search Nico's global job postings index** to discover openings (start here for job search)
2. Check if jobs already exist in Nico (by URL or company name)
3. Parse job posting URLs to extract details
4. Create new proposed jobs for review

## Configuration

Set these environment variables:
- `NICO_API_KEY`: Your Nico API key (required)
- `NICO_API_URL`: Nico API base URL, scheme optional (default: `api.nico-jobagent.com`)

## Workflow

When searching for jobs, **search Nico's own index first** — it already contains
hundreds of thousands of postings ingested from employers' ATSes, deduplicated and
kept fresh. Only fall back to external job boards for gaps.

1. **Search Nico's index** for matching positions — pick a geographic filter
   (`--region`/`--city`) for on-site roles, OR `--work-mode remote` for remote roles,
   but not both together (see caveat below):
   `python3 scripts/nico_client.py search-postings --title "<phrase>" --country <CC> [--region <name> | --city <name> | --work-mode remote]`
   Each result already carries `url`, `company_name`, `location`, `work_mode`, salary, and dates.
2. **(Optional) Fill gaps from external job boards** for roles not yet in Nico.
3. **For each job URL you want to add as a proposal:**
   - Check if it already exists: `python3 scripts/nico_client.py search --url "<job_url>"`
   - If exists (`"exists": true`), skip it
   - If not exists, parse the URL: `python3 scripts/nico_client.py parse-url --url "<job_url>"`
   - Create the job: `python3 scripts/nico_client.py create --title "<title>" --company "<company>" --url "<url>" --location "<location>" --work-mode "<work_mode>"`
4. **Report results** to the user

> Note: `search-postings` (discovering openings in Nico's index) is different from
> `search` (checking your own tracked applications for duplicates). Use `search-postings`
> to find jobs; use `search` to avoid creating duplicates.

## Commands

### Search Nico's global job postings index

Discover openings across all employers Nico tracks. `--country` is **required**.

```bash
# By title (repeat --title to OR several phrases)
python3 scripts/nico_client.py search-postings \
  --title "backend engineer" --title "staff engineer" \
  --country US --region California

# At specific employers (each name must resolve to exactly one employer)
python3 scripts/nico_client.py search-postings --employers "Anthropic" --country US --work-mode remote

# Radius search around a city (region required for US/CA cities)
python3 scripts/nico_client.py search-postings --city "Berlin" --country DE --radius-km 25 --title designer
```

Returns:
```json
{"job_postings": [{"id": "...", "title": "...", "company_name": "...", "location": "...",
                   "work_mode": "...", "employment_type": "...", "salary_min": null,
                   "posted_at": "...", "url": "..."}], "count": 12}
```

Options:
- `--title PHRASE` — case-insensitive substring; repeat to OR several
- `--employers NAME` — employer name; repeat for several (each must be unambiguous)
- `--country CC` — ISO 3166-1 alpha-2 (required)
- `--region NAME` — state/province; required with `--city` when country is US or CA
- `--city NAME` — city for radius search (resolved against Nico's geocoded index)
- `--radius-km N` — radius around `--city` (default 25, max 250)
- `--work-mode {remote,onsite}` — repeat for several
- `--limit N` — max results (default 20, max 100)

> **Don't combine `--region`/`--city` with `--work-mode remote`.** Remote postings
> aren't pinned to a location, so a geographic filter + `remote` almost always returns
> zero. Search remote roles by country only (optionally `--work-mode remote`), and use
> `--region`/`--city` for on-site/hybrid roles.

Errors are returned as `{"error": "..."}` (e.g. unknown/ambiguous employer, unknown
location, `country_code is required`, or job search not enabled for the account).

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
   python3 scripts/nico_client.py search --url "https://careers.company.com/jobs/123"

   # If not found, parse the URL
   python3 scripts/nico_client.py parse-url --url "https://careers.company/jobs/123"

   # Create the job with parsed data
   python3 scripts/nico_client.py create \
     --title "Senior Backend Engineer" \
     --company "Example Corp" \
     --url "https://example.com/jobs/senior-backend" \
     --location "Berlin, Germany" \
     --work-mode "hybrid"
   ```

## Notes

- `search-postings` mirrors Nico's MCP `search_job_postings` tool exactly (same inputs, same
  output shape) — the client resolves employer/city names to ids for you, so no MCP client is needed.
- `search-postings` requires **job search to be enabled** for the account; otherwise it returns
  `{"error": "Job search is not enabled for this account"}`.
- Jobs created by this skill have status `proposed` and require owner approval
- The `parse-url` command uses Nico's built-in parsers to extract job details
- Duplicate detection is by exact URL match
- Company names are matched case-insensitively
