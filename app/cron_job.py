from config.config import redis_client

# Function to delete Redis data
def delete_conversation_data(conversation_key):
    try:
        redis_client.delete(conversation_key)
        print(f"Deleted data for key: {conversation_key}")
    except Exception as e:
        print(f"Failed to delete data for key {conversation_key}: {e}")

# The key to delete
conversation_key = 'conversation_history_138626'

if __name__ == "__main__":
    delete_conversation_data(conversation_key)