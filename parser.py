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
    {"name": "Plays", "values": [">", 5]},
    {"name": "Plays Initiated", "values": [">", 5]},
    {"name": "EBVS (%)", "values": ["<", 60]},
    {"name": "Startup Error (%)", "values": ["<", 60]},
]
issues_count = 0
all_asset = 0
report_line = ''
report_false = ''

devices = ["android", "appletv", "web", "firetv", "androidtv", "roku", "ios"]

with open("movies.txt", "r") as f:
    titles = [line.strip() for line in f]


def create_dict():
    
    with open("movies.txt", "r") as f:
        titles = [line.strip() for line in f]
    
    assets = []
    for i in range(len(titles)):
        for j in range(len(devices)):
            asset = {}
            asset["Title"] = titles[i]
            asset["Visibility"] = "Unknown"
            asset["Device"] = devices[j]
            asset["network"] = 'amc'
            for param in params:
                asset[param['name']] = 0.0
            assets.append(asset)
            
    return assets
   

def check_if_asset_is_accessible():
    global all_asset
    
    for file in os.listdir("."):
        if ".csv" in file:
            print("\nWorking with file:" + file+'\n')
            with open(file) as f:
                reader = csv.reader(f, delimiter=",")
                line_count = 0
                for row in reader:
                    if line_count == 0:
                        #print(f'Column names are {", ".join(row)}')
                        columns = row
                        line_count += 1
                    else:
                        all_asset += 1
                        for item in assets:
                            if item["Title"] in row[0] and item["Device"] in file:
                                    item.update({"Visibility":"Yes"})
                                    for param in params:
                                        item.update({param['name']:row[columns.index(param['name'])]})
              
                 
def validate_metrics():
    global issues_count
    global report_line, report_false

    for device in devices:
        report_line += cl.format('yellow', "\n\n <==================== %s ====================>" % device)
        report_false += "\n\n <==================== %s ====================>" % device
        for title in assets:
            if device == title["Device"]:
                if title["Visibility"] == "Unknown":
                    report_line += "\n" + "{0:<30}".format(title["Title"]) + "%s" % cl.format('red', "Not Found")
                    report_false += "\n" + "{0:<30}".format(title["Title"]) + "Not Found"
                    issues_count += 1
                else:
                    report_line += "\n" + "{0:<30}".format(title["Title"])
                    report_false += "\n" + "{0:<30}".format(title["Title"])
                    for param in params:
                        if param['values'][0] == ">":
                            if float(title[param['name']]) < param['values'][1]:
                                issues_count += 1
                                report_line += "%s: " % cl.format('red', param['name']) + " [ %s %s %s ]" % (str(float(title[param['name']])),param['values'][0], param['values'][1])
                                report_false += param["name"] + " [ %s %s %s ]" % (str(float(title[param['name']])),param['values'][0], param['values'][1])
                            else:
                                report_line += "%s: " % cl.format('green',param['name']) + " [ %s %s %s ]" % (str(float(title[param['name']])), param['values'][0], param['values'][1])
                        if param['values'][0] == "<":
                            if float(title[param['name']]) > param['values'][1]:
                                issues_count += 1
                                report_line += "%s: " % cl.format('red', param['name']) + " [ %s %s %s ]" % (str(float(title[param['name']])), param['values'][0], param['values'][1])
                                report_false += param["name"] + " [ %s %s %s ]" % (str(float(title[param['name']])), param['values'][0], param['values'][1])

                            else:
                                report_line += "%s: " % cl.format('green', param['name']) + " [ %s %s %s ]" % (str(float(title[param['name']])), param['values'][0], param['values'][1])


if __name__ == '__main__':

    time_start = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    assets = create_dict()
    check_if_asset_is_accessible()

    print("Searched for", len(assets), "assets among ", all_asset, "assets")
    
    validate_metrics()
    out_filename = "results_" + time_start + ".txt"
    
    if issues_count == 0:
        print(cl.format('green', "Everything fine, no issues found") + '\n')
    elif issues_count == 1:
        print(cl.format('red', "%s issue has been found, details in results file: ") % issues_count, out_filename + '\n')
    else:
        print(cl.format('red', "%s issues have been found, details in results file: ") % issues_count, out_filename + '\n')
    print(report_line)
    
    f = open(out_filename, 'w', encoding='utf-8')
    f.write("Searched for %s assets" % len(assets) + " among %s assets" % all_asset + "\n\n")
    f.write("%s issues with assets metrics have been found" % issues_count + "\n\n")
    f.write(report_false + "\n")
    f.close()
    # pprint.pprint(assets)