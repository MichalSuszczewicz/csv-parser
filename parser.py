import csv
import os
import pprint
from datetime import datetime
import shutil
from dominate.tags import *
import dominate


class ColorLog:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def format(self, coloring, text):
        output = ''

        if coloring == 'ok' or coloring == 'green' or coloring is True:
            output = self.OKGREEN + text + self.ENDC
        elif coloring == 'fail' or coloring == 'red' or coloring is False:
            output = self.FAIL + text + self.ENDC
        elif coloring == 'warning' or coloring == 'yellow':
            output = self.WARNING + text + self.ENDC
        elif coloring == 'span' or coloring == 'blue':
            output = self.OKBLUE + text + self.ENDC

        return output


cl = ColorLog()


params = [
    {'name': 'Plays', 'values': ['>', 5]},
    {'name': 'Plays Initiated', 'values': ['>', 5]},
    {'name': 'EBVS (%)', 'values': ['<', 60]},
    {'name': 'Startup Error (%)', 'values': ['<', 60]},
]
issues_count = 0
report_items = 0
report_line = ''

devices = {
    'android': False,
    'appletv': False,
    'web': False,
    'firetv': False,
    'androidtv': False,
    'roku': False,
    'ios': False
}

try:
    with open('movies.txt', 'r') as f:
        titles = [line.strip() for line in f]
except FileNotFoundError:
    print(cl.format('red', 'File movies.txt not found, exiting'))
    exit(1)


def check_devices_reports():
    detected_devices = ''
    for file in os.listdir('.'):
        if '.csv' in file:
            for k in devices:
                if k in file and not devices[k]:
                    devices[k] = True
                    detected_devices += ' %s' % k
    if detected_devices:
        print(cl.format('green', '\nDetected devices are:%s' % detected_devices))
    else:
        print(cl.format('red', '\nNo device or CSV report was detected in the script directory'))
        quit()


def create_dict():
    global titles
    assets_to_check = []
    for i in range(len(titles)):
        for k in devices:
            if devices[k]:
                asset = {'Title': titles[i], 'Visibility': 'Unknown', 'Device': k, 'network': 'amc'}
                for param in params:
                    asset[param['name']] = 0.0
                assets_to_check.append(asset)
            
    return assets_to_check
   

def prepare_assets_list():
    global report_items

    for file in os.listdir('.'):
        if '.csv' in file:
            print(cl.format('green', 'csv file has been found: %s' % file))
            with open(file) as csv_file:
                reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                for row in reader:
                    if line_count == 0:
                        columns = row
                        line_count += 1
                    else:
                        report_items += 1
                        for item in assets:
                            if item['Title'] in row[0] and item['Device'] in file.lower():
                                item['Visibility'] = 'Yes'
                                for param in params:
                                    item[param['name']] = row[columns.index(param['name'])]


