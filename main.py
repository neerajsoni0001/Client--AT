from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto
from config import *
from db import *

# Create a Telethon client
client = TelegramClient("CLIENT_PROD", api_id=19039081, api_hash="99a625135a721998787c2230acdd587b")

async def main():
    try:
        SOURCE_CHANNEL = get_all_sources()[0]
        DESTINATION_CHANNEL = get_all_destinations()

        print(f"Listening for new messages in {SOURCE_CHANNEL}...")

        async def process_message_text(message_text):
            """Process and replace usernames and URLs in the message text."""
            try:
                input_usernames = get_input_usernames()
                output_username = get_output_username()
                banned_urls = get_banned_url()
                output_url = get_output_url()

                # Replace usernames
                for i_username in input_usernames:
                    if i_username in message_text:
                        message_text = message_text.replace(i_username, output_username)

                # Replace banned URLs
                for banned_url in banned_urls:
                    if banned_url in message_text:
                        message_text = message_text.replace(banned_url, output_url)

            except Exception as e:
                print(f"[ERROR] Failed to process message text: {e}")
            return message_text

        @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
        async def forward_message(event):
            print("[INFO] New message detected.")
            try:
                current_status = get_current_status()
                if current_status != "running":
                    print("[INFO] Current status is not 'running'. Ignoring message.")
                    return

                # Check the current status for image forwarding
                current_image_status = get_image_status()

                # If the message contains media (e.g., an image)
                if event.message.media and isinstance(event.message.media, MessageMediaPhoto):
                    if current_image_status == "on":
                        try:
                            # Process caption text (if present)
                            caption = event.message.text or ""
                            processed_caption = await process_message_text(caption)
                            print(f"[INFO] Received an image with caption: {processed_caption}")

                            # Forward the image with the processed caption
                            for dest_channel in DESTINATION_CHANNEL:
                                await client.send_message(dest_channel, event.message, caption=processed_caption)
                            print("[SUCCESS] Image message forwarded.")
                        except Exception as e:
                            print(f"[ERROR] Failed to forward image message: {e}")
                    else:
                        print("[INFO] Image messages are disabled. Ignoring this image.")

                # If the message is plain text
                elif event.message.text:
                    try:
                        print(f"[INFO] Received a text message: {event.message.text}")
                        processed_text = await process_message_text(event.message.text)

                        # Forward the text message
                        for dest_channel in DESTINATION_CHANNEL:
                            await client.send_message(dest_channel, processed_text)
                        print("[SUCCESS] Text message forwarded.")
                    except Exception as e:
                        print(f"[ERROR] Failed to forward text message: {e}")

                # For other types of messages (e.g., unsupported media)
                else:
                    print("[INFO] Received a message of unsupported type. Ignoring it.")

            except Exception as e:
                print(f"[ERROR] Error while processing message: {e}")

        # Keep the client running
        await client.run_until_disconnected()

    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to set up the script: {e}")

# Run the script
if __name__ == "__main__":
    try:
        with client:
            print("[INFO] Starting the Telegram client...")
            client.loop.run_until_complete(main())
    except Exception as e:
        print(f"[FATAL ERROR] Unexpected error occurred: {e}")
