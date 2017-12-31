import matplotlib
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib._color_data import TABLEAU_COLORS,TABLEAU_COLORS,XKCD_COLORS,CSS4_COLORS
import seaborn as sns
from math import sqrt
import numpy as np
from collections import OrderedDict
from operator import itemgetter
from decimal import Decimal
import itertools
import os
import sys
from sys import platform as _platform


import tkinter as tk
from tkinter import ttk  
def return_platform():
    if _platform == "linux" or _platform == "linux2":
       platform = 'LINUX'
    elif _platform == "darwin":
       platform = 'MAC'
    elif _platform == "win32":
       platform = 'WINDOWS'
    elif _platform == "win64":
        platform = 'WINDOWS'
        
    return platform    

    
platform = return_platform() 


defaultFont = 'Verdana'
if platform == 'WINDOWS':
	corrFontSize = -1
else:
	corrFontSize = 0
LARGE_FONT = (defaultFont, 11+corrFontSize, "bold")
NORM_FONT = (defaultFont, 11+corrFontSize)
SMALL_FONT = (defaultFont,7+corrFontSize)
HELP_FONT=(defaultFont, 9+corrFontSize , "bold")
TITLE_FONT = (defaultFont,12+corrFontSize,"bold")
TITLE_FONT_NORM = (defaultFont,12+corrFontSize)

websiteUrl = 'http://www.instantclue.uni-koeln.de' 
websiteUrlVideos = 'http://www.instantclue.uni-koeln.de/videos.html'
webisteUrlTutorial = 'http://www.instantclue.uni-koeln.de/tutorials.html' 
gitHubUrl = 'http://github.com/hnolCol/InstantClue'
path_file = os.path.dirname(sys.argv[0])
tutorialPath = os.path.join(path_file,'InstantClueTutorial.pdf')
 
GREY = (211/255,211/255,211/255)
MAC_GREY = '#ededed'

titleLabelProperties = dict(font = LARGE_FONT, fg="#4C626F",
							bg = MAC_GREY, justify=tk.LEFT)



if platform == "WINDOWS":                             
    right_click = "<Button-3>"
    col_menu = "white"
    defaultFontSize = 9
    
elif platform == "MAC":
    right_click = "<Button-2>"
    col_menu = MAC_GREY
    defaultFontSize = 12
     
    

styleDict = {'tearoff':0,'background' : col_menu,'foreground':"black"}

color_schemes = ["Greys","Blues","Greens","Purples",'Reds',"BuGn","PuBu","PuBuGn","BuPu","OrRd","BrBG","PuOr","Spectral","RdBu","RdYlBu","RdYlGn",
                                    'Accent','Dark2','Paired','Pastel1','Pastel2','Set1','Set2','Set3','Set4','Set5']
linkage_methods = ['single','complete','average','weighted','centroid','median','ward']
             
pdist_metric = ['braycurtis', 'canberra', 'chebyshev', 'cityblock', 'correlation', 'cosine', 'dice', 'euclidean', 'hamming', 'jaccard', 'kulsinski', 'matching', 'minkowski',
                'rogerstanimoto', 'russellrao', 'seuclidean', 'sokalmichener', 'sokalsneath', 'sqeuclidean']

  
   
def merge_two_dicts(x,y):
	z = x.copy()
	z.update(y)
	return z
namedColors = dict()
## get colors
for colorDict in [TABLEAU_COLORS,CSS4_COLORS]:
	namedColors = merge_two_dicts(namedColors,colorDict)

                                  
arrow_args = dict(arrowstyle="-", color = "0.5")
bbox_args = None
signLineProps = dict(lw=0.5,color='k')
standardTextProps = dict(ha='center', va='bottom')

     	 	
multCorrAbbr = {'bonferroni':'bonferroni',
				'sidak':'sidak',
				'holm-sidak':'holm-sidak',
				'holm':'holm',
				'simes-hochberg':'simes-hochberg',
				'hommel':'hommel',
				'benjamini-hochberg':'fdr_bh',
				'benjamini-yekutieli':'fdr_by',
				'2-stage-set-up benjamini-krieger-yekutieli (recom.)':'fdr_tsbky',
				'gavrilov-benjamini-sarkar':'fdr_gbs',
				'storey-tibshirani':'storey-tibshirani'} 


