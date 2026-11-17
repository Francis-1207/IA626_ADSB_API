## ADSB API

## JSON responses

Each response has `req`, `code`, `msg`, `sqltime`, and `data`.
`req` is the endpoint name, `code` is 1 if the request worked and 0 if it failed,
`msg` explains what happened, and `sqltime` is the query time in seconds.

- `/getData` returns a list of datapoints. If the request fails, the list is empty.
- `/countInPolygon` returns a count, like `{"count": 9368}`. If the request fails, `data` is `null`.
- `/getAvgSpeedByFlight` returns a list with a `flight_num` and `avg_speed` for each flight. If the request fails, the list is empty.