#*****************************************************************************
#
#  System        : 
#  Module        : 
#  Object Name   : $RCSfile$
#  Revision      : $Revision$
#  Date          : $Date$
#  Author        : $Author$
#  Created By    : Robert Heller
#  Created       : Fri Jun 16 14:40:12 2023
#  Last Modified : <230621.1354>
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

class Material(object):
    __instances__ = list()
    def __init__(self,name,*attributes):
        self.name=name
        self.__count__ = 1
        self.attrs=dict()
        for a in attributes:
            key,val = (a.split('='))
            self.attrs[key] = val
        Material.__instances__.append(self)
    def __match__(self,name,*attributes):
        if self.name != name:
            return False
        if len(attributes) != len(self.attrs):
            return False
        for a in attributes:
            key,val = (a.split('='))
            if key in self.attrs:
                if self.attrs[key] != val:
                    return False
            else:
                return False
        return True
    @classmethod
    def AddMaterial(cls,name,*attributes):
        for i in cls.__instances__:
            if i.__match__(name,*attributes):
                i.__count__ = i.__count__+1
                return i
        Material(name,*attributes)
    @classmethod
    def BOM(cls,filename):
        fp = open(filename,"w")
        cls.__instances__.sort(key=lambda m: m.name)
        for i in cls.__instances__:
            i.output(fp)
        fp.close()
    def output(self,fp):
        fp.write("%d,%s"%(self.__count__,self.name))
        for k in self.attrs:
            fp.write(",%s=%s"%(k,self.attrs[k]))
        fp.write("\n")
        

