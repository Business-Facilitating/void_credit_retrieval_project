#!/bin/bash
# UPS Web Automation with Virtual Display (Xvfb)
# This script allows running the browser automation on headless Linux servers

# Configuration
DISPLAY_NUM=99
SCREEN_RESOLUTION="1920x1080x24"
LOG_DIR="logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p "$LOG_DIR"

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}🚀 UPS Web Automation with Virtual Display${NC}"
echo -e "${GREEN}============================================================${NC}"

# Check if Xvfb is installed
if ! command -v Xvfb &> /dev/null; then
    echo -e "${RED}❌ Error: Xvfb is not installed${NC}"
    echo -e "${YELLOW}Install it with: sudo apt-get install -y xvfb${NC}"
    exit 1
fi

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Error: Poetry is not installed${NC}"
    echo -e "${YELLOW}Install it with: curl -sSL https://install.python-poetry.org | python3 -${NC}"
    exit 1
fi

# Kill any existing Xvfb on this display
echo -e "${YELLOW}🔍 Checking for existing Xvfb processes...${NC}"
if pgrep -f "Xvfb :$DISPLAY_NUM" > /dev/null; then
    echo -e "${YELLOW}⚠️  Killing existing Xvfb on display :$DISPLAY_NUM${NC}"
    pkill -f "Xvfb :$DISPLAY_NUM"
    sleep 1
fi

# Start Xvfb
echo -e "${GREEN}🖥️  Starting virtual display :$DISPLAY_NUM ($SCREEN_RESOLUTION)...${NC}"
Xvfb :$DISPLAY_NUM -screen 0 $SCREEN_RESOLUTION > "$LOG_DIR/xvfb_$TIMESTAMP.log" 2>&1 &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Check if Xvfb started successfully
if ! ps -p $XVFB_PID > /dev/null; then
    echo -e "${RED}❌ Error: Failed to start Xvfb${NC}"
    echo -e "${YELLOW}Check logs: $LOG_DIR/xvfb_$TIMESTAMP.log${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual display started (PID: $XVFB_PID)${NC}"

# Export display variable
export DISPLAY=:$DISPLAY_NUM
echo -e "${GREEN}📺 Display set to: $DISPLAY${NC}"

# Run the automation
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}🤖 Running UPS automation...${NC}"
echo -e "${GREEN}============================================================${NC}"

poetry run python src/src/ups_web_login.py 2>&1 | tee "$LOG_DIR/automation_$TIMESTAMP.log"

# Capture exit code
EXIT_CODE=${PIPESTATUS[0]}

# Display results
echo -e "${GREEN}============================================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Automation completed successfully${NC}"
else
    echo -e "${RED}❌ Automation failed with exit code: $EXIT_CODE${NC}"
fi
echo -e "${GREEN}============================================================${NC}"

# Show log locations
echo -e "${YELLOW}📁 Logs saved to:${NC}"
echo -e "   - Automation: $LOG_DIR/automation_$TIMESTAMP.log"
echo -e "   - Xvfb: $LOG_DIR/xvfb_$TIMESTAMP.log"

# Show screenshot location
if [ -d "data/output" ]; then
    SCREENSHOT_COUNT=$(ls -1 data/output/*.png 2>/dev/null | wc -l)
    if [ $SCREENSHOT_COUNT -gt 0 ]; then
        echo -e "${YELLOW}📸 Screenshots: data/output/ ($SCREENSHOT_COUNT files)${NC}"
        echo -e "   Latest screenshots:"
        ls -lt data/output/*.png | head -5 | awk '{print "   - " $9}'
    fi
fi

# Kill Xvfb
echo -e "${YELLOW}🛑 Stopping virtual display...${NC}"
kill $XVFB_PID 2>/dev/null
wait $XVFB_PID 2>/dev/null

echo -e "${GREEN}✅ Cleanup complete${NC}"

# Exit with same code as automation
exit $EXIT_CODE

