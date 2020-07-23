import base64
import sys
import json
import googleapiclient.discovery
import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler
from googleapiclient.discovery_cache.base import Cache # pylint: disable=import-error

## Logging Configuration
client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
google.cloud.logging.handlers.setup_logging(handler)
logging.getLogger().setLevel(logging.WARN)


## Process the log from pub/sub trigger, main function logic
def process_log_entry(data, context):
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)
    service = create_service()

## Check if member still exists, if not - exit
    outside_member_id_list = log_entry['jsonPayload']['properties']['bindingDeltas']
    outside_member_ids = find_member(outside_member_id_list)
    print(f"Outside Anomalous Member(s): {outside_member_ids}")

## Determine if project or organization and perform logic based on bound resource layer
    properties = log_entry['jsonPayload']['properties']
    for entry in properties:
        if 'project_id' in entry:
            resource = properties['project_id']
            print(f"The Project ID is {resource}")

            resource_bindings = retrieve_bindings(service, resource)
            check_if_member_exists = check_member_on_resource(outside_member_ids, resource_bindings)

            if check_if_member_exists is True:
                bindings_removed = remove_anomalous_iam_resource(outside_member_ids, resource_bindings)
                set_iam_binding_resource(resource, service, bindings_removed)
            else:
                logging.debug("Member does not exist.")
                sys.exit(0)
        elif 'organization_id' in entry:
                resource = 'organizations/' + properties['organization_id']
                print(f"The Organization is {resource}")

                resource_bindings = retrieve_bindings(service, resource)
                check_if_member_exists = check_member_on_resource(outside_member_ids, resource_bindings)
                
                if check_if_member_exists is True:
                    bindings_removed = remove_anomalous_iam_resource(outside_member_ids, resource_bindings)
                    set_iam_binding_resource(resource, service, bindings_removed)
                else:
                    logging.debug("Member does not exist.")
                    sys.exit(0)

## Finds the bound anomalous member as GCP stores it. Member input capitalization may vary
## so this is to capture how it is stored in GCP.
def find_member(outside_member_id_list):
    members = []
    try:
        for member in outside_member_id_list:
            member = member['member']
            members.append(member)
    except:
        logging.debug("Could not find anomalous member on resource.")
        sys.exit(0)

    return members

## Resources have IAM bindings. We need to return those to parse through.
def retrieve_bindings(service, resource):
    if 'organizations' in resource:
        request = service.organizations().getIamPolicy(resource=f"{resource}")
        response = request.execute()
        resource_bindings = response.pop("bindings")
        print(f"Current organization bindings: {resource_bindings}")
    else:
        request = service.projects().getIamPolicy(resource=resource)
        response = request.execute()
        resource_bindings = response.pop("bindings")
        print(f"Current project bindings: {resource_bindings}")

    return resource_bindings

## Check if member is still bound to resource
def check_member_on_resource(outside_member_ids, resource_bindings):
    for bindings in resource_bindings:
        for values in bindings.values():
            for member in outside_member_ids:
                if member in values:
                    try:
                        print(f"Member found: {member}")
                        return True
                    except:
                        logging.info("Did not find the anomalous member.")
                        continue
                else:
                    logging.debug("Did not find the anomalous member.")

## Looks for our anomalous IAM member and removes from resource bindings
def remove_anomalous_iam_resource(outside_member_ids, resource_bindings):
    bindings_removed = resource_bindings
    for dic in bindings_removed:
        if 'members' in dic:
            for values in dic.values():
                for member in outside_member_ids:
                    if member in values:
                        try:
                            values.remove(member)
                            print(f"Member removed: {member}")
                        except:
                            logging.info(f"{member} not found.")
                            continue
                    else:
                        logging.debug(f"{member} not found.")
    print(f"New bindings after anomalous member(s) removed: {bindings_removed}")

    return bindings_removed

## Set our new resource IAM bindings
def set_iam_binding_resource(resource, service, bindings_removed):
    set_iam_policy_request_body = {
        "policy": {
            "bindings": [
                bindings_removed
            ]
        }
    }
    if 'organizations' in resource:
        request = service.organizations().setIamPolicy(resource=f"{resource}", body=set_iam_policy_request_body)
        binding_response = request.execute()
        print(f"New policy attached to the organization: {binding_response}")
    else:
        request = service.projects().setIamPolicy(resource=resource, body=set_iam_policy_request_body)
        binding_response = request.execute()
        print(f"New policy attached to the project: {binding_response}")

## Creates the GCP Cloud Resource Service
def create_service():
    return googleapiclient.discovery.build('cloudresourcemanager', 'v1', cache=MemoryCache())

class MemoryCache(Cache):
    """
    File-based cache to resolve GCP Cloud Function noisey log entries.
    """
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content
