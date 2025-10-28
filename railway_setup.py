#!/usr/bin/env python3
"""
Railway API setup script - Configure the open-video-channel-indexer deployment
"""
import requests
import json
import sys

# Railway API endpoint
API_URL = "https://backboard.railway.app/graphql/v2"

# Get token from config
with open("/Users/tylerbishop/.railway/config.json") as f:
    config = json.load(f)
    TOKEN = config["user"]["token"]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def query_graphql(query, variables=None):
    """Execute GraphQL query"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    return response.json()

# Get all projects
print("Step 1: Fetching Railway projects...")
query = """
query {
  me {
    projects {
      edges {
        node {
          id
          name
          services {
            edges {
              node {
                id
                name
              }
            }
          }
          environments {
            edges {
              node {
                id
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

result = query_graphql(query)
if not result or 'errors' in result:
    print("Failed to fetch projects")
    print(json.dumps(result, indent=2))
    sys.exit(1)

# Find project by searching for the service name
project = None
service = None
for edge in result['data']['me']['projects']['edges']:
    proj = edge['node']
    # Check if this project has the open-video-channel-indexer service
    for svc_edge in proj['services']['edges']:
        if 'open-video-channel' in svc_edge['node']['name'].lower():
            project = proj
            service = svc_edge['node']
            break
    if project:
        break

if not project:
    print("Could not find project with 'open-video-channel-indexer' service")
    print("\nAll projects and services:")
    for edge in result['data']['me']['projects']['edges']:
        proj = edge['node']
        print(f"\nProject: {proj['name']}")
        for svc_edge in proj['services']['edges']:
            print(f"  - Service: {svc_edge['node']['name']}")
    sys.exit(1)

print(f"✓ Found project: {project['name']} (ID: {project['id']})")
print(f"✓ Found service: {service['name']} (ID: {service['id']})")

# Get environment ID (production)
environment = None
for env_edge in project['environments']['edges']:
    if env_edge['node']['name'] == 'production':
        environment = env_edge['node']
        break

if not environment:
    environment = project['environments']['edges'][0]['node']

print(f"✓ Using environment: {environment['name']} (ID: {environment['id']})")

# Write project config to .railway directory
railway_config = {
    "projectId": project['id'],
    "serviceId": service['id'],
    "environmentId": environment['id']
}

with open("/Users/tylerbishop/open-video-channel-indexer/.railway.json", "w") as f:
    json.dump(railway_config, f, indent=2)

print(f"\n✓ Project linked! Config saved to .railway.json")
print(f"\nNext steps:")
print(f"  - Project ID: {project['id']}")
print(f"  - Service ID: {service['id']}")
print(f"  - Environment ID: {environment['id']}")
