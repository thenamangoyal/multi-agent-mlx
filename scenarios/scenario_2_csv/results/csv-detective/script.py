import csv
import random
import datetime

# Step 1: Generate the CSV file
random.seed(42)

with open('sales_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['date', 'product', 'region', 'units', 'price_per_unit'])
    
    products = ['Widget', 'Gadget', 'Doohickey']
    regions = ['North', 'South', 'East', 'West']
    
    for _ in range(200):
        date = random.choice(list(datetime.date(2025, 1, 1) + datetime.timedelta(days=x) for x in range(365)))
        product = random.choice(products)
        region = random.choice(regions)
        units = random.randint(1, 100)
        price_per_unit = round(random.uniform(5.00, 50.00), 2)
        
        writer.writerow([date, product, region, units, price_per_unit])

# Step 2: Read the CSV file and compute the required metrics
revenue_by_product = {}
total_revenue = 0
month_revenue = {}

with open('sales_data.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        product = row['product']
        units = int(row['units'])
        price_per_unit = float(row['price_per_unit'])
        revenue = units * price_per_unit
        
        revenue_by_product[product] = revenue_by_product.get(product, 0) + revenue
        total_revenue += revenue
        
        month = datetime.datetime.strptime(row['date'], '%Y-%m-%d').strftime('%B')
        month_revenue[month] = month_revenue.get(month, 0) + revenue

top_product = max(revenue_by_product, key=revenue_by_product.get)
top_region = max(month_revenue, key=month_revenue.get)
top_month = max(month_revenue, key=month_revenue.get)

# Step 3: Print the formatted report
print("=== Sales Analysis Report ===")
print("Revenue by Product:")
for product, revenue in sorted(revenue_by_product.items(), key=lambda x: x[1], reverse=True):
    print(f"  {product}: ${revenue:,.2f}")
print(f"Top Region: {top_region} (${month_revenue[top_region]:,.2f})")
print