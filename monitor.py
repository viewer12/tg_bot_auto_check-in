import os
import asyncio
import logging
import json
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Message, MessageService, KeyboardButtonCallback, KeyboardButton
from telethon.events import NewMessage, CallbackQuery, MessageEdited

# --- 日志记录设置 ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitor_logs.txt", mode='w'),
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
        logging.error("未找到API凭据，请确保config.py文件正确配置")
        return
    
    logging.info("启动监听程序...")
    logging.info(f"使用API ID: {api_id}")
    
    client = TelegramClient("monitor_session", api_id, api_hash)
    await client.start()
    
    user = await client.get_me()
    logging.info(f"已登录账户: {user.first_name} (@{user.username})")
    logging.info(f"开始监听 {bot_username} 的所有交互...")
    
    # 监听机器人发送的消息
    @client.on(NewMessage(from_users=bot_username))
    async def bot_message_handler(event):
        message_details = await analyze_message(event.message)
        logging.info(f"收到来自 {bot_username} 的[新]消息:")
        logging.info(json.dumps(message_details, ensure_ascii=False, indent=2))
        
        # 特别关注按钮
        if hasattr(event.message, 'reply_markup') and event.message.reply_markup:
            logging.info("检测到按钮面板，详细信息如下:")
            for i, row in enumerate(event.message.reply_markup.rows):
                for j, button in enumerate(row.buttons):
                    btn_info = analyze_button(button)
                    logging.info(f"按钮[{i},{j}] - 文本: '{button.text}', 类型: {type(button).__name__}")
                    
                    # 针对不同类型按钮的详细信息
                    if isinstance(button, KeyboardButtonCallback):
                        try:
                            data = button.data.decode('utf-8')
                            logging.info(f"  回调数据: {data}")
                        except:
                            logging.info(f"  回调数据(二进制): {button.data}")
    
    # 监听机器人发送的编辑消息
    @client.on(MessageEdited(from_users=bot_username))
    async def bot_edited_message_handler(event):
        message_details = await analyze_message(event.message)
        logging.info(f"检测到 {bot_username} 编辑了消息:")
        logging.info(json.dumps(message_details, ensure_ascii=False, indent=2))
    
    # 监听发送给机器人的消息
    @client.on(NewMessage(outgoing=True, chats=bot_username))
    async def outgoing_message_handler(event):
        logging.info(f"发送给 {bot_username} 的消息: {event.message.text}")

    # 监听按钮回调
    @client.on(CallbackQuery)
    async def callback_handler(event):
        if not event.chat:
            return
            
        chat_username = event.chat.username if hasattr(event.chat, 'username') else None
        if chat_username and (f"@{chat_username}" == bot_username or chat_username == bot_username.replace('@', '')):
            logging.info(f"检测到按钮回调事件")
            try:
                data = event.data.decode('utf-8') if event.data else None
                logging.info(f"按钮回调数据: {data}")
                
                # 记录回调后的响应（添加短暂延迟等待响应）
                await asyncio.sleep(1)
                messages = await client.get_messages(bot_username, limit=1)
                if messages:
                    message_details = await analyze_message(messages[0])
                    logging.info(f"按钮回调后的最新消息:")
                    logging.info(json.dumps(message_details, ensure_ascii=False, indent=2))
            except Exception as e:
                logging.error(f"处理回调数据时出错: {e}")

    # 发送开始消息
    await client.send_message(bot_username, "/start")
    logging.info(f"已发送 /start 命令给 {bot_username}")
    logging.info("请手动与机器人互动并进行签到操作，系统会记录所有交互。")
    logging.info("监控日志将保存到 monitor_logs.txt 文件")
    logging.info("按 Ctrl+C 结束监听。")
    
    # 保持客户端运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("监听结束，正在关闭客户端...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # 默认监听的机器人用户名
    target_bot = "@micu_user_bot"
    
    # 如果命令行参数提供了机器人用户名，则使用提供的用户名
    if len(sys.argv) > 1:
        target_bot = sys.argv[1]
        if not target_bot.startswith('@'):
            target_bot = '@' + target_bot
    
    logging.info(f"将监听机器人: {target_bot}")
    
    # 运行监听
    try:
        asyncio.run(monitor_bot(target_bot))
    except KeyboardInterrupt:
        logging.info("程序被用户中断") 