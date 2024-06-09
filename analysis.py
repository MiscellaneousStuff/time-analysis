import re
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict

start_date = datetime(2024, 2, 19)
end_date = datetime(2024, 6, 9)
dtstart_pattern = re.compile(r'^DTSTART.*:(.*)')
dtend_pattern = re.compile(r'^DTEND.*:(.*)')
summary_pattern = re.compile(r'^SUMMARY:(.*)')

# Load the .ics file
file_path = 'cal.ics'
with open(file_path, 'r') as f:
    lines = f.readlines()
    
# Function to parse datetime from ics format, handle both date and datetime strings
def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str.rstrip('Z'), '%Y%m%dT%H%M%S')
    except ValueError:
        return datetime.strptime(dt_str, '%Y%m%d')

# Function to clean and categorize events, excluding all-day events and filtering for work categories
def get_work_hours_per_day(calendar_lines):
    work_hours_per_day = defaultdict(float)
    current_event = {}
    work_categories = {'travel', 'codeverse', 'anterion', 'anterior', 'occupation', 'hackathon', 'project'}

    for line in calendar_lines:
        if line.startswith('BEGIN:VEVENT'):
            current_event = {}
        elif line.startswith('END:VEVENT'):
            if 'DTSTART' in current_event and 'DTEND' in current_event and 'SUMMARY' in current_event:
                event_start = parse_datetime(current_event['DTSTART'])
                event_end = parse_datetime(current_event['DTEND'])
                if start_date <= event_start <= end_date and 'T' in current_event['DTSTART']:  # Exclude all-day events
                    duration = (event_end - event_start).total_seconds() / 3600
                    summary = current_event['SUMMARY'].lower()
                    summary = re.sub(r'\(.*?\)\s*', '', summary)  # Remove (Desc.) part
                    parts = summary.split(":")
                    category = parts[0].strip("() ")
                    if category in work_categories:
                        work_hours_per_day[event_start.date()] += duration
        else:
            dtstart_match = dtstart_pattern.match(line)
            dtend_match = dtend_pattern.match(line)
            summary_match = summary_pattern.match(line)
            if dtstart_match:
                current_event['DTSTART'] = dtstart_match.group(1)
            elif dtend_match:
                current_event['DTEND'] = dtend_match.group(1)
            elif summary_match:
                current_event['SUMMARY'] = summary_match.group(1)
    
    return work_hours_per_day

# Get work hours per day
work_hours_per_day = get_work_hours_per_day(lines)

# # Prepare data for plotting
dates = sorted(work_hours_per_day.keys())
hours = [work_hours_per_day[date] for date in dates]

# # Plotting the graph
# plt.figure(figsize=(14, 7))
# plt.plot(dates, hours, marker='o', linestyle='-', color='b')
# plt.title('Work Hours per Day (Week 8 to Week 22, 2024)')
# plt.xlabel('Date')
# plt.ylabel('Work Hours')
# plt.xticks(rotation=45)
# plt.grid(True)
# plt.tight_layout()

# # Show the plot
# plt.show()

import numpy as np
from scipy.stats import linregress

# Calculate mean and median
mean_hours = np.mean(hours)
median_hours = np.median(hours)

# Perform linear regression to get the line of best fit
slope, intercept, r_value, p_value, std_err = linregress([date.toordinal() for date in dates], hours)
line_of_best_fit = [slope * date.toordinal() + intercept for date in dates]

# Plotting the graph with line of best fit
plt.figure(figsize=(14, 7))
plt.plot(dates, hours, marker='o', linestyle='-', color='b', label='Work Hours')
plt.plot(dates, line_of_best_fit, color='r', label='Line of Best Fit')
plt.axhline(y=mean_hours, color='g', linestyle='--', label=f'Mean: {mean_hours:.2f} hrs')
plt.axhline(y=median_hours, color='y', linestyle='--', label=f'Median: {median_hours:.2f} hrs')

# Adding titles and labels
plt.title('Work Hours per Day (Week 8 to Week 22, 2024)')
plt.xlabel('Date')
plt.ylabel('Work Hours')
plt.xticks(rotation=45)
plt.grid(True)
plt.legend()
plt.tight_layout()

# Show the plot
plt.show()

# # Function to clean and categorize events, excluding all-day events
# def clean_and_categorize_events(calendar_lines):
#     category_durations = defaultdict(float)
#     current_event = {}
#     for line in calendar_lines:
#         if line.startswith('BEGIN:VEVENT'):
#             current_event = {}
#         elif line.startswith('END:VEVENT'):
#             if 'DTSTART' in current_event and 'DTEND' in current_event and 'SUMMARY' in current_event:
#                 event_start = parse_datetime(current_event['DTSTART'])
#                 event_end = parse_datetime(current_event['DTEND'])
#                 if start_date <= event_start <= end_date and 'T' in current_event['DTSTART']:  # Exclude all-day events
#                     duration = (event_end - event_start).total_seconds() / 3600
#                     summary = current_event['SUMMARY']
#                     summary = re.sub(r'\(.*?\)\s*', '', summary)  # Remove (Desc.) part
#                     parts = summary.split(":")
#                     category = parts[0].strip("() ")
#                     category_durations[category] += duration
#         else:
#             dtstart_match = dtstart_pattern.match(line)
#             dtend_match = dtend_pattern.match(line)
#             summary_match = summary_pattern.match(line)
#             if dtstart_match:
#                 current_event['DTSTART'] = dtstart_match.group(1)
#             elif dtend_match:
#                 current_event['DTEND'] = dtend_match.group(1)
#             elif summary_match:
#                 current_event['SUMMARY'] = summary_match.group(1)
#     return category_durations

# # Clean and categorize events
# category_durations = clean_and_categorize_events(lines)

# # Plotting the pie chart with hours and percentage
# labels = category_durations.keys()
# sizes = category_durations.values()
# total_hours = sum(sizes)

# plt.figure(figsize=(10, 7))
# plt.pie(sizes, labels=[f'{label} ({size:.1f} hrs)' for label, size in zip(labels, sizes)], autopct=lambda p: f'{p:.1f}% ({p*total_hours/100:.1f} hrs)', startangle=140)
# plt.title('Event Durations by Category (Week 8 to Week 22, 2024)')
# plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
# plt.show()