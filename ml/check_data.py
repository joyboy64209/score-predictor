from app import db  
q = 'SELECT COUNT(*) AS c FROM {t!r}'  
for t in ['Fixture','Team','Standing']:  
    print(t, db.fetch_all(q.format(t=t))[0]['c'])  
