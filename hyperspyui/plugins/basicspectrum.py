# -*- coding: utf-8 -*-
"""
Created on Sun Mar 01 15:20:55 2015

@author: Vidar Tonaas Fauske
"""

from hyperspyui.plugins.plugin import Plugin

from python_qt_binding import QtGui, QtCore
from QtCore import *
from QtGui import *

from hyperspyui.widgets.elementpicker import ElementPickerWidget
from hyperspyui.threaded import Threaded
from hyperspyui.util import win2sig, load_cursor
from hyperspyui.tools import SelectionTool, SignalFigureTool

import hyperspy.signals
from hyperspy.misc.eds.utils import _get_element_and_line
import numpy as np

import os
from functools import partial


def tr(text):
    return QCoreApplication.translate("BasicSpectrumPlugin", text)


class Namespace:
    pass


QWIDGETSIZE_MAX = 16777215


class SignalTypeFilter(object):

    def __init__(self, signal_type, ui, space=None):
        self.signal_type = signal_type
        self.ui = ui
        self.space = space

    def __call__(self, win, action):
        sig = win2sig(win, self.ui.signals, self.ui._plotting_signal)
        valid = sig is not None and isinstance(sig.signal, self.signal_type)
        if valid and self.space:
            # Check that we have right figure
            if not ((self.space == "navigation" and win is sig.navigator_plot)
                    or
                    (self.space == "signal" and win is sig.signal_plot)):
                valid = False
        action.setEnabled(valid)


class BasicSpectrumPlugin(Plugin):
    name = "Basic spectrum tools"

    def create_actions(self):
        self.add_action('remove_background', "Remove Background",
                        self.remove_background,
                        icon='power_law.svg',
                        tip="Interactively define the background, and " +
                            "remove it",
                        selection_callback=SignalTypeFilter(
                            hyperspy.signals.Spectrum, self.ui))

        self.add_action('fourier_ratio', "Fourier Ratio Deconvoloution",
                        self.fourier_ratio,
                        icon='fourier_ratio.svg',
                        tip="Use the Fourier-Ratio method" +
                        " to deconvolve one signal from another",
                        selection_callback=SignalTypeFilter(
                            hyperspy.signals.EELSSpectrum, self.ui))

        self.add_action('estimate_thickness', "Estimate thickness",
                        self.estimate_thickness,
                        icon="t_over_lambda.svg",
                        tip="Estimates the thickness (relative to the mean " +
                        "free path) of a sample using the log-ratio method.",
                        selection_callback=SignalTypeFilter(
                            hyperspy.signals.EELSSpectrum, self.ui))

    def create_menus(self):
        self.add_menuitem("EELS", self.ui.actions['remove_background'])
        self.add_menuitem('EELS', self.ui.actions['fourier_ratio'])
        self.add_menuitem('EELS', self.ui.actions['estimate_thickness'])

    def create_toolbars(self):
        self.add_toolbar_button("EELS", self.ui.actions['remove_background'])
        self.add_toolbar_button("EELS", self.ui.actions['fourier_ratio'])
        self.add_toolbar_button("EELS", self.ui.actions['estimate_thickness'])

    def create_tools(self):
        try:
            from hyperspy.misc.eds.utils import get_xray_lines_near_energy as _
            self.picker_tool = ElementPickerTool()
            self.picker_tool.picked[basestring].connect(self.pick_element)
            self.add_tool(self.picker_tool,
                          SignalTypeFilter(
                              (hyperspy.signals.EELSSpectrum,
                               hyperspy.signals.EDSSEMSpectrum,
                               hyperspy.signals.EDSTEMSpectrum),
                              self.ui))
        except ImportError:
            pass
        self.background_tool = EdsBackgroundwindowTool()
        self.add_tool(self.background_tool,
                      SignalTypeFilter(
                          (hyperspy.signals.EELSSpectrum,
                           hyperspy.signals.EDSSEMSpectrum,
                           hyperspy.signals.EDSTEMSpectrum),
                          self.ui))

    def _toggle_fixed_height(self, floating):
        w = self.picker_widget
        if floating:
            w.setFixedHeight(QWIDGETSIZE_MAX)
        else:
            w.setFixedHeight(w.minimumSize().height())

    def create_widgets(self):
        self.picker_widget = ElementPickerWidget(self.ui, self.ui)
        self.picker_widget.topLevelChanged[bool].connect(
            self._toggle_fixed_height)
        self.add_widget(self.picker_widget)
        self._toggle_fixed_height(False)

    def pick_element(self, element, signal=None):
        if signal is None:
            f = self.picker_tool.widget.ax.figure
            window = f.canvas.parent()
            sw = window.property('hyperspyUI.SignalWrapper')
            if sw is None:
                return
            signal = sw.signal

        wp = [w for w in self.ui.widgets if
              isinstance(w, ElementPickerWidget)][0]
        wp.set_element(element, True)
        if not wp.chk_markers.isChecked():
            wp.chk_markers.setChecked(True)

    def fourier_ratio(self):
        signals = self.ui.select_x_signals(2, [tr("Core loss"),
                                               tr("Low loss")])
        if signals is not None:
            s_core, s_lowloss = signals

            # Variable to store return value in
            ns = Namespace()
            ns.s_return = None

