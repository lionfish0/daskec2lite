#!/usr/bin/env python

import sys
import boto3
import botocore
import os
import time
import argparse

def destroy_cluster(instance_ids,region_name='eu-west-1'):
    ec2 = boto3.resource('ec2', region_name=region_name)
    ec2.instances.filter(InstanceIds=instance_ids).terminate()


def main():
    parser = argparse.ArgumentParser(description='''Destroy an EC2 spot-price cluster.\n
    Example: 
    
        daskec2lite-destroy

    ''')
    parser.add_argument('--region', type=str, nargs='?',dest='region_name',default='eu-west-1',action='store',
                        help='Region to use')                                 
                       
    args = parser.parse_args()
    
    with open('ec2litecluster.csv', 'r') as file_handler:
        instance_ids = []
        a = file_handler.read()
        instance_ids = a.split('\n')
        instance_ids = [i for i in instance_ids if len(i)>1] #strim short/empty strings    

    print("Destroying Cluster (%d instances)" % len(instance_ids))
    destroy_cluster(instance_ids,args.region_name)  
    
    #empty the file
    with open('ec2litecluster.csv', 'w') as file_handler:
        file_handler.write("\n")
        
main()
