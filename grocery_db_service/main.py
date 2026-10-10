import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import os
import re
import sqlite3
import urllib.parse
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from seed_db import seed, DB_PATH

# Ensure DB exists on startup
if not os.path.exists(DB_PATH):
    seed()

app = FastAPI(
    title="FreshMarket Grocery Database API",
    description="Standalone microservice providing FreshMarket grocery products, SGD pricing, images, and direct buy URLs.",
    version="1.0.0",
)


class ProductRecord(BaseModel):
    sku: str
    product_name: str
    brand: str
    ingredient_category: str
    search_keywords: str
    pack_size: str
    price_sgd: float
    promo_price_sgd: Optional[float] = None
    unit_price_display: Optional[str] = None
    dietary_tags: Optional[str] = None
    in_stock: bool
    image_url: str
    product_url: str


class IngredientMatchRequest(BaseModel):
    ingredients: List[str]


class MatchedIngredientItem(BaseModel):
    recipe_ingredient: str
    matched_product: ProductRecord
    match_confidence: str


class IngredientMatchResponse(BaseModel):
    results: List[MatchedIngredientItem]
    total_estimated_sgd: float


def get_all_products() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM grocery_products")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    for r in rows:
        r["in_stock"] = bool(r["in_stock"])
    return rows


STOPWORDS = {
    "cup", "cups", "tsp", "tbsp", "teaspoon", "teaspoons", "tablespoon", "tablespoons",
    "oz", "lb", "lbs", "pound", "pounds", "g", "kg", "ml", "l", "pinch", "small", "medium",
    "large", "can", "jar", "tube", "packet", "pack", "strips", "slices", "sliced", "diced",
    "minced", "chopped", "finely", "fresh", "freshly", "room", "temperature", "softened",
    "melted", "optional", "to", "taste", "or", "and", "with", "for", "of", "in", "into",
    "half", "rounds", "peeled", "rinsed", "drained", "lightly", "beaten", "sifted", "warm"
}


def clean_ingredient_text(raw: str) -> str:
    # Remove quantities like 1/2, 2 1/2, numbers, parentheses
    text = re.sub(r"\([^)]*\)", " ", raw.lower())
    text = re.sub(r"[^a-zA-Z\s-]", " ", text)
    tokens = [t for t in text.split() if t not in STOPWORDS and len(t) > 1]
    return " ".join(tokens).strip() or raw.strip()


def match_single_ingredient(raw_ing: str, products: List[Dict[str, Any]]) -> MatchedIngredientItem:
    raw_lower = raw_ing.lower()
    cleaned = clean_ingredient_text(raw_ing)
    cleaned_tokens = set(cleaned.split())

    best_prod = None
    best_score = 0.0

    for prod in products:
        score = 0.0
        kw_list = [k.strip().lower() for k in prod["search_keywords"].split(",") if k.strip()]
        for kw in kw_list:
            # Check phrase match
            if kw in raw_lower or kw in cleaned:
                # Longer phrase matches get a strong boost
                score = max(score, 10.0 + len(kw.split()) * 5.0)
            else:
                kw_tokens = set(kw.split())
                overlap = len(cleaned_tokens.intersection(kw_tokens))
                if overlap > 0:
                    score = max(score, overlap * 3.0)

        # Also check product name tokens
        prod_name_tokens = set(re.sub(r"[^a-zA-Z\s]", " ", prod["product_name"].lower()).split())
        overlap_name = len(cleaned_tokens.intersection(prod_name_tokens))
        score += overlap_name * 1.5

        if score > best_score:
            best_score = score
            best_prod = prod

    if best_prod and best_score >= 3.0:
        return MatchedIngredientItem(
            recipe_ingredient=raw_ing,
            matched_product=ProductRecord(**best_prod),
            match_confidence="high" if best_score >= 10.0 else "medium",
        )

    # Fallback: dynamic FreshMarket Search product for any custom recipe ingredient
    display_title = cleaned.title() if cleaned else raw_ing.title()
    encoded_query = urllib.parse.quote(cleaned or raw_ing)
    fallback_prod = ProductRecord(
        sku=f"GROC-CUSTOM-{abs(hash(cleaned)) % 10000:04d}",
        product_name=f"FreshMarket Selected {display_title}",
        brand="FreshMarket",
        ingredient_category="Grocery & Pantry",
        search_keywords=cleaned,
        pack_size="Standard Retail Pack",
        price_sgd=4.50,
        promo_price_sgd=3.95,
        unit_price_display="FreshMarket Online",
        dietary_tags="Available Online",
        in_stock=True,
        image_url="https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&auto=format&fit=crop&q=80",
        product_url=f"https://groceries.example.com/search?query={encoded_query}",
    )
    return MatchedIngredientItem(
        recipe_ingredient=raw_ing,
        matched_product=fallback_prod,
        match_confidence="search_fallback",
    )


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "grocery-db-service"}


@app.get("/products", response_model=List[ProductRecord])
def list_products(category: Optional[str] = Query(None), q: Optional[str] = Query(None)):
    products = get_all_products()
    if category:
        products = [p for p in products if category.lower() in p["ingredient_category"].lower()]
    if q:
        q_lower = q.lower()
        products = [
            p for p in products
            if q_lower in p["product_name"].lower()
            or q_lower in p["search_keywords"].lower()
            or q_lower in p["brand"].lower()
        ]
    return products


@app.post("/products/match", response_model=IngredientMatchResponse)
def match_ingredients(req: IngredientMatchRequest):
    products = get_all_products()
    results = []
    seen_skus = set()
    total_sgd = 0.0

    for raw_ing in req.ingredients:
        if not raw_ing or not raw_ing.strip():
            continue
        matched = match_single_ingredient(raw_ing.strip(), products)
        results.append(matched)
        sku = matched.matched_product.sku
        if sku not in seen_skus:
            seen_skus.add(sku)
            effective_price = matched.matched_product.promo_price_sgd or matched.matched_product.price_sgd
            total_sgd += effective_price

    return IngredientMatchResponse(
        results=results,
        total_estimated_sgd=round(total_sgd, 2),
    )
