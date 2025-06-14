# Telegram 自动签到脚本

这是一个通用的 Telegram Bot 自动签到脚本，基于 [Telethon](https://github.com/LonamiWebs/Telethon) 开发，并使用 GitHub Actions 实现每日自动运行。

## 功能

- 支持多个 Telegram 机器人自动签到。
- 可通过配置文件轻松添加和管理机器人。
- 使用 GitHub Actions 实现每日定时自动执行。
- 安全地通过 GitHub Secrets 管理您的个人凭据。

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

编辑 `config.py` 文件，在 `BOT_CONFIGS` 列表中为您想要签到的机器人添加配置。

例如，为 `@micu_user_bot` 添加签到配置：

```python
# ...

BOT_CONFIGS = [
    {
        "bot_username": "@micu_user_bot",
        "start_command": "/start",
        "checkin_button": [1, 1]  # [行, 列]，都从 0 开始计数。第二行第二个按钮是 [1, 1]
    },
    # 在这里添加更多机器人配置
    # {
    #     "bot_username": "@another_bot",
    #     "start_command": "/checkin",
    #     "checkin_button": "签到" # 也可以是按钮上的文字
    # },
]
```

-   `bot_username`: 机器人的用户名。
-   `start_command`: 用于触发操作面板的命令。
-   `checkin_button`:
    -   可以是按钮的**精确**文本，例如 `"签到"`。
    -   也可以是按钮的位置，格式为 `[行, 列]`（从 0 开始计数）。例如，第二行第二个按钮是 `[1, 1]`。

### 6. 启用 GitHub Actions 并测试

1.  将您修改后的 `config.py` 文件推送到 GitHub 仓库。
2.  在您的仓库页面，点击 "Actions" 选项卡。
3.  在左侧找到 "Telegram Bot Check-in" 工作流程，并点击 "Enable workflow"。
4.  您可以等待定时任务自动执行，或者手动触发一次以进行测试。点击 "Run workflow" -> "Run workflow" 来手动运行。

## 注意事项

-   请勿将您的 `api_id`, `api_hash`, Session 字符串或包含这些信息的 `config.py` 文件公开。`.gitignore` 文件已配置为忽略 `*.session` 文件。
-   GitHub Actions 的定时任务可能不会完全准时执行，会有一些延迟。
-   如果某个机器人的界面或按钮发生变化，您需要相应地更新 `config.py` 中的配置。 