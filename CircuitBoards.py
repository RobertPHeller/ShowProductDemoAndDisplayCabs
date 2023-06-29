#*****************************************************************************
#
#  System        : 
#  Module        : 
#  Object Name   : $RCSfile$
#  Revision      : $Revision$
#  Date          : $Date$
#  Author        : $Author$
#  Created By    : Robert Heller
#  Created       : Thu Jun 29 11:48:09 2023
#  Last Modified : <230629.1518>
#
#  Description	
#
#  Notes
#
#  History
#	
#*****************************************************************************
#
#    Copyright (C) 2023  Robert Heller D/B/A Deepwoods Software
#			51 Locke Hill Road
#			Wendell, MA 01379-9728
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# 
#
#*****************************************************************************


import Part
from FreeCAD import Base
import FreeCAD as App

from abc import ABCMeta, abstractmethod, abstractproperty  

import os
import sys
sys.path.append(os.path.dirname(__file__))

class CircuitBoard(object):
    __metaclass__ = ABCMeta
    @abstractproperty
    def Length(self):
        pass
    @abstractproperty
    def Width(self):
        pass
    @property
    def Normal(self):
        return Base.Vector(0,0,1)
    @property
    def Thick(self):
        return 1.5
    @property
    def Extrude(self):
        norm = self.Normal
        return Base.Vector(self.Thick*norm.x,\
                           self.Thick*norm.y,\
                           self.Thick*norm.z)
    @property
    def Color(self):
        return (0.0,1.0,0.0)
    def __init__(self,name,origin):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
        self.origin = origin
        self.board = Part.makePlane(self.Length,self.Width,origin,self.Normal)\
                    .extrude(self.Extrude)
    def show(self,doc=None):
        if doc==None:
            doc = App.activeDocument()
        obj = doc.addObject("Part::Feature",self.name)
        obj.Shape = self.board
        obj.Label = self.name
        obj.ViewObject.ShapeColor=self.Color
        

class BeagleBoneBlack(CircuitBoard):
    @property
    def Length(self):
        return 3.4*25.4
    @property
    def Width(self):
        return 2.15*25.4
    @property
    def Normal(self):
        return Base.Vector(0,1,0)
    @property
    def Color(self):
        return (0.0,0.0,0.0)
    __LCornerRadius__ = .25*25.4
    __LCornerOffset__ = .125*25.4
    __RCornerRadius__ = .5*25.4
    __RCornerOffset__ = .25*25.4
    __MountingHoleDiameter__ = .125*25.4
    __MountingHoles__ = {\
        1: Base.Vector(.125*25.4,0,.575*25.4),\
        2: Base.Vector(2.025*25.4,0,.575*25.4),\
        3: Base.Vector(.25*25.4,0,3.175*25.4),\
        4: Base.Vector(1.9*25.4,0,3.175*25.4)\
    }
    def __init__(self,name,origin):
        CircuitBoard.__init__(self,name,origin)
        corner = Part.makePlane(self.__LCornerRadius__,\
                                self.__LCornerRadius__,\
                          origin.add(Base.Vector(0,\
                                                 0,\
                                                 0)),\
                                self.Normal).extrude(self.Extrude)
        corner = corner.cut(Part.Face(Part.Wire(Part.makeCircle(\
                self.__LCornerRadius__,\
                origin.add(Base.Vector(self.__LCornerRadius__,\
                                       0,\
                                       self.__LCornerRadius__)),\
                self.Normal))).extrude(self.Extrude))
        self.board = self.board.cut(corner)
        corner = Part.makePlane(self.__LCornerRadius__,\
                                self.__LCornerRadius__,\
                                origin.add(Base.Vector(self.Width-self.__LCornerRadius__,\
                                                       0,\
                                                       0)),\
                                self.Normal).extrude(self.Extrude)
        corner = corner.cut(Part.Face(Part.Wire(Part.makeCircle(\
                self.__LCornerRadius__,\
                origin.add(Base.Vector(self.Width-self.__LCornerRadius__,\
                                       0,\
                                       self.__LCornerRadius__)),\
                self.Normal))).extrude(self.Extrude))
        self.board = self.board.cut(corner)

        corner = Part.makePlane(self.__RCornerRadius__,\
                                self.__RCornerRadius__,\
                                origin.add(Base.Vector(0,\
                                                       0,\
                                                       self.Length-self.__RCornerRadius__)),\
                                self.Normal).extrude(self.Extrude)
        corner = corner.cut(Part.Face(Part.Wire(Part.makeCircle(\
                self.__RCornerRadius__,\
                origin.add(Base.Vector(self.__RCornerRadius__,\
                                       0,
                                       self.Length-self.__RCornerRadius__)),self.Normal))).extrude(self.Extrude))
        self.board = self.board.cut(corner)
        corner = Part.makePlane(self.__RCornerRadius__,\
                                self.__RCornerRadius__,\
                                origin.add(Base.Vector(self.Width-self.__RCornerRadius__,\
                                                       0,
                                                       self.Length-self.__RCornerRadius__)),\
                                self.Normal).extrude(self.Extrude)
        corner = corner.cut(Part.Face(Part.Wire(Part.makeCircle(\
                self.__RCornerRadius__,\
                origin.add(Base.Vector(self.Width-self.__RCornerRadius__,\
                                       0,
                                       self.Length-self.__RCornerRadius__\
                                       )),self.Normal))).extrude(self.Extrude))
        self.board = self.board.cut(corner)

        for i in [1,2,3,4]:
            self.board = self.board.cut(self.MountingHole(i,\
                                                          origin.z,self.Thick))

    def MountingHole(self,i,y,depth):
        mho = self.origin.add(self.__MountingHoles__[i])
        mho = Base.Vector(mho.x,y,mho.z)
        return Part.Face(Part.Wire(Part.makeCircle(\
                    self.__MountingHoleDiameter__/2.0,\
                    mho,
                    self.Normal))).extrude(Base.Vector(0,depth,0))

class DemoControlPanel(CircuitBoard):
    @property
    def Length(self):
        return 160
    @property
    def Width(self):
        return 100
    @property
    def Color(self):
        return (.9,.65,0.0)
        
class MultiFunctionUT(CircuitBoard):
    @property
    def Width(self):
        return 125.73
    @property
    def Length(self):
        return 99.06
    @property
    def Normal(self):
        return Base.Vector(0,1,0)

if __name__ == '__main__':
    doc = App.newDocument('test')
    mfunct = MultiFunctionUT('MultiFunct',Base.Vector(0,0,0))
    mfunct.show(doc)
    App.ActiveDocument=doc
    Gui.ActiveDocument=doc
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewFront()
