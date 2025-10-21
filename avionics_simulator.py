import sys
import requests
import numpy as np
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QFrame, QGraphicsView, 
                             QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem,
                             QGraphicsTextItem, QGraphicsProxyWidget, QGraphicsRectItem,
                             QComboBox, QCheckBox, QDoubleSpinBox, QFormLayout, QGraphicsObject,
                             QGraphicsItemGroup, QGraphicsPolygonItem)
from PyQt6.QtGui import QColor, QBrush, QPen, QFont, QPainter, QPolygonF, QPainterPath, QLinearGradient
from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPointF, 
                            QPoint, QSize, pyqtProperty, QSequentialAnimationGroup)
from PyQt6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
import json
import time

# Configuration
AVIATIONSTACK_API_URL = "http://api.aviationstack.com/v1/flights"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"

# Sample Data for Demo Mode
SAMPLE_FLIGHT_DATA = {
    "800A0A": { "callsign": "VTI812", "lon": 77.1025, "lat": 28.5665, "altitude": 35000, "velocity": 450, "vertical_rate": 0, "dep_airport": "Indira Gandhi Int'l", "dep_iata": "DEL", "arr_airport": "Chhatrapati Shivaji Maharaj Int'l", "arr_iata": "BOM" },
    "800C3B": { "callsign": "IGO6031", "lon": 72.8777, "lat": 19.0896, "altitude": 28000, "velocity": 400, "vertical_rate": 1500, "dep_airport": "Chhatrapati Shivaji Maharaj Int'l", "dep_iata": "BOM", "arr_airport": "Kempegowda Int'l", "arr_iata": "BLR" },
    "8006E1": { "callsign": "AIC505", "lon": 77.5946, "lat": 12.9716, "altitude": 32000, "velocity": 420, "vertical_rate": -500, "dep_airport": "Kempegowda Int'l", "dep_iata": "BLR", "arr_airport": "Netaji Subhas Chandra Bose Int'l", "arr_iata": "CCU" }
}

# Custom Toast Notification Widget
class Toast(QWidget):
    def __init__(self, parent, message):
        super().__init__(parent); self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout(); self.label = QLabel(message); self.label.setStyleSheet("background-color: rgba(0, 0, 0, 180); color: #E0E0E0; font-family: 'Segoe UI', sans-serif; font-size: 14px; padding: 10px 15px; border-radius: 8px;")
        layout.addWidget(self.label); self.setLayout(layout)
        self.animation = QPropertyAnimation(self, b"windowOpacity"); self.animation.setDuration(500); self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.timeout.connect(self.hide_toast)
    def show_toast(self):
        self.setWindowOpacity(0.0); self.show(); parent_geometry = self.parent().geometry(); self.move(parent_geometry.right() - self.width() - 15, parent_geometry.bottom() - self.height() - 15)
        self.animation.setStartValue(0.0); self.animation.setEndValue(1.0); self.animation.start(); self.timer.start(3000)
    def hide_toast(self):
        self.animation.setStartValue(1.0); self.animation.setEndValue(0.0); self.animation.finished.connect(self.close); self.animation.start()

# Custom Themed Modal Dialog
class ModalDialog(QWidget):
    def __init__(self, parent, title, message):
        super().__init__(parent); self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog); self.setWindowModality(Qt.WindowModality.ApplicationModal); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground); self.setFixedSize(parent.size())
        self.background = QFrame(self); self.background.setGeometry(self.rect()); self.background.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.dialog_widget = QFrame(self); self.dialog_widget.setStyleSheet("background-color: #1E1E2F; border: 1px solid #4A4A6A; border-radius: 12px;"); dialog_layout = QVBoxLayout(self.dialog_widget); dialog_layout.setContentsMargins(20, 20, 20, 20); dialog_layout.setSpacing(15)
        title_label = QLabel(title); title_label.setAlignment(Qt.AlignmentFlag.AlignCenter); title_label.setStyleSheet("color: #E0E0E0; font-size: 20px; font-weight: bold; border: none;")
        message_label = QLabel(message); message_label.setWordWrap(True); message_label.setAlignment(Qt.AlignmentFlag.AlignCenter); message_label.setStyleSheet("color: #C0C0C0; font-size: 14px; border: none;")
        self.ok_button = QPushButton("OK"); self.ok_button.setCursor(Qt.CursorShape.PointingHandCursor); self.ok_button.setStyleSheet("QPushButton { background-color: #5A67D8; color: white; font-size: 14px; font-weight: bold; padding: 10px; border: none; border-radius: 8px; } QPushButton:hover { background-color: #434190; }"); self.ok_button.clicked.connect(self.close)
        dialog_layout.addWidget(title_label); dialog_layout.addWidget(message_label); dialog_layout.addWidget(self.ok_button)
        self.dialog_widget.setFixedSize(450, 220); self.dialog_widget.move(int((self.width() - self.dialog_widget.width()) / 2), int((self.height() - self.dialog_widget.height()) / 2))
        self.animation = QPropertyAnimation(self.dialog_widget, b"geometry"); self.animation.setDuration(300); self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        start_pos = QRect(self.dialog_widget.x(), -self.dialog_widget.height(), self.dialog_widget.width(), self.dialog_widget.height()); end_pos = self.dialog_widget.geometry()
        self.animation.setStartValue(start_pos); self.animation.setEndValue(end_pos); self.animation.start(); self.show()