#            s_core.signal.remove_background()
            def run_fr():
                ns.s_return = s_core.signal.fourier_ratio_deconvolution(
                    s_lowloss.signal)
                ns.s_return.data = np.ma.masked_array(
                    ns.s_return.data,
                    mask=(np.isnan(ns.s_return.data) |
                          np.isinf(ns.s_return.data)))

            def fr_complete():
                ns.s_return.metadata.General.title = \
                    s_core.name + "[Fourier-ratio]"
                ns.s_return.plot()

            t = Threaded(self.ui, run_fr, fr_complete)
            t.run()

    def remove_background(self, signal=None):
        if signal is None:
            signal = self.ui.get_selected_wrapper()
        signal.signal.remove_background()

    def estimate_thickness(self):
        ui = self.ui
        s = ui.get_selected_signal()
        s_t = s.estimate_thickness(3.0)
        s_t.plot()


class ElementPickerTool(SelectionTool):
    picked = Signal(basestring)

    def __init__(self, windows=None):
        super(ElementPickerTool, self).__init__(windows)
        self.ranged = False
        self.valid_dimensions = [1]

    def get_name(self):
        return "Element picker tool"

    def get_category(self):
        return 'EDS'

    def get_icon(self):
        return os.path.dirname(__file__) + '/../images/periodic_table.svg'

    def on_pick_line(self, line):
        el, _ = _get_element_and_line(line)
        self.picked.emit(el)

    def on_mouseup(self, event):
        if event.inaxes is None:
            return
        self.accept()
        energy = event.xdata
        a = self.axes[0]
        if a.units.lower() == 'ev':
            energy /= 1000.0
        from hyperspy.misc.eds.utils import get_xray_lines_near_energy
        lines = get_xray_lines_near_energy(energy)
        if lines:
            m = QMenu()
            for line in lines:
                m.addAction(line, partial(self.on_pick_line, line))
            m.exec_(QCursor.pos())

        self.cancel()


class EdsBackgroundwindowTool(SignalFigureTool):

#    cancelled = QtCore.Signal()

    def __init__(self, windows=None):
        super(EdsBackgroundwindowTool, self).__init__(windows)

    def get_name(self):
        return "EDS background window tool"

    def get_category(self):
        return 'EDS'
#
#    def get_icon(self):
#        return os.path.dirname(__file__) + '/../images/periodic_table.svg'

    def make_cursor(self):
        return load_cursor(os.path.dirname(__file__) +
                           '/../images/picker.svg', 8, 8)

    def on_mousedown(self, event):
        s = self._get_signal(event.canvas.figure)
        if s is None:
            return
        xray_lines = s._get_xray_lines()
        print xray_lines
        if not hasattr(s, '_add_background_windows_rois'):
            return
        if not hasattr(s, '_background_window_rois'):
            s._background_window_rois = {}
        if s._background_window_rois.keys() != xray_lines:
            bwml = s._background_window_rois.keys()
            to_remove = set(bwml) - set(xray_lines)
            to_add = list(set(xray_lines) - set(bwml))
            for line in to_remove:
                g = s._background_window_rois.pop(line)
                for m in g[1]:
                    m.close()
                for r in g[0]:
                    for w, _ in r.signal_map:
                        w.close()
                    r.signal_map.clear()
            bw = s.estimate_background_windows(xray_lines=to_add)
            rois, markers = s._add_background_windows_rois(bw)
            for i, xl in enumerate(to_add):
                s._background_window_rois[xl] = (rois[i], markers[i])

    def estimate_background(self, signal=None):
        if signal is None:
            signal = self._get_signal(gcf())
            if signal is None:
                return
        xray_lines = signal._get_xray_lines()
        bw = signal.estimate_background_windows(xray_lines=xray_lines)
        rois, markers = signal._add_background_windows_rois(bw)
        for i, xl in enumerate(to_add):
            s._background_window_rois[xl] = (rois[i], markers[i])

    def is_selectable(self):
        return True

#    def cancel(self):
#        self.cancelled.emit()
#
#    def disconnect_windows(self, windows):
#        super(EdsBackgroundwindowTool, self).disconnect_windows(windows)
#        self.cancel()