namedColors = matplotlib.colors.get_named_colors_mapping()



def evaluate_screen(screen_width,screen_height,w,h):
     '''
     Checks if the desired resultion (w,h) fits to screen
     '''
		
	
     if screen_width < w or screen_height < h:

          if screen_width < w:
                screen_width_ = screen_width - (screen_width*0.075)
                screen_height_ = int(screen_width_ * (h/w))
                
                if screen_height_ > screen_height:
                     screen_height_ = screen_height - (screen_height*0.075)
                     screen_width_ = int(screen_height_ * (w/h))
                     
          elif screen_height < h:
                screen_height_ = screen_height - (screen_height*0.075)
                screen_width_ = int(screen_height_ * (w/h))
                if screen_width_ > screen_width:
                     screen_width_ = screen_width - (screen_width*0.075)
                     screen_height_ = int(screen_width_ * (h/w))
                     
          geom_ = "{}x{}".format(int(screen_width_),int(screen_height_))
     else:
          geom_ = "{}x{}".format(w,h)

     return geom_
		






def distance(co1, co2):
        return sqrt(pow(abs(co1[0] - co2[0]), 2) + pow(abs(co1[1] - co2[1]), 2))
    
def closest_coord_idx(list_, coord):
            if coord is not None:

            	dist_list = [distance(co,coord) for co in list_]
            	idx = min(enumerate(dist_list),key=itemgetter(1))
            	return idx
            	
def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return array[idx]
    
def find_nearest_index(array,value):
        idx = (np.abs(array-value)).argmin()
        return idx       
       
def fill_listbox(listbox,entryList):
	listbox.delete(0,tk.END)
	for entry in entryList:
		listbox.insert(tk.END, entry)
	
      
def col_c(color):
	'''
	from rgb to hex
	'''
	if '#' in color:
		return color
	if isinstance(color,tuple):
		y = tuple([int(float(z) * 255) for z in color])
		hexCol = "#{:02x}{:02x}{:02x}".format(y[0],y[1],y[2])
	elif 'xkcd:'+str(color) in XKCD_COLORS:
		hexCol = XKCD_COLORS['xkcd:'+str(color)]
	elif 'tab:'+str(color) in TABLEAU_COLORS:
		hexCol = TABLEAU_COLORS['tab:'+str(color)]
	elif color in namedColors:
		hexCol = namedColors[color]

	else:
		try:
			hexCol = matplotlib.colors.to_hex(color)
		except:
			hexCol = 'error'
			
	
	return hexCol   
				
              
              

def scale_data_between_0_and_1(inputData,min = None,max = None):
	'''
	Will log data before if useful. 
	'''
	if min is None:
		min  = inputData.min()
	if max is None:
		max = inputData.max()
		
	if max/(min+1) > 100000:
		inputData = np.log2(inputData)
		inputData = inputData.replace('-inf',0)
		min = np.log2(min)
		max = np.log2(max) 
		
	outputData = (inputData-min)/(max-min)
	return outputData
	

def minimumEditDistance(s1,s2):
	#'''
	#From: http://rosettacode.org/wiki/Levenshtein_distance#Python
	#'''
    if len(s1) > len(s2):
        s1,s2 = s2,s1
    distances = range(len(s1) + 1)
    for index2,char2 in enumerate(s2):
        newDistances = [index2+1]
        for index1,char1 in enumerate(s1):
            if char1 == char2:
                newDistances.append(distances[index1])
            else:
                newDistances.append(1 + min((distances[index1],
                                             distances[index1+1],
                                             newDistances[-1])))
        distances = newDistances
    return distances[-1]
	
def replace_key_in_dict( to_be_replaced, dict_input, replace):  
         
	dict_input.update({to_be_replaced: replace})
	return dict_input
     
def replace_nan_in_color_dict(colorMap,nanColor=GREY,additionalNanLevels = []):
	levelsToMakeNaN = ['nan',' ']+additionalNanLevels
	
	for level in levelsToMakeNaN:
		col_map_update = replace_key_in_dict(level, colorMap, nanColor) 
	return col_map_update
	

