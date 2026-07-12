#!/usr/bin/env python3
"""
Nico Job Agent API Client

A simple CLI client for interacting with the Nico Job Agent API.
Used by AI agents to search for and create job applications.

Environment variables:
    NICO_API_KEY: API key for authentication (required)
    NICO_API_URL: Base URL, scheme optional (default: api.nico-jobagent.com)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error


def get_config():
    """Get API configuration from environment variables."""
    api_key = os.environ.get("NICO_API_KEY")
    if not api_key:
        print("Error: NICO_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    # `or` (not a get default) so a set-but-empty NICO_API_URL falls back too.
    api_url = os.environ.get("NICO_API_URL") or "api.nico-jobagent.com"
    # Accept a bare host (e.g. "api.nico-jobagent.com") — normalize to a full
    # URL. A scheme the user supplied (http:// for local dev) is preserved.
    if not api_url.startswith(("http://", "https://")):
        api_url = "https://" + api_url.lstrip("/")
    return api_key, api_url


def make_request(method, endpoint, api_key, api_url, params=None, data=None, on_error="exit"):
    """Make an authenticated request to the Nico API.

    on_error="exit" (default): print the error and exit(1) — the behavior the
    existing commands rely on. on_error="return": return
    {"_error": {"code", "body"}} instead so the caller can translate it into a
    structured result (used by search-postings to mirror the MCP tool's
    {"error": ...} response shape).
    """
    # Build URL
    url = api_url.rstrip("/") + "/" + endpoint.lstrip("/")

    # Add query parameters for GET requests
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"

    # Prepare request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "NicoJobAgentClient/1.0"
    }

    body = None
    if data:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = {}
        try:
            error_body = json.loads(e.read().decode("utf-8"))
        except:
            pass
        if on_error == "return":
            return {"_error": {"code": e.code, "body": error_body}}
        print(f"API Error ({e.code}): {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        if on_error == "return":
            return {"_error": {"code": None, "body": {"error": f"Request failed: {e.reason}"}}}
        print(f"Request failed: {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_parse_url(args):
    """Parse a job posting URL to extract details."""
    api_key, api_url = get_config()

    result = make_request(
        "POST",
        "/api/job_applications/parse_url",
        api_key,
        api_url,
        data={"url": args.url}
    )

    print(json.dumps(result, indent=2))


def cmd_search(args):
    """Search for existing job applications."""
    api_key, api_url = get_config()

    params = {}
    if args.url:
        params["url"] = args.url
    if args.company_name:
        params["company_name"] = args.company_name
    if args.status:
        params["filter"] = args.status

    if not params:
        print("Error: At least one search parameter required (--url or --company-name)", file=sys.stderr)
        sys.exit(1)

    result = make_request(
        "GET",
        "/api/job_applications",
        api_key,
        api_url,
        params=params
    )

    jobs = result.get("job_applications", [])

    if args.url and jobs:
        # When searching by URL, we're checking for duplicates
        print(json.dumps({"exists": True, "count": len(jobs), "job_applications": jobs}, indent=2))
    elif args.url and not jobs:
        print(json.dumps({"exists": False, "count": 0}, indent=2))
    else:
        print(json.dumps(result, indent=2))


def cmd_create(args):
    """Create a new proposed job application."""
    api_key, api_url = get_config()

    job_data = {
        "job_application": {
            "title": args.title,
            "company_name": args.company,
        }
    }

    if args.url:
        job_data["job_application"]["url"] = args.url
    if args.location:
        job_data["job_application"]["location"] = args.location
    if args.work_mode:
        job_data["job_application"]["work_mode"] = args.work_mode
    if args.employment_type:
        job_data["job_application"]["employment_type"] = args.employment_type

    result = make_request(
        "POST",
        "/api/job_applications",
        api_key,
        api_url,
        data=job_data
    )

    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# search-postings — exact parity with the MCP `search_job_postings` tool.
#
# The MCP tool accepts employer/city NAMES and resolves them server-side; the
# REST API (`GET /api/job_postings`) takes pre-resolved employer_ids /
# location_id. To keep the backend API unchanged while exposing the same
# name-based interface to agents, this command does the resolution itself via
# existing read endpoints, then remaps the REST list rows into the MCP tool's
# exact output shape. Resolution rules (exactly-one-match, region-required for
# US/CA, radius/limit clamps) mirror the tool so behavior and error messages
# match.
# ---------------------------------------------------------------------------

def _fail_json(message, code=1):
    """Emit the MCP tool's {"error": ...} shape and exit non-zero."""
    print(json.dumps({"error": message}, indent=2))
    sys.exit(code)


def _unwrap_or_fail(resp):
    """Translate a returned HTTP error (on_error='return') into {"error": ...}."""
    if isinstance(resp, dict) and resp.get("_error"):
        err = resp["_error"]
        body = err.get("body") or {}
        _fail_json(body.get("error") or f"HTTP {err.get('code')}", code=3)
    return resp


