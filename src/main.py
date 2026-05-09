import os
from typing import Any, Optional, Literal
from contextvars import ContextVar
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from .client import LinkwardenServiceClient

# Context variable to store the current user's token
_current_user_token: ContextVar[Optional[str]] = ContextVar("current_user_token", default=None)

class AuthMiddleware:
    """ASGI middleware to extract Authorization header and set context variable."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                _current_user_token.set(token)
        await self.app(scope, receive, send)

# Initialize MCP server
mcp = FastMCP("linkwarden-mcp-server")

# Initialize client (URL from env)
_client: Optional[LinkwardenServiceClient] = None

def get_client() -> LinkwardenServiceClient:
    """Get or create the Linkwarden client."""
    global _client
    if _client is None:
        _client = LinkwardenServiceClient()
    return _client

def get_user_token() -> Optional[str]:
    """Get the current user's token from context or environment."""
    token = _current_user_token.get()
    if token:
        return token
    return os.getenv("LINKWARDEN_API_KEY")

# =============================================================================
# Parameter Models
# =============================================================================

class CreateCollectionParam(BaseModel):
    name: str = Field(description="Name of the new collection")
    description: str = Field(description="Description of the collection")
    color: str = Field(description="Hex color code for the collection icon")
    icon: Literal["Smiley", "Heart", "Star", "Airplane", "Camera", "Music", "Video", "Book", "GraduationCap", "Briefcase", "ShoppingBag", "CreditCard", "MapPin", "Globe", "Cloud", "Sun", "Moon", "Fire", "Leaf", "Tree", "Coffee", "BeerBottle", "Car", "Bicycle", "Train", "Building", "House", "Bed", "Chair", "Computer", "Laptop", "Smartphone", "Watch", "Headphones", "Microphone", "Speaker", "Palette", "Pen", "Pencil", "Hammer", "Wrench", "Gear", "Bolt", "Lightbulb", "Gift", "GameController", "Trophy", "Medal", "Dumbbell", "Pizza", "Apple", "Ghost", "Skull", "Biohazard", "Microscope", "Dna", "Rocket", "Anchor", "Compass", "Target", "Bell", "Envelope", "Chat", "Paperclip", "Lock", "Key", "Shield", "Question", "Info", "Check", "Trash", "Download", "Upload", "Link", "Share", "Search", "Filter", "Calendar", "Clock", "Newspaper", "File", "Folder", "Database", "Map", "CompassRose", "Mountain", "Fish", "Bird", "Dog", "Cat", "Hospital", "Pill", "Stethoscope", "Money", "Calculator", "Toolbox", "Ticket", "FilmStrip", "PaintBrush", "Brain"] = Field(description="Must be from this list: Smiley, Heart, Star, Airplane, Camera, Music, Video, Book, GraduationCap, Briefcase, ShoppingBag, CreditCard, MapPin, Globe, Cloud, Sun, Moon, Fire, Leaf, Tree, Coffee, BeerBottle, Car, Bicycle, Train, Building, House, Bed, Chair, Computer, Laptop, Smartphone, Watch, Headphones, Microphone, Speaker, Palette, Pen, Pencil, Hammer, Wrench, Gear, Bolt, Lightbulb, Gift, GameController, Trophy, Medal, Dumbbell, Pizza, Apple, Ghost, Skull, Biohazard, Microscope, Dna, Rocket, Anchor, Compass, Target, Bell, Envelope, Chat, Paperclip, Lock, Key, Shield, Question, Info, Check, Trash, Download, Upload, Link, Share, Search, Filter, Calendar, Clock, Newspaper, File, Folder, Database, Map, CompassRose, Mountain, Fish, Bird, Dog, Cat, Hospital, Pill, Stethoscope, Money, Calculator, Toolbox, Ticket, FilmStrip, PaintBrush, Brain")
    iconWeight: str = Field(description="Icon weight (e.g., 'bold', 'regular')")
    parentId: Optional[int] = Field(default=None, description="ID of the parent collection")