class ProductDisplay(object):
    _OuterWidth  = 3*12
    _OuterHeight = 3*12
    _BackODepth  = 7
    _LidODepth   = 2
    _PlyThick    = 3.0/8.0
    _BoardThick  = 3.0/4.0
    _woodColor   = tuple([210/255.0,180/255.0,140/255.0])
    _pegthick    = 1.0/8.0
    _pegholedia  = 3.0/16.0
    _pegholespace = 1
    _pegboardColor = tuple([139/255.0,35/255.0,35/255.0])
    def __init__(self,name,origin):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
        self.origin = origin
        YNorm = Base.Vector(0,1,0)
        BackExtrude = Base.Vector(0,self._PlyThick,0)
        self.back   = Part.makePlane(self._OuterWidth,self._OuterHeight,\
                                     origin,YNorm).extrude(BackExtrude)
        Material.AddMaterial("plywood","thick=3/8",\
                             "width=%f"%self._OuterWidth,\
                             "length=%f"%self._OuterHeight)
        #
        XNormL = Base.Vector(-1,0,0)
        XNormR = Base.Vector(1,0,0)
        LeftExtrude = Base.Vector(-self._BoardThick,0,0)
        RightExtrude = Base.Vector(self._BoardThick,0,0)
        self.left = Part.makePlane(self._OuterHeight,\
                                   self._BackODepth-self._PlyThick,\
                                   origin.add(Base.Vector(self._BoardThick,self._BackODepth,self._OuterHeight)),XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BackODepth-self._PlyThick),\
                             "length=%f"%(self._OuterHeight))
        self.leftPegB = Part.makePlane(self._OuterHeight-(2*self._BoardThick),\
                                       1,
                                       origin.add(Base.Vector(self._BoardThick*2,self._PlyThick+1,self._OuterHeight-self._BoardThick)),XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4","width=1",\
                             "length=%f"%(self._OuterHeight-(2*self._BoardThick)))
        self.right = Part.makePlane(self._OuterHeight,\
                                    self._BackODepth-self._PlyThick,\
                                    origin.add(Base.Vector(self._OuterWidth-self._BoardThick,self._BackODepth,0)),XNormR).extrude(RightExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BackODepth-self._PlyThick),\
                             "length=%f"%(self._OuterHeight))
        self.rightPegB = Part.makePlane(self._OuterHeight-(2*self._BoardThick),\
                                    1,\
                                    origin.add(Base.Vector(self._OuterWidth-(self._BoardThick*2),self._PlyThick+1,self._BoardThick)),XNormR).extrude(RightExtrude)
        Material.AddMaterial("pine","thick=3/4","width=1",\
                             "length=%f"%(self._OuterHeight-(2*self._BoardThick)))
        #
        ZNormB = Base.Vector(0,0,1)
        ZNormT = Base.Vector(0,0,-1)
        BottomExtrude = Base.Vector(0,0,self._BoardThick)
        TopExtrude = Base.Vector(0,0,-self._BoardThick)
        self.bottom = Part.makePlane(self._OuterWidth-(2*self._BoardThick),\
                                     self._BackODepth-self._PlyThick,\
                                     origin.add(Base.Vector(self._BoardThick,self._PlyThick,0)),ZNormB).extrude(BottomExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BackODepth-self._PlyThick),\
                             "length=%f"%(self._OuterWidth-(2*self._BoardThick)))
        self.bottomPegB = Part.makePlane(self._OuterWidth-(4*self._BoardThick),\
                                     1,\
                                     origin.add(Base.Vector(self._BoardThick*2,self._PlyThick,self._BoardThick)),ZNormB).extrude(BottomExtrude)
        Material.AddMaterial("pine","thick=3/4","width=1",\
                             "length=%f"%(self._OuterWidth-(4*self._BoardThick)))
        self.top = Part.makePlane(self._OuterWidth-(2*self._BoardThick),\
                                     self._BackODepth-self._PlyThick,\
                                     origin.add(Base.Vector(self._BoardThick,self._PlyThick,self._OuterHeight)),ZNormB).extrude(TopExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BackODepth-self._PlyThick),\
                             "length=%f"%(self._OuterWidth-(2*self._BoardThick)))
        self.topPegB = Part.makePlane(self._OuterWidth-(4*self._BoardThick),\
                                     1,\
                                     origin.add(Base.Vector(self._BoardThick*2,self._PlyThick,self._OuterHeight-self._BoardThick)),ZNormB).extrude(TopExtrude)
        Material.AddMaterial("pine","thick=3/4","width=1",\
                             "length=%f"%(self._OuterWidth-(4*self._BoardThick)))
        self.pegboard = self.__pegboard(self._OuterWidth-(2*self._BoardThick),\
                                        self._OuterHeight-(2*self._BoardThick),\
                                        origin.add(Base.Vector(self._BoardThick,1+self._PlyThick,self._BoardThick)))
        Material.AddMaterial("pegboard","thick=1/8",\
                             "width=%f"%(self._OuterWidth-(2*self._BoardThick)),\
                             "length=%f"%(self._OuterHeight-(2*self._BoardThick)))
        self.lid = Part.makePlane(self._OuterWidth,self._OuterHeight,\
                                  origin.add(Base.Vector(0, \
                                                         self._BackODepth+self._LidODepth-self._PlyThick,0)),YNorm).extrude(BackExtrude)
        Material.AddMaterial("plywood","thick=3/8",\
                             "width=%f"%self._OuterWidth,\
                             "length=%f"%self._OuterHeight)
        self.left_lid = Part.makePlane(self._OuterHeight,\
                                       self._LidODepth-self._PlyThick,\
                                       origin.add(Base.Vector(self._BoardThick, \
                                                              self._BackODepth+self._LidODepth-self._PlyThick,self._OuterHeight)),\
                                       XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._LidODepth-self._PlyThick),\
                             "length=%f"%(self._OuterHeight))
        self.right_lid = Part.makePlane(self._OuterHeight,\
                                    self._LidODepth-self._PlyThick,\
                                    origin.add(Base.Vector(self._OuterWidth-self._BoardThick,\
                                    self._BackODepth+self._LidODepth-self._PlyThick,0)),XNormR).extrude(RightExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._LidODepth-self._PlyThick),\
                             "length=%f"%(self._OuterHeight))
        self.bottom_lid = Part.makePlane(self._OuterWidth-(2*self._BoardThick),\
                                     self._LidODepth-self._PlyThick,\
                                     origin.add(Base.Vector(self._BoardThick,\
                                     self._BackODepth,0)),ZNormB).extrude(BottomExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._LidODepth-self._PlyThick),\
                             "length=%f"%(self._OuterWidth-(2*self._BoardThick)))
        self.top_lid = Part.makePlane(self._OuterWidth-(2*self._BoardThick),\
                                     self._LidODepth-self._PlyThick,\
                                     origin.add(Base.Vector(self._BoardThick,\
                                     self._BackODepth,self._OuterHeight)),ZNormB).extrude(TopExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._LidODepth-self._PlyThick),\
                             "length=%f"%(self._OuterWidth-(2*self._BoardThick)))
    def __pegboard(self,width,height,o=Base.Vector(0,0,0)):
        pextrude=Base.Vector(0,self._pegthick,0)
        n = Base.Vector(0,1,0)
        peg = Part.makePlane(width,height,o,n).extrude(pextrude)
        return peg
        hole_y = 1
        while hole_y < height:
            #sys.__stderr__.write("*** ProductDisplay.__pegboard(): hole_y = %f\n"%(hole_y))
            hole_x = 1
            while hole_x < width:
                #sys.__stderr__.write("*** ProductDisplay.__pegboard(): hole_x = %f\n"%(hole_x))
                hole_o = o.add(Base.Vector(hole_x,0,hole_y))
                hole = Part.Face(Part.Wire(Part.makeCircle(self._pegholedia/2.0,hole_o,n))).extrude(pextrude)
                peg = peg.cut(hole)
                hole_x = hole_x + self._pegholespace
            hole_y = hole_y + self._pegholespace
        return peg
    def show(self,doc=None):
        if doc==None:
            doc = App.activeDocument()
        obj = doc.addObject("Part::Feature",self.name+"_back")
        obj.Shape = self.back
        obj.Label = self.name+"_back"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_left")
        obj.Shape = self.left
        obj.Label = self.name+"_left"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_leftPegB")
        obj.Shape = self.leftPegB
        obj.Label = self.name+"_leftPegB"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_right")
        obj.Shape = self.right
        obj.Label = self.name+"_right"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_rightPegB")
        obj.Shape = self.rightPegB
        obj.Label = self.name+"_rightPegB"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_bottom")
        obj.Shape = self.bottom
        obj.Label = self.name+"_bottom"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_bottomPegB")
        obj.Shape = self.bottomPegB
        obj.Label = self.name+"_bottomPegB"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_top")
        obj.Shape = self.top
        obj.Label = self.name+"_top"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_topPegB")
        obj.Shape = self.topPegB
        obj.Label = self.name+"_topPegB"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_pegboard")
        obj.Shape = self.pegboard
        obj.Label = self.name+"_pegboard"
        obj.ViewObject.ShapeColor=self._pegboardColor
        obj = doc.addObject("Part::Feature",self.name+"_lid")
        obj.Shape = self.lid
        obj.Label = self.name+"_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_left_lid")
        obj.Shape = self.left_lid
        obj.Label = self.name+"_left_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_right_lid")
        obj.Shape = self.right_lid
        obj.Label = self.name+"_right_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_bottom_lid")
        obj.Shape = self.bottom_lid
        obj.Label = self.name+"_bottom_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_top_lid")
        obj.Shape = self.top_lid
        obj.Label = self.name+"_top_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        