def resolve_employer_ids(names, api_key, api_url):
    """Map employer names -> external_ids. Each name must match exactly one
    live employer (case-insensitive), else error — mirrors the MCP tool."""
    resp = _unwrap_or_fail(
        make_request("GET", "/api/employers/single_page_minimal", api_key, api_url, on_error="return")
    )
    employers = resp.get("employers", [])
    ids = []
    for raw in names:
        name = raw.strip()
        if not name:
            continue
        matches = [e for e in employers if (e.get("name") or "").strip().lower() == name.lower()]
        if not matches:
            _fail_json(f"Unknown employer: {name}")
        if len(matches) > 1:
            _fail_json(f"Ambiguous employer: multiple matches for {name} — please refine")
        ids.append(matches[0]["id"])
    return ids


def resolve_location_id(city, region, country, api_key, api_url):
    """Resolve a city name -> geocoded location external_id via the locations
    autocomplete, filtered to an exact (city, region?, country) match."""
    country = (country or "").strip().upper()
    region_val = (region or "").strip()
    if country in ("US", "CA") and not region_val:
        _fail_json(f"region (state/province) is required for city search in {country}")

    resp = _unwrap_or_fail(
        make_request("GET", "/api/locations/search", api_key, api_url,
                     params={"q": city.strip()}, on_error="return")
    )
    cands = [
        loc for loc in resp.get("locations", [])
        if loc.get("type") == "city"
        and (loc.get("city") or "").strip().lower() == city.strip().lower()
        and (loc.get("country_code") or "").upper() == country
        and (not region_val or (loc.get("region") or "").strip().lower() == region_val.lower())
    ]
    if not cands:
        _fail_json(f"Location not found: {city}")
    if len(cands) > 1:
        _fail_json(f"Ambiguous location: multiple matches for {city} — please refine")
    return cands[0]["id"]


def clamp_radius(raw):
    """Clamp into [1, 250] km (matches the MCP tool's MAX_RADIUS_KM)."""
    return max(1, min(int(raw), 250))


def resolve_limit(raw):
    """Default 20, max 100 (matches the MCP tool)."""
    requested = int(raw or 0)
    if requested <= 0:
        requested = 20
    return min(requested, 100)


def remap_posting(posting):
    """Reshape a REST /api/job_postings list row into the MCP tool's output."""
    employer = posting.get("employer") or {}
    return {
        # The API serializes a posting's external_id under the key "id" (see
        # HasExternalId); there is no "external_id" key in the response.
        "id": posting.get("id"),
        "title": posting.get("title"),
        "company_name": employer.get("name"),
        "company_id": employer.get("id"),
        "location": posting.get("location"),
        "work_mode": posting.get("work_mode"),
        "employment_type": posting.get("employment_type"),
        "salary_min": posting.get("salary_min"),
        "salary_max": posting.get("salary_max"),
        "salary_currency": posting.get("salary_currency"),
        "salary_period": posting.get("salary_period"),
        "posted_at": posting.get("posted_at"),
        "effective_posted_at": posting.get("effective_posted_at"),
        "url": posting.get("url"),
    }


def cmd_search_postings(args):
    """Search Nico's global job postings index (agent job discovery)."""
    api_key, api_url = get_config()

    # country_code is required — surfaced as the MCP tool's {"error": ...}
    # rather than an argparse usage error.
    if not (args.country or "").strip():
        _fail_json("country_code is required", code=2)
    country = args.country.strip().upper()

    params = {}
    if args.title:
        # The REST endpoint OR-splits on " OR "; joining the repeated --title
        # values reconstructs the MCP tool's title[] array semantics.
        terms = [t.strip() for t in args.title if t.strip()]
        if terms:
            params["title"] = " OR ".join(terms)
    if args.employers:
        ids = resolve_employer_ids(args.employers, api_key, api_url)
        if ids:
            params["employer_ids"] = ",".join(ids)
    if args.work_mode:
        params["work_mode"] = ",".join(args.work_mode)

    if (args.city or "").strip():
        # Location wins over country/region in JobPostings::Search, so — like
        # the MCP tool — we send location_id (+ radius) instead of country.
        params["location_id"] = resolve_location_id(args.city, args.region, country, api_key, api_url)
        if args.radius_km:
            params["radius_km"] = clamp_radius(args.radius_km)
    else:
        params["country_code"] = country
        if (args.region or "").strip():
            params["region"] = args.region.strip()

    params["per_page"] = resolve_limit(args.limit)

    resp = _unwrap_or_fail(
        make_request("GET", "/api/job_postings", api_key, api_url, params=params, on_error="return")
    )
    postings = [remap_posting(p) for p in resp.get("job_postings", [])]
    print(json.dumps({"job_postings": postings, "count": len(postings)}, indent=2))