def build_rgb_layer_dict(rgbColors,GREY,naColor):
	'''
	'''
	
	layerColorDict = {}
	for n,color in enumerate(rgbColors):
		layerColorDict[color] = n+1
	
	layerColorDict[GREY] = -1
	layerColorDict[naColor] = -2
	
	return layerColorDict
		



		
def fill_axes_with_plot(data, x , y , hue, ax, cmap, plot_type = 'boxplot', 
							order = None,dodge=False, hue_order = None, inmutableCollections = [],
							addSwarmSettings = {'label':None,'sizes':[20],'facecolor':'white',
							'edgecolor':'black','linewidth':0.4,'alpha':1}):
    	 
         if plot_type == 'boxplot':
                         sns.boxplot(x= x, y=y,data=data, hue = hue, palette = cmap, order = order, 
                         fliersize = 3, linewidth=0.65, ax = ax, hue_order = hue_order)
         elif plot_type in ['add_swarm','swarm']:
                         if len(data.index) < 1000:
                         	sns.swarmplot(x= x, y=y,data=data, palette = cmap, hue = hue, 
                         	split = True, order=order, ax = ax, hue_order = hue_order)                         	
                         else:
                         	sns.stripplot(x= x, y=y,data=data, palette = cmap, hue = hue, 
                         	split = True, order=order, ax = ax, hue_order = hue_order, jitter = True)  
                         if plot_type == 'add_swarm':
                         	collections = ax.collections
                         	for collection in collections:
                         		if collection not in inmutableCollections:
                         			collection.set(**addSwarmSettings)      
                         			
         elif plot_type == 'barplot':
                         sns.barplot(x= x, y=y, hue = hue, data=data, order = order, 
                         palette = cmap,errwidth=0.5, capsize=0.09, edgecolor=".25", ax = ax,
                         hue_order = hue_order)
         elif plot_type == 'pointplot':
                         sns.pointplot(x= x, y=y, hue = hue, data=data, order = order, capsize=0.05, 
                                     	errwidth=0.4, scale=0.55,palette=cmap,dodge=dodge,ax=ax,
                                     	hue_order = hue_order)
         elif plot_type == 'violinplot':
                         sns.violinplot(x= x, y=y, hue = hue, data=data, palette = cmap ,order=order, 
                         linewidth=0.65, ax = ax, hue_order = hue_order)
                         give_violins_edge_color(ax)
       
		 

def give_violins_edge_color(ax):
	
         
    axCollection = ax.collections
    axCollection = axCollection[::2]
    for  collection in axCollection:
    	collection.set_edgecolor("black")
    	collection.set_linewidth(0.55)	
                       
def match_color_to_uniqe_value(uniqueValues, colorMap):
	'''
	Unique values  
	Needed for correct color when missing values occur / categorical plotting
	'''
	if isinstance(uniqueValues,np.ndarray):
		uniqueValues = uniqueValues.tolist()
	
	if isinstance(uniqueValues[0],list):
		uniqueValues = [tuple(x) for x in uniqueValues]
	numbUniqueValues = len(uniqueValues)

	colorMap = sns.color_palette(colorMap,numbUniqueValues)
	colorDict = OrderedDict(zip(uniqueValues,colorMap))
	return colorDict
	
