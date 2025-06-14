import os
import asyncio
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon.tl.types import Message, MessageService, KeyboardButtonCallback, KeyboardButton, ReplyInlineMarkup
from telethon.events import NewMessage, MessageEdited, CallbackQuery
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest

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

# 添加一个新的工具函数用于智能模糊匹配
def fuzzy_text_match(text1, text2):
    """
    实现模糊文本匹配，忽略大小写、空格、标点符号和表情符号前后的差异
    
    Args:
        text1: 第一个文本字符串
        text2: 第二个文本字符串
    
    Returns:
        bool: 如果两个字符串模糊匹配则返回True
    """
    if not text1 or not text2:
        return False
    
    # 原始文本记录
    original_text1 = text1
    original_text2 = text2
    
    # 将两个字符串都转为小写
    text1 = text1.lower()
    text2 = text2.lower()
    
    # 去除常见标点符号和空白
    import re
    pattern = r'[\s.,，。:：;；!！?？_\-—～~()]'
    text1 = re.sub(pattern, '', text1)
    text2 = re.sub(pattern, '', text2)
    
    # 清除表情符号和其他特殊字符
    emoji_pattern = r'[\U00010000-\U0010ffff]'
    text1 = re.sub(emoji_pattern, '', text1, flags=re.UNICODE)
    text2 = re.sub(emoji_pattern, '', text2, flags=re.UNICODE)
    
    # 基础检查：一个字符串是否包含在另一个字符串中
    base_match = text1 in text2 or text2 in text1
    
    # 如果基础检查失败，进行关键词匹配
    if not base_match:
        # 签到关键词匹配
        checkin_keywords = ["签到", "打卡", "checkin", "check", "签", "到"]
        
        # 提取文本中的关键词
        text1_keywords = [kw for kw in checkin_keywords if kw in text1]
        text2_keywords = [kw for kw in checkin_keywords if kw in text2]
        
        # 如果两边都有共同的签到关键词，认为匹配成功
        keyword_match = bool(set(text1_keywords) & set(text2_keywords))
        
        result = keyword_match
    else:
        result = base_match
    
    if result:
        logging.debug(f"模糊匹配成功: '{original_text1}' 与 '{original_text2}'")
        logging.debug(f"  处理后: '{text1}' 与 '{text2}'")
    else:
        logging.debug(f"模糊匹配失败: '{original_text1}' 与 '{original_text2}'")
        logging.debug(f"  处理后: '{text1}' 与 '{text2}'")
    
    return result

