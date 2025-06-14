import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

def get_config():
    """
    尝试导入用户配置。如果找不到文件或配置，则提供指导。
    """
    try:
        from config import API_ID, API_HASH
        return API_ID, API_HASH
    except ImportError:
        print("错误：找不到 `config.py` 文件。")
        print("请将 `config.py.example` 文件重命名为 `config.py`，并填入您的 API_ID 和 API_HASH。")
        exit(1)
    except AttributeError:
        print("错误：`config.py` 文件中缺少 API_ID 或 API_HASH。")
        print("请确保在 `config.py` 中正确设置了这两个变量。")
        exit(1)

async def main():
    """
    主函数，用于生成和打印 session 字符串。
    """
    print("--- Telegram Session 生成器 ---")
    
    api_id, api_hash = get_config()

    if api_id == 12345 or api_hash == "your_api_hash":
        print("\n警告：您正在使用示例配置中的默认 API_ID 和 API_HASH。")
        print("请打开 `config.py` 文件，并替换为从 my.telegram.org 获取的真实凭据。")
        exit(1)

    # 使用内存会话开始，这样不会在本地创建 .session 文件
    async with TelegramClient(StringSession(), api_id, api_hash) as client:
        print("客户端已创建。现在将生成 Session 字符串。")
        print("您需要输入您的电话号码、密码（如果设置了）和收到的登录验证码。")
        
        # client.start() 会处理登录流程
        await client.start()
        
        session_string = client.session.save()
        
        print("\n登录成功！")
        print("这是您的 Session 字符串，请妥善保管，不要泄露给任何人：\n")
        print(f"TELEGRAM_SESSION=\n{session_string}\n")
        print("请将此字符串复制并粘贴到您 GitHub 仓库的 Secrets 中。")
        print("有关详细步骤，请参阅 README.md 文件。")

if __name__ == "__main__":
    asyncio.run(main()) 