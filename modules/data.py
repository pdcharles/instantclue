
import numpy as np
from scipy.signal import lfilter
from sklearn.neighbors import KernelDensity

import pandas as pd


from collections import OrderedDict
from modules.utils import *

def z_score(x):
	mean = x.mean()
	std = x.std() 
	vector = (x-mean)/std
	return vector
   
       
calculations = {'log2':np.log2,
					'-log2':lambda x:np.log2(x)*(-1),
					'log10':np.log10,
					'-log10':lambda x: np.log10(x)*(-1),
					'ln':np.log,
					'Z-Score':lambda x: z_score(x),
					}	
	


class DataCollection(object):
	'''
	'''

	def __init__(self, dataFrame = None):
	
		self.currentDataFile = None
		self.df = pd.DataFrame()
		self.df_columns = []
		self.dfs = OrderedDict()
		self.dfsDataTypesAndColumnNames = OrderedDict() 
		self.fileNameByID = OrderedDict() 
		self.rememberSorting = dict()
		self.replaceObjectNan = '-'
	
	
	def add_data_frame(self,dataFrame, id = None, fileName = ''):
		'''
		Adds new dataFrame to Dict.
		'''
		if id is None:
			id = self.get_next_available_id()
		
		self.extract_data_type_of_columns(dataFrame,id)
		self.dfs[id] = dataFrame
		self.fileNameByID[id] = fileName
	
	
	def add_count_through_column(self, columnName = None):
		'''
		Simply adds a column that enumerates over the data.
		'''
		if columnName is None:
			columnName = 'CountThrough'
		nRow = self.get_row_number() 
		countThrough = np.arange(0,nRow) 
		columnName = self.evaluate_column_name(columnName=columnName)
		
		self.insert_column_at_index(0,columnName,countThrough)
		self.update_columns_of_current_data()
		return columnName
	
	
	def add_column_to_current_data(self,columnName,columnData,evaluateName = True):
		'''
		Adds a new column to the current data
		'''
		if evaluateName:
			columnName = self.evaluate_column_name(columnName)
		self.df.loc[:,columnName] = columnData
		self.update_columns_of_current_data() 
	
		
	def calculate_kernel_density_estimate(self,numericColumns):
		'''
		'''
		newColumnName = 'kde_{}'.format(numericColumns)
		data = self.df[numericColumns].dropna(subset=numericColumns)
		indexSubset = data.index
		nRows = len(indexSubset)
		nColumns = len(numericColumns) 
		bandwidth = nRows**(-1/(nColumns+4)) 
		
		kde = KernelDensity(bandwidth=bandwidth,
                        kernel='gaussian', algorithm='ball_tree')
		
		kde.fit(data) 
		kde_exp = pd.DataFrame(np.exp(kde.score_samples(data)),columns = [newColumnName], index=indexSubset)
		self.df = self.df.join(kde_exp)
		
		return newColumnName
	
         
         
		
	def calculate_rolling_metric(self,numericColumns,windowSize,metric,quantile = 0.5):
		'''
		Calculates rolling windows and metrices (like mean, median etc). 
		Can be used for smoothing
		'''
		newColumnNames = ['[{}_w{}]_{}'.format(metric,windowSize,columnName) for columnName in numericColumns] 
		rollingWindow = self.df[numericColumns].rolling(window=windowSize)
		
		if metric == 'mean':
			self.df[newColumnNames] = rollingWindow.mean() 
		elif metric == 'median':
			self.df[newColumnNames] = rollingWindow.median()
		elif metric == 'sum':
			self.df[newColumnNames] = rollingWindow.sum() 
		elif metric == 'max':
			self.df[newColumnNames] = rollingWindow.max()
		elif metric == 'min':
			self.df[newColumnNames] = rollingWindow.min()
		elif metric == 'std':
			self.df[newColumnNames] = rollingWindow.std()
		elif metric == 'quantile':
			self.df[newColumnNames] = rollingWindow.quantile(quantile=quantile)
		self.update_columns_of_current_data()
		
		return newColumnNames
		

	def calculate_row_wise_metric(self,metric,numericColumns,promptN):
		'''
		'''

		if metric == 'Mean & Stdev [row]':
			newColumnName = ['{}_{}'.format(metric,get_elements_from_list_as_string(numericColumns))\
			 for metric in ['Mean','Stdev']]
		elif metric == 'Mean & Sem [row]':
			newColumnName = ['{}_{}'.format(metric,get_elements_from_list_as_string(numericColumns))\
			 for metric in ['Mean','Sem']]
		elif metric == 'Square root [row]':
			newColumnName = ['{}_{}'.format(metric.replace(' [row]','')	,columnName) for columnName in numericColumns]
		elif metric in ['N ^ x [row]','x ^ N [row]','x * N [row]']:
			newColumnName = ['{}({})_{}'.format(metric.replace(' [row]','')	,promptN,columnName) for columnName in numericColumns]
		else:
			newColumnName = '{}_{}'.format(metric.replace(' [row]','')	,get_elements_from_list_as_string(numericColumns))
		if metric == 'Mean [row]':
			self.df[newColumnName] = self.df[numericColumns].mean(axis=1)
		elif metric == 'Square root [row]':
			self.df[newColumnName] = self.df[numericColumns].apply(np.sqrt,axis=1) 
		elif metric == 'Stdev [row]':
			self.df[newColumnName] = self.df[numericColumns].std(axis=1)
		elif metric == 'Sem [row]':
			self.df[newColumnName] = self.df[numericColumns].sem(axis=1)
		elif metric == 'Median [row]':
			self.df[newColumnName] = self.df[numericColumns].median(axis=1)
		elif metric == 'x * N [row]':
			self.df[newColumnName] = self.df[numericColumns] * promptN#.apply(lambda row, pow=promptN: np.multiply(row,pow),axis=1)
		elif metric == 'N ^ x [row]':
			self.df[newColumnName] = self.df[numericColumns].apply(lambda row, pow=promptN: np.power(pow,row),axis=1)
		elif metric == 'x ^ N [row]':
			self.df[newColumnName] = self.df[numericColumns]** promptN# .apply(lambda row, pow=promptN: np.power(row,pow), axis=1)
		elif metric == 'Mean & Stdev [row]':
			self.df[newColumnName[0]] = self.df[numericColumns].mean(axis=1)
			self.df[newColumnName[1]] = self.df[numericColumns].std(axis=1)
		elif metric == 'Mean & Sem [row]':
			self.df[newColumnName[0]] = self.df[numericColumns].mean(axis=1)
			self.df[newColumnName[1]] = self.df[numericColumns].sem(axis=1)
		
		if isinstance(newColumnName,str):
			newColumnName = [newColumnName]
			
		self.update_columns_of_current_data()

		return newColumnName		 
		
	

	def change_data_type_in_current_data(self,columnList, newDataType):
		'''
		Changes the DataType of a List of column Names
		'''
		try:		
			self.df[columnList] = self.df[columnList].astype(newDataType)
		except ValueError:
			return 'ValueError'
			
		if newDataType == 'object':
			self.df[columnList].fillna(self.replaceObjectNan,inplace=True)
			
		self.update_columns_of_current_data()
		return 'worked'
		
	def combine_columns_by_label(self,columnLabelList, sep='_'):
		'''
		'''
		combinedRowEntries = []
		
		for columnName in columnLabelList[1:]:
			combinedRowEntries.append(self.df[columnName].astype(str).values.tolist())
			
		columnName = 'Comb.: '+str(columnLabelList)[1:-1]
		columnNameEval = self.evaluate_column_name(columnName)
		self.df.loc[:,columnNameEval] = self.df[columnLabelList[0]].astype(str).str.cat(combinedRowEntries,sep=sep)
		
		self.update_columns_of_current_data()
		return columnNameEval

			
	def delete_rows_by_index(self, index):
		'''
		Delete rows by index
		'''
		self.df.drop(index, inplace=True)
		self.save_current_data()
			
		
	def delete_column_by_index(self, index):
		'''
		Deletes columns of current df by index
		'''
		colname = self.df_columns[index]
		self.df.drop([colname], axis=1, inplace=True) 
		self.update_columns_of_current_data()
		return
		
		
	def delete_columns_by_label_list(self,columnLabelList):
		'''
		Delete columns by Column Name List. 
		'''
		self.df.drop(columnLabelList,axis=1,inplace=True)
		self.update_columns_of_current_data()
				
	def delete_data_file_by_id(self,id):
		'''
		Deletes DataFile
		'''	
		
		del self.dfs[id]
		del self.fileNameByID[id]
		del self.dfsDataTypesAndColumnNames[id]
		
		if id == self.currentDataFile:
			self.df = pd.DataFrame()
			self.df_columns = []

	def divide_columns_by_value(self,columnAndValues,baseString):
		'''
		columnAndValues - dict - keys = columns, values = value
		'''
		newColumnNames = []
		for column, correctionValue in columnAndValues.items():
			name = '{} {}'.format(baseString,column)
			newColumnName = self.evaluate_column_name(name)
			self.df[name] = self.df[column] / correctionValue
			newColumnNames.append(newColumnName) 
		self.update_columns_of_current_data()
		return newColumnNames
		
	def drop_rows_with_nan(self,columnLabelList,thresh=None):
		'''
		Drops rows with NaN
		'''
		if isinstance(columnLabelList,list):
			pass
		elif isinstance(columnLabelList,str):
			columnLabelList = [columnLabelList]
		self.df.dropna(subset=columnLabelList,inplace=True, thresh=thresh)
			
	def duplicate_columns(self,columnLabelList):
		'''
		Duplicates a list of columns and inserts the column at the position + 1
		of the original column. 
		'''
		columnLabelListDuplicate = ['Dupl_'+col for col in columnLabelList]
		columnIndexRaw = [self.df_columns.index(col)  for col in self.df_columns if col in columnLabelList]
		
		for i,columnIndex in enumerate(columnIndexRaw):
			columnIndex = columnIndex + 1 + i
			columnColumn = columnLabelListDuplicate[i]
			columnLabel = columnLabelList[i]
			newColumnData = self.df[columnLabel]
			self.insert_column_at_index(columnIndex, columnColumn, newColumnData)
			
		self.update_columns_of_current_data()
		return columnLabelListDuplicate
		
	def evaluate_columnNames_of_df(self, df):
		'''
		Checks each column name individually to avoid same naming and overriding.
		'''
		columns = df.columns.values.tolist() 
		evalColumns = [self.evaluate_column_name(column) for column in columns]
		df.columns = evalColumns
		return df
		
			
	def evaluate_column_name(self,columnName,columnList = None, useExact = False, maxLength = 80):
		'''
		Check if the column name already exists and how often. Adds a suffix.
		'''
		if columnList is None:
			columnList = self.df_columns 
		if useExact:
			columnNameExists = [col for col in columnList if columnName == col]
		else:
			columnNameExists = [col for col in columnList if columnName in col]
		
		numberColumnNameExists = len(columnNameExists)
		if numberColumnNameExists > 0:
			newColumnName = columnName+'_'+str(numberColumnNameExists)
		else:
			newColumnName = columnName
		if len(newColumnName) > maxLength-10:
			newColumnName = newColumnName[:maxLength-30]+'___'+newColumnName[-30:]
		return newColumnName
	
	def extract_data_type_of_columns(self,dataFrame,id):
		'''
		Saves the columns name per data type. In InstantClue there is no difference between
		objects and others non float, int, bool like columns.
		'''
		dataTypeColumnRelationship = dict() 
		for dataType in ['float64','int64','object','bool']:
			try:
				if dataType != 'object':
					dfWithSpecificDataType = dataFrame.select_dtypes(include=[dataType])
				else:
					dfWithSpecificDataType = dataFrame.select_dtypes(exclude=['float64','int64','bool'])
			except ValueError:
				dfWithSpecificDataType = pd.DataFrame() 		
			columnHeaders = dfWithSpecificDataType.columns.values.tolist()
			dataTypeColumnRelationship[dataType] = columnHeaders
		self.dfsDataTypesAndColumnNames[id] = dataTypeColumnRelationship
	
		
	def export_current_data(self,format='txt',path = ''):
		'''
		
		'''
		if format == 'txt':
			self.df.to_csv(path, index=None, na_rep ='NaN', sep='\t')
		elif format == 'Excel':
			self.df.to_excel(path, index=None, sheet_name = sheet_name, na_rep = 'NaN')
		

	def export_data_by_id(self, id, format):
		'''
		Set current data and then export the current data.
		'''
		
		self.set_current_data_by_id(id=id)
		self.export_current_data(format=format) 		
	
	def fill_na_in_columnList(self,columnLabelList,naFill = None):
		'''
		Replaces nan in certain columns by value
		'''
		if naFill is None:
			naFill = self.replaceObjectNan
		self.df[columnLabelList] = self.df[columnLabelList].fillna(naFill)
	
	def get_numeric_columns(self):
		'''
		Returns columns names that are float and integers
		'''
		numColumns = self.dfsDataTypesAndColumnNames[self.currentDataFile]['float64'] + \
		self.dfsDataTypesAndColumnNames[self.currentDataFile]['int64']
		
		return numColumns
		
	def get_data_as_list_of_tuples(self, columns, data = None):
		'''
		Returns data as list of tuples. Can be used for Lasso contains events.
		'''
		if len(columns) < 2:
			return
		if data is None:
			data = self.df
		tuples = list(zip(data[columns[0]], data[columns[1]]))
		return tuples
		
						
	def get_columns_data_type_relationship(self):
		'''
		Returns columns datatypes relationship
		'''
		return self.dfsDataTypesAndColumnNames[self.currentDataFile]
		
	def get_columns_data_type_relationship_by_id(self, id):
		'''
		Returns columns datatypes relationship by ID
		'''
		return self.dfsDataTypesAndColumnNames[id]	
	
	
	def get_data_types_for_list_of_columns(self,columnNameList):
		'''
		'''
		dataTypeList = [self.df[column].dtype for column in columnNameList]
		return dataTypeList
			
	def get_complete_data_collection(self):
		'''
		Returns an orderedDictionary with all added data.
		'''
		
		self.save_current_data()
		return self.dfs 
	
	def get_file_names(self):
		'''
		Returns the available file names
		'''
		return list(self.fileNameByID.values())
		
	def get_number_of_columns_in_current_data(self):
		'''
		Returns number of columns
		'''	
		return len(self.df_columns) 
		
	def get_columns_of_current_data(self):
		'''
		Returns column names of current data
		'''
		return self.df_columns	
	
	def get_columns_of_df_by_id(self,id):
		'''
		'''
		return self.dfs[id].columns.values.tolist()
	
	def get_current_data_by_column_list(self,columnList):
		'''
		Returns sliced self.df
		'''	
		return self.df[columnList]
		
	def get_current_data(self):
		'''
		Returns current df 
		'''
		return self.df
		
	def get_data_by_id(self,id, setDataToCurrent = False):
		'''
		Returns df by id that was given in function: addDf(self)..
		'''
			
		if setDataToCurrent:
			self.set_current_data_by_id(id = id) 
			return self.df
		else:
			return self.dfs[id]
	
	def get_file_name_of_current_data(self):
		'''
		Returns the file name of currently selected data frame.
		'''
		return self.fileNameByID[self.currentDataFile]
			
	def get_groups_by_column_list(self,columnList, sort = False):
		'''
		Returns gorupby object of selected columnList
		'''
		
		if isinstance(columnList,list):
			groupByObject = self.df.groupby(columnList,sort = sort)
			
			return groupByObject
		else:
			return
		
	
	def get_id_of_current_data(self):
		'''
		Returns the currently active data frame ID.
		'''
		return self.currentDataFile
		
	
	def get_next_available_id(self):
		'''
		To provide consistent labeling, use this function to get the id the new df should be added
		'''
		addedDataFrames = len(self.dfs)
		idForNextDataFrame = 'DataFrame: {}'.format(addedDataFrames)
		
		return idForNextDataFrame
	
	def get_row_number(self):
		'''
		Returns the number of rows.
		'''
		return len(self.df.index)	
	
	def get_unique_values(self,categoricalColumn, forceListOutput = False):
		'''
		Return unique values of a categorical column. If multiple columns are
		provided in form of a list. It returns a list of pandas series having all
		unique values.
		'''
		if isinstance(categoricalColumn,list):
			if len(categoricalColumn) == 1:
				categoricalColumn = categoricalColumn[0]
				uniqueCategories = self.df[categoricalColumn].unique()
			else:
				collectUniqueSeries = []
				for category in categoricalColumn:
					collectUniqueSeries.append(self.df[category].unique())
				return collectUniqueSeries
		else:
			uniqueCategories = self.df[categoricalColumn].unique()
		if forceListOutput:
			return [uniqueCategories]
		else:
			return uniqueCategories
		
	
	def iir_filter(self,columnNameList,n):
		'''
		Uses an iir filter to smooth data. Extremely useful in time series.
		'''
		b = [1.0/n]*n
		a=1
		newColumnNames = [self.evaluate_column_name('IIR(n_{})_{}'.format(n,columnName)) for columnName in columnNameList]
		
		transformedDataFrame = self.df[columnNameList].apply(lambda x: lfilter(b,a,x))

		self.df[newColumnNames] = transformedDataFrame
		self.update_columns_of_current_data()
		return newColumnNames
		
		
	
	def insert_data_frame_at_index(self, dataFrame, columnList, indexStart, indexList = None):
		'''
		Inserts Data Frame at certain location
		'''
		if any(columnName in self.df_columns for columnName in columnList):		
			return   
			
		for n,columnName in enumerate(columnList):
			
		
			if indexList is None:
				index = indexStart + 1 + n 
			else:
				index = indexList[n]
			newColumnData = dataFrame[columnName]
				
			self.insert_column_at_index(index,columnName,newColumnData)
		
			
			
	def insert_column_at_index(self, index, columnName, newColumnData):
		'''
		Inserts data at given index in current df.
		'''
		self.df.insert(index,columnName,newColumnData) 
		
	def join_series_to_currently_selected_df(self,series):
		'''
		'''
		self.df = self.df.join(series)
		self.update_columns_of_current_data()
		
	def join_df_to_currently_selected_df(self,dfToAdd, exportColumns = False):
		'''
		Joins another dataframe onto the currently selected one
		'''
		dfToAdd = self.evaluate_columnNames_of_df(dfToAdd)
		self.df = self.df.join(dfToAdd, rsuffix='_', lsuffix = '' ) 
		self.update_columns_of_current_data()
		
		if exportColumns:
			return dfToAdd.columns.values.tolist()
		
	def join_df_to_df_by_id(self,dfToAdd,id):
		'''
		Joins another data frame onto the df that is defined by id
		'''
		saveId = self.currentDataFile
		# we need to change to have a suitable evaluation
		self.set_current_data_by_id(id)
		df = self.dfs[id]
		dfToAdd = self.evaluate_columnNames_of_df(dfToAdd)
		self.dfs[id] = df.join(dfToAdd,rsuffix='_', lsuffix = ''  ) 
		self.set_current_data_by_id(saveId)
				
		
	def join_missing_columns_to_other_df(self,otherDf, id, definedColumnsList = []):
		'''
		'''
		if id == self.currentDataFile:
			storedData = self.df
		else:
			storedData = self.dfs[id]
		columnsJoinDf = otherDf.columns
		if len(definedColumnsList) == 0:
			columnsMissing = [columnName for columnName in storedData.columns  if columnName\
			 not in columnsJoinDf]
		else:
			# check if data are not in tobe joined df but are in general in the df that the 
			# values are taken from
			columnsMissing = [columnName for columnName in definedColumnsList if columnName \
			not in columnsJoinDf and columnName in storedData.columns]
		if len(columnsMissing) != 0: 
			resultDataFrame = otherDf.join(storedData[columnsMissing])
			return resultDataFrame
		else:
			return otherDf
		
		
		
	def melt_data_by_column(self,columnNameList):
		'''
		Melts data frame.
		'''
		indxName = self.add_count_through_column(columnName = 'PriorMeltIndex')
		idVars = [column for column in self.df.columns if column not in columnNameList] #all columns but the selected ones
		valueName = self.evaluate_column_name('melt_value{}'.format(columnNameList).replace("'",''))
		variableName = self.evaluate_column_name('melt_variable{}'.format(columnNameList).replace("'",''))		
		
		meltedDataFrame = pd.melt(self.df, id_vars = idVars, value_vars = columnNameList,
								var_name = variableName,
								value_name = valueName)
		## determine file name
		baseFile = self.get_file_name_of_current_data()	
		numMeltedfiles = len([file for file in self.fileNameByID.values() if 'Melted_' in file])			
		fileName =  'Melted_{}_of_{}'.format(numMeltedfiles,baseFile)	
		
		#delete indexColumn again
		self.delete_columns_by_label_list([indxName])
		
		id = self.get_next_available_id()					
		self.add_data_frame(meltedDataFrame,id = id, fileName = fileName)
		
		return id,fileName,self.dfsDataTypesAndColumnNames[id]
		
	
	def transform_data(self,columnNameList,transformation):
		'''
		Calculates data transformation and adds these to the data frame.
		'''
	
		
		newColumnNames = [self.evaluate_column_name('{}_{}'.format(transformation,columnName)) for columnName in columnNameList]
		if transformation == 'Z-Score_row':
			transformation = 'Z-Score'
			axis = 1
		elif transformation == 'Z-Score_col':
			transformation = 'Z-Score' 
			axis = 0 
		else:
			axis = 0 
		transformedDataFrame = self.df[columnNameList].apply(calculations[transformation], axis=axis)
		transformedDataFrame.columns = newColumnNames
		
		transformedDataFrame[~np.isfinite(transformedDataFrame)] = np.nan
		
		self.df[newColumnNames] = transformedDataFrame
		self.update_columns_of_current_data()
		
		return newColumnNames
	

	def update_data_frame(self,id,dataFrame):
		'''
		Updates dataframe, input: id and dataframe
		'''
		self.dfs[id] = dataFrame
		self.extract_data_type_of_columns(dataFrame,id)
		if id == self.currentDataFile:
			self.df = dataFrame
		
			

	def update_columns_of_current_data(self):
		'''
		Updates the variable: self.df_columns and renews the data type - column relationship.
		'''	
		self.df_columns = self.df.columns.values.tolist() 
		self.extract_data_type_of_columns(self.df,self.currentDataFile)	
		self.save_current_data()

	def replace_values_by_dict(self,replaceDict,id=None):
		'''
		Replaces values by dict. Dict must be nested in the form:
		{ColumnName:{Value:NewValue}}
		'''
		if id is None:
			pass
		else:
			self.set_current_data_by_id(id)
		self.df.replace(replaceDict,inplace=True)
		self.save_current_data()
		

	def resort_columns_in_current_data(self):
		'''
		Resorts columns alphabatically
		'''
		self.df.sort_index(axis = 1, inplace = True)
		self.update_columns_of_current_data()
		
		
		
	def save_current_data(self):
		'''
		Save the current active df into the dictionary self.dfs
		'''

		self.dfs[self.currentDataFile] = self.df	
	
	def set_current_data_by_id(self,id = None):
		'''
		Change current data by ID
		'''
		if id is None:
			return
		
		if self.currentDataFile != id:
			if self.df.empty == False:
		
				self.save_current_data() 
		
			self.df = self.dfs[id]
			self.df_columns = self.df.columns.values.tolist()
			
			self.currentDataFile = id
					
		
				
	def sort_columns_alphabetically(self):
		'''
		Sorts collumns alphabetically
		'''
		
		self.df.reindex_axis(sorted(self.df_columns), axis=1, inplace=True)
		self.update_columns_of_current_data()
		
	def sort_columns_by_string_length(self, columnName):
		'''
		Sort columns by string length. 
		
		'''
		columnNameLen = 'stringLen{}'.format(columnName)
		internalColumnNameForSorting = self.evaluate_column_name(columnNameLen)
		if self.df[columnName].dtype in [np.int64,np.float64]:
			self.df[internalColumnNameForSorting] = self.df[columnName].astype('str').str.len()
		else:
			self.df[internalColumnNameForSorting] = self.df[columnName].str.len()
		
		self.df.sort_values(internalColumnNameForSorting,kind='mergesort',inplace=True) 
		
		self.delete_columns_by_label_list([internalColumnNameForSorting])
		
		
		
			
	def sort_columns_by_value(self,columnNameOrListOfColumns, kind = 'mergesort', ascending = True, na_position = 'last'):
		'''
		Sort rows in one or multiple columns.
		'''
		if isinstance(columnNameOrListOfColumns, str):
			columnNameOrListOfColumns = [columnNameOrListOfColumns]
		
		if self.currentDataFile in self.rememberSorting:
			
			columnNameThatWereSortedAscending = self.rememberSorting[self.currentDataFile]			
			changeToDescending = [col for col in columnNameOrListOfColumns if col in columnNameThatWereSortedAscending]
			## Check if all columns were sorted already in ascending order 
			numToDescending = len(changeToDescending)
			if numToDescending == len(columnNameOrListOfColumns) and numToDescending > 0:
				ascending = False
				columnNameThatWereSortedAscending = [col for col in columnNameThatWereSortedAscending if col not in columnNameOrListOfColumns] 
				self.rememberSorting[self.currentDataFile] = columnNameThatWereSortedAscending
	
		
		self.df.sort_values(by = columnNameOrListOfColumns, kind= kind,
							ascending = ascending,
							na_position = na_position,
							inplace = True)			
		if ascending:
			## save columns that were already sorted 
			if self.currentDataFile in self.rememberSorting:
			
				columnNameThatWereSortedAscending = self.rememberSorting[self.currentDataFile]
				columnNamesToAdd = [col for col in columnNameOrListOfColumns if col not in columnNameThatWereSortedAscending] 
				columnNameThatWereSortedAscending.extend(columnNamesToAdd)
				self.rememberSorting[self.currentDataFile] = columnNameThatWereSortedAscending
					
			else:
				self.rememberSorting[self.currentDataFile] = columnNameOrListOfColumns	
						
		return ascending		
		
	def split_columns_by_string(self,columnNameOrListOfColumns,splitString):
		'''
		Function to Split Columns by a String provided by the User.
		Columns that are not already an object, are first changed. This is more a precaution since there are only rare cases
		when this can happen if any. 
		Data are inserted at the correct position after the input column. 
		(Might be a bit slower than join function but usually does not handle many datacolumns)
		'''
		indexInTreeview = 'end'
		if isinstance(columnNameOrListOfColumns,str):
			columnNameOrListOfColumns = [columnNameOrListOfColumns]
		for columnName in columnNameOrListOfColumns:
			if self.df[columnName].dtype == 'object':
				df_split = self.df[columnName].str.split(splitString ,expand=True) 
			else:
				df_split= self.df[columnName].astype('str').str.split(splitString ,expand=True) 
			expandedSplitOnDataColumns = df_split.columns	
			if len(expandedSplitOnDataColumns) == 1:
				return None, None
				
			indexColumnInData = self.df_columns.index(columnName)
			indexInTreeview = self.dfsDataTypesAndColumnNames[self.currentDataFile]['object'].index(columnName)
			
			newColumnNames = df_split.columns = ["{}_[by_{}]_{}".format(columnName,splitString,colIndex) for colIndex in expandedSplitOnDataColumns]
			df_split.fillna(self.replaceObjectNan,inplace=True)
			self.insert_data_frame_at_index(df_split,newColumnNames,indexColumnInData)
			
		self.update_columns_of_current_data()
		
		return newColumnNames, indexInTreeview 

			
			
			
	def rename_columnNames_in_current_data(self,replaceDict):
		'''
		Replaces column names in currently selected data frame.
		'''
		self.df.rename(str,columns=replaceDict,inplace=True)
		
		self.update_columns_of_current_data()		
		
		
		
				
		
	
		
		
		
	
	
	
	
	
	
		
		










