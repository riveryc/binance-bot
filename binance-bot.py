import os, time, re
from binance.client import Client
from slackclient import SlackClient


# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
bruno_id = None

# binance information fetch
quoteAsset = "BTC"
apikey = "api-key"
apisecret = "api-secret"
proxies = {
    'http': os.environ.get('http_proxy'),
    'https': os.environ.get('https_proxy')
}
client = Client(apikey, apisecret, {'proxies': proxies})
exchangeInfo = client.get_exchange_info()
quoteAssetSymbol = [item["symbol"] for item in exchangeInfo["symbols"]
            if item["symbol"].endswith(quoteAsset)]

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == bruno_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    BTCUSDT = client.get_symbol_ticker(symbol="BTCUSDT")
    if quoteAssetSymbol.__contains__(command.upper()+quoteAsset):
        # Check the Symbol price
        result = client.get_symbol_ticker(symbol=command.upper()+quoteAsset)
        price_in_Dollar = float(result['price'])*float(BTCUSDT['price'])
        response = "{0} vs BTC: {1}, about ${2}".format(command.upper(),result['price'],price_in_Dollar)
    elif command.upper() == "BTC":
        # Check BTC's price vs USDT
        response = "BTC: ${0}".format(BTCUSDT['price'])
    else:
        response = "I just need valid Coin name, I cannot do more than that right now..."


    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response
    )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        bruno_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
