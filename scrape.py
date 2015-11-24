# -*- coding: utf-8 -*-
import re
from lxml import html
import requests
from difflib import SequenceMatcher as sm
import cPickle as pickle

link_pattern = re.compile(".*_.*\.htm")
section_pattern = re.compile("(\d)\.")
money_pattern = re.compile(u"£([\d,]+)")
hours_pattern = re.compile("([\d\.]+) hrs")

mp_pattern = re.compile(".+,.+")


def get_page_tree(url):
    page = requests.get(url, timeout=360)
    tree = html.fromstring(page.content)
    return tree


def get_money(text):
    matches = money_pattern.search(text)
    # print text
    # print matches
    money = 0
    if matches:
        groups = matches.groups()
        money = float(groups[-1].replace(',', ''))
    return money


def get_hours(text):
    matches = hours_pattern.search(text)
    # print text
    # print matches
    hours = 0
    if matches:
        groups = matches.groups()
        for group in groups:
            hours += float(group)
    return hours


def get_interests(url):
    # print html.tostring(page_tree, pretty_print=True)
    try:
        with open(url) as f:
            page_tree = html.fromstring(f.read())
    except:
        page_url = base_url + url
        page_tree = get_page_tree(page_url)
        with open(url, "w") as f:
            f.write(html.tostring(page_tree, pretty_print=True))

    headings = page_tree.xpath('//strong')

    print url

    interests = {}
    for heading in headings:
        if not heading.text:
            continue
        match = section_pattern.search(heading.text)
        # print match
        # print heading.text
        if match:
            n = match.group(1)
            # print "SCECTION %s" % n
            element = heading.getparent().getnext()
            # print heading
            # print html.tostring(element, pretty_print=True)
            money = 0
            hours = 0
            full_text = ""
            while element.tag == 'p' and element.text:
                text = html.tostring(element, method='text', encoding='UTF-8')
                money += get_money(text)
                hours += get_hours(text)
                full_text += text + "\n"
                element = element.getnext()

            interests[n] = {'money': money, 'hours': hours, 'text': full_text.replace('"', "'")}



    return interests


# print heading.text


base_url = "http://www.publications.parliament.uk/pa/cm/cmregmem/151109/"


def get_members_interests(url):
    tree = get_page_tree(url)

    elements = tree.xpath('//p/a')

    members = []
    for e in elements:
        if link_pattern.match(e.attrib['href']):
            url = e.attrib['href']
            member = url.replace("_", " ").replace(".htm", "")
            interests = get_interests(url)
            # members.append({'member' : url, 'interests' : interests })
            yield {'member': member, 'interests': interests , "party": get_party(member), "url": base_url+url}

    # print members

def get_party(member):
    if member in members_party:
        return members_party[member]
    else :
        max_score = 0
        for m, party in members_party.items():
            score = sm(None, member, m).ratio()
            if score > max_score:
                max_score = score
                closest = m
        return members_party[m]


def to_csv(data):
    with open('output.csv', 'wr') as w:
        headers = ['member', "party", "url"] + [str(n) + "_money" for n in range(1,11)] + [str(n) + "_hours" for n in range(1,11)] + [str(n) + "_text" for n in range(1,11)]

        w.write(",".join(headers)+"\n")
        for datum in data:
            line = [datum['member'], datum['party'], datum['url']] + [""] * 30
            for i in range(1,11):
                if str(i) in datum['interests'] :
                    line[i+2] = datum['interests'][str(i)]['money']
            for i in range(1,11):
                if str(i) in datum['interests'] :
                    line[i+12] = datum['interests'][str(i)]['hours']
            for i in range(1,11):
                if str(i) in datum['interests'] :
                    line[i+22] = '"' + datum['interests'][str(i)]['text'] + '"'
            w.write(",".join([str(item) for item in line])+"\n")


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
            # print member, party
        # print members
        with open("members.pickle", 'w') as f:
            pickle.dump(members, f)

        return members


if __name__ == "__main__":
    url = base_url + "part1contents.htm"
    global members_party
    members_party = get_members_party()
    to_csv(get_members_interests(url))

# print index
