import os
import json
import datetime
import uuid

CHAT_FOLDER = "chats"

# Make sure chats folder exists
if not os.path.exists(CHAT_FOLDER):
    os.makedirs(CHAT_FOLDER)

class ChatManager:
    def __init__(self):
        self.current_chat_id = None

    def create_new_chat(self):
        chat_id = str(uuid.uuid4())
        chat_data = {
            "id": chat_id,
            "name": f"New Chat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "messages": [],
            "last_updated": datetime.datetime.now().isoformat()
        }
        self.save_chat(chat_data)
        self.current_chat_id = chat_id
        return chat_id, chat_data['name']

    def save_message_to_chat(self, chat_id, message):
        path = os.path.join(CHAT_FOLDER, f"{chat_id}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
        else:
            chat_data = {"id": chat_id, "messages": [], "name": "Unnamed Chat", "last_updated": datetime.datetime.now().isoformat()}

        chat_data['messages'].append(message)
        chat_data['last_updated'] = datetime.datetime.now().isoformat()

        self.save_chat(chat_data)

    def load_chat(self, chat_id):
        path = os.path.join(CHAT_FOLDER, f"{chat_id}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return None

    def delete_chat(self, chat_id):
        path = os.path.join(CHAT_FOLDER, f"{chat_id}.json")
        if os.path.exists(path):
            os.remove(path)

    def list_all_chats(self):
        chats = []
        for filename in os.listdir(CHAT_FOLDER):
            if filename.endswith(".json"):
                path = os.path.join(CHAT_FOLDER, filename)
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    chats.append({
                        "id": data.get("id"),
                        "name": data.get("name", "Unnamed Chat"),
                        "last_updated": data.get("last_updated", "Unknown")
                    })
        chats.sort(key=lambda x: x['last_updated'], reverse=True)
        return chats

    def save_chat(self, chat_data):
        path = os.path.join(CHAT_FOLDER, f"{chat_data['id']}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2)

# Example usage
if __name__ == "__main__":
    manager = ChatManager()
    new_chat_id, chat_name = manager.create_new_chat()
    manager.save_message_to_chat(new_chat_id, {"role": "user", "text": "Hello!"})
    print(manager.load_chat(new_chat_id))
    print(manager.list_all_chats())