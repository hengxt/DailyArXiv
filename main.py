import sys
import time
import pytz
from datetime import datetime

from utils import get_daily_papers_by_keyword_with_retries, generate_table, back_up_files,\
    restore_files, remove_backups, get_daily_date


beijing_timezone = pytz.timezone('Asia/Shanghai')

# NOTE: arXiv API seems to sometimes return an unexpected empty list.

# get current beijing time date in the format of "2021-08-01"
current_date = datetime.now(beijing_timezone).strftime("%Y-%m-%d")
# get last update date from README.md
with open("README.md", "r") as f:
    while True:
        line = f.readline()
        if "Last update:" in line: break
    last_update_date = line.split(": ")[1].strip()
    # if last_update_date == current_date:
        # sys.exit("Already updated today!")

# 信号处理DoA估计相关的关键词
keywords = [
    "Direction of Arrival estimation",
    "DOA estimation",
    "Sound source localization",
    "Array signal processing",
    "Beamforming",
    "Microphone array",
    "Acoustic source localization",
    "Wideband DOA",
    "Broadband direction finding",
    "Speech source localization",
    "MUSIC algorithm",
    "ESPRIT algorithm",
    "Compressed sensing DOA",
    "Sparse array",
    "Adaptive beamforming"
]

max_result = 100 # maximum query results from arXiv API for each keyword
issues_result = 15 # maximum papers to be included in the issue

# all columns: Title, Authors, Abstract, Link, Tags, Comment, Date
# fixed_columns = ["Title", "Link", "Date"]

column_names = ["Title", "Link", "Abstract", "Date", "Comment"]

back_up_files() # back up README.md and ISSUE_TEMPLATE.md

# write to README.md
f_rm = open("README.md", "w") # file for README.md
f_rm.write("# Daily Papers - DoA Estimation & Array Signal Processing\n")
f_rm.write("This project automatically fetches the latest papers from arXiv on Direction of Arrival (DoA) estimation, array signal processing, and related topics.\n\n")
f_rm.write("Topics covered include:\n")
f_rm.write("- Direction of Arrival (DoA) estimation algorithms\n")
f_rm.write("- Sound/speech source localization\n")
f_rm.write("- Microphone array processing\n")
f_rm.write("- Beamforming techniques\n")
f_rm.write("- Wideband and broadband signal processing\n")
f_rm.write("- Acoustic source localization\n")
f_rm.write("- Array signal processing\n\n")
f_rm.write("The subheadings in the README file represent the search keywords.\n")
f_rm.write("Only the most recent articles for each keyword are retained, up to a maximum of 100 papers.\n")
f_rm.write("You can click the 'Watch' button to receive daily email notifications.\n\n")
f_rm.write("Last update: {0}\n\n".format(current_date))

# write to ISSUE_TEMPLATE.md
f_is = open(".github/ISSUE_TEMPLATE.md", "w") # file for ISSUE_TEMPLATE.md
f_is.write("---\n")
f_is.write("title: Latest DoA Estimation Papers - {0}\n".format(get_daily_date()))
f_is.write("labels: documentation, signal-processing, doa-estimation\n")
f_is.write("---\n")
f_is.write("**Latest papers on Direction of Arrival (DoA) estimation, array signal processing, and acoustic source localization**\n\n")
f_is.write("**Please check the [Github](https://github.com/zezhishao/MTS_Daily_ArXiv) page for a better reading experience and more papers.**\n\n")

for keyword in keywords:
    f_rm.write("## {0}\n".format(keyword))
    f_is.write("## {0}\n".format(keyword))
    if len(keyword.split()) == 1: link = "AND" # for keyword with only one word, We search for papers containing this keyword in both the title and abstract.
    else: link = "OR"
    papers = get_daily_papers_by_keyword_with_retries(keyword, column_names, max_result, link)
    if papers is None: # failed to get papers
        print("Failed to get papers!")
        f_rm.close()
        f_is.close()
        restore_files()
        sys.exit("Failed to get papers!")
    rm_table = generate_table(papers)
    is_table = generate_table(papers[:issues_result], ignore_keys=["Abstract"])
    f_rm.write(rm_table)
    f_rm.write("\n\n")
    f_is.write(is_table)
    f_is.write("\n\n")
    time.sleep(5) # avoid being blocked by arXiv API

f_rm.close()
f_is.close()
remove_backups()
