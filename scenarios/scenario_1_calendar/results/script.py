import datetime

# Function to determine the day of the week for a given date
def get_day_of_week(year, month, day):
    return datetime.datetime(year, month, day).weekday()

# Function to generate the calendar for a given month and year
def generate_calendar(year, month):
    # Get the number of days in the month
    if month == 2:
        is_leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        num_days = 29 if is_leap_year else 28
    elif month in [4, 6, 9, 11]:
        num_days = 30
    else:
        num_days = 31
    
    # Get the day of the week for the first day of the month
    first_day = get_day_of_week(year, month, 1)
    
    # Print the title line
    print(f"      {month} {year}")
    
    # Print the column headers
    print(" Mon Tue Wed Thu Fri Sat Sun")
    
    # Print the days of the month in a grid
    for i in range(first_day):
        print("    ", end="")
    for day in range(1, num_days + 1):
        print(f"{day:4d}", end="")
        if (first_day + day - 1) % 7 == 6:
            print()
    print()
    
    # Count the number of weekdays and weekend days
    weekdays = 0
    weekend_days = 0
    for day in range(1, num_days + 1):
        if (first_day + day - 1) % 7 < 5:
            weekdays += 1
        else:
            weekend_days += 1
    
    # Print the final line
    print(f"Weekdays: {weekdays}, Weekend days: {weekend_days}")

# Generate the calendar for March 2026
generate_calendar(2026, 3)
