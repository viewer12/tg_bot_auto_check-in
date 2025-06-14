import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon.tl.types import Message, MessageService
from telethon.events import NewMessage

# --- 日志记录设置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 配置加载 ---
def get_credentials():
    """
    从环境变量或配置文件中获取凭据。
    优先使用环境变量（用于 GitHub Actions）。
    """
    api_id = os.environ.get('API_ID')
    api_hash = os.environ.get('API_HASH')
    session_string = os.environ.get('TELEGRAM_SESSION')

    if not all([api_id, api_hash, session_string]):
        logging.info("未找到环境变量，尝试从 config.py 加载...")
        try:
            from config import API_ID, API_HASH
            api_id = API_ID
            api_hash = API_HASH
            session_string = None  # 本地运行时使用文件 session
        except (ImportError, AttributeError):
            logging.error("无法从环境变量或 config.py 加载凭据。请检查您的配置。")
            return None, None, None
    
    return api_id, api_hash, session_string

def get_bot_configs():
    """从 bot_configs.py 加载机器人配置。"""
    try:
        from bot_configs import BOT_CONFIGS
        return BOT_CONFIGS
    except (ImportError, AttributeError):
        logging.error("无法从 bot_configs.py 加载 BOT_CONFIGS。请确保文件存在且配置正确。")
        return []

async def click_button(client: TelegramClient, bot_username: str, button_def, start_command: str):
    """
    发送命令并点击指定的按钮。

    Args:
        client: TelegramClient 实例。
        bot_username: 机器人的用户名。
        button_def: 按钮的定义（文本或 [行, 列] 坐标）。
        start_command: 触发按钮面板的命令。
    """
    try:
        # 创建一个 future 来等待新消息
        future = client.loop.create_future()

        @client.on(NewMessage(from_users=bot_username))
        async def handler(event: NewMessage.Event):
            # 忽略服务消息或没有按钮的消息
            if isinstance(event.message, MessageService) or not event.message.reply_markup:
                return
            future.set_result(event.message)
            client.remove_event_handler(handler)

        logging.info(f"正在向 {bot_username} 发送 '{start_command}'...")
        await client.send_message(bot_username, start_command)

        try:
            # 等待带有按钮的响应，设置超时
            message: Message = await asyncio.wait_for(future, timeout=15.0)
            logging.info(f"收到了来自 {bot_username} 的响应。")

            buttons = [b for row in message.reply_markup.rows for b in row.buttons]
            target_button = None

            if isinstance(button_def, str):
                # 按文本查找按钮
                target_button = next((b for b in buttons if b.text == button_def), None)
            elif isinstance(button_def, list) and len(button_def) == 2:
                # 按位置查找按钮
                row, col = button_def
                if row < len(message.reply_markup.rows) and col < len(message.reply_markup.rows[row].buttons):
                    target_button = message.reply_markup.rows[row].buttons[col]

            if target_button:
                logging.info(f"找到按钮 '{target_button.text}'...")
                
                try:
                    # 优先尝试 .click()，适用于 Inline Keyboard (Callback) buttons
                    logging.info("尝试使用 .click() 方法 (适用于内联按钮)...")
                    click_result = await target_button.click()
                    
                    # 检查弹窗
                    alert_message = getattr(click_result, 'message', None)
                    if alert_message:
                        logging.info(f"✅ 来自 {bot_username} 的弹窗响应: {alert_message}")
                    else:
                        # 如果没有弹窗，等待片刻后检查聊天中的最新消息
                        logging.info(f"已点击按钮，未收到弹窗。等待 3 秒后检查最新消息...")
                        await asyncio.sleep(3)
                        last_msg = await client.get_messages(bot_username, limit=1)
                        if last_msg:
                            logging.info(f"✅ 来自 {bot_username} 的最新消息: {last_msg[0].text.strip()}")
                        else:
                            logging.warning(f"点击后未在与 {bot_username} 的对话中找到任何新消息。")

                except AttributeError:
                    # .click() 失败，假定为 Reply Keyboard button，发送其文本
                    logging.warning(".click() 方法失败。尝试作为回复键盘按钮处理，发送按钮文本。")

                    # 创建一个 future 来等待机器人的新回复
                    response_future = client.loop.create_future()
                    handler = None
                    try:
                        @client.on(NewMessage(from_users=bot_username))
                        async def response_handler(event: NewMessage.Event):
                            response_future.set_result(event.message)
                            client.remove_event_handler(response_handler)
                        
                        handler = response_handler # 保存 handler 以便在 finally 中移除

                        await client.send_message(bot_username, target_button.text)
                        logging.info(f"已发送按钮文本，等待 15 秒以接收机器人的回复...")
                        
                        response_message: Message = await asyncio.wait_for(response_future, timeout=15.0)
                        logging.info(f"✅ 来自 {bot_username} 的响应消息: {response_message.text.strip()}")

                    except asyncio.TimeoutError:
                        logging.warning(f"发送按钮文本后，等待机器人响应超时。")
                    finally:
                        if handler:
                            client.remove_event_handler(handler)
                
                except Exception as e:
                    logging.error(f"处理按钮点击时发生未知错误: {e}")

                logging.info(f"对 {bot_username} 的操作已完成。")
            else:
                logging.warning(f"在 {bot_username} 的响应中未找到指定的按钮。定义: {button_def}")

        except asyncio.TimeoutError:
            logging.error(f"等待 {bot_username} 响应超时。")
        finally:
            # 确保事件处理器被移除
            if not future.done():
                client.remove_event_handler(handler)

    except Exception as e:
        logging.error(f"处理 {bot_username} 时发生错误: {e}")


async def main():
    """主执行函数"""
    api_id, api_hash, session_string = get_credentials()
    if not api_id:
        return

    bot_configs = get_bot_configs()
    if not bot_configs:
        return

    session = StringSession(session_string) if session_string else "telegram_session"
    
    async with TelegramClient(session, api_id, api_hash) as client:
        user = await client.get_me()
        logging.info(f"成功登录账户：{user.first_name} (@{user.username})")

        for config in bot_configs:
            bot_username = config.get("bot_username")
            start_command = config.get("start_command")
            button_def = config.get("checkin_button")

            if not all([bot_username, start_command, button_def]):
                logging.warning(f"跳过一个不完整的机器人配置: {config}")
                continue
            
            await click_button(client, bot_username, button_def, start_command)
            logging.info(f"已完成对 {bot_username} 的处理。等待 5 秒进入下一个任务...")
            await asyncio.sleep(5)

    logging.info("所有签到任务已完成。")


if __name__ == "__main__":
    asyncio.run(main()) 