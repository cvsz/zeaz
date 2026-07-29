declare const process: { env: Record<string, string | undefined> };
export interface AppEnv { API_URL: string; NODE_ENV: "development" | "test" | "production"; }
export function readEnv(source: Record<string, string | undefined> = typeof process !== "undefined" ? process.env : {}): AppEnv { const API_URL=source.API_URL ?? "http://127.0.0.1:8000"; if (!/^https?:\/\//.test(API_URL)) throw new Error("API_URL must be an absolute HTTP(S) URL"); const NODE_ENV=(source.NODE_ENV ?? "development") as AppEnv["NODE_ENV"]; return { API_URL, NODE_ENV }; }
