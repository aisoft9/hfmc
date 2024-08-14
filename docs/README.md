# HuggingFace Model Cache

[简体中文](https://github.com/madstorage-dev/hffs/blob/main/doc/README.zh.md)

HuggingFace Model Cache (referred to as "HFMC") is a compact and efficient tool designed to help users use models on HuggingFace faster and more easily. HFMC assists users in the following ways:

1. Sharing model files between different HFMC nodes to avoid downloading the same model repeatedly from hf.co;
2. Automatically selecting the best download method from local networks, mirror sites, and hf sources;
3. Supporting resuming model downloads from the point of interruption to reduce wasted bandwidth and precious time due to unstable networks;
4. Quickly viewing, adding, and deleting local model files to make model management easier.

## Features of HFMC

### Model Sharing

Within the same local network, HFMC nodes can share models with each other. For instance, if node "Pegasus" has downloaded the meta-llama-3.1-8B model and node "Cygnus" wants to download it, HFMC will fetch the model from node "Pegasus" over the local network. This is faster, more stable, and more cost-effective than downloading from huggingface.co.

In this way, colleagues within the same lab or office can quickly share models, and users can also use HFMC to rapidly distribute models within a GPU cluster.

### Multi-Source Download

HFMC integrates multiple download sources to provide model download functionality. Specifically, when a user downloads a model via HFMC, it will sequentially attempt to download the target model from the local network (from other HFMC nodes), hf mirror sites (such as hf-mirror.com), and hf source sites.

### Resume Interrupted Downloads

Compared to manually downloading models from HuggingFace via a browser, HFMC offers resuming interrupted downloads. HFMC supports "cross-source resume" functionality, meaning an interrupted download on a local network can seamlessly continue from a mirror site.

### Model Management

HFMC provides a command-line tool to help users browse, download, and delete local model files. Information about model file sizes, quantities, and paths can be easily reviewed with a single command.

## Installing HFMC

HFMC supports Python version 3.8 and above. Install HFMC using the following command:

    pip install hfmc

## Detailed Documentation

- [HFMC User Guide](https://github.com/madstorage-dev/hffs/blob/main/doc/GUIDELINE.en.md)
- [HFMC Command Line Reference](https://github.com/madstorage-dev/hffs/blob/main/doc/REFERENCE.en.md)