# Data Flow Diagram Widget
class DataFlowView(QGraphicsView):
    def __init__(self):
        super().__init__(); self.setScene(QGraphicsScene(self)); self.setRenderHint(QPainter.RenderHint.Antialiasing); self.setFrameShape(QFrame.Shape.NoFrame); self.setBackgroundBrush(QBrush(QColor("#1E1E2F")))
        self._draw_diagram()
    def _create_node(self, x, y, w, h, text):
        node = QGraphicsRectItem(x, y, w, h); node.setBrush(QBrush(QColor("#2D2D4D"))); node.setPen(QPen(QColor("#4A4A6A"), 2)); self.scene().addItem(node)
        text_item = QGraphicsTextItem(text, node); text_item.setDefaultTextColor(QColor("#E0E0E0")); text_item.setPos(x + w/2 - text_item.boundingRect().width()/2, y + h/2 - text_item.boundingRect().height()/2)
    def _draw_diagram(self):
        self._create_node(20, 20, 100, 50, "Sensors\n(GPS/ADC)"); self._create_node(160, 20, 100, 50, "Processor\n(FMC)"); self._create_node(300, 20, 100, 50, "Displays\n(PFD/MFD)")
        pen = QPen(QColor("#5A67D8"), 2, Qt.PenStyle.DashLine); path1 = QPainterPath(); path1.moveTo(120, 45); path1.lineTo(160, 45); self.scene().addPath(path1, pen)
        path2 = QPainterPath(); path2.moveTo(260, 45); path2.lineTo(300, 45); self.scene().addPath(path2, pen)

# PFD Widgets
class AttitudeIndicator(QGraphicsView):
    def __init__(self):
        super().__init__(); self.setScene(QGraphicsScene(self)); self.setRenderHint(QPainter.RenderHint.Antialiasing); self.setFrameShape(QFrame.Shape.NoFrame); self.setBackgroundBrush(QBrush(QColor("#000000"))); self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pitch = 0; self.roll = 0; self._horizon = None; self._aircraft_symbol = None; self._create_ui()
    
    def _create_ui(self):
        scene = self.scene(); scene.setSceneRect(-150, -150, 300, 300)
        self._horizon_sky = QGraphicsRectItem(-500, -500, 1000, 500); self._horizon_sky.setBrush(QBrush(QColor("#3A7CA5"))); self._horizon_sky.setPen(QPen(Qt.PenStyle.NoPen))
        self._horizon_ground = QGraphicsRectItem(-500, 0, 1000, 500); self._horizon_ground.setBrush(QBrush(QColor("#8B4513"))); self._horizon_ground.setPen(QPen(Qt.PenStyle.NoPen))
        self._horizon = QGraphicsItemGroup(); self._horizon.addToGroup(self._horizon_sky); self._horizon.addToGroup(self._horizon_ground)
        scene.addItem(self._horizon)

        self._pitch_ladder = QGraphicsItemGroup()
        pitch_pen = QPen(QColor("#FFFFFF"), 2); font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        for p in range(-90, 91, 10):
            if p == 0: line = QGraphicsLineItem(-80, 0, 80, 0); line.setPen(QPen(QColor("#FFD700"), 3)); self._pitch_ladder.addToGroup(line)
            else:
                line_length = 40 if abs(p) % 20 == 0 else 20; line = QGraphicsLineItem(-line_length/2, p*3, line_length/2, p*3); line.setPen(pitch_pen)
                text = QGraphicsTextItem(str(abs(p))); text.setDefaultTextColor(QColor("#FFFFFF")); text.setFont(font); text.setPos(line_length/2 + 5, p*3 - text.boundingRect().height()/2)
                self._pitch_ladder.addToGroup(line); self._pitch_ladder.addToGroup(text)
        scene.addItem(self._pitch_ladder)
        
        outer_circle_radius = 140
        roll_circle = QGraphicsEllipseItem(-outer_circle_radius, -outer_circle_radius, outer_circle_radius*2, outer_circle_radius*2); roll_circle.setPen(QPen(QColor("#4A4A6A"), 2)); scene.addItem(roll_circle)
        roll_mark_pen = QPen(QColor("#E0E0E0"), 2)
        for angle in range(-60, 61, 10):
            if angle == 0: continue
            line_length = 15 if abs(angle) % 30 == 0 else 10; line = QGraphicsLineItem(0, -outer_circle_radius + 5, 0, -outer_circle_radius + 5 + line_length)
            line.setPen(roll_mark_pen); line.setTransformOriginPoint(0, 0); line.setRotation(angle); scene.addItem(line)
        pointer_poly = QPolygonF([QPointF(0, -outer_circle_radius), QPointF(-7, -outer_circle_radius-10), QPointF(7, -outer_circle_radius-10)])
        roll_pointer = QGraphicsPolygonItem(pointer_poly); roll_pointer.setBrush(QBrush(QColor("#FFD700"))); roll_pointer.setPen(QPen(Qt.PenStyle.NoPen)); scene.addItem(roll_pointer)

        self._aircraft_symbol = QGraphicsItemGroup()
        left_wing = QGraphicsLineItem(-80, 0, -20, 0); left_wing.setPen(QPen(QColor("#FFD700"), 3))
        right_wing = QGraphicsLineItem(20, 0, 80, 0); right_wing.setPen(QPen(QColor("#FFD700"), 3))
        center_dot = QGraphicsEllipseItem(-3, -3, 6, 6); center_dot.setBrush(QBrush(QColor("#FFD700"))); center_dot.setPen(QPen(Qt.PenStyle.NoPen))
        self._aircraft_symbol.addToGroup(left_wing); self._aircraft_symbol.addToGroup(right_wing); self._aircraft_symbol.addToGroup(center_dot)
        scene.addItem(self._aircraft_symbol)

    def update_attitude(self, pitch, roll):
        self.pitch, self.roll = pitch, roll
        display_pitch = np.clip(pitch, -45, 45)
        self._horizon.setRotation(self.roll); self._horizon.setY(display_pitch * 3)
        self._pitch_ladder.setRotation(self.roll); self._pitch_ladder.setY(display_pitch * 3)
        self.centerOn(0, 0)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

