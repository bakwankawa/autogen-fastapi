import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient
import azure.cosmos.cosmos_client as cosmos_client
import redis

# Load environment variables
load_dotenv()

# Set environment variables
os.environ["AUTOGEN_USE_DOCKER"] = "0"

# GPT-4 Configuration
gpt4_config = {
    "cache_seed": None,
    "temperature": 0,
    "config_list": json.loads(os.getenv("GPT4_CONFIG_LIST")),
    "timeout": 120,
}

# Access environment variables
SERPER_API_KEY = os.getenv("SERP_API_KEY")
# AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
COSMOSDB_URL = os.getenv("COSMOSDB_URL")
COSMOSDB_AUTH = os.getenv("COSMOSDB_AUTH")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

apify_client = ApifyClient(token=os.getenv("APIFY_API_KEY"))
cosmosdb_client = cosmos_client.CosmosClient(url=COSMOSDB_URL, credential=COSMOSDB_AUTH)
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    ssl=True,
    ssl_cert_reqs=None
)