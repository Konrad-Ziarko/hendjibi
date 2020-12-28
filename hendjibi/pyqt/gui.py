import atexit
import random
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QAction, QFileDialog, QDesktopWidget

from hendjibi import PROJECT_NAME
from hendjibi.pyqt.consts import QCOLOR_DARK, QCOLOR_HIGHLIGHT, QCOLOR_WHITE
from hendjibi.pyqt.widgets import MainWidget, NewEntryDialog
from hendjibi.tools.app_logger import get_logger
from hendjibi.tools.misc import get_resource_path
from hendjibi.tools.translator import translate as _
from hendjibi.model.dac import DataManager
from hendjibi.model.entry import EntryType, ProgressStatus

logger = get_logger(__name__)


GUI_HINTS = [
    '',
]


class Application(QApplication):
    def __init__(self, config, args):
        QApplication.__init__(self, args)
        self.setStyle('fusion')
        self.setWindowIcon(QIcon(get_resource_path('icons/favicon.png')))
        self._default_palette = self.palette()

        gui = GUI(self, config)
        gui.connect_action(self.set_dark_palette, self.set_default_palette)
        atexit.register(gui.before_exit)
        gui.redraw_palette(config.dark_mode)

    def set_dark_palette(self):
        p = self.palette()
        p.setColor(QPalette.Window, QCOLOR_DARK)
        p.setColor(QPalette.Button, QCOLOR_DARK)
        p.setColor(QPalette.Highlight, QCOLOR_HIGHLIGHT)
        p.setColor(QPalette.ButtonText, QCOLOR_WHITE)
        p.setColor(QPalette.PlaceholderText, QCOLOR_WHITE)
        p.setColor(QPalette.Background, QCOLOR_DARK)
        p.setColor(QPalette.Base, QCOLOR_DARK)
        p.setColor(QPalette.Text, QCOLOR_WHITE)
        p.setColor(QPalette.PlaceholderText, QCOLOR_WHITE)
        p.setColor(QPalette.Foreground, QCOLOR_WHITE)
        self.setPalette(p)

    def set_default_palette(self):
        self.setPalette(self._default_palette)