class ValueDisplay(QFrame):
    def __init__(self, title, unit):
        super().__init__(); self.setMinimumSize(120, 80); self.setStyleSheet("background-color: black; border: 1px solid #4A4A6A; border-radius: 8px;")
        layout = QVBoxLayout(self); layout.setSpacing(2); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel(title); self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.title_label.setStyleSheet("color: #E0E0E0; font-size: 12px; border: none; background: transparent;")
        self.value_label = QLabel("0"); self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.value_label.setStyleSheet("color: #4CAF50; font-size: 28px; font-weight: bold; border: none; background: transparent;")
        self.unit_label = QLabel(unit); self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.unit_label.setStyleSheet("color: #C0C0C0; font-size: 10px; border: none; background: transparent;")
        layout.addWidget(self.title_label); layout.addWidget(self.value_label); layout.addWidget(self.unit_label)
    def update_value(self, value): self.value_label.setText(f"{value:.0f}")

# --- Main Window ---
class AvionicsGUI(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("A.V.I.O.N. - Avionics Digital Twin"); self.setGeometry(100, 100, 1600, 900); self.setStyleSheet("background-color: #1A1A2A; color: #E0E0E0;"); self.flight_data = None; self.icao = None; self.gps_noise = 0.0; self.map_initialized = False; self.instruments_frozen = False
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget); self.main_layout = QHBoxLayout(self.central_widget); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(0)
        self._create_pfd(); self._create_mfd(); self.main_layout.addWidget(self.pfd_frame, 1); self.main_layout.addWidget(self.mfd_frame, 2)
        self._create_maintenance_panel(); self._create_diagnostics_panel(); self.statusBar().setStyleSheet("background-color: #101018; color: #C0C0C0;")
        self.api_timer = QTimer(self); self.api_timer.timeout.connect(self.fetch_flight_data); self.demo_timer = QTimer(self); self.demo_timer.timeout.connect(self.update_demo_data)
        self.toggle_demo_mode(self.demo_mode_checkbox.isChecked()); self.update_diagnostics_simulation()
    def _create_pfd(self):
        self.pfd_frame = QFrame(); self.pfd_frame.setFrameShape(QFrame.Shape.StyledPanel); self.pfd_frame.setStyleSheet("background-color: black; border-right: 2px solid #4A4A6A;")
        pfd_layout = QVBoxLayout(self.pfd_frame); pfd_layout.setSpacing(10); pfd_layout.setContentsMargins(10, 10, 10, 10)
        
        top_layout = QHBoxLayout(); self.airspeed_display = ValueDisplay("AIRSPEED", "KTS"); self.altitude_display = ValueDisplay("ALTITUDE", "M")
        top_layout.addWidget(self.airspeed_display); top_layout.addStretch(); top_layout.addWidget(self.altitude_display)
        
        self.attitude_indicator = AttitudeIndicator()
        
        pfd_layout.addLayout(top_layout); pfd_layout.addWidget(self.attitude_indicator, 1)

    def _create_mfd(self):
        self.mfd_frame = QFrame(); mfd_layout = QVBoxLayout(self.mfd_frame); mfd_layout.setSpacing(10); mfd_layout.setContentsMargins(10, 10, 10, 10)
        api_bar = QHBoxLayout(); api_bar.addWidget(QLabel("AviationStack API Key:")); self.api_key_input = QLineEdit(); self.api_key_input.setText("aeec3a3fa431b84d7641244444662827"); self.api_key_input.setPlaceholderText("Enter API Key"); self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password); self.api_key_input.setStyleSheet("background-color: #2D2D4D; border: 1px solid #4A4A6A; padding: 8px; border-radius: 5px;")
        self.demo_mode_checkbox = QCheckBox("Demo Mode"); self.demo_mode_checkbox.toggled.connect(self.toggle_demo_mode); api_bar.addWidget(self.api_key_input); api_bar.addWidget(self.demo_mode_checkbox); mfd_layout.addLayout(api_bar)
        control_bar = QHBoxLayout(); self.flight_selector = QComboBox(); self.flight_selector.setStyleSheet("QComboBox { background-color: #2D2D4D; border: 1px solid #4A4A6A; padding: 8px; border-radius: 5px; font-size: 14px; } QComboBox::drop-down { border: none; }"); self.refresh_button = QPushButton("Refresh List"); self.refresh_button.clicked.connect(self.fetch_active_flights)
        self.connect_button = QPushButton("Connect"); self.connect_button.clicked.connect(self.toggle_connection); self.diagnostics_button = QPushButton("System Diagnostics"); self.diagnostics_button.clicked.connect(self.toggle_diagnostics_panel); self.maintenance_button = QPushButton("Maintenance"); self.maintenance_button.clicked.connect(self.toggle_maintenance_panel)
        for btn in [self.connect_button, self.maintenance_button, self.refresh_button, self.diagnostics_button]: btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setStyleSheet("QPushButton { background-color: #3D3D5D; padding: 8px; border-radius: 5px; border: 1px solid #4A4A6A; } QPushButton:hover { background-color: #4A4A6A; }")
        control_bar.addWidget(QLabel("Track:")); control_bar.addWidget(self.flight_selector, 1); control_bar.addWidget(self.refresh_button); control_bar.addWidget(self.connect_button); control_bar.addStretch(); control_bar.addWidget(self.diagnostics_button); control_bar.addWidget(self.maintenance_button); mfd_layout.addLayout(control_bar)
        route_display_frame = QFrame(); route_display_frame.setStyleSheet("background-color: #2D2D4D; border-radius: 5px; padding: 8px;"); self.route_display_layout = QHBoxLayout(route_display_frame); self.dep_airport_label = QLabel("DEP: N/A"); self.route_arrow_label = QLabel("→"); self.arr_airport_label = QLabel("ARR: N/A")
        for label in [self.dep_airport_label, self.route_arrow_label, self.arr_airport_label]: label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E0E0E0; background-color: transparent;")
        self.route_display_layout.addWidget(self.dep_airport_label, 1, Qt.AlignmentFlag.AlignRight); self.route_display_layout.addWidget(self.route_arrow_label); self.route_display_layout.addWidget(self.arr_airport_label, 1, Qt.AlignmentFlag.AlignLeft); mfd_layout.addWidget(route_display_frame)
        self.map_view = QWebEngineView(); self._initialize_map(); mfd_layout.addWidget(self.map_view, 1)
        status_layout = QHBoxLayout(); self.gps_status = self._create_status_indicator("GPS"); self.api_status = self._create_status_indicator("API"); self.weather_status = self._create_status_indicator("WEATHER SYS"); status_layout.addWidget(self.gps_status); status_layout.addWidget(self.api_status); status_layout.addWidget(self.weather_status); mfd_layout.addLayout(status_layout)
    def _create_maintenance_panel(self):
        self.maintenance_panel = QFrame(self); self.maintenance_panel.setFrameShape(QFrame.Shape.StyledPanel); self.maintenance_panel.setStyleSheet("background-color: #1E1E2F; border-left: 2px solid #4A4A6A;"); panel_width = 350; self.maintenance_panel.setGeometry(self.width(), 0, panel_width, self.height()); panel_layout = QVBoxLayout(self.maintenance_panel)
        panel_layout.setContentsMargins(20, 20, 20, 20); panel_layout.setSpacing(15); title_bar_layout = QHBoxLayout(); title = QLabel("Maintenance & Simulation"); title.setStyleSheet("font-size: 20px; font-weight: bold; color: #E0E0E0;"); close_button = QPushButton("X"); close_button.setCursor(Qt.CursorShape.PointingHandCursor); close_button.setFixedSize(30, 30); close_button.clicked.connect(self.toggle_maintenance_panel); close_button.setStyleSheet("QPushButton { background-color: #4A4A6A; color: #E0E0E0; font-size: 16px; font-weight: bold; border-radius: 15px; } QPushButton:hover { background-color: #D85A5A; }"); title_bar_layout.addWidget(title); title_bar_layout.addStretch(); title_bar_layout.addWidget(close_button)
        fault_title = QLabel("Fault Simulation"); fault_title.setStyleSheet("font-size: 16px; color: #C0C0C0; border-top: 1px solid #4A4A6A; padding-top: 10px;"); self.emi_button = QPushButton("Trigger EMI/EMC Interference"); self.emi_button.setCheckable(True); self.emi_button.toggled.connect(self.simulate_emi); self.shielding_button = QPushButton("Enable GPS Shielding"); self.shielding_button.setEnabled(False); self.shielding_button.clicked.connect(self.enable_shielding)
        sys_check_title = QLabel("New Module Integration"); sys_check_title.setStyleSheet("font-size: 16px; color: #C0C0C0; border-top: 1px solid #4A4A6A; padding-top: 10px;"); self.sys_check_button = QPushButton("Check 'AI Weather' Compatibility"); self.sys_check_button.clicked.connect(self.run_compatibility_check)
        for btn in [self.emi_button, self.shielding_button, self.sys_check_button]: btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setStyleSheet("QPushButton { background-color: #2D2D4D; padding: 10px; border-radius: 5px; border: 1px solid #4A4A6A; } QPushButton:hover { background-color: #4A4A6A; } QPushButton:checked { background-color: #D85A5A; }")
        panel_layout.addLayout(title_bar_layout); panel_layout.addSpacing(10); panel_layout.addWidget(fault_title); panel_layout.addWidget(self.emi_button); panel_layout.addWidget(self.shielding_button); panel_layout.addSpacing(20); panel_layout.addWidget(sys_check_title); panel_layout.addWidget(self.sys_check_button); panel_layout.addStretch()
        self.panel_animation = QPropertyAnimation(self.maintenance_panel, b"geometry"); self.panel_animation.setDuration(500); self.panel_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
    def _create_diagnostics_panel(self):
        panel_width = 420; self.diagnostics_panel = QFrame(self); self.diagnostics_panel.setFrameShape(QFrame.Shape.StyledPanel); self.diagnostics_panel.setStyleSheet("background-color: #1E1E2F; border-right: 2px solid #4A4A6A;"); self.diagnostics_panel.setGeometry(-panel_width, 0, panel_width, self.height())
        panel_layout = QVBoxLayout(self.diagnostics_panel); panel_layout.setContentsMargins(20, 20, 20, 20); panel_layout.setSpacing(15); title_bar_layout = QHBoxLayout(); title = QLabel("System Diagnostics"); title.setStyleSheet("font-size: 20px; font-weight: bold; color: #E0E0E0;"); close_button = QPushButton("X"); close_button.setCursor(Qt.CursorShape.PointingHandCursor); close_button.setFixedSize(30, 30); close_button.clicked.connect(self.toggle_diagnostics_panel); close_button.setStyleSheet("QPushButton { background-color: #4A4A6A; color: #E0E0E0; font-size: 16px; font-weight: bold; border-radius: 15px; } QPushButton:hover { background-color: #D85A5A; }"); title_bar_layout.addWidget(title); title_bar_layout.addStretch(); title_bar_layout.addWidget(close_button)
        panel_layout.addLayout(title_bar_layout); panel_layout.addSpacing(10)
        
        flow_title = QLabel("Subsystem Data Flow"); flow_title.setStyleSheet("font-size: 16px; color: #C0C0C0; border-top: 1px solid #4A4A6A; padding-top: 10px;"); self.data_flow_view = DataFlowView()
        panel_layout.addWidget(flow_title); panel_layout.addWidget(self.data_flow_view, 1)

        config_title = QLabel("Interface Configuration"); config_title.setStyleSheet("font-size: 16px; color: #C0C0C0; border-top: 1px solid #4A4A6A; padding-top: 10px;"); form_layout = QFormLayout()
        self.baud_rate_combo = QComboBox(); self.baud_rate_combo.addItems(["9600", "19200", "38400", "115200"]); self.voltage_spinbox = QDoubleSpinBox(); self.voltage_spinbox.setRange(0, 12); self.voltage_spinbox.setValue(5.0); self.voltage_spinbox.setSingleStep(0.1)
        self.signal_type_combo = QComboBox(); self.signal_type_combo.addItems(["RS-232", "ARINC 429", "Ethernet"])
        for widget in [self.baud_rate_combo, self.voltage_spinbox, self.signal_type_combo]: widget.setStyleSheet("background-color: #2D2D4D; padding: 8px; border-radius: 5px; border: 1px solid #4A4A6A;");
        self.baud_rate_combo.currentTextChanged.connect(self.update_diagnostics_simulation); self.voltage_spinbox.valueChanged.connect(self.update_diagnostics_simulation); self.signal_type_combo.currentTextChanged.connect(self.update_diagnostics_simulation)
        form_layout.addRow("Baud Rate:", self.baud_rate_combo); form_layout.addRow("Voltage Level (V):", self.voltage_spinbox); form_layout.addRow("Signal Type:", self.signal_type_combo)
        panel_layout.addWidget(config_title); panel_layout.addLayout(form_layout)
        
        sim_results_title = QLabel("Simulation Results"); sim_results_title.setStyleSheet("font-size: 16px; color: #C0C0C0; border-top: 1px solid #4A4A6A; padding-top: 10px;"); panel_layout.addWidget(sim_results_title)
        results_layout = QFormLayout(); self.snr_label = QLabel(); self.ber_label = QLabel(); self.integrity_label = QLabel()
        results_layout.addRow("Signal-to-Noise (SNR):", self.snr_label); results_layout.addRow("Bit Error Rate (BER):", self.ber_label); results_layout.addRow("Data Integrity:", self.integrity_label); panel_layout.addLayout(results_layout)

        panel_layout.addStretch()
        self.diag_panel_animation = QPropertyAnimation(self.diagnostics_panel, b"geometry"); self.diag_panel_animation.setDuration(500); self.diag_panel_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def _create_status_indicator(self, name):
        widget = QFrame(); layout = QHBoxLayout(widget); label = QLabel(name); status_text = QLabel("NOMINAL"); status_text.setObjectName("status_text"); label.setStyleSheet("font-weight: bold; font-size: 14px;"); status_text.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px;"); layout.addWidget(label); layout.addWidget(status_text); layout.addStretch(); widget.setStyleSheet("background-color: #2D2D4D; border-radius: 5px; padding: 5px;"); return widget
    def _update_status(self, indicator, text, color, is_fault=False):
        status_text = indicator.findChild(QLabel, "status_text"); status_text.setText(text); status_text.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        if is_fault: self.flash_animation = QPropertyAnimation(indicator, b"styleSheet"); self.flash_animation.setDuration(1000); self.flash_animation.setLoopCount(3); self.flash_animation.setKeyValueAt(0, "background-color: #2D2D4D; border-radius: 5px; padding: 5px;"); self.flash_animation.setKeyValueAt(0.5, f"background-color: {color}; border-radius: 5px; padding: 5px;"); self.flash_animation.setKeyValueAt(1, "background-color: #2D2D4D; border-radius: 5px; padding: 5px;"); self.flash_animation.start()
    def _initialize_map(self):
        fig = go.Figure(go.Scattermapbox()); fig.update_layout(title="Awaiting Flight Selection", mapbox_style="carto-darkmatter", margin={"r":0,"t":40,"l":0,"b":0}, mapbox=dict(center=dict(lat=20.5937, lon=78.9629), zoom=4), paper_bgcolor="#1A1A2A", font_color="#E0E0E0"); self.map_view.setHtml(fig.to_html(include_plotlyjs='cdn'))
    def toggle_demo_mode(self, checked):
        self.api_key_input.setEnabled(not checked); self.refresh_button.setEnabled(not checked); self.api_timer.stop(); self.demo_timer.stop(); self.flight_selector.clear(); self.statusBar().showMessage("Demo Mode Enabled. Select a sample flight." if checked else "Demo Mode Disabled. Enter API key and refresh list.")
        if checked: self.fetch_active_flights()
    def fetch_active_flights(self):
        if self.demo_mode_checkbox.isChecked():
            self.flight_selector.clear()
            for icao, data in SAMPLE_FLIGHT_DATA.items(): self.flight_selector.addItem(f"{data['callsign']} ({data['dep_iata']} → {data['arr_iata']})", userData=icao)
            self.statusBar().showMessage(f"Loaded {len(SAMPLE_FLIGHT_DATA)} sample flights."); return
        params = {'access_key': self.api_key_input.text()};
        if not params['access_key']: ModalDialog(self, "API Key Missing", "Please enter your AviationStack API Key."); return
        params['flight_status'] = 'active'; self.statusBar().showMessage("Fetching flights..."); self.refresh_button.setEnabled(False)
        try:
            response = requests.get(AVIATIONSTACK_API_URL, params=params, timeout=15); response.raise_for_status(); data = response.json(); self.flight_selector.clear()
            if data.get('data'):
                for flight in data['data']:
                    icao = flight.get('flight', {}).get('icao'); callsign = flight.get('flight', {}).get('iata') or icao
                    if callsign and icao: dep = flight.get('departure', {}).get('iata', 'N/A'); arr = flight.get('arrival', {}).get('iata', 'N/A'); self.flight_selector.addItem(f"{callsign} ({dep} → {arr})", userData=icao)
                self.statusBar().showMessage(f"Found {self.flight_selector.count()} active flights.")
            else: self.statusBar().showMessage("No active flights found.")
        except requests.RequestException as e: ModalDialog(self, "API Error", f"Could not fetch flight list.\n\nDetails: {e}")
        finally: self.refresh_button.setEnabled(True)
    def toggle_connection(self):
        timer = self.demo_timer if self.demo_mode_checkbox.isChecked() else self.api_timer
        if timer.isActive(): timer.stop(); self.connect_button.setText("Connect"); self.statusBar().showMessage("Disconnected."); self._update_status(self.api_status, "DISCONNECTED", "#E0E0E0")
        else:
            self.icao = self.flight_selector.currentData();
            if not self.icao: self.statusBar().showMessage("Error: No flight selected."); return
            self.connect_button.setText("Disconnect"); self.map_initialized = False # Force map reload for new flight
            if self.demo_mode_checkbox.isChecked(): self.load_demo_data(); timer.start(2000)
            else: self.statusBar().showMessage(f"Connecting to {self.icao.upper()}..."); self.fetch_flight_data(); timer.start(60000)
    def load_demo_data(self):
        self.flight_data = SAMPLE_FLIGHT_DATA[self.icao].copy(); 
        self.flight_data["altitude"] /= 3.28084 # Convert sample feet to meters
        self.flight_data["roll"] = np.sin(time.time()/5) * 15; self.flight_data["pitch"] = np.cos(time.time()/5) * 5; self.update_ui()
    def update_demo_data(self):
        if not self.flight_data: return
        self.flight_data['lon'] += np.random.normal(0, 0.01); self.flight_data['lat'] += np.random.normal(0, 0.01)
        self.flight_data['altitude'] = np.clip(self.flight_data['altitude'] + np.random.normal(0, 15), 6000, 12000) # In meters
        self.flight_data['velocity'] = np.clip(self.flight_data['velocity'] + np.random.normal(0, 5), 350, 500)
        self.flight_data['vertical_rate'] = np.clip(self.flight_data['vertical_rate'] + np.random.normal(0, 100), -2000, 2000)
        self.flight_data['roll'] = np.sin(time.time()/5) * 15; self.flight_data['pitch'] = np.cos(time.time()/5) * 5; self.update_ui()
    def fetch_flight_data(self):
        params = {'access_key': self.api_key_input.text()};
        if not params['access_key'] or not self.icao: return
        params['flight_icao'] = self.icao
        try:
            response = requests.get(AVIATIONSTACK_API_URL, params=params, timeout=10); response.raise_for_status(); data = response.json()
            if data.get('data'):
                flight_info = data['data'][0]; live_data = flight_info.get('live')
                if not live_data: raise ValueError("No live tracking data available.")
                self.flight_data = {"callsign": flight_info.get('flight',{}).get('iata', 'N/A'), "lon": live_data.get('longitude'), "lat": live_data.get('latitude'), "altitude": live_data.get('altitude', 0), "velocity": live_data.get('speed_horizontal', 0) * 0.54, "vertical_rate": live_data.get('speed_vertical', 0) * 54.68, "dep_airport": flight_info.get('departure',{}).get('airport', 'N/A'), "dep_iata": flight_info.get('departure',{}).get('iata', 'N/A'), "arr_airport": flight_info.get('arrival',{}).get('airport', 'N/A'), "arr_iata": flight_info.get('arrival',{}).get('iata', 'N/A')}
                self.flight_data["roll"] = np.sin(time.time()/5) * 15; self.flight_data["pitch"] = np.cos(time.time()/5) * 5
                self.statusBar().showMessage(f"Tracking {self.flight_data['callsign']}. Alt: {self.flight_data['altitude']:.0f}m, Spd: {self.flight_data['velocity']:.0f} kts"); self._update_status(self.api_status, "CONNECTED", "#4CAF50"); self.update_ui()
            else: self.statusBar().showMessage(f"No live data for {self.icao.upper()}."); self._update_status(self.api_status, "NO DATA", "#FFA500")
        except (requests.RequestException, ValueError) as e: self.statusBar().showMessage(f"API Error: {e}"); self._update_status(self.api_status, "ERROR", "#F44336", is_fault=True)
    def update_ui(self):
        if not self.flight_data: return
        if self.instruments_frozen:
            lon = self.flight_data["lon"] + np.random.normal(0, self.gps_noise); lat = self.flight_data["lat"] + np.random.normal(0, self.gps_noise)
            if self.map_initialized: self.map_view.page().runJavaScript(f"updateAircraftPosition({lat}, {lon});")
            return

        self.altitude_display.update_value(self.flight_data["altitude"]); self.airspeed_display.update_value(self.flight_data["velocity"]); 
        self.attitude_indicator.update_attitude(self.flight_data["pitch"], self.flight_data["roll"])
        self.dep_airport_label.setText(f"DEP: {self.flight_data['dep_iata']}"); self.arr_airport_label.setText(f"ARR: {self.flight_data['arr_iata']}"); self.dep_airport_label.setToolTip(self.flight_data['dep_airport']); self.arr_airport_label.setToolTip(self.flight_data['arr_airport'])
        lon = self.flight_data["lon"] + np.random.normal(0, self.gps_noise); lat = self.flight_data["lat"] + np.random.normal(0, self.gps_noise)
        
        if not self.map_initialized:
            fig = go.Figure(go.Scattermapbox(lat=[lat], lon=[lon], mode='markers', marker=go.scattermapbox.Marker(size=15, color='cyan'), text=[self.flight_data['callsign']]))
            fig.update_layout(title=f"Live Track: {self.flight_data['callsign']}", mapbox_style="carto-darkmatter", margin={"r":0,"t":40,"l":0,"b":0}, mapbox=dict(center=dict(lat=lat, lon=lon), zoom=7), paper_bgcolor="#1A1A2A", font_color="#E0E0E0")
            html = fig.to_html(include_plotlyjs='cdn'); js_script = """<script> function updateAircraftPosition(lat, lon) { var mapDiv = document.querySelector('.plotly-graph-div'); if (mapDiv) { Plotly.restyle(mapDiv, { lat: [[lat]], lon: [[lon]] }, [0]); Plotly.relayout(mapDiv, { 'mapbox.center.lat': lat, 'mapbox.center.lon': lon }); } } </script>"""
            self.map_view.setHtml(html + js_script); self.map_initialized = True
        else: self.map_view.page().runJavaScript(f"updateAircraftPosition({lat}, {lon});")

    def toggle_maintenance_panel(self):
        start_x_hidden = self.width(); start_x_visible = self.width() - self.maintenance_panel.width()
        if self.maintenance_panel.x() == self.width(): self.panel_animation.setStartValue(QRect(start_x_hidden, 0, self.maintenance_panel.width(), self.height())); self.panel_animation.setEndValue(QRect(start_x_visible, 0, self.maintenance_panel.width(), self.height()))
        else: self.panel_animation.setStartValue(QRect(start_x_visible, 0, self.maintenance_panel.width(), self.height())); self.panel_animation.setEndValue(QRect(start_x_hidden, 0, self.maintenance_panel.width(), self.height()))
        self.panel_animation.start()
    def toggle_diagnostics_panel(self):
        panel_width = self.diagnostics_panel.width(); start_x_hidden = -panel_width; start_x_visible = 0
        if self.diagnostics_panel.x() == start_x_hidden: self.diag_panel_animation.setStartValue(QRect(start_x_hidden, 0, panel_width, self.height())); self.diag_panel_animation.setEndValue(QRect(start_x_visible, 0, panel_width, self.height()))
        else: self.diag_panel_animation.setStartValue(QRect(start_x_visible, 0, panel_width, self.height())); self.diag_panel_animation.setEndValue(QRect(start_x_hidden, 0, panel_width, self.height()))
        self.diag_panel_animation.start()
    def update_diagnostics_simulation(self):
        baud = self.baud_rate_combo.currentText(); voltage = self.voltage_spinbox.value(); signal_type = self.signal_type_combo.currentText()
        v_noise = 0.1; snr = 20 * math.log10(voltage / v_noise) if voltage > 0 else -100
        snr_color = "#4CAF50" if snr > 20 else "#FFA500" if snr > 10 else "#F44336"; self.snr_label.setText(f"{snr:.2f} dB"); self.snr_label.setStyleSheet(f"color: {snr_color}; font-weight: bold;")
        
        ber_map = {"9600": 0.0001, "19200": 0.0005, "38400": 0.001, "115200": 0.005}; ber = ber_map.get(baud, 0.05)
        ber_color = "#4CAF50" if ber < 0.001 else "#FFA500" if ber < 0.005 else "#F44336"; self.ber_label.setText(f"{ber*100:.3f}%"); self.ber_label.setStyleSheet(f"color: {ber_color}; font-weight: bold;")
        
        type_reliability = {"Ethernet": 1.0, "ARINC 429": 0.98, "RS-232": 0.95}.get(signal_type, 0.9)
        integrity = type_reliability * (1 - (ber * 10)) * (np.clip(snr, 0, 35) / 35) * 100
        integrity_color = "#4CAF50" if integrity > 90 else "#FFA500" if integrity > 70 else "#F44336"; self.integrity_label.setText(f"{integrity:.2f}% ({'HEALTHY' if integrity > 90 else 'DEGRADED' if integrity > 70 else 'FAULT'})")
        self.integrity_label.setStyleSheet(f"color: {integrity_color}; font-weight: bold;")

    def simulate_emi(self, checked):
        if checked: 
            Toast(self, "EMI/EMC Interference Triggered!").show_toast(); self.gps_noise = 0.05; self._update_status(self.gps_status, "FAULT", "#F44336", is_fault=True); 
            self.shielding_button.setEnabled(True); self.emi_button.setText("Stop Interference"); self.instruments_frozen = True
        else: 
            self.gps_noise = 0.0; self._update_status(self.gps_status, "NOMINAL", "#4CAF50"); self.shielding_button.setEnabled(False); 
            self.emi_button.setText("Trigger EMI/EMC Interference"); self.instruments_frozen = False
    
    def enable_shielding(self): 
        Toast(self, "GPS Shielding Enabled").show_toast(); 
        self.gps_noise = 0.005; 
        self._update_status(self.gps_status, "STABILIZING", "#FFA500"); 
        self.shielding_button.setEnabled(False)
        QTimer.singleShot(5000, self.revert_gps_to_nominal)

    def revert_gps_to_nominal(self):
        Toast(self, "GPS System Stabilized.").show_toast()
        self.emi_button.setChecked(False)

    def run_compatibility_check(self):
        if not self.flight_data: ModalDialog(self, "Compatibility Check Failed", "No active flight data available."); return
        lat, lon = self.flight_data["lat"], self.flight_data["lon"]
        try:
            self._update_status(self.weather_status, "CHECKING...", "#3498DB"); response = requests.get(WEATHER_API_URL.format(lat=lat, lon=lon), timeout=5); response.raise_for_status()
            weather_data = response.json(); weather_code = weather_data['current_weather']['weathercode']; report_title = "AI Weather Module Check: "
            if weather_code > 80: report_title += "FAIL"; report_message = f"Reason: Severe weather (Code: {weather_code}).\nModule cannot process extreme weather."; self._update_status(self.weather_status, "FAIL", "#F44336", is_fault=True)
            else: report_title += "PASS"; report_message = "Reason: System bus compatible; weather within operational parameters."; self._update_status(self.weather_status, "PASS", "#4CAF50")
            ModalDialog(self, report_title, report_message)
        except requests.RequestException as e: ModalDialog(self, "Compatibility Check Error", f"Could not connect to weather service.\n\nDetails: {e}"); self._update_status(self.weather_status, "API ERROR", "#F44336", is_fault=True)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'maintenance_panel'):
            if self.maintenance_panel.x() < self.width(): self.maintenance_panel.setGeometry(self.width() - self.maintenance_panel.width(), 0, self.maintenance_panel.width(), self.height())
            else: self.maintenance_panel.setGeometry(self.width(), 0, self.maintenance_panel.width(), self.height())
        if hasattr(self, 'diagnostics_panel'):
            if self.diagnostics_panel.x() == 0: self.diagnostics_panel.setGeometry(0, 0, self.diagnostics_panel.width(), self.height())
            else: self.diagnostics_panel.setGeometry(-self.diagnostics_panel.width(), 0, self.diagnostics_panel.width(), self.height())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AvionicsGUI()
    window.show()
    sys.exit(app.exec())

