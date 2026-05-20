"""
Kentucky 2026 Democratic Senate Primary — Live Results Tracker
Data source: NPR/AP via apps.npr.org
Run:     streamlit run app.py
"""

import streamlit as st
import requests
import pandas as pd
import re
import time
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
COUNTIES_URL  = "https://apps.npr.org/primary-election-results-2026/data/KY_S_5_19_2026_counties.json"
STATEWIDE_URL = "https://apps.npr.org/primary-election-results-2026/data/KY_S_5_19_2026.json"
AUTO_REFRESH  = 60
REQUEST_TIMEOUT = 15

CAND_KEYS = ["McGrath", "Booker", "Stevenson", "Romans", "Forsythe", "Blanton", "Thompson"]

# ─────────────────────────────────────────────
# KENTUCKY FIPS → COUNTY NAME
# ─────────────────────────────────────────────
KY_FIPS = {
    "21001":"Adair","21003":"Allen","21005":"Anderson","21007":"Ballard","21009":"Barren",
    "21011":"Bath","21013":"Bell","21015":"Boone","21017":"Bourbon","21019":"Boyd",
    "21021":"Boyle","21023":"Bracken","21025":"Breathitt","21027":"Breckinridge","21029":"Bullitt",
    "21031":"Butler","21033":"Caldwell","21035":"Calloway","21037":"Campbell","21039":"Carlisle",
    "21041":"Carroll","21043":"Carter","21045":"Casey","21047":"Christian","21049":"Clark",
    "21051":"Clay","21053":"Clinton","21055":"Crittenden","21057":"Cumberland","21059":"Daviess",
    "21061":"Edmonson","21063":"Elliott","21065":"Estill","21067":"Fayette","21069":"Fleming",
    "21071":"Floyd","21073":"Franklin","21075":"Fulton","21077":"Gallatin","21079":"Garrard",
    "21081":"Grant","21083":"Graves","21085":"Grayson","21087":"Green","21089":"Greenup",
    "21091":"Hancock","21093":"Hardin","21095":"Harlan","21097":"Harrison","21099":"Hart",
    "21101":"Henderson","21103":"Henry","21105":"Hickman","21107":"Hopkins","21109":"Jackson",
    "21111":"Jefferson","21113":"Jessamine","21115":"Johnson","21117":"Kenton","21119":"Knott",
    "21121":"Knox","21123":"Larue","21125":"Laurel","21127":"Lawrence","21129":"Lee",
    "21131":"Leslie","21133":"Letcher","21135":"Lewis","21137":"Lincoln","21139":"Livingston",
    "21141":"Logan","21143":"Lyon","21145":"Madison","21147":"Magoffin","21149":"Marion",
    "21151":"Marshall","21153":"Martin","21155":"Mason","21157":"McCracken","21159":"McCreary",
    "21161":"McLean","21163":"Meade","21165":"Menifee","21167":"Mercer","21169":"Metcalfe",
    "21171":"Monroe","21173":"Montgomery","21175":"Morgan","21177":"Muhlenberg","21179":"Nelson",
    "21181":"Nicholas","21183":"Ohio","21185":"Oldham","21187":"Owen","21189":"Owsley",
    "21191":"Pendleton","21193":"Perry","21195":"Pike","21197":"Powell","21199":"Pulaski",
    "21201":"Robertson","21203":"Rockcastle","21205":"Rowan","21207":"Russell","21209":"Scott",
    "21211":"Shelby","21213":"Simpson","21215":"Spencer","21217":"Taylor","21219":"Todd",
    "21221":"Trigg","21223":"Trimble","21225":"Union","21227":"Warren","21229":"Washington",
    "21231":"Wayne","21233":"Webster","21235":"Whitley","21237":"Wolfe","21239":"Woodford",
}

# ─────────────────────────────────────────────
# COUNTY → PAGE-ID MAPPING  (alphabetical, IDs 3-122)
# ─────────────────────────────────────────────
COUNTY_IDS = {
    "Adair":3,"Allen":4,"Anderson":5,"Ballard":6,"Barren":7,"Bath":8,"Bell":9,
    "Boone":10,"Bourbon":11,"Boyd":12,"Boyle":13,"Bracken":14,"Breathitt":15,
    "Breckinridge":16,"Bullitt":17,"Butler":18,"Caldwell":19,"Calloway":20,
    "Campbell":21,"Carlisle":22,"Carroll":23,"Carter":24,"Casey":25,
    "Christian":26,"Clark":27,"Clay":28,"Clinton":29,"Crittenden":30,
    "Cumberland":31,"Daviess":32,"Edmonson":33,"Elliott":34,"Estill":35,
    "Fayette":36,"Fleming":37,"Floyd":38,"Franklin":39,"Fulton":40,
    "Gallatin":41,"Garrard":42,"Grant":43,"Graves":44,"Grayson":45,
    "Green":46,"Greenup":47,"Hancock":48,"Hardin":49,"Harlan":50,
    "Harrison":51,"Hart":52,"Henderson":53,"Henry":54,"Hickman":55,
    "Hopkins":56,"Jackson":57,"Jefferson":58,"Jessamine":59,"Johnson":60,
    "Kenton":61,"Knott":62,"Knox":63,"Larue":64,"Laurel":65,"Lawrence":66,
    "Lee":67,"Leslie":68,"Letcher":69,"Lewis":70,"Lincoln":71,"Livingston":72,
    "Logan":73,"Lyon":74,"Madison":75,"Magoffin":76,"Marion":77,"Marshall":78,
    "Martin":79,"Mason":80,"McCracken":81,"McCreary":82,"McLean":83,"Meade":84,
    "Menifee":85,"Mercer":86,"Metcalfe":87,"Monroe":88,"Montgomery":89,
    "Morgan":90,"Muhlenberg":91,"Nelson":92,"Nicholas":93,"Ohio":94,
    "Oldham":95,"Owen":96,"Owsley":97,"Pendleton":98,"Perry":99,"Pike":100,
    "Powell":101,"Pulaski":102,"Robertson":103,"Rockcastle":104,"Rowan":105,
    "Russell":106,"Scott":107,"Shelby":108,"Simpson":109,"Spencer":110,
    "Taylor":111,"Todd":112,"Trigg":113,"Trimble":114,"Union":115,"Warren":116,
    "Washington":117,"Wayne":118,"Webster":119,"Whitley":120,"Wolfe":121,
    "Woodford":122,
}

