import os
import time
import pytz
import shutil
import datetime
import urllib.parse
import urllib.request
from typing import List, Dict

import feedparser
from easydict import EasyDict

def remove_duplicated_spaces(text: str) -> str:
    return " ".join(text.split())

def request_paper_with_arXiv_api(keyword: str, max_results: int) -> List[Dict[str, str]]:
    # 使用 all: 进行全字段搜索，不加引号以允许模糊匹配
    query = "all:{0}".format(keyword)
    search_query = urllib.parse.quote(query)
    
    url = "http://export.arxiv.org/api/query?search_query={0}&max_results={1}&sortBy=lastUpdatedDate&sortOrder=descending".format(search_query, max_results)
    
    try:
        response = urllib.request.urlopen(url).read().decode('utf-8')
        feed = feedparser.parse(response)
    except Exception as e:
        print(f"Error calling arXiv API: {e}")
        return []

    papers = []
    for entry in feed.entries:
        entry = EasyDict(entry)
        paper = EasyDict()
        
        paper.Title = remove_duplicated_spaces(entry.title.replace("\n", " "))
        paper.Abstract = remove_duplicated_spaces(entry.summary.replace("\n", " "))
        paper.Authors = [remove_duplicated_spaces(_["name"].replace("\n", " ")) for _ in entry.authors]
        paper.Link = remove_duplicated_spaces(entry.link.replace("\n", " "))
        paper.Tags = [remove_duplicated_spaces(_["term"].replace("\n", " ")) for _ in entry.tags]
        paper.Comment = remove_duplicated_spaces(entry.get("arxiv_comment", "").replace("\n", " "))
        paper.Date = entry.updated

        papers.append(paper)
    return papers

def filter_tags(papers: List[Dict[str, str]], target_fields: List[str] = None) -> List[Dict[str, str]]:
    # 扩展领域：eess(电气工程), physics(物理/声学), math(数学), cs(计算机)
    if target_fields is None:
        target_fields = ["cs", "stat", "eess", "physics", "math"]
        
    results = []
    for paper in papers:
        tags = paper.Tags
        for tag in tags:
            if tag.split(".")[0] in target_fields:
                results.append(paper)
                break
    return results

def get_daily_papers_by_keyword_with_retries(keyword: str, column_names: List[str], max_result: int, retries: int = 3) -> List[Dict[str, str]]:
    for i in range(retries):
        papers = get_daily_papers_by_keyword(keyword, column_names, max_result)
        # 如果获取到数据，或者确实没有数据(空列表也是有效结果)，都返回
        if papers is not None: 
            return papers
        else:
            print(f"Retry {i+1} for {keyword}...")
            time.sleep(10)
    return None

def get_daily_papers_by_keyword(keyword: str, column_names: List[str], max_result: int) -> List[Dict[str, str]]:
    papers = request_paper_with_arXiv_api(keyword, max_result)
    if not papers:
        return [] # 返回空列表而不是 None
        
    papers = filter_tags(papers)
    
    # 格式化输出列
    final_papers = []
    for paper in papers:
        new_paper = {}
        for column_name in column_names:
            new_paper[column_name] = paper.get(column_name, "")
        final_papers.append(new_paper)
    return final_papers

def generate_table(papers: List[Dict[str, str]], ignore_keys: List[str] = []) -> str:
    if not papers:
        return "No recent papers found."

    formatted_papers = []
    keys = papers[0].keys()
    for paper in papers:
        formatted_paper = EasyDict()
        formatted_paper.Title = "**" + "[{0}]({1})".format(paper["Title"], paper["Link"]) + "**"
        formatted_paper.Date = paper["Date"].split("T")[0]
        
        for key in keys:
            if key in ["Title", "Link", "Date"] or key in ignore_keys:
                continue
            elif key == "Abstract":
                formatted_paper[key] = "<details><summary>Show</summary><p>{0}</p></details>".format(paper[key])
            elif key == "Authors":
                if paper[key]:
                    formatted_paper[key] = paper[key][0] + " et al."
                else:
                    formatted_paper[key] = "Unknown"
            elif key == "Tags":
                tags = ", ".join(paper[key])
                if len(tags) > 10:
                    formatted_paper[key] = "<details><summary>{0}...</summary><p>{1}</p></details>".format(tags[:5], tags)
                else:
                    formatted_paper[key] = tags
            elif key == "Comment":
                if not paper[key]:
                    formatted_paper[key] = ""
                elif len(paper[key]) > 20:
                    formatted_paper[key] = "<details><summary>{0}...</summary><p>{1}</p></details>".format(paper[key][:5], paper[key])
                else:
                    formatted_paper[key] = paper[key]
        formatted_papers.append(formatted_paper)

    columns = formatted_papers[0].keys()
    columns = ["**" + column + "**" for column in columns]
    header = "| " + " | ".join(columns) + " |"
    header = header + "\n" + "| " + " | ".join(["---"] * len(formatted_papers[0].keys())) + " |"
    
    body = ""
    for paper in formatted_papers:
        body += "\n| " + " | ".join(paper.values()) + " |"
    return header + body

def back_up_files():
    if os.path.exists("README.md"):
        shutil.move("README.md", "README.md.bk")
    if os.path.exists(".github/ISSUE_TEMPLATE.md"):
        shutil.move(".github/ISSUE_TEMPLATE.md", ".github/ISSUE_TEMPLATE.md.bk")

def restore_files():
    if os.path.exists("README.md.bk"):
        shutil.move("README.md.bk", "README.md")
    if os.path.exists(".github/ISSUE_TEMPLATE.md.bk"):
        shutil.move(".github/ISSUE_TEMPLATE.md.bk", ".github/ISSUE_TEMPLATE.md")

def remove_backups():
    if os.path.exists("README.md.bk"):
        os.remove("README.md.bk")
    if os.path.exists(".github/ISSUE_TEMPLATE.md.bk"):
        os.remove(".github/ISSUE_TEMPLATE.md.bk")

def get_daily_date():
    beijing_timezone = pytz.timezone('Asia/Shanghai')
    today = datetime.datetime.now(beijing_timezone)
    return today.strftime("%B %d, %Y")
