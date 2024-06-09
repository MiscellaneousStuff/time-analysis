import icalendar
import requests
import arrow
import pytz
import re
import regex
import urllib.request

from dotenv import dotenv_values
import matplotlib.pyplot as plt
from datetime import datetime, date, timezone
from icalendar import Calendar as iCalendar
from pytz import all_timezones as timezones_table

categories_re = regex.compile("([-\w]+:\s?)+") # Working well on diff cat levels
# categories_re = regex.compile("([^,\n])+")

def flatten(t):
    return [item for sublist in t for item in sublist]

def process_ics(ics_txt):
    events = []
    cal = iCalendar.from_ical(ics_txt)
    calendar_method = None
    for component in cal.walk():
        if component.name == "VCALENDAR":
            # Top-level calendar event
            calendar_method = component.get('method')

        elif component.name == "VTIMEZONE":
            tzname = component.get('TZID')
            assert tzname in timezones_table,\
                "Non-UTC timezone should be in table"

        elif component.name == "VEVENT":
            # Original start/end dt
            try:
                original_start = component.get('dtstart').dt
                original_end = component.get('dtend').dt
            except Exception as e:
                print(e)
            
            # Convert dates
            start = arrow.get(original_start)
            end = arrow.get(original_end)
            
            assert isinstance(start, type(end)), "Start and end should be of "\
                "the same type"
            
            # Summaries
            title = None
            summaries = component.get('summary', [])
            if not isinstance(summaries, list):
                summaries = [summaries]
            if summaries != []:
                title = " - ".join(summaries)

            # Desc.
            description = str(component.get('description'))

            # Event Duration
            duration = end - start
            seconds_per_day = 24 * 60 * 60
            if duration.seconds >= seconds_per_day: # Seconds 
                all_day = True
            else:
                all_day = False

            # Categories
            mixed = False
            desc = False
            if not title:
                title = ""
            tmp_title = title.lower().strip()
            if "mixed:" in tmp_title:
                mixed = True
            if "(desc.)" in tmp_title:
                desc = True
            tmp_title = tmp_title.replace("(desc.) ", "")
            tmp_title = tmp_title.replace("mixed: ", "")
            categories = categories_re.match(tmp_title)
            if "fincheck" in tmp_title:
                print('cats:', categories)
            if categories:
                cats = []
                print('CAT CHECK:', categories)
                for i in range(len(categories.groups())):
                    cur = categories.group(i)
                    cur = cur.strip().split(":")
                    # NOTE: This is a hack to get sleep as top-level category before
                    #       level 1+ regex is implemented properly
                    if "sleep" in tmp_title:
                        cur[0] = "sleep"
                    cats.append(cur)
                categories = cats
            else:
                categories = []
            if "fincheck" in tmp_title:
                print('FINAL CATS:', categories)

            # Event
            event = {
                "title": title,
                "description": description,
                "start": start,
                "end": end,
                "duration": duration,
                "categories": categories,
                "mixed": mixed,
                "all_day": all_day
            }
            events.append(event)

    # print("EVENTS:", events)
    return events

class Calendar(object):
    def __init__(self, filename):
        try:
            with open(filename, encoding="utf-8") as f:
                txt = f.read()
                self.events = process_ics(txt)
        except Exception as e:
            print('Error initializing cal:', e)

    def get_events_between(self, start_range, end_range):
        events = []

        for event in self.events:
            # Only check for events within range (inclusive of start and end)
            # for now
            if event["start"] >= start_range and \
                event["end"] <= end_range:
                events.append(event)

        print('ev:', events[0])
        return events

    def get_category_hours(self, start_range, end_range, cat_depth=0, ignore_cats=[]):
        # Get relevant events
        events = self.get_events_between(start_range, end_range)

        # Get all categories
        uniq_cats = [[c[cat_depth] if len(c) >= cat_depth+1 else ""
                      for c in e["categories"]]
                      for e in events]
        uniq_cats = flatten(uniq_cats)
        uniq_cats = set(uniq_cats)

        # Calculate category accounts, account for mixed events
        totals = {}
        for c in uniq_cats:
            totals[c] = 0
        for ev in events:
            cats = ev["categories"]
            tops = [c[cat_depth] if len(c) >= cat_depth+1 else "" for c in cats]
            duration = ev["duration"]
            mixed = ev["mixed"]
            for t in tops:
                if mixed:
                    duration /= len(tops)
                totals[t] += (duration.seconds) / 3600
        
        for ig in ignore_cats:
            totals.pop(ig, None)

        return totals

    def plot_category_hours(self, start_range, end_range, cat_depth=0, ignore_cats=[]):
        # Get relevant events
        data = self.get_category_hours(start_range, end_range, cat_depth, ignore_cats)

        # Data
        labels = data.keys()
        sizes = list(data.values())
        total = sum(sizes)
        print('data:', labels, sizes, total)

        # Ignore categories

        # Per Plot Function
        def per_plot(pc):
            val = (pc / 100) * total
            return f"{val:10.2f} hrs\n{pc:10.2f}%"

        # Plot details
        fig1, ax1 = plt.subplots()
        #ax1.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        ax1.pie(sizes, labels=labels, autopct=per_plot, shadow=True, startangle=90)
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        
        # Show plot
        plt.show()
        
if __name__ == "__main__":
    config = dotenv_values(".env")
    ical_secret_url = config["ICAL_SECRET"]

    urllib.request.urlretrieve(ical_secret_url, './cal.ics')

    cal = Calendar("./cal.ics")
    
    # from datetime import datetime, timedelta

    d = 7
    start      = arrow.utcnow()
    start      = start.shift(days=-d*0)
    week       = start.span('week')
    week_start = week[0]
    week_end   = week[1].shift(days=0)

    print(week_start, week_end)

    print("time span:", week_start, week_end)

    cal.plot_category_hours(
        week_start,
        week_end,
        cat_depth=0,
        ignore_cats=[])

    # for d in [0]: # range(0, 7+1):
    #     start      = arrow.utcnow()
    #     start      = start.shift(days=-d*7)
    #     week       = start.span('week')
    #     week_start = week[0]
    #     # week_end   = week[1].shift(days=-30)
    #     week_end   = week[1]

    #     print("time span:", week_start, week_end)

    #     cal.plot_category_hours(
    #         week_start,
    #         week_end,
    #         cat_depth=0,
    #         ignore_cats=[])
    
    # events = cal.get_events_between(week_start, week_end)
    # events = [ev
    #           for ev in events
    #           if "Pyrocloud" in ev["title"]]
    # for ev in events:
    #     print(ev)