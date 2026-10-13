#!/usr/bin/env python3
"""eval_pipeline.py - Evaluation and test pipeline for the recipe agent system.

Runs three test suites against the *running* services over HTTP. The services
can run locally (uvicorn) or on Cloud Run:

  1. API payload integrity   - health checks, A2A agent cards, grocery API
                               schemas and totals, A2A JSON-RPC envelopes.
  2. Tool-execution fidelity - golden prompts sent to the agents. Checks that the
                               right tool ran with the right arguments by
                               inspecting the A2UI output (surface, recipe,
                               servings, groceries, category filter).
  3. System responsiveness   - simulated concurrent traffic on the grocery
                               /products/match endpoint (p50/p95/max, RPS, errors).

Usage:
  python3 eval_pipeline.py                                  # localhost defaults
  python3 eval_pipeline.py --grocery-url=https://... --recipe-url=https://... \
                           --chatbot-url=https://...        # Cloud Run
  python3 eval_pipeline.py --skip-agents                    # no LLM calls
  python3 eval_pipeline.py --json-out=results.json

For private (IAM-only) Cloud Run services, pass an identity token:
  ID_TOKEN=$(gcloud auth print-identity-token) python3 eval_pipeline.py ...

Uses only the Python standard library. Exits 1 if any check fails.
"""

import argparse
import concurrent.futures
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid

