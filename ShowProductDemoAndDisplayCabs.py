#!/usr/bin/freecad
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
#  Last Modified : <230628.1438>
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


import Part, TechDraw, TechDrawGui
import FreeCADGui
from FreeCAD import Console
from FreeCAD import Base
import FreeCAD as App

from abc import ABCMeta, abstractmethod, abstractproperty

import os
import sys
sys.path.append(os.path.dirname(__file__))

import datetime

from COBLEDStrip import *
from Electrical import *

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
        
class GenerateDrawings(object):
    # doc.addObject('TechDraw::DrawSVGTemplate','USLetterLandscapeTemplate')
    # doc.USLetterTemplate.Template = App.getResourceDir()+"Mod/TechDraw/Templates/USLetter_Landscape.svg"
    # edt = doc.USLetterTemplate.EditableTexts    
    # "CompanyName"
    # "CompanyAddress"
    # "DrawingTitle1"
    # "DrawingTitle2"
    # "DrawingTitle3"
    # "DrawingNumber"
    # "Revision"
    # "DrawnBy"
    # "CheckedBy"
    # "Approved1"
    # "Approved2"
    # "Scale"
    # "Code"
    # "Weight"
    # "Sheet"
    # doc.USLetterTemplate.EditableTexts = edt
    # doc.addObject('TechDraw::DrawPage','name')
    # doc.name.Template = doc.USLetterTemplate
    # edt = doc.name.Template.EditableTexts
    # "DrawingTitle2"
    # "Scale"
    # "Sheet"
    # doc.name.Template.EditableTexts = edt
    __metaclass__ = ABCMeta
    @abstractmethod
    def generateDrawings(self,doc):
        pass
    def createTemplate(self,doc,title,numsheets,revision="A"):
        self.drawtemplate = doc.addObject('TechDraw::DrawSVGTemplate','USLetterLandscapeTemplate')
        self.drawtemplate.Template = App.getResourceDir()+"Mod/TechDraw/Templates/USLetter_Landscape.svg"
        edt = self.drawtemplate.EditableTexts
        edt['CompanyName'] = "Deepwoods Software"
        edt['CompanyAddress'] = '51 Locke Hill Road, Wendell, MA 01379 USA'
        edt['DrawingTitle1']= title
        edt['DrawingTitle3']= ""
        edt['DrawnBy'] = "Robert Heller"
        edt['CheckedBy'] = ""
        edt['Approved1'] = ""
        edt['Approved2'] = ""
        edt['Code'] = ""
        edt['Weight'] = ''
        edt['DrawingNumber'] = datetime.datetime.now().ctime()
        edt['Revision'] = revision
        self.drawtemplate.EditableTexts = edt
        self.sheet = 0
        self.sheetcount = numsheets
    def createSheet(self,doc,sheettitle,scale="1"):
        self.sheet = self.sheet + 1
        sheetname = "Sheet%dOf%d"%(self.sheet,self.sheetcount)
        thissheet = doc.addObject('TechDraw::DrawPage',sheetname)
        thissheet.Template = self.drawtemplate
        edt = thissheet.Template.EditableTexts
        edt['DrawingTitle2']= sheettitle
        edt['Scale'] = scale
        edt['Sheet'] = "Sheet %d of %d"%(self.sheet,self.sheetcount)
        thissheet.Template.EditableTexts = edt
        thissheet.ViewObject.show()
        return thissheet
    
        



