
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
>
> - 确保你安装了 Python 3.11+ 版本并且安装了 pip。
> - 可以考虑使用 [Miniconda](https://docs.anaconda.com/miniconda/miniconda-install/) 安装和管理不同版本的 Python。
> - pip 的使用见 [这里](https://pip.pypa.io/en/stable/cli/pip_install/)。

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
> 关于自动 Peer 管理：为了提高易用性，HFFS 计划加入自动 Peer 管理功能（HFFS 自动发现、连接 Peer）。在该功能发布以前，用户可以通过下面的命令手动管理 Peer。在 Unix-like 操作系统上，可以使用 [这里](https://www.51cto.com/article/720658.html) 介绍的 `ifconfig` 或者 `hostname` 命令行查找机器的 IP 地址。 在 Windows 操作系统上，可以使用 [这里](https://support.microsoft.com/zh-cn/windows/%E5%9C%A8-windows-%E4%B8%AD%E6%9F%A5%E6%89%BE-ip-%E5%9C%B0%E5%9D%80-f21a9bbc-c582-55cd-35e0-73431160a1b9) 介绍的方式找到机器的 IP 地址。

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
> 如果 peer 互通在 Windows 上出现问题，请检查：1. Daemon 是否已经启动，2. Windows 的防火墙是否打开（参见 [这里](https://support.microsoft.com/zh-cn/windows/%E5%85%81%E8%AE%B8%E5%BA%94%E7%94%A8%E9%80%9A%E8%BF%87-windows-defender-%E9%98%B2%E7%81%AB%E5%A2%99%E7%9A%84%E9%A3%8E%E9%99%A9-654559af-3f54-3dcf-349f-71ccd90bcc5c)）

#### 删除 Peer

```bash
hffs peer rm IP [--port PORT_NUM]
```

用户通过上面的命令删除 peer 节点。

### 模型管理

#### 添加模型

```bash
hffs model add REPO_ID [--file FILE] [--revision REVISION]
```

使用 HFFS 下载并管理指定的模型。

下载顺序为 peer $\rightarrow$ 镜像网站 $\rightarrow$ hf.co 原站；如果 peer 节点中并未找到目标模型，并且镜像网站（hf-mirror.com 等）和 hf.co 原站都无法访问（镜像网站关闭、原站由于代理设置不当而无法联通等原因），则下载失败。

参数说明

- `REPO_ID` 的 [相关文档](https://huggingface.co/docs/hub/en/api#get-apimodelsrepoid-or-apimodelsrepoidrevisionrevision)
- `FILE` 是模型文件相对 git root 目录的相对路径
  - 该路径可以在 huggingface 的网页上查看
  - 在执行添加、删除模型文件命令的时候，都需要使用该路径作为参数指定目标文件
  - 例如，模型 [google/timesfm-1.0-200m](https://hf-mirror.com/google/timesfm-1.0-200m) 中 [checkpoint](https://hf-mirror.com/google/timesfm-1.0-200m/tree/main/checkpoints/checkpoint_1100000/state) 文件的路径为 `checkpoints/checkpoint_1100000/state`
- `REVISION` 的 [相关文档](https://huggingface.co/docs/hub/en/api#get-apimodelsrepoid-or-apimodelsrepoidrevisionrevision)
  - revision 可以是 git 分支名称/ref（如 `main`, `master` 等），或是模型在 git 中提交时的 commit 哈希值
  - 如果 revision 是 ref，HFFS 会把它映射成 commit 哈希值。

如果只提供了 `REPO_ID` 参数（没有制定 `FILE` 参数）

1. HFFS 会先从镜像网站（hf-mirror.com 等）或 hf.co 原站扫描 repo 中所有文件的文件列表；如果列表获取失败，则下载失败，HFFS 会在终端显示相关的失败原因
2. 成功获取文件列表后，HFFS 根据文件列表中的信息依次下载各个模型文件。

如果同时提供了 `REPO_ID` 参数和 `FILE` 参数，HFFS 和以 “peer $\rightarrow$ 镜像网站 $\rightarrow$ hf.co 原站”的顺序下载指定文件。

> [!NOTE] 什么时候需要使用 `FILE` 参数？
> 下列情况可以使用 `FILE` 参数
>
> 1. 只需要下载某些模型文件，而不是 repo 中所有文件
> 2. 用户自己编写脚本进行文件下载
> 3. 由于网络原因，终端无法访问 hf.co，但是浏览器可以访问 hf.co

#### 查看模型

```bash
hffs model ls [--repo_id REPO_ID] [--file FILE]
```

扫描已经下载到 HFFS 中的模型。

`REPO_ID` 和 `FILE` 参数的说明见 [[#添加模型]] 部分。

该命令返回如下信息：

- 如果没有指定 `REPO_ID`，返回 repo 列表
- 如果制定了 `REPO_ID`，但是没有指定 `FILE`，返回 repo 中所有缓存的文件
- 如果同时制定了 `REPO_ID` 和 `FILE`，返回指定文件在本机文件系统中的绝对路径
  - 用户可以使用该绝对路径访问模型文件
  - 注意：在 Unix-like 的操作系统中，由于缓存内部使用了软连接的方式保存文件，目标模型文件的 git 路径（即 `FILE` 值）和文件在本地的存放路径并没有直接关系

#### 删除模型

```bash
hffs model rm REPO_ID [--file FILE] [--revision REVISION]
```

删除 HFFS 下载的模型文件。

`REPO_ID`, `FILE`, 和 `REVISION` 参数的说明见 [[#添加模型]] 部分。

工作原理：

- 如果没有指定 `REVISION` 参数，默认删除 `main` 中的模型文件，否则删除 `REVISION` 指定版本的文件；如果本地找不到匹配的 `REVISION` 值，则不删除任何文件
- 如果制定了 `FILE` 参数，只删除目标文件；如果没有指定 `FILE` 参数，删除整个 repo；如果本地找不到匹配的 `FILE`，则不删除任何文件

#### 导入模型

```bash
hffs model import SRC_PATH REPO_ID \
 [--file FILE] \
 [--revision REVISION] \
 [--method IMPORT_METHOD]
```

将已经下载到本机的模型导入给 HFFS 管理。

交给 HFFS 管理模型的好处有：

1. 通过 [[#查看模型|hffs model ls 命令]] 查看本机模型文件的统计信息（文件数量、占用硬盘空间的大小等）
2. 通过 [[#删除模型|hffs model rm 命令]] 方便地删除模型文件、优化硬盘空间的使用率
3. 通过 HFFS 和其他 peer 节点分享模型文件

参数说明：

1. `REPO_ID`, `FILE`, 和 `REVISION` 参数的说明见 [[#添加模型]] 部分
2. `SRC_PATH` 指向待导入模型在本地的路径
3. `IMPORT_METHOD` 指定导入的方法，默认值是 `cp`（拷贝目标文件）

工作原理：

- HFFS 会把放在 `SRC_PATH` 中的模型导入到 HFFS 管理的 [[#工作目录管理|工作目录]] 中
- 如果 `SRC_PATH`
  - 指向一个文件，则必须提供 `FILE` 参数，作为该文件在 repo 根目录下的相对路径
  - 指向一个目录，则 `SRC_PATH` 会被看作 repo 的根目录，该目录下所有文件都会被导入 HFFS 的工作目录中，并保持原始目录结构；同时，`FILE` 参数的值会被忽略
- 如果 `REVISION`
  - 没有指定，HFFS 内部会用 `0000000000000000000000000000000000000000` 作为文件的 revision 值，并创建 `main` ref 指向该 revision
  - 是 40 位的 hash 值，HFFS 会使用该值作为文件的 revision 值，并创建 `main` ref 指向该 revision
  - 是一个字符串，HFFS 会使用该值作为分支名称/ref，并将 revision 值设置为 `0000000000000000000000000000000000000000`，然后将 ref 指向这个 revision
- `IMPORT_METHOD` 有支持下列值
  - `cp` （默认）- 拷贝目标文件
  - `mv` - 拷贝目标文件，成功后删除原始文件
  - `ln` - 在目标位置位原始文件创建连接（Windows 平台不支持）

#### 搜索模型

```bash
hffs model search REPO_ID [--file FILE] [--revision REVISION]
```

搜索 peer 节点，查看目标模型文件在哪些 peer 上已经存在。

`REPO_ID`, `FILE`, 和 `REVISION` 参数的说明见 [[#添加模型]] 部分。

工作原理：

- 如果没有指定 `REVISION` 参数，默认搜索 `main` 中的模型文件，否则搜索 `REVISION` 指定版本的文件
- 如果制定了 `FILE` 参数，只搜索目标模型文件；如果没有指定 `FILE` 参数，搜索和 repo 相关的所有文件
- HFFS 在终端中打印的结果包含如下信息：`peer-id:port,repo-id,file`

### 配置管理

#### 工作目录管理

HFFS 的工作目录中包括

- HFFS 的配置文件
- HFFS 所下载和管理的模型文件，以及其他相关文件

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

获取当前生效的工作目录。注意：此路径非 set 设置的路径，环境变量会覆盖 set 设置的路径。

##### 工作目录重置

```bash
hffs conf cache reset
```

恢复配置的工作目录路径为默认路径。注意：此操作无法重置环境变量的设置。

## 卸载 HFFS

> [!WARNING]
> 卸载软件将会清除所有添加的配置以及已下载的模型，无法恢复，请谨慎操作！

```bash
# 清除用户数据
hffs uninstall

# 卸载软件包
pip uninstall hffs
```
