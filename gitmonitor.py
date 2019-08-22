#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Github Monitor Server (python2.7.*)
~~~~~~~~~~~~~~~~~~

Github中关键字内容(code)和关键字关联内容用户的匹配查询，附带导出结果功能。

包含内容：
1、gmServer.py      主程序）
2、config.ini      （配置文件）
3、requirements.txt（依赖库）

usage:

    python gmServer.py


Author:

    amm907

"""

import os
import time
import requests
import traceback
import ConfigParser
from json import loads
from datetime import datetime as dt
from pynput.keyboard import Listener, Key


class GithubMonitor(object):
    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read('config.ini')
        self.access_token = config.get('ACCESS_TOKEN', 'access_token')
        self.keyword_sp = config.get('KEYWORD', 'users_key')
        self.keyword_sc = config.get('KEYWORD', 'key')
        self.mark = config.getint('INTOFILE', 'mark')

    def get_users(self, at):
        page = 1
        pages = 2
        print_user_list = []

        # 输出关联库结果
        print "1.USERS: users_key:{keyword} | Users_key in these Users: "\
            .format(keyword=self.keyword_sp)
        keyword_sp = self.keyword_sp.replace(",", ".")

        while page < pages:
            url_sp = "https://api.github.com/search/code?q={keyword}" \
                     "&page={page}&per_page=100" \
                     "&access_token={at}" \
                     .format(keyword=keyword_sp, page=page, at=at)
            try:
                resp_sp = requests.get(url_sp)
            except:
                print traceback.format_exc()
                print url_sp
            resp_sp = _exceed_limit(url_sp, resp_sp)
            content_sp = loads(resp_sp.content)

            # 计算库总数
            try:
                total_count = content_sp["total_count"]
            except:
                print ur"\\\\\\\\ INFO: 查询量超出限制，结果只有前一千行可用。剩余内容不继续查询，可以手动处理: " \
                      u"users_key({user}) ////////"\
                    .format(user=keyword_sp)
                break

            pages = total_count / 100 + 2
            page += 1

            # 列出关键字匹配的库
            items = content_sp["items"]
            for item in items:
                print_user_list.append(item["repository"]["full_name"].split('/')[0])

        print_user_list2 = list(set(print_user_list))
        print_user_list2.sort(key=print_user_list.index)

        # 输出库总数
        # print "1.REPOS: keyword:{keyword} | repos_total_count:{tc}"\
        #     .format(num=num, keyword=keyword_sp, tc=len(print_user_list2))

        for user in print_user_list2:
            print user

        # 输出user总数
        print "1.SUM.USERS: ========= USERS_KEY:{keyword} ========= total_count:{tc}\n" \
            .format(keyword=self.keyword_sp, tc=len(print_user_list2))

        return print_user_list2

    def key_in_users(self, code, at):
        num = 0
        url_list = []
        name_repo_result = []
        total_code_count = 0
        code_repo_count = 0
        keyword_sc = code.replace(",", ".")

        # 输出每个code在每个repo匹配的内容
        print ">>> CODE:{keyword_sc} in USERS(keyword):{keyword_sp}"\
            .format(keyword_sc=code, keyword_sp=self.keyword_sp)
        name_user_list = self.get_users(at)

        # 输出link结果
        print "2.CODES: code:({keyword}) | Codes in these Links: "\
            .format(keyword=code)

        for name_repo in name_user_list:
            page = 1
            pages = 2
            num += 1

            while page < pages:
                url_sc = "https://api.github.com/search/code?q={keyword}+user:{name_repo}" \
                         "&page={page}&per_page=100" \
                         "&access_token={at}" \
                         .format(keyword=keyword_sc, name_repo=name_repo, page=page, at=at)
                try:
                    resp_sc = requests.get(url_sc)
                except:
                    print traceback.format_exc()
                    print url_sc
                resp_sc = _exceed_limit(url_sc, resp_sc)
                content_sc = loads(resp_sc.content)

                # 计算结果链接总数
                try:
                    code_repo_count = content_sc["total_count"]
                except:
                    print ur"\\\\\\\\ INFO: 查询量超出限制，结果只有前一千行可用。剩余内容不继续查询，可以手动处理: " \
                          u"code({keyword_sc}) repos({name_repo}) ////////"\
                        .format(keyword_sc=keyword_sc, name_repo=name_repo)
                    break

                pages = code_repo_count / 100 + 2
                page += 1

                # 输出每个库中匹配的结果数目
                if page == 2:
                    print "2.{num}.CODES: code({keyword_sc}) in user({name_repo}) | links_total_count:{crc}"\
                        .format(num=num, keyword_sc=code, name_repo=name_repo, crc=code_repo_count)

                # 列出每个结果的链接，收集用户名/资产（去重）
                n = 0
                items = content_sc["items"]
                for item in items:
                    item_url = item["html_url"]
                    name_repo_result.append(item["repository"]["full_name"].split('/')[0])
                    # 去重，输出链接
                    if n == 0:
                        url_list.append(item_url)
                        print item_url
                        n += 1
                        continue
                    if os.path.split(url_list[-1])[0] != os.path.split(item_url)[0]:
                        url_list.append(item_url)
                        print item_url
                    n += 1
            total_code_count += code_repo_count

        name_repo_result2 = list(set(name_repo_result))
        name_repo_result2.sort(key=name_repo_result.index)

        # 输出link总数
        print "2.SUM.CODES: ========= CODE:{keyword_sc} IN USERS(keyword):{keyword_sp} ========= total_count:{tc} \n"\
            .format(keyword_sc=keyword_sc, keyword_sp=self.keyword_sp, tc=total_code_count)

        return name_repo_result2, url_list

    def detect(self):
        """检测关键字是否有匹配。"""
        repos_dir = str(dt.now())[:19].replace("-", "").replace(" ", "").replace(":", "")
        keyword_sc = self.keyword_sc.split("|")
        for code in keyword_sc:

            name_user_list, result = self.key_in_users(code, self.access_token)
            print "3.{option} Codes({keyword_sc}) in these Users:" \
                .format(option="Output, please wait..." if self.mark else "SHOWING Users.", keyword_sc=code)
            for name_repo in name_user_list:
                print name_repo
            if self.mark == 1:
                self._into_file(repos_dir, code, result)
            print "3.SUM.USERS: ========= TOTAL USERS ========= total_count:{tc}\n\n".format(tc=len(name_user_list))

    def _into_file(self, repos_dir, code, url_list):
        """输出结果到文件。关键字组合-时间。"""
        print "3.INTOFILE: ./{code}={nt}={dir}.txt".format(code=self.keyword_sc.replace('|', '_or_'), nt=self.keyword_sp, dir=repos_dir)
        with open("./{code}={nt}={dir}.txt".format(code=self.keyword_sc.replace('|', '_or_'), nt=self.keyword_sp, dir=repos_dir),
                  "ab") as f:
            f.write(code+":\n")
            for url in url_list:
                f.write(url+"\n")
            f.write("\n\n")


def _deduplicat(url_list):
    """按key把链接去重。(暂时没用上)"""
    num = 0
    result = []
    for i in url_list:
        # 第一条必加
        if num == 0:
            result.append(i)
            num += 1
            continue
        # 第二条起，每条与上一条比较-最后一级之前的路径
        if os.path.split(url_list[num-1])[0] != os.path.split(i)[0]:
            result.append(i)
        num += 1
    return result


def _exceed_limit(url, resp):
    """若超出查询量上限(30/min)，暂停5秒后重新运行。"""
    while ("API rate limit exceeded for user" in resp.content) or \
            ("You have triggered an abuse detection mechanism" in resp.content):
        time.sleep(5)
        resp = requests.get(url)
    return resp


def _exit(key):
    """按Esc退出系统。"""
    if key == Key.esc:
        exit(0)


def main():
    a = 1
    github_monitor = GithubMonitor()
    github_monitor.detect()
    print "All Done! Press ESC for exit."
    # 监听输入esc关闭程序
    with Listener(on_press=_exit) as listener:
        listener.join()


if __name__ == '__main__':
    main()
