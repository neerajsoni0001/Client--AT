from telethon import TelegramClient, sync, events
from telethon.tl.types import MessageMediaPhoto
from config import *
from db import *

# Create a Telethon client
client = TelegramClient("Client_PROD", api_id=19039081, api_hash="99a625135a721998787c2230acdd587b")
async def main():
    SOURCE_CHANNEL = get_all_sources()[0]
    DESTINATION_CHANNEL = get_all_destinations()

    print(f"Listening for new messages in {SOURCE_CHANNEL}...")

    async def process_message_text(message_text):
        """Process and replace usernames and URLs in the message text."""
        input_usernames = get_input_usernames()
        output_username = get_output_username()
        banned_urls = get_banned_url()
        output_url = get_output_url()

        try:
            # Replace usernames
            for i_username in input_usernames:
                if i_username in message_text:
                    message_text = message_text.replace(i_username, output_username)

            # Replace banned URLs
            for banned_url in banned_urls:
                if banned_url in message_text:
                    message_text = message_text.replace(banned_url, output_url)

        except IndexError:
            print("Username replacement lists are mismatched.")
        return message_text

    try:
        @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
        async def forward_message(event):
            try:
                # Check the current status for image forwarding
                current_image_status = get_image_status()

                # If the message contains media (e.g., an image)
                if event.message.media and isinstance(event.message.media, MessageMediaPhoto):
                    if current_image_status == "on":
                        # Process caption text (if present)
                        caption = event.message.text or ""
                        processed_caption = await process_message_text(caption)
                        print(f"Received an image with caption: {processed_caption}")

                        # Forward the image with the processed caption
                        for dest_channel in DESTINATION_CHANNEL:
                            await client.send_message(dest_channel, event.message, caption=processed_caption)
                        print("Image message forwarded.")
                    else:
                        print("Image messages are disabled. Ignoring this image.")

                # If the message is plain text
                elif event.message.text:
                    print(f"Received a text message: {event.message.text}")
                    processed_text = await process_message_text(event.message.text)

                    # Forward the text message
                    for dest_channel in DESTINATION_CHANNEL:
                        await client.send_message(dest_channel, processed_text)
                    print("Text message forwarded.")

                # For other types of messages (e.g., unsupported media)
                else:
                    print("Received a message of another type. Ignoring it.")

            except Exception as e:
                print(f"Failed to forward message: {e}")

    except Exception as e:
        print(f"Error setting up message listener: {e}")

    # Keep the client running
    await client.run_until_disconnected()

# Run the script
with client:
    client.loop.run_until_complete(main())
