欢迎来到Cowrie GitHub存储库

这是Cowrie SSH和Telnet蜜罐项目的官方存储库。
Cowrie是一个中高交互SSH和Telnet蜜罐，旨在记录暴力攻击和攻击者执行的shell交互。在中等交互模式（shell）中，它用Python模拟UNIX系统，在高交互模式（代理）中，它作为SSH和Telnet代理，观察攻击者对另一台系统的行为。
Cowrie <http://github.com/cowrie/cowrie/>_由Michel Oosterhof维护。
文档

文档可以在 这里 <https://cowrie.readthedocs.io/en/latest/index.html>_ 找到。
Slack

您可以加入Cowrie社区的 Slack工作区 <https://www.cowrie.org/slack/>_。
特点

可选择作为模拟shell运行（默认）：
假文件系统，具有添加/删除文件的功能。包含一个完整的伪文件系统，类似于Debian 5.0安装
可以添加假文件内容，使攻击者可以cat文件，例如/etc/passwd。只包含最小的文件内容
Cowrie保存通过wget/curl下载或通过SFTP和scp上传的文件，以便以后检查
或者代理SSH和Telnet到另一个系统
作为纯Telnet和SSH代理运行，并进行监视
或者让Cowrie管理一组QEMU模拟的服务器，以提供要登录的系统 对于这两种设置：
会话日志以 UML兼容 <http://user-mode-linux.sourceforge.net/>_ 格式存储，可以使用 bin/playlog 实用程序轻松重播。
支持文件上传的SFTP和SCP
支持SSH exec命令
记录直接tcp连接尝试（ssh代理）
将SMTP连接转发到SMTP蜜罐（例如mailoney <https://github.com/awhitehatter/mailoney>_）
JSON日志记录，方便在日志管理解决方案中处理 Docker
有Docker版本可用。

要快速开始并尝试Cowrie，请运行：
$ docker run -p 2222:2222 cowrie/cowrie:latest
$ ssh -p 2222 root@localhost
在Docker Hub上：https://hub.docker.com/r/cowrie/cowrie
配置Docker中的Cowrie Cowrie在Docker中可以使用环境变量进行配置。 变量以COWRIE_开头，然后是大写的部分名称，后跟大写的部分。 以下是一个示例，用于启用telnet支持：
COWRIE_TELNET_ENABLED=yes
或者，Cowrie在Docker中可以使用etc卷来存储配置数据。 在etc卷内创建cowrie.cfg，其中包含以下内容以在Docker中启用Cowrie蜜罐中的telnet：

[telnet]
enabled = yes
要求

本地运行所需软件：

Python 3.8+
python-virtualenv 对于Python依赖项，请参阅 requirements.txt <https://github.com/cowrie/cowrie/blob/master/requirements.txt>_。 感兴趣的文件：
etc/cowrie.cfg - Cowrie的配置文件。 默认值可以在 etc/cowrie.cfg.dist <https://github.com/cowrie/cowrie/blob/master/etc/cowrie.cfg.dist>_ 中找到。
share/cowrie/fs.pickle - 假文件系统
etc/userdb.txt - 访问蜜罐的凭据
honeyfs/ <https://github.com/cowrie/cowrie/tree/master/honeyfs>_ - 伪文件系统的文件内容 - 可以复制真实系统到这里或使用 bin/fsctl
honeyfs/etc/issue.net - 登录前横幅
honeyfs/etc/motd <https://github.com/cowrie/cowrie/blob/master/honeyfs/etc/issue>_ - 登录后横幅
var/log/cowrie/cowrie.json - JSON格式的交易输出
var/log/cowrie/cowrie.log - 日志/调试输出
var/lib/cowrie/tty/ - 会话日志，可以使用 bin/playlog 实用程序重播。
var/lib/cowrie/downloads/ - 从攻击者传输到蜜罐的文件存储在这里
share/cowrie/txtcmds/ <https://github.com/cowrie/cowrie/tree/master/share/cowrie/txtcmds>_ - 简单伪命令的文件内容
bin/createfs <https://github.com/cowrie/cowrie/blob/master/bin/createfs>_ - 用于创建伪文件系统
bin/playlog <https://github.com/cowrie/cowrie/blob/master/bin/playlog>_ - 用于重播会话日志的实用程序 
