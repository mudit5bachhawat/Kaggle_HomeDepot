from utilities import SimpleTransform
from generate_dataset import generate_dataset
__author__ = 'mudit'

if __name__ == '__main__':

    features = [
        ('ngram_match_brand', SimpleTransform()),
        ('brand_features', SimpleTransform()),
        ('edit_dist_in_info', SimpleTransform()),
        ('edit_dist_in_product_description', SimpleTransform()),
        ('edit_dist_in_product_title', SimpleTransform()),
        ('edit_in_brand', SimpleTransform()),
        ('edit_in_product_description', SimpleTransform()),
        ('edit_in_product_title', SimpleTransform()),
        ('edit_ratio_in_info', SimpleTransform()),
        ('edit_ratio_in_product_description', SimpleTransform()),
        ('edit_ratio_in_product_title', SimpleTransform()),
        ('len_of_brand', SimpleTransform()),
        ('len_of_product_description', SimpleTransform()),
        ('len_of_product_title', SimpleTransform()),
        ('len_of_search_term', SimpleTransform()),
        ('ngram_match_product_description', SimpleTransform()),
        ('ngram_match_product_title', SimpleTransform()),
        ('query_in_description', SimpleTransform()),
        ('query_in_title', SimpleTransform()),
        ('search_term_features', SimpleTransform()),
        ('seq_edit_in_brand', SimpleTransform()),
        ('seq_edit_in_product_description', SimpleTransform()),
        ('seq_edit_in_product_title', SimpleTransform()),
        ('tfidf_svd50_product_description_vector', SimpleTransform()),
        ('tfidf_svd50_product_title_vector', SimpleTransform()),
        ('tfidf_svd50_search_term_vector', SimpleTransform()),
        ('word_in_brand', SimpleTransform()),
        ('word_in_product_description', SimpleTransform()),
        ('word_in_product_title', SimpleTransform()),
        ('word_ratio_in_brand', SimpleTransform()),
        ('word_ratio_in_product_description', SimpleTransform()),
        ('word_ratio_in_product_title', SimpleTransform()),
    ]


    generate_dataset(features, 'svd50x3')