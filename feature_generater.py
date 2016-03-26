from gensim.models.doc2vec import TaggedDocument
from sklearn import pipeline
from sklearn.base import TransformerMixin
from sklearn.base import BaseEstimator
from sklearn.decomposition import TruncatedSVD, NMF, PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import make_scorer, mean_squared_error
from sklearn.pipeline import FeatureUnion
import logging
import Levenshtein
from utilities import cust_txt_col, cust_regression_vals

logging.getLogger().setLevel(logging.INFO)

__author__ = 'mudit'

from load_preprocessed import *
import numpy as np
from gensim.models import Doc2Vec
from nltk.util import ngrams

print('- Data and Modules Loaded')

edit_ratio = lambda x, y: Levenshtein.ratio(x, y)
edit_seqratio = lambda x, y: Levenshtein.seqratio(x, y)


def min_edit_dist(query, text):
    t_query = query.split()
    t_text = text.split()
    s = 0
    for t in t_query:
        s += min([Levenshtein.distance(t, token) for token in t_text])
    return s


def str_common_word(str1, str2):
    words, cnt = str1.split(), 0
    for word in words:
        if str2.find(word) >= 0:
            cnt += 1
    return cnt


def str_whole_word(str1, str2, i_):
    cnt = 0
    while i_ < len(str2):
        i_ = str2.find(str1, i_)
        if i_ == -1:
            return cnt
        else:
            cnt += 1
            i_ += len(str1)
    return cnt


def ngram_match(query, string):
    q_tokens = query.split(' ')
    max_n = len(q_tokens)
    total = 0
    similar = 0
    for i in range(1, max_n + 1):
        ngms = ngrams(q_tokens, i)
        for gram in ngms:
            if string.find(" ".join(gram)) >= 0:
                similar += 1
            total += 1
    return similar / float(total)


df_all = df_all.fillna(' ')

# Extracting common features
df_all['len_of_query'] = df_all['search_term'].map(lambda x: len(x.split())).astype(np.int64)
df_all['len_of_title'] = df_all['product_title'].map(lambda x: len(x.split())).astype(np.int64)
df_all['len_of_description'] = df_all['product_description'].map(lambda x: len(x.split())).astype(np.int64)
df_all['len_of_brand'] = df_all['brand'].map(lambda x: len(x.split())).astype(np.int64)

df_all['product_info'] = df_all['search_term'] + "\t" + df_all['product_title'] + "\t" + df_all['product_description']
df_all['attr'] = df_all['search_term'] + "\t" + df_all['brand']

df_all['query_in_title'] = df_all['product_info'].map(lambda x: str_whole_word(x.split('\t')[0], x.split('\t')[1], 0))
df_all['query_in_description'] = df_all['product_info'].map(
    lambda x: str_whole_word(x.split('\t')[0], x.split('\t')[2], 0))
df_all['edit_dist_in_info'] = df_all['product_info'].map(
    lambda x: min_edit_dist(x.split('\t')[0], x.split('\t')[1] + ' ' + x.split('\t')[2]))
df_all['edit_ratio_in_info'] = df_all['edit_dist_in_info'] / df_all['len_of_query']

df_all['word_in_title'] = df_all['product_info'].map(lambda x: str_common_word(x.split('\t')[0], x.split('\t')[1]))
df_all['edit_in_title'] = df_all['product_info'].map(lambda x: edit_ratio(x.split('\t')[0], x.split('\t')[1]))
df_all['seq_edit_in_title'] = df_all['product_info'].map(lambda x: edit_seqratio(x.split('\t')[0], x.split('\t')[1]))
df_all['word_in_description'] = df_all['product_info'].map(
    lambda x: str_common_word(x.split('\t')[0], x.split('\t')[2]))
df_all['word_in_brand'] = df_all['attr'].map(lambda x: str_common_word(x.split('\t')[0], x.split('\t')[1]))

