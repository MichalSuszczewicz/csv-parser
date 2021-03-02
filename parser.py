import csv
import os
import pprint
from datetime import datetime
import shutil


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
    with open('assets.txt', 'r') as f:
        titles = [line.strip() for line in f]
except FileNotFoundError:
    print(cl.format('red', 'File assets.txt not found, exiting'))
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
        return detected_devices
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
            csvfile = open(file,'r',encoding='utf-8')
            reader = csv.reader(csvfile, delimiter=',')
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


def initiate_html_report(environment, time, html_report_name):
    html_file = open(html_report_name, 'w')
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
                       #assets, #metrics{
                            display: none;
                       }
                       button{
                            cursor: pointer;
                            margin: 5px;
                       }
           </style>
           <script>
               function showAssets() {
                    var x = document.getElementById("assets");
                    if (x.style.display == "block") {
                         x.style.display = "none";
                     }
                     else {
                         x.style.display = "block";
                     }
                }
                function showMetrics() {
                    var x = document.getElementById("metrics");
                    if (x.style.display == "block") {
                         x.style.display = "none";
                     }
                     else {
                         x.style.display = "block";
                     }
                }
            </script>
       </head>
       <body>
       """)
    html_file.write('<h1>Test report</h1>')
    html_file.write('<h4>Execution Date: %s</h4><h3>Environment:</h3><p>%s</p>' % (time, environment))
    html_file.write('<h3>Input reports:</h3> <ul>')
    for file in os.listdir('.'):
        if '.csv' in file:
            for k in devices:
                if k in file:
                    html_file.write('<li>%s</li>' % file)
    html_file.write('</ul><button onclick="showMetrics()">Verified Metrics</button>')
    html_file.write('<button onclick="showAssets()">Searched assets</button><ol id="assets">')
    for item in titles:
        html_file.write('<li>%s</li>' % item)
    html_file.write('</ol>')
    html_file.write('<table id="metrics"><tr>')
    for param in params:
        html_file.write('<td>%s</td><td>%s</td><td>%s</td></tr>' % (param['name'], param['values'][0], param['values'][1]))
    html_file.write('</table>')
    html_file.close()
    
    
def validate_metrics(report_file_name):
    global issues_count

    html_file = open(report_file_name, 'a')

    for device in devices:
        if devices[device]:
            passed_assets = []
            print(cl.format('yellow', '\n<==================== %s ====================>' % device))
            html_file.write('<h4>Assets for manual verification on %s device:</h4>' % device)
            html_file.write('<table><tr>')
            for title in assets:
                if title['Device'] == device:

                    if title['Visibility'] == 'Unknown':
                        print(cl.format('red', '{0:<30}'.format(title['Title']) + '%s' % 'Not Found'))
                        html_file.write('<td>%s:</td><td><span class="fail"> Not Found</span></td></tr>' % title['Title'])
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
                            print('%s%s%s' % (
                                cl.format('red', '{0:<30}'.format(title['Title'])),
                                cl.format('red', errors_line),
                                cl.format('green', success_line)))
                            html_file.write('<td>%s:</td><td><span class="fail"> %s </span></td><td><span class="pass"> %s </span></td></tr>' % (title['Title'],
                                            errors_line, success_line))
                        else:
                            passed_assets.append(title['Title'])
            html_file.write('</table>')
            html_file.write('<h4>Assets passed auto verification on %s device:</h4>' % device)
            html_file.write('<table><tr>')
            for item in passed_assets:
                html_file.write('<td><span class="pass">%s</td></tr>' % item)
            html_file.write('</table>')

    html_file.close()
    
    
def archive_report(html_file):
    
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
                if '.csv' in file:
                    shutil.move(file, path + file)
                    print(cl.format('blue', '{0:<100}'.format(file)), cl.format('yellow', 'was archived'))
                elif '.txt' in file:
                    shutil.copy(file, path + file)
                    print(cl.format('blue', '{0:<100}'.format(file)), cl.format('yellow', 'was archived as a copy'))
                elif html_file in file and not 'last_results.html' == file:
                    shutil.copy(file, path + file)
                    if os.path.exists(os.getcwd()+'/last_results.html'):
                        os.remove('last_results.html')
                    os.rename(file, 'last_results.html')
                    print(cl.format('blue', '{0:<100}'.format(file)), cl.format('yellow', 'was archived as a copy'))
            return True
        elif confirm.lower() in ('n', 'no'):
            print(cl.format('blue', 'Results were not archived.'))
            for file in os.listdir('.'):
                if html_file in file:
                    if os.path.exists(os.getcwd()+'/last_results.html'):
                        os.remove('last_results.html')
                    os.rename(file, 'last_results.html')
            return False
        else:
            print('\nInvalid Option. Please Enter a Valid Option.')


if __name__ == '__main__':

    time_start = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    out_filename = 'results_' + time_start + '.html'
    detected_devices = check_devices_reports()
    assets = create_dict()
    prepare_assets_list()
    initiate_html_report(detected_devices, time_start, out_filename)
    print(cl.format('yellow', 'Checking for %s assets among %s report entries' % (len(titles), report_items)))
    
    validate_metrics(out_filename)

    if issues_count == 0:
        print(cl.format('green', 'Everything fine, no issues found'))
    else:
        print(cl.format('red', '%s issue(s) have been found, details in results file: ')
              % issues_count, out_filename)
        
    archive_report(out_filename)
    import webbrowser

    new = 2  # open in a new tab, if possible
    url = 'file://' + os.getcwd() + '/last_results.html'
    webbrowser.open(url, new=new)
    # pprint.pprint(assets)
    # pprint.pprint(devices)