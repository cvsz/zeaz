resource "cloudflare_record" "zaffiliate_a" {
  zone_id = var.cloudflare_zone_id
  name    = "zaffiliate"
  value   = var.zaffiliate_origin_ip
  type    = "A"
  proxied = var.zaffiliate_proxied
  ttl     = var.zaffiliate_proxied ? 1 : 300

  comment = "Affiliate Automation OS - managed by Terraform"
}

output "zaffiliate_hostname" {
  value = "${cloudflare_record.zaffiliate_a.name}.zeaz.dev"
}

output "zaffiliate_proxied" {
  value = cloudflare_record.zaffiliate_a.proxied
}