class ProductDisplay(GenerateDrawings):
    _OuterWidth  = 3*12
    _OuterHeight = 3*12
    _BackODepth  = 7
    _LidODepth   = 2
    _PlyThick    = 3.0/8.0
    _BoardThick  = 3.0/4.0
    _woodColor   = (210/255.0,180/255.0,140/255.0)
    _pegthick    = 1.0/8.0
    _pegholedia  = 3.0/16.0
    _pegholespace = 1
    _pegboardColor = (139/255.0,35/255.0,35/255.0)
    _backbraceSize = 12
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
        polypoints = list()
        pstring = "polygon=["
        BackBraceExtrude = Base.Vector(0,-self._PlyThick,0)
        for tup in [(0,0),(self._backbraceSize,0),(0,self._backbraceSize),(0,0)]:
            x,z = tup
            polypoints.append(origin.add(Base.Vector(x+self._PlyThick,0,z)))
            pstring = pstring + "(%f,%f)"%(x,z)
        pstring = pstring + "]"
        self.braceL = Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                        .extrude(BackBraceExtrude)
        Material.AddMaterial("plywood","thick=3/8",pstring)
        polypoints = list()
        BackBraceExtrude = Base.Vector(0,-self._PlyThick,0)
        for tup in [(0,0),(-self._backbraceSize,0),(0,self._backbraceSize),(0,0)]:
            x,z = tup
            polypoints.append(origin.add(Base.Vector(x+self._OuterWidth-self._PlyThick,0,z)))
        self.braceR = Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                                .extrude(BackBraceExtrude)
        Material.AddMaterial("plywood","thick=3/8",pstring)
        self.leftlight = COBLEDStripYard(name+"_leftledstrip",\
                        origin.add(Base.Vector(self._BoardThick,\
                                   self._BackODepth-(1.8/25.4),\
                                   self._BoardThick)),'VL')
        Material.AddMaterial("COBLEDStrip",\
                             "length=%d"%(self.leftlight.Length))
        self.rightlight = COBLEDStripYard(name+"_rightledstrip",\
                    origin.add(Base.Vector(self._OuterWidth-self._BoardThick,\
                               self._BackODepth-(1.8/25.4),\
                               self._OuterHeight-self._BoardThick)),\
                               'VR')
        Material.AddMaterial("COBLEDStrip",\
                             "length=%d"%(self.leftlight.Length))
        self.toplight = COBLEDStripYard(name+"_topledstrip",\
                    origin.add(Base.Vector(self._OuterWidth-self._BoardThick,\
                               self._BackODepth-(1.8/25.4),\
                               self._OuterHeight-self._BoardThick)),\
                               'H')
        Material.AddMaterial("COBLEDStrip",\
                             "length=%d"%(self.leftlight.Length))
    def __pegboard(self,width,height,o=Base.Vector(0,0,0)):
        pextrude=Base.Vector(0,self._pegthick,0)
        n = Base.Vector(0,1,0)
        peg = Part.makePlane(width,height,o,n).extrude(pextrude)
        #return peg
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
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_left_lid")
        obj.Shape = self.left_lid
        obj.Label = self.name+"_left_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_right_lid")
        obj.Shape = self.right_lid
        obj.Label = self.name+"_right_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_bottom_lid")
        obj.Shape = self.bottom_lid
        obj.Label = self.name+"_bottom_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_top_lid")
        obj.Shape = self.top_lid
        obj.Label = self.name+"_top_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_braceL")
        obj.Shape = self.braceL
        obj.Label = self.name+"_braceL"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_braceR")
        obj.Shape = self.braceR
        obj.Label = self.name+"_braceR"
        obj.ViewObject.ShapeColor=self._woodColor
        self.leftlight.show(doc)
        self.rightlight.show(doc)
        self.toplight.show(doc)
    def __caseBackNoPegboard__(self,doc):
        black = (0.0,0.0,0.0)
        result=list()
        obj = doc.addObject("Part::Feature",self.name+"_back")
        obj.Shape = self.back
        obj.Label = self.name+"_back"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_left")
        obj.Shape = self.left
        obj.Label = self.name+"_left"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_leftPegB")
        obj.Shape = self.leftPegB
        obj.Label = self.name+"_leftPegB"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_right")
        obj.Shape = self.right
        obj.Label = self.name+"_right"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_rightPegB")
        obj.Shape = self.rightPegB
        obj.Label = self.name+"_rightPegB"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_bottom")
        obj.Shape = self.bottom
        obj.Label = self.name+"_bottom"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_bottomPegB")
        obj.Shape = self.bottomPegB
        obj.Label = self.name+"_bottomPegB"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_top")
        obj.Shape = self.top
        obj.Label = self.name+"_top"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_topPegB")
        obj.Shape = self.topPegB
        obj.Label = self.name+"_topPegB"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        return result
    def __caseBack__(self,doc):
        black = (0.0,0.0,0.0)
        result=self.__caseBackNoPegboard__(doc)
        obj = doc.addObject("Part::Feature",self.name+"_pegboard")
        obj.Shape = self.pegboard
        obj.Label = self.name+"_pegboard"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        return result
    def __lid__(self,doc):
        black = (0.0,0.0,0.0)
        result=list()
        obj = doc.addObject("Part::Feature",self.name+"_lid")
        obj.Shape = self.lid
        obj.Label = self.name+"_lid"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_left_lid")
        obj.Shape = self.left_lid
        obj.Label = self.name+"_left_lid"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_right_lid")
        obj.Shape = self.right_lid
        obj.Label = self.name+"_right_lid"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_bottom_lid")
        obj.Shape = self.bottom_lid
        obj.Label = self.name+"_bottom_lid"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_top_lid")
        obj.Shape = self.top_lid
        obj.Label = self.name+"_top_lid"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        return result        
    def generateDrawings(self,doc):
        self.createTemplate(doc,"Product Display Case",3)
        sheet1 = self.createSheet(doc,"Case Back (no pegboard)")
        tv = doc.addObject('TechDraw::DrawViewPart','TopViewNoPeg')
        sheet1.addView(tv)
        caseBackNoPegboard = self.__caseBackNoPegboard__(doc)
        tv.Source = caseBackNoPegboard
        tv.Direction=(0.0,1.0,0.0)
        tv.Scale = 1.0
        tv.X = 60
        tv.Y = 160
        rv = doc.addObject('TechDraw::DrawViewPart','RightViewNoPeg')
        sheet1.addView(rv)
        rv.Source = caseBackNoPegboard
        rv.Direction=(1.0,0.0,0.0)
        rv.Scale = 1.0
        rv.X = 160
        rv.Y = 160
        bv = doc.addObject('TechDraw::DrawViewPart','BottomViewNoPeg')
        sheet1.addView(bv)
        bv.Source = caseBackNoPegboard
        bv.Direction=(0.0,0.0,1.0)
        bv.Scale = 1.0
        bv.X = 60
        bv.Y = 60
        doc.recompute()
        TechDrawGui.exportPageAsPdf(sheet1,"ProductDisplayCaseP1.pdf")
        sheet2 = self.createSheet(doc,"Case Back (with pegboard)")
        tv = doc.addObject('TechDraw::DrawViewPart','TopViewPeg')
        caseBack = self.__caseBack__(doc)
        sheet2.addView(tv)
        tv.Source = caseBack 
        tv.Direction=(0.0,1.0,0.0)
        tv.Scale = 1.0
        tv.X = 60
        tv.Y = 160
        rv = doc.addObject('TechDraw::DrawViewPart','RightView')
        sheet2.addView(rv)
        rv.Source = caseBack
        rv.Direction=(1.0,0.0,0.0)
        rv.Scale = 1.0
        rv.X = 160
        rv.Y = 160
        bv = doc.addObject('TechDraw::DrawViewPart','BottomView')
        sheet2.addView(bv)
        bv.Source = caseBack
        bv.Direction=(0.0,0.0,1.0)
        bv.Scale = 1.0
        bv.X = 60
        bv.Y = 60
        doc.recompute()
        TechDrawGui.exportPageAsPdf(sheet2,"ProductDisplayCaseP2.pdf")
        sheet3 = self.createSheet(doc,"Case Lid")
        tv = doc.addObject('TechDraw::DrawViewPart','TopViewLid')
        sheet3.addView(tv)
        lid = self.__lid__(doc)
        tv.Source = lid
        tv.Direction=(0.0,1.0,0.0)
        tv.Scale = 1.0
        tv.X = 60
        tv.Y = 160
        rv = doc.addObject('TechDraw::DrawViewPart','RightViewLid')
        sheet3.addView(rv)
        rv.Source = lid
        rv.Direction=(1.0,0.0,0.0)
        rv.Scale = 1.0
        rv.X = 160
        rv.Y = 160
        bv = doc.addObject('TechDraw::DrawViewPart','BottomViewLid')
        sheet3.addView(bv)
        bv.Source = lid
        bv.Direction=(0.0,0.0,1.0)
        bv.Scale = 1.0
        bv.X = 60
        bv.Y = 60
        doc.recompute()
        TechDrawGui.exportPageAsPdf(sheet3,"ProductDisplayCaseP3.pdf")

