# HuggingFace Model Cache Command Line Reference

## HFMC Command Line Categories

HFMC command lines are mainly categorized as follows:

- [Model Management](#model-management): Add, delete, and browse local model files
- [Authorization Management](#authorization-management): Log in to HuggingFace via auth token on the command line (authorization is required for downloading ["Gated Models"](https://huggingface.co/docs/hub/en/models-gated))
- [Daemon Management](#daemon-management): HFMC shares model files over the local network via the Daemon process
- [Peer Management](#peer-management): Add, delete, and browse other HFMC nodes that can share model files
- [Configuration Management](#configuration-management): Modify and display HFMC configuration parameters

## Model Management

### Add and Delete Models

Add an entire model repository:

    hfmc model add -r REPO_ID [-v REVISION]

Delete an entire model repository:

    hfmc model rm -r REPO_ID [-v REVISION]

Add a single model file:

    hfmc model add -r REPO_ID -f FILE_NAME [-v REVISION]

Delete a single model file:

    hfmc model rm -r REPO_ID -f FILE_NAME [-v REVISION]

### Browse Downloaded Models

Browse model repository information:

    hfmc model ls

Browse files in a specific model repository:

    hfmc model ls -r REPO_ID

## Authorization Management

Log in to HuggingFace:

    hfmc auth login

Log out of HuggingFace:

    hfmc auth logout

## Daemon Management

Start the Daemon:

    hfmc daemon start

Check Daemon status:

    hfmc daemon status

Stop the Daemon:

    hfmc daemon stop

## Peer Management

Add a Peer:

    hfmc peer add IP [-p PORT]

Remove a Peer:

    hfmc peer rm IP [-p PORT]

Browse Peers:

    hfmc peer ls

## Configuration Management

Commands related to local cache path configuration:

    # Modify cache path
    hfmc conf cache set CACHE_PATH

    # View cache path
    hfmc conf cache get

    # Reset to default cache path
    hfmc conf cache reset

Commands related to Daemon port configuration:

    # Modify Daemon port
    hfmc conf port set DAEMON_PORT
    
    # View Daemon port
    hfmc conf port get
    
    # Reset to default Daemon port
    hfmc conf port reset
