#!/bin/bash

# 模拟 UniPortal 的启动脚本
# 创建 uniportal_storage 卷并填充测试数据

echo "=== 启动 UniPortal 模拟容器 ==="

# 1. 检查并创建 uniportal_storage 卷
echo "1. 检查 uniportal_storage 卷..."
if ! docker volume inspect uniportal_storage &>/dev/null; then
    echo "   创建 uniportal_storage 卷..."
    docker volume create uniportal_storage
fi

# 2. 启动模拟 UniPortal 容器，创建目录结构和测试数据
echo "2. 启动模拟 UniPortal 容器..."
docker run -d \
    --name uniportal-mock \
    -v uniportal_storage:/data/uniportal \
    alpine:latest \
    sh -c "
        # 创建模拟的目录结构
        mkdir -p /data/uniportal/portal_project_1/item_abc123/sample-project
        mkdir -p /data/uniportal/portal_project_1/item_xyz789/demo-app/src
        
        # 创建模拟的需求文件
        cat > /data/uniportal/portal_project_1/item_abc123/sample-project/requirements.json << 'EOF'
[
    {
        \"id\": \"req_001\",
        \"title\": \"用户登录功能\",
        \"description\": \"系统应支持用户通过用户名和密码登录\",
        \"module\": \"用户管理\",
        \"type\": \"功能需求\",
        \"priority\": \"高\"
    },
    {
        \"id\": \"req_002\",
        \"title\": \"数据导出功能\",
        \"description\": \"系统应支持将数据导出为Excel格式\",
        \"module\": \"数据管理\",
        \"type\": \"功能需求\",
        \"priority\": \"中\"
    }
]
EOF
        
        # 创建模拟的源码文件
        cat > /data/uniportal/portal_project_1/item_xyz789/demo-app/src/main.py << 'EOF'
def hello_world():
    print(\"Hello, UniPortal!\")

if __name__ == \"__main__\":
    hello_world()
EOF
        
        cat > /data/uniportal/portal_project_1/item_xyz789/demo-app/requirements.json << 'EOF'
[
    {
        \"id\": \"req_003\",
        \"title\": \"API接口\",
        \"description\": \"提供RESTful API接口\",
        \"module\": \"接口层\",
        \"type\": \"功能需求\",
        \"priority\": \"高\"
    }
]
EOF
        
        echo \"UniPortal 模拟数据创建完成\"
        # 保持容器运行
        tail -f /dev/null
    "

echo "3. 等待模拟容器启动..."
sleep 2

# 4. 验证数据创建
echo "4. 验证数据..."
docker exec uniportal-mock ls -la /data/uniportal/portal_project_1/

echo ""
echo "=== UniPortal 模拟容器已启动 ==="
echo "卷: uniportal_storage"
echo "项目列表:"
echo "  - item_abc123 (sample-project)"
echo "  - item_xyz789 (demo-app)"
echo ""
echo "现在可以运行: docker compose -f docker-compose.uniportal.yml up"
