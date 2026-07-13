---
name: nico-jobagent
description: Search Nico Job Agent's job index to discover openings, and add job postings as proposed jobs
user-invocable: true
---

## Overview

This skill integrates with the Nico Job Agent API. Its commands come in two groups:

- **`posting`** — job posting search: discover openings in Nico's index (read-only)
- **`application`** — job application management: your tracked applications (search, create, notes)

Typical use: search Nico's index for openings (`posting search`), pull details
(`posting get`), then track the interesting ones as proposed applications
(`application create`).

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
   `python3 scripts/nico_client.py posting search --title "<phrase>" --country <CC> [--region <name> | --city <name> | --work-mode remote]`
   Each result carries `id`, `company_name`, `location`, `work_mode`, salary, and dates
   (the search list is compact — it does NOT include the application `url` or description).
   To get the application `url` and full `description` for a result, fetch it by id:
   `python3 scripts/nico_client.py posting get --id "<id>"`
2. **(Optional) Fill gaps from external job boards** for roles not yet in Nico.
3. **For each job URL you want to add as a proposal:**
   - Check if it already exists: `python3 scripts/nico_client.py application search --url "<job_url>"`
   - If exists (`"exists": true`), skip it
   - If not exists, parse the URL: `python3 scripts/nico_client.py application parse-url --url "<job_url>"`
   - Create the job: `python3 scripts/nico_client.py application create --title "<title>" --company "<company>" --url "<url>" --location "<location>" --work-mode "<work_mode>"`
4. **Report results** to the user

> Note: `posting search` (discovering openings in Nico's index) is different from
> `application search` (checking your own tracked applications for duplicates). Use
> `posting search` to find jobs; use `application search` to avoid creating duplicates.

## Commands — `posting` (job posting search)

### posting search

Discover openings across all employers Nico tracks. `--country` is **required**.

```bash
# By title (repeat --title to OR several phrases)
python3 scripts/nico_client.py posting search \
  --title "backend engineer" --title "staff engineer" \
  --country US --region California

# At specific employers (each name must resolve to exactly one employer)
python3 scripts/nico_client.py posting search --employers "Anthropic" --country US --work-mode remote

# Radius search around a city (region required for US/CA cities)
python3 scripts/nico_client.py posting search --city "Berlin" --country DE --radius-km 25 --title designer
```

Returns (compact — no `url`/`description`; use `posting get` for those). The `pagination`
block tells you whether more pages exist — pass `--page N` to walk them:
```json
{"job_postings": [{"id": "...", "title": "...", "company_name": "...", "location": "...",
                   "work_mode": "...", "employment_type": "...", "salary_min": null,
                   "posted_at": "...", "effective_posted_at": "..."}],
 "count": 20,
 "pagination": {"current_page": 1, "total_pages": 5, "total_count": 99, "per_page": 20}}
```

Options:
- `--title PHRASE` — case-insensitive substring; repeat to OR several
- `--employers NAME` — employer name; repeat for several (each must be unambiguous)
- `--country CC` — ISO 3166-1 alpha-2 (required)
- `--region NAME` — state/province; required with `--city` when country is US or CA
- `--city NAME` — city for radius search (resolved against Nico's geocoded index)
- `--radius-km N` — radius around `--city` (default 25, max 250)
- `--work-mode {remote,onsite}` — repeat for several
- `--limit N` — results per page (default 20, max 100)
- `--page N` — page number (default 1); check `pagination.total_pages` in the output

> **Don't combine `--region`/`--city` with `--work-mode remote`.** Remote postings
> aren't pinned to a location, so a geographic filter + `remote` almost always returns
> zero. Search remote roles by country only (optionally `--work-mode remote`), and use
> `--region`/`--city` for on-site/hybrid roles.

Errors are returned as `{"error": "..."}` (e.g. unknown/ambiguous employer, unknown
location, `country_code is required`, or job search not enabled for the account).

### posting get

Fetch one posting (including its full `description`) by the `id` returned from `posting search`:

```bash
python3 scripts/nico_client.py posting get --id "019e5132-627d-799e-963e-3c24f72a9dd5"
```

Returns the same fields as a search result **plus the application `url` and the full
`description`** (both omitted from the compact search list). Returns
`{"error": "Job posting not found"}` for an unknown id.

## Commands — `application` (job application management)

### application search

Check whether a job is already tracked (duplicate check by exact URL, or search by company):

```bash
python3 scripts/nico_client.py application search --url "https://company.com/jobs/123"
python3 scripts/nico_client.py application search --company-name "Acme Inc"
```

Returns (URL search):
```json
{"exists": true, "count": 1, "job_applications": [...]}
```
or
```json
{"exists": false, "count": 0}
```

### application list

```bash
python3 scripts/nico_client.py application list --status draft
python3 scripts/nico_client.py application list --per-page 25 --page 2
```

Status groups: `draft`, `applied`, `interviewing`, `offer`, `finished`, `active`.
Paged — the response's `pagination` block carries `total_pages`.

### application get

Fetch one application's full detail, including its notes and interviews:

```bash
python3 scripts/nico_client.py application get --id "<application_id>"
```

### application create

```bash
python3 scripts/nico_client.py application create \
  --title "Software Engineer" \
  --company "Acme Inc" \
  --url "https://company.com/jobs/123" \
  --location "Berlin, Germany" \
  --work-mode "remote"
```

Work mode options: `remote`, `remote-optional`, `hybrid`, `on-site`

### application add-note

```bash
python3 scripts/nico_client.py application add-note --id "<application_id>" --body "Recruiter replied, call on Friday"
```

### application parse-url

Extract job details (title, company, location, work mode) from a job posting URL:

```bash
python3 scripts/nico_client.py application parse-url --url "https://jobs.lever.co/company/123"
```

Returns parsed data that can be used to create an application.

## Example Session

User: "Find me senior backend engineering jobs in Berlin"

```bash
# 1. Search Nico's index first
python3 scripts/nico_client.py posting search \
  --title "senior backend engineer" --city "Berlin" --country DE

# 2. Pull the application url + description for an interesting result
python3 scripts/nico_client.py posting get --id "<posting_id>"

# 3. Check it isn't already tracked
python3 scripts/nico_client.py application search --url "<application_url>"

# 4. Propose it
python3 scripts/nico_client.py application create \
  --title "Senior Backend Engineer" \
  --company "Example Corp" \
  --url "<application_url>" \
  --location "Berlin, Germany" \
  --work-mode "hybrid"
```

## Notes

- `posting search` takes employer and city **names** and resolves them to ids for you, so you
  don't need to look up any identifiers first.
- The `posting` commands require **job search to be enabled** for the account; otherwise they
  return `{"error": "Job search is not enabled for this account"}`.
- Applications created by this skill have status `proposed` and require owner approval
- `application parse-url` uses Nico's built-in parsers to extract job details
- Duplicate detection is by exact URL match
- Company names are matched case-insensitively