def get_color_category_dict(dfClass,categoricalColumn,colorMap,userDefinedColors,naColor = GREY,naString = '-'):
	'''
	This is needed for updating the color in scatter plots with same colors 
	Retrns a dict of : Categorical level - color
	'''	
	if isinstance(categoricalColumn,str):
		categoricalColumn = [categoricalColumn]
	numCategoricalColumn = len(categoricalColumn)	
	if  numCategoricalColumn == 1:

		uniqueCategories = dfClass.get_unique_values(categoricalColumn[0])
		numbUniqueCategories = uniqueCategories.size
		rgbColors = sns.color_palette(colorMap, numbUniqueCategories)
		colorMapDict = OrderedDict(zip(uniqueCategories ,rgbColors))
		colorMapDict = replace_nan_in_color_dict(colorMapDict,naColor,
							additionalNanLevels = [naString])
	
	else:
		collectUniqueCategories = []
		for categColumn in categoricalColumn:
			
			catUnique = dfClass.get_unique_values(categColumn)
			collectUniqueCategories.append(catUnique.tolist())
		
		theoreticalCombinations = list(itertools.product(*collectUniqueCategories))
		combinationsInData = dfClass.df[categoricalColumn].apply(tuple,axis=1)
		uniqueCategories = combinationsInData.unique() 
		numbUniqueCombData = uniqueCategories.size
		
		rgbColors = sns.color_palette(colorMap,numbUniqueCombData)
		
		colorMapDict = OrderedDict(zip(uniqueCategories ,rgbColors))	
		
		colorMapDict = replace_nan_in_color_dict(colorMapDict,naColor,
							additionalNanLevels = [(naString,)*numCategoricalColumn])
			 
	colorMapDictRaw = colorMapDict.copy()
	for category in uniqueCategories:
			if category in userDefinedColors:
				colorMapDict[category] = userDefinedColors[category]
	
	layerColorDict = build_rgb_layer_dict(rgbColors,GREY,naColor)	
	
	return colorMapDict, layerColorDict, colorMapDictRaw


def split_except_brac(self,s):
         parts = []
         bracket_level = 0
         current = []
         # trick to remove special-case of trailing chars
         for c in (s + " "):
             if c == " " and bracket_level == 0:
                 parts.append("".join(current))
                 current = []
             else:
                 if c == "{":
                     bracket_level += 1
                 elif c == "}":
                     bracket_level -= 1
                 current.append(c)
         return parts 		
		
def xLim_and_yLim_delta(ax):

        xmin,xmax = ax.get_xlim()
        ymin,ymax = ax.get_ylim()
        delta_x = xmax-xmin
        delta_y = ymax-ymin
        return delta_x,delta_y




def calculate_new_ylim_from_data(data, force_ylim_NULL = False):
                 get_max_val = data.max().max()
                 get_min_val = data.min().min()
                 add = 0.12
                 y_min = round(get_min_val-abs(get_min_val*add),2)
                 y_max = round(get_max_val+get_max_val*add,2)
                 if force_ylim_NULL:
                 	y_min = 0
                 
                 return (y_min,y_max)                     


def get_elements_from_list_as_string(itemList, addString = '',newLine = False, maxStringLength = 40):
	'''
	'''
	if isinstance(itemList,str):
		return itemList
	for n,item in enumerate(itemList):
		if maxStringLength is not None:
			item = str(item)[:maxStringLength]
		if n == 0:
			if newLine:
				addString = '{}\n{}'.format(addString,item)
			else:
			
				addString = '{}{}'.format(addString,item)
		else:
			addString = '{}, {}'.format(addString,item)     
			
	return addString
			
    
    
    
def return_readable_numbers(number):
     """Returns number as string in a meaningful and readable way to omit to many digits"""  
     if number < 0.1:
     		new_number = '{:.2E}'.format(number)
     elif number < 10:
     		new_number = round(number,2)
     elif number < 200:
     		new_number = float(Decimal(str(number)).quantize(Decimal('.01')))
     elif number < 10000:
     		new_number = round(number,0)
     else: 
     		new_number = '{:.2E}'.format(number)		
     return new_number              
            



def get_max_colors_from_pallete(cmap):
    '''
    '''
    
    if cmap in ["Greys","Blues","Greens","Purples",'Reds',"BuGn","PuBu","PuBuGn","BuPu","OrRd","BrBG","PuOr","Spectral","RdBu","RdYlBu","RdYlGn"]:
        n = 60
    elif cmap in ['Accent','Dark2','Pastel2','Set2','Set4']:
        n=8
    elif cmap in ['Paired','Set3']:
        n = 12
    elif cmap in ['Pastel1','Set1']:
        n = 9
    elif cmap == 'Set5':
        n = 13
    
    cmap = ListedColormap(sns.color_palette(cmap, n_colors = n ,desat = 0.85))  
    
    return cmap

def create_button(container, image = None, command = None , text = None, compound = None):
	'''
	'''
	if platform == 'WINDOWS':
		button = ttk.Button(container,text = text,image = image, command = command, compound = compound)
	else:
		button = tk.Button(container,text = text,image = image, command = command, compound = compound)
		
	return button
	


	
	
	
	
	
	
		
		
