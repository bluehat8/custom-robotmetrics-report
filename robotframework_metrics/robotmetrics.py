import os
import logging
from datetime import datetime
from robot.api import ExecutionResult
from jinja2 import Environment, FileSystemLoader
from .suite_results import SuiteResults
from .test_results import TestResults
from .keyword_results import KeywordResults
from .keyword_times import KeywordTimes
from .dashboard_stats import Dashboard

templates_dir = os.path.join(os.getcwd(), 'templates')
env = Environment( loader = FileSystemLoader(templates_dir) )
template = env.get_template('index.html')

IGNORE_LIBRARIES = ["SeleniumLibrary", "BuiltIn",
 "Collections", "DateTime", "Dialogs", "OperatingSystem"
 "Process", "Screenshot", "String", "Telnet", "XML"]

suite_list, test_list, kw_list, kw_times = [], [], [], []

def generate_report(opts):
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    # Ignores following library keywords in metrics report
    ignore_library = IGNORE_LIBRARIES
    if opts.ignore:
        ignore_library.extend(opts.ignore)
    
    # Report to support file location as arguments
    path = os.path.abspath(os.path.expanduser(opts.path))

    # output.xml files
    output_names = []
    # support "*.xml" of output files
    if ( opts.output == "*.xml" ):
        for item in os.listdir(path): 
            item = os.path.join(path, item)
            if os.path.isfile(item) and item.endswith('.xml'):
                output_names.append(item)
    else:
        for curr_name in opts.output.split(","):
            curr_path = os.path.join(path, curr_name)
            output_names.append(curr_path)
    
    # copy the list of output_names onto the one of required_files; the latter may (in the future) 
    # contain files that should not be processed as output_names
    required_files = list(output_names)
    missing_files = [filename for filename in required_files if not os.path.exists(filename)]
    if missing_files:
        # We have files missing.
        exit("output.xml file is missing: {}".format(", ".join(missing_files)))

    mt_time = datetime.now().strftime('%Y%m%d-%H%M%S')

    # Output result file location
    if opts.metrics_report_name:
        result_file_name = opts.metrics_report_name
    else:
        result_file_name = 'metrics-' + mt_time + '.html'
    result_file = os.path.join(path, result_file_name)
    
    # Read output.xml file
    result = ExecutionResult(*output_names)

    logging.info(" Converting .xml to .html file. This may take few minutes...")

    logging.info(" 1 of 4: Capturing suite metrics")
    result.visit(SuiteResults(suite_list))

    logging.info(" 2 of 4: Capturing test metrics")
    result.visit(TestResults(test_list))

    if opts.showkeyword == "True":
        logging.info(" 3 of 4: Capturing keyword metrics")
        result.visit(KeywordResults(kw_list, IGNORE_LIBRARIES))
        hide_keyword_menu = ""
    else:
        logging.info(" 3 of 4: Ignoring keyword metrics")
        result.visit(KeywordResults([], IGNORE_LIBRARIES))
        hide_keyword_menu = "hide"

    if opts.showkwtimes == "True":
        kw_times = KeywordTimes().get_keyword_times(kw_list)
        hide_kw_times_menu = ""
    else:
        kw_times = KeywordTimes().get_keyword_times([])
        hide_kw_times_menu = "hide"
    
    if opts.showtags == "True":
        hide_tags = ""
    else:
        hide_tags = "hide"

    logging.info(" 4 of 4: Preparing data for dashboard")
    dashboard_obj = Dashboard()
    suite_stats = dashboard_obj.get_suite_statistics(suite_list)
    test_stats = dashboard_obj.get_test_statistics(test_list)
    kw_stats = dashboard_obj.get_keyword_statistics(kw_list)
    error_stats = dashboard_obj.group_error_messages(test_list)

    logging.info(" Writing results to html file")
    with open(result_file_name, 'w') as fh:
        fh.write(template.render(
            hide_tags = hide_tags,
            hide_keyword_menu = hide_keyword_menu,
            hide_kw_times_menu = hide_kw_times_menu,
            suite_stats = suite_stats,
            test_stats = test_stats,
            kw_stats = kw_stats,
            suites = suite_list,
            tests = test_list,
            keywords = kw_list,
            keyword_times = kw_times,
            error_stats = error_stats
        ))
    logging.info(" Results file created successfully and can be found at {}".format(result_file))