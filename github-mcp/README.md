# GitHub MCP Server Setup

This folder contains the setup for using GitHub's official MCP server to interact with GitHub repositories, issues, pull requests, and more through AI assistants.

## 🚀 Quick Start

### 1. Get a GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name (e.g., "MCP Server")
4. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:packages` (Download packages from GitHub Package Registry)
   - `read:org` (Read org and team membership, read org projects)
5. Click "Generate token" and **copy the token**

### 2. Configure Environment Variables

Edit the `.env` file and add your GitHub token:

```bash
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
```

Also make sure you have your Gemini API key in the parent `.env` file:
```bash
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Pull the Docker Image

```bash
docker pull ghcr.io/github/github-mcp-server
```

### 4. Test the Connection

```bash
python test-connection.py
```

This will:
- Start the GitHub MCP server via Docker
- Connect to it via stdio
- List all available tools
- Try a sample GitHub operation

### 5. Use with Gemini

```bash
python client-gemini-github.py
```

This demonstrates how to use Gemini with GitHub MCP tools to perform GitHub operations through natural language.

## 📦 What's Included

### Files Created

1. **`.env`** - Environment variables (GitHub token, toolsets)
2. **`server-config.json`** - MCP server configuration for other clients
3. **`test-connection.py`** - Simple test script to verify GitHub MCP is working
4. **`client-gemini-github.py`** - Full Gemini client with GitHub MCP integration
5. **`README.md`** - This file

## 🔧 Available Toolsets

The GitHub MCP server organizes its functionality into toolsets. You can enable specific ones in `.env`:

```bash
GITHUB_TOOLSETS=repos,issues,pull_requests,actions,code_security
```

### Toolset Options:

- **`repos`** - Repository operations (list, search, get files, commits)
- **`issues`** - Issue management (create, read, update, close issues)
- **`pull_requests`** - PR operations (create, review, merge pull requests)
- **`actions`** - GitHub Actions (workflows, runs, logs)
- **`code_security`** - Security features (Dependabot, code scanning)
- **`discussions`** - GitHub Discussions

## 📝 Example Use Cases

### With Gemini Client

```python
# Example queries you can ask:
queries = [
    "List my recent repositories",
    "Show me open issues in my repo",
    "Create an issue in owner/repo with title 'Bug fix needed'",
    "Get the contents of README.md from owner/repo",
    "Show me recent pull requests in owner/repo",
    "Check the status of GitHub Actions in owner/repo",
]
```

### Customizing the Client

Edit `client-gemini-github.py` and modify the `queries` list in the `main()` function:

```python
async def main():
    client = GitHubMCPGeminiClient()
    await client.connect_to_github_mcp()
    
    queries = [
        "Your custom query here",
    ]
    
    for query in queries:
        response = await client.process_query(query)
        print(response)
    
    await client.cleanup()
```

## 🐳 Docker vs Local Build

### Using Docker (Recommended)

- ✅ Easiest setup
- ✅ No Go dependencies needed
- ✅ Consistent environment
- ✅ Auto-updates via new image pulls

This is configured by default in all scripts.

### Building from Source

If you prefer to build from source:

1. Clone the repository:
```bash
git clone https://github.com/github/github-mcp-server.git
cd github-mcp-server
```

2. Build the server:
```bash
cd cmd/github-mcp-server
go build
```

3. Update scripts to use the binary instead of Docker:
```python
server_params = StdioServerParameters(
    command="/path/to/github-mcp-server",
    args=["stdio"],
    env={
        "GITHUB_PERSONAL_ACCESS_TOKEN": github_token,
        "GITHUB_TOOLSETS": toolsets
    }
)
```

## 🔐 Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use minimum required scopes** for your token
3. **Rotate tokens periodically**
4. **Store tokens in environment variables**, not in code
5. **Restrict file permissions**: `chmod 600 .env`

## 🐛 Troubleshooting

### "Docker daemon is not running"
Start Docker Desktop or the Docker daemon:
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

### "GITHUB_PERSONAL_ACCESS_TOKEN is not set"
Make sure you've:
1. Created a `.env` file in this directory
2. Added your GitHub token to it
3. The token is not the placeholder text

### "Permission denied" errors
Your token might not have the required scopes. Regenerate with `repo`, `read:packages`, and `read:org` scopes.

### Tools not working as expected
Check the toolsets configuration in `.env`. You might need to enable specific toolsets for certain operations.

## 📚 Additional Resources

- [GitHub MCP Server Repository](https://github.com/github/github-mcp-server)
- [Model Context Protocol Documentation](https://github.com/modelcontextprotocol)
- [GitHub Personal Access Tokens Guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

## 🤝 Contributing

This is a setup example. For contributing to the actual GitHub MCP server, visit:
https://github.com/github/github-mcp-server

## 📄 License

The GitHub MCP server is licensed under MIT. This setup guide is provided as-is for educational purposes.
