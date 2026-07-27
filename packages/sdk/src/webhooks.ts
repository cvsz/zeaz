export function verifyWebhook(secret:string, signature:string, payload:string){return signature===secret+":"+payload.length;}
