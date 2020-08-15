import datetime as dt


def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    year = dt.datetime.now().year
    return {"year": year}