class Progressbar(object):
	def __init__(self,title = ''):
	
		self.title = title
		
		self.build_toplevel()
		self.build_widgets()
		
		

	def close(self):
		'''
		'''
		self.toplevel.destroy() 
		
	def build_toplevel(self):
		
		'''
		Builds the toplevel to put widgets in 
		'''
        
		popup = tk.Toplevel(bg=MAC_GREY) 
		popup.wm_title(self.title) 
         
		popup.protocol("WM_DELETE_WINDOW", self.close)
		w=210
		h=75
		self.toplevel = popup
		self.center_popup((w,h))
		
	
	def build_widgets(self):
 		'''
 		Builds the dialog for interaction with the user.
 		'''	 
 		
 		self.progressVariable = tk.IntVar()
 		self.progressText = tk.StringVar()
 		
 		
 		self.cont= tk.Frame(self.toplevel, background =MAC_GREY) 
 		self.cont.pack(expand =True, fill = tk.BOTH)
 		self.cont.grid_columnconfigure(0,weight=1)
 		
 		self.progressBar = ttk.Progressbar(self.cont, orient=tk.HORIZONTAL, variable=self.progressVariable)
 		
 		progressLabel = tk.Label(self.cont, textvariable = self.progressText, 
 									bg=MAC_GREY, justify = tk.RIGHT)
 		self.progressBar.grid(sticky=tk.EW,padx=10,pady=5)
 		progressLabel.grid(padx=5,sticky=tk.E)
 		  	
		#progressBar.grid()
		#progressLabel.grid()
		
	def update_progressbar_and_label(self,newValue,newText, updateText = True):
		'''
		'''
		self.progressVariable.set(newValue)
		if updateText:
			self.progressText.set(newText)
		self.toplevel.update()	
	  

	def center_popup(self,size):
         	'''
         	Casts poup and centers in screen mid
         	'''
	
         	w_screen = self.toplevel.winfo_screenwidth()
         	h_screen = self.toplevel.winfo_screenheight()
         	x = w_screen/2 - size[0]/2
         	y = h_screen/2 - size[1]/2
         	self.toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))		
		
	




"""
Created on Sun Jun 25 19:29:51 2017

@author: https://stackoverflow.com/questions/3221956/what-is-the-simplest-way-to-make-tooltips-in-tkinter
THANKS TO THE AUTHOR ## modofied to add a title Label and show colors
"""


def min_x_square(cm):
	n = np.linspace(-np.pi,np.pi/2, num=cm)
	
	out = [np.cos(x)+1.4 for x in n]
	return out

