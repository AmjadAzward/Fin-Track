"""FinTrack local SQLite persistence and accounting operations. All amounts: integer cents."""
import sqlite3
import hashlib
import json
import csv
from datetime import datetime, date
from pathlib import Path

DEFAULT_CATEGORIES = [
    ('Salary','income'),('Freelance','income'),('Other Income','income'),
    ('Groceries','expense'),('Dining','expense'),('Transport','expense'),('Utilities','expense'),
    ('Rent','expense'),('Shopping','expense'),('Healthcare','expense'),('Entertainment','expense'),
    ('Subscriptions','expense'),('Education','expense'),('Other Expense','expense'),
]

class FinanceDB:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.path)
        self.con.row_factory = sqlite3.Row
        self.con.execute('PRAGMA foreign_keys=ON')
        self.con.execute('PRAGMA journal_mode=WAL')
        self.con.execute('PRAGMA busy_timeout=5000')
        self._init()

    def _init(self):
        self.con.executescript('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL DEFAULT 'Bank', currency TEXT NOT NULL DEFAULT 'LKR',
                opening_cents INTEGER NOT NULL DEFAULT 0, archived INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL CHECK(kind IN ('income','expense'))
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES accounts(id),
                date TEXT NOT NULL, description TEXT NOT NULL, amount_cents INTEGER NOT NULL,
                category_id INTEGER REFERENCES categories(id), note TEXT NOT NULL DEFAULT '',
                source_key TEXT UNIQUE, transfer_group TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS budgets (
                month TEXT NOT NULL, category_id INTEGER NOT NULL REFERENCES categories(id),
                amount_cents INTEGER NOT NULL CHECK(amount_cents>=0),
                PRIMARY KEY(month,category_id)
            );
            CREATE TABLE IF NOT EXISTS imports (
                id INTEGER PRIMARY KEY, filename TEXT, account_id INTEGER,
                imported INTEGER, skipped INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, target_cents INTEGER NOT NULL CHECK(target_cents>0),
                saved_cents INTEGER NOT NULL DEFAULT 0 CHECK(saved_cents>=0), deadline TEXT, currency TEXT NOT NULL DEFAULT 'LKR',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS recurring (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(amount_cents != 0),
                category_id INTEGER REFERENCES categories(id), account_id INTEGER NOT NULL REFERENCES accounts(id),
                day_of_month INTEGER NOT NULL CHECK(day_of_month BETWEEN 1 AND 31),
                next_date TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date);
            CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id);
        ''')
        with self.con:
            self.con.executemany('INSERT OR IGNORE INTO categories(name,kind) VALUES (?,?)', DEFAULT_CATEGORIES)
            self.con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('currency','LKR')")

    def close(self):
        self.con.close()

    def setting(self, key, default=''):
        row=self.con.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return row['value'] if row else default

    def set_setting(self,key,value):
        with self.con:
            self.con.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,str(value)))

    def accounts(self, include_archived=False):
        sql='SELECT a.*, a.opening_cents+COALESCE(SUM(t.amount_cents),0) balance_cents FROM accounts a LEFT JOIN transactions t ON a.id=t.account_id'
        if not include_archived: sql+=' WHERE a.archived=0'
        sql+=' GROUP BY a.id ORDER BY a.name'
        return self.con.execute(sql).fetchall()

    def add_account(self,name,kind='Bank',currency='LKR',opening_cents=0):
        name=name.strip()
        if not name: raise ValueError('Account name is required')
        with self.con:
            return self.con.execute('INSERT INTO accounts(name,kind,currency,opening_cents) VALUES(?,?,?,?)',(name,kind,currency,int(opening_cents))).lastrowid

    def archive_account(self,account_id):
        with self.con:
            self.con.execute('UPDATE accounts SET archived=1 WHERE id=?',(account_id,))

    def categories(self,kind=None):
        return self.con.execute('SELECT * FROM categories '+('WHERE kind=? ' if kind else '')+'ORDER BY name',((kind,) if kind else ())).fetchall()

    def add_category(self,name,kind):
        if kind not in ('income','expense'): raise ValueError('Invalid category type')
        with self.con:
            self.con.execute('INSERT INTO categories(name,kind) VALUES(?,?)',(name.strip(),kind))

    def add_transaction(self,account_id,day,description,amount_cents,category_id=None,note='',source_key=None,transfer_group=None):
        date.fromisoformat(day)
        if not description.strip(): raise ValueError('A description is required')
        amount_cents=int(amount_cents)
        if amount_cents==0: raise ValueError('Amount must not be zero')
        with self.con:
            return self.con.execute('''INSERT INTO transactions(account_id,date,description,amount_cents,category_id,note,source_key,transfer_group)
                VALUES(?,?,?,?,?,?,?,?)''',(account_id,day,description.strip(),amount_cents,category_id,note,source_key,transfer_group)).lastrowid

    def edit_transaction(self, tx_id, day, description, amount_cents, category_id=None, note=''):
        date.fromisoformat(day)
        description=description.strip()
        amount_cents=int(amount_cents)
        if not description or not amount_cents:
            raise ValueError('Description and non-zero amount are required')
        row=self.con.execute('SELECT transfer_group FROM transactions WHERE id=?',(tx_id,)).fetchone()
        if row is None: raise ValueError('Transaction not found')
        if row['transfer_group']: raise ValueError('Transfers cannot be edited; delete and recreate them')
        if category_id is not None:
            category=self.con.execute('SELECT kind FROM categories WHERE id=?',(category_id,)).fetchone()
            if not category or category['kind']!=('income' if amount_cents>0 else 'expense'):
                raise ValueError('Category type must match the transaction direction')
        with self.con:
            self.con.execute("UPDATE transactions SET date=?,description=?,amount_cents=?,category_id=?,note=? WHERE id=?",(day,description,amount_cents,category_id,note,tx_id))

    def database_check(self):
        return self.con.execute('PRAGMA integrity_check').fetchone()[0]

    def export_transactions_csv(self,path,month=None,currency=None):
        query=self.transactions(month=month,limit=1000000)
        with open(path,'w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream)
            writer.writerow(['Date','Account','Description','Category','Amount','Currency','Note'])
            for t in query:
                if currency and t['currency']!=currency:continue
                writer.writerow([t['date'],t['account_name'],t['description'],t['category_name'] or
                    ('Transfer' if t['transfer_group'] else 'Uncategorized'),
                    f"{t['amount_cents']/100:.2f}",t['currency'],t['note']])

    def recurring_merchants(self,months=6,currency='LKR'):
        return self.con.execute("""SELECT LOWER(TRIM(t.description)) merchant,
                COUNT(*) occurrences, SUM(-t.amount_cents) total_cents,
                CAST(AVG(-t.amount_cents) AS INTEGER) average_cents
            FROM transactions t JOIN accounts a ON a.id=t.account_id
            WHERE a.currency=? AND t.amount_cents<0 AND t.transfer_group IS NULL
              AND t.date>=date('now', ?)
            GROUP BY LOWER(TRIM(t.description)) HAVING COUNT(*)>=2
            ORDER BY occurrences DESC,total_cents DESC LIMIT 30""",(currency,f'-{int(months)} months')).fetchall()

    def delete_transaction(self,tx_id):
        row=self.con.execute('SELECT transfer_group FROM transactions WHERE id=?',(tx_id,)).fetchone()
        if not row: return
        with self.con:
            if row['transfer_group']:
                self.con.execute('DELETE FROM transactions WHERE transfer_group=?',(row['transfer_group'],))
            else:
                self.con.execute('DELETE FROM transactions WHERE id=?',(tx_id,))

    def transfer(self,source_id,target_id,day,amount_cents,note='Transfer'):
        if source_id==target_id: raise ValueError('Select different accounts')
        source=self.con.execute('SELECT currency FROM accounts WHERE id=?',(source_id,)).fetchone()
        target=self.con.execute('SELECT currency FROM accounts WHERE id=?',(target_id,)).fetchone()
        if not source or not target: raise ValueError('Account not found')
        if source['currency']!=target['currency']: raise ValueError('Cross-currency transfers are not yet supported')
        date.fromisoformat(day)
        if amount_cents<=0: raise ValueError('Amount must be positive')
        import uuid
        group=str(uuid.uuid4())
        with self.con:
            self.con.execute('INSERT INTO transactions(account_id,date,description,amount_cents,transfer_group) VALUES(?,?,?,?,?)',(source_id,day,note,-amount_cents,group))
            self.con.execute('INSERT INTO transactions(account_id,date,description,amount_cents,transfer_group) VALUES(?,?,?,?,?)',(target_id,day,note,amount_cents,group))

    def transactions(self,month=None,account_id=None,search='',limit=5000):
        clauses=[]; params=[]
        if month:
            clauses.append('substr(t.date,1,7)=?');params.append(month)
        if account_id:
            clauses.append('t.account_id=?');params.append(account_id)
        if search:
            clauses.append('(t.description LIKE ? OR t.note LIKE ?)');params.extend([f'%{search}%']*2)
        sql='''SELECT t.*, a.name account_name, a.currency, c.name category_name, c.kind category_kind
            FROM transactions t JOIN accounts a ON a.id=t.account_id LEFT JOIN categories c ON c.id=t.category_id'''
        if clauses: sql+=' WHERE '+' AND '.join(clauses)
        sql+=' ORDER BY t.date DESC,t.id DESC LIMIT ?';params.append(limit)
        return self.con.execute(sql,params).fetchall()

    def update_category(self,tx_id,category_id):
        with self.con:
            self.con.execute('UPDATE transactions SET category_id=? WHERE id=? AND transfer_group IS NULL',(category_id,tx_id))

    def monthly_summary(self,month,currency='LKR'):
        row=self.con.execute('''SELECT
          COALESCE(SUM(CASE WHEN t.amount_cents>0 AND (c.kind='income' OR c.id IS NULL) THEN t.amount_cents ELSE 0 END),0) income,
          COALESCE(SUM(CASE WHEN t.amount_cents<0 AND (c.kind='expense' OR c.id IS NULL) THEN -t.amount_cents ELSE 0 END),0) expenses,
          COUNT(*) total
          FROM transactions t JOIN accounts a ON t.account_id=a.id
          LEFT JOIN categories c ON t.category_id=c.id
          WHERE substr(t.date,1,7)=? AND a.currency=? AND t.transfer_group IS NULL''',(month,currency)).fetchone()
        return dict(row)

    def category_spending(self,month,currency='LKR'):
        return self.con.execute('''SELECT COALESCE(c.name,'Uncategorized') name,SUM(-t.amount_cents) cents
            FROM transactions t JOIN accounts a ON a.id=t.account_id
            LEFT JOIN categories c ON c.id=t.category_id
            WHERE substr(t.date,1,7)=? AND t.amount_cents<0 AND a.currency=?
              AND t.transfer_group IS NULL AND (c.kind='expense' OR c.id IS NULL)
            GROUP BY c.name ORDER BY cents DESC''',(month,currency)).fetchall()

    def trend(self,months,currency='LKR'):
        return [(m,self.monthly_summary(m,currency)) for m in months]

    def budget_rows(self,month,currency='LKR'):
        return self.con.execute('''SELECT c.id,c.name,COALESCE(b.amount_cents,0) budget_cents,
          COALESCE((SELECT SUM(-t.amount_cents) FROM transactions t JOIN accounts a ON t.account_id=a.id
             WHERE t.category_id=c.id AND substr(t.date,1,7)=? AND t.amount_cents<0
             AND t.transfer_group IS NULL AND a.currency=?),0) spent_cents
          FROM categories c LEFT JOIN budgets b ON b.category_id=c.id AND b.month=?
          WHERE c.kind='expense' ORDER BY c.name''',(month,currency,month)).fetchall()

    def set_budget(self,month,category_id,amount_cents):
        with self.con:
            self.con.execute('''INSERT INTO budgets(month,category_id,amount_cents) VALUES(?,?,?)
                ON CONFLICT(month,category_id) DO UPDATE SET amount_cents=excluded.amount_cents''',(month,category_id,int(amount_cents)))

    def import_records(self,account_id,filename,records):
        """Each record: date, description, amount_cents, optional reference/category_id.
        Idempotent for matching source rows from the same statement AND account.
        """
        imported=skipped=0
        seen={}
        category_ids={r['name']:r['id'] for r in self.categories()}
        with self.con:
            for occurrence,record in enumerate(records):
                day=record['date'];date.fromisoformat(day)
                description=str(record['description']).strip()
                cents=int(record['amount_cents'])
                if not description or cents==0: raise ValueError(f'Invalid record at row {occurrence+1}')
                # Count repeated identical transactions separately while recognizing renamed files.
                identity=(day,description.casefold(),cents,str(record.get('reference','')).strip())
                seen[identity]=seen.get(identity,0)+1
                keydata=json.dumps([account_id,*identity,seen[identity]],ensure_ascii=False)
                key=hashlib.sha256(keydata.encode()).hexdigest()
                category_id=record.get('category_id')
                if category_id is None:
                    words=description.lower()
                    mappings=[('supermarket','Groceries'),('grocery','Groceries'),('fuel','Transport'),
                        ('petrol','Transport'),('taxi','Transport'),('uber','Transport'),
                        ('electricity','Utilities'),('water bill','Utilities'),('salary','Salary'),
                        ('netflix','Subscriptions'),('spotify','Subscriptions'),('restaurant','Dining')]
                    for fragment,category_name in mappings:
                        if fragment in words:
                            category_id=category_ids[category_name]
                            # Do not tag a refund as an expense or a payment as income.
                            kind='income' if cents>0 else 'expense'
                            actual_kind=self.con.execute('SELECT kind FROM categories WHERE id=?',(category_id,)).fetchone()['kind']
                            if kind!=actual_kind: category_id=None
                            break
                cur=self.con.execute('''INSERT OR IGNORE INTO transactions(account_id,date,description,amount_cents,category_id,note,source_key)
                    VALUES(?,?,?,?,?,?,?)''',(account_id,day,description,cents,category_id,record.get('reference',''),key))
                if cur.rowcount: imported+=1
                else: skipped+=1
            self.con.execute('INSERT INTO imports(filename,account_id,imported,skipped) VALUES(?,?,?,?)',(filename,account_id,imported,skipped))
        return imported,skipped

    def import_history(self):
        return self.con.execute('SELECT * FROM imports ORDER BY id DESC LIMIT 30').fetchall()

    def backup(self,target):
        dest=sqlite3.connect(str(target))
        try: self.con.backup(dest)
        finally: dest.close()

    def seed_demo(self):
        if self.accounts(include_archived=True): return False
        aid=self.add_account('Everyday Account','Bank','LKR',25000000)
        savings=self.add_account('Savings','Savings','LKR',15000000)
        cats={r['name']:r['id'] for r in self.categories()}
        month=date.today().strftime('%Y-%m')
        rows=[(3,'Monthly salary',18000000,'Salary'),(5,'Groceries and essentials',-1850000,'Groceries'),
              (7,'Fuel and travel',-780000,'Transport'),(9,'Coffee with friends',-195000,'Dining'),
              (11,'Internet and electricity',-920000,'Utilities'),(12,'Monthly subscription',-149900,'Subscriptions'),
              (15,'Clothing',-420000,'Shopping'),(18,'Freelance project',3500000,'Freelance')]
        for d,desc,value,cat in rows:
            safe=min(d,date.today().day)
            self.add_transaction(aid,f'{month}-{safe:02d}',desc,value,cats[cat])
        self.set_budget(month,cats['Groceries'],2500000)
        self.set_budget(month,cats['Transport'],1200000)
        self.set_budget(month,cats['Dining'],750000)
        return True

    # FinTrack 5.0 planning and analytics services.
    def add_goal(self,name,target_cents,currency='LKR',deadline=None):
        if not name.strip() or int(target_cents)<=0:raise ValueError('Enter a goal name and positive target')
        if deadline: date.fromisoformat(deadline)
        with self.con:
            return self.con.execute('INSERT INTO goals(name,target_cents,currency,deadline) VALUES(?,?,?,?)',
                (name.strip(),int(target_cents),currency,deadline)).lastrowid

    def goals(self,currency=None):
        return self.con.execute('SELECT * FROM goals'+(' WHERE currency=?' if currency else '')+' ORDER BY id DESC',
            (currency,) if currency else ()).fetchall()

    def contribute_goal(self,goal_id,amount_cents):
        if int(amount_cents)<=0:raise ValueError('Contribution must be positive')
        with self.con:
            result=self.con.execute('UPDATE goals SET saved_cents=saved_cents+? WHERE id=?',(int(amount_cents),goal_id))
            if not result.rowcount:raise ValueError('Goal not found')

    def delete_goal(self,goal_id):
        with self.con:self.con.execute('DELETE FROM goals WHERE id=?',(goal_id,))

    def add_recurring(self,name,account_id,amount_cents,category_id,next_date):
        if not name.strip() or int(amount_cents)==0:raise ValueError('Name and amount are required')
        day=date.fromisoformat(next_date)
        acc=self.con.execute('SELECT id FROM accounts WHERE id=?',(account_id,)).fetchone()
        if not acc:raise ValueError('Account not found')
        if category_id is not None:
            cat=self.con.execute('SELECT kind FROM categories WHERE id=?',(category_id,)).fetchone()
            if not cat or cat['kind']!=('income' if amount_cents>0 else 'expense'):
                raise ValueError('Category does not match direction')
        with self.con:
            return self.con.execute('INSERT INTO recurring(name,account_id,amount_cents,category_id,day_of_month,next_date) VALUES(?,?,?,?,?,?)',
                (name.strip(),account_id,int(amount_cents),category_id,day.day,next_date)).lastrowid

    def recurring(self):
        return self.con.execute("""SELECT r.*,a.name account_name,c.name category_name
            FROM recurring r JOIN accounts a ON a.id=r.account_id
            LEFT JOIN categories c ON c.id=r.category_id ORDER BY r.next_date,r.id""").fetchall()

    def delete_recurring(self,id):
        with self.con:self.con.execute('DELETE FROM recurring WHERE id=?',(id,))

    def post_recurring(self,id):
        import calendar
        row=self.con.execute('SELECT * FROM recurring WHERE id=? AND active=1',(id,)).fetchone()
        if not row:raise ValueError('Active scheduled transaction not found')
        dt=date.fromisoformat(row['next_date']);m=dt.month+1;y=dt.year
        if m==13:y+=1;m=1
        future=date(y,m,min(row['day_of_month'],calendar.monthrange(y,m)[1])).isoformat()
        with self.con:
            self.add_transaction(row['account_id'],row['next_date'],row['name'],row['amount_cents'],row['category_id'])
            self.con.execute('UPDATE recurring SET next_date=? WHERE id=?',(future,id))

    def analytics(self,month,currency='LKR'):
        month_date=date.fromisoformat(month+'-01')
        summary=self.monthly_summary(month,currency)
        spending=self.category_spending(month,currency)
        budget=self.budget_rows(month,currency)
        uncategorized=self.con.execute("""SELECT COUNT(*) FROM transactions t
            JOIN accounts a ON a.id=t.account_id WHERE substr(t.date,1,7)=? AND a.currency=?
            AND t.category_id IS NULL AND t.transfer_group IS NULL""",(month,currency)).fetchone()[0]
        merchant=self.con.execute("""SELECT description,COUNT(*) count,SUM(-amount_cents) cents FROM transactions t
            JOIN accounts a ON a.id=t.account_id WHERE substr(t.date,1,7)=? AND a.currency=?
            AND t.amount_cents<0 AND t.transfer_group IS NULL
            GROUP BY LOWER(TRIM(description)) ORDER BY cents DESC LIMIT 8""",(month,currency)).fetchall()
        return {'summary':summary,'spending':spending,'budgets':budget,
                'uncategorized':uncategorized,'merchants':merchant,
                'savings_rate':round((summary['income']-summary['expenses'])/summary['income']*100,1) if summary['income'] else None,
                'over_budget':[dict(r) for r in budget if r['budget_cents']>0 and r['spent_cents']>r['budget_cents']]}
