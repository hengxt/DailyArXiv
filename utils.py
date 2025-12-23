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
    # 【核心修改1】构建查询语句
    # 1. 给关键词加上双引号，强制进行“短语匹配”。
    #    例如搜索 "DOA estimation"，不会匹配到 "DOA... parameter estimation" (中间隔很远的情况)
    # 2. 限制在 Title (ti) 和 Abstract (abs) 中搜索，不再使用 all (全文)
    
    # 构造形式：(ti:"keyword" OR abs:"keyword")
    # quote_plus 会处理空格和特殊字符
    phrase = f'"{keyword}"'
    query = f'(ti:{phrase} OR abs:{phrase})'
    
    search_query = urllib.parse.quote(query)
    
    # 按最后更新时间排序
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

def filter_tags(papers: List[Dict[str, str]]) -> List[Dict[str, str]]:
    # 【核心修改2】严格的白名单机制
    # eess.SP: Signal Processing (最核心)
    # eess.AS: Audio and Speech Processing (核心)
    # cs.SD: Sound (核心)
    # cs.IT: Information Theory (部分相关)
    # cs.LG: Machine Learning (仅当内容确实相关时，由关键词保证)
    # 移除了: stat (统计学，避免医学统计), physics (避免量子/纯物理), math (太宽泛)
    
    target_fields = ["eess.SP", "eess.AS", "cs.SD", "cs.IT", "cs.LG", "eess.IV"]
    
    results = []
    for paper in papers:
        tags = paper.Tags
        is_target = False
        for tag in tags:
            # 检查 tag 是否在白名单中 (只要命中一个即可)
            # 比如 tag 是 "eess.SP"，它在 target_fields 里
            if tag in target_fields:
                is_target = True
                break
            # 或者是 target_fields 的子集（兼容性处理）
            for target in target_fields:
                if tag.startswith(target):
                    is_target = True
                    break
            if is_target: break
            
        if is_target:
            results.append(paper)
    return results

def get_daily_papers_by_keyword_with_retries(keyword: str, column_names: List[str], max_result: int, retries: int = 3) -> List[Dict[str, str]]:
    for i in range(retries):
        papers = get_daily_papers_by_keyword(keyword, column_names, max_result)
        if papers is not None: 
            return papers
        else:
            print(f"Retry {i+1} for {keyword}...")
            time.sleep(5)
    return []

def get_daily_papers_by_keyword(keyword: str, column_names: List[str], max_result: int) -> List[Dict[str, str]]:
    papers = request_paper_with_arXiv_api(keyword, max_result)
    if not papers:
        return [] 
        
    # 执行严格的学科过滤
    papers = filter_tags(papers)
    
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