class CreateToolTip(object):

    def __init__(self, widget,
                 *,
                 title_ = None,
                 bg='white',
                 pad=(5, 3, 5, 3),
                 text= None,
                 waittime=300,
                 wraplength=250,
                 showcolors = False,cm = None):

        self.waittime = waittime  # in miliseconds, originally 500
        self.wraplength = wraplength  # in pixels, originally 180
        self.widget = widget
        self.text = text
        self.title = title_
        self.widget.bind("<Enter>", self.onEnter)
        self.widget.bind("<Leave>", self.onLeave)
        self.widget.bind("<ButtonPress>", self.onLeave)
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None
        self.plat = platform
        self.showcolors = showcolors
        self.cm = cm
        self.f_tw  = None
        self.canvas = None

    def onEnter(self, event=None):
    	self.schedule()
        

    def onLeave(self, event=None):
    	if self.showcolors == True:
    		if self.f_tw  is not None and self.canvas is not None:
    			self.f_tw.clear()
    			plt.close(self.f_tw)
    			try:
    				self.canvas.get_tk_widget().delete("all")
    				self.canvas.get_tk_widget().destroy()
    			except:
    				pass 	
    			
    	self.unschedule()
    	self.hide()
    		
       
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self):
        def tip_pos_calculator(widget, label,
                               *,
                               tip_delta=(10, 5), pad=(5, 3, 5, 3)):

            w = widget

            s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()

            width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                             pad[1] + label.winfo_reqheight() + pad[3])

            mouse_x, mouse_y = w.winfo_pointerxy()

            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height

            x_delta = x2 - s_width
            if x_delta < 0:
                x_delta = 0
            y_delta = y2 - s_height
            if y_delta < 0:
                y_delta = 0

            offscreen = (x_delta, y_delta) != (0, 0)

            if offscreen:

                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width

                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height

            offscreen_again = y1 < 0  # out on the top

            if offscreen_again:
                y1 = 0

            return x1, y1

        bg = self.bg
        pad = self.pad
        widget = self.widget
        self.tw = tk.Toplevel(widget)
        

        if self.plat == 'WINDOWS':
        # Leaves only the label and removes the app window
            self.tw.wm_overrideredirect(True)
            font_size = 9
        else:
            self.tw.tk.call("::tk::unsupported::MacWindowStyle","style",self.tw._w, "plain", "none")
            font_size = 11
        win = tk.Frame(self.tw,
                       background=bg,
                       relief=tk.GROOVE,
                       )
        if self.text is not None:
        	title_label = tk.Label(win, text = self.title,background=bg,
                               justify =tk.LEFT,wraplength=self.wraplength,
                               font = (defaultFont, font_size,'bold'))
        	label = tk.Label(win,
                          text=self.text,
                          justify=tk.LEFT,
                          background=bg,
                          relief=tk.SOLID,
                          borderwidth=0.0,
                          wraplength=self.wraplength,
                          font = (defaultFont, font_size))
        	title_label.grid(sticky = tk.W) 
        	label.grid(padx=(pad[0], pad[2]),
                   pady=(pad[1], pad[3]),
                   sticky=tk.W)
        if self.showcolors == True:
                
        	self.f_tw = plt.figure(figsize = (4.0,1.2), facecolor='white')
        	self.f_tw.subplots_adjust(wspace=0.0, hspace=0.0,
        							 right = 1, top = 1, left = 0.0, bottom = 0.0)
        	ax = self.f_tw.add_subplot(111)
        	cm_ = sns.color_palette(self.cm,15)
        	cm = []
        	for color in cm_:
        		if color not in cm:
        			cm.append(color)
        	y_bar = min_x_square(len(cm)) 

        	ax.bar(range(len(cm)),y_bar, color= cm, edgecolor="darkgrey",linewidth=0.72)
        	ax.set_ylim(-0.1,max(y_bar)+0.5)
        	ax.set_xlim(-0.7,len(cm))
        	ax.axhline(0, color = "darkgrey", linewidth=0.72)
        	ax.axvline(-0.6,color="darkgrey",linewidth=0.72)
        	self.canvas = FigureCanvasTkAgg(self.f_tw,win)
        	plt.axis('off')
        	self.canvas._tkcanvas.grid(in_=win, sticky = tk.W,padx=10,pady=10)
        	self.canvas.get_tk_widget().grid(in_=win, sticky = tk.W,padx=10,pady=10)
        	if self.cm not in ['Accent','Pastel1','Pastel2','Set1','Set3','Spectra','RdYlGn']:
        		col_blind = 'True'
        	else:
        		col_blind = 'False'
        	if self.cm in ["Greys","Blues","Greens","Purples",'Reds',"BuGn","PuBu","PuBuGn","BuPu","OrRd"]:
        		type = 'sequential'
        		n = np.inf
        	elif self.cm in ["BrBG","PuOr","Spectral","RdBu","RdYlBu","RdYlGn"]:
        		type = 'diverging'
        		n = np.inf
        	else:
        		type = 'qualitative'
        		n = len(cm)
        	text = self.text + '\nMaximum number of colors: {}\nColorblind safe: {}\nType: {}'.format(n,col_blind,type)
        	label.configure(text=text)
        	if self.plat == 'WINDOWS':
                        self.tw.attributes('-topmost',True)
            
        win.grid()
        
		
        x, y = tip_pos_calculator(widget, label)
        

        self.tw.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        tw = self.tw
        if tw:
            tw.destroy()
        self.tw = None
        


