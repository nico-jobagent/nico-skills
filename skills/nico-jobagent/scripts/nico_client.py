#!/usr/bin/env python3
"""
Nico Job Agent API Client

A simple CLI client for interacting with the Nico Job Agent API.
Used by AI agents to search for and create job applications.

Environment variables:
    NICO_API_KEY: API key for authentication (required)
    NICO_API_URL: Base URL (default: https://staging.nico-jobagent.com)
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

    api_url = os.environ.get("NICO_API_URL", "https://staging.nico-jobagent.com")
    return api_key, api_url


def make_request(method, endpoint, api_key, api_url, params=None, data=None):
    """Make an authenticated request to the Nico API."""
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
        print(f"API Error ({e.code}): {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
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
  # Parse a job URL to extract details
  %(prog)s parse-url --url "https://company.com/jobs/123"

  # Check if a job already exists by URL
  %(prog)s search --url "https://company.com/jobs/123"

  # Search jobs by company name
  %(prog)s search --company-name "Acme Inc"

  # Create a new proposed job
  %(prog)s create --title "Software Engineer" --company "Acme Inc" \\
      --url "https://company.com/jobs/123" --location "Berlin" \\
      --work-mode "remote" --employment_type "full-time"

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
    create_parser.set_defaults(func=cmd_create)

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