class GUI(QMainWindow):
    def __init__(self, qt_app, config):
        QMainWindow.__init__(self)
        self.set_dark_palette = None
        self.set_default_palette = None

        self.qt_app = qt_app
        self.config = config
        self.setWindowTitle(PROJECT_NAME)
        self.data_manager = DataManager(self.config.data_dump_path)
        self.main_widget = MainWidget(self.config, self.data_manager)
        self.main_widget.connect_actions(self.show_msg_on_status_bar)
        self.setCentralWidget(self.main_widget)
        self.init_menu_bar()
        self.change_sot(self.config.stay_on_top)
        self.resize(self.config.width, self.config.height)
        qt_rect = self.frameGeometry()
        qt_rect.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(qt_rect.topLeft())

        self.show()
        self.show_msg_on_status_bar(random.choice(GUI_HINTS))

    def connect_action(self, set_dark_palette, set_default_palette):
        self.set_dark_palette = set_dark_palette
        self.set_default_palette = set_default_palette

    def import_db(self):
        # TODO
        path = str(QFileDialog.getExistingDirectory(self, _('Select Directory')))
        if path:
            self.show_msg_on_status_bar(_(F'Loaded DB from {self.config.db_path}'))

    def export_db(self):
        # TODO
        path = str(QFileDialog.getExistingDirectory(self, _('Select Directory')))
        if path:
            self.show_msg_on_status_bar(_(F'Loaded DB from {self.config.db_path}'))

    def filter_type_changed(self, entry_name, is_checked):
        setattr(self.config, entry_name.lower(), is_checked)
        self.main_widget.filter_type_changed(entry_name, is_checked)

    def filter_status_changed(self, entry_name, is_checked):
        setattr(self.config, entry_name.lower(), is_checked)
        self.main_widget.filter_status_changed(entry_name, is_checked)

    def add_filter(self, name, filter_menu, function):
        a = QAction(_(name), self)
        a.setCheckable(True)
        a.triggered.connect(lambda: function(name, a.isChecked()))
        filter_menu.addAction(a)
        a.setChecked(not getattr(self.config, name.lower()))
        a.trigger()

    def init_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu(_('File'))
        entry_menu = menu_bar.addMenu(_('Entry'))
        filter_menu = menu_bar.addMenu(_('Filter'))
        view_menu = menu_bar.addMenu(_('View'))

        redraw_on_release_grid_action = QAction(_('Refresh on slider release'), self)
        redraw_on_release_grid_action.setCheckable(True)
        redraw_on_release_grid_action.setChecked(True)
        view_menu.addAction(redraw_on_release_grid_action)
        redraw_on_release_grid_action.triggered.connect(lambda: self.change_redraw_on_release(redraw_on_release_grid_action.isChecked()))
        redraw_on_release_grid_action.setChecked(self.config.redraw_on_release)
        self.change_redraw_on_release(self.config.redraw_on_release)

        imp_act = QAction(_('Import db'), self)
        imp_act.triggered.connect(self.import_db)
        file_menu.addAction(imp_act)

        exp_act = QAction(_('Export db'), self)
        exp_act.triggered.connect(self.export_db)
        file_menu.addAction(exp_act)

        aot_menu = QAction(_('Stay on top'), self)
        aot_menu.setCheckable(True)
        aot_menu.triggered.connect(lambda: self.change_sot(aot_menu.isChecked()))
        view_menu.addAction(aot_menu)
        aot_menu.setChecked(self.config.stay_on_top)

        dark_mode = QAction(_('Dark mode'), self)
        dark_mode.setCheckable(True)
        dark_mode.triggered.connect(lambda: self.redraw_palette(dark_mode.isChecked()))
        view_menu.addAction(dark_mode)
        dark_mode.setChecked(self.config.dark_mode)

        new_entry = QAction(_('Add new entry'), self)
        new_entry.triggered.connect(self.add_new_entry)  # TODO
        entry_menu.addAction(new_entry)

        filter_menu.addSection('Entry type')
        for entry_type in EntryType:
            self.add_filter(entry_type.value, filter_menu, self.filter_type_changed)

        filter_menu.addSeparator()
        filter_menu.addSection('Progress status')
        for entry_status in ProgressStatus:
            self.add_filter(entry_status.value, filter_menu, self.filter_status_changed)

    def change_redraw_on_release(self, redraw_on_release):
        self.config.redraw_on_release = redraw_on_release
        self.main_widget.change_slider_action(redraw_on_release)

    def redraw_palette(self, is_dark_mode):
        self.config.dark_mode = is_dark_mode
        if self.config.dark_mode:
            self.set_dark_palette()
        else:
            self.set_default_palette()

    def before_exit(self):
        self.config.width = self.frameSize().width()
        self.config.height = self.frameSize().height()
        self.config.write_config()
        self.data_manager.save_dump()

    def change_sot(self, is_checked):
        self.config.stay_on_top = is_checked
        flags = QtCore.Qt.WindowFlags()
        hint = QtCore.Qt.WindowStaysOnTopHint
        if is_checked:
            self.setWindowFlags(flags | hint)
        else:
            self.setWindowFlags(flags & ~hint)
        self.show()

    def show_msg_on_status_bar(self, string: str = ''):
        self.statusBar().showMessage(string)

    def show_msg_window(self, title, msg):
        QMessageBox.question(self, title, msg, QMessageBox.Ok)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        QtWidgets.QMainWindow.resizeEvent(self, event)

    def add_new_entry(self):
        my_dialog = NewEntryDialog(self)
        my_dialog.exec_()
        if my_dialog.submitted is True:
            new_entry = my_dialog.get_values()
            self.data_manager.add_entry(new_entry)
            self.main_widget.add_entry(new_entry)


def start_gui(config):
    return_code = -1
    try:
        return_code = Application(config, sys.argv).exec_()
    except Exception as e:
        logger.critical(_(F'Application failed due to an error: {e}'))
    finally:
        sys.exit(return_code)
