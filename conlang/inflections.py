#! /usr/bin/env python3.3  # lint:ok


class InflectionTable():

    def __init__(self, rows):
        self.rows = rows
        self.data = {}
        numCells = 0
        for r in rows:
            numCells += len(r)
        for i in range(numCells):
            cell = ()
            for r in rows:
                cell += (r[i % len(r)],)
                i //= len(r)
            self.data[cell] = None

    def parse(self, string):
        return tuple(string.split('.'))

    def setCell(self, rc, *cell):
        if tuple(cell) in self.data:
            self.data[tuple(cell)] = rc
        else:
            self.data[self.parse(cell[0])] = rc

    def getCell(self, *cell):
        if tuple(cell) in self.data:
            return self.data[tuple(cell)]
        else:
            return self.data[self.parse(cell[0])]