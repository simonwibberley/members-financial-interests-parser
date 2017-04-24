# -*- coding: utf-8 -*-
import re
import os
from lxml import html
from lxml.html.soupparser import fromstring
import requests
from difflib import SequenceMatcher as sm
import pickle
from bs4 import BeautifulSoup

numbers = {
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10
}


link_pattern = re.compile(".*_.*\.htm")
section_pattern = re.compile("(\d)\.")
money_pattern = re.compile(u"£([\d,]+)")
hours_pattern = re.compile("([\d\.]+) hrs")

mp_pattern = re.compile(".+,.+")


def get_page_tree(url):
    page = requests.get(url, timeout=360)
    tree = fromstring(page.content)
    return tree


def get_money(text):
    matches = money_pattern.findall(text)
    # print(text)
    # print(matches)
    money = 0
    if matches:
        for match in matches:
            money += float(match.replace(',', ''))
    return money


def get_hours(text):
    matches = hours_pattern.findall(text)
    # print(text)
    # print(matches)
    hours = 0
    if matches:
        for match in matches:
            hours += float(match)
    return hours


def get_interests(url, year):
    # print(html.tostring(page_tree, pretty_print=True))
    path = year + os.sep + url
    try:
        with open(path) as f:
            page_tree = fromstring(f.read())
    except:
        page_url = base_url + url
        page_tree = get_page_tree(page_url)
        with open(path, "w") as f:
            out = html.tostring(page_tree, pretty_print=True, encoding='UTF-8').decode("utf-8")
            #print(out)
            f.write(out)

    headings = page_tree.xpath('//strong')

    print(url)

    interests = {}
    for heading in headings:
        if not heading.text:
            continue
        match = section_pattern.search(heading.text)
        # print(match)
        # print(heading.text)
        if match:
            n = match.group(1)
            # print("SCECTION %s" % n)
            element = heading.getparent().getnext()
            # print(heading)
            # print(html.tostring(element, pretty_print=True))
            money = 0
            hours = 0
            full_text = ""
            while element != None and element.tag == 'p' and element.text:
                text = html.tostring(element, method='text', encoding='UTF-8').decode("utf-8")
                money += get_money(text)
                hours += get_hours(text)
                full_text += text + "\n"
                element = element.getnext()
                if n == "6":
                    properties = parse_properties(text)
                    money += properties


            interests[n] = {'money': money, 'hours': hours, 'text': full_text.replace('"', "'")}



    return interests


def parse_properties(text) :
    total = 0;
    for line in text.split("\n"):
        line = line.strip().lower()
        if line:
            count = sum([int(val) for num, val in numbers.items() if re.match(r'\b'+num+r'\b', line)])
            if count == 0:
                count = 1
            total += count
    return total


def get_members_interests(url, year):
    tree = get_page_tree(url)

    elements = tree.xpath('//p/a')

    members = {}
    for e in elements:
        if link_pattern.match(e.attrib['href']):
            url = e.attrib['href']
            member = url.replace("_", " ").replace(".htm", "")
            data = get_interests(url, year)
            data['url'] = url
            members[member] = data
            #yield {'member': member, 'interests': data, "party": get_party(member), "url": base_url+url}

    for member, party in members_party.items():
        data = get_entry(member, members)
        yield {'member': member, 'interests': data, "party": party, "url": base_url+url}

    # print(members)

def get_entry(member, data):
    if member in data:
        return data[member]
    else :
        max_score = 0
        for m, _ in data.items():
            score = sm(None, member, m).ratio()
            if score > max_score:
                max_score = score
                closest = m
        return data[closest]


def to_csv(data, year):
    with open(year + '.csv', 'w') as w:
        headers = ['member', "party", "url"] + [str(n) + "_money" for n in range(1,11)] + [str(n) + "_hours" for n in range(1,11)] + [str(n) + "_text" for n in range(1,11)]

        w.write(",".join(headers)+"\n")
        for datum in data:
            line = [datum['member'], datum['party'], datum['url']] + [""] * 30
            for i in range(1,11):
                if str(i) in datum['interests'] :
                    line[i+2] = datum['interests'][str(i)]['money']
                else :
                    line[i + 2] = 0
            for i in range(1,11):
                if str(i) in datum['interests'] :
                    line[i+12] = datum['interests'][str(i)]['hours']
                else :
                    line[i + 12] = 0
            for i in range(1,11):
                if str(i) in datum['interests'] :
                    line[i+22] = '"' + datum['interests'][str(i)]['text'] + '"'
            w.write(",".join([str(item).replace(',', '') for item in line])+"\n")


def get_members_party():
    try :
        with open("members.pickle") as f:
            return pickle.load(f)
    except:
        tree = get_page_tree("http://www.parliament.uk/mps-lords-and-offices/mps/")
        elements = [el for el in tree.xpath("//td/a") if mp_pattern.match(el.text)]
        members = {}
        for element in elements:
            member = element.text.lower().replace(",", " ")
            member = re.sub(r" +", " ", member)
            party = element.tail.strip()
            members[member] = party
            # print(member, party)
        # print(members)
        with open("members.pickle", 'wb') as f:
            pickle.dump(members, f)

        return members

# print(heading.text)
base_urls = [
    # { 'year' : "2010-12", 'url' : "https://www.publications.parliament.uk/pa/cm/cmregmem/120430/", "listing" : "part1contents.htm"},
    # { 'year' : "2012-13", 'url' : "https://www.publications.parliament.uk/pa/cm/cmregmem/130507/", "listing" : "part1contents.htm"},
    # { 'year' : "2013-14", 'url' : "https://www.publications.parliament.uk/pa/cm/cmregmem/140602/", "listing" : "part1contents.htm"},
    # { 'year' : "2014-15", 'url' : "https://www.publications.parliament.uk/pa/cm/cmregmem/150330/", "listing" : "part1contents.htm"},
    { 'year' : "2015-16", 'url' : "https://www.publications.parliament.uk/pa/cm/cmregmem/160516/", "listing" : "contents.htm"},
    { 'year' : "2016-17", 'url' : "https://www.publications.parliament.uk/pa/cm/cmregmem/170410/", "listing" : "contents.htm"}

]
#base_url = "http://www.publications.parliament.uk/pa/cm/cmregmem/151109/"
base_url = "https://www.publications.parliament.uk/pa/cm/cmregmem/170410/"


if __name__ == "__main__":
    global members_party
    for entry in base_urls:

        base_url = entry['url']
        listing = entry['listing']
        year = entry['year']

        url = base_url + listing

        members_party = get_members_party()

        if not os.path.exists(year):
            os.mkdir(year)
        data = get_members_interests(url, year)
        to_csv(data, year)

# print(index)
