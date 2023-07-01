from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta

from birthday_reminder.birthday_event import BirthdayEvent, compare_events_file_and_google
from birthday_reminder.configs.main_config import MainConfig


class TestBirthdayEvent:
    def test_default_year_on_no_year_date(self):
        not_default_year = BirthdayEvent._DEFAULT_YEAR + 1
        event = BirthdayEvent(date=datetime(not_default_year, 1, 1), title="Ivan", has_year=False, config=MainConfig())
        assert event.date.year == BirthdayEvent._DEFAULT_YEAR

    def test_google_event_xor_config(self):
        with pytest.raises(AssertionError):
            BirthdayEvent(date=datetime(2020, 1, 1), title="Ivan", has_year=True)
        with pytest.raises(AssertionError):
            BirthdayEvent(date=datetime(2020, 1, 1), title="Ivan", has_year=True, config=MainConfig(), google_event={})

        # doesn't raise
        BirthdayEvent(date=datetime(2020, 1, 1), title="Ivan", has_year=True, config=MainConfig())
        BirthdayEvent(date=datetime(2020, 1, 1), title="Ivan", has_year=True, google_event={})

    DATES_PARAMETRIZATION = [
        (datetime(1980, 1, 1), True),
        (datetime(2020, 2, 29), True),  # leap year 29th of February
        (datetime(2120, 11, 30), True),
        (datetime(2020, 1, 1), False),  # no year
        (datetime(2020, 2, 29), False),  # no year, 29th of February
    ]

    @pytest.mark.parametrize("date, has_year", DATES_PARAMETRIZATION)
    def test_date_processing(self, date, has_year):
        event = BirthdayEvent(date=date, title="Ivan", has_year=has_year, config=MainConfig())
        assert event.date.day == date.day
        assert event.date.month == date.month
        if has_year:
            assert event.date.year == date.year
        else:
            assert event.date.year == BirthdayEvent._DEFAULT_YEAR

    @pytest.mark.parametrize("date, has_year", DATES_PARAMETRIZATION)
    def test_date_no_year(self, date, has_year):
        event = BirthdayEvent(date=date, title="Ivan", has_year=has_year, config=MainConfig())
        date_no_year = event.date_no_year
        assert date_no_year.day == date.day
        assert date_no_year.month == date.month
        assert date_no_year.year == BirthdayEvent._DEFAULT_YEAR

    AGES_PARAMETRIZATION = [0, 1, 10, 100]

    @pytest.mark.parametrize("age", AGES_PARAMETRIZATION)
    def test_age(self, age):
        now = datetime.now()
        age_years_ago = now - relativedelta(years=age)
        age_years_ago_minus_day = age_years_ago - relativedelta(days=1)
        age_years_ago_plus_day = age_years_ago + relativedelta(days=1)

        event = BirthdayEvent(date=age_years_ago, title="Ivan", has_year=True, config=MainConfig())
        assert event.age == age

        event = BirthdayEvent(date=age_years_ago_minus_day, title="Ivan", has_year=True, config=MainConfig())
        assert event.age == age

        event = BirthdayEvent(date=age_years_ago_plus_day, title="Ivan", has_year=True, config=MainConfig())
        assert event.age == age - 1

    @pytest.mark.parametrize("age", AGES_PARAMETRIZATION)
    def test_is_birthday_today(self, age):
        now = datetime.now()
        age_years_ago = now - relativedelta(years=age)
        age_years_ago_minus_day = age_years_ago - relativedelta(days=1)
        age_years_ago_plus_day = age_years_ago + relativedelta(days=1)

        event = BirthdayEvent(date=age_years_ago, title="Ivan", has_year=True, config=MainConfig())
        assert event.is_birthday_today

        event = BirthdayEvent(date=age_years_ago_minus_day, title="Ivan", has_year=True, config=MainConfig())
        assert not event.is_birthday_today

        event = BirthdayEvent(date=age_years_ago_plus_day, title="Ivan", has_year=True, config=MainConfig())
        assert not event.is_birthday_today

    @pytest.mark.parametrize("age", AGES_PARAMETRIZATION)
    def test_next_today(self, age):
        now = datetime.now()
        age_years_ago = now - relativedelta(years=age)
        age_years_ago_minus_day = age_years_ago - relativedelta(days=1)
        age_years_ago_plus_day = age_years_ago + relativedelta(days=1)

        fmt = "%Y-%m-%d"

        event = BirthdayEvent(date=age_years_ago, title="Ivan", has_year=True, config=MainConfig())
        assert event.next_birthday.strftime(fmt) == (now.date() + relativedelta(years=1)).strftime(fmt)

        event = BirthdayEvent(date=age_years_ago_minus_day, title="Ivan", has_year=True, config=MainConfig())
        assert event.next_birthday.strftime(fmt) == (now.date() + relativedelta(years=1, days=-1)).strftime(fmt)

        event = BirthdayEvent(date=age_years_ago_plus_day, title="Ivan", has_year=True, config=MainConfig())
        assert event.next_birthday.strftime(fmt) == (now.date() + relativedelta(days=1)).strftime(fmt)

    def test_display_title(self):
        event = BirthdayEvent(date=datetime(2020, 1, 1), title="Ivan", has_year=True, config=MainConfig())
        assert event.display_title == "🎁 Ivan"

        config = MainConfig()
        config.use_zodiac_signs = True
        config.use_zodiac_names = True
        config.title_prefix = "🎉 "
        config.title_postfix = " 🎂"
        event = BirthdayEvent(date=datetime(2020, 1, 1), title="Ivan", has_year=True, config=config)
        assert event.display_title == "🎉 Ivan 🎂 ♑ (Capricorn)"

    def test_to_from_google(self):
        event = BirthdayEvent(date=datetime(2020, 1, 1), title="Ivan", has_year=True, config=MainConfig())
        google_event = event.to_google_event()
        new_event = BirthdayEvent.from_google_event(google_event)
        assert event == new_event

    def test_compare_events_file_and_google(self):
        file_events = [
            BirthdayEvent(date=datetime(2020, 1, 1), title="Ivan", has_year=True, config=MainConfig()),
            BirthdayEvent(date=datetime(2020, 1, 2), title="Ivan2", has_year=True, config=MainConfig()),
            BirthdayEvent(date=datetime(2020, 1, 3), title="Ivan3", has_year=True, config=MainConfig()),
        ]
        google_events = [BirthdayEvent.from_google_event(event.to_google_event()) for event in file_events]
        assert file_events == google_events

        # modify second event
        config2 = MainConfig()
        config2.use_time = not config2.use_time
        file_events[1].config = config2

        # modify third event so that it becomes different event
        file_events[2].title += "x"

        cmp_result = compare_events_file_and_google(file_events, google_events)

        assert cmp_result.has_changes

        assert len(cmp_result.file_only_events) == 1
        assert len(cmp_result.google_only_events) == 1
        assert len(cmp_result.equal_events) == 1
        assert len(cmp_result.updated_events) == 1

        assert list(cmp_result.file_only_events)[0] == file_events[2]
        assert list(cmp_result.google_only_events)[0] == google_events[2]
        assert list(cmp_result.equal_events)[0] == file_events[0] == google_events[0]
        assert list(cmp_result.updated_events)[0] in [file_events[1], google_events[1]]
