# Linkwarden MCP Multitenant Proxy Server

This repository contains a Model Context Protocol (MCP) server that acts as a secure, multi-tenant proxy between an AI Assistant and the Linkwarden backend API.

## Features

- **Identity Passthrough**: Extracts the `Authorization: Bearer <token>` header from incoming HTTP requests and forwards it to the Linkwarden API.
- **Multi-Tenancy**: Uses Python `contextvars` to maintain thread-safe user identity isolation and ensures all AI-driven actions are performed within the context of the authenticated user's permissions.
- **High Fidelity**: Tools are mapped directly to verified Linkwarden API endpoints.
- **TOON Optimization**: Automatically optimizes data payloads using TOON to reduce token consumption and maximize context window efficiency.

## Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `LINKWARDEN_BASE_URL` | The base URL of the Linkwarden instance. | Required |
| `LINKWARDEN_API_KEY` | A fallback API key for system-level operations (optional). | None |

## Installation & Local Development

1. Ensure you have Python 3.12+ installed.
2. Install dependencies using `uv` or `pip`:
   ```bash
   pip install fastmcp httpx pydantic uvicorn
   ```
3. Run the server:
   ```bash
   export LINKWARDEN_BASE_URL=http://your-linkwarden-url:3000
   python -m src.main
   ```

## Docker Deployment

Build and run the server using Docker:

```bash
docker build -t linkwarden-mcp .
docker run -p 80:80 -e LINKWARDEN_BASE_URL=http://your-linkwarden-url:3000 linkwarden-mcp
```

## TOON-Optimized

This MCP server leverages **TOON (Token-Optimized Object Notation)** to optimize data transmission between the Linkwarden API and AI models:

*   **Compact Data Format**: Converts verbose JSON responses into a streamlined TOON format, reducing token usage by approximately 30-60%
*   **Cost Efficiency**: Lower token consumption translates to reduced operational costs when using token-based LLM pricing
*   **Enhanced Context Management**: More data can fit within the AI's limited context window, enabling richer responses
*   **Faster Processing**: Smaller payloads lead to quicker inference times and improved workflow efficiency
*   **Seamless Integration**: The TOON optimization is applied automatically across multiple tool responses, requiring no changes to agent configurations
*   **Bidirectional Support**: The server can encode data to TOON for AI consumption and decode it back to standard JSON when needed for storage or further processing

## API Tool Mapping

The server implements 17 MCP tools organized into the following categories:

### 📚 Collections Management

Tools for managing bookmark collections:

- **`get_all_collections`** - Lists all available collections with metadata (name, description, icon, color, link count)
- **`get_collection_by_id`** - Retrieves detailed metadata for a specific collection by ID
- **`create_collection`** - Creates a new collection with name, description, color, icon, and icon weight
- **`delete_collection_by_id`** - Deletes a collection by its unique ID
- **`get_public_collection_by_id`** - Retrieves metadata for a public collection (accessible without authentication)

### 🔗 Links/Bookmarks Management

Tools for managing individual bookmarks and links:

- **`get_all_links`** - Primary browsing tool with deep filtering (by collection, tag, search, pinned status, sorting, pagination)
- **`get_link_by_id`** - Retrieves full details of a single bookmark including text content and archives
- **`create_link`** - Adds a new bookmark with URL, name, description, type, collection, and tags
- **`delete_link_by_id`** - Deletes a single bookmark by its unique ID
- **`delete_links`** - Bulk delete multiple bookmarks by providing an array of link IDs
- **`archive_link`** - Archives a link, preserving content while removing media archives to save space

### 🌐 Public Collections

Tools for accessing public (unauthenticated) collections:

- **`get_public_collections_links`** - Advanced filtering for links in public collections (search, pinned only, sorting, pagination)
- **`get_public_collections_tags`** - Retrieves all tags used in a specific public collection

### 🏷️ Tags Management

Tools for managing the system-wide tagging taxonomy:

- **`get_all_tags`** - Lists all system tags with their usage counts and metadata
- **`delete_tag_by_id`** - Removes a tag from the system

### 🔍 Search & Utilities

Tools for searching and system operations:

- **`search_links`** - High-level keyword search across the entire library with filtering by collection and tag
- **`get_server_status`** - Checks connectivity to the Linkwarden backend API
