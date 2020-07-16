from . import client
# from .database import init_database, User, Game
# from .botlogic import respond
from threading import Timer


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await respond(message)


def main():
    # Timer(30, User.inventory_users, [client, Session()]).start()
    # Timer(60, Game.inventory_games, [client, Session()]).start()
    # client.run(config.token)


if __name__ == "__main__":
    main()