# 在这里添加您需要签到的机器人配置。
#
# 配置说明:
#   - bot_username: (必需) 机器人的用户名，例如 "@micu_user_bot"。
#   - start_command: (必需) 用于启动机器人并显示操作按钮的命令，例如 "/start"。
#   - checkin_button: (必需) 定义要点击的签到按钮。有两种方式：
#       1. 按位置: 使用一个列表 [row, col]，row 和 col 都从 0 开始。
#          例如, [0, 0] 表示第一行第一个按钮，[1, 1] 表示第二行第二个按钮。
#       2. 按文本: 使用按钮上的确切文本，例如 "签到"。
#
BOT_CONFIGS = [
    {
        "bot_username": "@micu_user_bot",
        "start_command": "/start",
        "checkin_button": [1, 1]  # 第二行，第二个按钮
    },
    # --- 在下面添加更多机器人配置 ---
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