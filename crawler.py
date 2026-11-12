import requests
import time
import re
from bs4 import BeautifulSoup
import os
import json
import hashlib
import pymysql

folder_destinatie = "posters"

os.makedirs(folder_destinatie, exist_ok=True)

url_repertoriu="https://www.teatruldavila.ro/repertoriu-curent/"
url_programari="https://www.teatruldavila.ro/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/jxl,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-GB,en;q=0.9,ro-RO;q=0.8,ro;q=0.7,en-US;q=0.6',
    'Cache-Control': 'max-age=0',
    'Priority': 'u=0, i',
    'Referer': url_repertoriu,
    'Sec-Ch-Ua': '"Not:A-Brand";v="8", "Chromium";v="156", "Google Chrome";v="156"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1'
}

session = requests.Session()

reVarsta=re.compile(r'v[âa]rst[ăa]',re.IGNORECASE)
reRegie=re.compile(r'regi[ae]',re.IGNORECASE)
reDurata=re.compile(r'durat[aă]',re.IGNORECASE)

reUpload=re.compile(r'https://www.teatruldavila\.ro/wp-content/uploads/', re.IGNORECASE)

def seteaza_valoare(container):
    if container is None:
        return "NotFound"
    return container.text.strip()


def calcSHA(cale_fisier):
    sha = hashlib.sha256()

    with open(cale_fisier,"rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha.update(chunk)

    return sha.hexdigest()

def prelucreaza_poster(url_img):
    if url_img=="NotFound":
        return "NotFound","NotFound"
    ok=False

    for incercari in range(5):
        try:
            print("incerc imaginea", url_img)
            raspuns_imagine = session.get(url_img)
            if raspuns_imagine.status_code == 200:
                ok=True
                break
        except requests.RequestException as e:
            print(f"Eroare rețea: {e}")
        time.sleep(2)
    if not ok:
        print("AM PRIMIT CODUL: ", raspuns_imagine.status_code)
        return "NotFound","NotFound"
    nume_fisier=url_img.split('/')[-1].split('?')[0]
    cale_completa = folder_destinatie + '/' + nume_fisier
    with open(cale_completa, "wb") as f:
        f.write(raspuns_imagine.content)

    sha=calcSHA(cale_completa)

    return cale_completa, sha



def insereaza_informatii_show(conexiune,d):
    with conexiune.cursor() as cursor:

        try:

            cursor.execute(
                "SELECT title, author, director, duration_minutes, duration_text, age_recommendation, cast_json, team_json, poster_path,"
                "poster_source_url, poster_hash, source_url FROM shows WHERE source_url = %s",
                (d['source_url'],),
            )
            exista_deja=cursor.fetchone()
            valori = (
                d['title'], d['author'], d['director'], d['duration_minutes'], d['duration_text'],
                d['age_recommendation'],
                d['cast_json'], d['team_json'],
                d['poster_path'],
                d['poster_source_url'], d['poster_hash'], d['source_url']
            )
            if exista_deja:
                update = False
                diferenta="Niciuna"
                for key,value in exista_deja.items():

                    if d[key]!=value:
                        update=True
                        diferenta=key
                        break

                if update:
                    sql = """
                                UPDATE shows 
                                SET title = %s, 
                                    author = %s, 
                                    director = %s, 
                                    duration_minutes = %s, 
                                    duration_text = %s, 
                                    age_recommendation = %s, 
                                    cast_json = %s, 
                                    team_json = %s, 
                                    poster_path = %s, 
                                    poster_source_url = %s, 
                                    poster_hash = %s
                                WHERE source_url = %s
                            """
                    cursor.execute(sql, valori)
                    print(f"Am dat update, erau diferente la {diferenta}")
                else:
                    print("E doar duplicat")

            else:
                sql="""
                    INSERT INTO SHOWS(title, author, director, duration_minutes, duration_text, age_recommendation, cast_json, team_json, poster_path,
                    poster_source_url, poster_hash, source_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(sql,valori)
        except Exception as e:
            print(f"Eroare la inserare {d['source_url']}: {e}")


def insereaza_informatii_programari(conexiune,d):
    with conexiune.cursor() as cursor:

        try:
            valori = (
                d['title'], d['author'], d['director'], d['duration_minutes'], d['duration_text'],
                d['age_recommendation'],
                d['cast_json'], d['team_json'],
                d['poster_path'],
                d['poster_source_url'], d['poster_hash'], d['source_url'],
            )

            cursor.execute(
                "SELECT title, author, director, duration_minutes, duration_text, age_recommendation, cast_json, team_json, poster_path,"
                "poster_source_url, poster_hash, source_url, productie_proprie, id FROM shows WHERE (poster_hash=%s and poster_hash!='NotFound') or source_url=%s or title=%s",
                (d['poster_hash'],d['source_url'],d['title'],),
            )
            exista_in_showuri=cursor.fetchone()

            if not exista_in_showuri:
                sql = """
                            INSERT INTO SHOWS(title, author, director, duration_minutes, duration_text, age_recommendation, cast_json, team_json, poster_path,
                            poster_source_url, poster_hash, source_url, productie_proprie) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                        """

                cursor.execute(sql, valori)

                cursor.execute(
                    "SELECT id FROM shows WHERE source_url = %s and title = %s",
                    (d['source_url'], d['title'],),
                )

                id=cursor.fetchone()['id']

                cursor.execute(
                    "INSERT INTO performances(show_id, start_at, venue, source_url, status) VALUES (%s, %s, %s, %s, %s)",
                    (id,d['start_at'],d['venue'],d['source_url'],d['status'],),
                )


            else:

                este_proprie=exista_in_showuri['productie_proprie']
                if not este_proprie:

                    update = False
                    diferenta="Niciuna"
                    for key,value in exista_in_showuri.items():
                        if key=='productie_proprie' or key=='id':
                            continue
                        if d[key]!=value:
                            update=True
                            diferenta=key
                            break

                    if update:
                        sql = """
                                    UPDATE shows 
                                    SET title = %s, 
                                        author = %s, 
                                        director = %s, 
                                        duration_minutes = %s, 
                                        duration_text = %s, 
                                        age_recommendation = %s, 
                                        cast_json = %s, 
                                        team_json = %s, 
                                        poster_path = %s, 
                                        poster_source_url = %s, 
                                        poster_hash = %s
                                    WHERE source_url = %s
                                """

                        cursor.execute(sql, valori)
                        print(f"Am dat update, erau diferente la {diferenta}")
                    else:
                        print("E doar duplicat")

                cursor.execute(
                    "SELECT start_at, venue, status from performances WHERE source_url=%s",
                    (d['source_url'],),

                )

                rezultat=cursor.fetchone()
                if rezultat:
                    if str(rezultat['start_at'])!=d['start_at'] or rezultat['venue']!=d['venue'] or rezultat['status']!=d['status']:

                        sql = """
                                UPDATE performances 
                                SET start_at= %s,
                                venue=%s,
                                status=%s
                                WHERE source_url = %s
                            """
                        cursor.execute(sql, (d['start_at'],d['venue'],d['status'],d['source_url'],))
                        print("de ce oare")
                    else:
                        print("e duplicat de performance")
                else:
                    cursor.execute(
                        "INSERT INTO performances(show_id, start_at, venue, source_url, status) VALUES (%s, %s, %s, %s, %s)",
                        (exista_in_showuri['id'], d['start_at'], d['venue'], d['source_url'], d['status'],),
                    )





        except Exception as e:
            print(f"Eroare la inserare {d['source_url']}: {e}")


def prelucreaza_durata(durataText):
    del_ora = r'or[eaă]|h'
    del_minut = r'min|minute|m|de minute|de min'

    durata_minute = 0
    gasit = False

    pattern_complet = rf'(\d+)\s*(?:{del_ora})\s*(?:(\d+)\s*(?:{del_minut}))?'
    match = re.search(pattern_complet, durataText, re.IGNORECASE)

    if match:
        ore = int(match.group(1))
        durata_minute += ore * 60
        gasit = True

        if match.group(2):
            minute = int(match.group(2))
            durata_minute += minute

    if not gasit:
        pattern_doar_minute = rf'(\d+)\s*(?:{del_minut})'
        match_min = re.search(pattern_doar_minute, durataText, re.IGNORECASE)
        if match_min:
            durata_minute += int(match_min.group(1))
            gasit = True

    if not gasit:
        return durataText.strip(), 0

    return durataText.strip(), durata_minute

def prelucreaza_varsta(varstaText):

    sablon_cheie=r'recomandat[ăa]|acceptat[ăa]'

    if re.search(sablon_cheie,varstaText,re.IGNORECASE):
        varstaText=re.split(r'/|:|\\|\|',varstaText)[-1].strip()
        return varstaText

    return varstaText


def prelucreaza_distributie(distributieText):
    linii=distributieText.splitlines()

    delim = (
        r'\s+-\s+'  
        r'|\s+‐\s+'  
        r'|\s+–\s+'  
        r'|\s+—\s+'  
        r'|\s+−\s+'  
        r'|\s+―\s+'  
        r'|\s+\|\s+'  
        r'|:\s+'  
        r'|\s{2,}' 
        r'|\s+\\\s+'  
        r'|\s+/\s+'
    )
    stp=' \n.,;'
    vd=[]
    for l in linii:
        if re.search(delim,l):
            rol,actor=re.split(delim,l, maxsplit=1)[:2]
            vd.append({'name':actor.strip(stp),'character':rol.strip(stp)})
        else:
            vd.append({'name':l.strip(stp)})

    return json.dumps(vd, ensure_ascii=False)

def prelucreaza_echipa(echipaText):
    linii=echipaText.splitlines()

    delim = (
        r'\s+-\s+'  
        r'|\s+‐\s+'  
        r'|\s+–\s+'  
        r'|\s+—\s+'  
        r'|\s+−\s+'  
        r'|\s+―\s+' 
        r'|\s+\|\s+'  
        r'|:\s+'  
        r'|\s{2,}'  
        r'|\s+\\\s+' 
        r'|\s+/\s+'
    )
    stp = ' \n.,;'
    vd = []
    regizor=None
    for l in linii:
        if re.search(delim,l):
            scop,persoana=re.split(delim,l, maxsplit=1)[:2]
            vd.append({'name':persoana.strip(stp),'role':scop.strip(stp)})
            if re.search(reRegie,scop):
                regizor=persoana.strip(stp)
        else:
            vd.append({'name':l.strip(stp)})

    return json.dumps(vd, ensure_ascii=False),regizor


def prelucreaza_data(dataText):
    if not dataText or dataText == "NotFound":
        return "1989-12-24 0:00:00"

    luni = {
        'ianuarie': '01', 'februarie': '02', 'martie': '03',
        'aprilie': '04', 'mai': '05', 'iunie': '06',
        'iulie': '07', 'august': '08', 'septembrie': '09',
        'octombrie': '10', 'noiembrie': '11', 'decembrie': '12'
    }

    match = re.search(r'(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})(?:.*?(\d{1,2}:\d{2}))?', dataText, re.IGNORECASE)

    if not match:
        return None

    zi, luna_str, an, ora_str = match.groups()

    luna_numar = luni.get(luna_str.lower())
    if not luna_numar:
        return None

    zi = zi.zfill(2)

    if ora_str:
        ora_completata = ora_str.zfill(5) + ":00"
    else:
        ora_completata = "00:00:00"

    timestamp_mysql = f"{an}-{luna_numar}-{zi} {ora_completata}"

    return timestamp_mysql



def scoate_informatii_show(url_secund,url_imagine_og="NotFound"):
    d={}
    session.headers.update({'Referer': url_repertoriu})
    ok=False
    for incercari in range(5):
        try:
            print("incerc", url_secund)
            raspuns_event = session.get(url_secund)
            if raspuns_event.status_code == 200:
                ok=True
                break
        except requests.RequestException as e:
            print(f"Eroare rețea: {e}")
        time.sleep(2)
    if not ok:
        print("AM PRIMIT CODUL: ", raspuns_event.status_code)
        return None

    soup_informatii=BeautifulSoup(raspuns_event.text,'lxml')
    container_inner=soup_informatii.select_one('.gt-site-inner')

    container_titlu= container_inner.select_one('.gt-page-title-bar .container h1')


    titlu=seteaza_valoare(container_titlu)
    titlu=titlu.upper().strip(' \n|-‐–—−―`~\'\"„”')

    container_detalii = container_inner.select_one('.container .gt-widget.gt-detail-widget')

    container_regizor = container_detalii.select_one('.gt-organizers .gt-inner')
    regizor = seteaza_valoare(container_regizor)




    container_sala=container_detalii.select_one('.gt-locations .gt-inner')
    sala=seteaza_valoare(container_sala)

    container_data=container_detalii.select_one('.gt-start-date .gt-inner')
    dataText=seteaza_valoare(container_data)

    container_status=container_detalii.select_one('.gt-status .gt-inner')
    status=seteaza_valoare(container_status)

    container_content=container_inner.select_one('.gt-content')

    container_author=container_content.select_one('[style*="text-align: right"]')

    author=" ".join(seteaza_valoare(container_author).splitlines()[:2])


    paragrafe=container_content.find_all('p')

    distributieText="NotFound"
    acum=False
    verbose=False
    for p in paragrafe:


        textP=p.get_text()


        if acum:
            distributieText=textP
            break
        match=re.search(r'distribu[țt]i[ae]',textP,re.IGNORECASE)

        if match:
            if len(textP)<31:
                acum = True
            else:
                continue



    echipaText="NotFound"


    varstaText="NotFound"
    durataText="NotFound"

    for p in paragrafe:
        textP=p.get_text()
        if reRegie.search(textP):
            echipaText=textP


        for linie in textP.splitlines():
            if reVarsta.search(linie):
                varstaText=linie.strip()
            if reDurata.search(linie):
                durataText=linie.strip()

    print(durataText)

    tag_imagine=container_content.find('img',src=reUpload)
    link_imagine="NotFound"
    if tag_imagine:
        link_imagine=tag_imagine['src']

    durata_text,durata_minute=prelucreaza_durata(durataText)
    varsta=prelucreaza_varsta(varstaText)
    cast=prelucreaza_distributie(distributieText)
    echipa,regizor_aux=prelucreaza_echipa(echipaText)
    if regizor_aux is not None:
        regizor=regizor_aux

    if link_imagine=='NotFound':
        link_imagine=url_imagine_og
    cale_poster,sha_poster = prelucreaza_poster(link_imagine)

    data=prelucreaza_data(dataText)

    d={
        'title':titlu,
        'author':author,
        'director':regizor,
        'duration_minutes':durata_minute,
        'duration_text':durata_text,
        'age_recommendation':varsta,
        'cast_json':cast,
        'team_json':echipa,
        'poster_path':cale_poster,
        'poster_source_url':link_imagine,
        'poster_hash':sha_poster,
        'source_url':url_secund,
        'venue':sala,
        'start_at':data,
        'status':status
      }

    return d


def scaneaza_showuri(conexiune):

    session.headers.update(headers)

    ok = False
    for _ in range(5):
        try:
            raspuns_repertoriu = session.get(url_repertoriu)
            if raspuns_repertoriu.status_code == 200:
                ok = True
                break
        except requests.RequestException as e:
            print(f"Eroare rețea: {e}")
        time.sleep(2)
    if not ok:
        print("AM PRIMIT CODUL: ", raspuns_repertoriu.status_code)
        return



    soup = BeautifulSoup(raspuns_repertoriu.text, 'lxml')
    containere_show = soup.select(
        '.wpb_column.vc_column_container.vc_col-sm-3 .wpb_images_carousel.wpb_content_element.vc_clearfix .vc_inner a'
    )

    print(len(containere_show))

    for show in containere_show:
        link_show=show['href']
        if "event" not in link_show:
            print("nu e tocmai link")
            continue

        tag_imagine = show.find('img', src=reUpload)
        url_imagine_og = "NotFound"
        if tag_imagine:
            url_imagine_og = tag_imagine['src']

        d=scoate_informatii_show(link_show, url_imagine_og)

        insereaza_informatii_show(conexiune,d)

        conexiune.commit()


    time.sleep(1)
    return

def scaneaza_programari(conexiune):
    session.headers.update(headers)

    ok = False
    for _ in range(5):
        try:
            raspuns_programari = session.get(url_programari)
            if raspuns_programari.status_code == 200:
                ok = True
                break
        except requests.RequestException as e:
            print(f"Eroare rețea: {e}")
        time.sleep(2)
    if not ok:
        print("AM PRIMIT CODUL: ", raspuns_programari.status_code)
        return

    soup = BeautifulSoup(raspuns_programari.text, 'lxml')
    containere_programari = soup.select(
        '.wpb_column.vc_column_container.vc_col-sm-12 .gt-event-listing .gt-columns.gt-column-3 .gt-col .gt-image a'
    )

    print(len(containere_programari))

    for show in containere_programari:
        link_show = show['href']
        if "event" not in link_show:
            print("nu e tocmai link")
            continue



        d = scoate_informatii_show(link_show)
        insereaza_informatii_programari(conexiune, d)

        conexiune.commit()


    time.sleep(1)
    return


def start_crawling():
    try:
        fisier_secret="secretraufrate.txt"
        with open(fisier_secret,'r') as f:
            host,database,user,password=f.read().splitlines()
        conexiune = pymysql.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )


        while(True):
            conexiune.ping(reconnect=True)
            scaneaza_showuri(conexiune)
            print("gata cu showurile")
            conexiune.ping(reconnect=True)
            scaneaza_programari(conexiune)
            print("gata cu programarile")
            time.sleep(60)

    except Exception as e:
        print(f'Eroare în crawler: {e}')

    finally:
        conexiune.close()
        print("CONEXIUNE INCHISA")
