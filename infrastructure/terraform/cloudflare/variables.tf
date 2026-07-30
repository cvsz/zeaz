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
  description = "Loopback Caddy origin reached by cloudflared for the public application."
  validation {
    condition     = var.moopiew_origin == "http://127.0.0.1:8080"
    error_message = "moopiew_origin must use the reviewed loopback Caddy proxy at http://127.0.0.1:8080."
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
  default     = "http://127.0.0.1:80"
  description = "Loopback Caddy origin reached by cloudflared for the protected dashboard."
  validation {
    condition     = var.piewdash_origin == "http://127.0.0.1:80"
    error_message = "piewdash_origin must use the reviewed Caddy authentication proxy at http://127.0.0.1:80."
  }
}

variable "piewdash_access_allowed_emails" {
  type        = set(string)
  description = "Exact operator emails allowed through Cloudflare Access."

  validation {
    condition = length(var.piewdash_access_allowed_emails) > 0 && alltrue([
      for email in var.piewdash_access_allowed_emails :
      can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", lower(email)))
    ])
    error_message = "piewdash_access_allowed_emails must contain at least one valid operator email."
  }
}

variable "zerp_hostname" {
  type        = string
  default     = "zerp.zeaz.dev"
  description = "Public hostname for the zERP web application."
  validation {
    condition     = endswith(lower(var.zerp_hostname), ".${lower(var.zone_name)}")
    error_message = "zerp_hostname must be a subdomain of zone_name."
  }
}

variable "zerp_origin" {
  type        = string
  default     = "http://127.0.0.1:80"
  description = "Loopback Caddy origin reached by cloudflared for zERP."
  validation {
    condition     = var.zerp_origin == "http://127.0.0.1:80"
    error_message = "zerp_origin must use the reviewed loopback Caddy proxy at http://127.0.0.1:80."
  }
}

variable "manage_tunnel_config" {
  type        = bool
  default     = false
  description = "Only true after importing and reviewing the current remote tunnel ingress."
}

variable "cmeerp_hostname" {
  type        = string
  default     = "cme.zeaz.dev"
  description = "Public hostname for the CME Pro ERP web application."
  validation {
    condition     = endswith(lower(var.cmeerp_hostname), ".${lower(var.zone_name)}")
    error_message = "cmeerp_hostname must be a subdomain of zone_name."
  }
}

variable "cmeerp_origin" {
  type        = string
  default     = "http://127.0.0.1:8001"
  description = "Loopback origin reached by cloudflared for CME Pro ERP."
  validation {
    condition     = can(regex("^http://127\\.0\\.0\\.1:[0-9]+$", var.cmeerp_origin))
    error_message = "cmeerp_origin must use a loopback address."
  }
}

