# UPS API Credential Rotation Implementation Summary

## Overview
Successfully implemented automatic credential rotation feature for `ups_label_only_filter.py` to handle UPS API rate limits and errors by automatically switching between two credential pairs.

## Changes Made

### 1. **New Imports**
- Added `dataclasses.dataclass` for credential container

### 2. **New Classes**

#### `UPSCredentials` (Dataclass)
Container for UPS API credentials with:
- `username`: UPS API client ID
- `password`: UPS API client secret
- `name`: Friendly name for logging (e.g., "Primary", "Secondary")

#### `CredentialManager` (Class)
Manages multiple credential pairs with automatic failover:
- `load_credentials()`: Loads credentials from environment variables
- `get_current_credentials()`: Returns currently active credentials
- `switch_to_next_credentials()`: Switches to next available credential pair
- `has_more_credentials()`: Checks if more credentials are available
- `get_credential_name()`: Returns name of current credential pair

### 3. **Modified Functions**

#### `get_ups_access_token(credentials, retry_count=3)`
**Changes:**
- Added `credentials` parameter to accept UPSCredentials object
- Uses credentials from parameter instead of global variables
- Logs credential name in success/error messages

#### `refresh_token_if_needed(current_token, token_timestamp, credentials, expiry_minutes=55)`
**Changes:**
- Added `credentials` parameter
- Passes credentials to `get_ups_access_token()`

#### `query_ups_tracking(tracking_number, access_token)`
**Changes:**
- Return type changed from `Optional[Dict]` to `Tuple[Optional[Dict], Optional[Dict]]`
- Returns tuple of `(response_data, error_info)`
- Detects HTTP 429 (rate limit) before raising exception
- Detects other HTTP errors (4xx, 5xx)
- Returns detailed error information including:
  - `status_code`: HTTP status code
  - `error_type`: `rate_limit`, `http_error`, `request_exception`, or `unexpected_error`
  - `error_message`: Detailed error description
  - `response_text`: Raw response text (for debugging)

#### `process_tracking_numbers(tracking_numbers, access_token, token_timestamp, credential_manager)`
**Changes:**
- Added `credential_manager` parameter
- Added `credential_switches` to results dictionary
- Tracks current credentials throughout processing
- Implements credential rotation logic:
  1. Detects rate limit or API errors
  2. Checks if more credentials are available
  3. Switches to next credential pair
  4. Obtains new access token with new credentials
  5. Retries failed tracking number with new credentials
  6. Continues processing with new credentials
- Enhanced error logging with error type and status code
- Logs credential switches with clear indicators

#### `print_summary(results)`
**Changes:**
- Added display of credential switches count

#### `main()`
**Changes:**
- Added Step 1: Initialize CredentialManager
- Renumbered subsequent steps (2-5)
- Gets initial credentials from credential manager
- Passes credential manager to `process_tracking_numbers()`
- Added logging for credential rotation feature

### 4. **Configuration Changes**
- Removed individual credential validation (now handled by CredentialManager)
- Kept `UPS_TOKEN_URL` and `UPS_TRACKING_URL` validation

## Environment Variables

### Required (Primary Credentials)
```bash
UPS_USERNAME=your_primary_client_id
UPS_PASSWORD=your_primary_client_secret
UPS_TOKEN_URL=https://onlinetools.ups.com/security/v1/oauth/token
UPS_TRACKING_URL=https://onlinetools.ups.com/api/track/v1/details/
```

### Optional (Secondary Credentials for Failover)
```bash
UPS_USERNAME_1=your_secondary_client_id
UPS_PASSWORD_1=your_secondary_client_secret
```

## Workflow

### Normal Operation (No Errors)
1. Load both credential pairs
2. Start with primary credentials
3. Process all tracking numbers
4. Auto-refresh token every 55 minutes

### With Rate Limit Error
1. Load both credential pairs
2. Start with primary credentials
3. Process tracking numbers until rate limit hit
4. Detect HTTP 429 error
5. Switch to secondary credentials
6. Get new access token
7. Retry failed tracking number
8. Continue with secondary credentials for remaining tracking numbers

### Error Handling
- **Rate Limit (HTTP 429)**: Triggers credential rotation
- **HTTP Errors (4xx, 5xx)**: Triggers credential rotation
- **Request Exceptions**: Triggers credential rotation
- **No More Credentials**: Logs error and continues with current credentials

## Statistics Tracked

New statistics in results:
- `credential_switches`: Number of times credentials were switched
- Enhanced `api_errors` with:
  - `error_type`: Type of error
  - `status_code`: HTTP status code (if available)

## Logging Enhancements

### Startup
```
✅ Loaded primary UPS credentials
✅ Loaded secondary UPS credentials
📊 Total credential pairs available: 2
🔑 Starting with Primary credentials
```

### Credential Switch
```
⚠️ API error detected (rate_limit): Rate limit exceeded (HTTP 429)
🔄 SWITCHING CREDENTIALS: Primary → Secondary
🔑 Obtaining new access token with new credentials...
✅ Successfully obtained token with new credentials
🔄 Retrying [tracking_number] with new credentials...
```

### Summary
```
🔑 Credential Switches: 1
```

## Testing Recommendations

1. **Test with both credentials**: Verify both credential pairs work
2. **Test with single credential**: Verify graceful handling when only primary exists
3. **Test rate limit scenario**: Simulate HTTP 429 to verify rotation
4. **Test error scenarios**: Verify handling of various HTTP errors
5. **Test token refresh**: Verify token refresh works with rotated credentials

## Backward Compatibility

✅ **Fully backward compatible**
- Works with single credential pair (no rotation)
- Existing `.env` files work without modification
- No breaking changes to output format

## Documentation

Created two documentation files:
1. `docs/UPS_CREDENTIAL_ROTATION.md` - User guide for the feature
2. `CREDENTIAL_ROTATION_IMPLEMENTATION.md` - Technical implementation details (this file)

## Next Steps

1. Test the implementation with real UPS API calls
2. Monitor credential switch frequency
3. Consider adding more credential pairs if needed
4. Consider implementing credential health monitoring
5. Consider implementing time-based rotation strategy

