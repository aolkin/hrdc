window.channels = (function() {
    class WebSocketBridge {
        constructor() {
            this.socket = null;
            this.streams = {};
            this.default_cb = null;
        }

        connect(path) {
            const scheme = location.protocol === "https:" ? "wss" : "ws";
            this.socket = new WebSocket(scheme + "://" + location.host + path);
            this.socket.addEventListener("message", (event) => {
                const msg = JSON.parse(event.data);
                if (msg.stream !== undefined) {
                    const cb = this.streams[msg.stream];
                    if (cb) {
                        cb(msg.payload, msg.stream);
                    }
                } else if (this.default_cb) {
                    this.default_cb(msg, undefined);
                }
            });
        }

        listen(cb) {
            this.default_cb = cb;
        }

        demultiplex(stream, cb) {
            this.streams[stream] = cb;
        }

        send(msg) {
            this.socket.send(JSON.stringify(msg));
        }

        stream(name) {
            return {
                send: (payload) => this.send({stream: name, payload: payload}),
            };
        }
    }

    return {WebSocketBridge: WebSocketBridge};
})();
