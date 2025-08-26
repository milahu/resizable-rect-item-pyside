#!/usr/bin/env python3

# based on https://stackoverflow.com/a/34442054/10440128

import sys

from PySide6.QtCore import (
    Qt,
    QRectF,
    QPointF,
)
from PySide6.QtGui import (
    QBrush,
    QPainterPath,
    QPainter,
    QColor,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsRectItem,
    QApplication,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
)


class ResizableRectItem(QGraphicsRectItem):

    handleTopLeft = 0
    handleTopMiddle = 1
    handleTopRight = 2
    handleMiddleLeft = 3
    handleMiddleRight = 4
    handleBottomLeft = 5
    handleBottomMiddle = 6
    handleBottomRight = 7

    handleSize = +8.0
    handleSpace = -4.0

    handleCursors = (
        Qt.SizeFDiagCursor, # handleTopLeft
        Qt.SizeVerCursor, # handleTopMiddle
        Qt.SizeBDiagCursor, # handleTopRight
        Qt.SizeHorCursor, # handleMiddleLeft
        Qt.SizeHorCursor, # handleMiddleRight
        Qt.SizeBDiagCursor, # handleBottomLeft
        Qt.SizeVerCursor, # handleBottomMiddle
        Qt.SizeFDiagCursor, # handleBottomRight
    )

    def __init__(self, *args):
        """
        Initialize the shape.
        """
        super().__init__(*args)
        self.handles = [None] * 8
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.initHandles()
        # Executed when the mouse is being moved over the item while being pressed.
        self.mouseMoveEvent = self.mouseMoveEventCenter
        self.mouseMoveEventByHandle = [
            self.mouseMoveEventTopLeft,
            self.mouseMoveEventTopMiddle,
            self.mouseMoveEventTopRight,
            self.mouseMoveEventMiddleLeft,
            self.mouseMoveEventMiddleRight,
            self.mouseMoveEventBottomLeft,
            self.mouseMoveEventBottomMiddle,
            self.mouseMoveEventBottomRight,
        ]

    def handleAt(self, point):
        """
        Returns the resize handle below the given point.
        """
        for k, v, in enumerate(self.handles):
            if v.contains(point):
                return k
        return None

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        """
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected is not None:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()
            self.mouseMoveEvent = self.mouseMoveEventByHandle[self.handleSelected]
        else:
            self.mouseMoveEvent = self.mouseMoveEventCenter
        super().mousePressEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.update()

    def boundingRect(self):
        """
        Returns the bounding rect of the shape (including the resize handles).
        """
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def initHandles(self):
        """
        Init current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopLeft] = QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTopMiddle] = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTopRight] = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight] = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomLeft] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QRectF(b.right() - s, b.bottom() - s, s, s)

    def updateHandlesPos(self):
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopLeft].setRect(b.left(), b.top(), s, s)
        self.handles[self.handleTopMiddle].setRect(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTopRight].setRect(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft].setRect(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight].setRect(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomLeft].setRect(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle].setRect(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight].setRect(b.right() - s, b.bottom() - s, s, s)

    def mouseMoveEventCenter(self, mouseEvent):
        super().mouseMoveEvent(mouseEvent)

    def mouseMoveEventTopLeft(self, mouseEvent):
        """
        Perform shape interactive resize.
        """
        mousePos = mouseEvent.pos()
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()

        self.prepareGeometryChange()

        fromX = self.mousePressRect.left()
        fromY = self.mousePressRect.top()
        toX = fromX + mousePos.x() - self.mousePressPos.x()
        toY = fromY + mousePos.y() - self.mousePressPos.y()
        boundingRect.setLeft(toX)
        boundingRect.setTop(toY)
        rect.setLeft(boundingRect.left() + offset)
        rect.setTop(boundingRect.top() + offset)
        self.setRect(rect)

        self.updateHandlesPos()

    def mouseMoveEventTopMiddle(self, mouseEvent):
        """
        Perform shape interactive resize.
        """
        mousePos = mouseEvent.pos()
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()

        self.prepareGeometryChange()

        fromY = self.mousePressRect.top()
        toY = fromY + mousePos.y() - self.mousePressPos.y()
        boundingRect.setTop(toY)
        rect.setTop(boundingRect.top() + offset)
        self.setRect(rect)

        self.updateHandlesPos()

    def mouseMoveEventTopRight(self, mouseEvent):
        """
        Perform shape interactive resize.
        """
        mousePos = mouseEvent.pos()
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()

        self.prepareGeometryChange()

        fromX = self.mousePressRect.right()
        fromY = self.mousePressRect.top()
        toX = fromX + mousePos.x() - self.mousePressPos.x()
        toY = fromY + mousePos.y() - self.mousePressPos.y()
        boundingRect.setRight(toX)
        boundingRect.setTop(toY)
        rect.setRight(boundingRect.right() - offset)
        rect.setTop(boundingRect.top() + offset)
        self.setRect(rect)

        self.updateHandlesPos()

    def mouseMoveEventMiddleLeft(self, mouseEvent):
        """
        Perform shape interactive resize.
        """
        mousePos = mouseEvent.pos()
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()

        self.prepareGeometryChange()

        fromX = self.mousePressRect.left()
        toX = fromX + mousePos.x() - self.mousePressPos.x()
        boundingRect.setLeft(toX)
        rect.setLeft(boundingRect.left() + offset)
        self.setRect(rect)

        self.updateHandlesPos()

    def mouseMoveEventMiddleRight(self, mouseEvent):
        """
        Perform shape interactive resize.
        """
        mousePos = mouseEvent.pos()
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()

        self.prepareGeometryChange()

        fromX = self.mousePressRect.right()
        toX = fromX + mousePos.x() - self.mousePressPos.x()
        boundingRect.setRight(toX)
        rect.setRight(boundingRect.right() - offset)
        self.setRect(rect)

        self.updateHandlesPos()

    def mouseMoveEventBottomLeft(self, mouseEvent):
        """
        Perform shape interactive resize.
        """
        mousePos = mouseEvent.pos()
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()

        self.prepareGeometryChange()

        fromX = self.mousePressRect.left()
        fromY = self.mousePressRect.bottom()
        toX = fromX + mousePos.x() - self.mousePressPos.x()
        toY = fromY + mousePos.y() - self.mousePressPos.y()
        boundingRect.setLeft(toX)
        boundingRect.setBottom(toY)
        rect.setLeft(boundingRect.left() + offset)
        rect.setBottom(boundingRect.bottom() - offset)
        self.setRect(rect)

        self.updateHandlesPos()

    def mouseMoveEventBottomMiddle(self, mouseEvent):
        """
        Perform shape interactive resize.
        """
        mousePos = mouseEvent.pos()
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()

        self.prepareGeometryChange()

        fromY = self.mousePressRect.bottom()
        toY = fromY + mousePos.y() - self.mousePressPos.y()
        boundingRect.setBottom(toY)
        rect.setBottom(boundingRect.bottom() - offset)
        self.setRect(rect)

        self.updateHandlesPos()

    def mouseMoveEventBottomRight(self, mouseEvent):
        """
        Perform shape interactive resize.
        """
        mousePos = mouseEvent.pos()
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()

        self.prepareGeometryChange()

        fromX = self.mousePressRect.right()
        fromY = self.mousePressRect.bottom()
        toX = fromX + mousePos.x() - self.mousePressPos.x()
        toY = fromY + mousePos.y() - self.mousePressPos.y()
        boundingRect.setRight(toX)
        boundingRect.setBottom(toY)
        rect.setRight(boundingRect.right() - offset)
        rect.setBottom(boundingRect.bottom() - offset)
        self.setRect(rect)

        self.updateHandlesPos()

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        """
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles:
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        """
        painter.setBrush(QBrush(QColor(255, 0, 0, 100)))
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.drawRect(self.rect())

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 0, 0, 255)))
        painter.setPen(QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for handle, rect in enumerate(self.handles):
            if self.handleSelected is None or handle == self.handleSelected:
                painter.drawEllipse(rect)


def main():

    app = QApplication(sys.argv)

    grview = QGraphicsView()
    scene = QGraphicsScene()
    scene.setSceneRect(0, 0, 680, 459)

    scene.addPixmap(QPixmap('qt.png'))
    grview.setScene(scene)

    item = ResizableRectItem(0, 0, 300, 150)
    scene.addItem(item)

    grview.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
    grview.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
