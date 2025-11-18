#!/bin/bash

# 启动 Edge 浏览器并开启调试端口
# 使用 Profile 1（您常用的配置）

echo "🚀 启动 Microsoft Edge 浏览器（调试模式）"
echo "📂 使用 Profile: Profile 1"
echo "🔌 调试端口: 9222"
echo ""

# 关闭现有的 Edge 进程
echo "⏹️  关闭现有 Edge 进程..."
pkill -9 "Microsoft Edge" 2>/dev/null || true
sleep 1

# 启动 Edge 浏览器
echo "▶️  启动 Edge 浏览器..."
/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge \
  --remote-debugging-port=9222 \
  --profile-directory="Profile 1" \
  --no-first-run \
  --no-default-browser-check \
  > /dev/null 2>&1 &

sleep 2

# 验证启动
if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "✅ Edge 浏览器启动成功！"
    echo "🔗 调试端口已开启: http://localhost:9222"
    echo ""
    echo "现在可以运行您的程序了，它会自动连接到这个浏览器实例。"
else
    echo "❌ Edge 浏览器启动失败或调试端口未开启"
    echo "请检查浏览器是否正常启动"
fi
