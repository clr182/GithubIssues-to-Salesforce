public class GitHubQueueable implements Queueable, Database.AllowsCallouts {
    private List<FeedItem> feedItems;

    public GitHubQueueable(List<FeedItem> feedItems) {
        this.feedItems = feedItems;
    }

    public void execute(QueueableContext context) {
        for (FeedItem item : feedItems) {
            Case relatedCase = [SELECT Id, GitHub_Repo_URL__c, CustomField_GitHub_Issue_ID__c FROM Case WHERE Id = :item.ParentId LIMIT 1];
            
            if (item.Visibility == 'AllUsers') {
                GitHubHandler.handlePublicFeedItem(item, relatedCase);
            } else {
                GitHubHandler.handleInternalFeedItem(item);
            }
        }
    }
}