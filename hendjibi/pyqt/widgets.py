from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPaintEvent, QPainter, QIcon, QPixmap, QIntValidator
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget, QScrollArea, QGroupBox, \
    QSlider, QDialog, QLabel, QLineEdit, QCheckBox, QComboBox, QPlainTextEdit, QFileDialog, QDateEdit, QToolButton

from hendjibi.tools.app_logger import get_logger
from hendjibi.tools.translator import translate as _
from hendjibi.model.entry import GenericEntry, EntryType, ProgressStatus, EntryStatus
from hendjibi.pyqt.qt_layout import FlowLayout
from hendjibi.tools.config import SLIDER_MAX, SLIDER_MIN

logger = get_logger(__name__)


class IconButton(QToolButton):
    def __init__(self, data_entry, parent=None):
        QToolButton.__init__(self, parent)
        self.data_entry = data_entry
        self.setText(repr(data_entry))

    def mouseDoubleClickEvent(self, a0) -> None:
        print(F"double pressed [{repr(self.data_entry)}]")


class ListWidget(QListWidget):
    def __init__(self, default_string=_('No Items')):
        QListWidget.__init__(self)
        self.default_string = default_string

    def paintEvent(self, e: QPaintEvent) -> None:
        QListWidget.paintEvent(self, e)
        if self.model() and self.model().rowCount(self.rootIndex()) > 0:
            return
        p = QPainter(self.viewport())
        p.drawText(self.rect(), QtCore.Qt.AlignCenter, self.default_string)


class MainWidget(QWidget):
    def connect_actions(self, show_msg_on_status_bar):
        self.show_msg_on_status_bar = show_msg_on_status_bar

    def add_entry(self, entry):
        if entry.entry_type.value not in self.group_boxes:
            g = QGroupBox(entry.entry_type.value)
            layout = FlowLayout(margin=10)
            g.setLayout(layout)
            self.group_boxes[entry.entry_type.value] = (g, layout)
            self.container_layout.addWidget(g)
        button = IconButton(entry, self)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        qp = QPixmap()
        qp.loadFromData(entry.cover_image)
        button.setIcon(QIcon(qp))
        self.change_cover_size(None, button)
        self.group_boxes[entry.entry_type.value][1].addWidget(button)

    def load_with_data(self):
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().deleteLater()
        for k, v in self.group_boxes.items():
            group_box, flow_layout = v
            group_box.deleteLater()
            for i in range(flow_layout.count()):
                flow_layout.itemAt(i).widget().deleteLater()
            flow_layout.deleteLater()

        for entry in self.data_manager.iterate_entries():
            self.add_entry(entry)
        ##
        self.container_layout.addStretch()
        self.container.setLayout(self.container_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.container)
        self.main_layout.addWidget(scroll_area)

    def __init__(self, config, data_manager):
        QWidget.__init__(self)
        self.show_msg_on_status_bar = None
        self.group_boxes = {}
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.config = config
        self.data_manager = data_manager  # type: DataManager

        self.root_layout = QVBoxLayout(self)
        self.cover_size_slider = QSlider(Qt.Horizontal)
        self.cover_size_slider.setMinimum(SLIDER_MIN)
        self.cover_size_slider.setMaximum(SLIDER_MAX)
        self.cover_size_slider.setValue(self.config.slider)
        self.change_slider_action(on_release=True)
        self.root_layout.addWidget(self.cover_size_slider)
        self.main_layout = QVBoxLayout(self)
        self.root_layout.addLayout(self.main_layout)

        self.load_with_data()

        self.setLayout(self.root_layout)

    def filter_type_changed(self, entry_name, is_checked):
        if entry_name in self.group_boxes:
            group = self.group_boxes[entry_name][0]
            if is_checked is True:
                group.show()
            else:
                group.hide()

    def filter_status_changed(self, entry_name, is_checked):
        pass

    def change_slider_action(self, on_release=True):
        if on_release is True:
            try:
                self.cover_size_slider.valueChanged.disconnect()
            except:
                pass
            finally:
                self.cover_size_slider.sliderReleased.connect(self.change_cover_size)
        else:
            try:
                self.cover_size_slider.sliderReleased.disconnect()
            except:
                pass
            finally:
                self.cover_size_slider.valueChanged.connect(self.change_cover_size)

    def refresh_entries(self):
        pass

    @staticmethod
    def _resize_object(obj, max_size):
        img_w = obj.iconSize().width()
        img_h = obj.iconSize().height()
        ratio_w_h = img_w / img_h
        if img_w > img_h:
            img_w = max_size
            img_h = max_size / ratio_w_h
        else:
            img_h = max_size
            img_w = max_size * ratio_w_h
        obj.setIconSize(QSize(img_w, img_h))

    def change_cover_size(self, _=None, obj=None):
        self.config.slider = self.cover_size_slider.value()
        icon_max_w_h = self.cover_size_slider.value()
        if obj is not None:
            self._resize_object(obj, icon_max_w_h)
        else:
            for k, v in self.group_boxes.items():
                group_box, flow_layout = v
                for o in group_box.children():
                    if isinstance(o, IconButton):
                        self._resize_object(o, icon_max_w_h)


class NewEntryDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.submitted = False
        self.cover_bytes = b''
        self.setWindowTitle('Add new entry')
        self.container = QWidget()
        self.horizontal_layout = QHBoxLayout()
        self.container_left_layout = QVBoxLayout()
        self.container_right_layout = QVBoxLayout()
        self.horizontal_layout.addLayout(self.container_left_layout)
        self.horizontal_layout.addLayout(self.container_right_layout)

        label_type = QLabel(_('Entry type:'))
        self.combo_type = QComboBox()
        label_type.setBuddy(self.combo_type)
        for entry in EntryType:
            self.combo_type.addItem(entry.value, entry)

        label_status = QLabel(_('Entry status:'))
        self.combo_status = QComboBox()
        label_status.setBuddy(self.combo_status)
        for entry in EntryStatus:
            self.combo_status.addItem(entry.value, entry)

        label_progress = QLabel(_('Progress status:'))
        self.combo_progress = QComboBox()
        label_progress.setBuddy(self.combo_progress)
        for entry in ProgressStatus:
            self.combo_progress.addItem(entry.value, entry)

        label_org_name = QLabel(_('Entry original name:'))
        self.line_org_name = QLineEdit()
        label_org_name.setBuddy(self.line_org_name)

        label_eng_name = QLabel(_('Entry english name:'))
        self.line_eng_name = QLineEdit()
        label_eng_name.setBuddy(self.line_eng_name)

        label_synonyms = QLabel(_('Synonym names:'))
        self.line_synonyms = QLineEdit()
        label_synonyms.setBuddy(self.line_synonyms)

        label_description = QLabel(_('Description:'))
        self.description_textbox = QPlainTextEdit()
        label_description.setBuddy(self.description_textbox)

        self.nsfw = QCheckBox(_('NSFW'))

        only_int = QIntValidator(bottom=0)
        label_current_progress = QLabel(_('Current progress:'))
        self.current_progress_textbox = QLineEdit()
        label_current_progress.setBuddy(self.current_progress_textbox)
        self.current_progress_textbox.setValidator(only_int)
        label_current_progress.setBuddy(self.current_progress_textbox)

        label_max_progress = QLabel(_('Max progress:'))
        self.max_progress_textbox = QLineEdit()
        label_max_progress.setBuddy(self.max_progress_textbox)
        self.max_progress_textbox.setValidator(only_int)
        label_max_progress.setBuddy(self.max_progress_textbox)

        label_release_date = QLabel(_('Release date:'))
        self.release_date1 = QDateEdit()
        self.release_date2 = QDateEdit()
        label_release_date.setBuddy(self.release_date1)
        label_release_date.setBuddy(self.release_date2)

        self.cover = QLabel("Cover:")
        self.load_cover_button = QPushButton(_('Load cover'))
        self.load_cover_button.clicked.connect(self.load_image)

        self.accept_button = QPushButton(_('Add'))

        self.container_left_layout.addWidget(self.cover)
        self.container_left_layout.addWidget(self.load_cover_button)

        self.container_right_layout.addWidget(label_type)
        self.container_right_layout.addWidget(self.combo_type)
        self.container_right_layout.addWidget(label_status)
        self.container_right_layout.addWidget(self.combo_status)
        self.container_right_layout.addWidget(label_progress)
        self.container_right_layout.addWidget(self.combo_progress)

        self.container_right_layout.addWidget(label_org_name)
        self.container_right_layout.addWidget(self.line_org_name)
        self.container_right_layout.addWidget(label_eng_name)
        self.container_right_layout.addWidget(self.line_eng_name)
        self.container_right_layout.addWidget(label_synonyms)
        self.container_right_layout.addWidget(self.line_synonyms)

        self.container_right_layout.addWidget(label_description)
        self.container_right_layout.addWidget(self.description_textbox)

        self.container_right_layout.addWidget(self.nsfw)

        self.container_right_layout.addWidget(label_current_progress)
        self.container_right_layout.addWidget(self.current_progress_textbox)
        self.container_right_layout.addWidget(label_max_progress)
        self.container_right_layout.addWidget(self.max_progress_textbox)

        self.container_right_layout.addWidget(label_release_date)
        date_layout = QHBoxLayout()
        date_layout.addWidget(self.release_date1)
        date_layout.addWidget(self.release_date2)
        self.container_right_layout.addLayout(date_layout)

        self.container_right_layout.addWidget(self.accept_button)

        self.root_layout = QVBoxLayout(self)
        self.main_layout = QVBoxLayout(self)
        self.root_layout.addLayout(self.main_layout)
        self.container.setLayout(self.horizontal_layout)
        self.main_layout.addWidget(self.container)
        self.setLayout(self.root_layout)

        self.accept_button.clicked.connect(self.submit)

    def submit(self):
        self.submitted = True
        self.close()

    def load_image(self):
        fname = QFileDialog.getOpenFileName(self, 'Select entry cover')
        image_path = fname[0]
        self.cover_bytes = open(image_path, 'rb').read()
        qp = QPixmap()
        qp.loadFromData(self.cover_bytes)
        self.cover.setPixmap(qp)

    def get_values(self):
        entry_status = self.combo_status.currentData()
        entry_type = self.combo_type.currentData()
        entry_progress = self.combo_progress.currentData()
        date1 = self.release_date1.date().toPyDate()
        date2 = self.release_date2.date().toPyDate()
        try:
            current_progress = int(self.current_progress_textbox.text())
        except:
            current_progress = 0
        try:
            max_progress = int(self.max_progress_textbox.text())
        except:
            max_progress = -1

        entry = GenericEntry(self.cover_bytes, self.line_eng_name.text(), self.line_org_name.text(),
                             self.line_synonyms.text(), date1, date2, entry_status,
                             self.description_textbox.toPlainText(), self.nsfw.isChecked(), entry_type,
                             current_progress, max_progress, entry_progress)
        return entry
