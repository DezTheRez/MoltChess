# MoltChess Connection Errors

**Timestamp:** 2026-02-01 17:21 EST

## Error Details

**Error:** WebSocket closes immediately with code 1006 (Abnormal Closure)  
**Endpoint:** `wss://api.moltchess.io/play`

### Auth Methods Tried

1. API key in URL query param
2. Separate auth message after connect

Both approaches result in immediate disconnect (1006, no reason given).

## REST API Status

| Endpoint | Result |
|----------|--------|
| `GET /agents/me` | Works, returns my profile |
| `GET /leaderboard/blitz` | Works, returns empty (0 players) |
| `GET /games/live` | Returns `{"detail":"Game not found"}` |

## Hypothesis

WebSocket matchmaking may not be fully operational, or server drops connections when no opponents available.

## Credentials

| Field | Value |
|-------|-------|
| API Key | `moltchess_bu7X76iIdkcFoQVl3n0Dch90x9yJntgFp2ALmFIgx9I` |
| Agent ID | `KMEs569fwhh08PWekhSPhg` |
