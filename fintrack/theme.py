"""Application-wide visual themes for FinTrack."""

COMMON = r'''
* { font-family: "Segoe UI", "Inter", "Arial"; font-size: 13px; }
QWidget { outline: none; }
QLabel { background: transparent; }
QLabel#brand { font-size: 27px; font-weight: 800; letter-spacing: .4px; }
QLabel#eyebrow { font-size: 10px; font-weight: 700; letter-spacing: 1.4px; }
QLabel#heading { font-size: 27px; font-weight: 750; }
QLabel#sectionTitle { font-size: 17px; font-weight: 700; }
QLabel#subheading { font-size: 13px; }
QLabel#cardTitle { font-size: 11px; font-weight: 700; letter-spacing: .5px; }
QLabel#cardValue { font-size: 24px; font-weight: 750; }
QLabel#metricHint { font-size: 11px; }
QFrame#card { border-radius: 14px; }
QFrame#metricCard { border-radius: 14px; }
QFrame#heroCard { border-radius: 16px; }
QPushButton { border-radius: 8px; padding: 9px 14px; font-weight: 600; min-height: 20px; }
QPushButton:focus { border-width: 2px; }
QPushButton:disabled { color: #7f8c99; }
QPushButton#primary { border: 0; }
QPushButton#danger { color: #e35d6a; }
QPushButton#nav { background: transparent; text-align: left; border: 0; border-radius: 8px; padding: 11px 13px; font-weight: 600; }
QPushButton#nav:checked { border-left-width: 3px; border-left-style: solid; }
QPushButton#iconButton { padding: 7px; min-width: 20px; }
QPushButton#selectedMonth { border-width: 1px; }
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox {
    border-radius: 8px; padding: 8px 10px; min-height: 20px;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus { border-width: 2px; }
QComboBox::drop-down { border: 0; width: 28px; }
QTableWidget { border-radius: 11px; gridline-color: transparent; selection-behavior: select-rows; }
QHeaderView::section { border: 0; padding: 10px 9px; font-size: 11px; font-weight: 700; }
QTableWidget::item { padding: 8px; border-bottom-width: 1px; border-bottom-style: solid; }
QScrollBar:vertical { width: 10px; margin: 2px; }
QScrollBar:horizontal { height: 10px; margin: 2px; }
QScrollBar::handle { border-radius: 4px; min-height: 28px; min-width: 28px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QProgressBar { border: none; border-radius: 4px; height: 8px; }
QProgressBar::chunk { border-radius: 4px; }
QDialog { border-radius: 12px; }
QDialogButtonBox QPushButton { min-width: 82px; }
QStatusBar { font-size: 11px; }
QToolTip { padding: 7px 9px; border-radius: 5px; }
'''

DARK = COMMON + r'''
QWidget { background: #0b1220; color: #e8eef7; }
QMainWindow, QDialog { background: #0b1220; }
QFrame#sidebar { background: #0e192a; border-right: 1px solid #1e2e44; }
QLabel#brand { color: #65e6c4; }
QLabel#eyebrow, QLabel#cardTitle { color: #8fa3ba; }
QLabel#subheading, QLabel#metricHint { color: #91a3b8; }
QFrame#card, QFrame#metricCard { background: #121f33; border: 1px solid #24364e; }
QFrame#heroCard { background: #11283a; border: 1px solid #245064; }
QPushButton { background: #182b43; color: #ecf3fa; border: 1px solid #2c425e; }
QPushButton:hover { background: #223a57; border-color: #3d5a78; }
QPushButton:pressed { background: #102238; }
QPushButton:focus { border-color: #55dcbc; }
QPushButton:disabled { background: #142235; border-color: #26364a; }
QPushButton#primary { background: #28c6a4; color: #052521; }
QPushButton#primary:hover { background: #61e2c6; }
QPushButton#nav { color: #aab9ca; }
QPushButton#nav:hover { background: #162740; color: #f2f7fb; }
QPushButton#nav:checked { background: #173c3d; color: #70e8cb; border-left-color: #47d5b4; }
QPushButton#selectedMonth { background: #28c6a4; color: #052521; border-color: #28c6a4; }
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox { background: #101e31; border: 1px solid #30465f; color: #f2f6fb; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus { border-color: #42d3b1; }
QComboBox QAbstractItemView { background: #182a41; color: #f2f6fb; selection-background-color: #236252; }
QTableWidget { background: #101d30; alternate-background-color: #13233a; border: 1px solid #263b54; selection-background-color: #205d53; }
QHeaderView::section { background: #182a42; color: #9fb3c8; }
QTableWidget::item { border-bottom-color: #20334a; }
QScrollBar { background: #0e1929; }
QScrollBar::handle { background: #3a516b; }
QProgressBar { background: #26384d; }
QProgressBar::chunk { background: #2ec9a6; }
QStatusBar { background: #0e192a; color: #8fa3b8; border-top: 1px solid #1e2e44; }
QToolTip { background: #192a40; color: #eef5fb; border: 1px solid #3b526d; }
'''

LIGHT = COMMON + r'''
QWidget { background: #f5f7fa; color: #172b3d; }
QMainWindow, QDialog { background: #f5f7fa; }
QFrame#sidebar { background: #ffffff; border-right: 1px solid #dce5ed; }
QLabel#brand { color: #087f6c; }
QLabel#eyebrow, QLabel#cardTitle { color: #687d91; }
QLabel#subheading, QLabel#metricHint { color: #697d90; }
QFrame#card, QFrame#metricCard { background: #ffffff; border: 1px solid #dfe7ee; }
QFrame#heroCard { background: #edf9f6; border: 1px solid #bfe6dc; }
QPushButton { background: #ffffff; color: #213c52; border: 1px solid #d5e0e9; }
QPushButton:hover { background: #eef4f7; border-color: #bdccd9; }
QPushButton:pressed { background: #e4edf2; }
QPushButton:focus { border-color: #109b82; }
QPushButton:disabled { background: #f1f4f6; border-color: #e0e6eb; }
QPushButton#primary { background: #0f967e; color: #ffffff; }
QPushButton#primary:hover { background: #087b67; }
QPushButton#nav { color: #617589; }
QPushButton#nav:hover { background: #f0f5f7; color: #18374b; }
QPushButton#nav:checked { background: #def3ed; color: #087762; border-left-color: #10a589; }
QPushButton#selectedMonth { background: #0f967e; color: #ffffff; border-color: #0f967e; }
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox { background: #ffffff; border: 1px solid #cedae4; color: #172b3d; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus { border-color: #109b82; }
QComboBox QAbstractItemView { background: #ffffff; color: #172b3d; selection-background-color: #cceee5; }
QTableWidget { background: #ffffff; alternate-background-color: #f7f9fb; border: 1px solid #dce5ec; selection-background-color: #cceee5; selection-color: #12362f; }
QHeaderView::section { background: #eef3f6; color: #607487; }
QTableWidget::item { border-bottom-color: #e9eef2; }
QScrollBar { background: #edf2f5; }
QScrollBar::handle { background: #b5c4d0; }
QProgressBar { background: #e3eaef; }
QProgressBar::chunk { background: #10a589; }
QStatusBar { background: #ffffff; color: #687d91; border-top: 1px solid #dce5ed; }
QToolTip { background: #ffffff; color: #172b3d; border: 1px solid #cbd8e2; }
'''
