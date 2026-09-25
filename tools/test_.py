from deepdict import *
from collections import Counter

orders = {
    "store": {
        "info": {
            "name": "Super Mall",
            "location": "New York",
            "contacts": {
                "phone": "212-555-1234",
                "email": "shop@example.com",
                "managers": [
                    {"name": "Mike Zhang", "phone": "212-555-1111"},
                    {"name": "Lisa Li", "phone": "212-555-2222"}
                ]
            }
        },
        "orders": {
            "2024-01": {
                "1001": {
                    "customer": {
                        "id": "c001",
                        "name": "John Zhang",
                        "level": "gold",
                        "contact": {
                            "phone": "212-555-8888",
                            "address": {
                                "city": "New York",
                                "street": "1 Wall Street"
                            }
                        }
                    },
                    "items": [
                        {
                            "product_id": "p001",
                            "name": "Phone",
                            "price": 2999,
                            "quantity": 2,
                            "specs": {
                                "color": "Black",
                                "storage": "256G"
                            }
                        },
                        {
                            "product_id": "p002",
                            "name": "Charger",
                            "price": 99,
                            "quantity": 1,
                            "specs": {
                                "type": "Fast Charge",
                                "power": "20W"
                            }
                        }
                    ],
                    "payment": {
                        "method": "WeChat Pay",
                        "status": "paid",
                        "amount": 6097,
                        "details": {
                            "card_last4": "1234",
                            "transaction_id": "wx_20240101_001"
                        }
                    },
                    "delivery": {
                        "status": "shipped",
                        "tracking": {
                            "company": "FedEx",
                            "number": "FDX123456789"
                        },
                        "address": {
                            "city": "New York",
                            "street": "1 Wall Street",
                            "receiver": "John Zhang"
                        }
                    }
                },
                "1002": {
                    "customer": {
                        "id": "c002",
                        "name": "Jane Li",
                        "level": "silver",
                        "contact": {
                            "phone": "415-555-9999",
                            "address": {
                                "city": "San Francisco",
                                "street": "100 Market Street"
                            }
                        }
                    },
                    "items": [
                        {
                            "product_id": "p003",
                            "name": "Laptop",
                            "price": 5999,
                            "quantity": 1,
                            "specs": {
                                "cpu": "i7",
                                "ram": "16G"
                            }
                        }
                    ],
                    "payment": {
                        "method": "Alipay",
                        "status": "pending",
                        "amount": 5999
                    },
                    "delivery": {
                        "status": "pending"
                    }
                }
            },
            "2024-02": {
                "1003": {
                    "customer": {
                        "id": "c001",
                        "name": "John Zhang",
                        "level": "gold",
                        "contact": {
                            "phone": "212-555-8888",
                            "address": {
                                "city": "New York",
                                "street": "1 Wall Street"
                            }
                        }
                    },
                    "items": [
                        {
                            "product_id": "p004",
                            "name": "Tablet",
                            "price": 3999,
                            "quantity": 1,
                            "specs": {
                                "size": "11 inch",
                                "color": "Silver"
                            }
                        }
                    ],
                    "payment": {
                        "method": "WeChat Pay",
                        "status": "paid",
                        "amount": 3999
                    },
                    "delivery": {
                        "status": "delivered",
                        "tracking": {
                            "company": "UPS",
                            "number": "UPS987654321"
                        },
                        "address": {
                            "city": "New York",
                            "street": "1 Wall Street",
                            "receiver": "John Zhang"
                        }
                    }
                }
            }
        }
    },
    "statistics": {
        "total_orders": 3,
        "total_revenue": 16095,
        "by_level": {
            "gold": 2,
            "silver": 1
        },
        "by_status": {
            "paid": 2,
            "pending": 1,
            "shipped": 1,
            "delivered": 1
        }
    }
}

# 1. Extract amounts of all paid orders
paid_amounts = [
    dget(od, "payment.amount")
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
    if dget(od, "payment.status") == "paid"
]
print(paid_amounts)

# 2. Find all order numbers of gold-level customers
gold_order_numbers = [
    order_num
    for date, ords in dget(orders, "store.orders").items()
    for order_num, od in ords.items()
    if dget(od, "customer.level") == "gold"
]
print(gold_order_numbers)

# 3. Count number of orders per city
city_counts = dict(Counter(
    dget(od, "customer.contact.address.city")
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
))
print(city_counts)

# 4. Extract all order numbers that contain a "Phone"
phone_orders = list({
    order_num
    for date, ords in dget(orders, "store.orders").items()
    for order_num, od in ords.items()
    for obj in dget(od, "items")
    if obj.get("name") == "Phone"
})
print(phone_orders)

# 5. Change all "pending" orders to "cancelled"
all(
    dset(od, "payment.status", "cancelled")
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
    if dget(od, "payment.status") == "pending"
)
print(dget(orders, "store.orders.2024-01.1002.payment.status"))

# 6. Calculate total spending per customer
temp = [
    (dget(od, "customer.id"), dget(od, "payment.amount"))
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
    if dget(od, "payment.status") == "paid"
]
spending = {}
for uid, amount in temp:
    spending[uid] = spending.get(uid, 0) + amount
print(spending)

# 7. Find all orders using "WeChat Pay"
wechat_orders = [
    order_num
    for date, ords in dget(orders, "store.orders").items()
    for order_num, od in ords.items()
    if dget(od, "payment.method") == "WeChat Pay"
]
print(wechat_orders)

# 8. Add a "total_items" field to each order (total quantity of items)
all(
    dset(od, "total_items", sum([dget(i, "quantity") for i in dget(od, "items")]))
    for date, ords in dget(orders, "store.orders").items()
    for order_num, od in ords.items()
)
print(dget(orders, "store.orders.2024-01.1001.total_items"), end="  ")  # 3
print(dget(orders, "store.orders.2024-01.1002.total_items"), end="  ")  # 1
print(dget(orders, "store.orders.2024-02.1003.total_items"))  # 1

# 9. Extract shipping info for all orders that are not pending
shipping_info = [
    {
        "order_id": order_num,
        "company": dget(od, "delivery.tracking.company"),
        "number": dget(od, "delivery.tracking.number")
    }
    for date, ords in dget(orders, "store.orders").items()
    for order_num, od in ords.items()
    if dget(od, "delivery.status") != "pending"
]
print(shipping_info)

# 10. Count how many times each product was purchased
product_counts = dict(Counter([
    item
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
    for i in dget(od, "items")
    for item in [dget(i, "name")] * dget(i, "quantity")
]))
print(product_counts)