## 蜜罐
本项目使用的蜜罐是在开源蜜罐Cowrie基础上修改而来。
### 部署
- 拉取Ubuntu镜像：
```shell
sudo docker pull ubuntu:latest
```
- 根据镜像生成容器：
```shell
sudo docker run -it -p 22:2222 -p 23:2223 --name <容器名> ubuntu /bin/bash
```
- 相关环境配置：
```shell
apt install vim git python3-virtualenv libssl-dev libffi-dev build-essential libpython3-dev python3-minimal authbind
```
- 自行添加用户后Git Clone本项目：
```shell
git clone https://github.com/cgy2003/cowrie
```
- 创建Python虚拟环境，并且安装依赖：
```shell
virtualenv --python=python3 env
source env/bin/activate
pip3 install --upgrade -r cowrie/requirements.txt
```
### 启动
每次启动之前要切换到非root用户下，并且激活Python虚拟环境
```shell
./cowrie/bin/cowrie start
```
这样安装和部署后，您就可以启动Cowrie蜜罐并开始监视潜在的攻击者
