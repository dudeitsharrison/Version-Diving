import sys
import os
import shutil
import datetime
import json
import webbrowser
import uuid
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QListWidget, QTabWidget, 
                            QSpinBox, QCheckBox, QLineEdit, QComboBox, QScrollArea, 
                            QMessageBox, QGroupBox, QRadioButton, QSplitter, QFrame,
                            QListWidgetItem, QMenu, QDialog, QSystemTrayIcon, QStyle,
                            QToolButton, QSlider, QTabBar, QTextEdit, QColorDialog, QStyleOptionTab)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QAction, QColor, QPalette, QMovie, QPainter
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint, QEvent
import hashlib

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(base_path, relative_path)

class ToastNotification(QDialog):
    def __init__(self, parent=None, message="", icon=None, timeout=3000):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Arial", 10))
        label.setStyleSheet("padding: 10px;")
        layout.addWidget(label)
        
        # Set size and position
        self.setFixedWidth(300)
        self.adjustSize()
        
        # Position at top-right corner
        desktop = QApplication.primaryScreen().geometry()
        self.move(desktop.width() - self.width() - 20, 50)
        
        # Auto-close timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(timeout)
        
    def showEvent(self, event):
        super().showEvent(event)
        # Add fade-in effect if desired
        
    def closeEvent(self, event):
        super().closeEvent(event)
        # Add fade-out effect if desired

