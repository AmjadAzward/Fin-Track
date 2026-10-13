"""Launch FinTrack desktop application."""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from fintrack.db import FinanceDB
from fintrack.ui import MainWindow


def data_location():
    if sys.platform=='win32':
        import os
        return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData'/'Local'))/'FinTrack'/'fintrack.db'
    if sys.platform=='darwin':return Path.home()/'Library'/'Application Support'/'FinTrack'/'fintrack.db'
    return Path.home()/'.local'/'share'/'FinTrack'/'fintrack.db'


def main():
    app=QApplication(sys.argv)
    app.setApplicationName('FinTrack')
    db=FinanceDB(data_location())
    win=MainWindow(db);win.show()
    code=app.exec();db.close();return code

if __name__=='__main__':sys.exit(main())
