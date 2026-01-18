#!/bin/bash
#
# Log Management Utility
# AI Anti-Spam Shield Project
#
# Usage: ./scripts/log-manager.sh [command] [options]
#

set -e

# Configuration
LOG_DIR="${LOG_DIR:-$(dirname "$0")/../logs}"
RETENTION_DAYS="${LOG_RETENTION_DAYS:-30}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  AI Anti-Spam Shield - Log Manager${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_usage() {
    print_header
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  status        Show log directory status and statistics"
    echo "  tail          Tail combined logs (use -f for follow)"
    echo "  errors        Show recent errors"
    echo "  search        Search logs for a pattern"
    echo "  clean         Remove logs older than retention period"
    echo "  archive       Archive current logs"
    echo "  rotate        Force log rotation"
    echo ""
    echo "Options:"
    echo "  -d, --dir     Specify log directory"
    echo "  -n, --lines   Number of lines to show (default: 50)"
    echo "  -f, --follow  Follow log output"
    echo "  -s, --service Service to filter (backend, model-service)"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 tail -f -s backend"
    echo "  $0 errors -n 100"
    echo "  $0 search \"error\" -s model-service"
    echo "  $0 clean --days 7"
    echo ""
}

get_size() {
    local path=$1
    if [ -d "$path" ]; then
        du -sh "$path" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

count_files() {
    local path=$1
    local pattern=$2
    find "$path" -name "$pattern" 2>/dev/null | wc -l | tr -d ' '
}

cmd_status() {
    print_header
    echo ""
    echo -e "${GREEN}Log Directory:${NC} $LOG_DIR"
    echo ""

    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${YELLOW}Log directory does not exist yet.${NC}"
        return
    fi

    echo -e "${GREEN}Directory Structure:${NC}"
    echo "├── backend/        $(get_size "$LOG_DIR/backend")"
    echo "├── model-service/  $(get_size "$LOG_DIR/model-service")"
    echo "└── combined/       $(get_size "$LOG_DIR/combined")"
    echo ""

    echo -e "${GREEN}Statistics:${NC}"
    echo "  Total Size:       $(get_size "$LOG_DIR")"
    echo "  Log Files:        $(count_files "$LOG_DIR" "*.log")"
    echo "  Archived Files:   $(count_files "$LOG_DIR" "*.gz")"
    echo ""

    echo -e "${GREEN}Recent Log Files:${NC}"
    find "$LOG_DIR" -name "*.log" -type f -printf "%T+ %p\n" 2>/dev/null | sort -r | head -10 | while read line; do
        echo "  $line"
    done
    echo ""
}

cmd_tail() {
    local follow=""
    local lines=50
    local service=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow) follow="-f"; shift ;;
            -n|--lines) lines=$2; shift 2 ;;
            -s|--service) service=$2; shift 2 ;;
            *) shift ;;
        esac
    done

    local log_path="$LOG_DIR"
    if [ -n "$service" ]; then
        log_path="$LOG_DIR/$service"
    fi

    if [ ! -d "$log_path" ]; then
        echo -e "${RED}Log directory not found: $log_path${NC}"
        exit 1
    fi

    local combined_log=$(find "$log_path" -name "combined*.log" -type f | sort -r | head -1)

    if [ -z "$combined_log" ]; then
        echo -e "${YELLOW}No combined log found in $log_path${NC}"
        exit 1
    fi

    echo -e "${GREEN}Tailing:${NC} $combined_log"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    tail -n "$lines" $follow "$combined_log"
}

cmd_errors() {
    local lines=50
    local service=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--lines) lines=$2; shift 2 ;;
            -s|--service) service=$2; shift 2 ;;
            *) shift ;;
        esac
    done

    local log_path="$LOG_DIR"
    if [ -n "$service" ]; then
        log_path="$LOG_DIR/$service"
    fi

    echo -e "${RED}Recent Errors:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    find "$log_path" -name "error*.log" -type f -exec cat {} \; 2>/dev/null | tail -n "$lines"
}

cmd_search() {
    local pattern=$1
    shift

    local service=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--service) service=$2; shift 2 ;;
            *) shift ;;
        esac
    done

    if [ -z "$pattern" ]; then
        echo -e "${RED}Error: Search pattern required${NC}"
        exit 1
    fi

    local log_path="$LOG_DIR"
    if [ -n "$service" ]; then
        log_path="$LOG_DIR/$service"
    fi

    echo -e "${GREEN}Searching for:${NC} $pattern"
    echo -e "${GREEN}In:${NC} $log_path"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    grep -rn --color=always "$pattern" "$log_path"/*.log 2>/dev/null || echo "No matches found"
}

cmd_clean() {
    local days=$RETENTION_DAYS

    while [[ $# -gt 0 ]]; do
        case $1 in
            --days) days=$2; shift 2 ;;
            *) shift ;;
        esac
    done

    echo -e "${YELLOW}Cleaning logs older than $days days...${NC}"

    local count=$(find "$LOG_DIR" -name "*.log" -type f -mtime +$days 2>/dev/null | wc -l)

    if [ "$count" -eq 0 ]; then
        echo -e "${GREEN}No old logs to clean.${NC}"
        return
    fi

    echo -e "${YELLOW}Found $count log files to remove.${NC}"
    read -p "Continue? (y/N) " confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        find "$LOG_DIR" -name "*.log" -type f -mtime +$days -delete 2>/dev/null
        echo -e "${GREEN}Cleaned $count log files.${NC}"
    else
        echo -e "${YELLOW}Cancelled.${NC}"
    fi
}

cmd_archive() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local archive_dir="$LOG_DIR/archives"

    mkdir -p "$archive_dir"

    echo -e "${GREEN}Archiving logs to:${NC} $archive_dir/logs_$timestamp.tar.gz"

    tar -czf "$archive_dir/logs_$timestamp.tar.gz" \
        -C "$LOG_DIR" \
        --exclude="archives" \
        . 2>/dev/null

    echo -e "${GREEN}Archive created successfully.${NC}"
    echo -e "${GREEN}Size:${NC} $(get_size "$archive_dir/logs_$timestamp.tar.gz")"
}

# Main
case "${1:-}" in
    status)
        shift
        cmd_status "$@"
        ;;
    tail)
        shift
        cmd_tail "$@"
        ;;
    errors)
        shift
        cmd_errors "$@"
        ;;
    search)
        shift
        cmd_search "$@"
        ;;
    clean)
        shift
        cmd_clean "$@"
        ;;
    archive)
        shift
        cmd_archive "$@"
        ;;
    *)
        print_usage
        ;;
esac