async def click_button(client: TelegramClient, bot_username: str, button_def, start_command: str):
    """
    发送命令并点击指定的按钮。

    Args:
        client: TelegramClient 实例。
        bot_username: 机器人的用户名。
        button_def: 按钮的定义（文本或 [行, 列] 坐标，或None表示仅发送命令，或字典 {"data": "回调数据"} 表示按回调数据查找）。
        start_command: 触发按钮面板的命令。
    """
    try:
        # 如果button_def为None，则只发送命令而不尝试点击按钮
        if button_def is None:
            logging.info(f"配置为仅发送命令模式，向 {bot_username} 发送 '{start_command}'...")
            
            # 创建一个 future 来等待新消息
            response_future = client.loop.create_future()
            
            @client.on(NewMessage(from_users=bot_username))
            async def cmd_handler(event):
                detailed_msg = await analyze_message(event.message)
                logging.info(f"命令 '{start_command}' 响应: {detailed_msg}")
                if not response_future.done():
                    response_future.set_result(event.message)
                    client.remove_event_handler(cmd_handler)
            
            await client.send_message(bot_username, start_command)
            
            try:
                cmd_response = await asyncio.wait_for(response_future, timeout=10.0)
                logging.info(f"✅ 命令 '{start_command}' 收到响应: {cmd_response.text.strip()}")
                return
            except asyncio.TimeoutError:
                logging.warning(f"命令 '{start_command}' 等待响应超时。")
                client.remove_event_handler(cmd_handler)
            except Exception as e:
                logging.error(f"处理命令 '{start_command}' 时出错: {e}")
                client.remove_event_handler(cmd_handler)
            return
            
        # 创建一个 future 来等待新消息
        future = client.loop.create_future()

        @client.on(NewMessage(from_users=bot_username))
        async def handler(event: NewMessage.Event):
            # 忽略服务消息
            if isinstance(event.message, MessageService):
                return
            
            # 详细记录所有收到的消息内容
            message_analysis = await analyze_message(event.message)
            logging.info(f"从 {bot_username} 收到新消息: {message_analysis}")
            
            if not event.message.reply_markup:
                logging.info(f"消息没有按钮面板: {event.message.text}")
            
            future.set_result(event.message)
            client.remove_event_handler(handler)

        # 监听所有回调查询事件，用于捕获和分析按钮点击
        @client.on(CallbackQuery())
        async def callback_handler(event):
            logging.info(f"检测到回调查询: {event.query}")
            logging.info(f"回调数据: {event.data.decode('utf-8') if event.data else None}")
            # 不要在此处设置 future 结果，保留监听以便捕获更多信息

        logging.info(f"正在向 {bot_username} 发送 '{start_command}'...")
        await client.send_message(bot_username, start_command)
        
        # 增加2秒延迟，等待机器人响应
        await asyncio.sleep(2)

        try:
            # 等待带有按钮的响应，设置超时
            message: Message = await asyncio.wait_for(future, timeout=15.0)
            logging.info(f"收到了来自 {bot_username} 的响应。")

            # 详细记录按钮结构
            if hasattr(message, 'reply_markup') and message.reply_markup:
                logging.info(f"按钮面板类型: {type(message.reply_markup).__name__}")
                
                for i, row in enumerate(message.reply_markup.rows):
                    for j, button in enumerate(row.buttons):
                        btn_info = analyze_button(button)
                        logging.info(f"按钮 [{i},{j}]: {btn_info}")

            buttons = [b for row in message.reply_markup.rows for b in row.buttons] if message.reply_markup else []
            target_button = None

            if isinstance(button_def, str):
                # 按文本查找按钮 - 先尝试完全匹配
                logging.info(f"尝试按文本匹配按钮: '{button_def}'")
                target_button = next((b for b in buttons if b.text == button_def), None)
                if target_button:
                    logging.info(f"通过完全匹配找到按钮: '{target_button.text}'")
                
                # 如果完全匹配失败，尝试部分匹配（按钮文本包含定义的文本）
                if not target_button:
                    target_button = next((b for b in buttons if button_def in b.text), None)
                    if target_button:
                        logging.info(f"通过部分匹配找到按钮: '{target_button.text}'")
                
                # 如果部分匹配也失败，尝试高级模糊匹配
                if not target_button:
                    logging.info("尝试使用高级模糊匹配...")
                    for button in buttons:
                        if fuzzy_text_match(button_def, button.text):
                            target_button = button
                            logging.info(f"通过模糊匹配找到按钮: '{target_button.text}'")
                            break

            elif isinstance(button_def, list) and len(button_def) == 2:
                # 按位置查找按钮
                row, col = button_def
                if message.reply_markup and row < len(message.reply_markup.rows) and col < len(message.reply_markup.rows[row].buttons):
                    target_button = message.reply_markup.rows[row].buttons[col]
                    
            elif isinstance(button_def, dict) and "data" in button_def:
                # 按回调数据查找按钮
                callback_data = button_def["data"]
                for button in buttons:
                    if hasattr(button, 'data') and button.data:
                        try:
                            button_data = button.data.decode('utf-8')
                            if button_data == callback_data:
                                target_button = button
                                logging.info(f"通过回调数据 '{callback_data}' 找到按钮: '{button.text}'")
                                break
                        except:
                            pass

            if target_button:
                logging.info(f"找到按钮 '{target_button.text}'...")
                logging.info(f"按钮详细信息: {analyze_button(target_button)}")
                
                # 增加延迟，有些机器人可能需要一段时间才能正确处理按钮点击
                await asyncio.sleep(2)
                
                try:
                    # 优先尝试 .click()，适用于 Inline Keyboard (Callback) buttons
                    logging.info("尝试使用 .click() 方法 (适用于内联按钮)...")
                    
                    # 修复 KeyboardButtonCallback 的点击方法
                    if hasattr(target_button, 'data') and target_button.data:
                        # 对于回调按钮，直接发送回调查询
                        logging.info(f"检测到回调按钮，使用回调数据: {target_button.data.decode('utf-8')}")
                        try:
                            click_result = await client(GetBotCallbackAnswerRequest(
                                peer=bot_username,
                                msg_id=message.id,
                                data=target_button.data
                            ))
                            
                            # 等待回调响应
                            logging.info("等待回调响应...")
                            await asyncio.sleep(3)  # 等待服务器处理回调
                        except Exception as e:
                            logging.info(f"机器人响应超时或出现错误: {str(e)} - 继续检查最新消息")
                        
                        # 获取最新消息查看是否有更新
                        last_msg = await client.get_messages(bot_username, limit=1)
                        if last_msg and last_msg[0].id != message.id:
                            logging.info(f"✅ 收到回调响应: {last_msg[0].text}")
                            detailed_msg = await analyze_message(last_msg[0])
                            logging.info(f"回调响应详情: {detailed_msg}")
                        else:
                            logging.warning("未检测到新消息回调响应")
                    else:
                        # 对于非回调按钮，使用普通的click方法
                        click_result = await target_button.click()
                    
                    # 检查弹窗
                    alert_message = getattr(click_result, 'message', None)
                    if alert_message:
                        logging.info(f"✅ 来自 {bot_username} 的弹窗响应: {alert_message}")
                    else:
                        # 如果没有弹窗，等待片刻后检查聊天中的最新消息
                        logging.info(f"已点击按钮，未收到弹窗。等待 5 秒后检查最新消息...")
                        await asyncio.sleep(5)  # 增加等待时间
                        last_msg = await client.get_messages(bot_username, limit=1)
                        if last_msg:
                            logging.info(f"✅ 来自 {bot_username} 的最新消息: {last_msg[0].text.strip()}")
                            detailed_msg = await analyze_message(last_msg[0])
                            logging.info(f"最新消息详情: {detailed_msg}")
                        else:
                            logging.warning(f"点击后未在与 {bot_username} 的对话中找到任何新消息。")

                except AttributeError as e:
                    # .click() 失败，假定为 Reply Keyboard button，发送其文本
                    logging.warning(f".click() 方法失败: {e}。尝试作为回复键盘按钮处理，发送按钮文本。")

                    # 创建一个 future 来等待机器人的新回复
                    response_future = client.loop.create_future()
                    handler = None
                    new_message_handler = None
                    edited_message_handler = None
                    
                    try:
                        # 分别注册事件处理器，避免使用列表语法
                        @client.on(NewMessage(from_users=bot_username))
                        async def new_message_handler(event):
                            detailed_msg = await analyze_message(event.message)
                            logging.info(f"收到新消息响应: {detailed_msg}")
                            if not response_future.done():
                                response_future.set_result(event.message)
                                logging.info("通过新消息事件捕获到响应")
                                client.remove_event_handler(new_message_handler)
                                client.remove_event_handler(edited_message_handler)
                        
                        @client.on(MessageEdited(from_users=bot_username))
                        async def edited_message_handler(event):
                            detailed_msg = await analyze_message(event.message)
                            logging.info(f"收到编辑消息响应: {detailed_msg}")
                            if not response_future.done():
                                response_future.set_result(event.message)
                                logging.info("通过编辑消息事件捕获到响应")
                                client.remove_event_handler(new_message_handler)
                                client.remove_event_handler(edited_message_handler)

                        await client.send_message(bot_username, target_button.text)
                        logging.info(f"已发送按钮文本，等待 20 秒以接收机器人的回复 (新消息或编辑消息)...")
                        
                        # 增加超时时间到20秒
                        response_message: Message = await asyncio.wait_for(response_future, timeout=20.0)
                        logging.info(f"✅ 来自 {bot_username} 的响应消息: {response_message.text.strip()}")

                    except asyncio.TimeoutError:
                        logging.warning(f"发送按钮文本后，等待机器人响应超时。")
                        
                        # 按钮点击和发送文本都失败后尝试第三种方法：直接发送通用签到命令
                        logging.info("尝试第三种方法：直接发送签到命令...")
                        direct_commands = ["/sign", "/checkin", "/签到", "/打卡", "签到", "打卡", "check in"]
                        
                        for cmd in direct_commands:
                            cmd_future = client.loop.create_future()
                            
                            @client.on(NewMessage(from_users=bot_username))
                            async def cmd_handler(event):
                                detailed_msg = await analyze_message(event.message)
                                logging.info(f"命令 '{cmd}' 响应: {detailed_msg}")
                                if not cmd_future.done():
                                    cmd_future.set_result(event.message)
                                    client.remove_event_handler(cmd_handler)
                            
                            logging.info(f"尝试发送命令: {cmd}")
                            await client.send_message(bot_username, cmd)
                            
                            try:
                                # 增加超时时间到8秒
                                cmd_response = await asyncio.wait_for(cmd_future, timeout=8.0)
                                logging.info(f"✅ 命令 '{cmd}' 收到响应: {cmd_response.text.strip()}")
                                # 成功收到响应，不再尝试其他命令
                                break
                            except asyncio.TimeoutError:
                                logging.info(f"命令 '{cmd}' 无响应，尝试下一个命令...")
                                client.remove_event_handler(cmd_handler)
                            except Exception as e:
                                logging.error(f"处理命令 '{cmd}' 时出错: {e}")
                                client.remove_event_handler(cmd_handler)
                        
                    finally:
                        # 确保移除所有事件处理器
                        if new_message_handler:
                            try:
                                client.remove_event_handler(new_message_handler)
                            except:
                                pass
                        if edited_message_handler:
                            try:
                                client.remove_event_handler(edited_message_handler)
                            except:
                                pass
                
                except Exception as e:
                    logging.error(f"处理按钮点击时发生未知错误: {e}")

                logging.info(f"对 {bot_username} 的操作已完成。")
            else:
                logging.warning(f"在 {bot_username} 的响应中未找到指定的按钮。定义: {button_def}")
                
                # 如果找不到按钮，尝试直接发送几个常见的签到命令
                logging.info("找不到指定按钮，尝试直接发送签到命令...")
                direct_commands = ["/sign", "/checkin", "/签到", "/打卡", "签到", "打卡", "check in"]
                
                for cmd in direct_commands:
                    cmd_future = client.loop.create_future()
                    
                    @client.on(NewMessage(from_users=bot_username))
                    async def cmd_handler(event):
                        detailed_msg = await analyze_message(event.message)
                        logging.info(f"命令 '{cmd}' 响应: {detailed_msg}")
                        if not cmd_future.done():
                            cmd_future.set_result(event.message)
                            client.remove_event_handler(cmd_handler)
                    
                    logging.info(f"尝试发送命令: {cmd}")
                    await client.send_message(bot_username, cmd)
                    
                    try:
                        # 增加超时时间到8秒
                        cmd_response = await asyncio.wait_for(cmd_future, timeout=8.0)
                        logging.info(f"✅ 命令 '{cmd}' 收到响应: {cmd_response.text.strip()}")
                        # 成功收到响应，不再尝试其他命令
                        break
                    except asyncio.TimeoutError:
                        logging.info(f"命令 '{cmd}' 无响应，尝试下一个命令...")
                        client.remove_event_handler(cmd_handler)
                    except Exception as e:
                        logging.error(f"处理命令 '{cmd}' 时出错: {e}")
                        client.remove_event_handler(cmd_handler)

        except asyncio.TimeoutError:
            logging.error(f"等待 {bot_username} 响应超时。")
        finally:
            # 确保事件处理器被移除
            if not future.done():
                client.remove_event_handler(handler)

    except Exception as e:
        logging.error(f"处理 {bot_username} 时发生错误: {e}")


