from datetime import datetime, timedelta
from .models import Holiday

def add_holiday(name, start_date, end_date=None):
    """
    Add a holiday to the database
    start_date and end_date should be in YYYY-MM-DD format
    """
    if end_date is None:
        end_date = start_date
    
    Holiday.objects.create(
        name=name,
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
        end_date=datetime.strptime(end_date, '%Y-%m-%d').date()
    )

def load_semester_holidays(semester, year):
    """
    Load holidays for a specific semester
    """
    if semester == 'Spring':
        holidays = [
            ("Shab-e-Meraj", f"{year}-01-28"),
            ("Saraswati Puja", f"{year}-02-03"),
            ("Shab-e-Barat", f"{year}-02-15"),
            ("International Mother Language Day", f"{year}-02-21"),
            ("National Independence Day", f"{year}-03-26"),
            ("Laylat al-Qadr", f"{year}-03-28"),
            ("Mid-term Break", f"{year}-03-16", f"{year}-03-22"),
            ("Eid-ul-Fitr", f"{year}-03-26", f"{year}-04-02"),
            ("Bengali New Year", f"{year}-04-14"),
            ("International Workers' Day", f"{year}-05-01"),
            ("Buddha Purnima", f"{year}-05-11"),
            ("Eid-ul-Adha", f"{year}-06-04", f"{year}-06-10"),
            ("Ashura", f"{year}-07-06")
        ]
    elif semester == 'Fall':
        holidays = [
            ("Eid-ul-Adha", f"{year}-06-04", f"{year}-06-10"),
            ("Ashura", f"{year}-07-06"),
            ("Durga Puja", f"{year}-10-15", f"{year}-10-19"),
            ("Eid-e-Miladunnabi", f"{year}-09-28"),
            ("Victory Day", f"{year}-12-16"),
            ("Christmas Day", f"{year}-12-25"),
            ("Mid-term Break", f"{year}-11-15", f"{year}-11-21")
        ]
    else:  # Summer
        holidays = [
            ("Eid-ul-Fitr", f"{year}-03-26", f"{year}-04-02"),
            ("Bengali New Year", f"{year}-04-14"),
            ("International Workers' Day", f"{year}-05-01"),
            ("Buddha Purnima", f"{year}-05-11")
        ]
    
    # Clear existing holidays for this semester
    start_date = datetime.strptime(f"{year}-01-01", '%Y-%m-%d').date()
    end_date = datetime.strptime(f"{year}-12-31", '%Y-%m-%d').date()
    Holiday.objects.filter(start_date__gte=start_date, end_date__lte=end_date).delete()
    
    # Add new holidays
    for holiday in holidays:
        if len(holiday) == 2:
            add_holiday(holiday[0], holiday[1])
        else:
            add_holiday(holiday[0], holiday[1], holiday[2])

def is_holiday(date):
    """
    Check if a given date is a holiday
    """
    return Holiday.objects.filter(
        start_date__lte=date,
        end_date__gte=date
    ).exists()

def get_holiday_name(date):
    """
    Get the name of the holiday for a given date
    """
    holiday = Holiday.objects.filter(
        start_date__lte=date,
        end_date__gte=date
    ).first()
    return holiday.name if holiday else None 