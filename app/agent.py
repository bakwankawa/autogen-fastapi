from autogen import register_function, GroupChat, GroupChatManager
from agent_wrapper import ChainlitAssistantAgent, ChainlitUserProxyAgent
from app.utils import load_yaml, load_conversation_history, get_nama_rm
from config.config import SERPER_API_KEY, gpt4_config, cosmosdb_client, apify_client
import requests, json
from typing_extensions import Annotated
from fastapi import HTTPException

# Load the messages from the YAML file
data = load_yaml('data/prompt.yaml')

# Example usage
selected_value = '138626'
nama_rm = get_nama_rm(selected_value)

# Extract the messages
admin_system_message = data['prompt']['admin_system_message'].replace("{rm_name}", nama_rm)
manager_system_message = data['prompt']['manager_system_message']
spokesman_system_message = data['prompt']['spokesman_system_message']
analyst_system_message = data['prompt']['analyst_system_message']
researcher_internal_system_message = data['prompt']['researcher_internal_system_message']
researcher_external_system_message = data['prompt']['researcher_external_system_message']

# Initialize Agents
admin = ChainlitUserProxyAgent(name="Admin", system_message=admin_system_message, code_execution_config=False)
manager = ChainlitAssistantAgent(
    name="Manager",
    system_message=manager_system_message,
    llm_config=gpt4_config,
)

spokesman = ChainlitAssistantAgent(
    name="Spokesman",
    system_message=spokesman_system_message,
    llm_config=gpt4_config,
    description="Can only be called after Analyst or Manager or Admin. Handling small talk is spokesman responsibility."
)

researcher_internal = ChainlitAssistantAgent(
    name="Researcher_Internal",
    system_message=researcher_internal_system_message,
    llm_config=gpt4_config,
)

researcher_external = ChainlitAssistantAgent(
    name="Researcher_External",
    system_message=researcher_external_system_message,
    llm_config=gpt4_config,
    description="A helpful and general-purpose AI assistant that has capability to gather information from public data including Google Search, Google Maps Search, and Web Scraping."
)

analyst = ChainlitAssistantAgent(
    name="Analyst",
    system_message=analyst_system_message,
    llm_config=gpt4_config,
)

executor = ChainlitUserProxyAgent(
    name="Executor",
    system_message="Executor. Execute the web browsing google map, web scrapping, and get relevant data from internal database",
    human_input_mode="NEVER"# Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
)

# Function for google search
def google_search(
    search_keyword: Annotated[str, "the keyword to search information by google api"]) -> Annotated[dict, "the json response from the google search api"]:
    """
    Perform a Google search using the provided search keyword.

    Args:
    search_keyword (str): The keyword to search on Google.

    Returns:
    str: The response text from the Google search API.
    """
    try:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": search_keyword})
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=payload)

        # Check if the response status is OK
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Google Search API error: {str(e)}")

# Function for google maps search
def google_maps_search(
    keyword: Annotated[str, "the keyword to search location"]) -> Annotated[dict, "the json response from the google maps api"]:
    """
    Perform a Google search using the provided search keyword.

    Args:
    search_keyword (str): The keyword to search on Google.

    Returns:
    str: The response text from the Google search API.
    """
    try:
        url = "https://google.serper.dev/maps"
        payload = json.dumps({"q": keyword})
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=payload)

        # Check if the response status is OK
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Google Maps API error: {str(e)}")

# Function for web scraping
def scrape_page(url: Annotated[str, "The URL of the web page to scrape"]) -> Annotated[str, "Scraped content"]:
    """
    Scrape the content from a specified web page URL using Apify's scraping capabilities.

    Args:
    url (str): The URL of the web page to scrape.

    Returns:
    str: The scraped content from the page.
    """
    try:
        # Prepare the Actor input
        run_input = {
            "startUrls": [{"url": url}],
            "useSitemaps": False,
            "crawlerType": "playwright:firefox",
            "includeUrlGlobs": [],
            "excludeUrlGlobs": [],
            "ignoreCanonicalUrl": False,
            "maxCrawlDepth": 0,
            "maxCrawlPages": 1,
            "initialConcurrency": 0,
            "maxConcurrency": 200,
            "initialCookies": [],
            "proxyConfiguration": {"useApifyProxy": True},
            "maxSessionRotations": 10,
            "maxRequestRetries": 5,
            "requestTimeoutSecs": 60,
            "dynamicContentWaitSecs": 10,
            "maxScrollHeightPixels": 5000,
            "removeElementsCssSelector": """nav, footer, script, style, noscript, svg,
        [role=\"alert\"],
        [role=\"banner\"],
        [role=\"dialog\"],
        [role=\"alertdialog\"],
        [role=\"region\"][aria-label*=\"skip\" i],
        [aria-modal=\"true\"]""",
            "removeCookieWarnings": True,
            "clickElementsCssSelector": '[aria-expanded="false"]',
            "htmlTransformer": "readableText",
            "readableTextCharThreshold": 100,
            "aggressivePrune": False,
            "debugMode": True,
            "debugLog": True,
            "saveHtml": True,
            "saveMarkdown": True,
            "saveFiles": False,
            "saveScreenshots": False,
            "maxResults": 9999999,
            "clientSideMinChangePercentage": 15,
            "renderingTypeDetectionPercentage": 10,
        }

        run = apify_client.actor("aYG0l9s7dbB7j3gbS").call(run_input=run_input)

        if run.get("status") != "SUCCEEDED":
            raise HTTPException(status_code=500, detail=f"Apify scraping failed with status {run.get('status')}")

        text_data = ""
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            text_data += item.get("text", "") + "\n"

        return text_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web scraping error: {str(e)}")

