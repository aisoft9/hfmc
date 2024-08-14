# HuggingFace Model Cache 使用指南

## 如何下载并共享模型

### 准备

1. 准备2台节点：Pegasus 和 Cygnus。这里使用两台节点的目的是演示局域网内模型共享功能。
2. 我们使用`prajjwal1/bert-medium`（[链接](https://huggingface.co/prajjwal1/bert-medium/tree/main)）模型做演示。
3. 在每个节点上安装 HFMC。HFMC 的安装说明请见[这里](/docs/README.zh.md#安装-hfmc)。

### 从 hf-mirror.com 下载模型

在节点 Pegasus 上，运行下面的命令下载目标模型。由于 HFMC 内部集成了 hf-mirror.com 镜像网站，中国大陆的用户即使不使用 VPN 也可以成功下载到目标模型。

    hfmc model add -r prajjwal1/bert-medium -v REV_NUM

然后，执行下面的命令查看下载好的模型。

    hfmc model ls

### 通过局域网分享模型

在节点 Pegasus 和 Cygnus 上分别通过下面的命令启动 HFMC Daemon。

    hfmc daemon start

然后，通过 `ifconfig` 或者类似的命令在系统上查找节点的 IP 地址。

之后，在节点 Cygnus 上，通过下面的命令把 Pegasus 加入自己的 Peer 列表中。

    hfmc peer add IP_OF_PEGAUS

最后，在节点 Cygnus 上，通过下面的命令从 Pegasus 上下载模型 `prajjwal1/bert-medium`。

    hfmc model add -r prajjwal1/bert-medium

由于目标模型通过局域网进行下载，所以速度应该明显加快。用户可以尝试使用更大的模型进行实验，这样更容易观察到下载效率和稳定性的区别。

## 如何下载需要Token的模型

某些模型（例如 meta-llama-3.1-8B）需要用户提供 auth token 才能下载。下载这些模型前，用户可以首先使用下面的命令进行 HuggingFace 认证，然后再下载模型。

    hfmc auth login

之后，hfmc 会提示用户输入 auth token。

> [!NOTE]
>
> HFMC 使用 [huggingface_hub](https://github.com/huggingface/huggingface_hub) 库处理用户的 auth token。HFMC 本身不会访问或者存储用户的 auth token 信息。

使用下面的命令logout。

    hfmc auth logout

## 如何下载单个模型文件

HFMC 不仅允许用户一次性下载、删除整个模型仓库，还支持用户以文件为单位管理模型。

下载通过使用 `-f` 参数指定目标文件。

    hfmc model add -r prajjwal1/bert-medium -f pytorch_model.bin

## 如何指定本地模型缓存路径

默认情况下，HFMC 把下载好的模型放在 `~/.cache/hfmc` 目录中。如果用户向修改该路径，可以使用下面的命令。

    hfmc conf cache set NEW_CACHE_DIR

通过执行下面的命令，用户可以查看当前的缓存路径。

    hfmc conf cache get

## 常见问题

### 为什么下载整个模型仓库的时候，必须提供 revision (-v) 参数？

使用 HFMC 添加模型仓库的时候，仓库中的文件可能来自不同的服务器。比如，文件 pytorch_model-1.bin 可能来自节点 Pegasus，而文件 pytorch_model-2.bin 可能来自节点 Cygnus。如果使用默认值 `main` 而不指定具体的 revision 值，有可能导致不同文件的版本不一致的情况。为了避免出现类似的情况，用户需要在下载整个模型仓库的时候指定明确的 revision 参数。（参见[这里](https://stackoverflow.com/questions/73145810/how-do-git-revisions-and-references-relate-to-each-other)了解 git revision 和 git reference 的区别会有助理解文件版本有可能不一致的原因。）

### 不启动 Daemon 还能使用 HFMC 吗？

HFMC Daemon 的作用和其他 HFMC Peer 协同工作。如果不启动 Daemon，用户仍然可以使用 HFMC 下载和管理模型。但此时，用户只能从镜像网站和 hf 原站下载模型，而不能从其他 HFMC 节点下载模型；用户也没有不能把自己的模型共享给其他 HFMC 节点。

### 如果下载过程中，Peer 失去链接会怎么样？

如果下载过程中，一个 Peer 下线了，HFMC 会尝试从其他 Peer 下载目标模型。如果其他 Peer 都没有目标模型，HFMC 会通过断点续传的方式从镜像网站和 hf 原站继续下载模型。

### 如何卸载 HFMC

可以执行下面的命令卸载 HFMC。

    hfmc uninstall
