resource "cloudflare_record" "zaffiliate_cname" {
  zone_id = var.cloudflare_zone_id
  name    = "zaffiliate"
  value   = "77107d8b-8293-421d-8189-85f74a73b30b.cfargotunnel.com"
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
