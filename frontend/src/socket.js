const WS_URL =
  (import.meta.env.VITE_API_URL || "http://localhost:8000")
    .replace(/^http/, "ws") + "/ws";

export function connectAmbulanceSocket(onMessage) {
  let ws = null;
  let reconnectTimer = null;

  function open() {
    ws = new WebSocket(WS_URL);

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onMessage(data);
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    ws.onclose = () => {
      reconnectTimer = setTimeout(open, 2000);
    };

    ws.onerror = () => {
      ws?.close();
    };
  }

  open();

  return () => {
    clearTimeout(reconnectTimer);
    ws?.close();
  };
}