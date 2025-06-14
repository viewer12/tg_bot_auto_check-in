# 在这里添加您需要签到的机器人配置。
#
# 配置说明:
#   - bot_username: (必需) 机器人的用户名，例如 "@micu_user_bot"。
#   - start_command: (必需) 用于启动机器人并显示操作按钮的命令，例如 "/start"。
#   - checkin_button: (必需) 定义要点击的签到按钮。有三种方式：
#       1. 按位置: 使用一个列表 [row, col]，row 和 col 都从 0 开始。
#          例如, [0, 0] 表示第一行第一个按钮，[1, 1] 表示第二行第二个按钮。
#       2. 按文本: 使用按钮上的确切文本，例如 "签到"。
#          现在支持模糊匹配，例如 "签到" 会匹配 "🎯 签到", "每日签到" 等。
#       3. 按回调数据: 使用字典格式 {"data": "callback_data"} 来指定按钮的回调数据。
#
BOT_CONFIGS = [
    # 优先使用回调数据方式（最准确）
    {
        "bot_username": "@micu_user_bot",
        "start_command": "/start",
        "checkin_button": {"data": "checkin"}  # 使用回调数据直接定位按钮
    },
    # 使用模糊匹配的不同写法测试
    {
        "bot_username": "@micu_user_bot",
        "start_command": "/start",
        "checkin_button": "签到"  # 使用基本文本，将模糊匹配到"🎯 签到"
    },
    {
        "bot_username": "@micu_user_bot",
        "start_command": "/start",
        "checkin_button": "签  到"  # 包含多余空格
    },
    {
        "bot_username": "@micu_user_bot",
        "start_command": "/start",
        "checkin_button": "每日签到"  # 与实际按钮文本不完全匹配
    },
    # 按钮位置方法
    {
        "bot_username": "@micu_user_bot",
        "start_command": "/start",
        "checkin_button": [1, 1]  # 使用正确的位置 [1, 1] 来定位签到按钮
    },
    # 直接命令方法（备用）
    {
        "bot_username": "@micu_user_bot", 
        "start_command": "/sign",  # 直接尝试签到命令而不是点击按钮
        "checkin_button": None     # 不需要点击按钮
    },
    {
        "bot_username": "@micu_user_bot",
        "start_command": "/checkin",  # 另一种可能的签到命令
        "checkin_button": None        # 不需要点击按钮
    },
    # --- 可以在下面添加其他机器人配置 ---
    #
    # 示例1: 使用按钮文本定位
    # {
    #     "bot_username": "@another_checkin_bot",
    #     "start_command": "/start",
    #     "checkin_button": "每日签到"
    # },
    #
    # 示例2: 使用位置定位
    # {
    #     "bot_username": "@some_other_bot",
    #     "start_command": "/begin",
    #     "checkin_button": [0, 2]  # 第一行，第三个按钮
    # },
] 