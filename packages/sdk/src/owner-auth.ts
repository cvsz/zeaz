export function ownerHeaders(adminKey: string): HeadersInit {
  const bytes = new TextEncoder().encode(adminKey);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return {"X-Admin-Key-B64": btoa(binary)};
}
