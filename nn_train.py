import pickle
from keras.layers import Embedding, Flatten, Dense
from keras.models import Graph
from keras.optimizers import Adam
import logging
from local_paths import *
import pandas as pd
import numpy as np

__author__ = 'mudit'

logging.getLogger().setLevel(logging.INFO)
[product_uid, input_features, output, train_query_vectors, query_vectors, prod, product_vectors] = pickle.load(
    open(OUTPUT_PATH + 'nn.pickle', 'rb'))

df_train = pd.read_csv(INPUT_PATH + 'df_train2.csv')
df_test = pd.read_csv(INPUT_PATH + 'df_test2.csv')

len_train = len(df_train)

input_features = pd.DataFrame(input_features).fillna(0).values


# product_uid = df_train['product_uid'].map(lambda x: product_id[x]).values.reshape(len_train, 1)
# input_features = df_train[['len_of_query', 'len_of_title',
#                            'len_of_description', 'len_of_brand',
#                            'query_in_title', 'query_in_description', 'word_in_title',
#                            'word_in_description', 'word_in_brand', 'ratio_title',
#                            'ratio_description', 'ratio_brand', 'brand_feature',
#                            'search_term_feature']].values
# output = df_train['relevance'].values
# train_query_vectors = query_vectors[:len_train]

graph = Graph()
graph.add_input(name='input_features', input_shape=(14,))
graph.add_input(name='product_uid', input_shape=(1,), dtype=int)
graph.add_input(name='query_vector', input_shape=(50,))
graph.add_node(Embedding(input_dim=len(prod)+1,
                         output_dim=50,
                         weights=[np.concatenate((np.zeros((1,50)),product_vectors),axis=0)],
                         trainable=True,
                         input_length=1),
               name='embedding',
               input='product_uid', )
graph.add_node(Flatten(), name='flatten', input='embedding')
graph.add_node(Dense(50, activation='sigmoid'), name='hidden0', inputs=['input_features', 'query_vector', 'flatten'],
               merge_mode="concat", concat_axis=1)
graph.add_node(Dense(50, activation='sigmoid'), name='hidden1', input='hidden0')
graph.add_node(Dense(50, activation='sigmoid'), name='hidden2', input='hidden1')
graph.add_node(Dense(1, activation='sigmoid'), name='output', input='hidden2', create_output=True)

graph.compile(optimizer='adadelta', loss={'output': 'mse'})

graph.fit(
    {'input_features': input_features, 'product_uid': product_uid, 'query_vector': train_query_vectors,
     'output': (output - 1) / 2},
    batch_size=256, nb_epoch=50, verbose=1, validation_split=0.2, shuffle=True)

test_input_features = df_test[['len_of_query', 'len_of_title',
                               'len_of_description', 'len_of_brand',
                               'query_in_title', 'query_in_description', 'word_in_title',
                               'word_in_description', 'word_in_brand', 'ratio_title',
                               'ratio_description', 'ratio_brand', 'brand_feature',
                               'search_term_feature']].values

test_input_features = pd.DataFrame(test_input_features).fillna(0).values
# Setting offset for product_id input
product_id = {}
k = prod.keys()
for id, prod_id in enumerate(k):
    product_id[prod_id] = id + 1

test_product_uid = df_test['product_uid'].map(lambda x: product_id[x]).values.reshape(len(df_test), 1)
test_query_vectors = query_vectors[len_train:]
test_output = df_test['relevance'].values

y_pred = graph.predict_on_batch({'input_features': test_input_features, 'product_uid': test_product_uid, 'query_vector': test_query_vectors})['output']

y_pred = y_pred*2+1

y_pred = y_pred.reshape(len(df_test))

pd.DataFrame({"id": df_test['id'].values, "relevance": y_pred}).to_csv('submission_nn_03.csv',index=False)



tuned_weights = graph.get_weights()[0]
# tuned_weights = tuned_weights

train_X = np.concatenate((input_features,tuned_weights[product_uid.reshape((len(product_uid)))]), axis=1)
train_X = np.concatenate((train_X, train_query_vectors), axis=1)

train_Y = output

test_X = np.concatenate((test_input_features,tuned_weights[test_product_uid.reshape((len(test_product_uid)))]), axis=1)
test_X = np.concatenate((test_X, test_query_vectors), axis = 1)

t_X = pd.DataFrame(train_X)
t_X.columns = ['feature_'+str(i) for i in range(114)]
t_X['relevance'] = output

t_X.to_csv(OUTPUT_PATH + 'X_features.csv', index=False)

t_Y = pd.DataFrame(test_X)
t_Y.columns = ['feature_'+str(i) for i in range(114)]
t_Y.to_csv(OUTPUT_PATH + 'X_features_test.csv', index=False)



# Evaluating error entries

train_y_pred = graph.predict({'input_features': input_features, 'product_uid': product_uid, 'query_vector': train_query_vectors})['output']
train_y_pred = train_y_pred*2+1
train_y_pred = train_y_pred.reshape((len(train_y_pred)))
train_error = output - train_y_pred

high_error_indexes = np.where(np.abs(train_error)>1)[0]

df_err = df_train.iloc[high_error_indexes]
df_err['predicted'] = train_y_pred[high_error_indexes]

df_err.to_csv(OUTPUT_PATH + 'high_error.csv', index=False)