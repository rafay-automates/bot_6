# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# import json
#
#
# # ----------------- Helper Functions -----------------
# def get_csrf_token(session):
#     """Fetch a fresh CSRF token from the homepage."""
#     home = session.get("https://linkdetective.pro/")
#     soup = BeautifulSoup(home.text, "html.parser")
#     token_input = soup.find("input", {"name": "_token"})
#     if token_input:
#         return token_input["value"]
#     return session.cookies.get("XSRF-TOKEN")
#
#
# def fetch_domain_data(session, csrf_token, domain_name):
#     """Fetch domain data, retrying if CSRF token fails."""
#     payload = {
#         "draw": 5,
#         "start": 0,
#         "length": 50,
#         "_token": csrf_token,
#         "domains[]": domain_name,
#         "buttons": "true"
#     }
#
#     resp = session.post("https://linkdetective.pro/api/domains", data=payload)
#
#     # Retry with new token if invalid
#     if resp.status_code == 419 or "invalid" in resp.text.lower():
#         csrf_token = get_csrf_token(session)
#         payload["_token"] = csrf_token
#         resp = session.post("https://linkdetective.pro/api/domains", data=payload)
#
#     try:
#         return resp.json()
#     except ValueError:
#         return None
#
#
# # ----------------- Main Logic -----------------
# def main():
#     # Take user input from console
#     domain_input = input("Enter domain(s), separated by commas: ").strip()
#
#     if not domain_input:
#         print(json.dumps({"error": "Please enter at least one domain."}, indent=4))
#         return
#
#     domains_list = [d.strip() for d in domain_input.split(",") if d.strip()]
#
#     session = requests.Session()
#     csrf_token = get_csrf_token(session)
#
#     results = []
#
#     for domain_name in domains_list:
#         data = fetch_domain_data(session, csrf_token, domain_name)
#         if not data:
#             results.append({
#                 "domain": domain_name,
#                 "error": "Failed to fetch data"
#             })
#             continue
#
#         sellers_by_domain = data.get("sellers", [])
#         domains = [row.get("Domain") for row in data.get("data", [])]
#
#         if not sellers_by_domain:
#             results.append({
#                 "domain": domain_name,
#                 "error": "No sellers found"
#             })
#         else:
#             for i, sellers in enumerate(sellers_by_domain):
#                 dom = domains[i] if i < len(domains) else domain_name
#                 for s in sellers:
#                     results.append({
#                         "domain": dom,
#                         "contact": s.get("contacts"),
#                         "price": s.get("price"),
#                         "date": s.get("date")
#                     })
#
#     # Print JSON output
#     print(json.dumps(results, indent=4))
#
#
# if __name__ == "__main__":
#     main()

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Guest Post Website Price API")

# Allow frontend to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- Helper Functions -----------------
def get_csrf_token(session):
    """Fetch a fresh CSRF token from the homepage."""
    home = session.get("https://linkdetective.pro/")
    soup = BeautifulSoup(home.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    if token_input:
        return token_input["value"]
    return session.cookies.get("XSRF-TOKEN")


def fetch_domain_data(session, csrf_token, domain_name):
    """Fetch domain data, retrying if CSRF token fails."""
    payload = {
        "draw": 5,
        "start": 0,
        "length": 50,
        "_token": csrf_token,
        "domains[]": domain_name,
        "buttons": "true"
    }

    resp = session.post("https://linkdetective.pro/api/domains", data=payload)

    # Retry with new token if invalid
    if resp.status_code == 419 or "invalid" in resp.text.lower():
        csrf_token = get_csrf_token(session)
        payload["_token"] = csrf_token
        resp = session.post("https://linkdetective.pro/api/domains", data=payload)

    try:
        return resp.json()
    except ValueError:
        return None


# ----------------- API Endpoint -----------------
@app.get("/fetch")
def fetch_domains(domains: str = Query(..., description="Comma-separated domain names")):
    session = requests.Session()
    csrf_token = get_csrf_token(session)

    domains_list = [d.strip() for d in domains.split(",") if d.strip()]
    results = []

    for domain_name in domains_list:
        data = fetch_domain_data(session, csrf_token, domain_name)
        if not data:
            results.append({
                "domain": domain_name,
                "error": "Failed to fetch data"
            })
            continue

        sellers_by_domain = data.get("sellers", [])
        domain_info = [row.get("Domain") for row in data.get("data", [])]

        if not sellers_by_domain:
            results.append({
                "domain": domain_name,
                "error": "No sellers found"
            })
        else:
            for i, sellers in enumerate(sellers_by_domain):
                dom = domain_info[i] if i < len(domain_info) else domain_name
                for s in sellers:
                    results.append({
                        "domain": dom,
                        "contact": s.get("contacts"),
                        "price": s.get("price"),
                        "date": s.get("date")
                    })

    return JSONResponse(content=results)
