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

        # Check for X-GitHub-Event header
        github_event = event.get('headers', {}).get('X-GitHub-Event')
        
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps('Error: No body found in the event')
            }

        data = json.loads(event['body'])
        repository = data.get('repository', {}).get('full_name')
        issue_data = data.get('issue', {})
        comment_data = data.get('comment', {})

        if github_event == 'issues':
            action = data.get('action')
            if action == 'opened':
                create_salesforce_ticket(access_token, instance_url, issue_data, repository)
        elif github_event == 'issue_comment':
            action = data.get('action')
            if action == 'created' and comment_data:
                add_salesforce_comment(access_token, instance_url, issue_data, comment_data)

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
        response = requests.get(url, headers=headers, params=data)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=data)

    # If the session is invalid, re-authenticate and retry the request
    if response.status_code == 401:  # Unauthorized / Token Expired
        access_token, instance_url = salesforce_authentication()
        headers['Authorization'] = f'Bearer {access_token}'
        if method == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)

    response.raise_for_status()
    return response.json()

def create_salesforce_ticket(access_token, instance_url, issue_data, repository):
    url = f"{instance_url}/services/data/v56.0/sobjects/Case"
    data = {
        'Subject': issue_data.get('title', 'No Title'),
        'Description': f"Issue in repo {repository}: {issue_data.get('body', 'No Description')}",
        'CustomField_GitHub_Issue_ID__c': issue_data.get('id', ''),
        'CustomField_GitHub_Repo__c': repository
    }

    return make_salesforce_request(url, method='POST', data=data, access_token=access_token, instance_url=instance_url)

def add_salesforce_comment(access_token, instance_url, issue_data, comment_data):
    # First, query to find the Case ID using the GitHub Issue ID
    query_url = f"{instance_url}/services/data/v56.0/query"
    query = f"SELECT Id FROM Case WHERE CustomField_GitHub_Issue_ID__c = '{issue_data.get('id', '')}'"
    
    try:
        cases = make_salesforce_request(query_url, method='GET', access_token=access_token, instance_url=instance_url, data={'q': query})
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error querying Salesforce: {str(e)}")
    
    if cases.get('totalSize', 0) > 0:
        case_id = cases['records'][0]['Id']
        comment_url = f"{instance_url}/services/data/v56.0/sobjects/CaseComment/"
        
        # Prepare data for the new comment
        data = {
            'ParentId': case_id,
            'CommentBody': comment_data.get('body', 'No Comment')
        }

        # POST request to create the new comment
        return make_salesforce_request(comment_url, method='POST', data=data, access_token=access_token, instance_url=instance_url)
    else:
        raise Exception(f"No case found with GitHub Issue ID: {issue_data.get('id', '')}")
