import boto3
import botocore
import click

session = boto3.Session(profile_name='tr-corporate-sandbox')
ec2 = session.resource('ec2')
iam = session.resource('iam')

def filter_instances(project):
    instances=[]
    
    if project:
        filters = [{'Name':'tag:Name', 'Values':[project]}] 
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@click.group()
def cli():
    '''
    Shotty manages snapshots
    '''
@cli.command()
@click.option('--prof', default=None,
    help="Specifies a profile for the process.")
def get_profile(profile):
    print(iam.get_user())
    return

@cli.group('snapshots')
def snapshots():
    '''
    Commands for snapshots
    '''

@snapshots.command('list')
@click.option('--project', default=None,
    help='Only snapshots for project (tag Project:<name>')
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="List all snapshots for each volume, not just the most recent")
def list_snapshots(project, list_all):
    "List EC2 snapshots"

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(", ".join((
                  s.id,
                  v.id,
                  i.id,
                  s.state,
                  s.progress,
                  s.start_time.strftime('%c')
                )))

                if s.state == 'completed' and not list_all: break
    return
            
@cli.group('volumes')
def volumes():
    '''
    Commands for volumes
    '''

@volumes.command('list')
@click.option('--project', default=None,
    help='Only volumes for project (tag Name:<name>')
def list_volumes(project):
    '''
    List EC2 volumes
    '''
    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            print(", ".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return

@cli.group('instances')
def instances():
    '''
    Commands for instances
    '''

@instances.command('reboot',
    help="Reboot some instances")
@click.option('--project', default=None,
    help="Only instances for project (tag Name:<name>)")
@click.option('--force', default=False, is_flag=True,
    help="Required flag if --project is not specified.")
def reboot_instances(project, force):
    # Initial safety check to make sure everything isn't rebooted
    if project is None and not force:
        print("ERROR: Use --force with command to reboot all instances")
        return

    instances = filter_instances(project)
        
    for i in instances:
        print("Stopping {}...".format(i.id))
        i.stop()
        i.wait_until_stopped()
        print("Restarting {}...".format(i.id))
        i.start()
        i.wait_until_running()
    print("No project specified.")
    return


@instances.command('snapshot',
    help="Create snapshots of all volumes")
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>")
@click.option('--force', default=False, is_flag=True,
    help="Required flag if --project is not specified.")
def create_snapshots(project, force):
    '''
    Create snapshots for EC2 instances
    '''
    if project is None and not force:
        print("ERROR: Use --force with command to create snapshots of all instances")
        return

    instances = filter_instances(project)

    for i in instances:
        print("Stopping {}...".format(i.id))
        i.stop()
        i.wait_until_stopped()
        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("  Skipping {}, snapshot already in progress".format(v.id))
                continue
            print("Creating snapshot of {}".format(v.id))
            v.create_snapshot(Description="Created by SnapshotAlyzer")
        print("Starting {}...".format(i.id))
        i.start()
        i.wait_until_running()
    print("Job's done!")
    return

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
@click.option('--force', default=None, is_flag=True,
    help="Required flag to run list if --project is not specified")
def list_instances(project, force):
    '''
    List EC2 instances
    '''
    if project is None and not force:
        print("ERROR: Use --force flag with argument to list all instances")
        return

    instances = filter_instances(project)

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or [] }
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('tr:resource-owner', '<no resource owner>'),
            tags.get('Name', '<no project>')
        )))
    return

# VERY dangerous command if using a public AWS account
@instances.command('stop')
@click.option('--project', default=None,
    help='Only instances for project')
@click.option('--force', default=False, is_flag=True,
    help="Required flag if --project is not specified.")
def stop_instances(project, force):
    "Stop EC2 instances"
    if project is None and not force:
        print("ERROR: Use --force flag with argument to stop all instances")
        return

    instances = filter_instances(project) 

    for i in instances:
        print("Stopping {}...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print(" Could not stop {}.".format(i.id) + str(e))
            continue

    return

@instances.command('start')
@click.option('--project', default=None,
    help='Only instances for project')
@click.option('--force', default=False, is_flag=True,
    help="Required flag if --project is not specified.")
def stop_instances(project, force):
    "Start EC2 instances"
    if project is None and not force:
        print("ERROR: Use --force flag with argument to start all instances")
        return

    instances = filter_instances(project) 

    for i in instances:
        print("Starting {}...".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print(" Could not start {}. ".format(i.id) + str(e))
            continue
    return

if __name__ == '__main__':
    cli()

