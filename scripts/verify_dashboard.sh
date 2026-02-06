#!/bin/bash

# Dashboard视图验证脚本
# 用于快速验证Dashboard视图功能是否正常工作

echo "=========================================="
echo "Dashboard视图功能验证"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} 文件存在: $1"
        return 0
    else
        echo -e "${RED}✗${NC} 文件缺失: $1"
        return 1
    fi
}

check_content() {
    if grep -q "$2" "$1"; then
        echo -e "${GREEN}✓${NC} $1 包含 '$2'"
        return 0
    else
        echo -e "${RED}✗${NC} $1 缺少 '$2'"
        return 1
    fi
}

# 计数器
total_checks=0
passed_checks=0

echo "1. 检查核心文件存在性..."
echo "----------------------------"

files=(
    "web_service/static/js/dashboard-view.js"
    "web_service/static/css/timeline.css"
    "tests/test_dashboard_simple.py"
    "docs/09_dashboard_view_implementation_report.md"
)

for file in "${files[@]}"; do
    total_checks=$((total_checks + 1))
    if check_file "$file"; then
        passed_checks=$((passed_checks + 1))
    fi
done
echo ""

echo "2. 检查workspace.html集成..."
echo "----------------------------"

total_checks=$((total_checks + 1))
if check_content "web_service/templates/workspace.html" "timeline.css"; then
    passed_checks=$((passed_checks + 1))
fi

total_checks=$((total_checks + 1))
if check_content "web_service/templates/workspace.html" "dashboard-view.js"; then
    passed_checks=$((passed_checks + 1))
fi
echo ""

echo "3. 检查workspace.js集成..."
echo "----------------------------"

total_checks=$((total_checks + 1))
if check_content "web_service/static/js/workspace.js" "DashboardView"; then
    passed_checks=$((passed_checks + 1))
fi

total_checks=$((total_checks + 1))
if check_content "web_service/static/js/workspace.js" "cleanupView"; then
    passed_checks=$((passed_checks + 1))
fi

total_checks=$((total_checks + 1))
if check_content "web_service/static/js/workspace.js" "WorkspaceApp"; then
    passed_checks=$((passed_checks + 1))
fi
echo ""

echo "4. 检查DashboardView模块功能..."
echo "----------------------------"

total_checks=$((total_checks + 1))
if check_content "web_service/static/js/dashboard-view.js" "loadData"; then
    passed_checks=$((passed_checks + 1))
fi

total_checks=$((total_checks + 1))
if check_content "web_service/static/js/dashboard-view.js" "renderDashboard"; then
    passed_checks=$((passed_checks + 1))
fi

total_checks=$((total_checks + 1))
if check_content "web_service/static/js/dashboard-view.js" "handleManualRefresh"; then
    passed_checks=$((passed_checks + 1))
fi

total_checks=$((total_checks + 1))
if check_content "web_service/static/js/dashboard-view.js" "startAutoRefresh"; then
    passed_checks=$((passed_checks + 1))
fi
echo ""

echo "5. 检查后端API端点..."
echo "----------------------------"

total_checks=$((total_checks + 1))
if check_content "web_service/routes/dashboard.py" "@router.get(\"/stats\")"; then
    passed_checks=$((passed_checks + 1))
fi

total_checks=$((total_checks + 1))
if check_content "web_service/routes/dashboard.py" "@router.get(\"/activity\")"; then
    passed_checks=$((passed_checks + 1))
fi

total_checks=$((total_checks + 1))
if check_content "web_service/routes/dashboard.py" "@router.get(\"/overview\")"; then
    passed_checks=$((passed_checks + 1))
fi
echo ""

echo "6. 运行单元测试..."
echo "----------------------------"

if python3 -m pytest tests/test_dashboard_simple.py -v --tb=short > /tmp/test_output.log 2>&1; then
    echo -e "${GREEN}✓${NC} 所有测试通过"
    passed_checks=$((passed_checks + 1))
else
    echo -e "${RED}✗${NC} 部分测试失败"
    cat /tmp/test_output.log
fi
total_checks=$((total_checks + 1))
echo ""

echo "=========================================="
echo "验证结果汇总"
echo "=========================================="
echo -e "通过: ${GREEN}${passed_checks}${NC}/${total_checks}"

if [ $passed_checks -eq $total_checks ]; then
    echo -e "${GREEN}所有检查通过！✓${NC}"
    echo ""
    echo "下一步："
    echo "1. 启动Web服务: python3 -m web_service.main"
    echo "2. 访问: http://localhost:8000/workspace"
    echo "3. 检查Dashboard视图功能"
    exit 0
else
    echo -e "${RED}部分检查失败！✗${NC}"
    echo "请检查上述失败项并修复。"
    exit 1
fi
