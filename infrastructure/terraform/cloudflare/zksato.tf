variable "zksato_hostname" {
  type        = string
  default     = "zksato.zeaz.dev"
  description = "Public hostname for the zksato trading control plane."

  validation {
    condition     = endswith(lower(var.zksato_hostname), ".${lower(var.zone_name)}")
    error_message = "zksato_hostname must be a subdomain of zone_name."
  }
}

variable "zksato_origin" {
  type        = string
  default     = "http://127.0.0.1:9569"
  description = "Loopback origin for the zksato API and dashboard."

  validation {
    condition     = var.zksato_origin == "http://127.0.0.1:9569"
    error_message = "zksato_origin must use the reviewed zksato origin at http://127.0.0.1:9569."
  }
}

resource "cloudflare_dns_record" "zksato" {
  zone_id = var.cloudflare_zone_id
  name    = var.zksato_hostname
  type    = "CNAME"
  content = local.tunnel_cname
  ttl     = 1
  proxied = true
  comment = "zksato trading control plane via Cloudflare Tunnel"
}

output "zksato_url" {
  value       = "https://${var.zksato_hostname}"
  description = "Public zksato URL after the proxied DNS record and tunnel ingress are active."
}
