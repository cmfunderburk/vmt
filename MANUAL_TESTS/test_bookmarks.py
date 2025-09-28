#!/usr/bin/env python3
"""
Test Bookmarking System for VMT Framework
=========================================

Professional bookmark management system for saving, organizing, and launching
favorite test configurations. Supports categories, search, import/export, and
quick launch capabilities for educational and research workflows.

Features:
- Save/organize favorite configurations with custom names and descriptions
- Category system for logical grouping (Educational, Research, Custom, etc.)
- Search and filter bookmarks by name, description, or parameters
- Import/export bookmarks for sharing between users/installations
- Quick launch directly from bookmark list
- Integration with Enhanced Test Launcher and Configuration Editor

Usage:
    python test_bookmarks.py
    # Or via Enhanced Test Launcher -> Bookmarks tab
"""

import sys
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set
from datetime import datetime
import subprocess

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
        QListWidget, QListWidgetItem, QGroupBox, QSplitter,
        QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox,
        QDialog, QDialogButtonBox, QFormLayout, QCheckBox,
        QTabWidget, QScrollArea, QFrame, QMenu, QFileDialog,
        QInputDialog
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QAction, QIcon
except ImportError as e:
    print(f"❌ PyQt6 import failed: {e}")
    print("Please ensure PyQt6 is installed in your virtual environment.")
    sys.exit(1)

try:
    # Try new framework location first
    import os
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(repo_root, "src"))
    from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS, TestConfiguration
except ImportError:
    try:
        # Fallback to old location (legacy)
        from MANUAL_TESTS.framework.test_configs import ALL_TEST_CONFIGS, TestConfiguration
    except ImportError:
        print("❌ Framework import failed. Please ensure framework is properly installed.")
        sys.exit(1)


