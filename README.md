# 什么是 HuggingFace FS ？

HuggingFace FS (简称 "HFFS") 目标成为一款“小而美”的工具，帮助中国大陆用户在使用 [HuggingFace](huggingface.co) 的时候，能够方便地下载、管理、分享来自 HF 的模型。

中国大陆用户需要配置代理服务才能访问 HuggingFace 主站。大陆地区和 HuggingFace 主站之间的网络带宽较低而且不稳定，可靠的镜像网站很少，模型文件又很大。因此，下载 HuggingFace 上模型文件的时间往往很长。HFFS 在 hf.co 的基础上增加了 P2P 的模型共享方式，让大陆地区用户能够以更快的速度获得所需要的模型。

![HFFS Diagram](https://raw.githubusercontent.com/sg-c/huggingface-fs/main/resources/hffs-readme-diagram.png)

HFFS 的典型使用场景有：

- **同伴之间模型共享**：如果实验室或者开发部门的其他小伙伴已经下载了你需要的模型文件**，HFFS 的 P2P 共享方式能让你从他们那里得到模型，模型的下载速度不再是个头疼的问题。当然，如果目标模型还没有被其他人下载过，jycache-model 会自动从模型仓库下载模型，然后你可以通过 jycache-model 把模型分享给其他小伙伴。
- **机器之间模型传输**：有些小伙伴需要两台主机（Windows 和 Linux）完成模型的下载和使用：Windows 上的 VPN 很容易配置，所以它负责下载模型；Linux 的开发环境很方便，所以它负责模型的微调、推理等任务。通过 jycache-model 的 P2P 共享功能，两台主机之间的模型下载和拷贝就不再需要手动操作了。
- **多源断点续传**：浏览器默认不支持模型下载的断点续传，但是 jycache-model 支持该功能。无论模型文件从哪里下载（模型仓库或者其他同伴的机器），jycache-model 支持不同下载源之间的断点续传。

## HFFS 如何工作

![HFFS Architecture](https://raw.githubusercontent.com/sg-c/huggingface-fs/main/resources/hffs-simple-architecture.png)

1. 通过 `hffs daemon start` 命令启动 HFFS daemon 服务；
2. 通过 `hffs peer add` 相关命令把局域网内其他机器作为 peer 和本机配对；
3. 通过 `hffs model add` 命令下载目标模型文件；

在下载目标模型文件的时候，本机的 daemon 服务会从其他匹配的 peer 机器以及 hf.co 主站以其镜像网站查找目标模型文件，并选择最快的方式进行下载。

`hffs daemon`、`hffs peer`、`hffs model` 命令还包括其他的功能，请见下面的文档说明。

## 安装 HFFS

> [!NOTE]
> 确保你安装了 Python 3.8+ 版本并且安装了 pip。
> 可以考虑使用 [Miniconda](https://docs.anaconda.com/miniconda/miniconda-install/) 安装和管理不同版本的 Python。
> pip 的使用见[这里](https://pip.pypa.io/en/stable/cli/pip_install/)。

```bash
pip install -i https://test.pypi.org/simple/ hffs
```

## HFFS 命令

### HFFS Daemon 服务管理

#### 启动 HFFS Daemon

```bash

hffs daemon start [--port PORT_NUM]

```

`--port` 参数配置 daemon 进程的端口号。

#### 关闭 HFFS

```bash

hffs daemon stop

```

### Peer 管理

> [!NOTE]
> 关于自动 Peer 管理：为了提高易用性，HFFS 计划加入自动 Peer 管理功能（HFFS 自动发现、连接 Peer）。在该功能发布以前，用户可以通过下面的命令手动管理 Peer。

在 Unix-like 操作系统上，可以使用[这里](https://www.51cto.com/article/720658.html)介绍的 `ifconfig` 或者 `hostname` 命令行查找机器的 IP 地址。 在 Windows 操作系统上，可以使用[这里](https://support.microsoft.com/zh-cn/windows/%E5%9C%A8-windows-%E4%B8%AD%E6%9F%A5%E6%89%BE-ip-%E5%9C%B0%E5%9D%80-f21a9bbc-c582-55cd-35e0-73431160a1b9)介绍的方式找到机器的 IP 地址。

#### 添加 Peer

```bash

hffs peer add IP [--port PORT_NUM]

```

用户通过上面的命令把 peer 节点配对。配对后，两个节点之间的模型实现互通共享。其中，

- `IP` 参数是目标节点的 ip 地址
- `PORT_NUM` 参数是目标节点 daemon 进程的端口号

#### 查看 Peer

```bash

hffs peer ls

```

用户通过上面的命令查看 peer 信息。
在 Daemon 已经启动的情况下， Daemon 会定期查询其他 peer 是否在线。`hffs peer ls` 命令会把在线的 peer 标注为 "_active_"。

> [!NOTE]
> 如果 peer 互通在 Windows 上出现问题，请检查：1. Daemon 是否已经启动，2. Windows的防火墙是否打开（参见[这里](https://support.microsoft.com/zh-cn/windows/%E5%85%81%E8%AE%B8%E5%BA%94%E7%94%A8%E9%80%9A%E8%BF%87-windows-defender-%E9%98%B2%E7%81%AB%E5%A2%99%E7%9A%84%E9%A3%8E%E9%99%A9-654559af-3f54-3dcf-349f-71ccd90bcc5c)）

#### 删除 Peer

```bash

hffs peer rm IP [--port PORT_NUM]

```

用户通过上面的命令删除 peer 节点。

### 模型管理

#### 查看模型

```bash

hffs model ls [--repo_id REPO_ID] [--file FILE]

```

扫描已经下载的模型。该命令返回如下信息：

- 如果没有指定 REPO_ID，返回 repo 列表
  - `REPO_ID` 的[相关文档](https://huggingface.co/docs/hub/en/api#get-apimodelsrepoid-or-apimodelsrepoidrevisionrevision)
- 如果制定了 REPO_ID，但是没有指定 FILE，返回 repo 中所有缓存的文件
  - `FILE` 是模型文件相对 git root 目录的相对路径，该路径可以在 huggingface 的网页上查看
  - 在执行添加、删除模型文件命令的时候，都需要使用该路径作为参数指定目标文件；
- 如果同时制定了 `REPO_ID` 和 `FILE`，返回指定文件在本机文件系统中的绝对路径
  - 用户可以使用该绝对路径访问模型文件
  - 注意：在 Unix-like 的操作系统中，由于缓存内部使用了软连接的方式保存文件，目标模型文件的 git 路径以及文件系统中的路径别没有直接关系

#### 搜索模型

```bash

hffs model search REPO_ID FILE [--revision REVISION]

```

搜索目标模型文件在哪些 peer 上已经存在。

- 如果模型还未下载到本地，从 peer 节点或者 hf.co 下载目标模型
- `REPO_ID`参数说明见`hffs model ls`命令
- `FILE`参数说明见`hffs model ls`命令
- `REVISION`的[相关文档](https://huggingface.co/docs/hub/en/api#get-apimodelsrepoid-or-apimodelsrepoidrevisionrevision)

#### 添加模型

```bash

hffs model add REPO_ID FILE [--revision REVISION]

```

下载指定的模型。

- 如果模型还未下载到本地，从 peer 节点或者 hf.co 下载目标模型
- `REPO_ID`参数说明见`hffs model ls`命令
- `FILE`参数说明见`hffs model ls`命令
- `REVISION`参数说明见`hffs model search`命令

#### 删除模型

```bash

hffs model rm REPO_ID FILE [--revision REVISION]

```

删除已经下载的模型数据。

- 如果模型还未下载到本地，从 peer 节点或者 hf.co 下载目标模型
- `REPO_ID`参数说明见`hffs model ls`命令
- `FILE`参数说明见`hffs model ls`命令
- `REVISION`的[相关文档](https://huggingface.co/docs/hub/en/api#get-apimodelsrepoid-or-apimodelsrepoidrevisionrevision)

### 配置管理

#### 工作目录管理

##### 工作目录设置

```bash
hffs conf cache set HOME_PATH
```

设置服务的工作目录，包括配置存放目录和文件下载目录

- `HOME_PATH` 工作目录的路径，路径必须已存在

##### 工作目录获取

```bash
hffs conf cache get
```

获取当前生效的工作目录。注意：此路径非set设置的路径，环境变量会覆盖set设置的路径。

##### 工作目录重置

```bash
hffs conf cache reset
```

恢复配置的工作目录路径为默认路径。注意：此操作无法重置环境变量的设置。

### 卸载管理

#### 卸载软件

> [!WARNING]
>
> 卸载软件将会清除所有添加的配置以及已下载的模型，无法恢复，请谨慎操作！

```bash
# 清除用户数据
hffs uninstall

# 卸载软件包
pip uninstall hffs
```
