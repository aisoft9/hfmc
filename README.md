# 什么是 HuggingFace FS ？

HuggingFace FS (简称 "HFFS") 目标成为一款“小而美”的工具，帮助中国大陆用户在使用 [HuggingFace](huggingface.co) 的时候，能够方便地下载、管理、分享来自 HF 的模型。

中国大陆用户需要配置代理服务才能访问 HuggingFace 主站。大陆地区和 HuggingFace 主站之间的网络带宽较低而且不稳定，可靠的镜像网站很少，模型文件又很大。因此，下载 HuggingFace 上模型文件的时间往往很长。HFFS 在 hf.co 的基础上增加了 P2P 的模型共享方式，让大陆地区用户能够以更快的速度获得所需要的模型。

HFFS 的典型使用场景有：

- 如果实验室或者开发部门的其他小伙伴已经下载了你需要的模型文件，HFFS 的 P2P 共享方式能让你从他们那里得到模型，模型的下载速度不再是个头疼的问题。当然，如果目标模型还没有被其他人下载过，HFFS 会自动从 hf.co 主站和镜像网站下载模型，然后你可以通过 HFFS 把模型分享给其他小伙伴。
- 有些小伙伴需要两台主机（Windows 和 Linux）完成模型的下载和使用：Windows 上的 VPN 很容易配置，所以它负责下载模型；Linux 的开发环境很方便，所以它负责模型的微调、推理等任务。通过 HFFS 的 P2P 共享功能，两台主机之间的模型下载和拷贝就不在再需要手动操作了。

下面是 HFFS 所提供的命令行文档。看看它们是如何帮助用户访问模型文件的吧。

# HFFS 的命令行

## HFFS 服务管理

### 启动 HFFS

```bash

hffs start

```

用户通过上面的命令开启本地 HFFS 服务。如果还未初始化，该命令则初始化 HFFS。

### 关闭 HFFS

```bash

hffs stop [--destroy-cache]

```

用户通过上面的命令关闭本地 HFFS 服务。如果指定 --destory-cache 选项，则删除本地下载的模型。

## Peer 管理

> [!NOTE]
> 关于自动 Peer 管理：为了提高易用性，HFFS 计划加入自动 Peer 管理功能（HFFS 自动发现、连接 Peer）。在该功能发布以前，用户可以通过下面的命令手动管理 Peer。

### 添加 Peer

```bash

hffs peer add [HOST|IP|FILE]

```

用户通过上面的命令把 peer 节点配对。配对后，两个节点之间的模型实现互通共享。

- `HOST|IP` 参数是目标节点的 host 或者 ip 地址，如果有多个值，用逗号隔开
- `FILE` 参数是配置文件路径，peer 的 host 或者 ip 可以保存在文件中管理

### 查看 Peer

```bash

hffs peer ls

```

用户通过上面的命令查看 peer 信息。

### 删除 Peer

```bash

hffs peer rm [HOST|IP|FILE]

```

用户通过上面的命令删除 peer 节点。

## 模型管理

### 查看模型

```bash

hffs model ls [repo-id]

```

扫描已经下载的模型。该命令返回如下信息：

- repo-id：repo-id 的 [相关文档](https://huggingface.co/docs/hub/en/api#get-apimodelsrepoid-or-apimodelsrepoidrevisionrevision)
- branch：默认是 `main`
- revision：默认是最新 revision
- size on disk：模型在本地文件系统中所占空间的大小
- num of files：模型所包括的文件个数
- local path：模型在本地文件系统中的路径
- fully downoaded：模型是否已经被完整下载

### 添加模型

```bash

hffs model add repo-id [--branch BRANCH] [--revision REVISION]

```

下载指定的模型。

- 如果模型已经下载到本地了，返回 `hffs model ls repo-id` 命令的返回信息
- 如果模型还未下载到本地，从 peer 节点或者 hf.co 下载目标模型，显示下载进度条，结束后返回 `hffs model ls repo-id` 命令的返回信息

### 删除模型

```bash

hffs model rm repo-id [--branch BRANCH] [--revision REVISION]

```

删除已经下载的模型数据。