class YardDemo(object):
    _OuterWidth  = 12
    _OuterLength = 3*12
    _BaseHeight  = 6.25
    _LexanHeight = 2
    _PlyThick    = 1.0/4.0
    _LexanThick  = 1.0/8.0
    _BoardThick  = 3.0/4.0
    _woodColor   = tuple([210/255.0,180/255.0,140/255.0])
    _lexColor    = tuple([1.0,1.0,1.0])
    def __init__(self,name,origin):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
        ZNorm = Base.Vector(0,0,1)
        PlyExtrude = Base.Vector(0,0,self._PlyThick)
        self.layoutbase = Part.makePlane(self._OuterLength,self._OuterWidth,\
                                         origin.add(Base.Vector(0,0,\
                                                                self._BaseHeight-self._PlyThick)),\
                                         ZNorm).extrude(PlyExtrude)
        Material.AddMaterial("birch plywood","thick=1/4",
                             "width=%f"%self._OuterWidth,\
                             "length=%f"%self._OuterLength)
        YNormF = Base.Vector(0,1,0)
        YNormB = Base.Vector(0,-1,0)
        FrontExtrude = Base.Vector(0,self._BoardThick,0)
        BackExtrude = Base.Vector(0,-self._BoardThick,0)
        self.front = Part.makePlane(self._BaseHeight-self._PlyThick,\
                                    self._OuterLength,\
                                    origin,YNormF).extrude(FrontExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BaseHeight-self._PlyThick),\
                             "length=%f"%self._OuterLength)
        self.back = Part.makePlane(self._BaseHeight-self._PlyThick,self._OuterLength,\
                                    origin.add(Base.Vector(0,self._OuterWidth,self._BaseHeight-self._PlyThick)),YNormB).extrude(BackExtrude)
        x = self._BaseHeight-self._PlyThick
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(x),\
                             "length=%f"%self._OuterLength)
        XNormL = Base.Vector(-1,0,0)
        XNormR = Base.Vector(1,0,0)
        LeftExtrude = Base.Vector(-self._BoardThick,0,0)
        RightExtrude = Base.Vector(self._BoardThick,0,0)
        self.left = Part.makePlane(self._BaseHeight-self._PlyThick,\
                                   self._OuterWidth-(2*self._BoardThick),\
                                   origin.add(Base.Vector(self._BoardThick,self._OuterWidth-self._BoardThick,self._BaseHeight-self._PlyThick)),\
                                   XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BaseHeight-self._PlyThick),\
                             "length=%f"%(self._OuterWidth-(2*self._BoardThick)))
        self.right = Part.makePlane(self._BaseHeight-self._PlyThick,\
                                   self._OuterWidth-(2*self._BoardThick),\
                                   origin.add(Base.Vector(self._OuterLength,self._OuterWidth-self._BoardThick,self._BaseHeight-self._PlyThick)),\
                                   XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BaseHeight-self._PlyThick),\
                             "length=%f"%(self._OuterWidth-(2*self._BoardThick)))
        LexFrontExtrude = Base.Vector(0,self._LexanThick,0)
        LexBackExtrude = Base.Vector(0,-self._LexanThick,0)
        self.lexfront = Part.makePlane(self._LexanHeight,\
                                       self._OuterLength,\
                                       origin.add(Base.Vector(0,0,\
                                       self._BaseHeight)),\
                                       YNormF).extrude(LexFrontExtrude)
        Material.AddMaterial("lexan","thick=1/8",\
                             "width=%f"%self._LexanHeight,\
                             "length=%f"%self._OuterLength)
        self.lexback = Part.makePlane(self._LexanHeight,\
                                       self._OuterLength,\
                                       origin.add(Base.Vector(0,self._OuterWidth-self._LexanThick,\
                                       self._BaseHeight+self._LexanHeight)),\
                                       YNormB).extrude(LexFrontExtrude)
        Material.AddMaterial("lexan","thick=1/8",\
                             "width=%f"%self._LexanHeight,\
                             "length=%f"%self._OuterLength)
        LexLeftExtrude = Base.Vector(-self._LexanThick,0,0)
        LexRightExtrude = Base.Vector(self._LexanThick,0,0)
        self.lexleft = Part.makePlane(self._LexanHeight,\
                                   self._OuterWidth-(2*self._LexanThick),\
                                   origin.add(Base.Vector(self._LexanThick,self._OuterWidth-self._LexanThick,self._BaseHeight+self._LexanHeight)),\
                                   XNormL).extrude(LexLeftExtrude)
        Material.AddMaterial("lexan","thick=1/8",\
                             "width=%f"%(self._LexanHeight),\
                             "length=%f"%(self._OuterWidth-(2*self._LexanThick)))
        self.lexright = Part.makePlane(self._LexanHeight,\
                                   self._OuterWidth-(2*self._LexanThick),\
                                   origin.add(Base.Vector(self._OuterLength,self._OuterWidth-self._LexanThick,self._BaseHeight+self._LexanHeight)),\
                                   XNormL).extrude(LexLeftExtrude)
        Material.AddMaterial("lexan","thick=1/8",\
                             "width=%f"%(self._LexanHeight),\
                             "length=%f"%(self._OuterWidth-(2*self._LexanThick)))
        
    def show(self,doc=None):
        if doc==None:
            doc = App.activeDocument()
        obj = doc.addObject("Part::Feature",self.name+"_layoutbase")
        obj.Shape = self.layoutbase
        obj.Label = self.name+"_layoutbase"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_front")
        obj.Shape = self.front
        obj.Label = self.name+"_front"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_back")
        obj.Shape = self.back
        obj.Label = self.name+"_back"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_left")
        obj.Shape = self.left
        obj.Label = self.name+"_left"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_right")
        obj.Shape = self.right
        obj.Label = self.name+"_right"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_lexfront")
        obj.Shape = self.lexfront
        obj.Label = self.name+"_lexfront"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lexback")
        obj.Shape = self.lexback
        obj.Label = self.name+"_lexback"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lexleft")
        obj.Shape = self.lexleft
        obj.Label = self.name+"_lexleft"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lexright")
        obj.Shape = self.lexright
        obj.Label = self.name+"_lexright"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
    

