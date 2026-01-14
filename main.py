import sys
import time
import pytz
from datetime import datetime

from utils import get_daily_papers_by_keyword_with_retries, generate_table, back_up_files,\
    restore_files, remove_backups, get_daily_date

beijing_timezone = pytz.timezone('Asia/Shanghai')

current_date = datetime.now(beijing_timezone).strftime("%Y-%m-%d")

# 检查是否已更新
# with open("README.md", "r") as f:
#     while True:
#         line = f.readline()
#         if "Last update:" in line: break
#     last_update_date = line.split(": ")[1].strip()
#     # if last_update_date == current_date:
#     #     sys.exit("Already updated today!")


keywords = [
    "MUSIC Array",      # 阵列MUSIC算法的DOA估计
    "SBL Array",      # 阵列SBL算法的DOA估计
    "Subspace Array",      # 阵列子空间算法的DOA估计
    "Speech",      # 语音的DOA估计
    "Acoustic",      # 声学信号的DOA估计
    "Broadband", # 宽带信号的DOA估计
    "" # 其他的DOA估计
]

max_result = 20
issues_result = 8

column_names = ["Title", "Link", "Abstract", "Date", "Comment"]

back_up_files()

# 更新 README.md
f_rm = open("README.md", "w", encoding="utf-8")
f_rm.write("# Daily Papers - DoA Estimation\n")
f_rm.write("Automatically fetches the latest arXiv papers on Direction of Arrival (DoA) estimation and Array Signal Processing.\n")
f_rm.write("Strictly filtered for Signal Processing (eess.SP, eess.AS) and Audio (cs.SD) fields.\n\n")
f_rm.write("Last update: {0}\n\n".format(current_date))

# 更新 ISSUE_TEMPLATE.md
f_is = open(".github/ISSUE_TEMPLATE.md", "w", encoding="utf-8")
f_is.write("---\n")
f_is.write("title: Latest DoA Papers - {0}\n".format(get_daily_date()))
f_is.write("labels: signal-processing, doa, array-processing\n")
f_is.write("---\n")
f_is.write("**Latest papers on DoA estimation**\n\n")

for keyword in keywords:
    # 标题美化：去掉引号等符号
    display_keyword = keyword.replace('"', '').replace('+', ' ')
    f_rm.write("## {0}\n".format(display_keyword))
    f_is.write("## {0}\n".format(display_keyword))
    
    papers = get_daily_papers_by_keyword_with_retries(keyword, column_names, max_result)
    
    if papers is None:
        print(f"Failed to get papers for {keyword}!")
        # 即使某个关键词失败，也不要直接退出，继续下一个
        continue
    
    if len(papers) == 0:
        f_rm.write("No new papers found.\n\n")
        f_is.write("No new papers found.\n\n")
        continue

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
