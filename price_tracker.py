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

    # Create table if it doesn't exist
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

# Fetch price data from Best Buy API
def fetch_price_data():
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

# Store price data in the database
def store_price_data(product_data):
    sku_id = product_data['data']['productBySkuId']['skuId']
    timestamp = datetime.now().isoformat()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for option in product_data['data']['productBySkuId']['openBoxOptions']:
        condition_type = option['type']
        price = option['product']['price']['customerPrice']
        pdp_url = option['product']['url']['pdp']
        
        print(f"Condition: {condition_type}")
        print(f"Price: ${price}")
        print(f"Product Link: {pdp_url}\n")
        
        # Store in the database
        cursor.execute('''
        INSERT INTO prices (sku_id, condition_type, price, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (sku_id, condition_type, price, timestamp))

    conn.commit()
    conn.close()

# Check for price changes
def check_price_changes(sku_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT condition_type, price, timestamp
    FROM prices
    WHERE sku_id = ?
    ORDER BY timestamp DESC
    ''', (sku_id,))

    prices = cursor.fetchall()

    # Compare the most recent price with the previous one
    if len(prices) >= 2:
        latest_price = prices[0][1]
        previous_price = prices[1][1]
        
        if latest_price != previous_price:
            print(f"Price for {prices[0][0]} condition has changed from ${previous_price} to ${latest_price}")
    else:
        print("Not enough data to compare prices.")

    conn.close()

def main():
    init_db()
    product_data = fetch_price_data()
    store_price_data(product_data)
    sku_id = product_data['data']['productBySkuId']['skuId']
    check_price_changes(sku_id)

if __name__ == "__main__":
    main()
