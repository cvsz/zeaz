variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

variable "cloudflare_zone_id" {
  type = string
}

variable "cloudflare_account_id" {
  type = string
}

variable "zaffiliate_origin_ip" {
  type    = string
  default = "171.6.6.191"
}

variable "zaffiliate_proxied" {
  type    = bool
  default = true
}
