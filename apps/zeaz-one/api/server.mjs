import http from "node:http";
import { readFile } from "node:fs/promises";

const port = Number.parseInt(process.env.PORT ?? "8080", 10);
const productLocation = process.env.PRODUCT_PATH ?? new URL("./product.json", import.meta.url);
const product = JSON.parse(await readFile(productLocation, "utf8"));

const commonHeaders = {
  "access-control-allow-origin": "*",
  "cache-control": "public, max-age=300",
  "content-type": "application/json; charset=utf-8",
  "referrer-policy": "no-referrer",
  "x-content-type-options": "nosniff",
};

function sendJson(response, status, body, method = "GET", extraHeaders = {}) {
  const payload = JSON.stringify(body, null, 2);
  response.writeHead(status, {
    ...commonHeaders,
    "content-length": Buffer.byteLength(payload),
    ...extraHeaders,
  });
  response.end(method === "HEAD" ? undefined : payload);
}

const server = http.createServer((request, response) => {
  const method = request.method ?? "GET";
  const url = new URL(request.url ?? "/", "http://localhost");

  if (method === "OPTIONS") {
    response.writeHead(204, {
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, HEAD, OPTIONS",
      "access-control-allow-headers": "content-type",
      "access-control-max-age": "86400",
    });
    response.end();
    return;
  }

  if (!new Set(["GET", "HEAD"]).has(method)) {
    sendJson(response, 405, { error: "method_not_allowed" }, method, { allow: "GET, HEAD, OPTIONS" });
    return;
  }

  if (url.pathname === "/" || url.pathname === "/health") {
    sendJson(response, 200, {
      service: "ZEAZ Product API",
      status: "ok",
      version: "1.0.0",
      product: "/v1/products/zeaz-one",
    }, method);
    return;
  }

  if (url.pathname === "/v1/products/zeaz-one" || url.pathname === "/v1/products/zeaz-one/") {
    sendJson(response, 200, product, method);
    return;
  }

  sendJson(response, 404, { error: "not_found", path: url.pathname }, method);
});

server.keepAliveTimeout = 65_000;
server.headersTimeout = 66_000;
server.requestTimeout = 15_000;

server.listen(port, "0.0.0.0", () => {
  console.log(JSON.stringify({ service: "zeaz-product-api", status: "listening", port }));
});

function shutdown(signal) {
  console.log(JSON.stringify({ service: "zeaz-product-api", signal, status: "shutting_down" }));
  server.close((error) => {
    if (error) {
      console.error(error);
      process.exit(1);
    }
    process.exit(0);
  });
  setTimeout(() => process.exit(1), 10_000).unref();
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