class GetCollectionByIdParam(BaseModel):
    id: int = Field(description="The unique ID of the collection")

class CreateLinkParam(BaseModel):
    url: str = Field(description="The URL of the bookmark")
    name: str = Field(description="The title of the bookmark")
    description: str = Field(description="A brief description of the bookmark")
    type: str = Field(description="Type of link (e.g., 'url')")
    collectionId: int = Field(description="The ID of the collection to add it to")
    tags: list[str] = Field(default_factory=list, description="List of tag names to associate with the link")
    
class GetLinkByIdParam(BaseModel):
    id: int = Field(description="The unique ID of the link")

class DeleteLinksBulkParam(BaseModel):
    linkIds: list[int] = Field(description="A list of link IDs to delete")

class SearchLinksParam(BaseModel):
    searchQueryString: str = Field(description="The keyword to search for")
    collectionId: Optional[int] = Field(default=None, description="Filter by collection ID")
    tagId: Optional[int] = Field(default=None, description="Filter by tag ID")
    sort: Optional[int] = Field(default=None, description="Sort order")
    cursor: Optional[int] = Field(default=None, description="Pagination cursor")

class GetPublicLinksParam(BaseModel):
    collectionId: int = Field(description="The ID of the public collection")
    searchQueryString: Optional[str] = Field(default=None, description="Search query within the public collection")
    pinnedOnly: Optional[bool] = Field(default=None, description="Whether to show only pinned links")
    sort: Optional[int] = Field(default=None, description="Sort order")
    cursor: Optional[int] = Field(default=None, description="Pagination cursor")

class GetPublicTagsParam(BaseModel):
    collectionId: int = Field(description="The ID of the public collection")
    search: Optional[str] = Field(default=None, description="Search term for tags")

# =============================================================================
# Collection Tools
# =============================================================================

@mcp.tool()
async def get_all_collections(ctx: Context) -> dict[str, Any]:
    """List all available collections."""
    collections = await get_client().get_all_collections(get_user_token())
    return {"collections": collections}

@mcp.tool()
async def get_collection_by_id(params: GetCollectionByIdParam, ctx: Context) -> dict[str, Any]:
    """Get metadata for a specific collection."""
    return await get_client().get_collection_by_id(params.id, get_user_token())

@mcp.tool()
async def create_collection(params: CreateCollectionParam, ctx: Context) -> dict[str, Any]:
    """Create a new collection."""
    return await get_client().create_collection(
        params.name, params.description, params.color, params.icon, params.iconWeight, params.parentId, get_user_token()
    )

@mcp.tool()
async def delete_collection_by_id(params: GetCollectionByIdParam, ctx: Context) -> dict[str, Any]:
    """Delete a collection."""
    return await get_client().delete_collection_by_id(params.id, get_user_token())

@mcp.tool()
async def get_public_collection_by_id(params: GetCollectionByIdParam, ctx: Context) -> dict[str, Any]:
    """Get metadata for a public collection."""
    return await get_client().get_public_collection_by_id(params.id)

@mcp.tool()
async def get_public_collections_links(params: GetPublicLinksParam, ctx: Context) -> dict[str, Any]:
    """Advanced filtering for public collection links."""
    collections_links = await get_client().get_public_collections_links(
        params.collectionId, params.searchQueryString, params.pinnedOnly, params.sort, params.cursor, api_key=get_user_token()
    )
    return {"collections_links": collections_links}

@mcp.tool()
async def get_public_collections_tags(params: GetPublicTagsParam, ctx: Context) -> dict[str, Any]:
    """Get tags used in a public collection."""
    collections_tags = await get_client().get_public_collections_tags(params.collectionId, params.search)
    return {"collections_tags": collections_tags}

# =============================================================================
# Link Tools
# =============================================================================

