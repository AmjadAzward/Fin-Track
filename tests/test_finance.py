from datetime import date
from fintrack.db import FinanceDB
from fintrack.importer import cents,convert,parse_date


def make(tmp_path):return FinanceDB(tmp_path/'finance.db')

def test_account_balance_and_cashflow(tmp_path):
    db=make(tmp_path)
    account=db.add_account('Main',opening_cents=100000)
    c={r['name']:r['id'] for r in db.categories()}
    db.add_transaction(account,'2026-10-01','Salary',200000,c['Salary'])
    db.add_transaction(account,'2026-10-02','Food',-45000,c['Groceries'])
    assert db.accounts()[0]['balance_cents']==255000
    assert db.monthly_summary('2026-10')['income']==200000
    assert db.monthly_summary('2026-10')['expenses']==45000
    db.close()

def test_transfer_is_not_income(tmp_path):
    db=make(tmp_path)
    x=db.add_account('A',opening_cents=200000);y=db.add_account('B')
    db.transfer(x,y,'2026-10-01',75000)
    assert db.monthly_summary('2026-10')['income']==0
    assert db.monthly_summary('2026-10')['expenses']==0
    assert [a['balance_cents'] for a in db.accounts()]==[125000,75000]
    db.delete_transaction(db.transactions()[0]['id'])
    assert len(db.transactions())==0
    db.close()

def test_import_idempotence_and_atomicity(tmp_path):
    db=make(tmp_path);a=db.add_account('Checking')
    rows=[{'date':'2026-10-05','description':'Coffee','amount_cents':-500},
          {'date':'2026-10-05','description':'Coffee','amount_cents':-500}]
    assert db.import_records(a,'statement.csv',rows)==(2,0)
    assert db.import_records(a,'statement.csv',rows)==(0,2)
    assert len(db.transactions())==2
    try:db.import_records(a,'bad.csv',[rows[0],{'date':'bad','description':'Invalid','amount_cents':300}])
    except ValueError:pass
    else:raise AssertionError('Invalid import should fail')
    assert len(db.transactions())==2
    db.close()

def test_budget(tmp_path):
    db=make(tmp_path);a=db.add_account('Wallet');cat={r['name']:r['id'] for r in db.categories()}['Groceries']
    db.set_budget('2026-10',cat,50000);db.add_transaction(a,'2026-10-12','Market',-12500,cat)
    r=next(r for r in db.budget_rows('2026-10') if r['id']==cat)
    assert r['budget_cents']==50000 and r['spent_cents']==12500
    db.close()

def test_import_conversion():
    rows=[['Date','Description','Debit','Credit'],['11/10/2026','Salary','','1000.00'],['12/10/2026','Taxi','125.50','']]
    transactions=convert(rows,{'date':0,'description':1,'debit':2,'credit':3})
    assert [x['amount_cents'] for x in transactions]==[100000,-12550]
    assert parse_date('2026-10-11')=='2026-10-11'
    assert cents('(1,234.50)')==-123450
