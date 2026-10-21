from apify_client import ApifyClient

# Required: Set your Apify API Token here.
# Obtain your token from your Apify account settings.
# For better security, use an environment variable instead of hardcoding the token.
APIFY_TOKEN = ""

# Required: Set the Apify Actor ID used to scrape Google Maps reviews.
ACTOR_ID = ""


def fetch_google_reviews(url, max_reviews=10):
    """Fetch raw Google Maps reviews using the Apify API."""

    client = ApifyClient(APIFY_TOKEN)

    run_input = {
        "startUrls": [{"url": url}],
        "maxReviews": max_reviews,
        "reviewsSort": "newest",
        "language": "en",
        "reviewsOrigin": "all",
        "personalData": True,
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)
    return client.dataset(run["defaultDatasetId"]).iterate_items()
