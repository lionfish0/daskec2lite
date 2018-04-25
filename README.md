# dask-ec2lite
Makes a bunch of EC2 spot priced instances and starts dask running on them.

### Install
Sorry, I forgot to include boto3 and paramiko in setup.py, so you've got to install them yourself;

    pip install boto3
    pip install paramiko
    pip install git+https://github.com/lionfish0/daskec2lite.git

### Usage
    daskec2lite --help

    usage: daskec2lite [-h] [--pathtokeyfile [PATHTOKEYFILE]]
                       [--keyname [KEYNAME]] [--username [USERNAME]]
                       [--numinstances [NUM_INSTANCES]]
                       [--instancetype [INSTANCE_TYPE]] [--imageid [IMAGEID]]
                       [--spotprice [SPOTPRICE]] [--region [REGION_NAME]]
                       [--wpi [WORKERS_PER_INSTANCE]] [--sgid [SGID]] [--destroy]

    Create an EC2 spot-price cluster, populate with a dask scheduler and workers.
    Example: daskec2lite --pathtokeyfile '/home/mike/.ssh/research.pem' --keyname
    'research' --username 'mike' --imageid ami-19a58760 --sgid sg-9146afe9

    optional arguments:
      -h, --help            show this help message and exit
      --pathtokeyfile [PATHTOKEYFILE]
                            path to keyfile [required]
      --keyname [KEYNAME]   key name to use to access instances [required]
      --username [USERNAME]
                            user to log into remote instances as [required]
      --numinstances [NUM_INSTANCES]
                            number of instances to start
      --instancetype [INSTANCE_TYPE]
                            type of instance to request
      --imageid [IMAGEID]   AWS image to use [required]
      --spotprice [SPOTPRICE]
                            Spot price limit ($/hour/instance)
      --region [REGION_NAME]
                            Region to use
      --wpi [WORKERS_PER_INSTANCE]
                            Workers per instance
      --sgid [SGID]         Security Group ID [required]
      --destroy             Destroy the cluster
