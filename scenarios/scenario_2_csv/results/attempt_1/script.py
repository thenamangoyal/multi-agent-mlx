import csv
import random
from datetime import datetime, timedelta

# Step 1: Generate the CSV file
def generate_csv():
    products = ["Widget", "Gadget", "Doohickey"]
    regions = ["North", "South", "East", "West"]
    data = []

    random.seed(42)
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)

    for _ in range(200):
        date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        product = random.choice(products)
        region = random.choice(regions)
        units = random.randint(1, 100)
        price_per_unit = round(random.uniform(5.00, 50.00), 2)
        revenue = units * price_per_unit
        data.append([date.strftime('%Y-%m-%d'), product, region, units, price_per_unit, revenue])

    with open('sales_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['date', 'product', 'region', 'units', 'price_per_unit', 'revenue'])
        writer.writerows(data)

# Step 2: Read the CSV and compute the required metrics
def analyze_data():
    with open('sales_data.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)

    revenue_by_product = {}
    total_revenue = 0
    region_revenue = {}
    month_revenue = {}

    for row in data:
        product = row['product']
        revenue = float(row['revenue'])
        region = row['region']
        month = datetime.strptime(row['date'], '%Y-%m-%d').strftime('%B')

        revenue_by_product[product] = revenue_by_product.get(product, 0) + revenue
        total_revenue += revenue
        region_revenue[region] = region_revenue.get(region, 0) + revenue
        month_revenue[month] = month_revenue.get(month, 0) + revenue

    top_product = max(revenue_by_product, key=revenue_by_product.get)
    top_region = max(region_revenue, key=region_revenue.get)
    top_month = max(month_revenue, key=month_revenue.get)

    return revenue_by_product, top_product, top_region, top_month, total_revenue

# Step 3: Print the formatted report
def print_report(revenue_by_product, top_product, top_region, top_month, total_revenue):
    print("=== Sales Analysis Report ===")
    print("Revenue by Product:")
    for product, revenue in sorted(revenue_by_product.items(), key=lambda x: x[1], reverse=True):
        print(f"  {product}: ${revenue:,.2f}")
    print(f"Top Region: {top_region} (${region_revenue[top_region]:,.2f})")
    print(f"Top Month: {top_month} (${month_revenue[top_month]:,.2f})")
    print(f"Total Records: {len(revenue_by_product)}")

# Main script
generate_csv()
revenue_by_product, top_product, top_region, top_month, total_revenue = analyze_data()
print_report(revenue_by_product, top_product, top_region, top_month, total_revenue)
