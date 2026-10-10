from typing import List, Dict, Any, Optional

GE_COMPOSITE_CATALOG_ID = (
    "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"
)


CATEGORIES_CONFIG = [
    ("All", "All Categories"),
    ("Appetisers", "Appetisers"),
    ("Mains", "Mains"),
    ("Desserts", "Desserts"),
]


def build_recipe_catalog_a2ui(
    recipes: List[Dict[str, Any]],
    selected_category: str = "All",
    expanded_recipe_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Builds a valid A2UI v0.9 JSON message list for the Halloween Recipe Collection with Category Filter Bar."""
    norm_selected = (selected_category or "All").strip()
    if norm_selected.lower() in ("all", "all categories", "all recipes", "all dishes", ""):
        norm_selected = "All"

    filter_btn_ids: List[str] = []
    filter_components: List[Dict[str, Any]] = []

    for idx, (cat_key, cat_label) in enumerate(CATEGORIES_CONFIG):
        is_active = (
            norm_selected.lower() == cat_key.lower()
            or (cat_key != "All" and norm_selected.lower() in cat_key.lower())
        )
        btn_id = f"cat-filter-btn-{idx}"
        filter_btn_ids.append(btn_id)

        prompt_txt = (
            "Show me all dishes in the recipe collection across all categories"
            if cat_key == "All"
            else f"Filter recipe collection to show only {cat_key} recipes"
        )

        filter_components.append(
            {
                "id": btn_id,
                "component": "MaterialButton",
                "label": cat_label,
                "variant": "flat" if is_active else "outlined",
                "appearance": "filled" if is_active else "outlined",
                "color": "primary",
                "style": {
                    "height": "auto",
                    "minHeight": "38px",
                    "backgroundColor": "#1d56db" if is_active else "#f8fafc",
                    "color": "#ffffff" if is_active else "#475569",
                    "border": "1px solid #1d56db" if is_active else "1px solid #e2e8f0",
                    "borderRadius": "8px",
                    "padding": "8px 18px",
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "lineHeight": "1.4",
                    "whiteSpace": "nowrap",
                    "textAlign": "center",
                },
                "action": {
                    "event": {
                        "name": "filter_recipes_by_category",
                        "context": {
                            "category": cat_key,
                            "prompt": prompt_txt,
                        },
                    }
                },
            }
        )

    count_badge_text = (
        f"{len(recipes)} Dishes — {norm_selected}"
        if norm_selected != "All"
        else f"{len(recipes)} Dishes Across 3 Categories"
    )

    components: List[Dict[str, Any]] = [
        {
            "id": "root",
            "component": "Column",
            "children": [
                "recipe-header-card",
                "recipe-list",
            ],
        },
        {
            "id": "recipe-header-card",
            "component": "MaterialCard",
            "appearance": "outlined",
            "style": {
                "backgroundColor": "#ffffff",
                "borderRadius": "16px",
                "border": "1px solid #e5e7eb",
                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.04)",
                "padding": "20px 24px",
                "marginBottom": "16px",
            },
            "children": ["recipe-header-col"],
        },
        {
            "id": "recipe-header-col",
            "component": "MaterialColumn",
            "style": {
                "gap": "16px",
                "width": "100%",
                "boxSizing": "border-box",
            },
            "children": [
                "recipe-title-row",
                "filter-bar-section",
            ],
        },
        {
            "id": "recipe-title-row",
            "component": "MaterialRow",
            "justify": "spaceBetween",
            "align": "center",
            "style": {
                "width": "100%",
                "justifyContent": "space-between",
                "alignItems": "center",
                "gap": "12px",
                "flexWrap": "wrap",
            },
            "children": ["recipe-title-left", "recipe-count-pill"],
        },
        {
            "id": "recipe-title-left",
            "component": "MaterialRow",
            "align": "center",
            "style": {
                "gap": "10px",
                "alignItems": "center",
            },
            "children": ["recipe-title-icon", "recipe-title"],
        },
        {
            "id": "recipe-title-icon",
            "component": "MaterialIcon",
            "icon": "restaurant_menu",
            "style": {
                "color": "#1d56db",
                "fontSize": "24px",
            },
        },
        {
            "id": "recipe-title",
            "component": "MaterialText",
            "usageHint": "h2",
            "text": "Halloween Recipe Collection",
            "style": {
                "fontSize": "22px",
                "fontWeight": "600",
                "color": "#1e293b",
                "margin": "0",
            },
        },
        {
            "id": "recipe-count-pill",
            "component": "MaterialColumn",
            "align": "center",
            "justify": "center",
            "style": {
                "backgroundColor": "#f0f5ff",
                "border": "1px solid #d6e4ff",
                "borderRadius": "8px",
                "padding": "6px 18px",
                "alignItems": "center",
                "justifyContent": "center",
            },
            "children": ["recipe-count-txt"],
        },
        {
            "id": "recipe-count-txt",
            "component": "MaterialText",
            "text": count_badge_text,
            "style": {
                "fontSize": "13px",
                "fontWeight": "500",
                "color": "#2563eb",
                "margin": "0",
            },
        },
        {
            "id": "filter-bar-section",
            "component": "MaterialColumn",
            "style": {
                "gap": "10px",
                "width": "100%",
            },
            "children": [
                "filter-bar-hdr-row",
                "category-filter-row",
            ],
        },
        {
            "id": "filter-bar-hdr-row",
            "component": "MaterialRow",
            "align": "center",
            "style": {
                "gap": "8px",
                "alignItems": "center",
            },
            "children": ["filter-bar-icon", "filter-bar-label"],
        },
        {
            "id": "filter-bar-icon",
            "component": "MaterialIcon",
            "icon": "filter_list",
            "style": {
                "color": "#64748b",
                "fontSize": "18px",
            },
        },
        {
            "id": "filter-bar-label",
            "component": "MaterialText",
            "text": f"Filter by Recipe Category (Active: {norm_selected})",
            "style": {
                "fontSize": "13px",
                "fontWeight": "500",
                "color": "#475569",
                "margin": "0",
            },
        },
        {
            "id": "category-filter-row",
            "component": "MaterialRow",
            "align": "center",
            "style": {
                "gap": "10px",
                "alignItems": "center",
                "flexWrap": "wrap",
                "width": "100%",
            },
            "children": filter_btn_ids,
        },
    ]
    components.extend(filter_components)

    card_ids: List[str] = []
    items_data: List[Dict[str, Any]] = []

    for idx, r in enumerate(recipes):
        rid = r.get("id", str(idx))
        name = r.get("name", f"Recipe {idx + 1}")
        category_name = r.get("category", "Appetisers")
        doc_url = r.get("doc_url", "https://drive.google.com")
        img_url = _get_recipe_hero_image(name, category_name)

        key_ings = r.get("key_ingredients", [])
        if not key_ings:
            lines = [line.strip() for line in r.get("content", "").splitlines() if line.strip()]
            key_ings = [lines[1]] if len(lines) > 1 else [r.get("category", "Halloween Special")]

        ings_text = ", ".join(key_ings)

        items_data.append({
            "id": rid,
            "name": name,
            "category": category_name,
            "ingredients": key_ings,
            "subtitle": f"Ingredients: {ings_text}",
            "docUrl": doc_url,
            "imageUrl": img_url,
        })

        cid = f"recipe-card-{idx}"
        card_ids.append(cid)

        col_children = [
            f"recipe-title-row-{idx}",
            f"recipe-badges-row-{idx}",
            f"recipe-panel-{idx}",
            f"recipe-actions-row-{idx}",
        ]

        card_components = [
            {
                "id": cid,
                "component": "MaterialCard",
                "appearance": "outlined",
                "style": {
                    "backgroundColor": "#ffffff",
                    "borderRadius": "16px",
                    "border": "1px solid #e5e7eb",
                    "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.04)",
                    "padding": "20px",
                    "marginBottom": "16px",
                },
                "children": [f"recipe-row-{idx}"],
            },
            {
                "id": f"recipe-row-{idx}",
                "component": "MaterialRow",
                "align": "stretch",
                "style": {
                    "gap": "24px",
                    "alignItems": "stretch",
                    "width": "100%",
                    "boxSizing": "border-box",
                },
                "children": [f"recipe-img-wrap-{idx}", f"recipe-col-{idx}"],
            },
            {
                "id": f"recipe-img-wrap-{idx}",
                "component": "MaterialColumn",
                "style": {
                    "width": "235px",
                    "minWidth": "235px",
                    "maxWidth": "235px",
                    "borderRadius": "12px",
                    "overflow": "hidden",
                    "flexShrink": "0",
                    "boxSizing": "border-box",
                },
                "children": [f"recipe-img-{idx}"],
            },
            {
                "id": f"recipe-img-{idx}",
                "component": "Image",
                "variant": "mediumFeature",
                "fit": "cover",
                "url": img_url,
                "description": name,
            },
            {
                "id": f"recipe-col-{idx}",
                "component": "MaterialColumn",
                "weight": 1,
                "justify": "spaceBetween",
                "style": {
                    "flex": "1",
                    "minWidth": "0",
                    "paddingLeft": "8px",
                    "boxSizing": "border-box",
                    "gap": "12px",
                    "justifyContent": "space-between",
                },
                "children": col_children,
            },
            {
                "id": f"recipe-title-row-{idx}",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "width": "100%",
                    "alignItems": "center",
                },
                "children": [f"recipe-name-{idx}"],
            },
            {
                "id": f"recipe-name-{idx}",
                "component": "MaterialText",
                "usageHint": "h2",
                "text": name,
                "style": {
                    "fontSize": "22px",
                    "fontWeight": "600",
                    "color": "#1e293b",
                    "margin": "0",
                },
            },
            {
                "id": f"recipe-badges-row-{idx}",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "8px",
                    "alignItems": "center",
                    "flexWrap": "wrap",
                },
                "children": [f"recipe-cat-badge-{idx}"],
            },
            {
                "id": f"recipe-cat-badge-{idx}",
                "component": "MaterialColumn",
                "style": {
                    "backgroundColor": "#f1f5f9",
                    "borderRadius": "6px",
                    "padding": "4px 12px",
                },
                "children": [f"recipe-cat-badge-txt-{idx}"],
            },
            {
                "id": f"recipe-cat-badge-txt-{idx}",
                "component": "MaterialText",
                "text": category_name,
                "style": {
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "color": "#334155",
                    "margin": "0",
                },
            },
            {
                "id": f"recipe-panel-{idx}",
                "component": "MaterialExpansionPanel",
                "title": "View ingredients",
                "expanded": False,
                "children": [f"recipe-panel-txt-{idx}"],
                "style": {
                    "backgroundColor": "#f8fafc",
                    "borderRadius": "8px",
                    "border": "1px solid #e2e8f0",
                    "marginTop": "4px",
                    "marginBottom": "4px",
                },
            },
            {
                "id": f"recipe-panel-txt-{idx}",
                "component": "MaterialText",
                "text": ings_text,
                "style": {
                    "fontSize": "13px",
                    "color": "#334155",
                    "lineHeight": "1.5",
                    "margin": "0",
                    "padding": "6px 10px",
                },
            },
        ]

        card_components.extend([
            {
                "id": f"recipe-actions-row-{idx}",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "12px",
                    "flexWrap": "wrap",
                    "marginTop": "8px",
                },
                "children": [f"recipe-btn-doc-{idx}", f"recipe-btn-groceries-{idx}"],
            },
            {
                "id": f"recipe-btn-doc-{idx}",
                "component": "MaterialButton",
                "label": "📄 View Recipe Doc",
                "variant": "outlined",
                "appearance": "outlined",
                "style": {
                    "borderRadius": "8px",
                    "padding": "8px 16px",
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "color": "#475569",
                    "border": "1px solid #cbd5e1",
                    "backgroundColor": "#ffffff",
                },
                "action": {
                    "functionCall": {
                        "call": "openUrl",
                        "args": {"url": doc_url},
                        "returnType": "void",
                    }
                },
            },
            {
                "id": f"recipe-btn-groceries-{idx}",
                "component": "MaterialButton",
                "label": "🛒 Get Groceries & Full Recipe",
                "variant": "flat",
                "appearance": "filled",
                "color": "primary",
                "style": {
                    "backgroundColor": "#1d56db",
                    "color": "#ffffff",
                    "borderRadius": "8px",
                    "padding": "8px 18px",
                    "fontSize": "13px",
                    "fontWeight": "500",
                },
                "action": {
                    "event": {
                        "name": "get_recipe_groceries",
                        "context": {
                            "recipeName": name,
                            "prompt": f"Please show me the FreshMarket groceries and full recipe for {name}",
                        },
                    }
                },
            },
        ])

        components.extend(card_components)

    components.append({
        "id": "recipe-list",
        "component": "List",
        "direction": "vertical",
        "children": card_ids,
    })

    return [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": "recipe_catalog_surface",
                "catalogId": GE_COMPOSITE_CATALOG_ID,
            },
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "recipe_catalog_surface",
                "components": components,
            },
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "recipe_catalog_surface",
                "path": "/recipes",
                "value": items_data,
            },
        },
    ]


def build_grocery_shopping_a2ui(
    recipe_title: str,
    total_sgd: float,
    matched_items: List[Dict[str, Any]],
    doc_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Builds a valid A2UI v0.9 JSON message list for FreshMarket Grocery Shopping Cards."""
    grocery_items = []
    card_ids = []

    header_children = ["grocery-title", "grocery-summary"]
    if doc_url:
        header_children.append("doc-link-btn")

    components: List[Dict[str, Any]] = [
        {
            "id": "root",
            "component": "Column",
            "children": ["header-card", "grocery-list"],
        },
        {
            "id": "header-card",
            "component": "Card",
            "child": "header-col",
        },
        {
            "id": "header-col",
            "component": "Column",
            "children": header_children,
        },
        {
            "id": "grocery-title",
            "component": "Text",
            "variant": "h1",
            "text": f"🛒 FreshMarket Groceries for: {recipe_title}",
        },
        {
            "id": "grocery-summary",
            "component": "Text",
            "text": (
                f"Found {len(matched_items)} ingredients available on FreshMarket • "
                f"Estimated Basket Total: SGD ${total_sgd:.2f}"
            ),
        },
    ]

    if doc_url:
        components.extend([
            {
                "id": "doc-link-btn",
                "component": "Button",
                "variant": "default",
                "child": "doc-link-txt",
                "action": {
                    "functionCall": {
                        "call": "openUrl",
                        "args": {"url": doc_url},
                        "returnType": "void",
                    }
                },
            },
            {
                "id": "doc-link-txt",
                "component": "Text",
                "text": "📄 Open Original Recipe Google Doc",
            },
        ])

    for idx, item in enumerate(matched_items):
        prod = item["matched_product"]
        price = prod.get("promo_price_sgd") or prod.get("price_sgd", 0.0)
        promo_badge = (
            f" (FreshMarket Promo! Was ${prod['price_sgd']:.2f})"
            if prod.get("promo_price_sgd")
            else ""
        )
        dietary = f" • {prod['dietary_tags']}" if prod.get("dietary_tags") else ""

        prod_name = prod.get("product_name", f"Ingredient {idx + 1}")
        brand_pack = f"🏷️ Brand: {prod.get('brand', 'FreshMarket')} • Pack Size: {prod.get('pack_size', 'Standard')}{dietary}"
        rec_need = f"📌 Recipe Need: {item.get('recipe_ingredient', prod_name)}"
        price_disp = f"💰 SGD ${price:.2f}{promo_badge}"
        img_url = prod.get(
            "image_url",
            "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&auto=format&fit=crop&q=80",
        )
        prod_url = prod.get("product_url", "https://groceries.example.com")

        grocery_items.append({
            "productName": prod_name,
            "brandAndPack": brand_pack,
            "recipeIngredient": rec_need,
            "priceDisplay": price_disp,
            "imageUrl": img_url,
            "productUrl": prod_url,
        })

        cid = f"grocery-card-{idx}"
        card_ids.append(cid)

        components.extend([
            {
                "id": cid,
                "component": "Card",
                "child": f"grocery-row-{idx}",
            },
            {
                "id": f"grocery-row-{idx}",
                "component": "Row",
                "children": [f"grocery-img-{idx}", f"grocery-col-{idx}"],
            },
            {
                "id": f"grocery-img-{idx}",
                "component": "Image",
                "variant": "mediumFeature",
                "weight": 1,
                "url": img_url,
            },
            {
                "id": f"grocery-col-{idx}",
                "component": "Column",
                "weight": 2,
                "children": [
                    f"prod-name-{idx}",
                    f"prod-recipe-{idx}",
                    f"prod-brand-{idx}",
                    f"prod-price-{idx}",
                    f"buy-btn-{idx}",
                ],
            },
            {
                "id": f"prod-name-{idx}",
                "component": "Text",
                "variant": "h3",
                "text": prod_name,
            },
            {
                "id": f"prod-recipe-{idx}",
                "component": "Text",
                "text": rec_need,
            },
            {
                "id": f"prod-brand-{idx}",
                "component": "Text",
                "text": brand_pack,
            },
            {
                "id": f"prod-price-{idx}",
                "component": "Text",
                "variant": "h3",
                "text": price_disp,
            },
            {
                "id": f"buy-btn-{idx}",
                "component": "Button",
                "variant": "primary",
                "child": f"buy-btn-label-{idx}",
                "action": {
                    "functionCall": {
                        "call": "openUrl",
                        "args": {"url": prod_url},
                        "returnType": "void",
                    }
                },
            },
            {
                "id": f"buy-btn-label-{idx}",
                "component": "Text",
                "text": "🛒 Buy on FreshMarket",
            },
        ])

    components.append({
        "id": "grocery-list",
        "component": "List",
        "direction": "vertical",
        "children": card_ids,
    })

    return [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": "grocery_shopping_surface",
                "catalogId": GE_COMPOSITE_CATALOG_ID,
            },
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "grocery_shopping_surface",
                "components": components,
            },
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "grocery_shopping_surface",
                "path": "/groceries",
                "value": grocery_items,
            },
        },
    ]