class YardDemo(GenerateDrawings):
    _OuterWidth  = 12
    _OuterLength = 3*12
    _BaseHeight  = 6.25
    _LexanHeight = 2
    _PlyThick    = 1.0/4.0
    _LexanThick  = 1.0/8.0
    _BoardThick  = 3.0/4.0
    _woodColor   = (210/255.0,180/255.0,140/255.0)
    _lexColor    = (1.0,1.0,1.0)
    _roadbedPoly = [
        (0.000000,8),\
        (0.000000,7.941824),\
        (2.134400,7.941824),\
        (5.269878,7.681286),\
        (27.750000,3.875000),\
        (36.000000,3.875000),\
        (36.000000,1.375000),\
        (0.000000,1.375000),\
        (0.000000,8)\
    ]
    _roadbedColor = (.5,.5,.5)
    _roadbedThick = 1.0/8.0
    _masoniteThick = 1.0/8.0
    _masoniteColor = (139/255.0,35/255.0,35/255.0)
    def __init__(self,name,origin):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
        self.origin = origin
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
        self.back = Part.makePlane(self._BaseHeight-self._PlyThick,\
                                    self._OuterLength,\
                                    origin.add(Base.Vector(0,self._OuterWidth,self._BaseHeight-self._PlyThick)),\
                                    YNormB).extrude(BackExtrude)
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
        polypoints = list()
        pstring = "polygon=["
        RoadbedExtrude = Base.Vector(0,0,self._roadbedThick)
        for tup in self._roadbedPoly:
            x,y = tup
            polypoints.append(origin.add(Base.Vector(x,y,self._BaseHeight)))
            pstring = pstring + "(%f,%f)"%(x,y-1.375)
        pstring = pstring + "]"
        self.roadbed = Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                        .extrude(RoadbedExtrude)
        Material.AddMaterial("homabed",pstring)
        self.cornerA = self.__corner__('A')
        self.cornerB = self.__corner__('B')
        self.cornerC = self.__corner__('C')
        self.cornerD = self.__corner__('D')
        self.lexmountF1 = self.__lexmount__('F',origin.add(Base.Vector(3,0,self._BaseHeight)))
        self.lexmountF2 = self.__lexmount__('F',origin.add(Base.Vector(self._OuterLength-(3+self._mountLength),0,self._BaseHeight)))
        self.lexmountB1 = self.__lexmount__('B',origin.add(Base.Vector(3,0,self._BaseHeight)))
        self.lexmountB2 = self.__lexmount__('B',origin.add(Base.Vector(self._OuterLength-(3+self._mountLength),0,self._BaseHeight)))
        self.frontCover = Part.makePlane(self._BaseHeight+self._LexanHeight,\
                                         self._OuterLength+(2*self._BoardThick),\
                                         origin.add(Base.Vector(-self._BoardThick,-self._BoardThick,0)),\
                                         YNormF).extrude(FrontExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BaseHeight+self._LexanHeight),\
                             "length=%f"%(self._OuterLength+(2*self._BoardThick)))
        self.backCover = Part.makePlane(self._BaseHeight+self._LexanHeight,\
                                        self._OuterLength+(2*self._BoardThick),\
                                        origin.add(Base.Vector(-self._BoardThick,self._OuterWidth+self._BoardThick,self._BaseHeight+self._LexanHeight)),\
                                        YNormB).extrude(BackExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BaseHeight+self._LexanHeight),\
                             "length=%f"%(self._OuterLength+(2*self._BoardThick)))
        self.leftCover = Part.makePlane(self._BaseHeight+self._LexanHeight,\
                                        self._OuterWidth,\
                                        origin.add(Base.Vector(0,self._OuterWidth,self._BaseHeight+self._LexanHeight)),\
                                        XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BaseHeight+self._LexanHeight),\
                             "length=%f"%(self._OuterWidth))
        self.rightCover = Part.makePlane(self._BaseHeight+self._LexanHeight,\
                                   self._OuterWidth,\
                                   origin.add(Base.Vector(self._OuterLength+self._BoardThick,self._OuterWidth,self._BaseHeight+self._LexanHeight)),\
                                   XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._BaseHeight+self._LexanHeight),\
                             "length=%f"%(self._OuterWidth))
        MasoniteExtrude = Base.Vector(0,0,self._masoniteThick)
        self.topCover = Part.makePlane(self._OuterLength+(2*self._BoardThick),\
                                       self._OuterWidth+(2*self._BoardThick),\
                                       origin.add(Base.Vector(-self._BoardThick,\
                                                              -self._BoardThick,\
                                                              self._BaseHeight+self._LexanHeight)),\
                                       ZNorm).extrude(MasoniteExtrude)
        Material.AddMaterial("masonite","thick=1/8",\
                             "width=%f"%(self._OuterWidth+(2*self._BoardThick)),\
                             "length=%f"%(self._OuterLength+(2*self._BoardThick)))
    _cornerPolys = {\
        'A': [(0.125,11.875),(1.125,11.875),(1.125,11.75),(.25,11.75),\
              (.25,10.875),(.125,10.875),(.125,11.875)],\
        'B': [(34.875,11.875),(35.875,11.875),(35.875,10.875),\
              (35.75,10.875),(35.75,11.75),(34.875,11.75),\
              (34.875,11.875)],\
        'C': [(34.875,0.125),(35.875,0.125),(35.875,1.125),(35.75,1.125),\
              (35.75,0.25),(34.875,0.25),(34.875,0.125)],\
        'D': [(.125,1.125),(.25,1.125),(.25,.25),(1.125,.25),(1.125,.25),\
              (1.125,.125),(.125,.125),(.125,1.125)]\
    }
    def __corner__(self,which):
        polypoints = list()
        CornerExtrude = Base.Vector(0,0,self._LexanHeight)
        for tup in self._cornerPolys[which]:
            x,y = tup
            polypoints.append(self.origin.add(Base.Vector(x,y,self._BaseHeight)))
        Material.AddMaterial("1x1_PVCAngle","length=%f"%(self._LexanHeight))
        return Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                .extrude(CornerExtrude)
    _lexmountPoly = {\
        'F': [(.125,1.),(.25,1.125),(.25,.125),(1.125,.125),(1.125,0),\
              (.125,0),(.125,1.)],\
        'B': [(10.875,0),(11.875,0),(11.875,1),(11.75,1),(11.75,.125),\
              (10.875,.125),(10.875,0)]\
    }
    _mountLength = 6
    def __lexmount__(self,side,o):
        polypoints = list()
        MountExtrude = Base.Vector(self._mountLength,0,0)
        for tup in self._lexmountPoly[side]:
            y,z = tup
            polypoints.append(o.add(Base.Vector(0,y,z)))
        Material.AddMaterial("1x1_PVCAngle","length=%f"%(self._mountLength))
        return Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                .extrude(MountExtrude)
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
        obj = doc.addObject("Part::Feature",self.name+"_roadbed")
        obj.Shape = self.roadbed
        obj.Label = self.name+"_roadbed"
        obj.ViewObject.ShapeColor=self._roadbedColor
        obj = doc.addObject("Part::Feature",self.name+"_cornerA")
        obj.Shape = self.cornerA
        obj.Label = self.name+"_cornerA"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_cornerB")
        obj.Shape = self.cornerB
        obj.Label = self.name+"_cornerB"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_cornerC")
        obj.Shape = self.cornerC
        obj.Label = self.name+"_cornerC"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_cornerD")
        obj.Shape = self.cornerD
        obj.Label = self.name+"_cornerD"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lexmountF1")
        obj.Shape = self.lexmountF1
        obj.Label = self.name+"_lexmountF1"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lexmountF2")
        obj.Shape = self.lexmountF2
        obj.Label = self.name+"_lexmountF2"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lexmountB1")
        obj.Shape = self.lexmountB1
        obj.Label = self.name+"_lexmountB1"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lexmountB2")
        obj.Shape = self.lexmountB2
        obj.Label = self.name+"_lexmountB2"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_frontCover")
        obj.Shape = self.frontCover
        obj.Label = self.name+"_frontCover"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 30
        obj = doc.addObject("Part::Feature",self.name+"_backCover")
        obj.Shape = self.backCover
        obj.Label = self.name+"_backCover"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 30
        obj = doc.addObject("Part::Feature",self.name+"_leftCover")
        obj.Shape = self.leftCover
        obj.Label = self.name+"_leftCover"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 30
        obj = doc.addObject("Part::Feature",self.name+"_rightCover")
        obj.Shape = self.rightCover
        obj.Label = self.name+"_rightCover"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 30
        obj = doc.addObject("Part::Feature",self.name+"_topCover")
        obj.Shape = self.topCover
        obj.Label = self.name+"_topCover"
        obj.ViewObject.ShapeColor=self._masoniteColor
        obj.ViewObject.Transparency = 30
    def __yardDemoBase__(self,doc):
        black = (0.0,0.0,0.0)
        result = list()
        obj = doc.addObject("Part::Feature",self.name+"_layoutbase")
        obj.Shape = self.layoutbase
        obj.Label = self.name+"_layoutbase"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_front")
        obj.Shape = self.front
        obj.Label = self.name+"_front"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_back")
        obj.Shape = self.back
        obj.Label = self.name+"_back"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_left")
        obj.Shape = self.left
        obj.Label = self.name+"_left"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_right")
        obj.Shape = self.right
        obj.Label = self.name+"_right"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexfront")
        obj.Shape = self.lexfront
        obj.Label = self.name+"_lexfront"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexback")
        obj.Shape = self.lexback
        obj.Label = self.name+"_lexback"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexleft")
        obj.Shape = self.lexleft
        obj.Label = self.name+"_lexleft"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexright")
        obj.Shape = self.lexright
        obj.Label = self.name+"_lexright"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_roadbed")
        obj.Shape = self.roadbed
        obj.Label = self.name+"_roadbed"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_cornerA")
        obj.Shape = self.cornerA
        obj.Label = self.name+"_cornerA"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_cornerB")
        obj.Shape = self.cornerB
        obj.Label = self.name+"_cornerB"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_cornerC")
        obj.Shape = self.cornerC
        obj.Label = self.name+"_cornerC"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_cornerD")
        obj.Shape = self.cornerD
        obj.Label = self.name+"_cornerD"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexmountF1")
        obj.Shape = self.lexmountF1
        obj.Label = self.name+"_lexmountF1"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexmountF2")
        obj.Shape = self.lexmountF2
        obj.Label = self.name+"_lexmountF2"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexmountB1")
        obj.Shape = self.lexmountB1
        obj.Label = self.name+"_lexmountB1"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexmountB2")
        obj.Shape = self.lexmountB2
        obj.Label = self.name+"_lexmountB2"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        return result
    def __yardDemoCover__(self,doc):
        black = (0.0,0.0,0.0)
        result = list()
        obj = doc.addObject("Part::Feature",self.name+"_frontCover")
        obj.Shape = self.frontCover
        obj.Label = self.name+"_frontCover"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_backCover")
        obj.Shape = self.backCover
        obj.Label = self.name+"_backCover"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_leftCover")
        obj.Shape = self.leftCover
        obj.Label = self.name+"_leftCover"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_rightCover")
        obj.Shape = self.rightCover
        obj.Label = self.name+"_rightCover"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_topCover")
        obj.Shape = self.topCover
        obj.Label = self.name+"_topCover"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        return result
    def generateDrawings(self,doc):
        self.createTemplate(doc,"Yard Ladder Demo",2)
        sheet1 = self.createSheet(doc,"Base")
        base = self.__yardDemoBase__(doc)
        tv = doc.addObject('TechDraw::DrawViewPart','TopViewBase')
        sheet1.addView(tv)
        tv.Source = base
        tv.Direction=(0.0,1.0,0.0)
        tv.Scale = 1.0
        tv.X = 60
        tv.Y = 160
        rv = doc.addObject('TechDraw::DrawViewPart','RightViewBase')
        sheet1.addView(rv)
        rv.Source = base
        rv.Direction=(1.0,0.0,0.0)
        rv.Scale = 1.0
        rv.X = 160
        rv.Y = 160
        bv = doc.addObject('TechDraw::DrawViewPart','BottomViewBase')
        sheet1.addView(bv)
        bv.Source = base
        bv.Direction=(0.0,0.0,1.0)
        bv.Scale = 1.0
        bv.X = 60
        bv.Y = 60 
        doc.recompute()
        TechDrawGui.exportPageAsPdf(sheet1,"YardLadderDemoP1.pdf")
        sheet2 = self.createSheet(doc,"Cover")
        cover = self.__yardDemoCover__(doc)
        tv = doc.addObject('TechDraw::DrawViewPart','TopViewCover')
        sheet2.addView(tv)
        tv.Source = cover
        tv.Direction=(0.0,1.0,0.0)
        tv.Scale = 1.0
        tv.X = 60
        tv.Y = 160
        rv = doc.addObject('TechDraw::DrawViewPart','RightViewCover')
        sheet2.addView(rv)
        rv.Source = cover
        rv.Direction=(1.0,0.0,0.0)
        rv.Scale = 1.0
        rv.X = 160
        rv.Y = 160
        bv = doc.addObject('TechDraw::DrawViewPart','BottomViewCover')
        sheet2.addView(bv)
        bv.Source = cover
        bv.Direction=(0.0,0.0,1.0)
        bv.Scale = 1.0
        bv.X = 60
        bv.Y = 60 
        doc.recompute()
        TechDrawGui.exportPageAsPdf(sheet2,"YardLadderDemoP2.pdf")
        
