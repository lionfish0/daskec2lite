# -*- coding: utf-8 -*-
"""dask-ec2lite:dask-ec2lite provides entry point main()."""
__version__ = "0.2.0"
import sys
import boto3
import paramiko
import botocore
import os
import time
import argparse


def pingserver(hostname):
    return os.system("ping -W 3 -c 1 " + hostname)==0


def start_cluster(num_instances=2, instance_type='c4.xlarge',imageid=None,keyname=None,spotprice='1.00',region_name=None,sgid=None):
    """
    Start a cluster
    
    """
    assert sgid is not None
    assert imageid is not None
    assert keyname is not None
    assert region_name is not None
    
    
    client = boto3.client('ec2', region_name=region_name)
    response = client.request_spot_instances(
        DryRun=False,
        SpotPrice=spotprice,
        InstanceCount=num_instances,
        Type='one-time',
        LaunchSpecification={
            'ImageId': imageid,
            'KeyName': keyname,
            'InstanceType': instance_type,
            'SecurityGroupIds': [ sgid ]
        }
    )

    sirids = []
    for sir in response['SpotInstanceRequests']:
        sirids.append(sir['SpotInstanceRequestId'])

    print("Waiting for spot instance object...")
    while True:
        try:
            response_desc = client.describe_spot_instance_requests(SpotInstanceRequestIds=sirids)
            break
        except botocore.exceptions.ClientError:
            pass
        time.sleep(1)


    print("Waiting for spot instances to be fulfilled")
    instance_ids = []

    while (True):
        time.sleep(3)
        response_desc = client.describe_spot_instance_requests(SpotInstanceRequestIds=sirids)
        for sir in response_desc['SpotInstanceRequests']:
            if(sir['Status']['Code']!='fulfilled'): #if any of them aren't fulfilled then we go 'round the loop again
                continue
        break #otherwise we've got them fulfilled

    print("Getting instance ids:")
    for sir in response_desc['SpotInstanceRequests']:    
        instance_ids.append(sir['InstanceId'])    

    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(InstanceIds=instance_ids)        

    addresses = []
    print("Waiting for spot instance IP addresses...")
    for rev in response['Reservations']:
        for ins in rev['Instances']:
            while (True): #wait for public ips to become available...
                try:
                    addresses.append(ins['PublicIpAddress'])
                    break
                except KeyError:
                    pass
                time.sleep(1)

    print("Waiting for instances to be up [respond to pings]...")
    allup = False
    while not allup:
        time.sleep(3)
        allup = True
        for address in addresses:
            time.sleep(0.1)
            if not pingserver(address):
                allup = False
                break #break out of loop and wait

    return addresses, instance_ids

def startdask(instance_ip, pathtokeyfile, username, scheduler_ip=None):
    """
    startdask(instance_ip, username, key, scheduler_ip=None)
    Start a worker or a scheduler on an instance
        instance_ip = string of instance IP
        username & key = username and path to key
        scheduler_ip = leave as None to set up the scheduler
    """
    key = paramiko.RSAKey.from_private_key_file(pathtokeyfile)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    
    if scheduler_ip is not None:
        cmd = 'export PATH="/home/mike/anaconda3/bin:$PATH"; nohup dask-worker %s:8786 &>/dev/null &' % scheduler_ip
    else:
        cmd = 'export PATH="/home/mike/anaconda3/bin:$PATH"; nohup dask-scheduler &>/dev/null &'
    client.connect(hostname=instance_ip, username=username, pkey=key)
    stdin, stdout, stderr = client.exec_command(cmd)
    client.close()

        
def start_dask_cluster(addresses,pathtokeyfile,username,workers_per_instance=4):
    scheduler_ip = addresses[0]
    startdask(scheduler_ip,pathtokeyfile,username)
    import time
    time.sleep(5) #wait for the scheduler to sort itself
    for address in addresses:
        for _ in range(workers_per_instance):
            startdask(address,pathtokeyfile,username,scheduler_ip)
            time.sleep(1)        

def destroy_cluster(instance_ids,region_name='eu-west-1'):
    if len(instance_ids)<1:
        return
    ec2 = boto3.resource('ec2', region_name=region_name)
    ec2.instances.filter(InstanceIds=instance_ids).terminate()


def main():
    parser = argparse.ArgumentParser(description='''Create an EC2 spot-price cluster, populate with a dask scheduler and workers. \n
    Example: 
    
        daskec2lite --pathtokeyfile '/home/mike/.ssh/research.pem' --keyname 'research' --username 'mike' --imageid ami-19a58760 --sgid sg-9146afe9

    ''')

    parser.add_argument('--pathtokeyfile', type=str, nargs='?',dest='pathtokeyfile',action='store',
                        help='path to keyfile [required]')
    parser.add_argument('--keyname', type=str, nargs='?',dest='keyname',action='store',
                        help='key name to use to access instances [required]')                         
    parser.add_argument('--username', type=str, nargs='?',dest='username',action='store',
                        help='user to log into remote instances as [required]')
    parser.add_argument('--numinstances', type=int, nargs='?',dest='num_instances',default=2,action='store',
                        help='number of instances to start')                        
    parser.add_argument('--instancetype', type=str, nargs='?',dest='instance_type',default='c4.xlarge',action='store',
                        help='type of instance to request')
    parser.add_argument('--imageid', type=str, nargs='?',dest='imageid',action='store',
                        help='AWS image to use [required]')
    parser.add_argument('--spotprice', type=str, nargs='?',dest='spotprice',default='1.00',action='store',
                        help='Spot price limit ($/hour/instance)')
    parser.add_argument('--region', type=str, nargs='?',dest='region_name',default='eu-west-1',action='store',
                        help='Region to use')  
    parser.add_argument('--wpi', type=int, nargs='?',dest='workers_per_instance',default=4,action='store',
                        help='Workers per instance')
    parser.add_argument('--sgid', type=str, nargs='?',dest='sgid',action='store',
                        help='Security Group ID [required]')    
    parser.add_argument('--destroy', dest='destroy',action='store_const', const=True, default=False,
                        help='Destroy the cluster')                            
                                                                                                                  
    args = parser.parse_args()
    
    if args.destroy:
        with open('ec2litecluster.csv', 'r') as file_handler:
            instance_ids = []
            a = file_handler.read()
            instance_ids = a.split('\n')
            instance_ids = [i for i in instance_ids if len(i)>1] #strim short/empty strings    

        if len(instance_ids)<1:
            print("No instances to terminate")
            return
        print("Destroying Cluster (%d instances)" % len(instance_ids))
        destroy_cluster(instance_ids,args.region_name)  
        
        #empty the file
        with open('ec2litecluster.csv', 'w') as file_handler:
            file_handler.write("\n")
        return

    addresses,instance_ids = start_cluster(num_instances=args.num_instances,instance_type=args.instance_type,
                imageid=args.imageid,keyname=args.keyname,spotprice=args.spotprice,region_name=args.region_name,sgid=args.sgid)  
    time.sleep(5) #give it a bit more time!
    start_dask_cluster(addresses,pathtokeyfile=args.pathtokeyfile,username = args.username,workers_per_instance = args.workers_per_instance)

    print("Connect to remote scheduler here:")
    print("\n")
    print("          http://%s:8787/status" % addresses[0])
    
    
    with open('ec2litecluster.csv', 'w') as file_handler:
        for item in instance_ids:
            file_handler.write("%s\n" % item)