def validate_metrics(report_file_name):
    global issues_count

    report_file = open(report_file_name, 'w', encoding='utf-8')

    html_file = open('results.html', 'w')
    html_file.write("""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
            "http://www.w3.org/TR/html4/loose.dtd">
    <html>
    <head>
        <title>Test Report</title>
        <style>
        
        body {
                        background-color: #F9F8F1;
                        color: #2C232A;
                        font-family: sans-serif;
                        font-size: 1em;
                        margin: 1em 1em;
                    }
                    .fail{
                        color: red;
                    }
                    .pass{
                        color: green;
                    }
        </style>
    </head>
    <body>
    """)
    html_file.write('<h1>Test report</h1>')

    for device in devices:
        if devices[device]:
            passed_assets = []
            print(cl.format('yellow', '\n<==================== %s ====================>' % device))
            report_file.write('\n<==================== %s ====================>' % device)
            report_file.write('\n\nAssets for manual verification:\n')
            html_file.write('<h4>Assets for manual verification on %s device:</h4>' % device)
            html_file.write('<ul>')
            for title in assets:
                if title['Device'] == device:

                    if title['Visibility'] == 'Unknown':
                        print(cl.format('red', '{0:<30}'.format(title['Title']) + '%s' % 'Not Found'))
                        report_file.write('\n' + '{0:<30}'.format(title['Title']) + 'Not Found')
                        html_file.write('<li>%s:<span class="fail"> Not Found</span></li>' % title['Title'])
                        issues_count += 1
                    else:
                        issue_detected = False
                        errors_line = ''
                        success_line = ''
                        for param in params:
                            param_issue = False
                            if param['values'][0] == '>':
                                if float(title[param['name']]) < param['values'][1]:
                                    issues_count += 1
                                    issue_detected = True
                                    param_issue = True
                            if param['values'][0] == '<':
                                if float(title[param['name']]) > param['values'][1]:
                                    issues_count += 1
                                    issue_detected = True
                                    param_issue = True

                            if param_issue:
                                errors_line += '{0:<30}'.format('%s: [ %s %s %s ]' % (
                                    param['name'],
                                    '{:.1f}'.format(float(title[param['name']])),
                                    param['values'][0],
                                    '{:.1f}'.format(param['values'][1])))
                            else:
                                success_line += '{0:<30}'.format('%s: [ %s %s %s ]' % (
                                    param['name'],
                                    '{:.1f}'.format(float(title[param['name']])),
                                    param['values'][0],
                                    '{:.1f}'.format(param['values'][1])))

                        if issue_detected:
                            report_file.write('\n' + '{0:<30}'.format(title['Title']) + errors_line)
                            print('%s%s%s' % (
                                cl.format('red', '{0:<30}'.format(title['Title'])),
                                cl.format('red', errors_line),
                                cl.format('green', success_line)))
                            html_file.write('<li>%s:<span class="fail"> %s </span> <span class="pass"> %s </span></li>' % (title['Title'],
                                            errors_line, success_line))
                        else:
                            passed_assets.append(title['Title'])
            html_file.write("</ul>")
            report_file.write('\n\nAssets passed auto verification:\n')
            html_file.write('<h4>Assets passed auto verification on %s device:</h4>' % device)
            html_file.write('<ul>')
            for item in passed_assets:
                report_file.write('\n' + '{0:<30}'.format(item))
                html_file.write('<li class="pass">%s</li>' % item)
            html_file.write("</ul>")

    report_file.close()
    html_file.close()

    import webbrowser
    new = 2  # open in a new tab, if possible
    url = "file://" + os.getcwd() + "/results.html"
    webbrowser.open(url, new=new)
    
    
def archive_report():
    
    while True:
        confirm = input('\nDo you want to archive this results? [y]Yes or [n]No: ')
        if confirm.lower() in ('y', 'yes'):
            month = datetime.now().strftime('%Y-%m')
            day = datetime.now().strftime('%d')
            path = os.getcwd() + '/reports/report_%s/%s/' % (month, day)
        
            try:
                os.makedirs(path)
            except OSError:
                if os.path.exists(path):
                    print('Archive directory already exists %s' % path)
                else:
                    print('Successfully created the archive directory %s' % path)
        
            for file in os.listdir('.'):
                if '.csv' in file or out_filename == file or '.html' in file:
                    shutil.move(file, path + file)
                    print(cl.format('blue', '{0:<100}'.format(file)), cl.format('yellow', 'was archived'))
                if '.txt' in file and out_filename not in file:
                    shutil.copy(file, path + file)
                    print(cl.format('blue', '{0:<100}'.format(file)), cl.format('yellow', 'was archived as a copy'))
            return True
        elif confirm.lower() in ('n', 'no'):
            print(cl.format('blue', 'Results were not archived.'))
            return False
        else:
            print('\nInvalid Option. Please Enter a Valid Option.')


if __name__ == '__main__':

    time_start = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    check_devices_reports()
    assets = create_dict()
    prepare_assets_list()
    print(cl.format('yellow', 'Checking for %s assets among %s report entries' % (len(titles), report_items)))

    out_filename = 'results_' + time_start + '.txt'
    #out_filename = 'results_tmp.txt'
    validate_metrics(out_filename)

    if issues_count == 0:
        print(cl.format('green', 'Everything fine, no issues found'))
    else:
        print(cl.format('red', '%s issue(s) have been found, details in results file: ')
              % issues_count, out_filename)
        
    archive_report()
    # pprint.pprint(assets)
    # pprint.pprint(devices)