@dataclass
class TestBookmark:
    """Represents a saved test configuration bookmark."""
    id: str
    name: str
    description: str
    category: str
    config: TestConfiguration
    created_date: datetime
    last_used: Optional[datetime] = None
    use_count: int = 0
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TestBookmark':
        """Create bookmark from dictionary."""
        # Handle datetime fields
        created_date = datetime.fromisoformat(data['created_date'])
        last_used = None
        if data.get('last_used'):
            last_used = datetime.fromisoformat(data['last_used'])
        
        # Create TestConfiguration from dict
        config_data = data['config']
        config = TestConfiguration(**config_data)
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            category=data['category'],
            config=config,
            created_date=created_date,
            last_used=last_used,
            use_count=data.get('use_count', 0),
            tags=data.get('tags', [])
        )
    
    def to_dict(self) -> dict:
        """Convert bookmark to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'config': asdict(self.config),
            'created_date': self.created_date.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'use_count': self.use_count,
            'tags': self.tags
        }


class BookmarkManager:
    """Manages bookmark storage and operations."""
    
    def __init__(self, bookmarks_file: str = "test_bookmarks.json"):
        self.bookmarks_file = Path(__file__).parent / bookmarks_file
        self.bookmarks: Dict[str, TestBookmark] = {}
        self.categories: Set[str] = {
            "Educational", "Research", "Custom", "Experiments", "Favorites"
        }
        self.load_bookmarks()
    
    def add_bookmark(self, bookmark: TestBookmark) -> bool:
        """Add a new bookmark."""
        if bookmark.id in self.bookmarks:
            return False
        
        self.bookmarks[bookmark.id] = bookmark
        self.categories.add(bookmark.category)
        self.save_bookmarks()
        return True
    
    def update_bookmark(self, bookmark: TestBookmark) -> bool:
        """Update existing bookmark."""
        if bookmark.id not in self.bookmarks:
            return False
        
        self.bookmarks[bookmark.id] = bookmark
        self.categories.add(bookmark.category)
        self.save_bookmarks()
        return True
    
    def delete_bookmark(self, bookmark_id: str) -> bool:
        """Delete a bookmark."""
        if bookmark_id not in self.bookmarks:
            return False
        
        del self.bookmarks[bookmark_id]
        self.save_bookmarks()
        return True
    
    def get_bookmark(self, bookmark_id: str) -> Optional[TestBookmark]:
        """Get bookmark by ID."""
        return self.bookmarks.get(bookmark_id)
    
    def get_bookmarks_by_category(self, category: str) -> List[TestBookmark]:
        """Get all bookmarks in a category."""
        return [bookmark for bookmark in self.bookmarks.values() 
                if bookmark.category == category]
    
    def search_bookmarks(self, query: str) -> List[TestBookmark]:
        """Search bookmarks by name, description, or tags."""
        query = query.lower()
        results = []
        
        for bookmark in self.bookmarks.values():
            tags_match = bookmark.tags and any(query in tag.lower() for tag in bookmark.tags)
            if (query in bookmark.name.lower() or 
                query in bookmark.description.lower() or
                tags_match):
                results.append(bookmark)
        
        return results
    
    def record_bookmark_use(self, bookmark_id: str):
        """Record bookmark usage for statistics."""
        if bookmark_id in self.bookmarks:
            bookmark = self.bookmarks[bookmark_id]
            bookmark.use_count += 1
            bookmark.last_used = datetime.now()
            self.save_bookmarks()
    
    def get_most_used_bookmarks(self, limit: int = 5) -> List[TestBookmark]:
        """Get most frequently used bookmarks."""
        return sorted(self.bookmarks.values(), 
                     key=lambda b: b.use_count, reverse=True)[:limit]
    
    def get_recent_bookmarks(self, limit: int = 5) -> List[TestBookmark]:
        """Get recently used bookmarks."""
        recent = [b for b in self.bookmarks.values() if b.last_used]
        return sorted(recent, key=lambda b: b.last_used, reverse=True)[:limit]
    
    def export_bookmarks(self, filename: str) -> bool:
        """Export bookmarks to file."""
        try:
            export_data = {
                'exported_date': datetime.now().isoformat(),
                'bookmarks': [bookmark.to_dict() for bookmark in self.bookmarks.values()],
                'categories': list(self.categories)
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def import_bookmarks(self, filename: str, merge: bool = True) -> bool:
        """Import bookmarks from file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            if not merge:
                self.bookmarks.clear()
                self.categories = {"Educational", "Research", "Custom", "Experiments", "Favorites"}
            
            for bookmark_data in data['bookmarks']:
                bookmark = TestBookmark.from_dict(bookmark_data)
                self.bookmarks[bookmark.id] = bookmark
                self.categories.add(bookmark.category)
            
            # Add imported categories
            if 'categories' in data:
                self.categories.update(data['categories'])
            
            self.save_bookmarks()
            return True
        except Exception as e:
            print(f"Import failed: {e}")
            return False
    
    def load_bookmarks(self):
        """Load bookmarks from file."""
        if not self.bookmarks_file.exists():
            return
        
        try:
            with open(self.bookmarks_file, 'r') as f:
                data = json.load(f)
            
            for bookmark_data in data.get('bookmarks', []):
                bookmark = TestBookmark.from_dict(bookmark_data)
                self.bookmarks[bookmark.id] = bookmark
            
            if 'categories' in data:
                self.categories.update(data['categories'])
                
        except Exception as e:
            print(f"Failed to load bookmarks: {e}")
    
    def save_bookmarks(self):
        """Save bookmarks to file."""
        try:
            data = {
                'version': '1.0',
                'saved_date': datetime.now().isoformat(),
                'bookmarks': [bookmark.to_dict() for bookmark in self.bookmarks.values()],
                'categories': list(self.categories)
            }
            
            with open(self.bookmarks_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save bookmarks: {e}")


class BookmarkDialog(QDialog):
    """Dialog for creating/editing bookmarks."""
    
    def __init__(self, config: TestConfiguration, bookmark: Optional[TestBookmark] = None, 
                 categories: Set[str] = None):
        super().__init__()
        self.config = config
        self.bookmark = bookmark
        self.categories = categories or set()
        self.init_ui()
        
        if bookmark:
            self.load_bookmark_data()
    
    def init_ui(self):
        self.setWindowTitle("Bookmark Configuration")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Form for bookmark details
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter bookmark name...")
        form_layout.addRow("Name:", self.name_edit)
        
        # Category field
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(sorted(self.categories))
        form_layout.addRow("Category:", self.category_combo)
        
        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Enter description...")
        form_layout.addRow("Description:", self.description_edit)
        
        # Tags field
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Enter tags separated by commas...")
        form_layout.addRow("Tags:", self.tags_edit)
        
        layout.addLayout(form_layout)
        
        # Configuration preview
        config_group = QGroupBox("Configuration Preview")
        config_layout = QVBoxLayout(config_group)
        
        config_text = f"""
Test ID: {self.config.test_id}
Description: {self.config.description}
Grid Size: {self.config.grid_width}x{self.config.grid_height}
Agent Count: {self.config.agent_count}
Resource Density: {self.config.resource_density:.2f}
Perception Radius: {self.config.perception_radius}
Distance Scaling: {self.config.distance_scaling_k:.1f}
        """.strip()
        
        config_label = QLabel(config_text)
        config_label.setStyleSheet("background-color: #f8f9fa; padding: 10px; border: 1px solid #ddd;")
        config_layout.addWidget(config_label)
        
        layout.addWidget(config_group)
        
        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Validation
        self.name_edit.textChanged.connect(self.validate_form)
        self.validate_form()
    
    def load_bookmark_data(self):
        """Load data from existing bookmark."""
        self.name_edit.setText(self.bookmark.name)
        self.category_combo.setCurrentText(self.bookmark.category)
        self.description_edit.setPlainText(self.bookmark.description)
        self.tags_edit.setText(", ".join(self.bookmark.tags or []))
    
    def validate_form(self):
        """Validate form and enable/disable OK button."""
        valid = bool(self.name_edit.text().strip())
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(valid)
    
    def get_bookmark(self) -> TestBookmark:
        """Create bookmark from form data."""
        bookmark_id = self.bookmark.id if self.bookmark else f"bm_{int(datetime.now().timestamp())}"
        
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
        
        return TestBookmark(
            id=bookmark_id,
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText().strip(),
            category=self.category_combo.currentText().strip(),
            config=self.config,
            created_date=self.bookmark.created_date if self.bookmark else datetime.now(),
            last_used=self.bookmark.last_used if self.bookmark else None,
            use_count=self.bookmark.use_count if self.bookmark else 0,
            tags=tags
        )


class BookmarkTreeWidget(QTreeWidget):
    """Custom tree widget for displaying bookmarks by category."""
    
    bookmarkSelected = pyqtSignal(TestBookmark)
    bookmarkLaunched = pyqtSignal(TestBookmark)
    bookmarkEdit = pyqtSignal(TestBookmark)
    bookmarkDelete = pyqtSignal(TestBookmark)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.bookmark_items = {}  # Map bookmark_id -> QTreeWidgetItem
    
    def init_ui(self):
        self.setHeaderLabels(["Name", "Description", "Last Used", "Uses"])
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        
        # Configure columns
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Double-click to launch
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def populate_bookmarks(self, bookmarks: List[TestBookmark]):
        """Populate tree with bookmarks organized by category."""
        self.clear()
        self.bookmark_items.clear()
        
        # Group bookmarks by category
        categories = {}
        for bookmark in bookmarks:
            if bookmark.category not in categories:
                categories[bookmark.category] = []
            categories[bookmark.category].append(bookmark)
        
        # Create category nodes
        for category, category_bookmarks in sorted(categories.items()):
            category_item = QTreeWidgetItem([category, f"{len(category_bookmarks)} bookmarks", "", ""])
            category_item.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
            self.addTopLevelItem(category_item)
            
            # Add bookmarks to category
            for bookmark in sorted(category_bookmarks, key=lambda b: b.name.lower()):
                last_used = bookmark.last_used.strftime("%Y-%m-%d") if bookmark.last_used else "Never"
                
                bookmark_item = QTreeWidgetItem([
                    bookmark.name,
                    bookmark.description[:50] + "..." if len(bookmark.description) > 50 else bookmark.description,
                    last_used,
                    str(bookmark.use_count)
                ])
                
                bookmark_item.setData(0, Qt.ItemDataRole.UserRole, bookmark.id)
                category_item.addChild(bookmark_item)
                self.bookmark_items[bookmark.id] = bookmark_item
        
        # Expand all categories
        self.expandAll()
    
    def get_selected_bookmark_id(self) -> Optional[str]:
        """Get ID of currently selected bookmark."""
        current = self.currentItem()
        if current and current.parent():  # It's a bookmark item, not category
            return current.data(0, Qt.ItemDataRole.UserRole)
        return None
    
    def on_selection_changed(self):
        """Handle selection changes."""
        bookmark_id = self.get_selected_bookmark_id()
        if bookmark_id:
            # Emit signal with bookmark data (you'd need to pass manager reference)
            pass
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click to launch bookmark."""
        if item.parent():  # It's a bookmark item
            bookmark_id = item.data(0, Qt.ItemDataRole.UserRole)
            if bookmark_id:
                # Emit launch signal
                pass
    
    def show_context_menu(self, position):
        """Show context menu for bookmark operations."""
        item = self.itemAt(position)
        if not item or not item.parent():  # Not a bookmark item
            return
        
        bookmark_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not bookmark_id:
            return
        
        menu = QMenu(self)
        
        launch_action = QAction("🚀 Launch Bookmark", self)
        edit_action = QAction("✏️ Edit Bookmark", self)
        delete_action = QAction("🗑️ Delete Bookmark", self)
        
        menu.addAction(launch_action)
        menu.addSeparator()
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        action = menu.exec(self.mapToGlobal(position))
        
        if action == launch_action:
            # Emit launch signal
            pass
        elif action == edit_action:
            # Emit edit signal
            pass
        elif action == delete_action:
            # Emit delete signal
            pass


class TestBookmarkManager(QWidget):
    """Main bookmark management interface."""
    
    bookmarkLaunched = pyqtSignal(TestBookmark)
    
    def __init__(self):
        super().__init__()
        self.bookmark_manager = BookmarkManager()
        self.init_ui()
        self.refresh_bookmarks()
    
    def init_ui(self):
        self.setWindowTitle("VMT Test Bookmark Manager")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Test Bookmark Manager")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search bookmarks...")
        self.search_edit.textChanged.connect(self.search_bookmarks)
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_edit)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentTextChanged.connect(self.filter_by_category)
        toolbar_layout.addWidget(QLabel("Category:"))
        toolbar_layout.addWidget(self.category_filter)
        
        toolbar_layout.addStretch()
        
        # Action buttons
        self.add_btn = QPushButton("➕ Add Bookmark")
        self.import_btn = QPushButton("📁 Import")
        self.export_btn = QPushButton("💾 Export")
        
        self.add_btn.clicked.connect(self.add_bookmark_from_config)
        self.import_btn.clicked.connect(self.import_bookmarks)
        self.export_btn.clicked.connect(self.export_bookmarks)
        
        toolbar_layout.addWidget(self.add_btn)
        toolbar_layout.addWidget(self.import_btn)
        toolbar_layout.addWidget(self.export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Bookmark tree
        tree_widget = QWidget()
        tree_layout = QVBoxLayout(tree_widget)
        
        tree_header = QLabel("Bookmarks")
        tree_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        tree_layout.addWidget(tree_header)
        
        self.bookmark_tree = BookmarkTreeWidget()
        tree_layout.addWidget(self.bookmark_tree)
        
        content_splitter.addWidget(tree_widget)
        
        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        details_header = QLabel("Bookmark Details")
        details_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        details_layout.addWidget(details_header)
        
        self.details_area = QTextEdit()
        self.details_area.setReadOnly(True)
        self.details_area.setMaximumWidth(300)
        details_layout.addWidget(self.details_area)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.launch_btn = QPushButton("🚀 Launch Bookmark")
        self.edit_btn = QPushButton("✏️ Edit Bookmark")
        self.delete_btn = QPushButton("🗑️ Delete Bookmark")
        
        self.launch_btn.clicked.connect(self.launch_selected_bookmark)
        self.edit_btn.clicked.connect(self.edit_selected_bookmark)
        self.delete_btn.clicked.connect(self.delete_selected_bookmark)
        
        # Initially disable action buttons
        self.launch_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        actions_layout.addWidget(self.launch_btn)
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addWidget(self.delete_btn)
        
        details_layout.addWidget(actions_group)
        details_layout.addStretch()
        
        content_splitter.addWidget(details_widget)
        content_splitter.setSizes([600, 300])
        
        layout.addWidget(content_splitter)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        self.total_bookmarks_label = QLabel("Total: 0")
        self.categories_label = QLabel("Categories: 0")
        self.most_used_label = QLabel("Most Used: None")
        
        stats_layout.addWidget(self.total_bookmarks_label)
        stats_layout.addWidget(self.categories_label)
        stats_layout.addWidget(self.most_used_label)
        stats_layout.addStretch()
        
        layout.addWidget(stats_group)
        
        # Connect tree signals
        self.bookmark_tree.itemSelectionChanged.connect(self.on_bookmark_selected)
    
    def refresh_bookmarks(self):
        """Refresh bookmark display."""
        bookmarks = list(self.bookmark_manager.bookmarks.values())
        self.bookmark_tree.populate_bookmarks(bookmarks)
        
        # Update category filter
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        for category in sorted(self.bookmark_manager.categories):
            self.category_filter.addItem(category)
        
        # Update statistics
        self.update_statistics()
    
    def update_statistics(self):
        """Update statistics display."""
        total = len(self.bookmark_manager.bookmarks)
        categories = len(self.bookmark_manager.categories)
        
        most_used = self.bookmark_manager.get_most_used_bookmarks(1)
        most_used_name = most_used[0].name if most_used else "None"
        
        self.total_bookmarks_label.setText(f"Total: {total}")
        self.categories_label.setText(f"Categories: {categories}")
        self.most_used_label.setText(f"Most Used: {most_used_name}")
    
    def on_bookmark_selected(self):
        """Handle bookmark selection."""
        bookmark_id = self.bookmark_tree.get_selected_bookmark_id()
        
        if bookmark_id:
            bookmark = self.bookmark_manager.get_bookmark(bookmark_id)
            if bookmark:
                self.show_bookmark_details(bookmark)
                self.launch_btn.setEnabled(True)
                self.edit_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
                return
        
        # No valid selection
        self.details_area.clear()
        self.launch_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
    
    def show_bookmark_details(self, bookmark: TestBookmark):
        """Show bookmark details in details panel."""
        details = f"""
<h3>{bookmark.name}</h3>
<p><strong>Category:</strong> {bookmark.category}</p>
<p><strong>Description:</strong><br>{bookmark.description}</p>

<h4>Configuration</h4>
<ul>
<li><strong>Test ID:</strong> {bookmark.config.test_id}</li>
<li><strong>Grid Size:</strong> {bookmark.config.grid_width}x{bookmark.config.grid_height}</li>
<li><strong>Agent Count:</strong> {bookmark.config.agent_count}</li>
<li><strong>Resource Density:</strong> {bookmark.config.resource_density:.2f}</li>
<li><strong>Perception Radius:</strong> {bookmark.config.perception_radius}</li>
<li><strong>Distance Scaling:</strong> {bookmark.config.distance_scaling_k:.1f}</li>
</ul>

<h4>Usage Statistics</h4>
<ul>
<li><strong>Created:</strong> {bookmark.created_date.strftime('%Y-%m-%d %H:%M')}</li>
<li><strong>Last Used:</strong> {bookmark.last_used.strftime('%Y-%m-%d %H:%M') if bookmark.last_used else 'Never'}</li>
<li><strong>Use Count:</strong> {bookmark.use_count}</li>
</ul>

<h4>Tags</h4>
<p>{', '.join(bookmark.tags) if bookmark.tags else 'No tags'}</p>
        """.strip()
        
        self.details_area.setHtml(details)
    
    def add_bookmark_from_config(self):
        """Add bookmark from a framework configuration."""
        # For demo, use first config
        configs = list(ALL_TEST_CONFIGS.values())
        if not configs:
            QMessageBox.warning(self, "No Configurations", 
                              "No test configurations available.")
            return
        
        # In real implementation, you'd have a config selector
        config = configs[0]  # Use first config for demo
        
        dialog = BookmarkDialog(config, categories=self.bookmark_manager.categories)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            bookmark = dialog.get_bookmark()
            if self.bookmark_manager.add_bookmark(bookmark):
                self.refresh_bookmarks()
                QMessageBox.information(self, "Success", 
                                      f"Bookmark '{bookmark.name}' added successfully!")
            else:
                QMessageBox.warning(self, "Error", 
                                  "Failed to add bookmark. ID may already exist.")
    
    def launch_selected_bookmark(self):
        """Launch the selected bookmark."""
        bookmark_id = self.bookmark_tree.get_selected_bookmark_id()
        if not bookmark_id:
            return
        
        bookmark = self.bookmark_manager.get_bookmark(bookmark_id)
        if bookmark:
            self.bookmark_manager.record_bookmark_use(bookmark_id)
            self.bookmarkLaunched.emit(bookmark)
            self.refresh_bookmarks()  # Update usage stats
    
    def edit_selected_bookmark(self):
        """Edit the selected bookmark."""
        bookmark_id = self.bookmark_tree.get_selected_bookmark_id()
        if not bookmark_id:
            return
        
        bookmark = self.bookmark_manager.get_bookmark(bookmark_id)
        if not bookmark:
            return
        
        dialog = BookmarkDialog(bookmark.config, bookmark, self.bookmark_manager.categories)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_bookmark = dialog.get_bookmark()
            if self.bookmark_manager.update_bookmark(updated_bookmark):
                self.refresh_bookmarks()
                QMessageBox.information(self, "Success", 
                                      f"Bookmark '{updated_bookmark.name}' updated successfully!")
    
    def delete_selected_bookmark(self):
        """Delete the selected bookmark."""
        bookmark_id = self.bookmark_tree.get_selected_bookmark_id()
        if not bookmark_id:
            return
        
        bookmark = self.bookmark_manager.get_bookmark(bookmark_id)
        if not bookmark:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete bookmark '{bookmark.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.bookmark_manager.delete_bookmark(bookmark_id):
                self.refresh_bookmarks()
                QMessageBox.information(self, "Success", 
                                      f"Bookmark '{bookmark.name}' deleted successfully!")
    
    def search_bookmarks(self):
        """Search bookmarks based on search text."""
        query = self.search_edit.text().strip()
        if query:
            results = self.bookmark_manager.search_bookmarks(query)
        else:
            results = list(self.bookmark_manager.bookmarks.values())
        
        # Apply category filter if active
        category = self.category_filter.currentText()
        if category != "All Categories":
            results = [b for b in results if b.category == category]
        
        self.bookmark_tree.populate_bookmarks(results)
    
    def filter_by_category(self):
        """Filter bookmarks by category."""
        category = self.category_filter.currentText()
        if category == "All Categories":
            results = list(self.bookmark_manager.bookmarks.values())
        else:
            results = self.bookmark_manager.get_bookmarks_by_category(category)
        
        # Apply search filter if active
        query = self.search_edit.text().strip()
        if query:
            results = [b for b in results 
                      if (query.lower() in b.name.lower() or 
                          query.lower() in b.description.lower() or
                          any(query.lower() in tag.lower() for tag in b.tags))]
        
        self.bookmark_tree.populate_bookmarks(results)
    
    def import_bookmarks(self):
        """Import bookmarks from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Bookmarks", "", "JSON Files (*.json)"
        )
        
        if not filename:
            return
        
        reply = QMessageBox.question(
            self, "Import Method",
            "How do you want to import bookmarks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        # Yes = merge, No = replace
        merge = reply == QMessageBox.StandardButton.Yes
        
        if self.bookmark_manager.import_bookmarks(filename, merge):
            self.refresh_bookmarks()
            QMessageBox.information(self, "Success", "Bookmarks imported successfully!")
        else:
            QMessageBox.warning(self, "Error", "Failed to import bookmarks.")
    
    def export_bookmarks(self):
        """Export bookmarks to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Bookmarks", "test_bookmarks_export.json", 
            "JSON Files (*.json)"
        )
        
        if not filename:
            return
        
        if self.bookmark_manager.export_bookmarks(filename):
            QMessageBox.information(self, "Success", 
                                  f"Bookmarks exported to {filename}")
        else:
            QMessageBox.warning(self, "Error", "Failed to export bookmarks.")


def main():
    """Run the bookmark manager as standalone application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    manager = TestBookmarkManager()
    manager.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()