# New class for the floating countdown timer
class FloatingCountdownTimer(QWidget):
    def __init__(self, parent=None, project_name="Project", project_color=None, project_id=None):
        super().__init__(parent)
        print(f"TIMER: Creating new floating timer: {project_name} (ID: {project_id})")
        
        # Store project ID for association tracking
        self.project_id = project_id
        
        # Track dragging state
        self.dragging = False
        
        # Create floating widget with no frame
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set a fixed size for the timer display
        self.setFixedSize(200, 30)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Set opacity levels
        self.default_opacity = 0.85
        self.hover_opacity = 1.0
        self.setWindowOpacity(self.default_opacity)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Project-specific hash for unique identification and color
        hash_val = hash(project_name) if project_name else hash(str(id(self)))
        hash_hex = format(abs(hash_val), '08x')[:6]  # Use first 6 hex chars
        
        # Create app logo/drag handle with the clock icon
        self.logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'clock.png'))
        if not logo_pixmap.isNull():
            # Scale to small icon size
            logo_pixmap = logo_pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(logo_pixmap)
        else:
            # Fallback if icon not found
            self.logo_label.setText("⏱")
            self.logo_label.setStyleSheet("color: white; font-size: 14px;")
        
        # Initially hide the logo/handle until hover
        self.logo_label.setVisible(False)
        
        # Set fixed width for logo
        self.logo_label.setFixedWidth(16)
        
        # Add the logo label to the layout
        layout.addWidget(self.logo_label)
        
        # Add project name label
        self.project_label = QLabel(project_name)
        self.project_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.project_label.setFont(QFont("Arial", 8))
        self.project_label.setStyleSheet("background-color: transparent; color: white;")
        # Make the project label click-through
        self.project_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.project_label)
        
        # Add spacer to push time to the right
        layout.addStretch(1)
        
        # Add text label
        self.time_label = QLabel("--:--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.time_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.time_label.setStyleSheet("background-color: transparent; color: white;")
        # Make the time label click-through
        self.time_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.time_label)
        
        # Use provided color or generate one
        if project_color and isinstance(project_color, QColor):
            bg_color = project_color
            # Make it a bit darker for better contrast
            bg_r = max(bg_color.red() // 2, 30)
            bg_g = max(bg_color.green() // 2, 30) 
            bg_b = max(bg_color.blue() // 2, 30)
            bg_color = QColor(bg_r, bg_g, bg_b)
        else:
            # Generate a unique color for this timer based on project name
            r = int(hash_hex[0:2], 16) % 128 + 32  # Keep it dark enough for white text
            g = int(hash_hex[2:4], 16) % 128 + 32
            b = int(hash_hex[4:6], 16) % 128 + 32
            bg_color = QColor(r, g, b)
        
        # Convert to hex for stylesheet
        bg_color_hex = f"#{bg_color.red():02x}{bg_color.green():02x}{bg_color.blue():02x}"
        
        # Set overall styling with project-specific color
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color_hex}; 
                border-radius: 5px;
                border: 1px solid #444444;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        # Find if this is part of a main window that has existing timers
        parent_window = None
        if parent:
            parent_window = parent
        else:
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow):
                    parent_window = widget
                    break
        
        # Get all existing timers to stack this one below them
        existing_timers = []
        if parent_window and hasattr(parent_window, 'all_floating_timers'):
            existing_timers = parent_window.all_floating_timers
        
        # Position in the top-right corner of the screen
        desktop = QApplication.primaryScreen().geometry()
        x_pos = desktop.width() - self.width() - 20  # 20px from right edge
        
        # If there are existing timers, position this one below the last one
        y_pos = 50  # Default starting position
        if existing_timers:
            # Find the lowest existing timer
            max_y = 50
            for timer in existing_timers:
                if timer and timer.isVisible():
                    timer_bottom = timer.y() + timer.height()
                    if timer_bottom > max_y:
                        max_y = timer_bottom
            
            y_pos = max_y + 10  # 10px spacing between timers
        
        # Ensure timers don't go off screen
        x_pos = max(10, min(x_pos, desktop.width() - self.width() - 10))
        y_pos = max(10, min(y_pos, desktop.height() - self.height() - 10))
        
        self.move(x_pos, y_pos)
        
        # Store the background color for possible updates
        self.bg_color = bg_color
        
        # Set up close detection
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Dragging support
        self.drag_position = QPoint()
    
    def update_project_name(self, name):
        """Update the project name displayed in the timer"""
        self.project_name = name
        self.project_label.setText(name)
    
    def eventFilter(self, obj, event):
        # Handle mouse events on the logo label
        if obj == self.logo_label:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.logo_label.setCursor(Qt.CursorShape.ClosedHandCursor)
                return True
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                self.dragging = False
                self.logo_label.setCursor(Qt.CursorShape.OpenHandCursor)
                return True
            elif event.type() == QEvent.Type.MouseMove and self.dragging:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    new_pos = event.globalPosition().toPoint() - self.drag_position
                    self.move(new_pos)
                    return True
        return super().eventFilter(obj, event)
    
    def mousePressEvent(self, event):
        # Only processes events not handled by the time_label (which is transparent to events)
        # or the logo_label (which has its own event filter)
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        event.accept()
    
    def mouseMoveEvent(self, event):
        # Only processes events not handled by the time_label or logo_label
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
        event.accept()
    
    def mouseReleaseEvent(self, event):
        # Only processes events not handled by the time_label or logo_label
        if self.dragging:
            self.dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Find parent window to reposition all timers
            parent_window = None
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow) and hasattr(widget, 'reposition_all_timers'):
                    parent_window = widget
                    break
                    
            # Call reposition_all_timers if available
            if parent_window:
                parent_window.reposition_all_timers()
                
        event.accept()
    
    def enterEvent(self, event):
        # When mouse enters the widget, show the logo and reduce opacity
        self.logo_label.setVisible(True)
        self.setWindowOpacity(self.hover_opacity)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # When mouse leaves, hide the logo and restore opacity
        if not self.dragging:
            self.logo_label.setVisible(False)
            self.setWindowOpacity(self.default_opacity)
        super().leaveEvent(event)
    
    def set_opacity(self, opacity):
        """Set the default opacity of the timer"""
        self.default_opacity = opacity
        if not self.underMouse():  # Only update if not being hovered over
            self.setWindowOpacity(self.default_opacity)
    
    def update_time(self, seconds_left):
        """Update the countdown display"""
        hours, remainder = divmod(seconds_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def update_color(self, color):
        """Update the background color of the timer"""
        if not isinstance(color, QColor):
            return
            
        # Make the color a bit darker for better contrast
        bg_r = max(color.red() // 2, 30)
        bg_g = max(color.green() // 2, 30) 
        bg_b = max(color.blue() // 2, 30)
        bg_color = QColor(bg_r, bg_g, bg_b)
        
        # Convert to hex for stylesheet
        bg_color_hex = f"#{bg_color.red():02x}{bg_color.green():02x}{bg_color.blue():02x}"
        
        # Update the styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color_hex}; 
                border-radius: 5px;
                border: 1px solid #444444;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        # Store the updated background color
        self.bg_color = bg_color

    def closeEvent(self, event):
        """Handle timer window close event"""
        project_name = self.project_label.text() if hasattr(self, 'project_label') else "Unknown"
        print(f"TIMER: Timer closing: {project_name} (ID: {self.project_id})")
        super().closeEvent(event)

class TabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        
        # Set styling for tabs and close button with dark theme
        self.setStyleSheet("""
            QTabBar::tab {
                background-color: #1E2226;
                border: 1px solid #444444;
                padding: 5px 8px;
                min-width: 80px;
                color: #CCCCCC;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2D3339;
                border-bottom-color: #2D3339;
                color: white;
            }
            QTabBar::tab:last {
                min-width: 30px;
                max-width: 30px;
                min-height: 25px;
                background-color: #2D4050;
            }
            QTabBar::tab:last:hover {
                background-color: #3D5060;
            }
        """)
    
    def paintEvent(self, event):
        """Override paint event to customize tab appearance"""
        painter = QPainter(self)
        option = QStyleOptionTab()
        
        # Paint each tab with custom styling
        for i in range(self.count()):
            self.initStyleOption(option, i)
            
            # Get any custom tab data (like background color)
            tab_data = self.tabData(i)
            
            # If this tab has custom background color data, use it
            if tab_data and isinstance(tab_data, dict) and 'bg_color' in tab_data:
                bg_color = tab_data['bg_color']
                
                # Create a custom rect for the tab
                rect = self.tabRect(i)
                
                # Draw custom background
                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(bg_color)
                
                # Draw rounded rectangle for the tab (except for the + tab)
                if i == self.count() - 1 and self.parent() and hasattr(self.parent(), 'add_tab_is_visible') and self.parent().add_tab_is_visible:
                    # The + tab uses the default styling
                    pass
                else:
                    painter.drawRoundedRect(rect, 3, 3)
                
                painter.restore()
        
        # Let the base class handle the rest of the painting
        super().paintEvent(event)
        
        # After painting, ensure close buttons are properly set on all tabs
        for i in range(self.count()):
            # Skip the last tab which is the + tab
            if i < self.count() - 1:
                # Update or create close button if needed
                existing_btn = self.tabButton(i, QTabBar.ButtonPosition.RightSide)
                if not existing_btn or not existing_btn.isVisible():
                    close_button = self.createCloseButton()
                    self.setTabButton(i, QTabBar.ButtonPosition.RightSide, close_button)
            else:
                # Ensure the + tab has no close button
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
    
    def tabInserted(self, index):
        """Handle tab insertion to manage close buttons"""
        super().tabInserted(index)
        
        # Process all tabs to make sure close buttons are correctly configured
        for i in range(self.count()):
            # Special handling for the + tab (last tab)
            if i == self.count() - 1:
                # Remove close button for the + tab
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
            else:
                # Create and set a visible close button with X for all regular tabs
                close_button = self.createCloseButton()
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, close_button)
    
    def closeTab(self, index):
        """Handle tab close event"""
        print(f"TAB_CLOSE: Start closeTab method for index {index}, total tabs {self.count()}")
        
        # Allow closing any tab except the + tab (last tab)
        if index != self.count() - 1:
            print(f"TAB_CLOSE: Closing non-plus tab at index {index}")
            
            # Check if this is the last regular tab
            if self.count() <= 2:  # Just this tab and the + tab
                # Don't close if it's the last tab
                print("TAB_CLOSE: Cannot close last tab")
                
                # Find the main window to show toast
                main_window = None
                parent = self.parent()
                while parent is not None:
                    if isinstance(parent, VersionDivingApp):
                        main_window = parent
                        break
                    parent = parent.parent()
                
                if main_window and hasattr(main_window, 'show_toast'):
                    main_window.show_toast("Cannot close the last project tab", 3000)
                else:
                    print("TAB_CLOSE: Could not find main window to show toast")
                return
            
            # Find the main window to access project data
            main_window = None
            parent = self.parent()
            while parent is not None:
                if isinstance(parent, VersionDivingApp):
                    main_window = parent
                    break
                parent = parent.parent()
                
            print(f"TAB_CLOSE: Got main window reference: {main_window}")
            
            if main_window and hasattr(main_window, 'project_tabs') and index < len(main_window.project_tabs):
                print(f"TAB_CLOSE: Closing tab {index}, project_tabs contains {len(main_window.project_tabs)} projects")
                
                # Store the tab widget before removing it
                tab_widget = self.parent().widget(index)
                print(f"TAB_CLOSE: Got tab widget reference: {tab_widget}")
                
                # Get the project being closed
                project = main_window.project_tabs[index]
                print(f"TAB_CLOSE: Project being closed: {project.get('name')}")
                
                # Log timer info for debugging
                if hasattr(main_window, 'debug_timers'):
                    print("TAB_CLOSE: Debugging timers before removal:")
                    main_window.debug_timers()
                
                # Remove the floating timer if it exists
                floating_timer = project.get('floating_timer')
                if floating_timer:
                    print(f"TAB_CLOSE: Removing timer for closed tab: {index}")
                    # Remove from the all_floating_timers list
                    if hasattr(main_window, 'all_floating_timers') and floating_timer in main_window.all_floating_timers:
                        print(f"TAB_CLOSE: Removing timer from all_floating_timers")
                        main_window.all_floating_timers.remove(floating_timer)
                    
                    # Close and destroy the timer
                    print(f"TAB_CLOSE: Closing timer")
                    floating_timer.close()
                    print(f"TAB_CLOSE: Deleting timer later")
                    floating_timer.deleteLater()
                    print(f"TAB_CLOSE: Setting project's timer to None")
                    project['floating_timer'] = None
                    
                # Stop any running timers
                timer = project.get('auto_create_timer')
                if timer and hasattr(timer, 'isActive') and timer.isActive():
                    print(f"TAB_CLOSE: Stopping auto_create_timer")
                    timer.stop()
                    
                countdown_timer = project.get('countdown_timer')
                if countdown_timer and hasattr(countdown_timer, 'isActive') and countdown_timer.isActive():
                    print(f"TAB_CLOSE: Stopping countdown_timer")
                    countdown_timer.stop()
                
                # Now remove the tab widget first
                print(f"TAB_CLOSE: Removing tab widget at index {index}")
                parent_tab_widget = self.parent()
                if isinstance(parent_tab_widget, QTabWidget):
                    parent_tab_widget.removeTab(index)
                    print(f"TAB_CLOSE: Tab removed, remaining tab count: {parent_tab_widget.count()}")
                else:
                    self.removeTab(index)
                    print(f"TAB_CLOSE: Tab removed via TabBar (not QTabWidget)")
                
                # Then remove the project from main_window.project_tabs
                print(f"TAB_CLOSE: Removing project from project_tabs list")
                main_window.project_tabs.pop(index)
                print(f"TAB_CLOSE: Project removed, remaining projects: {len(main_window.project_tabs)}")
                
                # Update current_project_index if needed
                print(f"TAB_CLOSE: Current project index before adjustment: {main_window.current_project_index}")
                if main_window.current_project_index >= len(main_window.project_tabs):
                    print(f"TAB_CLOSE: Adjusting current project index to last project")
                    main_window.current_project_index = len(main_window.project_tabs) - 1
                elif main_window.current_project_index >= index:
                    # If removing a tab before the current one, adjust the index
                    print(f"TAB_CLOSE: Adjusting current project index from {main_window.current_project_index} to {main_window.current_project_index - 1}")
                    main_window.current_project_index -= 1
                print(f"TAB_CLOSE: Current project index after adjustment: {main_window.current_project_index}")
                
                # Use the aggressive cleanup to fix any timer issues
                print("TAB_CLOSE: Running force_timer_cleanup after tab close")
                if hasattr(main_window, 'force_timer_cleanup'):
                    main_window.force_timer_cleanup()
                
                print(f"TAB_CLOSE: After cleanup, remaining tabs: {parent_tab_widget.count() if isinstance(parent_tab_widget, QTabWidget) else 'unknown'}")
                    
                # If we still have projects, load the current one
                if main_window.project_tabs:
                    print(f"TAB_CLOSE: Loading project state for index {main_window.current_project_index}")
                    main_window.load_project_state(main_window.current_project_index)
                
                print("TAB_CLOSE: Tab close completed successfully")
                return
                
            # Fallback: Just remove the tab if we can't find associated project data
            print(f"TAB_CLOSE: Fallback - no project data found for index {index}")
            self.removeTab(index)
            print(f"TAB_CLOSE: Tab removed via fallback path")
        else:
            print(f"TAB_CLOSE: Attempting to close the + tab, ignoring")
    
    def tabSizeHint(self, index):
        """Customize tab sizes"""
        size = super().tabSizeHint(index)
        
        # Make the + tab a small square (last tab is always the + tab)
        if index == self.count() - 1:
            size.setWidth(30)
            
        return size
    
    def createCloseButton(self):
        """Create a visible close button for tabs with a clear X"""
        # Create a direct button with text "X"
        button = QPushButton("✕")  # Using Unicode X symbol
        button.setFixedSize(16, 16)
        button.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        
        # Very clear styling with direct background and foreground colors
        button.setStyleSheet("""
            QPushButton {
                color: #CCCCCC;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                margin: 0px;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                color: white;
                background-color: #FF4444;
            }
        """)
        
        button.clicked.connect(lambda: self.tabCloseRequested.emit(self.tabAt(button.pos())))
        return button

class ProjectTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up tab bar and remove the default one
        self.custom_tab_bar = TabBar()
        self.setTabBar(self.custom_tab_bar)
        
        # Set tab position
        self.setTabPosition(QTabWidget.TabPosition.North)
        self.setMovable(True)
        
        # Store main window reference
        self.main_window = parent
        
        # Track the previous index for tab changes
        self.prev_index = 0
        
        # Flag to track the "+" tab visibility
        self.add_tab_is_visible = False
        
        # Dictionary to store tab colors
        self.tab_colors = {}
        
        # Create info button and add it to corner
        self.info_button = QPushButton()
        self.info_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        self.info_button.setToolTip("Show Help")
        self.info_button.setFixedSize(24, 24)
        self.info_button.setStyleSheet("""
            QPushButton {
                background-color: #3D4852;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4D5862;
            }
        """)
        
        # Create corner widget to host the info button
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(2, 2, 2, 2)
        corner_layout.addWidget(self.info_button)
        self.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
        
        # Add the "+" tab
        self.addTab(QWidget(), "+")
        self.add_tab_is_visible = True
        
        # Connect signals for tab management
        self.currentChanged.connect(self.handleTabChange)
        
        # Apply dark styling to match app theme - only style the pane
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #2D3339;
            }
        """)
    
    def setTabColor(self, index, color):
        """Set the color for a specific tab"""
        if index >= 0 and index < self.count():
            self.tab_colors[index] = color
            self.custom_tab_bar.setTabTextColor(index, color)
            
            # Create a custom background color that's a muted version of the text color
            r, g, b = color.red(), color.green(), color.blue()
            # Make it darker but maintain the hue
            bg_r = max(r // 2, 30)
            bg_g = max(g // 2, 30) 
            bg_b = max(b // 2, 30)
            
            # Apply specific style to this tab
            self.tabBar().setTabData(index, {'bg_color': QColor(bg_r, bg_g, bg_b)})
            self.tabBar().update()
    
    def getTabColor(self, index):
        """Get the color for a specific tab"""
        return self.tab_colors.get(index, QColor(255, 255, 255))  # Default white
    
    def handleTabChange(self, index):
        """Handle when tabs are changed by the user"""
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        return super().addTab(widget, label)

import sys
import os
import shutil
import datetime
import json
import webbrowser
import uuid
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QListWidget, QTabWidget, 
                            QSpinBox, QCheckBox, QLineEdit, QComboBox, QScrollArea, 
                            QMessageBox, QGroupBox, QRadioButton, QSplitter, QFrame,
                            QListWidgetItem, QMenu, QDialog, QSystemTrayIcon, QStyle,
                            QToolButton, QSlider, QTabBar, QTextEdit, QColorDialog, QStyleOptionTab)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QAction, QColor, QPalette, QMovie, QPainter
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint, QEvent
import hashlib

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(base_path, relative_path)

class ToastNotification(QDialog):
    def __init__(self, parent=None, message="", icon=None, timeout=3000):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Arial", 10))
        label.setStyleSheet("padding: 10px;")
        layout.addWidget(label)
        
        # Set size and position
        self.setFixedWidth(300)
        self.adjustSize()
        
        # Position at top-right corner
        desktop = QApplication.primaryScreen().geometry()
        self.move(desktop.width() - self.width() - 20, 50)
        
        # Auto-close timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(timeout)
        
    def showEvent(self, event):
        super().showEvent(event)
        # Add fade-in effect if desired
        
    def closeEvent(self, event):
        super().closeEvent(event)
        # Add fade-out effect if desired

# New class for the floating countdown timer
class FloatingCountdownTimer(QWidget):
    def __init__(self, parent=None, project_name="Project", project_color=None, project_id=None):
        super().__init__(parent)
        print(f"TIMER: Creating new floating timer: {project_name} (ID: {project_id})")
        
        # Store project ID for association tracking
        self.project_id = project_id
        
        # Track dragging state
        self.dragging = False
        
        # Create floating widget with no frame
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set a fixed size for the timer display
        self.setFixedSize(200, 30)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Set opacity levels
        self.default_opacity = 0.85
        self.hover_opacity = 1.0
        self.setWindowOpacity(self.default_opacity)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Project-specific hash for unique identification and color
        hash_val = hash(project_name) if project_name else hash(str(id(self)))
        hash_hex = format(abs(hash_val), '08x')[:6]  # Use first 6 hex chars
        
        # Create app logo/drag handle with the clock icon
        self.logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'clock.png'))
        if not logo_pixmap.isNull():
            # Scale to small icon size
            logo_pixmap = logo_pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(logo_pixmap)
        else:
            # Fallback if icon not found
            self.logo_label.setText("⏱")
            self.logo_label.setStyleSheet("color: white; font-size: 14px;")
        
        # Initially hide the logo/handle until hover
        self.logo_label.setVisible(False)
        
        # Set fixed width for logo
        self.logo_label.setFixedWidth(16)
        
        # Add the logo label to the layout
        layout.addWidget(self.logo_label)
        
        # Add project name label
        self.project_label = QLabel(project_name)
        self.project_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.project_label.setFont(QFont("Arial", 8))
        self.project_label.setStyleSheet("background-color: transparent; color: white;")
        # Make the project label click-through
        self.project_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.project_label)
        
        # Add spacer to push time to the right
        layout.addStretch(1)
        
        # Add text label
        self.time_label = QLabel("--:--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.time_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.time_label.setStyleSheet("background-color: transparent; color: white;")
        # Make the time label click-through
        self.time_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.time_label)
        
        # Use provided color or generate one
        if project_color and isinstance(project_color, QColor):
            bg_color = project_color
            # Make it a bit darker for better contrast
            bg_r = max(bg_color.red() // 2, 30)
            bg_g = max(bg_color.green() // 2, 30) 
            bg_b = max(bg_color.blue() // 2, 30)
            bg_color = QColor(bg_r, bg_g, bg_b)
        else:
            # Generate a unique color for this timer based on project name
            r = int(hash_hex[0:2], 16) % 128 + 32  # Keep it dark enough for white text
            g = int(hash_hex[2:4], 16) % 128 + 32
            b = int(hash_hex[4:6], 16) % 128 + 32
            bg_color = QColor(r, g, b)
        
        # Convert to hex for stylesheet
        bg_color_hex = f"#{bg_color.red():02x}{bg_color.green():02x}{bg_color.blue():02x}"
        
        # Set overall styling with project-specific color
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color_hex}; 
                border-radius: 5px;
                border: 1px solid #444444;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        # Find if this is part of a main window that has existing timers
        parent_window = None
        if parent:
            parent_window = parent
        else:
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow):
                    parent_window = widget
                    break
        
        # Get all existing timers to stack this one below them
        existing_timers = []
        if parent_window and hasattr(parent_window, 'all_floating_timers'):
            existing_timers = parent_window.all_floating_timers
        
        # Position in the top-right corner of the screen
        desktop = QApplication.primaryScreen().geometry()
        x_pos = desktop.width() - self.width() - 20  # 20px from right edge
        
        # If there are existing timers, position this one below the last one
        y_pos = 50  # Default starting position
        if existing_timers:
            # Find the lowest existing timer
            max_y = 50
            for timer in existing_timers:
                if timer and timer.isVisible():
                    timer_bottom = timer.y() + timer.height()
                    if timer_bottom > max_y:
                        max_y = timer_bottom
            
            y_pos = max_y + 10  # 10px spacing between timers
        
        # Ensure timers don't go off screen
        x_pos = max(10, min(x_pos, desktop.width() - self.width() - 10))
        y_pos = max(10, min(y_pos, desktop.height() - self.height() - 10))
        
        self.move(x_pos, y_pos)
        
        # Store the background color for possible updates
        self.bg_color = bg_color
        
        # Set up close detection
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Dragging support
        self.drag_position = QPoint()
    
    def update_project_name(self, name):
        """Update the project name displayed in the timer"""
        self.project_name = name
        self.project_label.setText(name)
    
    def eventFilter(self, obj, event):
        # Handle mouse events on the logo label
        if obj == self.logo_label:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.logo_label.setCursor(Qt.CursorShape.ClosedHandCursor)
                return True
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                self.dragging = False
                self.logo_label.setCursor(Qt.CursorShape.OpenHandCursor)
                return True
            elif event.type() == QEvent.Type.MouseMove and self.dragging:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    new_pos = event.globalPosition().toPoint() - self.drag_position
                    self.move(new_pos)
                    return True
        return super().eventFilter(obj, event)
    
    def mousePressEvent(self, event):
        # Only processes events not handled by the time_label (which is transparent to events)
        # or the logo_label (which has its own event filter)
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        event.accept()
    
    def mouseMoveEvent(self, event):
        # Only processes events not handled by the time_label or logo_label
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
        event.accept()
    
    def mouseReleaseEvent(self, event):
        # Only processes events not handled by the time_label or logo_label
        if self.dragging:
            self.dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Find parent window to reposition all timers
            parent_window = None
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow) and hasattr(widget, 'reposition_all_timers'):
                    parent_window = widget
                    break
                    
            # Call reposition_all_timers if available
            if parent_window:
                parent_window.reposition_all_timers()
                
        event.accept()
    
    def enterEvent(self, event):
        # When mouse enters the widget, show the logo and reduce opacity
        self.logo_label.setVisible(True)
        self.setWindowOpacity(self.hover_opacity)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # When mouse leaves, hide the logo and restore opacity
        if not self.dragging:
            self.logo_label.setVisible(False)
            self.setWindowOpacity(self.default_opacity)
        super().leaveEvent(event)
    
    def set_opacity(self, opacity):
        """Set the default opacity of the timer"""
        self.default_opacity = opacity
        if not self.underMouse():  # Only update if not being hovered over
            self.setWindowOpacity(self.default_opacity)
    
    def update_time(self, seconds_left):
        """Update the countdown display"""
        hours, remainder = divmod(seconds_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def update_color(self, color):
        """Update the background color of the timer"""
        if not isinstance(color, QColor):
            return
            
        # Make the color a bit darker for better contrast
        bg_r = max(color.red() // 2, 30)
        bg_g = max(color.green() // 2, 30) 
        bg_b = max(color.blue() // 2, 30)
        bg_color = QColor(bg_r, bg_g, bg_b)
        
        # Convert to hex for stylesheet
        bg_color_hex = f"#{bg_color.red():02x}{bg_color.green():02x}{bg_color.blue():02x}"
        
        # Update the styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color_hex}; 
                border-radius: 5px;
                border: 1px solid #444444;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        # Store the updated background color
        self.bg_color = bg_color

    def closeEvent(self, event):
        """Handle timer window close event"""
        project_name = self.project_label.text() if hasattr(self, 'project_label') else "Unknown"
        print(f"TIMER: Timer closing: {project_name} (ID: {self.project_id})")
        super().closeEvent(event)

class TabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        
        # Set styling for tabs and close button with dark theme
        self.setStyleSheet("""
            QTabBar::tab {
                background-color: #1E2226;
                border: 1px solid #444444;
                padding: 5px 8px;
                min-width: 80px;
                color: #CCCCCC;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2D3339;
                border-bottom-color: #2D3339;
                color: white;
            }
            QTabBar::tab:last {
                min-width: 30px;
                max-width: 30px;
                min-height: 25px;
                background-color: #2D4050;
            }
            QTabBar::tab:last:hover {
                background-color: #3D5060;
            }
        """)
    
    def paintEvent(self, event):
        """Override paint event to customize tab appearance"""
        painter = QPainter(self)
        option = QStyleOptionTab()
        
        # Paint each tab with custom styling
        for i in range(self.count()):
            self.initStyleOption(option, i)
            
            # Get any custom tab data (like background color)
            tab_data = self.tabData(i)
            
            # If this tab has custom background color data, use it
            if tab_data and isinstance(tab_data, dict) and 'bg_color' in tab_data:
                bg_color = tab_data['bg_color']
                
                # Create a custom rect for the tab
                rect = self.tabRect(i)
                
                # Draw custom background
                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(bg_color)
                
                # Draw rounded rectangle for the tab (except for the + tab)
                if i == self.count() - 1 and self.parent() and hasattr(self.parent(), 'add_tab_is_visible') and self.parent().add_tab_is_visible:
                    # The + tab uses the default styling
                    pass
                else:
                    painter.drawRoundedRect(rect, 3, 3)
                
                painter.restore()
        
        # Let the base class handle the rest of the painting
        super().paintEvent(event)
        
        # After painting, ensure close buttons are properly set on all tabs
        for i in range(self.count()):
            # Skip the last tab which is the + tab
            if i < self.count() - 1:
                # Update or create close button if needed
                existing_btn = self.tabButton(i, QTabBar.ButtonPosition.RightSide)
                if not existing_btn or not existing_btn.isVisible():
                    close_button = self.createCloseButton()
                    self.setTabButton(i, QTabBar.ButtonPosition.RightSide, close_button)
            else:
                # Ensure the + tab has no close button
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
    
    def tabInserted(self, index):
        """Handle tab insertion to manage close buttons"""
        super().tabInserted(index)
        
        # Process all tabs to make sure close buttons are correctly configured
        for i in range(self.count()):
            # Special handling for the + tab (last tab)
            if i == self.count() - 1:
                # Remove close button for the + tab
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
            else:
                # Create and set a visible close button with X for all regular tabs
                close_button = self.createCloseButton()
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, close_button)
    
    def closeTab(self, index):
        """Handle tab close event"""
        print(f"TAB_CLOSE: Start closeTab method for index {index}, total tabs {self.count()}")
        
        # Allow closing any tab except the + tab (last tab)
        if index != self.count() - 1:
            print(f"TAB_CLOSE: Closing non-plus tab at index {index}")
            
            # Check if this is the last regular tab
            if self.count() <= 2:  # Just this tab and the + tab
                # Don't close if it's the last tab
                print("TAB_CLOSE: Cannot close last tab")
                
                # Find the main window to show toast
                main_window = None
                parent = self.parent()
                while parent is not None:
                    if isinstance(parent, VersionDivingApp):
                        main_window = parent
                        break
                    parent = parent.parent()
                
                if main_window and hasattr(main_window, 'show_toast'):
                    main_window.show_toast("Cannot close the last project tab", 3000)
                else:
                    print("TAB_CLOSE: Could not find main window to show toast")
                return
            
            # Find the main window to access project data
            main_window = None
            parent = self.parent()
            while parent is not None:
                if isinstance(parent, VersionDivingApp):
                    main_window = parent
                    break
                parent = parent.parent()
                
            print(f"TAB_CLOSE: Got main window reference: {main_window}")
            
            if main_window and hasattr(main_window, 'project_tabs') and index < len(main_window.project_tabs):
                print(f"TAB_CLOSE: Closing tab {index}, project_tabs contains {len(main_window.project_tabs)} projects")
                
                # Store the tab widget before removing it
                tab_widget = self.parent().widget(index)
                print(f"TAB_CLOSE: Got tab widget reference: {tab_widget}")
                
                # Get the project being closed
                project = main_window.project_tabs[index]
                print(f"TAB_CLOSE: Project being closed: {project.get('name')}")
                
                # Log timer info for debugging
                if hasattr(main_window, 'debug_timers'):
                    print("TAB_CLOSE: Debugging timers before removal:")
                    main_window.debug_timers()
                
                # Remove the floating timer if it exists
                floating_timer = project.get('floating_timer')
                if floating_timer:
                    print(f"TAB_CLOSE: Removing timer for closed tab: {index}")
                    # Remove from the all_floating_timers list
                    if hasattr(main_window, 'all_floating_timers') and floating_timer in main_window.all_floating_timers:
                        print(f"TAB_CLOSE: Removing timer from all_floating_timers")
                        main_window.all_floating_timers.remove(floating_timer)
                    
                    # Close and destroy the timer
                    print(f"TAB_CLOSE: Closing timer")
                    floating_timer.close()
                    print(f"TAB_CLOSE: Deleting timer later")
                    floating_timer.deleteLater()
                    print(f"TAB_CLOSE: Setting project's timer to None")
                    project['floating_timer'] = None
                    
                # Stop any running timers
                timer = project.get('auto_create_timer')
                if timer and hasattr(timer, 'isActive') and timer.isActive():
                    print(f"TAB_CLOSE: Stopping auto_create_timer")
                    timer.stop()
                    
                countdown_timer = project.get('countdown_timer')
                if countdown_timer and hasattr(countdown_timer, 'isActive') and countdown_timer.isActive():
                    print(f"TAB_CLOSE: Stopping countdown_timer")
                    countdown_timer.stop()
                
                # Now remove the tab widget first
                print(f"TAB_CLOSE: Removing tab widget at index {index}")
                parent_tab_widget = self.parent()
                if isinstance(parent_tab_widget, QTabWidget):
                    parent_tab_widget.removeTab(index)
                    print(f"TAB_CLOSE: Tab removed, remaining tab count: {parent_tab_widget.count()}")
                else:
                    self.removeTab(index)
                    print(f"TAB_CLOSE: Tab removed via TabBar (not QTabWidget)")
                
                # Then remove the project from main_window.project_tabs
                print(f"TAB_CLOSE: Removing project from project_tabs list")
                main_window.project_tabs.pop(index)
                print(f"TAB_CLOSE: Project removed, remaining projects: {len(main_window.project_tabs)}")
                
                # Update current_project_index if needed
                print(f"TAB_CLOSE: Current project index before adjustment: {main_window.current_project_index}")
                if main_window.current_project_index >= len(main_window.project_tabs):
                    print(f"TAB_CLOSE: Adjusting current project index to last project")
                    main_window.current_project_index = len(main_window.project_tabs) - 1
                elif main_window.current_project_index >= index:
                    # If removing a tab before the current one, adjust the index
                    print(f"TAB_CLOSE: Adjusting current project index from {main_window.current_project_index} to {main_window.current_project_index - 1}")
                    main_window.current_project_index -= 1
                print(f"TAB_CLOSE: Current project index after adjustment: {main_window.current_project_index}")
                
                # Use the aggressive cleanup to fix any timer issues
                print("TAB_CLOSE: Running force_timer_cleanup after tab close")
                if hasattr(main_window, 'force_timer_cleanup'):
                    main_window.force_timer_cleanup()
                
                print(f"TAB_CLOSE: After cleanup, remaining tabs: {parent_tab_widget.count() if isinstance(parent_tab_widget, QTabWidget) else 'unknown'}")
                    
                # If we still have projects, load the current one
                if main_window.project_tabs:
                    print(f"TAB_CLOSE: Loading project state for index {main_window.current_project_index}")
                    main_window.load_project_state(main_window.current_project_index)
                
                print("TAB_CLOSE: Tab close completed successfully")
                return
                
            # Fallback: Just remove the tab if we can't find associated project data
            print(f"TAB_CLOSE: Fallback - no project data found for index {index}")
            self.removeTab(index)
            print(f"TAB_CLOSE: Tab removed via fallback path")
        else:
            print(f"TAB_CLOSE: Attempting to close the + tab, ignoring")
    
    def tabSizeHint(self, index):
        """Customize tab sizes"""
        size = super().tabSizeHint(index)
        
        # Make the + tab a small square (last tab is always the + tab)
        if index == self.count() - 1:
            size.setWidth(30)
            
        return size
    
    def createCloseButton(self):
        """Create a visible close button for tabs with a clear X"""
        # Create a direct button with text "X"
        button = QPushButton("✕")  # Using Unicode X symbol
        button.setFixedSize(16, 16)
        button.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        
        # Very clear styling with direct background and foreground colors
        button.setStyleSheet("""
            QPushButton {
                color: #CCCCCC;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                margin: 0px;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                color: white;
                background-color: #FF4444;
            }
        """)
        
        button.clicked.connect(lambda: self.tabCloseRequested.emit(self.tabAt(button.pos())))
        return button

class ProjectTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up tab bar and remove the default one
        self.custom_tab_bar = TabBar()
        self.setTabBar(self.custom_tab_bar)
        
        # Set tab position
        self.setTabPosition(QTabWidget.TabPosition.North)
        self.setMovable(True)
        
        # Store main window reference
        self.main_window = parent
        
        # Track the previous index for tab changes
        self.prev_index = 0
        
        # Flag to track the "+" tab visibility
        self.add_tab_is_visible = False
        
        # Dictionary to store tab colors
        self.tab_colors = {}
        
        # Create info button and add it to corner
        self.info_button = QPushButton()
        self.info_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        self.info_button.setToolTip("Show Help")
        self.info_button.setFixedSize(24, 24)
        self.info_button.setStyleSheet("""
            QPushButton {
                background-color: #3D4852;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4D5862;
            }
        """)
        
        # Create corner widget to host the info button
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(2, 2, 2, 2)
        corner_layout.addWidget(self.info_button)
        self.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
        
        # Add the "+" tab
        self.addTab(QWidget(), "+")
        self.add_tab_is_visible = True
        
        # Connect signals for tab management
        self.currentChanged.connect(self.handleTabChange)
        
        # Apply dark styling to match app theme - only style the pane
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #2D3339;
            }
        """)
    
    def setTabColor(self, index, color):
        """Set the color for a specific tab"""
        if index >= 0 and index < self.count():
            self.tab_colors[index] = color
            self.custom_tab_bar.setTabTextColor(index, color)
            
            # Create a custom background color that's a muted version of the text color
            r, g, b = color.red(), color.green(), color.blue()
            # Make it darker but maintain the hue
            bg_r = max(r // 2, 30)
            bg_g = max(g // 2, 30) 
            bg_b = max(b // 2, 30)
            
            # Apply specific style to this tab
            self.tabBar().setTabData(index, {'bg_color': QColor(bg_r, bg_g, bg_b)})
            self.tabBar().update()
    
    def getTabColor(self, index):
        """Get the color for a specific tab"""
        return self.tab_colors.get(index, QColor(255, 255, 255))  # Default white
    
    def handleTabChange(self, index):
        """Handle when tabs are changed by the user"""
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Override to ensure proper handling of project tabs"""
        print(f"PROJECT_TAB_WIDGET: removeTab called for index {index}")
        
        # Only handle regular tabs (not the + tab)
        if index != self.count() - 1:
            # Let the main application know a tab is being removed
            main_window = self.parent()
            if isinstance(main_window, VersionDivingApp) and hasattr(main_window, 'remove_project_tab'):
                print(f"PROJECT_TAB_WIDGET: Calling remove_project_tab on main window")
                # This will handle timer cleanup
                main_window.remove_project_tab(index)
            else:
                print(f"PROJECT_TAB_WIDGET: No main window found, calling superclass removeTab")
                super().removeTab(index)
        else:
            print(f"PROJECT_TAB_WIDGET: Cannot remove + tab")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    
    def handleTabChange(self, index):
        pass  # Add implementation as needed
import shutil
import datetime
import json
import webbrowser
import uuid
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QListWidget, QTabWidget, 
                            QSpinBox, QCheckBox, QLineEdit, QComboBox, QScrollArea, 
                            QMessageBox, QGroupBox, QRadioButton, QSplitter, QFrame,
                            QListWidgetItem, QMenu, QDialog, QSystemTrayIcon, QStyle,
                            QToolButton, QSlider, QTabBar, QTextEdit, QColorDialog, QStyleOptionTab)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QAction, QColor, QPalette, QMovie, QPainter
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint, QEvent
import hashlib

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(base_path, relative_path)

class ToastNotification(QDialog):
    def __init__(self, parent=None, message="", icon=None, timeout=3000):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Arial", 10))
        label.setStyleSheet("padding: 10px;")
        layout.addWidget(label)
        
        # Set size and position
        self.setFixedWidth(300)
        self.adjustSize()
        
        # Position at top-right corner
        desktop = QApplication.primaryScreen().geometry()
        self.move(desktop.width() - self.width() - 20, 50)
        
        # Auto-close timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(timeout)
        
    def showEvent(self, event):
        super().showEvent(event)
        # Add fade-in effect if desired
        
    def closeEvent(self, event):
        super().closeEvent(event)
        # Add fade-out effect if desired

# New class for the floating countdown timer
class FloatingCountdownTimer(QWidget):
    def __init__(self, parent=None, project_name="Project", project_color=None, project_id=None):
        super().__init__(parent)
        print(f"TIMER: Creating new floating timer: {project_name} (ID: {project_id})")
        
        # Store project ID for association tracking
        self.project_id = project_id
        
        # Track dragging state
        self.dragging = False
        
        # Create floating widget with no frame
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set a fixed size for the timer display
        self.setFixedSize(200, 30)
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Set opacity levels
        self.default_opacity = 0.85
        self.hover_opacity = 1.0
        self.setWindowOpacity(self.default_opacity)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Project-specific hash for unique identification and color
        hash_val = hash(project_name) if project_name else hash(str(id(self)))
        hash_hex = format(abs(hash_val), '08x')[:6]  # Use first 6 hex chars
        
        # Create app logo/drag handle with the clock icon
        self.logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'clock.png'))
        if not logo_pixmap.isNull():
            # Scale to small icon size
            logo_pixmap = logo_pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(logo_pixmap)
        else:
            # Fallback if icon not found
            self.logo_label.setText("⏱")
            self.logo_label.setStyleSheet("color: white; font-size: 14px;")
        
        # Initially hide the logo/handle until hover
        self.logo_label.setVisible(False)
        
        # Set fixed width for logo
        self.logo_label.setFixedWidth(16)
        
        # Add the logo label to the layout
        layout.addWidget(self.logo_label)
        
        # Add project name label
        self.project_label = QLabel(project_name)
        self.project_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.project_label.setFont(QFont("Arial", 8))
        self.project_label.setStyleSheet("background-color: transparent; color: white;")
        # Make the project label click-through
        self.project_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.project_label)
        
        # Add spacer to push time to the right
        layout.addStretch(1)
        
        # Add text label
        self.time_label = QLabel("--:--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.time_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.time_label.setStyleSheet("background-color: transparent; color: white;")
        # Make the time label click-through
        self.time_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.time_label)
        
        # Use provided color or generate one
        if project_color and isinstance(project_color, QColor):
            bg_color = project_color
            # Make it a bit darker for better contrast
            bg_r = max(bg_color.red() // 2, 30)
            bg_g = max(bg_color.green() // 2, 30) 
            bg_b = max(bg_color.blue() // 2, 30)
            bg_color = QColor(bg_r, bg_g, bg_b)
        else:
            # Generate a unique color for this timer based on project name
            r = int(hash_hex[0:2], 16) % 128 + 32  # Keep it dark enough for white text
            g = int(hash_hex[2:4], 16) % 128 + 32
            b = int(hash_hex[4:6], 16) % 128 + 32
            bg_color = QColor(r, g, b)
        
        # Convert to hex for stylesheet
        bg_color_hex = f"#{bg_color.red():02x}{bg_color.green():02x}{bg_color.blue():02x}"
        
        # Set overall styling with project-specific color
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color_hex}; 
                border-radius: 5px;
                border: 1px solid #444444;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        # Find if this is part of a main window that has existing timers
        parent_window = None
        if parent:
            parent_window = parent
        else:
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow):
                    parent_window = widget
                    break
        
        # Get all existing timers to stack this one below them
        existing_timers = []
        if parent_window and hasattr(parent_window, 'all_floating_timers'):
            existing_timers = parent_window.all_floating_timers
        
        # Position in the top-right corner of the screen
        desktop = QApplication.primaryScreen().geometry()
        x_pos = desktop.width() - self.width() - 20  # 20px from right edge
        
        # If there are existing timers, position this one below the last one
        y_pos = 50  # Default starting position
        if existing_timers:
            # Find the lowest existing timer
            max_y = 50
            for timer in existing_timers:
                if timer and timer.isVisible():
                    timer_bottom = timer.y() + timer.height()
                    if timer_bottom > max_y:
                        max_y = timer_bottom
            
            y_pos = max_y + 10  # 10px spacing between timers
        
        # Ensure timers don't go off screen
        x_pos = max(10, min(x_pos, desktop.width() - self.width() - 10))
        y_pos = max(10, min(y_pos, desktop.height() - self.height() - 10))
        
        self.move(x_pos, y_pos)
        
        # Store the background color for possible updates
        self.bg_color = bg_color
        
        # Set up close detection
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Dragging support
        self.drag_position = QPoint()
    
    def update_project_name(self, name):
        """Update the project name displayed in the timer"""
        self.project_name = name
        self.project_label.setText(name)
    
    def eventFilter(self, obj, event):
        # Handle mouse events on the logo label
        if obj == self.logo_label:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.logo_label.setCursor(Qt.CursorShape.ClosedHandCursor)
                return True
            elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                self.dragging = False
                self.logo_label.setCursor(Qt.CursorShape.OpenHandCursor)
                return True
            elif event.type() == QEvent.Type.MouseMove and self.dragging:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    new_pos = event.globalPosition().toPoint() - self.drag_position
                    self.move(new_pos)
                    return True
        return super().eventFilter(obj, event)
    
    def mousePressEvent(self, event):
        # Only processes events not handled by the time_label (which is transparent to events)
        # or the logo_label (which has its own event filter)
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        event.accept()
    
    def mouseMoveEvent(self, event):
        # Only processes events not handled by the time_label or logo_label
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
        event.accept()
    
    def mouseReleaseEvent(self, event):
        # Only processes events not handled by the time_label or logo_label
        if self.dragging:
            self.dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Find parent window to reposition all timers
            parent_window = None
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow) and hasattr(widget, 'reposition_all_timers'):
                    parent_window = widget
                    break
                    
            # Call reposition_all_timers if available
            if parent_window:
                parent_window.reposition_all_timers()
                
        event.accept()
    
    def enterEvent(self, event):
        # When mouse enters the widget, show the logo and reduce opacity
        self.logo_label.setVisible(True)
        self.setWindowOpacity(self.hover_opacity)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # When mouse leaves, hide the logo and restore opacity
        if not self.dragging:
            self.logo_label.setVisible(False)
            self.setWindowOpacity(self.default_opacity)
        super().leaveEvent(event)
    
    def set_opacity(self, opacity):
        """Set the default opacity of the timer"""
        self.default_opacity = opacity
        if not self.underMouse():  # Only update if not being hovered over
            self.setWindowOpacity(self.default_opacity)
    
    def update_time(self, seconds_left):
        """Update the countdown display"""
        hours, remainder = divmod(seconds_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def update_color(self, color):
        """Update the background color of the timer"""
        if not isinstance(color, QColor):
            return
            
        # Make the color a bit darker for better contrast
        bg_r = max(color.red() // 2, 30)
        bg_g = max(color.green() // 2, 30) 
        bg_b = max(color.blue() // 2, 30)
        bg_color = QColor(bg_r, bg_g, bg_b)
        
        # Convert to hex for stylesheet
        bg_color_hex = f"#{bg_color.red():02x}{bg_color.green():02x}{bg_color.blue():02x}"
        
        # Update the styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color_hex}; 
                border-radius: 5px;
                border: 1px solid #444444;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        # Store the updated background color
        self.bg_color = bg_color

    def closeEvent(self, event):
        """Handle timer window close event"""
        project_name = self.project_label.text() if hasattr(self, 'project_label') else "Unknown"
        print(f"TIMER: Timer closing: {project_name} (ID: {self.project_id})")
        super().closeEvent(event)

class TabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        
        # Set styling for tabs and close button with dark theme
        self.setStyleSheet("""
            QTabBar::tab {
                background-color: #1E2226;
                border: 1px solid #444444;
                padding: 5px 8px;
                min-width: 80px;
                color: #CCCCCC;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2D3339;
                border-bottom-color: #2D3339;
                color: white;
            }
            QTabBar::tab:last {
                min-width: 30px;
                max-width: 30px;
                min-height: 25px;
                background-color: #2D4050;
            }
            QTabBar::tab:last:hover {
                background-color: #3D5060;
            }
        """)
    
    def paintEvent(self, event):
        """Override paint event to customize tab appearance"""
        painter = QPainter(self)
        option = QStyleOptionTab()
        
        # Paint each tab with custom styling
        for i in range(self.count()):
            self.initStyleOption(option, i)
            
            # Get any custom tab data (like background color)
            tab_data = self.tabData(i)
            
            # If this tab has custom background color data, use it
            if tab_data and isinstance(tab_data, dict) and 'bg_color' in tab_data:
                bg_color = tab_data['bg_color']
                
                # Create a custom rect for the tab
                rect = self.tabRect(i)
                
                # Draw custom background
                painter.save()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(bg_color)
                
                # Draw rounded rectangle for the tab (except for the + tab)
                if i == self.count() - 1 and self.parent() and hasattr(self.parent(), 'add_tab_is_visible') and self.parent().add_tab_is_visible:
                    # The + tab uses the default styling
                    pass
                else:
                    painter.drawRoundedRect(rect, 3, 3)
                
                painter.restore()
        
        # Let the base class handle the rest of the painting
        super().paintEvent(event)
        
        # After painting, ensure close buttons are properly set on all tabs
        for i in range(self.count()):
            # Skip the last tab which is the + tab
            if i < self.count() - 1:
                # Update or create close button if needed
                existing_btn = self.tabButton(i, QTabBar.ButtonPosition.RightSide)
                if not existing_btn or not existing_btn.isVisible():
                    close_button = self.createCloseButton()
                    self.setTabButton(i, QTabBar.ButtonPosition.RightSide, close_button)
            else:
                # Ensure the + tab has no close button
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
    
    def tabInserted(self, index):
        """Handle tab insertion to manage close buttons"""
        super().tabInserted(index)
        
        # Process all tabs to make sure close buttons are correctly configured
        for i in range(self.count()):
            # Special handling for the + tab (last tab)
            if i == self.count() - 1:
                # Remove close button for the + tab
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
            else:
                # Create and set a visible close button with X for all regular tabs
                close_button = self.createCloseButton()
                self.setTabButton(i, QTabBar.ButtonPosition.RightSide, close_button)
    
    def closeTab(self, index):
        """Handle tab close event"""
        print(f"TAB_CLOSE: Start closeTab method for index {index}, total tabs {self.count()}")
        
        # Allow closing any tab except the + tab (last tab)
        if index != self.count() - 1:
            print(f"TAB_CLOSE: Closing non-plus tab at index {index}")
            
            # Check if this is the last regular tab
            if self.count() <= 2:  # Just this tab and the + tab
                # Don't close if it's the last tab
                print("TAB_CLOSE: Cannot close last tab")
                
                # Find the main window to show toast
                main_window = None
                parent = self.parent()
                while parent is not None:
                    if isinstance(parent, VersionDivingApp):
                        main_window = parent
                        break
                    parent = parent.parent()
                
                if main_window and hasattr(main_window, 'show_toast'):
                    main_window.show_toast("Cannot close the last project tab", 3000)
                else:
                    print("TAB_CLOSE: Could not find main window to show toast")
                return
            
            # Find the main window to access project data
            main_window = None
            parent = self.parent()
            while parent is not None:
                if isinstance(parent, VersionDivingApp):
                    main_window = parent
                    break
                parent = parent.parent()
                
            print(f"TAB_CLOSE: Got main window reference: {main_window}")
            
            if main_window and hasattr(main_window, 'project_tabs') and index < len(main_window.project_tabs):
                print(f"TAB_CLOSE: Closing tab {index}, project_tabs contains {len(main_window.project_tabs)} projects")
                
                # Store the tab widget before removing it
                tab_widget = self.parent().widget(index)
                print(f"TAB_CLOSE: Got tab widget reference: {tab_widget}")
                
                # Get the project being closed
                project = main_window.project_tabs[index]
                print(f"TAB_CLOSE: Project being closed: {project.get('name')}")
                
                # Log timer info for debugging
                if hasattr(main_window, 'debug_timers'):
                    print("TAB_CLOSE: Debugging timers before removal:")
                    main_window.debug_timers()
                
                # Remove the floating timer if it exists
                floating_timer = project.get('floating_timer')
                if floating_timer:
                    print(f"TAB_CLOSE: Removing timer for closed tab: {index}")
                    # Remove from the all_floating_timers list
                    if hasattr(main_window, 'all_floating_timers') and floating_timer in main_window.all_floating_timers:
                        print(f"TAB_CLOSE: Removing timer from all_floating_timers")
                        main_window.all_floating_timers.remove(floating_timer)
                    
                    # Close and destroy the timer
                    print(f"TAB_CLOSE: Closing timer")
                    floating_timer.close()
                    print(f"TAB_CLOSE: Deleting timer later")
                    floating_timer.deleteLater()
                    print(f"TAB_CLOSE: Setting project's timer to None")
                    project['floating_timer'] = None
                    
                # Stop any running timers
                timer = project.get('auto_create_timer')
                if timer and hasattr(timer, 'isActive') and timer.isActive():
                    print(f"TAB_CLOSE: Stopping auto_create_timer")
                    timer.stop()
                    
                countdown_timer = project.get('countdown_timer')
                if countdown_timer and hasattr(countdown_timer, 'isActive') and countdown_timer.isActive():
                    print(f"TAB_CLOSE: Stopping countdown_timer")
                    countdown_timer.stop()
                
                # Now remove the tab widget first
                print(f"TAB_CLOSE: Removing tab widget at index {index}")
                parent_tab_widget = self.parent()
                if isinstance(parent_tab_widget, QTabWidget):
                    parent_tab_widget.removeTab(index)
                    print(f"TAB_CLOSE: Tab removed, remaining tab count: {parent_tab_widget.count()}")
                else:
                    self.removeTab(index)
                    print(f"TAB_CLOSE: Tab removed via TabBar (not QTabWidget)")
                
                # Then remove the project from main_window.project_tabs
                print(f"TAB_CLOSE: Removing project from project_tabs list")
                main_window.project_tabs.pop(index)
                print(f"TAB_CLOSE: Project removed, remaining projects: {len(main_window.project_tabs)}")
                
                # Update current_project_index if needed
                print(f"TAB_CLOSE: Current project index before adjustment: {main_window.current_project_index}")
                if main_window.current_project_index >= len(main_window.project_tabs):
                    print(f"TAB_CLOSE: Adjusting current project index to last project")
                    main_window.current_project_index = len(main_window.project_tabs) - 1
                elif main_window.current_project_index >= index:
                    # If removing a tab before the current one, adjust the index
                    print(f"TAB_CLOSE: Adjusting current project index from {main_window.current_project_index} to {main_window.current_project_index - 1}")
                    main_window.current_project_index -= 1
                print(f"TAB_CLOSE: Current project index after adjustment: {main_window.current_project_index}")
                
                # Use the aggressive cleanup to fix any timer issues
                print("TAB_CLOSE: Running force_timer_cleanup after tab close")
                if hasattr(main_window, 'force_timer_cleanup'):
                    main_window.force_timer_cleanup()
                
                print(f"TAB_CLOSE: After cleanup, remaining tabs: {parent_tab_widget.count() if isinstance(parent_tab_widget, QTabWidget) else 'unknown'}")
                    
                # If we still have projects, load the current one
                if main_window.project_tabs:
                    print(f"TAB_CLOSE: Loading project state for index {main_window.current_project_index}")
                    main_window.load_project_state(main_window.current_project_index)
                
                print("TAB_CLOSE: Tab close completed successfully")
                return
                
            # Fallback: Just remove the tab if we can't find associated project data
            print(f"TAB_CLOSE: Fallback - no project data found for index {index}")
            self.removeTab(index)
            print(f"TAB_CLOSE: Tab removed via fallback path")
        else:
            print(f"TAB_CLOSE: Attempting to close the + tab, ignoring")
    
    def tabSizeHint(self, index):
        """Customize tab sizes"""
        size = super().tabSizeHint(index)
        
        # Make the + tab a small square (last tab is always the + tab)
        if index == self.count() - 1:
            size.setWidth(30)
            
        return size
    
    def createCloseButton(self):
        """Create a visible close button for tabs with a clear X"""
        # Create a direct button with text "X"
        button = QPushButton("✕")  # Using Unicode X symbol
        button.setFixedSize(16, 16)
        button.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        
        # Very clear styling with direct background and foreground colors
        button.setStyleSheet("""
            QPushButton {
                color: #CCCCCC;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                margin: 0px;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                color: white;
                background-color: #FF4444;
            }
        """)
        
        button.clicked.connect(lambda: self.tabCloseRequested.emit(self.tabAt(button.pos())))
        return button

class ProjectTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up tab bar and remove the default one
        self.custom_tab_bar = TabBar()
        self.setTabBar(self.custom_tab_bar)
        
        # Set tab position
        self.setTabPosition(QTabWidget.TabPosition.North)
        self.setMovable(True)
        
        # Store main window reference
        self.main_window = parent
        
        # Track the previous index for tab changes
        self.prev_index = 0
        
        # Flag to track the "+" tab visibility
        self.add_tab_is_visible = False
        
        # Dictionary to store tab colors
        self.tab_colors = {}
        
        # Create info button and add it to corner
        self.info_button = QPushButton()
        self.info_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        self.info_button.setToolTip("Show Help")
        self.info_button.setFixedSize(24, 24)
        self.info_button.setStyleSheet("""
            QPushButton {
                background-color: #3D4852;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4D5862;
            }
        """)
        
        # Create corner widget to host the info button
        corner_widget = QWidget()
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(2, 2, 2, 2)
        corner_layout.addWidget(self.info_button)
        self.setCornerWidget(corner_widget, Qt.Corner.TopRightCorner)
        
        # Add the "+" tab
        self.addTab(QWidget(), "+")
        self.add_tab_is_visible = True
        
        # Connect signals for tab management
        self.currentChanged.connect(self.handleTabChange)
        
        # Apply dark styling to match app theme - only style the pane
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #2D3339;
            }
        """)
    
    def setTabColor(self, index, color):
        """Set the color for a specific tab"""
        if index >= 0 and index < self.count():
            self.tab_colors[index] = color
            self.custom_tab_bar.setTabTextColor(index, color)
            
            # Create a custom background color that's a muted version of the text color
            r, g, b = color.red(), color.green(), color.blue()
            # Make it darker but maintain the hue
            bg_r = max(r // 2, 30)
            bg_g = max(g // 2, 30) 
            bg_b = max(b // 2, 30)
            
            # Apply specific style to this tab
            self.tabBar().setTabData(index, {'bg_color': QColor(bg_r, bg_g, bg_b)})
            self.tabBar().update()
    
    def getTabColor(self, index):
        """Get the color for a specific tab"""
        return self.tab_colors.get(index, QColor(255, 255, 255))  # Default white
    
    def handleTabChange(self, index):
        """Handle when tabs are changed by the user"""
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Remove a tab and preserve the + tab"""
        # If removing a regular tab (not the + tab)
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and index < self.count() - 1:
            # First notify the main window to remove the project data
            if self.main_window and hasattr(self.main_window, 'remove_project_tab'):
                self.main_window.remove_project_tab(index)
                
            # Then remove the actual tab widget
            super().removeTab(index)
        else:
            # Removing the + tab itself or we don't have add_tab_is_visible
            super().removeTab(index)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.cleanup_orphaned_timers()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def handleTabChange(self, index):
        # Check if the clicked tab is the "+" tab (last tab)
        if index == self.count() - 1 and self.add_tab_is_visible:
            # Block signals to prevent infinite loop
            self.blockSignals(True)
            # Set the active tab to the previous one
            prev_index = max(0, index - 1)
            self.setCurrentIndex(prev_index)
            # Unblock signals
            self.blockSignals(False)
            # Add new empty project tab
            if hasattr(self.main_window, 'add_project_tab'):
                self.main_window.add_project_tab()
    
    def addTab(self, widget, label):
        """Add a tab and handle the + tab properly"""
        # If we're adding the + tab
        if label == "+" and hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible:
            # Create a custom widget for the + tab with better styling
            plus_widget = QWidget()
            plus_layout = QVBoxLayout(plus_widget)
            plus_layout.setContentsMargins(1, 1, 1, 1)
            
            plus_button = QPushButton("+")
            plus_button.setStyleSheet("""
                QPushButton {
                    background-color: #3D5066;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #4D6076;
                }
                QPushButton:pressed {
                    background-color: #2D4056;
                }
            """)
            plus_button.clicked.connect(lambda: self.setCurrentIndex(self.count() - 1))
            plus_layout.addWidget(plus_button)
            
            # Add the tab with our custom widget
            index = super().addTab(plus_widget, "")
            
            # Ensure the close button is hidden for the + tab
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
            
            # Add a small plus icon to the tab
            icon_label = QLabel()
            icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
            icon_label.setText("+")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            return index
            
        # Call the parent class implementation for regular tabs
        index = super().addTab(widget, label)
        
        # If we have the + tab, keep it at the end
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and label != "+":
            # Move the + tab to the end
            plus_tab_widget = None
            # Block signals to prevent triggering unwanted events
            self.blockSignals(True)
            # Remove the + tab
            if self.count() > 1:
                plus_tab_widget = self.widget(self.count() - 1)
                super().removeTab(self.count() - 1)  # Use super().removeTab to avoid triggering our removeTab
            # Add it back at the end
            if plus_tab_widget:
                # Re-add the + tab
                plus_tab_index = super().addTab(plus_tab_widget, "")
                
                # Ensure the close button is hidden for the + tab
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.RightSide, None)
                
                # Add a small plus icon to the tab
                icon_label = QLabel()
                icon_label.setStyleSheet("QLabel { color: white; font-weight: bold; font-size: 18px; }")
                icon_label.setText("+")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabBar().setTabButton(plus_tab_index, QTabBar.ButtonPosition.LeftSide, icon_label)
            
            self.blockSignals(False)
        
        return index
    
    def removeTab(self, index):
        """Remove a tab and preserve the + tab"""
        # If removing a regular tab (not the + tab)
        if hasattr(self, 'add_tab_is_visible') and self.add_tab_is_visible and index < self.count() - 1:
            # First notify the main window to remove the project data
            if self.main_window and hasattr(self.main_window, 'remove_project_tab'):
                self.main_window.remove_project_tab(index)
                
            # Then remove the actual tab widget
            super().removeTab(index)
        else:
            # Removing the + tab itself or we don't have add_tab_is_visible
            super().removeTab(index)

class VersionDivingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Move these to be per-project properties
        self.origin_paths = []
        self.destination_path = ""
        self.projects_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recent_projects.json')
        self.recent_projects = self.load_recent_projects()
        
        # Track per-project auto-create state
        self.auto_create_running = False
        self.countdown_seconds = 0
        
        # We'll create these per-project in the switch_project method
        self.countdown_timer = None
        self.auto_create_timer = None
        self.floating_timer = None
        
        # Track all active floating timers across all projects
        self.all_floating_timers = []
        
        self.is_creating_version = False  # Flag to track when version creation is in progress
        # Store all project tabs
        self.project_tabs = []
        self.current_project_index = 0
        self.initUI()
        self.setup_system_tray()
        
        # Apply settings after UI initialization
        self.apply_initial_settings()
        
        # Set up a timer to periodically clean up orphaned timers
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_orphaned_timers)
        self.cleanup_timer.start(5000)  # Check every 5 seconds
    
    def apply_initial_settings(self):
        """Apply initial settings such as create on start and auto-create on load"""
        # Default settings if no recent projects
        create_on_start = False
        auto_create_on_load = False
        show_floating_timer = False
        
        # Get settings from most recent project if available
        if self.recent_projects and len(self.recent_projects) > 0:
            most_recent = self.recent_projects[0]
            create_on_start = most_recent.get('create_on_start', False)
            auto_create_on_load = most_recent.get('auto_create_on_load', False)
            show_floating_timer = most_recent.get('show_floating_timer', False)
            
            # Set UI from recent project settings without actually loading the project
            self.create_on_start_check.setChecked(create_on_start)
            self.auto_create_on_load_check.setChecked(auto_create_on_load)
            self.show_floating_timer_check.setChecked(show_floating_timer)
            
            # Don't load the project automatically
            # self.load_project(most_recent)
        
        # Apply floating timer setting
        self.toggle_floating_timer(show_floating_timer)
        
        # DO NOT start auto-create here - it will be started when loading the project if needed
    
    def setup_system_tray(self):
        """Set up the system tray icon and menu"""
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to use the logoicon.png first
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logoicon.png")
        
        if os.path.exists(logo_path):
            tray_icon = QIcon(logo_path)
            self.tray_icon.setIcon(tray_icon)
        else:
            # Use a system standard icon if custom icon not found
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            
        # Create tray menu
        self.tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        create_action = QAction("Create Version", self)
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.full_exit)
        create_action.triggered.connect(self.create_version)
        
        self.tray_menu.addAction(show_action)
        self.tray_menu.addAction(create_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Show a balloon message when minimized to tray
        self.tray_icon.messageClicked.connect(self.show)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Make sure the tray icon is visible
        self.tray_icon.setVisible(True)
        
        # Show a notification to confirm tray icon is working
        self.tray_icon.showMessage(
            "Version Diving", 
            "Application is running in the system tray",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def full_exit(self):
        # Stop all timers for all projects
        for project in self.project_tabs:
            timer = project.get('auto_create_timer')
            if timer and hasattr(timer, 'isActive') and timer.isActive():
                timer.stop()
                
            countdown_timer = project.get('countdown_timer')
            if countdown_timer and hasattr(countdown_timer, 'isActive') and countdown_timer.isActive():
                countdown_timer.stop()
        
        # Destroy all floating timers
        for timer in self.all_floating_timers:
            if timer:
                timer.close()
        self.all_floating_timers.clear()
        
        # Save settings
        self.save_recent_projects()
        
        # Exit the application
        QApplication.quit()
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Cleanup orphaned timers before closing
        self.force_timer_cleanup()
        
        # Prompt for saving unsaved work if needed
        event.accept()
    
    def show_toast(self, message, timeout=3000):
        toast = ToastNotification(self, message, timeout=timeout)
        toast.show()
        
    def load_recent_projects(self):
        if os.path.exists(self.projects_file):
            try:
                with open(self.projects_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_recent_projects(self):
        """Save the current project to the recent projects list"""
        # Get current settings
        current_project = {
            'origin_paths': self.origin_paths,
            'destination_path': self.destination_path,
            'prefix': self.prefix_edit.text(),
            'suffix': self.suffix_edit.text(),
            'format_index': self.name_format_combo.currentIndex(),
            'custom_format': self.custom_format_edit.text(),
            'auto_delete': self.auto_delete_check.isChecked(),
            'version_limit': self.version_limit_spin.value(),
            'auto_create': self.auto_create_check.isChecked(),
            'interval_value': self.interval_spin.value(),
            'interval_unit': self.interval_unit.currentIndex(),
            'create_on_start': self.create_on_start_check.isChecked(),
            'auto_create_on_load': self.auto_create_on_load_check.isChecked(),
            'show_floating_timer': self.show_floating_timer_check.isChecked(),
            'timer_opacity': self.timer_opacity_slider.value(),
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to recent projects if origin and destination are set
        if self.origin_paths and self.destination_path:
            # Remove existing entry with same paths
            self.recent_projects = [p for p in self.recent_projects 
                                 if not (p['origin_paths'] == self.origin_paths and 
                                        p['destination_path'] == self.destination_path)]
            
            # Add to beginning of list
            self.recent_projects.insert(0, current_project)
            
            # Keep only 10 most recent
            self.recent_projects = self.recent_projects[:10]
            
            # Save to file
            with open(self.projects_file, 'w') as f:
                json.dump(self.recent_projects, f)
            
            # Update recents tab
            self.update_recent_projects_list()
            
            # Show confirmation toast
            self.show_toast("Current project settings saved")
        else:
            self.show_toast("Cannot save: Please select both origin and destination", 5000)
    
    def initUI(self):
        self.setWindowTitle("Version Diving")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set application icon from logoicon.png
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logoicon.png")
        if os.path.exists(logo_path):
            app_icon = QIcon(logo_path)
            self.setWindowIcon(app_icon)
            # Set the application icon for the whole application
            QApplication.setWindowIcon(app_icon)
        else:
            # Fallback to resource icon
            icon_path = resource_path(os.path.join("resources", "app_icon.ico"))
            if os.path.exists(icon_path):
                app_icon = QIcon(icon_path)
                self.setWindowIcon(app_icon)
                QApplication.setWindowIcon(app_icon)
        
        # Create status bar with copyright notice
        status_bar = self.statusBar()
        status_bar.showMessage("Copyright © Version Diving - HE Design")
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create project tabs widget at the top
        self.project_tabs_widget = ProjectTabWidget(self)
        self.project_tabs_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.project_tabs_widget.currentChanged.connect(self.switch_project)
        
        # Connect the info button to show help
        self.project_tabs_widget.info_button.clicked.connect(self.show_help)
        
        # Add first project tab
        self.add_project_tab("Main Project")
        
        main_layout.addWidget(self.project_tabs_widget)
        
        self.setCentralWidget(main_widget)
        
    def update_origin_list(self):
        """Update the origin list widget"""
        self.origin_list.clear()
        for path in self.origin_paths:
            item = QListWidgetItem(path)
            if os.path.isdir(path):
                item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
            else:
                item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            self.origin_list.addItem(item)
        
        # Debug output
        print(f"Updated origin list with {len(self.origin_paths)} items")
    
    def update_button_states(self):
        """Update enabled/disabled state of buttons"""
        has_origin = len(self.origin_paths) > 0
        has_dest = bool(self.destination_path)
        
        # Update Create Version button
        self.create_version_btn.setEnabled(has_origin and has_dest)
        
        # Update Open buttons
        self.open_origin_btn.setEnabled(has_origin)
        self.open_dest_btn.setEnabled(has_dest)
    
    def update_contents_list(self):
        """Update the contents list with origin and destination files"""
        self.contents_list.clear()
        
        # Add origin contents
        if self.origin_paths:
            origin_header = QListWidgetItem("--- ORIGIN ---")
            origin_header.setBackground(QColor(240, 240, 240))
            origin_header.setForeground(QColor(0, 0, 0))
            self.contents_list.addItem(origin_header)
            
            for path in self.origin_paths:
                item = QListWidgetItem(path)
                if os.path.isdir(path):
                    item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                    # Also list the contents of the directory
                    try:
                        for subitem in os.listdir(path):
                            subitem_path = os.path.join(path, subitem)
                            sublist_item = QListWidgetItem(f"  {subitem}")
                            if os.path.isdir(subitem_path):
                                sublist_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                            else:
                                sublist_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                            self.contents_list.addItem(sublist_item)
                    except Exception as e:
                        error_item = QListWidgetItem(f"  Error listing directory: {str(e)}")
                        error_item.setForeground(QColor(255, 0, 0))
                        self.contents_list.addItem(error_item)
                else:
                    item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                self.contents_list.addItem(item)
        
        # Add destination contents
        if self.destination_path:
            self.contents_list.addItem("")
            dest_header = QListWidgetItem("--- DESTINATION ---")
            dest_header.setBackground(QColor(240, 240, 240))
            dest_header.setForeground(QColor(0, 0, 0))
            self.contents_list.addItem(dest_header)
            
            dest_item = QListWidgetItem(self.destination_path)
            dest_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
            self.contents_list.addItem(dest_item)
            
            try:
                for item in os.listdir(self.destination_path):
                    item_path = os.path.join(self.destination_path, item)
                    list_item = QListWidgetItem(f"  {item}")
                    if os.path.isdir(item_path):
                        list_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                        # List the contents of version folders (one level)
                        try:
                            for subitem in os.listdir(item_path):
                                subitem_path = os.path.join(item_path, subitem)
                                sublist_item = QListWidgetItem(f"    {subitem}")
                                if os.path.isdir(subitem_path):
                                    sublist_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                                else:
                                    sublist_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                                self.contents_list.addItem(sublist_item)
                        except Exception:
                            # Silently ignore errors listing sub-directories
                            pass
                    else:
                        list_item.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                    self.contents_list.addItem(list_item)
            except Exception as e:
                error_item = QListWidgetItem(f"Error listing directory: {str(e)}")
                error_item.setForeground(QColor(255, 0, 0))
                self.contents_list.addItem(error_item)
    
    def add_project_tab(self, name="New Project"):
        """Add a new project tab with all necessary widgets"""
        
        # Create a unique color for this project based on its name
        # We'll use this same color for both the tab and the floating timer
        hash_object = hashlib.md5(name.encode())
        hash_hex = hash_object.hexdigest()
        
        # Generate colors that are vivid enough - avoid too dark or too light
        r = int(hash_hex[0:2], 16) % 156 + 100  # Range 100-255
        g = int(hash_hex[2:4], 16) % 156 + 100
        b = int(hash_hex[4:6], 16) % 156 + 100
        project_color = QColor(r, g, b)

        # Create main widget for this tab
        project_widget = QWidget()
        project_layout = QVBoxLayout(project_widget)
        project_layout.setContentsMargins(5, 5, 5, 5)

        # Create horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Selection panel
        selection_widget = QWidget()
        selection_layout = QVBoxLayout(selection_widget)
        
        # Origin selection
        origin_group = QGroupBox("Origin Selection")
        origin_layout = QVBoxLayout()
        
        self.origin_list = QListWidget()
        # Add context menu support for origin list
        self.origin_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.origin_list.customContextMenuRequested.connect(self.show_origin_context_menu)
        origin_layout.addWidget(self.origin_list)
        
        origin_buttons = QHBoxLayout()
        self.browse_origin_btn = QPushButton("Add File")
        self.browse_origin_btn.clicked.connect(self.browse_origin)
        origin_buttons.addWidget(self.browse_origin_btn)
        
        self.browse_origin_dir_btn = QPushButton("Add Folder")
        self.browse_origin_dir_btn.clicked.connect(lambda: self.browse_origin(True))
        origin_buttons.addWidget(self.browse_origin_dir_btn)
        
        self.clear_origin_btn = QPushButton("Clear All")
        self.clear_origin_btn.clicked.connect(self.clear_origin)
        origin_buttons.addWidget(self.clear_origin_btn)
        
        origin_layout.addLayout(origin_buttons)
        
        self.open_origin_btn = QPushButton("Open Origin Location")
        self.open_origin_btn.clicked.connect(self.open_origin_folder)
        self.open_origin_btn.setEnabled(False)
        origin_layout.addWidget(self.open_origin_btn)
        
        origin_group.setLayout(origin_layout)
        selection_layout.addWidget(origin_group)
        
        # Destination selection
        dest_group = QGroupBox("Destination Folder")
        dest_layout = QVBoxLayout()
        
        self.dest_label = QLabel("No destination selected")
        dest_layout.addWidget(self.dest_label)
        
        dest_buttons = QHBoxLayout()
        self.browse_dest_btn = QPushButton("Browse")
        self.browse_dest_btn.clicked.connect(self.browse_destination)
        dest_buttons.addWidget(self.browse_dest_btn)
        
        self.clear_dest_btn = QPushButton("Clear")
        self.clear_dest_btn.clicked.connect(self.clear_destination)
        dest_buttons.addWidget(self.clear_dest_btn)
        
        dest_layout.addLayout(dest_buttons)
        
        self.open_dest_btn = QPushButton("Open Destination")
        self.open_dest_btn.clicked.connect(self.open_dest_folder)
        self.open_dest_btn.setEnabled(False)
        dest_layout.addWidget(self.open_dest_btn)
        
        dest_group.setLayout(dest_layout)
        selection_layout.addWidget(dest_group)
        
        # Create version button
        self.create_version_btn = QPushButton("Create Version")
        self.create_version_btn.setMinimumHeight(50)
        self.create_version_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.create_version_btn.clicked.connect(self.create_version)
        self.create_version_btn.setEnabled(False)
        selection_layout.addWidget(self.create_version_btn)
        
        # Buy me a coffee button
        bmc_layout = QHBoxLayout()
        
        # Create a container widget for the GIF
        bmc_container = QWidget()
        bmc_container.setFixedHeight(50)
        bmc_container.setMinimumWidth(170)
        bmc_container_layout = QHBoxLayout(bmc_container)
        bmc_container_layout.setContentsMargins(0, 0, 0, 0)
        bmc_container_layout.setSpacing(0)
        
        # Try multiple paths for the BMC button GIF
        bmc_gif_path = resource_path(os.path.join("resources", "bmc_button.gif"))
        alt_bmc_gif_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "bmc_button.gif")
        
        # Try resource path first, then direct file path
        if os.path.exists(bmc_gif_path):
            print(f"Using resource path for BMC button: {bmc_gif_path}")
            gif_path = bmc_gif_path
        elif os.path.exists(alt_bmc_gif_path):
            print(f"Using direct path for BMC button: {alt_bmc_gif_path}")
            gif_path = alt_bmc_gif_path
        else:
            print("BMC button GIF not found")
            gif_path = None
        
        if gif_path:
            self.bmc_gif_label = QLabel()
            self.bmc_movie = QMovie(gif_path)
            
            # Keep original aspect ratio without distortion
            original_size = self.bmc_movie.currentImage().size()
            self.bmc_gif_label.setFixedHeight(50)
            self.bmc_gif_label.setMinimumWidth(170)
            self.bmc_gif_label.setScaledContents(False)
            self.bmc_gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.bmc_gif_label.setMovie(self.bmc_movie)
            self.bmc_movie.start()
            
            # Style just the label
            self.bmc_gif_label.setStyleSheet("background-color: transparent;")
            bmc_container_layout.addWidget(self.bmc_gif_label, 0, Qt.AlignmentFlag.AlignCenter)
            
            # Make the container clickable
            self.bmc_gif_label.mousePressEvent = lambda event: self.show_bmc()
            self.bmc_gif_label.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            # Fallback to a text button if GIF is not found
            bmc_text_btn = QPushButton("Buy Me a Coffee")
            bmc_text_btn.setFixedHeight(50)
            bmc_text_btn.setMinimumWidth(170)
            bmc_text_btn.clicked.connect(self.show_bmc)
            bmc_text_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            bmc_container_layout.addWidget(bmc_text_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        bmc_layout.addWidget(bmc_container)
        
        self.save_project_btn = QPushButton("Save Current Settings")
        self.save_project_btn.setMinimumHeight(50)  # Match height with BMC button
        self.save_project_btn.clicked.connect(self.save_recent_projects)
        bmc_layout.addWidget(self.save_project_btn)
        
        selection_layout.addLayout(bmc_layout)
        
        # Right side - Content and settings
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Create tab control layout
        tab_control_layout = QHBoxLayout()
        
        # Start/Stop button for auto-create
        self.start_stop_btn = QToolButton()
        self.start_stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_stop_btn.setIconSize(QSize(16, 16))
        self.start_stop_btn.setToolTip("Start Auto-Create")
        self.start_stop_btn.clicked.connect(self.toggle_auto_create)
        tab_control_layout.addWidget(self.start_stop_btn)
        
        # Countdown indicator
        self.countdown_label = QLabel("--:--:--")
        self.countdown_label.setFont(QFont("Arial", 9))
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setMinimumWidth(80)
        tab_control_layout.addWidget(self.countdown_label)
        
        tab_control_layout.addStretch()
        content_layout.addLayout(tab_control_layout)
        
        # Create tab widget for contents, settings, and recents
        self.tab_widget = QTabWidget()
        
        # Add Contents tab
        contents_scroll = QScrollArea()
        contents_scroll.setWidgetResizable(True)
        contents_widget = QWidget()
        contents_layout = QVBoxLayout(contents_widget)
        
        self.contents_list = QListWidget()
        # Set up icons for the contents list
        folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        file_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        self.contents_list.setIconSize(QSize(16, 16))
        # Add double-click and context menu support
        self.contents_list.itemDoubleClicked.connect(self.open_content_item)
        self.contents_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.contents_list.customContextMenuRequested.connect(self.show_contents_context_menu)
        contents_layout.addWidget(self.contents_list)
        
        contents_scroll.setWidget(contents_widget)
        self.tab_widget.addTab(contents_scroll, "Contents")
        
        # Add Settings tab
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # Project Color settings
        color_group = QGroupBox("Project Color")
        color_layout = QHBoxLayout()
        
        color_label = QLabel("Tab and Timer Color:")
        color_layout.addWidget(color_label)
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 20)
        self.color_preview.setStyleSheet(f"background-color: rgb({project_color.red()}, {project_color.green()}, {project_color.blue()}); border: 1px solid #888888;")
        color_layout.addWidget(self.color_preview)
        
        self.color_picker_btn = QPushButton("Choose Color")
        self.color_picker_btn.clicked.connect(self.choose_project_color)
        color_layout.addWidget(self.color_picker_btn)
        
        color_layout.addStretch()
        color_group.setLayout(color_layout)
        settings_layout.addWidget(color_group)
        
        # Naming settings
        naming_group = QGroupBox("Version Naming")
        naming_layout = QVBoxLayout()
        
        # Prefix and suffix
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Prefix:"))
        self.prefix_edit = QLineEdit()
        prefix_layout.addWidget(self.prefix_edit)
        naming_layout.addLayout(prefix_layout)
        
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("Suffix:"))
        self.suffix_edit = QLineEdit()
        suffix_layout.addWidget(self.suffix_edit)
        naming_layout.addLayout(suffix_layout)
        
        # Format options
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.name_format_combo = QComboBox()
        self.name_format_combo.addItems([
            "Date and Time (YYYY-MM-DD_HH-MM-SS)", 
            "Date Only (YYYY-MM-DD)", 
            "Version Number (v001, v002, ...)",
            "Custom Format"
        ])
        self.name_format_combo.currentIndexChanged.connect(self.update_name_format)
        format_layout.addWidget(self.name_format_combo)
        naming_layout.addLayout(format_layout)
        
        # Custom format input
        custom_format_layout = QHBoxLayout()
        custom_format_layout.addWidget(QLabel("Custom:"))
        self.custom_format_edit = QLineEdit()
        self.custom_format_edit.setPlaceholderText("%Y-%m-%d_%H-%M-%S")
        self.custom_format_edit.setEnabled(False)
        custom_format_layout.addWidget(self.custom_format_edit)
        naming_layout.addLayout(custom_format_layout)
        
        naming_group.setLayout(naming_layout)
        settings_layout.addWidget(naming_group)
        
        # Auto-delete settings
        auto_delete_group = QGroupBox("Auto-Delete Old Versions")
        auto_delete_layout = QVBoxLayout()
        
        self.auto_delete_check = QCheckBox("Automatically delete older versions")
        self.auto_delete_check.stateChanged.connect(self.toggle_version_limit)
        auto_delete_layout.addWidget(self.auto_delete_check)
        
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Keep only the most recent:"))
        self.version_limit_spin = QSpinBox()
        self.version_limit_spin.setRange(1, 1000)
        self.version_limit_spin.setValue(10)
        self.version_limit_spin.setEnabled(False)
        limit_layout.addWidget(self.version_limit_spin)
        limit_layout.addWidget(QLabel("versions"))
        auto_delete_layout.addLayout(limit_layout)
        
        auto_delete_group.setLayout(auto_delete_layout)
        settings_layout.addWidget(auto_delete_group)
        
        # Auto-create settings
        auto_create_group = QGroupBox("Auto-Create Versions")
        auto_create_layout = QVBoxLayout()
        
        self.auto_create_check = QCheckBox("Automatically create versions at regular intervals")
        self.auto_create_check.stateChanged.connect(self.toggle_auto_create_settings)
        auto_create_layout.addWidget(self.auto_create_check)
        
        # Interval layout
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Create every:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1000)
        self.interval_spin.setValue(10)
        self.interval_spin.setEnabled(False)
        self.interval_spin.valueChanged.connect(self.interval_changed)
        interval_layout.addWidget(self.interval_spin)
        
        self.interval_unit = QComboBox()
        self.interval_unit.addItems(["Minutes", "Hours"])
        self.interval_unit.setEnabled(False)
        self.interval_unit.currentIndexChanged.connect(self.interval_changed)
        interval_layout.addWidget(self.interval_unit)
        auto_create_layout.addLayout(interval_layout)
        
        # Additional options
        self.create_on_start_check = QCheckBox("Create version on Start Button click")
        self.create_on_start_check.setEnabled(False)
        auto_create_layout.addWidget(self.create_on_start_check)
        
        self.auto_create_on_load_check = QCheckBox("Create version when loading project")
        self.auto_create_on_load_check.setEnabled(False)
        auto_create_layout.addWidget(self.auto_create_on_load_check)
        
        # Floating timer layout
        timer_layout = QVBoxLayout()
        self.show_floating_timer_check = QCheckBox("Show floating countdown timer")
        self.show_floating_timer_check.stateChanged.connect(self.toggle_floating_timer_setting)
        self.show_floating_timer_check.setEnabled(False)
        timer_layout.addWidget(self.show_floating_timer_check)
        
        # Opacity slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Timer Opacity:"))
        self.timer_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.timer_opacity_slider.setRange(20, 100)
        self.timer_opacity_slider.setValue(100)
        self.timer_opacity_slider.setEnabled(False)
        self.timer_opacity_slider.valueChanged.connect(self.update_timer_opacity)
        opacity_layout.addWidget(self.timer_opacity_slider)
        timer_layout.addLayout(opacity_layout)
        
        auto_create_layout.addLayout(timer_layout)
        
        auto_create_group.setLayout(auto_create_layout)
        settings_layout.addWidget(auto_create_group)
        
        settings_scroll.setWidget(settings_widget)
        self.tab_widget.addTab(settings_scroll, "Settings")
        
        # Add Recent Projects tab
        recents_scroll = QScrollArea()
        recents_scroll.setWidgetResizable(True)
        recents_widget = QWidget()
        recents_layout = QVBoxLayout(recents_widget)
        
        self.recent_projects_list = QListWidget()
        self.recent_projects_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recent_projects_list.customContextMenuRequested.connect(self.show_recent_context_menu)
        self.recent_projects_list.itemDoubleClicked.connect(self.load_selected_project)
        recents_layout.addWidget(self.recent_projects_list)
        
        recents_scroll.setWidget(recents_widget)
        self.tab_widget.addTab(recents_scroll, "Recent Projects")
        
        content_layout.addWidget(self.tab_widget)
        
        # Add selection and content widgets to the splitter
        splitter.addWidget(selection_widget)
        splitter.addWidget(content_widget)
        
        # Set the initial sizes for the splitter (30% / 70%)
        splitter.setSizes([300, 700])
        
        # Add the splitter to the main project layout
        project_layout.addWidget(splitter)
        
        # Create a dictionary to store the project data
        project_data = {
            'name': name,
            'widget': project_widget,
            'origin_paths': [],  # Initialize with empty list
            'destination_path': "",  # Initialize with empty string
            # Per-project timer state
            'auto_create_running': False,  # Not running initially, user must click start
            'countdown_seconds': 0,
            'countdown_timer': None,
            'auto_create_timer': None,
            'floating_timer': None,
            'project_color': project_color,  # Store the project color
            'controls': {
                'origin_list': self.origin_list,
                'dest_label': self.dest_label,
                'create_version_btn': self.create_version_btn,
                'open_origin_btn': self.open_origin_btn,
                'open_dest_btn': self.open_dest_btn,
                'prefix_edit': self.prefix_edit,
                'suffix_edit': self.suffix_edit,
                'name_format_combo': self.name_format_combo,
                'custom_format_edit': self.custom_format_edit,
                'auto_delete_check': self.auto_delete_check,
                'version_limit_spin': self.version_limit_spin,
                'auto_create_check': self.auto_create_check,
                'interval_spin': self.interval_spin,
                'interval_unit': self.interval_unit,
                'create_on_start_check': self.create_on_start_check,
                'auto_create_on_load_check': self.auto_create_on_load_check,
                'show_floating_timer_check': self.show_floating_timer_check,
                'timer_opacity_slider': self.timer_opacity_slider,
                'countdown_label': self.countdown_label,
                'start_stop_btn': self.start_stop_btn,
                'contents_list': self.contents_list,
                'tab_widget': self.tab_widget,
                'recent_projects_list': self.recent_projects_list,
                'color_preview': self.color_preview,
                'color_picker_btn': self.color_picker_btn
            }
        }
        
        # Store the project data
        self.project_tabs.append(project_data)
        
        # Save the current project state before switching if we have one
        if hasattr(self, 'current_project_index') and self.current_project_index >= 0:
            self.save_current_project_state()
            
        # Reset app state for the new tab
        self.origin_paths = []
        self.destination_path = ""
        # Reset all timer-related state
        self.auto_create_running = False
        self.countdown_seconds = 0
        self.countdown_timer = None
        self.auto_create_timer = None
        self.floating_timer = None
        
        # Update UI to reflect the fresh state
        self.update_origin_list()
        self.update_button_states()
        self.contents_list.clear()
        
        # Reset all UI control values
        self.prefix_edit.clear()
        self.suffix_edit.clear()
        self.name_format_combo.setCurrentIndex(0)
        self.custom_format_edit.clear()
        self.auto_delete_check.setChecked(False)
        self.version_limit_spin.setValue(5)
        
        # Enable auto-create features by default for all new projects
        self.auto_create_check.setChecked(True)
        self.interval_spin.setValue(5)
        self.interval_unit.setCurrentIndex(0)
        self.create_on_start_check.setChecked(True)
        self.auto_create_on_load_check.setChecked(True)
        self.show_floating_timer_check.setChecked(True)
        self.timer_opacity_slider.setValue(100)
        self.countdown_label.setText("--:--:--")
        self.start_stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_stop_btn.setToolTip("Start Auto-Create")
        
        # Call the toggle functions to update dependent controls
        self.toggle_auto_create_settings(Qt.CheckState.Checked.value)
        self.toggle_floating_timer_setting(Qt.CheckState.Checked.value)
        
        # Add the tab to the tab widget - insert before the + tab
        tab_index = self.project_tabs_widget.count() - 1  # Position before the + tab
        self.project_tabs_widget.insertTab(tab_index, project_widget, name)
        
        # Set the tab color
        self.project_tabs_widget.setTabColor(tab_index, project_color)
        
        # Update the color preview
        self.color_preview.setStyleSheet(f"background-color: rgb({project_color.red()}, {project_color.green()}, {project_color.blue()}); border: 1px solid #888888;")
        
        # Switch to the new tab
        self.project_tabs_widget.setCurrentIndex(tab_index)
        
        # Set the current project index
        self.current_project_index = tab_index
        
        # Debug info
        print(f"Created new project tab: {name} (index {tab_index})")
        print(f"Current origin paths: {self.origin_paths}")
        print(f"Current destination path: {self.destination_path}")
        
        # Notify
        self.show_toast(f"Created new project tab: {name}", 2000)
        
        # Set auto-create to enabled but not running
        # User must click the start button to begin the countdown
        self.auto_create_running = False  # Don't automatically start
        
        # Create a floating timer for this project by default
        # This ensures the timer is visible regardless of active tab
        timer = self.create_floating_timer(tab_index)
        
        # Make sure the timer is visible immediately
        if timer:
            timer.show()
        
        # Return the index of the new tab
        return tab_index
    
    def switch_project(self, index):
        """Switch to a different project tab"""
        # Don't do anything if the index is invalid
        if index < 0 or index >= len(self.project_tabs):
            return
            
        # Don't do anything if this is the + tab (the last tab)
        if index == self.project_tabs_widget.count() - 1:
            return
            
        # Save current project state if we're switching from a valid project
        if self.current_project_index >= 0 and self.current_project_index < len(self.project_tabs):
            self.save_current_project_state()
            
        # Update current project index
        self.current_project_index = index
        
        # Load the selected project state
        self.load_project_state(index)
        
        # Debug info
        print(f"Switched to project tab {index}")
        print(f"Current origin paths: {self.origin_paths}")
        print(f"Current destination path: {self.destination_path}")
    
    def save_current_project_state(self):
        """Save the current state of the active project"""
        if self.current_project_index < 0 or self.current_project_index >= len(self.project_tabs):
            return
            
        project = self.project_tabs[self.current_project_index]
        
        # Update project data with current state
        project['origin_paths'] = self.origin_paths.copy()
        project['destination_path'] = self.destination_path
        
        # Save timer state - keep timers running
        project['auto_create_running'] = self.auto_create_running
        project['countdown_seconds'] = self.countdown_seconds
        
        # Store references to timer objects but DO NOT stop them
        # This allows timers to continue running even when switching tabs
        project['countdown_timer'] = self.countdown_timer
        project['auto_create_timer'] = self.auto_create_timer
        project['floating_timer'] = self.floating_timer
        
        # Debug info
        print(f"Saved project state for tab #{self.current_project_index + 1}")
        print(f"Saved origin paths: {project['origin_paths']}")
        print(f"Saved destination path: {project['destination_path']}")
        print(f"Auto create running: {project['auto_create_running']}")
    
    def load_project_state(self, index):
        """Load the state of the selected project"""
        print(f"LOAD_STATE: Loading project state for index {index}")
        if index < 0 or index >= len(self.project_tabs):
            print(f"LOAD_STATE: Invalid index {index}, not loading")
            return
        
        # Make sure all existing timers remain visible
        print("LOAD_STATE: Ensuring all existing timers are visible")
        for i, project in enumerate(self.project_tabs):
            floating_timer = project.get('floating_timer')
            if floating_timer and not floating_timer.isVisible():
                print(f"LOAD_STATE: Making timer visible for project {i}")
                floating_timer.show()
        
        print(f"LOAD_STATE: Getting project at index {index}")
        project = self.project_tabs[index]
        
        # Update app state
        print("LOAD_STATE: Updating application state with project data")
        self.origin_paths = project.get('origin_paths', []).copy()
        self.destination_path = project.get('destination_path', "")
        
        # Restore timer state
        print("LOAD_STATE: Restoring timer state")
        self.auto_create_running = project.get('auto_create_running', False)
        self.countdown_seconds = project.get('countdown_seconds', 0)
        
        # Restore timer objects for this specific project
        self.countdown_timer = project.get('countdown_timer', None)
        self.auto_create_timer = project.get('auto_create_timer', None)
        
        # Get the floating timer for this project
        print("LOAD_STATE: Getting floating timer for the project")
        project_timer = project.get('floating_timer', None)
        
        if not project_timer:
            # If no timer exists for this project yet, create one now
            print("LOAD_STATE: No timer exists, creating a new one")
            self.floating_timer = self.create_floating_timer(index)
        else:
            # Use the existing timer for this project
            print("LOAD_STATE: Using existing timer")
            self.floating_timer = project_timer
            
            # Always ensure timer is visible and updated
            print("LOAD_STATE: Ensuring timer is visible and updated")
            self.floating_timer.show()
            if self.countdown_seconds > 0:
                print(f"LOAD_STATE: Updating timer with countdown: {self.countdown_seconds}")
                self.floating_timer.update_time(self.countdown_seconds)
            else:
                print("LOAD_STATE: Resetting timer to zeros")
                self.floating_timer.update_time(0)  # Show zeros if not counting down
        
        # Update UI controls
        print("LOAD_STATE: Updating UI controls")
        self.update_origin_list()
        self.update_contents_list()
        
        if self.origin_paths:
            print(f"LOAD_STATE: Loaded origin paths: {len(self.origin_paths)} items")
        else:
            print("LOAD_STATE: No origin paths loaded")
            
        print(f"LOAD_STATE: Loaded destination: {self.destination_path}")
        print(f"LOAD_STATE: Auto-create running: {self.auto_create_running}")
        print(f"LOAD_STATE: Has floating timer: {self.floating_timer is not None}")
        
        # Ensure all timers are visible and in front
        print("LOAD_STATE: Ensuring all timers are visible and in front")
        for timer in self.all_floating_timers:
            if timer and not timer.isVisible():
                print(f"LOAD_STATE: Making hidden timer visible")
                timer.show()
            elif timer and timer.isVisible():
                print(f"LOAD_STATE: Raising timer to front")
                timer.raise_()
        
        # Reposition all timers to make sure they stack properly
        print("LOAD_STATE: Repositioning all timers")
        self.reposition_all_timers()
        
        print("LOAD_STATE: Loading project state completed")
    
    def browse_origin(self, folder=False):
        """Browse for origin file or folder"""
        # Show warning if auto-create is running
        if self.auto_create_running:
            confirm = QMessageBox.question(
                self,
                "Warning - Auto-Create Running",
                "Auto-create is currently running. Changing origin files during auto-creation may cause issues.\n\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
        
        if folder:
            folder = QFileDialog.getExistingDirectory(self, "Select Origin Folder")
            if folder:
                # Add to list if not already there
                if folder not in self.origin_paths:
                    self.origin_paths.append(folder)
                    # Update UI immediately
                    self.update_origin_list()
                    self.update_button_states()
                    self.update_contents_list()
                    # Show confirmation
                    self.show_toast(f"Added folder: {folder}", 2000)
        else:
            files, _ = QFileDialog.getOpenFileNames(self, "Select Origin Files")
            if files:
                # Add files that aren't already in the list
                added = False
                for file in files:
                    if file not in self.origin_paths:
                        self.origin_paths.append(file)
                        added = True
                
                if added:
                    # Update UI immediately
                    self.update_origin_list()
                    self.update_button_states()
                    self.update_contents_list()
                    # Show confirmation
                    self.show_toast(f"Added {len(files)} file(s)", 2000)
        
        # Debug output
        print(f"Current origin_paths: {self.origin_paths}")
    
    def clear_origin(self):
        """Clear the origin paths"""
        if len(self.origin_paths) > 0:
            # Add confirmation check if auto-create is running
            if self.auto_create_running:
                confirm = QMessageBox.question(
                    self,
                    "Warning - Auto-Create Running",
                    "Auto-create is currently running. Clearing the origin selection may cause issues.\n\nDo you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return
                    
            self.origin_paths = []
            self.update_origin_list()
            self.update_button_states()
            self.update_contents_list()
            # Show toast notification for clearing origin
            self.show_toast("Origin items cleared")
            
            # Stop auto-create if it's running since we have no origin anymore
            if self.auto_create_running:
                self.stop_auto_create()
                self.show_toast("Auto-create stopped - no origin files selected", 3000)
    
    def browse_destination(self):
        """Browse for destination folder"""
        # Show warning if auto-create is running
        if self.auto_create_running:
            confirm = QMessageBox.question(
                self,
                "Warning - Auto-Create Running",
                "Auto-create is currently running. Changing the destination folder during auto-creation may cause issues.\n\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
                
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.destination_path = folder
            self.dest_label.setText(folder)
            self.update_button_states()
            self.update_contents_list()
            
            # Debug information
            self.show_toast(f"Destination set to: {folder}", 2000)
    
    def clear_destination(self):
        """Clear the destination path"""
        if self.destination_path:
            # Add confirmation check if auto-create is running
            if self.auto_create_running:
                confirm = QMessageBox.question(
                    self,
                    "Warning - Auto-Create Running",
                    "Auto-create is currently running. Clearing the destination folder will stop auto-create.\n\nDo you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return
                    
            self.destination_path = ""
            self.dest_label.setText("No destination selected")
            self.update_button_states()
            self.contents_list.clear()
            # Show toast notification for clearing destination
            self.show_toast("Destination folder cleared")
            
            # Stop auto-create if it's running since we have no destination anymore
            if self.auto_create_running:
                self.stop_auto_create()
                self.show_toast("Auto-create stopped - no destination folder selected", 3000)
    
        else:
            # We already have origin and destination, just need auto-create checkbox
            if self.auto_create_check.isChecked():
                # Check if we should create a version when starting auto-create
                if self.create_on_start_check.isChecked():
                    self.create_version()
                self.start_auto_create()
            else:
                # Enable auto-create and start
                self.auto_create_check.setChecked(True)
                # The check will trigger toggle_auto_create_settings, which will enable necessary controls
                if self.create_on_start_check.isChecked():
                    self.create_version()
                self.start_auto_create()
    
    def start_auto_create(self):
        """Start the auto-create functionality"""
        if self.current_project_index < 0 or self.current_project_index >= len(self.project_tabs):
            return
            
        if self.auto_create_check.isChecked() and len(self.origin_paths) > 0 and self.destination_path:
            # Start the timer for this project
            self.start_timer(self.current_project_index)
            
            # If floating timer is enabled, show it for this project
            if self.show_floating_timer_check.isChecked():
                self.create_floating_timer(self.current_project_index)
        else:
            self.show_toast("Cannot start auto-create: Please select origin and destination folders, and enable auto-create in settings.", 5000)
    
    def stop_auto_create(self):
        """Stop the auto-create functionality"""
        if self.current_project_index < 0 or self.current_project_index >= len(self.project_tabs):
            return
            
        # Stop the timer for the current project
        self.stop_timer(self.current_project_index)
    
    def update_countdown(self):
        """Update the countdown display"""
        if self.countdown_seconds > 0:
            self.countdown_seconds -= 1
            
            # Update the in-app countdown label
            hours, remainder = divmod(self.countdown_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.countdown_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update floating timer if active
            if self.floating_timer and self.floating_timer.isVisible():
                self.floating_timer.update_time(self.countdown_seconds)
        else:
            # When countdown reaches zero, restart it
            self.restart_countdown()
    
    def restart_countdown(self):
        """Restart the countdown timer with the current interval"""
        interval_value = self.interval_spin.value()
        unit = self.interval_unit.currentText()
        
        if unit == "Minutes":
            self.countdown_seconds = interval_value * 60
        else:  # Hours
            self.countdown_seconds = interval_value * 60 * 60
    
    def interval_changed(self):
        """Handle changes to interval settings"""
        # If auto-create is running, restart the timers with new interval
        if self.current_project_index >= 0:
            project = self.project_tabs[self.current_project_index]
            if project.get('auto_create_running', False):
                self.start_auto_create_timer(self.current_project_index)
    
    def load_project(self, project):
        """Load a project's settings"""
        # Load settings
        self.origin_paths = project['origin_paths']
        self.destination_path = project['destination_path']
        self.prefix_edit.setText(project['prefix'])
        self.suffix_edit.setText(project['suffix'])
        self.name_format_combo.setCurrentIndex(project['format_index'])
        self.custom_format_edit.setText(project['custom_format'])
        
        # Update UI
        self.update_origin_list()
        self.dest_label.setText(self.destination_path)
        self.update_button_states()
        self.update_contents_list()
        
        # Load auto-delete settings
        auto_delete = project.get('auto_delete', False)
        self.auto_delete_check.setChecked(auto_delete)
        self.version_limit_spin.setValue(project.get('version_limit', 5))
        # Force update of dependent controls
        self.toggle_version_limit(Qt.CheckState.Checked.value if auto_delete else Qt.CheckState.Unchecked.value)
        
        # Load auto-create settings if available
        auto_create = project.get('auto_create', False)
        if 'auto_create' in project:
            self.auto_create_check.setChecked(auto_create)
            self.interval_spin.setValue(project.get('interval_value', 5))
            self.interval_unit.setCurrentIndex(project.get('interval_unit', 0))
            
            # Force update of dependent controls
            self.toggle_auto_create_settings(Qt.CheckState.Checked.value if auto_create else Qt.CheckState.Unchecked.value)
        
        # Get auto-start settings
        create_on_start = project.get('create_on_start', False)
        auto_create_on_load = project.get('auto_create_on_load', False)
        show_floating_timer = project.get('show_floating_timer', False)
        timer_opacity = project.get('timer_opacity', 95)
        
        # Update checkboxes and slider
        self.create_on_start_check.setChecked(create_on_start)
        self.auto_create_on_load_check.setChecked(auto_create_on_load)
        self.show_floating_timer_check.setChecked(show_floating_timer)
        self.timer_opacity_slider.setValue(timer_opacity)
        
        # Force update of timer controls
        self.toggle_floating_timer_setting(Qt.CheckState.Checked.value if show_floating_timer else Qt.CheckState.Unchecked.value)
        
        # Apply create on start
        if create_on_start:
            self.create_version()
        
        # Apply auto-create on load - NOW we start if the setting is enabled
        if auto_create_on_load and auto_create and self.current_project_index >= 0:
            self.start_timer(self.current_project_index)
        
        # Debug information
        self.show_toast(f"Project loaded successfully", 2000)
    
    def load_selected_project(self, item):
        """Load the selected project from the recent list"""
        selected_row = self.recent_projects_list.currentRow()
        if selected_row >= 0 and selected_row < len(self.recent_projects):
            project = self.recent_projects[selected_row]
            # Use the load_project method which now properly handles all settings
            self.load_project(project)
    
    def create_version(self):
        # Check if auto-creation is currently in progress (in the middle of copying files)
        if hasattr(self, 'is_creating_version') and self.is_creating_version:
            QMessageBox.warning(
                self,
                "Auto-Create In Progress",
                "An automatic version is currently being created. Please wait for it to complete.",
                QMessageBox.StandardButton.Ok
            )
            return
            
        # Generate version folder name
        version_name = self.generate_version_name()
        version_path = os.path.join(self.destination_path, version_name)
        
        # Create the version folder
        try:
            os.makedirs(version_path, exist_ok=True)
            
            # Copy files/folders
            for source_path in self.origin_paths:
                if os.path.isdir(source_path):
                    # Copy directory contents
                    source_basename = os.path.basename(source_path)
                    dest_dir = os.path.join(version_path, source_basename)
                    shutil.copytree(source_path, dest_dir)
                else:
                    # Copy file
                    shutil.copy2(source_path, version_path)
            
            # Track if any versions were deleted
            deleted_count = 0
            
            # Cleanup old versions if needed
            if self.auto_delete_check.isChecked():
                deleted_count = self.cleanup_old_versions()
            
            # Update the contents view
            self.update_contents_list()
            
            # Always save current project to recents after creating a version
            self.save_recent_projects()
            
            # Reset the timer if auto-create is running for the current project
            timer_was_reset = False
            if self.current_project_index >= 0:
                project = self.project_tabs[self.current_project_index]
                if project.get('auto_create_running', False):
                    # Get interval value from the current project
                    interval_value = self.interval_spin.value()
                    unit = self.interval_unit.currentText()
                    
                    # Update countdown
                    if unit == "Minutes":
                        project['countdown_seconds'] = interval_value * 60
                    else:  # Hours
                        project['countdown_seconds'] = interval_value * 60 * 60
                        
                    # Update the countdown display
                    if 'controls' in project:
                        countdown_label = project['controls'].get('countdown_label')
                        if countdown_label:
                            hours, remainder = divmod(project['countdown_seconds'], 3600)
                            minutes, seconds = divmod(remainder, 60)
                            countdown_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                            
                    # Update floating timer if present
                    floating_timer = project.get('floating_timer')
                    if floating_timer:
                        floating_timer.update_time(project['countdown_seconds'])
                        
                    timer_was_reset = True
            
            # Show success message as toast instead of alert
            if deleted_count > 0:
                success_message = f"Version created successfully at: {version_name}\n{deleted_count} old version(s) removed"
                if timer_was_reset:
                    success_message += "\nAuto-create timer has been reset"
                self.show_toast(success_message, 5000)
            else:
                success_message = f"Version created successfully at: {version_name}"
                if timer_was_reset:
                    success_message += "\nAuto-create timer has been reset"
                self.show_toast(success_message, 3000)
                
        except Exception as e:
            error_message = f"Error creating version: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
    
    def generate_version_name(self):
        # Get current date and time
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")
        
        prefix = self.prefix_edit.text()
        suffix = self.suffix_edit.text()
        
        format_index = self.name_format_combo.currentIndex()
        
        if format_index == 0:  # Date_Time
            name = f"{date_str}_{time_str}"
        elif format_index == 1:  # Custom
            custom_format = self.custom_format_edit.text()
            name = custom_format.replace("{date}", date_str).replace("{time}", time_str)
        else:  # Counter
            # Find existing counter-based folders and increment
            counter = 1
            existing_folders = [f for f in os.listdir(self.destination_path) 
                               if os.path.isdir(os.path.join(self.destination_path, f))]
            
            while f"version_{counter:03d}" in existing_folders:
                counter += 1
            
            name = f"version_{counter:03d}"
        
        # Add prefix and suffix
        if prefix:
            name = f"{prefix}_{name}"
        if suffix:
            name = f"{name}_{suffix}"
            
        return name
    
    def cleanup_old_versions(self):
        limit = self.version_limit_spin.value()
        deleted_count = 0
        
        # Get all folders in the destination directory
        folders = [os.path.join(self.destination_path, f) 
                  for f in os.listdir(self.destination_path) 
                  if os.path.isdir(os.path.join(self.destination_path, f))]
        
        # Sort folders by creation time (newest first)
        folders.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        # Remove old folders
        if len(folders) > limit:
            for folder in folders[limit:]:
                try:
                    shutil.rmtree(folder)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error removing folder {folder}: {str(e)}")
        
        return deleted_count
    
    def update_name_format(self, index):
        self.custom_format_edit.setEnabled(index == 1)  # Enable for "Custom" option
    
    def show_recent_context_menu(self, position):
        if self.recent_projects_list.count() == 0:
            return
            
        menu = QMenu()
        remove_action = menu.addAction("Remove from List")
        action = menu.exec(self.recent_projects_list.mapToGlobal(position))
        
        if action == remove_action:
            selected_row = self.recent_projects_list.currentRow()
            if selected_row >= 0:
                # Remove from data
                del self.recent_projects[selected_row]
                
                # Save to file
                with open(self.projects_file, 'w') as f:
                    json.dump(self.recent_projects, f)
                
                # Update UI
                self.update_recent_projects_list()
    
    def update_recent_projects_list(self):
        self.recent_projects_list.clear()
        for project in self.recent_projects:
            # Display a summary of the project
            origins = ", ".join([os.path.basename(p) for p in project['origin_paths']])
            dest = os.path.basename(project['destination_path'])
            timestamp = project.get('timestamp', 'Unknown date')
            
            item_text = f"{timestamp} - {origins} → {dest}"
            self.recent_projects_list.addItem(item_text)
    
    def show_bmc(self):
        bmc_dialog = QMessageBox(self)
        bmc_dialog.setWindowTitle("Buy Me a Coffee")
        
        # Load the QR code image
        qr_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bmc_qr.png")
        if os.path.exists(qr_path):
            qr_pixmap = QPixmap(qr_path)
            qr_pixmap = qr_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            bmc_dialog.setIconPixmap(qr_pixmap)
        
        bmc_dialog.setText("If you find this tool helpful, please consider supporting me:")
        bmc_dialog.setInformativeText("<a href='https://buymeacoffee.com/L5ff3Ti0zc'>Buy Me a Coffee</a>")
        bmc_dialog.setTextFormat(Qt.TextFormat.RichText)
        
        # Add a direct link button
        open_link_button = bmc_dialog.addButton("Open in Browser", QMessageBox.ButtonRole.ActionRole)
        close_button = bmc_dialog.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        
        result = bmc_dialog.exec()
        
        if bmc_dialog.clickedButton() == open_link_button:
            webbrowser.open("https://buymeacoffee.com/L5ff3Ti0zc")

    def start_auto_create_timer(self, project_index=None):
        """Start the timer for a specific project (or current project if index not provided)"""
        # Use current project if no specific index provided
        if project_index is None:
            project_index = self.current_project_index
            
        # Validate project index
        if project_index < 0 or project_index >= len(self.project_tabs):
            return
            
        # Get the project data
        project = self.project_tabs[project_index]
        controls = project.get('controls', {})
        
        # Calculate interval
        interval_spin = controls.get('interval_spin')
        interval_unit = controls.get('interval_unit')
        
        if not interval_spin or not interval_unit:
            return
            
        interval_value = interval_spin.value()
        unit = interval_unit.currentText()
        
        # Calculate milliseconds for timer
        if unit == "Minutes":
            ms = interval_value * 60 * 1000
        else:  # Hours
            ms = interval_value * 60 * 60 * 1000
            
        # Set up countdown seconds
        project['countdown_seconds'] = interval_value * 60 if unit == "Minutes" else interval_value * 60 * 60
        
        # Stop existing timer if any
        timer = project.get('auto_create_timer')
        if timer and timer.isActive():
            timer.stop()
            
        # Create and start new timer
        project['auto_create_timer'] = QTimer()
        project['auto_create_timer'].timeout.connect(lambda: self.auto_create_snapshot(project_index))
        project['auto_create_timer'].start(ms)
        
        # Update project state
        project['auto_create_running'] = True
        
        # Update UI
        start_stop_btn = controls.get('start_stop_btn')
        if start_stop_btn:
            start_stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
            start_stop_btn.setToolTip("Stop Auto-Create")
            
        # Show toast indicating timer has started
        time_text = f"{interval_value} minute{'s' if interval_value != 1 else ''}" if unit == "Minutes" else f"{interval_value} hour{'s' if interval_value != 1 else ''}"
        project_name = project.get('name', 'project')
        self.show_toast(f"Auto-create enabled for {project_name} - will create versions every {time_text}")
    
    def stop_auto_create_timer(self):
        """Stop both timers"""
        if hasattr(self, 'auto_create_timer'):
            self.auto_create_timer.stop()
        
        if hasattr(self, 'countdown_timer') and self.countdown_timer:
            self.countdown_timer.stop()
    
    def auto_create_version(self):
        """Create a version automatically based on the timer"""
        # Set a flag to indicate we're in the middle of creating a version
        self.is_creating_version = True
        
        # Only create if both origin and destination are set
        if len(self.origin_paths) > 0 and self.destination_path:
            try:
                # Generate version folder name
                version_name = self.generate_version_name()
                version_path = os.path.join(self.destination_path, version_name)
                
                # Create the version folder
                os.makedirs(version_path, exist_ok=True)
                
                # Copy files/folders
                for source_path in self.origin_paths:
                    if os.path.isdir(source_path):
                        # Copy directory contents
                        source_basename = os.path.basename(source_path)
                        dest_dir = os.path.join(version_path, source_basename)
                        shutil.copytree(source_path, dest_dir)
                    else:
                        # Copy file
                        shutil.copy2(source_path, version_path)
                
                # Track if any versions were deleted
                deleted_count = 0
                
                # Cleanup old versions if needed
                if self.auto_delete_check.isChecked():
                    deleted_count = self.cleanup_old_versions()
                
                # Update the contents view if window is visible
                if self.isVisible():
                    self.update_contents_list()
                
                # Always save to recent projects after creating a version
                self.save_recent_projects()
                
                # Show toast notification
                if deleted_count > 0:
                    self.show_toast(f"New version created at: {version_name}\n{deleted_count} old version(s) removed", 5000)
                else:
                    self.show_toast(f"New version created at: {version_name}", 3000)
                
                # Restart the countdown
                self.restart_countdown()
                
            except Exception as e:
                self.show_toast(f"Error creating version: {str(e)}", 5000)
            finally:
                # Clear the creation flag when done
                self.is_creating_version = False
        else:
            # If we don't have origin and destination, stop auto-create
            self.show_toast("Auto-create failed: missing origin files or destination folder", 3000)
            self.stop_auto_create()
            self.is_creating_version = False

    def show_origin_context_menu(self, position):
        """Show context menu for the origin list to remove individual items"""
        if self.origin_list.count() == 0:
            return
            
        menu = QMenu()
        remove_action = menu.addAction("Remove Selected Item")
        action = menu.exec(self.origin_list.mapToGlobal(position))
        
        if action == remove_action:
            # Check if any project has auto-create running
            auto_create_running = False
            if self.current_project_index >= 0:
                project = self.project_tabs[self.current_project_index]
                auto_create_running = project.get('auto_create_running', False)
                
            # Show warning if auto-create is running
            if auto_create_running:
                confirm = QMessageBox.question(
                    self,
                    "Warning - Auto-Create Running",
                    "Auto-create is currently running. Removing origin files during auto-creation may cause issues.\n\nDo you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    return
                    
            selected_row = self.origin_list.currentRow()
            if selected_row >= 0 and selected_row < len(self.origin_paths):
                # Get the path being removed
                removed_path = self.origin_paths[selected_row]
                
                # Remove from data
                self.origin_paths.pop(selected_row)
                
                # Update UI
                self.update_origin_list()
                self.update_button_states()
                self.update_contents_list()
                
                # Show confirmation
                self.show_toast(f"Removed: {os.path.basename(removed_path)}", 2000)
                
                # Stop auto-create if we removed all origins
                if auto_create_running and len(self.origin_paths) == 0 and self.current_project_index >= 0:
                    self.stop_timer(self.current_project_index)
                    self.show_toast("Auto-create stopped - no origin files selected", 3000)

    def show_help(self):
        """Show the help dialog with app information"""
        help_dialog = HelpDialog(self)
        help_dialog.exec()

    def show_contents_context_menu(self, position):
        """Show context menu for the contents list"""
        item = self.contents_list.itemAt(position)
        if not item:
            return
            
        # Get the item text
        item_text = item.text()
        
        # Skip headers and empty items
        if item_text.startswith("---") or not item_text.strip():
            return
            
        menu = QMenu()
        
        if item_text.startswith("  "):  # It's a file or folder in destination
            open_action = menu.addAction("Open")
            open_containing_action = menu.addAction("Open Containing Folder")
            
            action = menu.exec(self.contents_list.mapToGlobal(position))
            
            if action == open_action:
                self.open_content_item(item)
            elif action == open_containing_action:
                # Open the destination folder
                if self.destination_path:
                    os.startfile(self.destination_path)
        else:  # It's either an origin item or the destination path itself
            open_action = menu.addAction("Open")
            
            action = menu.exec(self.contents_list.mapToGlobal(position))
            
            if action == open_action:
                self.open_content_item(item)
    
    def open_content_item(self, item):
        """Open the selected item from the contents list"""
        # Get the item text
        item_text = item.text()
        
        # Skip headers and empty items
        if item_text.startswith("---") or not item_text.strip():
            return
            
        try:
            # Handle items based on their format
            if item_text.startswith("  "):  # It's a subfolder or file in destination folder
                item_name = item_text.strip()
                item_path = os.path.join(self.destination_path, item_name)
                if os.path.exists(item_path):
                    os.startfile(item_path)
                else:
                    self.show_toast(f"Cannot find: {item_path}", 3000)
            else:  # It's either an origin path or the destination path itself
                if os.path.exists(item_text):
                    os.startfile(item_text)
                else:
                    self.show_toast(f"Cannot find: {item_text}", 3000)
        except Exception as e:
            self.show_toast(f"Error opening item: {str(e)}", 3000)

    def toggle_version_limit(self, state):
        """Enable/disable version limit spinbox based on the auto-delete checkbox"""
        # Print the actual state value to debug
        print(f"Raw auto-delete checkbox state value: {state}")
        
        # In PyQt6, the state is an enum, not a boolean, so we need to check it properly
        enabled = (state == Qt.CheckState.Checked.value)
        
        self.version_limit_spin.setEnabled(enabled)
        
        # Debug info
        print(f"Version limit spinner enabled: {enabled}")
    
    def toggle_auto_create_settings(self, state):
        """Enable/disable auto-create settings based on the checkbox state"""
        # Print the actual state value to debug
        print(f"Raw auto-create checkbox state value: {state}")
        
        # In PyQt6, the state is an enum, not a boolean, so we need to check it properly
        enabled = (state == Qt.CheckState.Checked.value)
        
        # Enable/disable interval controls
        self.interval_spin.setEnabled(enabled)
        self.interval_unit.setEnabled(enabled)
        
        # Enable/disable additional options
        self.create_on_start_check.setEnabled(enabled)
        self.auto_create_on_load_check.setEnabled(enabled)
        self.show_floating_timer_check.setEnabled(enabled)
        
        # Enable/disable timer opacity slider if floating timer is checked
        timer_enabled = enabled and self.show_floating_timer_check.isChecked()
        self.timer_opacity_slider.setEnabled(timer_enabled)
        
        # Debug info
        print(f"Auto-create enabled: {enabled}")
        print(f"Timer slider enabled: {timer_enabled}")
        
        if enabled:
            self.show_toast("Auto-create settings enabled", 2000)
    
    def toggle_floating_timer_setting(self, state):
        """Enable/disable timer opacity slider based on the floating timer checkbox"""
        # Print the actual state value to debug
        print(f"Raw floating timer checkbox state value: {state}")
        
        # In PyQt6, the state is an enum, not a boolean, so we need to check it properly
        enabled = (state == Qt.CheckState.Checked.value)
        
        # Only enable the opacity slider if auto-create is also enabled
        parent_enabled = self.auto_create_check.isChecked()
        self.timer_opacity_slider.setEnabled(enabled and parent_enabled)
        
        # Toggle just the visibility of the current timer, don't touch other timers
        if self.current_project_index >= 0 and self.current_project_index < len(self.project_tabs):
            project = self.project_tabs[self.current_project_index]
            floating_timer = project.get('floating_timer')
            
            if enabled:
                # Ensure the timer exists and is visible
                if not floating_timer:
                    # Create a new timer if it doesn't exist
                    floating_timer = self.create_floating_timer(self.current_project_index)
                
                # Show timer
                if floating_timer:
                    floating_timer.show()
                    floating_timer.raise_()
                    
                    # Reposition all timers to stack properly
                    self.reposition_all_timers()
                    
                self.show_toast("Floating timer enabled - drag icon to reposition", 3000)
            else:
                # Just hide the timer, don't destroy it
                if floating_timer:
                    floating_timer.hide()
                    
                    # Reposition remaining visible timers
                    self.reposition_all_timers()
                    
                self.show_toast("Floating timer hidden - it still tracks time in background", 3000)
        
        # Debug info
        print(f"Floating timer enabled: {enabled}")
        print(f"Opacity slider enabled: {enabled and parent_enabled}")
    
    def update_timer_opacity(self, value):
        """Update the opacity of the floating timer"""
        if self.floating_timer:
            opacity = value / 100.0
            self.floating_timer.set_opacity(opacity)
    
    def toggle_floating_timer(self, show):
        """Show or hide the floating timer for the current project"""
        if self.current_project_index < 0 or self.current_project_index >= len(self.project_tabs):
            return
            
        # Get the current project data
        project = self.project_tabs[self.current_project_index]
        
        if show:
            # Get current project name and color
            project_name = project.get('name', "Project")
            project_color = project.get('project_color')
            
            # Create a completely new floating timer specific to this project if it doesn't exist
            # or use the existing one if already created
            if not project.get('floating_timer'):
                # Create a new floating timer
                new_timer = FloatingCountdownTimer(project_name=project_name, project_color=project_color)
                
                # Set opacity from slider
                opacity_slider = project.get('controls', {}).get('timer_opacity_slider')
                if opacity_slider and hasattr(opacity_slider, 'value'):
                    opacity = opacity_slider.value() / 100.0
                    new_timer.set_opacity(opacity)
                else:
                    new_timer.set_opacity(1.0)  # Default to fully opaque
                
                # Update the timer with current countdown value
                # Always show the timer regardless of whether auto-create is running
                countdown_seconds = project.get('countdown_seconds', 0)
                if countdown_seconds > 0:
                    new_timer.update_time(countdown_seconds)
                else:
                    new_timer.update_time(0)  # Show zeros if countdown not set
                
                # Save the new timer reference in the project data
                self.floating_timer = new_timer
                project['floating_timer'] = new_timer
                
                # Show the new timer
                new_timer.show()
            else:
                # Use existing timer
                self.floating_timer = project['floating_timer']
                
                # Update timer with current countdown
                countdown_seconds = project.get('countdown_seconds', 0)
                if countdown_seconds > 0:
                    self.floating_timer.update_time(countdown_seconds)
                else:
                    self.floating_timer.update_time(0)
                    
                # Ensure timer is visible
                self.floating_timer.show()
        else:
            # If we want to hide this specific project's timer
            if project.get('floating_timer'):
                project['floating_timer'].hide()
                project['floating_timer'] = None
                
            # Update the app's current floating timer reference if it's the one being hidden
            if self.floating_timer and self.floating_timer == project.get('floating_timer'):
                self.floating_timer = None
    
    def toggle_auto_create(self):
        """Toggle the auto-create functionality on/off with the button"""
        if self.current_project_index < 0 or self.current_project_index >= len(self.project_tabs):
            return
            
        # Get the current project
        project = self.project_tabs[self.current_project_index]
        
        if project.get('auto_create_running', False):
            # Stop the auto-create process
            self.stop_timer(self.current_project_index)
        else:
            # Check if origin and destination are configured
            if len(self.origin_paths) > 0 and self.destination_path:
                # We have origin and destination, check if auto-create is enabled
                if self.auto_create_check.isChecked():
                    # Check if we should create a version when starting auto-create
                    if self.create_on_start_check.isChecked():
                        self.create_version()
                    self.start_timer(self.current_project_index)
                else:
                    # Enable auto-create and start
                    self.auto_create_check.setChecked(True)
                    # The check will trigger toggle_auto_create_settings
                    if self.create_on_start_check.isChecked():
                        self.create_version()
                    self.start_timer(self.current_project_index)
            else:
                # Show error message if origin or destination is missing
                self.show_toast("Cannot start auto-create: Please select origin and destination folders first.", 5000)

    def open_origin_folder(self):
        """Open the first origin folder or parent folder of the first file"""
        if self.origin_paths:
            path = self.origin_paths[0]
            if os.path.isfile(path):
                path = os.path.dirname(path)
            os.startfile(path)
    
    def open_dest_folder(self):
        """Open the destination folder in file explorer"""
        if self.destination_path:
            os.startfile(self.destination_path)

    def choose_project_color(self):
        """Open a color picker dialog to choose a project color"""
        if self.current_project_index < 0 or self.current_project_index >= len(self.project_tabs):
            return
            
        project = self.project_tabs[self.current_project_index]
        current_color = project.get('project_color', QColor(100, 100, 100))
        
        # Open color dialog
        color = QColorDialog.getColor(current_color, self, "Choose Project Color")
        
        # If a valid color was selected
        if color.isValid():
            # Update the project color
            project['project_color'] = color
            
            # Update the color preview
            if 'controls' in project and 'color_preview' in project['controls']:
                project['controls']['color_preview'].setStyleSheet(
                    f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid #888888;"
                )
            
            # Update the tab color
            self.project_tabs_widget.setTabColor(self.current_project_index, color)
            
            # Update the timer color if it exists
            if project.get('floating_timer'):
                # Update the existing timer's color
                project['floating_timer'].update_color(color)
                
                # If this is the current project, update the app state
                if self.current_project_index >= 0 and project == self.project_tabs[self.current_project_index]:
                    self.floating_timer = project['floating_timer']

    def start_timer(self, project_index):
        """Start the timer for a specific project"""
        # Validate project index
        if project_index < 0 or project_index >= len(self.project_tabs):
            return
            
        project = self.project_tabs[project_index]
        controls = project.get('controls', {})
        settings = project.get('settings', {})
        
        # Get interval from settings
        interval = settings.get('auto_create_interval', 5)
        try:
            interval = int(interval)
        except ValueError:
            interval = 5
            
        # Set up countdown
        project['countdown_seconds'] = interval * 60  # Convert minutes to seconds
        
        # Create timer if it doesn't exist
        if not project.get('auto_create_timer'):
            project['auto_create_timer'] = QTimer()
            project['auto_create_timer'].timeout.connect(lambda: self.update_timer(project_index))
            
        # Start the timer to update every second
        project['auto_create_timer'].start(1000)
        
        # Update project state
        project['auto_create_running'] = True
        
        # Update UI controls
        start_stop_btn = controls.get('start_stop_btn')
        if start_stop_btn:
            start_stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
            start_stop_btn.setToolTip("Stop Auto-Create")
            
        # Format the time for display
        countdown_seconds = project['countdown_seconds']
        hours = countdown_seconds // 3600
        minutes = (countdown_seconds % 3600) // 60
        seconds = countdown_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Update countdown label
        countdown_label = controls.get('countdown_label')
        if countdown_label:
            countdown_label.setText(time_str)
            
        # Always initialize or update floating timer for this project
        # If it already exists, it will be updated with the current countdown
        self.create_floating_timer(project_index)

    def update_timer(self, project_index):
        """Update the timer countdown for a specific project"""
        if project_index < 0 or project_index >= len(self.project_tabs):
            return
            
        # Get the project data for the specified index
        project = self.project_tabs[project_index]
        
        # Check if auto-create is running for this project
        if not project.get('auto_create_running', False):
            return
            
        # Get current countdown value
        countdown_seconds = project.get('countdown_seconds', 0)
        
        # Decrement the countdown
        countdown_seconds -= 1
        project['countdown_seconds'] = countdown_seconds
        
        # Format the time
        hours = countdown_seconds // 3600
        minutes = (countdown_seconds % 3600) // 60
        seconds = countdown_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Update the time display for this project
        controls = project.get('controls', {})
        countdown_label = controls.get('countdown_label')
        if countdown_label:
            countdown_label.setText(time_str)
            
        # Update the floating timer display if it exists for this project
        floating_timer = project.get('floating_timer')
        if floating_timer:
            floating_timer.update_time(countdown_seconds)
            
        # Check if countdown has reached zero
        if countdown_seconds <= 0:
            self.auto_create_snapshot(project_index)
            self.stop_timer(project_index)
    
    def auto_create_snapshot(self, project_index):
        """Create a version snapshot for a specific project when timer reaches zero"""
        if project_index < 0 or project_index >= len(self.project_tabs):
            return
            
        # Get the project data
        project = self.project_tabs[project_index]
        
        # Save current project state
        current_index = self.current_project_index
        
        # Temporarily switch to this project
        self.current_project_index = project_index
        
        # Set up the necessary data for creating a version
        self.origin_paths = project.get('origin_paths', []).copy()
        self.destination_path = project.get('destination_path', '')
        
        # Only create if we have both origin and destination paths
        if len(self.origin_paths) > 0 and self.destination_path:
            try:
                # Mark that we're creating a version
                self.is_creating_version = True
                
                # Create the version
                self.create_version()
                
                # Restart the timer
                interval_value = 5  # Default to 5 minutes if not found
                
                controls = project.get('controls', {})
                interval_spin = controls.get('interval_spin')
                if interval_spin and hasattr(interval_spin, 'value'):
                    interval_value = interval_spin.value()
                
                # Update countdown for next automatic version
                project['countdown_seconds'] = interval_value * 60
                
                # Update floating timer if it exists
                floating_timer = project.get('floating_timer')
                if floating_timer:
                    floating_timer.update_time(interval_value * 60)
                
                # Show notification
                self.show_toast(f"Auto-created version for {project.get('name', 'Project')}")
            except Exception as e:
                self.show_toast(f"Error creating auto-version: {str(e)}", 5000)
            finally:
                # Reset the flag
                self.is_creating_version = False
        
        # Restore current project index
        self.current_project_index = current_index

    def stop_timer(self, project_index):
        """Stop the timer for a specific project"""
        # Validate project index
        if project_index < 0 or project_index >= len(self.project_tabs):
            return
            
        project = self.project_tabs[project_index]
        controls = project.get('controls', {})
        
        # Stop the timer
        timer = project.get('auto_create_timer')
        if timer and timer.isActive():
            timer.stop()
            
        # Update project state
        project['auto_create_running'] = False
        
        # Update UI controls
        start_stop_btn = controls.get('start_stop_btn')
        if start_stop_btn:
            start_stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            start_stop_btn.setToolTip("Start Auto-Create")
            
        # Update countdown label
        countdown_label = controls.get('countdown_label')
        if countdown_label:
            countdown_label.setText("--:--:--")
            
        # Update floating timer if it exists, but KEEP IT VISIBLE
        floating_timer = project.get('floating_timer')
        if floating_timer:
            floating_timer.update_time(0)  # Reset the display to zeros
            # REMOVED: We no longer hide the floating timer even when timer is stopped
    
    def create_floating_timer(self, project_index):
        """Create and display a floating timer for a specific project"""
        # Validate project index
        if project_index < 0 or project_index >= len(self.project_tabs):
            print(f"Invalid project index for timer creation: {project_index}")
            return None
            
        print(f"Creating floating timer for project {project_index}")
        project = self.project_tabs[project_index]
        project_name = project.get('name', "Project")
        controls = project.get('controls', {})
        
        # If a timer already exists for this project, check if it's valid and re-use it
        existing_timer = project.get('floating_timer')
        if existing_timer:
            try:
                if hasattr(existing_timer, 'isVisible'):
                    print(f"Existing timer found for project {project_index}: {project_name}")
                    # Update the existing timer
                    existing_timer.update_project_name(project_name)
                    existing_timer.update_time(project.get('countdown_seconds', 0))
                    existing_timer.show()
                    
                    # Make sure it's in the all_floating_timers list
                    if not hasattr(self, 'all_floating_timers'):
                        self.all_floating_timers = []
                        
                    if existing_timer not in self.all_floating_timers:
                        self.all_floating_timers.append(existing_timer)
                        
                    # Update reference if this is the current project
                    if project_index == self.current_project_index:
                        self.floating_timer = existing_timer
                    
                    return existing_timer
            except (RuntimeError, AttributeError) as e:
                print(f"Error checking existing timer: {e}")
                project['floating_timer'] = None
        
        # Get project color for the new timer
        project_color = project.get('project_color')
        if not project_color or not isinstance(project_color, QColor):
            # Get color from tab if available
            project_color = self.project_tabs_widget.getTabColor(project_index)
        
        # Create a unique ID for this project to track timer associations
        project_id = project.get('id')
        if not project_id:
            project_id = str(uuid.uuid4())
            project['id'] = project_id
        
        print(f"Creating new timer for project {project_index}: {project_name} (ID: {project_id})")
        
        # Create a new floating timer with the project's color
        new_timer = FloatingCountdownTimer(
            parent=self, 
            project_name=project_name, 
            project_color=project_color,
            project_id=project_id
        )
        
        # Set opacity from slider
        opacity_slider = controls.get('timer_opacity_slider')
        if opacity_slider and hasattr(opacity_slider, 'value'):
            opacity = opacity_slider.value() / 100.0
            new_timer.set_opacity(opacity)
        
        # Update the timer with current countdown
        countdown_seconds = project.get('countdown_seconds', 0)
        if countdown_seconds > 0:
            new_timer.update_time(countdown_seconds)
        else:
            new_timer.update_time(0)  # Show zeros if no countdown
            
        # Show the timer - always visible by default
        new_timer.show()
        
        # Store the timer reference in the project data
        project['floating_timer'] = new_timer
        
        # Add to the global list of all floating timers if not already there
        if not hasattr(self, 'all_floating_timers'):
            self.all_floating_timers = []
            
        if new_timer not in self.all_floating_timers:
            self.all_floating_timers.append(new_timer)
        
        # If this is the current project, update the app's floating_timer reference
        if project_index == self.current_project_index:
            self.floating_timer = new_timer
        
        print(f"Created new timer for project {project_index}")
        # Use the non-recursive version to avoid cleanup calling create which calls cleanup...
        self._reposition_timers_without_cleanup()
        
        return new_timer

    def reposition_all_timers(self):
        """Reposition all floating timers to stack properly"""
        # First run cleanup to ensure we don't have orphaned timers
        self.cleanup_orphaned_timers()
        # No need to duplicate the repositioning code here as it's already in _reposition_timers_without_cleanup

    def remove_project_tab(self, index):
        """Remove a project tab and its associated data"""
        if index < 0 or index >= len(self.project_tabs):
            return
            
        # Get the project being removed
        removed_project = self.project_tabs[index]
        
        # Explicitly clean up any timers associated with this project
        floating_timer = removed_project.get('floating_timer')
        if floating_timer:
            # Remove from all_floating_timers list
            if floating_timer in self.all_floating_timers:
                self.all_floating_timers.remove(floating_timer)
            
            # Close and destroy the floating timer
            floating_timer.close()
            floating_timer.deleteLater()
            removed_project['floating_timer'] = None
            
        # Stop any countdown or auto-create timers
        auto_create_timer = removed_project.get('auto_create_timer')
        if auto_create_timer and hasattr(auto_create_timer, 'isActive') and auto_create_timer.isActive():
            auto_create_timer.stop()
            
        countdown_timer = removed_project.get('countdown_timer')
        if countdown_timer and hasattr(countdown_timer, 'isActive') and countdown_timer.isActive():
            countdown_timer.stop()
            
        # Now remove the project from our list
        self.project_tabs.pop(index)
        
        # Update current_project_index if needed
        if self.current_project_index >= len(self.project_tabs):
            self.current_project_index = len(self.project_tabs) - 1
        elif self.current_project_index >= index:
            # If removing a tab before the current one, adjust the index
            self.current_project_index -= 1
        
        # If we still have projects, load the current one
        if self.project_tabs:
            self.load_project_state(self.current_project_index)
            
        # Clean up any orphaned timers and reposition remaining ones
        self.cleanup_orphaned_timers()
        
        # Log the removal
        print(f"Removed project tab at index {index}")
        print(f"New current project index: {self.current_project_index}")
        print(f"Number of remaining projects: {len(self.project_tabs)}")

    def cleanup_orphaned_timers(self):
        """Check for and clean up any orphaned floating timers"""
        if not hasattr(self, 'all_floating_timers') or not self.all_floating_timers:
            return
        
        print(f"Before cleanup: {len(self.all_floating_timers)} floating timers")
        self.debug_timers()
        
        # AGGRESSIVE CLEANUP: Only keep timers for active projects
        # Get a list of all valid timer references from active project tabs
        valid_timers = []
        for project in self.project_tabs:
            floating_timer = project.get('floating_timer')
            if floating_timer:
                valid_timers.append(floating_timer)
        
        # Find all timers that aren't in the valid_timers list
        timers_to_remove = []
        for timer in self.all_floating_timers:
            if timer not in valid_timers:
                timers_to_remove.append(timer)
        
        # Remove all invalid timers
        for timer in timers_to_remove:
            print(f"Removing orphaned timer: {timer}")
            if timer in self.all_floating_timers:
                self.all_floating_timers.remove(timer)
            try:
                if timer and hasattr(timer, 'close'):
                    timer.close()
                    timer.deleteLater()
            except (RuntimeError, AttributeError) as e:
                print(f"Error while closing timer: {e}")
        
        print(f"Removed {len(timers_to_remove)} orphaned timers")
        
        # Ensure we don't have duplicate timers in all_floating_timers
        # This can happen if the same timer is added multiple times
        unique_timers = []
        seen_timers = set()
        for timer in self.all_floating_timers:
            if timer and timer not in seen_timers:
                seen_timers.add(timer)
                unique_timers.append(timer)
        
        # Update list with unique timers only
        self.all_floating_timers = unique_timers
        
        # Ensure each project's floating_timer is in all_floating_timers
        for project in self.project_tabs:
            floating_timer = project.get('floating_timer')
            if floating_timer and floating_timer not in self.all_floating_timers:
                self.all_floating_timers.append(floating_timer)
        
        # Reposition remaining timers
        self._reposition_timers_without_cleanup()
    
    def _reposition_timers_without_cleanup(self):
        """Reposition timers without calling cleanup (to avoid recursion)"""
        if not hasattr(self, 'all_floating_timers') or not self.all_floating_timers:
            return
        
        # Get screen dimensions
        desktop = QApplication.primaryScreen().geometry()
        
        # Start positions
        x_pos = desktop.width() - 200 - 20  # 200 is width of timer, 20px from right edge
        y_pos = 50  # Starting y position
        
        # Sort timers by their current y position to maintain relative order
        sorted_timers = sorted([t for t in self.all_floating_timers if t and t.isVisible()], 
                              key=lambda t: t.y())
        
        # Reposition each timer
        for timer in sorted_timers:
            timer.move(x_pos, y_pos)
            y_pos += timer.height() + 10  # Add spacing between timers
            
            # Ensure we don't go off screen
            if y_pos + timer.height() > desktop.height() - 10:
                # Start a new column to the left
                x_pos -= timer.width() + 20
                y_pos = 50
                
                # Prevent going off screen horizontally
                if x_pos < 10:
                    x_pos = 10

    def force_timer_cleanup(self):
        """Force cleanup of all floating timers and recreate only active ones"""
        print("*** FORCE TIMER CLEANUP ***")
        print(f"Current tab count: {self.project_tabs_widget.count() - 1}")  # Minus 1 for the + tab
        print(f"Current project tabs count: {len(self.project_tabs)}")
        
        # Check for inconsistencies before cleanup
        self.check_for_inconsistencies()
        
        # First, log the current state
        self.debug_timers()
        
        # Close and destroy all existing timers
        if hasattr(self, 'all_floating_timers'):
            timer_count = len(self.all_floating_timers)
            print(f"Closing {timer_count} timers")
            
            for timer in self.all_floating_timers.copy():  # Use copy to avoid modifying while iterating
                try:
                    if timer and hasattr(timer, 'close'):
                        print(f"Closing timer: {timer.project_label.text() if hasattr(timer, 'project_label') else 'Unknown'}")
                        timer.close()
                        timer.deleteLater()
                except (RuntimeError, AttributeError) as e:
                    print(f"Error while closing timer in force cleanup: {e}")
            
            # Clear the list
            self.all_floating_timers = []
        
        # Reset timer references in all projects
        for project in self.project_tabs:
            project['floating_timer'] = None
        
        print("All floating timers cleared")
        
        # Allow a short delay for Qt to process deletions
        QApplication.processEvents()
        
        print(f"Recreating timers for {len(self.project_tabs)} projects")
        
        # Recreate timers for all active projects
        for i, project in enumerate(self.project_tabs):
            print(f"Creating timer for project {i}: {project.get('name', 'Unknown')}")
            new_timer = self.create_floating_timer(i)
            if new_timer:
                print(f"Created timer for project {i}")
            else:
                print(f"Failed to create timer for project {i}")
                
        # Final check
        print("*** FORCE TIMER CLEANUP COMPLETE ***")
        self.debug_timers()
        
        # Check for inconsistencies after cleanup
        self.check_for_inconsistencies()

    def toggle_tab(self, index):
        """Switch to the selected tab or create a new one if it's the + tab"""
        print(f"TOGGLE_TAB: Toggling tab to index {index}, total tabs: {self.project_tabs_widget.count()}")
        if index == self.project_tabs_widget.count() - 1:
            # The + tab was clicked, create a new project tab
            print("TOGGLE_TAB: + tab clicked, creating new project tab")
            self.add_new_project_tab()
            return
        
        # A regular tab was clicked, switch to it
        # Is this a different tab than before?
        print(f"TOGGLE_TAB: Current index: {self.current_project_index}, New index: {index}")
        if self.current_project_index != index:
            # Save the state of the current project
            if self.current_project_index >= 0 and self.current_project_index < len(self.project_tabs):
                print(f"TOGGLE_TAB: Saving state of current project {self.current_project_index}")
                self.save_project_state(self.current_project_index)
            
            # Update the current project index
            print(f"TOGGLE_TAB: Updating current project index from {self.current_project_index} to {index}")
            self.current_project_index = index
            
            # Load the state of the newly selected project
            print(f"TOGGLE_TAB: Loading state of new project {index}")
            self.load_project_state(index)
            
            # Force cleanup of timers to ensure only active ones are displayed
            print("TOGGLE_TAB: Running cleanup of orphaned timers")
            self.cleanup_orphaned_timers()
            
            print(f"TOGGLE_TAB: Switched to project tab {index}")
        else:
            print(f"TOGGLE_TAB: Already on tab {index}, no action needed")

    def add_new_project_tab(self):
        """Add a new project tab with default settings"""
        print("ADD_TAB: Starting to add new project tab")
        # Save current project state first
        if self.current_project_index >= 0 and self.current_project_index < len(self.project_tabs):
            print(f"ADD_TAB: Saving current project state for index {self.current_project_index}")
            self.save_project_state(self.current_project_index)
            
        # Generate random color for this project tab
        project_color = QColor(
            random.randint(80, 180),  # Red
            random.randint(80, 180),  # Green
            random.randint(80, 180)   # Blue
        )
        print(f"ADD_TAB: Generated random color for tab")
        
        # Create a new project object
        name = f"New Project {len(self.project_tabs) + 1}"
        project_id = str(uuid.uuid4())
        print(f"ADD_TAB: Creating new project: {name} (ID: {project_id})")
        project = {
            'name': name,
            'origin_paths': [],
            'destination_path': "",
            'auto_create_running': False,
            'countdown_seconds': 0,
            'auto_create_timer': None,
            'countdown_timer': None,
            'floating_timer': None,
            'project_color': project_color,
            'id': project_id,
            'settings': {
                'auto_create_interval': 5,
                'auto_create_interval_unit': "Minutes",
                'floating_timer_enabled': True,
                'timer_opacity': 85,
            },
            'controls': {}
        }
        
        # Add to project tabs list
        print(f"ADD_TAB: Adding project to project_tabs list, current count: {len(self.project_tabs)}")
        self.project_tabs.append(project)
        print(f"ADD_TAB: Project added, new count: {len(self.project_tabs)}")
        
        # Create a widget for this project
        project_widget = QWidget()
        project['widget'] = project_widget
        
        # Set up the project tab UI (reusing the same UI for all tabs)
        # For simplicity, we're just using a placeholder widget
        layout = QVBoxLayout(project_widget)
        
        # Create content panel with origin and destination widgets
        content_panel = self.create_content_panel()
        layout.addWidget(content_panel)
        
        # Disable margins for the layout
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Set the destination path to the default path if it's not already set
        if not self.destination_path:
            default_path = os.path.join(os.path.expanduser("~"), "Version Diving")
            self.destination_path = default_path
            
        # Update project with current origin and destination
        project['origin_paths'] = self.origin_paths.copy()
        project['destination_path'] = self.destination_path
        
        # Update settings with current settings
        if hasattr(self, 'auto_create_check') and self.auto_create_check.isChecked():
            project['settings']['auto_create_enabled'] = True
        else:
            project['settings']['auto_create_enabled'] = False
            
        if hasattr(self, 'interval_spin'):
            project['settings']['auto_create_interval'] = self.interval_spin.value()
            
        if hasattr(self, 'interval_unit'):
            project['settings']['auto_create_interval_unit'] = self.interval_unit.currentText()
        
        # Make floating timer enabled by default
        print(f"ADD_TAB: Enabling floating timer for new project")
        self.toggle_floating_timer_setting(Qt.CheckState.Checked.value)
        
        # Add the tab to the tab widget - insert before the + tab
        tab_index = self.project_tabs_widget.count() - 1  # Position before the + tab
        print(f"ADD_TAB: Inserting tab at index {tab_index}, before + tab")
        self.project_tabs_widget.insertTab(tab_index, project_widget, name)
        print(f"ADD_TAB: Tab inserted, new tab count: {self.project_tabs_widget.count()}")
        
        # Set the tab color
        self.project_tabs_widget.setTabColor(tab_index, project_color)
        
        # Update the color preview
        self.color_preview.setStyleSheet(f"background-color: rgb({project_color.red()}, {project_color.green()}, {project_color.blue()}); border: 1px solid #888888;")
        
        # Switch to the new tab
        print(f"ADD_TAB: Switching to the new tab at index {tab_index}")
        self.project_tabs_widget.setCurrentIndex(tab_index)
        
        # Set the current project index
        print(f"ADD_TAB: Setting current project index from {self.current_project_index} to {tab_index}")
        self.current_project_index = tab_index
        
        # Debug info
        print(f"ADD_TAB: Created new project tab: {name} (index {tab_index})")
        print(f"ADD_TAB: Current origin paths: {self.origin_paths}")
        print(f"ADD_TAB: Current destination path: {self.destination_path}")
        
        # Notify
        self.show_toast(f"Created new project tab: {name}", 2000)
        
        # Set auto-create to enabled but not running
        # User must click the start button to begin the countdown
        self.auto_create_running = False  # Don't automatically start
        
        # Force a cleanup to ensure we don't have any orphaned timers
        print(f"ADD_TAB: Running force_timer_cleanup to ensure clean timer state")
        self.force_timer_cleanup()
        
        # Create a floating timer for this project
        print(f"ADD_TAB: Creating floating timer for the new project")
        timer = self.create_floating_timer(tab_index)
        
        # Make sure the timer is visible immediately
        if timer:
            print(f"ADD_TAB: Timer created successfully, making it visible")
            timer.show()
        else:
            print(f"ADD_TAB: Failed to create timer for the new project")
        
        print(f"ADD_TAB: Logging final state of all timers")
        self.debug_timers()
        
        # Return the index of the new tab
        print(f"ADD_TAB: New project tab creation completed")
        return tab_index

    def debug_timers(self):
        """Print debug information about all timers"""
        if not hasattr(self, 'all_floating_timers'):
            print("No floating timers list found")
            return
            
        print(f"All floating timers ({len(self.all_floating_timers)}):")
        for i, timer in enumerate(self.all_floating_timers):
            try:
                project_name = timer.project_label.text() if hasattr(timer, 'project_label') else "Unknown"
                project_id = getattr(timer, 'project_id', 'Unknown')
                is_visible = timer.isVisible() if hasattr(timer, 'isVisible') else "Unknown"
                print(f"  {i}: {project_name} (ID: {project_id}) - Visible: {is_visible}")
            except:
                print(f"  {i}: <Invalid timer>")
                
        print("Project timer references:")
        for i, project in enumerate(self.project_tabs):
            timer = project.get('floating_timer')
            project_name = project.get('name', 'Unknown')
            if timer:
                try:
                    timer_name = timer.project_label.text() if hasattr(timer, 'project_label') else "Unknown"
                    is_visible = timer.isVisible() if hasattr(timer, 'isVisible') else "Unknown"
                    print(f"  Project {i} ({project_name}): Timer {timer_name} - Visible: {is_visible}")
                except:
                    print(f"  Project {i} ({project_name}): <Invalid timer reference>")
            else:
                print(f"  Project {i} ({project_name}): No timer")

    def check_for_inconsistencies(self):
        """Check and log inconsistencies between project tabs and floating timers"""
        print("\n===== CHECKING FOR INCONSISTENCIES =====")
        
        # Check if there are more timers than projects
        try:
            if not hasattr(self, 'all_floating_timers'):
                print("No floating timers list found")
                return
                
            timer_count = len(self.all_floating_timers)
            project_count = len(self.project_tabs)
            
            print(f"Project count: {project_count}")
            print(f"Timer count: {timer_count}")
            
            if timer_count > project_count:
                print("WARNING: More timers than projects!")
                # Find the extra timers
                timer_names = []
                for timer in self.all_floating_timers:
                    try:
                        name = timer.project_label.text() if hasattr(timer, 'project_label') else "Unknown"
                        timer_names.append(name)
                    except:
                        timer_names.append("Invalid timer")
                        
                project_names = [p.get('name', 'Unknown') for p in self.project_tabs]
                
                print("Project names:")
                for name in project_names:
                    print(f"  {name}")
                    
                print("Timer names:")
                for name in timer_names:
                    print(f"  {name}")
                
            # Check for projects without timers
            projects_without_timers = []
            for i, project in enumerate(self.project_tabs):
                if not project.get('floating_timer'):
                    projects_without_timers.append((i, project.get('name', 'Unknown')))
                    
            if projects_without_timers:
                print("Projects without timers:")
                for idx, name in projects_without_timers:
                    print(f"  Project {idx}: {name}")
                    
            # Check for timers not in project_tabs
            timer_project_ids = set()
            for timer in self.all_floating_timers:
                if hasattr(timer, 'project_id') and timer.project_id:
                    timer_project_ids.add(timer.project_id)
                    
            project_ids = set()
            for project in self.project_tabs:
                if project.get('id'):
                    project_ids.add(project.get('id'))
                    
            orphan_ids = timer_project_ids - project_ids
            if orphan_ids:
                print("Orphaned timer IDs:")
                for timer_id in orphan_ids:
                    print(f"  {timer_id}")
                
            print("===== CONSISTENCY CHECK COMPLETE =====\n")
        except Exception as e:
            print(f"Error during consistency check: {e}")

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Version Diving Help")
        self.setMinimumSize(600, 450)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget for different help sections
        tabs = QTabWidget()
        
        # Overview tab
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logoicon.png")
        logo_label = QLabel()
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_pixmap = logo_pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            overview_layout.addWidget(logo_label)
            
        title = QLabel("<h1>Version Diving</h1>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overview_layout.addWidget(title)
        
        description = QLabel(
            "<p><b>Version Diving</b> helps you create and manage automatic versioning of your projects, "
            "keeping track of changes and allowing you to revert to previous states easily.</p>"
            "<p>This is especially valuable when working with AI coding assistants, where changes "
            "can happen rapidly and sometimes code can get accidentally lost or modified.</p>"
        )
        description.setWordWrap(True)
        overview_layout.addWidget(description)
        
        ai_coding = QLabel(
            "<h3>Benefits for AI-Assisted Coding:</h3>"
            "<ul>"
            "<li><b>Safety Net:</b> Never lose important code changes again - revert to any saved version</li>"
            "<li><b>Tracking Changes:</b> See how your project evolves as AI makes suggestions</li>"
            "<li><b>Experiment Freely:</b> Try bold code changes knowing you can always go back</li>"
            "<li><b>Preserve Good Ideas:</b> Keep intermediate versions in case you need to recover specific implementations</li>"
            "<li><b>Compare Evolution:</b> See how your project has changed from beginning to end</li>"
            "</ul>"
        )
        ai_coding.setWordWrap(True)
        overview_layout.addWidget(ai_coding)
        
        quick_start = QLabel(
            "<h3>Quick Start:</h3>"
            "<ol>"
            "<li>Select files/folders to track in the <b>Origin Selection</b> section</li>"
            "<li>Choose where to save versions in the <b>Destination Folder</b> section</li>"
            "<li>Click <b>Create Version</b> or set up auto-create in the <b>Settings</b> tab</li>"
            "</ol>"
        )
        quick_start.setWordWrap(True)
        overview_layout.addWidget(quick_start)
        
        overview_layout.addStretch()
        tabs.addTab(overview_widget, "Overview")
        
        # Features tab
        features_widget = QScrollArea()
        features_widget.setWidgetResizable(True)
        features_content = QWidget()
        features_layout = QVBoxLayout(features_content)
        
        features_title = QLabel("<h2>Feature Details</h2>")
        features_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_layout.addWidget(features_title)
        
        features = [
            ("<b>Project Tabs</b>", "Manage multiple versioning setups simultaneously. Use the + button to add a new project tab."),
            ("<b>Origin Selection</b>", "Select files or folders to track. You can add multiple sources, and individually remove entries with right-click."),
            ("<b>Destination Folder</b>", "Choose where versions will be saved. Each version will be created in a separate folder here."),
            ("<b>Create Version</b>", "Manually create a snapshot of your selected files/folders. Use this after making significant changes."),
            ("<b>Contents Tab</b>", "View a list of your selected files/folders and the contents of your destination folder."),
            ("<b>Settings Tab</b>", "Configure version naming, automatic cleanup, and automatic version creation."),
            ("<b>Version Naming</b>", "Customize how version folders are named, with options for date/time, sequential numbers, or custom formats."),
            ("<b>Auto-Delete Old Versions</b>", "Automatically maintain a limited number of versions to save disk space."),
            ("<b>Auto-Create Versions</b>", "Set the app to automatically create versions at regular intervals, ideal for long AI coding sessions."),
            ("<b>Floating Timer</b>", "Shows a countdown to the next automatic version. Can be positioned anywhere on your screen."),
            ("<b>System Tray</b>", "The app minimizes to your system tray and continues creating versions in the background."),
            ("<b>Toast Notifications</b>", "Non-intrusive popups confirm when versions are created or settings are changed."),
            ("<b>Recent Projects</b>", "Quickly load previously used project configurations from the Recent Projects tab.")
        ]
        
        for title, desc in features:
            feature_layout = QHBoxLayout()
            
            feature_title = QLabel(title)
            feature_title.setMinimumWidth(150)
            feature_layout.addWidget(feature_title)
            
            feature_desc = QLabel(desc)
            feature_desc.setWordWrap(True)
            feature_layout.addWidget(feature_desc, 1)
            
            features_layout.addLayout(feature_layout)
            
            # Add separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            features_layout.addWidget(separator)
            
        features_layout.addStretch()
        features_widget.setWidget(features_content)
        tabs.addTab(features_widget, "Features")
        
        # AI Workflow tab
        ai_widget = QScrollArea()
        ai_widget.setWidgetResizable(True)
        ai_content = QWidget()
        ai_layout = QVBoxLayout(ai_content)
        
        ai_title = QLabel("<h2>AI Coding Workflow</h2>")
        ai_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_layout.addWidget(ai_title)
        
        ai_tips = QLabel(
            "<p>When coding with AI assistants, changes can happen quickly and code can sometimes get lost "
            "or overwritten unintentionally. Here's how to use Version Diving effectively in your AI-assisted workflow:</p>"
        )
        ai_tips.setWordWrap(True)
        ai_layout.addWidget(ai_tips)
        
        workflows = [
            ("<b>Before Starting</b>", "Create a manual version before beginning an AI coding session to establish a clean baseline."),
            ("<b>Automatic Intervals</b>", "Set auto-create to 5-10 minute intervals to capture incremental changes during active work."),
            ("<b>Key Milestones</b>", "Create manual versions after achieving key functionality or when you reach a stable point."),
            ("<b>Before Major Changes</b>", "Create a version before asking the AI to make significant structural changes."),
            ("<b>After Iterations</b>", "Create a version after each significant iteration with the AI to track the evolution."),
            ("<b>Background Operation</b>", "Let Version Diving run in the background (minimized to system tray) during long coding sessions."),
            ("<b>Recovery Strategy</b>", "If the AI makes changes you need to revert, open your destination folder and compare the versions to recover specific code."),
            ("<b>Multiple Projects</b>", "Use project tabs to maintain different versioning setups for different coding projects."),
            ("<b>Before Refactoring</b>", "Create a version before requesting refactoring from AI, in case you need to recover original implementation details."),
            ("<b>Session Tracking</b>", "Name versions with meaningful prefixes to track different AI coding sessions or features.")
        ]
        
        for title, desc in workflows:
            workflow_layout = QHBoxLayout()
            
            workflow_title = QLabel(title)
            workflow_title.setMinimumWidth(150)
            workflow_layout.addWidget(workflow_title)
            
            workflow_desc = QLabel(desc)
            workflow_desc.setWordWrap(True)
            workflow_layout.addWidget(workflow_desc, 1)
            
            ai_layout.addLayout(workflow_layout)
            
            # Add separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            ai_layout.addWidget(separator)
        
        ai_layout.addStretch()
        ai_widget.setWidget(ai_content)
        tabs.addTab(ai_widget, "AI Workflow")
        
        # Add tab widget to main layout
        layout.addWidget(tabs)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a clean, modern look
    
    # Check if system tray is available with toast instead of alert
    if not QSystemTrayIcon.isSystemTrayAvailable():
        window = VersionDivingApp()
        window.show()
        window.show_toast("System tray is not available. The application will not minimize to the system tray.", 5000)
    else:
        window = VersionDivingApp()
        window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
