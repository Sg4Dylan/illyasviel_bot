# illyasviel bot
Yet another telegram inline bot -> [@illyasviel_bot](https://telegram.me/illyasviel_bot)

依赖
------------
* Python 3.5+
* Tornado
* Requests
* JSON
* PIL
* uuid
* urllib
* nginx

部署
------------
1. 配置 nginx 反代 `http://127.0.0.1:8022/`； 
2. 替换文件里的`[YOUR WEBSITE]` `[YOUR TOKEN]`替换为自己的反代地址和BOT TOKEN；
3. 将 134、138、143 行对应的文件设置好路径；
4. [设置你的 webhook](https://core.telegram.org/bots/api#setwebhook)； 
5. 运行 `python3 illyasviel.py`； 
6. 在聊天框里 at 机器人的名字然后输入字符`@illyasviel_bot 伊莉雅斯菲尔`