df_all['ratio_title'] = df_all['word_in_title'] / df_all['len_of_query']
df_all['ratio_description'] = df_all['word_in_description'] / df_all['len_of_query']
df_all['ratio_brand'] = df_all['word_in_brand'] / df_all['len_of_brand']
df_all['ngram_match_title'] = df_all['product_info'].map(lambda x: ngram_match(x.split('\t')[0], x.split('\t')[1]))
df_all['ngram_match_description'] = df_all['product_info'].map(lambda x: ngram_match(x.split('\t')[0], x.split('\t')[2]))

df_brand = pd.unique(df_all.brand.ravel())
d = {}
i = 1
for s in df_brand:
    d[s] = i
    i += 1
df_all['brand_feature'] = df_all['brand'].map(lambda x: d[x])
df_all['search_term_feature'] = df_all['search_term'].map(lambda x: len(x))

print('- Common Features Extracted')

df_train = df_all[:len_train]
df_test = df_all[len_train:]

df_train.to_csv(INPUT_PATH + "df_train2.csv", index=False)
df_test.to_csv(INPUT_PATH + "df_test2.csv", index=False)


# TF-IDF and other features
tfidf = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
tsvd = TruncatedSVD(n_components=20, random_state=2016)
tnmf = NMF(n_components=20, random_state=2016)
fu = FeatureUnion(
    transformer_list=[
        ('cst', cust_regression_vals()),
        ('txt1', pipeline.Pipeline([('s1', cust_txt_col(key='search_term')), ('tfidf1', tfidf), ('tsvd1', tsvd)])),
        (
            'txt2',
            pipeline.Pipeline([('s2', cust_txt_col(key='product_title')), ('tfidf2', tfidf), ('tsvd2', tsvd)])),
        ('txt3',
         pipeline.Pipeline([('s3', cust_txt_col(key='product_description')), ('tfidf3', tfidf), ('tsvd3', tsvd)])),
        ('txt4', pipeline.Pipeline([('s4', cust_txt_col(key='brand')), ('tfidf4', tfidf), ('tsvd4', tsvd)]))
    ],
    transformer_weights={
        'cst': 1.0,
        'txt1': 0.5,
        'txt2': 0.25,
        'txt3': 0.0,
        'txt4': 0.5
    },
    # n_jobs = -1
)

id_test = df_test['id']
y_train = df_train['relevance'].values
X_train = df_train[:].fillna(0)
X_test = df_test[:].fillna(0)


fu.fit(pd.concat((X_train, X_test)))
X_train = fu.transform(X_train)
X_test = fu.transform(X_test)

X_train.dump(INPUT_PATH + 'X_train.numpy')
X_test.dump(INPUT_PATH + 'X_test.numpy')
y_train.dump(INPUT_PATH + 'y_train.numpy')
id_test.values.dump(INPUT_PATH + 'id_test.numpy')

# Implementing Doc2Vec::Gensim
# print("- Extracting Doc2Vec Features")

# def array_to_document(sources):
#     sentences = []
#     for id, source in enumerate(sources):
#         sentences.append(TaggedDocument(source.split(), ['doc_' + str(id)]))
#     return sentences

# print('\t- Preparing data')

# product_info = (df_all['search_term'] + " " + df_all['product_title'] + " " + df_all['product_description']).astype(str)
# product_info = array_to_document(product_info)
#
# model = Doc2Vec(size=100, window=8, min_count=5, workers=384, alpha=0.025, min_alpha=0.025)
# model.build_vocab(product_info)
#
# for epoch in range(10):
#     print("\t- Train #" + str(epoch + 1))
#     model.train(product_info)
#     model.alpha -= 0.0002  # decrease the learning rate
#     model.min_alpha = model.alpha  # fix the learning rate, no decay
#
# print('\t- Saving Doc2Vec model')
# model.save(INPUT_PATH + 'doc2vec')

# model = Doc2Vec.load(INPUT_PATH + 'doc2vec')

# print('\t- Loaded Doc2Vec model')

# weights = [model.docvecs['doc_' + str(id)] for id in range(len(product_info))]
# weights = pd.DataFrame(weights)
# weights.columns = weights.columns.to_series().map(lambda x: 'feature_' + str(x))

# df_all = pd.concat([df_all, weights], axis=1)