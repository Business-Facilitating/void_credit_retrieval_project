# UPS API Credential Rotation Feature

## Overview

The UPS Label-Only Filter (`ups_label_only_filter.py`) now supports automatic credential rotation to handle rate limits and API errors. When the primary credential pair encounters a rate limit (HTTP 429) or any API error, the system automatically switches to the secondary credential pair and continues processing.

## Features

### 1. **Multiple Credential Support**
- Supports up to 2 credential pairs (can be extended)
- Primary credentials: `UPS_USERNAME` / `UPS_PASSWORD`
- Secondary credentials: `UPS_USERNAME_1` / `UPS_PASSWORD_1`

### 2. **Automatic Failover**
- Detects rate limit errors (HTTP 429)
- Detects other API errors (HTTP 4xx, 5xx)
- Automatically switches to next available credential pair
- Retries the failed tracking number with new credentials

### 3. **Enhanced Error Detection**
- Rate limit detection (HTTP 429)
- HTTP error detection (4xx, 5xx status codes)
- Request exceptions
- Detailed error logging with error type and status code

### 4. **Comprehensive Logging**
- Logs credential loading at startup
- Logs credential switches with clear indicators
- Logs token refresh events
- Tracks credential switch statistics

## Configuration

### Environment Variables

Add both credential pairs to your `.env` file:

```bash
# Primary UPS API Credentials
UPS_USERNAME=your_primary_client_id
UPS_PASSWORD=your_primary_client_secret

# Secondary UPS API Credentials (for failover)
UPS_USERNAME_1=your_secondary_client_id
UPS_PASSWORD_1=your_secondary_client_secret

# UPS API Endpoints
UPS_TOKEN_URL=https://onlinetools.ups.com/security/v1/oauth/token
UPS_TRACKING_URL=https://onlinetools.ups.com/api/track/v1/details/
```

### Credential Pairs

Your `.env` file already contains both credential pairs:
- **Primary**: `UPS_USERNAME` / `UPS_PASSWORD`
- **Secondary**: `UPS_USERNAME_1` / `UPS_PASSWORD_1`

## How It Works

### 1. **Initialization**
```
🔑 Step 1: Initializing credential manager...
✅ Loaded primary UPS credentials
✅ Loaded secondary UPS credentials
📊 Total credential pairs available: 2
```

### 2. **Processing with Primary Credentials**
- Starts with primary credentials
- Processes tracking numbers normally
- Monitors for API errors

### 3. **Error Detection & Rotation**
When a rate limit or API error is detected:
```
⚠️ API error detected (rate_limit): Rate limit exceeded (HTTP 429)
🔄 SWITCHING CREDENTIALS: Primary → Secondary
🔑 Obtaining new access token with new credentials...
✅ Successfully obtained token with new credentials
🔄 Retrying [tracking_number] with new credentials...
```

### 4. **Continued Processing**
- All remaining tracking numbers use the new credentials
- Token refresh continues with the active credential pair
- Statistics track credential switches

## Output & Statistics

### Enhanced Summary
```
🎯 UPS LABEL-ONLY FILTER SUMMARY
============================================================
📊 Total Processed: 150
✅ Label-Only Found: 45
❌ Excluded: 100
🚫 API Errors: 5
🔄 Token Refreshes: 2
🔑 Credential Switches: 1
📈 Label-Only Rate: 30.0%
```

### Error Information
API errors now include detailed information:
- `error_type`: `rate_limit`, `http_error`, `request_exception`, or `unexpected_error`
- `status_code`: HTTP status code (if available)
- `error_message`: Detailed error description

## Usage

Run the script normally - credential rotation is automatic:

```bash
poetry run python src/src/ups_label_only_filter.py
```

## Behavior

### With Both Credentials Available
1. Starts with primary credentials
2. On rate limit/error → switches to secondary
3. Continues with secondary for all remaining tracking numbers

### With Only Primary Credentials
1. Starts with primary credentials
2. On rate limit/error → logs warning but continues
3. No automatic failover (only one credential pair)

### Retry Logic
- When switching credentials, the failed tracking number is **automatically retried**
- If retry also fails, the error is logged and processing continues
- No tracking numbers are skipped due to credential rotation

## Benefits

1. **Increased Throughput**: Process more tracking numbers without hitting rate limits
2. **Automatic Recovery**: No manual intervention needed when rate limits are hit
3. **Transparent Operation**: Credential rotation happens automatically
4. **Detailed Tracking**: Full visibility into when and why credentials were switched
5. **Backward Compatible**: Works with single credential pair (no rotation)

## Technical Details

### CredentialManager Class
- Manages multiple credential pairs
- Tracks current active credentials
- Provides failover logic
- Thread-safe for future enhancements

### Error Detection
- HTTP 429: Rate limit exceeded
- HTTP 4xx/5xx: Client/server errors
- Request exceptions: Network/timeout errors
- All trigger credential rotation

### Token Management
- Each credential pair has its own token
- Tokens auto-refresh every 55 minutes
- Token refresh uses the currently active credentials

## Limitations

1. **Maximum 2 Credential Pairs**: Currently supports primary + secondary (can be extended)
2. **One-Way Rotation**: Does not rotate back to primary after switching
3. **No Rate Limit Prediction**: Switches only after hitting the limit
4. **Sequential Processing**: Processes one tracking number at a time

## Future Enhancements

- Support for 3+ credential pairs
- Intelligent rate limit prediction
- Parallel processing with credential pooling
- Automatic credential health monitoring
- Time-based credential rotation