RESULTS = []  # list of dicts: {suite, name, passed, ms, detail}


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #
def http(method, url, body=None, token=None, timeout=60):
    """Sends a JSON request. Returns (status_code, parsed_json_or_text)."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status, raw = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read().decode(errors="ignore")
    except (urllib.error.URLError, OSError) as e:  # connection refused, DNS, timeout
        return 0, str(e)
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, raw


def check(suite, name):
    """Decorator that times a check and records PASS/FAIL. The check returns a detail
    string on success and raises AssertionError (or any exception) on failure."""
    def wrap(fn):
        def run(*args, **kwargs):
            start = time.perf_counter()
            try:
                detail, passed = fn(*args, **kwargs) or "", True
            except Exception as e:  # noqa: BLE001 - report every failure
                detail, passed = f"{type(e).__name__}: {e}", False
            ms = (time.perf_counter() - start) * 1000
            RESULTS.append({"suite": suite, "name": name, "passed": passed, "ms": round(ms, 1), "detail": detail})
            mark = "\033[32mPASS\033[0m" if passed else "\033[31mFAIL\033[0m"
            print(f"  [{mark}] {name:<52} {ms:8.0f} ms  {detail}")
        return run
    return wrap


# --------------------------------------------------------------------------- #
# A2UI helpers
# --------------------------------------------------------------------------- #
def a2ui_data(messages, path):
    """Returns the value of the updateDataModel message at `path`, or None."""
    for m in messages:
        dm = m.get("updateDataModel")
        if dm and dm.get("path") == path:
            return dm.get("value")
    return None


def surfaces(messages):
    return {m["createSurface"]["surfaceId"] for m in messages if "createSurface" in m}


# --------------------------------------------------------------------------- #
# Suite 1: API payload integrity
# --------------------------------------------------------------------------- #
PRODUCT_FIELDS = {"sku", "product_name", "brand", "ingredient_category", "pack_size",
                  "price_sgd", "in_stock", "image_url", "product_url"}


def suite_payload_integrity(cfg):
    print("\n1. API payload integrity")
    S = "payload"

    for svc, url in cfg.urls.items():
        @check(S, f"GET /health ({svc})")
        def _(url=url):
            status, body = http("GET", f"{url}/health", token=cfg.token, timeout=cfg.timeout)
            assert status == 200, f"HTTP {status}"
            assert isinstance(body, dict) and body.get("status") == "healthy", f"body={body}"
            return f"service={body.get('service')}"
        _()

    for svc in ("recipe_agent", "main_chatbot"):
        @check(S, f"GET /.well-known/agent-card.json ({svc})")
        def _(svc=svc):
            status, card = http("GET", f"{cfg.urls[svc]}/.well-known/agent-card.json", token=cfg.token)
            assert status == 200, f"HTTP {status}"
            for key in ("name", "description", "url", "skills"):
                assert key in card, f"missing '{key}'"
            assert card["url"].endswith("/a2a/app"), f"url={card['url']}"
            skill_ids = [s["id"] for s in card["skills"]]
            assert skill_ids and all(skill_ids), "skills must have ids"
            return f"skills={skill_ids}"
        _()

    @check(S, "POST /products/match schema + total")
    def _():
        ingredients = ["2 english muffins", "1 cup mozzarella cheese", "pitted black olives", "4 strips bacon"]
        status, body = http("POST", f"{cfg.urls['grocery_db_service']}/products/match",
                            {"ingredients": ingredients}, cfg.token)
        assert status == 200, f"HTTP {status}"
        results = body["results"]
        assert len(results) == len(ingredients), f"{len(results)} results for {len(ingredients)} ingredients"
        unique = {}
        for r in results:
            assert r["match_confidence"] in ("high", "medium", "search_fallback"), r["match_confidence"]
            missing = PRODUCT_FIELDS - r["matched_product"].keys()
            assert not missing, f"product missing {missing}"
            p = r["matched_product"]
            unique[p["sku"]] = p["promo_price_sgd"] or p["price_sgd"]
        expected = round(sum(unique.values()), 2)
        assert abs(body["total_estimated_sgd"] - expected) < 0.01, \
            f"total {body['total_estimated_sgd']} != sum of unique products {expected}"
        return f"{len(results)} matched, total=${expected:.2f}"
    _()

    @check(S, "GET /products?q= filter")
    def _():
        status, products = http("GET", f"{cfg.urls['grocery_db_service']}/products?q=cheese", token=cfg.token)
        assert status == 200 and isinstance(products, list) and products, f"HTTP {status}"
        assert all("cheese" in (p["product_name"] + p["search_keywords"] + p["brand"]).lower() for p in products)
        return f"{len(products)} products"
    _()

    @check(S, "POST /products/match rejects bad payload (422)")
    def _():
        status, _ = http("POST", f"{cfg.urls['grocery_db_service']}/products/match", {"wrong": 1}, cfg.token)
        assert status == 422, f"expected 422, got {status}"
        return "HTTP 422"
    _()

    if not cfg.skip_agents:
        @check(S, "A2A JSON-RPC message/send envelope (recipe_agent)")
        def _():
            rpc_id = str(uuid.uuid4())
            req = {"jsonrpc": "2.0", "id": rpc_id, "method": "message/send", "params": {"message": {
                "messageId": str(uuid.uuid4()), "role": "user",
                "parts": [{"kind": "text", "text": "What recipes do you have in Google Drive?"}]}}}
            status, body = http("POST", f"{cfg.urls['recipe_agent']}/a2a/app", req, cfg.token, cfg.timeout)
            assert status == 200, f"HTTP {status}"
            assert body.get("jsonrpc") == "2.0" and body.get("id") == rpc_id, "bad JSON-RPC envelope"
            assert "result" in body, f"error={body.get('error')}"
            parts = body["result"].get("status", {}).get("message", {}).get("parts", [])
            data_parts = [p["data"] for p in parts if isinstance(p.get("data"), dict)]
            assert data_parts, "no A2UI data parts in response"
            assert all(d.get("version") == "v0.9" for d in data_parts), "A2UI version must be v0.9"
            return f"state={body['result'].get('status', {}).get('state')}, {len(data_parts)} A2UI parts"
        _()


# --------------------------------------------------------------------------- #
# Suite 2: Tool-execution fidelity (golden cases)
# --------------------------------------------------------------------------- #
# Each case: (service, prompt, expectations). Expectations are checked against the
# A2UI messages returned by POST /api/chat.
GOLDEN_CASES = [
    ("recipe_agent", "What recipes do you have in Google Drive?",
     {"surface": "recipe_catalog_surface", "recipe_count": 14}),
    ("recipe_agent", "Give me the recipe and groceries for Monster Burgers for 6 people",
     {"surface": "grocery_shopping_surface", "recipe": "Monster Burgers", "servings": 6}),
    ("recipe_agent", "I want to make Ghostly Pizza Mummies for 2 people",
     {"surface": "grocery_shopping_surface", "recipe": "Ghostly Pizza Mummies", "servings": 2}),
    ("recipe_agent", "I want to cook Chicken Rice with chicken breast, jasmine rice, garlic, ginger and soy sauce for 4 people",
     {"surface": "grocery_shopping_surface", "servings": 4, "min_groceries": 4}),
    ("recipe_agent", json.dumps({"event": {"name": "get_recipe_groceries",
                                           "context": {"recipeName": "Witch Finger Breadsticks", "servings": 8}}}),
     {"surface": "grocery_shopping_surface", "recipe": "Witch Finger Breadsticks", "servings": 8}),
    ("main_chatbot", "Show me only Desserts",
     {"surface": "recipe_catalog_surface", "category": "Desserts"}),
    ("main_chatbot", "I want to make Spiderweb Brownies for 4 people",
     {"surface": "grocery_shopping_surface", "recipe": "Spiderweb Brownies", "servings": 4}),
]


def verify_case(messages, exp):
    """Raises AssertionError if the A2UI output does not match the expectations."""
    assert messages, "no A2UI messages returned (tool not called?)"
    got = surfaces(messages)
    assert exp["surface"] in got, f"expected surface {exp['surface']}, got {sorted(got)}"
    notes = ["catalog" if exp["surface"] == "recipe_catalog_surface" else "grocery"]

    if "recipe_count" in exp:
        recipes = a2ui_data(messages, "/recipes") or []
        assert len(recipes) == exp["recipe_count"], f"{len(recipes)} recipes, expected {exp['recipe_count']}"
        notes.append(f"{len(recipes)} recipes")
    if "category" in exp:
        recipes = a2ui_data(messages, "/recipes") or []
        cats = {r.get("category") for r in recipes}
        assert recipes and cats == {exp["category"]}, f"categories={cats}"
        notes.append(f"{len(recipes)} {exp['category']}")
    if "recipe" in exp:
        assert exp["recipe"].lower() in json.dumps(messages).lower(), f"recipe '{exp['recipe']}' not in UI"
        notes.append(exp["recipe"])
    if "servings" in exp:
        servings = a2ui_data(messages, "/servings")
        assert servings == exp["servings"], f"servings={servings}, expected {exp['servings']}"
        notes.append(f"servings={servings}")
    if exp["surface"] == "grocery_shopping_surface":
        groceries = a2ui_data(messages, "/groceries") or []
        assert len(groceries) >= exp.get("min_groceries", 1), f"only {len(groceries)} grocery items"
        notes.append(f"{len(groceries)} groceries")
    return ", ".join(notes)


def suite_tool_fidelity(cfg):
    print("\n2. Tool-execution fidelity (golden cases)")
    for i, (svc, prompt, exp) in enumerate(GOLDEN_CASES, 1):
        label = prompt if len(prompt) <= 38 else prompt[:35] + "..."

        @check("tool_fidelity", f"#{i} {svc}: {label}")
        def _(svc=svc, prompt=prompt, exp=exp, i=i):
            last_error = None
            for attempt in range(cfg.retries + 1):  # LLM output can vary; allow retries
                status, body = http("POST", f"{cfg.urls[svc]}/api/chat",
                                    {"query": prompt, "session_id": f"eval-{i}-{attempt}-{uuid.uuid4().hex[:6]}"},
                                    cfg.token, cfg.timeout)
                try:
                    assert status == 200, f"HTTP {status}"
                    detail = verify_case(body.get("a2ui_messages", []), exp)
                    return detail + (f" (attempt {attempt + 1})" if attempt else "")
                except AssertionError as e:
                    last_error = e
            raise last_error
        _()


# --------------------------------------------------------------------------- #
# Suite 3: System responsiveness under simulated traffic
# --------------------------------------------------------------------------- #
LOAD_PAYLOADS = [
    ["2 english muffins", "4 strips bacon", "1 cup cheddar cheese"],
    ["1 lb minced beef", "brioche burger buns", "tomato ketchup", "dill pickles"],
    ["2 cups plain flour", "1 cup fine sugar", "3 eggs", "unsalted butter"],
    ["jasmine rice", "chicken breast", "fresh garlic", "fresh ginger", "soy sauce"],
    ["dragon fruit jam", "truffle salt"],  # exercises the search-fallback path
]


def suite_responsiveness(cfg):
    print(f"\n3. System responsiveness ({cfg.requests} requests to /products/match, concurrency {cfg.concurrency})")
    url = f"{cfg.urls['grocery_db_service']}/products/match"

    def one(i):
        start = time.perf_counter()
        status, _ = http("POST", url, {"ingredients": LOAD_PAYLOADS[i % len(LOAD_PAYLOADS)]}, cfg.token, 30)
        return status == 200, (time.perf_counter() - start) * 1000

    @check("responsiveness", "Simulated traffic on POST /products/match")
    def _():
        wall = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(cfg.concurrency) as pool:
            outcomes = list(pool.map(one, range(cfg.requests)))
        wall = time.perf_counter() - wall
        lat = sorted(ms for ok, ms in outcomes if ok)
        errors = sum(1 for ok, _ in outcomes if not ok)
        error_rate = errors / len(outcomes) * 100
        assert lat, "all requests failed"
        p50 = statistics.median(lat)
        p95 = statistics.quantiles(lat, n=20)[18] if len(lat) >= 2 else lat[0]
        cfg.load_metrics = {"requests": len(outcomes), "errors": errors, "error_rate_pct": round(error_rate, 2),
                            "rps": round(len(outcomes) / wall, 1), "p50_ms": round(p50, 1),
                            "p95_ms": round(p95, 1), "max_ms": round(lat[-1], 1)}
        summary = (f"RPS={cfg.load_metrics['rps']} p50={p50:.0f}ms p95={p95:.0f}ms "
                   f"max={lat[-1]:.0f}ms errors={error_rate:.1f}%")
        assert error_rate <= cfg.max_error_pct, f"error rate {error_rate:.1f}% > {cfg.max_error_pct}% ({summary})"
        assert p95 <= cfg.p95_ms, f"p95 {p95:.0f}ms > {cfg.p95_ms:.0f}ms ({summary})"
        return summary
    _()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--grocery-url", default=os.getenv("GROCERY_DB_SERVICE_URL", "http://localhost:8001"))
    p.add_argument("--recipe-url", default=os.getenv("RECIPE_AGENT_URL", "http://localhost:8002"))
    p.add_argument("--chatbot-url", default=os.getenv("MAIN_CHATBOT_URL", "http://localhost:8000"))
    p.add_argument("--id-token", default=os.getenv("ID_TOKEN"), help="Bearer token for private Cloud Run services")
    p.add_argument("--skip-agents", action="store_true", help="Skip checks that call the LLM agents")
    p.add_argument("--retries", type=int, default=1, help="Retries per golden case (default: 1)")
    p.add_argument("--timeout", type=float, default=90, help="Per-request timeout for agent calls (s)")
    p.add_argument("--requests", type=int, default=100, help="Load test request count (default: 100)")
    p.add_argument("--concurrency", type=int, default=10, help="Load test concurrency (default: 10)")
    p.add_argument("--p95-ms", type=float, default=1000, help="Max p95 latency for load test (default: 1000)")
    p.add_argument("--max-error-pct", type=float, default=5, help="Max load test error rate %% (default: 5)")
    p.add_argument("--json-out", help="Write results to this JSON file")
    cfg = p.parse_args()
    cfg.token = cfg.id_token
    cfg.load_metrics = None
    cfg.urls = {"grocery_db_service": cfg.grocery_url.rstrip("/"),
                "recipe_agent": cfg.recipe_url.rstrip("/"),
                "main_chatbot": cfg.chatbot_url.rstrip("/")}

    print("Evaluation targets:")
    unreachable = []
    for name, url in cfg.urls.items():
        status, _ = http("GET", f"{url}/health", token=cfg.token, timeout=10)
        state = "ok" if status == 200 else (f"HTTP {status}" if status else "unreachable")
        print(f"  {name:<20} {url}  ({state})")
        if status != 200:
            unreachable.append(name)
            if status in (401, 403):
                print("    -> service is private: set ID_TOKEN=$(gcloud auth print-identity-token)")
    if unreachable:
        sys.exit(f"\nNot healthy: {', '.join(unreachable)}. Start the services (see README) or pass --*-url flags.")

    suite_payload_integrity(cfg)
    if not cfg.skip_agents:
        suite_tool_fidelity(cfg)
    suite_responsiveness(cfg)

    failed = [r for r in RESULTS if not r["passed"]]
    print(f"\nSummary: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for r in failed:
        print(f"  FAILED [{r['suite']}] {r['name']}: {r['detail']}")

    if cfg.json_out:
        with open(cfg.json_out, "w", encoding="utf-8") as f:
            json.dump({"targets": cfg.urls, "passed": not failed, "results": RESULTS,
                       "load_metrics": cfg.load_metrics}, f, indent=2)
        print(f"Results written to {cfg.json_out}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
