# Model Context Protocol (MCP)

Official Repository: https://github.com/modelcontextprotocol

## Setup Instructions

### Create Virtual Environment

In your terminal, run these commands in sequence:

```bash
python -m venv venv
```

#### Activate the virtual environment:

**On Windows:**
```bash
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

#### To deactivate:
```bash
deactivate
```

### Install Dependencies

Once the environment is created, run the following command:

```bash
pip install -r requirements.txt
```

### Verify Installation

If you want to check if the packages are installed:

```bash
pip list
```

## Development Mode with MCP Inspector

To run your MCP server in development mode with the inspector:

```bash
mcp dev server.py

# Run a server directly
mcp run server.py

```

This will start the MCP inspector, allowing you to test and debug your MCP server tools interactively in a browser interface.


Kill a port 
lsof -ti:8050 | xargs kill -9
lsof -ti:6274 | xargs kill -9