# Function for getting internal pipeline data
def gather_internal_pipeline_data() -> str:
    """
    Function to be used by the ResearcherPipeline agent to gather data from Cosmos DB.

    Args:
    None

    Returns:
    str: A JSON string of the pipeline data for 'pn_rm' = selected_value.
    """
    database_name = 'rm_pipeline'
    container_name = selected_value

    # Mendapatkan referensi ke database dan kontainer
    database = cosmosdb_client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    # Mengambil semua data dari kontainer
    all_items = list(container.query_items(
        query="SELECT c.pn_rm, c.nama_rm, c.jenis_pipeline, c.pipeline_group, c.nama_calon_nasabah, c.no_telepon_nasabah, c.alamat, c.nilai_potensi, c.jenis_potensi, c.potensi_sales_volume, c.potensi_casa, c.potensi_freq_transaksi, c.day_last_trx, c.rating, c.keterangan_potensi, c.date ,c.action_plan ,c.program FROM c",
        enable_cross_partition_query=True
    ))[:50]

    # Convert the clean data to a JSON string
    result = json.dumps(all_items, separators=(',', ':'))
    
    # Format the result with the required sentence and two new lines
    formatted_result = f"Result from relevant pipeline data: \n\n{result}"
    
    return formatted_result

# Function for getting internal kpi data
def gather_internal_kpi_data() -> str:
    """
    Function to be used by the ResearcherKPI agent to gather data from Cosmos DB.

    Args:
    None

    Returns:
    str: A JSON string of the KPI data with unmet targets for 'pn_rm' = selected_value.
    """
    database_name = 'rm_kpi'
    container_name = selected_value

    # Mendapatkan referensi ke database dan kontainer
    database = cosmosdb_client.get_database_client(database_name)
    container = database.get_container_client(container_name)

    # Mengambil semua data dari kontainer
    all_items = list(container.query_items(
        query="SELECT c.pn_rm, c.nama_rm, c['key_performance_index (KPI)'], c.target_KPI, c.pencapaian_KPI FROM c",
        enable_cross_partition_query=True
    ))

    # Convert the clean data to a JSON string
    result = json.dumps(all_items, separators=(',', ':'))
    
    # Format the result with the required sentence and two new lines
    formatted_result = f"Result from relevant target KPI data: \n\n{result}"
    
    return formatted_result

register_function(
    google_search,
    caller=researcher_external,  # The planner agent can suggest calls to gather_pipeline_data.
    executor=executor,  # The ResearcherPipeline agent can execute the gather_pipeline_data calls.
    name="google_search",  # By default, the function name is used as the tool name.
    description="useful tool for search information about anything in internet"
)

register_function(
    google_maps_search,
    caller=researcher_external,  # The planner agent can suggest calls to gather_pipeline_data.
    executor=executor,  # The ResearcherPipeline agent can execute the gather_pipeline_data calls.
    name="google_maps_search",  # By default, the function name is used as the tool name.
    description="useful tool for search location by google maps api"
)

register_function(
    scrape_page,
    caller=researcher_external,  # The planner agent can suggest calls to gather_pipeline_data.
    executor=executor,  # The ResearcherPipeline agent can execute the gather_pipeline_data calls.
    name="scrap_page",  # By default, the function name is used as the tool name.
    description="useful tool for web scraping"
)

register_function(
    gather_internal_pipeline_data,
    caller=researcher_internal,  # The planner agent can suggest calls to gather_pipeline_data.
    executor=executor,  # The ResearcherPipeline agent can execute the gather_pipeline_data calls.
    name="gather_internal_pipeline_data",  # By default, the function name is used as the tool name.
    description="useful tool for getting internal pipeline data to provide recommendations"
)

register_function(
    gather_internal_kpi_data,
    caller=researcher_internal,  # The planner agent can suggest calls to gather_pipeline_data.
    executor=executor,  # The ResearcherPipeline agent can execute the gather_pipeline_data calls.
    name="gather_internal_kpi_data",  # By default, the function name is used as the tool name.
    description="useful tool for getting internal kpi target to provide recommendations"
)

async def main(message):
    disallowed_transition = {
        manager: [admin],
        admin: [researcher_external, researcher_internal, analyst],
        researcher_external: [manager, spokesman, admin],
        researcher_internal: [manager, spokesman, admin],
        analyst: [manager, admin]
    }

    # Load the conversation history (already formatted as a list of strings)
    conversation_history = await load_conversation_history('138626', 3)

    # Add the new user message as a JSON string to the history list
    new_message = json.dumps({"role": "Admin", "content": message})
    conversation_history.append(new_message)

    # Combine the history into a single JSON array string
    message_content = f"[{','.join(conversation_history)}]"

    # Debug print to check the final message content before initiating chat
    # print(f"[DEBUG] Final message content: {message_content}")

    # Create a GroupChat instance with the manager, planner, researchers, and analyst
    group_chat = GroupChat(
        agents=[admin, manager, spokesman, researcher_external, researcher_internal, analyst, executor],
        allowed_or_disallowed_speaker_transitions=disallowed_transition,
        speaker_transitions_type='disallowed',
        messages=[],
        max_round=20,
        speaker_selection_method="auto"
    )
    
    # Create a GroupChatManager
    chat_manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=gpt4_config,
        system_message="You are a Chat Manager, responsible to manage chat between multiple Agents. If the user asking complex query that need collaboration from other Agents to answer, please Ask Manager. If the user asking simple query and small talk, please ask Spokesman.")
    
    # Initiate chat with the combined message content
    admin.initiate_chat(
        chat_manager,
        message=message_content,
    )