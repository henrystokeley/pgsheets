"""Responses from Google API for use in testing"""
import datetime

def get_spreadsheet_element(key="test_key", title="title"):
    d = datetime.datetime(2015, 7, 18)
    data = (
        '<ns0:entry xmlns:ns0="http://www.w3.org/2005/Atom">'

        '<ns0:id>https://spreadsheets.google.com/feeds/spreadsheets/'
        'private/full/{key}</ns0:id>'

        '<ns0:updated>{update_year}-{update_month:02d}-{update_day:02d}'
        'T05:29:31.140Z</ns0:updated>'

        '<ns0:category scheme="http://schemas.google.com/spreadsheets/'
        '2006" term="http://schemas.google.com/spreadsheets/'
        '2006#spreadsheet" />'

        '<ns0:title type="text">{title}</ns0:title>'

        '<ns0:content type="text">{title}</ns0:content>'

        '<ns0:link href="https://spreadsheets.google.com/feeds/worksheets/'
        '{key}/private/full" rel="http://schemas.google.com/spreadsheets/'
        '2006#worksheetsfeed" type="application/atom+xml" />'

        '<ns0:link href="https://docs.google.com/spreadsheets/d/{key}/'
        'edit" rel="alternate" type="text/html" />'

        '<ns0:link href="https://spreadsheets.google.com/feeds/'
        'spreadsheets/private/full/{key}" rel="self" '
        'type="application/atom+xml" />'

        '<ns0:author>'
        '<ns0:name>{username}</ns0:name>'
        '<ns0:email>{mail}</ns0:email>'
        '</ns0:author>'
        '</ns0:entry>'
        .format(key=key,
                mail="fake@example.com",
                username="fake",
                update_year=d.year,
                update_month=d.month,
                update_day=d.day,
                title=title))
    return data.encode()

def get_worksheet_entry(key, sheet_title, encode=True):
    open_tag = ("<entry>" if not encode else 
        "<entry xmlns='http://www.w3.org/2005/Atom'"
        " xmlns:gs='http://schemas.google.com/spreadsheets/2006'>"
        )
    content = (
        "{open_tag}"
        "<id>https://spreadsheets.google.com/feeds/worksheets/{key}/"
        "private/full/{id}</id>"
        "<updated>2015-07-18T05:29:31.112Z</updated>"
        "<category scheme='http://schemas.google.com/spreadsheets/"
        "2006' term='http://schemas.google.com/spreadsheets/2006#"
        "worksheet'/>"
        "<title type='text'>{sheet_title}</title>"
        "<content type='text'>{sheet_title}</content>"

        "<link rel='http://schemas.google.com/spreadsheets/2006#"
        "listfeed' type='application/atom+xml' href='https://spreadshe"
        "ets.google.com/feeds/list/{key}/{id}/private/full'/>"
        "<link rel='http://schemas.google.com/spreadsheets/2006#"
        "cellsfeed' type='application/atom+xml' href='https://"
        "spreadsheets.google.com/feeds/cells/{key}/{id}/private/full'/>"
        "<link rel='http://schemas.google.com/visualization/2008#"
        "visualizationApi' type='application/atom+xml' href='"
        "https://docs.google.com/spreadsheets/d/{key}/gviz/tq?gid=0'/>"
        "<link rel='http://schemas.google.com/spreadsheets/2006#"
        "exportcsv' type='text/csv' href='https://docs.google.com/"
        "spreadsheets/d/{key}/export?gid=0&amp;format=csv'/>"
        "<link rel='self' type='application/atom+xml' href='https://"
        "spreadsheets.google.com/feeds/worksheets/{key}/private/full/"
        "{id}'/>"
        "<link rel='edit' type='application/atom+xml' href='"
        "https://spreadsheets.google.com/feeds/worksheets/{key}/"
        "private/full/{id}/{version}'/>"
        "<gs:colCount>{col_count}</gs:colCount>"
        "<gs:rowCount>{row_count}</gs:rowCount>"
        "</entry>"
        .format(open_tag=open_tag, key=key, col_count=2, row_count=2,
                sheet_title=sheet_title, id="od6", version="CCCC")
        )
    
    return content.encode() if encode else content

def get_worksheets_feed(key, sheet_names=["title"]):
    entries = "".join(get_worksheet_entry(key, t, encode=False) for t in sheet_names)

    d = datetime.datetime(2015, 7, 18)
    data = (
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<feed xmlns='http://www.w3.org/2005/Atom'"
        " xmlns:openSearch='http://a9.com/-/spec/opensearchrss/1.0/'"
        " xmlns:gs='http://schemas.google.com/spreadsheets/2006'>"

        "<id>https://spreadsheets.google.com/feeds/worksheets/{key}/"
        "private/full</id>"
        '<updated>{update_year}-{update_month:02d}-{update_day:02d}'
        'T05:29:31.140Z</updated>'
        "<category scheme='http://schemas.google.com/spreadsheets/2006' "
        "term='http://schemas.google.com/spreadsheets/2006#worksheet'/>"
        "<title type='text'>{title}</title>"

        "<link rel='alternate' type='application/atom+xml' href='"
        "https://docs.google.com/spreadsheets/d/{key}/edit'/>"
        "<link rel='http://schemas.google.com/g/2005#feed' type="
        "'application/atom+xml' href='https://spreadsheets.google.com/"
        "feeds/worksheets/{key}/private/full'/>"
        "<link rel='http://schemas.google.com/g/2005#post' type='"
        "application/atom+xml' href='https://spreadsheets.google.com/feeds"
        "/worksheets/{key}/private/full'/>"
        "<link rel='self' type='application/atom+xml' href='https://"
        "spreadsheets.google.com/feeds/worksheets/{key}/private/full'/>"

        "<author>"
        "<name>{username}</name>"
        "<email>{mail}</email>"
        "</author>"

        "<openSearch:totalResults>{results}</openSearch:totalResults>"
        "<openSearch:startIndex>1</openSearch:startIndex>"

        "{entries}"

        "</feed>"
        .format(key=key,
                mail="fake@example.com",
                username="fake",
                update_year=d.year,
                update_month=d.month,
                update_day=d.day,
                title="title",
                entries=entries,
                results=len(sheet_names)))
    return data.encode()
