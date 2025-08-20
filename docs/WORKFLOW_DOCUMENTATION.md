# 17Track API Workflow Implementation

## Overview
The tracking_17.py pipeline now implements the correct 17Track API workflow as per their documentation, which requires a two-step process with a mandatory 5-minute wait between steps.

## Workflow Steps

### Step 1: Registration
- **Action**: Register tracking numbers with 17Track API
- **Endpoint**: `https://api.17track.net/track/v2.2/register`
- **Method**: POST
- **Payload**: Array of objects with "number" and "carrier" fields
- **Duration**: ~1 second

### Step 2: Processing Wait
- **Action**: Wait for 17Track to process the registered tracking numbers
- **Duration**: 5 minutes (300 seconds)
- **Reason**: Required by 17Track documentation for proper data processing
- **Progress**: Minute-by-minute countdown display

### Step 3: Retrieval
- **Action**: Retrieve tracking information for registered numbers
- **Endpoint**: `https://api.17track.net/track/v2.4/gettrackinfo`
- **Method**: POST
- **Duration**: ~1 second

## Expected Timeline

### For 30 tracking numbers (1 batch):
```
00:00 - Start pipeline
00:01 - Registration complete
00:01 - Start 5-minute wait
05:01 - Retrieval complete
05:02 - Export files complete
```

### For 60+ tracking numbers (multiple batches):
```
00:00 - Start pipeline
00:01 - Batch 1 registration complete
00:01 - Start 5-minute wait for batch 1
05:01 - Batch 1 retrieval complete
05:02 - Batch 2 registration complete
05:02 - Start 5-minute wait for batch 2
10:02 - Batch 2 retrieval complete
10:03 - Export files complete
```

## Log Output Example
```
📝 Step 1: Registering batch 1 tracking numbers
📝 Registering 30 tracking numbers with 17Track API
✅ Registration successful
⏳ Waiting 5.0 minutes for 17Track to process registered tracking numbers...
⏰ 5m 0s remaining for processing...
⏰ 4m 0s remaining for processing...
⏰ 3m 0s remaining for processing...
⏰ 2m 0s remaining for processing...
⏰ 1m 0s remaining for processing...
📊 Step 2: Retrieving tracking info for batch 1
🔍 Getting tracking info for 30 tracking numbers
✅ Tracking query successful
✅ Batch 1 completed successfully (registered + retrieved)
```

## Key Implementation Details

1. **Mandatory Wait**: The 5-minute wait is required by 17Track documentation and cannot be skipped
2. **Progress Tracking**: Real-time countdown shows remaining wait time
3. **Error Handling**: Separate error handling for registration and retrieval steps
4. **Data Structure**: Results include both registration and tracking data
5. **Backward Compatibility**: CSV export format remains unchanged

## Usage Notes

- Plan for approximately 5+ minutes execution time per batch
- The wait time is necessary for 17Track to properly process tracking data
- Interrupting the wait period may result in incomplete or missing tracking information
- Multiple batches will each require their own 5-minute processing period
