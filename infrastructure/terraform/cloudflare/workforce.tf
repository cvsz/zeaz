variable "zwf_hostname" {
  type        = string
  default     = "zwf.zeaz.dev"
  description = "Public hostname for the zWorkforce API."

  validation {
    condition     = endswith(lower(var.zwf_hostname), ".${lower(var.zone_name)}")
    error_message = "zwf_hostname must be a subdomain of zone_name."
  }
}

variable "zwf_origin" {
  type        = string
  default     = "http://127.0.0.1:9570"
  description = "Loopback origin for the authenticated zWorkforce API."

  validation {
    condition     = var.zwf_origin == "http://127.0.0.1:9570"
    error_message = "zwf_origin must use the reviewed zWorkforce origin at http://127.0.0.1:9570."
  }
}

resource "cloudflare_dns_record" "zwf" {
  zone_id = var.cloudflare_zone_id
  name    = var.zwf_hostname
  type    = "CNAME"
  content = local.tunnel_cname
  ttl     = 1
  proxied = true
  comment = "zWorkforce API via Cloudflare Tunnel"
}

output "zwf_url" {
  value       = "https://${var.zwf_hostname}"
  description = "Public zWorkforce URL after the proxied DNS record and tunnel ingress are active."
}
