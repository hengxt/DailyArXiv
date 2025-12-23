import sys
import time
import pytz
from datetime import datetime

from utils import get_daily_papers_by_keyword_with_retries, generate_table, back_up_files,\
    restore_files, remove_backups, get_daily_date

beijing_timezone = pytz.timezone('Asia/Shanghai')

# 获取当前日期
current_date = datetime.now(beijing_timezone).strftime("%Y-%m-%d")

# 检查是否已更新
with open("README.md", "r") as f:
    while True:
        line = f.readline()
        if "Last update:" in line: break
    last_update_date = line.split(": ")[1].strip()
    # if last_update_date == current_date:
    #     sys.exit("Already updated today!")

# 精简后的关键词：阵列DOA、声音DOA、宽带DOA
keywords = [
    "Array DOA estimation",     # 阵列DOA
    "Sound DOA estimation",     # 声音DOA (也覆盖 Sound Source Localization)
    "Broadband DOA estimation"  # 宽带DOA
]

max_result = 100 
issues_result = 15 

column_names = ["Title", "Link", "Abstract", "Date", "Comment"]

back_up_files()

# 更新 README.md
f_rm = open("README.md", "w")
f_rm.write("# Daily Papers - DoA Estimation\n")
f_rm.write("Automatically fetches the latest arXiv papers on DoA estimation.\n\n")
f_rm.write("Last update: {0}\n\n".format(current_date))

# 更新 ISSUE_TEMPLATE.md
f_is = open(".github/ISSUE_TEMPLATE.md", "w")
f_is.write("---\n")
f_is.write("title: Latest DoA Papers - {0}\n".format(get_daily_date()))
f_is.write("labels: signal-processing, doa\n")
f_is.write("---\n")
f_is.write("**Latest papers on DoA estimation**\n\n")

for keyword in keywords:
    f_rm.write("## {0}\n".format(keyword))
    f_is.write("## {0}\n".format(keyword))
    
    # 获取论文 (移除 link 参数，底层改为 all 搜索)
    papers = get_daily_papers_by_keyword_with_retries(keyword, column_names, max_result)
    
    if papers is None:
        print(f"Failed to get papers for {keyword}!")
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
    
    time.sleep(2) 

f_rm.close()
f_is.close()
remove_backups()
