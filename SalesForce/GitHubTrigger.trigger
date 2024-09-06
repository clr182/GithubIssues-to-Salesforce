trigger GitHubTrigger on FeedItem (after insert) {
    List<FeedItem> publicFeedItems = new List<FeedItem>();
    
    for (FeedItem item : Trigger.new) {
        //Checks if the feed item is visible to all users i.e. public or internal
        if (item.Visibility == 'AllUsers') {
            publicFeedItems.add(item);
        }
        //Could add more conditions here for internal notes if needed
    }
    
    if (!publicFeedItems.isEmpty()) {
        // Enqueue the queueable job
        System.enqueueJob(new GitHubQueueable(publicFeedItems));
    }
}