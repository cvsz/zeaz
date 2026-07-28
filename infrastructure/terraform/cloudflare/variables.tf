variable "cloudflare_api_token" {
  type        = string
  sensitive   = true
  description = "Scoped Cloudflare API token. Supply through TF_VAR_cloudflare_api_token only."

  validation {
    condition     = length(trimspace(var.cloudflare_api_token)) >= 20
    error_message = "cloudflare_api_token must be a real scoped token."
  }
}

variable "cloudflare_account_id" {
  type        = string
  description = "Cloudflare account ID owning the existing tunnel."
  validation {
    condition     = can(regex("^[0-9a-f]{32}$", lower(var.cloudflare_account_id)))
    error_message = "cloudflare_account_id must be 32 hexadecimal characters."
  }
}

variable "cloudflare_zone_id" {
  type        = string
  description = "Cloudflare zone ID for zeaz.dev."
  validation {
    condition     = can(regex("^[0-9a-f]{32}$", lower(var.cloudflare_zone_id)))
    error_message = "cloudflare_zone_id must be 32 hexadecimal characters."
  }
}

variable "cloudflare_tunnel_id" {
  type        = string
  description = "Existing Cloudflare Tunnel ID, as a UUID or a 32-character hexadecimal value."
  validation {
    condition     = can(regex("^[0-9a-fA-F]{32}$", var.cloudflare_tunnel_id)) || can(regex("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", var.cloudflare_tunnel_id))
    error_message = "cloudflare_tunnel_id must be a UUID or 32 hexadecimal characters."
  }
}

variable "zone_name" {
  type        = string
  default     = "zeaz.dev"
  description = "The DNS zone containing the application hostname."
}

variable "moopiew_hostname" {
  type        = string
  default     = "moopiew.zeaz.dev"
  description = "Public hostname for the Moopiew preorder app."
  validation {
    condition     = endswith(lower(var.moopiew_hostname), ".${lower(var.zone_name)}")
    error_message = "moopiew_hostname must be a subdomain of zone_name."
  }
}

variable "moopiew_origin" {
  type        = string
  default     = "http://127.0.0.1:8080"
  description = "HTTP origin reached by cloudflared on the tunnel host."
  validation {
    condition     = can(regex("^https?://[^[:space:]]+$", var.moopiew_origin))
    error_message = "moopiew_origin must be an HTTP(S) URL."
  }
}

variable "piewdash_hostname" {
  type        = string
  default     = "piewdash.zeaz.dev"
  description = "Public hostname for the MooPiew engineering dashboard."
  validation {
    condition     = endswith(lower(var.piewdash_hostname), ".${lower(var.zone_name)}")
    error_message = "piewdash_hostname must be a subdomain of zone_name."
  }
}

variable "piewdash_origin" {
  type        = string
  default     = "http://127.0.0.1:8082"
  description = "Dashboard origin reached by cloudflared on the tunnel host."
  validation {
    condition     = can(regex("^https?://[^[:space:]]+$", var.piewdash_origin))
    error_message = "piewdash_origin must be an HTTP(S) URL."
  }
}

variable "manage_tunnel_config" {
  type        = bool
  default     = false
  description = "Only true after importing and reviewing the current remote tunnel ingress."
}
