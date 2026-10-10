from typing import Any, Optional, List, Dict
from a2a.types import AgentExtension, Part
from google.adk.a2a.utils.agent_to_a2a import _compat

A2UI_EXTENSION_BASE_URI = "https://a2ui.org/a2a-extension/a2ui"
MIME_TYPE_KEY = "mimeType"
# Gemini Enterprise (Discovery Engine / Dolphin / UCS Widget) requires application/json+a2ui
A2UI_MIME_TYPE = "application/json+a2ui"
LEGACY_A2UI_MIME_TYPE = "application/a2ui+json"

GE_COMPOSITE_CATALOG_ID = (
    "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"
)
GE_MATERIAL_CATALOG_ID = "https://a2ui.org/specification/v0_9/material_catalog.json"
GE_BASIC_CATALOG_ID = "https://a2ui.org/specification/v0_9/basic_catalog.json"


def get_a2ui_agent_extension(
    version: str = "0.9",
    accepts_inline_catalogs: bool = True,
    supported_catalog_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if accepts_inline_catalogs:
        params["acceptsInlineCatalogs"] = True
    if supported_catalog_ids is None:
        supported_catalog_ids = [
            GE_COMPOSITE_CATALOG_ID,
            GE_MATERIAL_CATALOG_ID,
            GE_BASIC_CATALOG_ID,
        ]
    if supported_catalog_ids:
        params["supportedCatalogIds"] = supported_catalog_ids

    clean_version = version.lstrip("v")
    return {
        "uri": f"{A2UI_EXTENSION_BASE_URI}/v{clean_version}",
        "description": "Provides agent driven UI using the A2UI JSON format.",
        "params": params,
    }


def build_a2ui_agent_card(
    name: str,
    description: str,
    url: str,
    skills: List[Dict[str, Any]],
) -> Any:
    ext = get_a2ui_agent_extension(
        "0.9",
        True,
        [
            GE_COMPOSITE_CATALOG_ID,
            GE_MATERIAL_CATALOG_ID,
            GE_BASIC_CATALOG_ID,
        ],
    )
    return _compat.build_agent_card(
        name=name,
        description=description,
        url=url,
        version="1.0.0",
        protocol_binding="JSONRPC",
        capabilities={
            "streaming": True,
            "extensions": [ext],
        },
        skills=skills,
        default_input_modes=["text/plain", A2UI_MIME_TYPE],
        default_output_modes=["text/plain", A2UI_MIME_TYPE, LEGACY_A2UI_MIME_TYPE],
    )


def create_text_part(text: str) -> Part:
    """Creates an A2A Part containing text."""
    return _compat.make_text_part(text)


def create_a2ui_part(a2ui_data: dict[str, Any]) -> Part:
    """Creates an A2A Part containing A2UI data with application/json+a2ui MIME type."""
    return _compat.make_data_part(
        data=a2ui_data,
        metadata={MIME_TYPE_KEY: A2UI_MIME_TYPE},
    )


def extract_part_text(part: Part) -> Optional[str]:
    return _compat.part_text(part)


def extract_part_data(part: Part) -> Optional[dict[str, Any]]:
    return _compat.data_part_dict(part)
