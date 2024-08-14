# HuggingFace Model Cache User Guideline

## How to Download and Share Models

### Preparation

1. Prepare two nodes: "Pegasus" and "Cygnus". The purpose of using two nodes here is to demonstrate the model sharing feature within a local network.
2. We will use the `prajjwal1/bert-medium` model ([link](https://huggingface.co/prajjwal1/bert-medium/tree/main)) for demonstration.
3. Install HFMC on each node. Installation instructions for HFMC can be found [here](/docs/README.en.md#install-hfmc).

### Downloading Models from hf-mirror.com

On node "Pegasus", run the following command to download the target model. Since HFMC integrates the hf-mirror.com mirror site, users in Mainland China can successfully download the target model even without using a VPN.

    hfmc model add -r prajjwal1/bert-medium

Then, execute the following command to view the downloaded model.

    hfmc model ls

### Sharing Models via Local Network

Start the HFMC Daemon using the following command on each node of "Pegasus" and "Cygnus".

    hfmc daemon start

Next, find the IP addresses of the nodes using `ifconfig` or a similar command.

On node "Cygnus", add "Pegasus" to its Peer list with the following command.

    hfmc peer add IP_OF_PEGAUS

Finally, on node "Cygnus", use the following command to download the `prajjwal1/bert-medium` model from "Pegasus".

    hfmc model add -r prajjwal1/bert-medium -v REV_NUM

Since the model is downloaded via the local network, the speed should be noticeably faster. Users can try experimenting with larger models to better observe the differences in download efficiency and stability.

## How to Download Models Requiring Tokens

Some models (e.g., meta-llama-3.1-8B) require users to provide an auth token to download. Before downloading these models, users can authenticate with HuggingFace using the following command.

    hfmc auth login

HFMC will then prompt users to enter their auth token.

> [!NOTE]
>
> HFMC uses the [huggingface_hub](https://github.com/huggingface/huggingface_hub) library to handle user auth tokens under the hood. HFMC itself does not access or store user auth token information.

To log out, use the following command.

    hfmc auth logout

## How to Download a Single Model File

HFMC allows users to manage models by file, in addition to downloading or deleting entire model repositories.

Specify the target file using the `-f` parameter.

    hfmc model add -r prajjwal1/bert-medium -f pytorch_model.bin

## How to Specify the Local Model Cache Path

By default, HFMC stores downloaded models in the `~/.cache/hfmc` directory. To change this path, use the following command.

    hfmc conf cache set NEW_CACHE_DIR

Execute the following command to view the current cache path.

    hfmc conf cache get

## Frequently Asked Questions

### Can I use HFMC without starting the Daemon?

The HFMC Daemon works with other HFMC Peers to collaborate. Without starting the Daemon, users can still use HFMC to download and manage models. However, users will only be able to download models from mirror sites and hf source sites, and they will not be able to share their models with other HFMC nodes.

### What happens if a Peer loses connection during download?

If a Peer goes offline during a download, HFMC will attempt to download the target model from other Peers. If no other Peers have the target model, HFMC will resume the download from the mirror site or hf source site using checkpointed downloads.

### How to Uninstall HFMC

To uninstall HFMC, use the following command.

    hfmc uninstall
