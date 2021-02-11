import csv
import os
import pprint
from datetime import datetime

# logging coloring

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

with open('movies.txt', 'r') as f:
    titles = [line.strip() for line in f]


def check_devices_reports():
    detected_devices = ''
    for file in os.listdir('.'):
        if '.csv' in file:
            for k in devices:
                if k in file:
                    devices[k] = True
    for device in devices:
        if devices[device]:
            detected_devices += ' %s' % device
    print(cl.format('green', '\ndetected devices are:%s' % detected_devices))


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
                            if item['Title'] in row[0] and item['Device'] in file:
                                item['Visibility'] = 'Yes'
                                for param in params:
                                    item[param['name']] = row[columns.index(param['name'])]


def validate_metrics(report_file_name):
    global issues_count

    report_file = open(report_file_name, 'w', encoding='utf-8')
    
    for device in devices:
        if devices[device]:
            passed_assets = []
            print(cl.format('yellow', '\n <==================== %s ====================>' % device))
            report_file.write('\n <==================== %s ====================>' % device)
            report_file.write('\n\nAssets for manual verification:\n')
            for title in assets:
                if title['Device'] == device:

                    if title['Visibility'] == 'Unknown':
                        print(cl.format('red', '{0:<30}'.format(title['Title']) + '%s' % 'Not Found'))
                        report_file.write('\n' + '{0:<30}'.format(title['Title']) + 'Not Found')
                        issues_count += 1
                    else:
                        issue_detected = False
                        errors_line = ''
                        success_line = ''
                        for param in params:
                            if param['values'][0] == '>':
                                if float(title[param['name']]) < param['values'][1]:
                                    issues_count += 1
                                    issue_detected = True
                                    errors_line += '{0:<30}'.format('%s: [ %s %s %s ]' % (
                                        param['name'],
                                        str(float(title[param['name']])),
                                        param['values'][0],
                                        param['values'][1]))
                                else:
                                    success_line += '{0:<30}'.format('%s: [ %s %s %s ]' % (
                                        param['name'],
                                        str(float(title[param['name']])),
                                        param['values'][0],
                                        param['values'][1]))
                            if param['values'][0] == '<':
                                if float(title[param['name']]) > param['values'][1]:
                                    issues_count += 1
                                    issue_detected = True
                                    errors_line += '{0:<30}'.format('%s: [ %s %s %s ]' % (
                                        param['name'],
                                        str(float(title[param['name']])),
                                        param['values'][0],
                                        param['values'][1]))
                                else:
                                    success_line += '{0:<30}'.format('%s: [ %s %s %s ]' % (
                                        param['name'],
                                        (str(float(title[param['name']]))),
                                        param['values'][0],
                                        param['values'][1]))
                        if issue_detected:
                            report_file.write('\n' + '{0:<30}'.format(title['Title']) + errors_line)
                            print('%s%s%s' % (
                                cl.format('red', '{0:<30}'.format(title['Title'])),
                                cl.format('red', errors_line),
                                cl.format('green', success_line)))
                        else:
                            passed_assets.append(title['Title'])
            report_file.write('\n\nAssets passed auto verification:\n')
            for item in passed_assets:
                report_file.write('\n' + '{0:<30}'.format(item))

    report_file.close()


if __name__ == '__main__':

    time_start = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    check_devices_reports()
    assets = create_dict()
    prepare_assets_list()
    print(cl.format('yellow', 'Checking for %s assets among %s report entries' % (len(titles), report_items)))

    # out_filename = 'results_' + time_start + '.txt'
    out_filename = 'results_tmp.txt'
    validate_metrics(out_filename)

    if issues_count == 0:
        print(cl.format('green', 'Everything fine, no issues found'))
    else:
        print(cl.format('red', '%s issue(s) have been found, details in results file: ')
              % issues_count, out_filename)

    # pprint.pprint(assets)
    # pprint.pprint(devices)

