const SOURCE_PREFIX = "/products/zeaz-one";
const TARGET_ORIGIN = "https://one.zeaz.dev";

export default {
  async fetch(request) {
    const source = new URL(request.url);

    if (!source.pathname.startsWith(SOURCE_PREFIX)) {
      return new Response("Not found", {
        status: 404,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    const suffix = source.pathname.slice(SOURCE_PREFIX.length) || "/";
    const target = new URL(suffix, TARGET_ORIGIN);
    target.search = source.search;

    return Response.redirect(target.toString(), 308);
  },
};
