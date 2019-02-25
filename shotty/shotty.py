import boto3
import click

session = boto3.Session(profile_name='tr-corporate-sandbox')
ec2 = session.resource('ec2')

@click.group()
def instances():
    '''
    Commands for instances
    '''

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances for project (tag Project:<name>)")
def list_instances(project):
    '''
    List EC2 instances
    '''
    instances=[]

    if project:
        filters = [{'Name':'tag:Project', 'Values':["a204503-J-Farrell-Guru-instances"]}] 
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or [] }
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>')
        )))
    return

@instances.command('stop')
@click.option('--project', defualt=None,
    help='Only instances for project')
def stop_instances(project):
    "Stop EC2 instances"
    instances=[]

    if project:
        filters = [{'Name':'tag:Project', 'Values':[project]}] 
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    for i in instances:
        print("Stopping {}...".format(i.id))
        i.stop()

if __name__ == '__main__':
    instances()

