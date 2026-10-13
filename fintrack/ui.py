"""FinTrack PySide6 desktop UI."""
import calendar
import os
import shutil
import sys
from datetime import date
from pathlib import Path
from PySide6.QtCore import Qt,QDate,QRectF,Signal
from PySide6.QtGui import QColor,QPainter,QPen,QFont,QKeySequence,QShortcut
from PySide6.QtWidgets import (QMainWindow,QWidget,QFrame,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,
 QStackedWidget,QTableWidget,QTableWidgetItem,QHeaderView,QLineEdit,QComboBox,QDateEdit,QDoubleSpinBox,QCalendarWidget,
 QMessageBox,QDialog,QDialogButtonBox,QFormLayout,QFileDialog,QProgressBar,QScrollArea,QCheckBox,QSpinBox)
from .db import FinanceDB
from .importer import read_rows,convert
from .reports import pdf,xlsx,money
from .theme import DARK,LIGHT


def text(s,objectname=None):
    label=QLabel(str(s))
    label.setWordWrap(True)
    if objectname:label.setObjectName(objectname)
    return label

def btn(label,click=None,primary=False):
    b=QPushButton(label)
    if primary:b.setObjectName('primary')
    if click:b.clicked.connect(click)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b

def table(headers):
    w=QTableWidget(0,len(headers));w.setHorizontalHeaderLabels(headers)
    w.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    w.setAlternatingRowColors(True);w.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    w.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    w.verticalHeader().setVisible(False);w.setSortingEnabled(False)
    w.verticalHeader().setDefaultSectionSize(42)
    w.setShowGrid(False);w.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    w.setAccessibleName('Data table')
    return w

def put(w,row,values,identifier=None):
    w.insertRow(row)
    for c,value in enumerate(values):
        item=QTableWidgetItem(str(value))
        if c==0 and identifier is not None:item.setData(Qt.ItemDataRole.UserRole,identifier)
        w.setItem(row,c,item)

def dialog(parent,title):
    d=QDialog(parent);d.setWindowTitle(title);d.setMinimumWidth(460);d.setModal(True)
    box=QVBoxLayout(d);box.setContentsMargins(24,22,24,22);box.setSpacing(18)
    box.addWidget(text(title,'sectionTitle'))
    form=QFormLayout();form.setSpacing(13);form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft);form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow);box.addLayout(form)
    return d,box,form

def finish(d,box):
    actions=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
    actions.accepted.connect(d.accept);actions.rejected.connect(d.reject)
    ok=actions.button(QDialogButtonBox.StandardButton.Ok)
    if ok:ok.setObjectName('primary');ok.setText('Save')
    box.addWidget(actions)

def money_edit(value=0):
    field=QDoubleSpinBox();field.setRange(0,100000000000);field.setDecimals(2);field.setValue(value);field.setGroupSeparatorShown(True)
    return field

def date_edit():
    field=QDateEdit();field.setCalendarPopup(True);field.setDisplayFormat('dd MMM yyyy');field.setDate(QDate.currentDate());field.setMinimumDate(QDate(1900,1,1));field.setMaximumDate(QDate(9999,12,31));return field

