import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch
from nra_integration.integration.item_integration import sync_item_to_digitax

class TestItemIntegration(FrappeTestCase):
    def setUp(self):
        # Create NRA Settings if not exists
        if not frappe.db.exists("NRA Settings"):
            doc = frappe.new_doc("NRA Settings")
            doc.enable_digitax_integration = 1
            doc.api_key = "test_key"
            doc.insert()
        else:
            doc = frappe.get_doc("NRA Settings")
            doc.enable_digitax_integration = 1
            doc.api_key = "test_key"
            doc.save()

    @patch('requests.post')
    def test_sync_item_to_digitax_success(self, mock_post):
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "DTX-001"}

        item = frappe.new_doc("Item")
        item.item_code = "TEST-ITEM-001"
        item.item_name = "Test Item"
        item.item_group = "Consumable"
        item.is_service = "No"
        item.hsn_code = "1234.56"
        item.insert()

        # Trigger sync manually
        sync_item_to_digitax(item)

        self.assertEqual(frappe.db.get_value("Item", item.name, "digitax_item_id"), "DTX-001")
        
        # Verify payload
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        self.assertEqual(payload['item_code'], "TEST-ITEM-001")
        self.assertEqual(payload['price_unit'], "NGN per 1")
        self.assertEqual(payload['product_category'], "Consumable")
        self.assertEqual(payload['is_service'], False)

    @patch('requests.post')
    def test_sync_item_to_digitax_service(self, mock_post):
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "DTX-002"}

        item = frappe.new_doc("Item")
        item.item_code = "TEST-SRV-001"
        item.item_name = "Test Service"
        item.item_group = "Service"
        item.is_service = "Yes"
        item.insert()

        sync_item_to_digitax(item)

        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        self.assertEqual(payload['is_service'], True)