class MultiDemo(GenerateDrawings):
    # control panel: 6.5"x4"
    # turnouts     : 9.66666" each
    # 8 Ball Club  : 8"
    # Outer box size: 36x24x7.875 (folded), 72x12x7.875 (unfolded)
    # depth calc: 3/8+6+1/8+1+3/8
    #             ply,space+lex+space+ply
    # Right half: servo turnout, twin coil turnout, single coil turnout, control panel
    #             9.66666+9.66666+9.66666+7 = 36
    # Left half:  Pricom, neopixel, 8 Ball Club, stall motor turnout
    #             9+9+8+9.83333
    _OuterWidthFolded = 36
    _OuterWidthUnfolded = 72
    _OuterHeightFolded = 24
    _OuterHeightUnfolded = 12
    _OuterDepthBase = (3.0/8.0)+6+(1.0/8.0)
    _OuterDepthLid  = (3.0/8.0)+1
    _InnerDepthBase = 6
    _InnerDepthLid  = 1
    _PlyThick    = 3.0/8.0
    _BirchPlyThick = 1.0/4.0
    _ShelfHeight = 7
    _LexanThick  = 1.0/8.0
    _BoardThick  = 3.0/4.0
    _woodColor   = (210/255.0,180/255.0,140/255.0)
    _lexColor    = (1.0,1.0,1.0)
    _backbraceSize = 12
    def __init__(self,name,origin):
        self.name = name
        if not isinstance(origin,Base.Vector):
            raise RuntimeError("origin is not a Vector!")
        self.origin = origin
        YNorm = Base.Vector(0,1,0)
        BackExtrude = Base.Vector(0,self._PlyThick,0)
        self.backR  = Part.makePlane(self._OuterHeightUnfolded,\
                                     self._OuterWidthFolded,\
                                     origin,YNorm).extrude(BackExtrude)
        self.backL  = Part.makePlane(self._OuterHeightUnfolded,\
                                     self._OuterWidthFolded,\
                                     origin.add(Base.Vector(0,0,\
                                            self._OuterHeightUnfolded)),\
                                     YNorm).extrude(BackExtrude)
        Material.AddMaterial("plywood","thick=3/8",\
                             "width=%f"%(self._OuterWidthFolded),\
                             "length=%f"%(self._OuterHeightUnfolded))
        Material.AddMaterial("plywood","thick=3/8",\
                             "width=%f"%(self._OuterWidthFolded),\
                             "length=%f"%(self._OuterHeightUnfolded))
                #
        XNormL = Base.Vector(-1,0,0)
        XNormR = Base.Vector(1,0,0)
        LeftExtrude = Base.Vector(-self._BoardThick,0,0)
        RightExtrude = Base.Vector(self._BoardThick,0,0)
        self.leftR = Part.makePlane(self._OuterHeightUnfolded,\
                                    self._InnerDepthBase,\
                                    origin.add(Base.Vector(self._BoardThick,\
                                                           0,\
                                                           self._OuterHeightUnfolded)),\
                                    XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthBase),\
                             "length=%f"%(self._OuterHeightUnfolded))
        self.leftL = Part.makePlane(self._OuterHeightUnfolded,\
                                    self._InnerDepthBase,\
                                    origin.add(Base.Vector(self._BoardThick,\
                                                           0,\
                                                           2*self._OuterHeightUnfolded)),XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthBase),\
                             "length=%f"%(self._OuterHeightUnfolded))
        self.rightR = Part.makePlane(self._OuterHeightUnfolded,\
                                    self._InnerDepthBase,\
                                    origin.add(Base.Vector(self._OuterWidthFolded-self._BoardThick,0,0)),XNormR).extrude(RightExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthBase),\
                             "length=%f"%(self._OuterHeightUnfolded))
        self.rightL = Part.makePlane(self._OuterHeightUnfolded,\
                                    self._InnerDepthBase,\
                                    origin.add(Base.Vector(self._OuterWidthFolded-self._BoardThick,0,self._OuterHeightUnfolded)),XNormR).extrude(RightExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthBase),\
                             "length=%f"%(self._OuterHeightUnfolded))
        #
        ZNormB = Base.Vector(0,0,1)
        ZNormT = Base.Vector(0,0,-1) 
        BottomExtrude = Base.Vector(0,0,self._BoardThick)
        TopExtrude = Base.Vector(0,0,-self._BoardThick)
        self.bottom = Part.makePlane(self._OuterWidthFolded-(2*self._BoardThick),\
                                     self._InnerDepthBase,\
                                     origin.add(Base.Vector(self._BoardThick,-(self._InnerDepthBase),0)),ZNormB).extrude(BottomExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthBase),\
                             "length=%f"%(self._OuterWidthFolded-(2*self._BoardThick)))
        self.top = Part.makePlane(self._OuterWidthFolded-(2*self._BoardThick),\
                                     self._InnerDepthBase,\
                                     origin.add(Base.Vector(self._BoardThick,-(self._InnerDepthBase),self._OuterHeightFolded)),ZNormB).extrude(TopExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthBase),\
                             "length=%f"%(self._OuterWidthFolded-(2*self._BoardThick)))
        ShelfRExtrude = Base.Vector(0,0,self._BirchPlyThick)
        ShelfLExtrude = Base.Vector(0,0,-self._BirchPlyThick)
        self.shelfR = Part.makePlane(self._OuterWidthFolded-(2*self._BoardThick),\
                                     self._InnerDepthBase,\
                                     origin.add(Base.Vector(self._BoardThick,-(self._InnerDepthBase),self._ShelfHeight)),ZNormB).extrude(ShelfRExtrude)
        Material.AddMaterial("birch plywood","thick=1/4",\
                "width=%f"%(self._InnerDepthBase),\
                "length=%f"%(self._OuterWidthFolded-(2*self._BoardThick)))
        self.shelfL = Part.makePlane(self._OuterWidthFolded-(2*self._BoardThick),\
                                     self._InnerDepthBase,\
                                     origin.add(Base.Vector(self._BoardThick,-(self._InnerDepthBase),self._OuterHeightFolded-self._ShelfHeight)),ZNormB).extrude(ShelfLExtrude)
        Material.AddMaterial("birch plywood","thick=1/4",\
                "width=%f"%(self._InnerDepthBase),\
                "length=%f"%(self._OuterWidthFolded-(2*self._BoardThick)))
        self.shelfRBraces = list()
        self.shelfLBraces = list()
        for x in [self._BoardThick+1,self._OuterWidthFolded/4,\
                  self._OuterWidthFolded/2,3*(self._OuterWidthFolded/4),\
                  self._OuterWidthFolded-(2*self._BoardThick)-1]:
            self.shelfRBraces.append(self.__shelfBrace__(x,self._ShelfHeight,'R'))
            self.shelfLBraces.append(self.__shelfBrace__(x,self._OuterHeightFolded-self._ShelfHeight,'L'))
        LexFrontExtrude = Base.Vector(0,self._LexanThick,0)
        self.lexFrontR = Part.makePlane(self._OuterHeightUnfolded,\
                                     self._OuterWidthFolded,\
                                     origin.add(Base.Vector(0,\
                                        -(self._InnerDepthBase+self._LexanThick),\
                                        0)),YNorm).extrude(LexFrontExtrude)
        Material.AddMaterial("lexan","thick=1/8",\
                             "width=%f"%(self._OuterHeightUnfolded),\
                             "length=%f"%(self._OuterWidthFolded))
        self.lexFrontL = Part.makePlane(self._OuterHeightUnfolded,\
                                     self._OuterWidthFolded,\
                                     origin.add(Base.Vector(0,\
                                            -(self._InnerDepthBase+self._LexanThick),\
                                            self._OuterHeightUnfolded)),\
                                     YNorm).extrude(LexFrontExtrude)
        Material.AddMaterial("lexan","thick=1/8",\
                             "width=%f"%(self._OuterHeightUnfolded),\
                             "length=%f"%(self._OuterWidthFolded))
        self.lexAngles = list()
        self.lexAngles.append(self.__lexAngle__(self._BoardThick,-self._InnerDepthBase,self._ShelfHeight/2,'L'))
        self.lexAngles.append(self.__lexAngle__(self._BoardThick,-self._InnerDepthBase,self._ShelfHeight*1.5,'L'))
        self.lexAngles.append(self.__lexAngle__(self._BoardThick,-self._InnerDepthBase,self._OuterHeightFolded-(self._ShelfHeight/2),'L'))
        self.lexAngles.append(self.__lexAngle__(self._BoardThick,-self._InnerDepthBase,self._OuterHeightFolded-(self._ShelfHeight*1.5),'L'))

        self.lexAngles.append(self.__lexAngle__(self._OuterWidthFolded-self._BoardThick,-self._InnerDepthBase,self._ShelfHeight/2,'R'))
        #self.lexAngles.append(self.__lexAngle__(self._OuterWidthFolded-self._BoardThick,-self._InnerDepthBase,self._ShelfHeight*1.5,'R'))
        self.lexAngles.append(self.__lexAngle__(self._OuterWidthFolded-self._BoardThick,-self._InnerDepthBase,self._OuterHeightFolded-(self._ShelfHeight/2),'R'))
        self.lexAngles.append(self.__lexAngle__(self._OuterWidthFolded-self._BoardThick,-self._InnerDepthBase,self._OuterHeightFolded-(self._ShelfHeight*1.5),'R'))
        
        self.lidLeft = Part.makePlane(self._OuterHeightFolded,\
                                      self._InnerDepthLid,\
                                      origin.add(Base.Vector(self._BoardThick,\
                                                             -(self._InnerDepthBase+self._LexanThick),\
                                                             self._OuterHeightFolded)),\
                                      XNormL).extrude(LeftExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthLid),\
                             "length=%f"%(self._OuterHeightFolded))
        self.lidRight = Part.makePlane(self._OuterHeightFolded,\
                                       self._InnerDepthLid,\
                                       origin.add(Base.Vector(self._OuterWidthFolded-self._BoardThick,\
                                                             -(self._InnerDepthBase+self._LexanThick),\
                                                             0)),\
                                       XNormR).extrude(RightExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthLid),\
                             "length=%f"%(self._OuterHeightFolded))
        self.lidBottom = Part.makePlane(self._OuterWidthFolded-(2*self._BoardThick),\
                                     self._InnerDepthLid,\
                                     origin.add(Base.Vector(self._BoardThick,\
                                                  -(self._InnerDepthBase+self._LexanThick+self._InnerDepthLid),\
                                                  0)),\
                                     ZNormB).extrude(BottomExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthLid),\
                             "length=%f"%(self._OuterWidthFolded-(2*self._BoardThick)))
        self.lidTop = Part.makePlane(self._OuterWidthFolded-(2*self._BoardThick),\
                                     self._InnerDepthLid,\
                                     origin.add(Base.Vector(self._BoardThick,\
                                               -(self._InnerDepthBase+self._LexanThick+self._InnerDepthLid),\
                                               self._OuterHeightFolded)),\
                                     ZNormB).extrude(TopExtrude)
        Material.AddMaterial("pine","thick=3/4",\
                             "width=%f"%(self._InnerDepthLid),\
                             "length=%f"%(self._OuterWidthFolded-(2*self._BoardThick)))
        
        self.lid = Part.makePlane(self._OuterHeightFolded,\
                                  self._OuterWidthFolded,\
                                  origin.add(Base.Vector(0,\
                                        -(self._InnerDepthBase+self._LexanThick+self._InnerDepthLid+self._PlyThick),\
                                        0)),\
                                  YNorm).extrude(BackExtrude)
        Material.AddMaterial("plywood","thick=3/8",\
                             "width=%f"%(self._OuterWidthFolded),\
                             "length=%f"%(self._OuterHeightFolded))
        polypoints = list()
        pstring = "polygon=["
        BackBraceExtrude = Base.Vector(0,self._PlyThick,0)
        for tup in [(0,0),(self._backbraceSize,0),(0,self._backbraceSize),(0,0)]:
            x,z = tup
            polypoints.append(origin.add(Base.Vector(x+self._PlyThick,self._PlyThick,z)))
            pstring = pstring + "(%f,%f)"%(x,z)
        pstring = pstring + "]"
        self.braceRL = Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                        .extrude(BackBraceExtrude)
        Material.AddMaterial("plywood","thick=3/8",pstring)
        polypoints = list()
        for tup in [(0,0),(-self._backbraceSize,0),(0,self._backbraceSize),(0,0)]:
            x,z = tup
            polypoints.append(origin.add(Base.Vector(x+self._OuterWidthFolded-self._PlyThick,self._PlyThick,z)))
        self.braceRR = Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                                .extrude(BackBraceExtrude)
        Material.AddMaterial("plywood","thick=3/8",pstring)
        polypoints = list()        
        for tup in [(0,0),(self._backbraceSize,0),(0,-self._backbraceSize),(0,0)]:
            x,z = tup
            polypoints.append(origin.add(Base.Vector(x+self._PlyThick,self._PlyThick,z+self._OuterHeightFolded)))
        self.braceLL = Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                            .extrude(BackBraceExtrude)
        Material.AddMaterial("plywood","thick=3/8",pstring)
        polypoints = list()
        for tup in [(0,0),(-self._backbraceSize,0),(0,-self._backbraceSize),(0,0)]:
            x,z = tup
            polypoints.append(origin.add(Base.Vector(x+self._OuterWidthFolded-self._PlyThick,self._PlyThick,z+self._OuterHeightFolded)))
        self.braceLR = Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                                .extrude(BackBraceExtrude)
        Material.AddMaterial("plywood","thick=3/8",pstring)
        self.electricboxes = list()
        for x in [self._BoardThick+1,self._OuterWidthFolded/4,\
                  self._OuterWidthFolded/2,3*(self._OuterWidthFolded/4),]:
            box=SingleGangUtilityBox(self.name+"_boxR1",origin.add(Base.Vector(\
                        x+self._BoardThick,-(SingleGangUtilityBox.Depth+self._PlyThick),self._BoardThick)))
            Material.AddMaterial("utility box","Gang=Single")
            Material.AddMaterial("outlet","type=duplex","voltage=125","current=15A")
            cover=SingleGangUtilityOutletCover(self.name+"_coverR1",\
                                    box.origin.add(Base.Vector(0,-SingleGangUtilityOutletCover.Depth,0)))
            Material.AddMaterial("utility box cover","type=duplex")
            self.electricboxes.append((box,cover))
            box=SingleGangUtilityBox(self.name+"_boxR1",origin.add(Base.Vector(\
                        x+self._BoardThick,-(SingleGangUtilityBox.Depth+self._PlyThick),self._OuterHeightFolded-self._BoardThick-SingleGangUtilityBox.Width)))
            Material.AddMaterial("utility box","Gang=Single")
            Material.AddMaterial("outlet","type=duplex","voltage=125","current=15A")
            cover=SingleGangUtilityOutletCover(self.name+"_coverR1",\
                                    box.origin.add(Base.Vector(0,-SingleGangUtilityOutletCover.Depth,0)))
            Material.AddMaterial("utility box cover","type=duplex")
            self.electricboxes.append((box,cover))
    _lexAnglePolys8ths = {\
        'R': [(8,0), (0,0), (0,-8), (1,-8), (1,-1), (8,-1), (8,0)],\
        'L': [(0,0), (0,8), (1,8),  (1,1),  (8,1),  (8,0),  (0,0)] \
    }
    _lexAngleLength = 1
    def __lexAngle__(self,xoff,yoff,zoff,which):
        polypoints = list()
        LexAngleExtrude = Base.Vector(0,0,self._lexAngleLength)
        for tup in self._lexAnglePolys8ths[which]:
            y,x = tup
            polypoints.append(self.origin.add(Base.Vector(xoff+(x/8.0),\
                                                          yoff+(y/8.0),\
                                                          zoff)))
        Material.AddMaterial("1x1_PVCAngle","length=%f"%(self._lexAngleLength))
        return Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                    .extrude(LexAngleExtrude)
    _shelfBracePoly = [(0,0), (-6,0), (0,3), (0,0)]
    def __shelfBrace__(self,xoff,zoff,which):
        sign=1
        if which == 'R':
            sign=-1
        polypoints = list()
        BraceExtrude = Base.Vector(self._BoardThick,0,0)
        pstring = "polygon=["
        for tup in self._shelfBracePoly:
            y,z = tup
            pstring = pstring + "(%f,%f)"%(abs(y),z)
            z = z*sign
            polypoints.append(self.origin.add(Base.Vector(xoff,y,z+zoff)))
        pstring = pstring + "]"
        Material.AddMaterial("pine","thick=3/4",pstring)
        return Part.Face(Part.Wire(Part.makePolygon(polypoints)))\
                .extrude(BraceExtrude)
    def show(self,doc=None):
        if doc==None:
            doc = App.activeDocument()
        obj = doc.addObject("Part::Feature",self.name+"_backR")
        obj.Shape = self.backR
        obj.Label = self.name+"_backR"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_backL")
        obj.Shape = self.backL
        obj.Label = self.name+"_backL"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_leftR")
        obj.Shape = self.leftR
        obj.Label = self.name+"_leftR"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_leftL")
        obj.Shape = self.leftL
        obj.Label = self.name+"_leftL"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_rightR")
        obj.Shape = self.rightR
        obj.Label = self.name+"_rightR"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_rightL")
        obj.Shape = self.rightL
        obj.Label = self.name+"_rightL"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_bottom")
        obj.Shape = self.bottom
        obj.Label = self.name+"_bottom"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_top")
        obj.Shape = self.top
        obj.Label = self.name+"_top"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_shelfR")
        obj.Shape = self.shelfR
        obj.Label = self.name+"_shelfR"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_shelfL")
        obj.Shape = self.shelfL
        obj.Label = self.name+"_shelfL"
        obj.ViewObject.ShapeColor=self._woodColor
        index = 1
        for b in self.shelfRBraces:
            n = "_shelfRB%d"%(index)
            obj = doc.addObject("Part::Feature",self.name+n)
            obj.Shape = b
            obj.Label = self.name+n
            obj.ViewObject.ShapeColor=self._woodColor
            index = index + 1
        index = 1
        for b in self.shelfLBraces:
            n = "_shelfLB%d"%(index)
            obj = doc.addObject("Part::Feature",self.name+n)
            obj.Shape = b
            obj.Label = self.name+n
            obj.ViewObject.ShapeColor=self._woodColor
            index = index + 1
        obj = doc.addObject("Part::Feature",self.name+"_lexFrontR")
        obj.Shape = self.lexFrontR
        obj.Label = self.name+"_lexFrontR"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lexFrontL")
        obj.Shape = self.lexFrontL
        obj.Label = self.name+"_lexFrontL"
        obj.ViewObject.ShapeColor=self._lexColor
        obj.ViewObject.Transparency = 90
        index = 1
        for a in self.lexAngles:
            n = "_lexAngles%d"%(index)
            obj = doc.addObject("Part::Feature",self.name+n)
            obj.Shape = a
            obj.Label = self.name+n
            obj.ViewObject.ShapeColor=self._lexColor
            obj.ViewObject.Transparency = 90
        obj = doc.addObject("Part::Feature",self.name+"_lidLeft")
        obj.Shape = self.lidLeft
        obj.Label = self.name+"_lidLeft"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_lidRight")
        obj.Shape = self.lidRight
        obj.Label = self.name+"_lidRight"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_lidBottom")
        obj.Shape = self.lidBottom
        obj.Label = self.name+"_lidBottom"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_lidTop")
        obj.Shape = self.lidTop
        obj.Label = self.name+"_lidTop"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_lid")
        obj.Shape = self.lid
        obj.Label = self.name+"_lid"
        obj.ViewObject.ShapeColor=self._woodColor
        obj.ViewObject.Transparency = 50
        obj = doc.addObject("Part::Feature",self.name+"_braceRL")
        obj.Shape = self.braceRL
        obj.Label = self.name+"_braceRL"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_braceLR")
        obj.Shape = self.braceLR
        obj.Label = self.name+"_braceLR"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_braceLL")
        obj.Shape = self.braceLL
        obj.Label = self.name+"_braceLL"
        obj.ViewObject.ShapeColor=self._woodColor
        obj = doc.addObject("Part::Feature",self.name+"_braceRR")
        obj.Shape = self.braceRR
        obj.Label = self.name+"_braceRR"
        obj.ViewObject.ShapeColor=self._woodColor
        for tup in self.electricboxes:
            box,cover = tup
            box.show(doc)
            cover.show(doc)
    def __base__(self,doc):
        black = (0.0,0.0,0.0)
        result = list()
        obj = doc.addObject("Part::Feature",self.name+"_backR")
        obj.Shape = self.backR
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_backL")
        obj.Shape = self.backL
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_leftR")
        obj.Shape = self.leftR
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_leftL")
        obj.Shape = self.leftL
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_rightR")
        obj.Shape = self.rightR
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_rightL")
        obj.Shape = self.rightL
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_bottom")
        obj.Shape = self.bottom
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_top")
        obj.Shape = self.top
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_shelfR")
        obj.Shape = self.shelfR
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_shelfL")
        obj.Shape = self.shelfL
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        index = 1
        for b in self.shelfRBraces:
            n = "_shelfRB%d"%(index)
            obj = doc.addObject("Part::Feature",self.name+n)
            obj.Shape = b
            obj.ViewObject.LineColor=black
            obj.ViewObject.LineWidth=2
            result.append(obj)
            index = index + 1
        index = 1
        for b in self.shelfLBraces:
            n = "_shelfLB%d"%(index)
            obj = doc.addObject("Part::Feature",self.name+n)
            obj.Shape = b
            obj.ViewObject.LineColor=black
            obj.ViewObject.LineWidth=2
            result.append(obj)
            index = index + 1
        return result
    def __lexan__(self,doc):
        black = (0.0,0.0,0.0)
        result = list()
        obj = doc.addObject("Part::Feature",self.name+"_lexFrontR")
        obj.Shape = self.lexFrontR
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lexFrontL")
        obj.Shape = self.lexFrontL
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        index = 1
        for a in self.lexAngles:
            n = "_lexAngles%d"%(index)
            obj = doc.addObject("Part::Feature",self.name+n)
            obj.Shape = a
            obj.ViewObject.LineColor=black
            obj.ViewObject.LineWidth=2
            result.append(obj)
        return result
    def __cover__(self,doc):
        black = (0.0,0.0,0.0)
        result = list()
        obj = doc.addObject("Part::Feature",self.name+"_lidLeft")
        obj.Shape = self.lidLeft
        obj.Label = self.name+"_lidLeft"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lidRight")
        obj.Shape = self.lidRight
        obj.Label = self.name+"_lidRight"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lidBottom")
        obj.Shape = self.lidBottom
        obj.Label = self.name+"_lidBottom"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lidTop")
        obj.Shape = self.lidTop
        obj.Label = self.name+"_lidTop"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        obj = doc.addObject("Part::Feature",self.name+"_lid")
        obj.Shape = self.lid
        obj.Label = self.name+"_lid"
        obj.ViewObject.LineColor=black
        obj.ViewObject.LineWidth=2
        result.append(obj)
        return result
    def generateDrawings(self,doc):
        self.createTemplate(doc,"Multi Demo",3)
        sheet1 = self.createSheet(doc,"Base")
        base = self.__base__(doc)        
        tv = doc.addObject('TechDraw::DrawViewPart','TopViewBase')
        sheet1.addView(tv)
        tv.Source = base
        tv.Direction=(0.0,1.0,0.0)
        tv.Scale = 1.0
        tv.X = 60
        tv.Y = 160
        rv = doc.addObject('TechDraw::DrawViewPart','RightViewBase')
        sheet1.addView(rv)
        rv.Source = base
        rv.Direction=(1.0,0.0,0.0)
        rv.Scale = 1.0
        rv.X = 160
        rv.Y = 160
        bv = doc.addObject('TechDraw::DrawViewPart','BottomViewBase')
        sheet1.addView(bv)
        bv.Source = base
        bv.Direction=(0.0,0.0,1.0)
        bv.Scale = 1.0
        bv.X = 60
        bv.Y = 60 
        doc.recompute()
        TechDrawGui.exportPageAsPdf(sheet1,"MultiDemoP1.pdf")
        sheet2 = self.createSheet(doc,"Lexan Detail")
        lexan = self.__lexan__(doc)
        tv = doc.addObject('TechDraw::DrawViewPart','TopViewLexan')
        sheet2.addView(tv)
        tv.Source = lexan
        tv.Direction=(0.0,1.0,0.0)
        tv.Scale = 1.0
        tv.X = 60
        tv.Y = 160
        rv = doc.addObject('TechDraw::DrawViewPart','RightViewLexan')
        sheet2.addView(rv)
        rv.Source = lexan
        rv.Direction=(1.0,0.0,0.0)
        rv.Scale = 1.0
        rv.X = 160
        rv.Y = 160
        bv = doc.addObject('TechDraw::DrawViewPart','BottomViewLexan')
        sheet2.addView(bv)
        bv.Source = lexan
        bv.Direction=(0.0,0.0,1.0)
        bv.Scale = 1.0
        bv.X = 60
        bv.Y = 60 
        doc.recompute()
        TechDrawGui.exportPageAsPdf(sheet2,"MultiDemoP2.pdf")
        sheet3 = self.createSheet(doc,"Cover")
        cover = self.__cover__(doc)
        tv = doc.addObject('TechDraw::DrawViewPart','TopViewCover')
        sheet3.addView(tv)
        tv.Source = cover
        tv.Direction=(0.0,1.0,0.0)
        tv.Scale = 1.0
        tv.X = 60
        tv.Y = 160
        rv = doc.addObject('TechDraw::DrawViewPart','RightViewCover')
        sheet3.addView(rv)
        rv.Source = cover
        rv.Direction=(1.0,0.0,0.0)
        rv.Scale = 1.0
        rv.X = 160
        rv.Y = 160
        bv = doc.addObject('TechDraw::DrawViewPart','BottomViewCover')
        sheet3.addView(bv)
        bv.Source = cover
        bv.Direction=(0.0,0.0,1.0)
        bv.Scale = 1.0
        bv.X = 60
        bv.Y = 60 
        doc.recompute()
        TechDrawGui.exportPageAsPdf(sheet3,"MultiDemoP3.pdf")

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
    pd.generateDrawings(pd_doc)
    yd_doc = App.newDocument('YardDemo')
    yd = YardDemo('YardDemo',Base.Vector(0,0,0))
    yd.show(yd_doc)
    App.ActiveDocument=yd_doc
    Gui.ActiveDocument=yd_doc
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewIsometric()
    yd.generateDrawings(yd_doc)
    md_doc = App.newDocument('MultiDemo')
    md = MultiDemo('MultiDemo',Base.Vector(0,0,0))
    md.show(md_doc)
    App.ActiveDocument=md_doc
    Gui.ActiveDocument=md_doc
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewFront()
    md.generateDrawings(md_doc)
    Material.BOM("ShowProductDemoAndDisplayCabs.bom")
    #sys.exit(1)
