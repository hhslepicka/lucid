from unittest.mock import Mock

import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDockWidget, QWidget

from lucid import LucidMainWindow


def test_add_multiple_docks(main_window, qtbot):
    first_dock = QDockWidget()
    second_dock = QDockWidget()
    for dock in (first_dock, second_dock):
        qtbot.addWidget(dock)
    main_window.addDockWidget(Qt.RightDockWidgetArea, first_dock)
    assert main_window.dockWidgetArea(first_dock) == Qt.RightDockWidgetArea
    assert first_dock in main_window._docks
    main_window.addDockWidget(Qt.RightDockWidgetArea, second_dock)
    assert main_window.dockWidgetArea(first_dock) == Qt.RightDockWidgetArea
    assert main_window.dockWidgetArea(second_dock) == Qt.RightDockWidgetArea


def test_main_window_find_window(main_window, qtbot):
    widget = QWidget()
    qtbot.addWidget(widget)
    dock = QDockWidget()
    qtbot.addWidget(dock)
    dock.setWidget(widget)
    main_window.addDockWidget(Qt.RightDockWidgetArea, dock)
    assert LucidMainWindow.find_window(widget) == main_window


def test_main_window_find_window_with_orphan(qtbot):
    widget = QWidget()
    qtbot.addWidget(widget)
    with pytest.raises(EnvironmentError):
        LucidMainWindow.find_window(widget)


def test_main_window_in_dock_no_args(main_window, qtbot):

    @LucidMainWindow.in_dock
    def create_widget():
        widget = QWidget(parent=main_window)
        qtbot.addWidget(widget)
        return widget

    create_widget()
    assert len(main_window._docks) == 1


def test_main_window_in_dock(main_window, qtbot):
    title = 'Test Dock'

    @LucidMainWindow.in_dock(area=Qt.RightDockWidgetArea,
                             title=title)
    def create_widget():
        widget = QWidget(parent=main_window)
        qtbot.addWidget(widget)
        return widget

    create_widget()
    assert len(main_window._docks) == 1
    assert main_window._docks[0].windowTitle() == title


def test_main_window_in_dock_with_orphan(qtbot):

    @LucidMainWindow.in_dock
    def create_widget():
        widget = QWidget()
        qtbot.addWidget(widget)
        return widget

    widget = create_widget()
    assert widget.isVisible()


def test_main_window_in_dock_repeat(main_window, qtbot):
    # Function to create show QWidget
    widget = QWidget(parent=main_window)
    qtbot.addWidget(widget)
    create_widget = LucidMainWindow.in_dock(lambda: widget)
    # Show widget once
    create_widget()
    dock = widget.parent()
    create_widget()
    assert dock == widget.parent()


def test_main_window_in_dock_active_slot(main_window, qtbot):
    with qtbot.wait_exposed(main_window):
        main_window.show()
    # Function to create show QWidget
    widget = QWidget(parent=main_window)
    qtbot.addWidget(widget)
    cb = Mock()
    create_widget = LucidMainWindow.in_dock(func=lambda:
                                            widget, active_slot=cb)
    create_widget()
    assert cb.called
    cb.assert_called_with(True)
    with qtbot.waitSignal(widget.parent().stateChanged):
        widget.parent().close()
    cb.assert_called_with(False)


@pytest.mark.parametrize('start_floating,close,finish_floating',
                         ((False, False, False),
                          (False, True, False),
                          (True, False, True),
                          (True, False, True)),
                         ids=('in tab', 'closed from tab',
                              'floating', 'closed from floating'))
def test_main_window_raise(main_window, qtbot,
                           start_floating, close, finish_floating):
    # Add our docks
    dock1 = QDockWidget()
    qtbot.addWidget(dock1)
    dock2 = QDockWidget()
    qtbot.addWidget(dock2)
    main_window.addDockWidget(Qt.RightDockWidgetArea, dock1)
    main_window.addDockWidget(Qt.RightDockWidgetArea, dock2)
    # Setup dock
    dock1.setFloating(start_floating)
    if close:
        dock1.close()
    # Re-raise
    main_window.raise_dock(dock1)
    assert dock1.isFloating() == finish_floating
    if not finish_floating:
        assert main_window.tabifiedDockWidgets(dock2) == [dock1]
