from channels.routing import include

channel_routing = [
    include("casting.routing.channel_routing", path="^/casting/")
]
