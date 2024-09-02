import json
import requests
import os

# Load Salesforce environment variables
SF_CLIENT_ID = os.environ['SF_CLIENT_ID']
SF_CLIENT_SECRET = os.environ['SF_CLIENT_SECRET']
SF_USERNAME = os.environ['SF_USERNAME']
SF_PASSWORD = os.environ['SF_PASSWORD']
SF_TOKEN = os.environ['SF_TOKEN']
SF_LOGIN_URL = "https://login.salesforce.com/services/oauth2/token"

def lambda_handler(event, context):
    try:
        # Ensure a fresh token is retrieved
        access_token, instance_url = salesforce_authentication()
        
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps('Error: No body found in the event')
            }

        data = json.loads(event['body'])
        repository = data.get('repository', {}).get('full_name')
        issue_data = data.get('issue')
        action = data.get('action')

        if action == 'opened':
            create_salesforce_ticket(access_token, instance_url, issue_data, repository)
        elif action == 'created':
            update_salesforce_ticket(access_token, instance_url, issue_data, data.get('comment'), repository)

        return {
            'statusCode': 200,
            'body': json.dumps('GitHub Webhook Processed Successfully')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error processing the request: {str(e)}")
        }

def salesforce_authentication():
    # Authenticate with Salesforce to obtain access token
    data = {
        'grant_type': 'password',
        'client_id': SF_CLIENT_ID,
        'client_secret': SF_CLIENT_SECRET,
        'username': SF_USERNAME,
        'password': SF_PASSWORD + SF_TOKEN
    }
    response = requests.post(SF_LOGIN_URL, data=data)
    response.raise_for_status()

    auth_response = response.json()
    access_token = auth_response['access_token']
    instance_url = auth_response['instance_url']

    return access_token, instance_url

def make_salesforce_request(url, method='GET', data=None, access_token=None, instance_url=None):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = None
    if method == 'GET':
        response = requests.get(url, headers=headers)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    elif method == 'PATCH':
        response = requests.patch(url, headers=headers, json=data)

    # If the session is invalid, re-authenticate and retry the request
    if response.status_code == 401:  # Unauthorized / Token Expired
        access_token, instance_url = salesforce_authentication()
        headers['Authorization'] = f'Bearer {access_token}'
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)

    response.raise_for_status()
    return response.json()

def create_salesforce_ticket(access_token, instance_url, issue_data, repository):
    url = f"{instance_url}/services/data/v56.0/sobjects/Case"
    data = {
        'Subject': issue_data['title'],
        'Description': f"Issue in repo {repository}: {issue_data['body']}",
        'CustomField_GitHub_Issue_ID__c': issue_data['id'],
        'CustomField_GitHub_Repo__c': repository  # Store the repo name in Salesforce
    }

    return make_salesforce_request(url, method='POST', data=data, access_token=access_token, instance_url=instance_url)

def update_salesforce_ticket(access_token, instance_url, issue_data, comment_data, repository):
    query_url = f"{instance_url}/services/data/v56.0/query"
    query = f"SELECT Id FROM Case WHERE CustomField_GitHub_Issue_ID__c = '{issue_data['id']}'"

    cases = make_salesforce_request(query_url, method='GET', access_token=access_token, instance_url=instance_url, data={'q': query})
    
    if cases['totalSize'] > 0:
        case_id = cases['records'][0]['Id']
        update_url = f"{instance_url}/services/data/v56.0/sobjects/Case/{case_id}"
        updated_description = f"Issue in repo {repository}: {issue_data['body']}"
        if comment_data:
            updated_description += f"\n\nComment: {comment_data['body']}"

        data = {
            'Description': updated_description
        }

        return make_salesforce_request(update_url, method='PATCH', data=data, access_token=access_token, instance_url=instance_url)
