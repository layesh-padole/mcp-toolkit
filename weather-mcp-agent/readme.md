# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather information using the OpenWeather API.

## Purpose

This MCP server provides a secure interface for AI assistants to access current weather data and forecasts for any city worldwide. It supports temperature unit conversions and multiple measurement systems.

## Features

### Current Implementation

- **`get_current_weather`** - Get real-time weather conditions for any city including temperature, humidity, wind speed, and conditions. Supports both Celsius (metric) and Fahrenheit (imperial) units.

- **`get_forecast`** - Get a 5-day weather forecast with 3-hour intervals for any city. Shows detailed predictions including temperature and weather conditions throughout each day.

- **`convert_temperature`** - Convert temperatures between Celsius, Fahrenheit, and Kelvin. Useful for quick unit conversions without making API calls.

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- OpenWeather API key (free tier available at https://openweathermap.org/api)
  - Sign up at https://openweathermap.org/home/sign_up
  - Free tier includes 1,000 API calls per day
  - API key activation takes 10 minutes to 2 hours

## Installation

See the step-by-step instructions provided with the files.

## Usage Examples

In Claude Desktop, you can ask:

- "What's the weather in London?" - Get current weather conditions
- "Show me the forecast for Tokyo" - Get 5-day forecast
- "What's the weather in New York in Fahrenheit?" - Get weather in imperial units
- "Give me the weather forecast for Paris" - Get detailed 5-day forecast
- "Convert 25 Celsius to Fahrenheit" - Convert temperature units
- "Convert 98.6 fahrenheit to celsius" - Temperature conversion
- "What's 300 Kelvin in Celsius?" - Scientific temperature conversion

## Architecture
```
Claude Desktop → MCP Gateway → Weather MCP Server → OpenWeather API
                                        ↓
                              Docker Desktop Secrets
                              (OPENWEATHER_API_KEY)
```

## API Information

This server uses the OpenWeather API:
- Current Weather API: https://api.openweathermap.org/data/2.5/weather
- 5-Day Forecast API: https://api.openweathermap.org/data/2.5/forecast

Both endpoints support:
- Geographic coordinates lookup by city name
- Multiple units: metric (Celsius), imperial (Fahrenheit), standard (Kelvin)
- JSON response format
- Global city coverage (200,000+ cities)

## Development

### Local Testing
```bash
# Set environment variable for testing
export OPENWEATHER_API_KEY="your-api-key-here"

# Run directly
python weather_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python weather_server.py
```

### Adding New Tools

1. Add the function to `weather_server.py`
2. Decorate with `@mcp.tool()`
3. Ensure single-line docstring
4. Use string parameters with empty string defaults
5. Return formatted string
6. Update the catalog entry with the new tool name
7. Rebuild the Docker image

### Possible Enhancements

- Add geocoding to accept coordinates
- Include weather alerts and warnings
- Add historical weather data
- Support for hourly forecasts
- Air quality index information
- UV index and sunrise/sunset times

## Troubleshooting

### Tools Not Appearing

- Verify Docker image built successfully: `docker images | grep weather`
- Check catalog file syntax: `cat ~/.docker/mcp/catalogs/custom.yaml`
- Verify registry file updated correctly
- Ensure Claude Desktop config includes custom catalog
- Restart Claude Desktop completely

### API Errors

- "Invalid API key": Verify secret with `docker mcp secret list`
- "City not found": Check city name spelling
- "API Error 429": Rate limit exceeded (1,000 calls/day on free tier)
- "API Error 401": API key not activated yet (wait 10 min - 2 hours)

### Authentication Errors

- Verify secret set: `docker mcp secret list`
- Ensure secret name matches: `OPENWEATHER_API_KEY`
- Check API key is valid at https://home.openweathermap.org/api_keys
- Remember: New API keys take 10 minutes to 2 hours to activate

## Security Considerations

- All API keys stored in Docker Desktop secrets
- Never hardcode credentials in source code
- Running as non-root user (mcpuser)
- API key never logged or exposed
- Rate limiting enforced by OpenWeather (1,000 calls/day free tier)

## Rate Limits

OpenWeather Free Tier:
- 1,000 API calls per day
- 60 calls per minute
- Current weather and 5-day forecast included

For higher limits, consider OpenWeather paid plans.

## License

MIT License