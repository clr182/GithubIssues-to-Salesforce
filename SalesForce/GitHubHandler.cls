public class GitHubHandler {

    // Method to handle public FeedItems
    public static void handlePublicFeedItem(FeedItem item, Case relatedCase) {
        // Send comment to GitHub
        sendToGitHub(relatedCase.GitHub_Repo_URL__c, relatedCase.CustomField_GitHub_Issue_ID__c, item);
    }

    // Method to handle internal FeedItems
    public static void handleInternalFeedItem(FeedItem item) {
        // Implementation for internal FeedItems (if needed)
    }

    // Method to send data to GitHub
public static void sendToGitHub(String repoUrl, String issueId, FeedItem item) {
    // Extract repository owner and name from the repoUrl
    String[] urlParts = repoUrl.replace('https://github.com/', '').split('/');
    String owner = urlParts[0];
    String repo = urlParts[1];
    
    // Construct the endpoint URL
    String endpointUrl = 'https://api.github.com/repos/' + owner + '/' + repo + '/issues/' + issueId + '/comments';
    
    // Create the HTTP request
    HttpRequest req = new HttpRequest();
    req.setEndpoint(endpointUrl);
    req.setMethod('POST');
    // Set the GitHub personal access token here (replace YOUR_GITHUB_PERSONAL_ACCESS_TOKEN with your actual token)
    req.setHeader('Authorization', 'Bearer YOUR_GITHUB_PERSONAL_ACCESS_TOKEN');
    req.setHeader('Content-Type', 'application/json');
    
    // Construct the request body
    String body = JSON.serialize(new Map<String, Object>{
        'body' => item.Body
    });
    req.setBody(body);
    
    // Send the request and get the response
    Http http = new Http();
    HttpResponse res = http.send(req);
    
    // Log the response
    System.debug('Response from GitHub: ' + res.getBody());
    
    // Handle the response, e.g., logging or error handling
    if (res.getStatusCode() != 201) {
        System.debug('Error posting comment to GitHub: ' + res.getBody());
    }
}

}