class fisher_on_mult_threads(object):
    """"Fisher Exact test for mutliprocessing"""
    def __init__(self, col, background):
        self.col = col
        self.background = background
    def __call__(self, category):    
        
                    
                    cat_select = self.background[self.col].str.contains(category, na=False)
                    self.background.loc[:,'Cat_to_test'+str(category)] = cat_select
                    cat_size = sum(cat_select)            
                    cross_tab = pd.crosstab(self.background['Cat_to_test'+str(category)] ,self.background['idx_in_selection'])
                    
                    if cross_tab.shape == (2,2):
                        cat_size_in_sel = cross_tab.iloc[1,1]
                        odds, p = fisher_exact(cross_tab)
                        
                        return self.col, category, int(cat_size), int(cat_size_in_sel),round(odds,3),"{:.2e}".format(p)
                    else:
                       pass
                
class perpetualTimer():
   """Timer to start process on different threat"""
   def __init__(self,t,hFunction):
      self.t=t
      self.hFunction = hFunction
      self.thread = Timer(self.t,self.handle_function)

   def handle_function(self):
      self.hFunction()
      self.thread = Timer(self.t,self.handle_function)
      self.thread.start()

   def start(self):
      self.thread.start()

   def cancel(self):
      self.thread.cancel()

class cd():
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

tooltip_information_plotoptions = [
        ["At least one numeric column\nMax. Categories for factorplot: 3\nData are represented by a single point showing the confidence interval (0.95) and are connected if they belong to the same group.",
         "Pointplot\n\nInput:"],
        ["At least two numeric columns (maximum 3)\ Categories for factorplot: up to 3 supported. More categories can be added using the color option. Simply drag & drop the desired numerical or categorical column to the color button.\nAdditional categories can be added using drag & drop to the newly created color button.",
         "Scatter\n\nInput:"],
         ["At least two numeric columns\nCategories are not supported.\nTime series option uses the first column as the x-axis and all addition columns are plotted against this value. E.g. the first column should be the time while the following columns are numeric values (measurements)",
         "Time Series\n\nInput:"],
          ["At least two numeric columns\nCategories are not supported.\nColors and Size changes might be added as described for scatter plots.",
         "Scatter Matrix\n\nInput:"],
           ["At least one numeric column\nUnlimtited categories can be added.\nIf categorical columns are present each combination of categories will be used to slice data and to display the density information.",
         "Density plot\n\nInput:"],
            ["At least one numeric column\nMax. Categories for factorplot: 3\nUnlimited when Split categories disabled.\nThe error bars indicate the confidence interval (0.95).\nAdditional Options: Split Categories and split categories in different subplots.",
         "Barplot\n\nInput:"],
        ["At least one numeric column\nMax. Categories for factorplot: 3\nUnlimited when Split categories disabled.\n\nAdditional Options: Split Categories and split categories in different subplots.",
         "Boxplot\n\nInput:"],
         ["At least one numeric column\nMax. Categories for factorplot: 3\nUnlimited when Split categories disabled.\n\nAdditional Options: Split Categories and\nsplit categories in different subplots.\nViolin plot show a boxplot inside as well kernel density information",
         "Violinplot\n\nInput:"],
        ["At least one numeric column\nMax. Categories for factorplot: 3\nUnlimited when Split categories disabled.\n\nAdditional Options: Split Categories and\nsplit categories in different subplots.\nSwarmplots show the raw data points separated by jitter on x-axis.",
         "Swarmplot\n\nInput:"],
        ["Raw datapoints separated by jitter can be added to: Box-, Bar-, and Violinplots. The datapoints cannot be changed in color and size.",
         "Add swarm to plot\n\nInput:"],
         ["At least two numeric column\nCategories are not supported.",
         "Hierachical Clustering\n\nInput:"],
        ["At least two numeric columns.\nA correlation matrix calculates the Pearson correlation coefficient and uses hierachical clustering for interpretation.",
         "Correlation Matrix\n\nInput:"],
        # ["Up to one nuermic column to control size of each node.\nAt least two categorical columns to describe the edges.",
        # "Network\n\nInput:"],
           ["Opens a popup that allows you too change details of your created chart.\nNote that you can also save settings as templates and load them to get the exact same chart configuration.\nFor same coloring it is essential that the categories are sorted in the same way as in the template.",
         "Configure\n\n"]
        ]






    	
    