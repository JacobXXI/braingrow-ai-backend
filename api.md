# API Documentation

## Search Videos

**Endpoint**: `GET /search/<searchQuery>`

**Description**:  
Searches for videos matching the given query in either title or tags.

**Parameters**:
- `searchQuery` (string, required): The search term to match against video titles and tags

**Response**:
- Returns JSON array of video objects
- Each video object contains:
  - `id` (integer): Unique video identifier
  - `title` (string): Video title
  - `description` (string): Video description
  - `url` (string): Video URL
  - `tags` (string): Comma-separated list of tags
  - `imageUrl` (string): Thumbnail image URL

**Example Request**:
```bash
GET /search/python