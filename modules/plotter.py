"""
	""PLOTTER - HANDLES CHART GENERATION""
	
	Contains two main classes:
		a) nonCategoricalPlotter
		b) categoricalPlotter
		
		these depent on other classes such as:
			a) hierarchical clustering
			b) scatter matrix
			c) line_plot 
			
			these classes are stored in the folder: plots.
		Axis Styling is done by the class axisStyler that is
		store in the file axis_styler.py within the "plots" folder.
	
    Instant Clue - Interactive Data Visualization and Analysis.
    Copyright (C) Hendrik Nolte

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import pandas as pd
import numpy as np
from scipy import interpolate
import os
import sys

import matplotlib
from matplotlib import cm
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import matplotlib.ticker as mtick

from matplotlib.collections import LineCollection

import seaborn as sns 
import tkinter as tk

from collections import OrderedDict
from modules import stats
from modules.plots.hierarchical_clustering import hierarchichalClustermapPlotter
from modules.plots.time_series_helper import _timeSeriesHelper
from modules.plots.scatter_with_categories import scatterWithCategories, binnedScatter
from modules.plots.grid_search_results import gridSearchVisualization 
from modules.plots.line_plot import linePlotHelper
from modules.dialogs import curve_fitting
from modules.plots.grid_search_results import chartToolTip
from modules.plots.axis_styler import axisStyler
from .utils import *

if platform == 'WINDOWS':
	sys.__stdout__ = sys.stdout	
	
fittingFuncs = curve_fitting._HelperCurveFitter()
fitFuncsDict = fittingFuncs.get_fit_functions
nonScatterPlotTypes = ['boxplot','barplot','violinplot','pointplot','swarm']


class _Plotter(object):
	
	def __init__(self,sourceDataClass,figure, workflow):
	
		self.dfClass = sourceDataClass
		self.workflow = workflow
		self.plotHistory = OrderedDict() 
		self.plotProperties = OrderedDict()
		
		self.tooltips = dict() 
		self.onMotionEvents = dict()
		
		
		self.set_axis_props()
		
		self.errorBar = 95
		self.numbBins = 10
		self.scaleBinsInScatter = True
		
		self.minSize, self.maxSize = 10, 180
		self.aggMethod = 'mean'
		
		self.binnedScatter = False
		
		self.axesLimits = OrderedDict()
		self.clusterEvalScores = OrderedDict() 
		self.statistics = OrderedDict()
		
		self.showSubplotBox = True
		self.showGrid = False
		self.castMenu = True
		self.immutableAxes = []
		
		self.plotCount = 0
		
		self.currentPlotType = None
		self.nonCategoricalPlotter  = None
		self.categoricalPlotter = None
		
		self.splitCategories = True
		self.plotCumulativeDist = False
		
		## define cluster defaults
		self.equalYLimits = True
		self.tightLayout = True
		
		self.setup_basic_design()
		self.set_hClust_settings()
		
		#self.set_dist_settings()
		self.set_style_collection_settings()
		self.addSwarm = False
		
		self.figure = figure
		
		self.axes = None
		
	
	def clean_up_figure(self):
		'''
		Removes everything from figure
		'''
		self.addSwarm =  False
		self.disconnect_event_bindings()
		self.figure.clf()
	
	def disconnect_event_bindings(self):
		'''
		'''
		for plotterClass in [self.nonCategoricalPlotter,self.categoricalPlotter]:
			if plotterClass is not None:
				try:
					plotterClass.disconnect_event_bindings()
				except:
					pass
		## disconnect tooltip events
		self.disconnect_tooltips()
		
		
	def disconnect_tooltips(self):		
		'''
		Disconnect tooltip activity.
		'''
		if len(self.onMotionEvents) != 0:
			for event in self.onMotionEvents.values():
				self.figure.canvas.mpl_disconnect(event)	
			self.onMotionEvents.clear()
			self.tooltips.clear()
				
	def initiate_chart(self,numericColumns,categoricalColumns,selectedPlotType, colorMap, 
							specificAxis= None, redraw = True):
		'''
		intiating a chart
		'''
		
		self.save_axis_limits()
		self.set_axis_props()
		self.clean_up_figure()
		self.immutableAxes = []
		self.nonCategoricalPlotter  = None
		self.categoricalPlotter = None
		self.plotCount += 1
		self.castMenu = True
		
		self.currentPlotType = selectedPlotType
		numbNumbericColumns, numbCategoricalColumns = self.get_lenghts_of_lists([numericColumns,categoricalColumns])
		if numbCategoricalColumns == 0:
			
			
			self.nonCategoricalPlotter = nonCategoricalPlotter(self,self.dfClass,self.figure, numericColumns,numbNumbericColumns,
												selectedPlotType,colorMap, 
												specificAxis)
		else:
			self.categoricalPlotter = categoricalPlotter(self,self.dfClass,self.figure, numericColumns,numbNumbericColumns,
												categoricalColumns,numbCategoricalColumns,selectedPlotType,colorMap, 
												specificAxis)

				
		self.axes = self.get_axes_of_figure()
		
		self.adjust_grid_and_box_around_subplot()
		
		if selectedPlotType in ['swarm','pointplot','grid_search_results']	:
			self.style_collection()
		if redraw:
			self.redraw()
		self.plotHistory[self.plotCount] = [self.nonCategoricalPlotter,self.categoricalPlotter]
		self.plotProperties[self.plotCount] = [numericColumns,
											   categoricalColumns,
											   selectedPlotType,
											   colorMap]

		lastNumColumns = []
		lastCatColumns = []
		prevCountPlot = self.plotCount-1
		if prevCountPlot in self.plotProperties:
			lastNumColumns = self.plotProperties[prevCountPlot][0]
			lastCatColumns = self.plotProperties[prevCountPlot][1]
		self.workflow.add(selectedPlotType,
						  self.dfClass.currentDataFile,
						  addInfo = {
						  'funcPlotterR':'reverse_plotting',
						  'argsPlotterR':{'plotCount':self.plotCount},
						  'funcAnalyzeR':'update_receiver_box',
						  'argsAnalyzeR':{'numericColumns':lastNumColumns,'categoricalColumns':lastCatColumns},
						  'description':
						  OrderedDict([('Activity:','Plotting - {} plot'.format(selectedPlotType)),
						  ('Description:','Data were plotted using the selected chart type.'),
						  ('Numeric Columns:',numericColumns),
						  ('Categorical Columns:',categoricalColumns),
						  ('Color Map:',colorMap),
						  ('Data ID:',self.dfClass.currentDataFile)])}, 
						  isChart = True)
		if selectedPlotType == 'corrmatrix':
				self.add_tooltip_info([])     
		
	def reverse_plotting(self,plotCount):
		
		if plotCount not in self.plotHistory:
			return
		
		del self.plotHistory[plotCount]
		del self.plotProperties[plotCount]
		self.plotCount -= 1 
		
		
		if plotCount == 1:
			
			self.clean_up_figure()
			self.redraw()
			
		
		else:
			
			self.reinitiate_chart()
				
	
	def reinitiate_chart(self, id = None, updateData = False):
		'''
		Reinitiate chart replots the last displayed chart when a saved session
		is opened-
		'''
		if self.plotCount not in self.plotHistory:
			return 
		plotterHelper = self.plotHistory[self.plotCount] 
		for helper in plotterHelper:
			if helper is not None:
				self.clean_up_figure()
				helper.replot(updateData)				
		self.redraw()

			
	def define_new_figure(self, figure):
		'''
		'''
		self.figure = figure
		for keys, plotHelper in self.plotHistory.items():
			for helper in plotHelper:
				if helper is not None:
					helper.define_new_figure(figure)
		
	def replot(self):
		'''
		'''
		if self.plotCount in self.plotProperties:
			self.initiate_chart(*self.plotProperties[self.plotCount])	
	
	@property
	def current_plot_settings(self):
		'''
		'''
		return self.plotProperties[self.plotCount]
				
	def get_lenghts_of_lists(self,inputLists):
		'''
		Utility - Calculates length of lists and returns list with integers
		To do - make it util module
		'''
		lengthOfLists = [len(x) for x in inputLists]
		return lengthOfLists
	
	
	def get_number_of_axis(self,axisInput):
		'''
		Return the integer of a specific axis in the current figure.
		'''
		
		for n,axis in enumerate(self.figure.axes):
			if axis == axisInput:
				return n
			else:
				pass
	
	def get_dataID_used_for_last_chart(self):
		'''
		Return dataID that was used in the last chart. 
		The data are stored by this ID in the self.sourceData
		collection. 
		'''
		helper = self.get_active_helper()
		if helper is not None:
			dataID = helper.dataID
			return dataID
		else:
			return None

	def set_axis_props(self):
		'''
		'''
		self.logAxes = {'y':False,'x':False}
		self.centerAxes = {'y':False,'x':False}
	
	def set_data_frame_of_last_chart(self):
		'''
		'''
		dataId = self.get_dataID_used_for_last_chart()
		self.dfClass.set_current_data_by_id(dataId)
		
	def get_axes_of_figure(self):
		'''
		Return all axes of a figure.
		'''
		return self.figure.axes 
		
	def get_active_helper(self):
		'''
		Returns the active helper function e.g. categorical or 
		non-categorical helper. 
		'''
		if len(self.plotHistory) != 0:
			if self.plotCount not in self.plotHistory:
				## emergency to avoid error when plotting was unsuccessful 
				self.plotCount -= 1
			for helper in self.plotHistory[self.plotCount]:
				if helper is not None:
					return helper
		else:
			return None	
					
	def redraw(self):
		'''
		Redraws the canvas
		'''
		for tooltip in self.tooltips.values():
			tooltip.set_invisible(update =False)
		
		self.figure.canvas.draw() 
		
		self.update_tooltip_background()
			
	def update_tooltip_background(self, event=None, redraw_ = False, updateProps = False):
		'''
		Updates the background of a tooltip object.
		'''	
		for tooltip in self.tooltips.values():
			tooltip.update_background(redraw = redraw_)
			if updateProps:
				tooltip.extract_ax_props()
	def set_scatter_point_properties(self,color = None,alpha = None,size = None):
		'''
		'''
		
		if size is not None:
			self.sizeScatterPoints = size
			self.settings_points['sizes'] = [size]
		if alpha is not None:
			self.alphaScatterPoints = alpha
			self.settings_points['alpha'] = alpha
		if color is not None:
			self.colorScatterPoints = color
		helper = self.get_active_helper()
		if hasattr(helper, 'get_scatter_props'):
			helper.get_scatter_props()
			
	def get_scatter_point_properties(self):
		'''
		'''
		return self.sizeScatterPoints,self.alphaScatterPoints,self.colorScatterPoints 

	def save_axis_limits(self):
		'''
		'''
		axesLimits = []
		for n,ax in enumerate(self.get_axes_of_figure()):
			xLim = ax.get_xlim()
			yLim = ax.get_ylim()
			axesLimits.append([xLim,yLim])
		
		self.axesLimits[self.plotCount] = axesLimits

	
	def set_style_collection_settings(self, edgecolor='black',linewidth=0.4,zorder=5,alpha=0.75,
             					sizes = [50]):
		'''
		Sets settings for collections that they appear in a cool style
		'''
		self.settings_points = dict(edgecolor=edgecolor,linewidth=linewidth,
									zorder=zorder,alpha=alpha,sizes = sizes)
									
	def style_collection(self,ax = None):
		'''
		Actually modifies the style of the collection
		'''
		if self.currentPlotType not in ['swarm','pointplot','grid_search_results']:
			return
		if ax is None:
			axes = self.get_axes_of_figure()
		else:
			axes = ax
		for ax in axes:  
				axCollections = ax.collections
				for collection in axCollections:
					
					collection.set(**self.settings_points)
				#leg = ax.get_legend()
				#if leg is not None and self.splitCategories: # if this is false we used patches to show legend
					#for handle in leg.legendHandles:
				#		handle.set(**self.settings_points)
		
	def set_limits_by_plotCount(self,plotCount,subplotNum,axis):
		'''
		Define axis limits
		'''
		if plotCount not in self.axesLimits:
			self.save_axis_limits()
		axesLimits = self.axesLimits[plotCount]
		self.set_limits_in_replot(ax,axesLimits[subplotNum])
	

	def log_axes(self,which='x', axes = None):
		'''
		Use log scale on particular axis
		Parameter 
		===========
		which - define which axes to be used. (x,y) 
		'''
		if self.currentPlotType in ['hclust','corrmatrix','cluster_analysis']:
			return		
		if axes is None:
			axes = self.get_axes_of_figure()
		for ax in axes:
			if self.logAxes[which]:
				scale = 'linear'
				self.logAxes[which] = False
			else:
				scale = 'symlog'
				self.logAxes[which] = True
			if which == 'x':
				ax.set_xscale(scale)
			elif which == 'y':
				ax.set_yscale(scale)
		self.update_axes_scales()
				
	def center_axes(self,which='x',lim = (0,1), axes = None):
		'''
		Center axis around 0.
		Parameter 
		===========
		which - define which axes to be used. (x,y) 
		'''
		if self.currentPlotType in ['hclust','corrmatrix','cluster_analysis']:
			return
		if axes is None:
			axes = self.get_axes_of_figure()
		for ax in axes:
			if self.centerAxes[which]:
				self.centerAxes[which] = False
			else:
				self.centerAxes[which] = True
				
			if which == 'x':
				ax.set_xlim(lim)
			elif which == 'y':
				ax.set_ylim(lim)
		self.update_axes_scales()
		
	
	def update_axes_scales(self):
		'''
		Update these params to the helper function
		'''
		plotter = self.get_active_helper()
		plotter.set_axes_modifications([self.logAxes,self.centerAxes])
		
		
	def reset_limits(self,subplotIdNumber,axisExport):
		'''
		Reset limits to axisExport by subplotIdNumber.
		'''
		
		axes = self.get_axes_of_figure()
		ax = axes[subplotIdNumber]
		axisExport.set_ylim(ax.get_ylim())
		axisExport.set_xlim(ax.get_xlim())
		
	def set_limits_in_replot(self,ax,limits):
		'''
		Sets the axis limits.
		Parameter 
		=============
		ax - axis to be changed
		limits - list with xLim and yLim in it
		'''
		xLim,yLim = limits
		ax.set_xlim(xLim)
		ax.set_ylim(yLim)		
			
	def set_split_settings(self, boolUpdate):
		'''
		Defines if categories should be split (and propably be separated in a 
		different subplot (nCategories > 2). If split_categories = False
		Then data are plotted versus the complete population. (Only possible if 
		two categories present and one of them is replaceObjectNan (from data module). 
		''' 
		if boolUpdate != self.splitCategories:
			self.splitCategories = boolUpdate
			if self.plotCount in self.plotProperties:
				self.initiate_chart(*self.plotProperties[self.plotCount])
		else:
			return
		
	def update_cluster_anaylsis_evalScores(self, scoreDict, clusterLabels):
		'''
		'''
		id = len(self.clusterEvalScores)
		self.clusterEvalScores[id+1] = scoreDict 
		self.clusterLabels = clusterLabels
		
		
	def save_statistics(self,params,resultDf ,type = 'sigLines'):
		'''
		Paramaeter
		========
		params - must be nested dict indicating either text or significance
				lines
		resultDf - pandas data frame with saved data
		'''
		self.statistics['{}_{}'.format(type,self.plotCount)] = params
		self.statistics['dfResults_{}_{}'.format(type,self.plotCount)] = resultDf
	
	def set_current_grid_search_results(self,data):
		'''
		Define result data by a grid search
		data - dict like
		'''
		
		self.gridSearchData = data
	
	def get_grid_search_results(self):
		'''
		'''
		
		return self.gridSearchData 
	
	def display_statistics(self,ax, axNumber = None, plotCount = None): ###IMPORTANT WITH ID OF AXIS!!
		''' 
		Shows the statistic - e.g. singifiance lines and p value
		'''
		if len(self.statistics) == 0:
			return 
		else:
			if plotCount is None:
				plotCount = self.plotCount
				
			for key, params in self.statistics.items():
				count = key.split('_')[-1]
				if 'dfResults' not in key and float(count) == float(plotCount):
					for id, props in params.items():
						if axNumber is None:
							pass
						else:
							if float(props['axisIndex']) != axNumber:
								continue
				
						xValuesLine,yValuesLine = props['linesAndText']['x'], props['linesAndText']['y']
						pValue = props['linesAndText']['pVal']	
						midXPosition, h =  props['linesAndText']['textPos']
						line = ax.plot(xValuesLine,yValuesLine,**signLineProps) 
						text_stat = ax.text(midXPosition, h, pValue, **standardTextProps)


	def set_auc_collection(self,aucClass):
		'''
		'''
		self.aucCollection = aucClass
	
	def store_auc_result(self,param):
		'''
		'''
		self.aucCollection.save_result(param)	
						
	def set_dim_reduction_data(self, calculationResults):
		'''
		A dimensional reduction calculations results in a dict having two
		keywords: 'data', 'method' and 'numericColumns'. In 'data' there is another 
		dict with keys: 'drivers','components','explained_variance', and 'predictor'
		'''
		
		self.dimRedResults = calculationResults
				
		    	      						
	def set_hClust_settings(self):
		'''
		Here we store the settings for hierarch clustering. That can be changed from
		outside this class and will be used every time we plot a new hierarch cluster.
		'''
		self.cmapClusterMap = 'RdYlBu'
		self.cmapRowDendrogram = 'Paired'
		self.cmapColorColumn = 'Blues'
		
		self.metric = self.metricRow = self.metricColumn = 'euclidean'
		self.method = self.methodRow = self.methodColumn = 'complete'
		
		self.circulizeDendrogram = False
		self.showCluster = True
		self.corrMatrixCoeff = 'pearson'
		
	def set_curveFitDisplay_settings(self,gridLayout,curveFitCollectionDict,
					subplotDataIdxDict,equalYLimits,tightLayout,labelColumn):
		'''
		'''
		self.curveFitLayout = gridLayout
		self.curveFitCollectionDict = curveFitCollectionDict
		self.subplotDataIdxDict = subplotDataIdxDict
		self.equalYLimits = equalYLimits
		self.tightLayout = tightLayout
		self.labelColumn = labelColumn
		
	def set_selectedCurveFits(self,curveFitList):
		'''
		'''
		self.curveFitList = curveFitList

	def set_size_interval(self,min,max):
		'''
		'''
		self.minSize = min
		self.maxSize = max 
		
	def get_size_interval(self):
		'''
		'''
		
		return self.minSize, self.maxSize

	def set_dist_settings(self,bool = False):
		'''
		Controls how the density should be calculated density in a density plot.
		'''
		if self.plotCumulativeDist != bool:
			self.plotCumulativeDist = bool
			self.initiate_chart(*self.plotProperties[self.plotCount])
			
	
			
	def get_dist_settings(self):
		'''
		Returns the settings that is used to calculate the density
		'''
		return self.plotCumulativeDist 	
		
	def get_hClust_settings(self):
		'''
		Returns als needed hclust settings
		'''
		return 	self.cmapClusterMap, self.cmapRowDendrogram, self.cmapColorColumn,\
		self.metricRow, self.metricColumn, self.methodRow, self.methodColumn, self.circulizeDendrogram,\
		self.showCluster

	def remove_color_level(self):
		
		if self.currentPlotType in ['scatter','PCA']:
			if self.nonCategoricalPlotter is not None:
				self.nonCategoricalPlotter.reset_color_and_size_level(resetColor=True)
			else:
				self.categoricalPlotter.scatterWithCategories.remove_color_and_size_changes(which='color')
		elif self.currentPlotType == 'line_plot':
			self.nonCategoricalPlotter.linePlotHelper.remove_color()
				
	def remove_size_level(self):
		'''
		Removes any changes in size of scatter points
		'''
		if self.currentPlotType in ['scatter','PCA']:
			if self.nonCategoricalPlotter is not None:
				self.nonCategoricalPlotter.reset_color_and_size_level(resetSize=True)
			else:
				self.categoricalPlotter.scatterWithCategories.remove_color_and_size_changes(which='size')
				
	def adjust_grid_and_box_around_subplot(self, axes = None, 
											boxBool = None, gridBool = None ):
		'''
		Two helper functions to adjust bbox and grids
		'''
		def change_box_setting(boolBox,axes):
			for ax in axes:
				if ax not in self.immutableAxes:
					ax.spines['right'].set_visible(boolBox)
					ax.spines['top'].set_visible(boolBox)	
					
		def change_grid_setting(boolGrid,axes):
			for ax in axes:
				if ax not in self.immutableAxes:
					if boolGrid:
						ax.grid(color='darkgrey', linewidth = 0.15)
					else:
						ax.grid('off')
								
		if self.currentPlotType in ['hclust','corrmatrix']:
			return
		if axes is None:
			axes = self.axes
			
		if boxBool is None: 
			boxBool = self.showSubplotBox
		if gridBool is None:
			gridBool = self.showGrid
			
		change_box_setting(boxBool,axes)	
		change_grid_setting(gridBool,axes)		
				
	
	def add_annotationLabel_to_plot(self,ax,text,xy = None, xytext = None, rotation = None,
					position='topleft', xycoords = 'axes fraction', arrowprops = None):
		'''
		'''
		ha = 'left'
		va = 'top'
		
		if isinstance(text,str) == False:
			text = str(text)
		if position == 'topleft':
			coordAxes = (0.05,0.95)
		elif position == 'bottomright':
			coordAxes = (0.9,0.05)
			va = 'bottom'
			ha = 'right'
		else:
			coordAxes = xy
		xycoords = xycoords

		annLabel = ax.annotate(text,xy = coordAxes, xytext = xytext, xycoords = xycoords,
					ha = ha, va= va, arrowprops=arrowprops, rotation = rotation) 
		annLabel.draggable(state=True, use_blit =True)
	

	def add_scatter_collection(self,ax,x,y, color = None, size=None,alpha = None,label=None,
									returnColl = False, picker=False):
		'''
		'''
		if color is None:
			color = self.colorScatterPoints
		if size is None:
			size = self.sizeScatterPoints
		if alpha is None:
			alpha = self.alphaScatterPoints
		
		collection = ax.scatter(x,y, edgecolor = 'black',
					linewidth = 0.3, s = size,
					alpha =  alpha, 
					color = color,
					label = label,
					picker = picker)	
		if returnColl:
			return collection
		else:
			return None


	def add_tooltip_info(self,annotationColumnList,scatterCombination=None,redraw=True):
		'''
		Add tooltip information.
		'''
		if self.currentPlotType == 'scatter_matrix':
			
			combinationsID , axesInScatterMatrix = zip(*list(self.nonCategoricalPlotter._scatterMatrix.axisWithScatter.values()))
		
		elif self.currentPlotType == 'scatter' and self.categoricalPlotter is not None:
			axScats = []
			for ax,_ in self.categoricalPlotter.scatterWithCategories.axes_combs.values():
				axScats.append(ax)
				
		axes = self.get_axes_of_figure()		
		
		for n,ax in enumerate(axes):
			if (self.currentPlotType in ['scatter','scatter_matrix','line_plot']) or \
			(self.currentPlotType in ['cluster_analysis','PCA'] and n == 0) or \
			(self.currentPlotType  in ['hclust','corrmatrix'] and n == 2) or \
			(self.currentPlotType  == 'hclust' and n == 0 and self.circulizeDendrogram):
				if self.currentPlotType == 'PCA':
					
					numericColumns = ['Comp_1','Comp_2']
					
				elif self.currentPlotType == 'scatter' and \
				self.categoricalPlotter is not None:
				
					if ax not in axScats:
						continue
					numericColumns = None
						
				elif self.currentPlotType == 'scatter_matrix':
					if ax in axesInScatterMatrix:
						idx = axesInScatterMatrix.index(ax)
						scatterCombination = combinationsID[idx]
						numericColumns = [self.nonCategoricalPlotter._scatterMatrix.numericColumns[idx] for idx in scatterCombination]
						if idx == 0:
							redraw = True
						else:
							redraw = False
					else:
						continue
				else:
					numericColumns = None
					
				self.tooltips[n] = chartToolTip(self,ax,'')
				self.tooltips[n].update_background(redraw)
				
				self.onMotionEvents[n] = self.figure.canvas.mpl_connect('motion_notify_event', self.on_tooltip_hover)			
				
				if self.currentPlotType not in ['hclust','corrmatrix']:
					self.tooltips[n].annotate_data_in_collections(self.dfClass,
															annotationColumnList,
															numericColumns,axisId = n,
															scatterCombination = scatterCombination)
					ax.callbacks.connect('ylim_changed', \
					lambda event:self.update_tooltip_background(redraw_ = True,updateProps=True))
					
				else:
						
					self.tooltips[n].annotate_cluster_map(self.dfClass,annotationColumnList,self.currentPlotType)	
						
							
	def on_tooltip_hover(self,event):
  		'''
  		Handles hover events.
  		'''
  		if event.inaxes:
  			n = self.get_number_of_axis(event.inaxes)
  			if n in self.tooltips:
  			
  				if self.currentPlotType in ['hclust','corrmatrix']:
  					self.tooltips[n].evaluate_event_in_cluster(event)
  				elif self.currentPlotType == 'line_plot':
  					self.tooltips[n].evaluate_event_in_lineCollection(event)
  				else:
  					self.tooltips[n].evaluate_event_for_collection(event)
  		else:
  			for tooltip in self.tooltips.values():
  				tooltip.set_invisible()        
         
	
					
					
	def setup_basic_design(self):
		'''
		Setups some parameters to obtain stylish charts. One could also
		change these parameters in the matplotrc file.
		'''
		
		plt.rc('legend',**{'fontsize':8})
		plt.rc('font',size = 8)
		plt.rc('axes',titlesize = 8)
		plt.rc('axes', labelsize=9)
		
		plt.rc('xtick', labelsize = 8, direction = 'in')
		plt.rc('ytick', labelsize= 8,direction = 'in')
		
		plt.rc('xtick.major', size=3,pad=2,width=0.5)
		plt.rc('ytick.major', size= 3,pad=2,width=0.5)
		
		matplotlib.rc('axes', linewidth = 0.6)	

		matplotlib.rcParams['savefig.directory'] = os.path.dirname(sys.argv[0])
		matplotlib.rcParams['savefig.dpi'] = 600      
		#matplotlib.rcParams['figure.facecolor'] = '#FDF6E3'
		#matplotlib.rcParams['axes.labelcolor'] = '#657b83'
	def __getstate__(self):
		'''
		Promotes sterilizing of this class (pickle)
		'''		
		state = self.__dict__.copy()
		for list in [ 'axes', 'figure']:#, 'nonCategoricalPlotter', 'plotHistory']:
			if list in state:
				del state[list]
		return state			
	



class categoricalPlotter(object):

	def __init__(self,_PlotterClass,sourceDataClass,figure, numericColumns,
						numbNumbericColumns,categoricalColumns,numbCategoricalColumns,
						selectedPlotType,colorMap, specificAxis = None):
	
		self.inmutableCollections = []
		self.plotter = _PlotterClass
		self.figure = figure
		self.numericColumns = numericColumns
		self.numbNumericColumns = numbNumbericColumns
		self.categoricalColumns = categoricalColumns
		self.numbCategoricalColumns = numbCategoricalColumns
		self.currentPlotType = selectedPlotType
		
		self.colorMap = colorMap
		self.dfClass = sourceDataClass
		self.dataID = sourceDataClass.currentDataFile
		
		if selectedPlotType == 'curve_fit':
			self.labelColumnForFits = self.plotter.labelColumn 
			if self.labelColumnForFits in self.dfClass.df.columns and \
			self.labelColumnForFits not in self.categoricalColumns:
				self.categoricalColumns.append(self.labelColumnForFits)
				

		
		self.axisDict = dict() 
		self.selectedPlotType = selectedPlotType
		self.adjustYLims = bool(self.plotter.equalYLimits)
		self.tightLayout = bool(self.plotter.tightLayout)

		self.get_data() 

		self.error = self.plotter.errorBar
		self.add_axis_to_figure() 
		
		self.filling_axis(selectedPlotType) 
		
		if self.plotter.addSwarm:
			self.add_swarm_to_plot()
			self.addSwarm = True
		else:
			self.addSwarm = False

		self.logAxes = self.plotter.logAxes.copy()
		self.centerAxes = self.plotter.centerAxes.copy()
	
	def get_data(self):
				
		
		if self.selectedPlotType != 'grid_search_results':
			columnList = self.numericColumns+self.categoricalColumns
			self.data = self.dfClass.get_current_data_by_column_list(columnList = columnList)
			
			
		else:
			self.data = self.plotter.get_grid_search_results() 
			
	def set_axes_modifications(self,dicts):
		'''
		'''
		self.logAxes, self.centerAxes = dicts	
		
	def bind_label_event(self, labelColumnList):
		'''
		'''
		if self.scatterWithCategories is not None:	
			self.scatterWithCategories.bind_label_event(labelColumnList)		
	
	def adjust_axis_scale(self, axes = None):
		'''
		'''
		if axes is None:
			axes = list(self.axisDict.values)
		for which,bool in self.logAxes.items():
				if bool:
					for ax in axes:
						if which == 'y':
							ax.set_yscale('symlog')
						else:
							ax.set_xscale('symlog')
					
						
	def add_axis_to_figure(self):
		'''
		Adds the needed axis for plotting. The arangement depends on the number of categories
		'''
		self.figure.subplots_adjust(bottom=.15,top=.88,left=.15)
		if self.currentPlotType == 'scatter':
			return
		elif self.currentPlotType == 'grid_search_results':
			return
		if self.currentPlotType == 'countplot':
		
			rows,cols = self.get_grid_layout_for_plotting(n=self.numbCategoricalColumns)
			for n,catColumn in enumerate(self.categoricalColumns):
				self.axisDict[n] = self.figure.add_subplot(rows,cols,n+1) 
			self.figure.subplots_adjust(wspace=0.31)
			
		elif self.currentPlotType in ['boxplot','barplot','violinplot','swarm','pointplot']:
		
			if self.plotter.splitCategories == False:
				
				rows,cols = self.get_grid_layout_for_plotting(self.numbNumericColumns)
				self.figure.subplots_adjust(wspace=0.31,hspace=0.15)
				for n in range(self.numbNumericColumns):
					self.axisDict[n] = self.figure.add_subplot(rows,cols,n+1) 
					

			elif self.numbCategoricalColumns == 1:
				
				ax_ = self.figure.add_subplot(221)
				self.firstCategoryLevels = self.data[self.categoricalColumns[0]].unique() 
				self.firstCategoryLevelsSize = self.firstCategoryLevels.size
				self.adjust_margin_of_figure(multFactor= (self.firstCategoryLevelsSize*self.numbNumericColumns))
				self.axisDict[0] = ax_

			elif self.numbCategoricalColumns == 2:
			
				rows,cols = self.get_grid_layout_for_plotting(self.numbNumericColumns)
				self.figure.subplots_adjust(wspace=0.36, hspace=0.36)  
				for n,numColumn in enumerate(self.numericColumns):
					
					self.axisDict[n] = self.figure.add_subplot(rows,cols,n+1)
					
			elif self.numbCategoricalColumns == 3:
				self.namesOfSubplotSplits = self.data[self.categoricalColumns[2]].unique()
				self.numberOfSubplotsCols = self.namesOfSubplotSplits.size	
				self.numberOfSubplots = self.numberOfSubplotsCols * self.numbNumericColumns
				rows,cols = self.get_grid_layout_for_plotting( n = self.numberOfSubplots,
																 cols = self.numberOfSubplotsCols)
				for n in range(self.numberOfSubplots):
					
					self.axisDict[n] = self.figure.add_subplot(rows,cols,n+1)
				self.adjust_margin_of_figure(self.numberOfSubplotsCols*1.7)
				
					
				self.figure.subplots_adjust(wspace=0, hspace=0.36) 
		
		elif self.currentPlotType == 'curve_fit':	
				gridLayout = self.plotter.curveFitLayout 
				row, columns = gridLayout
				sumAxis = row * columns
				
				for n in range(sumAxis):
					self.axisDict[n] = self.figure.add_subplot(row,columns,n+1)
				
				if self.tightLayout:
					self.figure.subplots_adjust(right=0.88 ,wspace=0, hspace=0)  
				else:
					self.figure.subplots_adjust(right=0.88, wspace=0.22, hspace=0.22)  
					
		elif self.currentPlotType == 'density':
				
				rows,cols = self.get_grid_layout_for_plotting(self.numbNumericColumns)
				self.figure.subplots_adjust(wspace=0.36, hspace=0.36)  
				for n,numColumn in enumerate(self.numericColumns):
					
					self.axisDict[n] = self.figure.add_subplot(rows,cols,n+1)
	@property
	def columns(self):
		return [self.numericColumns,self.categoricalColumns] 	
    				
				
	def replot(self, updateData = False):
		'''
		'''
		if updateData:
			self.get_data()
			
		if self.currentPlotType == 'scatter':
			self.scatterWithCategories.figure = self.figure
			self.scatterWithCategories.replot()
		else:
			self.axisDict = dict() 
			self.add_axis_to_figure() 
			self.filling_axis(self.selectedPlotType) 
		
		if len(self.inmutableCollections) != 0:
			self.add_swarm_to_plot()
			
		axesLimits = self.plotter.axesLimits[self.plotter.plotCount]
		for ax in self.figure.axes:
			axNum = self.plotter.get_number_of_axis(ax)	
			self.plotter.display_statistics(ax,axNum)
			self.plotter.set_limits_in_replot(ax,axesLimits[axNum])
			
		
					
	def filling_axis(self,plotType,onlySelectedAxis = None, axisExport = None, forceLegend = False):
		'''
		Takes care of data arrangements and plotting in created axis.
		'''
		if plotType == 'countplot':
		
			totalRows = len(self.data.index)
			for n,catColumn in enumerate(self.categoricalColumns):
				if onlySelectedAxis is not None:
					if n != onlySelectedAxis:
						continue
					else:
						ax = axisExport
				else:
					ax = self.axisDict[n]
				
				
				groupCounts = self.data.groupby([catColumn],sort=False).size()
				namesCounts = ['Compl.'] + list(groupCounts.index)
				valueCounts = [totalRows] + groupCounts.tolist()
				x = range(len(valueCounts))
				ax.bar(x, valueCounts)
				ax.set_xticks(x)
				ax.set_xticklabels(namesCounts)
				axisStyler(ax,ylabel='Counts',title = catColumn,
							rotationXTicks=90, #yLabelFirstCol = True,
							xLabelLastRow = True) 
		
		elif plotType == 'density':
			groupedData = self.data.groupby(self.categoricalColumns, sort=False)
			groupNames = [name for name,group in groupedData] #ugly but grouped.data.groups.keys() has random order
			colorDict = match_color_to_uniqe_value(groupNames ,self.colorMap)
			cdf = self.plotter.get_dist_settings()
			for n,numbColumn in enumerate(self.numericColumns):
			
				if onlySelectedAxis is not None:
					if n != onlySelectedAxis:
						continue
					else:
						ax = axisExport
				else:
					ax = self.axisDict[n]
				
				for name,group in groupedData:
					dataForPlot = group[numbColumn].dropna().values 
					if dataForPlot.size == 0:
						continue
					else:
						sns.distplot(dataForPlot, ax=ax, color = colorDict[name], hist=False,
									hist_kws={'cumulative':cdf},
									kde_kws={'cumulative':cdf})
					del dataForPlot
					
					ax.plot([],[],c = colorDict[name], label=name)
					if ax.is_first_col():
						titleLegend = get_elements_from_list_as_string(self.categoricalColumns,addString = 'Levels: ')
						kwsLegend = dict(leg_title=titleLegend)
						ylabel = 'Density'
					else:
						kwsLegend = dict() 
						ylabel = ''
						
					axisStyler(ax, xlabel = numbColumn, ylabel = ylabel, 
								nTicksOnYAxis = 4,nTicksOnXAxis = 4, 
								addLegendToFirstSubplot = True,
								kwsLegend= kwsLegend, forceLegend = forceLegend)

			 				
		elif plotType in ['boxplot','barplot','violinplot','swarm','add_swarm','pointplot']:
			
			
			if self.plotter.splitCategories == False:				
				
				for n,numColumn in enumerate(self.numericColumns):
					
					if onlySelectedAxis is not None:
						if n  != onlySelectedAxis:
							continue
						else:
							ax = axisExport
					else:
						ax = self.axisDict[n]
					dataCombined, complColumns = self.dfClass.get_positive_subsets([numColumn], self.categoricalColumns, self.data)

					dataForPlotting = pd.melt(dataCombined, id_vars = 'intIdxInstant', 
												value_name = 'Value', var_name = 'Column')
					dataForPlotting.dropna(subset=['Value'],inplace=True)					
					
					fill_axes_with_plot(ax=ax, x='Column',y='Value',hue = None,
									plot_type = plotType,cmap=self.colorMap,data=dataForPlotting,
									order = complColumns, dodge = 0, error = self.error)
					
					if self.numbNumericColumns > 3:
						removeXTicks = True
					else:
						removeXTicks = False
						
					axisStyler(ax,xlabel = '',ylabel = numColumn,
								rotationXTicks=90,nTicksOnYAxis=4,
								addLegendToFirstSubplot = True, 
								removeXTicks = removeXTicks,
								forceLegend = forceLegend,
								kwsLegend = {'addPatches':True,
											'legendItems' : complColumns,
											'colorMap' : self.colorMap,
											'leg_title':'Categorical Columns = +',}) 
		
			elif self.numbCategoricalColumns == 1:

				if onlySelectedAxis is not None:
					ax = axisExport		
				else:
					ax = self.axisDict[0]
				
				if self.numbNumericColumns > 1:
					
						
					sourcePlotData = pd.melt(self.data, 
							self.categoricalColumns[0], 
							var_name = "Columns", 
							value_name = "Value")
				
				kwsLeg = {'leg_title':self.categoricalColumns[0]}
		
				if self.numbNumericColumns != 1:
					
					fill_axes_with_plot(ax=ax,x='Columns',y='Value',hue = self.categoricalColumns[0],
									plot_type = plotType,cmap=self.colorMap,data=sourcePlotData,
									order = self.numericColumns,dodge = 0, 
									hue_order = sourcePlotData[self.categoricalColumns[0]].unique(),
									inmutableCollections = self.inmutableCollections, error = self.error)
					addLeg = True
				
				else:
					fill_axes_with_plot(ax=ax,x = self.categoricalColumns[0], y = self.numericColumns[0], hue = None,
										plot_type = plotType, order = self.firstCategoryLevels,
										data = self.data, cmap = self.colorMap, dodge=0,
										error = self.error)
					addLeg = False
					kwsLeg  = {}
					
				axisStyler(ax,rotationXTicks=90,xlabel= '', nTicksOnYAxis=4,
								addLegendToFirstCol = addLeg,
								kwsLegend= kwsLeg)
				
			elif self.numbCategoricalColumns == 2:
			
				xAxisOrder = self.data[self.categoricalColumns[0]].unique()
				hueOrder = self.data[self.categoricalColumns[1]].unique()
				colorDict = match_color_to_uniqe_value(xAxisOrder,self.colorMap)
				
				for n,numColumn in enumerate(self.numericColumns):
					if onlySelectedAxis is not None:
						if n != onlySelectedAxis:
							continue
						else:
							ax = axisExport
					else:
						ax = self.axisDict[n]

					fill_axes_with_plot(ax = ax,x= self.categoricalColumns[0], y = numColumn, hue = self.categoricalColumns[1],
										data = self.data, order = xAxisOrder, hue_order = hueOrder,
										plot_type = plotType, cmap = self.colorMap,
										inmutableCollections = self.inmutableCollections,
										error = self.error)
					leg = ax.get_legend()
					if leg is not None: leg.remove()					
					axisStyler(ax,rotationXTicks=90,nTicksOnYAxis=4,addLegendToFirstSubplot = True,
								forceLegend = forceLegend,
								kwsLegend= {'leg_title':self.categoricalColumns[1]})
					
				
			elif self.numbCategoricalColumns == 3:
			
				xAxisOrder = self.data[self.categoricalColumns[0]].unique()
				hueOrder = self.data[self.categoricalColumns[1]].unique()
				colorDict = match_color_to_uniqe_value(xAxisOrder,self.colorMap)
				
				
				groupedData =  self.data.groupby(self.categoricalColumns[2],sort=False)
				 
				subId = 0
				for numColumn in self.numericColumns:
				
					for name,group in groupedData:
						ax = self.axisDict[subId]
						
						if onlySelectedAxis is not None:
							if subId != onlySelectedAxis:
								subId += 1
								continue 
							else:
								ax = axisExport						
						
						fill_axes_with_plot(ax = ax,x= self.categoricalColumns[0], 
											y = numColumn, hue = self.categoricalColumns[1],
											data = group, order = xAxisOrder, hue_order = hueOrder,
											plot_type = plotType, cmap = self.colorMap,
											inmutableCollections = self.inmutableCollections,
											error = self.error)
						leg = ax.get_legend()
						if leg is not None: leg.remove()
						if plotType != 'add_swarm':
							if subId == 0:
								groupLabel = '{}:\n {}'.format(self.categoricalColumns[2],name)
							else:
								groupLabel = name
							self.plotter.add_annotationLabel_to_plot(ax,groupLabel)
						if self.numbNumericColumns == 1:
							xLabelLastRow = False
						else:
							xLabelLastRow = True
						axisStyler(ax,nTicksOnYAxis=4, xlabel = self.categoricalColumns[0], xLabelLastRow = xLabelLastRow,
														ylabel = 'mean({})'.format(numColumn), yLabelFirstCol = True,
														rotationXTicks = 90,addLegendToFirstSubplot = True,
														forceLegend = forceLegend,
														kwsLegend= {'leg_title':self.categoricalColumns[1]})
														
						subId += 1
				
		#self.aggregateScatterWithCategories = True
		#self.aggregateMethod = 'count'		
		
		elif plotType == 'scatter':
		
				self.scatterWithCategories = scatterWithCategories(self.plotter,self.dfClass,
								self.figure, self.categoricalColumns,self.numericColumns,
								self.colorMap)
	
		elif plotType == 'grid_search_results':
		
			self.gridSearchPlotter = gridSearchVisualization(self.plotter,self.data)
			
		elif plotType == 'curve_fit':
			
			
			self.columnsForFit = dict() 
			self.xValuesForFit = dict() 
			self.fitFuncForFit = dict()
			self.collectMinAndMax = []
			
			self.subplotDataIdxDict = self.plotter.subplotDataIdxDict.copy()
			mulitpleCurvefits = len(self.subplotDataIdxDict) == 0
			lenData = len(self.data.index)
			
			
			
			for fitId in self.plotter.curveFitList:
			
				self.columnsForFit[fitId] = self.plotter.curveFitCollectionDict[fitId]['columnNames']
				self.xValuesForFit[fitId] = self.plotter.curveFitCollectionDict[fitId]['xValues']
				self.fitFuncForFit[fitId] = self.plotter.curveFitCollectionDict[fitId]['fittingFunc']
				
				
			for n, ax in self.axisDict.items():
			 
				if onlySelectedAxis is not None:
					if n != onlySelectedAxis:
						continue
					else:
						ax = axisExport
				else:
					## ax is already defined, compared to other plot types the curve fit is special
					pass
				
				## get data 
				if mulitpleCurvefits:
					# this is true if no custom layout is designed
					if n >= lenData:
						self.figure.delaxes(ax)
						continue
						
					subsetData = self.data.iloc[n]
				else:
					idxList = self.subplotDataIdxDict[n]
					if len(idxList) == 0:
						self.figure.delaxes(ax)
						continue
					subsetData = self.data.loc[idxList,:]
					
				numFit = 0
				for fitId, columnNames in self.columnsForFit.items():
										
					xValues = self.xValuesForFit[fitId]

					if mulitpleCurvefits:
						yValues = subsetData[columnNames].values
						try:
							xValues,yValues = self.filter_x_and_y_for_nan(xValues,yValues)
						except:
							pass
						if yValues.size == 0:
							continue
						if True:
							coeffFuncs = self.get_fit_properties(self.plotter.curveFitCollectionDict[fitId]['fitData'],
									subsetData.name,self.fitFuncForFit[fitId])
							xLine,yLine, argMaxY = self.calculate_line_for_fit(xValues,self.fitFuncForFit[fitId],coeffFuncs)
							
							if numFit == 0:					
								if self.labelColumnForFits not in self.data.columns:
									label = 'ID: {}'.format(subsetData.name)
								else:
									label = str(subsetData[self.labelColumnForFits])
								self.plotter.add_annotationLabel_to_plot(ax,label,
																	  xy = (xLine.item(argMaxY),yLine.item(argMaxY))) 
							ax.plot(xLine,yLine, label = fitId)	
						else:
							pass
						
						if xValues.size > 0 and yValues.size == xValues.size: 
							ax.plot(xValues,yValues, marker='o',ls=' ', markerfacecolor='white', 
								markersize=7, markeredgewidth = 0.4 , markeredgecolor='black')	
						numFit += 1
					else:
						
						colors = sns.color_palette(self.colorMap,len(subsetData.index))
						for n,rowIdx in enumerate(subsetData.index):
							yValues = subsetData[columnNames].loc[rowIdx,:]
							try:
								xValues,yValues = self.filter_x_and_y_for_nan(xValues,yValues)
							except:
								continue
							try:
								coeffFuncs = self.get_fit_properties(self.plotter.curveFitCollectionDict[fitId]['fitData'],rowIdx,self.fitFuncForFit[fitId])
								xLine,yLine, argMaxY = self.calculate_line_for_fit(xValues,self.fitFuncForFit[fitId],coeffFuncs)
								if len(subsetData.index) > 1:
									self.plotter.add_annotationLabel_to_plot(ax,'ID: {}'.format(rowIdx),
																	  xy = (xLine.item(argMaxY),yLine.item(argMaxY)), 
																	  position='defined', 
																	  xycoords = 'data', 
																	  arrowprops=arrow_args)
									ax.plot(xLine,yLine, label = fitId, c = colors[n])		
							except:
								pass
							if xValues.size > 0 and yValues.size > 0:
								ax.plot(xValues,yValues, marker='o',ls=' ', markerfacecolor=colors[n], 
									markersize=7, markeredgewidth = 0.4,markeredgecolor="black")								
								
					if self.tightLayout:
					
						axisStyler(ax,nTicksOnYAxis =  4, ylabel = 'Value',yLabelFirstCol = True, 
    					   showYTicksOnlyFirst = True, addLegendToFirstSubplot = True)	
					else:
						axisStyler(ax,nTicksOnYAxis =  4, ylabel = 'Value',yLabelFirstCol = True, 
    					   showYTicksOnlyFirst = False, addLegendToFirstSubplot = True)	    
				
			if self.adjustYLims: 
					axes = self.figure.axes 
					yMin, yMax = zip(*self.collectMinAndMax)
					yMinOfAll, yMaxOfAll = min(yMin), max(yMax)
					newYLim = (yMinOfAll-0.05*yMinOfAll, yMaxOfAll+0.05*yMaxOfAll)
					for ax in axes:
						ax.set_ylim(newYLim)
					
	def change_nan_color(self,newColor):
		'''
		'''
		if hasattr(self,'scatterWithCategories'):
			self.scatterWithCategories.change_nan_color(newColor)

	def define_new_figure(self,figure):
 		'''
 		'''
 		self.figure = figure
 		self.axisDict = {}
 		            						
	def disconnect_event_bindings(self):
		'''
		'''
		if hasattr(self,'gridSearchPlotter'):
			self.gridSearchPlotter.disconnect_events()
	
	def remove_swarm(self):
		'''
		'''
		toBeRemoved = []
		for ax in self.figure.axes:
			for collection in ax.collections:
				if collection not in self.inmutableCollections:
					toBeRemoved.append(collection)
		for coll in toBeRemoved:
			coll.remove() 
		
		self.inmutableCollections = []	
		self.plotter.addSwarm = False		
		self.addSwarm = False

			
	
	def add_swarm_to_plot(self,subplotIdNumber = None,axisExport = None, export = False):
		'''
		Adds swarm to the currently selected chart type.
		'''
		self.inmutableCollections = []
		
		if export ==  False:
			for ax in self.figure.axes:
				self.inmutableCollections.extend(ax.collections)
				if self.currentPlotType == 'barplot':
					for line in ax.lines:
						line.set_zorder(20) ## ensure that error bars are ontop of swarm

		self.filling_axis('add_swarm',subplotIdNumber,axisExport)
		self.plotter.addSwarm = True
		self.addSwarm = True
		
	def get_fit_properties(self,data, idx, func = 'non cubic fit'):
		'''
		'''
		if func != 'cubic spline':
			coeffColumn = [col for col in data.columns.values.tolist() if 'Coeff' in col]
			coeff = [float(prop) for prop in data[coeffColumn].loc[idx].str.split(',').iloc[0] if prop != self.dfClass.replaceObjectNan]
		else:
			coeffColumn = [col for col in data.columns.values.tolist() if 'quadCubicSpline' in col]
			
			splitSlinesCoeff = data[coeffColumn].loc[idx].str.split(';').iloc[0]
			
			knots = np.array([float(x) for x in splitSlinesCoeff[0].split(',')])
			bSplineCoeff = 	np.array([float(x) for x in splitSlinesCoeff[1].split(',')])
			degree = int(float(splitSlinesCoeff[2]))
			
			coeff = (knots,bSplineCoeff,degree)
		return coeff
		
		
		
	def calculate_line_for_fit(self,x, func, popts, multiply = 10):
		'''
		'''
		
		xMin = x.min()
		xMax = x.max()
		xLin = np.linspace(xMin,
							xMax,
							num = x.size * multiply,
							endpoint = True)
		#print(fitFuncsDict[func])	
		if func in fitFuncsDict:	
			yLin = fitFuncsDict[func](xLin,*popts)
		elif func == 'polynomial fit':
			yLin = np.polyval(popts,xLin)  ##np.polyval(mode,x_space)
		elif func == 'cubic spline':
			yLin = interpolate.splev(xLin, popts) 
		
		argMaxY  = np.argmax(yLin)
		if argMaxY == yLin.size - 1:
			argMaxY = int(float(argMaxY/2))
		
		return xLin,yLin,argMaxY
		
	def filter_x_and_y_for_nan(self,x,y):
		'''
		x must be a numpy array
		'''
		y = np.array(y)
		
		x = x[~np.isnan(y)]
		y = y[~np.isnan(y)]
		
		## caluclate min and max to adjust y Limits if desired by user
		if self.adjustYLims and y.size > 0 and x.size > 0:
			self.collectMinAndMax.append((y.min(),y.max()))
			
		return x,y

	def export_selection(self,axisExport, subplotIdNumber, 
			fig,limits = None, boxBool = None, gridBool = None, plotCount = None):
		'''
		Uses a specific axis to export this plot. Main purpose to use this in a main figure.
		'''
		
			
		self.filling_axis(self.currentPlotType,subplotIdNumber,axisExport,forceLegend=True)
		
		if self.addSwarm:
			self.add_swarm_to_plot(subplotIdNumber,axisExport,export=True)
		self.plotter.display_statistics(axisExport,subplotIdNumber,plotCount)
		self.plotter.adjust_grid_and_box_around_subplot(boxBool = boxBool,
														gridBool = gridBool,
														axes = [axisExport])
		self.plotter.style_collection([axisExport])
		if limits is None:
			self.plotter.reset_limits(subplotIdNumber,axisExport)
		else:
			self.plotter.set_limits_in_replot(axisExport,limits)
		
		self.adjust_axis_scale(axes=[axisExport])
		
	def get_grid_layout_for_plotting(self,n,cols=3):
		'''
		'''
		 
		rows = np.ceil(n/cols)
		if rows == 1:
			rows = 2
		return rows,cols		
		
	def adjust_margin_of_figure(self,multFactor):
		'''
		Note: emperically determined.
		'''
		
		adjustRight = 0.18  + 0.09 *multFactor
		if adjustRight > 1.8:
			adjustRight = 1.75
		self.figure.subplots_adjust(right = adjustRight)  
	
	
	def __getstate__(self):
		'''
		Remove objects that cannot be sterilized. 
		'''
		state = self.__dict__.copy()
		for attr in ['figure','axisDict']:
			if attr in state: 
				del state[attr]
		return state
			
					

		
class nonCategoricalPlotter(object):

	def __init__(self,plotter,sourceDataClass,figure, numericColumns,
						numbNumbericColumns,selectedPlotType,
						colorMap, specificAxis = None, categoricalColumns = []):
	
		self.plotter = plotter
		self.figure = figure
		
		
		self.numericColumns = numericColumns
		self.categoricalColumns = categoricalColumns
		self.numbNumericColumns = numbNumbericColumns
		self.currentPlotType = selectedPlotType
		self.dfClass = sourceDataClass
		self.dataID = sourceDataClass.currentDataFile

		self.get_data() 
		
		self.colorMap = colorMap
		self.error = self.plotter.errorBar

		self.define_variables()
		
		self.add_axis_to_figure() 
		self.filling_axis()
		if self.plotter.addSwarm:
			self.add_swarm_to_plot()
			self.addSwarm = True
		else:
			self.addSwarm = False
		self.style_axis()
	
	@property
	def columns(self):
		return [self.numericColumns,self.categoricalColumns] 	 

	def get_data(self):
		
		if self.currentPlotType == 'PCA':
			self.data = self.plotter.dimRedResults['data']['Drivers']
			self.numericColumns = self.data.columns.values.tolist()
		else:
			self.data = self.dfClass.get_current_data_by_column_list(columnList = self.numericColumns)
		if self.currentPlotType in ['scatter','cluster_analysis']:
			self.data = self.data.dropna()
			 
	def define_variables(self):
				
		self.savedLegendCollections = []
		self.inmutableCollections = []
		self.lowessData = None
		self.annotationClass = None
		self.pcaProjectionAnnotations = None
		self._hclustPlotter = None
		self._scatterMatrix = None    
		self.sizeStatsAndColorChanges = OrderedDict()
		self.axisDict = dict()  
		self.categoricalColorDefinedByUser = dict()		
		self.get_scatter_props()
		self.get_size_interval()
		self.get_agg_method()

		self.logAxes = self.plotter.logAxes.copy()
		self.centerAxes = self.plotter.centerAxes.copy()
		
	def get_size_interval(self):
		
		self.minSize, self.maxSize = self.plotter.get_size_interval()
	
	def get_agg_method(self):
		'''
		'''
		self.aggMethod = self.plotter.aggMethod	
		
	def get_scatter_props(self):
		'''
		Get the current scatter properties from the "main" plotter class.
		'''
		self.sizeScatterPoints, self.alphaScatterPoints,\
		self.colorScatterPoints = self.plotter.get_scatter_point_properties()
		
		self.binnedScatter = bool(self.plotter.binnedScatter)
	
	
	def set_axes_modifications(self,dicts):
		'''
		'''
		self.logAxes, self.centerAxes = dicts
	
	
	def adjust_axis_scale(self, axes = None):
		'''
		'''
		if axes is None:
			axes = list(self.axisDict.values)
		for which,bool in self.logAxes.items():
				if bool:
					for ax in axes:
						if which == 'y':
							ax.set_yscale('symlog')
						else:
							ax.set_xscale('symlog')			
			 	
	def add_axis_to_figure(self):
			
			self.figure.subplots_adjust(wspace=0.05, hspace = 0.05,bottom=0.15)  
			if self.currentPlotType in nonScatterPlotTypes:
				self.axisDict[0] = self.figure.add_subplot(221) 
				self.adjust_margin_of_figure_for_non_scatter()
			elif self.currentPlotType in ['hclust','scatter_matrix','corrmatrix','line_plot']:
				pass
				
			elif self.currentPlotType == 'density':
			
				row,column = self.get_grid_layout_for_plotting()
				self.figure.subplots_adjust(wspace=0.25, hspace = 0.25)
				for n,numericColumn in enumerate(self.numericColumns):
					self.axisDict[n] = self.figure.add_subplot(row,column,n+1) 
					
			elif self.currentPlotType == 'PCA':
			
				row, column = 2,2
				for n in range(3):
					self.axisDict[n] = self.figure.add_subplot(row,column,n+1)
				self.figure.subplots_adjust(wspace=0.3,hspace=0.3,right=0.9)
							
			elif self.currentPlotType == 'cluster_analysis':
				
				grid_spec = plt.GridSpec(3,3) 
				self.figure.subplots_adjust(right=0.88, hspace = 0.3)
				
				subplotspec1 = grid_spec.new_subplotspec(loc=(0,0),rowspan=2,colspan=2)
				subplotspec2 = grid_spec.new_subplotspec(loc=(2,2),rowspan=1,colspan=1)
				subplotspec3 = grid_spec.new_subplotspec(loc=(1,2),rowspan=1,colspan=1)
			            
				self.axisDict[0] = self.figure.add_subplot(subplotspec1)
				self.axisDict[1] = self.figure.add_subplot(subplotspec2)
				self.axisDict[2] = self.figure.add_subplot(subplotspec3)
				self.figure.subplots_adjust(wspace=0.35, hspace = 0.35)     
			else:
				self.axisDict[0] = self.figure.add_subplot(111) 
	

	def replot(self, updateData = False):
		'''
		This handles a replot of the initilized plot.
		It is used when a stored session is opened.
		'''
		
		
		self.createIntWidgets = False
		if self.currentPlotType in ['hclust','corrmatrix']:
			self._hclustPlotter.replot(updateData) 
		elif self.currentPlotType == 'scatter_matrix':
			self._scatterMatrix.replot()
		elif self.currentPlotType == 'scatter' and self.binnedScatter:
			self.binnedScatterHelper.replot()	
		elif self.currentPlotType == 'line_plot':
			self.linePlotHelper.replot(updateData)
		else:
			if updateData:
				self.get_data() 
				
			self.axisDict = dict() 
			self.add_axis_to_figure() 
			self.filling_axis()
			if len(self.inmutableCollections) != 0:
				self.add_swarm_to_plot()
			axesLimits = self.plotter.axesLimits[self.plotter.plotCount]
			self.style_axis()
			for ax in self.figure.axes:	
				axNum = self.plotter.get_number_of_axis(ax)	
				self.plotter.display_statistics(ax,axNum)
				self.plotter.set_limits_in_replot(ax,axesLimits[axNum])
							
			### add color changes 
			for functionName,column in self.sizeStatsAndColorChanges.items():
				if functionName == 'change_color_by_categorical_columns':
					kws = {'updateColor' : False}
					self.createIntWidgets = True
				else:
					kws = {}
				getattr(self,functionName)(column,**kws)
				
			## add label changes	
			if self.annotationClass is not None:
				self.annotationClass.replotAllAnnotations(self.axisDict[0])
				textColumn = self.annotationClass.textAnnotationColumns
				self.bind_label_event(textColumn)
			
	
	def add_color_and_size_changes_to_dict(self,changeDescription,keywords):
		'''
		Adds information on how to modify the chart further
		'''
		self.sizeStatsAndColorChanges[changeDescription] = keywords
	
	def add_regression_line(self,numericColumnList, specificAxis=None):
		'''
		add regression line to scatter plot
		'''
		if self.currentPlotType != 'scatter':
			return

		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=numericColumnList)	
																  
		dat = self.data[numericColumnList] 												  			
		xList,yList,slope,intercept,rValue,pValue, stdErrorSlope = stats.get_linear_regression(dat)
		
		if specificAxis is None:
			ax = self.axisDict[0]
		else:
			ax = specificAxis

		regressionLabel = 'Slope: {}\nIntercept: {}\nr: {}\np-val: {:.2e}'.format(round(slope,2),round(intercept,2),round(rValue,2),pValue)  	
		self.plotter.add_annotationLabel_to_plot(ax,text=regressionLabel)
		
		ax.plot(xList,yList,linewidth = 1, linestyle= 'dashed')
		self.add_color_and_size_changes_to_dict('add_regression_line',numericColumnList)
			
		
	def add_lowess_line(self,numericColumnList,specificAxis=None):
		'''
		add lowess line to scatter plot
		'''
		if self.currentPlotType != 'scatter':
			return
			
		if self.lowessData is None: ## because lowess calculations are time consuming we save this for export to main figure
			self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=numericColumnList)	
			dat = self.data[numericColumnList]
			self.lowessData = stats.get_lowess(dat)		
														  
		if specificAxis is None:
			ax = self.axisDict[0]
		else:
			ax = specificAxis
			

		ax.plot(self.lowessData[:,0],self.lowessData[:,1],linewidth = 1, linestyle= 'dashed',color="red")														  
		self.add_color_and_size_changes_to_dict('add_lowess_line',numericColumnList)	
		
	
	def adjust_margin_of_figure_for_non_scatter(self):
		'''
		Note: emperically determined.
		'''
		
		adjustRight = 0.28 + 0.12*self.numbNumericColumns
		if adjustRight > 1.8:
			adjustRight = 1.75
		self.figure.subplots_adjust(right = adjustRight)   
	
	def bind_label_event(self,labelColumnList):
		'''
		To do - maybe make this an own class. Could then be used also for scatter with categories and for PCAs
		## Done
		'''
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=labelColumnList)
		self.textAnnotationColumns = labelColumnList
		
		if self.annotationClass is not None: ## useful to keep already added annotations by another column selectable
			madeAnnotations = self.annotationClass.madeAnnotations
			selectionLabels = self.annotationClass.selectionLabels
			## avoid wrong labeling
			try:
				self.annotationClass.disconnect_event_bindings()
			except:
				pass
		else:
			madeAnnotations = OrderedDict()
			selectionLabels = OrderedDict()
		self.annotationClass = annotateScatterPoints(self.plotter,self.figure,self.axisDict[0],
													  self.data,labelColumnList,self.numericColumns[:2],
													  madeAnnotations,selectionLabels) 

	def update_size_interval_in_chart(self):
		'''
		Update the size interval in a scatter plot.
		'''
		for key, categoricalColumns in self.sizeStatsAndColorChanges.items():
			if 'size' in key:
				self.get_size_interval()
				getattr(self,key)(categoricalColumns)
				break 
				
				
	def change_color_by_numerical_column(self, numericColumn, specificAxis = None):
		'''
		Accepts a numeric column from the dataCollection class. This column is added using 
		the index ensuring that correct dots get the right color. 
		'''
		cmap = get_max_colors_from_pallete(self.colorMap)
		if isinstance(numericColumn,str):
			numericColumn = [numericColumn]
		
		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=numericColumn)	
		if specificAxis is None:
			ax = self.axisDict[0]
			self.clean_up_saved_size_and_color_changes('color')
		else:
			ax = specificAxis
		
		axCollection = ax.collections
		if len(numericColumn) > 1:
			# check for updated aggregation method
			if specificAxis is None:
				self.get_agg_method()
			## merge columns 
			if self.aggMethod == 'mean':
				colorData = self.data[numericColumn].mean(axis=1)
			else:
				colorData = self.data[numericColumn].sum(axis=1)
		else:
			colorData = self.data[numericColumn[0]]
			
		scaledData = scale_data_between_0_and_1(colorData) 
		axCollection[0].set_facecolors(cmap(scaledData))
		
		self.add_color_and_size_changes_to_dict('change_color_by_numerical_column',numericColumn)

		
		
	def change_size_by_numerical_column(self, numericColumn, specificAxis = None, update = True):
		'''
		change sizes of scatter points by a numerical column
		'''
		if isinstance(numericColumn,str):
			numericColumn = [numericColumn]
		## update data if missing columns is used to encode color
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=numericColumn)	
		if specificAxis is None:
			ax = self.axisDict[0]
			# clean up stuff
			if update == False:
				self.clean_up_saved_size_and_color_changes('size')
		else:
			ax = specificAxis
		
		if len(numericColumn) > 1:
			# check for updated aggregation method
			if specificAxis is None:
				self.get_agg_method()
			## merge columns 
			if self.aggMethod == 'mean':
				sizeDataRaw = self.data[numericColumn].mean(axis=1)
			else:
				sizeDataRaw = self.data[numericColumn].sum(axis=1)
		else:
			sizeDataRaw = self.data[numericColumn[0]]
		
		axCollection = ax.collections
		scaledData = scale_data_between_0_and_1(sizeDataRaw)
		sizeData = (scaledData)*(self.maxSize-self.minSize) + self.minSize
		axCollection[0].set_sizes(sizeData)
		
		self.add_color_and_size_changes_to_dict('change_size_by_numerical_column',numericColumn)


	def change_size_by_categorical_column(self, categoricalColumn, specificAxis = None, update = True):
		'''
		changes sizes of collection by a cateogrical column
		'''
		if isinstance(categoricalColumn,str):
			categoricalColumn = [categoricalColumn]
		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=categoricalColumn)	
		if specificAxis is None:
			ax = self.axisDict[0]
			## clean up saved changes
			if update == False:
				self.clean_up_saved_size_and_color_changes('size')
		else:
			ax = specificAxis
			
		
		uniqueCategories = self.data[categoricalColumn].apply(tuple,axis=1).unique()
			
			
		numberOfUuniqueCategories = uniqueCategories.size

		scaleSizes = np.linspace(0.3,1,num=numberOfUuniqueCategories,endpoint=True)
		sizeMap = dict(zip(uniqueCategories, scaleSizes))
		
		sizeMap = replace_key_in_dict('-',sizeMap,0.1)
		scaledData = self.data[categoricalColumn].apply(tuple,axis=1).map(sizeMap)
		
		axCollection = ax.collections
		sizeData = (scaledData)*(self.maxSize-self.minSize) + self.minSize
		axCollection[0].set_sizes(sizeData)
		
		self.add_color_and_size_changes_to_dict('change_size_by_categorical_column',categoricalColumn)
	
	
		
	def change_color_by_categorical_columns(self, categoricalColumn, specificAxis = None, 
												updateColor = True, adjustLayer = True):
		'''
		Takes a categorical column and plots the levels present in different colors.
		Reorders the categories in a way that ensures that the NanReplaceString is 
		last in the list and also has the lowest zorder.
		'''
		if isinstance(categoricalColumn,str):
			categoricalColumn = [categoricalColumn]
			
		self.colorMapDict,layerMapDict, self.rawColorMapDict = get_color_category_dict(self.dfClass,categoricalColumn,
												self.colorMap, self.categoricalColorDefinedByUser,
												self.colorScatterPoints)
		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID,
																  definedColumnsList=categoricalColumn)	
		if specificAxis is None:
			ax = self.axisDict[0]
			## clean up changes
			if updateColor == False:
				self.clean_up_saved_size_and_color_changes('color')
		else:
			ax = specificAxis
		
		if len(categoricalColumn) == 1:
		
			self.data.loc[:,'color'] = self.data[categoricalColumn[0]].map(self.colorMapDict)
		else:
			self.data.loc[:,'color'] = self.data[categoricalColumn].apply(tuple,axis=1).map(self.colorMapDict)
		
		axCollection = ax.collections
		
		if updateColor == False and adjustLayer:
			
			self.data.loc[:,'layer'] = self.data['color'].map(layerMapDict)		
			self.data.loc[:,'size'] =  axCollection[0].get_sizes()	
			self.data.sort_values('layer', ascending = True, inplace=True)		
			
			axCollection[0].remove() 
		
		## we need to replot this, otherwise the layer/order cannot be changed. 
		
			self.plotter.add_scatter_collection(ax,x=self.data[self.numericColumns[0]],
											y = self.data[self.numericColumns[1]], size=self.data['size'],
											color = self.data['color'].values, picker = True)
			## index changed .. update data in annotation class
			if self.annotationClass is not None:
				self.annotationClass.update_data(self.data)								
		
			self.add_color_and_size_changes_to_dict('change_color_by_categorical_columns',categoricalColumn)
			if len(self.colorMapDict) < 21:
			
				self.add_legend_for_caetgories_in_scatter(ax,self.colorMapDict,categoricalColumn)
		
			
		elif adjustLayer == False:
			axCollection[0].set_facecolor(self.data['color'].values)
			
			self.add_color_and_size_changes_to_dict('change_color_by_categorical_columns',categoricalColumn)
			if len(self.colorMapDict) < 21:
				self.add_legend_for_caetgories_in_scatter(ax,self.colorMapDict,categoricalColumn)

		else:
			axCollection[0].set_facecolor(self.data['color'].values)
			if specificAxis is None: ##indicating that graph is not exported but only modified
				self.update_legend(ax,self.colorMapDict)
				
			else:
				if len(self.colorMapDict) < 21:
					self.add_legend_for_caetgories_in_scatter(ax,self.colorMapDict,
														  categoricalColumn, export = True)
			#print(specificAxis)	
			## check if we plot a cluster representation, and if then check if there are any line segments to plot
			if self.currentPlotType == 'cluster_analysis':
				
				if len(self.LineSegments) > 0:
					for n, lineSegment in enumerate(self.LineSegments):
						if specificAxis is not None:
							segments = lineSegment.get_segments() 
							color = lineSegment.get_color()
							self.add_line_collection(segments, specificAxis = specificAxis,
									colors = color, save = False)
						else:
							color = self.colorMapDict[str(n)]
							lineSegment.set_color(color)	
							

					
	def get_current_colorMapDict(self):
		'''
		Categorical columns can be used to display categorical levels within that column.
		The color is determined by the colorMapDict which can be accessed and used. 
		'''
		if hasattr(self,'colorMapDict'):
			return self.colorMapDict	
		else:
			return None
	
	def clean_up_saved_size_and_color_changes(self,which = 'color'):
		'''
		'''
		
		toDelete = []
		for functionName,column in self.sizeStatsAndColorChanges.items(): 
			if which in functionName:
				toDelete.append(functionName)
		if 'change_color_by_categorical_columns' in toDelete:
			self.delete_legend(self.axisDict[0])
			
		for func in toDelete:
			del self.sizeStatsAndColorChanges[func]	
			
				
	def reset_color_and_size_level(self,resetColor=False,resetSize=False):
		'''
		Takes collections and resets size and color
		'''
		self.sizeScatterPoints, self.alphaScatterPoints,self.colorScatterPoints = \
											self.plotter.get_scatter_point_properties()
		for ax in self.axisDict.values():
			axisCollections = ax.collections
			for axisCollection in axisCollections:
				if resetColor:
				
					axisCollection.set_facecolor(self.colorScatterPoints)
					self.clean_up_saved_size_and_color_changes('color')
					
					
					
				if resetSize:
				
					axisCollection.set_sizes([self.sizeScatterPoints])
					self.clean_up_saved_size_and_color_changes('size')
					
			self.delete_legend(ax)
			
	def delete_legend(self,ax):	
		'''
		Gets the current legend and deletes it. 
		'''
		legend = ax.get_legend()
		if legend is not None:
			legend.remove() 
					
	def change_nan_color(self,newColor, ignoreMadeChanges = False): 
		'''
		nan color is understood as: if not numerical or categorical column were used to alter the color
		or the color that represents in categorical column changes the nan string defined upon upload of
		the user. For other plottypes this changes simply the artist facecolor (boxplot,violin,bar) 
		'''
		
		if self.currentPlotType == 'scatter_matrix':
		
			self._scatterMatrix.colorScatterPoints = newColor	
			self._scatterMatrix.set_default_color()	
			return
		
		self.colorScatterPoints = newColor
		if 0 in self.axisDict:
			ax = self.axisDict[0]
		else:
			return
		
		## check if changes have been made on color and disable any further modification.
		if ignoreMadeChanges:
			categoricalColorChange = False
		else:
			categoricalColorChange = any(key in ['change_color_by_categorical_columns','change_color_by_numerical_column'] \
										    for key in self.sizeStatsAndColorChanges.keys())
										    
		if categoricalColorChange == False and self.currentPlotType in ['scatter','pointplot','violinplot']:

			axCollections = ax.collections
			if self.currentPlotType == 'violinplot':
				axCollections = ax.collections[::2] ## needed to not alter the small boxplot in violinplots
				 
			for collection in axCollections:
				collection.set_facecolor(newColor)
				
			if self.currentPlotType == 'pointplot': ##updating error bars 
				axLines = ax.lines
				for line in axLines:
					line.set_color(newColor)
					
			self.colorScatterPoints = newColor
				
		elif self.currentPlotType in ['boxplot','barplot']:
			if self.currentPlotType == 'barplot':
				axPatches = ax.patches	
			else:
				axPatches = ax.artists 
			for patch in axPatches:
				patch.set_facecolor(newColor) 
		
		
		elif self.currentPlotType == 'PCA':
			axCollections = ax.collections
			for collection in axCollections:
				collection.set_facecolor(newColor)
				
		elif categoricalColorChange:
			pass		
	
	def add_legend_for_caetgories_in_scatter(self,ax,colorMapDict,categoricalColumn, export = False):
		'''
		Add legend to scatter plot when color has been changed by categorical column
		'''
		if export == False:
			self.clean_up_old_legend_collections() 
		
		leg = ax.get_legend()
		if leg is not None:
			leg.remove()
		for level,color in colorMapDict.items():
		 	if str(level)  not in ['nan',' ']:
		 		# generate and save collection that is used for legend
		 		collectionLegend = self.plotter.add_scatter_collection(ax = ax,x=[],y=[],
		 										label = level,color = color, returnColl=True)
		 		if export == False:
		 			self.savedLegendCollections.append(collectionLegend)
		 		 
		legendTitle = get_elements_from_list_as_string(categoricalColumn, addString = 'Categorical Levels: ', newLine=True)	

		axisStyler(ax,forceLegend=True,kwsLegend={'leg_title':legendTitle})
			
	def update_legend(self,ax,colorMapDict):
		'''
		Updates the legend with a newly defined colorMapDict on the particular axis: ax
		'''
		leg = ax.get_legend()
		if leg is not None:
			n = 0
			for level,color in colorMapDict.items():
		 		if str(level)  not in ['nan',' ']:
		 			leg.legendHandles[n].set_facecolor(color)
		 			n += 1
					
		
	def clean_up_old_legend_collections(self):
		'''
		Cleaning up collections used to build up a legend. 
		'''
		if hasattr(self,'savedLegendCollections') == False:
			self.savedLegendCollections = []
		if len(self.savedLegendCollections) == 0:
			pass
		else:
			for collection in self.savedLegendCollections:
				try:
					collection.remove()
				except:
					pass
			self.savedLegendCollections = []
						
		
	def update_colorMap(self,newCmap = None):
		'''
		allows changes of color map by the user. Simply updates the color code.
		It also changes the object: self.colorMap so that it will also be used when graph is exported.
		Please note that if you just call the function it will cuase an update, this is particullary useful
		when the user used the interactive widgets to customize the color settings
		'''
		if newCmap is not None:
			self.colorMap = newCmap 
		for functionName,column in self.sizeStatsAndColorChanges.items(): 
			getattr(self,functionName)(column)  
			
	
	def export_selection(self,axisExport, subplotIdNumber, exportFigure = None,
			limits=None, boxBool = None, gridBool = None, plotCount = None):
		'''
		Exports a specific axis onto the axisExport axis (in a main figure). The integer id is used to
		identify the plot.
		'''
		plotTypesRestricted = ['PCA','cluster_analysis']
		if self.currentPlotType in ['hclust','corrmatrix']:
			axisExport.axis('off')
			self._hclustPlotter.export_selection(axisExport,exportFigure)
		elif self.currentPlotType == 'line_plot':
			self.linePlotHelper.export_selection(axisExport)
		elif self.currentPlotType == 'scatter' and self.binnedScatter:
			
			self.binnedScatterHelper.export_selection(axisExport)
				
					
		else:	
			self.filling_axis(subplotIdNumber,axisExport) 
			if self.addSwarm:
				self.add_swarm_to_plot(subplotIdNumber,axisExport,export=True)
			
			self.plotter.adjust_grid_and_box_around_subplot(axes = [axisExport], 
															boxBool = boxBool, 
															gridBool = gridBool)
			## this needs to be checked otherwise we cannot export other subplots 
			## from a PCA or cluster anaylsis 												
			if (self.currentPlotType in plotTypesRestricted and subplotIdNumber == 0) \
			or self.currentPlotType not in plotTypesRestricted:

				for functionName,column in self.sizeStatsAndColorChanges.items():
					getattr(self,functionName)(column,axisExport)
		
		## unpack annotations if any made.	
			if self.annotationClass is not None:
				for key,props in self.annotationClass.selectionLabels.items():
					axisExport.annotate(ha='left', arrowprops=arrow_args,**props)
			
			self.plotter.display_statistics(axisExport,subplotIdNumber,plotCount)
			self.plotter.style_collection([axisExport])
			if limits is None:
				self.plotter.reset_limits(subplotIdNumber,axisExport)
			else:
				self.plotter.set_limits_in_replot(axisExport,limits)
			
			self.adjust_axis_scale(axes = [axisExport])
			self.style_axis(axisExport,subplotIdNumber)
			
	
	
			
	def define_new_figure(self,figure):
		'''
		Define new figure for this class. Which is particularly important when restoring
		a session. Since tkinter widgets cannot be saved (e.g. the canvas that is used to
		display the figure)
		'''
		
		self.figure = figure
		self.axisDict = {}
		for plotHelper in [self._hclustPlotter,self.annotationClass,self._scatterMatrix]:
			if plotHelper is not None:
				plotHelper.figure = figure
			
		
	
	
	def filling_axis(self,onlySelectedAxis = None, axisExport = None,plotType = None):
		'''
		Filling the created axis/axes.
		'''
		dataInput = self.data
		colorMap = self.colorMap
		
		if plotType is None:
			plotType = self.currentPlotType
		
		if plotType not in ['density','scatter_matrix','hclust','corrmatrix','PCA','line_plot']:
			if onlySelectedAxis is None:
				ax = self.axisDict[0]
			else:
				ax = axisExport		
	
		if plotType in ['boxplot','barplot','violinplot','swarm','add_swarm','pointplot']:

		
			fill_axes_with_plot(ax=ax,x=None,y=None,hue = None,plot_type = plotType,
								cmap=colorMap,data=dataInput,order=self.numericColumns,
								inmutableCollections = self.inmutableCollections,
								error = self.error)
			
		
		elif plotType == 'density':
			if hasattr(self,'cdf') == False:
				self.cdf = self.plotter.get_dist_settings()
			for n,numericColumn in enumerate(self.numericColumns):
					if onlySelectedAxis is None:
					
						ax = self.axisDict[n]
					else:
						if n != onlySelectedAxis:
							continue
						else:
							ax = axisExport
					
					sns.distplot(dataInput[numericColumn].dropna().values, ax=ax, hist_kws={'cumulative':self.cdf},
															kde_kws={'cumulative':self.cdf})
					self.plotter.add_annotationLabel_to_plot(ax = ax, text = numericColumn)

		elif plotType == 'time_series':
		
			dataInput.sort_values(by=self.numericColumns[0], inplace = True)
			dataInput.dropna(subset = [self.numericColumns[0]], inplace=True)
			colors = sns.color_palette(colorMap,self.numbNumericColumns-1)
			xData = dataInput[self.numericColumns[0]].values
			collectLines = []
			for n,yDataColumn in enumerate(self.numericColumns[1:]):
				yData = dataInput[yDataColumn].values
				colorForLine = colors[n]
				line = ax.plot(xData,yData, linewidth=0.95, color=colorForLine, label=yDataColumn)
				collectLines.extend(line)
			if onlySelectedAxis is None:
				self.timeSeriesHelper = _timeSeriesHelper(self.plotter,self.dfClass,
										ax,dataInput,self.numericColumns,colors,collectLines)
			
			else:
				self.timeSeriesHelper.export_selection(ax)
			
			
			
		elif plotType == 'scatter':
			
			if self.numbNumericColumns == 2:
				if self.binnedScatter:
				
					self.binnedScatterHelper = binnedScatter(self.plotter,self.dfClass, 
							self.numericColumns, self.categoricalColumns)
				
				else:
			
			
					ax.scatter(dataInput[self.numericColumns[0]],
									dataInput[self.numericColumns[1]],
									edgecolor = 'black',
									linewidth = 0.3,
									s = self.sizeScatterPoints,
									alpha =  self.alphaScatterPoints,
									color = self.colorScatterPoints,
									picker=True, label = None)
		
		
		elif plotType == 'line_plot':
		
			self.linePlotHelper = linePlotHelper(self.plotter,self.dfClass,self.numericColumns,self.colorMap)
								
		elif plotType == 'scatter_matrix':
		
			self._scatterMatrix  = _scatterMatrixHelper(self.plotter,self.dfClass,self.figure,self.numericColumns,
														self.numbNumericColumns,colorMap,dataInput)
		elif plotType in ['hclust','corrmatrix']:
		
			plotCorrMatrix =  plotType == 'corrmatrix'
			progressBar = Progressbar(title= 'Hierarchical Clustering')
			self._hclustPlotter = hierarchichalClustermapPlotter(progressBar,self.dfClass,
											self.plotter,self.figure,self.numericColumns,
											plotCorrMatrix = plotCorrMatrix)
		
		elif plotType == 'cluster_analysis':
			axScores = None
			ax = None
			axCount = None
			
			if onlySelectedAxis is None:
				ax = self.axisDict[0]
				axScores = self.axisDict[1]
				axCount = self.axisDict[2]
				self.LineSegments = []
				
			else:
				if onlySelectedAxis == 0:
					ax = axisExport
				elif onlySelectedAxis == 2:
					axCount = axisExport
				elif onlySelectedAxis == 3:
					axScores = axisExport
				else:
					return
			
			if ax is not None:
				ax.scatter(dataInput[self.numericColumns[0]],
									dataInput[self.numericColumns[1]],
									edgecolor = 'black',
									linewidth = 0.3,
									s = self.sizeScatterPoints,
									alpha =  self.alphaScatterPoints,
									color = self.colorScatterPoints,
									picker=True, label=None)
			if axCount is not None:
				sns.countplot(x = self.plotter.clusterLabels.columns.values.tolist()[0],
						data = self.plotter.clusterLabels, ax=axCount, palette = colorMap)
			
			if axScores is not None:
				self.update_cluster_analysis_score(axScores)
			
		elif plotType == 'PCA':
			## plot drivers
			if onlySelectedAxis is None or onlySelectedAxis == 0:
				drivers = self.data
				if onlySelectedAxis is None:
					ax = self.axisDict[0]
				else:
					ax = axisExport
			
			
				ax.scatter(drivers.iloc[:,0],drivers.iloc[:,1],
									edgecolor = 'black',
									linewidth = 0.3,
									s = self.sizeScatterPoints,
									alpha =  self.alphaScatterPoints,
									color = self.colorScatterPoints,
									picker=True, label = None)
			
			## projections
			if onlySelectedAxis is None or onlySelectedAxis == 1:
				components = self.plotter.dimRedResults['data']['Components']
				if onlySelectedAxis is None:
					ax = self.axisDict[1]
				else:
					ax = axisExport
				ax.scatter(components.iloc[0,:], components.iloc[1,:],
									edgecolor = 'black',
									linewidth = 0.3,
									s = self.sizeScatterPoints,
									alpha =  self.alphaScatterPoints,
									color = self.colorScatterPoints,
									picker=True, label = None)
				data = components.T
				data['experiments'] = data.index
				
				if onlySelectedAxis is None:					
					self.pcaProjectionAnnotations = annotateScatterPoints(Plotter = self.plotter,
										figure = self.figure, ax = ax, data = data,
										numericColumns = data.columns.values.tolist()[:2],
										labelColumns = ['experiments'], madeAnnotations = OrderedDict(),
										selectionLabels = OrderedDict()) 
					self.pcaProjectionAnnotations.annotate_all_row_in_data()	
				else:
					self.update_color_in_projection(self.plotter.dimRedResults,ax)
					if self.pcaProjectionAnnotations is not None:
						for key,props in self.pcaProjectionAnnotations.selectionLabels.items():
							axisExport.annotate(ha='left', arrowprops=arrow_args,**props)
																			
									
										
			##explained variance
			if onlySelectedAxis is None or onlySelectedAxis == 2:
				if 'ExplainedVariance' in self.plotter.dimRedResults['data']:
				
					data = self.plotter.dimRedResults['data']['ExplainedVariance'].loc[:,0]
					xTicks = [x+1 for x in data.index.tolist()]
				else:
					data = self.plotter.dimRedResults['data']['ReconstructionError']
					xTicks = 1 
				if onlySelectedAxis is None:
					ax = self.axisDict[2]
				else:
					ax = axisExport
				ax.bar(xTicks, data)
			
	def update_color_in_projection(self,resultDict = None, ax = None):
		'''
		Projection plot in dimensional reduction show feature names and can
		be colored occording to groups. (For example if feature == name of experiment
		where expresison values of several proteins/genes have been measured (e.g Tutorial Data 2)
		'''
		if resultDict is None:
			resultDict =  self.plotter.dimRedResults
		
		if 'color' in resultDict:
			colorDict = resultDict['color']
			groupDict = resultDict['group']	 
			featureOrder = self.plotter.dimRedResults['data']['Components'].T.index
			colors = [colorDict[feature] for feature in featureOrder]
			groups = [groupDict[feature] for feature in featureOrder]
			uniqueValuesDict = OrderedDict((comb,True) for comb in list(zip(colors,groups)))
			colorsUnique,groupsUnique = zip(*list(uniqueValuesDict.keys()))
			if ax is None:
				ax = self.axisDict[1]
			ax.collections[0].set_facecolor(colors)
			axisStyler(ax,forceLegend = True ,kwsLegend = {'addPatches':True,
 									   		'legendItems' : list(groupsUnique),
 									   		'colorMap' : list(colorsUnique),
 									   		'leg_title':'Grouping',
 									   		 'patchKws':{'alpha':self.alphaScatterPoints,
 									   		 'lw':0.5}}) 
 									   
											
	def hide_show_feature_names(self):
	
		'''
		Handles feature names in projection plot of 
		a dimensional reduction procedure
		'''	
		if self.pcaProjectionAnnotations is not None:
			if len(self.pcaProjectionAnnotations.selectionLabels) != 0:
				self.pcaProjectionAnnotations.remove_all_annotations()
			else:
				self.pcaProjectionAnnotations.annotate_all_row_in_data()
			
			self.plotter.redraw()					
						
					
	def update_cluster_analysis_score(self, ax):
		'''
		'''
		calinski = []
		silhouette = []
		
		x = list(range(len(self.plotter.clusterEvalScores)))
		
		for n, scoreDict in self.plotter.clusterEvalScores.items():
			calinski.append(scoreDict['Calinski'])
			silhouette.append(scoreDict['Silhouette'])
		
		ax.plot(x,silhouette,'o-', linewidth = 0.4)
		ax.tick_params('y', colors='C0')
		ax2 = ax.twinx() 
		ax2.plot(x,calinski,marker='o',linestyle='dashed',markerfacecolor='white', 
					markeredgewidth=0.4,markeredgecolor="black",
					color='black', linewidth = 0.4)	
		
		axisStyler(ax,ylabel='Silhouette Score', xlabel = 'Cluster Analysis #') 	
		axisStyler(ax2,ylabel='Calinski Harabaz') 
		ax.set_ylim((0,1))

	def remove_swarm(self):
		'''
		'''
		toBeRemoved = []
		for ax in self.figure.axes:
			for collection in ax.collections:
				if collection not in self.inmutableCollections:
					toBeRemoved.append(collection)
		for coll in toBeRemoved:
			coll.remove() 
		
		self.inmutableCollections = []	
		self.plotter.addSwarm = False	
		self.addSwarm = False

			
	
	def add_swarm_to_plot(self,subplotIdNumber = None,axisExport = None, export = False):
		'''
		'''
		self.inmutableCollections = []
		
		if export ==  False:
			for ax in self.figure.axes:
				self.inmutableCollections.extend(ax.collections)
				if self.currentPlotType == 'barplot':
					for line in ax.lines:
						line.set_zorder(20) ## ensure that error bars are ontop of swarm

		self.filling_axis(subplotIdNumber,axisExport,plotType = 'add_swarm')
		self.plotter.addSwarm = True	
		self.addSwarm = True
		
				
			
	def add_line_collection(self,lineSegments, colors = None ,
							specificAxis = None, zorder= 2, linewidths = 0.4, save = True):
		'''
		'''
		if specificAxis is None:
			ax = self.axisDict[0]
		else:
			ax = specificAxis 
			
		lineSegments = LineCollection(lineSegments, colors = colors, 
									  zorder = zorder, linewidths = linewidths)
		ax.add_collection(lineSegments)
		if save:
			self.LineSegments.append(lineSegments)
				
	def get_grid_layout_for_plotting(self):
		'''
		'''
		cols = 3 
		rows = np.ceil(self.numbNumericColumns/3)
		if rows == 1:
			rows = 2
		return rows,cols
		
	def style_axis(self,ax = None, onlySelectedAxis = None):
	
		plotType = self.currentPlotType
		
		if plotType in ['hclust','corrmatrix','scatter_matrix','line_plot']:
			return
		if ax is None and plotType !='scatter_matrix':
			ax = self.axisDict[0]
			
		if plotType in nonScatterPlotTypes:
		
			axisStyler(ax, xlabel=None, ylabel = None,rotationXTicks = 90,nTicksOnYAxis=4)
			
		elif plotType == 'time_series':
			axisStyler(ax,xlabel=self.numericColumns[0],ylabel = 'Value',
						forceLegend = True, kwsLegend={'leg_title':'Time series'})
		
		elif plotType == 'PCA':
			if onlySelectedAxis is not None:
				if onlySelectedAxis < 2:
					axisStyler(ax, xlabel='Component 1', ylabel = 'Component 2')
				else:
					if self.plotter.dimRedResults['method'] != 'Non-Negative Matrix Factorization':
						axisStyler(ax, ylabel='Explained Variance Ratio', 
										 xlabel = 'Components')
					else:
						axisStyler(ax, ylabel='Reconstruction Error', 
										 xlabel = 'Analysis ID', newXLim = (-1,3))
			else:
				for n in [0,1]:
					axisStyler(self.axisDict[n], xlabel='Component 1', ylabel = 'Component 2',
									nTicksOnYAxis = 4, nTicksOnXAxis = 4)
				if self.plotter.dimRedResults['method'] != 'Non-Negative Matrix Factorization':
					axisStyler(self.axisDict[2], ylabel='Explained Variance Ratio', 
										 xlabel = 'Components',nTicksOnYAxis = 4)
				else:
					axisStyler(self.axisDict[2], ylabel='Reconstruction Error', 
										 xlabel = 'Analysis ID',newXLim = (-1,3))
		            
		elif plotType == 'density':
		
			for n,numericColumn in enumerate(self.numericColumns):
				
				
				if onlySelectedAxis is not None:
					if n != onlySelectedAxis:
						continue
						
				else:
					ax = self.axisDict[n]
				
			
				if ax.is_first_col():
					axisStyler(ax, ylabel='Density', nTicksOnYAxis = 4, nTicksOnXAxis=4)
				else:	
					axisStyler(ax, nTicksOnYAxis = 4, nTicksOnXAxis=4)
		else:
			if self.numbNumericColumns == 2:
				xlabel, ylabel = self.numericColumns[:2] # precaution
				axisStyler(ax, xlabel=xlabel, ylabel = ylabel,nTicksOnYAxis=5,nTicksOnXAxis=5)
						
	def disconnect_event_bindings(self):
		for eventBindingClass in [self._hclustPlotter,self.annotationClass,
											self.pcaProjectionAnnotations]:
			if eventBindingClass is not None:
				eventBindingClass.disconnect_event_bindings()								
	
	def __getstate__(self):
	
		state = self.__dict__.copy()
		for attr in ['figure','colorMapDict', 'savedLegendCollections',
					'pcaProjectionAnnotations','axisDict', 'LineSegments']:
			if attr in state: 
				del state[attr]
		return state
			#'_Plotter',
			
	
		
class _scatterMatrixHelper(object):
	
	
	def __init__(self,plotter,sourceDataClass,figure,numericColumns,numbNumbericColumns,colorMap,dataInput):
		self.addedAxis = dict()	
		self.axisWithScatter = dict()
		self.categoricalColorDefinedByUser = dict()
		self.linesInPlots = dict()
		self.dfClass = sourceDataClass	
		self.dataID = self.dfClass.currentDataFile			
		self.data = dataInput
		self.plotter=plotter
		self.get_scatter_point_properties(plotter)
		self.numericColumns = numericColumns
		self.numbNumericColumns = numbNumbericColumns
		self.colorMap = colorMap
		
		self.figure = figure		
		
		self.corrMatrix = self.dfClass.df[numericColumns].corr()
		self.axisLimits = self.get_max_and_min_limits()
		
		self.add_axes_to_figure()
		self.fill_axes()
		# disabled at the moment
		#self.add_bindings()
		
		
		
	def add_axes_to_figure(self):
		'''
		Adding axes to figure
		'''
		self.figure.subplots_adjust(wspace=0.05, hspace=0.05)
		for colComb in range(self.numbNumericColumns**2):
			ax = self.figure.add_subplot(self.numbNumericColumns,
										self.numbNumericColumns,
										colComb+1)
			self.check_position_of_ax_and_move_tick_labels(ax)
			ax.set_xlim(self.axisLimits)
			ax.set_ylim(self.axisLimits)
			self.addedAxis[colComb] = ax
		

	def disconnect_events(self):
		'''
		'''
		for event in [self.onPressEvent, self.onReleaseEvent]:
			self.plotter.figure.canvas.mpl_disconnect(event)
		
	def add_bindings(self):
		'''
		'''
		self.rectangleProps = dict(xy=None,linewidth=0.6,edgecolor="darkgrey",clip_on=False,
							  fill= True,facecolor = "lightgrey", animated=True, alpha=0.2)
		self.onPressEvent = self.plotter.figure.canvas.mpl_connect('button_press_event', self.on_press)
		self.onReleaseEvent = self.plotter.figure.canvas.mpl_connect('button_release_event', self.on_release)
		
	def identify_data(self,event):
		'''
		Identify data to mark.
		'''
		xRange = (self.rectangleProps['xy'][0],
			self.rectangleProps['xy'][0] + self.rectangleProps['width'])	
		yRange = (self.rectangleProps['xy'][1],
			self.rectangleProps['xy'][1] + self.rectangleProps['height'])
				
		for combination,ax in self.axisWithScatter.values():
			if ax == event.inaxes:
				columnNames = [self.numericColumns[idx] for idx in combination]
				break
		boolXData = self.data[columnNames[1]].between(min(xRange),max(xRange))
		boolYData = self.data[columnNames[0]].between(min(yRange),max(yRange))
		if 'color' not in self.data.columns:
			self.data['bool'] = np.sum([boolXData,boolYData], axis=0) == 2
			self.data['bool'] = self.data['bool'].map({False:"lightgrey",True:"blue"})
			
		for combination,ax in self.axisWithScatter.values():
			columnNames = [self.numericColumns[idx] for idx in combination]
			row,column = combination
			dataToPlot = self.data.dropna(subset=columnNames)
			collection = ax.collections[0]
			collection.set_facecolor(dataToPlot['bool'])
			ax.draw_artist(collection)
		
				
			
	def calculate_rectangle(self,event):
		'''
		Get width and height of the rectangle that indicates selection
		'''
		if self.rectangleProps['xy'] is None:
			self.rectangleProps['xy'] = (event.xdata,event.ydata)
			self.background = self.plotter.figure.canvas.copy_from_bbox(self.plotter.figure.bbox)
		
		width = event.xdata - self.rectangleProps['xy'][0]
		height = event.ydata - self.rectangleProps['xy'][1]
		self.rectangleProps['height'] = height
		self.rectangleProps['width'] = width
		
	def on_press(self,event):
		'''
		'''
		
		if event.inaxes is None:
			return
			
		ax = event.inaxes
		self.set_default_color()
		self.plotter.redraw()
		self.calculate_rectangle(event)
		self.rectangleSelection = patches.Rectangle(**self.rectangleProps)
		ax.add_patch(self.rectangleSelection)
		self.onMotionEvent = self.plotter.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
			
	def on_motion(self,event):
		'''
		'''
		if event.inaxes is None:
			self.plotter.figure.canvas.mpl_disconnect(self.onMotionEvent)
			self.rectangleProps['xy'] = None
			return
			
		self.plotter.figure.canvas.restore_region(self.background)			
		ax = event.inaxes
		self.calculate_rectangle(event)
		self.identify_data(event)
		self.rectangleSelection.set_width(self.rectangleProps['width'])
		self.rectangleSelection.set_height(self.rectangleProps['height'])
		ax.draw_artist(self.rectangleSelection)
		self.plotter.figure.canvas.blit(self.plotter.figure.bbox)
		
	# self.figure.canvas.restore_region(background)
# 		rectangle.set_xy((x,y))  
# 		ax.draw_artist(rectangle)
# 		self.figure.canvas.blit(ax.bbox)    
#           
# 	def disconnect_label_and_update_annotation(self,event,rectangle,annotation,keyClosest):
# 		'''
# 		Mouse release event. disconnects event handles and updates the annotation dict to
# 		keep track for export
# 		'''
# 		self.figure.canvas.mpl_disconnect(self.rectangleMoveEvent)
# 		self.figure.canvas.mpl_disconnect(self.releaseLabelEvent)
# 		
# 		xyRectangle = rectangle.get_xy()
# 		annotation.set_position(xyRectangle)
# 		
# 		rectangle.remove()
# 		self.plotter.redraw() 
# 		self.selectionLabels[keyClosest]['xytext'] = xyRectangle
# 
# 	def get_rectangle_size_on_text(self,ax,text,inv):
# 		'''
# 		Returns rectangle to mimic the position
# 		'''	
# 		renderer = self.figure.canvas.get_renderer() 
# 		fakeText = ax.text(0,0,s=text)
# 		patch = fakeText.get_window_extent(renderer)
# 		xy0 = list(inv.transform((patch.x0,patch.y0)))
# 		xy1 = list(inv.transform((patch.x1,patch.y1)))
# 		fakeText.remove()
# 		widthText = xy1[0]-xy0[0]			
		
					
	
	def on_release(self,event):	
		'''
		'''		
		self.plotter.figure.canvas.mpl_disconnect(self.onMotionEvent)
		self.rectangleProps['xy'] = None
	
	def replot(self):
		'''
		'''
		self.add_axes_to_figure()
		self.fill_axes()
		
		
	def change_size_by_numeric_column(self,numericColumn):
		'''
		Aceepts a numeric column from the dataCollection class. It sorts the index first 
		to ensure that the right dots get the right color.
		'''

		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID)
		# clean up saved changes
		#self.clean_up_saved_size_and_color_changes('size')
		
		for combination in self.saveCombination:
		
			columnNames = [self.numericColumns[idx] for idx in combination]
			row,column = combination
			dataToPlot = self.data.dropna(subset=columnNames)
			
			ax = self.addedAxis[row*self.numbNumericColumns+column]
			
			axCollection = ax.collections
			
			scaledData = scale_data_between_0_and_1(dataToPlot[numericColumn])
			scaledData = scaledData*100
			axCollection[0].set_sizes(scaledData)
			
	def change_color_by_numeric_column(self,numericColumn):
		'''
		Aceepts a numeric column from the dataCollection class. It sorts the index first 
		to ensure that the right dots get the right color.
		'''
		cmap = get_max_colors_from_pallete(self.colorMap)
		#if self.colorMap not in ['Set4','Set5']:  
		#	cmap = cm.get_cmap(self.colorMap) 
		#e#lse:
		#	cmap = ListedColormap(sns.color_palette(self.colorMap))
			
		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID)
		# clean up saved changes
		#self.clean_up_saved_size_and_color_changes('color')
		
		
		for combination in self.saveCombination:
		
			columnNames = [self.numericColumns[idx] for idx in combination]
			row,column = combination
			dataToPlot = self.data.dropna(subset=columnNames)
			
			ax = self.addedAxis[row*self.numbNumericColumns+column]
			
			axCollection = ax.collections
			
			scaledData = scale_data_between_0_and_1(dataToPlot[numericColumn])
			
			axCollection[0].set_facecolors(cmap(scaledData))
			del dataToPlot	
	
	def change_color_by_categorical_column(self,categoricalColumn):
		'''
		accepts a categorical column and will color the data accordingly to the 
		categorical levels in that column (can also be multiple ones)
		'''

		
		colorMapDict,layerMapDict, rawColorMapDict = get_color_category_dict(self.dfClass,categoricalColumn,
												self.colorMap, self.categoricalColorDefinedByUser,
												self.colorScatterPoints)
		## update data if missing columns 
		self.data = self.dfClass.join_missing_columns_to_other_df(self.data,id=self.dataID)
		data = self.data[categoricalColumn+self.numericColumns]
		#self.clean_up_saved_size_and_color_changes('color')
		
		if len(categoricalColumn) == 1:
		
			data.loc[:,'color'] = data[categoricalColumn[0]].map(colorMapDict)
		else:
			data.loc[:,'color'] = data[categoricalColumn].apply(tuple,axis=1).map(colorMapDict)
		
		data.loc[:,'layer'] = data['color'].map(layerMapDict)			
		data.sort_values('layer', ascending = True, inplace=True)
			
		for combination in self.saveCombination:
		
			columnNames = [self.numericColumns[idx] for idx in combination]
			row,column = combination
			dataToPlot = data.dropna(subset=columnNames)
			
			ax = self.addedAxis[row*self.numbNumericColumns+column]
			
			axCollection = ax.collections
			sizeUsed = axCollection[0].get_sizes()
			
			axCollection[0].remove() 	
			self.add_scatter_collection(ax,x=dataToPlot[columnNames[1]],
										y = dataToPlot[columnNames[0]], size=sizeUsed,
										color = dataToPlot['color'])
	
	
	def set_default_color(self):
		'''
		Removes all color changes made.
		'''
		for combination in self.saveCombination:
		
			columnNames = [self.numericColumns[idx] for idx in combination]
			row,column = combination
			
			ax = self.addedAxis[row*self.numbNumericColumns+column]
			axCollection = ax.collections
			axCollection[0].set_facecolors(self.colorScatterPoints)	
			
			
	def set_default_size(self):
		'''
		Sets all sizes to standard 
		'''
		for combination in self.saveCombination:
		
			columnNames = [self.numericColumns[idx] for idx in combination]
			row,column = combination
			
			ax = self.addedAxis[row*self.numbNumericColumns+column]
			axCollection = ax.collections
			axCollection[0].set_sizes(self.sizeScatterPoints)	
	 		
			
	def check_position_of_ax_and_move_tick_labels(self,ax):
	
	
                 if ax.is_first_col():
                     ax.yaxis.set_ticks_position('left')
                 if ax.is_last_col():
                     ax.yaxis.set_ticks_position('right')
                 if ax.is_first_row():
                     ax.xaxis.set_ticks_position('top')
                 if ax.is_last_row():
                     ax.xaxis.set_ticks_position('bottom')	
	
	def get_scatter_point_properties(self,_Plotter):
		'''
		'''
		self.sizeScatterPoints, self.alphaScatterPoints,self.colorScatterPoints = _Plotter.get_scatter_point_properties()	
		
	def get_max_and_min_limits(self):
		'''
		Calculating the max and min limits.
		'''
		
		minData = self.dfClass.df[self.numericColumns].min().min()
		maxData = self.dfClass.df[self.numericColumns].max().max()
		return (minData-0.075*minData,maxData+0.075*maxData)
	
	def add_scatter_collection(self,ax,x,y, color = None, size=None):
		'''
		'''
		if color is None:
			color = self.colorScatterPoints
		if size is None:
			size = self.sizeScatterPoints
		
		
		ax.scatter(x,y, edgecolor = 'black',
					linewidth = 0.3, s = size,
					alpha =  self.alphaScatterPoints, color = color)
										
	def fill_axes(self):
		'''
		Fills axis with data and information (scatter, name and pearson/p-value)
		'''
		data = self.dfClass.df.sort_index()
		self.saveCombination = []
		for row in range(self.numbNumericColumns):
			for column in range(self.numbNumericColumns):
				ax = self.addedAxis[row*self.numbNumericColumns+column]
				if row == column:
					ax.annotate(self.numericColumns[row], (0.5, 0.5), xycoords='axes fraction',
                           ha='center', va='center')
					ax.xaxis.set_visible(False)
					ax.yaxis.set_visible(False)
				else:
					
					combination = [row,column]
					columnNames = [self.numericColumns[idx] for idx in combination]
					
					if [column,row] in self.saveCombination:
						
						ax.annotate('r: {}'.format(round(self.corrMatrix.iloc[row,column],2)), 
                                   (0.5, 0.5), 
                                   xycoords='axes fraction',
                                   ha='center', va='center')
                                  
						
					else:
					
						self.saveCombination.append(combination)
						dataToPlot = data.dropna(subset=columnNames)
						self.axisWithScatter[str(combination)] = [combination,ax]
						self.add_scatter_collection(ax,dataToPlot[columnNames[1]],
													dataToPlot[columnNames[0]])
						
						
					if ax.is_last_col() and ax.is_first_row():
						pass
					elif ax.is_first_col() and ax.is_last_row():
						pass
					else:
						plt.setp(ax.get_yticklabels() , visible=False) 
						plt.setp(ax.get_xticklabels() , visible=False)

                              			
		
class annotateScatterPoints(object):
	'''
	Adds an annotation triggered by a pick event. Deletes annotations by right-mouse click
	and moves them around.
	Big advantage over standard draggable(True) is that it takes only the closest annotation to 
	the mouse click and not all the ones below the mouse event.
	'''
	def __init__(self,Plotter,figure,ax,data,labelColumns,
					numericColumns,madeAnnotations,selectionLabels):
		self.figure = figure
		self.plotter = Plotter
		self.ax = ax
		self.data = data
		self.numericColumns = numericColumns
		self.textAnnotationColumns = labelColumns
		self.eventOverAnnotation = False
		
		self.selectionLabels = selectionLabels
		self.madeAnnotations = madeAnnotations
		
		
		self.on_press =  self.plotter.figure.canvas.mpl_connect('button_press_event', lambda event:  self.onPressMoveAndRemoveAnnotions(event))
		self.on_pick_point =  self.plotter.figure.canvas.mpl_connect('pick_event', lambda event:  self.onClickLabelSelection(event))
	
	def disconnect_event_bindings(self):
		'''
		'''
		
		self.plotter.figure.canvas.mpl_disconnect(self.on_press)
		self.plotter.figure.canvas.mpl_disconnect(self.on_pick_point)
		
	def onClickLabelSelection(self,event):
		'''
		Drives a matplotlib pick event and labels the scatter points with the column choosen by the user
		using drag & drop onto the color button..
		'''
		if hasattr(event,'ind'):
			pass
		else:
			return
		## check if the axes is used that was initiated
		## allowing several subplots to have an annotation (PCA)
		if event.mouseevent.inaxes != self.ax:
			return
		
		if event.mouseevent.button != 1:
			self.plotter.castMenu = False
			return
					
		ind = event.ind
		## check if we should label
		xyEvent =  (event.mouseevent.xdata,event.mouseevent.ydata)
		self.find_closest_and_check_event(xyEvent,event.mouseevent)
		if self.eventOverAnnotation:
			return
		
		selectedData = self.data.iloc[ind]
		key = selectedData.index.values.item(0)
		clickedData = selectedData.iloc[0]
		
		
		if key in self.selectionLabels: ## easy way to check if that row is already annotated
			return
		
		xyDataLabel = tuple(clickedData[self.numericColumns])
		if len(self.textAnnotationColumns) != 1:
			textLabel = str(clickedData[self.textAnnotationColumns]).split('Name: ')[0] ## dangerous if 'Name: ' is in column name
		else:
			textLabel = str(clickedData[self.textAnnotationColumns].iloc[0])
		ax = self.ax
		xLimDelta,yLimDelta = xLim_and_yLim_delta(ax)
		xyText = (xyDataLabel[0]+ xLimDelta*0.02, xyDataLabel[1]+ yLimDelta*0.02)
		annotObject = ax.annotate(s=textLabel,xy=xyDataLabel,xytext= xyText, ha='left', arrowprops=arrow_args)
		
		self.selectionLabels[key] = dict(xy=xyDataLabel, s=textLabel, xytext = xyText)
		self.madeAnnotations[key] = annotObject
		
		self.plotter.redraw()
	
	def addAnnotationFromDf(self,dataFrame):
		'''
		'''
		ax = self.ax

		for rowIndex in dataFrame.index:
			if rowIndex not in self.data.index:
				continue
			textData = self.data[self.textAnnotationColumns].loc[rowIndex]
			textLabel = str(textData.iloc[0])
			
			key = rowIndex
			xyDataLabel = tuple(self.data[self.numericColumns].loc[rowIndex])
			xLimDelta,yLimDelta = xLim_and_yLim_delta(ax)
			xyText = (xyDataLabel[0]+ xLimDelta*0.02, xyDataLabel[1]+ yLimDelta*0.02)
			annotObject = ax.annotate(s=textLabel,xy=xyDataLabel,xytext= xyText, ha='left', arrowprops=arrow_args)
		
			self.selectionLabels[key] = dict(xy=xyDataLabel, s=textLabel, xytext = xyText)
			self.madeAnnotations[key] = annotObject	
		## redraws added annotations	
		self.plotter.redraw()

	
	def replotAllAnnotations(self, ax):
		'''
		If user opens a new session, we need to first replot annotation and then enable
		the drag&drop events..
		'''
		
		self.madeAnnotations.clear() 
		for key,annotationProps in self.selectionLabels.items():
			annotObject = ax.annotate(ha='left', arrowprops=arrow_args,**annotationProps)
			self.madeAnnotations[key] = annotObject
		
	def onPressMoveAndRemoveAnnotions(self,event):
		'''
		Depending on which button used by the user, it trigger either moving around (button-1 press)
		or remove the label.
		'''
		if event.inaxes is None:
			return 
		if event.button in [2,3]: ## mac is 2 and windows 3..
			self.remove_clicked_annotation(event)
		elif event.button == 1:
			self.move_annotations_around(event)
	
	def annotate_all_row_in_data(self):
		'''
		'''
		self.addAnnotationFromDf(self.data)
	
			
	def remove_clicked_annotation(self,event):
		'''
		Removes annotations upon click from dicts and figure
		does not redraw canvas
		'''
		self.plotter.castMenu = True
		toDelete = None
		for key,madeAnnotation  in self.madeAnnotations.items():
			if madeAnnotation.contains(event)[0]:
				self.plotter.castMenu = False
				madeAnnotation.remove()
				toDelete = key
				break
		if toDelete is not None:
			del self.selectionLabels[toDelete] 
			del self.madeAnnotations[toDelete] 
			self.eventOverAnnotation = False
			self.plotter.redraw()		
	
	def remove_all_annotations(self):
		'''
		Removes all annotations. Might be called from outside to let 
		the user delete all annotations added
		'''
		
		for madeAnnotation  in self.madeAnnotations.values():
				madeAnnotation.remove()
		self.madeAnnotations.clear()
		self.selectionLabels.clear()

	def find_closest_and_check_event(self,xyEvent,event):
		'''
		'''
		if len(self.selectionLabels) == 0:
			return
		annotationsKeysAndPositions = [(key,annotationDict['xytext']) for key,annotationDict \
		in self.selectionLabels.items()][::-1]
		
		keys, xyPositions = zip(*annotationsKeysAndPositions)
		idxClosest = closest_coord_idx(xyPositions,xyEvent)[0]
		keyClosest = keys[idxClosest]
		annotationClostest = self.madeAnnotations[keyClosest]
		self.eventOverAnnotation = annotationClostest.contains(event)[0]
		
		return annotationClostest,xyPositions,idxClosest,keyClosest

			
	def move_annotations_around(self,event):
		'''
		wrapper to move around labels. We did not use the annotation.draggable(True) option
		because this moves all artists around that are under the mouseevent.
		'''
		if len(self.selectionLabels) == 0 or event.inaxes is None:
			return 
		self.eventOverAnnotation = False	
		
		xyEvent =  (event.xdata,event.ydata)
		
		annotationClostest,xyPositions,idxClosest,keyClosest = \
		self.find_closest_and_check_event(xyEvent,event)	
					
		
		if self.eventOverAnnotation:
			ax = self.ax
			inv = ax.transData.inverted()
			
			#renderer = self.figure.canvas.renderer() 
			xyPositionOfLabelToMove = xyPositions[idxClosest] 
			background = self.figure.canvas.copy_from_bbox(ax.bbox)
			widthRect, heightRect = self.get_rectangle_size_on_text(ax,annotationClostest.get_text(),inv)
			recetangleToMimicMove = patches.Rectangle(xyPositionOfLabelToMove,width=widthRect,height=heightRect,
													fill=False, linewidth=0.6, edgecolor="darkgrey",
                             						animated = True,linestyle = 'dashed', clip_on = False)
			
			ax.add_patch(recetangleToMimicMove)
			
			self.rectangleMoveEvent = self.figure.canvas.mpl_connect('motion_notify_event', 
										lambda event:self.move_rectangle_around(event,recetangleToMimicMove,background,inv,ax))
                             									
                             									
			self.releaseLabelEvent = self.figure.canvas.mpl_connect('button_release_event', 
										lambda event: self.disconnect_label_and_update_annotation(event,
																					recetangleToMimicMove,
																					annotationClostest,
																					keyClosest))
		
	def move_rectangle_around(self,event,rectangle,background,inv, ax):
		'''
		actually moves the rectangle
		'''
		x_s,y_s = event.x, event.y
		x,y= list(inv.transform((x_s,y_s)))
		self.figure.canvas.restore_region(background)
		rectangle.set_xy((x,y))  
		ax.draw_artist(rectangle)
		self.figure.canvas.blit(ax.bbox)    
          
	def disconnect_label_and_update_annotation(self,event,rectangle,annotation,keyClosest):
		'''
		Mouse release event. disconnects event handles and updates the annotation dict to
		keep track for export
		'''
		self.figure.canvas.mpl_disconnect(self.rectangleMoveEvent)
		self.figure.canvas.mpl_disconnect(self.releaseLabelEvent)
		
		xyRectangle = rectangle.get_xy()
		annotation.set_position(xyRectangle)
		
		rectangle.remove()
		self.plotter.redraw() 
		self.selectionLabels[keyClosest]['xytext'] = xyRectangle

	def get_rectangle_size_on_text(self,ax,text,inv):
		'''
		Returns rectangle to mimic the position
		'''	
		renderer = self.figure.canvas.get_renderer() 
		fakeText = ax.text(0,0,s=text)
		patch = fakeText.get_window_extent(renderer)
		xy0 = list(inv.transform((patch.x0,patch.y0)))
		xy1 = list(inv.transform((patch.x1,patch.y1)))
		fakeText.remove()
		widthText = xy1[0]-xy0[0]
		heightText = xy1[1]-xy0[1]
		return widthText, heightText
                             
	def update_data(self,data):
		'''
		Updates data to be used. This is needed if the order of the data 
		changed.
		'''
		self.data = data		
			






	
	
	