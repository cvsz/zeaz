import { readEnv } from "./env.js"; export const APP_CONFIG={name:"Moopiew",...readEnv() } as const;
