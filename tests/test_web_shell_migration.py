import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class WebShellMigrationTests(unittest.TestCase):
    def test_migrated_public_entries_route_to_react_artifacts(self):
        entries = {
            "admin": "/src/admin.tsx",
            "api-monitor": "/src/portal.tsx",
            "dashboard": "/src/portal.tsx",
            "document-admin": "/src/documents.tsx",
            "documents": "/src/documents.tsx",
            "menu-preview": "/src/portal.tsx",
            "merchant-register": "/src/portal.tsx",
            "ops": "/src/operations.tsx",
            "rider-register": "/src/portal.tsx",
        }
        for page, entry in entries.items():
            legacy = (ROOT / "web" / f"{page}.html").read_text(encoding="utf-8")
            source = ROOT / "apps" / "web" / f"{page}.html"
            self.assertTrue(source.is_file(), source)
            self.assertIn(f"/platform/{page}.html", legacy)
            self.assertIn(f'src="{entry}"', source.read_text(encoding="utf-8"))

    def test_migrated_views_use_sdk_without_direct_fetch(self):
        component = (
            ROOT / "apps" / "web" / "src" / "portal.tsx"
        ).read_text(encoding="utf-8")
        service = (
            ROOT / "packages" / "sdk" / "src" / "applications.ts"
        ).read_text(encoding="utf-8")
        self.assertNotIn("fetch(", component)
        self.assertIn("api.applications.registerRider", component)
        self.assertIn("api.applications.registerMerchant", component)
        self.assertIn("api.menus.get", component)
        self.assertIn("api.monitoring.probe", component)
        self.assertIn('"/api/riders/register"', service)
        self.assertIn('"/api/merchants/register"', service)

    def test_removed_legacy_assets_are_absent(self):
        for asset in (
            "api-monitor.css",
            "api-monitor.js",
            "admin.js",
            "document-admin.js",
            "components/document-upload/document-page.js",
            "components/document-upload/document-upload.css",
            "components/document-upload/document-upload.js",
            "menu-preview.css",
            "menu-preview.js",
            "merchant-register.js",
            "ops.js",
            "rider-register.js",
            "style.css",
        ):
            self.assertFalse((ROOT / "web" / asset).exists())

    def test_storefront_uses_typed_sdk_and_preserves_customer_flow(self):
        component = (
            ROOT / "apps" / "web" / "src" / "main.tsx"
        ).read_text(encoding="utf-8")
        redirect = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("/platform/index.html", redirect)
        self.assertFalse((ROOT / "web" / "app.js").exists())
        self.assertNotIn("fetch(", component)
        for call in (
            "api.menus.get",
            "api.delivery.quote",
            "api.orders.create(",
            "api.orders.createScbQr",
            "api.orders.lookup",
            "api.orders.cancel",
            "api.delivery.subscribe",
        ):
            self.assertIn(call, component)

    def test_owner_dashboard_uses_sdk_without_persisting_credentials(self):
        component = (
            ROOT / "apps" / "web" / "src" / "admin.tsx"
        ).read_text(encoding="utf-8")
        service = (
            ROOT / "packages" / "sdk" / "src" / "admin.ts"
        ).read_text(encoding="utf-8")
        self.assertNotIn("fetch(", component)
        self.assertNotIn("localStorage", component)
        self.assertNotIn("sessionStorage", component)
        for call in (
            "api.admin.dashboard",
            "api.admin.updateSettings",
            "api.admin.createMenu",
            "api.admin.updateMenu",
            "api.admin.updateOrder",
            "api.admin.inquirePayment",
            "api.admin.startScbAuthorization",
            "api.admin.scbAuthorizationStatus",
        ):
            self.assertIn(call, component)
        self.assertIn("ownerHeaders(adminKey)", service)

    def test_operations_surface_uses_complete_typed_sdk_boundary(self):
        component = (
            ROOT / "apps" / "web" / "src" / "operations.tsx"
        ).read_text(encoding="utf-8")
        service = (
            ROOT / "packages" / "sdk" / "src" / "operations.ts"
        ).read_text(encoding="utf-8")
        self.assertNotIn("fetch(", component)
        self.assertNotIn("localStorage", component)
        self.assertNotIn("sessionStorage", component)
        for method in (
            "dashboard",
            "updateBusinessProfile",
            "updateDeliveryPricing",
            "createZone",
            "createRider",
            "updateRider",
            "reviewRiderApplication",
            "reviewMerchantApplication",
            "updateDelivery",
            "createInventory",
            "adjustInventory",
            "setRecipe",
            "createCoupon",
            "issueReceipt",
            "issueTaxInvoice",
            "printReceipt",
        ):
            self.assertIn(f"{method}(", service)
            self.assertIn(f"api.operations.{method}", component)


if __name__ == "__main__":
    unittest.main()
