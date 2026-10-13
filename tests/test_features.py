import pytest
from fintrack.db import FinanceDB


def test_goals_lifecycle(tmp_path):
    db=FinanceDB(tmp_path/'a.db')
    gid=db.add_goal('Emergency fund',100_000,'LKR','2027-12-31')
    db.contribute_goal(gid,25_000)
    assert db.goals('LKR')[0]['saved_cents']==25_000
    assert db.goals('USD')==[]
    with pytest.raises(ValueError):db.contribute_goal(gid,0)
    db.delete_goal(gid)
    assert db.goals()==[]
    db.close()


def test_recurring_posting_and_month_end(tmp_path):
    db=FinanceDB(tmp_path/'b.db')
    aid=db.add_account('Checking')
    cats={r['name']:r['id'] for r in db.categories()}
    rid=db.add_recurring('Monthly rent',aid,-50_000,cats['Rent'],'2027-01-31')
    db.post_recurring(rid)
    assert db.recurring()[0]['next_date']=='2027-02-28'
    assert db.monthly_summary('2027-01')['expenses']==50_000
    db.post_recurring(rid)
    assert db.recurring()[0]['next_date']=='2027-03-31'
    assert db.monthly_summary('2027-02')['expenses']==50_000
    assert db.database_check()=='ok'
    db.close()


def test_financial_insights_and_legacy_database_migration(tmp_path):
    path=tmp_path/'legacy.db';db=FinanceDB(path)
    aid=db.add_account('Checking')
    categories={r['name']:r['id'] for r in db.categories()}
    db.add_transaction(aid,'2026-10-10','Payday',150_000,categories['Salary'])
    db.add_transaction(aid,'2026-10-11','Local Market',-80_000,categories['Groceries'])
    db.add_transaction(aid,'2026-10-12','Misc',-5000)
    db.set_budget('2026-10',categories['Groceries'],50_000)
    r=db.analytics('2026-10')
    assert r['savings_rate']==round(65_000/150_000*100,1)
    assert r['uncategorized']==1
    assert len(r['over_budget'])==1
    assert r['merchants'][0]['description']=='Local Market'
    db.close()
    db=FinanceDB(path)
    assert db.analytics('2026-10')['summary']['expenses']==85_000
    assert db.goals()==[]
    db.close()


def test_recurring_validation(tmp_path):
    db=FinanceDB(tmp_path/'test.db')
    a=db.add_account('Checking');c={r['name']:r['id'] for r in db.categories()}
    with pytest.raises(ValueError):db.add_recurring('Wrong category',a,-200,c['Salary'],'2026-10-11')
    with pytest.raises(ValueError):db.add_recurring('Bad date',a,-200,c['Rent'],'2026-02-31')
    with pytest.raises(ValueError):db.add_goal('Bad',0)
    assert db.recurring()==[]
    db.close()
