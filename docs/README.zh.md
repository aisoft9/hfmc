
# HuggingFace Model Cache

[English](/README.md)

HuggingFace Model Cache (简称 "HFMC") 是一款“小而美”的工具，旨在帮助用户更快、更容易地使用HuggingFace上的模型。HFMC 可以帮助用户完成下面的工作：

1. 和其他 HFMC 节点之间共享模型文件，避免从 hf.co 原站重复下载同一个模型；
2. 自动从局域网、镜像网站、hf 源站之间选择最佳下载方式；
3. 实现模型下载的断点续传，减少由于网络不稳定而浪费的网络流量和宝贵时间；
4. 快速查看、增、删本地模型文件，让模型管理变得更加容易；

## HFMC 的功能

### 模型共享

在同一个局域网中，使用 HFMC 的两个节点之间可以通过局域网共享模型。比如节点 Pegasus 已经下载了 meta-llama-3.1-8B 模型，当节点 Cygnus 想要下载 meta-llama-3.1-8B 的时候，HFMC 会通过局域网从节点 Pegasus 下载模型，这比从 huggingface.co 下载更快速、更稳定、更便宜。

通过这种方式，同一个实验室或者办公室里的同事可以快速分享模型，用户还可以通过 HFMC 在一个GPU集群中快速分发模型。

### 多源下载

HFMC 整合了多个下载源为用户提供模型下载功能。具体说来，如果用户通过 HFMC 下载模型，HFMC 会依次尝试从局域网（来自其他 HFMC 的节点），hf 镜像网站（如 hf-mirror.com），和 hf 源站下载目标模型。

### 断点续传

相比通过浏览器手动下载 HuggingFace 上的模型，HFMC 提供了断点续传功能。HFMC 具备“跨源断点续传”功能，比如，在局域网上中断的下载可以无缝切换到镜像网站继续完成模型下载。

### 模型管理

HFMC 提供命令行工具帮助用户浏览、下载、删除本地的模型文件。模型文件的大小、数量、路径等信息可以通过一个命令一览无余。

## 安装 HFMC

HFMC 支持 3.8+ 版本的 Python。使用下面的命令即可以安装 HFMC.

    pip install hfmc

## 详细文档

- [HFMC 的使用指南](/docs/GUIDELINE.zh.md)
- [HFMC 命令行手册](/docs/REFERENCE.zh.md)
