variable "z_spark_hostname" {
  type        = string
  default     = "z-spark.zeaz.dev"
  description = "Public hostname for the z-spark client."

  validation {
    condition     = endswith(lower(var.z_spark_hostname), ".${lower(var.zone_name)}")
    error_message = "z_spark_hostname must be a subdomain of zone_name."
  }
}

variable "z_spark_origin" {
  type        = string
  default     = "http://127.0.0.1:8080"
  description = "Loopback Caddy origin serving the z-spark static build and API proxy."

  validation {
    condition     = var.z_spark_origin == "http://127.0.0.1:8080"
    error_message = "z_spark_origin must use the local Caddy origin at http://127.0.0.1:8080."
  }
}

resource "cloudflare_dns_record" "z_spark" {
  zone_id = var.cloudflare_zone_id
  name    = var.z_spark_hostname
  type    = "CNAME"
  content = local.tunnel_cname
  ttl     = 1
  proxied = true
  comment = "z-spark client via Cloudflare Tunnel"
}

output "z_spark_url" {
  value       = "https://${var.z_spark_hostname}"
  description = "Public z-spark client URL after the proxied DNS record and tunnel ingress are active."
}
