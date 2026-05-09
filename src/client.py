import os
import httpx
from typing import Any, Optional, List, Dict
from toon_mcp import json_to_toon

class LinkwardenServiceClient:
    """Client for Linkwarden API with authentication passthrough."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("LINKWARDEN_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("LINKWARDEN_API_KEY", "")
        if not self.base_url:
            raise ValueError(
                "Linkwarden URL required. Set LINKWARDEN_BASE_URL env var or pass base_url."
            )

    def _get_headers(self, api_key: Optional[str] = None) -> Dict[str, str]:
        token = api_key or self.api_key
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def request(
        self,
        method: str,
        path: str,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._get_headers(api_key)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                **kwargs,
            )
            response.raise_for_status()
            if "application/json" in response.headers.get("content-type", ""):
                data = response.json()
                # The Linkwarden API wraps everything in a 'response' key
                return data.get("response", data)
            return {"text": response.text}

    def to_upper_camel_case(self, iconName: str) -> str:
        if iconName and iconName[0].islower():
            return iconName[0].upper() + iconName[1:]
        return iconName

    async def get(self, path: str, api_key: Optional[str] = None, params: Optional[Dict] = None, **kwargs: Any) -> Any:
        return await self.request("GET", path, api_key, params=params, **kwargs)

    async def post(self, path: str, api_key: Optional[str] = None, json_data: Optional[Dict] = None, **kwargs: Any) -> Any:
        return await self.request("POST", path, api_key, json=json_data, **kwargs)

    async def put(self, path: str, api_key: Optional[str] = None, json_data: Optional[Dict] = None, **kwargs: Any) -> Any:
        return await self.request("PUT", path, api_key, json=json_data, **kwargs)

    async def delete(self, path: str, api_key: Optional[str] = None, json_data: Optional[Dict] = None, **kwargs: Any) -> Any:
        return await self.request("DELETE", path, api_key, json=json_data, **kwargs)

    # --- Collection Management ---
    async def get_all_collections(self, api_key: Optional[str] = None) -> Any:
        raw_data = await self.get("/api/v1/collections", api_key)
        return json_to_toon(raw_data)

    async def get_collection_by_id(self, collectionId: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/api/v1/collections/{collectionId}", api_key)

    async def create_collection(self, name: str, description: str, color: str, icon: str, iconWeight: str, parentId: Optional[int], api_key: Optional[str] = None) -> Any:
        icon = self.to_upper_camel_case(icon)
        payload = {
            "name": name,
            "description": description,
            "color": color,
            "icon": icon,
            "iconWeight": iconWeight,
        }
        if parentId is not None:
            payload["parentId"] = parentId
        return await self.post("/api/v1/collections", api_key, json_data=payload)

    async def delete_collection_by_id(self, collectionId: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/api/v1/collections/{collectionId}", api_key)

    async def get_public_collection_by_id(self, collectionId: int) -> Any:
        return await self.get(f"/api/v1/public/collections/{collectionId}")

    async def get_public_collections_links(self, collectionId: int, searchQueryString: Optional[str] = None, pinnedOnly: Optional[bool] = None, sort: Optional[int] = None, cursor: Optional[int] = None, search_by_name: bool = False, search_by_url: bool = False, search_by_description: bool = False, search_by_tags: bool = False, api_key: Optional[str] = None) -> Any:
        params = {
            "collectionId": collectionId,
            "searchQueryString": searchQueryString,
            "pinnedOnly": str(pinnedOnly).lower() if pinnedOnly is not None else None,
            "sort": sort,
            "cursor": cursor,
        }
        raw_data = await self.get("/api/v1/public/collections/links", api_key, params=params)
        return json_to_toon(raw_data)

    async def get_public_collections_tags(self, collectionId: int, search: Optional[str] = None, api_key: Optional[str] = None) -> Any:
        params = {"collectionId": collectionId, "search": search}
        raw_data = await self.get("/api/v1/public/collections/tags", api_key, params=params)
        return json_to_toon(raw_data)

    # --- Link Management ---
    async def get_all_links(self, collectionId: Optional[int] = None, tagId: Optional[int] = None, searchQueryString: Optional[str] = None, pinnedOnly: Optional[bool] = None, sort: Optional[int] = None, cursor: Optional[int] = None, search_by_name: bool = False, search_by_url: bool = False, search_by_description: bool = False, search_by_text: bool = False, search_by_tags: bool = False, api_key: Optional[str] = None) -> Any:
        params = {
            "collectionId": collectionId,
            "tagId": tagId,
            "searchQueryString": searchQueryString,
            "pinnedOnly": str(pinnedOnly).lower() if pinnedOnly is not None else None,
            "sort": sort,
            "cursor": cursor,
        }
        raw_data = await self.get("/api/v1/links", api_key, params=params)
        if isinstance(raw_data, list):
            for link in raw_data:
                if isinstance(link, dict):
                    link.pop("textContent", None)
        elif isinstance(raw_data, dict) and "links" in raw_data and isinstance(raw_data["links"], list):
            for link in raw_data["links"]:
                if isinstance(link, dict):
                    link.pop("textContent", None)
        return json_to_toon(raw_data)

    async def get_link_by_id(self, link_id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/api/v1/links/{link_id}", api_key)

    async def create_link(self, url: str, name: str, description: str, type: str, collectionId: int, tags: List[str], api_key: Optional[str] = None) -> Any:
        # First, fetch the collection to get its name to satisfy the backend schema
        collection = await self.get_collection_by_id(collectionId, api_key)
        collection_name = collection.get("name", "Unknown Collection")
        payload = {
            "url": url,
            "name": name,
            "description": description,
            "type": type,
            "collection": {
                "id": collectionId,
                "name": collection_name
            },
            "tags": [{"name": tag} for tag in tags]
        }
        return await self.post("/api/v1/links", api_key, json_data=payload)

    async def delete_link_by_id(self, link_id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/api/v1/links/{link_id}", api_key)

    async def delete_links_bulk(self, linkIds: List[int], api_key: Optional[str] = None) -> Any:
        return await self.delete("/api/v1/links", api_key, json_data={"linkIds": linkIds})

    async def archive_link(self, link_id: int, api_key: Optional[str] = None) -> Any:
        return await self.put(f"/api/v1/links/{link_id}/archive", api_key)

    # --- Tag Management ---
    async def get_all_tags(self, api_key: Optional[str] = None) -> Any:
        raw_data = await self.get("/api/v1/tags", api_key)
        return json_to_toon(raw_data)

    async def delete_tag_by_id(self, tagId: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/api/v1/tags/{tagId}", api_key)

    # --- Utilities ---
    async def search_links(self, searchQueryString: str, collectionId: Optional[int] = None, tagId: Optional[int] = None, sort: Optional[int] = None, cursor: Optional[int] = None, api_key: Optional[str] = None) -> Any:
        params = {
            "searchQueryString": searchQueryString,
            "collectionId": collectionId,
            "tagId": tagId,
            "sort": sort,
            "cursor": cursor
        }
        raw_data = await self.get("/api/v1/search", api_key, params=params)
        return json_to_toon(raw_data)

    async def get_user_info(self, api_key: Optional[str] = None) -> Any:
        return await self.get("/api/v1/users/me", api_key)
