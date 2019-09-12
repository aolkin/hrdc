from channels.routing import include

channel_routing = [
    include("casting.channels.channel_routing", path="^/casting/"),
    include("finance.channels.channel_routing", path="^/finance/")
]