class MultiDemo(object):
    def __init__(self,name,origin):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
    def show(self,doc=None):
        if doc==None:
            doc = App.activeDocument()
    


if __name__ == '__main__':
    doc = None
    for docname in App.listDocuments():
        if docname == 'ProductDisplay':
            App.closeDocument(docname)
        if docname == 'YardDemo':
            App.closeDocument(docname)
        if docname == 'MultiDemo':
            App.closeDocument(docname)
    pd_doc = App.newDocument('ProductDisplay')
    pd = ProductDisplay("ProductDisplayCase",Base.Vector(0,0,0))
    pd.show(pd_doc)
    App.ActiveDocument=pd_doc
    Gui.ActiveDocument=pd_doc
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewIsometric()
    yd_doc = App.newDocument('YardDemo')
    yd = YardDemo('YardDemo',Base.Vector(0,0,0))
    yd.show(yd_doc)
    App.ActiveDocument=yd_doc
    Gui.ActiveDocument=yd_doc
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewIsometric()
    #md_doc = App.newDocument('MultiDemo')
    #md = MultiDemo('MultiDemo',Base.Vector(0,0,0))
    #App.ActiveDocument=md_doc
    #Gui.ActiveDocument=md_doc
    #Gui.SendMsgToActiveView("ViewFit")
    #Gui.activeDocument().activeView().viewIsometric()
    Material.BOM("ShowProductDemoAndDisplayCabs.bom")
    
