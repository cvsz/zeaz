output "moopiew_url" {
  value       = "https://${var.moopiew_hostname}"
  description = "Public Moopiew preorder URL after the DNS record and tunnel ingress are active."
}

output "piewdash_url" {
  value       = "https://${var.piewdash_hostname}"
  description = "Public engineering dashboard URL."
}

output "piewdash_access_audience" {
  value       = cloudflare_zero_trust_access_application.piewdash.aud
  description = "Audience claim expected on Cloudflare Access JWTs for the dashboard."
}

output "cloudflared_ingress" {
  value = [
    { hostname = var.moopiew_hostname, service = var.moopiew_origin },
    { hostname = var.piewdash_hostname, service = var.piewdash_origin },
    { service = "http_status:404" },
  ]
  description = "Ingress fragment to merge before the terminal fallback of a locally managed tunnel."
}
