from channels.routing import include

channel_routing = [
    include("casting.channels.channel_routing", path="^/casting/")
]
