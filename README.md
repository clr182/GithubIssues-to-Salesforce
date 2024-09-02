# Github to salesforce

This is a simple project to create a connection between Github and Salesforce.
You can use this project to create a webhook in Github that will send a message to Salesforce when a new issue is created.

## Usage

1. Clone the repo
2. cd to repo
3. `pip install requests -t .`
4. `zip -r ../function.zip .`
5. Upload the zip file to AWS Lambda
6. Configure Salesforce connected app
7. Set env variables in AWS Lambda.
8. Set up API gateway to trigger the AWS Lambda function.
9. Configure github repo to send a webhook to the AWS Lambda function.
10. Test with a new issue in Github.


## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
