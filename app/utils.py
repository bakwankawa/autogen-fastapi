import yaml
import json
from config.config import redis_client, cosmosdb_client

# Load YAML data from a file
def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def save_message_to_redis(pn_rm, message, role, name):
    conversation_key = f"conversation_history_{pn_rm}"

    # Only save messages from "Admin" and "Spokesman"
    if name not in ["Admin", "Spokesman"]:
        return

    # Ensure message content is always saved as a string
    if isinstance(message, dict) and "content" in message:
        message_content = message["content"]
    else:
        message_content = message

    # Avoid saving the whole previous conversation history
    if isinstance(message_content, str):
        try:
            # Try to load it as JSON to check if it's mistakenly nested
            loaded_content = json.loads(message_content)
            if isinstance(loaded_content, list) and len(loaded_content) > 0 and isinstance(loaded_content[0], dict):
                # If it's a list of dicts, take the last message only
                message_content = loaded_content[-1]["content"]
        except json.JSONDecodeError:
            pass  # If it's not JSON, it's fine to save as is

    # Format the message in the desired structure as a JSON string
    formatted_message = json.dumps({"role": name, "content": message_content})

    # Save the formatted message to Redis as a string
    redis_client.rpush(conversation_key, formatted_message)

#     # Also save the conversation history to a local JSON file
#     save_conversation_to_json(pn_rm, formatted_message)

# def save_conversation_to_json(pn_rm, new_message):
#     # Define the file path for the JSON file
#     json_file_path = f"conversation_history_{pn_rm}.json"

#     # Check if the JSON file already exists
#     if os.path.exists(json_file_path):
#         # Load the existing conversation history from the JSON file
#         with open(json_file_path, 'r') as file:
#             conversation_history = json.load(file)
#     else:
#         # If the file does not exist, start with an empty history
#         conversation_history = []

#     # Append the new message to the conversation history
#     conversation_history.append(json.loads(new_message))

#     # Save the updated conversation history back to the JSON file
#     with open(json_file_path, 'w') as file:
#         json.dump(conversation_history, file, indent=4)

async def load_conversation_history(pn_rm, pair_count):
    conversation_key = f"conversation_history_{pn_rm}"
    # Load all conversation history from Redis
    history = redis_client.lrange(conversation_key, 0, -1)

    # Decode each history entry and keep it as a string
    loaded_history = [item.decode('utf-8') for item in history[-pair_count*2:]]
    
    return loaded_history

def get_container(database_name, container_name):
    database = cosmosdb_client.get_database_client(database_name)
    return database.get_container_client(container_name)

def get_nama_rm(selected_value) -> str:
    """
    Function to retrieve 'nama_rm' from the Cosmos DB for the given 'pn_rm'.

    Args:
    selected_value (str): The 'pn_rm' value to filter the data.

    Returns:
    str: The 'nama_rm' associated with the given 'pn_rm'.
    """
    container = get_container('rm_kpi', selected_value)
    query = "SELECT c.pn_rm, c.nama_rm FROM c"
    all_items = list(container.query_items(query=query, enable_cross_partition_query=True))

    for item in all_items:
        if str(item.get('pn_rm')) == str(selected_value):
            return item.get('nama_rm', "Unknown")
    return "Unknown"