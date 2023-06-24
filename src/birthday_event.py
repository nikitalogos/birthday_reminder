from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta


@dataclass
class BirthdayEvent:
    date: datetime
    title: str

    @property
    def age(self):
        now = datetime.now()
        was_birthday_this_year = (now.month, now.day) >= (self.date.month, self.date.day)
        return now.year - self.date.year - (not was_birthday_this_year)

    @property
    def next_birthday(self):
        next_birthday = self.date + relativedelta(years=self.age + 1)
        return next_birthday

    @property
    def days_until(self):
        return (self.next_birthday - datetime.now()).days

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} - {self.title} - {self.age} years old " \
               f"(Will be {self.age + 1} in {self.days_until} days)"
