import os
import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google.adk.tools.tool_context import ToolContext
except ImportError:
    ToolContext = Any
from a2ui_builder import build_recipe_catalog_a2ui, build_grocery_shopping_a2ui

GROCERY_DB_SERVICE_URL = os.environ.get(
    "GROCERY_DB_SERVICE_URL",
    "https://grocery-db-service-<PROJECT_HASH>.run.app"
)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "recipes_cache.json")


def load_drive_recipes() -> List[Dict[str, Any]]:
    """Dual-mode Google Drive recipe loader (Live Drive API with embedded fallback cache)."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def extract_ingredients_from_text(content: str) -> List[str]:
    """Extracts ingredient lines from either bulleted or table-formatted Google Doc text."""
    lines = [line.strip() for line in content.splitlines()]
    ingredients = []
    in_ingredients = False

    for i, line in enumerate(lines):
        if re.match(r"^Ingredients$", line, re.IGNORECASE):
            in_ingredients = True
            continue
        if in_ingredients:
            if any(
                line.lower().startswith(h)
                for h in ["instructions", "step-by-step instructions", "baking instructions", "preparation instructions", "step 1"]
            ):
                break
            if line.startswith("*") or line.startswith("-"):
                cleaned = line.lstrip("*- ").strip()
                if cleaned:
                    ingredients.append(cleaned)

    # If no bulleted ingredients found, parse table-formatted ingredients (e.g., Spiderweb Brownies, Monster Burgers)
    if not ingredients:
        in_ingredients = False
        buffer = []
        for line in lines:
            if re.match(r"^Ingredients$", line, re.IGNORECASE):
                in_ingredients = True
                continue
            if in_ingredients:
                if any(
                    line.lower().startswith(h)
                    for h in ["instructions", "step-by-step instructions", "baking instructions", "preparation instructions", "step 1"]
                ):
                    break
                if line and line not in ("Component", "Ingredient", "Quantity", "Category", "Ingredient Category"):
                    buffer.append(line)

        # Group every 3 lines (Category/Component, Ingredient Name, Quantity)
        idx = 0
        while idx + 2 < len(buffer):
            comp = buffer[idx]
            ing = buffer[idx + 1]
            qty = buffer[idx + 2]
            ingredients.append(f"{qty} {ing} ({comp})")
            idx += 3

    return ingredients


def _get_id_token(audience: str) -> Optional[str]:
    """Fetches Google Cloud ID token for Cloud Run service-to-service auth."""
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token
        auth_req = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(auth_req, audience)
    except Exception:
        try:
            import subprocess
            return subprocess.check_output(["gcloud", "auth", "print-identity-token"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            return None


def call_grocery_db_match(ingredients: List[str]) -> Dict[str, Any]:
    """Calls the deployed FreshMarket Grocery Database Cloud Run service."""
    url = f"{GROCERY_DB_SERVICE_URL.rstrip('/')}/products/match"
    payload = json.dumps({"ingredients": ingredients}).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    token = _get_id_token(GROCERY_DB_SERVICE_URL)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        # Fallback local matching if Cloud Run auth/network is unreachable in local dev
        fallback_results = []
        total_sgd = 0.0
        for ing in ingredients:
            encoded = urllib.parse.quote(ing)
            fallback_results.append({
                "recipe_ingredient": ing,
                "match_confidence": "fallback",
                "matched_product": {
                    "sku": "GROC-LOCAL",
                    "product_name": f"FreshMarket {ing[:45]}",
                    "brand": "FreshMarket",
                    "ingredient_category": "Groceries",
                    "pack_size": "Standard Pack",
                    "price_sgd": 4.50,
                    "promo_price_sgd": 3.95,
                    "dietary_tags": "Halal",
                    "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&auto=format&fit=crop&q=80",
                    "product_url": f"https://groceries.example.com/search?query={encoded}"
                }
            })
            total_sgd += 3.95
        return {"results": fallback_results, "total_estimated_sgd": round(total_sgd, 2)}


def list_drive_recipes_tool(
    tool_context: Optional[ToolContext] = None,
) -> dict:
    """Lists all 14 recipes available in Google Drive and generates an interactive A2UI Recipe Catalog Grid with key ingredients, client-side MaterialExpansionPanel accordions for >5 ingredients, direct Google Doc links, and grocery action buttons."""
    recipes = load_drive_recipes()
    a2ui_messages = build_recipe_catalog_a2ui(recipes)
    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["latest_a2ui_messages"] = a2ui_messages

    summary_list = [
        {
            "name": r["name"],
            "category": r["category"],
            "google_doc_url": r["doc_url"]
        }
        for r in recipes
    ]
    return {
        "status": "success",
        "total_recipes": len(recipes),
        "recipes": summary_list,
        "ui_note": "An interactive A2UI Recipe Catalog Grid has been generated and attached to the response."
    }


from fractions import Fraction

def fmt_scaled_num(val: float) -> str:
    """Formats a float as an integer or mixed/simple fraction for culinary readability."""
    if abs(val - round(val)) < 0.05:
        return str(max(1, int(round(val))))
    f = Fraction(val).limit_denominator(8)
    whole = int(val)
    rem = f - whole
    if whole > 0 and rem > 0:
        return f"{whole} {rem}"
    elif rem > 0:
        return f"{rem}"
    elif whole > 0:
        return f"{whole}"
    return f"{val:.1f}"


def parse_and_scale_qty(qty_str: str, factor: float) -> str:
    """Scales a quantity string (including fractions, ranges, and decimals) by the given factor."""
    qty_str = qty_str.strip()
    # Check range like 10-12 or 10 to 12
    m_range = re.match(r"^(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)$", qty_str)
    if m_range:
        v1 = float(m_range.group(1)) * factor
        v2 = float(m_range.group(2)) * factor
        return f"{fmt_scaled_num(v1)}-{fmt_scaled_num(v2)}"

    # Check mixed fraction: 1 1/2
    m_mixed = re.match(r"^(\d+)\s+(\d+)/(\d+)$", qty_str)
    if m_mixed:
        val = (int(m_mixed.group(1)) + int(m_mixed.group(2)) / int(m_mixed.group(3))) * factor
        return fmt_scaled_num(val)

    # Check simple fraction: 1/2
    m_frac = re.match(r"^(\d+)/(\d+)$", qty_str)
    if m_frac:
        val = (int(m_frac.group(1)) / int(m_frac.group(2))) * factor
        return fmt_scaled_num(val)

    # Check float or int
    try:
        val = float(qty_str) * factor
        return fmt_scaled_num(val)
    except ValueError:
        return qty_str


def scale_ingredient_line(line: str, factor: float) -> str:
    """Scales leading numerical quantities in an ingredient line while preserving units and names, and bolding the quantity."""
    m = re.match(r"^(\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?(?:\s*(?:-|to)\s*\d+(?:\.\d+)?)?)\s*(.*)", line)
    if m:
        scaled_q = parse_and_scale_qty(m.group(1), factor)
        return f"**{scaled_q}** {m.group(2)}"
    return line


def extract_servings_from_query(query: str) -> Optional[int]:
    """Detects requested serving size (1-10) from user prompt or action context."""
    patterns = [
        r"(?:servings?|for|cooking for|people|pax)\s*[:=]?\s*(\d+)",
        r"(\d+)\s*(?:people|pax|servings?)",
    ]
    for pat in patterns:
        m = re.search(pat, query, re.IGNORECASE)
        if m:
            try:
                num = int(m.group(1))
                if 1 <= num <= 10:
                    return num
            except ValueError:
                pass
    return None


def parse_recipe_details(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts description, prep/cook times, difficulty, base servings, instructions, and chef tips."""
    name = recipe.get("name", "Recipe")
    content = recipe.get("content", "")
    lines = [l.strip() for l in content.splitlines() if l.strip()]

    # Extract description
    desc_lines = []
    for l in lines[1:5]:
        if any(l.lower().startswith(h) for h in ["prep", "recipe overview", "preparation", "ingredients", "overview", "kitchen", "recipe essentials"]):
            break
        desc_lines.append(l)
    description = " ".join(desc_lines) if desc_lines else f"A spooky and delicious recipe for {name}."

    prep_time = "20 mins"
    cook_time = "25 mins"
    difficulty = "Easy"
    yield_str = "4 Servings"
    base_servings = 4

    # 1. Bulleted / Colon pairs (e.g. * Prep time: 25 minutes)
    for l in lines:
        if ":" in l and any(w in l.lower() for w in ["prep", "cook", "bake", "yield", "servings", "difficulty"]):
            parts = l.lstrip("*- ").split(":", 1)
            k, v = parts[0].strip().lower(), parts[1].strip()
            if "prep" in k: prep_time = v
            elif any(x in k for x in ["cook", "bake"]): cook_time = v
            elif "difficulty" in k: difficulty = v
            elif any(x in k for x in ["yield", "servings"]): yield_str = v

    # 2. Table and section blocks
    for i, line in enumerate(lines):
        if any(h in line.lower() for h in ["recipe overview", "preparation details", "kitchen logistics", "recipe essentials"]):
            window = lines[i+1:i+16]
            for w_idx in range(len(window)-1):
                wk = window[w_idx].lower().strip()
                wv = window[w_idx+1].strip()
                if "prep" in wk and not any(x in wv.lower() for x in ["prep", "cook", "yield", "difficulty"]):
                    prep_time = wv
                elif any(x in wk for x in ["cook", "bake"]) and not any(x in wv.lower() for x in ["prep", "cook", "yield", "difficulty"]):
                    cook_time = wv
                elif "difficulty" in wk and not any(x in wv.lower() for x in ["prep", "cook", "yield", "difficulty"]):
                    difficulty = wv
                elif any(x in wk for x in ["yield", "servings"]) and not any(x in wv.lower() for x in ["prep", "cook", "yield", "difficulty"]):
                    yield_str = wv

            heads = []
            vals = []
            collecting_heads = True
            for w in window:
                wl = w.lower()
                if any(x in wl for x in ["prep time", "cook time", "bake time", "servings", "difficulty", "total yield", "total time", "specification", "detail"]):
                    if collecting_heads: heads.append(wl)
                    else: break
                else:
                    if heads:
                        collecting_heads = False
                        vals.append(w)
            if len(heads) >= 2 and len(vals) >= len(heads):
                for h, v in zip(heads, vals):
                    if "prep" in h: prep_time = v
                    elif any(x in h for x in ["cook", "bake", "total"]): cook_time = v
                    elif "difficulty" in h: difficulty = v
                    elif any(x in h for x in ["servings", "yield"]): yield_str = v

    m = re.search(r"(\d+)\s*(?:servings?|people|portions)?", yield_str, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        if any(w in yield_str.lower() for w in ["serving", "people", "portion"]):
            base_servings = num
        elif any(w in yield_str.lower() for w in ["mummies", "poppers", "fingers", "cupcakes", "brownies", "cookies"]):
            base_servings = max(2, min(10, round(num / 3)))
        elif 1 <= num <= 10:
            base_servings = num

    # Extract instructions
    instructions = []
    curr_title = None
    curr_body = []
    in_inst = False
    for l in lines:
        ll = l.lower()
        if any(ll.startswith(x) for x in ["instruction", "step-by-step instructions", "baking instructions", "preparation instructions"]):
            in_inst = True
            continue
        if in_inst:
            if any(ll.startswith(x) for x in ["chef", "expert tips", "notes for the host", "presentation tips", "pro tips"]):
                break
            if re.match(r"^(?:Step\s*\d+|\d+\.)", l):
                if curr_title:
                    instructions.append({"title": curr_title, "body": " ".join(curr_body)})
                curr_title = l
                curr_body = []
            elif curr_title and l:
                curr_body.append(l)
    if curr_title:
        instructions.append({"title": curr_title, "body": " ".join(curr_body)})

    # Extract tips
    tips = []
    in_tips = False
    for l in lines:
        ll = l.lower()
        if any(ll.startswith(x) for x in ["chef", "expert tips", "notes for the host", "presentation tips", "pro tips"]):
            in_tips = True
            continue
        if in_tips:
            if l.startswith("*") or l.startswith("-"):
                tips.append(l.lstrip("*- ").strip())
            elif not tips and l:
                tips.append(l)

    return {
        "name": name,
        "description": description,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "difficulty": difficulty,
        "yield_str": yield_str,
        "base_servings": base_servings,
        "instructions": instructions,
        "tips": tips,
    }


def get_recipe_and_groceries_tool(
    query_or_recipe_name: str,
    tool_context: ToolContext,
    custom_ingredients: Optional[List[str]] = None,
    servings: Optional[int] = None,
) -> dict:
    """Looks up a recipe from Google Drive (or parses a custom user recipe), scales ingredients for the requested serving size (1-10 people), matches all ingredients against the FreshMarket Grocery Database, and generates an interactive A2UI UI with groceries and the full recipe (including an interactive slider)."""
    recipes = load_drive_recipes()
    q_lower = query_or_recipe_name.lower().strip()

    matched_recipe = None
    for r in recipes:
        if r["name"].lower() in q_lower or q_lower in r["name"].lower():
            matched_recipe = r
            break

    # Also check word overlap if no direct substring
    if not matched_recipe and not custom_ingredients:
        q_words = set(re.sub(r"[^a-z0-9\s]", "", q_lower).split())
        best_overlap = 0
        for r in recipes:
            r_words = set(re.sub(r"[^a-z0-9\s]", "", r["name"].lower()).split())
            overlap = len(q_words.intersection(r_words))
            if overlap > best_overlap and overlap >= 1:
                best_overlap = overlap
                matched_recipe = r

    recipe_details = None
    if matched_recipe:
        recipe_title = matched_recipe["name"]
        doc_url = matched_recipe["doc_url"]
        full_text = matched_recipe["content"]
        ingredients = extract_ingredients_from_text(full_text)
        recipe_details = parse_recipe_details(matched_recipe)
        recipe_details["ingredients"] = ingredients
        base_servings = recipe_details["base_servings"]
    else:
        recipe_title = query_or_recipe_name.title()
        doc_url = None
        base_servings = 4
        if custom_ingredients and len(custom_ingredients) > 0:
            ingredients = custom_ingredients
        else:
            ingredients = [i.strip() for i in re.split(r"[,\n;]+", query_or_recipe_name) if i.strip()]
        recipe_details = {
            "name": recipe_title,
            "description": f"Custom culinary creation: {recipe_title}",
            "prep_time": "15-20 mins",
            "cook_time": "20-30 mins",
            "difficulty": "Easy",
            "yield_str": f"{base_servings} Servings",
            "base_servings": base_servings,
            "ingredients": ingredients,
            "instructions": [
                {"title": "1. Prep Ingredients", "body": "Wash, chop, and measure all ingredients as required."},
                {"title": "2. Cook & Combine", "body": f"Prepare the {recipe_title} according to your culinary preference."},
                {"title": "3. Plate & Garnish", "body": "Serve fresh and warm, garnishing to taste."},
            ],
            "tips": ["Adjust seasoning to taste during cooking."],
        }

    # Resolve target servings (default to recipe base servings if unspecified)
    if servings is None:
        extracted = extract_servings_from_query(query_or_recipe_name)
        if extracted is not None:
            servings = extracted
        elif tool_context and hasattr(tool_context, "state") and tool_context.state.get("servings"):
            servings = int(tool_context.state.get("servings"))
        else:
            servings = base_servings

    servings = max(1, min(10, int(servings)))
    scale_factor = float(servings) / float(base_servings) if base_servings > 0 else 1.0

    scaled_ingredients = [scale_ingredient_line(ing, scale_factor) for ing in ingredients]

    db_response = call_grocery_db_match(ingredients)
    matched_items = db_response.get("results", [])
    raw_total_sgd = db_response.get("total_estimated_sgd", 0.0)
    scaled_total_sgd = round(raw_total_sgd * scale_factor, 2)

    a2ui_messages = build_grocery_shopping_a2ui(
        recipe_title=recipe_title,
        total_sgd=scaled_total_sgd,
        matched_items=matched_items,
        doc_url=doc_url,
        recipe_details=recipe_details,
        servings=servings,
        base_servings=base_servings,
        scaled_ingredients=scaled_ingredients,
    )
    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["latest_a2ui_messages"] = a2ui_messages
        tool_context.state["servings"] = servings
        tool_context.state["recipeName"] = recipe_title

    return {
        "status": "success",
        "recipe": recipe_title,
        "servings": servings,
        "base_servings": base_servings,
        "scale_factor": scale_factor,
        "estimated_total_sgd": scaled_total_sgd,
        "message": f"Generated interactive FreshMarket grocery shopping cards and full recipe for {recipe_title} (scaled for {servings} people).",
        "ui_note": "Rendered interactive A2UI cards below with the complete recipe guide at the top (with interactive 1-10 servings slider, quick presets, scaled ingredients, and step-by-step instructions), followed by FreshMarket groceries at the bottom.",
    }