class MonthPicker(QWidget):
    """Compact, keyboard-accessible report period picker (month and year only)."""
    monthChanged=Signal(str)

    def __init__(self, month, parent=None):
        super().__init__(parent)
        self._month=month
        row=QHBoxLayout(self);row.setContentsMargins(0,0,0,0);row.setSpacing(5)
        self.previous=btn('<',self.go_previous)
        self.previous.setToolTip('Previous month')
        self.previous.setAccessibleName('Previous month')
        self.choose=btn('')
        self.choose.setToolTip('Choose month and year')
        self.choose.setAccessibleName('Choose month and year')
        self.choose.clicked.connect(self.choose_month)
        self.next=btn('>',self.go_next)
        self.next.setToolTip('Next month')
        self.next.setAccessibleName('Next month')
        for b in (self.previous,self.next):b.setFixedWidth(36)
        self.choose.setMinimumWidth(140)
        for b in (self.previous,self.choose,self.next):row.addWidget(b)
        self.set_month(month,emit=False)

    def set_month(self,month,emit=False):
        parsed=date.fromisoformat(month+'-01')
        month=parsed.strftime('%Y-%m')
        changed=month!=self._month
        self._month=month
        self.choose.setText(f'{calendar.month_name[parsed.month]} {parsed.year}')
        if changed and emit:self.monthChanged.emit(month)

    def shift(self,delta):
        year,month=map(int,self._month.split('-'))
        month_number=year*12+(month-1)+delta
        new_year,new_month=divmod(month_number,12)
        if 1<=new_year<=9999:self.set_month(f'{new_year:04d}-{new_month+1:02d}',emit=True)

    def go_previous(self):self.shift(-1)
    def go_next(self):self.shift(1)

    def choose_month(self):
        dlg=QDialog(self)
        dlg.setWindowTitle('Select reporting month')
        dlg.setMinimumWidth(340)
        layout=QVBoxLayout(dlg)
        yr,mo=map(int,self._month.split('-'))
        year_label=QLabel()
        yearrow=QHBoxLayout()
        year_prev=btn('<');year_next=btn('>')
        yearrow.addWidget(year_prev);yearrow.addStretch();yearrow.addWidget(year_label);yearrow.addStretch();yearrow.addWidget(year_next)
        layout.addLayout(yearrow)
        grid=QGridLayout();grid.setSpacing(7);layout.addLayout(grid)
        buttons=[]
        current_year=[yr]
        def choose_month_index(m):
            self.set_month(f'{current_year[0]:04d}-{m:02d}',emit=True)
            dlg.accept()
        for i in range(1,13):
            b=btn(calendar.month_abbr[i])
            b.setMinimumHeight(38)
            b.clicked.connect(lambda checked=False, m=i:choose_month_index(m))
            grid.addWidget(b,(i-1)//3,(i-1)%3)
            buttons.append(b)
        def render():
            year_label.setText(str(current_year[0]))
            for i,b in enumerate(buttons,1):b.setObjectName('selectedMonth' if current_year[0]==yr and i==mo else 'monthChoice')
            dlg.style().unpolish(dlg);dlg.style().polish(dlg)
            for b in buttons:b.style().unpolish(b);b.style().polish(b)
            year_prev.setEnabled(current_year[0]>1);year_next.setEnabled(current_year[0]<9999)
        def move_year(step):
            current_year[0]=max(1,min(9999,current_year[0]+step));render()
        year_prev.clicked.connect(lambda:move_year(-1))
        year_next.clicked.connect(lambda:move_year(1))
        today=btn('This month',primary=True)
        def this_month():
            current_year[0]=date.today().year
            choose_month_index(date.today().month)
        today.clicked.connect(this_month)
        layout.addWidget(today)
        render()
        dlg.exec()

class Bars(QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.values=[];self.setMinimumHeight(210)
    def set_values(self,values):self.values=values;self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w=self.width();h=self.height();p.setPen(QColor('#879bb0'))
        if not self.values:
            p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'No chart data yet');return
        mx=max([x for _,a,b in self.values for x in (a,b)]+[1]);n=len(self.values)
        for i,(label,a,b) in enumerate(self.values):
            group=(w-40)/n;x=24+i*group;bar=max(7,min(22,group*0.24))
            avail=h-48
            ah=avail*a/mx;bh=avail*b/mx
            p.setBrush(QColor('#1fc6a5'));p.setPen(Qt.PenStyle.NoPen);p.drawRoundedRect(QRectF(x+group*.23,h-31-ah,bar,ah),4,4)
            p.setBrush(QColor('#4d75c9'));p.drawRoundedRect(QRectF(x+group*.23+bar+5,h-31-bh,bar,bh),4,4)
            p.setPen(QColor('#8da1b7'));p.drawText(QRectF(x,h-26,group,22),Qt.AlignmentFlag.AlignCenter,str(label))

class MainWindow(QMainWindow):
    def __init__(self,db):
        super().__init__();self.db=db;self.month=date.today().strftime('%Y-%m');self.currency='LKR'
        self.setWindowTitle('FinTrack - Personal Finance Manager');self.resize(1380,850);self.setMinimumSize(1024,680)
        self.theme=self.db.setting('theme','dark');self.build();self.apply_theme();self.refresh();self.setup_shortcuts()

    def build(self):
        base=QWidget();self.setCentralWidget(base);outer=QHBoxLayout(base);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        side=QFrame();side.setObjectName('sidebar');side.setFixedWidth(236);s=QVBoxLayout(side);s.setContentsMargins(16,25,16,18);s.setSpacing(7)
        s.addWidget(text('FinTrack','brand'));s.addWidget(text('YOUR MONEY, CLEARLY','eyebrow'));s.addSpacing(16)
        self.nav=[]; names=['Overview','Accounts','Transactions','Import Statements','Budgets','Reports','Insights','Goals','Recurring','Settings']
        icons=['01','02','03','04','05','06','07','08','09','10']
        self.stack=QStackedWidget()
        for i,(name,icon) in enumerate(zip(names,icons)):
            b=btn(f'{icon}   {name}',lambda _,ix=i:self.go(ix));b.setObjectName('nav');b.setCheckable(True);b.setToolTip(f'Open {name}');s.addWidget(b);self.nav.append(b)
            self.stack.addWidget(self.make_page(i,name))
        s.addStretch();s.addWidget(text('PRIVATE BY DEFAULT','eyebrow'));s.addWidget(text('Local and offline  |  v1.0','subheading'))
        outer.addWidget(side);outer.addWidget(self.stack,1);self.go(0)
        self.statusBar().showMessage('Ready  |  Data stays on this device')

    def setup_shortcuts(self):
        shortcuts=[('Ctrl+1',lambda:self.go(0)),('Ctrl+2',lambda:self.go(1)),('Ctrl+3',lambda:self.go(2)),('Ctrl+N',self.add_transaction),('Ctrl+I',self.import_file),('Ctrl+F',lambda:(self.go(2),self.search.setFocus())),('Ctrl+,',lambda:self.go(9))]
        self.shortcuts=[]
        for keys,callback in shortcuts:
            shortcut=QShortcut(QKeySequence(keys),self);shortcut.activated.connect(callback);self.shortcuts.append(shortcut)

    def make_page(self,index,name):
        page=QWidget();root=QVBoxLayout(page);root.setContentsMargins(30,25,30,24);root.setSpacing(16)
        top=QHBoxLayout();headers=['Financial overview','Your accounts','All transactions','Import bank statements','Monthly budgets','Reports & exports','Spending insights','Savings goals','Recurring payments','Preferences']
        heading=QVBoxLayout();heading.addWidget(text(headers[index],'heading'))
        sub=['Everything at a glance','Manage balances across your accounts','Search, review and manage your activity','CSV and Excel with a safe preview','Give every category a spending limit','Turn your transactions into useful summaries','Understand where your money goes','Plan for your financial milestones','Manage scheduled transactions','Make FinTrack work your way']
        heading.addWidget(text(sub[index],'subheading'));top.addLayout(heading);top.addStretch()
        if index in (0,2,4,5,6):
            picker=MonthPicker(self.month)
            picker.monthChanged.connect(self.update_month)
            top.addWidget(text('REPORTING PERIOD','eyebrow'));top.addWidget(picker)
            if not hasattr(self,'month_inputs'):self.month_inputs=[]
            self.month_inputs.append(picker)
        root.addLayout(top)
        if index==0:self.build_dashboard(root)
        elif index==1:self.build_accounts(root)
        elif index==2:self.build_transactions(root)
        elif index==3:self.build_import(root)
        elif index==4:self.build_budgets(root)
        elif index==5:self.build_reports(root)
        elif index==6:self.build_insights(root)
        elif index==7:self.build_goals(root)
        elif index==8:self.build_recurring(root)
        elif index==9:self.build_settings(root)
        return page

    def frame(self):
        f=QFrame();f.setObjectName('card');return f

    def build_dashboard(self,root):
        metrics=QGridLayout();metrics.setSpacing(15);self.metrics=[]
        for i,name in enumerate(['Total balances','Income','Expenses','Net cash flow']):
            card=QFrame();card.setObjectName('metricCard');l=QVBoxLayout(card);l.setContentsMargins(20,17,20,18);l.setSpacing(7);l.addWidget(text(name.upper(),'cardTitle'))
            value=text('--','cardValue');l.addWidget(value);l.addWidget(text(['Across active accounts','This reporting month','This reporting month','Income minus expenses'][i],'metricHint'));self.metrics.append(value);metrics.addWidget(card,0,i)
        root.addLayout(metrics)
        row=QHBoxLayout();row.setSpacing(16)
        trend=self.frame();tl=QVBoxLayout(trend);tl.setContentsMargins(22,18,22,18)
        tl.addWidget(text('CASH FLOW - INCOME VS EXPENSES','cardTitle'));self.chart=Bars();tl.addWidget(self.chart);row.addWidget(trend,2)
        breakdown=self.frame();bl=QVBoxLayout(breakdown);bl.setContentsMargins(22,18,22,18);bl.addWidget(text('Top spending categories','cardTitle'))
        self.category_box=QVBoxLayout();bl.addLayout(self.category_box);bl.addStretch();row.addWidget(breakdown,1)
        root.addLayout(row,2)
        card=self.frame();cl=QVBoxLayout(card);cl.addWidget(text('Recent transactions','cardTitle'))
        self.recent=table(['Date','Account','Description','Category','Amount']);cl.addWidget(self.recent);root.addWidget(card,2)

    def build_accounts(self,root):
        actions=QHBoxLayout();actions.addWidget(btn('+ Add account',self.add_account,True));actions.addWidget(btn('Transfer money',self.make_transfer));actions.addStretch();root.addLayout(actions)
        self.account_table=table(['Account','Type','Currency','Opening balance','Current balance']);root.addWidget(self.account_table)
        row=QHBoxLayout();row.addWidget(btn('Archive selected account',self.archive_account));row.addStretch();root.addLayout(row)

    def build_transactions(self,root):
        actions=QHBoxLayout();actions.addWidget(btn('+ Add transaction',self.add_transaction,True));actions.addWidget(btn('Edit selected',self.edit_transaction));actions.addWidget(btn('Delete selected',self.delete_transaction));actions.addWidget(btn('Change category',self.change_category));actions.addStretch()
        self.search=QLineEdit();self.search.setPlaceholderText('Search transactions...');self.search.setClearButtonEnabled(True);self.search.setMaximumWidth(290);self.search.setAccessibleName('Search transactions');self.search.textChanged.connect(self.refresh_transactions);actions.addWidget(self.search);root.addLayout(actions)
        self.tx_table=table(['Date','Account','Description','Category','Amount','Type / Note']);root.addWidget(self.tx_table)
        self.tx_table.doubleClicked.connect(self.edit_transaction)

    def build_import(self,root):
        card=self.frame();l=QVBoxLayout(card);l.setSpacing(15)
        l.addWidget(text('Import your statement','heading'))
        l.addWidget(text('Choose a CSV or XLSX file, map the columns and review every entry before importing.','subheading'))
        browse=btn('Choose CSV or Excel file',self.import_file,True);browse.setMinimumHeight(42);l.addWidget(browse);l.addWidget(text('Supported: CSV, XLSX  |  Dates: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY and more','subheading'))
        root.addWidget(card);root.addWidget(text('Recent imports','cardTitle'));self.history=table(['Date','File','Imported','Skipped']);root.addWidget(self.history)

    def build_budgets(self,root):
        actions=QHBoxLayout();actions.addWidget(btn('Set selected budget',self.set_budget,True));actions.addStretch();root.addLayout(actions)
        self.budget_table=table(['Category','Budget','Spent','Remaining','Utilization']);root.addWidget(self.budget_table)

    def build_reports(self,root):
        card=self.frame();v=QVBoxLayout(card);v.setSpacing(18);v.addWidget(text('Your monthly report','heading'))
        v.addWidget(text('Export filtered reports for the selected month and base currency.','subheading'))
        self.report_summary=text('');v.addWidget(self.report_summary)
        buttons=QHBoxLayout();buttons.addWidget(btn('Download PDF report',lambda:self.export('pdf'),True));buttons.addWidget(btn('Download Excel workbook',lambda:self.export('xlsx')));buttons.addWidget(btn('Export CSV',self.export_csv));buttons.addStretch();v.addLayout(buttons)
        root.addWidget(card);root.addStretch()


    def build_insights(self,root):
        card=self.frame();v=QVBoxLayout(card);v.setSpacing(12)
        v.addWidget(text('Your financial health','heading'))
        self.insight_summary=text('Loading insights...');v.addWidget(self.insight_summary)
        root.addWidget(card)
        row=QHBoxLayout()
        a=self.frame();al=QVBoxLayout(a);al.addWidget(text('Top merchants','cardTitle'))
        self.merchant_table=table(['Merchant / Description','Occurrences','Spend']);al.addWidget(self.merchant_table);row.addWidget(a)
        b=self.frame();bl=QVBoxLayout(b);bl.addWidget(text('Budget alerts','cardTitle'))
        self.alert_table=table(['Category','Over budget']);bl.addWidget(self.alert_table);row.addWidget(b)
        root.addLayout(row,1)

    def refresh_insights(self):
        data=self.db.analytics(self.month,self.currency)
        rate='N/A (no recorded income)' if data['savings_rate'] is None else f"{data['savings_rate']}%"
        self.insight_summary.setText(f"Savings rate: {rate}    |    Uncategorized: {data['uncategorized']}    |    Over budget: {len(data['over_budget'])}")
        self.merchant_table.setRowCount(0)
        for r in data['merchants']:
            put(self.merchant_table,self.merchant_table.rowCount(),[r['description'],r['count'],money(r['cents'],self.currency)])
        self.alert_table.setRowCount(0)
        for r in data['over_budget']:
            put(self.alert_table,self.alert_table.rowCount(),[r['name'],money(r['spent_cents']-r['budget_cents'],self.currency)])

    def build_goals(self,root):
        row=QHBoxLayout();row.addWidget(btn('+ New savings goal',self.add_goal,True));row.addWidget(btn('Add contribution',self.contribute_goal));row.addWidget(btn('Delete goal',self.delete_goal));row.addStretch();root.addLayout(row)
        root.addWidget(text('Goal progress is a planning ledger; contributions do not withdraw money from an account.','subheading'))
        self.goal_table=table(['Goal','Target','Saved','Remaining','Progress','Deadline']);root.addWidget(self.goal_table)

    def refresh_goals(self):
        self.goal_table.setRowCount(0)
        for g in self.db.goals(self.currency):
            pct=round(g['saved_cents']/g['target_cents']*100,1)
            put(self.goal_table,self.goal_table.rowCount(),[g['name'],money(g['target_cents'],g['currency']),money(g['saved_cents'],g['currency']),money(max(0,g['target_cents']-g['saved_cents']),g['currency']),f'{pct}%',g['deadline'] or '--'],g['id'])

    def add_goal(self):
        d,layout,form=dialog(self,'Create savings goal');name=QLineEdit();target=money_edit();deadline=date_edit();use_deadline=QCheckBox('Set deadline')
        form.addRow('Name',name);form.addRow('Target',target);form.addRow(use_deadline,deadline);finish(d,layout)
        if d.exec():self.run(lambda:self.db.add_goal(name.text(),round(target.value()*100),self.currency,deadline.date().toString('yyyy-MM-dd') if use_deadline.isChecked() else None))

    def contribute_goal(self):
        ident=self.selected(self.goal_table)
        if ident is None:return self.error('Select a savings goal')
        d,layout,form=dialog(self,'Record goal contribution');amount=money_edit();form.addRow('Contribution',amount);finish(d,layout)
        if d.exec():self.run(lambda:self.db.contribute_goal(ident,round(amount.value()*100)))

    def delete_goal(self):
        ident=self.selected(self.goal_table)
        if ident is None:return self.error('Select a savings goal')
        if QMessageBox.question(self,'Delete goal','Delete the selected savings goal?')==QMessageBox.StandardButton.Yes:self.run(lambda:self.db.delete_goal(ident))

    def build_recurring(self,root):
        row=QHBoxLayout();row.addWidget(btn('+ Schedule payment',self.add_recurring,True));row.addWidget(btn('Post selected now',self.post_recurring));row.addWidget(btn('Delete schedule',self.delete_recurring));row.addStretch();root.addLayout(row)
        root.addWidget(text('Scheduled entries are never posted automatically. Review and confirm each posting.','subheading'))
        self.recurring_table=table(['Description','Account','Category','Amount','Next date','Status']);root.addWidget(self.recurring_table)

    def refresh_recurring(self):
        self.recurring_table.setRowCount(0)
        for r in self.db.recurring():
            put(self.recurring_table,self.recurring_table.rowCount(),[r['name'],r['account_name'],r['category_name'] or 'Uncategorized',money(r['amount_cents']),r['next_date'],'Active' if r['active'] else 'Paused'],r['id'])

    def add_recurring(self):
        accounts=self.db.accounts()
        if not accounts:return self.error('Create an account first')
        d,layout,form=dialog(self,'Schedule recurring transaction');name=QLineEdit();account=QComboBox();amount=money_edit();direction=QComboBox();direction.addItems(['Expense','Income']);category=QComboBox();day=date_edit()
        for a in accounts:account.addItem(f"{a['name']} ({a['currency']})",a['id'])
        def categories():
            category.clear();category.addItem('Uncategorized',None)
            for c in self.db.categories('income' if direction.currentText()=='Income' else 'expense'):category.addItem(c['name'],c['id'])
        direction.currentTextChanged.connect(categories);categories()
        for label,w in [('Description',name),('Account',account),('Direction',direction),('Amount',amount),('Category',category),('Next due date',day)]:form.addRow(label,w)
        finish(d,layout)
        if d.exec():
            signed=round(amount.value()*100)*(-1 if direction.currentText()=='Expense' else 1)
            self.run(lambda:self.db.add_recurring(name.text(),account.currentData(),signed,category.currentData(),day.date().toString('yyyy-MM-dd')))

    def post_recurring(self):
        ident=self.selected(self.recurring_table)
        if ident is None:return self.error('Select a recurring entry')
        if QMessageBox.question(self,'Post recurring entry','Post this scheduled transaction to its account and advance the due date?')==QMessageBox.StandardButton.Yes:self.run(lambda:self.db.post_recurring(ident))

    def delete_recurring(self):
        ident=self.selected(self.recurring_table)
        if ident is None:return self.error('Select a recurring entry')
        if QMessageBox.question(self,'Delete schedule','Delete this recurring schedule? Existing transactions are unaffected.')==QMessageBox.StandardButton.Yes:self.run(lambda:self.db.delete_recurring(ident))

    def build_settings(self,root):
        card=self.frame();v=QVBoxLayout(card);v.setSpacing(18)
        v.addWidget(text('Appearance','heading'))
        r=QHBoxLayout();r.addWidget(text('Theme'));self.theme_choice=QComboBox();self.theme_choice.addItems(['Dark','Light']);self.theme_choice.setCurrentText(self.theme.title());self.theme_choice.currentTextChanged.connect(self.change_theme);r.addWidget(self.theme_choice);r.addStretch();v.addLayout(r)
        r=QHBoxLayout();r.addWidget(text('Base / reporting currency'));self.currency_choice=QComboBox();self.currency_choice.addItems(['LKR','USD','EUR','GBP','AED','MVR']);self.currency_choice.setCurrentText(self.db.setting('currency','LKR'));self.currency=self.currency_choice.currentText();self.currency_choice.currentTextChanged.connect(self.change_currency);r.addWidget(self.currency_choice);r.addStretch();v.addLayout(r)
        v.addWidget(text('Data & backups','heading'))
        v.addWidget(text('Financial records are stored on this computer. The database and manual backups are NOT encrypted. Protect your device and backup files.','subheading'))
        r=QHBoxLayout();r.addWidget(btn('Create database backup',self.backup,True));r.addWidget(btn('Open data folder',self.open_folder));r.addWidget(btn('Check database',self.check_database));r.addWidget(btn('Load demo data',self.demo));r.addStretch();v.addLayout(r)
        v.addWidget(text('Restore: close FinTrack, replace the database using a trusted backup, then reopen. Do not restore while the application is running.','subheading'))
        root.addWidget(card);root.addStretch()

    def go(self,index):
        self.stack.setCurrentIndex(index)
        for i,b in enumerate(self.nav):b.setChecked(i==index)
        self.statusBar().showMessage(f'{self.nav[index].text().strip()}  |  {self.currency}  |  {calendar.month_name[int(self.month[5:])]} {self.month[:4]}')
        if hasattr(self,'db'):self.refresh()

    def update_month(self,month):
        try:
            date.fromisoformat(month+'-01')
            if len(month)!=7:raise ValueError()
        except ValueError:
            self.error('Please select a valid reporting month');return
        self.month=month
        for inp in self.month_inputs:
            inp.set_month(month,emit=False)
        self.refresh()

    def refresh(self):
        self.refresh_dashboard();self.refresh_accounts();self.refresh_transactions();self.refresh_budgets();self.refresh_history();self.refresh_insights();self.refresh_goals();self.refresh_recurring()
        summ=self.db.monthly_summary(self.month,self.currency)
        self.report_summary.setText(f"Income  {money(summ['income'],self.currency)}     |     Expenses  {money(summ['expenses'],self.currency)}     |     Net  {money(summ['income']-summ['expenses'],self.currency)}")

    def refresh_dashboard(self):
        accounts=[a for a in self.db.accounts() if a['currency']==self.currency]
        summ=self.db.monthly_summary(self.month,self.currency)
        vals=[sum(a['balance_cents'] for a in accounts),summ['income'],summ['expenses'],summ['income']-summ['expenses']]
        for label,val in zip(self.metrics,vals):label.setText(money(val,self.currency))
        year,mon=map(int,self.month.split('-'));months=[]
        for offset in range(5,-1,-1):
            y=year+(mon-1-offset)//12;m=(mon-1-offset)%12+1
            months.append(f'{y:04d}-{m:02d}')
        self.chart.set_values([(m[5:],d['income'],d['expenses']) for m,d in self.db.trend(months,self.currency)])
        while self.category_box.count():
            item=self.category_box.takeAt(0)
            if item.widget():item.widget().deleteLater()
        spending=self.db.category_spending(self.month,self.currency)
        maximum=max([r['cents'] for r in spending]+[1])
        for r in spending[:6]:
            self.category_box.addWidget(text(f"{r['name']}   |   {money(r['cents'],self.currency)}"))
            progress=QProgressBar();progress.setTextVisible(False);progress.setValue(int(r['cents']/maximum*100));self.category_box.addWidget(progress)
        if not spending:self.category_box.addWidget(text('No spending records yet'))
        self.recent.setRowCount(0)
        for r in self.db.transactions(month=self.month,limit=30):
            if r['currency']==self.currency:put(self.recent,self.recent.rowCount(),[r['date'],r['account_name'],r['description'],r['category_name'] or ('Transfer' if r['transfer_group'] else 'Uncategorized'),money(r['amount_cents'],r['currency'])])

    def refresh_accounts(self):
        self.account_table.setRowCount(0)
        for a in self.db.accounts():put(self.account_table,self.account_table.rowCount(),[a['name'],a['kind'],a['currency'],money(a['opening_cents'],a['currency']),money(a['balance_cents'],a['currency'])],a['id'])

    def refresh_transactions(self,*_):
        self.tx_table.setRowCount(0)
        for r in self.db.transactions(self.month,search=self.search.text()):
            put(self.tx_table,self.tx_table.rowCount(),[r['date'],r['account_name'],r['description'],r['category_name'] or ('Transfer' if r['transfer_group'] else 'Uncategorized'),money(r['amount_cents'],r['currency']),r['note']],r['id'])

    def refresh_budgets(self):
        self.budget_table.setRowCount(0)
        for r in self.db.budget_rows(self.month,self.currency):
            budget=r['budget_cents'];spent=r['spent_cents'];pct=round(spent/budget*100) if budget else 0
            put(self.budget_table,self.budget_table.rowCount(),[r['name'],money(budget,self.currency),money(spent,self.currency),money(budget-spent,self.currency),f'{pct}%' if budget else 'Not set'],r['id'])

    def refresh_history(self):
        self.history.setRowCount(0)
        for r in self.db.import_history():put(self.history,self.history.rowCount(),[r['created_at'],r['filename'],r['imported'],r['skipped']])

    def selected(self,w):
        rows=w.selectionModel().selectedRows()
        return w.item(rows[0].row(),0).data(Qt.ItemDataRole.UserRole) if rows else None

    def error(self,msg):
        self.statusBar().showMessage(f'Action needed: {msg}',5000);QMessageBox.warning(self,'FinTrack',str(msg))
    def info(self,msg):
        self.statusBar().showMessage(str(msg),5000);QMessageBox.information(self,'FinTrack',str(msg))
    def run(self,callback):
        try:callback();self.refresh();self.statusBar().showMessage('Changes saved',3000)
        except Exception as e:self.error(e)

    def add_account(self):
        d,layout,form=dialog(self,'New account');name=QLineEdit();kind=QComboBox();kind.addItems(['Bank','Savings','Cash','Credit Card','Loan','Other']);currency=QComboBox();currency.addItems(['LKR','USD','EUR','GBP','AED','MVR']);amount=money_edit()
        form.addRow('Account name',name);form.addRow('Type',kind);form.addRow('Currency',currency);form.addRow('Opening balance',amount);finish(d,layout)
        if d.exec():self.run(lambda:self.db.add_account(name.text(),kind.currentText(),currency.currentText(),round(amount.value()*100)))

    def archive_account(self):
        aid=self.selected(self.account_table)
        if not aid:return self.error('Select an account first')
        if QMessageBox.question(self,'Archive account','Hide this account from the active account list? Existing transactions remain available.')==QMessageBox.StandardButton.Yes:self.run(lambda:self.db.archive_account(aid))

    def add_transaction(self):
        accounts=self.db.accounts()
        if not accounts:return self.error('Create an account first')
        d,layout,form=dialog(self,'New transaction');acc=QComboBox()
        for a in accounts:acc.addItem(f"{a['name']} ({a['currency']})",a['id'])
        day=date_edit();description=QLineEdit();kind=QComboBox();kind.addItems(['Expense','Income']);cat=QComboBox();value=money_edit();note=QLineEdit()
        def cats():
            cat.clear()
            for c in self.db.categories(kind.currentText().lower()):cat.addItem(c['name'],c['id'])
        kind.currentTextChanged.connect(cats);cats()
        for label,widget in [('Account',acc),('Date',day),('Description',description),('Type',kind),('Category',cat),('Amount',value),('Note (optional)',note)]:form.addRow(label,widget)
        finish(d,layout)
        if d.exec():
            signed=round(value.value()*100)*(1 if kind.currentText()=='Income' else -1)
            self.run(lambda:self.db.add_transaction(acc.currentData(),day.date().toString('yyyy-MM-dd'),description.text(),signed,cat.currentData(),note.text()))

    def edit_transaction(self):
        ident=self.selected(self.tx_table)
        if ident is None:return self.error('Select a transaction to edit')
        tx=self.db.con.execute('SELECT * FROM transactions WHERE id=?',(ident,)).fetchone()
        if tx['transfer_group']:return self.error('To adjust a transfer, delete and recreate it')
        d,layout,form=dialog(self,'Edit transaction')
        day=date_edit();day.setDate(QDate.fromString(tx['date'],'yyyy-MM-dd'))
        desc=QLineEdit(tx['description'])
        amount=money_edit(abs(tx['amount_cents'])/100)
        cat=QComboBox();cat.addItem('Uncategorized',None)
        for c in self.db.categories('income' if tx['amount_cents']>0 else 'expense'):
            cat.addItem(c['name'],c['id'])
            if c['id']==tx['category_id']:cat.setCurrentIndex(cat.count()-1)
        note=QLineEdit(tx['note'])
        for label,widget in [('Date',day),('Description',desc),('Amount',amount),('Category',cat),('Note',note)]:form.addRow(label,widget)
        finish(d,layout)
        if d.exec():
            signed=round(amount.value()*100)*(1 if tx['amount_cents']>0 else -1)
            self.run(lambda:self.db.edit_transaction(ident,day.date().toString('yyyy-MM-dd'),desc.text(),signed,cat.currentData(),note.text()))

    def delete_transaction(self):
        ident=self.selected(self.tx_table)
        if ident is None:return self.error('Select a transaction')
        if QMessageBox.question(self,'Delete transaction','Permanently delete this entry (and its matching transfer entry, if relevant)?')==QMessageBox.StandardButton.Yes:self.run(lambda:self.db.delete_transaction(ident))

    def change_category(self):
        ident=self.selected(self.tx_table)
        if ident is None:return self.error('Select a transaction')
        row=self.db.con.execute('SELECT amount_cents,transfer_group FROM transactions WHERE id=?',(ident,)).fetchone()
        if row['transfer_group']:return self.error('Transfers cannot have income or expense categories')
        d,layout,form=dialog(self,'Change transaction category');c=QComboBox()
        for item in self.db.categories('income' if row['amount_cents']>0 else 'expense'):c.addItem(item['name'],item['id'])
        form.addRow('Category',c);finish(d,layout)
        if d.exec():self.run(lambda:self.db.update_category(ident,c.currentData()))

    def make_transfer(self):
        accounts=self.db.accounts()
        if len(accounts)<2:return self.error('Create two accounts first')
        d,layout,form=dialog(self,'Transfer between accounts');src=QComboBox();dst=QComboBox()
        for a in accounts:
            src.addItem(f"{a['name']} ({a['currency']})",a['id']);dst.addItem(f"{a['name']} ({a['currency']})",a['id'])
        dst.setCurrentIndex(1);day=date_edit();amount=money_edit();description=QLineEdit('Internal transfer')
        for label,w in [('From account',src),('To account',dst),('Date',day),('Amount',amount),('Description',description)]:form.addRow(label,w)
        finish(d,layout)
        if d.exec():self.run(lambda:self.db.transfer(src.currentData(),dst.currentData(),day.date().toString('yyyy-MM-dd'),round(amount.value()*100),description.text()))

    def set_budget(self):
        ident=self.selected(self.budget_table)
        if ident is None:return self.error('Select a category')
        d,layout,form=dialog(self,'Set monthly budget');value=money_edit();old=self.db.con.execute('SELECT amount_cents FROM budgets WHERE month=? AND category_id=?',(self.month,ident)).fetchone()
        if old:value.setValue(old['amount_cents']/100)
        form.addRow(f'{self.month} budget ({self.currency})',value);finish(d,layout)
        if d.exec():self.run(lambda:self.db.set_budget(self.month,ident,round(value.value()*100)))

    def import_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Select bank statement','','Statements (*.csv *.xlsx)')
        if not path:return
        try:
            rows=read_rows(path)
            if len(rows)<2:raise ValueError('File must contain a header and at least one transaction')
            accounts=self.db.accounts()
            if not accounts:raise ValueError('Create an account first')
        except Exception as e:return self.error(e)
        d,layout,form=dialog(self,'Map statement columns');d.setMinimumWidth(620)
        acc=QComboBox()
        for a in accounts:acc.addItem(f"{a['name']} ({a['currency']})",a['id'])
        form.addRow('Import into account',acc)
        hdr=rows[0];choices=['-- Not mapped --']+[f'{i+1}. {str(h)[:42]}' for i,h in enumerate(hdr)]
        fields={}
        for field in ['date','description','amount','debit','credit','reference']:
            combo=QComboBox();combo.addItems(choices)
            aliases={'date':['date','transaction date','value date'],'description':['description','narration','particulars','details'],'amount':['amount','transaction amount'],'debit':['debit','withdrawal'],'credit':['credit','deposit'],'reference':['reference','ref']}
            for ix,val in enumerate(hdr):
                if str(val).strip().lower() in aliases[field]:combo.setCurrentIndex(ix+1);break
            fields[field]=combo;form.addRow(field.title(),combo)
        layout.addWidget(text('Map Amount for signed values OR both Debit and Credit for separate columns.','subheading'))
        finish(d,layout)
        if not d.exec():return
        mapping={name:widget.currentIndex()-1 for name,widget in fields.items() if widget.currentIndex()>0}
        if not all(k in mapping for k in ('date','description')):return self.error('Map Date and Description columns')
        if 'amount' not in mapping and not ('debit' in mapping and 'credit' in mapping):return self.error('Map Amount or both Debit and Credit columns')
        try:
            data=convert(rows,mapping)
        except Exception as e:return self.error(e)
        preview=QDialog(self);preview.setWindowTitle('Review imported transactions');preview.resize(850,580);v=QVBoxLayout(preview)
        v.addWidget(text(f'{len(data)} transactions found. Confirm only if amounts and signs are correct.','subheading'))
        t=table(['Date','Description','Signed amount','Reference'])
        for r in data[:500]:put(t,t.rowCount(),[r['date'],r['description'],money(r['amount_cents']),r.get('reference','')])
        v.addWidget(t);v.addWidget(text('Preview shows up to 500 rows. All validated rows will be imported.','subheading'));finish(preview,v)
        if preview.exec():
            def commit():
                count,skipped=self.db.import_records(acc.currentData(),Path(path).name,data)
                self.info(f'Imported {count} transactions. Skipped {skipped} already-imported rows.')
            self.run(commit)

    def export(self,format):
        extension='pdf' if format=='pdf' else 'xlsx'
        dest,_=QFileDialog.getSaveFileName(self,'Save finance report',f'FinTrack_{self.month}.{extension}',f'{extension.upper()} Files (*.{extension})')
        if not dest:return
        if not dest.lower().endswith('.'+extension):dest+='.'+extension
        def write():
            (pdf if format=='pdf' else xlsx)(self.db,dest,self.month,self.currency)
            self.info('Report exported successfully.')
        self.run(write)

    def export_csv(self):
        dest,_=QFileDialog.getSaveFileName(self,'Export transactions CSV',f'FinTrack_{self.month}.csv','CSV Files (*.csv)')
        if dest:
            if not dest.lower().endswith('.csv'):dest+='.csv'
            self.run(lambda:(self.db.export_transactions_csv(dest,self.month,self.currency),self.info('CSV exported successfully.')))

    def check_database(self):
        self.run(lambda:self.info('Database integrity: '+self.db.database_check()))

    def backup(self):
        dest,_=QFileDialog.getSaveFileName(self,'Save unencrypted database backup',f'fintrack_backup_{date.today()}.db','SQLite Database (*.db)')
        if dest:
            if not dest.lower().endswith('.db'):dest+='.db'
            self.run(lambda:(self.db.backup(dest),self.info('Backup saved. This file is NOT encrypted.')))

    def open_folder(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.db.path).parent)))

    def demo(self):
        if QMessageBox.question(self,'Sample data','Load demonstration accounts and transactions? This only works when no accounts exist.')==QMessageBox.StandardButton.Yes:
            self.run(lambda:self.info('Demo data created.' if self.db.seed_demo() else 'Accounts already exist. Demo load skipped.'))

    def change_theme(self,value):
        self.theme=value.lower();self.db.set_setting('theme',self.theme);self.apply_theme()

    def change_currency(self,value):
        self.currency=value;self.db.set_setting('currency',value);self.refresh()

    def apply_theme(self):
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(DARK if self.theme=='dark' else LIGHT)