def _get_recipe_hero_image(name: str, category: str) -> str:
    name_l = name.lower()
    if "pizza" in name_l:
        return "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&auto=format&fit=crop&q=80"
    if "pepper" in name_l:
        return "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=400&auto=format&fit=crop&q=80"
    if "jalapeno" in name_l or "popper" in name_l:
        return "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=400&auto=format&fit=crop&q=80"
    if "egg" in name_l:
        return "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400&auto=format&fit=crop&q=80"
    if "breadstick" in name_l:
        return "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&auto=format&fit=crop&q=80"
    if "cake" in name_l or "velvet" in name_l:
        return "https://images.unsplash.com/photo-1586788680434-30d324b2d46f?w=400&auto=format&fit=crop&q=80"
    if "cupcake" in name_l:
        return "https://images.unsplash.com/photo-1576618148400-f54bed99fcfd?w=400&auto=format&fit=crop&q=80"
    if "brownie" in name_l:
        return "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=400&auto=format&fit=crop&q=80"
    if "cookie" in name_l:
        return "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=400&auto=format&fit=crop&q=80"
    if "pasta" in name_l or "spaghetti" in name_l:
        return "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=400&auto=format&fit=crop&q=80"
    if "burger" in name_l:
        return "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&auto=format&fit=crop&q=80"
    if "meatloaf" in name_l:
        return "https://images.unsplash.com/photo-1544025162-d76694265947?w=400&auto=format&fit=crop&q=80"
    if "stew" in name_l:
        return "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&auto=format&fit=crop&q=80"
    return "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&auto=format&fit=crop&q=80"
