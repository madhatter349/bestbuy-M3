import requests
import json
import sqlite3
from datetime import datetime

# Database name
DB_NAME = 'price_tracker.db'

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        sku_id TEXT,
        condition_type TEXT,
        price REAL,
        timestamp TEXT
    )
    ''')

    conn.commit()
    conn.close()

def log_debug(message):
    with open('debug.log', 'a') as f:
        f.write(f"{datetime.now()}: {message}\n")

def fetch_price_data():
    try:
        cookies = {}

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://www.bestbuy.com',
            'referer': 'https://www.bestbuy.com/product/apple-macbook-air-13-inch-laptop-m3-chip-8gb-memory-256gb-ssd-midnight/6565837/openbox?condition=excellent',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
            'x-client-id': 'pdp-web',
        }

        json_data = [
            {
                'operationName': 'BuyingOptionsConditionTiles_Init',
                'variables': {
                    'skuId': '6565837',
                    'input': {
                        'salesChannel': 'LargeView',
                    },
                    'fulfillmentInput': {
                        'shipping': {
                            'destinationZipCode': '10001',
                        },
                        'inStorePickup': {
                            'storeId': '1531',
                        },
                        'buttonState': {
                            'fulfillmentOption': 'PICKUP',
                            'context': 'PDP',
                            'destinationZipCode': '10001',
                            'storeId': '1531',
                        },
                    },
                },
                'query': 'query BuyingOptionsConditionTiles_Init($skuId: String!, $input: ProductItemPriceInput!, $fulfillmentInput: ProductFulfillmentInput!) {\n  productBySkuId(skuId: $skuId) {\n    skuId\n    openBoxOptions {\n      code\n      type\n      product {\n        skuId\n        price(input: $input) {\n          customerPrice\n          skuId\n          openBoxCondition\n          __typename\n        }\n        url {\n          pdp\n          relativePdp\n          __typename\n        }\n        fulfillmentOptions(input: $fulfillmentInput) {\n          buttonStates {\n            buttonState\n            __typename\n          }\n          ispuDetails {\n            ispuAvailability {\n              pickupEligible\n              instoreInventoryAvailable\n              quantity\n              minPickupInHours\n              maxDate\n              __typename\n            }\n            __typename\n          }\n          shippingDetails {\n            shippingAvailability {\n              shippingEligible\n              customerLOSGroup {\n                customerLosGroupId\n                maxLineItemMaxDate\n                name\n                displayDateType\n                price\n                minLineItemMaxDate\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n        openBoxCondition\n      }\n      __typename\n    }\n    __typename\n    openBoxCondition\n  }\n}',
            },
        ]

        response = requests.post('https://www.bestbuy.com/gateway/graphql', cookies=cookies, headers=headers, json=json_data)
        return response.json()
    except Exception as e:
        log_debug(f"Error fetching price data: {str(e)}")
        raise

def main():
    log_debug("Starting price tracker")
    init_db()
    
    try:
        product_data = fetch_price_data()
        store_price_data(product_data)
        sku_id = product_data['data']['productBySkuId']['skuId']
        changes = check_price_changes(sku_id)
        
        if changes:
            save_price_changes(changes)
            send_email(changes)
    except Exception as e:
        log_debug(f"Script failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