# ─────────────────────────────────────────────
# COUNTY DEMOGRAPHIC DATA  (2020 Census ACS estimates)
# white_pct, black_pct, rural_pct, suburban_pct, urban_pct, college_pct
# ─────────────────────────────────────────────
COUNTY_DEMOS = {
    "Adair":{"white_pct":97.2,"black_pct":1.2,"rural_pct":82,"suburban_pct":5,"urban_pct":13,"college_pct":14.5},
    "Allen":{"white_pct":96.8,"black_pct":1.4,"rural_pct":78,"suburban_pct":6,"urban_pct":16,"college_pct":13.2},
    "Anderson":{"white_pct":95.2,"black_pct":2.1,"rural_pct":52,"suburban_pct":30,"urban_pct":18,"college_pct":22.8},
    "Ballard":{"white_pct":96.1,"black_pct":2.8,"rural_pct":76,"suburban_pct":5,"urban_pct":19,"college_pct":12.1},
    "Barren":{"white_pct":95.8,"black_pct":2.8,"rural_pct":58,"suburban_pct":10,"urban_pct":32,"college_pct":17.4},
    "Bath":{"white_pct":97.3,"black_pct":0.8,"rural_pct":83,"suburban_pct":5,"urban_pct":12,"college_pct":11.8},
    "Bell":{"white_pct":97.8,"black_pct":0.7,"rural_pct":75,"suburban_pct":5,"urban_pct":20,"college_pct":11.2},
    "Boone":{"white_pct":92.8,"black_pct":2.4,"rural_pct":10,"suburban_pct":82,"urban_pct":8,"college_pct":38.2},
    "Bourbon":{"white_pct":90.1,"black_pct":5.8,"rural_pct":56,"suburban_pct":12,"urban_pct":32,"college_pct":23.1},
    "Boyd":{"white_pct":96.2,"black_pct":1.8,"rural_pct":22,"suburban_pct":20,"urban_pct":58,"college_pct":20.4},
    "Boyle":{"white_pct":88.2,"black_pct":7.4,"rural_pct":35,"suburban_pct":20,"urban_pct":45,"college_pct":28.9},
    "Bracken":{"white_pct":97.8,"black_pct":0.8,"rural_pct":80,"suburban_pct":8,"urban_pct":12,"college_pct":13.4},
    "Breathitt":{"white_pct":98.2,"black_pct":0.5,"rural_pct":88,"suburban_pct":2,"urban_pct":10,"college_pct":9.8},
    "Breckinridge":{"white_pct":97.2,"black_pct":1.1,"rural_pct":74,"suburban_pct":8,"urban_pct":18,"college_pct":12.8},
    "Bullitt":{"white_pct":96.4,"black_pct":1.2,"rural_pct":25,"suburban_pct":67,"urban_pct":8,"college_pct":22.4},
    "Butler":{"white_pct":97.8,"black_pct":0.8,"rural_pct":79,"suburban_pct":5,"urban_pct":16,"college_pct":11.6},
    "Caldwell":{"white_pct":91.2,"black_pct":6.8,"rural_pct":58,"suburban_pct":8,"urban_pct":34,"college_pct":16.2},
    "Calloway":{"white_pct":95.8,"black_pct":1.8,"rural_pct":44,"suburban_pct":12,"urban_pct":44,"college_pct":32.4},
    "Campbell":{"white_pct":93.2,"black_pct":3.1,"rural_pct":8,"suburban_pct":18,"urban_pct":74,"college_pct":32.1},
    "Carlisle":{"white_pct":94.8,"black_pct":3.2,"rural_pct":78,"suburban_pct":5,"urban_pct":17,"college_pct":11.8},
    "Carroll":{"white_pct":93.2,"black_pct":2.8,"rural_pct":62,"suburban_pct":12,"urban_pct":26,"college_pct":14.4},
    "Carter":{"white_pct":97.8,"black_pct":0.8,"rural_pct":72,"suburban_pct":5,"urban_pct":23,"college_pct":12.8},
    "Casey":{"white_pct":98.4,"black_pct":0.6,"rural_pct":86,"suburban_pct":2,"urban_pct":12,"college_pct":11.2},
    "Christian":{"white_pct":64.8,"black_pct":32.1,"rural_pct":22,"suburban_pct":12,"urban_pct":66,"college_pct":24.8},
    "Clark":{"white_pct":93.8,"black_pct":3.8,"rural_pct":34,"suburban_pct":18,"urban_pct":48,"college_pct":24.6},
    "Clay":{"white_pct":98.6,"black_pct":0.4,"rural_pct":88,"suburban_pct":2,"urban_pct":10,"college_pct":9.4},
    "Clinton":{"white_pct":98.4,"black_pct":0.4,"rural_pct":84,"suburban_pct":2,"urban_pct":14,"college_pct":11.8},
    "Crittenden":{"white_pct":97.8,"black_pct":0.8,"rural_pct":74,"suburban_pct":5,"urban_pct":21,"college_pct":12.4},
    "Cumberland":{"white_pct":97.6,"black_pct":1.4,"rural_pct":82,"suburban_pct":2,"urban_pct":16,"college_pct":12.8},
    "Daviess":{"white_pct":92.8,"black_pct":4.8,"rural_pct":18,"suburban_pct":18,"urban_pct":64,"college_pct":24.2},
    "Edmonson":{"white_pct":97.8,"black_pct":0.5,"rural_pct":82,"suburban_pct":5,"urban_pct":13,"college_pct":12.4},
    "Elliott":{"white_pct":99.2,"black_pct":0.2,"rural_pct":96,"suburban_pct":1,"urban_pct":3,"college_pct":8.4},
    "Estill":{"white_pct":98.2,"black_pct":0.4,"rural_pct":72,"suburban_pct":5,"urban_pct":23,"college_pct":11.2},
    "Fayette":{"white_pct":75.4,"black_pct":14.8,"rural_pct":2,"suburban_pct":12,"urban_pct":86,"college_pct":44.8},
    "Fleming":{"white_pct":97.8,"black_pct":0.8,"rural_pct":78,"suburban_pct":5,"urban_pct":17,"college_pct":12.1},
    "Floyd":{"white_pct":98.4,"black_pct":0.4,"rural_pct":84,"suburban_pct":3,"urban_pct":13,"college_pct":12.8},
    "Franklin":{"white_pct":85.8,"black_pct":10.8,"rural_pct":14,"suburban_pct":18,"urban_pct":68,"college_pct":35.2},
    "Fulton":{"white_pct":60.4,"black_pct":38.4,"rural_pct":64,"suburban_pct":5,"urban_pct":31,"college_pct":13.8},
    "Gallatin":{"white_pct":96.4,"black_pct":1.2,"rural_pct":64,"suburban_pct":22,"urban_pct":14,"college_pct":15.8},
    "Garrard":{"white_pct":96.8,"black_pct":1.4,"rural_pct":66,"suburban_pct":12,"urban_pct":22,"college_pct":17.4},
    "Grant":{"white_pct":96.2,"black_pct":1.2,"rural_pct":58,"suburban_pct":24,"urban_pct":18,"college_pct":15.8},
    "Graves":{"white_pct":88.8,"black_pct":7.8,"rural_pct":46,"suburban_pct":10,"urban_pct":44,"college_pct":17.4},
    "Grayson":{"white_pct":97.4,"black_pct":0.8,"rural_pct":72,"suburban_pct":8,"urban_pct":20,"college_pct":13.2},
    "Green":{"white_pct":96.8,"black_pct":1.8,"rural_pct":78,"suburban_pct":5,"urban_pct":17,"college_pct":14.2},
    "Greenup":{"white_pct":97.8,"black_pct":0.6,"rural_pct":44,"suburban_pct":22,"urban_pct":34,"college_pct":18.4},
    "Hancock":{"white_pct":97.8,"black_pct":0.8,"rural_pct":66,"suburban_pct":12,"urban_pct":22,"college_pct":13.8},
    "Hardin":{"white_pct":82.8,"black_pct":9.8,"rural_pct":24,"suburban_pct":28,"urban_pct":48,"college_pct":28.4},
    "Harlan":{"white_pct":97.8,"black_pct":0.6,"rural_pct":74,"suburban_pct":5,"urban_pct":21,"college_pct":11.2},
    "Harrison":{"white_pct":94.8,"black_pct":2.8,"rural_pct":62,"suburban_pct":10,"urban_pct":28,"college_pct":17.4},
    "Hart":{"white_pct":93.2,"black_pct":4.8,"rural_pct":72,"suburban_pct":5,"urban_pct":23,"college_pct":12.8},
    "Henderson":{"white_pct":87.8,"black_pct":9.4,"rural_pct":18,"suburban_pct":12,"urban_pct":70,"college_pct":24.8},
    "Henry":{"white_pct":94.8,"black_pct":2.4,"rural_pct":62,"suburban_pct":22,"urban_pct":16,"college_pct":17.2},
    "Hickman":{"white_pct":82.4,"black_pct":14.8,"rural_pct":74,"suburban_pct":5,"urban_pct":21,"college_pct":12.8},
    "Hopkins":{"white_pct":90.4,"black_pct":6.8,"rural_pct":32,"suburban_pct":14,"urban_pct":54,"college_pct":17.8},
    "Jackson":{"white_pct":98.8,"black_pct":0.3,"rural_pct":92,"suburban_pct":2,"urban_pct":6,"college_pct":9.2},
    "Jefferson":{"white_pct":73.8,"black_pct":22.4,"rural_pct":2,"suburban_pct":8,"urban_pct":90,"college_pct":34.8},
    "Jessamine":{"white_pct":92.8,"black_pct":2.8,"rural_pct":22,"suburban_pct":58,"urban_pct":20,"college_pct":32.4},
    "Johnson":{"white_pct":98.8,"black_pct":0.4,"rural_pct":72,"suburban_pct":5,"urban_pct":23,"college_pct":13.8},
    "Kenton":{"white_pct":91.8,"black_pct":4.4,"rural_pct":6,"suburban_pct":16,"urban_pct":78,"college_pct":32.8},
    "Knott":{"white_pct":98.4,"black_pct":0.3,"rural_pct":92,"suburban_pct":2,"urban_pct":6,"college_pct":9.4},
    "Knox":{"white_pct":97.8,"black_pct":0.6,"rural_pct":68,"suburban_pct":5,"urban_pct":27,"college_pct":12.8},
    "Larue":{"white_pct":94.8,"black_pct":2.8,"rural_pct":62,"suburban_pct":14,"urban_pct":24,"college_pct":15.4},
    "Laurel":{"white_pct":97.2,"black_pct":0.8,"rural_pct":48,"suburban_pct":14,"urban_pct":38,"college_pct":17.8},
    "Lawrence":{"white_pct":98.8,"black_pct":0.3,"rural_pct":78,"suburban_pct":4,"urban_pct":18,"college_pct":11.2},
    "Lee":{"white_pct":98.8,"black_pct":0.4,"rural_pct":90,"suburban_pct":2,"urban_pct":8,"college_pct":9.8},
    "Leslie":{"white_pct":98.8,"black_pct":0.2,"rural_pct":96,"suburban_pct":1,"urban_pct":3,"college_pct":8.8},
    "Letcher":{"white_pct":97.8,"black_pct":0.4,"rural_pct":72,"suburban_pct":5,"urban_pct":23,"college_pct":14.4},
    "Lewis":{"white_pct":98.6,"black_pct":0.4,"rural_pct":84,"suburban_pct":3,"urban_pct":13,"college_pct":11.8},
    "Lincoln":{"white_pct":94.8,"black_pct":2.4,"rural_pct":68,"suburban_pct":8,"urban_pct":24,"college_pct":14.8},
    "Livingston":{"white_pct":97.4,"black_pct":0.8,"rural_pct":74,"suburban_pct":5,"urban_pct":21,"college_pct":13.4},
    "Logan":{"white_pct":87.8,"black_pct":9.8,"rural_pct":46,"suburban_pct":10,"urban_pct":44,"college_pct":17.8},
    "Lyon":{"white_pct":92.8,"black_pct":4.4,"rural_pct":68,"suburban_pct":8,"urban_pct":24,"college_pct":19.4},
    "Madison":{"white_pct":91.8,"black_pct":4.8,"rural_pct":24,"suburban_pct":12,"urban_pct":64,"college_pct":36.8},
    "Magoffin":{"white_pct":98.8,"black_pct":0.3,"rural_pct":94,"suburban_pct":1,"urban_pct":5,"college_pct":9.2},
    "Marion":{"white_pct":89.8,"black_pct":6.8,"rural_pct":62,"suburban_pct":8,"urban_pct":30,"college_pct":17.8},
    "Marshall":{"white_pct":97.4,"black_pct":0.4,"rural_pct":52,"suburban_pct":24,"urban_pct":24,"college_pct":22.8},
    "Martin":{"white_pct":99.2,"black_pct":0.2,"rural_pct":94,"suburban_pct":1,"urban_pct":5,"college_pct":8.4},
    "Mason":{"white_pct":91.8,"black_pct":4.8,"rural_pct":42,"suburban_pct":12,"urban_pct":46,"college_pct":19.8},
    "McCracken":{"white_pct":84.8,"black_pct":11.8,"rural_pct":16,"suburban_pct":18,"urban_pct":66,"college_pct":27.4},
    "McCreary":{"white_pct":98.8,"black_pct":0.3,"rural_pct":86,"suburban_pct":2,"urban_pct":12,"college_pct":9.8},
    "McLean":{"white_pct":97.8,"black_pct":0.8,"rural_pct":72,"suburban_pct":8,"urban_pct":20,"college_pct":13.4},
    "Meade":{"white_pct":88.8,"black_pct":5.4,"rural_pct":42,"suburban_pct":28,"urban_pct":30,"college_pct":21.8},
    "Menifee":{"white_pct":98.8,"black_pct":0.4,"rural_pct":90,"suburban_pct":2,"urban_pct":8,"college_pct":10.4},
    "Mercer":{"white_pct":93.8,"black_pct":3.8,"rural_pct":56,"suburban_pct":14,"urban_pct":30,"college_pct":24.8},
    "Metcalfe":{"white_pct":96.8,"black_pct":1.4,"rural_pct":78,"suburban_pct":5,"urban_pct":17,"college_pct":12.4},
    "Monroe":{"white_pct":97.8,"black_pct":0.6,"rural_pct":78,"suburban_pct":5,"urban_pct":17,"college_pct":12.8},
    "Montgomery":{"white_pct":93.8,"black_pct":2.8,"rural_pct":46,"suburban_pct":16,"urban_pct":38,"college_pct":19.4},
    "Morgan":{"white_pct":98.4,"black_pct":0.4,"rural_pct":90,"suburban_pct":2,"urban_pct":8,"college_pct":9.8},
    "Muhlenberg":{"white_pct":92.8,"black_pct":5.4,"rural_pct":52,"suburban_pct":10,"urban_pct":38,"college_pct":14.8},
    "Nelson":{"white_pct":92.8,"black_pct":4.8,"rural_pct":44,"suburban_pct":30,"urban_pct":26,"college_pct":22.8},
    "Nicholas":{"white_pct":97.4,"black_pct":1.0,"rural_pct":78,"suburban_pct":5,"urban_pct":17,"college_pct":14.4},
    "Ohio":{"white_pct":96.8,"black_pct":1.4,"rural_pct":72,"suburban_pct":8,"urban_pct":20,"college_pct":13.4},
    "Oldham":{"white_pct":91.8,"black_pct":3.4,"rural_pct":16,"suburban_pct":76,"urban_pct":8,"college_pct":47.8},
    "Owen":{"white_pct":96.8,"black_pct":1.2,"rural_pct":72,"suburban_pct":14,"urban_pct":14,"college_pct":15.8},
    "Owsley":{"white_pct":99.2,"black_pct":0.2,"rural_pct":96,"suburban_pct":1,"urban_pct":3,"college_pct":8.2},
    "Pendleton":{"white_pct":96.4,"black_pct":0.8,"rural_pct":52,"suburban_pct":32,"urban_pct":16,"college_pct":18.4},
    "Perry":{"white_pct":97.4,"black_pct":0.6,"rural_pct":62,"suburban_pct":5,"urban_pct":33,"college_pct":16.4},
    "Pike":{"white_pct":98.4,"black_pct":0.4,"rural_pct":70,"suburban_pct":8,"urban_pct":22,"college_pct":15.8},
    "Powell":{"white_pct":97.8,"black_pct":0.8,"rural_pct":72,"suburban_pct":5,"urban_pct":23,"college_pct":11.8},
    "Pulaski":{"white_pct":96.4,"black_pct":1.4,"rural_pct":44,"suburban_pct":14,"urban_pct":42,"college_pct":19.8},
    "Robertson":{"white_pct":99.4,"black_pct":0.2,"rural_pct":98,"suburban_pct":1,"urban_pct":1,"college_pct":11.8},
    "Rockcastle":{"white_pct":98.4,"black_pct":0.4,"rural_pct":80,"suburban_pct":4,"urban_pct":16,"college_pct":10.8},
    "Rowan":{"white_pct":96.8,"black_pct":0.8,"rural_pct":46,"suburban_pct":10,"urban_pct":44,"college_pct":28.4},
    "Russell":{"white_pct":97.8,"black_pct":0.6,"rural_pct":72,"suburban_pct":5,"urban_pct":23,"college_pct":13.8},
    "Scott":{"white_pct":89.8,"black_pct":4.8,"rural_pct":28,"suburban_pct":52,"urban_pct":20,"college_pct":33.4},
    "Shelby":{"white_pct":86.8,"black_pct":8.4,"rural_pct":22,"suburban_pct":62,"urban_pct":16,"college_pct":36.8},
    "Simpson":{"white_pct":82.8,"black_pct":13.8,"rural_pct":44,"suburban_pct":10,"urban_pct":46,"college_pct":22.4},
    "Spencer":{"white_pct":96.4,"black_pct":1.4,"rural_pct":38,"suburban_pct":54,"urban_pct":8,"college_pct":26.8},
    "Taylor":{"white_pct":93.8,"black_pct":3.4,"rural_pct":42,"suburban_pct":12,"urban_pct":46,"college_pct":21.8},
    "Todd":{"white_pct":72.4,"black_pct":26.8,"rural_pct":52,"suburban_pct":8,"urban_pct":40,"college_pct":15.4},
    "Trigg":{"white_pct":88.8,"black_pct":8.8,"rural_pct":66,"suburban_pct":8,"urban_pct":26,"college_pct":18.4},
    "Trimble":{"white_pct":95.8,"black_pct":1.4,"rural_pct":62,"suburban_pct":24,"urban_pct":14,"college_pct":14.8},
    "Union":{"white_pct":88.8,"black_pct":8.4,"rural_pct":52,"suburban_pct":8,"urban_pct":40,"college_pct":14.8},
    "Warren":{"white_pct":83.8,"black_pct":8.4,"rural_pct":18,"suburban_pct":12,"urban_pct":70,"college_pct":35.4},
    "Washington":{"white_pct":93.8,"black_pct":3.4,"rural_pct":66,"suburban_pct":8,"urban_pct":26,"college_pct":17.8},
    "Wayne":{"white_pct":97.4,"black_pct":0.6,"rural_pct":76,"suburban_pct":5,"urban_pct":19,"college_pct":12.4},
    "Webster":{"white_pct":94.8,"black_pct":2.8,"rural_pct":68,"suburban_pct":8,"urban_pct":24,"college_pct":14.8},
    "Whitley":{"white_pct":97.8,"black_pct":0.4,"rural_pct":62,"suburban_pct":10,"urban_pct":28,"college_pct":14.8},
    "Wolfe":{"white_pct":98.4,"black_pct":0.4,"rural_pct":94,"suburban_pct":1,"urban_pct":5,"college_pct":8.8},
    "Woodford":{"white_pct":88.8,"black_pct":6.4,"rural_pct":26,"suburban_pct":28,"urban_pct":46,"college_pct":40.4},
}

