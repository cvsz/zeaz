resource "cloudflare_record" "zaffiliate_cname" {
  zone_id = var.cloudflare_zone_id
  name    = "zaffiliate"
  value   = "45667e7e73834265b53e6a9e770a8554.cfargotunnel.com"
  type    = "CNAME"
  proxied = var.zaffiliate_proxied
  ttl     = var.zaffiliate_proxied ? 1 : 300

  comment = "Affiliate Automation OS via Cloudflare Tunnel - managed by Terraform"
}

output "zaffiliate_hostname" {
  value = "${cloudflare_record.zaffiliate_cname.name}.zeaz.dev"
}

output "zaffiliate_proxied" {
  value = cloudflare_record.zaffiliate_cname.proxied
}
