import csv
import random
import datetime

def generate_sales_data():
    products = ["Widget", "Gadget", "Doohickey"]
    regions = ["North", "South", "East", "West"]
    dates = [datetime.date(2025, 1, 1) + datetime.timedelta(days=x) for x in range(365)]
    data = []

    random.seed(42)
    for _ in range(200):
        date = random.choice(dates)
        product = random.choice(products)
        region = random.choice(regions)
        units = random.randint(1, 100)
        price_per_unit = round(random.uniform(5.00, 50.00), 2)
        revenue = units * price_per_unit
        data.append([date, product, region, units, price_per_unit, revenue])

    with open('sales_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['date', 'product', 'region', 'units', 'price_per_unit', 'revenue'])
        writer.writerows(data)

def analyze_data():
    revenue_by_product = {}
    region_revenue = {}
    month_revenue = {}

    with open('sales_data.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            product = row['product']
            region = row['region']
            units = int(row['units'])
            price_per_unit = float(row['price_per_unit'])
            revenue = units * price_per_unit

            revenue_by_product[product] = revenue_by_product.get(product, 0) + revenue
            region_revenue[region] = region_revenue.get(region, 0) + revenue

            month = datetime.datetime.strptime(row['date'], '%Y-%m-%d').strftime('%B')
            month_revenue[month] = month_revenue.get(month, 0) + revenue

    top_product = max(revenue_by_product, key=revenue_by_product.get)
    top_region = max(region_revenue, key=region_revenue.get)
    top_month = max(month_revenue, key=month_revenue.get)
    total_revenue = sum(revenue_by_product.values())

    return revenue_by_product, top_product, top_region, top_month, total_revenue, region_revenue

def print_report(revenue_by_product, top_product, top_region, top_month, total_revenue, region_revenue):
    print("=== Sales Analysis Report ===")
    print("Revenue by Product:")
    for product, revenue in sorted(revenue_by_product.items(), key=lambda x: x[1], reverse=True):
        print(f"  {product}: ${revenue:,.2f}")
    print(f"Top Region: {top_region} (${region_revenue[top_region]:,.2f})")
    print(f"Top Month: {top_month} (${month_revenue[top_month]:,.2f})")
    print(f"Total Records: {len(revenue_by_product)}")

# Step 1: Generate sales data
generate_sales_data()

# Step 2: Analyze data
revenue_by_product, top_product, top_region, top_month, total_revenue, region_revenue = analyze_data()

# Step 3: Print report
print_report(revenue_by_product, top_product, top_region, top_month, total_revenue, region_revenue)

# Write the script to a file
write_file({
    "path": "script.py",
    "content": """import csv
import random
import datetime

def generate_sales_data():
    products = ["Widget", "Gadget", "Doohickey"]
    regions = ["North", "South", "East", "West"]
    dates = [datetime.date(2025, 1, 1) + datetime.timedelta(days=x) for x in range(365)]
    data = []

    random.seed(42)
    for _ in range(200):
        date = random.choice(dates)
        product = random.choice(products)
        region = random.choice(regions)
        units = random.randint(1, 100)
        price_per_unit = round(random.uniform(5.00, 50.00), 2)
        revenue = units * price_per_unit
        data.append([date, product, region, units, price_per_unit, revenue])

    with open('sales_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['date', 'product', 'region', 'units', 'price_per_unit', 'revenue'])
        writer.writerows(data)

def analyze_data():
    revenue_by_product = {}
    region_revenue = {}
    month_revenue = {}

    with open('sales_data.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            product = row['product']
            region = row['region']
            units = int(row['units'])
            price_per_unit = float(row['price_per_unit'])
            revenue = units * price_per_unit

            revenue_by_product[product] = revenue_by_product.get(product, 0) + revenue
            region_revenue[region] = region_revenue.get(region, 0) + revenue

            month = datetime.datetime.strptime(row['date'], '%Y-%m-%d').strftime('%B')
            month_revenue[month] = month_revenue.get(month, 0) + revenue

    top_product = max(revenue_by_product, key=revenue_by_product.get)
    top_region = max(region_revenue, key=region_revenue.get)
    top_month = max(month_revenue, key=month_revenue.get)
    total_revenue = sum(revenue_by_product.values())

    return revenue_by_product, top_product, top_region, top_month, total_revenue, region_revenue

def print_report(revenue_by_product, top_product, top_region, top_month, total_revenue, region_revenue):
    print("=== Sales Analysis Report ===")
    print("Revenue by Product:")
    for product, revenue in sorted(revenue_by_product.items(), key=lambda x: x[1], reverse=True):
        print(f"  {product}: ${revenue:,.2f}")
    print(f"Top Region: {top_region} (${region_revenue[top_region]:,.2f})")
    print(f"Top Month: {top_month} (${month_revenue[top_month]:,.2f})")
    print(f"Total Records: {len(revenue_by_product)}")

# Step 1: Generate sales data
generate_sales_data()

# Step 2: Analyze data
revenue_by_product, top_product, top_region, top_month, total_revenue, region_revenue = analyze_data()

# Step 3: Print report
print_report(revenue_by_product, top_product, top_region, top_month, total_revenue, region_revenue)
"""
})
