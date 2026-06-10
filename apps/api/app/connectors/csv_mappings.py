"""CSV commerce mappings — fully CONFIG-DRIVEN (no parsing logic hardcoded in
the importer). Each file-kind mapping declares: required / optional columns,
type coercion, date parsing, currency handling, status mapping hook, and the
external_id rule. Add a platform = add a mapping dict, never importer code.
"""

# column spec: target_field -> {"col": csv column, "type": str|float|int|date, "required": bool}

GENERIC_MAPPING = {
    "mapping_id": "generic",
    "files": {
        "orders": {
            "external_id": {"col": "order_id", "required": True},
            "columns": {
                "order_number": {"col": "order_number", "type": "str"},
                "customer_external_id": {"col": "customer_id", "type": "str"},
                "customer_email": {"col": "email", "type": "str"},
                "raw_status": {"col": "status", "type": "str"},
                "total_amount": {"col": "total", "type": "float"},
                "currency": {"col": "currency", "type": "str"},
                "item_count": {"col": "items", "type": "int"},
                "country": {"col": "country", "type": "str"},
                "created_at_source": {"col": "created_at", "type": "date"},
            },
            "status_map": "order",
        },
        "order_items": {
            "external_id": {"col": "item_id", "required": True},
            "columns": {
                "order_external_id": {"col": "order_id", "type": "str", "required": True},
                "sku": {"col": "sku", "type": "str"},
                "title": {"col": "title", "type": "str"},
                "quantity": {"col": "quantity", "type": "int"},
                "unit_amount": {"col": "unit_price", "type": "float"},
                "currency": {"col": "currency", "type": "str"},
            },
        },
        "customers": {
            "external_id": {"col": "customer_id", "required": True},
            "columns": {
                "email": {"col": "email", "type": "str"},
                "name": {"col": "name", "type": "str"},
                "company": {"col": "company", "type": "str"},
                "country": {"col": "country", "type": "str"},
                "first_seen_at": {"col": "created_at", "type": "date"},
            },
        },
        "payments": {
            "external_id": {"col": "payment_id", "required": True},
            "columns": {
                "order_ref": {"col": "order_id", "type": "str", "required": True},
                "raw_status": {"col": "status", "type": "str"},
                "amount": {"col": "amount", "type": "float"},
                "currency": {"col": "currency", "type": "str"},
                "method": {"col": "method", "type": "str"},
                "created_at_source": {"col": "created_at", "type": "date"},
            },
            "status_map": "payment",
        },
    },
}

# Shopify CSV export column names (orders export + customers export).
SHOPIFY_MAPPING = {
    "mapping_id": "shopify",
    "files": {
        "orders": {
            "external_id": {"col": "Id", "required": True},
            "columns": {
                "order_number": {"col": "Name", "type": "str"},
                "customer_email": {"col": "Email", "type": "str"},
                "raw_status": {"col": "Financial Status", "type": "str"},
                "total_amount": {"col": "Total", "type": "float"},
                "currency": {"col": "Currency", "type": "str"},
                "country": {"col": "Shipping Country", "type": "str"},
                "created_at_source": {"col": "Created at", "type": "date"},
            },
            "status_map": "order",
        },
        "order_items": {
            "external_id": {"col": "Lineitem id", "required": True},
            "columns": {
                "order_external_id": {"col": "Id", "type": "str", "required": True},
                "sku": {"col": "Lineitem sku", "type": "str"},
                "title": {"col": "Lineitem name", "type": "str"},
                "quantity": {"col": "Lineitem quantity", "type": "int"},
                "unit_amount": {"col": "Lineitem price", "type": "float"},
                "currency": {"col": "Currency", "type": "str"},
            },
        },
        "customers": {
            "external_id": {"col": "Customer ID", "required": True},
            "columns": {
                "email": {"col": "Email", "type": "str"},
                "name": {"col": "Name", "type": "str"},
                "country": {"col": "Country", "type": "str"},
            },
        },
        "payments": {
            "external_id": {"col": "Transaction ID", "required": True},
            "columns": {
                "order_ref": {"col": "Order", "type": "str", "required": True},
                "raw_status": {"col": "Status", "type": "str"},
                "amount": {"col": "Amount", "type": "float"},
                "currency": {"col": "Currency", "type": "str"},
                "method": {"col": "Gateway", "type": "str"},
                "created_at_source": {"col": "Processed at", "type": "date"},
            },
            "status_map": "payment",
        },
    },
}

MAPPINGS = {"generic": GENERIC_MAPPING, "shopify": SHOPIFY_MAPPING}
