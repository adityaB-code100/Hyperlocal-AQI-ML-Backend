from add_raw_data_server import index
from processing_data import index2
from datetime import datetime


def get_current_date():
    return datetime.now().strftime("%d-%m-%Y")


date=get_current_date()
index(date)
index2(date)