# ─────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

@st.cache_data(ttl=AUTO_REFRESH)
def fetch_all_counties():
    """Single JSON fetch from NPR/AP — replaces 120 individual SoS page fetches."""
    try:
        r = requests.get(COUNTIES_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        data = r.json()
        race = data["races"][0]
    except Exception as e:
        st.error(f"Failed to fetch NPR data: {e}")
        return {}

    results = {}
    for county_result in race.get("results", []):
        fips = county_result.get("fips", "")
        county_name = KY_FIPS.get(fips)
        if not county_name:
            continue

        # Match candidates by last name
        votes = {k: 0 for k in CAND_KEYS}
        for cand in county_result.get("candidates", []):
            last = cand.get("last", "")
            for key in CAND_KEYS:
                if key.lower() == last.lower():
                    votes[key] = cand.get("votes", 0)
                    break

        total        = county_result.get("total", sum(votes.values()))
        pct_rep      = round(county_result.get("reportingPercentage", 0.0), 1)
        precincts    = county_result.get("precincts", 0)
        reporting    = county_result.get("reporting", 0)
        complete     = (precincts > 0 and reporting >= precincts)

        row = {
            "county": county_name,
            "total": total,
            "pct_reporting": pct_rep,
            "complete": complete,
            "no_data": total == 0,
        }
        row.update(votes)
        results[county_name] = row

    return results

# ─────────────────────────────────────────────
# ANALYSIS HELPERS
# ─────────────────────────────────────────────
def safe_pct(num, denom):
    return round(num / denom * 100, 1) if denom > 0 else 0.0

def build_summary(county_data):
    """Aggregate all counties into statewide totals."""
    totals = {k: 0 for k in CAND_KEYS}
    total_votes = 0
    reporting = complete = not_started = 0

    for row in county_data.values():
        for k in CAND_KEYS:
            totals[k] += row.get(k, 0)
        total_votes += row["total"]
        if row["pct_reporting"] >= 100:
            complete += 1
        elif row["pct_reporting"] > 0:
            reporting += 1
        else:
            not_started += 1

    counties_in = complete + reporting
    pct_counties = round(counties_in / 120 * 100, 1)

    result = {
        "total_votes": total_votes,
        "margin": round(safe_pct(totals["McGrath"], total_votes) - safe_pct(totals["Booker"], total_votes), 1),
        "counties_complete": complete, "counties_reporting": reporting,
        "counties_not_started": not_started, "pct_counties": pct_counties,
    }
    for k in CAND_KEYS:
        result[f"total_{k}"] = totals[k]
        result[f"pct_{k}"] = safe_pct(totals[k], total_votes)
    return result

def build_complete_only_summary(county_data):
    """Aggregate only counties that are 100% reported."""
    filtered = {k: v for k, v in county_data.items() if v["complete"]}
    return build_summary(filtered) if filtered else None

def build_demo_table(county_data):
    """Break results down by demographic bucket."""
    DEMO_GROUPS = [
        ("WHITE > 97%",   "white_pct",    97),
        ("BLACK > 25%",   "black_pct",    25),
        ("RURAL > 70%",   "rural_pct",    70),
        ("SUBURBAN > 65%","suburban_pct", 65),
        ("URBAN > 60%",   "urban_pct",    60),
        ("COLLEGE > 25%", "college_pct",  25),
    ]
    rows = []
    for label, field, threshold in DEMO_GROUPS:
        totals = {k: 0 for k in CAND_KEYS}
        total = 0
        for county, row in county_data.items():
            demos = COUNTY_DEMOS.get(county, {})
            if demos.get(field, 0) > threshold:
                for k in CAND_KEYS:
                    totals[k] += row.get(k, 0)
                total += row["total"]
        row_out = {"CATEGORY": label, "THRESHOLD": f"{threshold}%", "Total": f"{total:,}"}
        for k in CAND_KEYS:
            row_out[k] = f"{safe_pct(totals[k], total)}%"
            row_out[f"_{k}_pct"] = safe_pct(totals[k], total)
        row_out["MARGIN"] = f"{round(row_out['_McGrath_pct'] - row_out['_Booker_pct'], 1)}%"
        rows.append(row_out)
    return rows

def build_county_df(county_data):
    rows = []
    for county, row in sorted(county_data.items()):
        r = {"COUNTY": county, "% Reporting": row["pct_reporting"], "Total": row["total"]}
        for k in CAND_KEYS:
            r[f"{k} %"] = safe_pct(row.get(k, 0), row["total"])
            r[f"{k} Votes"] = row.get(k, 0)
        rows.append(r)
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────
BLUE   = "#1a4f8a"
ORANGE = "#d04e10"
GRAY   = "#5c5c5c"
LIGHT_BLUE = "#2b76b2"

def header_html(title, color=BLUE):
    return f"""<div style="background:{color};color:white;padding:6px 12px;
        font-weight:bold;font-size:14px;text-align:center;border-radius:4px 4px 0 0;
        margin-top:16px;">{title}</div>"""

def summary_table_html(label, summary, total_votes):
    """Vertical candidate table — all 7 candidates."""
    COLORS = {
        "McGrath":   LIGHT_BLUE,
        "Booker":    ORANGE,
        "Stevenson": "#4a8a4a",
        "Romans":    "#8a4a8a",
        "Forsythe":  "#4a8a8a",
        "Blanton":   "#8a8a4a",
        "Thompson":  "#8a4a4a",
    }
    rows_html = ""
    for k in CAND_KEYS:
        votes = summary.get(f"total_{k}", 0)
        pct   = summary.get(f"pct_{k}", 0.0)
        color = COLORS.get(k, "#555")
        rows_html += (
            f'<tr><td style="padding:5px 12px;font-weight:bold;color:{color};">{k}</td>'
            f'<td style="padding:5px 12px;text-align:right;color:{color};font-weight:bold;">{pct}%</td>'
            f'<td style="padding:5px 12px;text-align:right;">{votes:,}</td></tr>'
        )
    margin = summary.get("margin", 0)
    margin_str = f"+{margin}%" if margin >= 0 else f"{margin}%"
    lead = "McGrath leads" if margin > 0 else ("Booker leads" if margin < 0 else "Tied")
    html = (
        f'<table style="width:100%;max-width:500px;border-collapse:collapse;font-size:13px;border:1px solid #ccc;margin-bottom:8px;">'
        f'<thead><tr style="background:#555;color:white;">'
        f'<th style="padding:6px 12px;text-align:left;">{label}</th>'
        f'<th style="padding:6px 12px;text-align:right;">Share</th>'
        f'<th style="padding:6px 12px;text-align:right;">Votes</th>'
        f'</tr></thead><tbody>{rows_html}'
        f'<tr style="background:#eee;font-weight:bold;">'
        f'<td style="padding:5px 12px;">TOTAL</td>'
        f'<td style="padding:5px 12px;"></td>'
        f'<td style="padding:5px 12px;text-align:right;">{total_votes:,}</td></tr>'
        f'<tr style="background:#dde;">'
        f'<td style="padding:5px 12px;font-weight:bold;">MARGIN (McGrath−Booker)</td>'
        f'<td style="padding:5px 12px;text-align:right;font-weight:bold;">{margin_str}</td>'
        f'<td style="padding:5px 12px;color:#666;">{lead}</td></tr>'
        f'</tbody></table>'
    )
    return html

# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="KY 2026 Dem Senate Primary",
        page_icon="🗳️",
        layout="wide",
    )

    # ── Custom CSS ────────────────────────────
    st.markdown("""<style>
    .block-container{padding-top:1rem!important}
    .stDataFrame{font-size:12px}
    table{font-size:13px}
    </style>""", unsafe_allow_html=True)

    # ── Title ─────────────────────────────────
    st.markdown(
        "<h2 style='text-align:center;color:#1a4f8a;margin-bottom:0'>🗳️ 2026 Kentucky Democratic Senate Primary</h2>"
        "<p style='text-align:center;color:#666;font-size:13px;margin-top:4px'>"
        "McGrath · Booker · Stevenson · Romans · Forsythe · Blanton · Thompson · Live Results via KY Secretary of State</p>",
        unsafe_allow_html=True
    )

    # ── Controls ──────────────────────────────
    col_refresh, col_last, col_spacer = st.columns([1, 2, 4])
    with col_refresh:
        if st.button("🔄 Refresh Now"):
            st.cache_data.clear()
            st.rerun()
    with col_last:
        st.markdown(f"<small>Last fetched: {datetime.now().strftime('%I:%M:%S %p ET')}</small>",
                    unsafe_allow_html=True)

    # ── Fetch data ────────────────────────────
    with st.spinner("Fetching results from all 120 counties..."):
        county_data = fetch_all_counties()

    summary   = build_summary(county_data)
    s_100     = build_complete_only_summary(county_data)

    # ── Banner numbers ───────────────────────
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Counties Reporting", f"{summary['counties_reporting'] + summary['counties_complete']} / 120")
    b2.metric("McGrath", f"{summary['pct_McGrath']}%", f"{summary['total_McGrath']:,} votes")
    b3.metric("Booker", f"{summary['pct_Booker']}%", f"{summary['total_Booker']:,} votes")
    margin_val = summary['margin']
    lead = "McGrath leads" if margin_val > 0 else ("Booker leads" if margin_val < 0 else "Tied")
    b4.metric("Margin", f"{abs(margin_val):.1f}%", lead)

    st.divider()

    # ═══════════════════════════════════════════
    # SECTION 1 — Currently Reporting (ALL)
    # ═══════════════════════════════════════════
    st.markdown(header_html("📊 Currently Reporting"), unsafe_allow_html=True)

    pct_rep_display = f"{summary['pct_counties']}%"
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""<table style="width:100%;border-collapse:collapse;font-size:13px;">
          <tr><td style="padding:4px 10px;font-weight:bold;">% of Counties Reporting</td>
              <td style="padding:4px 10px;">{pct_rep_display}</td>
              <td style="padding:4px 10px;">{pct_rep_display}</td></tr>
        </table>""", unsafe_allow_html=True)

    st.markdown(summary_table_html(
        "All Reporting Counties", summary, summary["total_votes"]
    ), unsafe_allow_html=True)

    # ═══════════════════════════════════════════
    # SECTION 2 — 100% In Only
    # ═══════════════════════════════════════════
    st.markdown(header_html("✅ Currently Reporting (100% In Counties Only)"), unsafe_allow_html=True)

    if s_100 and s_100["total_votes"] > 0:
        st.markdown(summary_table_html(
            "Complete Counties Only", s_100, s_100["total_votes"]
        ), unsafe_allow_html=True)
    else:
        st.info("No counties fully reported yet.")

    # ═══════════════════════════════════════════
    # SECTION 3 — Outstanding
    # ═══════════════════════════════════════════
    outstanding = {k: v for k, v in county_data.items()
                   if not v["complete"] and v["pct_reporting"] < 100}
    st.markdown(header_html(f"⏳ Outstanding — {len(outstanding)} Counties Not 100% In"), unsafe_allow_html=True)

    out_total = sum(v["total"] for v in outstanding.values())

    if out_total > 0:
        out_summary = build_summary(outstanding)
        st.markdown(summary_table_html(
            "Partial Counties", out_summary, out_total
        ), unsafe_allow_html=True)
    else:
        st.markdown(f"""<table style="width:60%;border-collapse:collapse;font-size:13px;margin:4px 0;">
          <tr><td style="padding:5px 10px;background:#f5f5f5;">Outstanding Counties</td>
              <td style="padding:5px 10px;text-align:center;font-weight:bold;color:#333;">
                {len(outstanding)}</td>
              <td colspan=3 style="padding:5px 10px;color:#999;">— no partial votes yet —</td></tr>
        </table>""", unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════
    # SECTION 4 — DEMOGRAPHICS
    # ═══════════════════════════════════════════
    st.markdown(header_html("🏙️ DEMOS — Vote Breakdown by County Type"), unsafe_allow_html=True)

    demo_rows = build_demo_table(county_data)
    if demo_rows and any(int(r["Total"].replace(",","")) > 0 for r in demo_rows):
        demo_display = []
        for r in demo_rows:
            mg_p = r["_McGrath_pct"]
            cb_p = r["_Booker_pct"]
            margin_d = round(mg_p - cb_p, 1)
            d = {"": r["CATEGORY"], "Total": r["Total"]}
            for k in CAND_KEYS:
                d[k] = r[k]
            d["MARGIN"] = f"+{margin_d}%" if margin_d >= 0 else f"{margin_d}%"
            demo_display.append(d)
        df_demo = pd.DataFrame(demo_display)

        def color_row(row):
            mg_val = float(row["McGrath"].replace("%",""))
            cb_val = float(row["Booker"].replace("%",""))
            lead_mg = mg_val > cb_val
            colors = [""] * len(row)
            mg_idx = df_demo.columns.get_loc("McGrath")
            cb_idx = df_demo.columns.get_loc("Booker")
            margin_idx = df_demo.columns.get_loc("MARGIN")
            colors[mg_idx] = f"color: {LIGHT_BLUE}; font-weight: bold" if lead_mg else ""
            colors[cb_idx] = f"color: {ORANGE}; font-weight: bold" if not lead_mg else ""
            colors[margin_idx] = f"color: {LIGHT_BLUE}" if lead_mg else f"color: {ORANGE}"
            return colors

        styled = df_demo.style.apply(color_row, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.info("Demographic breakdown will appear once votes start reporting.")

    st.divider()

    # ═══════════════════════════════════════════
    # SECTION 5 — COUNTY TABLE
    # ═══════════════════════════════════════════
    col_tbl1, col_tbl2 = st.columns(2)

    county_df = build_county_df(county_data)

    # Percent share table (left)
    with col_tbl1:
        st.markdown(header_html("📋 Reporting by County — % Share"), unsafe_allow_html=True)
        pct_cols = ["COUNTY", "% Reporting"] + [f"{k} %" for k in CAND_KEYS] + ["Total"]
        pct_table = county_df[pct_cols].copy()

        fmt = {"% Reporting": "{:.1f}%", "Total": "{:,.0f}"}
        fmt.update({f"{k} %": "{:.1f}%" for k in CAND_KEYS})

        def style_pct_table(df):
            def highlight(row):
                styles = [""] * len(row)
                if row["% Reporting"] > 0:
                    mg_idx = df.columns.get_loc("McGrath %")
                    cb_idx = df.columns.get_loc("Booker %")
                    if row["McGrath %"] > row["Booker %"]:
                        styles[mg_idx] = f"color: {LIGHT_BLUE}; font-weight: bold"
                    else:
                        styles[cb_idx] = f"color: {ORANGE}; font-weight: bold"
                return styles
            return df.style.apply(highlight, axis=1).format(fmt)

        st.dataframe(style_pct_table(pct_table), use_container_width=True,
                     hide_index=True, height=600)

    # Raw vote table (right)
    with col_tbl2:
        st.markdown(header_html("📋 Reporting by County — Raw Votes"), unsafe_allow_html=True)
        vote_cols = ["COUNTY"] + [f"{k} Votes" for k in CAND_KEYS] + ["Total"]
        votes_table = county_df[vote_cols].copy()
        fmt_v = {f"{k} Votes": "{:,.0f}" for k in CAND_KEYS}
        fmt_v["Total"] = "{:,.0f}"
        st.dataframe(
            votes_table.style.format(fmt_v),
            use_container_width=True, hide_index=True, height=600
        )

    # ── Excel Export ─────────────────────────
    st.divider()
    st.markdown(header_html("📥 Export Results to Excel"), unsafe_allow_html=True)

    def build_excel_export(summary, s_100, demo_rows, county_df):
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:

            # Sheet 1 — Statewide Summary
            metrics = ["Counties Reporting", "Counties Complete", "Counties Not Started", "Total Votes"]
            values  = [f"{summary['counties_reporting'] + summary['counties_complete']} / 120",
                       summary['counties_complete'], summary['counties_not_started'], summary['total_votes']]
            for k in CAND_KEYS:
                metrics.append(f"{k} %")
                values.append(f"{summary[f'pct_{k}']}%")
                metrics.append(f"{k} Votes")
                values.append(summary[f"total_{k}"])
            metrics.append("McGrath−Booker Margin")
            values.append(f"{summary['margin']}%")
            pd.DataFrame({"Metric": metrics, "Value": values}).to_excel(
                writer, sheet_name="Statewide Summary", index=False)

            # Sheet 2 — 100% Reported Counties Only
            if s_100 and s_100["total_votes"] > 0:
                m2, v2 = ["Total Votes"], [s_100["total_votes"]]
                for k in CAND_KEYS:
                    m2.append(f"{k} %"); v2.append(f"{s_100[f'pct_{k}']}%")
                m2.append("McGrath−Booker Margin"); v2.append(f"{s_100['margin']}%")
                pd.DataFrame({"Metric": m2, "Value": v2}).to_excel(
                    writer, sheet_name="100pct Complete Only", index=False)

            # Sheet 3 — Demographics
            if demo_rows:
                demo_export = []
                for r in demo_rows:
                    d = {"Category": r["CATEGORY"], "Threshold": r["THRESHOLD"], "Total Votes": r["Total"]}
                    for k in CAND_KEYS:
                        d[f"{k} %"] = r[k]
                    d["McGrath−Booker Margin"] = r["MARGIN"]
                    demo_export.append(d)
                pd.DataFrame(demo_export).to_excel(writer, sheet_name="Demographics", index=False)

            # Sheet 4 — County Detail
            export_cols = ["COUNTY", "% Reporting"] + [f"{k} %" for k in CAND_KEYS] + \
                          [f"{k} Votes" for k in CAND_KEYS] + ["Total"]
            county_df[export_cols].to_excel(writer, sheet_name="County Detail", index=False)

        return output.getvalue()

    col_exp, _ = st.columns([1, 3])
    with col_exp:
        excel_data = build_excel_export(summary, s_100, demo_rows, county_df)
        st.download_button(
            label="📊 Download Excel Snapshot",
            data=excel_data,
            file_name=f"ky_primary_{datetime.now().strftime('%Y%m%d_%I%M%p')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ── Footer / auto-refresh ────────────────
    st.divider()
    st.markdown(
        f"<p style='text-align:center;color:#999;font-size:12px'>"
        f"Source: Kentucky Secretary of State — vrsws.sos.ky.gov · "
        f"All results unofficial · Auto-refreshes every {AUTO_REFRESH}s</p>",
        unsafe_allow_html=True
    )

    # Auto-refresh countdown
    placeholder = st.empty()
    for i in range(AUTO_REFRESH, 0, -1):
        placeholder.markdown(
            f"<p style='text-align:center;color:#aaa;font-size:11px'>"
            f"Next auto-refresh in {i}s</p>",
            unsafe_allow_html=True
        )
        time.sleep(1)
    st.cache_data.clear()
    st.rerun()


if __name__ == "__main__":
    main()
