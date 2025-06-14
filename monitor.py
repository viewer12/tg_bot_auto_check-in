import os
import asyncio
import logging
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Message, MessageService
from telethon.events import NewMessage, CallbackQuery

# --- 日志记录设置 ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitor_logs.txt"),
        logging.StreamHandler()
    ]
)

# --- 配置加载 ---
def get_credentials():
    """从配置文件中获取凭据"""
    try:
        from config import API_ID, API_HASH
        return API_ID, API_HASH
    except (ImportError, AttributeError):
        logging.error("无法从 config.py 加载凭据。请确保文件存在且配置正确。")
        return None, None

def analyze_button(button):
    """分析按钮的详细信息"""
    button_type = type(button).__name__
    button_info = {
        "类型": button_type,
        "文本": button.text
    }
    
    if hasattr(button, 'data'):
        try:
            button_info["数据"] = button.data.decode('utf-8')
        except:
            button_info["数据"] = str(button.data)
    
    if hasattr(button, 'url'):
        button_info["URL"] = button.url
        
    return button_info

async def analyze_message(message):
    """分析消息的详细内容，包括按钮结构"""
    if not message:
        return "消息为空"
    
    result = {
        "消息ID": message.id,
        "消息类型": type(message).__name__,
        "消息内容": message.text if hasattr(message, 'text') else "无文本内容",
    }
    
    # 分析按钮
    if hasattr(message, 'reply_markup') and message.reply_markup:
        markup_type = type(message.reply_markup).__name__
        result["按钮面板类型"] = markup_type
        result["按钮"] = []
        
        for i, row in enumerate(message.reply_markup.rows):
            for j, button in enumerate(row.buttons):
                btn_info = analyze_button(button)
                btn_info["位置"] = [i, j]
                result["按钮"].append(btn_info)
    
    return result

async def monitor_bot(bot_username):
    """监听指定机器人的所有交互"""
    api_id, api_hash = get_credentials()
    if not api_id:
        return
    
    client = TelegramClient("monitor_session", api_id, api_hash)
    await client.start()
    
    user = await client.get_me()
    logging.info(f"已登录账户: {user.first_name} (@{user.username})")
    logging.info(f"开始监听 {bot_username} 的所有交互...")
    
    # 监听机器人发送的消息
    @client.on(NewMessage(from_users=bot_username))
    async def bot_message_handler(event):
        message_details = await analyze_message(event.message)
        logging.info(f"收到来自 {bot_username} 的消息: {json.dumps(message_details, ensure_ascii=False, indent=2)}")
    
    # 监听发送给机器人的消息
    @client.on(NewMessage(outgoing=True, to_users=bot_username))
    async def outgoing_message_handler(event):
        logging.info(f"发送给 {bot_username} 的消息: {event.message.text}")

    # 监听按钮回调
    @client.on(CallbackQuery)
    async def callback_handler(event):
        if hasattr(event, 'chat') and event.chat and hasattr(event.chat, 'username'):
            chat_username = event.chat.username
            if f"@{chat_username}" == bot_username or chat_username == bot_username.replace('@', ''):
                logging.info(f"检测到回调查询: {event.query}")
                try:
                    data = event.data.decode('utf-8') if event.data else None
                    logging.info(f"回调数据: {data}")
                except:
                    logging.info(f"回调数据 (原始): {event.data}")

    # 发送开始消息
    await client.send_message(bot_username, "/start")
    logging.info(f"已发送 /start 命令给 {bot_username}")
    logging.info("监听已启动，请手动与机器人互动，系统将记录所有交互细节。按 Ctrl+C 结束监听。")
    
    # 保持客户端运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("监听结束，正在关闭客户端...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # 要监听的机器人用户名
    target_bot = "@micu_user_bot"  # 可以根据需要修改
    
    # 运行监听
    try:
        asyncio.run(monitor_bot(target_bot))
    except KeyboardInterrupt:
        logging.info("程序被用户中断") 