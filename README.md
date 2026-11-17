# ADSB API

## JSON responses

`req` is the endpoint name. `code` is 1 for success and 0 for failure.
`msg` explains what happened. `sqltime` is the query time in seconds.
`data` holds the result.

### JSON schema

```json
{
  "type": "object",
  "required": ["req", "code", "msg", "sqltime", "data"],
  "properties": {
    "req": { "type": "string" },
    "code": { "type": "integer", "enum": [0, 1] },
    "msg": { "type": "string" },
    "sqltime": { "type": "number", "minimum": 0 }
  },
  "oneOf": [
    {
      "properties": {
        "req": { "const": "getData" },
        "data": {
          "type": "array",
          "maxItems": 500,
          "items": { "type": "object" }
        }
      }
    },
    {
      "properties": {
        "req": { "const": "countInPolygon" },
        "data": {
          "type": ["object", "null"],
          "required": ["count"],
          "properties": {
            "count": { "type": "integer", "minimum": 0 }
          }
        }
      }
    },
    {
      "properties": {
        "req": { "const": "getAvgSpeedByFlight" },
        "data": {
          "type": "array",
          "maxItems": 500,
          "items": {
            "type": "object",
            "required": ["flight_num", "avg_speed"],
            "properties": {
              "flight_num": { "type": ["string", "null"] },
              "avg_speed": { "type": ["number", "null"] }
            }
          }
        }
      }
    }
  ]
}
```