def cmd_get_posting(args):
    """Fetch one posting's full detail from Nico's index by its id (external_id)."""
    api_key, api_url = get_config()
    posting_id = (args.id or "").strip()
    if not posting_id:
        _fail_json("id is required", code=2)

    resp = _unwrap_or_fail(
        make_request("GET", "/api/job_postings/" + urllib.parse.quote(posting_id, safe=""),
                     api_key, api_url, on_error="return")
    )
    # Same summary shape as search-postings, plus the detail-only fields.
    out = remap_posting(resp)
    out["description"] = resp.get("description")
    out["source_attribution"] = resp.get("source_attribution")
    out["source_provides_date"] = resp.get("source_provides_date")
    print(json.dumps(out, indent=2))


def cmd_list(args):
    """List job applications."""
    api_key, api_url = get_config()

    params = {}
    if args.status:
        params["filter"] = args.status
    if args.per_page:
        params["per_page"] = args.per_page

    result = make_request(
        "GET",
        "/api/job_applications",
        api_key,
        api_url,
        params=params
    )

    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Nico Job Agent API Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover openings in Nico's global index (start here for job search)
  %(prog)s search-postings --title "backend engineer" --country US --region California
  %(prog)s search-postings --employers "Anthropic" --country US --work-mode remote
  %(prog)s search-postings --city "Berlin" --country DE --radius-km 25 --title designer

  # Fetch one posting's full detail (description, etc.) by its id
  %(prog)s get-posting --id 019e5132-627d-799e-963e-3c24f72a9dd5

  # Parse a job URL to extract details
  %(prog)s parse-url --url "https://company.com/jobs/123"

  # Check if a job already exists by URL
  %(prog)s search --url "https://company.com/jobs/123"

  # Search jobs by company name
  %(prog)s search --company-name "Acme Inc"

  # Create a new proposed job
  %(prog)s create --title "Software Engineer" --company "Acme Inc" \\
      --url "https://company.com/jobs/123" --location "Berlin" \\
      --work-mode "remote" --employment-type "full-time"

  # List all proposed jobs
  %(prog)s list --status draft
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # parse-url command
    parse_url_parser = subparsers.add_parser("parse-url", help="Parse a job posting URL")
    parse_url_parser.add_argument("--url", required=True, help="Job posting URL to parse")
    parse_url_parser.set_defaults(func=cmd_parse_url)

    # search command
    search_parser = subparsers.add_parser("search", help="Search for existing job applications")
    search_parser.add_argument("--url", help="Search by exact URL")
    search_parser.add_argument("--company-name", help="Search by company name")
    search_parser.add_argument("--status", help="Filter by status (draft, applied, etc.)")
    search_parser.set_defaults(func=cmd_search)

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new proposed job application")
    create_parser.add_argument("--title", required=True, help="Job title")
    create_parser.add_argument("--company", required=True, help="Company name")
    create_parser.add_argument("--url", help="Job posting URL")
    create_parser.add_argument("--location", help="Job location")
    create_parser.add_argument("--work-mode", choices=["remote", "remote-optional", "hybrid", "on-site"],
                               help="Work mode (default: hybrid)")
    create_parser.add_argument("--employment-type", choices=["full-time", "part-time", "contract", "internship", "temporary"],
                               help="Employment type")
    create_parser.set_defaults(func=cmd_create)

    # search-postings command (global job index — exact parity with the MCP
    # `search_job_postings` tool)
    sp = subparsers.add_parser(
        "search-postings",
        help="Search Nico's global job postings index to discover openings"
    )
    sp.add_argument("--title", action="append", metavar="PHRASE",
                    help="Title phrase, case-insensitive substring; repeat to OR several "
                         "(e.g. --title 'backend engineer' --title 'staff engineer')")
    sp.add_argument("--employers", action="append", metavar="NAME",
                    help="Employer name; repeat for several. Each must resolve to exactly one employer.")
    sp.add_argument("--country", metavar="CC",
                    help="ISO 3166-1 alpha-2 country code (required). e.g. US, NL, FR")
    sp.add_argument("--region", help="State/province name. Required with --city when --country is US or CA.")
    sp.add_argument("--city", help="City for radius search (resolved against Nico's geocoded index).")
    sp.add_argument("--radius-km", type=int, help="Radius in km around --city (default 25, max 250).")
    sp.add_argument("--work-mode", action="append", choices=["remote", "onsite"],
                    help="Filter by work mode; repeat for several (remote, onsite).")
    sp.add_argument("--limit", type=int, default=20, help="Max results (default 20, max 100).")
    sp.set_defaults(func=cmd_search_postings)

    # get-posting command (full detail for one posting by id)
    gp = subparsers.add_parser(
        "get-posting",
        help="Fetch one posting's full detail (incl. description) by its id"
    )
    gp.add_argument("--id", required=True, help="Posting id (the `id` from search-postings results)")
    gp.set_defaults(func=cmd_get_posting)

    # list command
    list_parser = subparsers.add_parser("list", help="List job applications")
    list_parser.add_argument("--status", help="Filter by status group (draft, applied, interviewing, offer, finished, active)")
    list_parser.add_argument("--per-page", type=int, default=25, help="Items per page (default: 25)")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