@mcp.tool()
async def get_all_links(
    collectionId: Optional[int] = None, 
    tagId: Optional[int] = None, 
    searchQueryString: Optional[str] = None, 
    pinnedOnly: Optional[bool] = None, 
    sort: Optional[int] = None, 
    cursor: Optional[int] = None, 
    api_key: Optional[str] = None,
    ctx: Context = None
) -> dict[str, Any]:
    """Primary browsing tool with deep filtering."""
    links = await get_client().get_all_links(
        collectionId, tagId, searchQueryString, pinnedOnly, sort, cursor, api_key=get_user_token()
    )
    return {"links": links}

@mcp.tool()
async def get_link_by_id(params: GetLinkByIdParam, ctx: Context) -> dict[str, Any]:
    """Get full details of one bookmark."""
    return await get_client().get_link_by_id(params.id, get_user_token())

@mcp.tool()
async def create_link(params: CreateLinkParam, ctx: Context) -> dict[str, Any]:
    """Add a new bookmark."""
    return await get_client().create_link(
        params.url, params.name, params.description, params.type, params.collectionId, params.tags, get_user_token()
    )

@mcp.tool()
async def delete_link_by_id(params: GetLinkByIdParam, ctx: Context) -> dict[str, Any]:
    """Delete one bookmark."""
    return await get_client().delete_link_by_id(params.id, get_user_token())

@mcp.tool()
async def delete_links(params: DeleteLinksBulkParam, ctx: Context) -> dict[str, Any]:
    """Bulk delete bookmarks."""
    return await get_client().delete_links_bulk(params.linkIds, get_user_token())

@mcp.tool()
async def archive_link(params: GetLinkByIdParam, ctx: Context) -> dict[str, Any]:
    """Archive a link."""
    archived_links = await get_client().archive_link(params.id, get_user_token())
    return {"archived_links": archived_links}

# =============================================================================
# Tag Tools
# =============================================================================

@mcp.tool()
async def get_all_tags(ctx: Context) -> dict[str, Any]:
    """List all system tags."""
    all_tags = await get_client().get_all_tags(get_user_token())
    return {"all_tags": all_tags}

@mcp.tool()
async def delete_tag_by_id(params: GetCollectionByIdParam, ctx: Context) -> dict[str, Any]:
    """Remove a tag."""
    return await get_client().delete_tag_by_id(params.id, get_user_token())

# =============================================================================
# Utility Tools
# =============================================================================

@mcp.tool()
async def search_links(params: SearchLinksParam, ctx: Context) -> dict[str, Any]:
    """High-level keyword search across the library."""
    search_results = await get_client().search_links(
        params.searchQueryString, params.collectionId, params.tagId, params.sort, params.cursor, get_user_token()
    )
    return {"search_results": search_results}

@mcp.tool()
async def get_server_status(ctx: Context) -> dict[str, Any]:
    """Checks connectivity to the Linkwarden backend."""
    import httpx
    client = get_client()
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            response = await http_client.get(f"{client.base_url}/api/v1/users/me")
            return {"status": "connected", "backend_response": response.status_code}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}

@mcp.tool()
async def get_user_info(ctx: Context) -> dict[str, Any]:
    """Returns info about the authenticated user."""
    return await get_client().get_user_info(get_user_token())

# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Run the MCP server."""
    import sys
    import uvicorn
    if not os.getenv("LINKWARDEN_BASE_URL"):
        print("ERROR: LINKWARDEN_BASE_URL environment variable is required", file=sys.stderr)
        print("Example: export LINKWARDEN_BASE_URL=http://linkwarden-app:3000", file=sys.stderr)
        sys.exit(1)
    host = "0.0.0.0"
    port = 80
    path = "/mcp"
    app = mcp.http_app(path=path)
    app = AuthMiddleware(app)
    print(f"Starting Linkwarden MCP server on http://{host}:{port}{path}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
