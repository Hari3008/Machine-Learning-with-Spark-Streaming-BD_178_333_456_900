from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql import SQLContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, lower, regexp_replace
from pyspark.ml.feature import Tokenizer, StopWordsRemover, HashingTF
from nltk.stem.snowball import SnowballStemmer
from pyspark.sql.types import *
from pyspark.sql import functions as F
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.naive_bayes import MultinomialNB,BernoulliNB
from sklearn.linear_model import SGDClassifier,Perceptron
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix,f1_score
from sklearn.cluster import MiniBatchKMeans
import sys
import json
import pickle
clf = BernoulliNB()
clf2 = Perceptron()
clf3 = SGDClassifier()
#sc = SparkContext(master, appName)

def getTweets(rdd):
	
	x = rdd.collect()
	if(len(x)>0):
		df = spark.createDataFrame(json.loads(x[0]).values() , schema = ["Sentiment" , "Tweet"]) #creates the dataframe
		#df.show(truncate=False)
		#print(json.loads(x[0]).values())
		train_df = tweet_processing(df)
		train_models(train_df)

def tweet_processing(df):

	text_col = 'Tweet'
	Tweet = df.select(text_col).filter(F.col(text_col).isNotNull())
	# Clean text
	df_clean = df.select('Sentiment', (lower(regexp_replace('Tweet',"[^a-zA-Z\\s]", "")).alias('Tweet')))
	# Tokenize text
	tokenizer = Tokenizer(inputCol='Tweet', outputCol='Tokenized_words')
	df_words_token = 		tokenizer.transform(df_clean).select('Sentiment','Tokenized_words')
	# df_words_token.show(truncate=False)
	remover = StopWordsRemover(inputCol='Tokenized_words',outputCol='Clean_Tweets')
	df_cleaned = remover.transform(df_words_token).select('Sentiment','Clean_Tweets')
	# Stem text
	stemmer = SnowballStemmer(language='english')
	stemmer_udf = udf(lambda tokens: [stemmer.stem(token) for token in tokens], ArrayType(StringType()))
	df_stemmed = 	df_cleaned.withColumn("Stemmed_Tweets",stemmer_udf("Clean_Tweets")).select('Sentiment','Stemmed_Tweets')
	filter_length_udf = udf(lambda row: [x for x in row if len(x) >= 3], ArrayType(StringType()))
	df_final_words = df_stemmed.withColumn('Final_tweets',filter_length_udf(col('Stemmed_Tweets'))).select('Sentiment','Final_tweets')
	hashTF = HashingTF(inputCol='Final_tweets', outputCol="Features")
	numericTrainData = hashTF.transform(df_final_words).select('Sentiment', 'Final_tweets', 'Features')
	removed1 = udf(joinwords, StringType())
	new_df1 = numericTrainData.withColumn("Final_Tweets",removed1(numericTrainData["Final_Tweets"]))
	return new_df1

def joinwords(text):
  	new_text = " ".join(text)
  	return new_text 

def train_models(train_df):
	X=train_df.select('Final_Tweets').collect()
	X=[i['Final_Tweets'] for i in X]

	vectorizer = HashingVectorizer(n_features=10)
	X = vectorizer.fit_transform(X)
	y=train_df.select('Sentiment').collect()
	y=np.array([i[0] for i in np.array(y)])
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.33)
	
	#Bernoulli NB
	model = clf.partial_fit(X_train, y_train, classes = np.unique(y_train))
	pred1 = model.predict(X_test)
	ac1 = accuracy_score(y_test, pred1)
	prec1 = precision_score(y_test, pred1,pos_label=4)
	f11 = f1_score(y_test,pred1,pos_label=4)
	rec1 = recall_score(y_test, pred1,pos_label=4)
	conf_matrix1 = confusion_matrix(y_test, pred1)
	kmeans = MiniBatchKMeans(n_clusters=2, random_state=0, batch_size=6)
	kmodel = kmeans.fit(X_train)

	print("------------------BernoulliNB MODEL-----------------")
	print("Accuracy Score: ", ac1)
	print("Precision Score: ", prec1)
	print("F1 Score: ", f11)
	print("Recall Score: ", rec1)
	print("Confusion Matrix: \n", conf_matrix1)
	filename = 'Bernoulli_model.sav'
	pickle.dump(model,open(filename,'wb'))
	filenamek = 'Bernoulli_model_Kmeans.sav'
	pickle.dump(kmodel,open(filenamek,'wb'))
	
	#Perceptron Classifier
	model2 = clf2.partial_fit(X_train.toarray(), y_train, classes = np.unique(y_train))
	pred2 = model2.predict(X_test)
	ac2 = accuracy_score(y_test, pred2)
	f12 = f1_score(y_test,pred2,pos_label=4)
	prec2 = precision_score(y_test, pred2,pos_label=4)
	rec2 = recall_score(y_test, pred2,pos_label=4)
	conf_matrix2 = confusion_matrix(y_test, pred2)
	kmeans2 = MiniBatchKMeans(n_clusters=2, random_state=0, batch_size=6)
	kmodel2 = kmeans2.fit(X_train)

	print("------------------Perceptron MODEL-----------------")
	print("Accuracy Score: ", ac2)
	print("Precision Score: ", prec2)
	print("F1 Score: ", f12)
	print("Recall Score: ", rec2)
	print("Confusion Matrix: \n", conf_matrix2)
	filename = 'Perceptron_Model.sav'
	pickle.dump(model2,open(filename,'wb'))
	filenamek = 'Perceptron_Model_Kmeans.sav'
	pickle.dump(kmodel2,open(filenamek,'wb'))
	
	#SGD Classifier
	model3 = clf3.partial_fit(X_train.toarray(), y_train, classes = np.unique(y_train))
	pred3 = model3.predict(X_test)
	ac3 = accuracy_score(y_test, pred3)
	f13 = f1_score(y_test,pred3,pos_label=4)
	prec3 = precision_score(y_test, pred3,pos_label=4)
	rec3 = recall_score(y_test, pred3,pos_label=4)
	conf_matrix3 = confusion_matrix(y_test, pred3)
	kmeans3 = MiniBatchKMeans(n_clusters=2, random_state=0, batch_size=6)
	kmodel3 = kmeans3.fit(X_train)

	print("------------------SGD Classifier MODEL-----------------")
	print("Accuracy Score: ", ac3)
	print("Precision Score: ", prec3)
	print("F1 Score: ", f13)
	print("Recall Score: ", rec3)
	print("Confusion Matrix: \n", conf_matrix3)
	filename = 'SGD_Classifier.sav'
	pickle.dump(model3,open(filename,'wb'))
	filenamek = 'SGD_Classifier_Kmeans.sav'
	pickle.dump(kmodel3,open(filenamek,'wb'))
	
	
if __name__ == "__main__":
	
	spark = SparkSession.builder.master("local[2]").appName('GetTweet').getOrCreate()
	ssc = StreamingContext(spark.sparkContext,1)
	sqlContext = SQLContext(spark)
#lines = spark.readStream.format("socket").option("host","localhost").option("port", 6100).load()
#sqlContext = SQLContext(spark)
	lines = ssc.socketTextStream("localhost",6100)
	words = lines.flatMap(lambda line: line.split("\n"))
	words.foreachRDD(getTweets)
	
	ssc.start() # Start the computation
	ssc.awaitTermination()
