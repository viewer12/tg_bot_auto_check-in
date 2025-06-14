# Telegram 自动签到脚本

这是一个通用的 Telegram Bot 自动签到脚本，基于 [Telethon](https://github.com/LonamiWebs/Telethon) 开发，并使用 GitHub Actions 实现每日自动运行。

## 功能

- 支持多个 Telegram 机器人自动签到
- 支持多种按钮定位方式：文本匹配、位置匹配和回调数据匹配
- 智能模糊匹配功能，自动识别各种签到按钮
- 监控模式，可记录机器人交互细节，便于分析
- 使用 GitHub Actions 实现每日定时自动执行
- 安全地通过 GitHub Secrets 管理您的个人凭据

## 设置步骤

### 1. Fork 本项目

点击本项目页面右上角的 "Fork" 按钮，将此项目复制到您自己的 GitHub 仓库中。

### 2. 获取 Telegram API 凭据

要使用 Telegram API，您需要从 my.telegram.org 获取 `api_id` 和 `api_hash`。

1.  访问 [my.telegram.org](https://my.telegram.org) 并使用您的 Telegram 手机号登录。
2.  点击 "API development tools"。
3.  填写一个应用名称（任意填写），然后点击 "Create application"。
4.  您将获得 `api_id` 和 `api_hash`。请妥善保管这些信息。

### 3. 生成 Telegram Session 字符串

为了让脚本在 GitHub Actions 上运行，需要一个 Session 字符串来验证您的 Telegram 账户，而无需每次都登录。

1.  **在本地运行 `generate_session.py`**
    *   克隆您 Fork 后的仓库到本地：
        ```bash
        git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
        cd YOUR_REPOSITORY
        ```
    *   安装依赖：
        ```bash
        pip install -r requirements.txt
        ```
    *   在 `config.py` 文件中填入您的 `api_id` 和 `api_hash`。
    *   运行 `generate_session.py`:
        ```bash
        python generate_session.py
        ```
    *   根据提示输入您的手机号、密码（如果设置了二次验证），以及收到的验证码。
    *   成功登录后，脚本会在终端输出一长串 Session 字符串。请复制这个字符串。

### 4. 在 GitHub 仓库中设置 Secrets

1.  在您 Fork 的 GitHub 仓库页面，点击 "Settings" -> "Secrets and variables" -> "Actions"。
2.  点击 "New repository secret"，创建以下三个 Secret：

    *   `API_ID`: 您的 Telegram `api_id`。
    *   `API_HASH`: 您的 Telegram `api_hash`。
    *   `TELEGRAM_SESSION`: 您在上一步生成的 Session 字符串。

### 5. 配置要签到的机器人

编辑 `bot_configs.py` 文件，在 `BOT_CONFIGS` 列表中为您想要签到的机器人添加配置。此文件将被提交到您的 GitHub 仓库。

```python
# bot_configs.py

BOT_CONFIGS = [
    # 优先使用回调数据方式
    {
        "bot_username": "@example_bot",
        "start_command": "/start",
        "checkin_button": {"data": "checkin"}  # 使用回调数据直接定位按钮
    },
    # 使用文本匹配方式
    {
        "bot_username": "@another_bot",
        "start_command": "/start",
        "checkin_button": "签到"  # 通过按钮文本匹配
    },
    # 使用按钮位置方式
    {
        "bot_username": "@third_bot",
        "start_command": "/start",
        "checkin_button": [1, 1]  # 第二行第二个按钮
    },
    # 直接命令方式
    {
        "bot_username": "@fourth_bot", 
        "start_command": "/sign",  # 直接发送签到命令
        "checkin_button": None     # None 表示只发送命令不点按钮
    }
]
```

按钮定位支持三种方式：
1. **回调数据匹配**（最精确）：`{"data": "callback_data"}` - 使用按钮的回调数据进行匹配
2. **文本匹配**（支持模糊匹配）：`"签到"` - 使用按钮的文本进行匹配
3. **位置索引**：`[row, column]` - 通过位置定位按钮，行和列均从0开始

### 6. 使用监控模式分析按钮

如果您不确定某个机器人的按钮配置，可以使用监控模式来分析：

```bash
# 设置环境变量启用监控模式
export MONITOR_MODE=true

# 启动监控特定机器人
python monitor.py @bot_username
```

监控模式下，脚本会记录与机器人的所有交互，并将详细信息保存到 `monitor_logs.txt` 文件中，包括：
- 按钮的类型和结构
- 回调数据
- 消息内容和ID等

这有助于您确定正确的按钮定位方式，尤其是回调数据方式。

### 7. 启用 GitHub Actions 并测试

1.  将您修改后的 `bot_configs.py` 文件推送到 GitHub 仓库。
2.  在您的仓库页面，点击 "Actions" 选项卡。
3.  在左侧找到 "Telegram Bot Check-in" 工作流程，并点击 "Enable workflow"。
4.  您可以等待定时任务自动执行，或者手动触发一次以进行测试。点击 "Run workflow" -> "Run workflow" 来手动运行。

## 智能模糊匹配功能

脚本支持智能模糊匹配功能，使按钮识别更加准确：

- 忽略大小写差异（例如，"Check In" 可匹配 "check in"）
- 忽略空格和标点（例如，"签.到" 可匹配 "签到"）
- 忽略表情符号和特殊字符（例如，"🎯 签到" 可匹配 "签到"）
- 关键词匹配（例如，"每日签到" 可匹配 "签到"）

这大大提高了不同机器人按钮的识别率，减少了配置难度。

## 注意事项

-   请勿将您的 `api_id`, `api_hash`, Session 字符串或包含这些信息的 `config.py` 文件公开。`.gitignore` 文件已配置为忽略敏感文件。
-   GitHub Actions 的定时任务可能不会完全准时执行，会有一些延迟。
-   如果机器人界面变化导致签到失败，请使用监控模式分析新的按钮结构，然后更新配置。
-   脚本会在检测到"签到成功"或"已签到"等关键词时停止继续尝试其他配置，节省执行时间。 