async def monitor_mode(client, bot_username):
    """监听模式：记录与特定机器人的所有交互"""
    logging.info(f"启动监听模式，监听与 {bot_username} 的所有交互...")
    
    @client.on(NewMessage(from_users=bot_username))
    async def bot_handler(event):
        detailed_msg = await analyze_message(event.message)
        logging.info(f"监听到来自 {bot_username} 的新消息: {detailed_msg}")
    
    @client.on(NewMessage(outgoing=True, to_users=bot_username))
    async def user_handler(event):
        logging.info(f"监听到用户向 {bot_username} 发送消息: {event.message.text}")
    
    @client.on(CallbackQuery())
    async def callback_handler(event):
        if hasattr(event, 'chat') and event.chat and hasattr(event.chat, 'username') and event.chat.username == bot_username.replace('@', ''):
            logging.info(f"监听到回调查询事件: {event.query}")
            try:
                data = event.data.decode('utf-8') if event.data else None
                logging.info(f"回调数据: {data}")
            except:
                logging.info(f"回调数据 (原始): {event.data}")
    
    # 只是开始监听，不发送任何命令
    await client.send_message(bot_username, "您好，我正在进行签到分析，请手动执行签到操作以便我记录操作细节。")
    logging.info("监听已启动，请手动与机器人互动，系统将记录所有交互。输入 Ctrl+C 结束监听。")
    
    # 保持脚本运行
    while True:
        await asyncio.sleep(60)


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

        # 检查命令行参数是否包含 --monitor
        monitor_mode_enabled = os.environ.get('MONITOR_MODE', '').lower() in ('true', '1', 'yes')
        
        if monitor_mode_enabled:
            # 监听模式
            first_bot = bot_configs[0]["bot_username"] if bot_configs else "@micu_user_bot"
            await monitor_mode(client, first_bot)
        else:
            # 正常签到模式
            for config in bot_configs:
                bot_username = config.get("bot_username")
                start_command = config.get("start_command")
                button_def = config.get("checkin_button")

                if not all([bot_username, start_command]):
                    logging.warning(f"跳过一个不完整的机器人配置: {config}")
                    continue
                
                await click_button(client, bot_username, button_def, start_command)
                logging.info(f"已完成对 {bot_username} 的处理。等待 5 秒进入下一个任务...")
                await asyncio.sleep(5)

    logging.info("所有签到任务已完成。")


if __name__ == "__main__":
    asyncio.run(main()) 