from deepdict import *

orders = {
    "store": {
        "info": {
            "name": "超级商城",
            "location": "北京",
            "contacts": {
                "phone": "123-4567",
                "email": "shop@example.com",
                "managers": [
                    {"name": "张经理", "phone": "111-1111"},
                    {"name": "李经理", "phone": "222-2222"}
                ]
            }
        },
        "orders": {
            "2024-01": {
                "1001": {
                    "customer": {
                        "id": "c001",
                        "name": "张三",
                        "level": "gold",
                        "contact": {
                            "phone": "13800138000",
                            "address": {
                                "city": "北京",
                                "street": "长安街1号"
                            }
                        }
                    },
                    "items": [
                        {
                            "product_id": "p001",
                            "name": "手机",
                            "price": 2999,
                            "quantity": 2,
                            "specs": {
                                "color": "黑色",
                                "storage": "256G"
                            }
                        },
                        {
                            "product_id": "p002",
                            "name": "充电器",
                            "price": 99,
                            "quantity": 1,
                            "specs": {
                                "type": "快充",
                                "power": "20W"
                            }
                        }
                    ],
                    "payment": {
                        "method": "微信支付",
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
                            "company": "顺丰",
                            "number": "SF123456789"
                        },
                        "address": {
                            "city": "北京",
                            "street": "长安街1号",
                            "receiver": "张三"
                        }
                    }
                },
                "1002": {
                    "customer": {
                        "id": "c002",
                        "name": "李四",
                        "level": "silver",
                        "contact": {
                            "phone": "13900139000",
                            "address": {
                                "city": "上海",
                                "street": "南京路100号"
                            }
                        }
                    },
                    "items": [
                        {
                            "product_id": "p003",
                            "name": "笔记本",
                            "price": 5999,
                            "quantity": 1,
                            "specs": {
                                "cpu": "i7",
                                "ram": "16G"
                            }
                        }
                    ],
                    "payment": {
                        "method": "支付宝",
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
                        "name": "张三",
                        "level": "gold",
                        "contact": {
                            "phone": "13800138000",
                            "address": {
                                "city": "北京",
                                "street": "长安街1号"
                            }
                        }
                    },
                    "items": [
                        {
                            "product_id": "p004",
                            "name": "平板",
                            "price": 3999,
                            "quantity": 1,
                            "specs": {
                                "size": "11寸",
                                "color": "银色"
                            }
                        }
                    ],
                    "payment": {
                        "method": "微信支付",
                        "status": "paid",
                        "amount": 3999
                    },
                    "delivery": {
                        "status": "delivered",
                        "tracking": {
                            "company": "京东",
                            "number": "JD987654321"
                        },
                        "address": {
                            "city": "北京",
                            "street": "长安街1号",
                            "receiver": "张三"
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

# 1. 提取所有已支付订单的金额
pays = [
    dget(od, "payment.amount")
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
    if dget(od, "payment.status") == "paid"
]
print(pays)

# 2. 找出所有金卡用户的订单号
odnumbers = [
    odnum
    for date, ords in dget(orders, "store.orders").items()
    for odnum, od in ords.items()
    if dget(od, "customer.level") == "gold"
]
print(odnumbers)

from collections import Counter
# 3. 统计每个城市的订单数量
citys = dict(Counter(
    dget(od, "customer.contact.address.city")
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
))
print(citys)

# 4. 提取所有包含 "手机" 的订单
odnumbers = list({
    odnum
    for date, ords in dget(orders, "store.orders").items()
    for odnum, od in ords.items()
    for obj in dget(od, "items")
    if obj.get("name") == "手机"
})
print(odnumbers)

# 5. 把所有 "pending" 状态的订单改成 "cancelled"
all(
    dset(od, "payment.status", "cancelled")
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
    if dget(od, "payment.status") == "pending"
)
print(dget(orders, "store.orders.2024-01.1002.payment.status"))

# 6. 计算每个用户的消费总额
tmp = [
    (dget(od, "customer.id"), dget(od, "payment.amount"))
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
    if dget(od, "payment.status") == "paid"
]
pays = {}
for uid, paid in tmp:
    pays[uid] = pays.get(uid, 0) + paid
print(pays)

# 7. 找出所有使用 "微信支付" 的订单
odnumbers = [
    odnum
    for date, ords in dget(orders, "store.orders").items()
    for odnum, od in ords.items()
    if dget(od, "payment.method") == "微信支付"
]
print(odnumbers)

# 8. 给每个订单添加一个 "total_items" 字段（商品总数）
all(
    dset(od, "total_items", sum([dget(i, "quantity") for i in dget(od, "items")]))
    for date, ords in dget(orders, "store.orders").items()
    for odnum, od in ords.items()
)
print(dget(orders, "store.orders.2024-01.1001.total_items"), end="  ")  # 3
print(dget(orders, "store.orders.2024-01.1002.total_items"), end="  ")  # 1
print(dget(orders, "store.orders.2024-02.1003.total_items"))  # 1

# 9. 提取所有已发货订单的物流信息
infos = [
    {
        "order_id": odnum,
        "company": dget(od, "delivery.tracking.company"),
        "number": dget(od, "delivery.tracking.number")
    }
    for date, ords in dget(orders, "store.orders").items()
    for odnum, od in ords.items()
    if dget(od, "delivery.status") != "pending"
]
print(infos)

# 10. 统计每个商品被购买的次数
items = dict(Counter([
    item
    for date, ords in dget(orders, "store.orders").items()
    for od in ords.values()
    for i in dget(od, "items")
    for item in [dget(i, "name")] * dget(i, "quantity")
]))
print(items)