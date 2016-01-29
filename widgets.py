from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six
from skimage.viewer.widgets import BaseWidget, CheckBox, Text, ComboBox
from skimage.viewer.qt import Qt, QtWidgets, QtCore, Signal
from time import time


class DockWidget(QtWidgets.QDockWidget):
    """A QDockWidget that emits a signal when closed."""
    close_event_signal = Signal()

    def closeEvent(self, event):
        self.close_event_signal.emit()
        super(DockWidget, self).closeEvent(event)


class VideoTimer(QtCore.QTimer):
    next_frame = Signal(int)
    def __init__(self, *args):
        super(VideoTimer, self).__init__(*args)
        self.timeout.connect(self.next)
        self.index = None
        self._len = None

    @property
    def fps(self):
        return 1 / self._interval
    @fps.setter
    def fps(self, value):
        self._interval = 1 / value
        self.setInterval(self._interval * 1000)

    def start(self, index, length):
        self.start_index = index
        self._len = length
        self.start_time = time()
        super(VideoTimer, self).start()

    def stop(self):
        super(VideoTimer, self).stop()
        self.start_index = None
        self._len = None
        self.start_time = None

    def next(self):
        index = int((time() - self.start_time) // self._interval)
        index = (index + self.start_index) % self._len
        self.next_frame.emit(index)


class Slider(BaseWidget):
    """Slider widget for adjusting numeric parameters.

    Parameters
    ----------
    name : str
        Name of slider parameter. If this parameter is passed as a keyword
        argument, it must match the name of that keyword argument (spaces are
        replaced with underscores). In addition, this name is displayed as the
        name of the slider.
    low, high : float
        Range of slider values.
    value : float
        Default slider value. If None, use midpoint between `low` and `high`.
    value_type : {'float' | 'int'}, optional
        Numeric type of slider value.
    ptype : {'kwarg' | 'arg' | 'plugin'}, optional
        Parameter type.
    callback : callable f(widget_name, value), optional
        Callback function called in response to slider changes.
        *Note:* This function is typically set (overridden) when the widget is
        added to a plugin.
    orientation : {'horizontal' | 'vertical'}, optional
        Slider orientation.
    update_on : {'release' | 'move'}, optional
        Control when callback function is called: on slider move or release.
    """
    def __init__(self, name, low=0.0, high=1.0, value=None, value_type='float',
                 ptype='kwarg', callback=None, max_edit_width=60,
                 orientation='horizontal', update_on='release'):
        super(Slider, self).__init__(name, ptype, callback)

        if value is None:
            value = (high - low) / 2.

        # Set widget orientation
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if orientation == 'vertical':
            self.slider = QtWidgets.QSlider(Qt.Vertical)
            alignment = QtCore.Qt.AlignHCenter
            align_text = QtCore.Qt.AlignHCenter
            align_value = QtCore.Qt.AlignHCenter
            self.layout = QtWidgets.QVBoxLayout(self)
        elif orientation == 'horizontal':
            self.slider = QtWidgets.QSlider(Qt.Horizontal)
            alignment = QtCore.Qt.AlignVCenter
            align_text = QtCore.Qt.AlignLeft
            align_value = QtCore.Qt.AlignRight
            self.layout = QtWidgets.QHBoxLayout(self)
        else:
            msg = "Unexpected value %s for 'orientation'"
            raise ValueError(msg % orientation)
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # Set slider behavior for float and int values.
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if value_type == 'float':
            # divide slider into 1000 discrete values
            slider_max = 1000
            self._scale = float(high - low) / slider_max
            self.slider.setRange(0, slider_max)
            self.value_fmt = '%2.2f'
        elif value_type == 'int':
            self.slider.setRange(low, high)
            self.value_fmt = '%d'
        else:
            msg = "Expected `value_type` to be 'float' or 'int'; received: %s"
            raise ValueError(msg % value_type)
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.value_type = value_type
        self._low = low
        self._high = high
        # Update slider position to default value
        self.val = value

        if update_on == 'move':
            self.slider.valueChanged.connect(self._on_slider_changed)
        elif update_on == 'release':
            self.slider.sliderReleased.connect(self._on_slider_changed)
        else:
            raise ValueError("Unexpected value %s for 'update_on'" % update_on)
        self.slider.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.name_label = QtWidgets.QLabel()
        self.name_label.setText(self.name)
        self.name_label.setAlignment(align_text)

        self.editbox = QtWidgets.QLineEdit()
        self.editbox.setMaximumWidth(max_edit_width)
        self.editbox.setText(self.value_fmt % self.val)
        self.editbox.setAlignment(align_value)
        self.editbox.editingFinished.connect(self._on_editbox_changed)

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.editbox)

    def _on_slider_changed(self):
        """Call callback function with slider's name and value as parameters"""
        value = self.val
        self.editbox.setText(str(value))
        self.callback(self.name, value)

    def _on_editbox_changed(self):
        """Validate input and set slider value"""
        try:
            value = float(self.editbox.text())
        except ValueError:
            self._bad_editbox_input()
            return
        if not self._low <= value <= self._high:
            self._bad_editbox_input()
            return

        self.val = value
        self._good_editbox_input()
        self.callback(self.name, value)

    def _good_editbox_input(self):
        self.editbox.setStyleSheet("background-color: rgb(255, 255, 255)")

    def _bad_editbox_input(self):
        self.editbox.setStyleSheet("background-color: rgb(255, 200, 200)")

    @property
    def val(self):
        value = self.slider.value()
        if self.value_type == 'float':
            value = value * self._scale + self._low
        return value

    @val.setter
    def val(self, value):
        if self.value_type == 'float':
            value = (value - self._low) / self._scale
            value_str = '{0:.4f}'.format(value)
        else:
            value_str = str(value)
        self.slider.setValue(value)
        try:
            self.editbox.setText(value_str)
        except AttributeError:
            pass