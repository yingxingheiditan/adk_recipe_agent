from typing import List, Dict, Any, Optional

GE_COMPOSITE_CATALOG_ID = (
    "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"
)


def build_recipe_catalog_a2ui(
    recipes: List[Dict[str, Any]],
    expanded_recipe_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Builds a valid A2UI v0.9 JSON message list for the Google Drive Recipe Catalog Grid in Gemini Enterprise Material Design."""
    card_ids: List[str] = []
    items_data: List[Dict[str, Any]] = []

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
                "gap": "12px",
                "width": "100%",
                "boxSizing": "border-box",
            },
            "children": [
                "recipe-title-row",
                "recipe-subtitle",
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
            "text": "Google Drive Recipe Collection",
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
            "text": f"{len(recipes)} Dishes Available",
            "style": {
                "fontSize": "13px",
                "fontWeight": "500",
                "color": "#2563eb",
                "margin": "0",
            },
        },
        {
            "id": "recipe-subtitle",
            "component": "MaterialText",
            "text": "Browse recipes from Google Drive. Click 'View Recipe Doc' to open the original Google Doc, or 'Get Groceries & Full Recipe' for scaled ingredients and FreshMarket grocery shopping.",
            "style": {
                "fontSize": "14px",
                "color": "#475569",
                "margin": "0",
                "lineHeight": "1.5",
            },
        },
    ]

    for idx, r in enumerate(recipes):
        rid = r.get("id", str(idx))
        name = r.get("name", f"Recipe {idx + 1}")
        category_name = r.get("category", "Halloween Special")
        doc_url = r.get("doc_url", "https://drive.google.com")
        img_url = _get_recipe_hero_image(name, category_name)

        key_ings = r.get("key_ingredients", [])
        if not key_ings:
            lines = [line.strip() for line in r.get("content", "").splitlines() if line.strip()]
            key_ings = [lines[1]] if len(lines) > 1 else [category_name]

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
        ]

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
    recipe_details: Optional[Dict[str, Any]] = None,
    servings: int = 4,
    base_servings: int = 4,
    scaled_ingredients: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Builds a valid A2UI v0.9 JSON message list for FreshMarket Grocery Shopping Cards and Full Interactive Recipe in Gemini Enterprise Material Design."""
    grocery_items: List[Dict[str, Any]] = []
    card_ids: List[str] = []

    # Format total price display
    if isinstance(total_sgd, (int, float)):
        total_disp = f"SGD ${total_sgd:.2f}"
    else:
        total_disp = str(total_sgd)

    header_col_children = ["grocery-title-row", "grocery-summary-txt"]
    if doc_url and not recipe_details:
        header_col_children.append("doc-link-btn")

    if recipe_details:
        root_children = ["recipe-master-card", "grocery-header-card", "grocery-list"]
    else:
        root_children = ["grocery-header-card", "grocery-list"]

    components: List[Dict[str, Any]] = [
        {
            "id": "root",
            "component": "Column",
            "children": root_children,
        },
        # 1. Header Card
        {
            "id": "grocery-header-card",
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
            "children": ["grocery-header-col"],
        },
        {
            "id": "grocery-header-col",
            "component": "MaterialColumn",
            "style": {
                "gap": "14px",
                "width": "100%",
                "boxSizing": "border-box",
            },
            "children": header_col_children,
        },
        {
            "id": "grocery-title-row",
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
            "children": ["grocery-title-left", "grocery-total-pill"],
        },
        {
            "id": "grocery-title-left",
            "component": "MaterialRow",
            "align": "center",
            "style": {
                "gap": "10px",
                "alignItems": "center",
            },
            "children": ["grocery-title-icon", "grocery-title-txt"],
        },
        {
            "id": "grocery-title-icon",
            "component": "MaterialIcon",
            "icon": "shopping_cart",
            "style": {
                "color": "#1d56db",
                "fontSize": "26px",
            },
        },
        {
            "id": "grocery-title-txt",
            "component": "MaterialText",
            "usageHint": "h2",
            "text": f"FreshMarket Groceries: {recipe_title}",
            "style": {
                "fontSize": "22px",
                "fontWeight": "600",
                "color": "#1e293b",
                "margin": "0",
            },
        },
        {
            "id": "grocery-total-pill",
            "component": "MaterialColumn",
            "align": "center",
            "justify": "center",
            "style": {
                "backgroundColor": "#eff6ff",
                "border": "1px solid #bfdbfe",
                "borderRadius": "8px",
                "padding": "6px 18px",
                "alignItems": "center",
                "justifyContent": "center",
            },
            "children": ["grocery-total-txt"],
        },
        {
            "id": "grocery-total-txt",
            "component": "MaterialText",
            "text": f"Estimated Basket: {total_disp}",
            "style": {
                "fontSize": "14px",
                "fontWeight": "600",
                "color": "#1d56db",
                "margin": "0",
            },
        },
        {
            "id": "grocery-summary-txt",
            "component": "MaterialText",
            "text": f"Found {len(matched_items)} ingredients matched on FreshMarket • Scaled for {servings} people (Base: {base_servings} servings)",
            "style": {
                "fontSize": "14px",
                "color": "#475569",
                "margin": "0",
                "lineHeight": "1.5",
            },
        },
    ]

    if doc_url:
        components.append({
            "id": "doc-link-btn",
            "component": "MaterialButton",
            "label": "📄 Open Original Recipe Google Doc",
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
                "width": "fit-content",
            },
            "action": {
                "functionCall": {
                    "call": "openUrl",
                    "args": {"url": doc_url},
                    "returnType": "void",
                }
            },
        })

    # 2. Individual Grocery Ingredient Cards (Structured Horizontal MaterialCard per item)
    for idx, item in enumerate(matched_items):
        prod = item.get("matched_product") or item
        price = prod.get("promo_price_sgd") or prod.get("price_sgd", 0.0)
        is_promo = bool(prod.get("promo_price_sgd"))
        promo_text = f"FreshMarket Promo! Was ${prod['price_sgd']:.2f}" if is_promo else ""
        dietary = f" • {prod['dietary_tags']}" if prod.get("dietary_tags") else ""

        prod_name = prod.get("product_name", f"Ingredient {idx + 1}")
        brand_pack = f"🏷️ {prod.get('brand', 'FreshMarket')} • {prod.get('pack_size', 'Standard')}{dietary}"
        rec_need = f"📌 Recipe Need: {item.get('recipe_ingredient', prod_name)}"
        img_url = prod.get(
            "image_url",
            "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&auto=format&fit=crop&q=80",
        )
        prod_url = prod.get("product_url", "https://groceries.example.com")

        grocery_items.append({
            "productName": prod_name,
            "brandAndPack": brand_pack,
            "recipeIngredient": rec_need,
            "priceDisplay": f"SGD ${price:.2f}",
            "imageUrl": img_url,
            "productUrl": prod_url,
        })

        cid = f"grocery-card-{idx}"
        card_ids.append(cid)

        # Price row components
        price_row_children = [f"prod-price-{idx}"]
        if is_promo:
            price_row_children.append(f"prod-promo-badge-{idx}")

        item_components = [
            {
                "id": cid,
                "component": "MaterialCard",
                "appearance": "outlined",
                "style": {
                    "backgroundColor": "#ffffff",
                    "borderRadius": "16px",
                    "border": "1px solid #e5e7eb",
                    "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.04)",
                    "padding": "18px 20px",
                    "marginBottom": "12px",
                },
                "children": [f"grocery-row-{idx}"],
            },
            {
                "id": f"grocery-row-{idx}",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "20px",
                    "alignItems": "center",
                    "width": "100%",
                    "boxSizing": "border-box",
                },
                "children": [f"grocery-img-wrap-{idx}", f"grocery-col-{idx}", f"grocery-action-wrap-{idx}"],
            },
            {
                "id": f"grocery-img-wrap-{idx}",
                "component": "MaterialColumn",
                "style": {
                    "width": "110px",
                    "minWidth": "110px",
                    "maxWidth": "110px",
                    "height": "110px",
                    "borderRadius": "12px",
                    "overflow": "hidden",
                    "flexShrink": "0",
                    "boxSizing": "border-box",
                },
                "children": [f"grocery-img-{idx}"],
            },
            {
                "id": f"grocery-img-{idx}",
                "component": "Image",
                "variant": "mediumFeature",
                "fit": "cover",
                "url": img_url,
                "description": prod_name,
            },
            {
                "id": f"grocery-col-{idx}",
                "component": "MaterialColumn",
                "weight": 1,
                "style": {
                    "flex": "1",
                    "minWidth": "0",
                    "gap": "6px",
                    "boxSizing": "border-box",
                },
                "children": [
                    f"prod-name-{idx}",
                    f"prod-need-badge-{idx}",
                    f"prod-brand-txt-{idx}",
                    f"prod-price-row-{idx}",
                ],
            },
            {
                "id": f"prod-name-{idx}",
                "component": "MaterialText",
                "usageHint": "h3",
                "text": prod_name,
                "style": {
                    "fontSize": "16px",
                    "fontWeight": "600",
                    "color": "#1e293b",
                    "margin": "0",
                },
            },
            {
                "id": f"prod-need-badge-{idx}",
                "component": "MaterialColumn",
                "style": {
                    "backgroundColor": "#f0fdf4",
                    "border": "1px solid #bbf7d0",
                    "borderRadius": "6px",
                    "padding": "3px 10px",
                    "width": "fit-content",
                },
                "children": [f"prod-need-txt-{idx}"],
            },
            {
                "id": f"prod-need-txt-{idx}",
                "component": "MaterialText",
                "text": rec_need,
                "style": {
                    "fontSize": "12px",
                    "fontWeight": "500",
                    "color": "#15803d",
                    "margin": "0",
                },
            },
            {
                "id": f"prod-brand-txt-{idx}",
                "component": "MaterialText",
                "text": brand_pack,
                "style": {
                    "fontSize": "12px",
                    "color": "#64748b",
                    "margin": "0",
                },
            },
            {
                "id": f"prod-price-row-{idx}",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "8px",
                    "alignItems": "center",
                    "marginTop": "2px",
                },
                "children": price_row_children,
            },
            {
                "id": f"prod-price-{idx}",
                "component": "MaterialText",
                "text": f"SGD ${price:.2f}",
                "style": {
                    "fontSize": "16px",
                    "fontWeight": "700",
                    "color": "#1e293b",
                    "margin": "0",
                },
            },
        ]

        if is_promo:
            item_components.extend([
                {
                    "id": f"prod-promo-badge-{idx}",
                    "component": "MaterialColumn",
                    "style": {
                        "backgroundColor": "#fef2f2",
                        "border": "1px solid #fecaca",
                        "borderRadius": "6px",
                        "padding": "2px 8px",
                    },
                    "children": [f"prod-promo-txt-{idx}"],
                },
                {
                    "id": f"prod-promo-txt-{idx}",
                    "component": "MaterialText",
                    "text": promo_text,
                    "style": {
                        "fontSize": "11px",
                        "fontWeight": "600",
                        "color": "#b91c1c",
                        "margin": "0",
                    },
                },
            ])

        item_components.extend([
            {
                "id": f"grocery-action-wrap-{idx}",
                "component": "MaterialColumn",
                "align": "center",
                "justify": "center",
                "style": {
                    "flexShrink": "0",
                },
                "children": [f"buy-btn-{idx}"],
            },
            {
                "id": f"buy-btn-{idx}",
                "component": "MaterialButton",
                "label": "🛒 Buy on FreshMarket",
                "variant": "flat",
                "appearance": "filled",
                "color": "primary",
                "style": {
                    "backgroundColor": "#1d56db",
                    "color": "#ffffff",
                    "borderRadius": "8px",
                    "padding": "9px 18px",
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "whiteSpace": "nowrap",
                },
                "action": {
                    "functionCall": {
                        "call": "openUrl",
                        "args": {"url": prod_url},
                        "returnType": "void",
                    }
                },
            },
        ])

        components.extend(item_components)

    components.append({
        "id": "grocery-list",
        "component": "List",
        "direction": "vertical",
        "children": card_ids,
    })

    # 3. Full Recipe Guide (Unified Material Master Card)
    if recipe_details:
        prep_time = recipe_details.get("prep_time", "15-20 mins")
        cook_time = recipe_details.get("cook_time", "20-30 mins")
        difficulty = recipe_details.get("difficulty", "Easy")
        yield_str = recipe_details.get("yield_str", f"{base_servings} Servings")
        desc = recipe_details.get("description", "")
        instructions = recipe_details.get("instructions", [])
        tips = recipe_details.get("tips", [])
        ingredients_to_show = scaled_ingredients or recipe_details.get("ingredients", [])

        # Metadata cards row
        meta_items = [
            ("meta-prep", "timer", "Prep Time", prep_time),
            ("meta-cook", "local_fire_department", "Cook Time", cook_time),
            ("meta-diff", "star", "Difficulty", difficulty),
            ("meta-yield", "inventory_2", "Base Yield", yield_str),
        ]
        meta_col_ids = []
        meta_sub_components = []
        for mid, icon_name, lbl, val in meta_items:
            cid = f"{mid}-card"
            meta_col_ids.append(cid)
            meta_sub_components.extend([
                {
                    "id": cid,
                    "component": "MaterialColumn",
                    "style": {
                        "flex": "1",
                        "minWidth": "120px",
                        "backgroundColor": "#f8fafc",
                        "border": "1px solid #e2e8f0",
                        "borderRadius": "10px",
                        "padding": "12px 14px",
                        "gap": "4px",
                        "boxSizing": "border-box",
                    },
                    "children": [f"{mid}-top-row", f"{mid}-val"],
                },
                {
                    "id": f"{mid}-top-row",
                    "component": "MaterialRow",
                    "align": "center",
                    "style": {
                        "gap": "6px",
                        "alignItems": "center",
                    },
                    "children": [f"{mid}-icon", f"{mid}-lbl"],
                },
                {
                    "id": f"{mid}-icon",
                    "component": "MaterialIcon",
                    "icon": icon_name,
                    "style": {
                        "color": "#64748b",
                        "fontSize": "16px",
                    },
                },
                {
                    "id": f"{mid}-lbl",
                    "component": "MaterialText",
                    "text": lbl.upper(),
                    "style": {
                        "fontSize": "11px",
                        "fontWeight": "600",
                        "color": "#64748b",
                        "margin": "0",
                        "letterSpacing": "0.5px",
                    },
                },
                {
                    "id": f"{mid}-val",
                    "component": "MaterialText",
                    "text": val,
                    "style": {
                        "fontSize": "15px",
                        "fontWeight": "600",
                        "color": "#1e293b",
                        "margin": "0",
                    },
                },
            ])

        # Ingredients items (clean vertical list of styled rows)
        ing_row_ids = []
        ing_sub_components = []
        for i_idx, ing_line in enumerate(ingredients_to_show):
            row_id = f"recipe-ing-row-{i_idx}"
            txt_id = f"recipe-ing-txt-{i_idx}"
            dot_id = f"recipe-ing-dot-{i_idx}"
            ing_row_ids.append(row_id)
            clean_line = ing_line.lstrip("•*- ").strip()
            ing_sub_components.extend([
                {
                    "id": row_id,
                    "component": "MaterialRow",
                    "align": "center",
                    "style": {
                        "backgroundColor": "#f8fafc",
                        "border": "1px solid #e2e8f0",
                        "borderRadius": "8px",
                        "padding": "8px 14px",
                        "gap": "10px",
                        "alignItems": "center",
                        "width": "100%",
                        "boxSizing": "border-box",
                    },
                    "children": [dot_id, txt_id],
                },
                {
                    "id": dot_id,
                    "component": "MaterialIcon",
                    "icon": "check_circle",
                    "style": {
                        "color": "#1d56db",
                        "fontSize": "16px",
                        "flexShrink": "0",
                    },
                },
                {
                    "id": txt_id,
                    "component": "MaterialText",
                    "text": clean_line,
                    "style": {
                        "fontSize": "13px",
                        "color": "#334155",
                        "margin": "0",
                        "lineHeight": "1.4",
                    },
                },
            ])

        # Step-by-Step Cooking Instructions (numbered circular badges)
        inst_card_ids = []
        inst_sub_components = []
        for s_idx, step in enumerate(instructions):
            scard_id = f"recipe-step-card-{s_idx}"
            srow_id = f"recipe-step-row-{s_idx}"
            sbadge_id = f"recipe-step-badge-{s_idx}"
            snum_id = f"recipe-step-num-{s_idx}"
            scol_id = f"recipe-step-col-{s_idx}"
            title_id = f"recipe-step-title-{s_idx}"
            body_id = f"recipe-step-body-{s_idx}"

            inst_card_ids.append(scard_id)
            inst_sub_components.extend([
                {
                    "id": scard_id,
                    "component": "MaterialCard",
                    "appearance": "outlined",
                    "style": {
                        "backgroundColor": "#ffffff",
                        "borderRadius": "12px",
                        "border": "1px solid #e5e7eb",
                        "padding": "16px",
                        "marginBottom": "10px",
                    },
                    "children": [srow_id],
                },
                {
                    "id": srow_id,
                    "component": "MaterialRow",
                    "align": "start",
                    "style": {
                        "gap": "14px",
                        "alignItems": "flex-start",
                        "width": "100%",
                        "boxSizing": "border-box",
                    },
                    "children": [sbadge_id, scol_id],
                },
                {
                    "id": sbadge_id,
                    "component": "MaterialColumn",
                    "align": "center",
                    "justify": "center",
                    "style": {
                        "width": "30px",
                        "minWidth": "30px",
                        "height": "30px",
                        "borderRadius": "15px",
                        "backgroundColor": "#1d56db",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "flexShrink": "0",
                    },
                    "children": [snum_id],
                },
                {
                    "id": snum_id,
                    "component": "MaterialText",
                    "text": str(s_idx + 1),
                    "style": {
                        "fontSize": "13px",
                        "fontWeight": "700",
                        "color": "#ffffff",
                        "margin": "0",
                    },
                },
                {
                    "id": scol_id,
                    "component": "MaterialColumn",
                    "weight": 1,
                    "style": {
                        "flex": "1",
                        "minWidth": "0",
                        "gap": "4px",
                    },
                    "children": [title_id, body_id],
                },
                {
                    "id": title_id,
                    "component": "MaterialText",
                    "text": step.get("title", f"Step {s_idx + 1}"),
                    "style": {
                        "fontSize": "15px",
                        "fontWeight": "600",
                        "color": "#1e293b",
                        "margin": "0",
                    },
                },
                {
                    "id": body_id,
                    "component": "MaterialText",
                    "text": step.get("body", ""),
                    "style": {
                        "fontSize": "14px",
                        "color": "#475569",
                        "lineHeight": "1.5",
                        "margin": "0",
                    },
                },
            ])

        # Chef Tips section
        tip_card_components = []
        if tips:
            tip_text_ids = []
            for t_idx, tip in enumerate(tips):
                tid = f"recipe-tip-item-{t_idx}"
                tip_text_ids.append(tid)
                clean_tip = tip.lstrip("💡•*- ").strip()
                tip_card_components.append({
                    "id": tid,
                    "component": "MaterialText",
                    "text": f"• {clean_tip}",
                    "style": {
                        "fontSize": "13px",
                        "color": "#78350f",
                        "lineHeight": "1.5",
                        "margin": "0",
                    },
                })

            tip_card_components.extend([
                {
                    "id": "recipe-tips-card",
                    "component": "MaterialCard",
                    "appearance": "outlined",
                    "style": {
                        "backgroundColor": "#fffbeb",
                        "border": "1px solid #fde68a",
                        "borderRadius": "12px",
                        "padding": "16px 20px",
                        "marginTop": "10px",
                    },
                    "children": ["recipe-tips-col"],
                },
                {
                    "id": "recipe-tips-col",
                    "component": "MaterialColumn",
                    "style": {
                        "gap": "8px",
                        "width": "100%",
                    },
                    "children": ["recipe-tips-hdr-row"] + tip_text_ids,
                },
                {
                    "id": "recipe-tips-hdr-row",
                    "component": "MaterialRow",
                    "align": "center",
                    "style": {
                        "gap": "8px",
                        "alignItems": "center",
                    },
                    "children": ["recipe-tips-icon", "recipe-tips-title"],
                },
                {
                    "id": "recipe-tips-icon",
                    "component": "MaterialIcon",
                    "icon": "lightbulb",
                    "style": {
                        "color": "#d97706",
                        "fontSize": "20px",
                    },
                },
                {
                    "id": "recipe-tips-title",
                    "component": "MaterialText",
                    "text": "Chef's Tips & Notes",
                    "style": {
                        "fontSize": "15px",
                        "fontWeight": "600",
                        "color": "#92400e",
                        "margin": "0",
                    },
                },
            ])

        # Assemble master card column children
        master_col_children = [
            "recipe-master-hdr-row",
            "recipe-master-desc",
        ]
        if doc_url:
            master_col_children.append("doc-link-btn")
        master_col_children.extend([
            "recipe-meta-row",
            "div-servings",
            "servings-hdr-row",
            "servings-instruction-text",
            "servings-controls-row",
            "div-ingredients",
            "recipe-ingredients-hdr-row",
            "recipe-ingredients-note",
            "recipe-ingredients-list-col",
            "div-instructions",
            "recipe-instructions-hdr-row",
            "recipe-instructions-list-col",
        ])

        if tips:
            master_col_children.append("recipe-tips-card")

        # Master Card & Layout definitions
        components.extend([
            {
                "id": "recipe-master-card",
                "component": "MaterialCard",
                "appearance": "outlined",
                "style": {
                    "backgroundColor": "#ffffff",
                    "borderRadius": "16px",
                    "border": "1px solid #e5e7eb",
                    "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.04)",
                    "padding": "24px",
                    "marginBottom": "20px",
                },
                "children": ["recipe-master-col"],
            },
            {
                "id": "recipe-master-col",
                "component": "MaterialColumn",
                "style": {
                    "gap": "18px",
                    "width": "100%",
                    "boxSizing": "border-box",
                },
                "children": master_col_children,
            },
            # Header Row
            {
                "id": "recipe-master-hdr-row",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "10px",
                    "alignItems": "center",
                },
                "children": ["recipe-master-icon", "recipe-full-title"],
            },
            {
                "id": "recipe-master-icon",
                "component": "MaterialIcon",
                "icon": "menu_book",
                "style": {
                    "color": "#1d56db",
                    "fontSize": "26px",
                },
            },
            {
                "id": "recipe-full-title",
                "component": "MaterialText",
                "usageHint": "h2",
                "text": f"Full Recipe Guide: {recipe_title}",
                "style": {
                    "fontSize": "22px",
                    "fontWeight": "600",
                    "color": "#1e293b",
                    "margin": "0",
                },
            },
            {
                "id": "recipe-master-desc",
                "component": "MaterialText",
                "text": desc,
                "style": {
                    "fontSize": "14px",
                    "color": "#475569",
                    "lineHeight": "1.5",
                    "margin": "0",
                },
            },
            {
                "id": "recipe-meta-row",
                "component": "MaterialRow",
                "align": "stretch",
                "style": {
                    "gap": "12px",
                    "width": "100%",
                    "flexWrap": "wrap",
                    "boxSizing": "border-box",
                },
                "children": meta_col_ids,
            },
            {
                "id": "div-servings",
                "component": "Divider",
            },
            # Minimalist Serving Size Adjuster
            {
                "id": "servings-hdr-row",
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
                "children": ["servings-hdr-left", "servings-badge"],
            },
            {
                "id": "servings-hdr-left",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "8px",
                    "alignItems": "center",
                },
                "children": ["servings-hdr-icon", "servings-title"],
            },
            {
                "id": "servings-hdr-icon",
                "component": "MaterialIcon",
                "icon": "tune",
                "style": {
                    "color": "#1d56db",
                    "fontSize": "20px",
                },
            },
            {
                "id": "servings-title",
                "component": "MaterialText",
                "usageHint": "h3",
                "text": "Serving Size Adjuster (1–10 People)",
                "style": {
                    "fontSize": "16px",
                    "fontWeight": "600",
                    "color": "#1e293b",
                    "margin": "0",
                },
            },
            {
                "id": "servings-badge",
                "component": "MaterialColumn",
                "style": {
                    "backgroundColor": "#eff6ff",
                    "border": "1px solid #bfdbfe",
                    "borderRadius": "8px",
                    "padding": "6px 14px",
                },
                "children": ["servings-badge-txt"],
            },
            {
                "id": "servings-badge-txt",
                "component": "MaterialText",
                "text": f"Current: {servings} People (Base: {base_servings})",
                "style": {
                    "fontSize": "13px",
                    "fontWeight": "600",
                    "color": "#1d56db",
                    "margin": "0",
                },
            },
            {
                "id": "servings-instruction-text",
                "component": "MaterialText",
                "text": "Move the slider below to scale ingredient quantities and FreshMarket grocery costs:",
                "style": {
                    "fontSize": "13px",
                    "color": "#64748b",
                    "margin": "0",
                },
            },
            {
                "id": "servings-controls-row",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "16px",
                    "alignItems": "center",
                    "width": "100%",
                    "boxSizing": "border-box",
                },
                "children": ["servings-slider", "servings-apply-btn"],
            },
            {
                "id": "servings-slider",
                "component": "Slider",
                "weight": 1,
                "min": 1,
                "max": 10,
                "value": {"path": "/servings"},
                "label": f"Serving Size: {servings} People",
            },
            {
                "id": "servings-apply-btn",
                "component": "MaterialButton",
                "label": "🔄 Update Servings & Groceries",
                "variant": "flat",
                "appearance": "filled",
                "color": "primary",
                "style": {
                    "backgroundColor": "#1d56db",
                    "color": "#ffffff",
                    "borderRadius": "8px",
                    "padding": "10px 20px",
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "whiteSpace": "nowrap",
                },
                "action": {
                    "event": {
                        "name": "get_recipe_groceries",
                        "context": {
                            "recipeName": recipe_title,
                            "servings": {"path": "/servings"},
                            "prompt": f"Please recalculate the recipe and FreshMarket groceries for {recipe_title}",
                        },
                    }
                },
            },
            {
                "id": "div-ingredients",
                "component": "Divider",
            },
            # Scaled Ingredients
            {
                "id": "recipe-ingredients-hdr-row",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "8px",
                    "alignItems": "center",
                },
                "children": ["recipe-ingredients-icon", "recipe-ingredients-title"],
            },
            {
                "id": "recipe-ingredients-icon",
                "component": "MaterialIcon",
                "icon": "restaurant",
                "style": {
                    "color": "#1d56db",
                    "fontSize": "20px",
                },
            },
            {
                "id": "recipe-ingredients-title",
                "component": "MaterialText",
                "usageHint": "h3",
                "text": f"Scaled Ingredients ({servings} People)",
                "style": {
                    "fontSize": "18px",
                    "fontWeight": "600",
                    "color": "#1e293b",
                    "margin": "0",
                },
            },
            {
                "id": "recipe-ingredients-note",
                "component": "MaterialText",
                "text": f"Quantities automatically calculated for {servings} people (Base recipe yield: {base_servings} people):",
                "style": {
                    "fontSize": "13px",
                    "color": "#64748b",
                    "margin": "0",
                },
            },
            {
                "id": "recipe-ingredients-list-col",
                "component": "MaterialColumn",
                "style": {
                    "gap": "6px",
                    "width": "100%",
                },
                "children": ing_row_ids,
            },
            {
                "id": "div-instructions",
                "component": "Divider",
            },
            # Cooking Instructions
            {
                "id": "recipe-instructions-hdr-row",
                "component": "MaterialRow",
                "align": "center",
                "style": {
                    "gap": "8px",
                    "alignItems": "center",
                },
                "children": ["recipe-instructions-icon", "recipe-instructions-title"],
            },
            {
                "id": "recipe-instructions-icon",
                "component": "MaterialIcon",
                "icon": "soup_kitchen",
                "style": {
                    "color": "#1d56db",
                    "fontSize": "20px",
                },
            },
            {
                "id": "recipe-instructions-title",
                "component": "MaterialText",
                "usageHint": "h3",
                "text": "Step-by-Step Cooking Instructions",
                "style": {
                    "fontSize": "18px",
                    "fontWeight": "600",
                    "color": "#1e293b",
                    "margin": "0",
                },
            },
            {
                "id": "recipe-instructions-list-col",
                "component": "MaterialColumn",
                "style": {
                    "gap": "10px",
                    "width": "100%",
                },
                "children": inst_card_ids,
            },
        ])

        components.extend(meta_sub_components)
        components.extend(ing_sub_components)
        components.extend(inst_sub_components)
        components.extend(tip_card_components)

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
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "grocery_shopping_surface",
                "path": "/servings",
                "value": servings,
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
