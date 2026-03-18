from telethon import TelegramClient, events

api_id = 32424333
api_hash = "3fae8215547deff7b0930dbff9870226"

client = TelegramClient('session', api_id, api_hash)


channels = ["osinttv", "defencesphere","MappingConflicts","goreunit"]

@client.on(events.NewMessage(chats=channels))
async def handler(event):
    message = event.message.text
    
    print("\nNEW MESSAGE:")
    print(message)
    print("-" * 50)

client.start()
print("Listening for new messages...\n")

client.run_until_disconnected()